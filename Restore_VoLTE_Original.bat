@echo off
title HBG VoLTE and IMS Fixer - Restore Original State Tool
color 0C

cd /d "%~dp0"

echo ====================================================================
echo    HBG VoLTE and IMS FIXER - KHOI PHUC TRANG THAI BAN DAU (RESET)
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

echo [1/8] Dang kiem tra duong dan ADB...
echo       Path: "%ADB_PATH%"
echo.

:: 2. Quet thiet bi USB ADB
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
echo     Vui long cam cap USB va bat 'Sua loi USB' (USB Debugging).
echo.
echo Nhan phim ENTER de quet lai...
pause > nul
echo.
goto :check_device

:device_found
echo.
echo [OK] DA KET NOI THIET BI THANH CONG! (ID: %DEVICE_ID%)

set "BRAND=Unknown"
set "MODEL=Unknown"
set "ANDROID_VER=Unknown"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.product.brand > "%TEMP%\v_brand.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_brand.txt) do set "BRAND=%%i"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.product.model > "%TEMP%\v_model.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_model.txt) do set "MODEL=%%i"

"%ADB_PATH%" -s %DEVICE_ID% shell getprop ro.build.version.release > "%TEMP%\v_ver.txt" 2>&1
for /f "delims=" %%i in (%TEMP%\v_ver.txt) do set "ANDROID_VER=%%i"

echo     - Hang va Model : %BRAND% %MODEL%
echo     - Phien ban OS  : Android %ANDROID_VER%
echo.

echo CANH BAO: Tien trinh nay se RESTORE/XOA CONG TAC VoLTE VE TRANG THAI AN/TAT GOC!
echo Nhan ENTER de bat dau Khoi Phuc ve trang thai ban dau...
pause > nul
echo.

:: 3. Chay Native DEX Runner voi tham so RESET
echo [3/8] Chay Native Java Runner khoi phuc CarrierConfig (enable=false, hide=true)...
if exist "%~dp0classes.dex" (
    "%ADB_PATH%" -s %DEVICE_ID% push "%~dp0classes.dex" /data/local/tmp/hbg_volte_fixer.dex >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell app_process -Djava.class.path=/data/local/tmp/hbg_volte_fixer.dex /data/local/tmp com.hbg.volte.VolteFixer reset
)
echo     [OK] Da reset CarrierConfig qua AIDL Binder IPC.

:: 4. Reset System Properties ve 0 / false
echo.
echo [4/8] Dang reset System Properties ve trang thai an/tat...
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.volte_avail_ovr 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.vt_avail_ovr 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.wfc_avail_ovr 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_mismatch_op 1
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_enabled_by_default 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.cust.lte_config false
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.calls.on.ims 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.jbims 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.vowifi.disable.carrier.check false
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.volte.disable.carrier.check false
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.disable_carrier_check false
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.carrier.volte 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte.provider 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.volte 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio_oppo_ct_volte_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_volte_state 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.oppo.volte 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_volte_switch 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo_volte_switch 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.volte_enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.oppo.volte_enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.oppo_vt_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.oppo_volte_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.oppo_vowifi_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.volte.enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.volte.setting 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_ims_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_dynamic_ims_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.mtk_dynamic_ims_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oem.volte 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_state 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.mtk.volte.enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_ct_volte_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk_volte_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.mtk.wfc.enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte.enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_vt 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vivo.volte 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.oppo.vowifi 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.vilte_enabled 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.vilte.enable 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.vilte_support 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.calls.on.ims 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte.mode 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte_provisioned 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte_provisioned 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.radio.volte.provisioned 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.vendor.radio.volte.provisioned 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.sys.volte_provisioned 0
"%ADB_PATH%" -s %DEVICE_ID% shell setprop persist.dbg.volte_provisioned 0
echo     [OK] Da khoi phuc System Properties.

:: 5. Reset Broadcast & Settings DB
echo.
echo [5/8] Gui Broadcast va reset Settings Provider DB...
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.oppo.intent.action.VOLTE_SETTING --ei enable 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.IMS_SETTING --ei enable 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 0 --ei sim_id 0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 0 --ei sim_id 1 >nul 2>&1

"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global volte_vt_enabled >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global vt_ims_enabled >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global volte_provisioned >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete secure volte_provisioned >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system volte_provisioned >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global carrier_volte_provisioned_bool >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system oppo_volte_enable >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global oppo_volte_enable >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system oppo_vowifi_enable >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global oppo_vowifi_enable >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system volte_call >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global volte_call >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global mobivolte_enable >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global carrier_volte_available_bool >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global wfc_ims_enabled >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global enhanced_4g_mode_enabled >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system enhanced_4g_mode_enabled >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global enhanced_4g_mode_enabled_sub0 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete global enhanced_4g_mode_enabled_sub1 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell settings delete system vilte_user_enable >nul 2>&1
echo     [OK] Da reset Broadcast va Settings Provider DB.

:: 6. Xoa APN IMS da nap va don dep tep tin tam
echo.
echo [6/8] Xoa bo diem truy cap APN IMS va tep tin khoi tao tam...
"%ADB_PATH%" -s %DEVICE_ID% shell content delete --uri content://telephony/carriers --where "apn='ims' OR name='IMS Services'" >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell content update --uri content://telephony/carriers --bind type:s:default,supl --where "type LIKE '%%ims%%'" >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell rm /data/local/tmp/hbg_volte_fixer.dex >nul 2>&1
echo     [OK] Da don dep APN IMS va tep tin he thong.

:: 7. Gui ma khoa cong tac theo hang (Vidu Xiaomi carrier check)
echo.
echo [7/8] Gui ma khoa/an cong tac VoLTE theo hang...
if /i "%BRAND%"=="Xiaomi" (
    echo [*] Xiaomi / POCO / Redmi: Gui lai ma *#*#86583#*#* de bat lai Carrier Check (An cong tac VoLTE)...
    "%ADB_PATH%" -s %DEVICE_ID% shell am broadcast -a android.telephony.action.SECRET_CODE -d secret_code://86583 >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell am start -f 0x14000000 -a android.intent.action.DIAL >nul 2>&1
    "%ADB_PATH%" -s %DEVICE_ID% shell input text "*#*#86583#*#*" >nul 2>&1
)

:: 8. Force Stop Cai Dat & Reset dich vu song (Airplane mode toggle)
echo.
echo [8/8] Dang khoi dong lai ung dung Cai dat va mang di dong...
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.android.settings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.coloros.wirelesssettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.oplus.wirelesssettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.samsung.android.networksettings >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.miui.securitycenter >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell am force-stop com.android.phone >nul 2>&1

"%ADB_PATH%" -s %DEVICE_ID% shell cmd connectivity airplane-mode enable >nul 2>&1
ping 127.0.0.1 -n 3 >nul 2>&1
"%ADB_PATH%" -s %DEVICE_ID% shell cmd connectivity airplane-mode disable >nul 2>&1

echo.
echo ====================================================================
echo   [RESTORE COMPLETE] DA AN VA TAT TOAN BO CONG TAC VoLTE BAN DAU!
echo ====================================================================
echo.
echo  Bay gio ban co the kiem tra lai Cai Dat -> Mang di dong (Cong tac Cuoc goi VoLTE / 4G HD da bi an/tat).
echo  De test lai tool, hay mo lai file Fix_VoLTE_Direct.bat!
echo.
echo Nhan phim ENTER hoac phim bat ky de thoat...
pause
