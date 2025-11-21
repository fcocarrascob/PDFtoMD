"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
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

    def _parse_assignment(self, rhs: str, context: EvaluationContext) -> tuple[sp.Expr, Optional[Quantity]]:
        """Parse the right-hand side of an assignment, capturing units when present."""

        rhs = rhs.strip()

        # Detect numeric literal followed by optional units, e.g. "2.5 m"
        parts = rhs.split()
        if len(parts) >= 1:
            try:
                value = float(parts[0])
                if len(parts) > 1:
                    unit_registry = get_unit_registry()
                    units = " ".join(parts[1:])
                    quantity = value * unit_registry(units)
                    return sp.Float(value), quantity
                return sp.Float(value), None
            except ValueError:
                pass

        # Fall back to generic SymPy parsing
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

        # Normalize caret to python exponent for eval friendliness.
        expr = expression.replace("^", "**")
        try:
            return eval(expr, {"__builtins__": {}}, env)  # pylint: disable=eval-used
        except Exception:
            return None

    @staticmethod
    def _to_quantity(value) -> Optional[Quantity]:
        """Return value if it is a pint Quantity, else None."""

        if isinstance(value, Quantity):
            return value
        return None

    @staticmethod
    def _format_numeric_value(value: float) -> str:
        """Format numeric values consistently for display."""

        return f"{value:.2f}"

    @staticmethod
    def _format_quantity(quantity: Quantity) -> tuple[float, str]:
        """Normalize a quantity for display and numeric storage."""

        ureg = get_unit_registry()
        try:
            # Custom simplifications for common mechanical combos.
            if quantity.check("[pressure] * [length]"):
                quantity = quantity.to(ureg.newton / ureg.meter)
            elif quantity.check("[pressure]"):
                quantity = quantity.to(ureg.pascal)
        except Exception:
            pass

        try:
            compact = quantity.to_compact()
        except Exception:
            compact = quantity
        units_text = f"{compact.units:~P}".replace("\u00b7", "*").replace(" ", "")
        return float(compact.magnitude), units_text

    def evaluate(self, context: Optional[EvaluationContext] = None) -> None:
        """Parse and evaluate the expression using SymPy."""

        context = context or EvaluationContext()
        self.is_assignment = False
        self.units = None
        self.quantity = None
        self.variable_name = None
        self.numeric_value = None

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
                        magnitude, normalized_units = self._format_quantity(quantity)
                        self.numeric_value = magnitude
                        self.units = normalized_units
                        self.result = f"{self._format_numeric_value(magnitude)} {normalized_units}"
                    else:
                        # Try pint-eval using previously defined quantities.
                        pint_value = self._evaluate_with_pint(rhs, context)
                        quantity_value = self._to_quantity(pint_value)
                        if quantity_value is not None:
                            self.quantity = quantity_value
                            magnitude, normalized_units = self._format_quantity(quantity_value)
                            self.numeric_value = magnitude
                            self.units = normalized_units
                            self.result = f"{self._format_numeric_value(magnitude)} {normalized_units}"
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
                    display_latex = expr_latex
                    if self.units:
                        display_latex = f"{display_latex}\\;{html.escape(self.units)}"
                    self.latex = f"{html.escape(lhs)} = {display_latex}"
                    context.register_variable(lhs, expr_latex, self.numeric_value, self.units, self.quantity)
                    return

            # Regular expression (non-assignment)
            self.sympy_expr = sp.sympify(raw, locals=context.symbols)
            pint_value = self._evaluate_with_pint(raw, context)
            quantity_value = self._to_quantity(pint_value)
            if quantity_value is not None:
                self.quantity = quantity_value
                magnitude, normalized_units = self._format_quantity(quantity_value)
                self.numeric_value = magnitude
                self.units = normalized_units
                self.result = f"{self._format_numeric_value(magnitude)} {normalized_units}"
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
            self.result = f"Error: {exc}"
            self.latex = None

    def to_html(self) -> str:
        if self.sympy_expr is None and self.result is None:
            self.evaluate()

        latex_expr = self.latex or html.escape(self.raw)
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

    def evaluate(self) -> EvaluationContext:
        """Evaluate all formula blocks within a shared context."""

        with EvaluationContext() as context:
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
