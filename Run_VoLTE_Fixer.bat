@echo off
title HBG VoLTE Fixer Tool - Python Test Runner
cd /d "%~dp0"

echo ====================================================================
echo   HBG VOLTE FIXER TOOL - CHE DO THU NGHIEM PYTHON
echo ====================================================================
echo.

python volte_fixer_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [CANH BAO LOI] MA LOI BAO VE: %ERRORLEVEL%
    echo Vui long kiem tra vet loi (Traceback) o tren.
    echo ====================================================================
    echo.
    pause
)
