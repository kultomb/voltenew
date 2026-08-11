"""
Notification control via ADB — AppOps, cmd notification (Android 13+), suspend/unsuspend.
"""

from __future__ import annotations

import logging
import re
from typing import Callable, Optional

_FAIL_HINTS = (
    "error", "exception", "unknown command", "not found", "no such",
    "securityexception", "permission denial", "invalid", "failed",
)


class NotificationControl:
    """Tắt / bật thông báo app qua shell (ưu tiên lệnh tương thích đa hãng)."""

    def __init__(
        self,
        *,
        shell: Callable[..., str],
        serial_getter: Callable[[], Optional[str]],
        run_adb: Callable | None = None,
    ):
        self._shell = shell
        self._serial = serial_getter
        self._run = run_adb

    def _exec(self, *args: str, timeout: int = 10) -> tuple[int, str, str]:
        serial = self._serial()
        if not serial:
            return -1, "", "no device"
        if self._run:
            out, err, code = self._run(["-s", serial, "shell", *args], timeout=timeout)
            return code, (out or "").strip(), (err or "").strip()
        out = self._shell(list(args), timeout=timeout) or ""
        return 0, out.strip(), ""

    @staticmethod
    def _cmd_succeeded(code: int, out: str, err: str) -> bool:
        if code != 0:
            return False
        blob = f"{out} {err}".lower()
        return not any(h in blob for h in _FAIL_HINTS)

    def _run_step(self, args: list[str], steps: list[str]) -> bool:
        label = args[0] if len(args) == 1 else args[1] if args[0] in ("cmd", "pm", "am", "appops") else args[-2]
        code, out, err = self._exec(*args, timeout=10)
        ok = self._cmd_succeeded(code, out, err)
        if not ok:
            steps.append(f"{label}:fail")
        return ok

    def _shell_user_ids(self) -> list[str]:
        code, out, _, = self._exec("cmd", "user", "list", timeout=8)
        if code != 0 or not out:
            return ["0"]
        ids = re.findall(r"UserInfo\{(\d+):", out)
        return ids or ["0"]

    def _read_notifications_enabled(self, package: str) -> Optional[bool]:
        code, out, err = self._exec(
            "cmd", "notification", "get_notifications_enabled_for_package", package, timeout=8
        )
        if code == 0 and out:
            t = out.strip().lower()
            if t in ("false", "0", "disabled"):
                return False
            if t in ("true", "1", "enabled"):
                return True
        code, out, err = self._exec("dumpsys", "package", package, timeout=14)
        if code != 0:
            return None
        for line in out.splitlines():
            low = line.lower().replace(" ", "")
            if "mnotificationsenabled=false" in low:
                return False
            if "mnotificationsenabled=true" in low:
                return True
        blob = f"{out} {err}".lower()
        if "post_notification" in blob and ("mode=ignore" in blob or "mode=deny" in blob):
            return False
        return None

    def get_post_notification_mode(self, package: str) -> str:
        code, out, err = self._exec("cmd", "appops", "get", package, "POST_NOTIFICATION", timeout=8)
        blob = f"{out} {err}".lower()
        if code != 0:
            return "unknown"
        if "ignore" in blob or "deny" in blob:
            return "blocked"
        if "allow" in blob or "default" in blob:
            return "allowed"
        if "no operations" in blob:
            return "default"
        return "unknown"

    def is_package_notification_suspended(self, package: str) -> bool:
        for args in (
            ("cmd", "notification", "list_suspended_packages"),
            ("cmd", "notification", "list_blocked_packages"),
        ):
            code, out, err = self._exec(*args, timeout=8)
            if code != 0:
                continue
            text = f"{out}\n{err}"
            if re.search(rf"(?:^|\s|,){re.escape(package)}(?:\s|,|$)", text, re.M):
                return True
        return False

    def are_notifications_blocked(self, package: str) -> bool:
        enabled = self._read_notifications_enabled(package)
        if enabled is False:
            return True
        if enabled is True:
            return False
        if self.get_post_notification_mode(package) == "blocked":
            return True
        return self.is_package_notification_suspended(package)

    def _push_device_ui_refresh(self, package: str, *, enabled: bool) -> None:
        flag = "true" if enabled else "false"
        pkg_uri = f"package:{package}"
        for args in (
            ["cmd", "notification", "set_notifications_enabled_for_package", package, flag],
            [
                "am", "broadcast", "-a", "android.permission.action.POST_NOTIFICATIONS_CHANGED",
                "-d", pkg_uri, package,
            ],
            ["am", "broadcast", "-a", "android.intent.action.PACKAGE_CHANGED", "-d", pkg_uri, package],
            [
                "am", "broadcast", "-a", "android.intent.action.PACKAGE_CHANGED",
                "-d", pkg_uri, "--user", "0", package,
            ],
            ["am", "broadcast", "-a", "android.intent.action.APPLICATION_PREFERENCES_CHANGED", package],
            [
                "am", "broadcast", "-a", "android.intent.action.PACKAGE_CHANGED",
                "-d", pkg_uri, "-p", "com.android.settings", package,
            ],
        ):
            self._exec(*args, timeout=5)

    def _disable_attempts(self, package: str) -> list[list[str]]:
        attempts: list[list[str]] = [
            ["cmd", "notification", "set_notifications_enabled_for_package", package, "false"],
            ["cmd", "notification", "set_notifications_enabled_for_package", package, "0"],
            ["cmd", "appops", "set", package, "POST_NOTIFICATION", "deny"],
            ["cmd", "appops", "set", package, "POST_NOTIFICATION", "ignore"],
            ["appops", "set", package, "POST_NOTIFICATION", "deny"],
            ["appops", "set", package, "POST_NOTIFICATION", "ignore"],
        ]
        for uid in self._shell_user_ids():
            attempts.extend([
                ["cmd", "appops", "set", "--user", uid, package, "POST_NOTIFICATION", "deny"],
                ["cmd", "appops", "set", "--user", uid, package, "POST_NOTIFICATION", "ignore"],
                ["pm", "revoke", "--user", uid, package, "android.permission.POST_NOTIFICATIONS"],
                ["cmd", "notification", "suspend_package", "--user", uid, package],
            ])
        attempts.extend([
            ["pm", "revoke", "--user", "0", package, "android.permission.POST_NOTIFICATIONS"],
            ["pm", "revoke", package, "android.permission.POST_NOTIFICATIONS"],
            ["cmd", "notification", "suspend_package", "--user", "0", package],
            ["cmd", "notification", "suspend_package", package],
        ])
        return attempts

    def _enable_attempts(self, package: str) -> list[list[str]]:
        attempts: list[list[str]] = [
            ["cmd", "notification", "set_notifications_enabled_for_package", package, "true"],
            ["cmd", "notification", "set_notifications_enabled_for_package", package, "1"],
            ["cmd", "notification", "unsuspend_package", "--user", "0", package],
            ["cmd", "notification", "unsuspend_package", package],
            ["cmd", "appops", "set", package, "POST_NOTIFICATION", "allow"],
            ["cmd", "appops", "set", package, "POST_NOTIFICATION", "default"],
            ["appops", "set", package, "POST_NOTIFICATION", "allow"],
            ["appops", "set", package, "POST_NOTIFICATION", "default"],
        ]
        for uid in self._shell_user_ids():
            attempts.extend([
                ["cmd", "appops", "set", "--user", uid, package, "POST_NOTIFICATION", "allow"],
                ["cmd", "appops", "set", "--user", uid, package, "POST_NOTIFICATION", "default"],
                ["pm", "grant", "--user", uid, package, "android.permission.POST_NOTIFICATIONS"],
                ["cmd", "notification", "unsuspend_package", "--user", uid, package],
            ])
        attempts.extend([
            ["pm", "grant", "--user", "0", package, "android.permission.POST_NOTIFICATIONS"],
            ["pm", "grant", package, "android.permission.POST_NOTIFICATIONS"],
        ])
        return attempts

    def disable_notifications(self, package: str) -> tuple[bool, str]:
        if not package:
            return False, ""
        if self.are_notifications_blocked(package):
            return True, ""
        steps: list[str] = []
        ok_any = False
        for args in self._disable_attempts(package):
            if self._run_step(args, steps):
                ok_any = True
                if self._read_notifications_enabled(package) is False:
                    break
        self._push_device_ui_refresh(package, enabled=False)
        if self.are_notifications_blocked(package):
            return True, ""
        if ok_any:
            return True, ""
        logging.warning("notify disable failed %s: %s", package, " ".join(steps[:12]))
        return False, ""

    def enable_notifications(self, package: str) -> tuple[bool, str]:
        if not package:
            return False, ""
        if not self.are_notifications_blocked(package):
            return True, ""
        steps: list[str] = []
        ok_any = False
        for args in self._enable_attempts(package):
            if self._run_step(args, steps):
                ok_any = True
                if self._read_notifications_enabled(package) is True:
                    break
        self._push_device_ui_refresh(package, enabled=True)
        if not self.are_notifications_blocked(package):
            return True, ""
        if ok_any:
            return True, ""
        logging.warning("notify enable failed %s: %s", package, " ".join(steps[:12]))
        return False, ""
