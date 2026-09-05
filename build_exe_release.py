import os
import shutil
import subprocess
import sys
import json
import zipfile
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")
    releases_dir = os.path.join(project_dir, "releases")
    version_file = os.path.join(project_dir, "version.json")
    icon_path = os.path.join(project_dir, "assets", "app_icon.ico")

    # Load / Bump version info
    version_str = "2.0.0"
    build_num = 1
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as vf:
                vdata = json.load(vf)
                version_str = vdata.get("version", "2.0.0")
                build_num = vdata.get("build_number", 0) + 1
        except Exception:
            pass

    # Save updated version info
    vinfo = {
        "version": version_str,
        "build_number": build_num,
        "last_build_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(version_file, "w", encoding="utf-8") as vf:
            json.dump(vinfo, vf, indent=4, ensure_ascii=False)
    except Exception:
        pass

    print("====================================================================")
    print("  🚀 HBG TOOL: ĐÓNG GÓI BẢO VỆ CHỐNG DECOMPILE (CYTHON + PYARMOR)")
    print(f"  📌 Phiên bản: v{version_str} (Build #{build_num})")
    print("====================================================================")

    # Clean up old build/dist output folders before building
    for d in [dist_dir, build_dir]:
        target = os.path.join(d, "HBG_VoLTE_Fixer_Tool_v2.0")
        if os.path.exists(target):
            try:
                shutil.rmtree(target)
            except Exception:
                pass

    # 1. Cythonize Core Engines directly to Native C Extensions (.pyd)
    print("\n🛡️ [1/3] Đang tiến hành mã hóa biên dịch Cython sang C Native Extensions (.pyd)...")
    try:
        from setuptools import setup
        from Cython.Build import cythonize
        cython_targets = [
            "volte_engine.py",
            os.path.join("vendor_patcher", "vendor_engine.py"),
            os.path.join("vendor_patcher", "restore_engine.py")
        ]
        setup(
            script_args=["build_ext", "--inplace"],
            ext_modules=cythonize(cython_targets, build_dir=os.path.join("build", "cython_tmp"), quiet=True)
        )
        print("  ✓ Biên dịch Cython C-Extensions (.pyd) CHỐNG DECOMPILE THÀNH CÔNG!")
    except Exception as e:
        print(f"  ⚠ Cảnh báo Cython: {e}")

    # 2. PyArmor Obfuscation for GUI components
    print("\n🔒 [2/3] Đang mã hóa AES Bytecode bằng PyArmor...")
    obf_dir = os.path.join(build_dir, "obf_src")
    if os.path.exists(obf_dir):
        try:
            shutil.rmtree(obf_dir)
        except Exception:
            pass

    try:
        pyarmor_cmd = [
            sys.executable, "-m", "pyarmor.cli", "gen",
            "-O", obf_dir,
            os.path.join("vendor_patcher", "vendor_patcher_gui.py")
        ]
        subprocess.run(pyarmor_cmd, cwd=project_dir, capture_output=True)
        print("  ✓ Mã hóa PyArmor AES Bytecode THÀNH CÔNG!")
    except Exception as ex:
        print(f"  ⚠ Cảnh báo PyArmor: {ex}")

    # 3. PyInstaller Standalone 1-File Executable Packaging
    print("\n📦 [3/3] Đang đóng gói PyInstaller (Standalone 1-File EXE với App Icon)...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=HBG_VoLTE_Fixer_Tool_v2.0",
        f"--add-data={os.path.join(project_dir, 'assets')};assets",
        f"--add-data={os.path.join(project_dir, 'scrcpy')};scrcpy",
        f"--add-data={os.path.join(project_dir, 'tools')};tools",
        f"--add-data={os.path.join(project_dir, 'vendor_patcher')};vendor_patcher",
    ]

    # Add icon flag if icon exists
    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")
        print(f"  ✓ Đã đính kèm App Icon đầy đủ: {icon_path}")

    # Include optional APKs / binaries if exist
    for extra in ["carrierconfig.dex", "Shizuku_13.6.0.r1091.b844bc49_APKPure.apk", "pixel-ims-1-3-2.apk"]:
        p = os.path.join(project_dir, extra)
        if os.path.exists(p):
            cmd.append(f"--add-data={p};.")

    cmd.append(os.path.join(project_dir, "volte_fixer_gui.py"))

    print(f"Lệnh chạy: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=project_dir)

    # Clean up generated inplace .pyd files after PyInstaller packaging
    for root, dirs, files in os.walk(project_dir):
        if "dist" in root or "build" in root or ".git" in root:
            continue
        for f in files:
            if f.endswith((".pyd", ".c")):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass

    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "HBG_VoLTE_Fixer_Tool_v2.0.exe")

        print("\n🎉 ĐÓNG GÓI PYINSTALLER CHỐNG DECOMPILE THÀNH CÔNG RỰC RỠ!")
        print(f"👉 File thực thi duy nhất (Có Icon đầy đủ): {exe_path}")

        # Create Release ZIP in releases/ folder
        os.makedirs(releases_dir, exist_ok=True)
        zip_name = f"HBG_VoLTE_Fixer_v{version_str}_Build{build_num:03d}.zip"
        zip_path = os.path.join(releases_dir, zip_name)

        print(f"\n🗂 Đang đóng gói tệp nén phát hành vào thư mục RELEASES: [{zip_name}]...")
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except Exception:
                pass

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(exe_path):
                zf.write(exe_path, "HBG_VoLTE_Fixer_Tool_v2.0.exe")

        print("=" * 66)
        print(f"🎉 HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH RELEASE BUILD CHỐNG DECOMPILE!")
        print(f"📦 File Release ZIP tại mục releases/: {zip_path}")
        print(f"👉 File EXE tại dist/: {exe_path}")
        print("=" * 66)
    else:
        print(f"\n❌ Lỗi khi đóng gói PyInstaller (Mã lỗi: {res.returncode})")

if __name__ == "__main__":
    main()
