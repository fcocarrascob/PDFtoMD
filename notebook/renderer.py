"""HTML renderer for the calculation notebook preview."""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Iterable

from notebook.document import Document, FormulaBlock, TextBlock, VariableRecord


@dataclass
class NotebookTheme:
    """Simple theme holder to keep colors centralized."""

    background: str = "#1f1f1f"
    text: str = "#f0f0f0"
    panel: str = "#2a2a2a"
    accent: str = "#8bd450"
    border: str = "#3a3a3a"


class NotebookRenderer:
    """Render a document into an HTML page with MathJax support."""

    def __init__(self, theme: NotebookTheme | None = None) -> None:
        self.theme = theme or NotebookTheme()

    def render(self, document: Document) -> str:
        """Return full HTML including MathJax and styling."""

        context = document.evaluate()
        body = "\n".join(self._render_block(block) for block in document.blocks)
        if not body:
            body = "<p class='text-block'>No blocks yet.</p>"

        variable_table = self._render_variable_table(context.variables)
        if variable_table:
            body = f"{body}\n{variable_table}"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <style>
                {self._stylesheet()}
            </style>
        </head>
        <body>
            {body}
        </body>
        </html>
        """

    def _render_block(self, block) -> str:
        """Render a block while keeping types explicit."""

        if isinstance(block, (TextBlock, FormulaBlock)):
            return block.to_html()
        return ""

    def _render_variable_table(self, variables: Iterable[VariableRecord]) -> str:
        """Render a compact variable list below the document."""

        rows = []
        for variable in variables:
            value = self._format_value(variable.numeric_value, variable.units)
            rows.append(
                "<tr>"
                f"<td>{html.escape(variable.name)}</td>"
                f"<td>$$ {variable.expression} $$</td>"
                f"<td>{html.escape(value)}</td>"
                f"<td>{html.escape(variable.units or '')}</td>"
                "</tr>"
            )
        if not rows:
            return ""

        return (
            "<div class='variable-table'>"
            "<h3>Variables</h3>"
            "<table>"
            "<thead>"
            "<tr><th>Name</th><th>Expression</th><th>Value</th><th>Units</th></tr>"
            "</thead>"
            "<tbody>"
            + "".join(rows)
            + "</tbody>"
            "</table>"
            "</div>"
        )

    @staticmethod
    def _format_value(numeric_value, units: str | None) -> str:
        """Format numeric values and append units if present."""

        if numeric_value is None:
            return ""
        formatted = f"{float(numeric_value):.2f}"
        return f"{formatted} {units}" if units else formatted

    def _stylesheet(self) -> str:
        """Return CSS for the preview."""

        return f"""
            body {{ font-family: Arial, sans-serif; padding: 16px; background: {self.theme.background}; color: {self.theme.text}; }}
            .text-block {{ margin-bottom: 12px; line-height: 1.5; }}
            .formula-block {{ margin-bottom: 16px; padding: 12px; background: {self.theme.panel}; border-radius: 6px; border: 1px solid {self.theme.border}; }}
            .formula-input {{ font-size: 18px; margin-bottom: 6px; }}
            .formula-result {{ color: {self.theme.accent}; font-weight: bold; }}
            .variable-table {{ margin-top: 24px; background: {self.theme.panel}; padding: 12px; border-radius: 6px; border: 1px solid {self.theme.border}; }}
            .variable-table h3 {{ margin-top: 0; }}
            .variable-table table {{ width: 100%; border-collapse: collapse; }}
            .variable-table th, .variable-table td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid {self.theme.border}; }}
            .variable-table th {{ color: {self.theme.text}; opacity: 0.8; }}
        """
