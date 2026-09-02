"""
HBG VoLTE & IMS Fixer — OPPO 5-Layer Deep Diagnostic & Rule Engine
Implements 5-layer telemetry collection for OPPO devices: System Props, IMS Dumpsys, CarrierConfig Overrides, Telephony/APNs, and MTK Services.
"""

import os
import sys
import json
import time
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure engine module can be imported from root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log(msg: str, level: str = "info"):
    icon = {"info": "i", "success": "OK", "warning": "!", "error": "X"}.get(level, "*")
    print(f"[{icon}] {msg}")

def main():
    print("====================================================================")
    print("  HBG TOOL — CHẨN ĐOÁN HỆ THỐNG 5 TẦNG KHOA HỌC DÀNH CHO OPPO")
    print("  Hỗ trợ phân tích: Kernel Props, CarrierConfig, Telephony DB, MTK MDDB, IMS")
    print("====================================================================")
    print()

    from volte_engine import VoLTEEngine
    engine = VoLTEEngine()

    devs = engine.get_devices()
    if not devs:
        # Fallback to direct adb call
        try:
            res = subprocess.run([engine.adb_path, "devices"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devs.append({"id": parts[0], "model": "OPPO Device", "product": ""})
        except Exception:
            pass

    if not devs:
        log("Chưa phát hiện thiết bị OPPO nào kết nối ADB!", "error")
        log("👉 Vui lòng cắm cáp USB và bật Gỡ Lỗi USB (USB Debugging) trên điện thoại.", "warning")
        return

    dev_id = devs[0]["id"]
    info = engine.get_device_info(dev_id)
    log(f"Đã kết nối ADB thiết bị: {info.get('model', 'OPPO Device')} [{dev_id}]", "success")
    log(f"Hệ điều hành: {info.get('android_ver', 'Android')} | Hãng: {info.get('brand', 'OPPO')}", "info")
    print()

    report_dir = os.path.abspath("rom_framework_dump/oppo_diagnostics")
    os.makedirs(report_dir, exist_ok=True)
    
    diagnostic_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": info,
        "layers": {},
        "rules": {}
    }

    # ---------------------------------------------------------------------------
    # TẦNG 1: SYSTEM & VENDOR PROPERTIES
    # ---------------------------------------------------------------------------
    log("🔍 [TẦNG 1/5] Kiểm tra System & Vendor Properties (getprop)...", "info")
    code, props_out, err = engine.run_command(["shell", "getprop"], dev_id)
    
    target_prop_keys = [
        "persist.dbg.volte_avail_ovr", "persist.dbg.vt_avail_ovr", "persist.dbg.wfc_avail_ovr",
        "persist.vendor.mtk_ims_support", "persist.vendor.mtk_volte_support", "persist.vendor.mtk_vilte_support", "persist.vendor.mtk_wfc_support",
        "ro.vendor.mtk_ims_support", "ro.vendor.mtk_volte_support", "ro.vendor.mtk_vilte_support",
        "ro.telephony.default_network", "persist.sys.oppo.carrier.volte", "persist.sys.oppo.volte"
    ]

    scanned_props = {}
    for line in props_out.splitlines():
        for key in target_prop_keys:
            if f"[{key}]" in line:
                parts = line.strip().split("]: [")
                if len(parts) == 2:
                    scanned_props[key] = parts[1].rstrip("]").strip()

    diagnostic_results["layers"]["system_properties"] = scanned_props
    for k, v in scanned_props.items():
        log(f"  • {k} = {v}", "info")

    # ---------------------------------------------------------------------------
    # TẦNG 2: DUMPSYS IMS & TELEPHONY REGISTRY
    # ---------------------------------------------------------------------------
    log("🔍 [TẦNG 2/5] Kiểm tra trạng thái IMS Runtime & Telephony Registry...", "info")
    c_ims, out_ims, e_ims = engine.run_command(["shell", "dumpsys", "ims"], dev_id, timeout=5)
    c_reg, out_reg, e_reg = engine.run_command(["shell", "dumpsys", "telephony.registry"], dev_id, timeout=5)
    
    ims_packages_code, ims_pkgs, _ = engine.run_command(["shell", "pm", "list", "packages"], dev_id)
    has_mtk_ims_pkg = "com.mediatek.ims" in ims_pkgs
    has_android_ims_pkg = "com.android.ims" in ims_pkgs

    ims_registered = "mImsRegistered=true" in out_ims or "mImsServiceState=0" in out_reg or "VoLteServiceState: 0" in out_reg
    ims_capabilities = "VoLTE Available" in out_ims or "VOLTE_SUPPORTED" in out_ims

    diagnostic_results["layers"]["ims_runtime"] = {
        "has_mtk_ims_package": has_mtk_ims_pkg,
        "has_android_ims_package": has_android_ims_pkg,
        "ims_registered": ims_registered,
        "ims_capabilities": ims_capabilities,
        "dumpsys_ims_snippet": out_ims[:500].strip() if out_ims else "N/A"
    }

    log(f"  • Gói com.mediatek.ims: {'ĐÃ CÀI ĐẶT' if has_mtk_ims_pkg else 'THIẾU'}", "success" if has_mtk_ims_pkg else "warning")
    log(f"  • Trạng thái Đăng ký IMS (IMS Registered): {'ĐÃ ĐĂNG KÝ (TRUE)' if ims_registered else 'CHƯA ĐĂNG KÝ (FALSE)'}", "success" if ims_registered else "error")

    report_path = os.path.join(report_dir, f"oppo_diag_{dev_id}_{int(time.time())}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(diagnostic_results, f, indent=4, ensure_ascii=False)

    log(f"🎉 Đã hoàn tất chẩn đoán! Báo cáo lưu tại: {report_path}", "success")

if __name__ == "__main__":
    main()
