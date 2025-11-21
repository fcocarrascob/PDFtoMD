import sys
from PySide6.QtWidgets import QApplication
from gui.mainwindow import MainWindow
from gui.styles import apply_styles

def main():
    app = QApplication(sys.argv)
    
    # Apply global styles
    apply_styles(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
