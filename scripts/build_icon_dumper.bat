@echo off
setlocal
set ROOT=%~dp0..
set SRC=%ROOT%\tools\android_icon_dumper\IconDumper.java
set OUT=%ROOT%\core\assets
set DEX=%OUT%\hbg_icon_dumper.dex

if "%ANDROID_HOME%"=="" (
  if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
)
if "%ANDROID_HOME%"=="" (
  echo ANDROID_HOME not set. Install Android SDK platform-tools + build-tools.
  exit /b 1
)

for /f "delims=" %%i in ('dir /b /ad /o-n "%ANDROID_HOME%\build-tools" 2^>nul') do (
  set "BT=%ANDROID_HOME%\build-tools\%%i"
  goto :got_bt
)
:got_bt
for /f "delims=" %%i in ('dir /b /ad /o-n "%ANDROID_HOME%\platforms\android-*" 2^>nul') do (
  set "PLATFORM=%ANDROID_HOME%\platforms\%%i\android.jar"
  goto :got_plat
)
:got_plat

if not exist "%BT%\d8.bat" (
  echo d8 not found in %BT%
  exit /b 1
)
if not exist "%PLATFORM%" (
  echo android.jar not found
  exit /b 1
)

mkdir "%OUT%" 2>nul
set BUILD=%TEMP%\hbg_icon_build
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%BUILD%"

echo Compiling IconDumper...
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "%PLATFORM%" -d "%BUILD%" "%SRC%"
if errorlevel 1 exit /b 1

mkdir "%BUILD%\dex_out" 2>nul
echo Building dex...
call "%BT%\d8.bat" --min-api 21 --output "%BUILD%\dex_out" "%BUILD%\IconDumper.class"
if errorlevel 1 exit /b 1

copy /y "%BUILD%\dex_out\classes.dex" "%DEX%" >nul
echo Wrote %DEX%
rmdir /s /q "%BUILD%"
exit /b 0
