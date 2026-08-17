// Generated file. Do not edit.
// generator=1.0.0 model_sha256=beaafd39036a29aab6eb846082b6d4f2ceef830d7c2d83594d976bd681b5c305 integration_sha256=bd61f9887e1a99fb71f565198db4ac1b067c82492139f2a7194463b9236cbdf8
#pragma once
#include <array>
#include <cstddef>
#include <string>
#include <vector>
namespace xenophagy {
enum Place : std::size_t {
  SalRuffle = 0,
  SalVac = 1,
  SalCyt = 2,
  AdapSalCyt = 3,
  CapCyt = 4,
  AdapSalVac = 5,
  CapVac = 6,
  XenoSig = 7,
  AA = 8,
  AAstarvation = 9,
  Ap_Gal8 = 10,
  Ap_Gal8_Ub = 11,
  Ap_Gal8_Ub_N_S = 12,
  Ap_Gal8_Ub_OPTNp = 13,
  Ap_Ub = 14,
  Ap_Ub_N_S = 15,
  Ap_Ub_OPTNp = 16,
  E3_ligase = 17,
  Gal8 = 18,
  LC3_GABARAP = 19,
  N_S = 20,
  NDP52 = 21,
  OPTN = 22,
  S_damagedSCV = 23,
  S_Gal8 = 24,
  S_Gal8_NDP52 = 25,
  S_Gal8_Ub = 26,
  S_Gal8_Ub_NDP52 = 27,
  S_Gal8_Ub_NDP52_N_S = 28,
  S_Gal8_Ub_NDP52_OPTN_p62 = 29,
  S_Gal8_Ub_NDP52_OPTN_p62_N_S = 30,
  S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1 = 31,
  S_Gal8_Ub_NDP52_OPTN_p62_N_S_diTBK1i = 32,
  S_Gal8_Ub_NDP52_p62_OPTNp_N_S_OligoTBK1 = 33,
  S_Gal8_Ub_OPTN = 34,
  S_Gal8_Ub_p62 = 35,
  S_Ub = 36,
  S_Ub_NDP52 = 37,
  S_Ub_NDP52_N_S = 38,
  S_Ub_NDP52_OPTN_p62 = 39,
  S_Ub_NDP52_OPTN_p62_N_S = 40,
  S_Ub_NDP52_OPTN_p62_N_S_OligoTBK1 = 41,
  S_Ub_NDP52_OPTN_p62_N_S_diTBK1 = 42,
  S_Ub_NDP52_OPTN_p62_N_S_diTBK1i = 43,
  S_Ub_OPTN = 44,
  S_Ub_p62 = 45,
  SignalAutophagyInduction = 46,
  SignalSCVdamage = 47,
  TBK1 = 48,
  ULK1comp = 49,
  mTORC1_ULK1comp = 50,
  mTORC1_ULK1comp_SCV = 51,
  mTORC1inactive = 52,
  p62 = 53,
  LC3_signal = 54,
  LC3 = 55,
  XenoStart = 56,
  PLACE_COUNT = 57
};
using Marking = std::array<int, PLACE_COUNT>;
struct ModelParameters {
  double k_death = 1e-07;
  double death_threshold = 100.0;
  double cap_cyt_initial = 700.0;
  double cap_vac_initial = 150.0;
  double sigmoid_k = 5e-05;
  double sigmoid_mid_base = 1800.0;
  double sigmoid_mid_slope = 200.0;
  double mhc_alpha = 1.0;
  double mhc_beta = 1.0;
};
struct Arc { Place place; int weight; };
struct Transition { const char* id; double rate; bool uses_expression; bool enabled; std::vector<Arc> input; std::vector<Arc> output; };
extern const ModelParameters parameters;
extern const std::array<const char*, PLACE_COUNT> place_names;
extern const std::array<Transition, 80> transitions;
Marking initial_marking();
double expression_propensity(std::size_t transition_index, const Marking& m);
}
