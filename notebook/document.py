"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
import ast
import re
from functools import cached_property
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING
from uuid import uuid4
import copy
import json
import os
from time import perf_counter

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_equals_signs,
    parse_expr,
    standard_transformations,
)

from notebook.units import math_env

if TYPE_CHECKING:  # Avoid runtime import cycles with the renderer
    from notebook.renderer import NotebookRenderer


@dataclass
class SymbolRegistry(dict):
    """Dictionary that lazily creates SymPy symbols on demand."""

    def __missing__(self, key: str) -> sp.Symbol:
        # Special handling for array functions - always create as Functions
        if key in ("linspace", "arange"):
            func = sp.Function(key)
            self[key] = func
            return func
        symbol = sp.Symbol(key)
        self[key] = symbol
        return symbol


@dataclass
class VariableRecord:
    """Stores the evaluation details for a single variable."""

    name: str
    expression: str
    numeric_value: Optional[float] = None


@dataclass
class FunctionRecord:
    """Stores a user-defined function."""

    name: str
    parameters: list[str]
    expression: str
    sympy_lambda: Optional[callable] = None


@dataclass
class ArrayRecord:
    """Stores an array of numeric values."""

    name: str
    values: list[float]
    expression: str


@dataclass
class EvaluationContext:
    """Context manager that keeps symbol and numeric value registries."""

    symbols: SymbolRegistry = field(default_factory=SymbolRegistry)
    numeric_values: dict[str, float] = field(default_factory=dict)
    functions: dict[str, FunctionRecord] = field(default_factory=dict)
    arrays: dict[str, ArrayRecord] = field(default_factory=dict)
    variables: list[VariableRecord] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)

    def __enter__(self) -> "EvaluationContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def register_variable(
        self,
        name: str,
        expression: str,
        numeric_value: Optional[float],
    ) -> None:
        """Add a variable evaluation record and persist its numeric value."""

        _ = self.symbols[name]
        if numeric_value is not None:
            self.numeric_values[name] = numeric_value
        self.variables.append(
            VariableRecord(
                name=name,
                expression=expression,
                numeric_value=numeric_value,
            )
        )

    def register_function(
        self,
        name: str,
        parameters: list[str],
        expression: str,
        sympy_lambda: Optional[callable] = None,
    ) -> None:
        """Register a user-defined function."""

        self.functions[name] = FunctionRecord(
            name=name,
            parameters=parameters,
            expression=expression,
            sympy_lambda=sympy_lambda,
        )

    def register_array(
        self,
        name: str,
        values: list[float],
        expression: str,
    ) -> None:
        """Register an array of values."""

        self.arrays[name] = ArrayRecord(
            name=name,
            values=values,
            expression=expression,
        )

    def register_error(self, *, block_id: str, message: str, error_type: str) -> None:
        """Store evaluation errors so the renderer can surface them."""

        self.errors.append({"block_id": block_id, "message": message, "type": error_type})

    def log_run(
        self,
        *,
        block_id: str,
        expression: str,
        duration_ms: float,
        substitutions: list[str],
    ) -> None:
        """Persist a lightweight evaluation log entry."""

        self.logs.append(
            {
                "block_id": block_id,
                "expression": expression,
                "duration_ms": round(duration_ms, 2),
                "substitutions": substitutions,
            }
        )


@dataclass
class NotebookOptions:
    """User-tunable settings that influence evaluation and formatting."""

    hide_logs: bool = False


@dataclass
class Block:
    """Base class for notebook blocks."""

    raw: str
    block_id: str = field(default_factory=lambda: uuid4().hex)

    def to_html(self) -> str:
        """Render the block as HTML (implemented by subclasses)."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Serialize block metadata for persistence."""

        return {"type": self.__class__.__name__, "raw": self.raw, "id": self.block_id}

    @classmethod
    def from_dict(cls, payload: dict) -> "Block":
        """Recreate a block instance from serialized data."""

        block_type = payload.get("type", "TextBlock")
        common_kwargs = {"raw": payload.get("raw", ""), "block_id": payload.get("id", uuid4().hex)}
        if block_type == "FormulaBlock":
            return FormulaBlock(
                **common_kwargs,
                result=payload.get("result"),
                latex=payload.get("latex"),
                numeric_value=payload.get("numeric_value"),
                is_assignment=payload.get("is_assignment", False),
                variable_name=payload.get("variable_name"),
            )
        return TextBlock(**common_kwargs)


@dataclass
class TextBlock(Block):
    """Text block that stores explanatory content."""

    def to_html(self) -> str:
        rendered = self._markdown.render(self.raw)
        sanitized = html.escape(self.raw) if not rendered else self._sanitize(rendered)
        return (
            f"<div class='text-block' id='block-{self.block_id}' data-block-id='{self.block_id}'>"
            f"{sanitized}"
            "</div>"
        )

    @cached_property
    def _markdown(self):
        try:
            from markdown_it import MarkdownIt

            return MarkdownIt("commonmark", {"html": False, "linkify": True})
        except ModuleNotFoundError:
            # Lightweight fallback that supports headings, lists, and inline code
            class _FallbackMarkdown:
                def render(self_inner, text: str) -> str:
                    lines = []
                    in_list = False
                    for raw_line in text.splitlines():
                        line = raw_line.rstrip()
                        if line.startswith("# "):
                            if in_list:
                                lines.append("</ul>")
                                in_list = False
                            lines.append(f"<h1>{html.escape(line[2:].strip(), quote=False)}</h1>")
                            continue
                        if line.startswith("- "):
                            if not in_list:
                                lines.append("<ul>")
                                in_list = True
                            content = html.escape(line[2:].strip(), quote=False)
                            content = re.sub(r"`([^`]+)`", r"<code>\1</code>", content)
                            lines.append(f"<li>{content}</li>")
                            continue
                        if in_list:
                            lines.append("</ul>")
                            in_list = False
                        if line.strip():
                            content = html.escape(line.strip(), quote=False)
                            content = re.sub(r"`([^`]+)`", r"<code>\1</code>", content)
                            lines.append(f"<p>{content}</p>")
                    if in_list:
                        lines.append("</ul>")
                    return "".join(lines)

            return _FallbackMarkdown()

    @staticmethod
    def _sanitize(html_content: str) -> str:
        try:
            import bleach

            allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union(
                {"p", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "strong", "em"}
            )
            allowed_attrs = {
                **bleach.sanitizer.ALLOWED_ATTRIBUTES,
                "a": ["href", "title", "rel"],
                "code": ["class"],
                "span": ["class"],
            }
            return bleach.clean(
                html_content,
                tags=allowed_tags,
                attributes=allowed_attrs,
                protocols=["http", "https", "mailto"],
                strip=True,
            )
        except ModuleNotFoundError:
            # Fallback to already-escaped content when bleach is unavailable
            return html_content.replace("javascript:", "")


@dataclass
class FormulaBlock(Block):
    """Math expression block evaluated with SymPy."""

    sympy_expr: Optional[sp.Expr] = None
    result: Optional[str] = None
    latex: Optional[str] = None
    numeric_value: Optional[float] = None
    is_assignment: bool = False
    variable_name: Optional[str] = None
    is_function_def: bool = False
    function_name: Optional[str] = None
    function_params: Optional[list[str]] = None
    is_array: bool = False
    array_values: Optional[list[float]] = None
    evaluation_status: str = "ok"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    evaluation_time_ms: Optional[float] = None

    @staticmethod
    def _parse_function_definition(lhs: str) -> Optional[tuple[str, list[str]]]:
        """Detect function definition syntax: f(x, y) and return (name, [params])."""

        # Match pattern: function_name(param1, param2, ...)
        pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*([^)]*)\s*\)$'
        match = re.match(pattern, lhs.strip())

        if not match:
            return None

        func_name = match.group(1)
        params_str = match.group(2).strip()

        if not params_str:
            return None  # Function must have at least one parameter

        # Parse parameters
        params = [p.strip() for p in params_str.split(',') if p.strip()]

        if not params:
            return None

        # Validate parameter names
        for param in params:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param):
                return None

        return func_name, params

    def _parse_assignment(self, rhs: str, context: EvaluationContext) -> sp.Expr:
        """Parse the right-hand side of an assignment."""

        rhs = rhs.strip()

        # Detect numeric literal
        try:
            value = float(rhs)
            return sp.Float(value)
        except ValueError:
            pass

        # Fall back to generic SymPy parsing
        try:
            return self._safe_sympify(rhs, context)
        except Exception:  # pylint: disable=broad-except
            return None

    @staticmethod
    def _parse_conditional_expr(expression: str, context: EvaluationContext) -> Optional[sp.Expr]:
        """Convert Python conditionals (inline or multi-line) into ``Piecewise``."""

        try:
            tree = ast.parse(expression)
        except SyntaxError:
            return None

        def _convert_expr(node: ast.AST) -> sp.Expr:
            if isinstance(node, ast.IfExp):
                test = _convert_expr(node.test)
                body = _convert_expr(node.body)
                orelse = _convert_expr(node.orelse)
                return sp.Piecewise((body, test), (orelse, True))

            if isinstance(node, ast.Compare):
                left = _convert_expr(node.left)
                comparators = [_convert_expr(comp) for comp in node.comparators]
                ops = node.ops
                relations: list[sp.Expr] = []
                current_left = left
                for op, comparator in zip(ops, comparators):
                    if isinstance(op, ast.Gt):
                        relations.append(sp.Gt(current_left, comparator))
                    elif isinstance(op, ast.GtE):
                        relations.append(sp.Ge(current_left, comparator))
                    elif isinstance(op, ast.Lt):
                        relations.append(sp.Lt(current_left, comparator))
                    elif isinstance(op, ast.LtE):
                        relations.append(sp.Le(current_left, comparator))
                    elif isinstance(op, ast.Eq):
                        relations.append(sp.Eq(current_left, comparator))
                    elif isinstance(op, ast.NotEq):
                        relations.append(sp.Ne(current_left, comparator))
                    else:
                        return None
                    current_left = comparator

                if not relations:
                    return None
                if len(relations) == 1:
                    return relations[0]
                return sp.And(*relations)

            src = ast.get_source_segment(expression, node) or ast.unparse(node)
            normalized = FormulaBlock._normalize_expression(src)
            return FormulaBlock._safe_sympify(normalized, context, allow_conditional=False)

        def _extract_branch_expr(body_nodes: list[ast.stmt]) -> Optional[sp.Expr]:
            if len(body_nodes) != 1 or not isinstance(body_nodes[0], ast.Expr):
                return None
            return _convert_expr(body_nodes[0].value)

        if len(tree.body) != 1:
            return None

        first_stmt = tree.body[0]
        if isinstance(first_stmt, ast.Expr):
            if isinstance(first_stmt.value, ast.IfExp):
                return _convert_expr(first_stmt.value)
            return None

        if not isinstance(first_stmt, ast.If):
            return None

        branches = []
        current = first_stmt
        while True:
            body_expr = _extract_branch_expr(current.body)
            if body_expr is None:
                return None
            test_expr = _convert_expr(current.test)
            branches.append((body_expr, test_expr))

            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                current = current.orelse[0]
                continue

            if current.orelse:
                orelse_expr = _extract_branch_expr(current.orelse)
                if orelse_expr is None:
                    return None
                branches.append((orelse_expr, True))
            else:
                branches.append((sp.nan, True))
            break

        return sp.Piecewise(*branches)

    @staticmethod
    def _safe_sympify(expression: str, context: EvaluationContext, *, allow_conditional: bool = True) -> sp.Expr:
        """Sympify while avoiding accidental symbol injection for numeric-only inputs."""

        expr = expression.strip()

        if allow_conditional:
            piecewise_expr = FormulaBlock._parse_conditional_expr(expr, context)
            if piecewise_expr is not None:
                return piecewise_expr

        expr = FormulaBlock._normalize_expression(expr)
        if re.search(r"[A-Za-z]", expr):
            # Prefer SymPy math helpers so names like ``sqrt`` resolve to functions,
            # while still letting the SymbolRegistry lazily create new symbols.
            safe_locals = {
                "sqrt": sp.sqrt,
                "sin": sp.sin,
                "cos": sp.cos,
                "tan": sp.tan,
                "log": sp.log,
                "exp": sp.exp,
                "pi": sp.pi,
                "E": sp.E,
                "Integer": sp.Integer,
                "Float": sp.Float,
                "Rational": sp.Rational,
                "Symbol": sp.Symbol,
                "abs": sp.Abs,
                "sum": sp.Function("sum"),
                "min": sp.Function("min"),
                "max": sp.Function("max"),
                "range": sp.Function("range"),
                "linspace": sp.Function("linspace"),
                "arange": sp.Function("arange"),
                "sweep": sp.Function("sweep"),
                "And": sp.And,
                "Or": sp.Or,
                "Not": sp.Not,
            }
            for name, obj in safe_locals.items():
                context.symbols.setdefault(name, obj)
            # Add user-defined functions as undefined functions for sympy parsing
            for func_name in context.functions.keys():
                if func_name not in context.symbols:
                    context.symbols[func_name] = sp.Function(func_name)

            # Always ensure linspace and arange are Functions (create fresh objects)
            linspace_func = type('linspace', (sp.Function,), {})
            arange_func = type('arange', (sp.Function,), {})
            sweep_func = type('sweep', (sp.Function,), {})
            sum_func = type('sum', (sp.Function,), {})
            min_func = type('min', (sp.Function,), {})
            max_func = type('max', (sp.Function,), {})
            range_func = type('range', (sp.Function,), {})
            context.symbols["linspace"] = linspace_func
            context.symbols["arange"] = arange_func
            context.symbols["sweep"] = sweep_func
            context.symbols["sum"] = sum_func
            context.symbols["min"] = min_func
            context.symbols["max"] = max_func
            context.symbols["range"] = range_func

            return parse_expr(
                expr,
                local_dict=context.symbols,
                transformations=standard_transformations + (convert_equals_signs,),
            )
        return parse_expr(
            expr,
            transformations=standard_transformations + (convert_equals_signs,),
        )

    @staticmethod
    def _normalize_expression(expression: str) -> str:
        """Insert explicit multiplication between digits/closing parens and symbols/funcs."""

        # Turn "3sqrt(3)" into "3*sqrt(3)"
        expr = re.sub(r"(?<=\d)(?=[A-Za-z\(])", "*", expression)
        # Turn ")(" into ")*(" for implicit multiplication of parenthesized factors.
        expr = expr.replace(")(", ")*(")
        return expr

    def _evaluate_numeric(self, expression: str, context: EvaluationContext):
        """Evaluate the expression using numeric substitution."""

        env = {}
        env.update(math_env())
        # Add user-defined functions
        for func_name, func_record in context.functions.items():
            if func_record.sympy_lambda:
                env[func_name] = func_record.sympy_lambda
        # Fallback to numeric-only substitutions for symbols.
        for name, value in context.numeric_values.items():
            env.setdefault(name, value)
        # Also expose arrays as plain lists so helpers como sweep/len trabajen.
        for name, arr in context.arrays.items():
            env.setdefault(name, arr.values)

        # Normalize caret to python exponent for eval friendliness.
        expr = self._normalize_expression(expression).replace("^", "**")
        try:
            return eval(expr, {"__builtins__": {}}, env), None  # pylint: disable=eval-used
        except SyntaxError:
            try:
                sym_expr = self._safe_sympify(expression, context)
                substituted = sym_expr.subs(context.numeric_values)
                numeric = sp.N(substituted)
                return numeric, None
            except Exception as exc3:  # pylint: disable=broad-except
                return None, exc3
        except NameError as exc:
            # Retry once injecting all known numbers explicitly.
            for name, value in context.numeric_values.items():
                env[name] = value
            try:
                return eval(expr, {"__builtins__": {}}, env), None  # pylint: disable=eval-used
            except Exception as exc2:  # pylint: disable=broad-except
                # Last fallback: try SymPy numeric evaluation with substitutions
                try:
                    sym_expr = self._safe_sympify(expression, context)
                    substituted = sym_expr.subs(context.numeric_values)
                    numeric = sp.N(substituted)
                    return numeric, None
                except Exception as exc3:  # pylint: disable=broad-except
                    return None, exc3
        except Exception as exc:
            return None, exc

    @staticmethod
    def _format_numeric_value(value: float) -> str:
        """Format numeric values consistently for display."""

        return f"{value:.2f}"

    @staticmethod
    def _cleanup_latex(latex_expr: str) -> str:
        """Tidy up common artifacts in LaTeX output."""

        # Remove redundant leading "1 " before a fraction (e.g., "1 \\frac{1}{...}")
        latex_expr = re.sub(r"^1\s*(\\frac)", r"\\frac", latex_expr)
        # Normalize \cdot spacing
        latex_expr = latex_expr.replace("\\cdot", "\\cdot ")
        latex_expr = re.sub(r"^1\s*\\cdot\s*", "", latex_expr)
        latex_expr = re.sub(r"\s{2,}", " ", latex_expr)
        latex_expr = latex_expr.strip()
        return latex_expr

    def _lhs_latex(self, name: str) -> str:
        """Render a left-hand-side name with safe LaTeX (handles underscores as subscripts)."""

        try:
            symbol = sp.Symbol(name)
            return self._cleanup_latex(sp.latex(symbol, order="none", mul_symbol=" \\cdot "))
        except Exception:
            return html.escape(name)

    def _ensure_sympy_expr(self, expression: str, context: EvaluationContext) -> None:
        """Guarantee a sympy_expr for rendering."""

        if self.sympy_expr is not None:
            return
        try:
            self.sympy_expr = self._safe_sympify(expression, context)
            return
        except Exception as exc:
            last_exc = exc
        try:
            # Try a non-evaluating sympify with a sanitized locals dict (no SymbolRegistry side effects).
            locals_env = dict(context.symbols)
            locals_env.update(
                {
                    "Symbol": sp.Symbol,
                    "Integer": sp.Integer,
                    "Float": sp.Float,
                    "Rational": sp.Rational,
                }
            )
            self.sympy_expr = sp.sympify(expression, locals=locals_env, evaluate=False)
            return
        except Exception as exc:  # pylint: disable=broad-except
            last_exc = exc
        try:
            # Last resort: parse without locals just to get LaTeX for render.
            self.sympy_expr = parse_expr(
                self._normalize_expression(expression),
                transformations=standard_transformations + (convert_equals_signs,),
            )
            return
        except Exception as exc:  # pylint: disable=broad-except
            self.sympy_expr = None
            context.register_error(
                block_id=self.block_id,
                message=f"Render parse failed for '{expression}': {exc or last_exc}",
                error_type="ParseWarning",
            )

    def _handle_evaluation_error(
        self,
        exc: Exception,
        context: EvaluationContext,
        expr_latex: str,
        lhs: str | None = None,
    ) -> None:
        """Persist evaluation errors for downstream display."""

        self.result = f"Error evaluating: {exc}"
        self.evaluation_status = "error"
        self.error_type = type(exc).__name__
        self.error_message = str(exc)
        lhs_latex = self._lhs_latex(lhs) if lhs else None
        if lhs:
            self.latex = f"{lhs_latex} = {expr_latex}"
            context.register_variable(lhs, expr_latex, None)
        else:
            self.latex = expr_latex
        context.register_error(
            block_id=self.block_id,
            message=self.error_message,
            error_type=self.error_type,
        )

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "result": self.result,
                "latex": self.latex,
                "numeric_value": self.numeric_value,
                "is_assignment": self.is_assignment,
                "variable_name": self.variable_name,
            }
        )
        return base

    def evaluate(
        self,
        context: Optional[EvaluationContext] = None,
        options: Optional[NotebookOptions] = None,
    ) -> None:
        """Parse and evaluate the expression using SymPy."""

        context = context or EvaluationContext()
        options = options or NotebookOptions()
        start_time = perf_counter()
        self.is_assignment = False
        self.variable_name = None
        self.numeric_value = None
        self.evaluation_status = "ok"
        self.error_type = None
        self.error_message = None
        self.evaluation_time_ms = None

        raw = self.raw.strip()
        assignment_match = re.search(r"(?<![<>=!])=(?![=])", raw)
        try:
            if assignment_match:
                lhs = raw[: assignment_match.start()].strip()
                rhs = raw[assignment_match.end() :].strip()
                lhs = lhs.strip()
                rhs = rhs.strip()
                if lhs:
                    # Check if this is a function definition
                    func_def = self._parse_function_definition(lhs)
                    if func_def:
                        func_name, params = func_def
                        self.is_function_def = True
                        self.function_name = func_name
                        self.function_params = params

                        try:
                            # Create sympy symbols for parameters
                            param_symbols = [sp.Symbol(p) for p in params]

                            # Parse RHS with parameter symbols in context
                            temp_context = copy.copy(context)
                            for param in params:
                                temp_context.symbols[param] = sp.Symbol(param)

                            func_expr = self._safe_sympify(rhs, temp_context)
                            self.sympy_expr = func_expr
                            func_expr_for_lambda = func_expr.subs(context.numeric_values)

                            # Create sympy lambda function
                            # Use math module instead of numpy, and capture current numeric values + prior user lambdas
                            lambda_env = math_env()
                            lambda_env.update(context.numeric_values)
                            for existing in context.functions.values():
                                if existing.sympy_lambda:
                                    lambda_env[existing.name] = existing.sympy_lambda
                            sympy_lambda = sp.lambdify(param_symbols, func_expr_for_lambda, modules=[lambda_env, "math"])

                            # Register function
                            context.register_function(func_name, params, rhs, sympy_lambda)

                            # Format result
                            params_str = ", ".join(params)
                            self.result = f"Function {func_name}({params_str}) defined"

                            # Generate LaTeX
                            func_name_latex = self._lhs_latex(func_name)
                            params_latex = ", ".join(self._lhs_latex(param) for param in params)
                            func_expr_latex = sp.latex(func_expr, order="none", mul_symbol=" \\cdot ")
                            func_expr_latex = self._cleanup_latex(func_expr_latex)
                            self.latex = f"{func_name_latex}({params_latex}) = {func_expr_latex}"

                            return
                        except Exception as exc:
                            self.result = f"Error defining function: {exc}"
                            self.evaluation_status = "error"
                            self.error_type = type(exc).__name__
                            self.error_message = str(exc)
                            self.latex = f"{self._lhs_latex(lhs)} = {html.escape(rhs)}"
                            context.register_error(
                                block_id=self.block_id,
                                message=self.error_message,
                                error_type=self.error_type,
                            )
                            return

                    # Regular assignment
                    self.is_assignment = True
                    self.variable_name = lhs
                    self.sympy_expr = self._parse_assignment(rhs, context)

                    # Try numeric evaluation
                    numeric_value, numeric_error = self._evaluate_numeric(rhs, context)
                    if numeric_error is not None:
                        expr_latex = (
                            sp.latex(self.sympy_expr, order="none") if self.sympy_expr is not None else html.escape(rhs)
                        )
                        self._handle_evaluation_error(numeric_error, context, expr_latex, lhs)
                        return

                    # Check if result is an array
                    if isinstance(numeric_value, list):
                        self.is_array = True
                        self.array_values = [float(v) for v in numeric_value]
                        context.register_array(lhs, self.array_values, rhs)
                        if len(self.array_values) <= 5:
                            self.result = f"Array: [{', '.join(f'{v:.2f}' for v in self.array_values)}]"
                        else:
                            first_three = ', '.join(f'{v:.2f}' for v in self.array_values[:3])
                            self.result = f"Array ({len(self.array_values)} values): [{first_three}, ...]"
                    # Check if result is numeric
                    elif isinstance(numeric_value, (int, float)):
                        self.numeric_value = float(numeric_value)
                        self.result = self._format_numeric_value(self.numeric_value)
                    elif hasattr(numeric_value, 'is_real') and numeric_value.is_real:
                        try:
                            self.numeric_value = float(numeric_value)
                            self.result = self._format_numeric_value(self.numeric_value)
                        except (TypeError, ValueError):
                            self.result = str(numeric_value)
                    else:
                        # Try substitution with sympy
                        substitution = self.sympy_expr.subs(context.numeric_values)
                        evaluated = sp.N(substitution)
                        if evaluated.is_real:
                            try:
                                self.numeric_value = float(evaluated)
                                self.result = self._format_numeric_value(self.numeric_value)
                            except (TypeError, ValueError):
                                self.numeric_value = None
                                self.result = str(evaluated)
                        else:
                            self.result = str(evaluated)

                    expr_latex = (
                        sp.latex(self.sympy_expr, order="none", mul_symbol=" \\cdot ")
                        if self.sympy_expr is not None
                        else html.escape(rhs)
                    )
                    expr_latex = self._cleanup_latex(expr_latex)
                    self.latex = f"{self._lhs_latex(lhs)} = {expr_latex}"
                    context.register_variable(lhs, expr_latex, self.numeric_value)
                    return

            # Regular expression (non-assignment)
            self.sympy_expr = self._safe_sympify(raw, context)
            numeric_value, numeric_error = self._evaluate_numeric(raw, context)
            if numeric_error is not None:
                self.result = f"Error evaluating: {numeric_error}"
                self.evaluation_status = "error"
                self.error_type = type(numeric_error).__name__
                self.error_message = str(numeric_error)
                self.latex = sp.latex(self.sympy_expr, order="none")
                context.register_error(
                    block_id=self.block_id,
                    message=self.error_message,
                    error_type=self.error_type,
                )
                return

            # Check if result is numeric
            if isinstance(numeric_value, (int, float)):
                self.numeric_value = float(numeric_value)
                self.result = self._format_numeric_value(self.numeric_value)
            elif hasattr(numeric_value, 'is_real') and numeric_value.is_real:
                try:
                    self.numeric_value = float(numeric_value)
                    self.result = self._format_numeric_value(self.numeric_value)
                except (TypeError, ValueError):
                    self.result = str(numeric_value)
                    self._ensure_sympy_expr(raw, context)
            else:
                substitution = self.sympy_expr.subs(context.numeric_values)
                evaluated = sp.N(substitution)
                self.result = str(evaluated)
                if evaluated.is_real:
                    try:
                        self.numeric_value = float(evaluated)
                    except (TypeError, ValueError):
                        self.numeric_value = None
            self.latex = sp.latex(self.sympy_expr, order="none", mul_symbol=" \\cdot ")
            self.latex = self._cleanup_latex(self.latex)
        except Exception as exc:  # pylint: disable=broad-except
            # Keep evaluation errors but continue showing them in the UI.
            self.sympy_expr = None
            self.result = f"Error: {exc}"
            self.latex = None
            self.evaluation_status = "error"
            self.error_type = type(exc).__name__
            self.error_message = str(exc)
            context.register_error(block_id=self.block_id, message=self.error_message, error_type=self.error_type)
        finally:
            duration_ms = (perf_counter() - start_time) * 1000
            self.evaluation_time_ms = round(duration_ms, 2)
            substitutions: list[str] = []
            if self.sympy_expr is not None and hasattr(self.sympy_expr, "free_symbols"):
                symbol_names = {str(symbol) for symbol in self.sympy_expr.free_symbols}
                for name in sorted(symbol_names):
                    if name in context.numeric_values:
                        substitutions.append(f"{name}={context.numeric_values[name]:.2f}")
            context.log_run(
                block_id=self.block_id,
                expression=raw,
                duration_ms=duration_ms,
                substitutions=substitutions,
            )

    def to_html(self) -> str:
        if self.sympy_expr is None or (self.latex is None and self.result is None):
            self.evaluate()

        latex_expr = self.latex or html.escape(self.raw)
        status_class = " error" if self.evaluation_status == "error" else ""
        result_html = f"<div class='formula-result'>= {html.escape(self.result or '')}</div>"
        return (
            f"<div class='formula-block{status_class}' id='block-{self.block_id}' data-block-id='{self.block_id}'>"
            f"<div class='formula-input'>$$ {latex_expr} $$</div>"
            f"{result_html}"
            "</div>"
        )


@dataclass
class Document:
    """Ordered collection of blocks representing a notebook."""

    blocks: List[Block] = field(default_factory=list)
    _undo_stack: list[list[Block]] = field(default_factory=list, init=False, repr=False)
    _redo_stack: list[list[Block]] = field(default_factory=list, init=False, repr=False)

    HISTORY_LIMIT = 20

    def evaluate(self, options: Optional[NotebookOptions] = None) -> EvaluationContext:
        """Evaluate all formula blocks within a shared context."""

        with EvaluationContext() as context:
            for block in self.blocks:
                if isinstance(block, FormulaBlock):
                    block.evaluate(context, options)
            return context

    def add_block(self, block: Block) -> None:
        """Append a new block to the document."""

        self._push_history()
        self.blocks.append(block)
        self._redo_stack.clear()

    def to_html(
        self,
        renderer: Optional["NotebookRenderer"] = None,
        *,
        mathjax_path: str | None = None,
        mathjax_url: str | None = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        options: Optional[NotebookOptions] = None,
    ) -> str:
        """Create an HTML preview using the provided renderer."""

        renderer = renderer or self._default_renderer()
        return renderer.render(
            self,
            mathjax_path=mathjax_path,
            mathjax_url=mathjax_url,
            options=options,
        )

    def save_html(
        self,
        path: str,
        renderer: Optional["NotebookRenderer"] = None,
        *,
        mathjax_path: str | None = None,
        mathjax_url: str | None = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        options: Optional[NotebookOptions] = None,
    ) -> None:
        """Render the document to HTML and persist it to disk."""

        html_content = self.to_html(
            renderer=renderer,
            mathjax_path=mathjax_path,
            mathjax_url=mathjax_url,
            options=options,
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(html_content)

    def to_markdown(self) -> str:
        """Serialize the notebook to Markdown with LaTeX formulas and variables."""

        context = self.evaluate()
        lines: list[str] = []

        for block in self.blocks:
            if isinstance(block, TextBlock):
                lines.append(block.raw.strip())
            elif isinstance(block, FormulaBlock):
                if block.latex is None:
                    block.evaluate(context)
                latex_expr = block.latex or html.escape(block.raw)
                lines.append(f"$$ {latex_expr} $$")
                if block.result:
                    lines.append(f"Resultado: {block.result}")

        if context.variables:
            lines.append("\n## Variables")
            lines.append("| Name | Expression | Value |")
            lines.append("| --- | --- | --- |")
            for variable in context.variables:
                expression = variable.expression
                value = "" if variable.numeric_value is None else f"{variable.numeric_value:.2f}"
                lines.append(
                    f"| {variable.name} | $$ {expression} $$ | {value} |"
                )

        return "\n".join(line for line in lines if line is not None)

    def save_markdown(self, path: str) -> None:
        """Persist the Markdown export to disk."""

        markdown = self.to_markdown()
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(markdown)

    @staticmethod
    def _default_renderer() -> "NotebookRenderer":
        """Lazy import to avoid circular dependency when rendering."""

        from notebook.renderer import NotebookRenderer

        return NotebookRenderer()

    # Editing helpers
    def move_block(self, from_idx: int, to_idx: int) -> bool:
        """Move a block to a new index while maintaining history."""

        if not (0 <= from_idx < len(self.blocks)):
            return False
        to_idx = max(0, min(len(self.blocks) - 1, to_idx))
        if from_idx == to_idx:
            return False

        self._push_history()
        block = self.blocks.pop(from_idx)
        self.blocks.insert(to_idx, block)
        self._redo_stack.clear()
        return True

    def delete_block(self, index: int) -> bool:
        """Remove a block at a given index with undo support."""

        if not (0 <= index < len(self.blocks)):
            return False
        self._push_history()
        del self.blocks[index]
        self._redo_stack.clear()
        return True

    def insert_block(self, index: int, block: Block) -> bool:
        """Insert a block at a specific index while keeping undo history."""

        if not (0 <= index <= len(self.blocks)):
            return False
        self._push_history()
        self.blocks.insert(index, block)
        self._redo_stack.clear()
        return True

    # History management
    def _push_history(self) -> None:
        # Create a lightweight snapshot via serialization to avoid deepcopy issues
        # with objects that hold unpicklable state (e.g., cached Markdown parsers).
        snapshot = [Block.from_dict(block.to_dict()) for block in self.blocks]
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.HISTORY_LIMIT:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append([Block.from_dict(block.to_dict()) for block in self.blocks])
        self.blocks = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append([Block.from_dict(block.to_dict()) for block in self.blocks])
        self.blocks = self._redo_stack.pop()
        return True

    # Persistence helpers
    def to_dict(self) -> dict:
        return {"version": 1, "blocks": [block.to_dict() for block in self.blocks]}

    def save(self, path: str) -> None:
        data = self.to_dict()
        ext = os.path.splitext(path)[1].lower()
        if ext in {".yaml", ".yml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to save YAML notebooks.")
            with open(path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(data, handle, allow_unicode=True)
            return
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, payload: dict) -> "Document":
        blocks_data = payload.get("blocks", [])
        blocks: list[Block] = []
        for entry in blocks_data:
            blocks.append(Block.from_dict(entry))
        document = cls(blocks=blocks)
        document._undo_stack.clear()
        document._redo_stack.clear()
        return document

    @classmethod
    def load(cls, path: str) -> "Document":
        ext = os.path.splitext(path)[1].lower()
        with open(path, "r", encoding="utf-8") as handle:
            if ext in {".yaml", ".yml"}:
                if yaml is None:
                    raise RuntimeError("PyYAML is required to load YAML notebooks.")
                payload = yaml.safe_load(handle)
            else:
                payload = json.load(handle)
        return cls.from_dict(payload)
