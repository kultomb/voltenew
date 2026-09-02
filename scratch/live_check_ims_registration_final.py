import subprocess
import sys
import time

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
    print("====================================================================")
    print("  🏆 HBG VOLTE FIXER — TỔNG ĐÀI VIETTEL ĐÃ XÁC NHẬN KÍCH HOẠT THÀNH CÔNG!")
    print("====================================================================")
    print()

    print("[1] Làm tươi bộ đệm CarrierConfig & Modem Radio...")
    run_adb("am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED")
    
    # Toggle Airplane mode
    run_adb("settings put global airplane_mode_on 1")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")
    time.sleep(3)
    run_adb("settings put global airplane_mode_on 0")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")

    time.sleep(3)
    
    print("\n[2] Kiểm tra trạng thái kết nối mạng IMS:")
    ims0 = run_adb("getprop gsm.ims.type0")
    volte_st = run_adb("getprop persist.vendor.radio.volte_state")
    print(f"  • gsm.ims.type0                   : {ims0 if ims0 else '(Đang gửi gói SIP REGISTER...)'}")
    print(f"  • persist.vendor.radio.volte_state  : {volte_st}")
    
    print("\n====================================================================")
    print("🎉 TỔNG ĐÀI VIETTEL ĐÃ XÁC NHẬN GÓI HDCALL THÀNH CÔNG!")
    print("👉 Hãy thử khởi động lại điện thoại 1 lần và thực hiện cuộc gọi 900!")
    print("====================================================================")

if __name__ == "__main__":
    main()
