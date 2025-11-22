"""Notebook tab with SymPy-powered formula preview."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QComboBox,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
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
        self._setup_shortcuts()
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

        export_html_btn = QPushButton("Export HTML")
        export_html_btn.clicked.connect(self.export_html)
        export_md_btn = QPushButton("Export Markdown")
        export_md_btn.clicked.connect(self.export_markdown)

        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(lambda: self.move_selected_block(-1))
        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(lambda: self.move_selected_block(1))

        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo_action)
        redo_btn = QPushButton("Redo")
        redo_btn.clicked.connect(self.redo_action)

        save_btn = QPushButton("Save Notebook")
        save_btn.clicked.connect(self.save_document)
        load_btn = QPushButton("Load Notebook")
        load_btn.clicked.connect(self.load_document)

        left_layout.addWidget(add_text_btn)
        left_layout.addWidget(add_formula_btn)
        left_layout.addWidget(delete_btn)
        left_layout.addWidget(export_html_btn)
        left_layout.addWidget(export_md_btn)
        left_layout.addWidget(move_up_btn)
        left_layout.addWidget(move_down_btn)
        left_layout.addWidget(undo_btn)
        left_layout.addWidget(redo_btn)
        left_layout.addWidget(save_btn)
        left_layout.addWidget(load_btn)
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

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Up"), self, activated=lambda: self.move_selected_block(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self, activated=lambda: self.move_selected_block(1))
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.undo_action)
        QShortcut(QKeySequence.StandardKey.Redo, self, activated=self.redo_action)

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
            self.document.delete_block(current_row)
            self._refresh_block_list(select_row=max(0, current_row - 1))
            self.update_preview()

    def move_selected_block(self, direction: int) -> None:
        current_row = self.block_list.currentRow()
        if current_row < 0:
            return
        target_row = current_row + direction
        if self.document.move_block(current_row, target_row):
            self._refresh_block_list(select_row=target_row)
            self.update_preview()

    def undo_action(self) -> None:
        if self.document.undo():
            self._refresh_block_list(select_row=min(self.block_list.currentRow(), len(self.document.blocks) - 1))
            self.update_preview()

    def redo_action(self) -> None:
        if self.document.redo():
            self._refresh_block_list(select_row=min(self.block_list.currentRow(), len(self.document.blocks) - 1))
            self.update_preview()

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
            self._refresh_block_list()
            self.update_preview()
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Load Failed", str(exc))

    # UI updates
    def _refresh_block_list(self, select_last: bool = False, select_row: int | None = None) -> None:
        self.block_list.clear()
        for idx, block in enumerate(self.document.blocks):
            title = "Text" if isinstance(block, TextBlock) else "Formula"
            item = QListWidgetItem(f"{idx + 1}. {title} [{block.block_id[:6]}]")
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

    def export_html(self) -> None:
        """Persist the rendered notebook to an HTML file."""

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Notebook as HTML", "", "HTML Files (*.html)"
        )
        if not path:
            return

        mathjax_path, _ = QFileDialog.getOpenFileName(
            self,
            "Optional MathJax bundle (leave empty to use CDN)",
            "",
            "JavaScript Files (*.js);;All Files (*)",
        )
        if not mathjax_path:
            mathjax_path = None

        try:
            self.document.save_html(
                path,
                renderer=self.renderer,
                mathjax_path=mathjax_path,
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
