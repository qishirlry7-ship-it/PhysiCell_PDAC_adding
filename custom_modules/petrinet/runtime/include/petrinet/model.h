#pragma once

#include <map>
#include <string>
#include <vector>

namespace petrinet {

struct Arc {
    int place = -1;
    int weight = 1;
};

struct Place {
    std::string id;
    int tokens = 0;
};

struct Transition {
    std::string id;
    double rate = 0.0;
    bool has_rate = false;
    std::string expression;
    bool has_expression = false;
    bool enabled = true;
    // Marks a reaction whose rate should be evaluated as a saturable
    // (Michaelis-Menten style) continuous process rather than a plain
    // mass-action constant. It is a *rate law* hint, not an on/off switch:
    // deterministic reactions still participate in the SSA.
    bool deterministic = false;
    std::vector<Arc> input;
    std::vector<Arc> output;
};

struct Model {
    std::string name;
    std::vector<Place> places;
    std::vector<Transition> transitions;
    std::map<std::string, double> params;
    std::map<std::string, int> place_index;
    std::map<std::string, int> transition_index;

    int place_id(const std::string& id) const;
    int transition_id(const std::string& id) const;
    std::vector<int> initial_marking() const;
};

Model load_json_model(const std::string& path);

} // namespace petrinet
