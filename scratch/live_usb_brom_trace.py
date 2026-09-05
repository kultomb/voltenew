"""
Real-time Millisecond Windows USB & COM Port Live Trace Tool for MTK BROM Handshake Analysis
"""

import sys
import os
import time
import datetime
import serial.tools.list_ports

sys.stdout.reconfigure(encoding='utf-8')

log_file = os.path.abspath("scratch/live_usb_trace.log")
with open(log_file, "w", encoding="utf-8") as f:
    f.write(f"=== BẮT ĐẦU THEO DÕI CỔNG USB / COM REAL-TIME [{datetime.datetime.now()}] ===\n")

print("=" * 70)
print("⚡ BẮT ĐẦU GIÁM SÁT REAL-TIME CỔNG USB / COM PORT (ĐỘ CHÍNH XÁC 10MS)")
print("👉 Hãy cắm cáp USB (Tắt nguồn máy, giữ phím Tăng + Giảm âm lượng)...")
print("=" * 70)

seen_ports = {}

try:
    start_time = time.time()
    last_heartbeat = 0
    while time.time() - start_time < 120.0:  # Listen for 120 seconds
        elapsed = time.time() - start_time
        if elapsed - last_heartbeat >= 10.0:
            last_heartbeat = elapsed
            remaining = 120.0 - elapsed
            hb_msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⏳ Đang tích cực chờ cắm cáp USB (Thời gian còn lại: {remaining:.0f}s)..."
            print(hb_msg)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(hb_msg + "\n")

        current_ports = {p.device: p for p in serial.tools.list_ports.comports()}
        
        # Check newly connected ports
        for dev, p in current_ports.items():
            if dev not in seen_ports:
                now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                desc = p.description or "N/A"
                hwid = p.hwid or "N/A"
                vid = f"{p.vid:04X}" if p.vid else "N/A"
                pid = f"{p.pid:04X}" if p.pid else "N/A"
                
                info_line = f"[{now_str}] 🔌 CẮM CÁP MỚI -> CỔNG: {dev} | Tên: {desc} | VID:{vid} PID:{pid} | HWID: {hwid}"
                print(info_line)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(info_line + "\n")
                    
                seen_ports[dev] = (p, time.time())
                
        # Check disconnected ports
        removed_ports = [dev for dev in seen_ports if dev not in current_ports]
        for dev in removed_ports:
            now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            p, connect_time = seen_ports[dev]
            duration = time.time() - connect_time
            desc = p.description or "N/A"
            
            disconnect_line = f"[{now_str}] ❌ ĐÃ RÚT CÁP / NGẮT KẾT NỐI -> CỔNG: {dev} | Tên: {desc} | Thời gian duy trì: {duration:.2f} giây"
            print(disconnect_line)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(disconnect_line + "\n")
                
            del seen_ports[dev]
            
        time.sleep(0.01)  # 10ms high precision sampling
        
except KeyboardInterrupt:
    print("\nĐã dừng theo dõi.")

print("=" * 70)
print(f"✓ Hoàn tất theo dõi. Nhật ký đã lưu tại: {log_file}")
print("=" * 70)
