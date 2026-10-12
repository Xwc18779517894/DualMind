@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo DualMind is ready. Open the launcher, then configure your models.
echo Codex CLI: npm install -g @openai/codex  then  codex login
pause
exit /b 0
:failed
echo Setup failed. Install Python 3.11+ from python.org and check your network.
pause
exit /b 1
