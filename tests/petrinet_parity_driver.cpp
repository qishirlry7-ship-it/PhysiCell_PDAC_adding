#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cstdlib>
#include <iostream>
#include <string>

using namespace xenophagy;

int main(int argc, char** argv) {
    const int samples = argc > 1 ? std::atoi(argv[1]) : 100;
    if (samples <= 0) return 2;

    std::cout << "seed,steps,burden_final,activity_peak,activity_final,"
                 "xenosig_final,pmhc_peak,pmhc_final\n";

    PetriNetEngine engine;
    const int ix_sal_vac = engine.place_index("SalVac");
    const int ix_xenosig = engine.place_index("XenoSig");
    if (ix_sal_vac < 0 || ix_xenosig < 0) {
        std::cerr << "parity driver: required places missing from model\n";
        return 1;
    }

    for (int seed = 0; seed < samples; ++seed) {
        CellPetriNetState state(static_cast<std::uint64_t>(seed));
        // Seed from the model, then place the intracellular cohort by hand so
        // every sample starts from the same fixed condition.
        state.marking = engine.model().initial_marking();
        state.marking[ix_sal_vac] = 50;
        state.active = true;
        const WindowResult result = engine.advance(state, 8.0 * 3600.0);
        std::cout << seed << ',' << result.reactions_fired << ','
                  << result.intracellular_bacteria << ','
                  << result.peak_xenophagy_activity << ','
                  << result.xenophagy_activity << ','
                  << state.marking[ix_xenosig] << ','
                  << result.peak_surface_pMHC << ',' << state.mhc.P << '\n';
    }
    return 0;
}
