"""Notebook tab with SymPy-powered formula preview."""
from __future__ import annotations

import os
import re

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QLabel,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from notebook.document import Block, Document, FormulaBlock, NotebookOptions, TextBlock
from notebook.renderer import NotebookRenderer


class ParenthesisHighlighter(QSyntaxHighlighter):
    """Colors matching parentheses based on nesting depth for formulas."""

    def __init__(self, document):
        super().__init__(document)
        self.enabled = False
        self.palette = [
            QColor("#2a82da"),
            QColor("#e67e22"),
            QColor("#27ae60"),
            QColor("#9b59b6"),
            QColor("#d35400"),
            QColor("#16a085"),
            QColor("#c0392b"),
            QColor("#8e44ad"),
            QColor("#2980b9"),
            QColor("#f1c40f"),
        ]

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        if not self.enabled:
            return

        depth = self.previousBlockState()
        depth = 0 if depth < 0 else depth
        fmt = QTextCharFormat()

        for i, ch in enumerate(text):
            if ch == "(":
                color = self.palette[depth % len(self.palette)]
                fmt.setForeground(color)
                self.setFormat(i, 1, fmt)
                depth += 1
            elif ch == ")":
                depth = max(depth - 1, 0)
                color = self.palette[depth % len(self.palette)]
                fmt.setForeground(color)
                self.setFormat(i, 1, fmt)

        self.setCurrentBlockState(depth)


class NotebookTab(QWidget):
    """Simple calculation notebook UI with block list, editor, and preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = Document()
        self.renderer = NotebookRenderer()
        self.paren_highlighter = None

        self.settings = getattr(parent, "settings", QSettings("MyCompany", "PDFtoMD"))

        # UI elements
        self.block_list = QListWidget()
        self.editor = QTextEdit()
        self.variable_search = QLineEdit()
        self.snippet_table = QTableWidget()
        self.preview = QWebEngineView()
        self._delete_armed = False
        self.hint_label = QLabel()
        self._last_selected_block_id = None
        self._last_context = None

        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._seed_document()

    def _setup_ui(self) -> None:
        """Create layout with controls, editor, preview, and toolbar."""

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left column: controls + lists + editor (controls on the left)
        left_panel = QWidget()
        left_outer = QHBoxLayout(left_panel)
        left_outer.setContentsMargins(6, 6, 6, 6)
        left_outer.setSpacing(6)

        # Controls column (grouped vertically)
        controls_panel = QWidget()
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(4)

        def _add_group(title: str, buttons: list[QPushButton]) -> None:
            label = QLabel(title)
            label.setStyleSheet("font-weight: bold; margin-top: 4px;")
            controls_layout.addWidget(label)
            for btn in buttons:
                btn.setMinimumWidth(120)
                controls_layout.addWidget(btn)

        add_text_btn = QPushButton("Add\nText")
        add_text_btn.clicked.connect(self.add_text_block)
        add_formula_btn = QPushButton("Add\nFormula")
        add_formula_btn.clicked.connect(self.add_formula_block)
        delete_btn = QPushButton("Delete\nSelected")
        delete_btn.clicked.connect(self.delete_selected_block)

        move_up_btn = QPushButton("Move\nUp")
        move_up_btn.clicked.connect(lambda: self.move_selected_block(-1))
        move_down_btn = QPushButton("Move\nDown")
        move_down_btn.clicked.connect(lambda: self.move_selected_block(1))

        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo_action)
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.redo_action)

        save_btn = QPushButton("Save\nNotebook")
        save_btn.clicked.connect(self.save_document)
        load_btn = QPushButton("Load\nNotebook")
        load_btn.clicked.connect(self.load_document)
        export_html_btn = QPushButton("Export\nHTML")
        export_html_btn.clicked.connect(self.export_html)
        export_md_btn = QPushButton("Export\nMarkdown")
        export_md_btn.clicked.connect(self.export_markdown)

        _add_group("Blocks", [add_text_btn, add_formula_btn, delete_btn])
        _add_group("Order", [move_up_btn, move_down_btn])
        _add_group("Edit", [undo_btn, redo_btn])
        _add_group("File", [save_btn, load_btn, export_html_btn, export_md_btn])
        controls_layout.addStretch()

        # Main content (lists + editor)
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        block_list_label = QLabel("Blocks (type / id / summary)")
        left_layout.addWidget(block_list_label)
        self.block_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.block_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.block_list, 1)

        self.editor.setPlaceholderText("Enter text or a SymPy-friendly expression (use * for multiplication: 3*a, 2*d)...")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.editor.setFont(font)
        left_layout.addWidget(self.editor, 1)
        self.paren_highlighter = ParenthesisHighlighter(self.editor.document())
        self.hint_label.setStyleSheet("color: #f7c6c5; font-size: 11px;")
        left_layout.addWidget(self.hint_label)

        # Snippets panel for variables/arrays/functions
        snippets_box = QWidget()
        snippets_layout = QVBoxLayout(snippets_box)
        snippets_layout.setContentsMargins(0, 0, 0, 0)
        snippets_layout.setSpacing(4)

        search_row = QHBoxLayout()
        search_label = QLabel("Filtro")
        search_label.setStyleSheet("font-weight: bold;")
        search_row.addWidget(search_label)
        self.variable_search.setPlaceholderText("Filtrar por nombre...")
        search_row.addWidget(self.variable_search, 1)
        snippets_layout.addLayout(search_row)

        table_label = QLabel("Variables / Arrays / Funciones")
        table_label.setStyleSheet("font-weight: bold; margin-top: 4px;")
        snippets_layout.addWidget(table_label)

        self.snippet_table.setColumnCount(3)
        self.snippet_table.setHorizontalHeaderLabels(["Variable", "Array", "Función"])
        header = self.snippet_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(120)
        self.snippet_table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.snippet_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.snippet_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.snippet_table.setAlternatingRowColors(True)
        self.snippet_table.setMinimumHeight(200)
        self.snippet_table.setWordWrap(True)
        self.snippet_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.snippet_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        snippets_layout.addWidget(self.snippet_table)

        snippets_box.setMinimumHeight(220)
        left_layout.addWidget(snippets_box)

        left_outer.addWidget(controls_panel)
        left_outer.addWidget(left_content, 1)

        # Center column: preview
        center_panel = QWidget()
        center_panel.setMinimumWidth(400)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(6, 6, 6, 6)
        center_layout.setSpacing(6)
        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold;")
        center_layout.addWidget(preview_label)
        center_layout.addWidget(self.preview, 1)

        # Right column: toolbar
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)
        right_layout.addWidget(self._build_toolbar())
        right_layout.addStretch()

        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)
    def _connect_signals(self) -> None:
        self.block_list.currentItemChanged.connect(self.on_block_selected)
        self.editor.textChanged.connect(self.on_editor_changed)
        self.variable_search.textChanged.connect(self._apply_snippet_filter)
        self.snippet_table.itemActivated.connect(self._insert_from_table)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Up"), self, activated=lambda: self.move_selected_block(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self, activated=lambda: self.move_selected_block(1))
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.undo_action)
        QShortcut(QKeySequence.StandardKey.Redo, self, activated=self.redo_action)
        QShortcut(QKeySequence("A"), self.block_list, activated=lambda: self._insert_block_keyboard(above=True))
        QShortcut(QKeySequence("B"), self.block_list, activated=lambda: self._insert_block_keyboard(above=False))
        QShortcut(QKeySequence("T"), self.block_list, activated=lambda: self._insert_block_keyboard(above=False, force_type="text"))
        QShortcut(QKeySequence("F"), self.block_list, activated=lambda: self._insert_block_keyboard(above=False, force_type="formula"))
        QShortcut(QKeySequence("Shift+Return"), self.editor, activated=self._evaluate_and_advance)
        QShortcut(QKeySequence("D"), self.block_list, activated=self._handle_delete_shortcut)

    def _seed_document(self) -> None:
        """Add a starter text and formula block so the preview is not empty."""
        intro = TextBlock("Start adding notes and formulas for your calculations.")
        example = FormulaBlock("2 * (3 + 5)")
        example.evaluate()
        self.document.add_block(intro)
        self.document.add_block(example)
        self._refresh_block_views()
        self.update_preview()

    # Block management
    def add_text_block(self) -> None:
        block = TextBlock("New text block")
        self.document.add_block(block)
        self._refresh_block_views(select_last=True)
        self.update_preview()

    def add_formula_block(self) -> None:
        block = FormulaBlock("a + b")
        block.evaluate()
        self.document.add_block(block)
        self._refresh_block_views(select_last=True)
        self.update_preview()

    def delete_selected_block(self) -> None:
        current_row = self._current_row()
        if 0 <= current_row < len(self.document.blocks):
            self.document.delete_block(current_row)
            self._refresh_block_views(select_row=max(0, current_row - 1))
            self.update_preview()

    def move_selected_block(self, direction: int) -> None:
        current_row = self._current_row()
        if current_row < 0:
            return
        target_row = current_row + direction
        if self.document.move_block(current_row, target_row):
            self._refresh_block_views(select_row=target_row)
            self.update_preview()

    def undo_action(self) -> None:
        if self.document.undo():
            target = min(self._current_row(), len(self.document.blocks) - 1)
            self._refresh_block_views(select_row=target)
            self.update_preview()

    def redo_action(self) -> None:
        if self.document.redo():
            target = min(self._current_row(), len(self.document.blocks) - 1)
            self._refresh_block_views(select_row=target)
            self.update_preview()

    def _new_block(self, block_type: str) -> Block:
        if block_type == "formula":
            block = FormulaBlock("a + b")
            block.evaluate()
            return block
        return TextBlock("New text block")

    def _insert_block_keyboard(self, above: bool, force_type: str | None = None) -> None:
        """Insert a block relative to the active one, inspired by Jupyter A/B shortcuts."""

        if not self.document.blocks:
            base_type = force_type or "text"
            block = self._new_block(base_type)
            self.document.add_block(block)
            self._refresh_block_views(select_last=True)
            self.update_preview()
            self._focus_list()
            return

        current_row = self._current_row()
        if current_row < 0:
            current_row = len(self.document.blocks) - 1

        active_block = self.document.blocks[current_row]
        base_type = "formula" if isinstance(active_block, FormulaBlock) else "text"
        block_type = force_type or base_type
        insert_at = current_row if above else current_row + 1

        block = self._new_block(block_type)
        if self.document.insert_block(insert_at, block):
            self._refresh_block_views(select_row=insert_at)
            self.update_preview()
            self._focus_list()

    def _evaluate_and_advance(self) -> None:
        """Evaluate current block and move to the next one (creating if needed)."""

        self.on_editor_changed()
        current_row = self._current_row()
        if current_row < 0:
            return
        next_row = current_row + 1
        if next_row >= len(self.document.blocks):
            self._insert_block_keyboard(above=False, force_type="formula")
        else:
            self._select_row(next_row)
            self._load_editor_from_row(next_row)
        self._focus_list()

    def _handle_delete_shortcut(self) -> None:
        """Double-tap D to delete the active block without using the mouse."""

        if self._delete_armed:
            self._delete_armed = False
            self.delete_selected_block()
            return
        self._delete_armed = True
        QTimer.singleShot(600, lambda: setattr(self, "_delete_armed", False))

    def save_document(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Notebook", "", "Notebook Files (*.json *.yaml *.yml)"
        )
        if not path:
            return
        try:
            self.document.save(path)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Save Failed", str(exc))

    def load_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Notebook", "", "Notebook Files (*.json *.yaml *.yml)"
        )
        if not path:
            return
        try:
            self.document = Document.load(path)
            self.renderer = NotebookRenderer()
            self._refresh_block_views()
            self.update_preview()
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Load Failed", str(exc))

    # UI updates
    def _refresh_block_views(self, select_last: bool = False, select_row: int | None = None) -> None:
        self.block_list.clear()
        for idx, block in enumerate(self.document.blocks):
            title = "Text" if isinstance(block, TextBlock) else "Formula"
            summary = block.raw.strip().splitlines()[0] if block.raw.strip() else "(empty)"
            if len(summary) > 60:
                summary = summary[:57] + "..."
            label = f"{idx + 1}. {title} [{block.block_id[:6]}] — {summary}"
            item = QListWidgetItem(label)
            item.setToolTip(block.raw.strip() or title)
            self.block_list.addItem(item)

        if self.document.blocks:
            if select_last:
                target_row = len(self.document.blocks) - 1
            elif select_row is not None:
                target_row = select_row
            else:
                target_row = 0
            self._select_row(target_row)
            self._load_editor_from_row(target_row)
            self._remember_selected_block(target_row)
            self._scroll_preview_later()
        else:
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)

    def _select_row(self, row: int) -> None:
        """Sync selection across both block lists without feedback loops."""

        self.block_list.blockSignals(True)
        self.block_list.setCurrentRow(row)
        self.block_list.blockSignals(False)

    def _remember_selected_block(self, row: int) -> None:
        """Store the block id for later scroll sync."""

        if 0 <= row < len(self.document.blocks):
            self._last_selected_block_id = self.document.blocks[row].block_id
        else:
            self._last_selected_block_id = None

    def _current_row(self) -> int:
        """Return the active row from the unified list."""

        return self.block_list.currentRow()

    def _load_editor_from_row(self, row: int) -> None:
        if row < 0 or row >= len(self.document.blocks):
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)
            return
        block = self.document.blocks[row]
        self.editor.blockSignals(True)
        self.editor.setPlainText(block.raw)
        self.editor.blockSignals(False)
        if self.paren_highlighter:
            self.paren_highlighter.enabled = isinstance(block, FormulaBlock)
            self.paren_highlighter.rehighlight()

    def _update_list_item(self, row: int) -> None:
        """Refresh the block list label for a single row without rebuilding all items."""

        if row < 0 or row >= len(self.document.blocks):
            return
        block = self.document.blocks[row]
        title = "Text" if isinstance(block, TextBlock) else "Formula"
        summary = block.raw.strip().splitlines()[0] if block.raw.strip() else "(empty)"
        if len(summary) > 60:
            summary = summary[:57] + "..."
        label = f"{row + 1}. {title} [{block.block_id[:6]}] — {summary}"
        item = self.block_list.item(row)
        if item:
            item.setText(label)
            item.setToolTip(block.raw.strip() or title)

    def _focus_list(self) -> None:
        self.block_list.setFocus(Qt.FocusReason.OtherFocusReason)

    def _update_hint(self, raw_text: str) -> None:
        """Show a gentle reminder when implicit multiplication is detected."""

        pattern = re.compile(r"(\d)([A-Za-z])|(\d)\(|\)(\d)|\)([A-Za-z])|([A-Za-z])\(")
        message = "Usa * para multiplicar: ej. 3*a, 2*d, a*(b)"
        if pattern.search(raw_text):
            self.hint_label.setText(message)
        else:
            self.hint_label.setText("")

    def on_block_selected(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        row = self.block_list.currentRow()
        if row < 0:
            self._load_editor_from_row(-1)
            return
        self._select_row(row)
        self._load_editor_from_row(row)
        self._remember_selected_block(row)
        self._scroll_preview_later()

    def on_editor_changed(self) -> None:
        row = self._current_row()
        if row < 0 or row >= len(self.document.blocks):
            return
        block = self.document.blocks[row]
        block.raw = self.editor.toPlainText()
        if isinstance(block, FormulaBlock):
            block.evaluate()
        self._update_list_item(row)
        self.update_preview()
        self._update_hint(block.raw)

    def update_preview(self) -> None:
        """Render the document into the web view with MathJax."""
        mathjax_path, mathjax_url = self._mathjax_args(for_export=False)
        context = self.document.evaluate(options=self._evaluation_options(hide_logs=False))
        self._last_context = context
        self._refresh_snippet_panel(context)
        html_content = self.document.to_html(
            renderer=self.renderer,
            mathjax_path=mathjax_path,
            mathjax_url=mathjax_url,
            options=self._evaluation_options(hide_logs=False),
        )
        self.preview.setHtml(html_content)
        self._scroll_preview_later()

    def _scroll_preview_later(self) -> None:
        """Scroll to the last selected block after the preview is ready."""

        if not self._last_selected_block_id:
            return

        def _scroll():
            js = (
                "(() => {"
                f" const el = document.getElementById('block-{self._last_selected_block_id}');"
                " if (el) { el.scrollIntoView({behavior: 'smooth', block: 'center'}); }"
                "})();"
            )
            self.preview.page().runJavaScript(js)

        QTimer.singleShot(150, _scroll)

    def export_html(self) -> None:
        """Persist the rendered notebook to an HTML file."""

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Notebook as HTML", "", "HTML Files (*.html)"
        )
        if not path:
            return

        mathjax_path, mathjax_url = self._mathjax_args(for_export=True)
        if mathjax_path == "__missing_local__":
            QMessageBox.warning(
                self,
                "MathJax bundle not found",
                "Local MathJax bundle not found. Falling back to CDN.",
            )
            mathjax_path = None
            mathjax_url = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"

        try:
            self.document.save_html(
                path,
                renderer=self.renderer,
                mathjax_path=mathjax_path,
                mathjax_url=mathjax_url,
                options=self._evaluation_options(hide_logs=self._hide_logs_pref()),
            )
            QMessageBox.information(self, "Export complete", f"Saved HTML to {path}")
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Export failed", str(exc))

    def export_markdown(self) -> None:
        """Save the notebook as a Markdown document."""

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Notebook as Markdown", "", "Markdown Files (*.md)"
        )
        if not path:
            return

        try:
            self.document.save_markdown(path)
            QMessageBox.information(
                self, "Export complete", f"Saved Markdown to {path}"
            )
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Export failed", str(exc))

    # Toolbar helpers
    def _build_toolbar(self) -> QWidget:
        """Create a vertical toolbar grouped by function type, 4 columns per group."""

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        container.setMinimumWidth(220)

        def _add_group(title: str, items: list[tuple[str, str]]) -> None:
            lbl = QLabel(title)
            lbl.setStyleSheet("font-weight: bold; margin-top: 4px;")
            layout.addWidget(lbl)
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(4)
            grid.setVerticalSpacing(2)
            for idx, (label, snippet) in enumerate(items):
                btn = QToolButton()
                btn.setText(label)
                btn.setToolTip(f"Insert {label}")
                btn.clicked.connect(lambda _=False, s=snippet: self.insert_snippet(s))
                btn.setMinimumWidth(52)
                btn.setMinimumHeight(24)
                row, col = divmod(idx, 3)
                grid.addWidget(btn, row, col)
            layout.addWidget(grid_widget)

        _add_group("Operadores", [
            ("+", " + "),
            ("-", " - "),
            ("*", " * "),
            ("/", " / "),
            ("^", " ** "),
            ("sqrt", "sqrt()"),
            ("?", " \u22c5 "),
            ("?", " \u2248 "),
        ])

        _add_group("Funciones", [
            ("sin", "sin()"),
            ("cos", "cos()"),
            ("tan", "tan()"),
            ("exp", "exp()"),
            ("log", "log()"),
            ("pi", "pi"),
            ("abs", "abs()"),
        ])

        _add_group("Agregados", [
            ("sum", "sum()"),
            ("min", "min()"),
            ("max", "max()"),
            ("range", "range()"),
        ])

        _add_group("Arrays", [
            ("linspace", "linspace( , , )"),
            ("arange", "arange( , , )"),
            ("sweep", "sweep(f, xs)"),
        ])

        _add_group("Condicionales", [
            ("if/else", "(a) if (condicion) else (b)"),
            ("if/elif/else", "(a) if (cond1) else ((b) if (cond2) else (c))"),
        ])

        _add_group("Lógico", [
            ("A and B", "(A) and (B)"),
            ("A or B", "(A) or (B)"),
            ("not A", "not (A)"),
        ])

        _add_group("Definir f(x)", [
            ("f(x)", "f(x) = "),
        ])

        _add_group("LaTeX", [
            ("Inline $", r"$ $"),
            ("Frac", r"\frac{}{}"),
            ("Sqrt", r"\sqrt{}"),
            ("Sub", r"x_{}"),
            ("Sup", r"x^{}"),
        ])

        greek_label = QLabel("Greek")
        greek_label.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(greek_label)
        self.greek_combo = QComboBox()
        greek_items = [r"\alpha", r"\beta", r"\gamma", r"\delta", r"\phi", r"\theta", r"\lambda", r"\pi", r"\sigma", r"\omega"]
        self.greek_combo.addItems(greek_items)
        self.greek_combo.setToolTip("Insert Greek symbol (LaTeX)")
        greek_btn = QToolButton()
        greek_btn.setText("Insert")
        greek_btn.setToolTip("Insert selected Greek symbol")
        greek_btn.clicked.connect(lambda: self.insert_snippet(self.greek_combo.currentText()))
        layout.addWidget(self.greek_combo)
        layout.addWidget(greek_btn)

        layout.addStretch()
        return container

    def insert_snippet(self, text: str) -> None:
        """Insert a math snippet at the current cursor position."""

        cursor = self.editor.textCursor()
        cursor.insertText(text)
        self.editor.setTextCursor(cursor)

    # Snippet panel helpers
    def _refresh_snippet_panel(self, context) -> None:
        """Update variables/arrays/functions lists from the latest evaluation context."""

        if context is None:
            self.snippet_table.setRowCount(0)
            return
        filter_text = self.variable_search.text().strip().lower()

        def _matches(name: str) -> bool:
            return filter_text in name.lower() if filter_text else True

        # Build rows with max length among the three categories
        array_names = set(context.arrays.keys())
        variables = [v for v in context.variables if v.name not in array_names and _matches(v.name)]
        arrays = [a for a in context.arrays.values() if _matches(a.name)]
        functions = [f for f in context.functions.values() if _matches(f.name)]
        max_len = max(len(variables), len(arrays), len(functions))
        self.snippet_table.setRowCount(max_len)

        def _make_item(text: str, tooltip: str, payload: str) -> QTableWidgetItem:
            item = QTableWidgetItem(text)
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, payload)
            return item

        for row in range(max_len):
            if row < len(variables):
                v = variables[row]
                if v.numeric_value is not None:
                    value = str(v.numeric_value)
                    text = f"{v.name}\n{value}"
                else:
                    text = f"{v.name}\n{v.expression}"
                self.snippet_table.setItem(row, 0, _make_item(text, f"{v.name} = {v.expression}", v.name))
            else:
                self.snippet_table.setItem(row, 0, QTableWidgetItem(""))

            if row < len(arrays):
                a = arrays[row]
                display = a.values
                if len(display) > 6:
                    preview = ", ".join(f"{v:.2f}" for v in display[:3]) + ", ..."
                else:
                    preview = ", ".join(f"{v:.2f}" for v in display)
                text = f"{a.name}\n[{preview}]"
                self.snippet_table.setItem(row, 1, _make_item(text, f"{a.name} = {a.expression}", a.name))
            else:
                self.snippet_table.setItem(row, 1, QTableWidgetItem(""))

            if row < len(functions):
                f = functions[row]
                signature = f"{f.name}({', '.join(f.parameters)})"
                text = f"{signature}"
                self.snippet_table.setItem(row, 2, _make_item(text, f"{signature} = {f.expression}", f.name))
            else:
                self.snippet_table.setItem(row, 2, QTableWidgetItem(""))

        self.snippet_table.resizeRowsToContents()

    def _apply_snippet_filter(self) -> None:
        """Filter the snippet lists without re-evaluating."""

        self._refresh_snippet_panel(self._last_context)

    def _insert_from_table(self, item) -> None:
        """Insert the identifier stored in the activated table cell."""

        if not item:
            return
        payload = item.data(Qt.ItemDataRole.UserRole)
        if payload:
            self.insert_snippet(payload)

    def _hide_logs_pref(self) -> bool:
        stored = self.settings.value("render/hide_logs", False)
        if isinstance(stored, str):
            return stored.lower() in {"1", "true", "yes"}
        return bool(stored)

    def _mathjax_args(self, for_export: bool = False) -> tuple[str | None, str | None]:
        default_cdn = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        mode = str(self.settings.value("render/mathjax_mode", "cdn") or "cdn")
        path = str(self.settings.value("render/mathjax_path", "") or "")
        if mode == "local":
            if path and os.path.exists(path):
                return path, None
            # Signal missing bundle for export so we can notify, silently fall back for preview
            if for_export:
                return "__missing_local__", None
            return None, default_cdn
        return None, default_cdn

    def _evaluation_options(self, hide_logs: bool = False) -> NotebookOptions:
        return NotebookOptions(
            hide_logs=hide_logs,
        )
