#pragma once

#include <algorithm>
#include <cmath>

namespace xenophagy {

inline double mhcii_cd4_recognition(double surface_pmhc, double half_max,
                                    double hill) {
    if (!(surface_pmhc > 0.0) || !(half_max > 0.0) || !(hill > 0.0))
        return 0.0;
    const double ratio = surface_pmhc / half_max;
    const double powered = std::pow(ratio, hill);
    if (!std::isfinite(powered)) return 1.0;
    return std::max(0.0, std::min(1.0, powered / (1.0 + powered)));
}

} // namespace xenophagy
