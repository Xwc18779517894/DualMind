@echo off
setlocal
cd /d "%~dp0"
rem Exit any running DualMind instance before using this launcher.
rem Clash Verge local HTTP/mixed proxy port verified on this computer: 7897.
set "DUALMIND_GEMINI_PROXY=http://127.0.0.1:7897"
call "%~dp0launch.cmd" --browser
