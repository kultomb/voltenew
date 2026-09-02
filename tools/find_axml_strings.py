import os

p = "THU_MUC_RUT_SYSTEM_OPPO/system.bin"
if os.path.exists(p):
    with open(p, "rb") as f:
        data = f.read()

    print("SEARCHING AXML STRINGS IN SYSTEM.BIN:")
    idx = data.find(b"comm_simsettings")
    print("comm_simsettings INDEX:", idx)
    if idx != -1:
        snippet = data[idx:idx+500]
        print("SNIPPET NEAR COMM_SIMSETTINGS:", repr(snippet))

    idx2 = data.find(b"volte_status")
    print("volte_status INDEX:", idx2)
    if idx2 != -1:
        snippet2 = data[idx2:idx2+500]
        print("SNIPPET NEAR VOLTE_STATUS:", repr(snippet2))
