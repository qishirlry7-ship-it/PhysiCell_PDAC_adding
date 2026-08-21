#!/usr/bin/env python3
"""Generate deterministic C++11 model data from the upstream Petri-net JSON."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "2.1.0"
ALLOWED_FUNCS = {"min", "max", "abs", "sqrt", "exp", "log"}
REQUIRED_PARAMETERS = {
    "k_death", "death_threshold", "cap_cyt_initial", "cap_vac_initial",
    "sigmoid_k", "sigmoid_mid_base", "sigmoid_mid_slope", "mhc_alpha",
    "mhc_beta", "xeno_signal_mode", "division_daughter_fraction",
    "mhc_d_X", "mhc_d_M", "mhc_k_T", "mhc_d_C",
    "mhc_d_P", "mhc_k_load", "mhc_S_M_base", "mhc_V_M_IFN",
    "mhc_K_M_IFN", "mhc_ifn_gamma", "mhc_r_pep", "mhc_X0", "mhc_M0",
    "mhc_C0", "mhc_P0", "mhc_max_step_seconds",
    "bacterial_uptake_rate", "bacterial_uptake_interval",
    "bacterial_uptake_distance",
}


class GenerationError(ValueError):
    pass


def load_parameters(path: Path) -> dict:
    root = ET.parse(path).getroot()
    if root.tag != "petrinet_parameters":
        raise GenerationError("parameter XML root must be petrinet_parameters")
    values = {}
    for section_name in ("engine", "mhc", "coupling"):
        section = root.find(section_name)
        if section is None:
            raise GenerationError(f"parameter XML requires {section_name}")
        for node in section.findall("parameter"):
            name, raw = node.get("name"), node.get("value")
            if not name or name in values or raw is None:
                raise GenerationError(f"invalid or duplicate parameter in {section_name}")
            try:
                value = float(raw)
            except ValueError as exc:
                raise GenerationError(f"parameter {name!r} is not numeric") from exc
            if not math.isfinite(value):
                raise GenerationError(f"parameter {name!r} must be finite")
            values[name] = value
    missing = sorted(REQUIRED_PARAMETERS - values.keys())
    if missing:
        raise GenerationError("missing required parameters: " + ", ".join(missing))
    if values["mhc_K_M_IFN"] + values["mhc_ifn_gamma"] == 0.0:
        raise GenerationError("mhc_K_M_IFN + mhc_ifn_gamma must be non-zero")
    if values["xeno_signal_mode"] not in (0.0, 1.0):
        raise GenerationError("xeno_signal_mode must be 0 or 1")
    if not 0.0 <= values["division_daughter_fraction"] <= 1.0:
        raise GenerationError("division_daughter_fraction must be in [0,1]")
    if values["mhc_max_step_seconds"] <= 0.0:
        raise GenerationError("mhc_max_step_seconds must be positive")
    if values["bacterial_uptake_rate"] < 0.0:
        raise GenerationError("bacterial_uptake_rate must be non-negative")
    if values["bacterial_uptake_interval"] <= 0.0:
        raise GenerationError("bacterial_uptake_interval must be positive")
    if values["bacterial_uptake_distance"] < 0.0:
        raise GenerationError("bacterial_uptake_distance must be non-negative")
    marking = {}
    for node in root.findall("./initial_marking/place"):
        name, raw = node.get("id"), node.get("tokens")
        if not name or name in marking or raw is None:
            raise GenerationError("invalid or duplicate initial marking")
        try:
            value = int(raw)
        except ValueError as exc:
            raise GenerationError(f"initial marking {name!r} is not an integer") from exc
        if value < 0:
            raise GenerationError(f"initial marking {name!r} must be non-negative")
        marking[name] = value
    disabled = [node.get("id") for node in root.findall("./transitions/disable")]
    overrides = {}
    for node in root.findall("./transitions/override"):
        name, expression = node.get("id"), (node.text or "").strip()
        if not name or name in overrides or not expression:
            raise GenerationError("invalid or duplicate transition override")
        overrides[name] = expression
    return {"parameters": values, "initial_marking": marking,
            "disable": disabled, "override": overrides}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cpp_ident(value: str) -> str:
    result = re.sub(r"\W", "_", value)
    if not result or result[0].isdigit():
        result = "P_" + result
    return result


class ExpressionCompiler(ast.NodeVisitor):
    def __init__(self, places: dict[str, int], params: set[str]):
        self.places = places
        self.params = params

    def compile(self, expression: str) -> str:
        try:
            return self.visit(ast.parse(expression, mode="eval").body)
        except (SyntaxError, GenerationError) as exc:
            raise GenerationError(f"invalid expression {expression!r}: {exc}") from exc

    def visit_Constant(self, node: ast.Constant) -> str:
        if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
            raise GenerationError("only numeric constants are allowed")
        if not math.isfinite(float(node.value)):
            raise GenerationError("constants must be finite")
        return repr(float(node.value))

    def visit_Name(self, node: ast.Name) -> str:
        if node.id in self.places:
            return f"static_cast<double>(m[{cpp_ident(node.id)}])"
        if node.id in self.params:
            return f"parameters.{cpp_ident(node.id)}"
        raise GenerationError(f"unknown identifier {node.id!r}")

    def visit_BinOp(self, node: ast.BinOp) -> str:
        ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
        op = ops.get(type(node.op))
        if op is None:
            raise GenerationError(f"operator {type(node.op).__name__} is not allowed")
        return f"({self.visit(node.left)} {op} {self.visit(node.right)})"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        if isinstance(node.op, ast.USub):
            return f"(-{self.visit(node.operand)})"
        if isinstance(node.op, ast.UAdd):
            return f"(+{self.visit(node.operand)})"
        raise GenerationError("only unary +/- are allowed")

    def visit_Call(self, node: ast.Call) -> str:
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCS:
            raise GenerationError("function is not in the whitelist")
        if node.keywords:
            raise GenerationError("keyword arguments are not allowed")
        args = [self.visit(arg) for arg in node.args]
        name = node.func.id
        if name in {"min", "max"}:
            if len(args) < 2:
                raise GenerationError(f"{name} requires at least two arguments")
            func = "std::min" if name == "min" else "std::max"
            out = f"{func}({args[0]}, {args[1]})"
            for arg in args[2:]:
                out = f"{func}({out}, {arg})"
            return out
        if len(args) != 1:
            raise GenerationError(f"{name} requires one argument")
        func = "std::fabs" if name == "abs" else f"std::{name}"
        return f"{func}({args[0]})"

    def generic_visit(self, node: ast.AST) -> str:
        raise GenerationError(f"syntax {type(node).__name__} is not allowed")


def validate(model: dict, integration: dict) -> tuple[list[dict], dict[str, int]]:
    if not isinstance(model.get("places"), list) or not isinstance(model.get("transitions"), list):
        raise GenerationError("model requires places and transitions arrays")
    place_ids = [p.get("id") for p in model["places"]]
    if any(not isinstance(p, str) or not p for p in place_ids) or len(place_ids) != len(set(place_ids)):
        raise GenerationError("place IDs must be unique non-empty strings")
    places = {name: i for i, name in enumerate(place_ids)}
    for name, count in integration.get("initial_marking", {}).items():
        if name not in places:
            raise GenerationError(f"initial_marking references unknown place {name!r}")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise GenerationError(f"initial_marking[{name!r}] must be a non-negative integer")
    transitions = model["transitions"]
    ids = [t.get("id") for t in transitions]
    if any(not isinstance(t, str) or not t for t in ids) or len(ids) != len(set(ids)):
        raise GenerationError("transition IDs must be unique non-empty strings")
    known = set(ids)
    for name in list(integration.get("disable", [])) + list(integration.get("override", {})):
        if name not in known:
            raise GenerationError(f"integration references unknown transition {name!r}")
    for transition in transitions:
        for direction, key in (("input", "from"), ("output", "to")):
            for arc in transition.get(direction, []):
                if arc.get(key) not in places:
                    raise GenerationError(f"{transition['id']}: unknown place {arc.get(key)!r}")
                weight = arc.get("weight", 1)
                if not isinstance(weight, int) or isinstance(weight, bool) or weight <= 0:
                    raise GenerationError(f"{transition['id']}: weights must be positive integers")
        rate = transition.get("rate")
        expression = integration.get("override", {}).get(transition["id"], transition.get("expression"))
        if expression is None and rate is None and transition["id"] not in integration.get("disable", []):
            raise GenerationError(f"{transition['id']}: missing rate/expression")
        if rate is not None and (not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate < 0):
            raise GenerationError(f"{transition['id']}: rate must be finite and non-negative")
    return transitions, places


def render(model_path: Path, parameters_path: Path) -> tuple[str, str]:
    model = json.loads(model_path.read_text(encoding="utf-8"))
    integration = load_parameters(parameters_path)
    transitions, places = validate(model, integration)
    params = integration.get("parameters", {})
    compiler = ExpressionCompiler(places, set(params))
    disabled = set(integration.get("disable", []))
    overrides = integration.get("override", {})
    header = [
        "// Generated file. Do not edit.",
        f"// generator={VERSION} model_sha256={sha256(model_path)} parameters_sha256={sha256(parameters_path)}",
        "#pragma once", "#include <array>", "#include <cstddef>", "#include <string>", "#include <vector>",
        "namespace xenophagy {",
        "enum Place : std::size_t {",
    ]
    header += [f"  {cpp_ident(name)} = {idx}," for name, idx in places.items()]
    header += [f"  PLACE_COUNT = {len(places)}", "};", "using Marking = std::array<int, PLACE_COUNT>;", "struct ModelParameters {"]
    header += [f"  double {cpp_ident(name)} = {float(value)!r};" for name, value in params.items()]
    header += [
        "};",
        "struct Arc { Place place; int weight; };",
        "struct Transition { const char* id; double rate; bool uses_expression; bool enabled; std::vector<Arc> input; std::vector<Arc> output; };",
        "extern const ModelParameters parameters;",
        "extern const std::array<const char*, PLACE_COUNT> place_names;",
        f"extern const std::array<Transition, {len(transitions)}> transitions;",
        "Marking initial_marking();",
        "double expression_propensity(std::size_t transition_index, const Marking& m);",
        "}", "",
    ]
    source = [
        "// Generated file. Do not edit.",
        f"// generator={VERSION} model_sha256={sha256(model_path)} parameters_sha256={sha256(parameters_path)}",
        '#include "xenophagy_model_generated.h"', "#include <algorithm>", "#include <cmath>",
        "namespace xenophagy {", "const ModelParameters parameters{};",
        "const std::array<const char*, PLACE_COUNT> place_names = {{",
    ]
    source += [f'  "{name}",' for name in places]
    source += ["}};", f"const std::array<Transition, {len(transitions)}> transitions = {{{{"]
    for transition in transitions:
        inputs = ", ".join(f"{{{cpp_ident(a['from'])}, {a.get('weight', 1)}}}" for a in transition.get("input", []))
        outputs = ", ".join(f"{{{cpp_ident(a['to'])}, {a.get('weight', 1)}}}" for a in transition.get("output", []))
        expr = overrides.get(transition["id"], transition.get("expression"))
        rate = float(transition.get("rate") or 0.0)
        source.append(f'  {{"{transition["id"]}", {rate!r}, {str(expr is not None).lower()}, {str(transition["id"] not in disabled).lower()}, {{{inputs}}}, {{{outputs}}}}},')
    source += ["}};", "Marking initial_marking() {", "  Marking m{};"]
    initial_override = integration.get("initial_marking", {})
    for place in model["places"]:
        tokens = initial_override.get(place["id"], place.get("tokens", 0))
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
            raise GenerationError(f"{place['id']}: tokens must be a non-negative integer")
        source.append(f"  m[{cpp_ident(place['id'])}] = {tokens};")
    source += ["  return m;", "}", "double expression_propensity(std::size_t i, const Marking& m) {", "  switch (i) {"]
    for i, transition in enumerate(transitions):
        expr = overrides.get(transition["id"], transition.get("expression"))
        if expr is not None:
            source.append(f"    case {i}: return {compiler.compile(expr)};")
    source += ["    default: return 0.0;", "  }", "}", "}", ""]
    return "\n".join(header), "\n".join(source)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("config/petrinet/xenophagy_model.json"))
    parser.add_argument("--parameters", type=Path, default=Path("config/petrinet/parameters.xml"))
    parser.add_argument("--out-dir", type=Path, default=Path("custom_modules/generated"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        header, source = render(args.model, args.parameters)
    except (OSError, json.JSONDecodeError, ET.ParseError, GenerationError) as exc:
        print(f"generation failed: {exc}", file=sys.stderr)
        return 2
    expected = {"xenophagy_model_generated.h": header, "xenophagy_model_generated.cpp": source}
    if args.check:
        stale = [name for name, content in expected.items() if not (args.out_dir / name).exists() or (args.out_dir / name).read_text(encoding="utf-8") != content]
        if stale:
            print("stale generated files: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("generated Petri-net files are current")
        return 0
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in expected.items():
        (args.out_dir / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"generated {len(expected)} files in {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
