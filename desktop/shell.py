import sys
import os
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile

class AgnuxShellWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGNUX OS v2.0 - Shell Cognitivo")
        self.resize(1280, 800)
        
        # Frameless option can be enabled, but native border keeps desktop resizing robust
        # self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Configure WebEngine Settings for local file access & CORS
        profile = QWebEngineProfile.defaultProfile()
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        # Setup layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create WebEngineView
        self.webView = QWebEngineView(centralWidget)
        layout.addWidget(self.webView)
        
        # Load local index.html
        baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        htmlPath = os.path.join(baseDir, "frontend", "index.html")
        fileUrl = QUrl.fromLocalFile(htmlPath)
        
        print(f"🖥️ [DESKTOP] Cargando interfaz desde: {fileUrl.toString()}")
        self.webView.load(fileUrl)

def launchShell():
    # Set environment variables for smooth Qt WebEngine rendering
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    
    app = QApplication(sys.argv)
    window = AgnuxShellWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launchShell()
