@echo off
chcp 65001 > NUL
title HBG VoLTE ^& IMS Fixer — Build Release Manager ⚡

echo ====================================================================
echo   ⚡ HBG VoLTE ^& IMS Fixer — BỘ ĐÓNG GÓI RELEASE 1-CLICK TỰ ĐỘNG
echo ====================================================================
echo.

cd /d "%~dp0"
python build_version.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LỖI] Có lỗi xảy ra trong quá trình Build Release!
    echo Vui lòng kiểm tra lại Python, PyInstaller và môi trường Git.
)

echo.
pause
