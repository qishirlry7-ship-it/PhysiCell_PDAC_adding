#pragma once

#include "runtime/include/petrinet/expression.h"
#include "runtime/include/petrinet/model.h"

#include <array>
#include <cstdint>
#include <deque>
#include <map>
#include <random>
#include <string>
#include <vector>

namespace xenophagy {

using Marking = std::vector<int>;

struct ModelParameters {
    double k_death = 1e-7;
    double death_threshold = 100.0;
    double cap_cyt_initial = 700.0;
    double cap_vac_initial = 150.0;
    double sigmoid_k = 5e-5;
    double sigmoid_mid_base = 1800.0;
    double sigmoid_mid_slope = 200.0;
    double mhc_alpha = 1.0;
    double mhc_beta = 1.0;
    double xeno_signal_mode = 0.0;
    double division_daughter_fraction = 1.0;
    double mhc_d_X = 0.2;
    double mhc_d_M = 0.07;
    double mhc_k_T = 1.0;
    double mhc_d_C = 0.03;
    double mhc_d_P = 0.069;
    double mhc_k_load = 1e-4;
    // Constant MHC synthesis rates (molecules/h). IFN-gamma modulation was
    // removed -- see the note in petrinet_engine.cpp. Values equal the old
    // double-counted saturation expression S_M_base + V_M_IFN*I/(K_M_IFN+I)
    // where S_M_base was already the resolved saturated rate, so presentation
    // levels are preserved exactly.
    double mhc_S_M_base = 7472.0;
    // IFN-gamma-induced MHC-II synthesis, restored. See the field comment in
    // MHCParameters for the units decision. V_M_ifn = 4000 against
    // S_M_base = 7472 gives a maximal induction of about 1.53x on the CURRENT
    // (resolved) baseline -- note the baseline itself was set to the fully
    // induced value when the IFN-gamma term was removed, so this is a modest
    // additional range rather than the original 20x. Set V_M_ifn = 0 to
    // restore exactly the previous constant-synthesis behaviour.
    double mhc2_V_M_ifn = 4000.0;
    double mhc2_K_M_ifn = 0.5;
    double mhc_r_pep = 5.0;
    double mhc_max_step_seconds = 60.0;
    double mhc_X0 = 0.0;
    double mhc_M0 = 10000.0;
    double mhc_C0 = 0.0;
    double mhc_P0 = 0.0;
    // MHC-I branch: cross-presentation of xenophagy-derived antigen onto MHC-I.
    // The rate set is much faster than MHC-II and does not share its parameters.
    bool mhc1_enable = true;
    double mhc1_cross_frac = 0.05;
    double mhc1_d_X = 14.4;
    double mhc1_d_M = 1.663;
    double mhc1_k_T = 28.8;
    double mhc1_d_C = 0.1663;
    double mhc1_d_P = 0.0433;
    double mhc1_k_load = 0.018144;
    // MHC-I synthesis: the old code passed mhc1_S_M_base (=200) into the
    // saturating expression, so the resolved constant is 200 + V*I/(K+I) with
    // I = mhc1_ifn_gamma = 150, i.e. 4187 -- not a double-counted value.
    double mhc1_S_M = 4187.0;
    double mhc1_M0 = 10000.0;
    double mhc1_r_pep = 1.0;
    double mhc2_d_P_mature = 0.007;
    double bacterial_uptake_rate = 0.02;
    double bacterial_uptake_interval = 1.0;
    double bacterial_uptake_distance = 20.0;
    double mhcii_cd4_attack_max = 0.15;
    // Half-saturation for the MHC-II -> CD4 recognition Hill function.
    // RECALIBRATED 30 -> 5000. At 30 this was saturated for every infected
    // cell: measured surface_pMHC_II is 1550..59460 (p50 = 39120), roughly
    // 1300x the old half-max, so mhcii_cd4_recognition sat at 0.98..0.9995 and
    // carried no information beyond "is this cell infected". 5000 puts 94.5%
    // of infected cells inside the 0.05..0.95 discriminating band.
    // The asymmetry with MHC-I is real: mhci_cd8_half_max = 24 sits sensibly
    // against a measured surface_pMHC_I of 64..131, so ONLY the MHC-II branch
    // was mis-scaled.
    double mhcii_cd4_half_max = 5000.0;
    double mhcii_cd4_hill = 1.0;
};

const ModelParameters& parameters();

struct EntryEvent {
    double time_seconds = 0.0;
    int to_ruffle = 0;
    int to_cytosol = 0;
    int to_vacuole = 0;

    EntryEvent() = default;
    EntryEvent(double time, int cytosol, int vacuole)
        : time_seconds(time), to_cytosol(cytosol), to_vacuole(vacuole) {}
    EntryEvent(double time, int ruffle, int cytosol, int vacuole)
        : time_seconds(time), to_ruffle(ruffle), to_cytosol(cytosol),
          to_vacuole(vacuole) {}
};

struct MHCState {
    double X = 0.0;
    double M = 10000.0;
    double C = 0.0;
    double P = 0.0;
};

struct MHCParameters {
    // Two independent presentation branches. MHC-I uses its own (much faster)
    // rate set; MHC-II is the xenophagy/cross-presentation branch. Defaults are
    // aligned with the reference implementation in model2's
    // examples/xenophagy_population (population.h, struct MHCParams).
    bool mhc1_enable = true;
    double mhc1_cross_frac = 0.05;
    double alpha = 1.0;
    double beta = 1.0;

    double mhc1_d_X;
    double mhc1_d_M;
    double mhc1_k_T;
    double mhc1_d_C;
    double mhc1_d_P;
    double mhc1_k_load;
    double mhc1_S_M;
    double mhc1_M0;
    double mhc1_r_pep;

    double d_X;
    double d_M;
    double k_T;
    double d_C;
    double d_P;
    // MHC-II surface decay depends on maturation state; the immature (default)
    // rate keeps pMHC-II short-lived, the mature rate stabilises it.
    double mhc2_d_P_immature;
    double k_load;
    double S_M;
    double r_pep;
    // IFN-gamma-induced MHC-II synthesis. Restored from the reference model:
    //   S_M_eff(c) = S_M + V_M_ifn * c / (K_M_ifn + c)
    // c is the cell's LOCAL, DIMENSIONLESS PhysiCell IFN_gamma field value --
    // no unit conversion is attempted. K_M_ifn is therefore on that same
    // field scale; the measured field peaks near 0.4-0.46 and the original
    // K was 0.5, so the pre-existing value is reused rather than re-invented.
    // V_M_ifn = 4000 with S_M_base = 200 reproduces the original 20x maximal
    // induction. Set V_M_ifn <= 0 to restore constant synthesis exactly.
    double mhc2_V_M_ifn = 0.0;
    double mhc2_K_M_ifn = 0.5;

    explicit MHCParameters(bool mhc2_mature = false,
                           const ModelParameters& p = parameters());
};

struct CellPetriNetState {
    Marking marking{};
    double internal_time_seconds = 0.0;
    std::uint64_t cell_seed = 0;
    std::uint64_t update_index = 0;
    bool active = false;
    bool petrinet_death_triggered = false;
    double death_time_minutes = -1.0;
    MHCState mhc;
    MHCState mhc1;
    std::deque<EntryEvent> entries;
    std::mt19937_64 rng;

    explicit CellPetriNetState(std::uint64_t seed = 0);
};

struct WindowResult {
    double integrated_death_hazard = 0.0;
    double death_probability = 0.0;
    double antigen_flux = 0.0;
    int deg_count = 0;
    double xenophagy_activity = 0.0;
    double peak_xenophagy_activity = 0.0;
    double peak_surface_pMHC = 0.0;
    double peak_surface_pMHC_I = 0.0;
    double peak_surface_pMHC_II = 0.0;
    int intracellular_bacteria = 0;
    int sal_ruffle_tokens = 0;
    int uptaken_bacteria = 0;
    std::uint64_t reactions_fired = 0;
    // True when the SSA loop hit EngineConfig::max_events before reaching the
    // requested window end, so the caller knows the window was truncated.
    bool reactions_capped = false;
};

struct EngineConfig {
    enum class XenoSignalMode {
        PythonPostReactionBernoulli,
        ContinuousCompetingHazard
    };

    std::string model_json = "config/petrinet/xenophagy_model.json";
    ModelParameters model = parameters();
    bool mhc2_mature = false;
    MHCParameters mhc = MHCParameters(mhc2_mature, model);
    XenoSignalMode xeno_signal_mode = parameters().xeno_signal_mode == 0.0
        ? XenoSignalMode::PythonPostReactionBernoulli
        : XenoSignalMode::ContinuousCompetingHazard;

    // Parameter overrides applied to the loaded model at construction time.
    // The JSON topology carries the network structure; the PHYSICELL XML (or a
    // caller-provided table) carries the calibrated rates. Without this the
    // XML would be dead configuration, which is exactly the bug this fixes.
    std::map<std::string, std::string> override_expression;
    std::map<std::string, int> initial_marking;
    int cap_cyt = -1;  // <0 keeps the model's own value
    int cap_vac = -1;

    // Michaelis-Menten synthesis. Transitions flagged "deterministic" in the
    // JSON are saturable synthesis/degradation steps: their rate law is
    //     k * baseline / (baseline + substrate_tokens)
    // with `substrate` the place named here per transition id. Reactions with
    // no substrate entry fall back to their own JSON rate (mass action).
    std::map<std::string, std::string> syn_mm;
    double syn_baseline = 200.0;

    // Hard cap on SSA reactions per advance() call. With a large initial
    // marking the total propensity can reach O(1000)/s, which would otherwise
    // make a multi-hour window spin for millions of iterations. The cap keeps
    // per-callback cost bounded and is reported via reactions_capped.
    int max_events = 100000;
};

class PetriNetEngine {
public:
    explicit PetriNetEngine(const EngineConfig& config = EngineConfig());

    void enqueue(CellPetriNetState& state, const EntryEvent& event) const;
    WindowResult advance(CellPetriNetState& state, double window_end_seconds,
                         double local_ifn_gamma = -1.0) const;
    void split(CellPetriNetState& parent, CellPetriNetState& child,
               double daughter_fraction, std::uint64_t child_seed) const;

    double propensity(std::size_t transition_index, const Marking& marking) const;
    int bacterial_burden(const Marking& marking) const;    int uptaken_bacterial_burden(const Marking& marking) const;
    int sal_ruffle_tokens(const Marking& marking) const;
    int gal8_autophagosome_tokens(const Marking& marking) const;
    int ub_autophagosome_tokens(const Marking& marking) const;
    double xenophagy_activity(const Marking& marking) const;

    // The model is loaded from JSON at run time, so place and transition
    // indices are not compile-time constants. These accessors let callers
    // (tests, benchmarks, diagnostics) resolve them by name instead of
    // hard-coding enum values that no longer exist.
    const petrinet::Model& model() const { return model_; }
    std::size_t place_count() const { return model_.places.size(); }
    std::size_t transition_count() const { return model_.transitions.size(); }
    int place_index(const std::string& id) const;
    int transition_index(const std::string& id) const;
    int token(const Marking& marking, const std::string& place_id) const;
    int token(const Marking& marking, int index) const;

private:
    EngineConfig config_;
    petrinet::Model model_;
    std::vector<petrinet::Expression> expressions_;
    // Lazy transition table: only transitions the model can actually fire are
    // visited each SSA step. Every other transition has zero propensity by
    // construction, so scanning it is pure overhead.
    std::vector<std::size_t> active_transitions_;
    std::vector<petrinet::Expression> active_expressions_;
    int ix_sal_ruffle_ = -1;
    int ix_sal_vac_ = -1;
    int ix_sal_cyt_ = -1;
    int ix_adap_sal_cyt_ = -1;
    int ix_adap_sal_vac_ = -1;
    int ix_cap_cyt_ = -1;
    int ix_cap_vac_ = -1;
    int ix_xenosig_ = -1;
    std::array<int, 4> bacterial_places_{{-1, -1, -1, -1}};
    std::array<int, 4> gal8_ap_places_{{-1, -1, -1, -1}};
    std::array<int, 3> ub_ap_places_{{-1, -1, -1}};

    double sigmoid_propensity(const CellPetriNetState& state) const;
    double active_propensity(std::size_t active_i, const Marking& marking) const;
    void fire(std::size_t transition_index, Marking& marking) const;
    void apply_entry(CellPetriNetState& state, const EntryEvent& event) const;
    void integrate_interval(CellPetriNetState& state, double dt_seconds,
                            WindowResult& result) const;
    void integrate_mhc_window(CellPetriNetState& state, int deg_count,
                              double dt_seconds, WindowResult& result,
                              double local_ifn_gamma = -1.0) const;
    void rebuild_capacity(Marking& marking) const;
    // Applies config_.override_expression / initial_marking / capacities to the
    // freshly loaded model, then rebuilds the active transition table.
    void apply_overrides();
    // Rewrites deterministic transitions that have a configured substrate into
    // their saturable Michaelis-Menten rate law.
    void apply_saturating_rates();
    void rebuild_active_transitions();
};

} // namespace xenophagy
