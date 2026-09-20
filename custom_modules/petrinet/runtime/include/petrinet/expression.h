#pragma once

#include "model.h"

#include <stdexcept>
#include <string>
#include <vector>

namespace petrinet {

class ExpressionError : public std::runtime_error {
public:
    explicit ExpressionError(const std::string& message) : std::runtime_error(message) {}
};

class Expression {
public:
    Expression() = default;
    Expression(const std::string& source, const Model& model);

    double evaluate(const std::vector<int>& marking,
                    const std::map<std::string, double>& params) const;
    const std::string& source() const { return source_; }
    bool empty() const { return rpn_.empty(); }

private:
    enum class Kind { Number, Place, Param, Op, Func };
    struct Token {
        Kind kind;
        double number = 0.0;
        int index = -1;
        char op = 0;
        std::string text;
        int argc = 0;
    };

    std::string source_;
    std::vector<Token> rpn_;
};

} // namespace petrinet
