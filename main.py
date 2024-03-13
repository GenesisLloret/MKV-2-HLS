import sys, fastapi, os, base64, threading, json, subprocess,  winreg,  secrets,  logging,  uvicorn
from loads import FAVICON
from lenguajes import LENGUAJES
from typing import List
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget
from PySide6.QtCore import QUrl, Qt, QByteArray, QTimer, QObject, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings
from sources.ffmpeg_utils import ffprobe_path, ffmpeg_path
from sources.processing import VideoPath
from sources.api import run_server, stop_server, urls_para_abrir

class CustomWebEngineView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            print("Ruta del archivo arrastrado:", filepath.encode('utf-8'))
            self.page().runJavaScript(f"filePaths.push('{filepath}');")
            self.page().runJavaScript(f"displayFilePaths('{filepath}');")
        event.acceptProposedAction()

    def contextMenuEvent(self, event):
        pass

class FileHandler(QObject):
    @Slot(str, result=str)
    def handleFileDrop(self, filePath):
        print(f"Archivo recibido: {filePath}")
        return filePath

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.open_windows = []
        self.setWindowTitle('Navegador con PySide6')
        self.browser = CustomWebEngineView(self)
        self.setCentralWidget(self.browser)
        self.browser.load(QUrl("http://localhost:15580"))
        self.dev_tools_window = None
        self.setWindowIconFromBase64(FAVICON)
        self.check_for_new_windows_timer = QTimer(self)
        self.check_for_new_windows_timer.timeout.connect(self.check_for_new_windows)
        self.check_for_new_windows_timer.start(1000)
        self.channel = QWebChannel(self.browser.page())
        self.fileHandler = FileHandler()
        self.channel.registerObject("fileHandler", self.fileHandler)
        self.browser.page().setWebChannel(self.channel)
        self.setAcceptDrops(True)

    def check_for_new_windows(self):
        global urls_para_abrir
        while urls_para_abrir:
            url = urls_para_abrir.pop(0)
            self.open_new_window(url)

    def open_new_window(self, url):
        web_window = CustomWebEngineView()
        settings = self.browser.page().settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        web_window.setUrl(QUrl(url))
        web_window.show()
        self.open_windows.append(web_window)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_I and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.toggle_dev_tools()
        else:
            super().keyPressEvent(event)

    def toggle_dev_tools(self):
        if not self.dev_tools_window:
            self.dev_tools_window = QDockWidget("Dev Tools", self)
            self.dev_tools = QWebEngineView()
            self.dev_tools_window.setWidget(self.dev_tools)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.dev_tools_window)
            self.browser.page().setDevToolsPage(self.dev_tools.page())
        self.dev_tools_window.setVisible(not self.dev_tools_window.isVisible())

    def setWindowIconFromBase64(self, base64_icon):
        icon_bytes = base64.b64decode(base64_icon)
        icon_qbytearray = QByteArray(icon_bytes)
        icon_pixmap = QPixmap()
        icon_pixmap.loadFromData(icon_qbytearray)
        self.setWindowIcon(QIcon(icon_pixmap))

    def closeEvent(self, event):
        stop_server()
        event.accept()
        log_file.close()

if __name__ == "__main__":
    logging.info("Iniciando aplicación...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    app = QApplication(sys.argv)
    window = MainWindow()
    availableGeometry = window.screen().availableGeometry()
    window.resize(availableGeometry.width() * 2 / 3, availableGeometry.height() * 2 / 3)
    window.show()
    sys.exit(app.exec())
