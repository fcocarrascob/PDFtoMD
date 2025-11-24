"""HTML renderer for the calculation notebook preview."""
from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Iterable

from notebook.document import Document, FormulaBlock, TextBlock, VariableRecord


@dataclass
class NotebookTheme:
    """Simple theme holder to keep colors centralized."""

    background: str = "#f7f8fa"
    text: str = "#1f1f1f"
    panel: str = "#ffffff"
    accent: str = "#2a82da"
    border: str = "#dbe1ea"


class NotebookRenderer:
    """Render a document into an HTML page with MathJax support."""

    def __init__(self, theme: NotebookTheme | None = None) -> None:
        self.theme = theme or NotebookTheme()

    def render(
        self,
        document: Document,
        *,
        mathjax_path: str | None = None,
        mathjax_url: str | None = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
        options=None,
    ) -> str:
        """Return full HTML including MathJax and styling.

        The caller can provide ``mathjax_path`` to embed a local MathJax bundle for
        offline viewing. If omitted, the renderer falls back to the provided
        ``mathjax_url`` (defaulting to the CDN build).
        """

        context = document.evaluate(options=options)
        body = "\n".join(self._render_block(block) for block in document.blocks)
        if not body:
            body = "<p class='text-block'>No blocks yet.</p>"

        variable_table = self._render_variable_table(context.variables)
        error_panel = self._render_error_panel(context.errors)
        hide_logs = bool(getattr(options, "hide_logs", False)) if options is not None else False
        log_panel = "" if hide_logs else self._render_log_panel(context.logs)
        if variable_table:
            body = f"{body}\n{variable_table}"
        if error_panel:
            body = f"{body}\n{error_panel}"
        if log_panel:
            body = f"{body}\n{log_panel}"

        mathjax_script = self._mathjax_script(mathjax_path, mathjax_url)
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            {mathjax_script}
            <style>
                {self._stylesheet()}
            </style>
        </head>
        <body>
            <div class='page'>
                {body}
            </div>
        </body>
        </html>
        """

    def _render_block(self, block) -> str:
        """Render a block while keeping types explicit."""

        if isinstance(block, (TextBlock, FormulaBlock)):
            return block.to_html()
        return ""

    def _render_error_panel(self, errors) -> str:
        """Render accumulated evaluation errors."""

        if not errors:
            return ""

        items = []
        for error in errors:
            block_id = html.escape(error.get("block_id", ""))
            message = html.escape(error.get("message", ""))
            error_type = html.escape(error.get("type", "Error"))
            items.append(f"<li><strong>{error_type}</strong> ({block_id}): {message}</li>")

        return (
            "<div class='error-panel'>"
            "<h3>Errores de evaluación</h3>"
            "<ul>"
            + "".join(items)
            + "</ul>"
            "</div>"
        )

    def _render_log_panel(self, logs) -> str:
        """Render a compact evaluation log to show timings and substitutions."""

        if not logs:
            return ""

        rows = []
        for entry in logs:
            substitutions = ", ".join(entry.get("substitutions", [])) or "-"
            rows.append(
                "<tr>"
                f"<td>{html.escape(entry.get('block_id', '')[:6])}</td>"
                f"<td>{html.escape(entry.get('expression', ''))}</td>"
                f"<td>{entry.get('duration_ms', 0):.2f} ms</td>"
                f"<td>{html.escape(substitutions)}</td>"
                "</tr>"
            )

        return (
            "<div class='log-panel'>"
            "<h3>Registro de evaluación</h3>"
            "<table>"
            "<thead>"
            "<tr><th>Bloque</th><th>Expresión</th><th>Tiempo</th><th>Sustituciones</th></tr>"
            "</thead>"
            "<tbody>"
            + "".join(rows)
            + "</tbody>"
            "</table>"
            "</div>"
        )

    def _render_variable_table(self, variables: Iterable[VariableRecord]) -> str:
        """Render a compact variable list below the document."""

        rows = []
        for variable in variables:
            value = self._format_value(variable.numeric_value)
            rows.append(
                "<tr>"
                f"<td>{html.escape(variable.name)}</td>"
                f"<td>$$ {variable.expression} $$</td>"
                f"<td>{html.escape(value)}</td>"
                "</tr>"
            )
        if not rows:
            return ""

        return (
            "<div class='variable-table'>"
            "<h3>Variables</h3>"
            "<table>"
            "<thead>"
            "<tr><th>Name</th><th>Expression</th><th>Value</th></tr>"
            "</thead>"
            "<tbody>"
            + "".join(rows)
            + "</tbody>"
            "</table>"
            "</div>"
        )

    @staticmethod
    def _format_value(numeric_value) -> str:
        """Format numeric values consistently."""

        if numeric_value is None:
            return ""
        return f"{float(numeric_value):.2f}"

    def _stylesheet(self) -> str:
        """Return CSS for the preview."""

        return f"""
            @page {{
                size: A4;
                margin: 12mm;
            }}
            body {{
                font-family: Arial, sans-serif;
                padding: 24px;
                background: #eceff4;
                color: {self.theme.text};
                display: flex;
                justify-content: center;
            }}
            .page {{
                background: {self.theme.background};
                color: {self.theme.text};
                max-width: 210mm;
                min-height: 297mm;
                width: 100%;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
                border: 1px solid #e5e8ee;
                border-radius: 6px;
                padding: 24px;
                box-sizing: border-box;
            }}
            .text-block {{ margin-bottom: 12px; line-height: 1.5; }}
            .text-block h1, .text-block h2, .text-block h3, .text-block h4, .text-block h5, .text-block h6 {{
                margin: 0 0 8px 0;
                font-weight: 700;
                color: {self.theme.accent};
            }}
            .text-block ul, .text-block ol {{
                padding-left: 20px;
                margin: 6px 0 12px 0;
            }}
            .text-block li {{ margin-bottom: 4px; }}
            .text-block code {{
                background: {self.theme.panel};
                border: 1px solid {self.theme.border};
                padding: 2px 4px;
                border-radius: 4px;
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            }}
            .formula-block {{ margin-bottom: 16px; padding: 12px; background: {self.theme.panel}; border-radius: 6px; border: 1px solid {self.theme.border}; }}
            .formula-block.error {{ border-color: #d9534f; background: #fdecea; }}
            .formula-input {{ font-size: 18px; margin-bottom: 6px; }}
            .formula-result {{ color: {self.theme.accent}; font-weight: bold; }}
            .formula-block.error .formula-result {{ color: #d9534f; }}
            .variable-table {{ margin-top: 24px; background: {self.theme.panel}; padding: 12px; border-radius: 6px; border: 1px solid {self.theme.border}; }}
            .variable-table h3 {{ margin-top: 0; }}
            .variable-table table {{ width: 100%; border-collapse: collapse; }}
            .variable-table th, .variable-table td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid {self.theme.border}; }}
            .variable-table th {{ color: {self.theme.text}; opacity: 0.8; }}
            .error-panel, .log-panel {{ margin-top: 16px; background: {self.theme.panel}; padding: 12px; border-radius: 6px; border: 1px solid {self.theme.border}; }}
            .error-panel h3 {{ margin-top: 0; color: #d9534f; }}
            .log-panel h3 {{ margin-top: 0; color: {self.theme.accent}; }}
            .error-panel ul {{ padding-left: 18px; margin: 8px 0; }}
            .error-panel li {{ margin-bottom: 6px; }}
            .log-panel table {{ width: 100%; border-collapse: collapse; }}
            .log-panel th, .log-panel td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid {self.theme.border}; }}
            .log-panel th {{ color: {self.theme.text}; opacity: 0.8; }}
        """

    @staticmethod
    def _mathjax_script(mathjax_path: str | None, mathjax_url: str | None) -> str:
        """Return the MathJax loader script, embedding when a local path is given."""

        config = """
        <script>
        window.MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$','$$'], ['\\\\[','\\\\]']]
          },
          options: {
            skipHtmlTags: ['script','noscript','style','textarea','pre','code']
          }
        };
        </script>
        """

        if mathjax_path:
            try:
                with open(mathjax_path, "r", encoding="utf-8") as handle:
                    content = handle.read()
                return f"{config}<script>{content}</script>"
            except OSError:
                # Fall back to external URL if the path cannot be read.
                pass

        if mathjax_url:
            return f"{config}<script src=\"{html.escape(mathjax_url)}\"></script>"
        return config
