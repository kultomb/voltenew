import subprocess
import json
import sys

def run_adb(cmd):
    try:
        res = subprocess.run(f"adb shell \"{cmd}\"", shell=True, capture_output=True, text=True, errors="ignore")
        return res.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

def main():
    print("==================================================")
    print("   ADB LIVE PHONE DIAGNOSTIC & VOLTE ANALYSIS     ")
    print("==================================================")

    # 1. Device Info
    print("\n--- [1] DEVICE IDENTIFICATION ---")
    print("Model:          ", run_adb("getprop ro.product.model"))
    print("Brand/Device:   ", run_adb("getprop ro.product.brand"), "/", run_adb("getprop ro.product.device"))
    print("Product Name:   ", run_adb("getprop ro.product.name"))
    print("Build Display:  ", run_adb("getprop ro.build.display.id"))
    print("Android Ver:    ", run_adb("getprop ro.build.version.release"))
    print("ColorOS Ver:    ", run_adb("getprop ro.build.version.opporom"))
    print("Platform:       ", run_adb("getprop ro.board.platform"))
    print("Baseband:       ", run_adb("getprop vendor.gsm.project.baseband"))

    # 2. SIM & Network
    print("\n--- [2] SIM & OPERATOR STATUS ---")
    print("SIM State:      ", run_adb("getprop gsm.sim.state"))
    print("Operator MCC/MNC:", run_adb("getprop gsm.sim.operator.numeric"))
    print("Operator Name:  ", run_adb("getprop gsm.sim.operator.alpha"))
    print("Network Type:   ", run_adb("getprop gsm.network.type"))

    # 3. Key VoLTE & IMS System Properties
    print("\n--- [3] VOLTE / IMS SYSTEM PROPERTIES ---")
    props = [
        "persist.mtk.ims_support",
        "persist.mtk.volte_support",
        "persist.mtk.volte.enable",
        "persist.radio.volte_state",
        "persist.dbg.volte_avail_ovr",
        "persist.dbg.vt_avail_ovr",
        "persist.vendor.mtk.ims_support",
        "persist.vendor.mtk.volte_support",
        "persist.vendor.mtk.volte.enable",
        "persist.vendor.radio.volte_state",
        "persist.vendor.mtk_dynamic_ims_switch",
        "persist.vendor.ims_support",
        "persist.vendor.mims_support",
        "persist.sys.oppo.carrier.volte",
        "persist.radio_oppo_ct_volte_support",
        "persist.vendor.mtk_ct_volte_support",
        "ro.vendor.md_auto_setup_ims",
        "persist.vendor.mtk_wfc_support",
        "persist.vendor.vilte_support",
        "persist.vendor.viwifi_support"
    ]
    for p in props:
        val = run_adb(f"getprop {p}")
        print(f"  {p:<38} = [{val}]")

    # 4. IMS Service / Registration Dumpsys
    print("\n--- [4] TELEPHONY REGISTRY & IMS REGISTRATION STATUS ---")
    telephony_reg = run_adb("dumpsys telephony.registry")
    ims_lines = []
    for line in telephony_reg.splitlines():
        if any(k in line.lower() for k in ["ims", "volte", "mvoiceregstat", "mdataregstat", "servicestate"]):
            ims_lines.append(line)
    
    if ims_lines:
        for l in ims_lines[:25]:
            print("  ", l)
    else:
        print("   (No telephony.registry IMS lines found)")

    # 5. Carrier Config check for Viettel (45204)
    print("\n--- [5] CARRIER CONFIG VOLTE KEYS ---")
    carrier_cfg = run_adb("dumpsys carrier_config")
    cfg_keys = ["carrier_volte_available_bool", "carrier_volte_provisioned_bool", "carrier_volte_provisioning_required_bool", "volte"]
    for line in carrier_cfg.splitlines():
        if any(k in line for k in cfg_keys):
            print("  ", line.strip())

    # 6. Check overlay packages on phone
    print("\n--- [6] INSTALLED OVERLAY PACKAGES ---")
    cmd_packages = run_adb("cmd overlay list")
    for line in cmd_packages.splitlines():
        if "volte" in line.lower() or "gaq" in line.lower() or "oppo" in line.lower():
            print("  ", line)

if __name__ == "__main__":
    main()
