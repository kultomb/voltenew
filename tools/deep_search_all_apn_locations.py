"""
Deep APN XML Finder across system.bin and vendor.bin
"""
import os, sys

def search_bin(bin_path, bin_name):
    print(f"=== SEARCHING {bin_name} ({os.path.getsize(bin_path)} bytes) ===")
    with open(bin_path, "rb") as f:
        data = f.read()

    targets = [
        b"apns-conf",
        b"apns-version",
        b"v-internet",
        b"mcc=\"452\"",
        b"plmn=\"45204\"",
        b"45204",
        b"comm_simsettings"
    ]

    for t in targets:
        pos = 0
        matches = []
        while True:
            idx = data.find(t, pos)
            if idx == -1:
                break
            matches.append(idx)
            pos = idx + len(t)
        print(f"Target [{t.decode('utf-8', errors='ignore')}]: {len(matches)} matches")
        for m in matches[:10]:
            snippet = data[max(0, m-30) : m + len(t) + 70]
            print(f"  Offset {m}: {snippet}")
        print()

if __name__ == "__main__":
    sys_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    ven_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")
    search_bin(sys_path, "system.bin")
    search_bin(ven_path, "vendor.bin")
