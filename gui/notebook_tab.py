"""Notebook tab with SymPy-powered formula preview."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from notebook.document import Document, FormulaBlock, TextBlock
from notebook.renderer import NotebookRenderer
from notebook.units import COMMON_UNITS


class NotebookTab(QWidget):
    """Simple calculation notebook UI with block list, editor, and preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = Document()
        self.renderer = NotebookRenderer()

        # UI elements
        self.block_list = QListWidget()
        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        self._setup_ui()
        self._connect_signals()
        self._seed_document()

    def _setup_ui(self) -> None:
        """Create layout with controls, editor, and preview."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left column: block list and buttons
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(4, 4, 4, 4)

        add_text_btn = QPushButton("Add Text Block")
        add_text_btn.clicked.connect(self.add_text_block)
        add_formula_btn = QPushButton("Add Formula Block")
        add_formula_btn.clicked.connect(self.add_formula_block)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected_block)

        left_layout.addWidget(add_text_btn)
        left_layout.addWidget(add_formula_btn)
        left_layout.addWidget(delete_btn)
        left_layout.addWidget(self.block_list, 1)

        # Right column: editor + preview stacked vertically
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)

        right_layout.addWidget(self._build_toolbar())
        self.editor.setPlaceholderText("Enter text or a SymPy-friendly expression...")
        right_layout.addWidget(self.editor, 1)
        right_layout.addWidget(self.preview, 2)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 2)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self.block_list.currentItemChanged.connect(self.on_block_selected)
        self.editor.textChanged.connect(self.on_editor_changed)

    def _seed_document(self) -> None:
        """Add a starter text and formula block so the preview is not empty."""
        intro = TextBlock("Start adding notes and formulas for your calculations.")
        example = FormulaBlock("2 * (3 + 5)")
        example.evaluate()
        self.document.add_block(intro)
        self.document.add_block(example)
        self._refresh_block_list()
        self.update_preview()

    # Block management
    def add_text_block(self) -> None:
        block = TextBlock("New text block")
        self.document.add_block(block)
        self._refresh_block_list(select_last=True)
        self.update_preview()

    def add_formula_block(self) -> None:
        block = FormulaBlock("a + b")
        block.evaluate()
        self.document.add_block(block)
        self._refresh_block_list(select_last=True)
        self.update_preview()

    def delete_selected_block(self) -> None:
        current_row = self.block_list.currentRow()
        if 0 <= current_row < len(self.document.blocks):
            del self.document.blocks[current_row]
            self._refresh_block_list(select_row=max(0, current_row - 1))
            self.update_preview()

    # UI updates
    def _refresh_block_list(self, select_last: bool = False, select_row: int | None = None) -> None:
        self.block_list.clear()
        for idx, block in enumerate(self.document.blocks):
            title = "Text" if isinstance(block, TextBlock) else "Formula"
            item = QListWidgetItem(f"{idx + 1}. {title}")
            self.block_list.addItem(item)
        if self.document.blocks:
            if select_last:
                self.block_list.setCurrentRow(len(self.document.blocks) - 1)
            elif select_row is not None:
                self.block_list.setCurrentRow(select_row)
            else:
                self.block_list.setCurrentRow(0)

    def on_block_selected(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        row = self.block_list.currentRow()
        if row < 0 or row >= len(self.document.blocks):
            self.editor.clear()
            return
        block = self.document.blocks[row]
        self.editor.blockSignals(True)
        self.editor.setPlainText(block.raw)
        self.editor.blockSignals(False)

    def on_editor_changed(self) -> None:
        row = self.block_list.currentRow()
        if row < 0 or row >= len(self.document.blocks):
            return
        block = self.document.blocks[row]
        block.raw = self.editor.toPlainText()
        if isinstance(block, FormulaBlock):
            block.evaluate()
        self.update_preview()

    def update_preview(self) -> None:
        """Render the document into the web view with MathJax."""
        html_content = self.document.to_html(renderer=self.renderer)
        self.preview.setHtml(html_content)

    # Toolbar helpers
    def _build_toolbar(self) -> QWidget:
        """Create a small toolbar with math operators and unit picker."""

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 4)

        ops = [
            ("+", " + "),
            ("-", " - "),
            ("\u00d7", " * "),
            ("\u00f7", " / "),
            ("^", " ** "),
            ("\u221a", "sqrt()"),
        ]
        for label, snippet in ops:
            btn = QToolButton()
            btn.setText(label)
            btn.setToolTip(f"Insert {label}")
            btn.clicked.connect(lambda _=False, s=snippet: self.insert_snippet(s))
            layout.addWidget(btn)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(COMMON_UNITS)
        unit_btn = QToolButton()
        unit_btn.setText("Unit")
        unit_btn.setToolTip("Insert selected unit")
        unit_btn.clicked.connect(self.insert_selected_unit)

        layout.addWidget(self.unit_combo)
        layout.addWidget(unit_btn)
        layout.addStretch()
        return container

    def insert_snippet(self, text: str) -> None:
        """Insert a math snippet at the current cursor position."""

        cursor = self.editor.textCursor()
        cursor.insertText(text)
        self.editor.setTextCursor(cursor)

    def insert_selected_unit(self) -> None:
        """Insert the unit chosen from the combo."""

        unit = self.unit_combo.currentText()
        self.insert_snippet(f" {unit}")
