// WT vs EXP xenophagy PetriNet comparison at the pure-engine level.
//
// Both models share identical topology and initial marking; EXP adds exactly
// two transitions (EXP1: S_damagedSCV+NDP52 -> S_Gal8_NDP52, rate 0.1;
// EXP2: S_damagedSCV+E3_ligase -> S_Gal8_Ub, rate 0.01). This driver runs the
// same initial condition through both and emits the MHC-I / MHC-II time series
// so the experimental branch's effect on antigen presentation is visible
// without any PhysiCell coupling.
//
// Usage: petrinet_wt_exp [hours] [samples] [moi]
#include "../custom_modules/petrinet/petrinet_engine.h"

#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>

using namespace xenophagy;

namespace {

struct RunResult {
    std::string label;
    std::vector<double> t_hours;
    std::vector<double> mhc1;
    std::vector<double> mhc2;
    std::vector<double> xenosig;
    std::vector<int> burden;
    std::uint64_t reactions = 0;
};

// Drive one model over the requested horizon, sampling MHC-I / MHC-II surface
// levels at a fixed cadence. The PetriNet engine integrates MHC internally per
// advance() window, so sampling finer than the window is the caller's job.
RunResult run_model(const std::string& label, const std::string& model_json,
                    double hours, int samples, int moi) {
    RunResult out;
    out.label = label;

    EngineConfig config;
    config.model_json = model_json;
    // Adding/Removing gate how much of the medium gun's 1500 bacteria actually
    // reach the cell. The raw JSON rates are 1.0/1.0, which is a 50/50 split;
    // scale them by MOI exactly as the reference runner does so the inoculum
    // is the stated value rather than an artefact of the default rates.
    config.override_expression["Adding"] = std::to_string(moi / 2.0);
    config.override_expression["Removing"] = std::to_string(1000.0 - moi / 2.0);

    // Saturating synthesis. Every "deterministic" transition needs its
    // substrate named so the engine can build k*baseline/(baseline+substrate).
    // Syn3 is absent from the topology (LRSAM1 was folded into E3_ligase), so
    // it is intentionally not listed.
    config.syn_mm = {
        {"Syn1", "Gal8"},
        {"Syn2", "E3_ligase"},
        {"Syn4", "p62"},
        {"Syn5", "NDP52"},
        {"Syn6", "OPTN"},
        {"Syn7", "N_S"},
        {"Syn8", "TBK1"},
        {"Syn9", "mTORC1_ULK1comp"},
        {"Syn10", "LC3"},
    };
    config.syn_baseline = 200.0;

    PetriNetEngine engine(config);

    const int ix_xenosig = engine.place_index("XenoSig");
    if (ix_xenosig < 0) {
        std::cerr << "wt_exp: XenoSig missing from " << model_json << "\n";
        std::exit(1);
    }

    CellPetriNetState state(42);
    state.marking = engine.model().initial_marking();
    state.active = true;

    const double dt_hours = hours / samples;
    out.t_hours.reserve(samples + 1);
    out.mhc1.reserve(samples + 1);
    out.mhc2.reserve(samples + 1);
    out.xenosig.reserve(samples + 1);
    out.burden.reserve(samples + 1);

    out.t_hours.push_back(0.0);
    out.mhc1.push_back(state.mhc1.P);
    out.mhc2.push_back(state.mhc.P);
    out.xenosig.push_back(0.0);
    out.burden.push_back(0);

    for (int i = 1; i <= samples; ++i) {
        const WindowResult r = engine.advance(state, i * dt_hours * 3600.0);
        out.reactions += r.reactions_fired;
        out.t_hours.push_back(i * dt_hours);
        out.mhc1.push_back(state.mhc1.P);
        out.mhc2.push_back(state.mhc.P);
        out.xenosig.push_back(static_cast<double>(state.marking[ix_xenosig]));
        out.burden.push_back(r.intracellular_bacteria);
    }
    return out;
}

void emit_long(const RunResult& r) {
    std::cout << "model,t_hours,mhc1_surface,pmhc2_surface,xenosig,intracellular\n";
    std::cout << std::fixed << std::setprecision(4);
    for (std::size_t i = 0; i < r.t_hours.size(); ++i) {
        std::cout << r.label << ',' << r.t_hours[i] << ',' << r.mhc1[i] << ','
                  << r.mhc2[i] << ',' << r.xenosig[i] << ',' << r.burden[i] << '\n';
    }
}

} // namespace

int main(int argc, char** argv) {
    const double hours = argc > 1 ? std::atof(argv[1]) : 48.0;
    const int samples = argc > 2 ? std::atoi(argv[2]) : 96;
    const int moi = argc > 3 ? std::atoi(argv[3]) : 150;
    if (hours <= 0.0 || samples <= 0 || moi <= 0) return 2;

    const RunResult wt = run_model("WT", "config/petrinet/wt_model.json",
                                   hours, samples, moi);
    const RunResult ex = run_model("EXP", "config/petrinet/exp_model.json",
                                   hours, samples, moi);

    emit_long(wt);
    emit_long(ex);

    std::cerr << "WT  reactions=" << wt.reactions
              << "  final mhc1=" << wt.mhc1.back() << " mhc2=" << wt.mhc2.back() << "\n";
    std::cerr << "EXP reactions=" << ex.reactions
              << "  final mhc1=" << ex.mhc1.back() << " mhc2=" << ex.mhc2.back() << "\n";
    return 0;
}
