from PySide6.QtWidgets import QApplication

def apply_styles(app: QApplication):
    # Use Fusion engine as base and rely on the default light palette
    app.setStyle("Fusion")

    # Optional light tweaks for tooltips and progress bars
    app.setStyleSheet("""
        QToolTip {
            color: #000000;
            background-color: #e6f0ff;
            border: 1px solid #2a82da;
        }
        QProgressBar {
            border: 1px solid #bfc7d5;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #2a82da;
            width: 20px;
        }
    """)
