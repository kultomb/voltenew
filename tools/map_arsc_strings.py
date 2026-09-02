"""
Map exact string index to ResTable entry in resources.arsc
"""
import zipfile
import os
import struct

apk_path = os.path.abspath("rom_framework_dump/rro.apk")
with zipfile.ZipFile(apk_path, "r") as z:
    arsc_data = bytearray(z.read("resources.arsc"))

# Find string pool offset
# String pool header starts at offset 12 (0x0C)
sp_header_off = 12
header_type, header_size, chunk_size, string_count, style_count, flags, strings_start, styles_start = struct.unpack("<HHIIIIII", arsc_data[sp_header_off:sp_header_off+28])

print(f"String count: {string_count}, strings_start: {strings_start}")

# Read string offsets table
offsets_table_start = sp_header_off + 28
string_offsets = []
for i in range(string_count):
    off = struct.unpack("<I", arsc_data[offsets_table_start + i*4 : offsets_table_start + i*4 + 4])[0]
    string_offsets.append(off)

# Find index of "config_device_volte_available" in string pool
actual_strings = []
strings_data_start = sp_header_off + strings_start
volte_string_idx = -1

is_utf8 = (flags & (1 << 8)) != 0

for idx, str_off in enumerate(string_offsets):
    p = strings_data_start + str_off
    if is_utf8:
        # UTF-8: u16 char len, u16 byte len, string bytes
        # read byte len at p+1 (if len < 128)
        length = arsc_data[p+1]
        s_bytes = arsc_data[p+2 : p+2+length]
    else:
        # UTF-16: u16 char len
        length = struct.unpack("<H", arsc_data[p:p+2])[0]
        s_bytes = arsc_data[p+2 : p+2+length*2].decode("utf-16le", errors="ignore").encode("utf-8")
    
    s_name = s_bytes.decode("utf-8", errors="ignore")
    if "config_device_volte_available" in s_name:
        volte_string_idx = idx
        print(f"MATCH! 'config_device_volte_available' is string index #{idx} in String Pool!")
    elif "carrier_volte_available" in s_name:
        print(f"MATCH! 'carrier_volte_available' is string index #{idx} in String Pool!")
    elif "mtk_ct_volte_status" in s_name:
        print(f"MATCH! 'mtk_ct_volte_status' is string index #{idx} in String Pool!")

print("\nFinished mapping string pool!")
