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
    print("=== HBG TOOL: KÍCH HOẠT DỊCH VỤ BACKGROUND COM.MEDIATEK.IMS ===")
    
    # 1. Enable package com.mediatek.ims
    print("\n[1] Bật ứng dụng dịch vụ com.mediatek.ims...")
    run_adb("pm enable com.mediatek.ims")
    
    # 2. Start service
    print("\n[2] Khởi chạy ImsService Binder...")
    out1 = run_adb("am startservice com.mediatek.ims/.ImsService")
    print(f"  • Result startservice: {out1}")
    
    out2 = run_adb("am startservice -a com.mediatek.ims.ImsService")
    print(f"  • Result action ims: {out2}")

    # 3. Re-check binder
    import time
    time.sleep(2)
    print("\n[3] Kiểm tra danh sách Binder Service hiện tại:")
    srv = run_adb("service list | grep -i ims")
    print(f"  • IMS Binder Services:\n{srv if srv else 'Chưa có binder'}")

if __name__ == "__main__":
    main()
