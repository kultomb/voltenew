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
    print("  🛡️ HBG VOLTE FIXER — KHÔI PHỤC VOLTE GỐC CHO OPPO A53 / ALL MODELS")
    print("====================================================================")
    print()

    # 1. Inspect connected device
    model = run_adb("getprop ro.product.model")
    brand = run_adb("getprop ro.product.brand")
    chip = run_adb("getprop ro.board.platform")
    android = run_adb("getprop ro.build.version.release")

    print(f"📱 THIẾT BỊ ĐANG KẾT NỐI: {brand.upper()} {model} (Android {android}, Chip: {chip})")

    # 2. Reset system properties to stock defaults
    print("\n[1] Đang xóa các cờ ghi đè VoLTE và khôi phục cài đặt gốc...")
    
    reset_props = [
        "persist.vendor.radio.volte_state",
        "persist.vendor.mtk.volte.enable",
        "persist.vendor.mtk_ct_volte_support",
        "persist.vendor.mtk_dynamic_ims_switch",
        "persist.vendor.volte_support",
        "persist.sys.oppo.carrier.volte",
        "persist.radio.volte.enable"
    ]

    for p in reset_props:
        out = run_adb(f"setprop {p} ''")
        print(f"  • Restored property [{p}] -> default")

    # Reset Airplane mode to force fresh registration
    print("\n[2] Làm tươi kết nối mạng di động...")
    run_adb("settings put global airplane_mode_on 1")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")
    import time
    time.sleep(2)
    run_adb("settings put global airplane_mode_on 0")
    run_adb("am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")

    print("\n====================================================================")
    print(f"🎉 ĐÃ KHÔI PHỤC THÀNH CÔNG VỀ BẢN VOLTE GỐC CHO {model}!")
    print("====================================================================")

if __name__ == "__main__":
    main()
