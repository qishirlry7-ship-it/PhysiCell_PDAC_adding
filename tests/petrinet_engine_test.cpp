#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace xenophagy;

int main() {
    PetriNetEngine engine;

    CellPetriNetState state(42);
    assert(state.marking[SalRuffle] == 150);
    assert(state.marking[CapCyt] == 700);
    engine.enqueue(state, EntryEvent{10.0, 120, 30});
    engine.enqueue(state, EntryEvent{10.0, 1, 2});
    WindowResult result = engine.advance(state, 10.0);
    assert(state.active);
    assert(state.marking[SalCyt] == 121);
    assert(state.marking[SalVac] == 32);
    assert(result.intracellular_bacteria == 153);

    // With no interval after entry, hazard is zero. Over the following second,
    // its exact integral is determined by the piecewise-constant SSA path.
    result = engine.advance(state, 11.0);
    assert(result.integrated_death_hazard >= 0.0);
    assert(result.death_probability >= 0.0 && result.death_probability <= 1.0);

    Marking before = state.marking;
    CellPetriNetState child(0);
    engine.split(state, child, 0.5, 99);
    for (std::size_t i = 0; i < PLACE_COUNT; ++i) {
        if (i == CapCyt || i == CapVac) continue;
        assert(state.marking[i] + child.marking[i] == before[i]);
    }
    assert(state.marking[CapCyt] == std::max(0, 700 - state.marking[SalCyt] - state.marking[AdapSalCyt]));
    assert(child.marking[CapVac] == std::max(0, 150 - child.marking[SalVac] - child.marking[AdapSalVac]));

    bool rejected = false;
    try { engine.enqueue(state, EntryEvent{-1.0, 1, 0}); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);

    std::cout << "petrinet_engine_test: ok\n";
    return 0;
}
