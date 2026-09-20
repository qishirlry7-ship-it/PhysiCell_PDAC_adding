#include "petrinet/json.h"

#include <cctype>
#include <fstream>
#include <sstream>

namespace petrinet {
namespace {

class Parser {
public:
    explicit Parser(const std::string& text) : text_(text) {}

    Json parse() {
        Json value = parse_value();
        skip_ws();
        if (pos_ != text_.size()) fail("unexpected trailing input");
        return value;
    }

private:
    const std::string& text_;
    std::size_t pos_ = 0;

    void fail(const std::string& message) const {
        throw JsonError(message + " at byte " + std::to_string(pos_));
    }

    void skip_ws() {
        while (pos_ < text_.size() && std::isspace(static_cast<unsigned char>(text_[pos_]))) ++pos_;
    }

    bool consume(char ch) {
        skip_ws();
        if (pos_ < text_.size() && text_[pos_] == ch) {
            ++pos_;
            return true;
        }
        return false;
    }

    void expect(char ch) {
        if (!consume(ch)) fail(std::string("expected '") + ch + "'");
    }

    Json parse_value() {
        skip_ws();
        if (pos_ >= text_.size()) fail("unexpected end");
        const char ch = text_[pos_];
        if (ch == '"') return Json(parse_string());
        if (ch == '{') return parse_object();
        if (ch == '[') return parse_array();
        if (ch == '-' || std::isdigit(static_cast<unsigned char>(ch))) return Json(parse_number());
        if (text_.compare(pos_, 4, "true") == 0) {
            pos_ += 4;
            return Json(true);
        }
        if (text_.compare(pos_, 5, "false") == 0) {
            pos_ += 5;
            return Json(false);
        }
        if (text_.compare(pos_, 4, "null") == 0) {
            pos_ += 4;
            return Json(nullptr);
        }
        fail("unexpected value");
        return Json();
    }

    std::string parse_string() {
        expect('"');
        std::string out;
        while (pos_ < text_.size()) {
            char ch = text_[pos_++];
            if (ch == '"') return out;
            if (ch == '\\') {
                if (pos_ >= text_.size()) fail("bad escape");
                char esc = text_[pos_++];
                switch (esc) {
                    case '"': out.push_back('"'); break;
                    case '\\': out.push_back('\\'); break;
                    case '/': out.push_back('/'); break;
                    case 'b': out.push_back('\b'); break;
                    case 'f': out.push_back('\f'); break;
                    case 'n': out.push_back('\n'); break;
                    case 'r': out.push_back('\r'); break;
                    case 't': out.push_back('\t'); break;
                    case 'u':
                        if (pos_ + 4 > text_.size()) fail("short unicode escape");
                        out.push_back('?');
                        pos_ += 4;
                        break;
                    default: fail("bad escape");
                }
            } else {
                out.push_back(ch);
            }
        }
        fail("unterminated string");
        return out;
    }

    double parse_number() {
        const std::size_t start = pos_;
        if (text_[pos_] == '-') ++pos_;
        while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        if (pos_ < text_.size() && text_[pos_] == '.') {
            ++pos_;
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        }
        if (pos_ < text_.size() && (text_[pos_] == 'e' || text_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < text_.size() && (text_[pos_] == '+' || text_[pos_] == '-')) ++pos_;
            while (pos_ < text_.size() && std::isdigit(static_cast<unsigned char>(text_[pos_]))) ++pos_;
        }
        return std::stod(text_.substr(start, pos_ - start));
    }

    Json parse_array() {
        expect('[');
        std::vector<Json> values;
        if (consume(']')) return Json(std::move(values));
        while (true) {
            values.push_back(parse_value());
            if (consume(']')) break;
            expect(',');
        }
        return Json(std::move(values));
    }

    Json parse_object() {
        expect('{');
        std::map<std::string, Json> values;
        if (consume('}')) return Json(std::move(values));
        while (true) {
            skip_ws();
            if (pos_ >= text_.size() || text_[pos_] != '"') fail("expected object key");
            std::string key = parse_string();
            expect(':');
            values[key] = parse_value();
            if (consume('}')) break;
            expect(',');
        }
        return Json(std::move(values));
    }
};

} // namespace

Json::Json() : type_(Type::Null), bool_value_(false), number_value_(0.0) {}
Json::Json(std::nullptr_t) : Json() {}
Json::Json(bool value) : type_(Type::Bool), bool_value_(value), number_value_(0.0) {}
Json::Json(double value) : type_(Type::Number), bool_value_(false), number_value_(value) {}
Json::Json(const std::string& value) : type_(Type::String), bool_value_(false), number_value_(0.0), string_value_(value) {}
Json::Json(std::string&& value) : type_(Type::String), bool_value_(false), number_value_(0.0), string_value_(std::move(value)) {}
Json::Json(const std::vector<Json>& value) : type_(Type::Array), bool_value_(false), number_value_(0.0), array_value_(value) {}
Json::Json(std::vector<Json>&& value) : type_(Type::Array), bool_value_(false), number_value_(0.0), array_value_(std::move(value)) {}
Json::Json(const std::map<std::string, Json>& value) : type_(Type::Object), bool_value_(false), number_value_(0.0), object_value_(value) {}
Json::Json(std::map<std::string, Json>&& value) : type_(Type::Object), bool_value_(false), number_value_(0.0), object_value_(std::move(value)) {}

bool Json::as_bool() const { if (!is_bool()) throw JsonError("expected bool"); return bool_value_; }
double Json::as_number() const { if (!is_number()) throw JsonError("expected number"); return number_value_; }
int Json::as_int() const { return static_cast<int>(as_number()); }
const std::string& Json::as_string() const { if (!is_string()) throw JsonError("expected string"); return string_value_; }
const std::vector<Json>& Json::as_array() const { if (!is_array()) throw JsonError("expected array"); return array_value_; }
const std::map<std::string, Json>& Json::as_object() const { if (!is_object()) throw JsonError("expected object"); return object_value_; }

bool Json::contains(const std::string& key) const {
    return is_object() && object_value_.find(key) != object_value_.end();
}

const Json& Json::at(const std::string& key) const {
    if (!is_object()) throw JsonError("expected object");
    auto it = object_value_.find(key);
    if (it == object_value_.end()) throw JsonError("missing key: " + key);
    return it->second;
}

Json Json::parse(const std::string& text) {
    return Parser(text).parse();
}

Json Json::parse_file(const std::string& path) {
    std::ifstream in(path.c_str(), std::ios::binary);
    if (!in) throw JsonError("cannot open JSON file: " + path);
    std::ostringstream buffer;
    buffer << in.rdbuf();
    return parse(buffer.str());
}

} // namespace petrinet
