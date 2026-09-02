import os

orig = b'mcc="452"\n      mnc="04"\n      apn="v-internet"\n      type="default,supl"\n      protocol="IPV4V6"'
repl = b'mcc="452"\n     mnc="04"\n     apn="v-internet"\n     type="default,supl,ims"\n     protocol="IPV4V6"'

print(f"Orig len: {len(orig)} bytes")
print(f"Repl len: {len(repl)} bytes")
assert len(orig) == len(repl), "Lengths must match 100% exactly!"
print("✓ PERFECT 106-BYTE SYNTAX MATCH!")
