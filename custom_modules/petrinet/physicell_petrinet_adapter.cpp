#include "physicell_petrinet_adapter.h"
#include "mhcii_cd4_coupling.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <limits>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace xenophagy {
namespace {

const char* target_names[] = {
    "PD-L1lo_tumor", "PD-L1hi_tumor",
    "PD-L1lo_tumor_infected", "PD-L1lo_tumor_xenophagy",
    "PD-L1hi_tumor_infected", "PD-L1hi_tumor_xenophagy"
};

const char* cd4_names[] = {"PD-1hi_CD4_Tcell", "PD-1lo_CD4_Tcell"};

void set_cd4_immunogenicity(PhysiCell::Cell* tumor, double value) {
    for (const char* cd4_name : cd4_names)
        tumor->phenotype.cell_interactions.immunogenicity(cd4_name) = value;
}

struct ScheduledEntry {
    double time_minutes;
    long long cell_id;
    int cytosol;
    int vacuole;
};

// The engine is constructed in setup_petrinet_integration(), once the run XML
// is parsed: the model JSON path is a run parameter, not a compile-time choice.
std::unique_ptr<PetriNetEngine> engine_ptr;
std::vector<std::unique_ptr<CellPetriNetState>> state_pool;
std::vector<std::size_t> free_slots;
std::unordered_map<unsigned int, std::size_t> slots_by_cell;
std::mutex pool_mutex;
std::vector<ScheduledEntry> schedule;
std::size_t next_schedule = 0;
std::uint64_t global_seed = 0;
bool integration_enabled = false;
std::ofstream metrics_file;
std::ofstream uptake_file;
double metrics_interval_minutes = 0.0;
double next_metrics_time_minutes = 0.0;
double next_uptake_time_minutes = 0.0;
std::mt19937_64 uptake_rng;

enum class BacterialInputMode { Manual = 0, Agent = 1, Hybrid = 2 };
BacterialInputMode input_mode = BacterialInputMode::Manual;

bool manual_input_enabled() {
    return input_mode == BacterialInputMode::Manual ||
           input_mode == BacterialInputMode::Hybrid;
}

bool agent_input_enabled() {
    return input_mode == BacterialInputMode::Agent ||
           input_mode == BacterialInputMode::Hybrid;
}

std::uint64_t mix_seed(std::uint64_t value) {
    value += 0x9e3779b97f4a7c15ULL;
    value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
    value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
    return value ^ (value >> 31);
}

std::size_t allocate_locked(unsigned int cell_id, double time_seconds) {
    auto found = slots_by_cell.find(cell_id);
    if (found != slots_by_cell.end()) return found->second;
    std::size_t slot;
    if (free_slots.empty()) {
        slot = state_pool.size();
        state_pool.emplace_back();
    } else {
        slot = free_slots.back();
        free_slots.pop_back();
    }
    const std::uint64_t seed = mix_seed(global_seed ^ static_cast<std::uint64_t>(cell_id));
    state_pool[slot].reset(new CellPetriNetState(seed));
    state_pool[slot]->internal_time_seconds = time_seconds;
    slots_by_cell[cell_id] = slot;
    return slot;
}

CellPetriNetState* state_for(PhysiCell::Cell* cell, bool create) {
    std::lock_guard<std::mutex> guard(pool_mutex);
    auto found = slots_by_cell.find(cell->ID);
    if (found == slots_by_cell.end()) {
        if (!create) return nullptr;
        const std::size_t slot = allocate_locked(cell->ID, PhysiCell::PhysiCell_globals.current_time * 60.0);
        cell->custom_data["pn_state_index"] = static_cast<double>(slot);
        return state_pool[slot].get();
    }
    return state_pool[found->second].get();
}

void add_observables(PhysiCell::Cell_Definition* definition) {
    if (definition->custom_data.find_variable_index("pn_state_index") < 0)
        definition->custom_data.add_variable("pn_state_index", "dimensionless", -1.0);
    if (definition->custom_data.find_variable_index("pn_active") < 0)
        definition->custom_data.add_variable("pn_active", "dimensionless", 0.0);
    if (definition->custom_data.find_variable_index("intracellular_bacteria") < 0)
        definition->custom_data.add_variable("intracellular_bacteria", "count", 0.0);
    if (definition->custom_data.find_variable_index("sal_ruffle_tokens") < 0)
        definition->custom_data.add_variable("sal_ruffle_tokens", "count", 0.0);
    if (definition->custom_data.find_variable_index("uptaken_bacteria") < 0)
        definition->custom_data.add_variable("uptaken_bacteria", "count", 0.0);
    if (definition->custom_data.find_variable_index("xenophagy_activity") < 0)
        definition->custom_data.add_variable("xenophagy_activity", "count", 0.0);
    if (definition->custom_data.find_variable_index("ap_gal8_tokens") < 0)
        definition->custom_data.add_variable("ap_gal8_tokens", "count", 0.0);
    if (definition->custom_data.find_variable_index("ap_ub_tokens") < 0)
        definition->custom_data.add_variable("ap_ub_tokens", "count", 0.0);
    if (definition->custom_data.find_variable_index("surface_pMHC") < 0)
        definition->custom_data.add_variable("surface_pMHC", "count", 0.0);
    if (definition->custom_data.find_variable_index("surface_pMHC_I") < 0)
        definition->custom_data.add_variable("surface_pMHC_I", "count", 0.0);
    if (definition->custom_data.find_variable_index("surface_pMHC_II") < 0)
        definition->custom_data.add_variable("surface_pMHC_II", "count", 0.0);
    if (definition->custom_data.find_variable_index("mhcii_cd4_recognition") < 0)
        definition->custom_data.add_variable("mhcii_cd4_recognition", "dimensionless", 0.0);
    if (definition->custom_data.find_variable_index("pn_death_probability") < 0)
        definition->custom_data.add_variable("pn_death_probability", "dimensionless", 0.0);
}

std::vector<std::string> split_csv(const std::string& line) {
    std::vector<std::string> fields;
    std::stringstream stream(line);
    std::string field;
    while (std::getline(stream, field, ',')) fields.push_back(field);
    return fields;
}

void load_schedule(const std::string& path) {
    schedule.clear();
    next_schedule = 0;
    if (path.empty()) return;
    std::ifstream file(path.c_str());
    if (!file) throw std::runtime_error("cannot open PetriNet entry CSV: " + path);
    std::string line;
    if (!std::getline(file, line) || line != "time_min,cell_id,to_cytosol,to_vacuole")
        throw std::runtime_error("invalid PetriNet entry CSV header");
    std::size_t row = 1;
    while (std::getline(file, line)) {
        ++row;
        if (line.empty()) continue;
        const std::vector<std::string> f = split_csv(line);
        if (f.size() != 4) throw std::runtime_error("invalid entry CSV row " + std::to_string(row));
        ScheduledEntry event{std::stod(f[0]), std::stoll(f[1]), std::stoi(f[2]), std::stoi(f[3])};
        if (!std::isfinite(event.time_minutes) || event.time_minutes < 0.0 || event.cell_id < -1 ||
            event.cytosol < 0 || event.vacuole < 0)
            throw std::runtime_error("invalid value in entry CSV row " + std::to_string(row));
        schedule.push_back(event);
    }
    std::stable_sort(schedule.begin(), schedule.end(), [](const ScheduledEntry& a, const ScheduledEntry& b) {
        return a.time_minutes < b.time_minutes;
    });
}

} // namespace

bool is_target_tumor_cell(const PhysiCell::Cell* cell) {
    for (const char* name : target_names) if (cell->type_name == name) return true;
    return false;
}

void register_petrinet_custom_data() {
    // PhysiCell's MultiCellDS writer expects every definition to share the
    // default custom-data layout. Register before parsing inherited types.
    add_observables(&PhysiCell::cell_defaults);
}

void setup_petrinet_integration() {
    integration_enabled = PhysiCell::parameters.bools("petrinet_enabled");
    if (!integration_enabled) return;
    global_seed = static_cast<std::uint64_t>(PhysiCell::parameters.ints("petrinet_global_seed"));
    const int configured_mode = PhysiCell::parameters.ints("petrinet_input_mode");
    if (configured_mode < 0 || configured_mode > 2)
        throw std::runtime_error("petrinet_input_mode must be 0, 1, or 2");
    input_mode = static_cast<BacterialInputMode>(configured_mode);

    // Build the engine from the run-selected model. Empty keeps the historical
    // default so existing configs are unaffected.
    EngineConfig engine_config;
    const std::string model_json = PhysiCell::parameters.strings("petrinet_model_json");
    if (!model_json.empty()) engine_config.model_json = model_json;
    engine_config.syn_mm = {
        {"Syn1", "Gal8"},
        {"Syn2", "E3_ligase"},
        {"Syn4", "p62"},
        {"Syn5", "NDP52"},
        {"Syn6", "OPTN"},
        {"Syn7", "N_S"},
        {"Syn8", "TBK1"},
        {"Syn9", "mTORC1_ULK1comp"},
        {"Syn10", "LC3"},
    };
    engine_config.syn_baseline = 200.0;
    engine_ptr.reset(new PetriNetEngine(engine_config));
    std::cout << "[PetriNet] model: " << engine_config.model_json << "\n";

    uptake_rng.seed(mix_seed(global_seed ^ 0x42555054414b45ULL));
    next_uptake_time_minutes = parameters().bacterial_uptake_interval;
    if (manual_input_enabled())
        load_schedule(PhysiCell::parameters.strings("petrinet_entry_csv"));
    metrics_interval_minutes = PhysiCell::parameters.doubles("petrinet_metrics_interval");
    const std::string metrics_path = PhysiCell::parameters.strings("petrinet_metrics_csv");
    if (!metrics_path.empty()) {
        metrics_file.open(metrics_path.c_str(), std::ios::out | std::ios::trunc);
        if (!metrics_file) throw std::runtime_error("cannot open PetriNet metrics CSV: " + metrics_path);
        metrics_file << "time_min,cell_id,cell_type,intracellular_bacteria,"
                        "sal_ruffle_tokens,uptaken_bacteria,"
                        "ap_gal8_tokens,ap_ub_tokens,xenophagy_activity,"
                        "surface_pMHC,surface_pMHC_I,surface_pMHC_II,"
                        "mhcii_cd4_recognition,physicell_damage,"
                        "death_probability,is_dead,"
                        "petrinet_death_triggered,death_time_min\n";
    }
    if (agent_input_enabled()) {
        const std::string uptake_path = PhysiCell::parameters.strings("petrinet_uptake_csv");
        if (!uptake_path.empty()) {
            uptake_file.open(uptake_path.c_str(), std::ios::out | std::ios::trunc);
            if (!uptake_file) throw std::runtime_error("cannot open PetriNet uptake CSV: " + uptake_path);
            uptake_file << "time_min,bacteria_id,tumor_id,tokens,entry_place,result\n";
        }
    }
    for (const char* name : target_names) {
        PhysiCell::Cell_Definition* definition = PhysiCell::find_cell_definition(name);
        if (!definition) continue;
        definition->functions.update_phenotype = petrinet_phenotype;
        definition->functions.cell_division_function = petrinet_division;
        for (const char* cd4_name : cd4_names)
            definition->phenotype.cell_interactions.immunogenicity(cd4_name) = 0.0;
    }
    for (const char* cd4_name : cd4_names) {
        PhysiCell::Cell_Definition* definition = PhysiCell::find_cell_definition(cd4_name);
        if (!definition) continue;
        for (const char* target_name : target_names)
            definition->phenotype.cell_interactions.attack_rate(target_name) =
                parameters().mhcii_cd4_attack_max;
    }
}

void inject_hardcoded_demo_event() {
    if (!integration_enabled || !manual_input_enabled()) return;
    const int bacteria = PhysiCell::parameters.ints("petrinet_demo_vacuolar_bacteria");
    if (bacteria <= 0) return;
    for (PhysiCell::Cell* cell : *PhysiCell::all_cells) {
        if (!cell->phenotype.death.dead && is_target_tumor_cell(cell))
            enqueue_bacterial_entry(cell, 0.0, 0, bacteria);
    }
    std::cout << "[PetriNet demo] injected " << bacteria
              << " vacuolar bacteria into each target tumor cell at t=0 min\n";
}

void enqueue_bacterial_entry(PhysiCell::Cell* cell, double time_minutes,
                              int to_cytosol, int to_vacuole) {
    if (!integration_enabled || !cell || !is_target_tumor_cell(cell)) return;
    CellPetriNetState* state = state_for(cell, true);
    engine_ptr->enqueue(*state, EntryEvent(time_minutes * 60.0, to_cytosol, to_vacuole));
}

void enqueue_bacterial_uptake(PhysiCell::Cell* cell, double time_minutes,
                               int bacteria_count) {
    if (!integration_enabled || !cell || !is_target_tumor_cell(cell)) return;
    if (bacteria_count < 0) throw std::invalid_argument("bacterial uptake count must be non-negative");
    if (bacteria_count == 0) return;
    CellPetriNetState* state = state_for(cell, true);
    engine_ptr->enqueue(*state, EntryEvent(time_minutes * 60.0, bacteria_count, 0, 0));
}

void process_bacterial_entry_schedule(double current_time_minutes) {
    if (!integration_enabled || !manual_input_enabled()) return;
    while (next_schedule < schedule.size() && schedule[next_schedule].time_minutes <= current_time_minutes + 1e-12) {
        const ScheduledEntry& event = schedule[next_schedule++];
        bool delivered = false;
        for (PhysiCell::Cell* cell : *PhysiCell::all_cells) {
            if (cell->phenotype.death.dead || !is_target_tumor_cell(cell)) continue;
            if (event.cell_id == -1 || static_cast<long long>(cell->ID) == event.cell_id) {
                enqueue_bacterial_entry(cell, event.time_minutes, event.cytosol, event.vacuole);
                delivered = true;
            }
        }
        if (!delivered && event.cell_id != -1)
            std::cerr << "[PetriNet] entry target cell " << event.cell_id << " was not found\n";
    }
}

void process_extracellular_bacterial_uptake(double current_time_minutes) {
    if (!integration_enabled || !agent_input_enabled()) return;
    const double interval = parameters().bacterial_uptake_interval;
    if (current_time_minutes + 1e-9 < next_uptake_time_minutes) return;

    struct Decision {
        PhysiCell::Cell* bacterium;
        PhysiCell::Cell* tumor;
        double event_time;
    };

    while (next_uptake_time_minutes <= current_time_minutes + 1e-9) {
        std::vector<PhysiCell::Cell*> bacteria;
        for (PhysiCell::Cell* cell : *PhysiCell::all_cells) {
            if (!cell->phenotype.death.dead && !cell->phenotype.flagged_for_removal &&
                cell->type_name == "Bifidobacterium_longum")
                bacteria.push_back(cell);
        }
        std::sort(bacteria.begin(), bacteria.end(), [](const PhysiCell::Cell* a, const PhysiCell::Cell* b) {
            return a->ID < b->ID;
        });

        std::vector<Decision> decisions;
        const double radius2 = parameters().bacterial_uptake_distance *
                               parameters().bacterial_uptake_distance;
        const double probability = -std::expm1(
            -parameters().bacterial_uptake_rate * interval);

        for (PhysiCell::Cell* bacterium : bacteria) {
            const int voxel = bacterium->get_current_mechanics_voxel_index();
            if (voxel < 0) continue;
            PhysiCell::Cell* nearest = nullptr;
            double nearest_d2 = std::numeric_limits<double>::infinity();
            std::vector<int> voxels(1, voxel);
            const std::vector<int>& adjacent = bacterium->get_container()->underlying_mesh
                .moore_connected_voxel_indices[voxel];
            voxels.insert(voxels.end(), adjacent.begin(), adjacent.end());
            for (int candidate_voxel : voxels) {
                for (PhysiCell::Cell* candidate : bacterium->get_container()->agent_grid[candidate_voxel]) {
                    if (candidate->phenotype.death.dead || candidate->phenotype.flagged_for_removal ||
                        !is_target_tumor_cell(candidate)) continue;
                    const double dx = bacterium->position[0] - candidate->position[0];
                    const double dy = bacterium->position[1] - candidate->position[1];
                    const double dz = bacterium->position[2] - candidate->position[2];
                    const double d2 = dx * dx + dy * dy + dz * dz;
                    if (d2 > radius2) continue;
                    if (!nearest || d2 < nearest_d2 - 1e-12 ||
                        (std::fabs(d2 - nearest_d2) <= 1e-12 && candidate->ID < nearest->ID)) {
                        nearest = candidate;
                        nearest_d2 = d2;
                    }
                }
            }
            if (nearest && std::generate_canonical<double, 53>(uptake_rng) < probability)
                // Use the public clock, not the idealized scheduler boundary:
                // a lazily-created state starts at current_time and must never
                // receive an event a few floating-point ticks in its past.
                decisions.push_back(Decision{bacterium, nearest, current_time_minutes});
        }

        std::sort(decisions.begin(), decisions.end(), [](const Decision& a, const Decision& b) {
            return a.bacterium->ID < b.bacterium->ID;
        });
        for (const Decision& decision : decisions) {
            const unsigned int bacteria_id = decision.bacterium->ID;
            const unsigned int tumor_id = decision.tumor->ID;
            enqueue_bacterial_uptake(decision.tumor, decision.event_time, 1);
            if (uptake_file.is_open())
                uptake_file << decision.event_time << ',' << bacteria_id << ',' << tumor_id
                            << ",1,SalRuffle,accepted\n";
            PhysiCell::delete_cell(decision.bacterium);
        }
        if (uptake_file.is_open()) uptake_file.flush();
        next_uptake_time_minutes += interval;
    }
}

void write_petrinet_metrics(double current_time_minutes) {
    if (!integration_enabled || !metrics_file.is_open() || metrics_interval_minutes <= 0.0) return;
    if (current_time_minutes + 1e-9 < next_metrics_time_minutes) return;
    while (next_metrics_time_minutes <= current_time_minutes + 1e-9)
        next_metrics_time_minutes += metrics_interval_minutes;
    for (PhysiCell::Cell* cell : *PhysiCell::all_cells) {
        if (!is_target_tumor_cell(cell)) continue;
        CellPetriNetState* state = state_for(cell, false);
        if (!state || !state->active) continue;
        if (cell->phenotype.death.dead && state->death_time_minutes < 0.0)
            state->death_time_minutes = current_time_minutes;
        metrics_file << current_time_minutes << ',' << cell->ID << ',' << cell->type_name << ','
                     << cell->custom_data["intracellular_bacteria"] << ','
                     << engine_ptr->sal_ruffle_tokens(state->marking) << ','
                     << engine_ptr->uptaken_bacterial_burden(state->marking) << ','
                     << engine_ptr->gal8_autophagosome_tokens(state->marking) << ','
                     << engine_ptr->ub_autophagosome_tokens(state->marking) << ','
                     << cell->custom_data["xenophagy_activity"] << ','
                     << cell->custom_data["surface_pMHC"] << ','
                     << cell->custom_data["surface_pMHC_I"] << ','
                     << cell->custom_data["surface_pMHC_II"] << ','
                     << cell->custom_data["mhcii_cd4_recognition"] << ','
                     << cell->phenotype.cell_integrity.damage << ','
                     << cell->custom_data["pn_death_probability"] << ','
                     << (cell->phenotype.death.dead ? 1 : 0) << ','
                     << (state->petrinet_death_triggered ? 1 : 0) << ','
                     << state->death_time_minutes << '\n';
    }
    metrics_file.flush();
}

void petrinet_phenotype(PhysiCell::Cell* cell, PhysiCell::Phenotype& phenotype,
                        double dt_minutes) {
    if (!integration_enabled || phenotype.death.dead) return;
    CellPetriNetState* state = state_for(cell, false);
    if (!state) return;
    // PhysiCell calls this callback at the end of the elapsed phenotype
    // interval. Synchronize to the public clock; do not advance one interval
    // into the future.
    const double window_end = PhysiCell::PhysiCell_globals.current_time * 60.0;
    WindowResult result = engine_ptr->advance(*state, window_end);
    cell->custom_data["pn_active"] = state->active ? 1.0 : 0.0;
    cell->custom_data["intracellular_bacteria"] = result.intracellular_bacteria;
    cell->custom_data["sal_ruffle_tokens"] = result.sal_ruffle_tokens;
    cell->custom_data["uptaken_bacteria"] = result.uptaken_bacteria;
    cell->custom_data["ap_gal8_tokens"] = engine_ptr->gal8_autophagosome_tokens(state->marking);
    cell->custom_data["ap_ub_tokens"] = engine_ptr->ub_autophagosome_tokens(state->marking);
    cell->custom_data["xenophagy_activity"] = result.xenophagy_activity;
    cell->custom_data["surface_pMHC"] = state->mhc.P;
    cell->custom_data["surface_pMHC_I"] = state->mhc1.P;
    cell->custom_data["surface_pMHC_II"] = state->mhc.P;
    const double cd4_recognition = mhcii_cd4_recognition(
        state->mhc.P, parameters().mhcii_cd4_half_max,
        parameters().mhcii_cd4_hill);
    cell->custom_data["mhcii_cd4_recognition"] = cd4_recognition;
    set_cd4_immunogenicity(cell, cd4_recognition);
    cell->custom_data["pn_death_probability"] = result.death_probability;
    const double draw = std::generate_canonical<double, 53>(state->rng);
    if (draw < result.death_probability) {
        const int apoptosis = phenotype.death.find_death_model_index(
            PhysiCell::PhysiCell_constants::apoptosis_death_model);
        if (apoptosis >= 0) {
            state->petrinet_death_triggered = true;
            state->death_time_minutes = PhysiCell::PhysiCell_globals.current_time;
            cell->start_death(apoptosis);
        }
    }
}

void petrinet_division(PhysiCell::Cell* parent, PhysiCell::Cell* child) {
    if (!integration_enabled) return;
    CellPetriNetState* parent_state = state_for(parent, false);
    if (!parent_state) return;
    CellPetriNetState* child_state = state_for(child, true);
    engine_ptr->split(*parent_state, *child_state, parameters().division_daughter_fraction,
                 mix_seed(global_seed ^ static_cast<std::uint64_t>(child->ID)));
    parent->custom_data["pn_active"] = parent_state->active ? 1.0 : 0.0;
    child->custom_data["pn_active"] = child_state->active ? 1.0 : 0.0;
}

void cleanup_petrinet_states() {
    if (!integration_enabled) return;
    std::unordered_set<unsigned int> alive;
    for (PhysiCell::Cell* cell : *PhysiCell::all_cells) alive.insert(cell->ID);
    std::lock_guard<std::mutex> guard(pool_mutex);
    for (auto it = slots_by_cell.begin(); it != slots_by_cell.end();) {
        if (alive.count(it->first)) { ++it; continue; }
        state_pool[it->second].reset();
        free_slots.push_back(it->second);
        it = slots_by_cell.erase(it);
    }
}

} // namespace xenophagy
