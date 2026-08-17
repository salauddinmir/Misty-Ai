# ruff: noqa: RUF001

"""LLM-independent deterministic mathematics reasoning for MISTY.

The engine intentionally accepts a small, safe grammar and rejects unsupported
input instead of guessing. It covers common arithmetic, percentages, powers,
roots, linear equations, sequences, geometry, combinatorics, probability, and
basic descriptive statistics.
"""

from __future__ import annotations

import ast
import math
import operator
import re
import statistics
from dataclasses import dataclass
from typing import ClassVar

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


@dataclass(frozen=True)
class MathResult:
    answer: str
    exact: str
    category: str
    steps: tuple[str, ...] = ()
    confidence: float = 0.98


class MathEngine:
    """Safe deterministic solver for school and introductory university math."""

    _binary: ClassVar[dict[type[ast.operator], object]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    _unary: ClassVar[dict[type[ast.unaryop], object]] = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    _functions: ClassVar[dict[str, object]] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "abs": abs,
        "factorial": math.factorial,
    }

    def solve(self, text: str) -> MathResult | None:
        normalized = self._normalize(text)
        if not self.looks_mathematical(normalized):
            return None
        clean = normalized.rstrip("?.!").strip()

        for parser in (
            self._parse_combinatorics,
            self._parse_statistics,
            self._parse_geometry,
            self._parse_linear_equation,
            self._parse_sequence,
        ):
            result = parser(clean)
            if result is not None:
                return result

        expression = self._extract_expression(clean)
        if expression is None:
            return None
        try:
            value = self._evaluate(expression)
        except (ArithmeticError, ValueError, SyntaxError, TypeError, OverflowError):
            return MathResult(
                answer="I could not safely solve that expression.",
                exact="unsupported",
                category="error",
                confidence=0.2,
            )
        return self._numeric_result(value, expression)

    @staticmethod
    def looks_mathematical(text: str) -> bool:
        lowered = text.lower()
        markers = (
            "calculate",
            "compute",
            "evaluate",
            "solve",
            "what is",
            "equals",
            "কত",
            "হিসাব",
            "সমাধান",
            "যোগ",
            "বিয়োগ",
            "বিয়োগ",
            "গুণ",
            "ভাগ",
            "শতাংশ",
            "percent",
            "area",
            "ক্ষেত্রফল",
            "perimeter",
            "পরিসীমা",
            "volume",
            "আয়তন",
            "আয়তন",
            "mean",
            "average",
            "গড়",
            "গড়",
            "median",
            "মধ্যক",
            "variance",
            "probability",
            "সম্ভাবনা",
            "factorial",
            "ফ্যাক্টোরিয়াল",
            "sqrt",
            "square root",
            "বর্গমূল",
            "equation",
            "সমীকরণ",
                        "sequence", "ধারা", "combination", "permutation", "সমাবেশ", "বিন্যাস",
            "circle", "বৃত্ত", "triangle", "ত্রিভুজ", "rectangle", "আয়তক্ষেত্র", "আয়তক্ষেত্র",
        )
        return any(marker in lowered for marker in markers) or bool(re.search(r"\d\s*[+\-*/^%=]", lowered))

    @staticmethod
    def _normalize(text: str) -> str:
        replacements = {
            "×": "*",
            "÷": "/",
            "−": "-",
            "–": "-",
            "—": "-",
            "^": "**",
            "π": "pi",
            "শতাংশ": "%",
        }
        result = text.translate(_BN_DIGITS)
        for source, target in replacements.items():
            result = result.replace(source, target)
        return re.sub(r"\s+", " ", result).strip()

    def _extract_expression(self, text: str) -> str | None:
        candidate = text.lower()
        candidate = re.sub(r"^(please\s+)?(calculate|compute|evaluate|what is|equals)\s+", "", candidate)
        candidate = re.sub(r"^(হিসাব করো|হিসাব করুন|সমাধান করো|কত হয়|কত হয়)\s*", "", candidate)
        candidate = re.sub(r"\b(square root of|বর্গমূল(?:এর)?)\s+([0-9.]+)", r"sqrt(\2)", candidate)
        candidate = candidate.replace(" pi", " 3.141592653589793")
        candidate = re.sub(r"\bof\b", "*", candidate)
        candidate = candidate.replace("%", "/100")
        candidate = re.sub(r"[^0-9a-zA-Z_+*/().,\- ]", "", candidate).strip()
        return candidate if re.search(r"\d", candidate) else None

    def _evaluate(self, expression: str) -> int | float:
        tree = ast.parse(expression, mode="eval")

        def visit(node: ast.AST) -> int | float:
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if not math.isfinite(float(node.value)):
                    raise ValueError("non-finite number")
                return node.value
            if isinstance(node, ast.Name) and node.id == "pi":
                return math.pi
            if isinstance(node, ast.UnaryOp) and type(node.op) in self._unary:
                return self._unary[type(node.op)](visit(node.operand))
            if isinstance(node, ast.BinOp) and type(node.op) in self._binary:
                left, right = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Pow) and abs(float(right)) > 100:
                    raise ValueError("exponent too large")
                return self._binary[type(node.op)](left, right)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                function = self._functions.get(node.func.id)
                if function is None or node.keywords or len(node.args) not in (1, 2):
                    raise ValueError("invalid function")
                return function(*(visit(arg) for arg in node.args))
            raise ValueError("unsupported syntax")

        value = visit(tree.body)
        if not math.isfinite(float(value)):
            raise ArithmeticError("non-finite result")
        return value

    @staticmethod
    def _numeric_result(value: int | float, expression: str) -> MathResult:
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        exact = str(value)
        answer = f"{exact} (প্রায় {value:.10g})" if isinstance(value, float) else exact
        return MathResult(answer, exact, "arithmetic", (f"{expression} = {exact}",))

    def _parse_linear_equation(self, text: str) -> MathResult | None:
        match = re.search(
            r"(?:solve|সমাধান\s+করো|সমীকরণ)\s*:??\s*([0-9xX+*\-/(). ]+)\s*=\s*([0-9xX+*\-/(). ]+)",
            text,
            re.I,
        ) or re.fullmatch(r"\s*([0-9xX+*\-/(). ]+)\s*=\s*([0-9xX+*\-/(). ]+)\s*", text)
        if not match or "x" not in (match.group(1) + match.group(2)).lower():
            return None
        left, right = (match.group(1).replace(" ", ""), match.group(2).replace(" ", ""))

        def coefficients(side: str) -> tuple[float, float]:
            side = side.replace("-", "+-")
            coefficient, constant = 0.0, 0.0
            for term in side.split("+"):
                if not term:
                    continue
                if "x" in term.lower():
                    raw = term.lower().replace("x", "")
                    coefficient += -1.0 if raw == "-" else 1.0 if raw in ("", "+") else float(raw)
                else:
                    constant += float(term)
            return coefficient, constant

        try:
            left_a, left_b = coefficients(left)
            right_a, right_b = coefficients(right)
            denominator = left_a - right_a
            if abs(denominator) < 1e-12:
                return MathResult("No unique solution exists.", "undefined", "equation", confidence=0.7)
            value = (right_b - left_b) / denominator
        except (ValueError, ZeroDivisionError):
            return None
        return MathResult(
            f"x = {value:g}",
            f"x = {value:g}",
            "equation",
            (f"{left_a:g}x + ({left_b:g}) = {right_a:g}x + ({right_b:g})", f"x = {value:g}"),
        )

    def _parse_sequence(self, text: str) -> MathResult | None:
        match = re.search(
            r"(?:sequence|ধারা)\s*[:：]?\s*([0-9, .-]+)(?:.*?(?:next|পরের)\s*(\d+))?",
            text,
            re.I,
        )
        if not match:
            return None
        values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", match.group(1))]
        if len(values) < 2:
            return None
        count = int(match.group(2) or 1)
        ratio = values[-1] / values[-2] if values[-2] else None
        if ratio is not None and all(abs(values[i] * ratio - values[i + 1]) < 1e-9 for i in range(len(values) - 1)):
            next_values = [values[-1] * ratio**i for i in range(1, count + 1)]
            rule = f"geometric ratio = {ratio:g}"
        else:
            difference = values[-1] - values[-2]
            next_values = [values[-1] + difference * i for i in range(1, count + 1)]
            rule = f"arithmetic difference = {difference:g}"
        formatted = ", ".join(f"{value:g}" for value in next_values)
        return MathResult(formatted, formatted, "sequence", (rule,))

    def _parse_geometry(self, text: str) -> MathResult | None:
        numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", text)]
        lowered = text.lower()
        if ("circle" in lowered or "বৃত্ত" in text) and numbers:
            radius = numbers[0]
            area, circumference = math.pi * radius**2, 2 * math.pi * radius
            return MathResult(
                f"area = {area:.10g}, circumference = {circumference:.10g}",
                f"A=πr²={area:.10g}",
                "geometry",
                (f"r = {radius:g}", "A = πr²", "C = 2πr"),
            )
        if ("triangle" in lowered or "ত্রিভুজ" in text) and len(numbers) >= 2:
            area = numbers[0] * numbers[1] / 2
            return MathResult(f"area = {area:g}", f"A={area:g}", "geometry", ("A = ½ × base × height",))
        if ("rectangle" in lowered or "আয়তক্ষেত্র" in text or "আয়তক্ষেত্র" in text) and len(numbers) >= 2:
            area = numbers[0] * numbers[1]
            perimeter = 2 * sum(numbers[:2])
            return MathResult(
                f"area = {area:g}, perimeter = {perimeter:g}",
                f"A={area:g}, P={perimeter:g}",
                "geometry",
                ("A = length × width", "P = 2(length + width)"),
            )
        return None

    def _parse_statistics(self, text: str) -> MathResult | None:
        if not any(
            word in text.lower() for word in ("mean", "average", "median", "variance", "গড়", "গড়", "মধ্যক", "statistics")
        ):
            return None
        values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", text)]
        if not values:
            return None
        mean = statistics.fmean(values)
        median = statistics.median(values)
        mode = ", ".join(f"{value:g}" for value in statistics.multimode(values))
        variance = statistics.pvariance(values)
        answer = f"mean = {mean:g}, median = {median:g}, mode = {mode}, population variance = {variance:g}"
        return MathResult(
            answer, answer, "statistics", (f"sum = {sum(values):g}", f"n = {len(values)}", "mean = sum / n")
        )

    def _parse_combinatorics(self, text: str) -> MathResult | None:
        lowered = text.lower()
        numbers = [int(value) for value in re.findall(r"\d+", text)]
        if len(numbers) < 2 or not any(word in lowered for word in ("combination", "permutation", "সমাবেশ", "বিন্যাস")):
            return None
        n, r = numbers[:2]
        if r > n:
            return MathResult("r cannot be greater than n.", "undefined", "combinatorics", confidence=0.7)
        if "permutation" in lowered or "বিন্যাস" in text:
            value = math.factorial(n) // math.factorial(n - r)
            formula = "nPr = n! / (n-r)!"
        else:
            value = math.comb(n, r)
            formula = "nCr = n! / (r!(n-r)!)"
        return MathResult(str(value), str(value), "combinatorics", (formula,))


MATH_ENGINE = MathEngine()

MATHEMATICS_CONCEPTS = [
    {"name": name, "type": "Mathematics"}
    for name in (
        "Mathematics",
        "Arithmetic",
        "Algebra",
        "Geometry",
        "Trigonometry",
        "Calculus",
        "Probability",
        "Statistics",
        "Number Theory",
        "Linear Algebra",
        "Discrete Mathematics",
        "Mathematical Logic",
        "Set Theory",
        "Differential Equations",
        "Numerical Methods",
        "Combinatorics",
    )
]

MATHEMATICS_RELATIONS = [
    {"source": "Mathematics", "target": target, "type": "includes"}
    for target in (item["name"] for item in MATHEMATICS_CONCEPTS if item["name"] != "Mathematics")
]

MATHEMATICS_FACTS = [
    {"subject": "Mathematics", "predicate": "studies", "obj": "quantity, structure, space, and change"},
    {
        "subject": "Arithmetic",
        "predicate": "includes",
        "obj": "addition, subtraction, multiplication, division, fractions, ratios, and percentages",
    },
    {"subject": "Algebra", "predicate": "uses", "obj": "symbols, equations, functions, and variables"},
    {"subject": "Geometry", "predicate": "studies", "obj": "points, lines, angles, shapes, area, volume, and space"},
    {"subject": "Calculus", "predicate": "includes", "obj": "limits, derivatives, integrals, and infinite series"},
    {"subject": "Probability", "predicate": "measures", "obj": "uncertainty and likelihood"},
    {"subject": "Statistics", "predicate": "analyzes", "obj": "mean, median, mode, variance, and distributions"},
    {"subject": "Misty", "predicate": "has_capability", "obj": "deterministic mathematics solving without an LLM"},
]


def mathematics_package() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    return MATHEMATICS_CONCEPTS, MATHEMATICS_RELATIONS, MATHEMATICS_FACTS


__all__ = ["MATH_ENGINE", "MathEngine", "MathResult", "mathematics_package"]
