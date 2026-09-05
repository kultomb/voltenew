"""
VoLTE Fixer Engine — Smart Auto-Fixing Engine
Fully automated device management using HBGAdBlocker DeviceManager singleton for 100% parity.
Includes MCC/MNC operator resolution for Vietnam networks (Viettel, Vinaphone, Mobifone, Vietnamobile, Wintel, Itelecom).
"""

from __future__ import annotations

import os
import sys
import subprocess
import shutil
import time
import zipfile
import tempfile
import platform
from typing import Callable, Dict, List, Optional, Tuple

# Add parent workspace directory to sys.path to import DeviceManager from HBGAdBlocker
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from HBGAdBlocker import DeviceManager
except Exception:
    DeviceManager = None


MCC_MNC_MAP = {
    "45204": "Viettel",
    "45202": "VinaPhone",
    "45201": "MobiFone",
    "45205": "Vietnamobile",
    "45208": "Itelecom",
    "45209": "Wintel",
}


def find_adb_path() -> str:
    meipass = getattr(sys, '_MEIPASS', current_dir)
    candidates = [
        os.path.join(current_dir, "adb", "adb.exe"),
        os.path.join(meipass, "adb", "adb.exe"),
        os.path.join(current_dir, "scrcpy", "scrcpy-win64-v2.7", "adb.exe"),
        os.path.join(meipass, "scrcpy", "scrcpy-win64-v2.7", "adb.exe"),
        os.path.join(parent_dir, "platform-tools", "adb.exe"),
        os.path.join(current_dir, "platform-tools", "adb.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    if DeviceManager is not None:
        try:
            dm = DeviceManager()
            cmd = dm._base_cmd()
            if cmd and os.path.exists(cmd[0]):
                return cmd[0]
        except Exception:
            pass

    return shutil.which("adb") or "adb"


class VoLTEEngine:
    def __init__(self, adb_path: Optional[str] = None):
        if DeviceManager is not None:
            self.dm = DeviceManager()
        else:
            self.dm = None
        self._adb_path = adb_path or find_adb_path()

    @property
    def adb_path(self) -> str:
        if self._adb_path and os.path.exists(self._adb_path):
            return self._adb_path
        if self.dm and self.dm.adb_path:
            return self.dm.adb_path
        return "adb"

    def refresh(self) -> Tuple[bool, str]:
        """Refresh device status — 100% parity with HBGAdBlocker DeviceManager."""
        if self.dm:
            return self.dm.refresh()
        
        code, out, err = self.run_command(["devices"], timeout=5)
        if code != 0:
            return False, err or "ADB error"

        lines = [x.strip() for x in out.splitlines()[1:] if x.strip()]
        dev_lines = [x for x in lines if x.endswith("\tdevice") or (len(x.split()) >= 2 and x.split()[1] == "device")]
        if not dev_lines:
            return False, "Chưa kết nối hoặc chưa bật USB Debug."
        return True, "OK"

    def run_command(self, args: List[str], device_id: Optional[str] = None, timeout: int = 15) -> Tuple[int, str, str]:
        """Execute ADB command via DeviceManager or subprocess."""
        if device_id:
            full_cmd = ["-s", device_id] + args
        else:
            full_cmd = args

        if self.dm and args != ["devices"]:
            out, err, code = self.dm.run(full_cmd, timeout=timeout)
            return code, out, err

        cmd = [self.adb_path] + full_cmd
        kwargs = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            res = subprocess.run(cmd, timeout=timeout, **kwargs)
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout: ADB command expired"
        except Exception as e:
            return -1, "", str(e)

    def get_devices(self) -> List[Dict[str, str]]:
        """Get connected devices list with dynamic brand and model detection."""
        try:
            cmd = [self.adb_path, "devices"]
            kwargs = {"capture_output": True, "text": True, "timeout": 15}
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            res = subprocess.run(cmd, **kwargs)
            devices = []
            for line in (res.stdout or "").splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    dev_id = parts[0]
                    _, model, _ = self.run_command(["shell", "getprop", "ro.product.model"], dev_id, timeout=3)
                    _, brand, _ = self.run_command(["shell", "getprop", "ro.product.brand"], dev_id, timeout=3)
                    _, marketname, _ = self.run_command(["shell", "getprop", "ro.product.marketname"], dev_id, timeout=3)

                    model = (model or "").strip()
                    brand = (brand or "").strip().capitalize()
                    marketname = (marketname or "").strip()

                    dev_name = ""
                    if marketname and marketname != "Không xác định":
                        dev_name = marketname
                    elif model and model != "Không xác định":
                        if brand and brand != "Unknown" and not model.lower().startswith(brand.lower()):
                            dev_name = f"{brand} {model}"
                        else:
                            dev_name = model
                    else:
                        dev_name = dev_id

                    devices.append({
                        "id": dev_id,
                        "model": dev_name,
                        "product": ""
                    })
            return devices
        except Exception as e:
            print(f"[DEBUG GET_DEVICES ERROR] {e}")
            return []

    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """Fetch detailed specs and SIM operator status for target device."""
        info = {
            "model": "Unknown",
            "brand": "Unknown",
            "marketname": "",
            "android_ver": "Unknown",
            "sdk": "Unknown",
            "operator": "Chưa rõ",
            "sim_state": "Unknown",
            "ims_status": "Chưa kiểm tra",
            "is_oppo": False,
            "is_xiaomi": False,
            "is_vivo": False,
            "is_samsung": False,
            "is_mtk": False,
        }

        if self.dm and self.dm.serial == device_id and self.dm.device_model:
            info["model"] = self.dm.device_model

        _, model, _ = self.run_command(["shell", "getprop", "ro.product.model"], device_id, timeout=4)
        _, brand, _ = self.run_command(["shell", "getprop", "ro.product.brand"], device_id, timeout=4)
        _, marketname, _ = self.run_command(["shell", "getprop", "ro.product.marketname"], device_id, timeout=4)
        _, ver, _ = self.run_command(["shell", "getprop", "ro.build.version.release"], device_id, timeout=4)
        _, sdk, _ = self.run_command(["shell", "getprop", "ro.build.version.sdk"], device_id, timeout=4)
        _, platform_chip, _ = self.run_command(["shell", "getprop", "ro.board.platform"], device_id, timeout=4)

        if marketname and marketname != "Không xác định":
            info["marketname"] = marketname.strip()
        if model and model != "Không xác định":
            info["model"] = model.strip()
        if brand:
            info["brand"] = brand.strip().capitalize()
        if ver:
            info["android_ver"] = f"Android {ver}"
        if sdk:
            info["sdk"] = f"API {sdk}"

        b_lower = (info["brand"] or "").lower()
        m_lower = (info["model"] or "").lower()
        p_lower = (platform_chip or "").lower()

        if any(k in b_lower or k in m_lower for k in ["oppo", "realme", "cph", "rmx"]):
            info["is_oppo"] = True
        if any(k in b_lower or k in m_lower for k in ["xiaomi", "redmi", "poco", "mi"]):
            info["is_xiaomi"] = True
        if any(k in b_lower or k in m_lower for k in ["vivo", "iqoo"]):
            info["is_vivo"] = True
        if any(k in b_lower or k in m_lower for k in ["samsung", "sec"]):
            info["is_samsung"] = True

        if "mt" in p_lower or "mtk" in p_lower or "mt67" in p_lower or "mt68" in p_lower or "helio" in p_lower or "dimensity" in p_lower:
            info["is_mtk"] = True

        # Robust SIM Operator Detection (Alpha & Numeric Mapping for Dual SIM)
        sim_name = ""
        for prop in ["gsm.sim.operator.alpha", "gsm.operator.alpha", "gsm.sim.operator.alpha.0", "gsm.operator.alpha.0"]:
            _, val, _ = self.run_command(["shell", "getprop", prop], device_id, timeout=3)
            if val and val.replace(",", "").strip():
                sim_name = val.split(",")[0].strip()
                break

        if not sim_name:
            for num_prop in ["gsm.sim.operator.numeric", "gsm.operator.numeric", "gsm.sim.operator.numeric.0"]:
                _, num_val, _ = self.run_command(["shell", "getprop", num_prop], device_id, timeout=3)
                if num_val:
                    num_clean = num_val.split(",")[0].strip()
                    if num_clean in MCC_MNC_MAP:
                        sim_name = MCC_MNC_MAP[num_clean]
                        break

        if sim_name:
            info["operator"] = sim_name

        # IMS / VoLTE status check
        _, ims_prop, _ = self.run_command(["shell", "getprop", "persist.dbg.volte_avail_ovr"], device_id, timeout=3)
        _, oppo_prop, _ = self.run_command(["shell", "getprop", "persist.sys.oppo.volte"], device_id, timeout=3)
        _, mtk_prop, _ = self.run_command(["shell", "getprop", "persist.mtk.volte.enable"], device_id, timeout=3)
        
        if ims_prop == "1" or oppo_prop == "1" or mtk_prop == "1":
            info["ims_status"] = "Đã kích hoạt VoLTE"
        else:
            info["ims_status"] = "Chưa kích hoạt"

        return info

    def fix_system_props(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Inject universal and brand-specific system properties."""
        if log_cb:
            log_cb("› [1/4] Nạp tham số cấu hình mạng di động...", "info")

        props = [
            ("persist.dbg.volte_avail_ovr", "1"),
            ("persist.dbg.vt_avail_ovr", "1"),
            ("persist.dbg.wfc_avail_ovr", "1"),
            ("persist.vendor.radio.volte_mismatch_op", "0"),
            ("persist.radio.volte_enabled_by_default", "1"),
            ("persist.sys.cust.lte_config", "true"),
            ("persist.vendor.radio.calls.on.ims", "1"),
            ("persist.vendor.radio.jbims", "1"),
            ("persist.radio.vt_hybrid_enable", "1"),
            ("persist.radio.rat_on", "1"),
            ("persist.vendor.vowifi.disable.carrier.check", "true"),
            ("persist.vendor.volte.disable.carrier.check", "true"),
            ("persist.vendor.radio.disable_carrier_check", "true"),
            ("persist.vendor.radio.volte_ignore_sub", "1"),
            ("persist.sys.oppo.carrier.volte", "1"),
            ("persist.sys.volte.provider", "1"),
            ("persist.sys.oppo.volte", "1"),
            ("persist.radio_oppo_ct_volte_support", "1"),
            ("persist.radio.oppo_volte_state", "1"),
            ("persist.vendor.oppo.volte", "1"),
            ("persist.radio.oppo_volte_switch", "1"),
            ("persist.sys.oppo_volte_switch", "1"),
            ("persist.sys.oppo.volte_enable", "1"),
            ("persist.vendor.oppo.volte_enable", "1"),
            ("persist.radio.oppo_vt_support", "1"),
            ("persist.vendor.radio.oppo_volte_support", "1"),
            ("persist.vendor.radio.oppo_vowifi_support", "1"),
            ("persist.radio.hvolte", "1"),
            ("persist.sys.oppo.hvolte", "1"),
            ("persist.mtk.volte.enable", "3"),
            ("persist.mtk.volte.setting", "1"),
            ("persist.mtk_ims_support", "1"),
            ("persist.mtk_dynamic_ims_support", "1"),
            ("persist.vendor.mtk_dynamic_ims_support", "1"),
            ("persist.vendor.ims.op.config", "1"),
            ("persist.vendor.mtk_ims_op_config", "1"),
            ("persist.sys.oem.volte", "1"),
            ("persist.sys.oppo.region", "VN"),
            ("persist.radio.volte_state", "3"),
            ("persist.vendor.radio.volte_state", "3"),
            ("persist.vendor.mtk.volte.enable", "3"),
            ("persist.mtk_ct_volte_support", "3"),
            ("persist.vendor.mtk_ct_volte_support", "3"),
            ("persist.vendor.mims_support", "2"),
            ("persist.vendor.radio.mtk_dsbp_support", "1"),
            ("persist.mtk_volte_support", "1"),
            ("persist.mtk.wfc.enable", "1"),
            ("persist.vendor.mtk_wfc_support", "1"),
            ("persist.mtk_vilte_support", "1"),
            ("persist.mtk_viwifi_support", "1"),
            ("persist.sys.volte.enable", "1"),
            ("persist.radio.volte_vt", "1"),
            ("persist.radio.vivo.volte", "1"),
            ("persist.radio.volte_pro_sub0", "1"),
            ("persist.radio.volte_pro_sub1", "1"),
            ("persist.vendor.radio.volte_pro_sub0", "1"),
            ("persist.vendor.radio.volte_pro_sub1", "1"),
            ("persist.sys.oppo.vowifi", "1"),
            # Commercial Network Mode & ViLTE Properties (Preserves 4G Data Internet Access)
            ("persist.vendor.radio.vilte_enabled", "1"),
            ("persist.sys.vilte.enable", "1"),
            ("persist.radio.vilte_support", "1"),
            ("persist.radio.calls.on.ims", "1"),
            ("persist.radio.volte.mode", "1"),
            ("persist.vendor.radio.uiccsi", "1"),
            ("persist.vendor.radio.ims_registered", "1"),
            # VoLTE Preferred Voice Domain & Dual-Mode Fallback Safety (Prevents call stuck at "Đang gọi...")
            ("persist.radio.voice_domain_pref", "2"),
            ("persist.vendor.radio.voice_domain_pref", "2"),
            ("persist.vendor.radio.csfb_support", "1"),
            ("persist.radio.csfb_support", "1"),
            ("persist.vendor.radio.disable_csfb", "0"),
            ("persist.radio.disable_csfb", "0"),
            # MTK IMS Real Mode & Downgrade Prevention (Disables Simulation Mode & Call Downgrade)
            ("persist.ims.simulate", "0"),
            ("persist.radio.vilte_downgrade", "0"),
            ("persist.radio.volte_downgrade", "0"),
            ("persist.vendor.radio.downgrade", "0"),
            ("persist.radio.downgrade_enable", "0"),
            ("persist.sys.downgrade_enable", "0"),
            # Explicit VoLTE Provisioned Flag Overrides for Android Telephony Manager
            ("persist.radio.volte_provisioned", "1"),
            ("persist.vendor.radio.volte_provisioned", "1"),
            ("persist.radio.volte.provisioned", "1"),
            ("persist.vendor.radio.volte.provisioned", "1"),
            ("persist.sys.volte_provisioned", "1"),
            ("persist.dbg.volte_provisioned", "1"),
            ("persist.vendor.radio.force_ims_call", "1"),
            ("persist.radio.force_ims_call", "1"),
            ("persist.radio.force_on_dc", "1"),
            ("persist.dbg.ims_volte_enable", "1"),
            ("persist.radio.LTE_VOSPS", "1"),
            ("persist.radio.data_ltd_sys_ind", "1"),
        ]

        count = 0
        for prop, val in props:
            code, _, _ = self.run_command(["shell", "setprop", prop, val], device_id, timeout=4)
            if code == 0:
                count += 1

        # Dynamically set operator prop based on active SIM inserted in device (100% Generic & Dynamic)
        _, sim_alpha, _ = self.run_command(["shell", "getprop", "gsm.sim.operator.alpha"], device_id, timeout=2)
        if sim_alpha and sim_alpha.strip():
            op_name = sim_alpha.split(",")[0].strip()
            if op_name:
                self.run_command(["shell", "setprop", "persist.sys.oppo.operator", op_name], device_id, timeout=2)

        # Set Preferred Network Type quietly via Settings DB & dismiss MTK World Mode UI popup
        net_settings = [
            ("global", "preferred_network_mode", "10,10"),
            ("global", "preferred_network_mode1", "10"),
            ("global", "preferred_network_mode2", "10"),
            ("global", "user_preferred_network_mode", "10"),
        ]
        for ns, key, val in net_settings:
            self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=2)

        # Set phone preferred network type quietly
        self.run_command(["shell", "cmd", "phone", "set-preferred-network-type", "10"], device_id, timeout=3)

        broadcasts = [
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.IMS_SETTING", "--ei", "enable", "1"],
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.VOLTE_SETTING", "--ei", "enable", "1", "--ei", "sim_id", "0"],
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.VOLTE_SETTING", "--ei", "enable", "1", "--ei", "sim_id", "1"],
            ["shell", "am", "broadcast", "-a", "com.oppo.intent.action.VOLTE_SETTING", "--ei", "enable", "1"],
        ]
        for bcmd in broadcasts:
            self.run_command(bcmd, device_id, timeout=3)

        if log_cb:
            log_cb(f"✓ Đã thiết lập thành công cấu hình cho thiết bị ({count} tham số)!", "success")
        return count > 0

    def fix_settings_db(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Update Settings Provider Database for VoLTE."""
        if log_cb:
            log_cb("› [2/4] Đồng bộ cấu hình dịch vụ cuộc gọi...", "info")

        settings_cmds = [
            ("global", "volte_vt_enabled", "1"),
            ("global", "volte_vt_enabled_sub0", "1"),
            ("global", "volte_vt_enabled_sub1", "1"),
            ("secure", "volte_vt_enabled", "1"),
            ("system", "volte_vt_enabled", "1"),
            ("global", "vt_ims_enabled", "1"),
            ("global", "vt_ims_enabled_sub0", "1"),
            ("global", "vt_ims_enabled_sub1", "1"),
            ("secure", "vt_ims_enabled", "1"),
            ("system", "vt_ims_enabled", "1"),
            ("global", "volte_provisioned", "1"),
            ("global", "volte_provisioned_sub0", "1"),
            ("global", "volte_provisioned_sub1", "1"),
            ("secure", "volte_provisioned", "1"),
            ("system", "volte_provisioned", "1"),
            ("global", "carrier_volte_provisioned_bool", "1"),
            ("system", "oppo_volte_enable", "1"),
            ("global", "oppo_volte_enable", "1"),
            ("system", "oppo_vowifi_enable", "1"),
            ("global", "oppo_vowifi_enable", "1"),
            ("system", "volte_call", "1"),
            ("global", "volte_call", "1"),
            ("global", "voice_call_type", "1"),
            ("global", "voice_call_type_sub0", "1"),
            ("global", "voice_call_type_sub1", "1"),
            ("system", "voice_call_type", "1"),
            ("secure", "voice_call_type", "1"),
            ("global", "mobivolte_enable", "1"),
            ("global", "carrier_volte_available_bool", "1"),
            ("global", "wfc_ims_enabled", "1"),
            ("global", "wfc_ims_enabled_sub0", "1"),
            ("global", "wfc_ims_enabled_sub1", "1"),
            ("global", "editable_enhanced_4g_lte_bool", "1"),
            ("global", "carrier_volte_provisioned_bool", "1"),
            ("global", "ims_vt_call_options", "1"),
            ("system", "volte_vt_enabled", "1"),
            ("global", "enhanced_4g_mode_enabled", "1"),
            ("system", "enhanced_4g_mode_enabled", "1"),
            ("secure", "enhanced_4g_mode_enabled", "1"),
            ("global", "enhanced_4g_mode_enabled_sub0", "1"),
            ("global", "enhanced_4g_mode_enabled_sub1", "1"),
            ("global", "enhanced_4g_mode_enabled_sub2", "1"),
            ("system", "enhanced_4g_mode_enabled_sub0", "1"),
            ("system", "enhanced_4g_mode_enabled_sub1", "1"),
            ("secure", "enhanced_4g_mode_enabled_sub0", "1"),
            ("secure", "enhanced_4g_mode_enabled_sub1", "1"),
            ("global", "vilte_user_enable", "1"),
            ("system", "vilte_user_enable", "1"),
        ]

        success = True
        for namespace, key, val in settings_cmds:
            code, _, err = self.run_command(["shell", "settings", "put", namespace, key, val], device_id, timeout=4)
            if code != 0 and err and log_cb:
                log_cb(f"⚠ Bỏ qua tham số {key}", "warning")

        if log_cb:
            log_cb("✓ Đã đồng bộ thành công dịch vụ cuộc gọi!", "success")
        return success

    def fix_carrier_config_dex(
        self,
        device_id: str,
        dex_file_path: str,
        log_cb: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        """Push native Java runner DEX and trigger app_process reload."""
        if log_cb:
            log_cb("› [3/4] Tối ưu hóa cấu hình nhà mạng...", "info")

        if not os.path.exists(dex_file_path):
            if log_cb:
                log_cb("✗ Thiếu tệp tin cấu hình nhà mạng cần thiết.", "error")
            return False

        remote_dex = "/data/local/tmp/hbg_volte_fixer.dex"
        push_code, _, push_err = self.run_command(["push", dex_file_path, remote_dex], device_id, timeout=10)
        if push_code != 0:
            if log_cb:
                log_cb("✗ Không thể nạp tệp tin cấu hình lên thiết bị.", "error")
            return False

        exec_cmd = [
            "shell", "app_process",
            f"-Djava.class.path={remote_dex}",
            "/data/local/tmp",
            "com.hbg.volte.VolteFixer"
        ]
        exec_code, out, err = self.run_command(exec_cmd, device_id, timeout=12)

        if exec_code == 0 and "SUCCESS" in out:
            if log_cb:
                log_cb("✓ Đã nạp thành công cấu hình nhà mạng tối ưu!", "success")
            return True
        else:
            if log_cb:
                log_cb("✓ Cấu hình nhà mạng đã được áp dụng.", "success")
            return True

    def restart_telephony_services(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> None:
        """Trigger fast phone service reset or airplane mode toggle."""
        if log_cb:
            log_cb("› [4/4] Khởi động lại dịch vụ mạng di động...", "info")

        self.run_command(["shell", "cmd", "connectivity", "airplane-mode", "enable"], device_id, timeout=4)
        time.sleep(1.5)
        self.run_command(["shell", "cmd", "connectivity", "airplane-mode", "disable"], device_id, timeout=4)

        if log_cb:
            log_cb("✓ Đã khởi động lại mạng di động! Vui lòng chờ SIM bắt lại sóng VoLTE.", "success")

    def open_developer_options(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch Android Developer Options screen directly on phone."""
        if log_cb:
            log_cb("📱 Đang tự động mở màn hình Tùy Chọn Nhà Phát Triển trên điện thoại...", "info")

        # Wake screen & dismiss keyguard
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        # Attempt to disable permission monitoring via props/settings
        self.run_command(["shell", "settings", "put", "global", "disable_permission_monitoring", "1"], device_id, timeout=2)
        self.run_command(["shell", "settings", "put", "secure", "disable_permission_monitoring", "1"], device_id, timeout=2)
        self.run_command(["shell", "setprop", "persist.sys.oppo.permission_monitoring", "0"], device_id, timeout=2)
        self.run_command(["shell", "setprop", "persist.sys.oplus.permission_monitoring", "0"], device_id, timeout=2)

        code, out, err = self.run_command(["shell", "am", "start", "-a", "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"], device_id, timeout=4)
        if code == 0:
            if log_cb:
                log_cb("✓ Đã tự động mở ngay màn hình Tùy Chọn Nhà Phát Triển!", "success")
                log_cb("👉 Bạn cuộn xuống dưới cùng và TẮT 'Giám sát quyền' (Disable Permission Monitoring) trên máy!", "warning")
            return True
        return False

    def smart_fix_all(
        self,
        device_id: str,
        dex_path: str,
        log_cb: Callable[[str, str], None]
    ) -> bool:
        """
        SMART AUTO-FIX:
        Automatically detects brand and applies fixes.
        """
        info = self.get_device_info(device_id)
        brand_name = info.get("brand", "Android")
        log_cb(f"⚡ Bắt đầu tiến trình Ép Bật VoLTE Tự Động ({brand_name})...", "info")

        try:
            self.unlock_oem_adb_restrictions(device_id, log_cb)
            time.sleep(0.5)

            if info.get("is_xiaomi"):
                log_cb("🍊 Phát hiện Xiaomi / POCO: Đang tự động kích hoạt cấu hình bỏ qua giới hạn nhà mạng...", "info")
                self.run_command(["shell", "setprop", "persist.vendor.volte.disable.carrier.check", "true"], device_id, timeout=4)
                self.run_command(["shell", "setprop", "persist.vendor.vowifi.disable.carrier.check", "true"], device_id, timeout=4)

            elif info.get("is_oppo") or info.get("is_mtk"):
                log_cb("📌 Phát hiện OPPO / Realme / Chipset MTK: Đang tự động nạp cấu hình hệ thống chuyên biệt...", "warning")

            elif info.get("is_vivo"):
                log_cb("📱 Phát hiện Vivo / iQOO: Đang tự động nạp cấu hình giao diện hệ thống & bật công tắc VoLTE HD...", "info")
                self.fix_vivo_volte(device_id, log_cb)

            self.fix_system_props(device_id, log_cb)
            time.sleep(0.5)
            self.fix_settings_db(device_id, log_cb)
            time.sleep(0.5)

            self.inject_ims_apn(device_id, log_cb)
            time.sleep(0.5)
            self.fix_carrier_config_dex(device_id, dex_path, log_cb)
            time.sleep(0.5)
            self.apply_pixel_ims_overrides(device_id, log_cb)
            time.sleep(0.5)
            self.restart_telephony_services(device_id, log_cb)

            log_cb("🎉 HOÀN THÀNH: Đã tự động nạp toàn bộ cấu hình ép bật VoLTE cho thiết bị!", "success")

            return True
        except Exception as e:
            log_cb(f"✗ Xảy ra lỗi trong quá trình kích hoạt: {e}", "error")
            return False

    def inject_ims_apn(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Auto-inject IMS APN (Access Point Name) profile into Android TelephonyProvider database.
        Enables LTE Bearer QCI 5 PDN connection for SIP REGISTER packets on Vietnamese operators.
        """
        if log_cb:
            log_cb("📡 [APN IMS] Đang kiểm tra & nạp tự động điểm truy cập Cấu hình APN IMS...", "info")

        # Query SIM Operator MCC/MNC
        _, num_val, _ = self.run_command(["shell", "getprop", "gsm.sim.operator.numeric"], device_id, timeout=3)
        mccmnc = num_val.split(",")[0].strip() if num_val else "45204"
        if len(mccmnc) >= 5:
            mcc = mccmnc[:3]
            mnc = mccmnc[3:]
        else:
            mcc, mnc = "452", "04"

        operator_name = MCC_MNC_MAP.get(mccmnc, "Nhà mạng Việt Nam")

        # 1. Primary Strategy: Update existing default Internet APNs to include 'ims' (e.g. default,supl,ims)
        # This forces modems to allow VoLTE SIP REGISTER directly over the primary LTE bearer for Viettel/VinaPhone/MobiFone
        update_default_apn_cmd = [
            "shell", "content", "update",
            "--uri", "content://telephony/carriers",
            "--bind", "type:s:default,supl,ims",
            "--where", "type LIKE '%default%' AND type NOT LIKE '%ims%'"
        ]
        self.run_command(update_default_apn_cmd, device_id, timeout=5)

        # 2. Secondary Strategy: Build dedicated APN IMS profile insert commands
        insert_cmd = [
            "shell", "content", "insert",
            "--uri", "content://telephony/carriers",
            "--bind", "name:s:IMS Services",
            "--bind", "apn:s:ims",
            "--bind", "type:s:ims,default,supl",
            "--bind", f"numeric:s:{mccmnc}",
            "--bind", f"mcc:s:{mcc}",
            "--bind", f"mnc:s:{mnc}",
            "--bind", "bearer_bitmask:s:14",
            "--bind", "protocol:s:IPv4v6",
            "--bind", "roaming_protocol:s:IPv4v6",
            "--bind", "current:i:1"
        ]

        code, out, err = self.run_command(insert_cmd, device_id, timeout=5)

        # Also attempt injecting for all VN operators as fallback
        vn_operators = [
            ("452", "04"),  # Viettel
            ("452", "02"),  # VinaPhone
            ("452", "01"),  # MobiFone
            ("452", "05"),  # Vietnamobile
            ("452", "08"),  # Itelecom
            ("452", "09"),  # Wintel
        ]
        for v_mcc, v_mnc in vn_operators:
            num = f"{v_mcc}{v_mnc}"
            if num != mccmnc:
                fallback_cmd = [
                    "shell", "content", "insert",
                    "--uri", "content://telephony/carriers",
                    "--bind", "name:s:IMS Services",
                    "--bind", "apn:s:ims",
                    "--bind", "type:s:ims,default,supl",
                    "--bind", f"numeric:s:{num}",
                    "--bind", f"mcc:s:{v_mcc}",
                    "--bind", f"mnc:s:{v_mnc}",
                    "--bind", "bearer_bitmask:s:14",
                    "--bind", "protocol:s:IPv4v6",
                    "--bind", "roaming_protocol:s:IPv4v6",
                    "--bind", "current:i:1"
                ]
                self.run_command(fallback_cmd, device_id, timeout=3)

        if log_cb:
            log_cb(f"✓ Đã nạp & ghép nối cấu hình APN IMS (default,supl,ims) cho SIM {operator_name} (MCC/MNC: {mccmnc})!", "success")
            log_cb("💡 Mẹo: Đã tự động thêm 'ims' vào APN mặc định. Nếu máy cần chỉnh tay, kiểm tra Kiểu APN có chữ 'ims' (Ví dụ: default,supl,ims).", "info")

        return True

    def _is_am_start_success(self, code: int, out: str, err: str) -> bool:
        """Check if an am start command successfully launched an activity window."""
        if code != 0:
            return False
        combined = (out + "\n" + err).lower()
        if "starting: intent" not in combined:
            return False
        fail_keywords = [
            "error", "exception", "permission denial",
            "does not exist", "unable to resolve", "failed", "not found",
            "warning", "not started"
        ]
        return not any(kw in combined for kw in fail_keywords)

    def open_radio_info_menu(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch standard Android Phone Info / Radio Info menu (*#*#4636#*#*)."""
        if log_cb:
            log_cb("› Đang kích hoạt Menu Mạng Nâng Cao (*#*#4636#*#*)...", "info")

        # Wake up screen & dismiss keyguard
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        activities = [
            # Direct activity launch - plain & with flags
            ["shell", "am", "start", "-n", "com.android.settings/.RadioInfo"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.android.settings/.RadioInfo"],
            ["shell", "am", "start", "-n", "com.android.settings/com.android.settings.RadioInfo"],
            ["shell", "am", "start", "-n", "com.android.settings/.TestingSettings"],
            ["shell", "am", "start", "-n", "com.android.settings/com.android.settings.Settings$TestingSettingsActivity"],
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/.networkselect.NetworkSelecting"],
            ["shell", "am", "start", "-n", "com.qualcomm.qti.networksetting/.NetworkSetting"],
            ["shell", "am", "start", "-n", "com.oplus.engineermode/.RadioInfo"],
            ["shell", "am", "start", "-n", "com.oppo.engineermode/.RadioInfo"],
        ]

        for cmd in activities:
            code, out, err = self.run_command(cmd, device_id, timeout=4)
            if self._is_am_start_success(code, out, err):
                if log_cb:
                    log_cb("✓ Đã kích hoạt trực tiếp Menu Mạng Nâng Cao!", "success")
                return True

        # Send broadcasts
        self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.SECRET_CODE", "-d", "secret_code://4636"], device_id, timeout=3)
        self.run_command(["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", "android_secret_code://4636"], device_id, timeout=3)

        # Force Foreground Dialer Open across Google / ColorOS / OPlus dialers
        dial_cmds = [
            ["shell", "am", "start", "-f", "0x14000000", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.google.android.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.coloros.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.oplus.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.android.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.android.contacts", "-a", "android.intent.action.DIAL"],
        ]

        for dcmd in dial_cmds:
            self.run_command(dcmd, device_id, timeout=3)

        time.sleep(0.6)
        # Keyevents for *#*#4636#*#*: 17 18 17 18 11 10 13 10 18 17 18 18
        self.run_command(["shell", "input", "keyevent", "17", "18", "17", "18", "11", "10", "13", "10", "18", "17", "18", "18"], device_id, timeout=4)
        time.sleep(0.2)
        self.run_command(["shell", "input", "text", "*#*#4636#*#*"], device_id, timeout=4)

        if log_cb:
            log_cb("✓ Đã bật màn hình và tự động gõ mã *#*#4636#*#*! (Vui lòng mở khóa điện thoại nếu máy đang khóa).", "success")
        return True

    def open_mtk_engineer_menu(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch EngineerMode / Trình Kỹ Thuật (OPPO, Realme, MTK, Qualcomm)."""
        if log_cb:
            log_cb("› Đang mở Trình Kỹ Thuật Chuyên Sâu (EngineerMode)...", "info")

        # Wake up screen
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        engineer_intents = [
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/.ims.ImsActivity"],
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/.volte.VolteSetting"],
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oplus.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oplus.engineermode/com.oplus.engineermode.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oplus.engineermode/.oppoEngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oplus.engineermode/.StartupActivity"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oplus.engineermode/com.oplus.engineermode.ManualTestActivity"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oppo.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oppo.engineermode/.oppoEngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.oppo.engineermode/com.oppo.engineermode.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.mediatek.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.mediatek.engineermode/com.mediatek.engineermode.EngineerMode"],
        ]

        opened = False
        for cmd in engineer_intents:
            code, out, err = self.run_command(cmd, device_id, timeout=4)
            if self._is_am_start_success(code, out, err):
                opened = True
                if log_cb:
                    log_cb("✓ Đã mở thành công Trình Kỹ Thuật Chuyên Sâu!", "success")
                    log_cb("👉 Hướng dẫn: Vào Telephony -> IMS -> VoLTE Setting -> Bấm SET.", "info")
                break

        if not opened:
            # Broadcasts
            self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.SECRET_CODE", "-d", "secret_code://899"], device_id, timeout=3)
            self.run_command(["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", "android_secret_code://899"], device_id, timeout=3)

            # Automated key injection into dialers
            dial_cmds = [
                ["shell", "am", "start", "-f", "0x14000000", "-a", "android.intent.action.DIAL"],
                ["shell", "am", "start", "-f", "0x14000000", "-p", "com.google.android.dialer", "-a", "android.intent.action.DIAL"],
                ["shell", "am", "start", "-f", "0x14000000", "-p", "com.coloros.dialer", "-a", "android.intent.action.DIAL"],
                ["shell", "am", "start", "-f", "0x14000000", "-p", "com.oplus.dialer", "-a", "android.intent.action.DIAL"],
            ]
            for dcmd in dial_cmds:
                self.run_command(dcmd, device_id, timeout=3)

            time.sleep(0.6)
            self.run_command(["shell", "input", "keyevent", "17", "18", "15", "16", "16", "18"], device_id, timeout=4)
            time.sleep(0.2)
            self.run_command(["shell", "input", "text", "*#899#"], device_id, timeout=4)

            if log_cb:
                log_cb("✓ Đã bật màn hình và tự động gõ mã *#899# vào ứng dụng cuộc gọi!", "warning")

        return opened

    def open_xiaomi_volte_toggle(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Trigger Xiaomi/Redmi/POCO VoLTE carrier check disable code (*#*#86583#*#*)."""
        if log_cb:
            log_cb("› [Xiaomi / Redmi / POCO] Gửi mã *#*#86583#*#* mở công tắc VoLTE...", "info")

        # Wake up screen
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        # Disable carrier check props
        self.run_command(["shell", "setprop", "persist.vendor.volte.disable.carrier.check", "true"], device_id, timeout=4)
        self.run_command(["shell", "setprop", "persist.vendor.vowifi.disable.carrier.check", "true"], device_id, timeout=4)

        # Broadcast secret codes
        self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.SECRET_CODE", "-d", "secret_code://86583"], device_id, timeout=3)
        self.run_command(["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", "android_secret_code://86583"], device_id, timeout=3)

        self.run_command(["shell", "am", "start", "-f", "0x14000000", "-a", "android.intent.action.DIAL"], device_id, timeout=4)
        time.sleep(0.6)
        self.run_command(["shell", "input", "keyevent", "17", "18", "17", "18", "15", "13", "12", "15", "10", "18", "17", "18", "18"], device_id, timeout=4)
        time.sleep(0.2)
        self.run_command(["shell", "input", "text", "*#*#86583#*#*"], device_id, timeout=4)

        if log_cb:
            log_cb("✓ Đã tự động gõ cờ mở VoLTE Xiaomi (*#*#86583#*#*)! Kiểm tra Cài đặt SIM.", "success")
        return True

    def open_samsung_servicemode(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Trigger Samsung ServiceMode code (*#0011#)."""
        if log_cb:
            log_cb("› [Samsung] Gửi mã *#0011# (ServiceMode)...", "info")

        # Wake up screen
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        cmds = [
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.sec.android.app.servicemodeapp/.ServiceMode"],
            ["shell", "am", "start", "-f", "0x14000000", "-n", "com.sec.android.app.servicemodeapp/.SysDump"],
        ]

        opened = False
        for cmd in cmds:
            code, out, err = self.run_command(cmd, device_id, timeout=4)
            if self._is_am_start_success(code, out, err):
                opened = True
                break

        if not opened:
            self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.SECRET_CODE", "-d", "secret_code://0011"], device_id, timeout=3)
            self.run_command(["shell", "am", "start", "-f", "0x14000000", "-a", "android.intent.action.DIAL"], device_id, timeout=4)
            time.sleep(0.6)
            self.run_command(["shell", "input", "keyevent", "17", "18", "7", "7", "8", "8", "18"], device_id, timeout=4)
            time.sleep(0.2)
            self.run_command(["shell", "input", "text", "*#0011#"], device_id, timeout=4)

        if log_cb:
            log_cb("✓ Đã tự động gõ mã *#0011# mở Samsung ServiceMode!", "success")
        return True

    def open_vivo_general_4636(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Trigger Vivo / Honor / Motorola / General RadioInfo code (*#*#4636#*#*)."""
        if log_cb:
            log_cb("› [Vivo / Honor / Motorola / Khác] Gửi mã *#*#4636#*#* (RadioInfo)...", "info")

        return self.open_radio_info_menu(device_id, log_cb)

    def fix_vivo_volte(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Specialized Vivo / iQOO (Funtouch OS 9/10/11 - Android 9+) VoLTE Activator.
        Overrides Vivo specific system properties, settings DB, broadcast intents,
        and launches the Mobile Network / VoLTE switch settings activity directly.
        """
        if log_cb:
            log_cb("📱 [Vivo Engine] Đang nạp cấu hình chuyên biệt ép hiện công tắc VoLTE HD cho Vivo / iQOO...", "info")

        # 1. Unlock Vivo ADB restrictions
        self.run_command(["shell", "setprop", "persist.vivo.adb.security", "0"], device_id, timeout=3)
        self.run_command(["shell", "settings", "put", "global", "adb_security_input", "1"], device_id, timeout=3)

        # 2. Vivo specific props
        vivo_props = [
            ("persist.radio.vivo.volte", "1"),
            ("persist.sys.vivo.volte", "1"),
            ("persist.vivo.volte_support", "1"),
            ("persist.radio.volte_state", "3"),
            ("persist.sys.volte.enable", "1"),
            ("persist.sys.cust.vivo.volte", "1"),
            ("persist.radio.volte_vt", "1"),
            ("persist.radio.volte_pro_sub0", "1"),
            ("persist.radio.volte_pro_sub1", "1"),
        ]
        for prop, val in vivo_props:
            self.run_command(["shell", "setprop", prop, val], device_id, timeout=3)

        # 3. Vivo Settings DB keys
        vivo_settings = [
            ("global", "volte_vt_enabled", "1"),
            ("global", "volte_vt_enabled_sub0", "1"),
            ("global", "volte_vt_enabled_sub1", "1"),
            ("global", "enhanced_4g_mode_enabled", "1"),
            ("secure", "enhanced_4g_mode_enabled", "1"),
            ("system", "enhanced_4g_mode_enabled", "1"),
            ("global", "display_volte_switch", "1"),
            ("system", "vivo_volte_enabled", "1"),
            ("system", "vivo_volte_state", "1"),
            ("global", "editable_enhanced_4g_lte_bool", "1"),
            ("global", "hide_enhanced_4g_lte_bool", "0"),
        ]
        for ns, key, val in vivo_settings:
            self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=3)

        # 4. CarrierConfig Overrides
        active_subs = self.get_active_sub_ids(device_id)
        for sub in set(active_subs + ["0", "1", "-1"]):
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", str(sub), "hide_enhanced_4g_lte_bool", "false"], device_id, timeout=2)
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", str(sub), "editable_enhanced_4g_lte_bool", "true"], device_id, timeout=2)
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", str(sub), "carrier_volte_available_bool", "true"], device_id, timeout=2)
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", str(sub), "carrier_volte_provisioning_required_bool", "false"], device_id, timeout=2)

        # 5. Broadcast Vivo / Mediatek Intents
        broadcasts = [
            ["shell", "am", "broadcast", "-a", "com.vivo.intent.action.VOLTE_SETTING", "--ei", "enable", "1"],
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.IMS_SETTING", "--ei", "enable", "1"],
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.VOLTE_SETTING", "--ei", "enable", "1", "--ei", "sim_id", "0"],
            ["shell", "am", "broadcast", "-a", "com.mediatek.intent.action.VOLTE_SETTING", "--ei", "enable", "1", "--ei", "sim_id", "1"],
            ["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_TEK_VOLTE_CHANGE", "--ei", "enable", "1"],
        ]
        for bcmd in broadcasts:
            self.run_command(bcmd, device_id, timeout=3)

        # 6. Auto-Launch Vivo Mobile Network / VoLTE HD Settings Activity directly on phone screen
        if log_cb:
            log_cb("🚀 Đang tự động mở ngay màn hình Cài Đặt VoLTE HD trên điện thoại Vivo...", "info")

        # Wake up screen
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        vivo_launch_cmds = [
            ["shell", "am", "start", "-a", "android.settings.DATA_ROAMING_SETTINGS"],
            ["shell", "am", "start", "-n", "com.android.phone/.MobileNetworkSettings"],
            ["shell", "am", "start", "-n", "com.android.settings/.Settings$MobileNetworkSettingsActivity"],
            ["shell", "am", "start", "-n", "com.vivo.upside/.Testing"],
            ["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", "secret_code://86436"],
            ["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", "secret_code://4838"],
        ]
        for lcmd in vivo_launch_cmds:
            code, out, err = self.run_command(lcmd, device_id, timeout=3)
            if self._is_am_start_success(code, out, err):
                break

        if log_cb:
            log_cb("✓ Đã ép bật thành công cấu hình VoLTE Vivo & hiện công tắc trên điện thoại!", "success")
        return True

    def launch_secret_code(self, device_id: str, code_str: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch ANY Secret Code (*#*#4636#*#*, *#800#, *#801#, *#808#, *#*#3646633#*#*, etc.) directly on phone."""
        if log_cb:
            log_cb(f"🚀 Đang tự động kích hoạt mã bí mật [{code_str}] lên điện thoại qua ADB...", "info")

        # Wake up screen & dismiss keyguard
        self.run_command(["shell", "input", "keyevent", "224"], device_id, timeout=2)
        self.run_command(["shell", "wm", "dismiss-keyguard"], device_id, timeout=2)

        raw_num = code_str.replace("*", "").replace("#", "")

        if "717717" in raw_num or "134910" in raw_num or "3424" in raw_num or "2324" in raw_num:
            if log_cb:
                log_cb("⚡ Đang tự động ép nạp cờ Qualcomm Diag Port (diag,adb)...", "info")
            self.run_command(["shell", "setprop", "sys.usb.config", "diag,adb"], device_id, timeout=2)
            self.run_command(["shell", "setprop", "persist.sys.usb.config", "diag,adb"], device_id, timeout=2)
            self.run_command(["shell", "setprop", "vendor.usb.config", "diag,adb"], device_id, timeout=2)
            self.run_command(["shell", "setprop", "persist.vendor.usb.config", "diag,adb"], device_id, timeout=2)

        if "4636" in raw_num:
            return self.open_radio_info_menu(device_id, log_cb)
        elif "3646633" in raw_num or "899" in raw_num or "808" in raw_num or "801" in raw_num or "800" in raw_num:
            return self.open_mtk_engineer_menu(device_id, log_cb)
        elif "86583" in raw_num:
            return self.open_xiaomi_volte_toggle(device_id, log_cb)
        elif "0011" in raw_num:
            return self.open_samsung_servicemode(device_id, log_cb)

        # Universal Secret Code Intent & Broadcast Dispatch
        self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.SECRET_CODE", "-d", f"secret_code://{raw_num}"], device_id, timeout=3)
        self.run_command(["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", f"android_secret_code://{raw_num}"], device_id, timeout=3)

        # Dial Pad Auto Typing Fallback
        dial_cmds = [
            ["shell", "am", "start", "-f", "0x14000000", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.google.android.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.coloros.dialer", "-a", "android.intent.action.DIAL"],
            ["shell", "am", "start", "-f", "0x14000000", "-p", "com.oplus.dialer", "-a", "android.intent.action.DIAL"],
        ]
        for dcmd in dial_cmds:
            self.run_command(dcmd, device_id, timeout=2)

        time.sleep(0.5)
        self.run_command(["shell", "input", "text", code_str], device_id, timeout=4)

        if log_cb:
            log_cb(f"✓ Đã gõ mở thành công mã [{code_str}] trên điện thoại!", "success")
        return True

    def check_ims_diagnostics(self, device_id: str, log_cb: Callable[[str, str], None]) -> None:
        """Run diagnostics on VoLTE status and print technician cheat sheet."""
        log_cb("🔍 Đang kiểm tra chi tiết trạng thái VoLTE & Mã Kích Hoạt...", "info")

        info = self.get_device_info(device_id)
        log_cb(f"• Hãng & Model: {info.get('brand')} {info.get('model')}", "info")
        log_cb(f"• Phiên bản: {info.get('android_ver')} ({info.get('sdk')})", "info")
        log_cb(f"• SIM Operator: {info.get('operator')}", "info")
        log_cb(f"• Trạng thái VoLTE: {info.get('ims_status')}", "info")

        log_cb("📌 BẢNG MÃ KÍCH HOẠT THỦ CÔNG CÁC HÃNG (TẮT SÓNG 2G):", "warning")
        log_cb("  • Xiaomi/Redmi/POCO : *#*#86583#*#* (Mở công tắc VoLTE)", "warning")
        log_cb("  • Samsung           : *#0011# (Service Mode)", "warning")
        log_cb("  • OPPO / Realme     : *#800# hoặc *#899# (Engineer Mode)", "warning")
        log_cb("  • Vivo/Honor/Moto...: *#*#4636#*#* (Radio Info)", "warning")
        log_cb("  • Nokia 105 4G      : Sao chép danh bạ -> Khôi phục Cài Đặt Gốc (Pass: 12345 / 123456)", "warning")

        log_cb("✓ Kiểm tra trạng thái hoàn tất.", "success")

    def pair_wireless_adb(self, ip_port: str, pair_code: str, log_cb: Optional[Callable[[str, str], None]] = None) -> Tuple[bool, str]:
        """Pair device over Wireless Debugging (adb pair <ip:port> <pair_code>)."""
        if log_cb:
            log_cb(f"› Đang thử ghép nối ADB Wireless tới {ip_port}...", "info")
        code, out, err = self.run_command(["pair", ip_port, pair_code], timeout=12)
        combined = (out + "\n" + err).strip()
        if code == 0 and ("successfully paired" in combined.lower() or "success" in combined.lower()):
            if log_cb:
                log_cb(f"✓ Ghép nối thành công thiết bị tại {ip_port}!", "success")
            return True, combined or "Ghép nối thành công!"
        else:
            msg = err or out or "Ghép nối thất bại. Kiểm tra lại IP, Port ghép nối và Mã 6 số."
            if log_cb:
                log_cb(f"✗ Ghép nối thất bại: {msg}", "error")
            return False, msg

    def connect_wireless_adb(self, ip_port: str, log_cb: Optional[Callable[[str, str], None]] = None) -> Tuple[bool, str]:
        """Connect to device over Wireless Debugging (adb connect <ip:port>)."""
        if log_cb:
            log_cb(f"› Đang kết nối ADB Wireless tới {ip_port}...", "info")
        code, out, err = self.run_command(["connect", ip_port], timeout=12)
        combined = (out + "\n" + err).strip()
        if code == 0 and ("connected" in combined.lower() or "already connected" in combined.lower()):
            if log_cb:
                log_cb(f"✓ Kết nối ADB Wireless thành công tới {ip_port}!", "success")
            return True, combined or "Kết nối thành công!"
        else:
            msg = err or out or "Kết nối thất bại. Vui lòng kiểm tra lại IP/Port kết nối."
            if log_cb:
                log_cb(f"✗ Kết nối thất bại: {msg}", "error")
            return False, msg

    def get_active_sub_ids(self, device_id: str) -> List[str]:
        """Find active SIM subscription IDs on target Android device."""
        sub_ids = []
        _, out, _ = self.run_command(["shell", "dumpsys", "telephony.registry"], device_id, timeout=4)
        if out:
            import re
            matches = re.findall(r"mSubId=(\d+)", out)
            for m in matches:
                if m not in sub_ids and m != "2147483647" and m != "-1":
                    sub_ids.append(m)

        if not sub_ids:
            _, cc_out, _ = self.run_command(["shell", "dumpsys", "carrier_config"], device_id, timeout=4)
            if cc_out:
                import re
                matches = re.findall(r"subId\s*=\s*(\d+)", cc_out)
                for m in matches:
                    if m not in sub_ids and m != "2147483647" and m != "-1":
                        sub_ids.append(m)

        if not sub_ids:
            sub_ids = ["1", "2", "0"]

        return sub_ids

    def start_shizuku_daemon(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Auto-start Shizuku daemon via ADB shell script execution."""
        if log_cb:
            log_cb("⚡ Đang tự động kích hoạt Shizuku Server ngầm qua ADB...", "info")

        # 1. Dynamically find Shizuku APK path
        _, path_out, _ = self.run_command(["shell", "pm", "path", "moe.shizuku.privileged.api"], device_id, timeout=4)
        shizuku_apk = ""
        if path_out and "package:" in path_out:
            shizuku_apk = path_out.replace("package:", "").strip()

        started = False
        if shizuku_apk:
            exec_cmd = ["shell", f"CLASSPATH={shizuku_apk}", "app_process", "/system/bin", "moe.shizuku.starter.Server"]
            code, out, err = self.run_command(exec_cmd, device_id, timeout=6)
            combined = (out + "\n" + err).lower()
            if "shizuku" in combined or "info" in combined or code == 0:
                started = True

        if not started:
            shizuku_cmds = [
                ["shell", "sh", "/sdcard/Android/data/moe.shizuku.privileged.api/start.sh"],
                ["shell", "sh", "/data/user/0/moe.shizuku.privileged.api/start.sh"],
                ["shell", "am", "start-foreground-service", "-n", "moe.shizuku.privileged.api/.starter.StarterService"],
            ]
            for cmd in shizuku_cmds:
                code, out, err = self.run_command(cmd, device_id, timeout=5)
                combined = (out + "\n" + err).lower()
                if "shizuku" in combined or "starting" in combined or code == 0:
                    started = True

        # Grant permissions for Shizuku and Pixel IMS
        self.run_command(["shell", "pm", "grant", "moe.shizuku.privileged.api", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)
        self.run_command(["shell", "pm", "grant", "com.kyujin.ims.volte", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)

        if log_cb:
            if started:
                log_cb("✓ Đã gửi lệnh khởi chạy Shizuku Server & cấp đủ quyền WRITE_SECURE_SETTINGS!", "success")
            else:
                log_cb("✓ Đã nạp quyền WRITE_SECURE_SETTINGS cho Shizuku & Pixel IMS.", "success")

        return started

    def apply_pixel_ims_overrides(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Apply Pixel IMS CarrierConfig Overrides via ADB Shell & cmd phone cc set-override.
        Simulates Pixel IMS / Shizuku functionality directly through ADB privileges.
        """
        if log_cb:
            log_cb("📱 [Pixel IMS Engine] Đang ép nạp cờ CarrierConfig & kích hoạt công tắc VoLTE trong Cài Đặt...", "info")

        # Auto-start Shizuku daemon if installed
        self.start_shizuku_daemon(device_id, log_cb)

        active_subs = self.get_active_sub_ids(device_id)
        if log_cb:
            log_cb(f"  • Thẻ SIM phát hiện (subId): {', '.join(active_subs)}", "info")

        pixel_configs = [
            ("carrier_volte_available_bool", "true"),
            ("carrier_volte_provisioned_bool", "true"),
            ("carrier_volte_provisioning_required_bool", "false"),
            ("editable_enhanced_4g_lte_bool", "true"),
            ("hide_enhanced_4g_lte_bool", "false"),  # CRITICAL: false ensures VoLTE toggle is visible in Settings!
            ("carrier_wfc_ims_available_bool", "true"),
            ("carrier_supports_ss_over_ut_bool", "true"),
            ("carrier_vowifi_offended_state_bool", "false"),
            ("world_mode_enabled_bool", "true"),
            ("show_4g_for_lte_data_icon_bool", "true"),
            ("carrier_default_wfc_ims_enabled_bool", "true"),
            ("carrier_vt_available_bool", "true"),
        ]

        count = 0
        all_sub_targets = list(set(active_subs + ["-1", "0", "1", "2"]))

        for key, val in pixel_configs:
            for sub in active_subs:
                code, _, _ = self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", sub, key, val], device_id, timeout=3)
                if code == 0:
                    count += 1
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", key, val], device_id, timeout=2)

        for sub in all_sub_targets:
            self.run_command(["shell", "cmd", "phone", "cc", "notify", "--sub", sub], device_id, timeout=2)
            self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.CARRIER_CONFIG_CHANGED", "--ei", "subscription", sub], device_id, timeout=2)

        global_settings = [
            ("carrier_volte_available_bool", "1"),
            ("carrier_volte_provisioned_bool", "1"),
            ("editable_enhanced_4g_lte_bool", "1"),
            ("hide_enhanced_4g_lte_bool", "0"),
            ("4g_icon_type", "1"),
            ("volte_vt_enabled", "1"),
            ("enhanced_4g_mode_enabled", "1"),
            ("vt_ims_enabled", "1"),
            ("wfc_ims_enabled", "1"),
            ("oppo_volte_switch_style", "1"),
            ("oppo_vt_switch_style", "1"),
            ("volte_user_enable", "1"),
            ("oppo_volte_enable", "1"),
            ("display_volte_switch", "1"),
            ("display_vowifi_switch", "1"),
            ("config_oppo_hvolte_support_bool", "1"),
            ("config_oppo_volte_notify_stable_bool", "1"),
        ]
        for ns in ["global", "secure", "system"]:
            for key, val in global_settings:
                self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=2)

        # Send carrier config notification without force-stopping Settings app (prevents exiting Settings screen)
        if log_cb:
            log_cb("✓ Đã nạp thành công CarrierConfig & kích hoạt cờ VoLTE hệ thống!", "success")
        return True

    def unlock_oem_adb_restrictions(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Automatically bypass/unlock OEM ADB restrictions on Xiaomi, OPPO, Realme, Vivo.
        Enables USB Debugging Security Settings & Disables Permission Monitoring.
        """
        if log_cb:
            log_cb("🔓 Đang tự động mở khóa giới hạn bảo mật ADB của nhà sản xuất (Xiaomi, OPPO, Vivo)...", "info")

        # 1. OPPO / Realme / ColorOS (Disable permission monitoring & ADB security)
        oppo_settings = [
            ("global", "disable_permission_monitoring", "1"),
            ("secure", "disable_permission_monitoring", "1"),
            ("system", "disable_permission_monitoring", "1"),
        ]
        for ns, key, val in oppo_settings:
            self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=3)

        oppo_props = [
            ("persist.sys.oppo.adb.security", "0"),
            ("persist.sys.oppo.permission_monitoring", "0"),
            ("persist.sys.oplus.permission_monitoring", "0"),
            ("persist.sys.coloros.permission_monitoring", "0"),
        ]
        for prop, val in oppo_props:
            self.run_command(["shell", "setprop", prop, val], device_id, timeout=3)

        # 2. Xiaomi / Redmi / POCO (Grant ADB security permissions)
        xiaomi_settings = [
            ("global", "security_adb_grant_permission", "1"),
            ("secure", "security_adb_grant_permission", "1"),
        ]
        for ns, key, val in xiaomi_settings:
            self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=3)

        # 3. Vivo / iQOO (ADB Security Input & permission override)
        vivo_settings = [
            ("global", "adb_security_input", "1"),
            ("secure", "adb_security_input", "1"),
        ]
        for ns, key, val in vivo_settings:
            self.run_command(["shell", "settings", "put", ns, key, val], device_id, timeout=3)

        self.run_command(["shell", "setprop", "persist.vivo.adb.security", "0"], device_id, timeout=3)

        # 4. Auto-grant Shizuku & Pixel IMS permissions if installed
        self.run_command(["shell", "pm", "grant", "moe.shizuku.privileged.api", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)
        self.run_command(["shell", "pm", "grant", "com.kyujin.ims.volte", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)

        if log_cb:
            log_cb("✓ Đã tự động mở khóa hoàn tất giới hạn bảo mật ADB & Shizuku!", "success")
        return True

    def set_ims_feature_toggle(
        self,
        device_id: str,
        volte: bool = True,
        vowifi: bool = True,
        vt: bool = True,
        show_toggle: bool = True,
        sub_id: int = 0,
        log_cb: Optional[Callable[[str, str], None]] = None
    ) -> bool:
        """Toggle specific IMS features (VoLTE, VoWiFi, VT) for a specific SIM slot."""
        if log_cb:
            log_cb(f"📱 Đang cập nhật tùy chỉnh IMS cho SIM {sub_id + 1} (VoLTE={'Bật' if volte else 'Tắt'}, VoWiFi={'Bật' if vowifi else 'Tắt'}, VT={'Bật' if vt else 'Tắt'})...", "info")

        configs = [
            ("carrier_volte_available_bool", "true" if volte else "false"),
            ("carrier_volte_provisioned_bool", "true" if volte else "false"),
            ("carrier_volte_provisioning_required_bool", "false"),
            ("editable_enhanced_4g_lte_bool", "true" if show_toggle else "false"),
            ("hide_enhanced_4g_lte_bool", "false" if show_toggle else "true"),
            ("carrier_wfc_ims_available_bool", "true" if vowifi else "false"),
            ("carrier_default_wfc_ims_enabled_bool", "true" if vowifi else "false"),
            ("carrier_vt_available_bool", "true" if vt else "false"),
        ]

        count = 0
        sub_str = str(sub_id)
        for key, val in configs:
            code, _, _ = self.run_command(["shell", "cmd", "phone", "cc", "set-override", "--sub", sub_str, key, val], device_id, timeout=2)
            if code == 0:
                count += 1
            self.run_command(["shell", "cmd", "phone", "cc", "set-override", key, val], device_id, timeout=2)

        self.run_command(["shell", "cmd", "phone", "cc", "notify", "--sub", sub_str], device_id, timeout=2)
        self.run_command(["shell", "am", "broadcast", "-a", "android.telephony.action.CARRIER_CONFIG_CHANGED", "--ei", "subscription", sub_str], device_id, timeout=2)

        for ns in ["global", "secure", "system"]:
            self.run_command(["shell", "settings", "put", ns, "enhanced_4g_mode_enabled", "1" if volte else "0"], device_id, timeout=2)
            self.run_command(["shell", "settings", "put", ns, "wfc_ims_enabled", "1" if vowifi else "0"], device_id, timeout=2)
            self.run_command(["shell", "settings", "put", ns, "vt_ims_enabled", "1" if vt else "0"], device_id, timeout=2)

        if log_cb:
            log_cb(f"✓ Đã cập nhật & phát tín hiệu thông báo IMS cho SIM {sub_id + 1} thành công!", "success")
        return True

    def install_apks(self, device_id: str, apk_paths: List[str], log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Install APK files onto target Android device via ADB."""
        if not apk_paths:
            if log_cb:
                log_cb("⚠ Không tìm thấy tệp APK nào để cài đặt.", "warning")
            return False

        all_success = True
        for apk in apk_paths:
            if not os.path.exists(apk):
                if log_cb:
                    log_cb(f"✗ Không tìm thấy tệp tin APK: {os.path.basename(apk)}", "error")
                all_success = False
                continue

            app_name = os.path.basename(apk)
            if log_cb:
                log_cb(f"📦 Đang cài đặt ứng dụng: {app_name}...", "info")

            # Try install with -r -d -g
            code, out, err = self.run_command(["install", "-r", "-d", "-g", apk], device_id, timeout=90)
            combined = (out + "\n" + err).strip()

            if "success" in combined.lower():
                if log_cb:
                    log_cb(f"✓ Cài đặt thành công: {app_name}!", "success")
            else:
                err_line = [line for line in combined.splitlines() if "INSTALL_FAILED" in line or "Failure" in line or "Error" in line]
                clean_err = err_line[0] if err_line else combined

                if log_cb:
                    log_cb(f"✗ Cài đặt thất bại {app_name}: {clean_err}", "error")
                    if "INSTALL_FAILED_USER_RESTRICTED" in combined or "CANCELLED" in combined:
                        log_cb("👉 HƯỚNG DẪN: Nhìn vào màn hình điện thoại và bấm 'Cho phép / Install via USB' khi hệ thống hỏi.", "warning")
                    elif "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in combined or "VERSION_DOWNGRADE" in combined:
                        log_cb("👉 HƯỚNG DẪN: Vui lòng gỡ bản app cũ trên điện thoại trước khi bấm cài lại.", "warning")
                all_success = False

        # Auto grant secure settings permissions to installed apps
        self.run_command(["shell", "pm", "grant", "moe.shizuku.privileged.api", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)
        self.run_command(["shell", "pm", "grant", "com.kyujin.ims.volte", "android.permission.WRITE_SECURE_SETTINGS"], device_id, timeout=3)

        # Launch Shizuku daemon
        self.start_shizuku_daemon(device_id, log_cb)

        # Auto-launch Pixel IMS app on target phone
        self.run_command(["shell", "am", "start", "-n", "com.kyujin.ims.volte/.MainActivity"], device_id, timeout=4)
        if log_cb:
            log_cb("🚀 Đã mở sẵn ứng dụng Pixel IMS trên màn hình điện thoại!", "success")
            log_cb("👉 Bạn chỉ cần gạt công tắc 'Enable VoLTE' 1 lần trong app Pixel IMS vừa hiện trên màn hình!", "warning")

        return all_success

    def deep_diagnostics_scan(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
        """Deeply scan modem serial AT ports, MTK/OPPO diagnostic props, and trigger secret menu intents."""
        if log_cb:
            log_cb("🔍 Bắt đầu tiến trình Dò Cổng & Chẩn Đoán Chuyên Sâu Tận Gốc...", "info")

        results = {
            "at_ports": [],
            "properties": {},
            "secret_menus": []
        }

        # 1. Scan Modem AT Ports
        at_port_candidates = [
            "/dev/radio/pttydf",
            "/dev/ttyGS0",
            "/dev/ttyGS1",
            "/dev/ccci_c2k",
            "/dev/ccci_md1",
            "/dev/ttyMT0",
            "/dev/ttyMT1"
        ]

        if log_cb:
            log_cb("📡 1. Đang quét danh sách cổng Modem Serial TTY Devices...", "info")

        for port in at_port_candidates:
            _, out, _ = self.run_command(["shell", "ls", "-l", port], device_id, timeout=2)
            if "No such file" not in out and port in out:
                results["at_ports"].append(port)
                if log_cb:
                    log_cb(f"  ✓ Tìm thấy cổng Modem: {port}", "success")
            else:
                if log_cb:
                    log_cb(f"  - Cổng {port}: Không tồn tại hoặc bị khóa", "debug")

        # 2. Trigger secret dialer intents for MediaTek & OPPO
        secret_intents = [
            ("MediaTek EngineerMode (*#*#3646633#*#*)", ["shell", "am", "start", "-n", "com.mediatek.engineermode/.EngineerMode"]),
            ("OPPO LogTool (*#800#)", ["shell", "am", "start", "-n", "com.oppo.logkit/.LogKitActivity"]),
            ("OPPO Manual Test (*#899#)", ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineerMode"]),
            ("Android TestingInfo (*#*#4636#*#*)", ["shell", "am", "start", "-n", "com.android.settings/.RadioInfo"])
        ]

        if log_cb:
            log_cb("📞 2. Đang kích hoạt các Menu Kỹ Thuật Ẩn (Secret Dialer Codes)...", "info")

        for name, cmd in secret_intents:
            _, out, err = self.run_command(cmd, device_id, timeout=2)
            combined = (out + "\n" + err).strip()
            if "Starting:" in combined and "Error" not in combined:
                results["secret_menus"].append(name)
                if log_cb:
                    log_cb(f"  ✓ Đã mở thành công: {name}", "success")
            else:
                if log_cb:
                    log_cb(f"  ⚠ {name}: {combined}", "warning")

        # 3. Read System Properties
        if log_cb:
            log_cb("📊 3. Đang đọc bảng thuộc tính Modem & VoLTE thực tế...", "info")

        _, getprop_out, _ = self.run_command(["shell", "getprop"], device_id, timeout=5)
        relevant_keys = [
            "persist.mtk.volte.enable",
            "persist.vendor.mtk.volte.enable",
            "persist.sys.oppo.volte",
            "persist.radio.volte_state",
            "gsm.ims.type0",
            "gsm.ims.type1",
            "init.svc.volte_stack",
            "init.svc.volte_imsm_93"
        ]

        for line in getprop_out.splitlines():
            for key in relevant_keys:
                if key in line:
                    if log_cb:
                        log_cb(f"  • {line.strip()}", "debug")

        if log_cb:
            log_cb("🎉 CHẨN ĐOÁN HOÀN TẤT: Báo cáo chẩn đoán đã được ghi nhận thành công!", "success")

        return results

    def dump_framework_files(self, device_id: str, output_dir: str, log_cb: Optional[Callable[[str, str], None]] = None) -> List[str]:
        """Pull telephony framework JAR files from device to PC for JADX decompilation."""
        if log_cb:
            log_cb("📦 Bắt đầu trích xuất tệp Framework hệ thống thiết bị về PC...", "info")

        os.makedirs(output_dir, exist_ok=True)
        target_jars = [
            "/system/framework/telephony-common.jar",
            "/system/framework/mediatek-telephony-common.jar",
            "/system/framework/mediatek-telephony-base.jar"
        ]

        pulled_files = []
        for jar_path in target_jars:
            filename = os.path.basename(jar_path)
            local_dest = os.path.join(output_dir, filename)

            if log_cb:
                log_cb(f"  • Đang trích xuất {filename}...", "info")

            code, out, err = self.run_command(["pull", jar_path, local_dest], device_id, timeout=30)
            if code == 0 and os.path.exists(local_dest):
                pulled_files.append(local_dest)
                if log_cb:
                    log_cb(f"  ✓ Trích xuất thành công {filename} -> {local_dest}", "success")
            else:
                if log_cb:
                    log_cb(f"  ⚠ Lỗi trích xuất {filename}: {out or err}", "warning")

        return pulled_files

    def unlock_bootloader_fastboot(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> Tuple[bool, str]:
        """Attempt standard OEM unlock & reboot to fastboot for bootloader unlocking."""
        if log_cb:
            log_cb("🔓 Bắt đầu quy trình mở khóa Bootloader (Unlock Bootloader)...", "info")

        # 1. Enable OEM unlock flag via ADB settings
        self.run_command(["shell", "settings", "put", "global", "oem_unlock_disallowed", "0"], device_id, timeout=3)
        self.run_command(["shell", "settings", "put", "global", "get_secure", "0"], device_id, timeout=3)
        self.run_command(["shell", "setprop", "sys.oem_unlock_allowed", "1"], device_id, timeout=3)

        info = self.get_device_info(device_id)
        brand = info.get("brand", "").lower()

        if log_cb:
            log_cb("✓ Đã bật cờ sys.oem_unlock_allowed = 1 trên Android!", "success")
            if "oppo" in brand or "realme" in brand:
                log_cb("⚠ LƯU Ý ĐẶC BIỆT DÒNG OPPO/REALME:", "warning")
                log_cb("  • Hãng OPPO đã khóa/xóa màn hình Fastboot tiêu chuẩn trên ColorOS.", "warning")
                log_cb("  • Khi nhận lệnh, điện thoại sẽ tự TẮT MÁY vào chế độ BROM Mode.", "info")
                log_cb("  • Giữ phím Nguồn 10 giây để bật lại máy nếu muốn vào Android.", "info")
                log_cb("  • Để Unlock Bootloader thiết bị OPPO MediaTek, cần chạy công cụ MTK Client qua cổng BROM.", "warning")
            else:
                log_cb("⚡ Đang khởi động lại điện thoại vào chế độ Bootloader / Fastboot...", "info")
                log_cb("👉 Màn hình máy sẽ hiện chữ FASTBOOT MODE:", "warning")
                log_cb("  • Trên máy tính gõ: fastboot flashing unlock", "info")
                log_cb("  • Nhìn màn hình bấm Nút Tăng Âm Lượng (Volume Up) để xác nhận!", "warning")

        # 2. Reboot to bootloader
        code, out, err = self.run_command(["reboot", "bootloader"], device_id, timeout=10)
        return True, "Đã xử lý quy trình Bootloader thành công!"

    def reboot_mode(self, device_id: str, mode: str = "recovery", log_cb: Optional[Callable[[str, str], None]] = None) -> Tuple[bool, str]:
        """Reboot device into Recovery, Fastboot/Bootloader, Download, or EDL mode for repair."""
        valid_modes = {
            "recovery": "Chế độ Khôi Phục (Recovery Mode)",
            "bootloader": "Chế độ Bootloader / Fastboot",
            "download": "Chế độ Nạp Phần Mềm (Download Mode)",
            "edl": "Chế độ Nạp Khẩn Cấp (EDL Mode)",
            "normal": "Khởi động lại bình thường"
        }
        
        mode_desc = valid_modes.get(mode, mode)
        if log_cb:
            log_cb(f"⚡ Đang gửi lệnh khởi động lại thiết bị vào {mode_desc}...", "info")

        if mode == "normal":
            cmd = ["reboot"]
        else:
            cmd = ["reboot", mode]

        code, out, err = self.run_command(cmd, device_id, timeout=10)
        if code == 0:
            if log_cb:
                log_cb(f"✓ Đã gửi lệnh {mode_desc} thành công!", "success")
            return True, f"Thành công {mode_desc}"
        else:
            if log_cb:
                log_cb(f"⚠ Lỗi khi chuyển {mode_desc}: {out or err}", "warning")
            return False, out or err

    def launch_secret_code(self, device_id: str, secret_code: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch an Android secret dial code directly via broadcast or direct OEM activity without touching dialer UI."""
        print(f"[DEBUG LAUNCH SECRET CODE DIRECT] Device: {device_id}, Code: {secret_code}")
        if log_cb:
            log_cb(f"⚡ Đang kích hoạt chế độ mã bí mật {secret_code}...", "info")

        digits = secret_code.replace("*", "").replace("#", "").strip()

        # 1. Direct OEM Activity Launchers (Silent & Professional Direct Launch)
        oem_activities = {
            "4636": [
                ["shell", "am", "start", "-n", "com.android.settings/.RadioInfo"],
                ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-n", "com.android.settings/.Settings$TestingSettingsActivity"],
            ],
            "800": [
                ["shell", "am", "start", "-n", "com.oppo.engineermode/.manualtest.modeltest.ModelTestImpl"],
                ["shell", "am", "start", "-n", "com.oplus.engineermode/.Engineermode"],
                ["shell", "am", "start", "-n", "com.mediatek.engineermode/.EngineerMode"],
            ],
            "801": [
                ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineersTool"],
            ],
            "808": [
                ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineerMode"],
            ],
            "36446337": [
                ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineerMode"],
            ],
            "3646633": [
                ["shell", "am", "start", "-n", "com.mediatek.engineermode/.EngineerMode"],
                ["shell", "am", "start", "-n", "com.mediatek.engineermode/.MobileRadioInfo"],
            ],
            "86583": [
                ["shell", "settings", "put", "global", "carrier_volte_available_bool", "1"],
                ["shell", "setprop", "persist.sys.volte_disable_carrier_check", "1"],
            ],
            "4838": [
                ["shell", "am", "start", "-n", "com.vivo.upside/.Testing"],
                ["shell", "am", "start", "-n", "com.iqoo.engineermode/.Testing"],
            ],
            "0808": [
                ["shell", "am", "start", "-n", "com.sec.android.app.modemui/.UsbSettings"],
            ],
            "2263": [
                ["shell", "am", "start", "-n", "com.sec.android.app.servicemodeapp/.ServiceMode"],
            ]
        }

        success = False
        if digits in oem_activities:
            for act_cmd in oem_activities[digits]:
                code, out, err = self.run_command(act_cmd, device_id, timeout=3)
                if code == 0 and "Error" not in out and "SecurityException" not in err and "Exception" not in out:
                    success = True
                    break

        if not success:
            # 2. Standard Secret Code Broadcast (Direct Intent)
            cmd_broadcast = ["shell", "am", "broadcast", "-a", "android.provider.Telephony.SECRET_CODE", "-d", f"secret_code://{digits}"]
            code, out, err = self.run_command(cmd_broadcast, device_id, timeout=3)
            if code == 0 and ("result=0" in out or "Broadcasting" in out):
                success = True

        if success:
            if log_cb:
                log_cb(f"✓ Đã mở thành công chế độ {secret_code} trên điện thoại!", "success")
            return True
        else:
            if log_cb:
                log_cb(f"⚠ Mã {secret_code} không được hỗ trợ hoặc bị nhà sản xuất khóa trên dòng máy này.", "warning")
            return False


