#pragma once

#include "../generated/xenophagy_model_generated.h"

#include <cstdint>
#include <deque>
#include <random>

namespace xenophagy {

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
    double X = parameters.mhc_X0;
    double M = parameters.mhc_M0;
    double C = parameters.mhc_C0;
    double P = parameters.mhc_P0;
};

struct MHCParameters {
    double d_X;
    double d_M;
    double k_T;
    double d_C;
    double d_P;
    double k_load;
    double S_M;
    double r_pep;

    explicit MHCParameters(const ModelParameters& p = parameters)
        : d_X(p.mhc_d_X), d_M(p.mhc_d_M), k_T(p.mhc_k_T),
          d_C(p.mhc_d_C), d_P(p.mhc_d_P), k_load(p.mhc_k_load),
          S_M(p.mhc_S_M_base + p.mhc_V_M_IFN * p.mhc_ifn_gamma /
              (p.mhc_K_M_IFN + p.mhc_ifn_gamma)), r_pep(p.mhc_r_pep) {}
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
    std::deque<EntryEvent> entries;
    std::mt19937_64 rng;

    explicit CellPetriNetState(std::uint64_t seed = 0);
};

struct WindowResult {
    double integrated_death_hazard = 0.0;
    double death_probability = 0.0;
    double antigen_flux = 0.0;
    double xenophagy_activity = 0.0;
    double peak_xenophagy_activity = 0.0;
    double peak_surface_pMHC = 0.0;
    int intracellular_bacteria = 0;
    int sal_ruffle_tokens = 0;
    int uptaken_bacteria = 0;
    std::uint64_t reactions_fired = 0;
};

struct EngineConfig {
    enum class XenoSignalMode {
        PythonPostReactionBernoulli,
        ContinuousCompetingHazard
    };

    ModelParameters model = parameters;
    MHCParameters mhc = MHCParameters(model);
    XenoSignalMode xeno_signal_mode = parameters.xeno_signal_mode == 0.0
        ? XenoSignalMode::PythonPostReactionBernoulli
        : XenoSignalMode::ContinuousCompetingHazard;
};

class PetriNetEngine {
public:
    explicit PetriNetEngine(const EngineConfig& config = EngineConfig());

    void enqueue(CellPetriNetState& state, const EntryEvent& event) const;
    WindowResult advance(CellPetriNetState& state, double window_end_seconds) const;
    void split(CellPetriNetState& parent, CellPetriNetState& child,
               double daughter_fraction, std::uint64_t child_seed) const;

    double propensity(std::size_t transition_index, const Marking& marking) const;
    int bacterial_burden(const Marking& marking) const;
    int uptaken_bacterial_burden(const Marking& marking) const;
    int gal8_autophagosome_tokens(const Marking& marking) const;
    int ub_autophagosome_tokens(const Marking& marking) const;
    double xenophagy_activity(const Marking& marking) const;

private:
    EngineConfig config_;

    double sigmoid_propensity(const CellPetriNetState& state) const;
    void fire(std::size_t transition_index, Marking& marking) const;
    void apply_entry(CellPetriNetState& state, const EntryEvent& event) const;
    void integrate_interval(CellPetriNetState& state, double dt_seconds,
                            WindowResult& result) const;
    void rebuild_capacity(Marking& marking) const;
};

} // namespace xenophagy
