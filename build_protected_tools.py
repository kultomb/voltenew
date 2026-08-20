import os
import base64
import subprocess
import sys

def obfuscate_bat(src_bat_path, dest_bat_path, title_name, color_code="0A"):
    if not os.path.exists(src_bat_path):
        print(f"Error: {src_bat_path} does not exist.")
        return False
        
    with open(src_bat_path, "r", encoding="ascii", errors="ignore") as f:
        raw_code = f.read()
        
    b64_code = base64.b64encode(raw_code.encode("utf-8")).decode("ascii")
    
    chunk_size = 100
    b64_chunks = [b64_code[i:i+chunk_size] for i in range(0, len(b64_code), chunk_size)]
    
    bat_lines = [
        "@echo off",
        f"title {title_name}",
        f"color {color_code}",
        "cd /d \"%~dp0\"",
        "setlocal enabledelayedexpansion",
        "set \"B64_DATA=\""
    ]
    for chunk in b64_chunks:
        bat_lines.append(f"set \"B64_DATA=!B64_DATA!{chunk}\"")
        
    bat_lines.extend([
        "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$b=[System.Convert]::FromBase64String('!B64_DATA!');$s=[System.Text.Encoding]::UTF8.GetString($b);$p=[System.IO.Path]::Combine($env:TEMP, [System.IO.Path]::GetRandomFileName()+'.bat');[System.IO.File]::WriteAllText($p,$s);& cmd.exe /c $p; Remove-Item $p -ErrorAction SilentlyContinue\"",
        "exit /b %ERRORLEVEL%"
    ])
    
    with open(dest_bat_path, "w", encoding="ascii") as f:
        f.write("\n".join(bat_lines))
        
    print(f"[OK] Created Encrypted Batch File: {dest_bat_path}")
    return True

def create_py_wrapper(src_bat_path, py_dest_path, title):
    with open(src_bat_path, "r", encoding="ascii", errors="ignore") as f:
        raw_code = f.read()
    b64_code = base64.b64encode(raw_code.encode("utf-8")).decode("ascii")
    
    py_code = f'''import os
import sys
import base64
import tempfile
import subprocess

b64_data = "{b64_code}"

def main():
    raw_bytes = base64.b64decode(b64_data)
    temp_dir = tempfile.gettempdir()
    temp_bat = os.path.join(temp_dir, f"volte_run_{{os.getpid()}}.bat")
    
    with open(temp_bat, "wb") as f:
        f.write(raw_bytes)
        
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        res = subprocess.run([temp_bat], cwd=current_dir)
        sys.exit(res.returncode)
    finally:
        if os.path.exists(temp_bat):
            try:
                os.remove(temp_bat)
            except Exception:
                pass

if __name__ == "__main__":
    main()
'''
    with open(py_dest_path, "w", encoding="utf-8") as f:
        f.write(py_code)
    print(f"[OK] Created Python Wrapper: {py_dest_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    fix_bat = os.path.join(base_dir, "Fix_VoLTE_Direct.bat")
    restore_bat = os.path.join(base_dir, "Restore_VoLTE_Original.bat")
    
    enc_fix_bat = os.path.join(base_dir, "Fix_VoLTE_Direct_Encrypted.bat")
    enc_restore_bat = os.path.join(base_dir, "Restore_VoLTE_Original_Encrypted.bat")
    
    # 1. Obfuscate BAT files
    obfuscate_bat(fix_bat, enc_fix_bat, "HBG VoLTE Fixer (Encrypted 1-Click)", "0A")
    obfuscate_bat(restore_bat, enc_restore_bat, "HBG VoLTE Restore (Encrypted Reset)", "0C")
    
    # 2. Build Python Wrappers for PyInstaller
    fix_py = os.path.join(base_dir, "run_fix_exe.py")
    restore_py = os.path.join(base_dir, "run_restore_exe.py")
    
    create_py_wrapper(fix_bat, fix_py, "VoLTE Fixer Direct")
    create_py_wrapper(restore_bat, restore_py, "VoLTE Restore State")
    
    # 3. Compile EXE binaries using PyInstaller
    print("\nBuilding EXE files with PyInstaller...")
    
    dist_dir = os.path.join(base_dir, "dist_exe")
    build_dir = os.path.join(base_dir, "build_tmp")
    
    cmd_fix = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--console",
        "--name", "Fix_VoLTE_Direct",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        fix_py
    ]
    subprocess.run(cmd_fix, cwd=base_dir)
    
    cmd_restore = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile", "--console",
        "--name", "Restore_VoLTE_Original",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        restore_py
    ]
    subprocess.run(cmd_restore, cwd=base_dir)
    
    print("\nEncrypted and Compiled Tools Build Complete!")
    print(f"  * Encrypted BAT Fix     : {enc_fix_bat}")
    print(f"  * Encrypted BAT Restore : {enc_restore_bat}")
    print(f"  * Standalone EXE Fix    : {os.path.join(dist_dir, 'Fix_VoLTE_Direct.exe')}")
    print(f"  * Standalone EXE Restore: {os.path.join(dist_dir, 'Restore_VoLTE_Original.exe')}")

if __name__ == "__main__":
    main()
