from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenuBar,
    QRadioButton,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QAction, QKeySequence
from converter.engine import PDFConverter
import os

from converter.ai_agent import AIAgent
from gui.notebook_tab import NotebookTab


class SettingsDialog(QDialog):
    """Dialog for configuring OpenAI credentials and model."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = getattr(parent, "settings", QSettings("MyCompany", "PDFtoMD"))

        layout = QVBoxLayout(self)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        layout.addWidget(QLabel("OpenAI API Key"))
        layout.addWidget(self.api_key_input)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
        layout.addWidget(QLabel("Model"))
        layout.addWidget(self.model_combo)

        layout.addWidget(QLabel("MathJax source (for preview/export)"))
        mathjax_row = QHBoxLayout()
        self.mathjax_cdn_radio = QRadioButton("Use CDN (online)")
        self.mathjax_local_radio = QRadioButton("Use local bundle")
        mathjax_row.addWidget(self.mathjax_cdn_radio)
        mathjax_row.addWidget(self.mathjax_local_radio)
        layout.addLayout(mathjax_row)

        path_row = QHBoxLayout()
        self.mathjax_path_input = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_mathjax_bundle)
        path_row.addWidget(self.mathjax_path_input, 1)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        self.hide_logs_checkbox = QCheckBox("Hide log panel in exports")
        layout.addWidget(self.hide_logs_checkbox)

        self._load_render_settings()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_api_key(self):
        return self.api_key_input.text().strip()

    def get_model(self):
        return self.model_combo.currentText()

    def get_mathjax_mode(self):
        return "local" if self.mathjax_local_radio.isChecked() else "cdn"

    def get_mathjax_path(self):
        return self.mathjax_path_input.text().strip()

    def get_hide_logs(self):
        return self.hide_logs_checkbox.isChecked()

    def _load_render_settings(self):
        mode = self.settings.value("render/mathjax_mode", "cdn")
        path = self.settings.value("render/mathjax_path", "")
        hide_logs = self.settings.value("render/hide_logs", False)

        self.mathjax_cdn_radio.setChecked(mode != "local")
        self.mathjax_local_radio.setChecked(mode == "local")
        self.mathjax_path_input.setText(path)
        if isinstance(hide_logs, str):
            hide_logs = hide_logs.lower() in {"1", "true", "yes"}
        self.hide_logs_checkbox.setChecked(bool(hide_logs))
        self._update_mathjax_controls()

        self.mathjax_cdn_radio.toggled.connect(self._update_mathjax_controls)
        self.mathjax_local_radio.toggled.connect(self._update_mathjax_controls)

    def _update_mathjax_controls(self):
        use_local = self.mathjax_local_radio.isChecked()
        self.mathjax_path_input.setEnabled(use_local)

    def _browse_mathjax_bundle(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MathJax bundle (mathjax.js)",
            "",
            "JavaScript Files (*.js);;All Files (*)",
        )
        if path:
            self.mathjax_path_input.setText(path)
            self.mathjax_local_radio.setChecked(True)

class ConversionWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, pdf_path, api_key=None, model_name='gpt-4o'):
        super().__init__()
        self.pdf_path = pdf_path
        self.api_key = api_key
        self.model_name = model_name
        self.converter = PDFConverter()

    def run(self):
        try:
            result = self.converter.convert(self.pdf_path, progress_callback=self.progress.emit, ai_api_key=self.api_key, ai_model=self.model_name)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF to Markdown Converter")
        self.resize(600, 500)
        
        # Persistent Settings
        self.settings = QSettings("MyCompany", "PDFtoMD")
        self.api_key = self.settings.value("openai_api_key", "")
        self.ai_model = self.settings.value("openai_model", "gpt-4o")
        
        self.file_queue = []
        self.total_files = 0
        self.current_file_index = 0
        
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self._build_menu_bar()

        # Tabs: Notebook first (default), then PDF to Markdown
        self.notebook_tab = NotebookTab(self)
        self.tab_widget.addTab(self.notebook_tab, "Calculation Notebook")

        self.pdf_tab = QWidget()
        self.tab_widget.addTab(self.pdf_tab, "PDF to Markdown")
        self.tab_widget.setCurrentIndex(0)

        self.pdf_layout = QVBoxLayout(self.pdf_tab)
        self.pdf_layout.setSpacing(20)
        self.pdf_layout.setContentsMargins(40, 40, 40, 40)

        # Top Bar (Split only; settings moved to menu)
        top_layout = QHBoxLayout()

        self.split_btn = QPushButton("Split PDF")
        self.split_btn.clicked.connect(self.split_pdf_dialog)
        top_layout.addWidget(self.split_btn)

        top_layout.addStretch()

        self.pdf_layout.addLayout(top_layout)

        # Drop Area
        self.label = QLabel("Drag & Drop PDF files here")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 10px;
                padding: 20px;
                font-size: 18px;
                color: #ddd;
                background-color: #333;
            }
            QLabel:hover {
                border-color: #3498db;
                background-color: #3d3d3d;
            }
        """)
        self.pdf_layout.addWidget(self.label)

        # Queue Info
        self.queue_label = QLabel("Queue: 0 files")
        self.queue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_layout.addWidget(self.queue_label)

        # Queue controls
        queue_controls = QHBoxLayout()

        # AI Toggle
        self.ai_checkbox = QCheckBox("Use AI Agent (OpenAI)")
        self.ai_checkbox.setToolTip("Requires API Key in Settings. Slower but better for complex PDFs.")
        queue_controls.addWidget(self.ai_checkbox)

        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.setEnabled(False)
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_controls.addWidget(self.clear_queue_btn)

        queue_controls.addStretch()
        self.pdf_layout.addLayout(queue_controls)

        # Start Button
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_batch_processing)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.pdf_layout.addWidget(self.start_btn)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        self.pdf_layout.addWidget(self.progress)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_layout.addWidget(self.status_label)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _build_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menu_bar.addMenu("&Settings")
        preferences_action = QAction("Preferences...", self)
        preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.triggered.connect(self.open_settings)
        settings_menu.addAction(preferences_action)

        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: QMessageBox.information(self, "About", "PDF to Markdown Converter + Notebook"))
        help_menu.addAction(about_action)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.api_key_input.setText(self.api_key)
        dialog.model_combo.setCurrentText(self.ai_model)
        
        if dialog.exec():
            new_key = dialog.get_api_key()
            new_model = dialog.get_model()
            new_mathjax_mode = dialog.get_mathjax_mode()
            new_mathjax_path = dialog.get_mathjax_path()
            new_hide_logs = dialog.get_hide_logs()
            
            changes = False
            if new_key != self.api_key:
                self.api_key = new_key
                self.settings.setValue("openai_api_key", self.api_key)
                changes = True
                
            if new_model != self.ai_model:
                self.ai_model = new_model
                self.settings.setValue("openai_model", self.ai_model)
                changes = True

            prev_mode = self.settings.value("render/mathjax_mode", "cdn")
            prev_path = self.settings.value("render/mathjax_path", "")
            prev_hide_logs = self.settings.value("render/hide_logs", False)
            prev_hide_logs_bool = (
                prev_hide_logs.lower() in {"1", "true", "yes"} if isinstance(prev_hide_logs, str) else bool(prev_hide_logs)
            )

            if new_mathjax_mode != prev_mode:
                self.settings.setValue("render/mathjax_mode", new_mathjax_mode)
                changes = True
            if new_mathjax_path != prev_path:
                self.settings.setValue("render/mathjax_path", new_mathjax_path)
                changes = True
            if bool(new_hide_logs) != prev_hide_logs_bool:
                self.settings.setValue("render/hide_logs", bool(new_hide_logs))
                changes = True
                
            if changes:
                QMessageBox.information(self, "Settings", "Settings saved successfully.")

    def split_pdf_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF to Split", "", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        pages, ok = QInputDialog.getInt(self, "Split PDF", "Pages per chunk:", 50, 1, 1000)
        if ok:
            try:
                converter = PDFConverter()
                chunks = converter.split_pdf(file_path, pages)
                QMessageBox.information(self, "Success", f"Created {len(chunks)} parts in the same folder.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to split PDF:\n{str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            self.file_queue.extend(pdf_files)
            self.update_queue_ui()
        else:
            self.status_label.setText("Please drop PDF files")
            
    def update_queue_ui(self):
        count = len(self.file_queue)
        self.queue_label.setText(f"Queue: {count} files ready")
        self.start_btn.setEnabled(count > 0)
        self.start_btn.setText(f"Start Processing ({count})")
        self.clear_queue_btn.setEnabled(count > 0)

    def clear_queue(self):
        self.file_queue = []
        self.update_queue_ui()
        self.label.setText("Drag & Drop PDF files here")
        self.status_label.clear()
        self.progress.hide()
        self.setAcceptDrops(True)
        self.split_btn.setEnabled(True)

    def start_batch_processing(self):
        if not self.file_queue:
            return
            
        self.total_files = len(self.file_queue)
        self.current_file_index = 0
        self.start_btn.setEnabled(False)
        self.split_btn.setEnabled(False)
        self.start_next_conversion()

    def start_next_conversion(self):
        if self.current_file_index < self.total_files:
            file_path = self.file_queue[self.current_file_index]
            self.start_conversion(file_path)
        else:
            self.status_label.setText("All files processed successfully!")
            self.label.setText("Drag & Drop PDF files here")
            self.progress.hide()
            self.setAcceptDrops(True)
            self.file_queue = []
            self.update_queue_ui()
            self.split_btn.setEnabled(True)
            QMessageBox.information(self, "Batch Complete", f"Processed {self.total_files} files.")

    def start_conversion(self, file_path):
        use_ai = self.ai_checkbox.isChecked()
        if use_ai and not self.api_key:
            QMessageBox.warning(self, "Missing API Key", "Please enter your OpenAI API Key in Settings to use AI mode.")
            self.start_btn.setEnabled(True)
            self.split_btn.setEnabled(True)
            return

        mode_text = "AI Agent" if use_ai else "Standard"
        file_name = os.path.basename(file_path)
        self.label.setText(f"Converting ({self.current_file_index + 1}/{self.total_files}): {file_name}...")
        self.progress.setValue(0)
        self.progress.show()
        self.status_label.setText(f"Processing {file_name}...")
        self.setAcceptDrops(False) 
        
        api_key_to_use = self.api_key if use_ai else None
        self.worker = ConversionWorker(file_path, api_key=api_key_to_use, model_name=self.ai_model)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.start()

    def on_conversion_finished(self, message):
        self.current_file_index += 1
        self.start_next_conversion()

    def on_conversion_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Failed to convert file:\n{error_msg}")
        self.current_file_index += 1
        self.start_next_conversion()
