#include "petrinet/expression.h"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <sstream>

namespace petrinet {
namespace {

struct Lex {
    enum Type { Number, Ident, Op, LParen, RParen, Comma, End } type = End;
    std::string text;
    double number = 0.0;
};

class Lexer {
public:
    explicit Lexer(const std::string& source) : source_(source) {}

    Lex next() {
        while (pos_ < source_.size() && std::isspace(static_cast<unsigned char>(source_[pos_]))) ++pos_;
        if (pos_ >= source_.size()) return Lex();
        char ch = source_[pos_];
        if (std::isdigit(static_cast<unsigned char>(ch)) || ch == '.') {
            const std::size_t start = pos_;
            while (pos_ < source_.size() &&
                   (std::isdigit(static_cast<unsigned char>(source_[pos_])) || source_[pos_] == '.')) ++pos_;
            if (pos_ < source_.size() && (source_[pos_] == 'e' || source_[pos_] == 'E')) {
                ++pos_;
                if (pos_ < source_.size() && (source_[pos_] == '+' || source_[pos_] == '-')) ++pos_;
                while (pos_ < source_.size() && std::isdigit(static_cast<unsigned char>(source_[pos_]))) ++pos_;
            }
            Lex out;
            out.type = Lex::Number;
            out.text = source_.substr(start, pos_ - start);
            out.number = std::stod(out.text);
            return out;
        }
        if (std::isalpha(static_cast<unsigned char>(ch)) || ch == '_') {
            const std::size_t start = pos_;
            while (pos_ < source_.size() &&
                   (std::isalnum(static_cast<unsigned char>(source_[pos_])) || source_[pos_] == '_')) ++pos_;
            Lex out;
            out.type = Lex::Ident;
            out.text = source_.substr(start, pos_ - start);
            return out;
        }
        ++pos_;
        Lex out;
        out.text = std::string(1, ch);
        if (ch == '(') out.type = Lex::LParen;
        else if (ch == ')') out.type = Lex::RParen;
        else if (ch == ',') out.type = Lex::Comma;
        else if (ch == '+' || ch == '-' || ch == '*' || ch == '/') out.type = Lex::Op;
        else throw ExpressionError("unexpected character in expression: " + out.text);
        return out;
    }

private:
    const std::string& source_;
    std::size_t pos_ = 0;
};

bool is_func(const std::string& name) {
    return name == "min" || name == "max" || name == "abs" || name == "sqrt" ||
           name == "exp" || name == "log" || name == "sin" || name == "cos";
}

int precedence(char op) {
    if (op == '~') return 3;
    if (op == '*' || op == '/') return 2;
    if (op == '+' || op == '-') return 1;
    return 0;
}

} // namespace

Expression::Expression(const std::string& source, const Model& model) : source_(source) {
    struct StackItem {
        char kind = 0; // op, func, paren
        char op = 0;
        std::string text;
        int argc = 0;
    };

    Lexer lexer(source);
    std::vector<Lex> tokens;
    for (;;) {
        Lex t = lexer.next();
        tokens.push_back(t);
        if (t.type == Lex::End) break;
    }

    std::vector<StackItem> stack;
    bool expect_value = true;
    for (std::size_t i = 0; i < tokens.size(); ++i) {
        const Lex& tok = tokens[i];
        if (tok.type == Lex::End) break;
        if (tok.type == Lex::Number) {
            Token out;
            out.kind = Kind::Number;
            out.number = tok.number;
            rpn_.push_back(out);
            expect_value = false;
        } else if (tok.type == Lex::Ident) {
            bool call = (i + 1 < tokens.size() && tokens[i + 1].type == Lex::LParen);
            if (call) {
                if (!is_func(tok.text)) throw ExpressionError("function is not allowed: " + tok.text);
                StackItem item;
                item.kind = 'f';
                item.text = tok.text;
                item.argc = 1;
                stack.push_back(item);
            } else {
                Token out;
                auto pit = model.place_index.find(tok.text);
                if (pit != model.place_index.end()) {
                    out.kind = Kind::Place;
                    out.index = pit->second;
                } else if (model.params.find(tok.text) != model.params.end()) {
                    out.kind = Kind::Param;
                    out.text = tok.text;
                } else if (tok.text == "pi") {
                    out.kind = Kind::Number;
                    out.number = 3.14159265358979323846;
                } else if (tok.text == "e") {
                    out.kind = Kind::Number;
                    out.number = 2.71828182845904523536;
                } else {
                    throw ExpressionError("unknown identifier: " + tok.text);
                }
                rpn_.push_back(out);
                expect_value = false;
            }
        } else if (tok.type == Lex::Op) {
            char op = tok.text[0];
            if (expect_value && (op == '-' || op == '+')) op = op == '-' ? '~' : '#';
            if (op == '#') continue;
            while (!stack.empty() && stack.back().kind == 'o' &&
                   precedence(stack.back().op) >= precedence(op)) {
                Token out;
                out.kind = Kind::Op;
                out.op = stack.back().op;
                stack.pop_back();
                rpn_.push_back(out);
            }
            StackItem item;
            item.kind = 'o';
            item.op = op;
            stack.push_back(item);
            expect_value = true;
        } else if (tok.type == Lex::LParen) {
            StackItem item;
            item.kind = '(';
            stack.push_back(item);
            expect_value = true;
        } else if (tok.type == Lex::Comma) {
            while (!stack.empty() && stack.back().kind != '(') {
                Token out;
                out.kind = Kind::Op;
                out.op = stack.back().op;
                stack.pop_back();
                rpn_.push_back(out);
            }
            for (auto it = stack.rbegin(); it != stack.rend(); ++it) {
                if (it->kind == 'f') {
                    ++it->argc;
                    break;
                }
            }
            expect_value = true;
        } else if (tok.type == Lex::RParen) {
            while (!stack.empty() && stack.back().kind != '(') {
                Token out;
                out.kind = Kind::Op;
                out.op = stack.back().op;
                stack.pop_back();
                rpn_.push_back(out);
            }
            if (stack.empty()) throw ExpressionError("mismatched parenthesis");
            stack.pop_back();
            if (!stack.empty() && stack.back().kind == 'f') {
                Token out;
                out.kind = Kind::Func;
                out.text = stack.back().text;
                out.argc = stack.back().argc;
                stack.pop_back();
                rpn_.push_back(out);
            }
            expect_value = false;
        }
    }
    while (!stack.empty()) {
        if (stack.back().kind == '(') throw ExpressionError("mismatched parenthesis");
        Token out;
        if (stack.back().kind == 'f') {
            out.kind = Kind::Func;
            out.text = stack.back().text;
            out.argc = stack.back().argc;
        } else {
            out.kind = Kind::Op;
            out.op = stack.back().op;
        }
        stack.pop_back();
        rpn_.push_back(out);
    }
}

double Expression::evaluate(const std::vector<int>& marking,
                            const std::map<std::string, double>& params) const {
    std::vector<double> stack;
    for (const Token& tok : rpn_) {
        if (tok.kind == Kind::Number) stack.push_back(tok.number);
        else if (tok.kind == Kind::Place) stack.push_back(static_cast<double>(marking[tok.index]));
        else if (tok.kind == Kind::Param) {
            auto it = params.find(tok.text);
            if (it == params.end()) throw ExpressionError("missing parameter: " + tok.text);
            stack.push_back(it->second);
        } else if (tok.kind == Kind::Op) {
            if (tok.op == '~') {
                if (stack.empty()) throw ExpressionError("bad unary expression");
                stack.back() = -stack.back();
                continue;
            }
            if (stack.size() < 2) throw ExpressionError("bad binary expression");
            double b = stack.back(); stack.pop_back();
            double a = stack.back(); stack.pop_back();
            if (tok.op == '+') stack.push_back(a + b);
            else if (tok.op == '-') stack.push_back(a - b);
            else if (tok.op == '*') stack.push_back(a * b);
            else if (tok.op == '/') stack.push_back(a / b);
        } else if (tok.kind == Kind::Func) {
            if (stack.size() < static_cast<std::size_t>(tok.argc)) throw ExpressionError("bad function call");
            std::vector<double> args(tok.argc);
            for (int i = tok.argc - 1; i >= 0; --i) {
                args[i] = stack.back();
                stack.pop_back();
            }
            if (tok.text == "min") stack.push_back(*std::min_element(args.begin(), args.end()));
            else if (tok.text == "max") stack.push_back(*std::max_element(args.begin(), args.end()));
            else if (tok.text == "abs") stack.push_back(std::fabs(args.at(0)));
            else if (tok.text == "sqrt") stack.push_back(std::sqrt(args.at(0)));
            else if (tok.text == "exp") stack.push_back(std::exp(args.at(0)));
            else if (tok.text == "log") stack.push_back(std::log(args.at(0)));
            else if (tok.text == "sin") stack.push_back(std::sin(args.at(0)));
            else if (tok.text == "cos") stack.push_back(std::cos(args.at(0)));
        }
    }
    if (stack.size() != 1) throw ExpressionError("expression did not reduce to one value: " + source_);
    return stack.back();
}

} // namespace petrinet
