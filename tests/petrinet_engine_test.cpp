#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace xenophagy;

int main() {
    PetriNetEngine engine;

    CellPetriNetState state(42);
    assert(state.marking[SalRuffle] == 0);
    assert(state.marking[CapCyt] == 700);
    engine.enqueue(state, EntryEvent{10.0, 120, 30});
    engine.enqueue(state, EntryEvent{10.0, 1, 2});
    WindowResult result = engine.advance(state, 10.0);
    assert(state.active);
    assert(state.marking[SalCyt] == 121);
    assert(state.marking[SalVac] == 32);
    assert(result.intracellular_bacteria == 153);
    assert(engine.gal8_autophagosome_tokens(state.marking) == 0);
    assert(engine.ub_autophagosome_tokens(state.marking) == 0);

    // Agent uptake is one-to-one at SalRuffle. Compartment choice remains an
    // enabled SSA competition with the rates from the upstream JSON.
    CellPetriNetState uptake(7);
    engine.enqueue(uptake, EntryEvent{0.0, 1, 0, 0});
    engine.enqueue(uptake, EntryEvent{0.0, 1, 0, 0});
    WindowResult uptake_result = engine.advance(uptake, 0.0);
    assert(uptake.marking[SalRuffle] == 2);
    assert(uptake_result.sal_ruffle_tokens == 2);
    assert(uptake_result.intracellular_bacteria == 0);
    assert(uptake_result.uptaken_bacteria == 2);
    std::size_t staying = transitions.size();
    std::size_t entering = transitions.size();
    for (std::size_t i = 0; i < transitions.size(); ++i) {
        if (std::string(transitions[i].id) == "StayingVac") staying = i;
        if (std::string(transitions[i].id) == "EnteringCyt") entering = i;
    }
    assert(staying < transitions.size() && entering < transitions.size());
    assert(transitions[staying].enabled && transitions[entering].enabled);
    assert(std::fabs(engine.propensity(staying, uptake.marking) - 0.012) < 1e-12);
    assert(std::fabs(engine.propensity(entering, uptake.marking) - 0.008) < 1e-12);

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
    rejected = false;
    try { engine.enqueue(uptake, EntryEvent{1.0, -1, 0, 0}); }
    catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected);

    std::cout << "petrinet_engine_test: ok\n";
    return 0;
}
