from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QProgressBar, QMessageBox, QPushButton, QDialog, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QComboBox
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from converter.engine import PDFConverter
import os

from converter.ai_agent import AIAgent

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 150)
        
        layout = QVBoxLayout(self)
        
        # API Key Input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter OpenAI API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("OpenAI API Key:"))
        layout.addWidget(self.api_key_input)
        
        # Model Selector
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o", "gpt-4o-mini"])
        layout.addWidget(QLabel("Select AI Model:"))
        layout.addWidget(self.model_combo)
        
        # Test Button
        self.test_btn = QPushButton("Test Key")
        self.test_btn.clicked.connect(self.test_key)
        layout.addWidget(self.test_btn)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def test_key(self):
        key = self.api_key_input.text()
        model = self.model_combo.currentText()
        if not key:
            QMessageBox.warning(self, "Warning", "Please enter a key first.")
            return
            
        self.test_btn.setText("Testing...")
        self.test_btn.setEnabled(False)
        QApplication.processEvents()
        
        agent = AIAgent(key, model_name=model)
        is_valid, msg = agent.validate_key()
        
        self.test_btn.setText("Test Key")
        self.test_btn.setEnabled(True)
        
        if is_valid:
            QMessageBox.information(self, "Success", f"API Key is valid! (Model: {model})")
        else:
            QMessageBox.critical(self, "Error", f"Invalid Key:\n{msg}")
        
    def get_api_key(self):
        return self.api_key_input.text()
        
    def get_model(self):
        return self.model_combo.currentText()

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
        self.resize(600, 450)
        
        # Persistent Settings
        self.settings = QSettings("MyCompany", "PDFtoMD")
        self.api_key = self.settings.value("openai_api_key", "")
        self.ai_model = self.settings.value("openai_model", "gpt-4o")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Top Bar (Settings)
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_btn)
        self.layout.addLayout(top_layout)
        
        # Drop Area
        self.label = QLabel("Drag & Drop PDF here")
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
        self.layout.addWidget(self.label)
        
        # AI Toggle
        self.ai_checkbox = QCheckBox("Use AI Agent (OpenAI)")
        self.ai_checkbox.setToolTip("Requires API Key in Settings. Slower but better for complex PDFs.")
        self.layout.addWidget(self.ai_checkbox)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        self.layout.addWidget(self.progress)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Enable drag and drop
        self.setAcceptDrops(True)

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.api_key_input.setText(self.api_key)
        dialog.model_combo.setCurrentText(self.ai_model)
        
        if dialog.exec():
            new_key = dialog.get_api_key()
            new_model = dialog.get_model()
            
            changes = False
            if new_key != self.api_key:
                self.api_key = new_key
                self.settings.setValue("openai_api_key", self.api_key)
                changes = True
                
            if new_model != self.ai_model:
                self.ai_model = new_model
                self.settings.setValue("openai_model", self.ai_model)
                changes = True
                
            if changes:
                QMessageBox.information(self, "Settings", "Settings saved successfully.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        if pdf_files:
            self.process_queue(pdf_files)
        else:
            self.status_label.setText("Please drop PDF files")

    def process_queue(self, files):
        self.file_queue = files
        self.total_files = len(files)
        self.current_file_index = 0
        self.start_next_conversion()

    def start_next_conversion(self):
        if self.current_file_index < self.total_files:
            file_path = self.file_queue[self.current_file_index]
            self.start_conversion(file_path)
        else:
            self.status_label.setText("All files processed successfully!")
            self.label.setText("Drag & Drop PDF here")
            self.progress.hide()
            self.setAcceptDrops(True)
            QMessageBox.information(self, "Batch Complete", f"Processed {self.total_files} files.")

    def start_conversion(self, file_path):
        use_ai = self.ai_checkbox.isChecked()
        if use_ai and not self.api_key:
            QMessageBox.warning(self, "Missing API Key", "Please enter your OpenAI API Key in Settings to use AI mode.")
            return

        mode_text = "AI Agent" if use_ai else "Standard"
        file_name = os.path.basename(file_path)
        self.label.setText(f"Converting ({self.current_file_index + 1}/{self.total_files}): {file_name}...")
        self.progress.setValue(0)
        self.progress.show()
        self.status_label.setText(f"Processing {file_name}...")
        self.setAcceptDrops(False) # Disable drops during conversion
        
        api_key_to_use = self.api_key if use_ai else None
        self.worker = ConversionWorker(file_path, api_key=api_key_to_use, model_name=self.ai_model)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.start()

    def on_conversion_finished(self, message):
        self.current_file_index += 1
        if self.current_file_index < self.total_files:
            self.start_next_conversion()
        else:
            self.start_next_conversion() # Will trigger completion logic

    def on_conversion_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Failed to convert file:\n{error_msg}")
        # Continue with next file even if one fails
        self.current_file_index += 1
        self.start_next_conversion()
