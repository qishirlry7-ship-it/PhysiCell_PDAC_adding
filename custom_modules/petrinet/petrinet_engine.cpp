#include "petrinet_engine.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace xenophagy {
namespace {

double choose_count(int count, int weight) {
    if (weight < 0 || count < weight) return 0.0;
    if (weight == 0) return 1.0;
    double value = 1.0;
    for (int i = 1; i <= weight; ++i) {
        value *= static_cast<double>(count - weight + i) / static_cast<double>(i);
    }
    return value;
}

double unit_open(std::mt19937_64& rng) {
    return (static_cast<double>(rng()) + 1.0) /
           (static_cast<double>(std::mt19937_64::max()) + 2.0);
}

int count_places(const Marking& m, const Place* places, std::size_t size) {
    int total = 0;
    for (std::size_t i = 0; i < size; ++i) total += m[places[i]];
    return total;
}

} // namespace

CellPetriNetState::CellPetriNetState(std::uint64_t seed)
    : marking(initial_marking()), cell_seed(seed), rng(seed) {}

PetriNetEngine::PetriNetEngine(const EngineConfig& config) : config_(config) {}

void PetriNetEngine::enqueue(CellPetriNetState& state, const EntryEvent& event) const {
    if (!std::isfinite(event.time_seconds) || event.time_seconds < state.internal_time_seconds)
        throw std::invalid_argument("entry time must be finite and not precede cell time");
    if (event.to_cytosol < 0 || event.to_vacuole < 0)
        throw std::invalid_argument("entry counts must be non-negative");
    if (event.to_cytosol == 0 && event.to_vacuole == 0) return;
    auto it = std::lower_bound(state.entries.begin(), state.entries.end(), event.time_seconds,
        [](const EntryEvent& lhs, double time) { return lhs.time_seconds < time; });
    if (it != state.entries.end() && std::fabs(it->time_seconds - event.time_seconds) < 1e-12) {
        it->to_cytosol += event.to_cytosol;
        it->to_vacuole += event.to_vacuole;
    } else {
        state.entries.insert(it, event);
    }
}

double PetriNetEngine::propensity(std::size_t i, const Marking& m) const {
    if (i >= transitions.size()) throw std::out_of_range("transition index");
    const Transition& transition = transitions[i];
    if (!transition.enabled) return 0.0;
    for (const Arc& arc : transition.input) {
        if (m[arc.place] < arc.weight) return 0.0;
    }
    double value = 0.0;
    if (transition.uses_expression) {
        value = expression_propensity(i, m);
    } else {
        value = transition.rate;
        for (const Arc& arc : transition.input) value *= choose_count(m[arc.place], arc.weight);
    }
    return std::isfinite(value) && value > 0.0 ? value : 0.0;
}

double PetriNetEngine::sigmoid_propensity(const CellPetriNetState& state) const {
    const double sc = static_cast<double>(state.marking[SalCyt] + state.marking[AdapSalCyt]);
    const double mid = config_.model.sigmoid_mid_base /
        (1.0 + config_.model.sigmoid_mid_slope * sc / config_.model.sigmoid_mid_base);
    const double z = config_.model.sigmoid_k * (state.internal_time_seconds - mid);
    if (z >= 40.0) return 1.0;
    if (z <= -40.0) return 0.0;
    return 1.0 / (1.0 + std::exp(-z));
}

void PetriNetEngine::fire(std::size_t i, Marking& m) const {
    for (const Arc& arc : transitions[i].input) m[arc.place] -= arc.weight;
    for (const Arc& arc : transitions[i].output) m[arc.place] += arc.weight;
}

void PetriNetEngine::apply_entry(CellPetriNetState& state, const EntryEvent& event) const {
    state.marking[SalCyt] += event.to_cytosol;
    state.marking[SalVac] += event.to_vacuole;
    state.active = true;
}

int PetriNetEngine::bacterial_burden(const Marking& m) const {
    static const Place bacterial[] = {SalCyt, AdapSalCyt, SalVac, AdapSalVac};
    return count_places(m, bacterial, sizeof(bacterial) / sizeof(bacterial[0]));
}

double PetriNetEngine::xenophagy_activity(const Marking& m) const {
    return config_.model.mhc_alpha * gal8_autophagosome_tokens(m) +
           config_.model.mhc_beta * ub_autophagosome_tokens(m);
}

int PetriNetEngine::gal8_autophagosome_tokens(const Marking& m) const {
    static const Place places[] = {Ap_Gal8, Ap_Gal8_Ub, Ap_Gal8_Ub_OPTNp, Ap_Gal8_Ub_N_S};
    return count_places(m, places, sizeof(places) / sizeof(places[0]));
}

int PetriNetEngine::ub_autophagosome_tokens(const Marking& m) const {
    static const Place places[] = {Ap_Ub, Ap_Ub_OPTNp, Ap_Ub_N_S};
    return count_places(m, places, sizeof(places) / sizeof(places[0]));
}

void PetriNetEngine::integrate_interval(CellPetriNetState& state, double dt_seconds,
                                        WindowResult& result) const {
    if (dt_seconds <= 0.0) return;
    const int burden = bacterial_burden(state.marking);
    const double death_rate = config_.model.k_death *
        std::max(0.0, static_cast<double>(burden) - config_.model.death_threshold);
    result.integrated_death_hazard += death_rate * dt_seconds;

    const double phi = xenophagy_activity(state.marking);
    result.peak_xenophagy_activity = std::max(result.peak_xenophagy_activity, phi);
    result.antigen_flux += phi * dt_seconds / 3600.0;
    const int steps = std::max(1, static_cast<int>(std::ceil(dt_seconds / 60.0)));
    const double dh = dt_seconds / 3600.0 / steps;
    for (int step = 0; step < steps; ++step) {
        const MHCState old = state.mhc;
        const double load = config_.mhc.k_load * old.X * old.M;
        state.mhc.X = std::max(0.0, old.X + dh * (phi - config_.mhc.d_X * old.X - load));
        state.mhc.M = std::max(0.0, old.M + dh * (config_.mhc.S_M - config_.mhc.d_M * old.M - load));
        state.mhc.C = std::max(0.0, old.C + dh * (load - (config_.mhc.k_T + config_.mhc.d_C) * old.C));
        state.mhc.P = std::max(0.0, old.P + dh * (config_.mhc.k_T * old.C - config_.mhc.d_P * old.P));
        result.peak_surface_pMHC = std::max(result.peak_surface_pMHC, state.mhc.P);
    }
}

WindowResult PetriNetEngine::advance(CellPetriNetState& state, double end) const {
    if (!std::isfinite(end) || end < state.internal_time_seconds)
        throw std::invalid_argument("window end must not precede cell time");
    WindowResult result;
    result.peak_xenophagy_activity = xenophagy_activity(state.marking);
    result.peak_surface_pMHC = state.mhc.P;
    while (state.internal_time_seconds < end) {
        while (!state.entries.empty() && state.entries.front().time_seconds <= state.internal_time_seconds + 1e-12) {
            apply_entry(state, state.entries.front());
            state.entries.pop_front();
        }
        if (!state.active) {
            const double next = state.entries.empty() ? end : std::min(end, state.entries.front().time_seconds);
            state.internal_time_seconds = next;
            continue;
        }
        std::vector<double> props(transitions.size(), 0.0);
        double ordinary_a0 = 0.0;
        for (std::size_t i = 0; i < transitions.size(); ++i) {
            props[i] = propensity(i, state.marking);
            ordinary_a0 += props[i];
        }
        const bool continuous_signal = config_.xeno_signal_mode ==
            EngineConfig::XenoSignalMode::ContinuousCompetingHazard;
        const double signal_a = continuous_signal ? sigmoid_propensity(state) : 0.0;
        const double a0 = ordinary_a0 + signal_a;
        const double reaction_dt = a0 > 0.0
            ? -std::log(unit_open(state.rng)) / a0
            : std::numeric_limits<double>::infinity();
        const double reaction_time = state.internal_time_seconds + reaction_dt;
        const double entry_time = state.entries.empty()
            ? std::numeric_limits<double>::infinity() : state.entries.front().time_seconds;
        const double next = std::min(end, std::min(reaction_time, entry_time));
        integrate_interval(state, next - state.internal_time_seconds, result);
        state.internal_time_seconds = next;
        if (next >= end - 1e-12) break;
        if (entry_time <= reaction_time) continue;

        double pick = unit_open(state.rng) * a0;
        bool fired = false;
        for (std::size_t i = 0; i < props.size(); ++i) {
            pick -= props[i];
            if (pick <= 0.0) {
                fire(i, state.marking);
                fired = true;
                break;
            }
        }
        if (!fired) {
            // Optional strict continuous-time formulation retained for future
            // mechanistic runs. It is not the Python reproduction mode.
            state.marking[XenoSig] += 1;
        } else if (!continuous_signal) {
            // agent_core.py performs this Bernoulli check once, immediately
            // after each ordinary SSA reaction, using that reaction's dt.
            const double probability = sigmoid_propensity(state) * reaction_dt;
            if (unit_open(state.rng) < probability) state.marking[XenoSig] += 1;
        }
        result.peak_xenophagy_activity = std::max(
            result.peak_xenophagy_activity, xenophagy_activity(state.marking));
        ++result.reactions_fired;
    }
    while (!state.entries.empty() && state.entries.front().time_seconds <= end + 1e-12) {
        apply_entry(state, state.entries.front());
        state.entries.pop_front();
    }
    ++state.update_index;
    result.intracellular_bacteria = bacterial_burden(state.marking);
    result.xenophagy_activity = xenophagy_activity(state.marking);
    result.death_probability = -std::expm1(-result.integrated_death_hazard);
    return result;
}

void PetriNetEngine::rebuild_capacity(Marking& m) const {
    m[CapCyt] = std::max(0, static_cast<int>(config_.model.cap_cyt_initial) - m[SalCyt] - m[AdapSalCyt]);
    m[CapVac] = std::max(0, static_cast<int>(config_.model.cap_vac_initial) - m[SalVac] - m[AdapSalVac]);
}

void PetriNetEngine::split(CellPetriNetState& parent, CellPetriNetState& child,
                           double fraction, std::uint64_t child_seed) const {
    if (!(fraction >= 0.0 && fraction <= 1.0)) throw std::invalid_argument("division fraction must be in [0,1]");
    child = CellPetriNetState(child_seed);
    child.marking.fill(0);
    child.internal_time_seconds = parent.internal_time_seconds;
    child.active = parent.active;
    child.petrinet_death_triggered = false;
    child.death_time_minutes = -1.0;
    for (std::size_t i = 0; i < PLACE_COUNT; ++i) {
        if (i == CapCyt || i == CapVac) continue;
        std::binomial_distribution<int> distribution(parent.marking[i], fraction);
        const int allocated = distribution(parent.rng);
        parent.marking[i] -= allocated;
        child.marking[i] = allocated;
    }
    child.mhc.X = parent.mhc.X * fraction; parent.mhc.X -= child.mhc.X;
    child.mhc.M = parent.mhc.M * fraction; parent.mhc.M -= child.mhc.M;
    child.mhc.C = parent.mhc.C * fraction; parent.mhc.C -= child.mhc.C;
    child.mhc.P = parent.mhc.P * fraction; parent.mhc.P -= child.mhc.P;
    rebuild_capacity(parent.marking);
    rebuild_capacity(child.marking);
}

} // namespace xenophagy
