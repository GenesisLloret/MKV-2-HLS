import subprocess
import base64
import json
import asyncio
from .utils import ffprobe_path, ffmpeg_path

class VideoPath:
    def __init__(self, file_path: str):
        self.file_path = file_path

async def obtener_info_ffprobe(video: VideoPath) -> dict:
    comando = [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video.file_path]
    try:
        proceso = await asyncio.create_subprocess_exec(*comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)  # Cambia text a False
        stdout, stderr = await proceso.communicate()
        if proceso.returncode == 0:
            return json.loads(stdout.decode())  # Decodifica la salida binaria
        else:
            raise Exception(stderr.decode())  # Decodifica el error binario
    except Exception as e:
        print(f"Error al obtener información de ffprobe: {e}")
        raise e

