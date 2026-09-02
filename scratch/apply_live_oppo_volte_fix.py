import subprocess
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, errors="ignore", timeout=30)
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def main():
    print("==========================================================================")
    print("  🚀 HBG VOLTE FIXER — KÍCH HOẠT THANH SÓNG VOLTE TRỰC TIẾP QUA ADB")
    print("==========================================================================")

    # 1. Single-command batch setprop
    batch_props_cmd = (
        'adb shell "'
        'setprop persist.mtk.ims_support 1; '
        'setprop persist.mtk.volte_support 1; '
        'setprop persist.mtk.volte.enable 1; '
        'setprop persist.radio.volte_state 1; '
        'setprop persist.dbg.volte_avail_ovr 1; '
        'setprop persist.dbg.vt_avail_ovr 1; '
        'setprop persist.vendor.mtk.ims_support 1; '
        'setprop persist.vendor.mtk.volte_support 1; '
        'setprop persist.vendor.mtk.volte.enable 3; '
        'setprop persist.vendor.radio.volte_state 3; '
        'setprop persist.vendor.mtk_dynamic_ims_switch 0; '
        'setprop persist.vendor.mtk_ct_volte_support 1; '
        'setprop persist.sys.oppo.carrier.volte 1; '
        'setprop persist.radio_oppo_ct_volte_support 1; '
        'su -c \'setprop persist.vendor.radio.volte_state 3; setprop persist.vendor.mtk.volte.enable 3\' 2>/dev/null'
        '"'
    )

    print("⚡ [1/3] Đang nạp hàng loạt 14 thuộc tính Master VoLTE...")
    res = run_cmd(batch_props_cmd)
    print("  ✓ Đã gửi lệnh nạp thuộc tính batch!")

    # 2. Check and install Overlay APK
    overlay_apk = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../extracted_vendor_volte/unpacked_vendor_files/overlay/GAQVoLTE/GAQ_OPPO_MTK_VoLTE_Overlay.apk"
    ))

    print("\n📦 [2/3] Kiểm tra tệp CarrierConfig RRO Overlay...")
    if os.path.exists(overlay_apk):
        print(f"  ✓ Tìm thấy tệp Overlay: [{os.path.basename(overlay_apk)}]")
        inst_res = run_cmd(f'adb install -r -d "{overlay_apk}"')
        print(f"  👉 Kết quả cài đặt ADB: {inst_res}")
        if "Overlay" in inst_res and "is static but not pre-installed" in inst_res:
            print("  💡 LƯU Ý KỸ THUẬT: Tệp Overlay GAQ VoLTE là Static RRO Overlay (Yêu cầu pre-installed).")
            print("     -> Để biểu tượng VoLTE hiện 100% trên thanh sóng, CẦN NẠP TỆP VENDOR.IMG VÁ BẰNG UNLOCKTOOL vào phân vùng /vendor/overlay!")
    else:
        print("  ⚠ Không tìm thấy tệp Overlay APK.")

    # 3. Refresh Network Telephony
    print("\n🔄 [3/3] Đang làm mới kết nối SIM & Mạng...")
    run_cmd('adb shell "settings put global airplane_mode_on 1; am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"')
    import time
    time.sleep(1)
    run_cmd('adb shell "settings put global airplane_mode_on 0; am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false"')

    # 4. Check results
    print("\n=== THÔNG SỐ SAU KHI NẠP ===")
    vstate = run_cmd('adb shell "getprop persist.vendor.radio.volte_state"')
    venable = run_cmd('adb shell "getprop persist.vendor.mtk.volte.enable"')
    vct = run_cmd('adb shell "getprop persist.vendor.mtk_ct_volte_support"')
    print(f"  persist.vendor.radio.volte_state: [{vstate}]")
    print(f"  persist.vendor.mtk.volte.enable:   [{venable}]")
    print(f"  persist.vendor.mtk_ct_volte_support:[{vct}]")

    print("\n🎉 THỰC THI HOÀN TẤT!")

if __name__ == "__main__":
    main()
