import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    video_file = r"C:\Users\CMD\Desktop\Video_Huong_Dan_VoLTE_OPPO_A31.mp4"
    if os.path.exists(video_file):
        print(f"🎬 Đang mở Video MP4 đầy đủ 100% (739 MB): {video_file}")
        os.startfile(video_file)

if __name__ == "__main__":
    main()
