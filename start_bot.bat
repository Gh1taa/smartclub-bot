@echo off
rem Double-click this file to start the Smart Club bot on this PC. Close the window to stop it.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo First start: installing the bot, please wait...
    python -m venv .venv || goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)
".venv\Scripts\python.exe" -u bot.py
pause
exit /b

:error
echo Installation failed. Is Python installed? (python.org, tick "Add python.exe to PATH")
pause
