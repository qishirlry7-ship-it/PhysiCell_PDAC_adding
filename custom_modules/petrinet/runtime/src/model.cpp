#include "petrinet/model.h"
#include "petrinet/json.h"

#include <stdexcept>

namespace petrinet {
namespace {

int optional_int(const Json& object, const std::string& key, int fallback) {
    return object.contains(key) && !object.at(key).is_null() ? object.at(key).as_int() : fallback;
}

Arc parse_arc(const Json& arc_json, const Model& model, const std::string& key) {
    Arc arc;
    const std::string place = arc_json.at(key).as_string();
    arc.place = model.place_id(place);
    arc.weight = optional_int(arc_json, "weight", 1);
    if (arc.weight <= 0) throw std::runtime_error("arc weight must be positive");
    return arc;
}

} // namespace

int Model::place_id(const std::string& id) const {
    auto it = place_index.find(id);
    if (it == place_index.end()) throw std::runtime_error("unknown place: " + id);
    return it->second;
}

int Model::transition_id(const std::string& id) const {
    auto it = transition_index.find(id);
    if (it == transition_index.end()) throw std::runtime_error("unknown transition: " + id);
    return it->second;
}

std::vector<int> Model::initial_marking() const {
    std::vector<int> out(places.size(), 0);
    for (std::size_t i = 0; i < places.size(); ++i) out[i] = places[i].tokens;
    return out;
}

Model load_json_model(const std::string& path) {
    Json root = Json::parse_file(path);
    Model model;
    if (root.contains("name") && root.at("name").is_string()) model.name = root.at("name").as_string();
    if (root.contains("params") && root.at("params").is_object()) {
        for (const auto& kv : root.at("params").as_object()) {
            if (kv.second.is_number()) model.params[kv.first] = kv.second.as_number();
        }
    }
    for (const Json& p : root.at("places").as_array()) {
        Place place;
        place.id = p.at("id").as_string();
        place.tokens = optional_int(p, "tokens", 0);
        if (place.tokens < 0) throw std::runtime_error("place tokens must be non-negative: " + place.id);
        if (model.place_index.count(place.id)) throw std::runtime_error("duplicate place: " + place.id);
        model.place_index[place.id] = static_cast<int>(model.places.size());
        model.places.push_back(place);
    }
    for (const Json& t : root.at("transitions").as_array()) {
        Transition transition;
        transition.id = t.at("id").as_string();
        if (model.transition_index.count(transition.id)) throw std::runtime_error("duplicate transition: " + transition.id);
        if (t.contains("rate") && !t.at("rate").is_null()) {
            transition.rate = t.at("rate").as_number();
            transition.has_rate = true;
        }
        if (t.contains("expression") && !t.at("expression").is_null()) {
            transition.expression = t.at("expression").as_string();
            transition.has_expression = true;
        }
        if (t.contains("deterministic") && t.at("deterministic").is_bool()) {
            // Record the flag; do NOT fold it into "enabled". A deterministic
            // reaction is a rate-law property (saturable synthesis/degradation)
            // and must remain firable, so disabling it here silently removed
            // the entire Deg*/Syn* subsystem from every simulation.
            transition.deterministic = t.at("deterministic").as_bool();
        }
        if (t.contains("enabled") && t.at("enabled").is_bool()) {
            transition.enabled = t.at("enabled").as_bool();
        }
        if (t.contains("input")) {
            for (const Json& arc : t.at("input").as_array()) transition.input.push_back(parse_arc(arc, model, "from"));
        }
        if (t.contains("output")) {
            for (const Json& arc : t.at("output").as_array()) transition.output.push_back(parse_arc(arc, model, "to"));
        }
        model.transition_index[transition.id] = static_cast<int>(model.transitions.size());
        model.transitions.push_back(transition);
    }
    return model;
}

} // namespace petrinet
