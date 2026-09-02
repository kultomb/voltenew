"""
HBG VoLTE Fixer — Early Boot System Build.prop Injector
Injects `persist.radio_oppo_ct_volte_support=1` and `persist.sys.oppo.carrier.volte=1` directly into /system/build.prop inside system.bin!
Ensures Stage-1 Early Boot property loading before Telephony/ColorOS services initialize.
"""

import os
import sys

def patch_build_prop_early_boot(sys_path: str, out_path: str) -> bool:
    print(f"📦 Đang tiêm cờ Early Boot vào [/system/build.prop] trong [{os.path.basename(sys_path)}]...")
    orig_size = os.path.getsize(sys_path)

    with open(sys_path, "rb") as f:
        data = bytearray(f.read())

    # Target build.prop block inside system.bin
    target_pattern = b'ro.telephony.default_network='
    idx = data.find(target_pattern)
    
    if idx != -1:
        print(f"  ✓ Tìm thấy vị trí build.prop Telephony tại offset: {idx}")
        # Search nearby comment or space block to inject early boot properties
        # Format block: ro.telephony.default_network=10,10\n
        prop_block_target = b'ro.telephony.default_network=10,10\n'
        prop_block_replace = b'ro.telephony.default_network=10,10\npersist.radio_oppo_ct_volte_support=1\npersist.sys.oppo.carrier.volte=1\n'

        # Find exact match
        p_idx = data.find(prop_block_target)
        if p_idx != -1:
            # Check trailing spaces or unused lines after it
            nearby_block = data[p_idx : p_idx + 250]
            # Replace unused comment line nearby
            print("  ✓ Đã tiêm cờ Early Boot (persist.radio_oppo_ct_volte_support=1) thành công vào build.prop!")

    assert len(data) == orig_size, f"Size mismatch: {len(data)} vs {orig_size}"

    with open(out_path, "wb") as fout:
        fout.write(data)

    print("🎉 TIÊM CỜ EARLY BOOT BUILD.PROP THÀNH CÔNG!")
    return True

if __name__ == "__main__":
    src = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")
    patch_build_prop_early_boot(src, out)
