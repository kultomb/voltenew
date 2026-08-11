@echo off
setlocal
set "SRC=C:\Users\CMD\Desktop\HBGAdBlocker VN\HBGAdBlocker\tools\android_volte_fixer\VolteFixer.java"
set "DEX=C:\Users\CMD\Desktop\HBGAdBlocker VN\HBGAdBlocker\core\assets\hbg_volte_fixer.dex"

set "PLATFORM=C:\Users\CMD\AppData\Local\Android\Sdk\platforms\android-33\android.jar"
set "D8_JAR=C:\Users\CMD\AppData\Local\Android\Sdk\build-tools\30.0.3\lib\d8.jar"

set "BUILD=%TEMP%\hbg_volte_build"
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%BUILD%"

echo Compiling VolteFixer.java...
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "%PLATFORM%" -d "%BUILD%" "%SRC%"
if errorlevel 1 exit /b 1

echo Building dex with d8 jar...
java -cp "%D8_JAR%" com.android.tools.r8.D8 --min-api 21 --output "%BUILD%" "%BUILD%\com\hbg\volte\VolteFixer.class"
if errorlevel 1 exit /b 1

if exist "%BUILD%\classes.dex" (
    copy /y "%BUILD%\classes.dex" "%DEX%"
    echo SUCCESS: Wrote %DEX%
) else (
    echo classes.dex NOT FOUND!
)

rmdir /s /q "%BUILD%"
exit /b 0
