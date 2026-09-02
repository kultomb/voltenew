import subprocess
import os
import sys

ADB = r"c:\Users\CMD\Desktop\volte_fixer_tool\adb\adb.exe"
DEV = "AEO7SCZTSSWCHMRK"

def run_adb(args):
    cmd = [ADB, "-s", DEV] + args
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return res.stdout.strip()

def main():
    print("=== DEEP LIVE ADB DIAGNOSTIC FOR OPPO A31 (AEO7SCZTSSWCHMRK) ===")
    
    # 1. Properties
    props_raw = run_adb(["shell", "getprop"])
    print("\n--- 1. CRITICAL VOLTE & IMS SYSTEM PROPERTIES ---")
    volte_props = []
    for line in props_raw.splitlines():
        if any(k in line.lower() for k in ["volte", "ims", "oppo", "mtk", "dsbp", "nvram", "carrier"]):
            volte_props.append(line)
            print(line)

    # 2. Settings Global & System & Secure
    print("\n--- 2. SYSTEM SETTINGS TOGGLES ---")
    for key in ["ims_vt_call_enabled", "volte_vt_enabled", "volte_user_setting", "vt_ims_enabled", "enhanced_4g_mode_enabled"]:
        val = run_adb(["shell", "settings", "get", "global", key])
        print(f"  • Global [{key}]: {val}")
        val_sec = run_adb(["shell", "settings", "get", "secure", key])
        print(f"  • Secure [{key}]: {val_sec}")

    # 3. Telephony Registry IMS State
    print("\n--- 3. TELEPHONY REGISTRY & IMS STATE ---")
    tele_raw = run_adb(["shell", "dumpsys", "telephony.registry"])
    for line in tele_raw.splitlines():
        if any(k in line.lower() for k in ["ims", "volte", "serviceState", "mServiceState", "mDataConnectionState"]):
            print(line[:120])

    # 4. APN Settings
    print("\n--- 4. APN CARRIER SETTINGS ---")
    apn_raw = run_adb(["shell", "content", "query", "--uri", "content://telephony/carriers/preferapn"])
    print("Prefer APN:", apn_raw[:200])

if __name__ == "__main__":
    main()
