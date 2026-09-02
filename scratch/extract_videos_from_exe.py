import os
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    exe_path = r"C:\Users\CMD\Downloads\VENDOR_VoLTE.exe"
    out_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\extracted_media"
    os.makedirs(out_dir, exist_ok=True)

    print("=== HBG TOOL: DÒ TÌM VIDEO VÀ HƯỚNG DẪN TRONG VENDOR_VOLTE.EXE ===")
    print(f"📦 Đang quét tệp EXE: {exe_path}")

    with open(exe_path, "rb") as f:
        data = f.read()

    print(f"Kích thước file EXE: {len(data):,} bytes")

    # Search for MP4 / AVI / MKV signatures
    # MP4 signature: ftyp
    mp4_signatures = [b"ftypmp42", b"ftypisom", b"ftypMSNV", b"ftyp"]
    print("\n🔍 Dò tìm định dạng Video MP4...")
    found_videos = []
    
    for sig in mp4_signatures:
        pos = 0
        while True:
            idx = data.find(sig, pos)
            if idx == -1:
                break
            # Start of atom is 4 bytes before ftyp
            start_offset = max(0, idx - 4)
            found_videos.append((start_offset, sig))
            pos = idx + len(sig)

    print(f"  • Phát hiện {len(found_videos)} điểm nghi vấn video MP4")
    for i, (offset, sig) in enumerate(found_videos):
        print(f"    -> Offset {offset}: {sig}")

    # Also check if there are other embedded ZIP archives
    zip_sig = b"PK\x03\x04"
    pos = 0
    zip_offsets = []
    while True:
        idx = data.find(zip_sig, pos)
        if idx == -1:
            break
        zip_offsets.append(idx)
        pos = idx + 4

    print(f"\n📦 Phát hiện {len(zip_offsets)} lưu trữ ZIP bên trong EXE:")
    for z_off in zip_offsets:
        print(f"  -> ZIP Offset: {z_off}")
        try:
            # Try opening Zip at offset
            with open(exe_path, "rb") as f:
                f.seek(z_off)
                with zipfile.ZipFile(f) as zf:
                    print("     Danh sách file bên trong ZIP này:")
                    for info in zf.infolist():
                        print(f"       • {info.filename} ({info.file_size:,} bytes)")
                        # If video or image, extract it!
                        if info.filename.lower().endswith((".mp4", ".avi", ".mkv", ".png", ".jpg", ".txt", ".mp3")):
                            zf.extract(info.filename, out_dir)
                            print(f"       🎉 ĐÃ XUẤT MEDIA: {os.path.join(out_dir, info.filename)}")
        except Exception as ex:
            print(f"     (Không giải nén được trực tiếp tại offset này: {ex})")

if __name__ == "__main__":
    main()
