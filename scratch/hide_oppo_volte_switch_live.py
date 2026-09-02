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
    print("=== HBG TOOL: ÉP ẨN TRIỆT ĐỂ NÚT CÀI ĐẶT VOLTE TRONG COLOROS ===")
    
    # 1. Force set false to all OPPO carrier props
    oppo_hide_props = [
        ("persist.sys.oppo.carrier.volte", "0"),
        ("persist.sys.oppo.volte", "0"),
        ("persist.sys.oppo.ims", "0"),
        ("persist.vendor.volte_support", "0"),
        ("persist.vendor.mtk_ct_volte_support", "0"),
        ("persist.vendor.radio.volte_state", "0"),
        ("persist.vendor.mtk.volte.enable", "0")
    ]

    for p, v in oppo_hide_props:
        run_adb(f"setprop {p} {v}")
        print(f"  ✓ Executed setprop [{p}] = {v}")

    # 2. Kill SimSettings to force UI refresh
    print("\n[2] Tắt ứng dụng Cài Đặt SIM để ép vẽ lại giao diện...")
    run_adb("am force-stop com.coloros.simsettings")
    run_adb("am force-stop com.android.phone")
    run_adb("am force-stop com.android.settings")

    print("\n🎉 Đã gửi lệnh ẩn công tắc VoLTE và kill SimSettings!")

if __name__ == "__main__":
    main()
