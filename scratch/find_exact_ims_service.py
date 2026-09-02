import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_adb(cmd):
    try:
        res = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True, timeout=10)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=== DÒ TÌM COMPONENT CHÍNH XÁC CỦA MEDIATEK IMS SERVICE ===")
    
    pkg_info = run_adb("dumpsys package com.mediatek.ims | grep -iE 'ServiceRecord|service|receiver'")
    print("Các Service components trong com.mediatek.ims:")
    if pkg_info:
        for line in pkg_info.split('\n')[:30]:
            print(f"  {line.strip()}")
    else:
        print("  Không lấy được dumpsys package")

if __name__ == "__main__":
    main()
