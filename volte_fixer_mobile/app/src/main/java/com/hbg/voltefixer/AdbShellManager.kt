package com.hbg.voltefixer

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import rikka.shizuku.Shizuku
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

object AdbShellManager {

    var isWirelessAdbConnected = false

    fun isRootAvailable(): Boolean {
        return try {
            val file = File("/system/xbin/su") 
                if (file.exists()) return true
            val file2 = File("/system/bin/su")
                if (file2.exists()) return true
            val file3 = File("/sbin/su")
                if (file3.exists()) return true
            false
        } catch (e: Throwable) {
            false
        }
    }

    fun isShizukuAvailable(): Boolean {
        return try {
            Shizuku.pingBinder() && Shizuku.checkSelfPermission() == android.content.pm.PackageManager.PERMISSION_GRANTED
        } catch (e: Throwable) {
            false
        }
    }

    suspend fun pairWirelessAdb(port: Int, code: String): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        try {
            val cmd = "adb pair 127.0.0.1:$port $code"
            val process = ProcessBuilder("sh", "-c", cmd).redirectErrorStream(true).start()
            val reader = BufferedReader(InputStreamReader(process.inputStream))
            val output = StringBuilder()
            var line: String?

            while (reader.readLine().also { line = it } != null) {
                output.append(line).append("\n")
            }

            val exitCode = process.waitFor()
            val resultText = output.toString().trim()

            if (resultText.contains("not found", ignoreCase = true) || resultText.contains("inaccessible", ignoreCase = true)) {
                Pair(false, "ROM điện thoại không tích hợp sẵn file nhị phân 'adb'. Vui lòng dùng Shizuku hoặc PC Tool!")
            } else {
                val success = exitCode == 0 || resultText.contains("Successfully paired", ignoreCase = true)
                if (success) {
                    isWirelessAdbConnected = true
                }
                Pair(success, resultText)
            }
        } catch (e: Throwable) {
            Pair(false, e.localizedMessage ?: "Lỗi ghép nối Wi-Fi")
        }
    }

    suspend fun executeCommand(cmd: String): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        try {
            val envp: Array<String>? = null
            val dir: String? = null

            val process = if (isRootAvailable()) {
                val command = arrayOf("su", "-c", cmd)
                ProcessBuilder(*command).redirectErrorStream(true).start()
            } else if (isShizukuAvailable()) {
                val command = arrayOf("sh", "-c", cmd)
                try {
                    val method = Shizuku::class.java.getDeclaredMethod(
                        "newProcess",
                        Array<String>::class.java,
                        Array<String>::class.java,
                        String::class.java
                    )
                    method.isAccessible = true
                    method.invoke(null, command, envp, dir) as Process
                } catch (e: Throwable) {
                    ProcessBuilder("sh", "-c", cmd).redirectErrorStream(true).start()
                }
            } else {
                val command = arrayOf("sh", "-c", cmd)
                ProcessBuilder(*command).redirectErrorStream(true).start()
            }

            val reader = BufferedReader(InputStreamReader(process.inputStream))
            val output = StringBuilder()
            var line: String?

            while (reader.readLine().also { line = it } != null) {
                output.append(line).append("\n")
            }

            val exitCode = process.waitFor()
            Pair(exitCode == 0, output.toString().trim())
        } catch (e: Throwable) {
            Pair(false, e.localizedMessage ?: "Unknown Error")
        }
    }

    suspend fun executeBatchCommands(
        cmds: List<String>,
        onProgress: (String) -> Unit
    ): Boolean = withContext(Dispatchers.IO) {
        var allSuccess = true
        for ((index, cmd) in cmds.withIndex()) {
            val (ok, out) = executeCommand(cmd)
            withContext(Dispatchers.Main) {
                if (ok) {
                    onProgress("✓ [${index + 1}/${cmds.size}] $cmd")
                } else {
                    onProgress("⚠ [${index + 1}/${cmds.size}] $cmd -> $out")
                    allSuccess = false
                }
            }
        }
        allSuccess
    }

    fun applyNativeJavaReflectionFixes(context: Context): List<String> {
        val logs = mutableListOf<String>()
        try {
            // 1. Direct ContentResolver Injection
            val cr = context.contentResolver
            val settingsGlobal = android.provider.Settings.Global::class.java

            val putIntMethod = settingsGlobal.getDeclaredMethod(
                "putInt",
                android.content.ContentResolver::class.java,
                String::class.java,
                Int::class.javaPrimitiveType
            )
            putIntMethod.isAccessible = true

            val keysToInject = listOf(
                "carrier_volte_available_bool",
                "carrier_volte_provisioned_bool",
                "volte_provisioned_sub0",
                "volte_provisioned_sub1",
                "enhanced_4g_mode_enabled",
                "enhanced_4g_mode_enabled_sub0",
                "enhanced_4g_mode_enabled_sub1",
                "enhanced_4g_mode_enabled_sub2",
                "volte_vt_enabled",
                "volte_vt_enabled_sub0",
                "volte_vt_enabled_sub1",
                "voice_call_type",
                "voice_call_type_sub0",
                "voice_call_type_sub1",
                "oppo_volte_switch_style",
                "oppo_vt_switch_style",
                "volte_user_enable",
                "oppo_volte_enable",
                "display_volte_switch",
                "display_vowifi_switch"
            )

            for (key in keysToInject) {
                try {
                    putIntMethod.invoke(null, cr, key, 1)
                    logs.add("✓ Java Reflection ContentResolver: $key = 1")
                } catch (e: Throwable) {
                    // Ignore individual permission failures
                }
            }

            // 2. Telephony ImsManager Reflection
            try {
                val imsManagerClass = Class.forName("com.android.ims.ImsManager")
                val getInstanceMethod = imsManagerClass.getDeclaredMethod("getInstance", Context::class.java, Int::class.javaPrimitiveType)
                getInstanceMethod.isAccessible = true
                val imsManager = getInstanceMethod.invoke(null, context, 0)

                val setAdvanced4GModeMethod = imsManagerClass.getDeclaredMethod("setAdvanced4GModeStatus", Context::class.java, Boolean::class.javaPrimitiveType)
                setAdvanced4GModeMethod.isAccessible = true
                setAdvanced4GModeMethod.invoke(imsManager, context, true)
                logs.add("✓ Java Reflection ImsManager: setAdvanced4GModeStatus(true) thành công!")
            } catch (e: Throwable) {
                logs.add("ℹ Note: Native ImsManager requires system signature or ADB/Root.")
            }
        } catch (e: Throwable) {
            logs.add("⚠ Native Java Reflection Error: ${e.localizedMessage}")
        }
        return logs
    }
}
