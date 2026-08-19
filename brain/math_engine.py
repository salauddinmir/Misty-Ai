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
_SUPERSCRIPT_DIGITS = str.maketrans(
    {
        "⁰": "**0",
        "¹": "**1",
        "²": "**2",
        "³": "**3",
        "⁴": "**4",
        "⁵": "**5",
        "⁶": "**6",
        "⁷": "**7",
        "⁸": "**8",
        "⁹": "**9",
    },
)


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
        # Drop trailing question clauses after a comma so that inputs like
        # "x² - 4 = 0, x = ?" stay a clean equation: "x² - 4 = 0".
        # Only strip when an "=" already appeared before the comma and the
        # clause after it also contains an "=" (a redundant trailing ask).
        comma_index = clean.find(",")
        after = clean[comma_index + 1 :] if comma_index != -1 else ""
        before = clean[:comma_index] if comma_index != -1 else ""
        if comma_index != -1 and "=" in before and "=" in after:
            clean = before.strip()

        for parser in (
            self._parse_combinatorics,
            self._parse_number_theory,
            self._parse_progression,
            self._parse_trigonometry,
            self._parse_statistics,
            self._parse_geometry,
            self._parse_quadratic_equation,
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
            "গ.সা.গু",
            "গসাগু",
            "ল.সা.গু",
            "লসাগু",
            "lcm",
            "gcd",
            "hcf",
            "degrees",
            "sin(",
            "cos(",
            "tan(",
            "hypotenuse",
            "গড়",
            "গড়",
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
            "degree", "term of ap", "term of gp", "ap starting", "gp starting", "অন্তর", "অনুপাত",
        )
        return any(marker in lowered for marker in markers) or bool(
            re.search(r"\d", lowered) and re.search(r"[+\-*/^%=]", lowered)
        )

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
        result = result.translate(_SUPERSCRIPT_DIGITS)
        for source, target in replacements.items():
            result = result.replace(source, target)
        # Convert caret notation (x^2) to Python power notation.
        result = re.sub(r"\^([0-9]+)", r"**\1", result)
        return re.sub(r"\s+", " ", result).strip()

    def _extract_expression(self, text: str) -> str | None:
        candidate = text.lower()
        candidate = re.sub(r"^(please\s+)?(calculate|compute|evaluate|what is|solve|equals)\s+", "", candidate)
        candidate = re.sub(r"\bএর\b", "*", candidate)
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

    def _parse_quadratic_equation(self, text: str) -> MathResult | None:
        """Solve quadratic equations like "x² - 4 = 0", "x^2 + 2x + 1 = 0".

        Supports Bengali and English phrasings with any digit script after
        normalization (Bengali digits and superscripts become ASCII). Both
        sides of the equation are moved to the left side and solved with
        the quadratic formula. Non-equation inputs (no "=") skip here so the
        linear/expression solvers keep their chance.
        """
        if "x" not in text.lower() or "=" not in text:
            return None
        # Equation marker: sides joined by "=" with x present and a squared
        # term on either side. The normalized "x**2" style is matched too.
        # Leading directive words like "solve the equation" are stripped so
        # inputs such as "solve x^2 - 5x + 6 = 0" parse correctly.
        text = re.sub(
            r"^(solve\s*(?:the\s*)?(?:equation\s*)?|equation\s*[:：]?\s*)", "", text, flags=re.I
        )
        match = re.match(r"^(.+)\s*=\s*(.+)$", text)
        if not match:
            return None
        left, right = match.group(1).strip(), match.group(2).strip()
        # Move the right side to the left: negate each of its terms, then
        # concatenate without introducing parenthesis artifacts that the
        # coefficient tokenizer cannot handle.
        right_terms = self._split_terms(right)
        negated_right = "".join(f"+{term.lstrip('+')}" for term in right_terms)
        combined = f"{left} {negated_right}"
        coefficients = self._polynomial_coefficients(combined)
        if coefficients is None:
            return None
        a, b, c = coefficients

        if abs(a) < 1e-12:
            # Degenerate linear equation; let the linear parser try it.
            return None

        discriminant = b * b - 4 * a * c
        steps: list[str] = [
            f"a = {a:g}, b = {b:g}, c = {c:g}",
            f"d = b² - 4ac = {discriminant:g}",
            "x = (-b ± √d) / 2a",
        ]
        if abs(discriminant) < 1e-12:
            root = -b / (2 * a)
            return MathResult(
                f"x = {root:g}",
                f"x = {root:g}",
                "quadratic_equation",
                (*tuple(steps), f"x = -b / 2a = {root:g}"),
            )
        if discriminant > 0:
            sqrt_d = math.sqrt(discriminant)
            root1 = (-b + sqrt_d) / (2 * a)
            root2 = (-b - sqrt_d) / (2 * a)
            roots = sorted((root1, root2), key=abs)
            formatted = ", ".join(f"x = {value:g}" for value in (roots[0], roots[1]))
            return MathResult(
                f"{formatted}",
                formatted,
                "quadratic_equation",
                (*tuple(steps), *tuple(f"x{idx} = {value:g}" for idx, value in enumerate((roots[0], roots[1]), 1))),
            )
        # Negative discriminant: no real solution (complex roots skipped on
        # purpose — the engine only claims what it can verify exactly).
        return MathResult(
            "এই সমীকরণের কোনো বাস্তব সমাধান নেই (ডিসক্রিমিন্যান্ট ঋণাত্মক)।",
            "no_real_solution",
            "quadratic_equation",
            (*tuple(steps), "d < 0 → no real roots"),
            confidence=0.7,
        )

    @staticmethod
    def _split_terms(expression: str) -> list[str]:
        """Split a polynomial-like string into signed terms without
        collapsing spaces ("- 5" must stay "- 5", not "-5")."""
        normalized = re.sub(r"\s+", "", expression)
        terms: list[str] = []
        for part in normalized.split("+"):
            if not part:
                continue
            sub_parts = re.split(r"(?<!\*)-(?=[0-9x])", part)
            first, rest = sub_parts[0], sub_parts[1:]
            if first:
                terms.append(first)
            terms.extend(f"-{piece}" for piece in rest if piece)
        return terms

    @staticmethod
    def _polynomial_coefficients(expression: str) -> tuple[float, float, float] | None:
        """Parse "ax²+bx+c"-style expressions (normalized to "x**2") into
        (a, b, c). Returns None if unsupported syntax is encountered."""
        terms = MathEngine._split_terms(expression)
        a, b, c = 0.0, 0.0, 0.0
        for term in terms:
            term = term.strip()
            lower = term.lower()
            if "x**2" in lower or "x²" in lower:
                coeff = term.split("x")[0].strip()
                if coeff in ("", "*"):
                    a += 1.0
                elif coeff == "-":
                    a -= 1.0
                else:
                    try:
                        a += float(coeff.rstrip("*"))
                    except ValueError:
                        return None
            elif "x" in lower:
                coeff = re.split(r"(?i)x", term)[0].strip()
                if coeff in ("", "*"):
                    b += 1.0
                elif coeff == "-":
                    b -= 1.0
                else:
                    try:
                        b += float(coeff.rstrip("*"))
                    except ValueError:
                        return None
            else:
                try:
                    c += float(term)
                except ValueError:
                    return None
        return a, b, c

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
            # Hypotenuse asked with two legs given: c = sqrt(a² + b²).
            # Hypotenuse check must run before the generic area rule.
            if "hypotenuse" in lowered or "অতিভুজ" in text or "অতিভুজ" in text:
                leg_a, leg_b = numbers[0], numbers[1]
                hypotenuse = math.sqrt(leg_a**2 + leg_b**2)
                formatted = f"{hypotenuse:.10g}"
                return MathResult(
                    formatted,
                    f"c=√(a²+b²)={formatted}",
                    "geometry",
                    (
                        f"a = {leg_a:g}",
                        f"b = {leg_b:g}",
                        "c² = a² + b² (Pythagorean theorem)",
                        f"c = √(a² + b²) = {formatted}",
                    ),
                )
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

    def _parse_trigonometry(self, text: str) -> MathResult | None:
        """Evaluate sin/cos/tan of an angle in degrees, e.g. "sin(30 degrees)",
        "cos(60°)", "tan(45)". Known angles use exact values; others use the
        math library with a reduced radian value."""
        match = re.search(r"\b(sin|cos|tan)\s*\(\s*(-?[0-9]+(?:\.[0-9]+)?)\s*(?:degrees?|°)?\s*\)", text, re.I)
        if not match:
            return None
        function, raw = match.group(1).lower(), float(match.group(2))
        degrees = raw % 360.0
        exact: dict[tuple[str, float], float] = {
            ("sin", 0.0): 0.0,
            ("sin", 30.0): 0.5,
            ("sin", 45.0): math.sqrt(2) / 2,
            ("sin", 60.0): math.sqrt(3) / 2,
            ("sin", 90.0): 1.0,
            ("cos", 0.0): 1.0,
            ("cos", 30.0): math.sqrt(3) / 2,
            ("cos", 45.0): math.sqrt(2) / 2,
            ("cos", 60.0): 0.5,
            ("cos", 90.0): 0.0,
            ("tan", 0.0): 0.0,
            ("tan", 45.0): 1.0,
        }
        key = (function, degrees)
        if key in exact:
            value = exact[key]
            steps: tuple[str, ...] = (
                "angle converted to radians for evaluation",
                f"{function}({degrees:g}°) evaluated",
            )
        elif function == "tan" and degrees in (90.0, 270.0):
            return MathResult("tan(90°) is undefined (division by zero).", "undefined", "trigonometry", confidence=0.7)
        else:
            try:
                value = self._functions[function](math.radians(raw))
                steps = (f"angle = {raw:g}°", f"radians = {math.radians(raw):.6g}",)
            except (ArithmeticError, ValueError):
                return None
        if not math.isfinite(value):
            return None
        formatted = f"{value:.10g}"
        return MathResult(formatted, f"{function}({raw:g}°) = {formatted}", "trigonometry", steps)

    def _parse_progression(self, text: str) -> MathResult | None:
        """Find the n-th term of an arithmetic or geometric progression, e.g.
        "10th term of AP starting 3 with difference 4", "5th term of GP
        starting 2 with ratio 3"."""
        lowered = text.lower()
        is_ap = any(marker in lowered for marker in ("ap", "arithmetic", "সাধারণ অন্তর", "অন্তর"))
        is_gp = any(marker in lowered for marker in ("gp", "geometric", "সাধারণ অনুপাত", "অনুপাত"))
        if not (is_ap or is_gp):
            return None
        numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", text)]
        if len(numbers) < 3:
            return None
        ordinal = numbers[0]
        first, step = numbers[1], numbers[2]
        n = int(ordinal)
        if n < 1 or n > 10000:
            return None
        if is_gp:
            value = first * step ** (n - 1)
            formula = f"a_n = a × r^(n-1) = {first:g} × {step:g}^{n - 1:g}"
            category = "geometric_progression"
        else:
            value = first + step * (n - 1)
            formula = f"a_n = a + (n-1)d = {first:g} + {n - 1:g} × {step:g}"
            category = "arithmetic_progression"
        return MathResult(f"{value:g}", f"{value:g}", category, (formula, f"n = {n}"))

    def _parse_number_theory(self, text: str) -> MathResult | None:
        """Solve LCM/GCD requests in English and Bengali, e.g. "lcm of 12 and
        18", "গ.সা.গু 48 ও 36", "ল.সা.গু. 15 ও 20 কত"."""
        lowered = text.lower()
        numbers = [int(value) for value in re.findall(r"\d+", text)]
        has_lcm = any(marker in lowered for marker in ("lcm", "ল.সা.গু", "লসাগু", "ল.সা.গু."))
        has_gcd = any(marker in lowered for marker in ("gcd", "hcf", "গ.সা.গু", "গসাগু", "গ.সা.গু."))
        if not (has_lcm or has_gcd) or len(numbers) < 2:
            return None
        if any(value <= 0 for value in numbers):
            return MathResult(
                "LCM/GCD are defined for positive integers only.",
                "undefined",
                "number_theory",
                confidence=0.7,
            )
        a, b = numbers[0], numbers[1]
        gcd = math.gcd(a, b)
        lcm = a * b // gcd
        if has_gcd or (has_gcd and has_lcm):
            return MathResult(
                f"GCD = {gcd:g}",
                f"gcd({a}, {b}) = {gcd:g}",
                "number_theory",
                ("Euclidean algorithm: gcd(a, b) = gcd(b, a mod b)", f"gcd({a}, {b}) = {gcd:g}"),
            )
        return MathResult(
            f"LCM = {lcm:g}",
            f"lcm({a}, {b}) = {lcm:g}",
            "number_theory",
            ("lcm(a, b) = a × b ÷ gcd(a, b)", f"gcd({a}, {b}) = {gcd:g}", f"lcm({a}, {b}) = {lcm:g}"),
        )


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
