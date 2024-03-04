import sys, os, base64, threading, base64, json, subprocess, winreg, secrets, logging, uvicorn
from typing import List
from pydantic import BaseModel
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget
from PySide6.QtCore import QUrl, Qt, QByteArray, QTimer, QObject, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from loads import FAVICON
from lenguajes import LENGUAJES

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

static_path = resource_path('static')
urls_para_abrir = []
app = FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"], allow_credentials=True,allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=static_path), name="static")
security = HTTPBasic()
username = secrets.token_hex(4)
password = secrets.token_hex(8)

# CLASES
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
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if "popover" in message:
            return
        else:
            super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)
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
class UnicodeJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content,ensure_ascii=False,indent=2).encode('utf-8')

class VideoPath(BaseModel):
    file_path: str
    

# DEFINICIONES
async def obtener_info_ffprobe(ruta_video: str) -> dict:
    comando = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', ruta_video]
    try:
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, encoding='utf-8')
        return json.loads(resultado.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar ffprobe: {e.stderr}")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error de decodificación Unicode: {e}")
    
async def generar_thumbnail_base64(ruta_video: str, tiempo: str = "00:00:01", tamaño: str = "320x240") -> str:
    comando = ['ffmpeg','-i', ruta_video,'-ss', tiempo,'-vf', f'scale={tamaño}','-vframes', '1','-f', 'image2pipe','-c:v', 'png','-']
    try:
        resultado = subprocess.check_output(comando)
        thumbnail_base64 = base64.b64encode(resultado).decode("utf-8")
        return thumbnail_base64
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el thumbnail: {e.stderr}")
    
async def generar_thumbnails_base64(ruta_video: str, duracion: int) -> list:
    thumbnails_base64 = []
    segmento = duracion // 5
    for i in range(1, 4):
        tiempo = segmento * i
        tiempo_str = f"{tiempo//3600}:{(tiempo%3600)//60}:{tiempo%60}"
        thumbnail_base64 = await generar_thumbnail_base64(ruta_video, tiempo=tiempo_str)
        thumbnails_base64.append(thumbnail_base64)
    return thumbnails_base64

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# RUTAS FASTAPI
@app.get("/secure-data")
async def read_secure_data(username: str = Depends(get_current_username)):
    return {"message": "Acceso a datos seguros concedido", "user": username}

@app.get("/")
async def read_root():
    if sys.platform.startswith('win'):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            mode, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            if mode == 1:
                CSS_preset = '//localhost:15580/static/light.css'
            else:
                CSS_preset = '//localhost:15580/static/dark.css'
        except Exception as e:
                CSS_preset = '//localhost:15580/static/light.css'
    elif sys.platform.startswith('darwin'):
        try:
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
            darkison = 'Dark' in result.stdout
            if darkison == True:
                CSS_preset = '//localhost:15580/static/light.css'
            else:
                CSS_preset = '//localhost:15580/static/dark.css'
        except subprocess.CalledProcessError:
            CSS_preset = '//localhost:15580/static/light.css'
    elif sys.platform.startswith('linux'):
        try:
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], capture_output=True, text=True)
            darkison = 'dark' in result.stdout.lower()
            if darkison == True:
                CSS_preset = '//localhost:15580/static/light.css'
            else:
                CSS_preset = '//localhost:15580/static/dark.css'
        except Exception as e:
            CSS_preset = '//localhost:15580/static/light.css'
    else:
        CSS_preset = '//localhost:15580/static/light.css'   
    html_content = f"""
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="shortcut icon" href="data:image/x-icon;base64,{FAVICON}" />
            <link rel="stylesheet" type="text/css" href="{CSS_preset}" />
            <link rel="stylesheet" type="text/css" href="//localhost:15580/static/style.css" />
            <script type="text/javascript" src="//localhost:15580/static/qwebchannel.js"></script>
            
        </head>
        <body>
            <div id="app">
                <header><h1>Conversor de Videos MKV a HLS</h1></header>
                <main>
                    <section id="drag-and-drop-area">
                        <div id="drop_zone"><p>Arrastra y suelta tus archivos MKV aquí</p></div>
                    </section>
                    <section id="file-details"></section>
                </main>
                <footer>
                    <p>Conversor de Videos MKV. Creado por <a href="#" onclick="openNewWindow('https://github.com/GenesisLloret');">Génesis Lloret</a> .</p>
                </footer>
            </div>
            <script>
                const username = "{username}";
                const password = "{password}";
                console.log("Username: {username}","Password: {password}")
            </script>
            <script src="//localhost:15580/static/scripts.js"></script>
        </body>
        </html>
    """
    return HTMLResponse(content=html_content)

@app.put("/open-new-window")
async def open_new_window(url: str):
    global urls_para_abrir
    urls_para_abrir.append(url)
    return {"message": "Solicitud para abrir ventana recibida", "url": url}

@app.post("/procesar-video")
async def procesar_video(video_path: VideoPath, username: str = Depends(get_current_username)):
    file_path = video_path.file_path
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(result.stderr)
        info_video = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
        raise HTTPException(status_code=500, detail="Error al ejecutar ffprobe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return info_video

@app.get("/languages/{search_text}")
async def search_language_by_name_or_id(search_text: str):
    try:
        filtered_languages = [
            lang for lang in LENGUAJES
            if search_text.lower() in lang.get('native', '').lower() or search_text.lower() in lang.get('label', '').lower()
        ]
        sorted_languages = sorted(filtered_languages, key=lambda lang: (
            search_text.lower() not in lang.get('native', '').lower(),
            search_text.lower() not in lang.get('label', '').lower()
        ))
        return UnicodeJSONResponse(content={"languages": sorted_languages})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"Error processing the request: {e}"})
    
@app.get("/languages/tag/{code}")
async def get_language_by_code(code: str):
    for language in LENGUAJES:
        if code in language.get('iso6393', []) or code in language.get('iso6392', []) or code in language.get('iso6391', []) or code in language.get('wmCode', []):
            return language
    raise HTTPException(status_code=404, detail="Language not found")

@app.get("/languages/")
async def read_languages():
    try:
        return UnicodeJSONResponse(content={"languages": LENGUAJES})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"Error processing the request: {e}"})

log_file = open('uvicorn_log.txt', 'w')
sys.stdout = log_file
sys.stderr = log_file
configServer = uvicorn.Config(app=app, host="0.0.0.0", port=15580, access_log=False)
server = uvicorn.Server(config=configServer)
def run_server():
    logging.info("Iniciando servidor Uvicorn...")
    server.run()
def stop_server():
    logging.info("Deteniendo el servidor Uvicorn...")
    server.should_exit = True
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