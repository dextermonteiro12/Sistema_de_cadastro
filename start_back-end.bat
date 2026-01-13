@echo off
echo Iniciando Backend...
cd %~dp0
call venv\Scripts\activate
python app.py
pause