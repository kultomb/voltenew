import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    video_path = r"C:\Users\CMD\Desktop\Video_Huong_Dan_VoLTE_OPPO_A31.mp4"
    if os.path.exists(video_path):
        print(f"Đang mở Video Hướng Dẫn cho bạn xem: {video_path}")
        os.startfile(video_path)

if __name__ == "__main__":
    main()
