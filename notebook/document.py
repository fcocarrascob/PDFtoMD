"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import List, Optional

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr


@dataclass
class SymbolRegistry(dict):
    """Dictionary that lazily creates SymPy symbols on demand."""

    def __getitem__(self, key: str) -> sp.Symbol:  # pragma: no cover - simple helper
        # Avoid shadowing SymPy's own callables such as Integer, Symbol, etc.
        if dict.__contains__(self, key):
            return dict.__getitem__(self, key)

        if hasattr(sp, key):
            raise KeyError(key)

        symbol = sp.Symbol(key)
        dict.__setitem__(self, key, symbol)
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
    variables: list[VariableRecord] = field(default_factory=list)

    def __enter__(self) -> "EvaluationContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def register_variable(
        self, name: str, expression: str, numeric_value: Optional[float], units: Optional[str]
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
                units=units,
            )
        )

    def variable_table_html(self) -> str:
        """Render the registry as an HTML table for the preview."""

        if not self.variables:
            return ""

        header = """
        <div class='variable-table'>
            <h3>Variables</h3>
            <table>
                <thead>
                    <tr><th>Nombre</th><th>Expresión</th><th>Valor</th><th>Unidades</th></tr>
                </thead>
                <tbody>
        """

        rows = []
        for variable in self.variables:
            value = "" if variable.numeric_value is None else str(variable.numeric_value)
            rows.append(
                "<tr>"
                f"<td>{html.escape(variable.name)}</td>"
                f"<td>$$ {variable.expression} $$</td>"
                f"<td>{html.escape(value)}</td>"
                f"<td>{html.escape(variable.units or '')}</td>"
                "</tr>"
            )

        footer = """
                </tbody>
            </table>
        </div>
        """

        return header + "\n".join(rows) + footer


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

    def _parse_assignment(self, rhs: str, context: EvaluationContext) -> tuple[sp.Expr, str]:
        """Parse the right-hand side of an assignment, capturing units when present."""

        rhs = rhs.strip()

        # Detect numeric literal followed by optional units, e.g. "2.5 m"
        parts = rhs.split()
        if len(parts) >= 1:
            try:
                value = float(parts[0])
                if len(parts) > 1:
                    self.units = " ".join(parts[1:])
                expr = sp.Float(value)
                return expr, sp.latex(expr)
            except ValueError:
                pass

        # Fall back to generic SymPy parsing without eager evaluation to preserve the
        # original expression (e.g., keep ``sqrt(9)`` instead of reducing to ``3``).
        expr = parse_expr(rhs, local_dict=context.symbols, evaluate=False)
        return expr, sp.latex(expr)

    def evaluate(self, context: Optional[EvaluationContext] = None) -> None:
        """Parse and evaluate the expression using SymPy."""

        context = context or EvaluationContext()
        self.is_assignment = False
        self.units = None
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
                    self.sympy_expr, expr_latex = self._parse_assignment(rhs, context)
                    substitution = self.sympy_expr.subs(context.numeric_values)
                    evaluated = sp.N(substitution)
                    if evaluated.is_real:
                        try:
                            self.numeric_value = float(evaluated)
                        except (TypeError, ValueError):
                            self.numeric_value = None
                    self.result = str(evaluated)
                    display_latex = expr_latex
                    if self.units:
                        display_latex = f"{display_latex}\\;{html.escape(self.units)}"
                    self.latex = f"{html.escape(lhs)} = {display_latex}"
                    context.register_variable(lhs, expr_latex, self.numeric_value, self.units)
                    return

            # Regular expression (non-assignment)
            self.sympy_expr = parse_expr(raw, local_dict=context.symbols, evaluate=False)
            substitution = self.sympy_expr.subs(context.numeric_values)
            evaluated = sp.N(substitution)
            self.result = str(evaluated)
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

    def to_html(self) -> str:
        """Create an HTML preview containing all blocks with MathJax."""
        context = self.evaluate()
        body = "\n".join(block.to_html() for block in self.blocks) or "<p>No blocks yet.</p>"
        body += context.variable_table_html()
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 16px; background: #1f1f1f; color: #f0f0f0; }}
                .text-block {{ margin-bottom: 12px; }}
                .formula-block {{ margin-bottom: 16px; padding: 12px; background: #2a2a2a; border-radius: 6px; }}
                .formula-input {{ font-size: 18px; margin-bottom: 6px; }}
                .formula-result {{ color: #8bd450; font-weight: bold; }}
                .variable-table {{ margin-top: 24px; background: #2a2a2a; padding: 12px; border-radius: 6px; }}
                .variable-table h3 {{ margin-top: 0; }}
                .variable-table table {{ width: 100%; border-collapse: collapse; }}
                .variable-table th, .variable-table td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid #3a3a3a; }}
                .variable-table th {{ color: #d0d0d0; }}
            </style>
        </head>
        <body>
            {body}
        </body>
        </html>
        """
