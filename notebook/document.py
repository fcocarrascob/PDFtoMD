"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

import sympy as sp
from pint import Quantity

from notebook.units import get_unit_registry, math_env

if TYPE_CHECKING:  # Avoid runtime import cycles with the renderer
    from notebook.renderer import NotebookRenderer


@dataclass
class SymbolRegistry(dict):
    """Dictionary that lazily creates SymPy symbols on demand."""

    def __missing__(self, key: str) -> sp.Symbol:
        symbol = sp.Symbol(key)
        self[key] = symbol
        return symbol


@dataclass
class VariableRecord:
    """Stores the evaluation details for a single variable."""

    name: str
    expression: str
    numeric_value: Optional[float] = None
    units: Optional[str] = None


@dataclass
class EvaluationContext:
    """Context manager that keeps symbol and numeric value registries."""

    symbols: SymbolRegistry = field(default_factory=SymbolRegistry)
    numeric_values: dict[str, float] = field(default_factory=dict)
    quantities: dict[str, Quantity] = field(default_factory=dict)
    variables: list[VariableRecord] = field(default_factory=list)
    precision: int = 2
    simplify_units: bool = True

    def __enter__(self) -> "EvaluationContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def register_variable(
        self,
        name: str,
        expression: str,
        numeric_value: Optional[float],
        units: Optional[str],
        quantity: Optional[Quantity],
    ) -> None:
        """Add a variable evaluation record and persist its numeric value."""

        _ = self.symbols[name]
        if numeric_value is not None:
            self.numeric_values[name] = numeric_value
        if quantity is not None:
            self.quantities[name] = quantity
        self.variables.append(
            VariableRecord(
                name=name,
                expression=expression,
                numeric_value=numeric_value,
                units=units,
            )
        )


@dataclass
class Block:
    """Base class for notebook blocks."""

    raw: str

    def to_html(self) -> str:
        """Render the block as HTML (implemented by subclasses)."""
        raise NotImplementedError


@dataclass
class TextBlock(Block):
    """Text block that stores explanatory content."""

    def to_html(self) -> str:
        safe_text = html.escape(self.raw)
        return f"<p class='text-block'>{safe_text}</p>"


@dataclass
class FormulaBlock(Block):
    """Math expression block evaluated with SymPy."""

    sympy_expr: Optional[sp.Expr] = None
    result: Optional[str] = None
    latex: Optional[str] = None
    numeric_value: Optional[float] = None
    is_assignment: bool = False
    variable_name: Optional[str] = None
    units: Optional[str] = None
    quantity: Optional[Quantity] = None
    error_message: Optional[str] = None

    def _parse_assignment(self, rhs: str, context: EvaluationContext) -> tuple[sp.Expr | None, Optional[Quantity]]:
        """Parse the right-hand side of an assignment, capturing units when present."""

        rhs = rhs.strip()
        ureg = get_unit_registry()
        variable_names = set(context.symbols.keys())
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", rhs))
        if tokens & variable_names:
            return sp.sympify(rhs, locals=context.symbols), None

        # Try pint parser first to support direct unit math (e.g., "3 m + 4 cm").
        try:
            parsed = ureg.parse_expression(rhs.replace("^", "**"))
            if isinstance(parsed, Quantity):
                return None, parsed
        except Exception:
            pass

        # Fall back to generic SymPy parsing with symbol registry.
        return sp.sympify(rhs, locals=context.symbols), None

    def _evaluate_with_pint(self, expression: str, context: EvaluationContext):
        """Try to evaluate the expression using pint quantities when available."""

        ureg = get_unit_registry()
        env = {"ureg": ureg}
        env.update(math_env())
        env.update(context.quantities)
        # Fallback to numeric-only substitutions for symbols without units.
        for name, value in context.numeric_values.items():
            env.setdefault(name, value)
        # Seed unit names so expressions con unidades literales (ej. "3 m + 4 cm") funcionen.
        for unit_name in ureg._units:  # pylint: disable=protected-access
            try:
                env.setdefault(unit_name, getattr(ureg, unit_name))
            except Exception:
                continue

        # Normalize caret to python exponent for eval friendliness.
        expr = expression.replace("^", "**")
        # Insert multiplicative operator when a number is directly followed by a unit with space.
        expr = re.sub(r"(?<=\\d)\\s+(?=[A-Za-z])", " * ", expr)
        try:
            return eval(expr, {"__builtins__": {}}, env), None  # pylint: disable=eval-used
        except Exception as exc:  # capture to surface errors in UI
            return None, exc

    @staticmethod
    def _to_quantity(value) -> Optional[Quantity]:
        """Return value if it is a pint Quantity, else None."""

        if isinstance(value, Quantity):
            return value
        return None

    @staticmethod
    def _format_numeric_value(value: float, precision: int) -> str:
        """Format numeric values consistently for display."""

        return f"{value:.{precision}f}"

    @staticmethod
    def _format_quantity(quantity: Quantity, context: EvaluationContext) -> tuple[float, str]:
        """Normalize a quantity for display and numeric storage."""

        # Optionally simplify units; if not, keep original units.
        if context.simplify_units:
            ureg = get_unit_registry()
            try:
                if quantity.check("[pressure] * [length]"):
                    quantity = quantity.to(ureg.newton / ureg.meter)
                elif quantity.check("[pressure]"):
                    quantity = quantity.to(ureg.pascal)
            except Exception:
                pass
            try:
                quantity = quantity.to_compact()
            except Exception:
                pass
            magnitude = float(quantity.magnitude)
            units_text = f"{quantity.units:~P}".replace("\u00b7", "*").replace(" ", "")
            return magnitude, units_text

        # No simplification: keep as provided.
        magnitude = float(quantity.magnitude)
        units_text = f"{quantity.units:~P}".replace("\u00b7", "*").replace(" ", "")
        return magnitude, units_text

    def evaluate(self, context: Optional[EvaluationContext] = None) -> None:
        """Parse and evaluate the expression using SymPy."""

        context = context or EvaluationContext()
        self.is_assignment = False
        self.units = None
        self.quantity = None
        self.variable_name = None
        self.numeric_value = None
        self.error_message = None

        raw = self.raw.strip()
        try:
            if "=" in raw:
                lhs, rhs = raw.split("=", 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                if lhs:
                    self.is_assignment = True
                    self.variable_name = lhs
                    self.sympy_expr, quantity = self._parse_assignment(rhs, context)
                    # First try with explicit quantity from parsing.
                    if quantity is not None:
                        self.quantity = quantity
                        magnitude, normalized_units = self._format_quantity(quantity, context)
                        self.numeric_value = magnitude
                        self.units = normalized_units
                        self.result = f"{self._format_numeric_value(magnitude, context.precision)} {normalized_units}"
                    else:
                        # Try pint-eval using previously defined quantities.
                        pint_value, pint_error = self._evaluate_with_pint(rhs, context)
                        if pint_error:
                            raise pint_error
                        quantity_value = self._to_quantity(pint_value)
                        if quantity_value is not None:
                            self.quantity = quantity_value
                            magnitude, normalized_units = self._format_quantity(quantity_value, context)
                            self.numeric_value = magnitude
                            self.units = normalized_units
                            self.result = f"{self._format_numeric_value(magnitude, context.precision)} {normalized_units}"
                        else:
                            substitution = self.sympy_expr.subs(context.numeric_values)
                            evaluated = sp.N(substitution)
                            if evaluated.is_real:
                                try:
                                    self.numeric_value = float(evaluated)
                                except (TypeError, ValueError):
                                    self.numeric_value = None
                            self.result = str(evaluated)
                    expr_latex = sp.latex(self.sympy_expr) if self.sympy_expr is not None else html.escape(rhs)
                    self.latex = f"{html.escape(lhs)} = {expr_latex}"
                    context.register_variable(lhs, expr_latex, self.numeric_value, self.units, self.quantity)
                    return

            # Regular expression (non-assignment)
            self.sympy_expr = sp.sympify(raw, locals=context.symbols)
            pint_value, pint_error = self._evaluate_with_pint(raw, context)
            if pint_error:
                raise pint_error
            quantity_value = self._to_quantity(pint_value)
            if quantity_value is not None:
                self.quantity = quantity_value
                magnitude, normalized_units = self._format_quantity(quantity_value, context)
                self.numeric_value = magnitude
                self.units = normalized_units
                self.result = f"{self._format_numeric_value(magnitude, context.precision)} {normalized_units}"
            else:
                substitution = self.sympy_expr.subs(context.numeric_values)
                evaluated = sp.N(substitution)
                self.result = str(evaluated)
                if evaluated.is_real:
                    try:
                        self.numeric_value = float(evaluated)
                    except (TypeError, ValueError):
                        self.numeric_value = None
            self.latex = sp.latex(self.sympy_expr)
        except Exception as exc:  # pylint: disable=broad-except
            # Keep evaluation errors but continue showing them in the UI.
            self.sympy_expr = None
            self.result = None
            self.latex = None
            self.error_message = str(exc)

    def to_html(self) -> str:
        if self.sympy_expr is None and self.result is None:
            self.evaluate()

        latex_expr = self.latex or html.escape(self.raw)
        result_html = ""
        if self.error_message:
            result_html = f"<div class='formula-error'>Error: {html.escape(self.error_message)}</div>"
        else:
            result_html = f"<div class='formula-result'>= {html.escape(self.result or '')}</div>"
        return (
            "<div class='formula-block'>"
            f"<div class='formula-input'>$$ {latex_expr} $$</div>"
            f"{result_html}"
            "</div>"
        )


@dataclass
class Document:
    """Ordered collection of blocks representing a notebook."""

    blocks: List[Block] = field(default_factory=list)
    precision: int = 2
    simplify_units: bool = True

    def evaluate(self) -> EvaluationContext:
        """Evaluate all formula blocks within a shared context."""

        with EvaluationContext(precision=self.precision, simplify_units=self.simplify_units) as context:
            for block in self.blocks:
                if isinstance(block, FormulaBlock):
                    block.evaluate(context)
            return context

    def add_block(self, block: Block) -> None:
        """Append a new block to the document."""
        self.blocks.append(block)

    def to_html(self, renderer: Optional["NotebookRenderer"] = None) -> str:
        """Create an HTML preview using the provided renderer."""

        renderer = renderer or self._default_renderer()
        return renderer.render(self)

    @staticmethod
    def _default_renderer() -> "NotebookRenderer":
        """Lazy import to avoid circular dependency when rendering."""

        from notebook.renderer import NotebookRenderer

        return NotebookRenderer()
