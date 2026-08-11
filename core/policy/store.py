"""Runtime blacklist: load/save from AppData, merge with shipped defaults."""

import json
import logging
import os

from .blacklist_defaults import DEFAULT_BLACKLIST
from .whitelists import TRUSTED_ANALYSIS_PACKAGES

# Mutable runtime list; use replace_blacklist() instead of rebinding this name.
BLACKLIST: list[str] = []


def replace_blacklist(items) -> None:
    BLACKLIST[:] = sorted(set(items))


def _strip_trusted() -> None:
    replace_blacklist(p for p in BLACKLIST if p not in TRUSTED_ANALYSIS_PACKAGES)


def load_config(appdata_dir: str) -> None:
    config_path = os.path.join(appdata_dir, "config.json")
    if not os.path.exists(config_path):
        return
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if "blacklist" in config:
            replace_blacklist(config["blacklist"])
        _strip_trusted()
    except Exception as e:
        logging.error(f"Lỗi tải cấu hình: {e}")


def load_blacklist_file(appdata_dir: str) -> None:
    blacklist_path = os.path.join(appdata_dir, "blacklist.txt")
    if not os.path.exists(blacklist_path):
        return
    try:
        with open(blacklist_path, "r", encoding="utf-8") as f:
            loaded = [line.strip() for line in f if line.strip()]
        replace_blacklist(list(BLACKLIST) + loaded)
        logging.info(f"Đã tải {len(loaded)} package từ blacklist.txt")
    except Exception as e:
        logging.error(f"Lỗi tải blacklist: {e}")


def save_blacklist(appdata_dir: str) -> None:
    blacklist_path = os.path.join(appdata_dir, "blacklist.txt")
    try:
        with open(blacklist_path, "w", encoding="utf-8") as f:
            for package in sorted(BLACKLIST):
                f.write(f"{package}\n")
        logging.info(f"Đã lưu {len(BLACKLIST)} package vào blacklist.txt")
    except Exception as e:
        logging.error(f"Lỗi lưu blacklist: {e}")


def save_config(appdata_dir: str) -> None:
    config_path = os.path.join(appdata_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"blacklist": list(BLACKLIST)}, f, indent=2)


def persist_blacklist(appdata_dir: str) -> None:
    """Write runtime blacklist to AppData (config + txt)."""
    save_config(appdata_dir)
    save_blacklist(appdata_dir)


def init_policy(appdata_dir: str) -> None:
    replace_blacklist(DEFAULT_BLACKLIST)
    load_config(appdata_dir)
    load_blacklist_file(appdata_dir)
    _strip_trusted()


def is_valid_package(package) -> bool:
    if not package or not isinstance(package, str):
        return False
    if not package[0].isalnum():
        return False
    return all(c.isalnum() or c in "._" for c in package)


def add_to_blacklist(package: str, appdata_dir: str) -> bool:
    if not is_valid_package(package):
        logging.warning(f"Package không hợp lệ: {package}")
        return False
    if package in BLACKLIST:
        logging.info(f"Package đã tồn tại trong blacklist: {package}")
        return True
    from .rules import is_protected_package

    if is_protected_package(package):
        logging.warning(f"Không thêm package được bảo vệ (TikTok, ngân hàng, v.v.): {package}")
        return False
    replace_blacklist(list(BLACKLIST) + [package])
    save_blacklist(appdata_dir)
    logging.info(f"Đã thêm package vào blacklist: {package}")
    return True
