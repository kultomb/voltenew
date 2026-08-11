Dong goi file cai dat HBG AdBlocker
===================================

1. Dat icons\app_icon.ico (bat buoc — icon file .exe va Setup).

2. Portable EXE (khong can Inno Setup):
   Chay:  build_exe.bat
   Ket qua: dist\releases\HBGAdBlocker{version}.exe

3. EXE + file Setup cai dat (khuyen nghi phat hanh):
   - Cai Inno Setup 6: https://jrsoftware.org/isinfo.php
   - Chay:  build_installer.bat
   Ket qua:
     dist\releases\HBGAdBlocker{version}.exe          (portable)
     dist\releases\HBGAdBlocker_Setup_v{version}.exe  (cai dat)

Tuy chon — nhung ADB vao EXE:
   - Giai nen platform-tools vao thu muc platform-tools\, hoac
   - Dat platform-tools.zip canh HBGAdBlocker.py
   Neu khong co, app tim adb trong PATH he thong.
