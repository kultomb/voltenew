@echo off
chcp 65001 > NUL
title HBG VoLTE ^& IMS Fixer Tool (Standalone)

echo ========================================================
echo   DANG KHOI CHAY CONG CU SUA LOI VoLTE CHUYEN DUNG...
echo ========================================================
echo.

cd /d "%~dp0"
python volte_fixer_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the chay volte_fixer_gui.py!
    echo Vui long kiem tra lai Python va thu vien customtkinter.
    pause
)
