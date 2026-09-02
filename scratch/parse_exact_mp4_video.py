import os
import sys
import struct

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    exe_path = r"C:\Users\CMD\Downloads\VENDOR_VoLTE.exe"
    out_video = r"C:\Users\CMD\Desktop\Video_Huong_Dan_VoLTE_OPPO_A31.mp4"

    print("=== HBG TOOL: DÒ ĐÚNG KÍCH THƯỚC ATOM MP4 NGUYÊN BẢN ===")

    with open(exe_path, "rb") as f:
        data = f.read()

    # Locate 'ftyp'
    idx = data.find(b"ftyp")
    if idx == -1:
        print("❌ Không tìm thấy ftyp atom")
        return

    # 4 bytes before 'ftyp' is the 32-bit big-endian size of the ftyp atom
    atom_start = idx - 4
    print(f"📍 Bắt đầu Video MP4 tại offset: {atom_start}")

    # Read MP4 atoms sequentially to find the total video file size
    pos = atom_start
    total_size = 0
    
    while pos < len(data) - 8:
        size, atom_type = struct.unpack(">I4s", data[pos:pos+8])
        if size == 0:  # Extends to EOF
            total_size = len(data) - atom_start
            break
        elif size == 1: # 64-bit extended size
            size = struct.unpack(">Q", data[pos+8:pos+16])[0]
        
        # Check valid atom type (4 ascii chars)
        if not (atom_type.isalnum() or atom_type in [b"free", b"mdat", b"moov", b"ftyp", b"wide"]):
            print(f"  • Kết thúc cấu trúc MP4 tại offset {pos} (Gặp tag: {atom_type})")
            total_size = pos - atom_start
            break

        print(f"  • Atom [{atom_type.decode('ascii', errors='ignore')}]: Size {size:,} bytes @ offset {pos}")
        pos += size
        if pos >= len(data):
            total_size = pos - atom_start
            break

    print(f"\n🎉 KÍCH THƯỚC VIDEO MP4 CHÍNH XÁC: {total_size:,} bytes ({total_size/(1024*1024):.2f} MB)")

    # Extract exact video bytes
    video_bytes = data[atom_start : atom_start + total_size]
    with open(out_video, "wb") as f_out:
        f_out.write(video_bytes)

    print(f"✅ Đã ghi lại file Video MP4 chuẩn vào: {out_video}")

if __name__ == "__main__":
    main()
