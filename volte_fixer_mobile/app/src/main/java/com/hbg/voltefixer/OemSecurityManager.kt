package com.hbg.voltefixer

object OemSecurityManager {

    fun getUnlockCommands(): List<String> {
        val cmds = mutableListOf<String>()

        // 1. OPPO / Realme / ColorOS (Disable permission monitoring & ADB security)
        cmds.add("settings put global disable_permission_monitoring 1")
        cmds.add("settings put secure disable_permission_monitoring 1")
        cmds.add("settings put system disable_permission_monitoring 1")
        cmds.add("setprop persist.sys.oppo.adb.security 0")
        cmds.add("setprop persist.sys.oppo.permission_monitoring 0")
        cmds.add("setprop persist.sys.oplus.permission_monitoring 0")
        cmds.add("setprop persist.sys.coloros.permission_monitoring 0")

        // 2. Xiaomi / Redmi / POCO (Grant ADB security permissions)
        cmds.add("settings put global security_adb_grant_permission 1")
        cmds.add("settings put secure security_adb_grant_permission 1")

        // 3. Vivo / iQOO (ADB Security Input & permission override)
        cmds.add("settings put global adb_security_input 1")
        cmds.add("settings put secure adb_security_input 1")
        cmds.add("setprop persist.vivo.adb.security 0")

        // 4. Auto-grant self secure settings permission
        cmds.add("pm grant com.hbg.voltefixer android.permission.WRITE_SECURE_SETTINGS")

        return cmds
    }
}
