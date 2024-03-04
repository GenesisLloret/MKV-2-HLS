@echo off
echo Creando entorno virtual...
python -m venv venv

echo Instalando dependencias desde requirements.txt...
.\venv\Scripts\python.exe -m pip install -r requirements.txt

echo Configuración completada.
pause
