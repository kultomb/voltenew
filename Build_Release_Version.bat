@echo off
chcp 65001 > NUL
title HBG VoLTE ^& IMS Fixer — Build Release Manager

echo ========================================================
echo   HBG VoLTE ^& IMS Fixer — BỘ CÔNG CỤ BUILD PHIÊN BẢN TỰ ĐỘNG
echo ========================================================
echo.

cd /d "%~dp0"
python build_version.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co loi xay ra trong qua trinh Build Release!
    echo Vui long kiem tra lai Python, PyInstaller va Git environment.
)

echo.
pause
