import subprocess
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_adb(cmd):
    try:
        res = subprocess.run(f"adb shell \"{cmd}\"", shell=True, capture_output=True, text=True, errors="ignore")
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def main():
    print("==========================================================================")
    print("  🔍 DEEP DIAGNOSTIC: PHÂN TÍCH NGUYÊN NHÂN CHƯA HIỆN VOLTE THANH SÓNG")
    print("==========================================================================")

    # 1. Device Info
    print("\n--- [1] THÔNG TIN THIẾT BỊ & SIM ---")
    print("Model:            ", run_adb("getprop ro.product.model"))
    print("Android / ColorOS:", run_adb("getprop ro.build.version.release"), "/", run_adb("getprop ro.build.version.opporom"))
    print("SIM Operator:     ", run_adb("getprop gsm.sim.operator.numeric"), "(", run_adb("getprop gsm.sim.operator.alpha"), ")")

    # 2. IMS Registration State
    print("\n--- [2] TRẠNG THÁI ĐĂNG KÝ IMS THỰC TẾ (MODEM NETWORK LEVEL) ---")
    reg_out = run_adb("dumpsys telephony.registry")
    ims_lines = [l for l in reg_out.splitlines() if any(k in l.lower() for k in ["ims", "volte", "mvoiceregstate"])]
    if ims_lines:
        for l in ims_lines[:15]:
            print("  ", l)
    else:
        print("  (Không tìm thấy dòng mImsState trong dumpsys)")

    # 3. Check Current APNs on Phone (Does IMS APN exist?)
    print("\n--- [3] KIỂM TRA ĐIỂM TRUY CẬP APN NẠP TRÊN SIM VIETTEL ---")
    apn_out = run_adb("content query --uri content://telephony/carriers/current --projection name:apn:type:mcc:mnc")
    print("  Danh sách APN hiện tại:")
    if apn_out:
        for line in apn_out.splitlines()[:10]:
            print("  ", line)
    else:
        print("  (Không thể truy vấn APN qua content query)")

    # 4. SystemUI & Oppo Carrier Whitelist Flags
    print("\n--- [4] KIỂM TRA CỜ SYSTEMUI & CẤU HÌNH NHÀ MẠNG COLOROS ---")
    sys_flags = [
        "persist.sys.oppo.carrier.volte",
        "ro.oppo.has_operator_flag",
        "ro.oppo.version",
        "persist.sys.oppo.region",
        "persist.vendor.radio.volte_state",
        "persist.vendor.mtk.volte.enable",
        "persist.vendor.mtk_ct_volte_support"
    ]
    for sf in sys_flags:
        print(f"  {sf:<38} = [{run_adb(f'getprop {sf}')}]")

    # 5. DM-Verity / VBMeta Status
    print("\n--- [5] KIỂM TRA DM-VERITY & VBMETA ---")
    print("  ro.boot.veritymode:    ", run_adb("getprop ro.boot.veritymode"))
    print("  ro.boot.verifiedbootstate:", run_adb("getprop ro.boot.verifiedbootstate"))

if __name__ == "__main__":
    main()
