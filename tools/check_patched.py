import os

p = "THU_MUC_RUT_SYSTEM_OPPO/system_patched.bin"
if os.path.exists(p):
    with open(p, "rb") as f:
        data = f.read()
    print("FILE SIZE:", len(data))
    print("COUNT VOLTE_STATUS=1:", data.count(b'volte_status="1"'))
    print("COUNT VOLTE_STATUS=0:", data.count(b'volte_status="0"'))
else:
    print("FILE NOT FOUND")
