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
    print("=== HBG TOOL: DÒ TÌM VÀ KÍCH HOẠT DỊCH VỤ IMS KHẮP HỆ THỐNG ===")
    
    # Send broadcast to trigger IMS service start
    broadcasts = [
        "com.mediatek.ims.ACTION_IMS_SERVICE_UP",
        "android.intent.action.BOOT_COMPLETED",
        "com.android.intent.action.IMS_CONFIG_CHANGED",
        "com.mediatek.intent.action.VOLTE_SETTING_CHANGED"
    ]
    
    for b in broadcasts:
        out = run_adb(f"am broadcast -a {b}")
        print(f"  • Broadcast [{b}]: {out}")

    print("\n🎉 Đã gửi phát sóng kích hoạt IMS Daemon ngầm!")

if __name__ == "__main__":
    main()
