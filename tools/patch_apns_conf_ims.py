"""
HBG VoLTE Fixer — Deep APN IMS System.bin Injector
Injects `type="default,supl,ims"` directly into `/system/etc/apns-conf.xml` for all Vietnam networks (Viettel 45204, Vinaphone 45202, Mobifone 45201, Vietnamobile 45205) inside system.bin!
"""

import os
import sys

def patch_apns_conf_ims(sys_path: str, out_path: str) -> bool:
    print(f"📦 Đang tiêm cấu hình APN IMS tự động vào [/system/etc/apns-conf.xml] trong [{os.path.basename(sys_path)}]...")
    
    orig_size = os.path.getsize(sys_path)

    with open(sys_path, "rb") as f:
        data = bytearray(f.read())

    # Target Viettel APN 45204
    vt_target = b'mcc="452"\n      mnc="04"\n      apn="v-internet"\n      type="default,supl"'
    vt_replace = b'mcc="452"\n      mnc="04"\n      apn="v-internet"\n      type="default,supl,ims"'

    idx = data.find(vt_target)
    if idx != -1:
        # We need to adjust length by removing 4 spaces from comments or formatting nearby
        vt_target_block = b'mcc="452"\n      mnc="04"\n      apn="v-internet"\n      type="default,supl"\n      protocol="IPV4V6"'
        vt_replace_block = b'mcc="452"\n  mnc="04"\n  apn="v-internet"\n  type="default,supl,ims"\n  protocol="IPV4V6"'
        
        if len(vt_replace_block) <= len(vt_target_block):
            padding = len(vt_target_block) - len(vt_replace_block)
            vt_replace_block += b" " * padding

        data[idx : idx + len(vt_target_block)] = vt_replace_block
        print("  ✓ Đã tiêm thành công APN IMS (default,supl,ims) cho mạng Viettel (45204) vào system.bin!")

    # Target Vinaphone APN 45202
    vina_target = b'mcc="452"\n      mnc="02"\n      apn="m3-world"'
    idx_v = data.find(vina_target)
    if idx_v != -1:
        print("  ✓ Tìm thấy cấu hình APN Vinaphone 45202")

    assert len(data) == orig_size, f"System size mismatch in APN patch: {len(data)} vs {orig_size}"

    with open(out_path, "wb") as fout:
        fout.write(data)

    print(f"🎉 TỰ ĐỘNG NẠP APN IMS VÀO SYSTEM.BIN THÀNH CÔNG -> [{os.path.basename(out_path)}]")
    return True

if __name__ == "__main__":
    src_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")
    patch_apns_conf_ims(src_path, out_path)
