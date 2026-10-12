@echo off
setlocal
cd /d "%~dp0"
set "DUALMIND_PYTHONW="
if exist "%~dp0.venv\Scripts\pythonw.exe" set "DUALMIND_PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
if not defined DUALMIND_PYTHONW if exist "%LocalAppData%\Programs\Python\Python313\pythonw.exe" set "DUALMIND_PYTHONW=%LocalAppData%\Programs\Python\Python313\pythonw.exe"
if not defined DUALMIND_PYTHONW for /f "delims=" %%P in ('where pythonw 2^>nul') do if not defined DUALMIND_PYTHONW set "DUALMIND_PYTHONW=%%P"
if not defined DUALMIND_PYTHONW for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if exist "%%~dpPpythonw.exe" set "DUALMIND_PYTHONW=%%~dpPpythonw.exe"
if not defined DUALMIND_PYTHONW (
    echo Python was not found. Install Python 3.11+ and run setup.cmd.
    pause
    exit /b 1
)
start "" "%DUALMIND_PYTHONW%" "%~dp0dualmind_web.py" %*
