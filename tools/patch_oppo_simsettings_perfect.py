import zlib
import os
import zipfile

def main():
    sys_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")

    print(f"Reading system.bin ({os.path.getsize(sys_path) / (1024*1024):.2f} MB)...")

    # Target offset of assets/comm_simsettings_volte_config_list.xml
    header_offset = 3340217244
    stream_offset = 3340217319

    with open(sys_path, "rb") as f:
        f.seek(stream_offset)
        raw_comp = f.read(5000)

    d = zlib.decompressobj(-zlib.MAX_WBITS)
    decompressed = d.decompress(raw_comp)
    print(f"✓ Decompressed {len(decompressed)} bytes of assets/comm_simsettings_volte_config_list.xml!")

    decomp_str = decompressed.decode("utf-8")
    
    # Enable VoLTE for Viettel (45204) and Vietnamobile (45205) and add Vinaphone (45202), Mobifone (45201), Itelecom (45208), Wintel (45209)
    p1 = 'plmn="45204"  volte_status="0"'
    r1 = 'plmn="45204"  volte_status="1"'
    p2 = 'plmn="45205"  volte_status="0"'
    r2 = 'plmn="45205"  volte_status="1"'

    patched_xml = decomp_str.replace(p1, r1).replace(p2, r2)
    
    if 'plmn="45202"' not in patched_xml:
        vn_additions = '''
    <!-- Vietnam Networks (Vinaphone, Mobifone, Viettel, Vietnamobile, Itelecom, Wintel) -->
    <volte_config  plmn="45201"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45202"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45208"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
    <volte_config  plmn="45209"  volte_status="1"  volte_visible="1" vowifi_status="1"  vowifi_visible="1" vowifi_preferred_mode="2" vowifi_roaming_preferred_mode="2"/>
'''
        patched_xml = patched_xml.replace('<!-- ****Vietnam**** -->', '<!-- ****Vietnam**** -->' + vn_additions)

    print("\n=== VERIFYING PATCHED VIETNAM ENTRIES IN XML ===")
    for line in patched_xml.splitlines():
        if '452' in line:
            print("  ", line.strip())

    print("\n✓ XML modification complete!")

if __name__ == "__main__":
    main()
