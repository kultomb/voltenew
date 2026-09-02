"""
Parse all package chunks in resources.arsc
"""
import zipfile
import os
import struct

apk_path = os.path.abspath("rom_framework_dump/rro.apk")
with zipfile.ZipFile(apk_path, "r") as z:
    arsc_data = bytearray(z.read("resources.arsc"))

pos = 0
while pos < len(arsc_data):
    if pos + 8 > len(arsc_data):
        break
    chunk_type, header_size, chunk_size = struct.unpack("<HHI", arsc_data[pos:pos+8])
    print(f"Chunk at {pos}: type=0x{chunk_type:04x}, header_size={header_size}, chunk_size={chunk_size}")
    if chunk_type == 0x0200: # RES_TABLE_PACKAGE_TYPE
        pkg_id = struct.unpack("<I", arsc_data[pos+8:pos+12])[0]
        print(f"  RES_TABLE_PACKAGE_TYPE, pkg_id={pkg_id}")
    elif chunk_type == 0x0001: # RES_STRING_POOL_TYPE
        string_count, style_count, flags, strings_start, styles_start = struct.unpack("<IIIII", arsc_data[pos+8:pos+28])
        print(f"  RES_STRING_POOL_TYPE: strings={string_count}, flags=0x{flags:08x}")
    pos += chunk_size
    if chunk_size == 0:
        break
