"""
UnlockTool Direct Standby Listener (Zero Subprocess Delay)
"""

import os
import sys
import time
import datetime
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

log_file = os.path.abspath("scratch/live_brom_debug.log")
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"=== BẮT ĐẦU THEO DÕI LIVE UNLOCKTOOL STANDBY DUMP [{datetime.datetime.now()}] ===\n")

print("=" * 70)
print("⚡ BẮT ĐẦU KÍCH HOẠT UNLOCKTOOL DIRECT STANDBY BROM LISTENER")
print("👉 Tiến trình đang đứng chờ sẵn trên cổng COM (Chế độ --serialport DETECT)...")
print("👉 Bạn hãy TẮT NGUỒN MÁY, Giữ phím TĂNG + GIẢM ÂM LƯỢNG và CẮM CÁP USB...")
print("=" * 70)

MTK_CLIENT_PY = os.path.abspath("tools/mtkclient/mtk.py")
out_img = os.path.abspath("scratch/test_dump_vendor.img")

# Direct Standby mode (No subprocess delay gap after port detection!)
cmd = [sys.executable, MTK_CLIENT_PY, "--serialport", "DETECT", "--crash", "r", "vendor", out_img]
print("Lệnh thực thi:", " ".join(cmd))

proc_mtk = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="ignore",
    cwd=os.path.dirname(MTK_CLIENT_PY)
)

try:
    while True:
        line = proc_mtk.stdout.readline()
        if not line and proc_mtk.poll() is not None:
            break
        if line:
            clean = line.strip()
            if clean:
                now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                log_line = f"[{now_str}] [UNLOCKTOOL BROM] {clean}"
                print(log_line)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
except KeyboardInterrupt:
    proc_mtk.kill()

proc_mtk.poll()
print("=" * 70)
print(f"=== HOÀN TẤT LUỒNG TRUY VẤN VENDOR | LOG ĐÃ LƯU TẠI: {log_file} ===")
print("=" * 70)
