import os
import requests
import zipfile
import platform
import subprocess

# Función para verificar y descargar FFmpeg y FFprobe
def verificar_y_descargar_ffmpeg_ffprobe(directorio_bin="bin"):
    if not os.path.exists(directorio_bin):
        os.makedirs(directorio_bin)
    ffmpeg_executable = "ffmpeg" + (".exe" if platform.system() == "Windows" else "")
    ffprobe_executable = "ffprobe" + (".exe" if platform.system() == "Windows" else "")
    ffmpeg_path = os.path.join(directorio_bin, ffmpeg_executable)
    ffprobe_path = os.path.join(directorio_bin, ffprobe_executable)
    if os.path.isfile(ffmpeg_path) and os.path.isfile(ffprobe_path):
        print("ffmpeg y ffprobe ya están disponibles.")
        return ffmpeg_path, ffprobe_path
    arquitectura, _ = platform.architecture()
    os_name = platform.system().lower()
    arch_map = {
        ('linux', '32bit'): 'linux-32',
        ('linux', '64bit'): 'linux-64',
        ('windows', '32bit'): 'windows-32',
        ('windows', '64bit'): 'windows-64',
        ('darwin', '64bit'): 'osx-64',
    }
    machine = platform.machine()
    if 'arm' in machine:
        arch = 'linux-arm' + ('64' if '64' in machine else 'hf' if '7l' in machine else 'el')
    else:
        arch = arch_map.get((os_name, arquitectura))
        if arch is None:
            raise RuntimeError(f"Plataforma no soportada: {os_name}, Arquitectura: {arquitectura}")
    respuesta = requests.get("https://ffbinaries.com/api/v1/version/latest")
    data = respuesta.json()
    ffmpeg_url = data['bin'].get(arch, {}).get('ffmpeg')
    ffprobe_url = data['bin'].get(arch, {}).get('ffprobe')
    if not ffmpeg_url or not ffprobe_url:
        raise RuntimeError(f"No se encontraron URLs de descarga para la arquitectura: {arch}")
    descargar_y_descomprimir(ffmpeg_url, directorio_bin)
    descargar_y_descomprimir(ffprobe_url, directorio_bin)
    return ffmpeg_path, ffprobe_path

def descargar_y_descomprimir(url, directorio):
    nombre_zip = os.path.join(directorio, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(nombre_zip, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    with zipfile.ZipFile(nombre_zip, 'r') as zip_ref:
        zip_ref.extractall(directorio)
    os.remove(nombre_zip)

ffmpeg_path, ffprobe_path = verificar_y_descargar_ffmpeg_ffprobe()