#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cstdlib>
#include <iostream>

using namespace xenophagy;

int main(int argc, char** argv) {
    const int samples = argc > 1 ? std::atoi(argv[1]) : 100;
    if (samples <= 0) return 2;

    std::cout << "seed,steps,burden_final,activity_peak,activity_final,"
                 "xenosig_final,pmhc_peak,pmhc_final\n";
    PetriNetEngine engine;
    for (int seed = 0; seed < samples; ++seed) {
        CellPetriNetState state(static_cast<std::uint64_t>(seed));
        state.marking[SalVac] = 50;
        state.active = true;
        const WindowResult result = engine.advance(state, 8.0 * 3600.0);
        std::cout << seed << ',' << result.reactions_fired << ','
                  << result.intracellular_bacteria << ','
                  << result.peak_xenophagy_activity << ','
                  << result.xenophagy_activity << ','
                  << state.marking[XenoSig] << ','
                  << result.peak_surface_pMHC << ',' << state.mhc.P << '\n';
    }
}
