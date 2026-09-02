import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    stock_path = r'C:\Users\CMD\Desktop\volte_fixer_tool\scratch\vendor_stock_dump.bin'
    patched_path = r'C:\Users\CMD\Desktop\volte_fixer_tool\scratch\vendor_stock_dump_patched.bin'

    print("==========================================================================")
    print("   🔍 HBG VOLTE FIXER — PHÂN TÍCH TỆP VENDOR_PATCHED CỦA KHÁCH HÀNG")
    print("==========================================================================")

    if not os.path.exists(stock_path) or not os.path.exists(patched_path):
        print("❌ Không tìm thấy tệp vendor_stock_dump.bin hoặc vendor_stock_dump_patched.bin!")
        return

    stock_size = os.path.getsize(stock_path)
    patched_size = os.path.getsize(patched_path)

    print("\n--- [1] KIỂM TRA THÔNG TIN TỆP & KÍCH THƯỚC ---")
    print(f"Tệp Gốc (Stock Dump) : [{os.path.basename(stock_path)}] -> {stock_size:,} bytes")
    print(f"Tệp Đã Vá (User Patch): [{os.path.basename(patched_path)}] -> {patched_size:,} bytes")
    print(f"Giữ nguyên kích thước 100%: {'✅ HỢP LỆ' if stock_size == patched_size else '❌ KÍCH THƯỚC SAI'}")

    with open(stock_path, 'rb') as f:
        sdata = f.read()

    with open(patched_path, 'rb') as f:
        pdata = f.read()

    print("\n--- [2] EXT4 SUPERBLOCK INTEGRITY ---")
    magic = pdata[1080:1082].hex()
    print(f"ext4 Magic tại offset 1080: [0x{magic}] -> {'✅ HỢP LỆ (0x53ef)' if magic == '53ef' else '❌ LỖI'}")

    print("\n--- [3] PHÂN TÍCH CÁC QUY TẮC VÁ TIÊM BẢN VÁ CỦA BẠN (PATCHED VS STOCK) ---")
    check_props = [
        (b"persist.vendor.mtk_ct_volte_support=3", b"persist.vendor.mtk_ct_volte_support=1", "MTK CT VoLTE (Khóa SIM CT=3 -> Mở tất cả nhà mạng=1)"),
        (b"persist.vendor.mtk.volte.enable=1", b"persist.vendor.mtk.volte.enable=3", "MTK VoLTE Enable (Gốc=1 -> Dual Hardware Active=3)"),
        (b"persist.vendor.mtk.volte.enable=2", b"persist.vendor.mtk.volte.enable=3", "MTK VoLTE Enable (Gốc=2 -> Dual Hardware Active=3)"),
        (b"persist.vendor.radio.volte_state=1", b"persist.vendor.radio.volte_state=3", "Radio VoLTE State (Gốc=1 -> Hardware Active=3)"),
        (b"persist.vendor.radio.volte_state=2", b"persist.vendor.radio.volte_state=3", "Radio VoLTE State (Gốc=2 -> Hardware Active=3)"),
        (b"persist.vendor.mtk_dynamic_ims_switch=1", b"persist.vendor.mtk_dynamic_ims_switch=0", "MTK Dynamic IMS Switch (Gốc=1 -> Bỏ qua giới hạn SIM=0)"),
        (b"persist.vendor.volte_support=1", None, "Vendor VoLTE Support Active"),
        (b"GAQ_OPPO_MTK_VoLTE_Overlay.apk", None, "Tệp CarrierConfig Static RRO Overlay"),
        (b"gaq_oppo_mtk_volte.rc", None, "Tệp Init Script tự động nạp khi khởi động")
    ]

    for old_b, new_b, desc in check_props:
        scnt = sdata.count(old_b)
        pcnt = pdata.count(new_b) if new_b else pdata.count(old_b)
        
        if new_b:
            print(f"  • {desc:<60}:")
            print(f"     Gốc [{old_b.decode('latin1')}]: {scnt} vị trí -> Đã vá [{new_b.decode('latin1')}]: {pcnt} vị trí {'✅ ĐÃ TIÊM' if pcnt > 0 else '⚠ CHƯA TIÊM'}")
        else:
            cnt = pdata.count(old_b)
            print(f"  • {desc:<60}: {'✅ ĐÃ CÓ (' + str(cnt) + ' vị trí)' if cnt > 0 else '❌ CHƯA CÓ TRONG VENDOR'}")

    print("\n==========================================================================")

if __name__ == "__main__":
    main()
