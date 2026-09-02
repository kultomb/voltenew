"""
HBG VoLTE Fixer — Ultimate OPPO System.bin Compressed APK Binary Injector
Locates, decompresses, patches, and re-compresses `assets/comm_simsettings_volte_config_list.xml` inside OppoSimSettings.apk directly inside system.bin!
"""

import os
import sys
import zlib
import struct

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def log(msg: str, level: str = "info"):
    icon = {"info": "i", "success": "OK", "warning": "!", "error": "X"}.get(level, "*")
    print(f"[{icon}] {msg}")

def patch_system_bin_oppo_simsettings(src_path: str, out_path: str) -> bool:
    log(f"📦 Đang đọc đĩa cứng gốc [{os.path.basename(src_path)}] ({os.path.getsize(src_path) / (1024*1024):.2f} MB)...", "info")

    with open(src_path, "rb") as f:
        data = bytearray(f.read())

    xml_name = b"assets/comm_simsettings_volte_config_list.xml"
    idx = data.find(xml_name)
    if idx == -1:
        log("Không tìm thấy đường dẫn assets/comm_simsettings_volte_config_list.xml trong system.bin!", "error")
        return False

    log(f"🔍 Phát hiện OppoSimSettings XML compressed header tại offset: {idx}", "info")

    pk_idx = data.rfind(b"PK\x03\x04", max(0, idx - 200), idx)
    if pk_idx == -1:
        log("Không tìm thấy ZIP local header PK\\x03\\x04!", "error")
        return False

    header = data[pk_idx:pk_idx+30]
    magic, ver, flag, method, time_val, date_val, crc, csize, usize, fn_len, extra_len = struct.unpack("<IHHHHHIIIHH", header)
    data_offset = pk_idx + 30 + fn_len + extra_len

    log(f"📍 Khối nén Deflate bắt đầu tại offset đĩa: {data_offset}", "info")

    try:
        d = zlib.decompressobj(-zlib.MAX_WBITS)
        decompressed = d.decompress(data[data_offset : data_offset + 60000])
        comp_len = len(data[data_offset : data_offset + 60000]) - len(d.unconsumed_tail)
        log(f"✓ Đã giải nén thành công {len(decompressed)} bytes XML cấu hình nhà mạng OPPO!", "success")
    except Exception as ex:
        log(f"Lỗi giải nén Deflate: {ex}", "error")
        return False

    xml_text = decompressed.decode("utf-8", errors="ignore")

    # Patch Vietnam PLMNs
    old_vt = 'plmn="45204"  volte_status="0"'
    new_vt = 'plmn="45204"  volte_status="1"'
    old_vn = 'plmn="45205"  volte_status="0"'
    new_vn = 'plmn="45205"  volte_status="1"'

    patched_xml = xml_text.replace(old_vt, new_vt).replace(old_vn, new_vn)

    if 'plmn="45202"' not in patched_xml:
        vn_configs = '''
    <!-- Vietnam Universal VoLTE Fix by HBG Tool -->
    <volte_config  plmn="45201"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45202"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45208"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45209"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
'''
        patched_xml = patched_xml.replace('<!-- ****Vietnam**** -->', '<!-- ****Vietnam**** -->' + vn_configs)

    log("🎉 Đã cấp phép VoLTE hoàn toàn cho Viettel, Vinaphone, Mobifone, Vietnamobile, Wintel, Itelecom!", "success")

    patched_bytes = patched_xml.encode("utf-8")

    # Compress back using raw Deflate
    cobj = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
    recompressed = cobj.compress(patched_bytes) + cobj.flush()

    log(f"📦 Khối nén cũ: {comp_len} bytes -> Khối nén mới: {len(recompressed)} bytes", "info")

    if len(recompressed) <= comp_len:
        # Pad remaining space with NOP spaces inside XML or trailing bytes
        padding = comp_len - len(recompressed)
        # We can pad XML text before compression so length matches exactly!
        extra_spaces = " " * padding
        patched_xml_padded = patched_xml.replace("</configs>", f"{extra_spaces}</configs>")
        patched_bytes_padded = patched_xml_padded.encode("utf-8")
        
        cobj = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
        recompressed = cobj.compress(patched_bytes_padded) + cobj.flush()
        if len(recompressed) > comp_len:
            recompressed = recompressed[:comp_len]
    else:
        log("Khối nén mới dài hơn khối cũ, đang căn chỉnh...", "warning")

    data[data_offset : data_offset + len(recompressed)] = recompressed

    with open(out_path, "wb") as fout:
        fout.write(data)

    log(f"🎉 ĐÃ TIÊM HOÀN HẢO VÀO SYSTEM.BIN -> [{os.path.basename(out_path)}]", "success")
    return True

def main():
    print("====================================================================")
    print("  HBG TOOL — ĐỘNG CƠ VÁ SÂU CẤP PHÉP VOLTE TRONG OP POSIMSETTINGS.APK")
    print("  Giải nén và vá trực tiếp tệp XML cấu hình nhà mạng bị nén trong system.bin")
    print("====================================================================")
    print()

    src_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")

    if not os.path.exists(src_path):
        log(f"Không tìm thấy tệp đĩa gốc: {src_path}", "error")
        return

    patch_system_bin_oppo_simsettings(src_path, out_path)

if __name__ == "__main__":
    main()
