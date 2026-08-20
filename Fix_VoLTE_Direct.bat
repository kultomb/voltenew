@echo off
title HBG VoLTE and IMS Fixer - Direct ADB 1-Click Tool
color 0A

cd /d "%~dp0"

echo ====================================================================
echo    HBG VoLTE and IMS FIXER TOOL - 1-CLICK TU DONG ADB (KHONG GUI)
echo ====================================================================
echo.

:: 1. Tim duong dan ADB
set "ADB_PATH="
if exist "%~dp0adb\adb.exe" (
    set "ADB_PATH=%~dp0adb\adb.exe"
) else if exist "%~dp0scrcpy\scrcpy-win64-v2.7\adb.exe" (
    set "ADB_PATH=%~dp0scrcpy\scrcpy-win64-v2.7\adb.exe"
) else (
    set "ADB_PATH=adb"
)

echo [1/8] Dang kiem tra va tim duong dan ADB...
echo       Path: "%ADB_PATH%"
echo.

:: 2. Vong lap tu dong nhan dien thiet bi USB ADB
:check_device
echo [2/8] Dang quet va nhan dien thiet bi Android qua USB ADB...
set "DEVICE_ID="

"%ADB_PATH%" devices > "%TEMP%\volte_adb_dev.txt" 2>&1

for /f "tokens=1,2" %%A in ('type "%TEMP%\volte_adb_dev.txt" ^| findstr /v "List of devices"') do (
    if "%%B"=="device" (
        set "DEVICE_ID=%%A"
        goto :device_found
    )
)

echo.
echo [!] KHONG TIM THEY THIET BI ANDROID KET NOI QUA USB!
echo.
echo     Vui long thuc hien cac buoc sau tren dien thoai:
echo     1. Cam cap USB ket noi dien thoai voi may tinh.
echo     2. Vao Cai dat -^> Tuy chon nha phat trien -^> Bat 'Sua loi USB' (USB Debugging).
echo     3. Tich chon 'Luon cho phep' va bam 'Cho phep' khi man hinh dien thoai hoi.
echo.
echo Nhan phim ENTER hoac phim bat ky de quet lai ket noi...
pause > nul
echo.
goto :check_device

:device_found
echo.
echo [OK] DA KET NOI THIET BI THANH CONG! (ID: %DEVICE_ID%)

set "BRAND=Unknown"
set "MODEL=Unknown"
set "ANDROID_VER=Unknown"
set "OPERATOR=Chua ro"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.product.brand > "%TEMP%\v_brand.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_brand.txt) do set "BRAND=%%i"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.product.model > "%TEMP%\v_model.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_model.txt) do set "MODEL=%%i"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.build.version.release > "%TEMP%\v_ver.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_ver.txt) do set "ANDROID_VER=%%i"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop gsm.sim.operator.alpha > "%TEMP%\v_op.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_op.txt) do set "OPERATOR=%%i"

echo     - Hang va Model : %BRAND% %MODEL%
echo     - Phien ban OS  : Android %ANDROID_VER%
echo     - Nha mang SIM  : %OPERATOR%
echo.

echo Nhan ENTER de bat dau qua trinh Ep Bat VoLTE va IMS...
pause > nul
echo.

:: 3. Mo khoa gioi han bao mat ADB cua cac hang
echo [3/8] Dang mo khoa bao mat ADB va cap quyen he thong...
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global disable_permission_monitoring 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put secure disable_permission_monitoring 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put system disable_permission_monitoring 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.adb.security 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.permission_monitoring 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oplus.permission_monitoring 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.coloros.permission_monitoring 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global security_adb_grant_permission 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put secure security_adb_grant_permission 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global adb_security_input 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put secure adb_security_input 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vivo.adb.security 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell pm grant moe.shizuku.privileged.api android.permission.WRITE_SECURE_SETTINGS >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell pm grant com.kyujin.ims.volte android.permission.WRITE_SECURE_SETTINGS >nul 2>&1
echo     [OK] Da thuc hien go bo rao can bao mat ADB.

:: 4. Nap 60+ Tham so System Properties cho VoLTE (Kèm cờ chống Reset trên Android 10)
echo.
echo [4/8] Dang nap tham so cau hinh mang di dong (System Properties)...
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.volte_avail_ovr 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.vt_avail_ovr 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.wfc_avail_ovr 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_mismatch_op 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_enabled_by_default 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.cust.lte_config true
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.calls.on.ims 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.jbims 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vt_hybrid_enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.rat_on 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.vowifi.disable.carrier.check true
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.volte.disable.carrier.check true
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.disable_carrier_check true
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_ignore_sub 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.carrier.volte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte.provider 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.volte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio_oppo_ct_volte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_volte_state 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.oppo.volte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_volte_switch 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo_volte_switch 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.volte_enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.oppo.volte_enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_vt_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.oppo_volte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.oppo_vowifi_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.hvolte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.hvolte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.volte.enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.volte.setting 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_ims_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_dynamic_ims_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.mtk_dynamic_ims_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oem.volte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.region VN
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_state 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.mtk.volte.enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_ct_volte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_volte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.wfc.enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.mtk_wfc_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_vilte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_viwifi_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte.enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_vt 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vivo.volte 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_pro_sub0 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_pro_sub1 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_pro_sub0 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_pro_sub1 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.vowifi 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.vilte_enabled 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.vilte.enable 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vilte_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.calls.on.ims 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte.mode 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.uiccsi 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.ims_registered 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.voice_domain_pref 2
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.voice_domain_pref 2
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.csfb_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.csfb_support 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.disable_csfb 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.disable_csfb 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.ims.simulate 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vilte_downgrade 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_downgrade 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.downgrade 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.downgrade_enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.downgrade_enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte.provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte.provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte_provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.volte_provisioned 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.force_ims_call 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.force_ims_call 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.force_on_dc 1
echo     [OK] Da thiet lap hoan tat System Properties cho dien thoai.

:: 5. Cap nhat Settings Provider DB (Bao gom toan bo bien Sub_ID cho Android 10)
echo.
echo [5/8] Dong bo co VoLTE va dich vu cuoc goi trong Settings DB...
for %%N in (global secure system) do (
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_vt_enabled 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_vt_enabled_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_vt_enabled_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N vt_ims_enabled 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N vt_ims_enabled_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N vt_ims_enabled_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_provisioned 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_provisioned_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_provisioned_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N carrier_volte_provisioned_bool 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N oppo_volte_enable 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N oppo_vowifi_enable 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N volte_call 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N voice_call_type 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N voice_call_type_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N voice_call_type_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N mobivolte_enable 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N carrier_volte_available_bool 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N wfc_ims_enabled 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N wfc_ims_enabled_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N wfc_ims_enabled_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N editable_enhanced_4g_lte_bool 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N enhanced_4g_mode_enabled 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N enhanced_4g_mode_enabled_sub0 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N enhanced_4g_mode_enabled_sub1 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N enhanced_4g_mode_enabled_sub2 1 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell settings put %%N vilte_user_enable 1 >nul 2>&1
)
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global preferred_network_mode 10,10 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global preferred_network_mode1 10 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings put global preferred_network_mode2 10 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell cmd phone set-preferred-network-type 10 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.IMS_SETTING --ei enable 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 1 --ei sim_id 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 1 --ei sim_id 1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.oppo.intent.action.VOLTE_SETTING --ei enable 1 >nul 2>&1
echo     [OK] Da cap nhat va dong bo Settings Provider DB.

:: 6. Nap APN IMS cho tat ca nha mang Viet Nam
echo.
echo [6/8] Nap diem truy cap APN IMS cho cac nha mang Viet Nam...
"%ADB_PATH%" -s %DEVICE_ID% shell content update --uri content://telephony/carriers --bind type:s:default,supl,ims --where "type LIKE '%%default%%' AND type NOT LIKE '%%ims%%'" >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45204 --bind mcc:s:452 --bind mnc:s:04 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45202 --bind mcc:s:452 --bind mnc:s:02 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45201 --bind mcc:s:452 --bind mnc:s:01 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45205 --bind mcc:s:452 --bind mnc:s:05 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45208 --bind mcc:s:452 --bind mnc:s:08 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content insert --uri content://telephony/carriers --bind name:s:IMS Services --bind apn:s:ims --bind type:s:ims,default,supl --bind numeric:s:45209 --bind mcc:s:452 --bind mnc:s:09 --bind bearer_bitmask:s:14 --bind protocol:s:IPv4v6 --bind roaming_protocol:s:IPv4v6 --bind current:i:1 >nul 2>&1
echo     [OK] Da ghep noi cau hinh APN IMS (default,supl,ims).

:: 7. Push classes.dex native runner va Pixel IMS CarrierConfig Overrides
echo.
echo [7/8] Nap CarrierConfig Overrides va Chay khoi tao he thong...
if exist "%~dp0classes.dex" (
    "%ADB_PATH%" -s %DEVICE_ID% push "%~dp0classes.dex" /data/local/tmp/hbg_volte_fixer.dex >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell app_process -Djava.class.path=/data/local/tmp/hbg_volte_fixer.dex /data/local/tmp com.hbg.volte.VolteFixer >nul 2>&1
)

for %%S in (0 1 2 -1) do (
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_volte_available_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_volte_provisioned_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_volte_provisioning_required_bool false >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S editable_enhanced_4g_lte_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S hide_enhanced_4g_lte_bool false >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_wfc_ims_available_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_supports_ss_over_ut_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S show_4g_for_lte_data_icon_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_default_wfc_ims_enabled_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc set-override --sub %%S carrier_vt_available_bool true >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell cmd phone cc notify --sub %%S >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED --ei subscription %%S >nul 2>&1
)
echo     [OK] Da ep nap cong tac VoLTE vao Cai Dat Telephony.

:: Force stop settings apps to refresh UI
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.android.settings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.coloros.wirelesssettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.oplus.wirelesssettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.samsung.android.networksettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.miui.securitycenter >nul 2>&1

:: 8. Reset dich vu song (Airplane Mode toggle)
echo.
echo [8/8] Dang khoi dong lai mang di dong (Che do may bay)...
"%ADB_PATH%" -s %DEVICE_ID% shell cmd connectivity airplane-mode enable >nul 2>&1
ping 127.0.0.1 -n 3 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell cmd connectivity airplane-mode disable >nul 2>&1
echo     [OK] Da khoi dong lai dich vu SIM va VoLTE.

:: Bonus: Kich hoat cong tac dac thu theo hang
if /i "%BRAND%"=="Xiaomi" (
    echo.
    echo [*] Xiaomi / POCO / Redmi: Dang gui ma mo cong tac VoLTE *#*#86583#*#*...
    "%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a android.telephony.action.SECRET_CODE -d secret_code://86583 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell am start -f 0x14000000 -a android.intent.action.DIAL >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell input text "*#*#86583#*#*" >nul 2>&1
) else if /i "%BRAND%"=="Samsung" (
    echo.
    echo [*] Samsung: Dang gui ma ServiceMode *#0011#...
    "%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a android.telephony.action.SECRET_CODE -d secret_code://0011 >nul 2>&1
) else if /i "%BRAND%"=="Oppo" (
    echo.
    echo [*] OPPO / Realme: Dang mo Menu ky thuat EngineerMode...
    "%ADB_PATH%" -s %DEVICE_ID% shell am start -n com.oppo.engineermode/.EngineerMode >nul 2>&1
) else if /i "%BRAND%"=="Realme" (
    echo.
    echo [*] OPPO / Realme: Dang mo Menu ky thuat EngineerMode...
    "%ADB_PATH%" -s %DEVICE_ID% shell am start -n com.oppo.engineermode/.EngineerMode >nul 2>&1
)

echo.
echo ====================================================================
echo   [SUCCESS] DA HOAN THANH KIEN TAO AND EP BAT VoLTE CHO DIEN THOAI!
echo ====================================================================
echo.
echo  Meo:
echo  1. Kiem tra xem bieu tuong VoLTE / 4G HD da xuat hien tren thanh trang thai chua.
echo  2. Neu chua thay, hay vao Cai dat -^> Mang di dong -^> Bat 'Cuoc goi VoLTE'.
echo.
echo Nhan phim ENTER hoac phim bat ky de thoat...
pause
