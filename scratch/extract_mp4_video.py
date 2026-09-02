import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    exe_path = r"C:\Users\CMD\Downloads\VENDOR_VoLTE.exe"
    out_video = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\extracted_media\huong_dan_volte_oppo_a31.mp4"
    os.makedirs(os.path.dirname(out_video), exist_ok=True)

    print("=== HBG TOOL: TRÍCH XUẤT TỆP VIDEO MP4 HƯỚNG DẪN TỪ VENDOR_VOLTE.EXE ===")
    
    offset_start = 10316356 - 4  # 4 bytes before ftyp
    offset_end = 304816000      # Until the next zip section

    with open(exe_path, "rb") as f:
        f.seek(offset_start)
        # Read the video data
        video_data = f.read(offset_end - offset_start)

    with open(out_video, "wb") as f_out:
        f_out.write(video_data)

    print(f"🎉 TRÍCH XUẤT THÀNH CÔNG! Tệp Video đã được lưu tại:")
    print(f"👉 {out_video}")
    print(f"   Dung lượng: {len(video_data):,} bytes ({len(video_data)/(1024*1024):.2f} MB)")

if __name__ == "__main__":
    main()
