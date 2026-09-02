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
    print("=== HBG TOOL: DÒ SÂU LÝ DO KHI GỌI BỊ HẠ VỀ 2G ===")
    
    print("\n[1] Kiểm tra trạng thái IMS Registration:")
    ims_state = run_adb("getprop gsm.ims.type0")
    volte_state = run_adb("getprop persist.vendor.radio.volte_state")
    print(f"  • gsm.ims.type0                     : {ims_state if ims_state else '(Chưa đăng ký SIP IMS)'}")
    print(f"  • persist.vendor.radio.volte_state  : {volte_state}")

    print("\n[2] Kiểm tra tin nhắn phản hồi tổng đài 191...")
    sms = run_adb("content query --uri content://sms/inbox --projection address:body --where \"address='191'\"")
    if sms:
        print(f"  • Tin nhắn 191 nhận được:\n{sms[:500]}")
    else:
        print("  • Chưa thấy tin nhắn phản hồi từ 191.")

    print("\n[3] Gửi tín hiệu Reset mạng di động...")
    run_adb("settings put global airplane_mode_on 1")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")
    import time
    time.sleep(2)
    run_adb("settings put global airplane_mode_on 0")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")
    print("  • Đã toggle Airplane Mode để ép Modem đăng ký lại SIP IMS!")

if __name__ == "__main__":
    main()
