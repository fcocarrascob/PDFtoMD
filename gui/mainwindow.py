from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QProgressBar, QMessageBox, QPushButton, QDialog, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QComboBox, QFileDialog, QInputDialog
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from converter.engine import PDFConverter
import os

from converter.ai_agent import AIAgent

# ... (SettingsDialog remains unchanged) ...

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
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Top Bar (Settings & Split)
        top_layout = QHBoxLayout()
        
        self.split_btn = QPushButton("Split PDF")
        self.split_btn.clicked.connect(self.split_pdf_dialog)
        top_layout.addWidget(self.split_btn)
        
        top_layout.addStretch()
        
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_btn)
        
        self.layout.addLayout(top_layout)
        
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
        self.layout.addWidget(self.label)
        
        # Queue Info
        self.queue_label = QLabel("Queue: 0 files")
        self.queue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.queue_label)
        
        # AI Toggle
        self.ai_checkbox = QCheckBox("Use AI Agent (OpenAI)")
        self.ai_checkbox.setToolTip("Requires API Key in Settings. Slower but better for complex PDFs.")
        self.layout.addWidget(self.ai_checkbox)
        
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
        self.layout.addWidget(self.start_btn)
        
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
