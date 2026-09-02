@echo off
title HBG VoLTE Fixer - Universal Vendor Patcher
cd /d "%~dp0"

python vendor_patcher_gui.py

if errorlevel 1 (
    echo.
    echo --------------------------------------------------------------------
    echo   HBG VOLTE FIXER - DONG LENH CMD
    echo --------------------------------------------------------------------
    python vendor_engine.py
)

pause
