// Generated file. Do not edit.
// generator=1.0.0 model_sha256=beaafd39036a29aab6eb846082b6d4f2ceef830d7c2d83594d976bd681b5c305 integration_sha256=0f63f40a98aacf1b6aa376275a2670fd506bb0a3a5d07b20dbd11428eb7949f1
#include "xenophagy_model_generated.h"
#include <algorithm>
#include <cmath>
namespace xenophagy {
const ModelParameters parameters{};
const std::array<const char*, PLACE_COUNT> place_names = {{
  "SalRuffle",
  "SalVac",
  "SalCyt",
  "AdapSalCyt",
  "CapCyt",
  "AdapSalVac",
  "CapVac",
  "XenoSig",
  "AA",
  "AAstarvation",
  "Ap_Gal8",
  "Ap_Gal8_Ub",
  "Ap_Gal8_Ub_N_S",
  "Ap_Gal8_Ub_OPTNp",
  "Ap_Ub",
  "Ap_Ub_N_S",
  "Ap_Ub_OPTNp",
  "E3_ligase",
  "Gal8",
  "LC3_GABARAP",
  "N_S",
  "NDP52",
  "OPTN",
  "S_damagedSCV",
  "S_Gal8",
  "S_Gal8_NDP52",
  "S_Gal8_Ub",
  "S_Gal8_Ub_NDP52",
  "S_Gal8_Ub_NDP52_N_S",
  "S_Gal8_Ub_NDP52_OPTN_p62",
  "S_Gal8_Ub_NDP52_OPTN_p62_N_S",
  "S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1",
  "S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1i",
  "S_Gal8_Ub_NDP52_p62_OPTNp_N_S_OligoTBK1",
  "S_Gal8_Ub_OPTN",
  "S_Gal8_Ub_p62",
  "S_Ub",
  "S_Ub_NDP52",
  "S_Ub_NDP52_N_S",
  "S_Ub_NDP52_OPTN_p62",
  "S_Ub_NDP52_OPTN_p62_N_S",
  "S_Ub_NDP52_OPTN_p62_N_S_OligoTBK1",
  "S_Ub_NDP52_OPTN_p62_N_S_diTBK1",
  "S_Ub_NDP52_OPTN_p62_N_S_diTBK1i",
  "S_Ub_OPTN",
  "S_Ub_p62",
  "SignalAutophagyInduction",
  "SignalSCVdamage",
  "TBK1",
  "ULK1comp",
  "mTORC1_ULK1comp",
  "mTORC1_ULK1comp_SCV",
  "mTORC1inactive",
  "p62",
  "LC3_signal",
  "LC3",
  "XenoStart",
}};
const std::array<Transition, 80> transitions = {{
  {"StayingVac", 0.006, false, false, {{SalRuffle, 1}}, {{SalVac, 1}}},
  {"EnteringCyt", 0.004, false, false, {{SalRuffle, 1}}, {{SalCyt, 1}}},
  {"ProSalVac", 0.0001, true, true, {{AdapSalVac, 1}, {CapVac, 1}}, {{SalVac, 2}}},
  {"ProSalCyt", 0.0001, true, true, {{AdapSalCyt, 1}, {CapCyt, 1}}, {{SalCyt, 2}}},
  {"AdaptingCyt", 0.0167, false, true, {{SalCyt, 1}}, {{AdapSalCyt, 1}}},
  {"AdaptingVac", 0.036, false, true, {{SalVac, 1}}, {{AdapSalVac, 1}}},
  {"XenoDeg", 0.0001, true, true, {{SalCyt, 1}}, {{XenoSig, 1}, {SalCyt, 1}}},
  {"VacDamage", 0.018, false, true, {{SalVac, 1}}, {{SalCyt, 1}}},
  {"XenoDeg2", 0.0001, true, true, {{AdapSalCyt, 1}}, {{XenoSig, 1}, {AdapSalCyt, 1}}},
  {"Deg1", 0.001, false, true, {{Ap_Gal8, 1}}, {}},
  {"Deg2", 0.001, false, true, {{Ap_Gal8_Ub_OPTNp, 1}}, {}},
  {"Deg2i", 0.001, false, true, {{Ap_Gal8_Ub_N_S, 1}}, {}},
  {"Deg2ii", 0.001, false, true, {{Ap_Gal8_Ub, 1}}, {}},
  {"Deg3", 0.001, false, true, {{Ap_Ub_OPTNp, 1}}, {}},
  {"Deg3i", 0.001, false, true, {{Ap_Ub_N_S, 1}}, {}},
  {"Deg3ii", 0.001, false, true, {{Ap_Ub, 1}}, {}},
  {"Output", 0.001, false, true, {{mTORC1_ULK1comp_SCV, 1}}, {}},
  {"Syn1", 0.0005, true, true, {}, {{Gal8, 1}}},
  {"Syn2", 0.0005, true, true, {}, {{E3_ligase, 1}}},
  {"Syn4", 0.0005, true, true, {}, {{p62, 1}}},
  {"Syn5", 0.0005, true, true, {}, {{NDP52, 1}}},
  {"Syn6", 0.0005, true, true, {}, {{OPTN, 1}}},
  {"Syn7", 0.0005, true, true, {}, {{N_S, 1}}},
  {"Syn8", 0.0005, true, true, {}, {{TBK1, 1}}},
  {"Syn9", 0.0005, true, true, {}, {{mTORC1_ULK1comp, 1}}},
  {"T1", 0.01, false, true, {{Gal8, 1}, {S_damagedSCV, 1}}, {{S_Gal8, 1}}},
  {"T10", 0.01, false, true, {{N_S, 1}, {S_Gal8_Ub_NDP52, 1}}, {{S_Gal8_Ub_NDP52_N_S, 1}}},
  {"T10i", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62, 1}, {N_S, 1}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}}},
  {"T11", 0.01, false, true, {{S_Gal8_Ub_NDP52_N_S, 1}}, {{N_S, 1}, {S_Gal8_Ub, 1}}},
  {"T12", 0.01, false, true, {{N_S, 1}, {p62, 1}, {S_Gal8_Ub, 1}, {OPTN, 1}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}}},
  {"T13", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 2}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1, 1}}},
  {"T13i", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 2}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1i, 1}}},
  {"T14", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1, 1}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 1}}},
  {"T14i", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1i, 1}}, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 1}}},
  {"T15", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 2}}, {{S_Gal8_Ub_NDP52_p62_OPTNp_N_S_OligoTBK1, 1}}},
  {"T16", 0.01, false, true, {{LC3_GABARAP, 1}, {S_Gal8_Ub_NDP52_p62_OPTNp_N_S_OligoTBK1, 1}}, {{Ap_Gal8_Ub_OPTNp, 1}}},
  {"T16i", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62_N_S, 1}, {LC3_GABARAP, 1}}, {{Ap_Gal8_Ub_N_S, 1}}},
  {"T16ii", 0.01, false, true, {{S_Gal8_Ub_NDP52_OPTN_p62, 1}, {LC3_GABARAP, 1}}, {{Ap_Gal8_Ub, 1}}},
  {"T18", 0.01, false, true, {{E3_ligase, 1}, {S_damagedSCV, 1}}, {{S_Ub, 1}}},
  {"T19", 0.01, false, true, {{S_Ub, 1}, {p62, 1}}, {{S_Ub_p62, 1}}},
  {"T2", 0.01, false, true, {{E3_ligase, 1}, {S_Gal8, 1}}, {{S_Gal8_Ub, 1}}},
  {"T20", 0.01, false, true, {{S_Ub_p62, 1}}, {{S_Ub, 1}, {p62, 1}}},
  {"T21", 0.01, false, true, {{S_Ub, 1}, {OPTN, 1}}, {{S_Ub_OPTN, 1}}},
  {"T22", 0.01, false, true, {{S_Ub_OPTN, 1}}, {{S_Ub, 1}, {OPTN, 1}}},
  {"T23", 0.01, false, true, {{NDP52, 1}, {S_Ub, 1}}, {{S_Ub_NDP52, 1}}},
  {"T24", 0.01, false, true, {{S_Ub_NDP52, 1}}, {{NDP52, 1}, {S_Ub, 1}}},
  {"T25", 0.01, false, true, {{S_Ub, 1}, {OPTN, 1}, {p62, 1}, {NDP52, 1}}, {{S_Ub_NDP52_OPTN_p62, 1}}},
  {"T26", 0.01, false, true, {{N_S, 1}, {S_Ub_NDP52, 1}}, {{S_Ub_NDP52_N_S, 1}}},
  {"T26i", 0.01, false, true, {{N_S, 1}, {S_Ub_NDP52_OPTN_p62, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S, 1}}},
  {"T27", 0.01, false, true, {{S_Ub_NDP52_N_S, 1}}, {{N_S, 1}, {S_Ub, 1}}},
  {"T28", 0.01, false, true, {{N_S, 1}, {S_Ub, 1}, {OPTN, 1}, {p62, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S, 1}}},
  {"T29", 0.01, false, true, {{TBK1, 2}, {S_Ub_NDP52_OPTN_p62_N_S, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S_diTBK1, 1}}},
  {"T29_", 0.01, false, true, {{TBK1, 2}, {S_Ub_NDP52_OPTN_p62_N_S, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S_diTBK1i, 1}}},
  {"T2i", 0.01, false, true, {{S_Gal8_NDP52, 1}, {E3_ligase, 1}}, {{S_Gal8_Ub_NDP52, 1}}},
  {"T3", 0.01, false, true, {{NDP52, 1}, {S_Gal8_Ub, 1}}, {{S_Gal8_Ub_NDP52, 1}}},
  {"T3_release", 0.01, false, true, {{S_Gal8_Ub_NDP52, 1}}, {{S_Gal8_Ub, 1}, {NDP52, 1}}},
  {"T30", 0.01, false, true, {{S_Ub_NDP52_OPTN_p62_N_S_diTBK1, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 1}}},
  {"T30_", 0.01, false, true, {{S_Ub_NDP52_OPTN_p62_N_S_diTBK1i, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S, 1}, {TBK1, 1}}},
  {"T31", 0.01, false, true, {{TBK1, 2}, {S_Ub_NDP52_OPTN_p62_N_S, 1}}, {{S_Ub_NDP52_OPTN_p62_N_S_OligoTBK1, 1}}},
  {"T32", 0.01, false, true, {{LC3_GABARAP, 1}, {S_Ub_NDP52_OPTN_p62_N_S_OligoTBK1, 1}}, {{Ap_Ub_OPTNp, 1}}},
  {"T32i", 0.01, false, true, {{LC3_GABARAP, 1}, {S_Ub_NDP52_OPTN_p62_N_S, 1}}, {{Ap_Ub_N_S, 1}}},
  {"T32ii", 0.01, false, true, {{S_Ub_NDP52_OPTN_p62, 1}, {LC3_GABARAP, 1}}, {{Ap_Ub, 1}}},
  {"T33", 0.01, false, true, {{SignalSCVdamage, 1}, {AA, 1}}, {{AAstarvation, 1}}},
  {"T34", 0.01, false, true, {{AAstarvation, 1}, {mTORC1_ULK1comp, 1}}, {{mTORC1inactive, 1}, {ULK1comp, 1}}},
  {"T35", 0.01, false, true, {{mTORC1inactive, 1}, {ULK1comp, 1}}, {{AA, 1}, {mTORC1_ULK1comp, 1}, {mTORC1_ULK1comp_SCV, 1}}},
  {"T36", 0.01, false, true, {{ULK1comp, 1}}, {{SignalAutophagyInduction, 1}}},
  {"T37", 0.01, false, true, {{SignalAutophagyInduction, 1}}, {{ULK1comp, 1}, {LC3_signal, 1}}},
  {"T3i", 0.01, false, true, {{NDP52, 1}, {S_Gal8, 1}}, {{S_Gal8_NDP52, 1}}},
  {"T4", 0.01, false, true, {{S_Gal8_NDP52, 1}, {LC3_GABARAP, 1}}, {{Ap_Gal8, 1}}},
  {"T5", 0.01, false, true, {{OPTN, 1}, {S_Gal8_Ub, 1}}, {{S_Gal8_Ub_OPTN, 1}}},
  {"T6", 0.01, false, true, {{S_Gal8_Ub_OPTN, 1}}, {{S_Gal8_Ub, 1}, {OPTN, 1}}},
  {"T7", 0.01, false, true, {{S_Gal8_Ub, 1}, {p62, 1}}, {{S_Gal8_Ub_p62, 1}}},
  {"T8", 0.01, false, true, {{S_Gal8_Ub_p62, 1}}, {{S_Gal8_Ub, 1}, {p62, 1}}},
  {"T9", 0.01, false, true, {{p62, 1}, {S_Gal8_Ub, 1}, {NDP52, 1}, {OPTN, 1}}, {{S_Gal8_Ub_NDP52_OPTN_p62, 1}}},
  {"Bridge", 1.0, true, true, {{XenoStart, 1}, {XenoSig, 1}}, {{S_damagedSCV, 1}, {SignalSCVdamage, 1}}},
  {"Syn10", 1.0, true, true, {}, {{LC3, 1}}},
  {"T38", 0.01, false, true, {{LC3_signal, 1}, {LC3, 1}}, {{LC3_GABARAP, 1}}},
  {"XenoDeg3", 0.0001, true, true, {{SalCyt, 1}}, {{XenoStart, 1}}},
  {"XenoDeg4", 0.0001, true, true, {{AdapSalCyt, 1}}, {{XenoStart, 1}}},
  {"XenoFail", 1.0, true, true, {{XenoStart, 1}}, {{SalCyt, 1}}},
}};
Marking initial_marking() {
  Marking m{};
  m[SalRuffle] = 150;
  m[SalVac] = 0;
  m[SalCyt] = 0;
  m[AdapSalCyt] = 0;
  m[CapCyt] = 700;
  m[AdapSalVac] = 0;
  m[CapVac] = 150;
  m[XenoSig] = 0;
  m[AA] = 1;
  m[AAstarvation] = 0;
  m[Ap_Gal8] = 0;
  m[Ap_Gal8_Ub] = 0;
  m[Ap_Gal8_Ub_N_S] = 0;
  m[Ap_Gal8_Ub_OPTNp] = 0;
  m[Ap_Ub] = 0;
  m[Ap_Ub_N_S] = 0;
  m[Ap_Ub_OPTNp] = 0;
  m[E3_ligase] = 200;
  m[Gal8] = 200;
  m[LC3_GABARAP] = 200;
  m[N_S] = 200;
  m[NDP52] = 200;
  m[OPTN] = 200;
  m[S_damagedSCV] = 0;
  m[S_Gal8] = 0;
  m[S_Gal8_NDP52] = 0;
  m[S_Gal8_Ub] = 0;
  m[S_Gal8_Ub_NDP52] = 0;
  m[S_Gal8_Ub_NDP52_N_S] = 0;
  m[S_Gal8_Ub_NDP52_OPTN_p62] = 0;
  m[S_Gal8_Ub_NDP52_OPTN_p62_N_S] = 0;
  m[S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1] = 0;
  m[S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1i] = 0;
  m[S_Gal8_Ub_NDP52_p62_OPTNp_N_S_OligoTBK1] = 0;
  m[S_Gal8_Ub_OPTN] = 0;
  m[S_Gal8_Ub_p62] = 0;
  m[S_Ub] = 0;
  m[S_Ub_NDP52] = 0;
  m[S_Ub_NDP52_N_S] = 0;
  m[S_Ub_NDP52_OPTN_p62] = 0;
  m[S_Ub_NDP52_OPTN_p62_N_S] = 0;
  m[S_Ub_NDP52_OPTN_p62_N_S_OligoTBK1] = 0;
  m[S_Ub_NDP52_OPTN_p62_N_S_diTBK1] = 0;
  m[S_Ub_NDP52_OPTN_p62_N_S_diTBK1i] = 0;
  m[S_Ub_OPTN] = 0;
  m[S_Ub_p62] = 0;
  m[SignalAutophagyInduction] = 0;
  m[SignalSCVdamage] = 0;
  m[TBK1] = 200;
  m[ULK1comp] = 0;
  m[mTORC1_ULK1comp] = 200;
  m[mTORC1_ULK1comp_SCV] = 0;
  m[mTORC1inactive] = 0;
  m[p62] = 200;
  m[LC3_signal] = 0;
  m[LC3] = 0;
  m[XenoStart] = 0;
  return m;
}
double expression_propensity(std::size_t i, const Marking& m) {
  switch (i) {
    case 2: return ((0.000105 * static_cast<double>(m[AdapSalVac])) * (1.0 - (static_cast<double>(m[AdapSalVac]) / 150.0)));
    case 3: return ((0.000105 * static_cast<double>(m[AdapSalCyt])) * (1.0 - (static_cast<double>(m[AdapSalCyt]) / 700.0)));
    case 6: return (((0.0001 * static_cast<double>(m[SalCyt])) * 100.0) / (100.0 + static_cast<double>(m[XenoSig])));
    case 8: return (((0.0001 * static_cast<double>(m[AdapSalCyt])) * 100.0) / (100.0 + static_cast<double>(m[XenoSig])));
    case 17: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[Gal8])));
    case 18: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[E3_ligase])));
    case 19: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[p62])));
    case 20: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[NDP52])));
    case 21: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[OPTN])));
    case 22: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[N_S])));
    case 23: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[TBK1])));
    case 24: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[mTORC1_ULK1comp])));
    case 74: return (0.01 * std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0));
    case 75: return ((0.001 * 200.0) / (200.0 + static_cast<double>(m[LC3_GABARAP])));
    case 77: return (((((0.001 * static_cast<double>(m[SalCyt])) * std::min(static_cast<double>(m[Gal8]), 1.0)) * std::min(static_cast<double>(m[E3_ligase]), 1.0)) * std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0)) / (300.0 + std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0)));
    case 78: return (((((0.001 * static_cast<double>(m[AdapSalCyt])) * std::min(static_cast<double>(m[Gal8]), 1.0)) * std::min(static_cast<double>(m[E3_ligase]), 1.0)) * std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0)) / (300.0 + std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0)));
    case 79: return (0.01 * std::max((static_cast<double>(m[XenoSig]) - 200.0), 0.0));
    default: return 0.0;
  }
}
}
