@echo off
title HBG VoLTE and IMS Fixer - Build Release Manager

echo ====================================================================
echo   HBG VoLTE and IMS Fixer - BO DONG GOI RELEASE 1-CLICK TU DONG
echo ====================================================================
echo.

cd /d "%~dp0"
python build_version.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co loi xay ra trong qua trinh Build Release!
    echo Vui long kiem tra lai Python, PyInstaller va moi truong Git.
)

echo.
pause
