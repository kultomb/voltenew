"""
HBG VoLTE Fixer — Deep Vendor.bin MTK RIL Modem Patching Module
Patches libmtk-ril.so and vendor.build.prop inside vendor.bin to force MediaTek modem baseband VoLTE support!
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def patch_vendor_bin_modem(vendor_path: str, out_path: str) -> bool:
    print(f"📦 Đang xử lý tiêm sâu vào Vendor RIL Modem Driver [{os.path.basename(vendor_path)}]...")
    
    orig_size = os.path.getsize(vendor_path)

    with open(vendor_path, "rb") as f:
        data = bytearray(f.read())

    patches_applied = 0

    # 1. Patch persist.vendor.volte_support\x000 -> \x001
    target1 = b"persist.vendor.volte_support\x000"
    replace1 = b"persist.vendor.volte_support\x001"
    
    pos = 0
    while True:
        idx = data.find(target1, pos)
        if idx == -1:
            break
        data[idx : idx + len(target1)] = replace1
        patches_applied += 1
        print(f"  ✓ Đã vá cờ RIL Modem persist.vendor.volte_support=1 tại offset: {idx}")
        pos = idx + len(target1)

    # 2. Patch persist.sys.oppo.carrier.volte=0 or empty in vendor
    target2 = b"persist.radio_oppo_ct_volte_support=2"
    replace2 = b"persist.radio_oppo_ct_volte_support=1"
    pos = 0
    while True:
        idx = data.find(target2, pos)
        if idx == -1:
            break
        data[idx : idx + len(target2)] = replace2
        patches_applied += 1
        print(f"  ✓ Đã vá cờ RIL Modem persist.radio_oppo_ct_volte_support=1 tại offset: {idx}")
        pos = idx + len(target2)

    # 3. Patch persist.vendor.mtk.volte.enable=0
    target3 = b"persist.vendor.mtk.volte.enable=0"
    replace3 = b"persist.vendor.mtk.volte.enable=1"
    pos = 0
    while True:
        idx = data.find(target3, pos)
        if idx == -1:
            break
        data[idx : idx + len(target3)] = replace3
        patches_applied += 1
        print(f"  ✓ Đã vá cờ RIL Modem persist.vendor.mtk.volte.enable=1 tại offset: {idx}")
        pos = idx + len(target3)

    assert len(data) == orig_size, f"Vendor file size mismatch: {len(data)} vs {orig_size}"

    with open(out_path, "wb") as fout:
        fout.write(data)

    print(f"🎉 ĐÃ VÁ THÀNH CÔNG {patches_applied} VỊ TRÍ TRONG VENDOR.BIN -> [{os.path.basename(out_path)}]")
    return True

if __name__ == "__main__":
    vpath = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\vendor_patched.bin")
    patch_vendor_bin_modem(vpath, out_path)
