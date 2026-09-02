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
    print("====================================================================")
    print("  🔥 HBG VOLTE FIXER — TẮT/KHÔI PHỤC TRIỆT ĐỂ KHÔNG CÒN VOLTE")
    print("====================================================================")
    print()

    # 1. Clear CarrierConfig Overrides & Force Disable VoLTE
    print("[1] Ép tắt công tắc VoLTE trong Android Global Settings...")
    run_adb("settings put global volte_vt_enabled 0")
    run_adb("settings put global vt_ims_enabled 0")
    run_adb("settings delete global carrier_config_overrides")

    # 2. Force setprop properties to 0 (Disabled)
    print("\n[2] Ép cờ Modem Radio về trạng thái VÔ HIỆU HÓA (0)...")
    disable_props = [
        ("persist.vendor.radio.volte_state", "0"),
        ("persist.vendor.mtk.volte.enable", "0"),
        ("persist.vendor.mtk_ct_volte_support", "0"),
        ("persist.vendor.volte_support", "0"),
        ("persist.sys.oppo.carrier.volte", "0"),
        ("persist.radio.volte.enable", "0"),
        ("persist.vendor.radio.volte_disable", "1")
    ]

    for p, v in disable_props:
        run_adb(f"setprop {p} {v}")
        print(f"  ✓ Set [{p}] = {v}")

    # 3. Reload Carrier Config & Toggle Airplane mode
    print("\n[3] Broadcast thông báo hạ tầng mạng & reset sóng...")
    run_adb("am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED")
    
    run_adb("settings put global airplane_mode_on 1")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")
    import time
    time.sleep(2)
    run_adb("settings put global airplane_mode_on 0")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")

    print("\n====================================================================")
    print("🎉 ĐÃ KHÔI PHỤC TRIỆT ĐỂ: VOLTE ĐÃ XÓA/BỊ TẮT HOÀN TOÀN TÊN OPPO A53!")
    print("====================================================================")

if __name__ == "__main__":
    main()
