#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <omp.h>
#include <vector>

using namespace xenophagy;

int main(int argc, char** argv) {
    const int cells = argc > 1 ? std::atoi(argv[1]) : 100;
    const double hours = argc > 2 ? std::atof(argv[2]) : 1.0;
    const int threads = argc > 3 ? std::atoi(argv[3]) : 1;
    if (cells <= 0 || hours <= 0.0 || threads <= 0) return 2;

    omp_set_num_threads(threads);
    PetriNetEngine engine;
    const int ix_xenosig = engine.place_index("XenoSig");
    if (ix_xenosig < 0) {
        std::cerr << "benchmark: XenoSig missing from model\n";
        return 1;
    }

    std::vector<CellPetriNetState> states;
    states.reserve(cells);
    for (int i = 0; i < cells; ++i) {
        states.emplace_back(static_cast<std::uint64_t>(42 + i));
        states.back().marking = engine.model().initial_marking();
        engine.enqueue(states.back(), EntryEvent(0.0, 0, 50));
    }

    std::uint64_t reactions = 0;
    std::uint64_t checksum = 0;
    const double start = omp_get_wtime();
#pragma omp parallel for reduction(+:reactions,checksum) schedule(static)
    for (int i = 0; i < cells; ++i) {
        WindowResult result = engine.advance(states[i], hours * 3600.0);
        reactions += result.reactions_fired;
        checksum += static_cast<std::uint64_t>(
            result.intracellular_bacteria + states[i].marking[ix_xenosig]);
    }
    const double elapsed = omp_get_wtime() - start;

    std::cout << "cells,hours,threads,seconds,reactions,reactions_per_second,checksum\n"
              << cells << ',' << hours << ',' << threads << ','
              << std::setprecision(10) << elapsed << ',' << reactions << ','
              << (elapsed > 0.0 ? reactions / elapsed : 0.0) << ',' << checksum << '\n';
    return 0;
}
