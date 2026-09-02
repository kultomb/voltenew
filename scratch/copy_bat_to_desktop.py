import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    desktop_bat1 = r"C:\Users\CMD\Desktop\Run_VoLTE_Fixer.bat"
    desktop_bat2 = r"C:\Users\CMD\Desktop\Chay_Tool_VoLTE.bat"

    desktop_bat_content = """@echo off
chcp 65001 > NUL
title HBG VoLTE Fixer Tool v2.0 - Live Python Test Mode

cd /d "C:\\Users\\CMD\\Desktop\\volte_fixer_tool"

echo ====================================================================
echo   HBG VOLTE FIXER TOOL - CHẾ ĐỘ THỬ NGHIỆM PYTHON CODE TRỰC TIẾP
echo ====================================================================
echo.

python volte_fixer_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ====================================================================
    echo [CẢNH BÁO LỖI] THOÁT CODE VỚI MÃ LỖI %ERRORLEVEL%!
    echo Vui lòng kiểm tra dòng vết lỗi (Traceback) ở trên.
    echo ====================================================================
    echo.
    pause
)
"""
    with open(desktop_bat1, "w", encoding="utf-8") as f:
        f.write(desktop_bat_content)

    with open(desktop_bat2, "w", encoding="utf-8") as f:
        f.write(desktop_bat_content)

    print("SAO CHEP FILE .BAT RA DESKTOP THANH CONG!")
    print(f"👉 {desktop_bat1}")
    print(f"👉 {desktop_bat2}")

if __name__ == "__main__":
    main()
