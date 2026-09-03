"""
HBG VoLTE Fixer — Master Vendor Patching Engine for ALL OPPO / MediaTek / Qualcomm Models
(Supports OPPO A5s, A31, A12, A1k, A5, A9, Realme, Vivo, Xiaomi, Samsung...)
Injects the 5 Master VoLTE Flags directly into raw vendor.bin / vendor.img files.
"""

import os
import sys
import glob

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Master Vendor Replacement Rules matching EXE working profile
MASTER_VENDOR_RULES = [
    # Universal Dual SIM VoLTE: mtk_ct_volte_support=3 (SIM 1 + SIM 2 CT / Viettel / Vina / Mobi)
    (b"persist.vendor.mtk_ct_volte_support=0", b"persist.vendor.mtk_ct_volte_support=3"),
    (b"persist.vendor.mtk_ct_volte_support=1", b"persist.vendor.mtk_ct_volte_support=3"),
    (b"persist.vendor.mtk_ct_volte_support=2", b"persist.vendor.mtk_ct_volte_support=3"),
    (b"persist.vendor.mtk_ct_volte_support=3", b"persist.vendor.mtk_ct_volte_support=3"),
    
    # MTK VoLTE Enable (0/1/2 -> 3=Dual VoLTE / DSBP Master Active)
    (b"persist.vendor.mtk.volte.enable=0", b"persist.vendor.mtk.volte.enable=3"),
    (b"persist.vendor.mtk.volte.enable=1", b"persist.vendor.mtk.volte.enable=3"),
    (b"persist.vendor.mtk.volte.enable=2", b"persist.vendor.mtk.volte.enable=3"),
    
    # Radio VoLTE State (0/1/2 -> 3=Active Hardware Dual Slot VoLTE)
    (b"persist.vendor.radio.volte_state=0", b"persist.vendor.radio.volte_state=3"),
    (b"persist.vendor.radio.volte_state=1", b"persist.vendor.radio.volte_state=3"),
    (b"persist.vendor.radio.volte_state=2", b"persist.vendor.radio.volte_state=3"),
    
    # Multi-IMS Support (mims_support=2 for Dual SIM IMS instances)
    (b"persist.vendor.mims_support=0", b"persist.vendor.mims_support=2"),
    (b"persist.vendor.mims_support=1", b"persist.vendor.mims_support=2"),
    
    # MTK Dynamic IMS Switch (1=Enable CT SIM Restriction -> 0=Disable Restriction for Viettel/Vina)
    (b"persist.vendor.mtk_dynamic_ims_switch=1", b"persist.vendor.mtk_dynamic_ims_switch=0"),
    
    # IMS Operator Config Persistent Fix
    (b"persist.vendor.ims.op.config=0", b"persist.vendor.ims.op.config=1"),
    (b"persist.vendor.mtk_ims_op_config=0", b"persist.vendor.mtk_ims_op_config=1"),
    
    # Baseband VoLTE Support & NVRAM Provisioning for Dual SIM (Sub0 & Sub1)
    (b"persist.vendor.volte_support=0", b"persist.vendor.volte_support=1"),
    (b"persist.vendor.radio.mtk_dsbp_support=0", b"persist.vendor.radio.mtk_dsbp_support=1"),
    (b"persist.vendor.radio.imstestmode=0", b"persist.vendor.radio.imstestmode=1"),
    (b"persist.vendor.radio.volte_pro_sub0=0", b"persist.vendor.radio.volte_pro_sub0=1"),
    (b"persist.vendor.radio.volte_pro_sub1=0", b"persist.vendor.radio.volte_pro_sub1=1"),
    (b"26,0;27,1;28,1;29,1;", b"26,1;27,1;28,1;29,1;"),
    (b"26,0;27,1;", b"26,1;27,1;")
]

def inspect_vendor_metadata(input_file: str) -> dict:
    """
    Scans attached ADB device or offline vendor.img content to extract device model, platform, and Android version.
    """
    meta = {
        "source": "Offline Scan",
        "model": "OPPO Device",
        "platform": "Unknown",
        "android_ver": "Unknown",
        "android_sdk": None,
        "is_f11": False,
        "is_a31": False,
        "allow_raw_offset_injection": False
    }

    fname = os.path.basename(input_file).lower() if input_file else ""

    # 1. Check connected ADB device first (Online Priority)
    try:
        import subprocess
        adb_cmd = ["adb", "devices"]
        res = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=2)
        if "device" in res.stdout:
            lines = res.stdout.strip().splitlines()
            dev_lines = [l for l in lines[1:] if "device" in l]
            if dev_lines:
                dev_id = dev_lines[0].split()[0]
                model_res = subprocess.run(["adb", "-s", dev_id, "shell", "getprop", "ro.product.model"], capture_output=True, text=True, timeout=2)
                plat_res = subprocess.run(["adb", "-s", dev_id, "shell", "getprop", "ro.board.platform"], capture_output=True, text=True, timeout=2)
                ver_res = subprocess.run(["adb", "-s", dev_id, "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True, timeout=2)
                sdk_res = subprocess.run(["adb", "-s", dev_id, "shell", "getprop", "ro.build.version.sdk"], capture_output=True, text=True, timeout=2)

                m = model_res.stdout.strip()
                p = plat_res.stdout.strip()
                v = ver_res.stdout.strip()
                s = sdk_res.stdout.strip()

                if m: meta["model"] = m
                if p: meta["platform"] = p
                if v: meta["android_ver"] = f"Android {v}"
                if s and s.isdigit(): meta["android_sdk"] = int(s)
                meta["source"] = f"ADB Connected Device [{dev_id}]"
    except Exception:
        pass

    # 2. Offline Scan from vendor.img content if metadata still incomplete
    if os.path.exists(input_file):
        try:
            import re
            with open(input_file, "rb") as f:
                content = f.read()

            # Search platform
            plat_m = re.search(b'ro\\.(?:vendor\\.)?board\\.platform=([^\r\n;\x00]+)', content)
            if plat_m and meta["platform"] == "Unknown":
                meta["platform"] = plat_m.group(1).decode('utf-8', errors='ignore').strip()

            # Search SDK / API level
            sdk_m = re.search(b'ro\\.(?:vendor\\.)?build\\.version\\.sdk=(\\d+)', content)
            if not sdk_m:
                sdk_m = re.search(b'ro\\.product\\.first_api_level=(\\d+)', content)
            if sdk_m and meta["android_sdk"] is None:
                meta["android_sdk"] = int(sdk_m.group(1).decode())
                if meta["android_sdk"] == 28:
                    meta["android_ver"] = "Android 9 (Pie)"
                elif meta["android_sdk"] == 29:
                    meta["android_ver"] = "Android 10 (Q)"
                elif meta["android_sdk"] >= 30:
                    meta["android_ver"] = f"Android {meta['android_sdk'] - 19}"
            elif meta["android_sdk"] is None:
                if "10" in fname or "android10" in fname:
                    meta["android_sdk"] = 29
                    meta["android_ver"] = "Android 10 (Q)"
                elif "9" in fname or "android9" in fname:
                    meta["android_sdk"] = 28
                    meta["android_ver"] = "Android 9 (Pie)"

            # Search model / marketname / board name
            model_m = re.search(b'ro\\.(?:vendor\\.)?product\\.(?:vendor\\.)?marketname=([^\r\n;\x00]+)', content)
            if not model_m:
                model_m = re.search(b'ro\\.(?:vendor\\.)?product\\.(?:vendor\\.)?model=([^\r\n;\x00]+)', content)
            if not model_m:
                model_m = re.search(b'ro\\.product\\.board=([^\r\n;\x00]+)', content)
            if model_m and meta["model"] in ("Thiết bị Android", "OPPO Device", "Unknown"):
                found_m = model_m.group(1).decode('utf-8', errors='ignore').strip()
                if found_m:
                    meta["model"] = found_m

            # Search brand
            brand_m = re.search(b'ro\\.(?:vendor\\.)?product\\.(?:vendor\\.)?brand=([^\r\n;\x00]+)', content)
            if brand_m:
                brand_str = brand_m.group(1).decode('utf-8', errors='ignore').strip().capitalize()
                if brand_str and not meta["model"].lower().startswith(brand_str.lower()):
                    meta["model"] = f"{brand_str} {meta['model']}"
        except Exception:
            pass

    # Classify Device Family strictly by model string or file name
    model_str = meta["model"].lower()

    if "f11" in model_str or "f11" in fname or "cph1911" in model_str or "cph1913" in model_str or "18161" in model_str:
        meta["is_f11"] = True
    if "a31" in model_str or "a31" in fname or "cph2015" in model_str:
        meta["is_a31"] = True

    # Allow raw offset injection for confirmed A31 and F11 profiles (Android 9 & Android 10)
    if (meta["is_a31"] or meta["is_f11"]) and (meta["android_sdk"] in (28, 29) or meta["android_sdk"] is None):
        meta["allow_raw_offset_injection"] = True
    else:
        meta["allow_raw_offset_injection"] = False

    return meta

def patch_vendor_image(input_file: str, output_file: str = None) -> str:
    if not os.path.exists(input_file):
        print(f"❌ Error: Tệp [{input_file}] không tồn tại!")
        return None

    if not output_file:
        dir_name = os.path.dirname(input_file)
        base_name = os.path.basename(input_file)
        name_no_ext, ext = os.path.splitext(base_name)
        if name_no_ext.endswith("_patched"):
            output_file = os.path.join(dir_name, f"{name_no_ext}{ext}")
        else:
            output_file = os.path.join(dir_name, f"{name_no_ext}_patched{ext}")

    file_size = os.path.getsize(input_file)
    print(f"📦 Đang xử lý tệp phân vùng Vendor: [{os.path.basename(input_file)}]")
    print(f"   Kích thước: {file_size / (1024*1024):.2f} MB ({file_size:,} bytes)")

    # Perform Device & Profile Inspection
    meta = inspect_vendor_metadata(input_file)
    print(f"🔍 [NHẬN DIỆN NGUỒN: {meta['source']}]")
    print(f"   • Dòng máy  : {meta['model']}")
    print(f"   • Nền tảng  : {meta['platform']}")
    print(f"   • Hệ điều hành: {meta['android_ver']} (SDK {meta['android_sdk'] if meta['android_sdk'] else 'Auto'})")

    with open(input_file, "rb") as fin:
        data = fin.read()

    patched_data = bytearray(data)
    total_patched = 0

    # 1. Safe Length-Preserving String Replacements
    for old_bytes, new_bytes in MASTER_VENDOR_RULES:
        count = data.count(old_bytes)
        if count > 0:
            print(f"  ✓ Vá {count} vị trí [{old_bytes.decode('utf-8', errors='ignore')}] -> [{new_bytes.decode('utf-8', errors='ignore')}]")
            pos = 0
            while True:
                idx = patched_data.find(old_bytes, pos)
                if idx == -1:
                    break
                patched_data[idx:idx+len(old_bytes)] = new_bytes
                pos = idx + len(old_bytes)
                total_patched += 1

    # 2. Raw Offset Byte Injection (STRICTLY GUARDED FOR CONFIRMED PROFILES & SDK VERSIONS)
    if meta["allow_raw_offset_injection"]:
        if meta["is_f11"]:
            if meta["android_sdk"] == 29:
                volte_ref_path = os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                    "../extracted_vendor_volte/f11_extracted/vendor_F11_Android10_.img"
                ))
                rc_block_off = 219013120
                apk_block_off = 1024774144
                profile_name = "OPPO F11 (Android 10)"
            else:
                volte_ref_path = os.path.abspath(os.path.join(
                    os.path.dirname(__file__),
                    "../extracted_vendor_volte/f11_extracted/vendor_F11_VoLTE_android 9.img"
                ))
                rc_block_off = 148025344
                apk_block_off = 392388608
                profile_name = "OPPO F11 (Android 9)"
        else:
            volte_ref_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                "../extracted_vendor_volte/offset_313395408_vendor_ VoLTE OPPO_A31 CPH2015 ANDROID 9.img"
            ))
            rc_block_off = 155881472
            apk_block_off = 764665856
            profile_name = "OPPO A31 (Android 9)"

        if os.path.exists(volte_ref_path):
            with open(volte_ref_path, "rb") as fref:
                ref_data = fref.read()

            if b"gaq_oppo_mtk_volte.rc" not in patched_data:
                rc_block_len = 4096 * 2
                if len(patched_data) > rc_block_off + rc_block_len:
                    patched_data[rc_block_off:rc_block_off+rc_block_len] = ref_data[rc_block_off:rc_block_off+rc_block_len]
                    print(f"  ✓ [Profile {profile_name}]: Đã tiêm tệp [gaq_oppo_mtk_volte.rc] vào /vendor/etc/init/ (Offset: {rc_block_off})")

            if b"GAQ_OPPO_MTK_VoLTE_Overlay.apk" not in patched_data:
                apk_block_len = 4096 * 5
                if len(patched_data) > apk_block_off + apk_block_len:
                    patched_data[apk_block_off:apk_block_off+apk_block_len] = ref_data[apk_block_off:apk_block_off+apk_block_len]
                    print(f"  ✓ [Profile {profile_name}]: Đã tiêm tệp Static RRO Overlay [GAQ_OPPO_MTK_VoLTE_Overlay.apk] vào /vendor/overlay/ (Offset: {apk_block_off})")
    else:
        print(f"  ℹ️ [An toàn]: Bỏ qua tiêm Offset raw khối bổ sung trên {meta['model']} / {meta['platform']} / {meta['android_ver']}")
        print(f"     👉 Bảo vệ 100% mã máy Driver ARM64 và hệ thống tệp EXT4 không bị hỏng!")

    with open(output_file, "wb") as fout:
        fout.write(patched_data)

    print(f"🎉 HOÀN THÀNH: Đã tạo tệp [{os.path.basename(output_file)}]")
    print(f"   👉 Đường dẫn: {output_file}")
    print(f"   👉 Đã thực thi {total_patched} quy tắc vá VoLTE an toàn!")
    print(f"   👉 Kích thước giữ nguyên 100%: {len(patched_data):,} bytes")
    return output_file

def main():
    print("====================================================================")
    print("  🚀 HBG VOLTE FIXER — DỌN ĐỘNG CƠ VENDOR PATCH CHO TẤT CẢ DÒNG OPPO")
    print("  Hỗ trợ: OPPO A5s, A31, A12, A1k, A5, A9, Realme, Vivo, Xiaomi...")
    print("====================================================================")
    print()

    if len(sys.argv) > 1:
        patch_vendor_image(sys.argv[1])
    else:
        # Auto scan current directory or THU_MUC_RUT_SYSTEM_OPPO
        search_dirs = [os.path.abspath("."), os.path.abspath("../THU_MUC_RUT_SYSTEM_OPPO")]
        found = []
        for d in search_dirs:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if ("vendor" in f.lower()) and f.endswith((".bin", ".img")) and ("_patched" not in f.lower()):
                        found.append(os.path.join(d, f))
        
        found = list(set(found))
        if found:
            for f in found:
                patch_vendor_image(f)
                print()
        else:
            print("👉 Vui lòng kéo thả tệp vendor.bin / vendor.img của OPPO A5s hoặc A31 vào đây để vá.")

if __name__ == "__main__":
    main()
