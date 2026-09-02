import os
import struct
import zlib

def main():
    sys_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    xml_name = b"assets/comm_simsettings_volte_config_list.xml"
    
    with open(sys_path, "rb") as f:
        data = f.read()

    pos = 0
    while True:
        idx = data.find(xml_name, pos)
        if idx == -1:
            break
        print(f"\nFound string match at index: {idx}")
        # Search backwards for PK\x03\x04
        pk_idx = data.rfind(b"PK\x03\x04", max(0, idx - 200), idx)
        if pk_idx != -1:
            print(f"  Found PK Header at: {pk_idx}")
            header = data[pk_idx:pk_idx+30]
            magic, ver, flag, method, time_val, date_val, crc, csize, usize, fn_len, extra_len = struct.unpack("<IHHHHHIIIHH", header)
            print(f"  ZIP Local Header: fn_len={fn_len}, extra_len={extra_len}, method={method}, csize={csize}, usize={usize}")
            data_offset = pk_idx + 30 + fn_len + extra_len
            print(f"  Compressed Data Offset: {data_offset}")
            
            # Decompress
            try:
                comp_data = data[data_offset : data_offset + csize]
                decomp = zlib.decompress(comp_data, -zlib.MAX_WBITS)
                print(f"  ✓ DECOMPRESSED SUCCESS! Length: {len(decomp)} bytes")
                print("  Snippet:", decomp[:150].decode('utf-8', errors='ignore'))
            except Exception as e:
                print(f"  Decompress error: {e}")
        pos = idx + len(xml_name)

if __name__ == "__main__":
    main()
