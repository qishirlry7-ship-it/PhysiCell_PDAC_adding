#include "petrinet/ssa.h"

#include <cmath>
#include <numeric>
#include <stdexcept>

namespace petrinet {
namespace {

double unit_open(std::mt19937_64& rng) {
    return (static_cast<double>(rng()) + 1.0) /
           (static_cast<double>(std::mt19937_64::max()) + 2.0);
}

} // namespace

double combination(int count, int weight) {
    if (weight < 0 || count < weight) return 0.0;
    if (weight == 0) return 1.0;
    double value = 1.0;
    for (int i = 1; i <= weight; ++i) {
        value *= static_cast<double>(count - weight + i) / static_cast<double>(i);
    }
    return value;
}

SSA::SSA(const Model& model) : model_(model) {
    for (const Transition& t : model_.transitions) {
        if (t.has_expression) expressions_.push_back(Expression(t.expression, model_));
        else expressions_.push_back(Expression());
    }
}

double SSA::propensity(int transition_index, const std::vector<int>& marking) const {
    const Transition& t = model_.transitions.at(static_cast<std::size_t>(transition_index));
    if (!t.enabled) return 0.0;
    for (const Arc& arc : t.input) {
        if (marking[arc.place] < arc.weight) return 0.0;
    }
    double value = 0.0;
    if (t.has_expression) {
        value = expressions_[transition_index].evaluate(marking, model_.params);
    } else if (t.has_rate) {
        value = t.rate;
        for (const Arc& arc : t.input) value *= combination(marking[arc.place], arc.weight);
    }
    return std::isfinite(value) && value > 0.0 ? value : 0.0;
}

void SSA::fire(int transition_index, std::vector<int>& marking) const {
    const Transition& t = model_.transitions.at(static_cast<std::size_t>(transition_index));
    for (const Arc& arc : t.input) marking[arc.place] -= arc.weight;
    for (const Arc& arc : t.output) marking[arc.place] += arc.weight;
}

TimeSeries SSA::simulate(std::vector<int> marking, const SSAOptions& options) const {
    TimeSeries series;
    for (const Place& p : model_.places) series.place_order.push_back(p.id);
    series.steps.push_back(TimePoint{0.0, "__init__", marking});

    std::mt19937_64 rng(options.seed);
    double clock = 0.0;
    int events = 0;
    while (clock < options.t_end && events < options.max_events) {
        std::vector<double> props(model_.transitions.size(), 0.0);
        double a0 = 0.0;
        for (std::size_t i = 0; i < model_.transitions.size(); ++i) {
            props[i] = propensity(static_cast<int>(i), marking);
            a0 += props[i];
        }
        if (a0 <= 0.0) break;
        const double dt = -std::log(unit_open(rng)) / a0;
        if (clock + dt > options.t_end) {
            clock = options.t_end;
            series.steps.push_back(TimePoint{clock, "__end__", marking});
            break;
        }
        clock += dt;
        double pick = unit_open(rng) * a0;
        int chosen = -1;
        for (std::size_t i = 0; i < props.size(); ++i) {
            pick -= props[i];
            if (pick <= 0.0) {
                chosen = static_cast<int>(i);
                break;
            }
        }
        if (chosen < 0) chosen = static_cast<int>(props.size() - 1);
        fire(chosen, marking);
        ++events;
        series.steps.push_back(TimePoint{clock, model_.transitions[chosen].id, marking});
    }
    return series;
}

} // namespace petrinet
