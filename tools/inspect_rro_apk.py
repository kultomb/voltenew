"""
Inspect framework-res__auto_generated_rro.apk
"""
import zipfile
import os

apk_path = os.path.abspath("rom_framework_dump/rro.apk")
with zipfile.ZipFile(apk_path, "r") as z:
    for name in z.namelist():
        print(f"File in APK: {name}")
        if name == "resources.arsc" or name.endswith(".xml"):
            data = z.read(name)
            # Find string keys inside resources.arsc or axml
            pos = 0
            while True:
                idx = data.find(b"volte", pos)
                if idx == -1:
                    break
                snippet = data[max(0, idx-30):min(len(data), idx+40)]
                clean = "".join([chr(b) if 32 <= b <= 126 else "." for b in snippet])
                print(f"  Match in {name} @ {idx}: {clean}")
                pos = idx + 5
