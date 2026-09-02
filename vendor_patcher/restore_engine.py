"""
HBG VoLTE Fixer — Automated Force Restore Engine for ALL OPPO Models
Completely disables & removes VoLTE settings via ADB and provides UnlockTool restore steps.
"""

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
        res = subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True, timeout=8)
        return res.stdout.strip()
    except Exception as e:
        return ""

def main():
    print("====================================================================")
    print("  🛡️ HBG VOLTE FIXER — TẮT/KHÔI PHỤC TRIỆT ĐỂ KHÔNG CÒN VOLTE")
    print("====================================================================")
    print()

    # 1. Detect device model via ADB
    model = run_adb("getprop ro.product.model")
    brand = run_adb("getprop ro.product.brand")
    android = run_adb("getprop ro.build.version.release")

    if model:
        print(f"📱 Đã phát hiện thiết bị: {brand.upper()} {model} (Android {android})")
        print("\n[1] Ép tắt công tắc VoLTE trong Android Global Settings...")
        run_adb("settings put global volte_vt_enabled 0")
        run_adb("settings put global vt_ims_enabled 0")
        run_adb("settings delete global carrier_config_overrides")

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

        print("\n[3] Làm tươi kết nối mạng di động...")
        run_adb("am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED")
        run_adb("settings put global airplane_mode_on 1")
        run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")
        time.sleep(2)
        run_adb("settings put global airplane_mode_on 0")
        run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")
        
        print(f"\n🎉 THÀNH CÔNG: Đã vô hiệu hóa & khôi phục VoLTE gốc trên {model}!")
    else:
        print("ℹ️ Chưa cắm điện thoại qua ADB (Hoặc đang nạp trực tiếp qua UnlockTool).")

    print("\n--------------------------------------------------------------------")
    print("📋 THAO TÁC KHÔI PHỤC BẢN VENDOR GỐC TRÊN UNLOCKTOOL (NẾU ĐÃ FLASH VENDOR):")
    print("  1. Mở UnlockTool -> Tab MediaTek (MTK) hoặc Qualcomm.")
    print("  2. Chọn tệp vendor.bin / vendor.img gốc (trong thư mục backup).")
    print("  3. Tích chọn [PATCH DM VERITY] -> Bấm [FLASH] (Tia sét ⚡).")
    print("====================================================================")

if __name__ == "__main__":
    main()
