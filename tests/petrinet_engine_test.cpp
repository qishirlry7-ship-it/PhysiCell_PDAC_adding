#include "../custom_modules/petrinet/petrinet_engine.h"
#include "../custom_modules/petrinet/mhcii_cd4_coupling.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>

using namespace xenophagy;

namespace {

// The model is loaded from JSON at run time, so places and transitions are
// resolved by name rather than through compile-time enum constants.
int place(const PetriNetEngine& engine, const std::string& id) {
    const int ix = engine.place_index(id);
    assert(ix >= 0 && "unknown place id");
    return ix;
}

std::size_t transition(const PetriNetEngine& engine, const std::string& id) {
    const int ix = engine.transition_index(id);
    assert(ix >= 0 && "unknown transition id");
    return static_cast<std::size_t>(ix);
}

} // namespace

int main() {
    assert(mhcii_cd4_recognition(0.0, 30.0, 1.0) == 0.0);
    assert(std::fabs(mhcii_cd4_recognition(30.0, 30.0, 1.0) - 0.5) < 1e-12);
    assert(std::fabs(mhcii_cd4_recognition(90.0, 30.0, 1.0) - 0.75) < 1e-12);
    assert(mhcii_cd4_recognition(1e300, 30.0, 2.0) == 1.0);

    PetriNetEngine engine;

    const int ix_sal_ruffle = place(engine, "SalRuffle");
    const int ix_sal_cyt = place(engine, "SalCyt");
    const int ix_sal_vac = place(engine, "SalVac");
    const int ix_cap_cyt = place(engine, "CapCyt");
    const int ix_cap_vac = place(engine, "CapVac");
    const int ix_adap_sal_cyt = place(engine, "AdapSalCyt");
    const int ix_adap_sal_vac = place(engine, "AdapSalVac");

    CellPetriNetState state(42);
    // A freshly constructed state has an empty marking -- the engine seeds it
    // from the loaded model on first use (see apply_entry / advance). Seed it
    // explicitly here so pre-advance indexing is valid.
    state.marking = engine.model().initial_marking();
    // SalRuffle is seeded with 100 tokens by the JSON topology, so counts are
    // relative to that baseline rather than to zero.
    const int sal_ruffle_baseline = state.marking[ix_sal_ruffle];
    assert(state.marking[ix_cap_cyt] == 700);
    engine.enqueue(state, EntryEvent{10.0, 120, 30});
    engine.enqueue(state, EntryEvent{10.0, 1, 2});
    WindowResult result = engine.advance(state, 10.0);
    assert(state.active);
    assert(state.marking[ix_sal_cyt] == 121);
    assert(state.marking[ix_sal_vac] == 32);
    assert(result.intracellular_bacteria == 153);
    assert(engine.gal8_autophagosome_tokens(state.marking) == 0);
    assert(engine.ub_autophagosome_tokens(state.marking) == 0);

    // Agent uptake is one-to-one at SalRuffle. Compartment choice remains an
    // enabled SSA competition with the rates from the upstream JSON.
    CellPetriNetState uptake(7);
    uptake.marking = engine.model().initial_marking();
    const int uptake_baseline = uptake.marking[ix_sal_ruffle];
    engine.enqueue(uptake, EntryEvent{0.0, 1, 0, 0});
    engine.enqueue(uptake, EntryEvent{0.0, 1, 0, 0});
    WindowResult uptake_result = engine.advance(uptake, 0.0);
    assert(uptake.marking[ix_sal_ruffle] == uptake_baseline + 2);
    assert(uptake_result.sal_ruffle_tokens == uptake_baseline + 2);
    assert(uptake_result.intracellular_bacteria == 0);
    assert(uptake_result.uptaken_bacteria == uptake_baseline + 2);

    const std::size_t staying = transition(engine, "StayingVac");
    const std::size_t entering = transition(engine, "EnteringCyt");
    assert(engine.model().transitions[staying].enabled);
    assert(engine.model().transitions[entering].enabled);
    // Mass-action propensity is rate * combination(tokens, input weight). The
    // two transitions compete for the same SalRuffle token pool, so assert the
    // ratio and the absolute value against the loaded rate rather than against
    // hard-coded numbers that assumed a zero baseline.
    const petrinet::Transition& t_stay = engine.model().transitions[staying];
    const petrinet::Transition& t_enter = engine.model().transitions[entering];
    const double expected_stay = t_stay.rate * uptake.marking[ix_sal_ruffle];
    const double expected_enter = t_enter.rate * uptake.marking[ix_sal_ruffle];
    assert(std::fabs(engine.propensity(staying, uptake.marking) - expected_stay) < 1e-12);
    assert(std::fabs(engine.propensity(entering, uptake.marking) - expected_enter) < 1e-12);
    assert(expected_stay > expected_enter && "StayingVac must out-compete EnteringCyt");

    // With no interval after entry, hazard is zero. Over the following second,
    // its exact integral is determined by the piecewise-constant SSA path.
    result = engine.advance(state, 11.0);
    assert(result.integrated_death_hazard >= 0.0);
    assert(result.death_probability >= 0.0 && result.death_probability <= 1.0);

    Marking before = state.marking;
    CellPetriNetState child(0);
    child.marking = engine.model().initial_marking();
    engine.split(state, child, 0.5, 99);
    for (std::size_t i = 0; i < engine.place_count(); ++i) {
        if (static_cast<int>(i) == ix_cap_cyt || static_cast<int>(i) == ix_cap_vac) continue;
        assert(state.marking[i] + child.marking[i] == before[i]);
    }
    assert(state.marking[ix_cap_cyt] ==
           std::max(0, 700 - state.marking[ix_sal_cyt] - state.marking[ix_adap_sal_cyt]));
    assert(child.marking[ix_cap_vac] ==
           std::max(0, 150 - child.marking[ix_sal_vac] - child.marking[ix_adap_sal_vac]));

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
