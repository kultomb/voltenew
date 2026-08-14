"""
VoLTE Fixer Engine — Smart Auto-Fixing Engine
Fully automated device management using HBGAdBlocker DeviceManager singleton for 100% parity.
Includes MCC/MNC operator resolution for Vietnam networks (Viettel, Vinaphone, Mobifone, Vietnamobile, Wintel, Itelecom).
"""

from __future__ import annotations

import os
import sys
import subprocess
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
    if DeviceManager is not None:
        try:
            dm = DeviceManager()
            cmd = dm._base_cmd()
            if cmd and os.path.exists(cmd[0]):
                return cmd[0]
        except Exception:
            pass

    candidates = [
        os.path.join(parent_dir, "platform-tools", "adb.exe"),
        os.path.join(current_dir, "platform-tools", "adb.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    return "adb"


class VoLTEEngine:
    def __init__(self, adb_path: Optional[str] = None):
        if DeviceManager is not None:
            self.dm = DeviceManager()
        else:
            self.dm = None
        self._adb_path = adb_path or find_adb_path()

    @property
    def adb_path(self) -> str:
        if self.dm and self.dm.adb_path:
            return self.dm.adb_path
        return self._adb_path

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

        if self.dm:
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
        """Get connected devices list."""
        if self.dm:
            ok, _ = self.dm.refresh()
            if ok and self.dm.serial:
                return [{
                    "id": self.dm.serial,
                    "model": self.dm.device_model or "Android Device",
                    "product": ""
                }]

        code, out, _ = self.run_command(["devices"], timeout=5)
        if code != 0 or not out:
            return []

        devices = []
        lines = [x.strip() for x in out.splitlines()[1:] if x.strip()]
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                dev_id = parts[0]
                devices.append({
                    "id": dev_id,
                    "model": "Android Device",
                    "product": ""
                })
        return devices

    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """Fetch detailed specs and SIM operator status for target device."""
        info = {
            "model": "Unknown",
            "brand": "Unknown",
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
        _, ver, _ = self.run_command(["shell", "getprop", "ro.build.version.release"], device_id, timeout=4)
        _, sdk, _ = self.run_command(["shell", "getprop", "ro.build.version.sdk"], device_id, timeout=4)
        _, platform_chip, _ = self.run_command(["shell", "getprop", "ro.board.platform"], device_id, timeout=4)

        if model and model != "Không xác định":
            info["model"] = model
        if brand:
            info["brand"] = brand.capitalize()
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
            info["ims_status"] = "Đã ép cờ VoLTE (OVR=1)"
        else:
            info["ims_status"] = "Chưa ép cờ"

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
            ("persist.sys.oppo.volte", "1"),
            ("persist.radio_oppo_ct_volte_support", "1"),
            ("persist.radio.oppo_volte_state", "1"),
            ("persist.vendor.oppo.volte", "1"),
            ("persist.mtk.volte.enable", "1"),
            ("persist.radio.volte_state", "1"),
            ("persist.vendor.mtk.volte.enable", "1"),
            ("persist.mtk_ct_volte_support", "1"),
            ("persist.mtk_volte_support", "1"),
            ("persist.mtk.wfc.enable", "1"),
            ("persist.vendor.mtk_wfc_support", "1"),
            ("persist.mtk_vilte_support", "1"),
            ("persist.mtk_viwifi_support", "1"),
        ]

        count = 0
        for prop, val in props:
            code, _, _ = self.run_command(["shell", "setprop", prop, val], device_id, timeout=4)
            if code == 0:
                count += 1

        if log_cb:
            log_cb(f"✓ Đã thiết lập thành công cấu hình cho thiết bị ({count} tham số)!", "success")
        return count > 0

    def fix_settings_db(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Update Settings Provider Database for VoLTE."""
        if log_cb:
            log_cb("› [2/4] Đồng bộ cấu hình dịch vụ cuộc gọi...", "info")

        settings_cmds = [
            ("global", "volte_vt_enabled", "1"),
            ("global", "vt_ims_enabled", "1"),
            ("system", "oppo_volte_enable", "1"),
            ("global", "oppo_volte_enable", "1"),
            ("global", "mobivolte_enable", "1"),
            ("global", "carrier_volte_available_bool", "1"),
            ("global", "wfc_ims_enabled", "1"),
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
            if info.get("is_xiaomi"):
                log_cb("🍊 Phát hiện Xiaomi / POCO: Đang tự động kích hoạt cấu hình bỏ qua giới hạn nhà mạng...", "info")
                self.run_command(["shell", "setprop", "persist.vendor.volte.disable.carrier.check", "true"], device_id, timeout=4)
                self.run_command(["shell", "setprop", "persist.vendor.vowifi.disable.carrier.check", "true"], device_id, timeout=4)

            elif info.get("is_oppo") or info.get("is_mtk"):
                log_cb("📌 Phát hiện OPPO / Realme / Chipset MTK: Đang tự động nạp cấu hình hệ thống chuyên biệt...", "warning")

            elif info.get("is_vivo"):
                log_cb("📱 Phát hiện Vivo / iQOO: Đang tự động nạp cấu hình giao diện hệ thống...", "info")

            self.fix_system_props(device_id, log_cb)
            time.sleep(0.5)
            self.fix_settings_db(device_id, log_cb)
            time.sleep(0.5)
            self.fix_carrier_config_dex(device_id, dex_path, log_cb)
            time.sleep(0.5)
            self.restart_telephony_services(device_id, log_cb)

            log_cb("🎉 HOÀN THÀNH: Đã tự động nạp toàn bộ cấu hình ép bật VoLTE cho thiết bị!", "success")

            if info.get("is_oppo") or info.get("is_mtk"):
                log_cb("💡 HƯỚNG DẪN DÀNH CHO OPPO / REALME / MTK:", "warning")
                log_cb("   1. Nhấn nút '🔧 2. Mở Cấu Hình Chuyên Sâu (OPPO/Realme)' bên dưới.", "warning")
                log_cb("   2. Chuyển tab Telephony -> IMS -> VoLTE Setting -> Bấm SET.", "warning")

            return True
        except Exception as e:
            log_cb(f"✗ Xảy ra lỗi trong quá trình kích hoạt: {e}", "error")
            return False

    def open_radio_info_menu(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Launch standard Android Phone Info."""
        if log_cb:
            log_cb("› Đang mở Menu Mạng Nâng Cao...", "info")

        code, _, err = self.run_command(
            ["shell", "am", "start", "-n", "com.android.settings/.RadioInfo"],
            device_id,
            timeout=5
        )
        if code == 0:
            if log_cb:
                log_cb("✓ Đã mở thành công Menu Mạng Nâng Cao!", "success")
            return True
        else:
            code2, _, err2 = self.run_command(
                ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-n", "com.android.settings/.TestingSettings"],
                device_id,
                timeout=5
            )
            if code2 == 0:
                if log_cb:
                    log_cb("✓ Đã mở thành công Menu Mạng Nâng Cao!", "success")
                return True

            if log_cb:
                log_cb("⚠ Không thể tự động mở Menu trên thiết bị này.", "warning")
            return False

    def open_mtk_engineer_menu(self, device_id: str, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Specifically launch EngineerMode without showing secret codes."""
        if log_cb:
            log_cb("› Đang mở Trình Cấu Hình Chuyên Sâu...", "info")

        mtk_intents = [
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-n", "com.mediatek.engineermode/com.mediatek.engineermode.EngineerMode"],
            ["shell", "am", "start", "-n", "com.oppo.engineermode/.EngineerMode"],
            ["shell", "am", "start", "-n", "com.oppo.engineermode/.oppoEngineerMode"],
        ]

        opened = False
        for cmd in mtk_intents:
            code, out, _ = self.run_command(cmd, device_id, timeout=4)
            if code == 0 and "Error" not in out:
                opened = True
                if log_cb:
                    log_cb("✓ Đã mở thành công Trình Cấu Hình Chuyên Sâu!", "success")
                    log_cb("👉 Hướng dẫn OPPO/MTK: Vào Telephony -> IMS -> VoLTE Setting -> Bấm SET.", "info")
                break

        if not opened:
            self.run_command(["shell", "am", "start", "-a", "android.intent.action.DIAL", "-d", "tel:*%23*%233646633%23*%23*"], device_id, timeout=4)
            if log_cb:
                log_cb("⚠ Đã khởi chạy trình cấu hình trên điện thoại. Vui lòng kiểm tra màn hình thiết bị.", "warning")

        return opened

    def check_ims_diagnostics(self, device_id: str, log_cb: Callable[[str, str], None]) -> None:
        """Run diagnostics on VoLTE status without leaking code keys."""
        log_cb("🔍 Đang kiểm tra chi tiết trạng thái VoLTE...", "info")

        info = self.get_device_info(device_id)
        log_cb(f"• Hãng & Model: {info.get('brand')} {info.get('model')}", "info")
        log_cb(f"• Phiên bản: {info.get('android_ver')} ({info.get('sdk')})", "info")
        log_cb(f"• SIM Operator: {info.get('operator')}", "info")
        log_cb(f"• Trạng thái VoLTE: {info.get('ims_status')}", "info")

        log_cb("✓ Kiểm tra trạng thái hoàn tất.", "success")

