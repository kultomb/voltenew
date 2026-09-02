import os
import shutil
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    project_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool"
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")

    print("=== HBG TOOL: BẮT ĐẦU ĐÓNG GÓI TỆP THỰC THI MONOLITHIC HBG_VOLTE_FIXER_TOOL.EXE ===")

    # Prepare PyInstaller command flags
    cmd = [
        "python", "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",  # Clean folder build for maximum speed
        "--windowed", # No black CMD console window
        "--name=HBG_VoLTE_Fixer_Tool_v2.0",
        f"--add-data={os.path.join(project_dir, 'assets')};assets",
        f"--add-data={os.path.join(project_dir, 'tools')};tools",
        f"--add-data={os.path.join(project_dir, 'vendor_patcher')};vendor_patcher",
    ]

    # Include optional APKs / binaries if exist
    for extra in ["carrierconfig.dex", "Shizuku_13.6.0.r1091.b844bc49_APKPure.apk", "pixel-ims-1-3-2.apk"]:
        p = os.path.join(project_dir, extra)
        if os.path.exists(p):
            cmd.append(f"--add-data={p};.")

    cmd.append(os.path.join(project_dir, "volte_fixer_gui.py"))

    print("\n📦 Đang biên dịch PyInstaller...")
    print(f"Lệnh chạy: {' '.join(cmd)}")

    res = subprocess.run(cmd, cwd=project_dir)

    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "HBG_VoLTE_Fixer_Tool_v2.0", "HBG_VoLTE_Fixer_Tool_v2.0.exe")
        print("\n🎉 ĐÓNG GÓI THÀNH CÔNG RỰC RỠ!")
        print(f"👉 Thư mục phần mềm hoàn chỉnh cho người khác dùng: {os.path.dirname(exe_path)}")
        print(f"👉 Tệp chạy chính: {exe_path}")
    else:
        print(f"\n❌ Lỗi khi đóng gói PyInstaller (Mã lỗi: {res.returncode})")

if __name__ == "__main__":
    main()
