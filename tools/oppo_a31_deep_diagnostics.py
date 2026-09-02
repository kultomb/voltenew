"""
HBG VoLTE & IMS Fixer — OPPO A31 (CPH2015 MT6765) 5-Layer Deep Diagnostic & Rule Engine
Implements rigorous 5-layer telemetry collection: System Props, IMS Dumpsys, CarrierConfig Overrides, Telephony/APNs, and MTK Services.
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

def log(msg: str, level: str = "info"):
    icon = {"info": "i", "success": "OK", "warning": "!", "error": "X"}.get(level, "*")
    print(f"[{icon}] {msg}")

def main():
    print("====================================================================")
    print("  HBG TOOL — CHẨN ĐOÁN HỆ THỐNG 5 TẦNG KHOA HỌC DÀNH CHO OPPO A31")
    print("  Model: OPPO CPH2015 | Chipset: MediaTek Helio P35 (MT6765) | Android 9")
    print("====================================================================")
    print()

    from volte_engine import VoLTEEngine
    engine = VoLTEEngine()

    devs = engine.get_devices()
    if not devs:
        # Fallback to direct adb call
        import subprocess
        try:
            res = subprocess.run([engine.adb_path, "devices"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devs.append({"id": parts[0], "model": "OPPO A31", "product": ""})
        except Exception:
            pass

    if not devs:
        log("Chưa phát hiện thiết bị OPPO A31 nào kết nối ADB!", "error")
        log("👉 Vui lòng cắm cáp USB và bật Gỡ Lỗi USB (USB Debugging) trên điện thoại.", "warning")
        return

    dev_id = devs[0]["id"]
    info = engine.get_device_info(dev_id)
    log(f"Đã kết nối ADB thiết bị: {info.get('model', 'OPPO CPH2015')} [{dev_id}]", "success")
    log(f"Hệ điều hành: {info.get('android_ver', 'Android 9')} | Hãng: {info.get('brand', 'OPPO')}", "info")
    print()

    report_dir = os.path.abspath("rom_framework_dump/oppo_a31_diagnostics")
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

    # ---------------------------------------------------------------------------
    # TẦNG 3: CARRIER CONFIG & OVERLAYS
    # ---------------------------------------------------------------------------
    log("🔍 [TẦNG 3/5] Kiểm tra CarrierConfig Dumpsys & Vendor Overlays...", "info")
    c_cc, out_cc, e_cc = engine.run_command(["shell", "dumpsys", "carrier_config"], dev_id, timeout=5)
    
    cc_flags = {}
    cc_target_keys = [
        "carrier_volte_available_bool", "carrier_vt_available_bool", "carrier_wfc_ims_available_bool",
        "editable_enhanced_4g_lte_bool", "hide_enhanced_4g_lte_bool", "carrier_volte_provisioned_bool"
    ]
    
    for line in out_cc.splitlines():
        for key in cc_target_keys:
            if key in line:
                parts = line.strip().split("=")
                if len(parts) == 2:
                    cc_flags[key] = parts[1].strip()

    c_ov, out_ov, e_ov = engine.run_command(["shell", "ls", "-la", "/vendor/overlay/"], dev_id)
    has_vendor_overlays = "CarrierConfig" in out_ov or "Overlay" in out_ov

    diagnostic_results["layers"]["carrier_config"] = {
        "flags": cc_flags,
        "vendor_overlays": out_ov.strip() if out_ov else "N/A"
    }
    for k, v in cc_flags.items():
        log(f"  • {k} = {v}", "info")

    # ---------------------------------------------------------------------------
    # TẦNG 4: VENDOR IMS FILES & PACKAGES
    # ---------------------------------------------------------------------------
    log("🔍 [TẦNG 4/5] Kiểm tra các tệp tin Vendor IMS & Cấu hình MediaTek RIL...", "info")
    c_v_etc, out_v_etc, _ = engine.run_command(["shell", "ls", "-la", "/vendor/etc/"], dev_id)
    has_mddb = "mddb" in out_v_etc
    has_apns = "apns-conf.xml" in out_v_etc or os.path.exists("rom_framework_dump/vendor_dump_oppo_a31/apns-conf.xml")

    diagnostic_results["layers"]["vendor_files"] = {
        "has_mddb_folder": has_mddb,
        "has_apns_conf": has_apns
    }

    # ---------------------------------------------------------------------------
    # TẦNG 5: RULE ENGINE — ĐÁNH GIÁ ĐIỂM NGHẼN CHÍNH XÁC
    # ---------------------------------------------------------------------------
    print()
    print("====================================================================")
    print("📊 KẾT QUẢ ĐÁNH GIÁ TỰ ĐỘNG BẰNG RULE ENGINE (RULE ENGINE DIAGNOSIS):")
    print("====================================================================")

    r1 = "PASS" if has_mtk_ims_pkg else "FAIL"
    r2 = "PASS" if ims_registered else "FAIL"
    
    volte_bool_str = cc_flags.get("carrier_volte_available_bool", "false").lower()
    r3 = "PASS" if volte_bool_str == "true" else "FAIL"

    if "persist.vendor.mtk_volte_support" in scanned_props:
        prop_val = scanned_props["persist.vendor.mtk_volte_support"]
        r4 = "PASS" if prop_val == "1" else "PROPERTY_FALSE"
    else:
        r4 = "PROPERTY_MISSING"

    rules_summary = [
        (f"[{r1}] MediaTek IMS Package (com.mediatek.ims)", "Đã cài đặt gói dịch vụ IMS MediaTek chính chủ" if r1 == "PASS" else "Thiếu gói com.mediatek.ims trong ROM"),
        (f"[{r2}] IMS Service Registration (dumpsys telephony.registry)", "SIM đã đăng ký thành công IMS với trạm phát sóng 4G" if r2 == "PASS" else "SIM CHƯA ĐĂNG KÝ ĐƯỢC IMS (Mất luồng đàm thoại 4G)"),
        (f"[{r3}] CarrierConfig VoLTE Available (carrier_volte_available_bool)", "Cờ CarrierConfig cho phép chạy VoLTE" if r3 == "PASS" else "CarrierConfig ĐANG KHÓA CỜ carrier_volte_available_bool = false"),
        (f"[{r4}] MTK Baseband Prop (persist.vendor.mtk_volte_support)", "Cờ Baseband MTK đã bật (=1)" if r4 == "PASS" else ("Cờ Baseband MTK bị đặt = 0" if r4 == "PROPERTY_FALSE" else "CỜ KHÔNG TỒN TẠI TRONG GETPROP (PROPERTY_MISSING)"))
    ]

    for status_tag, desc in rules_summary:
        icon = "✓" if "[PASS]" in status_tag else ("✗" if "[FAIL]" in status_tag else "❓")
        print(f"  {icon} {status_tag}: {desc}")

    diagnostic_results["rules"]["summary"] = rules_summary

    # Save complete JSON
    json_path = os.path.join(report_dir, "oppo_a31_diagnostic_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(diagnostic_results, f, indent=4, ensure_ascii=False)

    print()
    print("--------------------------------------------------------------------")
    print("💡 CHẨN ĐOÁN KẾT LUẬN CHÍNH XÁC VỀ ĐIỂM NGHẼN TRÊN OPPO A31 CỦA BẠN:")

    if r3 == "FAIL":
        print("  🔴 ĐIỂM NGHẼN CHÍNH: Nằm ở TẦNG 3 (CarrierConfig / Overlay).")
        print("     Cờ carrier_volte_available_bool đang bị khống chế = false bởi file CarrierConfig/Overlay của ColorOS.")
    elif r2 == "FAIL":
        print("  🔴 ĐIỂM NGHẼN CHÍNH: Nằm ở TẦNG 2 (IMS Registration & Carrier Provisioning).")
        print("     Gói com.mediatek.ims đã có nhưng Modem chưa hoàn tất thủ tục P-CSCF Discovery với nhà mạng.")
    elif r4 == "FAIL":
        print("  🔴 ĐIỂM NGHẼN CHÍNH: Nằm ở TẦNG 1 (Vendor System Properties).")

    print()
    print(f"📄 Chi tiết dữ liệu chẩn đoán JSON đã lưu tại: {json_path}")
    print("====================================================================")

if __name__ == "__main__":
    main()
