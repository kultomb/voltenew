"""
HBG VoLTE & IMS Fixer — Automated Release & Build Management System
Automates version incrementing, code string updates, PyInstaller EXE packaging,
release ZIP archiving, and Git commit/tagging/pushing.
"""

from __future__ import annotations

import sys
import os
import re
import json
import shutil
import zipfile
import subprocess
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
RELEASES_DIR = os.path.join(BASE_DIR, "releases")
GUI_FILE = os.path.join(BASE_DIR, "volte_fixer_gui.py")
ENGINE_FILE = os.path.join(BASE_DIR, "volte_engine.py")
GRADLE_FILE = os.path.join(BASE_DIR, "volte_fixer_mobile", "app", "build.gradle.kts")
JAVA_FILE = os.path.join(BASE_DIR, "VolteFixer.java")


def load_version_info() -> dict:
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "3.6.0",
        "build_number": 1,
        "last_build_time": ""
    }


def save_version_info(data: dict):
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def bump_version(current_ver: str, bump_type: str) -> str:
    parts = current_ver.strip().lstrip("v").split(".")
    while len(parts) < 3:
        parts.append("0")

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        major, minor, patch = 3, 6, 0

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0

    return f"{major}.{minor}.{patch}"


def update_source_code_versions(ver_str: str, build_num: int):
    print(f"\n📝 Đang tự động cập nhật phiên bản 'v{ver_str}' (Build #{build_num}) vào toàn bộ mã nguồn...")

    # 1. Update volte_fixer_gui.py (badge_ver & window title)
    if os.path.exists(GUI_FILE):
        with open(GUI_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # Update badge_ver text
        content = re.sub(
            r'text="v\d+\.\d+[^"]*"',
            f'text="v{ver_str} ULTRA"',
            content
        )
        # Update window title
        content = re.sub(
            r'self\.title\("HBG VoLTE & IMS Fixer ⚡[^"]*"\)',
            f'self.title("HBG VoLTE & IMS Fixer ⚡ v{ver_str}")',
            content
        )
        with open(GUI_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Đã cập nhật {os.path.basename(GUI_FILE)}")

    # 2. Update volte_engine.py
    if os.path.exists(ENGINE_FILE):
        with open(ENGINE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(
            r'VoLTE Fixer Engine v\d+\.\d+.*',
            f'VoLTE Fixer Engine v{ver_str} (Build #{build_num})',
            content
        )
        with open(ENGINE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Đã cập nhật {os.path.basename(ENGINE_FILE)}")

    # 3. Update Android Mobile build.gradle.kts
    if os.path.exists(GRADLE_FILE):
        with open(GRADLE_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        content = re.sub(r'versionCode\s*=\s*\d+', f'versionCode = {build_num}', content)
        content = re.sub(r'versionName\s*=\s*"[^"]*"', f'versionName = "{ver_str}"', content)

        with open(GRADLE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Đã cập nhật {os.path.basename(GRADLE_FILE)}")


def run_pyinstaller_build(ver_str: str) -> bool:
    print("\n📦 Bắt đầu tiến trình đóng gói PyInstaller Standalone Executable (EXE)...")

    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")
    spec_file = os.path.join(BASE_DIR, "HBG_VoLTE_Fixer.spec")

    # Clean old build dirs
    for d in [dist_dir, build_dir]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception:
                pass
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
        except Exception:
            pass

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=HBG_VoLTE_Fixer",
        f"--add-data=adb{os.path.pathsep}adb",
        f"--add-data=assets{os.path.pathsep}assets",
        f"--add-data=scrcpy{os.path.pathsep}scrcpy",
        f"--add-data=Shizuku_13.6.0.r1091.b844bc49_APKPure.apk{os.path.pathsep}.",
        f"--add-data=pixel-ims-1-3-2.apk{os.path.pathsep}.",
        "volte_fixer_gui.py"
    ]

    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode == 0:
        print("  ✓ Đóng gói PyInstaller EXE thành công!")
        return True
    else:
        print("  ⚠ Cảnh báo: Đóng gói PyInstaller thất bại (Sẽ dùng bộ launcher script fallback).")
        return False


def build_release_zip(ver_str: str, build_num: int) -> str:
    print("\n🗂 Đang tạo tệp nén Release ZIP hoàn chỉnh cho phiên bản...")
    os.makedirs(RELEASES_DIR, exist_ok=True)

    zip_name = f"HBG_VoLTE_Fixer_v{ver_str}_Build{build_num:03d}.zip"
    zip_path = os.path.join(RELEASES_DIR, zip_name)

    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except Exception:
            pass

    exe_dist = os.path.join(BASE_DIR, "dist", "HBG_VoLTE_Fixer")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(exe_dist):
            for root, dirs, files in os.walk(exe_dist):
                # Explicitly exclude source code and build cache directories
                dirs[:] = [d for d in dirs if d not in ["volte_fixer_mobile", ".gradle", ".idea", "__pycache__", "build"]]
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, exe_dist)
                    zf.write(full_path, os.path.join(f"HBG_VoLTE_Fixer_v{ver_str}", rel_path))
        else:
            # Fallback package structure (Only include compiled PC release files)
            files_to_include = [
                "Run_VoLTE_Fixer.bat",
                "volte_fixer_gui.py",
                "volte_engine.py",
                "VolteFixer.java",
                "classes.dex",
                "Shizuku_13.6.0.r1091.b844bc49_APKPure.apk",
                "pixel-ims-1-3-2.apk",
                "hbg-volte-fixer-v1.apk"
            ]
            dirs_to_include = ["adb", "assets", "scrcpy"]

            folder_in_zip = f"HBG_VoLTE_Fixer_v{ver_str}"
            for f in files_to_include:
                fp = os.path.join(BASE_DIR, f)
                if os.path.exists(fp):
                    zf.write(fp, os.path.join(folder_in_zip, f))

            for d in dirs_to_include:
                dp = os.path.join(BASE_DIR, d)
                if os.path.exists(dp) and d != "volte_fixer_mobile":
                    for root, dirs, files in os.walk(dp):
                        dirs[:] = [subd for subd in dirs if subd not in ["__pycache__", ".gradle"]]
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, BASE_DIR)
                            zf.write(full_path, os.path.join(folder_in_zip, rel_path))

    print(f"  ✓ Đã loại bỏ hoàn toàn thư mục nguồn Android Studio ('volte_fixer_mobile') khỏi bộ đóng gói.")
    print(f"🎉 TẠO FILE RELEASE ZIP THÀNH CÔNG: {zip_path}")
    return zip_path


def git_commit_and_tag(ver_str: str, build_num: int):
    print("\n🚀 Đang tự động Git Commit, Tạo Tag và Push lên GitHub Repository...")
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        commit_msg = f"Release version v{ver_str} (Build #{build_num})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR)

        tag_name = f"v{ver_str}"
        # Delete tag locally if exists
        subprocess.run(["git", "tag", "-d", tag_name], cwd=BASE_DIR, capture_output=True)

        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name} Build #{build_num}"], cwd=BASE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main", "--tags"], cwd=BASE_DIR, check=True)
        print(f"✓ Đã Commit, Tạo Tag '{tag_name}' và Push thành công lên GitHub!")
    except Exception as e:
        print(f"⚠ Git Push/Tag thất bại: {e}")


def main():
    print("=" * 60)
    print("  HBG VoLTE & IMS Fixer — BỘ CÔNG CỤ BUILD PHIÊN BẢN TỰ ĐỘNG")
    print("=" * 60)

    info = load_version_info()
    current_ver = info.get("version", "3.6.0")
    build_num = info.get("build_number", 1)

    print(f"\n📌 Phiên bản hiện tại : v{current_ver}")
    print(f"📌 Lần Build (Build #)  : #{build_num}")
    print("\n[ LỰA CHỌN PHIÊN BẢN BUILD TIẾP THEO ]")
    print(" 1. Build Patch Release  (VD: v3.6.0 -> v3.6.1)")
    print(" 2. Build Minor Release  (VD: v3.6.0 -> v3.7.0)")
    print(" 3. Build Major Release  (VD: v3.6.0 -> v4.0.0)")
    print(" 4. Nhập phiên bản tùy chỉnh")
    print(" 5. Re-build lại phiên bản hiện tại")

    choice = input("\n👉 Nhập lựa chọn (1-5) [Mặc định: 1]: ").strip()
    if not choice:
        choice = "1"

    if choice == "1":
        new_ver = bump_version(current_ver, "patch")
        build_num += 1
    elif choice == "2":
        new_ver = bump_version(current_ver, "minor")
        build_num += 1
    elif choice == "3":
        new_ver = bump_version(current_ver, "major")
        build_num += 1
    elif choice == "4":
        custom_v = input("   Nhập chuỗi phiên bản (VD: 3.6.5): ").strip().lstrip("v")
        new_ver = custom_v if custom_v else current_ver
        build_num += 1
    elif choice == "5":
        new_ver = current_ver
    else:
        new_ver = bump_version(current_ver, "patch")
        build_num += 1

    # Save version info
    info["version"] = new_ver
    info["build_number"] = build_num
    info["last_build_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_version_info(info)

    # 1. Update source code files
    update_source_code_versions(new_ver, build_num)

    # 2. PyInstaller Packaging
    run_pyinstaller_build(new_ver)

    # 3. Create Release ZIP
    zip_path = build_release_zip(new_ver, build_num)

    # 4. Git Commit & Tag & Push
    git_commit_and_tag(new_ver, build_num)

    print("\n" + "=" * 60)
    print(f"🎉 HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH BUILD PHIÊN BẢN v{new_ver} (Build #{build_num})!")
    print(f"📦 File Release ZIP: {zip_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
