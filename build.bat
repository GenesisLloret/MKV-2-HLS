@echo off
if exist main.spec del main.spec
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
pause
call venv\Scripts\activate
pyinstaller --onefile --noconsole --add-data "static/*;static/" --icon "static/favicon.ico" main.py
deactivate
pause
