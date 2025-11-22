"""Data model for a simple calculation notebook."""
from __future__ import annotations

import html
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
    errors: list[dict] = field(default_factory=list)
    logs: list[dict] = field(default_factory=list)

    def __enter__(self) -> "EvaluationContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False


@dataclass
class NotebookOptions:
    """User-tunable settings that influence evaluation and formatting."""

    target_unit: str | None = None
    simplify_units: bool = True

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

    def register_error(self, *, block_id: str, message: str, error_type: str) -> None:
        """Store evaluation errors so the renderer can surface them."""

        self.errors.append({"block_id": block_id, "message": message, "type": error_type})

    def log_run(
        self,
        *,
        block_id: str,
        expression: str,
        duration_ms: float,
        units: Optional[str],
        substitutions: list[str],
    ) -> None:
        """Persist a lightweight evaluation log entry."""

        self.logs.append(
            {
                "block_id": block_id,
                "expression": expression,
                "duration_ms": round(duration_ms, 2),
                "units": units,
                "substitutions": substitutions,
            }
        )


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
                units=payload.get("units"),
            )
        return TextBlock(**common_kwargs)


@dataclass
class TextBlock(Block):
    """Text block that stores explanatory content."""

    def to_html(self) -> str:
        rendered = self._markdown.render(self.raw)
        sanitized = html.escape(self.raw) if not rendered else self._sanitize(rendered)
        return f"<div class='text-block'>{sanitized}</div>"

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
    units: Optional[str] = None
    quantity: Optional[Quantity] = None
    evaluation_status: str = "ok"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    evaluation_time_ms: Optional[float] = None

    def _parse_assignment(self, rhs: str, context: EvaluationContext) -> tuple[sp.Expr, Optional[Quantity]]:
        """Parse the right-hand side of an assignment, capturing units when present."""

        rhs = rhs.strip()

        # Detect numeric literal followed by optional units, e.g. "2.5 m"
        parts = rhs.split()
        if len(parts) in {1, 2}:
            try:
                value = float(parts[0])
                if len(parts) == 2:
                    unit_registry = get_unit_registry()
                    units = " ".join(parts[1:])
                    quantity = value * unit_registry(units)
                    return sp.Float(value), quantity
                return sp.Float(value), None
            except (ValueError, Exception):
                pass

        # Fall back to generic SymPy parsing
        return self._safe_sympify(rhs, context), None

    @staticmethod
    def _safe_sympify(expression: str, context: EvaluationContext) -> sp.Expr:
        """Sympify while avoiding accidental symbol injection for numeric-only inputs."""

        if re.search(r"[A-Za-z]", expression):
            return sp.sympify(expression, locals=context.symbols)
        return sp.sympify(expression)

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
            return eval(expr, {"__builtins__": {}}, env), None  # pylint: disable=eval-used
        except Exception as exc:
            return None, exc

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
    def _format_quantity(quantity: Quantity, options: "NotebookOptions") -> tuple[float, str]:
        """Normalize a quantity for display and numeric storage."""

        ureg = get_unit_registry()

        target_unit = (options.target_unit or "").strip() if options else ""
        if target_unit:
            quantity = quantity.to(target_unit)

        simplify_units = True if options is None else options.simplify_units

        if simplify_units:
            try:
                # Custom simplifications for common mechanical combos.
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

        units_text = f"{quantity.units:~P}".replace("\u00b7", "*").replace(" ", "")
        return float(quantity.magnitude), units_text

    def _handle_unit_error(
        self,
        exc: Exception,
        context: EvaluationContext,
        expr_latex: str,
        lhs: str | None = None,
    ) -> None:
        """Persist unit conversion errors for downstream display."""

        self.result = f"Error converting units: {exc}"
        self.evaluation_status = "error"
        self.error_type = type(exc).__name__
        self.error_message = str(exc)
        if lhs:
            self.latex = f"{html.escape(lhs)} = {expr_latex}"
            context.register_variable(lhs, expr_latex, None, None, None)
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
                "units": self.units,
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
        self.units = None
        self.quantity = None
        self.variable_name = None
        self.numeric_value = None
        self.evaluation_status = "ok"
        self.error_type = None
        self.error_message = None
        self.evaluation_time_ms = None

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
                        try:
                            magnitude, normalized_units = self._format_quantity(quantity, options)
                        except Exception as exc:
                            expr_latex = sp.latex(self.sympy_expr) if self.sympy_expr is not None else html.escape(rhs)
                            self._handle_unit_error(exc, context, expr_latex, lhs)
                            return
                        self.numeric_value = magnitude
                        self.units = normalized_units
                        self.result = f"{self._format_numeric_value(magnitude)} {normalized_units}"
                    else:
                        # Try pint-eval using previously defined quantities.
                        pint_value, pint_error = self._evaluate_with_pint(rhs, context)
                        if pint_error is not None:
                            expr_latex = sp.latex(self.sympy_expr) if self.sympy_expr is not None else html.escape(rhs)
                            self.result = f"Error evaluating units: {pint_error}"
                            self.evaluation_status = "error"
                            self.error_type = type(pint_error).__name__
                            self.error_message = str(pint_error)
                            self.latex = f"{html.escape(lhs)} = {expr_latex}"
                            context.register_variable(lhs, expr_latex, None, None, None)
                            context.register_error(
                                block_id=self.block_id,
                                message=self.error_message,
                                error_type=self.error_type,
                            )
                            return

                        quantity_value = self._to_quantity(pint_value)
                        if quantity_value is not None:
                            self.quantity = quantity_value
                            try:
                                magnitude, normalized_units = self._format_quantity(quantity_value, options)
                            except Exception as exc:
                                expr_latex = sp.latex(self.sympy_expr) if self.sympy_expr is not None else html.escape(rhs)
                                self._handle_unit_error(exc, context, expr_latex, lhs)
                                return
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
            self.sympy_expr = self._safe_sympify(raw, context)
            pint_value, pint_error = self._evaluate_with_pint(raw, context)
            if pint_error is not None:
                self.result = f"Error evaluating units: {pint_error}"
                self.evaluation_status = "error"
                self.error_type = type(pint_error).__name__
                self.error_message = str(pint_error)
                self.latex = sp.latex(self.sympy_expr)
                context.register_error(
                    block_id=self.block_id,
                    message=self.error_message,
                    error_type=self.error_type,
                )
                return

            quantity_value = self._to_quantity(pint_value)
            if quantity_value is not None:
                self.quantity = quantity_value
                try:
                    magnitude, normalized_units = self._format_quantity(quantity_value, options)
                except Exception as exc:
                    expr_latex = sp.latex(self.sympy_expr) if self.sympy_expr is not None else html.escape(raw)
                    self._handle_unit_error(exc, context, expr_latex)
                    return
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
            self.evaluation_status = "error"
            self.error_type = type(exc).__name__
            self.error_message = str(exc)
            context.register_error(block_id=self.block_id, message=self.error_message, error_type=self.error_type)
        finally:
            duration_ms = (perf_counter() - start_time) * 1000
            self.evaluation_time_ms = round(duration_ms, 2)
            substitutions: list[str] = []
            if self.sympy_expr is not None:
                symbol_names = {str(symbol) for symbol in self.sympy_expr.free_symbols}
                for name in sorted(symbol_names):
                    if name in context.numeric_values:
                        substitutions.append(f"{name}={context.numeric_values[name]:.2f}")
            context.log_run(
                block_id=self.block_id,
                expression=raw,
                duration_ms=duration_ms,
                units=self.units,
                substitutions=substitutions,
            )

    def to_html(self) -> str:
        if self.sympy_expr is None and self.result is None:
            self.evaluate()

        latex_expr = self.latex or html.escape(self.raw)
        status_class = " error" if self.evaluation_status == "error" else ""
        result_html = f"<div class='formula-result'>= {html.escape(self.result or '')}</div>"
        return (
            f"<div class='formula-block{status_class}'>"
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
        options: Optional[NotebookOptions] = None,
    ) -> str:
        """Create an HTML preview using the provided renderer."""

        renderer = renderer or self._default_renderer()
        return renderer.render(self, options=options)

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

    # History management
    def _push_history(self) -> None:
        snapshot = copy.deepcopy(self.blocks)
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.HISTORY_LIMIT:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(copy.deepcopy(self.blocks))
        self.blocks = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(copy.deepcopy(self.blocks))
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
