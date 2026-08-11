@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo  HBG AdBlocker - Build EXE (portable)
echo ========================================
echo.
echo Thu muc build: %CD%
echo (Chi build o day — KHONG dung ban trong "HBG ADS")
echo.
echo Goi y: dung build_installer.bat de them file Setup cai dat.
echo.

if not exist "icons\app_icon.ico" (
    echo LOI: Thieu icons\app_icon.ico
    echo Dat file .ico vao thu muc icons\ roi chay lai.
    goto :fail
)

echo [1/4] Cai dat phu thuoc...
pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/4] Tang phien ban va sinh metadata...
python scripts\prepare_build.py > build_version.tmp
if errorlevel 1 goto :fail
set /p HBG_VERSION=<build_version.tmp
for /f "skip=1 tokens=*" %%a in (build_version.tmp) do set HBG_EXE_BASENAME=%%a
del build_version.tmp
call build_env.bat
echo     Phien ban: %HBG_VERSION%
echo     Ten file:  %HBG_EXE_BASENAME%.exe
echo     Icon:      icons\app_icon.ico
echo.
echo [3/4] Build PyInstaller (icon .exe + runtime)...
pyinstaller HBGAdBlocker.spec --noconfirm --clean
if errorlevel 1 goto :fail

echo.
echo [4/4] Luu vao dist\releases...
if not exist "dist\releases" mkdir "dist\releases"
if not exist "dist\%HBG_EXE_BASENAME%.exe" (
    echo LOI: Khong tim thay dist\%HBG_EXE_BASENAME%.exe
    goto :fail
)
copy /Y "dist\%HBG_EXE_BASENAME%.exe" "dist\releases\%HBG_EXE_BASENAME%.exe" >nul

findstr /C:"Fix Bank" "dist\releases\%HBG_EXE_BASENAME%.exe" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo LOI: File EXE van chua "Fix Bank" — dang build nham source cu.
    echo Hay build trong: HBGAdBlocker VN\HBGAdBlocker
    goto :fail
)

echo.
echo ========================================
echo  BUILD THANH CONG
echo  %CD%\dist\releases\%HBG_EXE_BASENAME%.exe
echo  Phien ban: v%HBG_VERSION%
echo.
echo  MO FILE NAY — khong mo HBGAdBlocker.exe cu trong dist\
echo ========================================
pause
exit /b 0

:fail
echo.
echo BUILD THAT BAI.
pause
exit /b 1
