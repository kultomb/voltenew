import os
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    dist_folder = r"C:\Users\CMD\Desktop\volte_fixer_tool\dist\HBG_VoLTE_Fixer_Tool_v2.0"
    out_zip = r"C:\Users\CMD\Desktop\HBG_VoLTE_Fixer_Tool_v2.0_PORTABLE.zip"

    print("=== HBG TOOL: NÉN THƯ MỤC PHẦN MỀM THÀNH TỆP ZIP PORTABLE DỄ CHIA SẺ ===")
    print(f"📦 Thư mục nguồn: {dist_folder}")

    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dist_folder))
                zipf.write(file_path, arcname)

    sz = os.path.getsize(out_zip)
    print("\n🎉 NÉN TỆP ZIP THÀNH CÔNG RỰC RỠ!")
    print(f"👉 Tệp Zip Portable sẵn sàng chia sẻ: {out_zip}")
    print(f"   Dung lượng tệp ZIP: {sz / (1024*1024):.2f} MB ({sz:,} bytes)")

if __name__ == "__main__":
    main()
