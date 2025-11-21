"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import List, Optional

import sympy as sp


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

    def evaluate(self) -> None:
        """Parse and evaluate the expression using SymPy."""
        try:
            self.sympy_expr = sp.sympify(self.raw)
            evaluated = sp.N(self.sympy_expr)
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

    def add_block(self, block: Block) -> None:
        """Append a new block to the document."""
        self.blocks.append(block)

    def to_html(self) -> str:
        """Create an HTML preview containing all blocks with MathJax."""
        body = "\n".join(block.to_html() for block in self.blocks) or "<p>No blocks yet.</p>"
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
            </style>
        </head>
        <body>
            {body}
        </body>
        </html>
        """
