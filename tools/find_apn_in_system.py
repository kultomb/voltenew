import os

def main():
    sys_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    
    with open(sys_path, "rb") as f:
        sdata = f.read()

    print("=== SEARCHING APNs IN SYSTEM.BIN ===")
    
    targets = [
        b"apns-conf.xml",
        b"apn carrier=",
        b'apn="v-internet"',
        b'apn="v-wap"',
        b'mcc="452"',
        b'apn="ims"'
    ]

    for t in targets:
        pos = 0
        matches = []
        while True:
            idx = sdata.find(t, pos)
            if idx == -1:
                break
            matches.append(idx)
            pos = idx + len(t)
        print(f"Target [{t.decode('utf-8', errors='ignore')}]: {len(matches)} matches")
        for m in matches[:5]:
            print(f"  Offset {m}: {sdata[max(0, m-20) : m + len(t) + 60]}")
        print()

if __name__ == "__main__":
    main()
