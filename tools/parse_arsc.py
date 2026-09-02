"""
Parse resources.arsc in rro.apk to find exact boolean values
"""
import zipfile
import os

apk_path = os.path.abspath("rom_framework_dump/rro.apk")
with zipfile.ZipFile(apk_path, "r") as z:
    arsc_data = z.read("resources.arsc")

print(f"resources.arsc size: {len(arsc_data)} bytes")

# Find "config_device_volte_available" in arsc_data
target_str = b"config_device_volte_available"
idx = arsc_data.find(target_str)
print(f"String 'config_device_volte_available' index in arsc: {idx}")

if idx != -1:
    # Print 200 bytes around string index
    snippet = arsc_data[max(0, idx-50):min(len(arsc_data), idx+len(target_str)+150)]
    print(f"Hex snippet around string:\n{snippet.hex()}")
    clean = "".join([chr(b) if 32 <= b <= 126 else "." for b in snippet])
    print(f"Text snippet:\n{clean}")

# Find boolean values in arsc_data (0x00 0x00 0x05 0x08 / TYPE_INT_BOOLEAN)
# Res_value struct in resources.arsc: uint16_t size (0x0008), uint8_t res0, uint8_t dataType (0x12 = TYPE_INT_BOOLEAN), uint32_t data (0x00000000 = false, 0xffffffff or 0x00000001 = true)
pos = 0
bool_entries = []
while True:
    # 08 00 00 12 (size=8, res0=0, dataType=0x12 TYPE_INT_BOOLEAN)
    idx_b = arsc_data.find(b"\x08\x00\x00\x12", pos)
    if idx_b == -1:
        break
    val_bytes = arsc_data[idx_b+4 : idx_b+8]
    val_int = int.from_bytes(val_bytes, "little")
    bool_entries.append({"offset": idx_b, "val_hex": val_bytes.hex(), "val_int": val_int})
    pos = idx_b + 8

print(f"\nFound {len(bool_entries)} TYPE_INT_BOOLEAN (0x12) entries in resources.arsc:")
for b in bool_entries[:15]:
    print(f"  Offset {b['offset']}: val = {b['val_int']} (hex: {b['val_hex']})")
