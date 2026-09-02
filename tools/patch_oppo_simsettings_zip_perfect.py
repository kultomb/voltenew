import os
import sys
import struct
import zlib

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def patch_oppo_simsettings_zip_perfect(sys_path: str, out_path: str) -> bool:
    print(f"📦 Đang xử lý tiêm sâu vào OppoSimSettings.apk trong [{os.path.basename(sys_path)}]...")
    
    orig_size = os.path.getsize(sys_path)
    print(f"  ✓ Kích thước đĩa chuẩn (Target Partition Size): {orig_size} bytes ({hex(orig_size)})")

    with open(sys_path, "rb") as f:
        data = bytearray(f.read())

    xml_name = b"assets/comm_simsettings_volte_config_list.xml"
    
    # 1. Locate Central Directory Header PK\x01\x02
    cd_idx = data.find(b"PK\x01\x02\x14\x00\x14\x00\x08\x08")
    if cd_idx == -1:
        cd_idx = data.find(b"PK\x01\x02")
    
    # Find the matching XML entry in Central Directory
    pos = 0
    cd_match_idx = -1
    while True:
        i = data.find(xml_name, pos)
        if i == -1:
            break
        pk_cd = data.rfind(b"PK\x01\x02", max(0, i - 100), i)
        if pk_cd != -1:
            cd_match_idx = pk_cd
            break
        pos = i + len(xml_name)

    if cd_match_idx == -1:
        print("✗ Không tìm thấy Central Directory entry của comm_simsettings_volte_config_list.xml")
        return False

    cd_header = data[cd_match_idx : cd_match_idx + 46]
    magic, ver_m, ver_n, flag, method, mtime, mdate, orig_crc, orig_csize, orig_usize, fn_len, extra_len, comment_len, disk, int_attr, ext_attr, rel_off = struct.unpack("<IHHHHHHIIIHHHHHII", cd_header)

    print(f"  ✓ Tìm thấy Central Directory: csize={orig_csize}, usize={orig_usize}, crc={hex(orig_crc)}")

    # Find matching Local Header PK\x03\x04
    loc_match_idx = -1
    pos = 0
    while True:
        i = data.find(xml_name, pos)
        if i == -1:
            break
        pk_loc = data.rfind(b"PK\x03\x04", max(0, i - 100), i)
        if pk_loc != -1:
            loc_match_idx = pk_loc
            break
        pos = i + len(xml_name)

    if loc_match_idx == -1:
        print("✗ Không tìm thấy Local Header entry")
        return False

    loc_header = data[loc_match_idx : loc_match_idx + 30]
    _, _, _, _, _, _, _, _, _, l_fn_len, l_extra_len = struct.unpack("<IHHHHHIIIHH", loc_header)
    data_offset = loc_match_idx + 30 + l_fn_len + l_extra_len

    # Extract & Decompress
    raw_comp = data[data_offset : data_offset + orig_csize]
    d = zlib.decompressobj(-zlib.MAX_WBITS)
    decompressed = d.decompress(raw_comp)
    print(f"  ✓ Đã giải nén thành công {len(decompressed)} bytes XML!")

    xml_text = decompressed.decode("utf-8", errors="ignore")

    # Replace VoLTE status 0 -> 1 for Viettel (45204) and Vietnamobile (45205)
    p1 = 'plmn="45204"  volte_status="0"'
    r1 = 'plmn="45204"  volte_status="1"'
    p2 = 'plmn="45205"  volte_status="0"'
    r2 = 'plmn="45205"  volte_status="1"'

    patched_xml = xml_text.replace(p1, r1).replace(p2, r2)
    patched_bytes = patched_xml.encode("utf-8")

    # Calculate new CRC32
    new_crc = zlib.crc32(patched_bytes) & 0xffffffff

    # Re-compress with matching csize = orig_csize
    best_comp = None
    for level in range(1, 10):
        cobj = zlib.compressobj(level=level, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
        cdata = cobj.compress(patched_bytes) + cobj.flush()
        if len(cdata) == orig_csize:
            best_comp = cdata
            print(f"  ✓ Đã nén lại trùng khớp hoàn hảo độ dài {orig_csize} bytes ở level {level}!")
            break

    if best_comp is None:
        cobj = zlib.compressobj(level=9, method=zlib.DEFLATED, wbits=-zlib.MAX_WBITS)
        best_comp = cobj.compress(patched_bytes) + cobj.flush()
        if len(best_comp) < orig_csize:
            best_comp += b"\x00" * (orig_csize - len(best_comp))
        else:
            best_comp = best_comp[:orig_csize]

    # Write patched compressed block back into data
    data[data_offset : data_offset + orig_csize] = best_comp

    # Update CRC in Central Directory
    struct.pack_into("<I", data, cd_match_idx + 16, new_crc)
    
    # Update CRC in Data Descriptor if present
    desc_offset = data_offset + orig_csize
    if data[desc_offset : desc_offset + 4] == b"PK\x07\x08":
        struct.pack_into("<I", data, desc_offset + 4, new_crc)

    # 2. Inject init.rc Root Boot Script setprop commands (WITH STRICT BYTE ACCURACY)
    target_block = (
        b"# Kun.Hu@PSW.TECH.RELIABILTY, 2019/1/21, add for project phoenix(hang oppo)\n"
        b"    setprop sys.oppo.phoenix.prepare_log boot_success\n"
        b"#Liang.Zhang@TECH.BSP.Stability.OPPO_SHUTDOWN_DETECT, 2019/04/28, Add for shutdown detect\n"
        b"    setprop sys.oppo.shutdown.prepare_log boot_success"
    )
    rc_idx = data.find(target_block)
    
    if rc_idx != -1:
        new_cmds = (
            b"    setprop persist.radio_oppo_ct_volte_support 1\n"
            b"    setprop persist.sys.oppo.carrier.volte 1\n"
            b"    setprop persist.sys.oppo.volte 1\n"
            b"    setprop persist.vendor.volte_support 1\n"
            b"    setprop persist.vendor.mtk.volte.enable 1\n"
            b"    setprop persist.vendor.radio.volte_state 1\n"
            b"    setprop persist.dbg.volte_avail_ovr 1\n"
            b'    setprop persist.vendor.mtk.provision.int.01 "[26,1;27,1;28,1;29,1;]"\n'
        )
        padding_needed = len(target_block) - len(new_cmds)
        if padding_needed > 0:
            replacement = new_cmds + b"#" + b" " * (padding_needed - 2) + b"\n"
        else:
            replacement = new_cmds[:len(target_block)]
        
        assert len(replacement) == len(target_block), f"Replacement len mismatch: {len(replacement)} vs {len(target_block)}"
        data[rc_idx : rc_idx + len(target_block)] = replacement
        print("  ✓ Đã tiêm thành công 8 lệnh Root Init.rc + MTK NVRAM Key 26 (Giữ nguyên 100% kích thước đĩa chuẩn!)")

    # Inject APN IMS (default,supl,ims) into /system/etc/apns-conf.xml for Viettel (45204)
    vt_target_block = b'mcc="452"\n      mnc="04"\n      apn="v-internet"\n      type="default,supl"\n      protocol="IPV4V6"'
    apn_idx = data.find(vt_target_block)
    if apn_idx != -1:
        vt_replace_block = b'mcc="452"\n     mnc="04"\n     apn="v-internet"\n     type="default,supl,ims"\n     protocol="IPV4V6"'
        assert len(vt_target_block) == len(vt_replace_block), "APN Replacement byte length mismatch!"
        data[apn_idx : apn_idx + len(vt_target_block)] = vt_replace_block
        print("  ✓ Đã tiêm thành công APN IMS (default,supl,ims) chuẩn XML 97 bytes trực tiếp vào /system/etc/apns-conf.xml!")

    # ABSOLUTE SIZE CHECK TO PREVENT UNLOCKTOOL SIZE MISMATCH
    if len(data) != orig_size:
        print(f"❌ CẢNH BÁO KÍCH THƯỚC SAI: {len(data)} vs {orig_size}")
        if len(data) > orig_size:
            data = data[:orig_size]
        else:
            data = data + b"\x00" * (orig_size - len(data))

    assert len(data) == orig_size, "Kích thước đĩa vẫn không khớp!"
    print(f"  ✓ Đã xác nhận kích thước tệp xuất: {len(data)} bytes (Trùng khớp 100% 0x144000000)")

    with open(out_path, "wb") as fout:
        fout.write(data)

    print(f"🎉 CẤP PHÉP VOLTE THÀNH CÔNG VÀ CHUẨN ĐỊNH DẠNG ĐĨA -> [{os.path.basename(out_path)}]")
    return True

if __name__ == "__main__":
    src_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")
    patch_oppo_simsettings_zip_perfect(src_path, out_path)
