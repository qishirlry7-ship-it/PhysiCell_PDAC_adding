#pragma once

#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace petrinet {

class JsonError : public std::runtime_error {
public:
    explicit JsonError(const std::string& message) : std::runtime_error(message) {}
};

class Json {
public:
    enum class Type { Null, Bool, Number, String, Array, Object };

    Json();
    explicit Json(std::nullptr_t);
    explicit Json(bool value);
    explicit Json(double value);
    explicit Json(const std::string& value);
    explicit Json(std::string&& value);
    explicit Json(const std::vector<Json>& value);
    explicit Json(std::vector<Json>&& value);
    explicit Json(const std::map<std::string, Json>& value);
    explicit Json(std::map<std::string, Json>&& value);

    Type type() const { return type_; }
    bool is_null() const { return type_ == Type::Null; }
    bool is_bool() const { return type_ == Type::Bool; }
    bool is_number() const { return type_ == Type::Number; }
    bool is_string() const { return type_ == Type::String; }
    bool is_array() const { return type_ == Type::Array; }
    bool is_object() const { return type_ == Type::Object; }

    bool as_bool() const;
    double as_number() const;
    int as_int() const;
    const std::string& as_string() const;
    const std::vector<Json>& as_array() const;
    const std::map<std::string, Json>& as_object() const;

    bool contains(const std::string& key) const;
    const Json& at(const std::string& key) const;
    const Json& operator[](const std::string& key) const { return at(key); }

    static Json parse(const std::string& text);
    static Json parse_file(const std::string& path);

private:
    Type type_;
    bool bool_value_;
    double number_value_;
    std::string string_value_;
    std::vector<Json> array_value_;
    std::map<std::string, Json> object_value_;
};

} // namespace petrinet
