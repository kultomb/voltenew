import os
import zipfile
import shutil

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    release_dir = os.path.join(base_dir, "releases")
    pkg_dir = os.path.join(release_dir, "HBG_VoLTE_Fixer_1Click")
    
    if os.path.exists(pkg_dir):
        shutil.rmtree(pkg_dir)
    os.makedirs(pkg_dir, exist_ok=True)
    
    # 1. Copy adb folder
    adb_src = os.path.join(base_dir, "adb")
    adb_dest = os.path.join(pkg_dir, "adb")
    if os.path.exists(adb_src):
        shutil.copytree(adb_src, adb_dest)
        
    # 2. Copy classes.dex
    dex_src = os.path.join(base_dir, "classes.dex")
    if os.path.exists(dex_src):
        shutil.copy2(dex_src, os.path.join(pkg_dir, "classes.dex"))
        
    # 3. Copy Encrypted BAT files
    fix_bat_enc = os.path.join(base_dir, "Fix_VoLTE_Direct_Encrypted.bat")
    restore_bat_enc = os.path.join(base_dir, "Restore_VoLTE_Original_Encrypted.bat")
    
    if os.path.exists(fix_bat_enc):
        shutil.copy2(fix_bat_enc, os.path.join(pkg_dir, "Chay_Ep_Bat_VoLTE_Quick.bat"))
    if os.path.exists(restore_bat_enc):
        shutil.copy2(restore_bat_enc, os.path.join(pkg_dir, "Khoi_Phuc_Trang_Thai_Goc.bat"))
        
    # 4. Copy EXE files if available
    dist_exe_dir = os.path.join(base_dir, "dist_exe")
    fix_exe = os.path.join(dist_exe_dir, "Fix_VoLTE_Direct.exe")
    restore_exe = os.path.join(dist_exe_dir, "Restore_VoLTE_Original.exe")
    
    if os.path.exists(fix_exe):
        shutil.copy2(fix_exe, os.path.join(pkg_dir, "Fix_VoLTE_Direct.exe"))
    if os.path.exists(restore_exe):
        shutil.copy2(restore_exe, os.path.join(pkg_dir, "Restore_VoLTE_Original.exe"))
        
    # 5. Create README.txt
    readme_content = """====================================================================
   HBG VoLTE and IMS Fixer Tool - Bo Cong Cu 1-Click Cho Khach Hang
====================================================================

HUONG DAN SU DUNG:

1. Ket noi dien thoai Android voi may tinh qua cap USB.
2. Tren dien thoai: Vao Cai Dat -> Tuy chon nha phat trien -> Bat "Sua loi USB" (USB Debugging).
3. De EP BAT VoLTE: Nhap dub vao "Fix_VoLTE_Direct.exe" (hoac "Chay_Ep_Bat_VoLTE_Quick.bat") -> Nhan ENTER -> Hoan thanh!
4. De KHOI PHUC TRANG THAI GOC: Nhap dub vao "Restore_VoLTE_Original.exe" (hoac "Khoi_Phuc_Trang_Thai_Goc.bat") -> Nhan ENTER.

LUU Y:
- Giu nguyen thu muc 'adb' va file 'classes.dex' nam cung thu muc tool!
"""
    with open(os.path.join(pkg_dir, "Huong_Dan_Su_Dung.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 6. Create Zip archive
    zip_path = os.path.join(release_dir, "HBG_VoLTE_Fixer_1Click_v1.0.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(pkg_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, release_dir)
                zipf.write(abs_file, rel_file)
                
    print(f"[OK] Customer Release Package Created: {zip_path}")
    print(f"     Folder: {pkg_dir}")

if __name__ == "__main__":
    main()
