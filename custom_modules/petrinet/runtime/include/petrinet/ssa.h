#pragma once

#include "expression.h"
#include "model.h"

#include <cstdint>
#include <random>
#include <string>
#include <vector>

namespace petrinet {

struct TimePoint {
    double time = 0.0;
    std::string event_id;
    std::vector<int> marking;

    TimePoint() = default;
    TimePoint(double t, const std::string& event, const std::vector<int>& state)
        : time(t), event_id(event), marking(state) {}
};

struct TimeSeries {
    std::vector<std::string> place_order;
    std::vector<TimePoint> steps;
};

struct SSAOptions {
    double t_end = 0.0;
    int max_events = 100000;
    std::uint64_t seed = 0;
};

class SSA {
public:
    explicit SSA(const Model& model);

    double propensity(int transition_index, const std::vector<int>& marking) const;
    void fire(int transition_index, std::vector<int>& marking) const;
    TimeSeries simulate(std::vector<int> marking, const SSAOptions& options) const;

private:
    const Model& model_;
    std::vector<Expression> expressions_;
};

double combination(int count, int weight);

} // namespace petrinet
