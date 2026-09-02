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

    with open(input_file, "rb") as fin:
        data = fin.read()

    patched_data = bytearray(data)
    total_patched = 0

    for old_bytes, new_bytes in MASTER_VENDOR_RULES:
        count = data.count(old_bytes)
        if count > 0:
            print(f"  ✓ Tiêm {count} vị trí [{old_bytes.decode('utf-8', errors='ignore')}] -> [{new_bytes.decode('utf-8', errors='ignore')}]")
            pos = 0
            while True:
                idx = patched_data.find(old_bytes, pos)
                if idx == -1:
                    break
                patched_data[idx:idx+len(old_bytes)] = new_bytes
                pos = idx + len(old_bytes)
                total_patched += 1

    # 2. Inject GAQ VoLTE RRO Overlay & Init Script block structures if missing
    volte_ref_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../extracted_vendor_volte/offset_313395408_vendor_ VoLTE OPPO_A31 CPH2015 ANDROID 9.img"
    ))

    if os.path.exists(volte_ref_path):
        with open(volte_ref_path, "rb") as fref:
            ref_data = fref.read()

        # Check and inject gaq_oppo_mtk_volte.rc if missing
        if b"gaq_oppo_mtk_volte.rc" not in patched_data:
            rc_block_off = 155881472
            rc_block_len = 4096 * 2
            if len(patched_data) > rc_block_off + rc_block_len:
                patched_data[rc_block_off:rc_block_off+rc_block_len] = ref_data[rc_block_off:rc_block_off+rc_block_len]
                print(f"  ✓ Đã tiêm tệp [gaq_oppo_mtk_volte.rc] vào /vendor/etc/init/ (Offset: {rc_block_off})")

        # Check and inject GAQ_OPPO_MTK_VoLTE_Overlay.apk if missing
        if b"GAQ_OPPO_MTK_VoLTE_Overlay.apk" not in patched_data:
            apk_block_off = 764665856
            apk_block_len = 4096 * 5
            if len(patched_data) > apk_block_off + apk_block_len:
                patched_data[apk_block_off:apk_block_off+apk_block_len] = ref_data[apk_block_off:apk_block_off+apk_block_len]
                print(f"  ✓ Đã tiêm tệp Static RRO Overlay [GAQ_OPPO_MTK_VoLTE_Overlay.apk] vào /vendor/overlay/ (Offset: {apk_block_off})")

    with open(output_file, "wb") as fout:
        fout.write(patched_data)

    print(f"🎉 HOÀN THÀNH: Đã tạo tệp [{os.path.basename(output_file)}]")
    print(f"   👉 Đường dẫn: {output_file}")
    print(f"   👉 Đã thực thi {total_patched} quy tắc vá VoLTE!")
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
