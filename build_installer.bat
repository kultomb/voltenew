@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo  HBG AdBlocker - Build EXE + Cai dat
echo ========================================
echo.
echo Thu muc build: %CD%
echo (Chi build o HBGAdBlocker VN — khong dung thu muc HBG ADS)
echo.

if not exist "icons\app_icon.ico" (
    echo LOI: Thieu icons\app_icon.ico
    echo Dat file .ico vao thu muc icons\ roi chay lai.
    goto :fail
)

echo [1/5] Cai dat phu thuoc...
pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/5] Tang phien ban va sinh metadata...
python scripts\prepare_build.py > build_version.tmp
if errorlevel 1 goto :fail
set /p HBG_VERSION=<build_version.tmp
for /f "skip=1 tokens=*" %%a in (build_version.tmp) do set HBG_EXE_BASENAME=%%a
del build_version.tmp
call build_env.bat
echo     Phien ban: %HBG_VERSION%
echo     EXE:       %HBG_EXE_BASENAME%.exe
echo     Icon:      icons\app_icon.ico
echo.

echo [3/5] Build PyInstaller (onefile, co icon .exe)...
pyinstaller HBGAdBlocker.spec --noconfirm --clean
if errorlevel 1 goto :fail

if not exist "dist\%HBG_EXE_BASENAME%.exe" (
    echo LOI: Khong tim thay dist\%HBG_EXE_BASENAME%.exe
    goto :fail
)

echo.
echo [4/5] Luu ban phat hanh...
if not exist "dist\releases" mkdir "dist\releases"
copy /Y "dist\%HBG_EXE_BASENAME%.exe" "dist\releases\%HBG_EXE_BASENAME%.exe" >nul

findstr /C:"Fix Bank" "dist\releases\%HBG_EXE_BASENAME%.exe" >nul 2>&1
if not errorlevel 1 (
    echo LOI: EXE van chua Fix Bank — source/build sai thu muc.
    goto :fail
)

echo.
echo [5/5] Dong goi Setup (Inno Setup)...
set "ISCC="
where iscc >nul 2>&1 && set "ISCC=iscc"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo     Canh bao: chua cai Inno Setup 6 — bo qua file Setup.
    echo     Tai: https://jrsoftware.org/isinfo.php
    echo     Chi co file portable: dist\releases\%HBG_EXE_BASENAME%.exe
    goto :ok_portable
)

"%ISCC%" "installer\HBGAdBlocker.iss"
if errorlevel 1 goto :fail

:ok_portable
echo.
echo ========================================
echo  BUILD THANH CONG
echo  Portable: %CD%\dist\releases\%HBG_EXE_BASENAME%.exe
if defined ISCC echo  Cai dat:  %CD%\dist\releases\HBGAdBlocker_Setup_v%HBG_VERSION%.exe
echo  Phien ban: v%HBG_VERSION%
echo ========================================
pause
exit /b 0

:fail
echo.
echo BUILD THAT BAI.
pause
exit /b 1
