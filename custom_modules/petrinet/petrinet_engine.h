#pragma once

#include "../generated/xenophagy_model_generated.h"

#include <cstdint>
#include <deque>
#include <random>

namespace xenophagy {

struct EntryEvent {
    double time_seconds = 0.0;
    int to_cytosol = 0;
    int to_vacuole = 0;

    EntryEvent() = default;
    EntryEvent(double time, int cytosol, int vacuole)
        : time_seconds(time), to_cytosol(cytosol), to_vacuole(vacuole) {}
};

struct MHCState {
    double X = 0.0;
    double M = 10000.0;
    double C = 0.0;
    double P = 0.0;
};

struct MHCParameters {
    double d_X = 0.2;
    double d_M = 0.07;
    double k_T = 1.0;
    double d_C = 0.03;
    double d_P = 0.069;
    double k_load = 0.0001;
    double S_M = 200.0 + 4000.0 * 5.0 / (0.5 + 5.0);
};

struct CellPetriNetState {
    Marking marking{};
    double internal_time_seconds = 0.0;
    std::uint64_t cell_seed = 0;
    std::uint64_t update_index = 0;
    bool active = false;
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
    std::uint64_t reactions_fired = 0;
};

struct EngineConfig {
    enum class XenoSignalMode {
        PythonPostReactionBernoulli,
        ContinuousCompetingHazard
    };

    ModelParameters model;
    MHCParameters mhc;
    XenoSignalMode xeno_signal_mode = XenoSignalMode::PythonPostReactionBernoulli;
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
