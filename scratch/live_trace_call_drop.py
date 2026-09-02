import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_adb(cmd):
    try:
        res = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True, timeout=12)
        return res.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print("====================================================================")
    print("  🔍 HBG VOLTE FIXER — SOI CHI TIẾT RADIO LOGCAT KHI GỌI BỊ RỚT 2G")
    print("====================================================================")
    print()

    # 1. Kiểm tra trạng thái cờ RIL & IMS
    print("--- 1. CÁC CỜ TRẠNG THÁI RIL ---")
    v_state = run_adb("getprop persist.vendor.radio.volte_state")
    ims_state = run_adb("getprop gsm.ims.type0")
    print(f"  • persist.vendor.radio.volte_state: {v_state}")
    print(f"  • gsm.ims.type0                   : {ims_state if ims_state else '(Chưa kết nối SIP IMS)'}")

    # 2. Dịch vụ IMS Binder
    print("\n--- 2. KIỂM TRA BINDER SERVICE CELLULAR IMS ---")
    srv = run_adb("service list | grep -i ims")
    print(srv if srv else "Không tìm thấy IMS service binder")

    # 3. Quét Logcat Radio chi tiết cho SIP / REGISTER / CSFB / CALL
    print("\n--- 3. SO SÁNH NHẬT KÝ RADIO LOGCAT ---")
    logs = run_adb("logcat -b radio -d -t 400 | grep -iE 'ims|volte|csfb|sip|register|call|cause'")
    if logs:
        lines = logs.split('\n')
        print(f"  🔍 Phát hiện {len(lines)} dòng log radio:")
        for l in lines[-25:]:
            print(f"    {l}")
    else:
        print("  (Không có log radio gần đây)")

    print("\n====================================================================")

if __name__ == "__main__":
    main()
