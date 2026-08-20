package com.hbg.voltefixer

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action
        Log.d("VoLTEFixerBoot", "Khởi động thiết bị phát hiện Action: $action")

        if (Intent.ACTION_BOOT_COMPLETED == action ||
            Intent.ACTION_LOCKED_BOOT_COMPLETED == action ||
            "android.intent.action.MY_PACKAGE_REPLACED" == action
        ) {
            CoroutineScope(Dispatchers.IO).launch {
                try {
                    Log.d("VoLTEFixerBoot", "⚡ Đang tự động nạp lại toàn bộ cờ ép bật VoLTE sau khi khởi động...")

                    // 1. Apply native Java reflection fixes
                    AdbShellManager.applyNativeJavaReflectionFixes(context)

                    // 2. Generate and execute full batch commands (VoLTE, VoWiFi, VT, CMW500, APN IMS)
                    val cmds = ImsOverrideManager.getFixAllCommands(
                        volte = true,
                        vowifi = true,
                        vt = true,
                        carrierCheckBypass = true
                    )

                    AdbShellManager.executeBatchCommands(cmds) { msg ->
                        Log.d("VoLTEFixerBoot", msg)
                    }

                    Log.d("VoLTEFixerBoot", "🎉 Nạp lại VoLTE tự động khi khởi động máy hoàn tất!")
                } catch (e: Throwable) {
                    Log.e("VoLTEFixerBoot", "✗ Lỗi nạp VoLTE tự động: ${e.localizedMessage}")
                }
            }
        }
    }
}
