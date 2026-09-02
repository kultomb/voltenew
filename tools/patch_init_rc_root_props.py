"""
HBG VoLTE Fixer — Root Init.rc Boot Property Injector for OPPO
Injects permanent root setprop commands into init.rc inside system.bin so Android init process executes them on every boot as root!
"""

import os
import sys

def patch_init_rc(sys_path: str, out_path: str) -> bool:
    print(f"📦 Đang đọc [{os.path.basename(sys_path)}] để tiêm lệnh Root Init.rc...")

    with open(sys_path, "rb") as f:
        data = bytearray(f.read())

    target_comment = b"# Kun.Hu@PSW.TECH.RELIABILTY, 2019/1/21, add for project phoenix(hang oppo)\n    setprop sys.oppo.phoenix.prepare_log boot_success"
    idx = data.find(target_comment)

    if idx == -1:
        print("✗ Không tìm thấy khối init.rc target")
        return False

    print(f"✓ Tìm thấy khối init.rc tại offset: {idx}")

    # Build replacement of exact same length
    replacement = b"    setprop persist.radio_oppo_ct_volte_support 1\n    setprop persist.sys.oppo.carrier.volte 1\n    setprop persist.vendor.mtk.volte.enable 1"
    
    if len(replacement) < len(target_comment):
        padding = len(target_comment) - len(replacement)
        replacement += b"\n" + b"#" * (padding - 1)

    print(f"  Gốc ({len(target_comment)} bytes) -> Thay thế ({len(replacement)} bytes)")

    data[idx : idx + len(target_comment)] = replacement

    with open(out_path, "wb") as fout:
        fout.write(data)

    print(f"🎉 TIÊM LỆNH ROOT INIT.RC THÀNH CÔNG -> [{os.path.basename(out_path)}]")
    return True

if __name__ == "__main__":
    src_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")
    patch_init_rc(src_path, out_path)
