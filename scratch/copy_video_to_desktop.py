import os
import shutil
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    src_video = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\extracted_media\huong_dan_volte_oppo_a31.mp4"
    dst_desktop = r"C:\Users\CMD\Desktop\Video_Huong_Dan_VoLTE_OPPO_A31.mp4"
    dst_workspace = r"C:\Users\CMD\Desktop\volte_fixer_tool\Video_Huong_Dan_VoLTE_OPPO_A31.mp4"

    if os.path.exists(src_video):
        print(f"📦 Đang sao chép Video Hướng Dẫn ({os.path.getsize(src_video):,} bytes)...")
        shutil.copy2(src_video, dst_desktop)
        shutil.copy2(src_video, dst_workspace)
        print("\n🎉 ĐÃ SAO CHÉP VIDEO RA DESKTOP VÀ WORKSPACE:")
        print(f"  👉 Desktop: {dst_desktop}")
        print(f"  👉 Workspace: {dst_workspace}")

if __name__ == "__main__":
    main()
