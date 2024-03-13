from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from loads import FAVICON
from lenguajes import LENGUAJES
from sources.processing import obtener_info_ffprobe, VideoPath
import secrets, os, sys, subprocess, base64, json, winreg, uvicorn, logging
from pydantic import BaseModel

class VideoPathRequest(BaseModel):
    video_path: str
    
class UnicodeJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')
    
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

username = secrets.token_hex(4)
password = secrets.token_hex(8)

app = FastAPI()
security = HTTPBasic()

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

static_path = resource_path('sources/static')


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

urls_para_abrir = []

app.mount(
    "/static",
    StaticFiles(directory=static_path),
    name="static",
)
security = HTTPBasic()


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
async def procesar_video(request: VideoPathRequest, username: str = Depends(get_current_username)):
    file_path = request.video_path
    video = VideoPath(file_path)
    try:
        info_video = await obtener_info_ffprobe(video)
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
