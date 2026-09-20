// Fast smoke check for the aligned PetriNet engine.
//
// Purpose: confirm the engine produces finite, monotone-plausible MHC output
// over a short horizon without running the full 8-hour parity sweep. The
// window is 30 minutes and the internal RK4 step is 0.02 h, so this is ~25
// integration steps instead of ~400 -- seconds, not minutes.
//
// Usage: petrinet_quick_sim [minutes] [seed]
#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>

using namespace xenophagy;

int main(int argc, char** argv) {
    const double minutes = argc > 1 ? std::atof(argv[1]) : 30.0;
    const int seed = argc > 2 ? std::atoi(argv[2]) : 42;
    if (minutes <= 0.0) return 2;

    PetriNetEngine engine;

    const int ix_sal_vac = engine.place_index("SalVac");
    const int ix_sal_cyt = engine.place_index("SalCyt");
    const int ix_xenosig = engine.place_index("XenoSig");
    if (ix_sal_vac < 0 || ix_sal_cyt < 0 || ix_xenosig < 0) {
        std::cerr << "quick_sim: required places missing from model\n";
        return 1;
    }

    CellPetriNetState state(static_cast<std::uint64_t>(seed));
    state.marking = engine.model().initial_marking();
    // Start with a small intracellular cohort so the xenophagy chain has
    // something to act on immediately, like an infected target cell would.
    state.marking[ix_sal_vac] = 50;
    engine.enqueue(state, EntryEvent(0.0, 1, 0, 0));
    state.active = true;

    std::cout << "t_min,reactions,burden,xenosig,sal_cyt,sal_vac,"
                 "xeno_activity,pmhc_i,pmhc_ii\n";

    const double step_minutes = minutes / 10.0;
    for (int i = 1; i <= 10; ++i) {
        const double t = step_minutes * i;
        const WindowResult r = engine.advance(state, t * 60.0);
        std::cout << std::fixed << std::setprecision(2) << t << ','
                  << r.reactions_fired << ','
                  << r.intracellular_bacteria << ','
                  << state.marking[ix_xenosig] << ','
                  << state.marking[ix_sal_cyt] << ','
                  << state.marking[ix_sal_vac] << ','
                  << std::setprecision(4) << r.xenophagy_activity << ','
                  << state.mhc1.P << ',' << state.mhc.P << '\n';
    }
    return 0;
}
