#include "petrinet_engine.h"

#include "runtime/include/petrinet/ssa.h"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace xenophagy {
namespace {

ModelParameters default_parameters;

double unit_open(std::mt19937_64& rng) {
    return (static_cast<double>(rng()) + 1.0) /
           (static_cast<double>(std::mt19937_64::max()) + 2.0);
}

bool is_deg_transition(const std::string& id) {
    return id.compare(0, 3, "Deg") == 0;
}

// Expression text needs the baseline as a literal. Use enough precision that
// values like 200.0 and 1e-7 round-trip without scientific-notation surprises.
std::string format_number(double value) {
    std::ostringstream out;
    out << std::setprecision(17) << value;
    return out.str();
}

// Per-branch MHC rate set. MHC-I and MHC-II differ by orders of magnitude in
// their turnover rates, so they must not share a parameter block.
struct MhcBranch {
    double d_X;
    double d_M;
    double k_T;
    double d_C;
    double d_P;
    double k_load;
    // Constant MHC synthesis rate. IFN-gamma dependence was deliberately
    // removed: this model represents a uniformly high-IFN-gamma state, so the
    // saturating term V*I/(K+I) was a constant in practice and only added
    // three parameters plus an unresolved unit mismatch (the PhysiCell field
    // is dimensionless, the PetriNet parameter was annotated ng/mL).
    double S_M;
};

MHCState mhc_rhs(const MHCState& s, double phi, const MhcBranch& b) {
    MHCState ds;
    ds.X = phi - b.d_X * s.X;
    ds.M = b.S_M - b.d_M * s.M;
    ds.C = b.k_load * s.X * s.M - b.k_T * s.C - b.d_C * s.C;
    ds.P = b.k_T * s.C - b.d_P * s.P;
    return ds;
}

MHCState add_scaled(const MHCState& a, const MHCState& b, double scale) {
    MHCState out;
    out.X = a.X + scale * b.X;
    out.M = a.M + scale * b.M;
    out.C = a.C + scale * b.C;
    out.P = a.P + scale * b.P;
    return out;
}

// Classical RK4. The C equation couples X and M multiplicatively, so the
// system has no closed form and the integrator choice is part of the model.
void rk4_step(MHCState& s, double phi, const MhcBranch& b, double dt_h) {
    const MHCState k1 = mhc_rhs(s, phi, b);
    const MHCState k2 = mhc_rhs(add_scaled(s, k1, 0.5 * dt_h), phi, b);
    const MHCState k3 = mhc_rhs(add_scaled(s, k2, 0.5 * dt_h), phi, b);
    const MHCState k4 = mhc_rhs(add_scaled(s, k3, dt_h), phi, b);
    s.X += dt_h * (k1.X + 2.0 * k2.X + 2.0 * k3.X + k4.X) / 6.0;
    s.M += dt_h * (k1.M + 2.0 * k2.M + 2.0 * k3.M + k4.M) / 6.0;
    s.C += dt_h * (k1.C + 2.0 * k2.C + 2.0 * k3.C + k4.C) / 6.0;
    s.P += dt_h * (k1.P + 2.0 * k2.P + 2.0 * k3.P + k4.P) / 6.0;
    s.X = std::max(0.0, s.X);
    s.M = std::max(0.0, s.M);
    s.C = std::max(0.0, s.C);
    s.P = std::max(0.0, s.P);
}

} // namespace

const ModelParameters& parameters() {
    return default_parameters;
}

MHCParameters::MHCParameters(bool mhc2_mature, const ModelParameters& p)
    : mhc1_enable(p.mhc1_enable),
      mhc1_cross_frac(p.mhc1_cross_frac),
      alpha(p.mhc_alpha),
      beta(p.mhc_beta),
      mhc1_d_X(p.mhc1_d_X), mhc1_d_M(p.mhc1_d_M), mhc1_k_T(p.mhc1_k_T),
      mhc1_d_C(p.mhc1_d_C), mhc1_d_P(p.mhc1_d_P), mhc1_k_load(p.mhc1_k_load),
      mhc1_S_M(p.mhc1_S_M), mhc1_M0(p.mhc1_M0), mhc1_r_pep(p.mhc1_r_pep),
      d_X(p.mhc_d_X), d_M(p.mhc_d_M), k_T(p.mhc_k_T),
      d_C(p.mhc_d_C),
      d_P(mhc2_mature ? p.mhc2_d_P_mature : p.mhc_d_P),
      mhc2_d_P_immature(p.mhc_d_P),
      k_load(p.mhc_k_load),
      S_M(p.mhc_S_M_base),
      r_pep(p.mhc_r_pep) {}

CellPetriNetState::CellPetriNetState(std::uint64_t seed)
    : cell_seed(seed), rng(seed) {
    mhc.M = parameters().mhc_M0;
    mhc1.M = parameters().mhc1_M0;
}

PetriNetEngine::PetriNetEngine(const EngineConfig& config) : config_(config) {
    model_ = petrinet::load_json_model(config_.model_json);
    apply_overrides();
    expressions_.reserve(model_.transitions.size());
    for (const petrinet::Transition& t : model_.transitions) {
        expressions_.push_back(t.has_expression ? petrinet::Expression(t.expression, model_)
                                                : petrinet::Expression());
    }

    ix_sal_ruffle_ = place_index("SalRuffle");
    ix_sal_vac_ = place_index("SalVac");
    ix_sal_cyt_ = place_index("SalCyt");
    ix_adap_sal_cyt_ = place_index("AdapSalCyt");
    ix_adap_sal_vac_ = place_index("AdapSalVac");
    ix_cap_cyt_ = place_index("CapCyt");
    ix_cap_vac_ = place_index("CapVac");
    ix_xenosig_ = place_index("XenoSig");
    bacterial_places_ = {{ix_sal_cyt_, ix_adap_sal_cyt_, ix_sal_vac_, ix_adap_sal_vac_}};
    gal8_ap_places_ = {{
        place_index("Ap_Gal8"),
        place_index("Ap_Gal8_Ub"),
        place_index("Ap_Gal8_Ub_OPTNp"),
        place_index("Ap_Gal8_Ub_N_S")
    }};
    ub_ap_places_ = {{
        place_index("Ap_Ub"),
        place_index("Ap_Ub_OPTNp"),
        place_index("Ap_Ub_N_S")
    }};
    apply_saturating_rates();
    rebuild_active_transitions();
}

void PetriNetEngine::apply_overrides() {
    for (petrinet::Transition& t : model_.transitions) {
        auto oit = config_.override_expression.find(t.id);
        if (oit == config_.override_expression.end()) continue;
        // Validate the expression against the model before committing it, so a
        // typo in the XML fails loudly at construction rather than silently
        // producing a zero-propensity dead transition.
        try {
            petrinet::Expression probe(oit->second, model_);
            (void)probe;
        } catch (const std::exception& e) {
            throw std::runtime_error("invalid override for transition '" + t.id +
                                     "': " + e.what());
        }
        t.has_expression = true;
        t.expression = oit->second;
        t.has_rate = false;
        t.rate = 0.0;
        t.enabled = true;
    }

    for (const auto& kv : config_.initial_marking) {
        auto it = model_.place_index.find(kv.first);
        if (it == model_.place_index.end()) continue;
        model_.places[static_cast<std::size_t>(it->second)].tokens = std::max(0, kv.second);
    }
}

void PetriNetEngine::apply_saturating_rates() {
    for (petrinet::Transition& t : model_.transitions) {
        if (!t.deterministic) continue;
        auto sit = config_.syn_mm.find(t.id);
        if (sit == config_.syn_mm.end()) continue;
        const std::string expr = "0.001 * " + format_number(config_.syn_baseline) +
            " / (" + format_number(config_.syn_baseline) + " + " + sit->second + ")";
        try {
            petrinet::Expression probe(expr, model_);
            (void)probe;
        } catch (const std::exception& e) {
            throw std::runtime_error("invalid saturating rate for '" + t.id +
                                     "': " + e.what());
        }
        t.has_expression = true;
        t.expression = expr;
        t.has_rate = false;
        t.rate = 0.0;
    }
}

void PetriNetEngine::rebuild_active_transitions() {
    active_transitions_.clear();
    active_expressions_.clear();
    for (std::size_t i = 0; i < model_.transitions.size(); ++i) {
        const petrinet::Transition& t = model_.transitions[i];
        // A transition is firable when it is enabled and carries a rate law.
        // The "deterministic" flag is a rate-law hint, never an off switch, so
        // it deliberately does not participate in this test.
        if (!t.enabled) continue;
        if (!t.has_rate && !t.has_expression) continue;
        active_transitions_.push_back(i);
        active_expressions_.push_back(
            t.has_expression ? petrinet::Expression(t.expression, model_)
                             : petrinet::Expression());
    }
}

int PetriNetEngine::place_index(const std::string& id) const {
    auto it = model_.place_index.find(id);
    return it == model_.place_index.end() ? -1 : it->second;
}

int PetriNetEngine::transition_index(const std::string& id) const {
    auto it = model_.transition_index.find(id);
    return it == model_.transition_index.end() ? -1 : it->second;
}

int PetriNetEngine::token(const Marking& marking, const std::string& place_id) const {
    return token(marking, place_index(place_id));
}

int PetriNetEngine::token(const Marking& marking, int index) const {
    return index < 0 ? 0 : marking[static_cast<std::size_t>(index)];
}

void PetriNetEngine::enqueue(CellPetriNetState& state, const EntryEvent& event) const {
    if (!std::isfinite(event.time_seconds) || event.time_seconds < state.internal_time_seconds)
        throw std::invalid_argument("entry time must be finite and not precede cell time");
    if (event.to_ruffle < 0 || event.to_cytosol < 0 || event.to_vacuole < 0)
        throw std::invalid_argument("entry counts must be non-negative");
    if (event.to_ruffle == 0 && event.to_cytosol == 0 && event.to_vacuole == 0) return;
    auto it = std::lower_bound(state.entries.begin(), state.entries.end(), event.time_seconds,
        [](const EntryEvent& lhs, double time) { return lhs.time_seconds < time; });
    if (it != state.entries.end() && std::fabs(it->time_seconds - event.time_seconds) < 1e-12) {
        it->to_ruffle += event.to_ruffle;
        it->to_cytosol += event.to_cytosol;
        it->to_vacuole += event.to_vacuole;
    } else {
        state.entries.insert(it, event);
    }
}

double PetriNetEngine::propensity(std::size_t i, const Marking& m) const {
    if (i >= model_.transitions.size()) throw std::out_of_range("transition index");
    const petrinet::Transition& transition = model_.transitions[i];
    if (!transition.enabled) return 0.0;
    for (const petrinet::Arc& arc : transition.input) {
        if (m[static_cast<std::size_t>(arc.place)] < arc.weight) return 0.0;
    }
    double value = 0.0;
    if (transition.has_expression) {
        value = expressions_[i].evaluate(m, model_.params);
    } else if (transition.has_rate) {
        value = transition.rate;
        for (const petrinet::Arc& arc : transition.input) {
            value *= petrinet::combination(m[static_cast<std::size_t>(arc.place)], arc.weight);
        }
    }
    return std::isfinite(value) && value > 0.0 ? value : 0.0;
}

double PetriNetEngine::active_propensity(std::size_t active_i, const Marking& m) const {
    const std::size_t ti = active_transitions_[active_i];
    const petrinet::Transition& transition = model_.transitions[ti];
    for (const petrinet::Arc& arc : transition.input) {
        if (m[static_cast<std::size_t>(arc.place)] < arc.weight) return 0.0;
    }
    double value = 0.0;
    if (transition.has_expression) {
        value = active_expressions_[active_i].evaluate(m, model_.params);
    } else if (transition.has_rate) {
        value = transition.rate;
        for (const petrinet::Arc& arc : transition.input) {
            value *= petrinet::combination(m[static_cast<std::size_t>(arc.place)], arc.weight);
        }
    }
    return std::isfinite(value) && value > 0.0 ? value : 0.0;
}

double PetriNetEngine::sigmoid_propensity(const CellPetriNetState& state) const {
    const double sc = static_cast<double>(
        token(state.marking, ix_sal_cyt_) + token(state.marking, ix_adap_sal_cyt_));
    const double mid = config_.model.sigmoid_mid_base /
        (1.0 + config_.model.sigmoid_mid_slope * sc / config_.model.sigmoid_mid_base);
    const double z = config_.model.sigmoid_k * (state.internal_time_seconds - mid);
    if (z >= 40.0) return 1.0;
    if (z <= -40.0) return 0.0;
    return 1.0 / (1.0 + std::exp(-z));
}

void PetriNetEngine::fire(std::size_t i, Marking& m) const {
    const petrinet::Transition& transition = model_.transitions[i];
    for (const petrinet::Arc& arc : transition.input) m[static_cast<std::size_t>(arc.place)] -= arc.weight;
    for (const petrinet::Arc& arc : transition.output) m[static_cast<std::size_t>(arc.place)] += arc.weight;
}

void PetriNetEngine::apply_entry(CellPetriNetState& state, const EntryEvent& event) const {
    if (state.marking.empty()) state.marking = model_.initial_marking();
    if (ix_sal_ruffle_ >= 0) state.marking[static_cast<std::size_t>(ix_sal_ruffle_)] += event.to_ruffle;
    if (ix_sal_cyt_ >= 0) state.marking[static_cast<std::size_t>(ix_sal_cyt_)] += event.to_cytosol;
    if (ix_sal_vac_ >= 0) state.marking[static_cast<std::size_t>(ix_sal_vac_)] += event.to_vacuole;
    state.active = true;
}

int PetriNetEngine::bacterial_burden(const Marking& m) const {
    int total = 0;
    for (int ix : bacterial_places_) total += token(m, ix);
    return total;
}

int PetriNetEngine::uptaken_bacterial_burden(const Marking& m) const {
    return token(m, ix_sal_ruffle_) + bacterial_burden(m);
}

int PetriNetEngine::sal_ruffle_tokens(const Marking& m) const {
    return token(m, ix_sal_ruffle_);
}

int PetriNetEngine::gal8_autophagosome_tokens(const Marking& m) const {
    int total = 0;
    for (int ix : gal8_ap_places_) total += token(m, ix);
    return total;
}

int PetriNetEngine::ub_autophagosome_tokens(const Marking& m) const {
    int total = 0;
    for (int ix : ub_ap_places_) total += token(m, ix);
    return total;
}

double PetriNetEngine::xenophagy_activity(const Marking& m) const {
    return config_.model.mhc_alpha * gal8_autophagosome_tokens(m) +
           config_.model.mhc_beta * ub_autophagosome_tokens(m);
}

void PetriNetEngine::integrate_interval(CellPetriNetState& state, double dt_seconds,
                                        WindowResult& result) const {
    if (dt_seconds <= 0.0) return;
    const int burden = bacterial_burden(state.marking);
    const double death_rate = config_.model.k_death *
        std::max(0.0, static_cast<double>(burden) - config_.model.death_threshold);
    result.integrated_death_hazard += death_rate * dt_seconds;
}

void PetriNetEngine::integrate_mhc_window(CellPetriNetState& state, int deg_count,
                                          double dt_seconds, WindowResult& result) const {
    if (dt_seconds <= 0.0) return;
    const double dt_hours = dt_seconds / 3600.0;
    const double phi_total = config_.mhc.r_pep * static_cast<double>(deg_count) / dt_hours;
    const double mhc1_cross_frac = config_.mhc.mhc1_enable
        ? std::max(0.0, std::min(1.0, config_.mhc.mhc1_cross_frac))
        : 0.0;
    const double phi_i = mhc1_cross_frac * config_.mhc.mhc1_r_pep * phi_total;
    const double phi_ii = (1.0 - mhc1_cross_frac) * config_.mhc.r_pep * phi_total;
    result.antigen_flux += phi_total * dt_hours;
    result.peak_xenophagy_activity = std::max(result.peak_xenophagy_activity, phi_total);

    const MhcBranch b1 = {
        config_.mhc.mhc1_d_X, config_.mhc.mhc1_d_M, config_.mhc.mhc1_k_T,
        config_.mhc.mhc1_d_C, config_.mhc.mhc1_d_P, config_.mhc.mhc1_k_load,
        config_.mhc.mhc1_S_M
    };
    const MhcBranch b2 = {
        config_.mhc.d_X, config_.mhc.d_M, config_.mhc.k_T,
        config_.mhc.d_C, config_.mhc.d_P, config_.mhc.k_load,
        config_.mhc.S_M
    };

    // Fixed internal step, independent of the caller's window length. RK4 is
    // stable at this size for both the fast MHC-I branch and the stiffer
    // MHC-II branch, whereas a single Euler step over the whole window is not.
    // The step count is computed as an integer: accumulating a floating-point
    // remainder leaves a ~1e-13 residue that keeps the loop alive for one extra
    // pass per call, which is pure waste when the caller invokes this every
    // diffusion step.
    const double internal_dt_h = 0.02;
    const int n_steps = std::max(1, static_cast<int>(std::ceil(dt_hours / internal_dt_h - 1e-9)));
    const double h = dt_hours / n_steps;
    for (int step = 0; step < n_steps; ++step) {
        if (config_.mhc.mhc1_enable) rk4_step(state.mhc1, phi_i, b1, h);
        rk4_step(state.mhc, phi_ii, b2, h);
        result.peak_surface_pMHC_I = std::max(result.peak_surface_pMHC_I, state.mhc1.P);
        result.peak_surface_pMHC_II = std::max(result.peak_surface_pMHC_II, state.mhc.P);
        result.peak_surface_pMHC = std::max(result.peak_surface_pMHC, state.mhc.P);
    }
}

WindowResult PetriNetEngine::advance(CellPetriNetState& state, double end) const {
    if (!std::isfinite(end) || end < state.internal_time_seconds)
        throw std::invalid_argument("window end must not precede cell time");
    if (state.marking.empty()) state.marking = model_.initial_marking();
    WindowResult result;
    const double window_start = state.internal_time_seconds;
    result.peak_xenophagy_activity = xenophagy_activity(state.marking);
    result.peak_surface_pMHC = state.mhc.P;
    result.peak_surface_pMHC_I = state.mhc1.P;
    result.peak_surface_pMHC_II = state.mhc.P;
    while (state.internal_time_seconds < end) {
        if (static_cast<int>(result.reactions_fired) >= config_.max_events) {
            result.reactions_capped = true;
            break;
        }
        while (!state.entries.empty() && state.entries.front().time_seconds <= state.internal_time_seconds + 1e-12) {
            apply_entry(state, state.entries.front());
            state.entries.pop_front();
        }
        if (!state.active) {
            const double next = state.entries.empty() ? end : std::min(end, state.entries.front().time_seconds);
            state.internal_time_seconds = next;
            continue;
        }
        std::vector<double> props(active_transitions_.size(), 0.0);
        double ordinary_a0 = 0.0;
        for (std::size_t i = 0; i < active_transitions_.size(); ++i) {
            props[i] = active_propensity(i, state.marking);
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
        std::size_t fired_active = active_transitions_.size();
        for (std::size_t i = 0; i < props.size(); ++i) {
            pick -= props[i];
            if (pick <= 0.0) {
                // Index into the lazy table, not the full transition list.
                const std::size_t real_index = active_transitions_[i];
                fire(real_index, state.marking);
                fired_active = i;
                fired = true;
                break;
            }
        }
        if (fired && is_deg_transition(
                model_.transitions[active_transitions_[fired_active]].id)) {
            ++result.deg_count;
        }
        if (!fired) {
            if (ix_xenosig_ >= 0) ++state.marking[static_cast<std::size_t>(ix_xenosig_)];
        } else if (!continuous_signal) {
            const double probability = sigmoid_propensity(state) * reaction_dt;
            if (unit_open(state.rng) < probability && ix_xenosig_ >= 0)
                ++state.marking[static_cast<std::size_t>(ix_xenosig_)];
        }
        result.peak_xenophagy_activity = std::max(
            result.peak_xenophagy_activity, xenophagy_activity(state.marking));
        ++result.reactions_fired;
    }
    integrate_mhc_window(state, result.deg_count, end - window_start, result);
    while (!state.entries.empty() && state.entries.front().time_seconds <= end + 1e-12) {
        apply_entry(state, state.entries.front());
        state.entries.pop_front();
    }
    ++state.update_index;
    result.intracellular_bacteria = bacterial_burden(state.marking);
    result.sal_ruffle_tokens = token(state.marking, ix_sal_ruffle_);
    result.uptaken_bacteria = uptaken_bacterial_burden(state.marking);
    result.xenophagy_activity = xenophagy_activity(state.marking);
    result.death_probability = -std::expm1(-result.integrated_death_hazard);
    return result;
}

void PetriNetEngine::rebuild_capacity(Marking& m) const {
    if (ix_cap_cyt_ >= 0)
        m[static_cast<std::size_t>(ix_cap_cyt_)] = std::max(0,
            static_cast<int>(config_.model.cap_cyt_initial) -
            token(m, ix_sal_cyt_) - token(m, ix_adap_sal_cyt_));
    if (ix_cap_vac_ >= 0)
        m[static_cast<std::size_t>(ix_cap_vac_)] = std::max(0,
            static_cast<int>(config_.model.cap_vac_initial) -
            token(m, ix_sal_vac_) - token(m, ix_adap_sal_vac_));
}

void PetriNetEngine::split(CellPetriNetState& parent, CellPetriNetState& child,
                           double fraction, std::uint64_t child_seed) const {
    if (!(fraction >= 0.0 && fraction <= 1.0)) throw std::invalid_argument("division fraction must be in [0,1]");
    child = parent;
    child.cell_seed = child_seed;
    child.rng.seed(child_seed);
    child.petrinet_death_triggered = false;
    child.death_time_minutes = -1.0;
    child.entries.clear();

    // Partition the mother's tokens between the daughters. Capacity places are
    // recomputed afterwards from the partitioned burden rather than split,
    // because capacity is a derived quantity, not a conserved pool.
    if (child.marking.size() != parent.marking.size())
        child.marking.assign(parent.marking.size(), 0);
    for (std::size_t i = 0; i < parent.marking.size(); ++i) {
        if (static_cast<int>(i) == ix_cap_cyt_ || static_cast<int>(i) == ix_cap_vac_) {
            child.marking[i] = 0;
            continue;
        }
        if (parent.marking[i] <= 0) {
            child.marking[i] = 0;
            continue;
        }
        std::binomial_distribution<int> distribution(parent.marking[i], fraction);
        const int allocated = distribution(parent.rng);
        parent.marking[i] -= allocated;
        child.marking[i] = allocated;
    }

    // MHC molecules are divided proportionally, keeping the total conserved.
    child.mhc.X = parent.mhc.X * fraction; parent.mhc.X -= child.mhc.X;
    child.mhc.M = parent.mhc.M * fraction; parent.mhc.M -= child.mhc.M;
    child.mhc.C = parent.mhc.C * fraction; parent.mhc.C -= child.mhc.C;
    child.mhc.P = parent.mhc.P * fraction; parent.mhc.P -= child.mhc.P;
    child.mhc1.X = parent.mhc1.X * fraction; parent.mhc1.X -= child.mhc1.X;
    child.mhc1.M = parent.mhc1.M * fraction; parent.mhc1.M -= child.mhc1.M;
    child.mhc1.C = parent.mhc1.C * fraction; parent.mhc1.C -= child.mhc1.C;
    child.mhc1.P = parent.mhc1.P * fraction; parent.mhc1.P -= child.mhc1.P;

    rebuild_capacity(parent.marking);
    rebuild_capacity(child.marking);
}

} // namespace xenophagy
