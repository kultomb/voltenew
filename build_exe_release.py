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
    print("  🚀 HBG TOOL: ĐÓNG GÓI TỆP THỰC THI MONOLITHIC & TẠO BAN RELEASE")
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

    # Prepare PyInstaller command flags (Standalone Single EXE file with icon)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=HBG_VoLTE_Fixer_Tool_v2.0",
        f"--add-data={os.path.join(project_dir, 'assets')};assets",
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

    print("\n📦 Đang biên dịch PyInstaller (Standalone 1-File EXE)...")
    print(f"Lệnh chạy: {' '.join(cmd)}")

    res = subprocess.run(cmd, cwd=project_dir)

    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "HBG_VoLTE_Fixer_Tool_v2.0.exe")

        print("\n🎉 ĐÓNG GÓI PYINSTALLER THÀNH CÔNG RỰC RỠ!")
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
        print(f"🎉 HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH RELEASE BUILD!")
        print(f"📦 File Release ZIP tại mục releases/: {zip_path}")
        print(f"👉 File EXE tại dist/: {exe_path}")
        print("=" * 66)
    else:
        print(f"\n❌ Lỗi khi đóng gói PyInstaller (Mã lỗi: {res.returncode})")

if __name__ == "__main__":
    main()
