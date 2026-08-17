@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (python app\claude_pojia.py gui) else (py app\claude_pojia.py gui)
