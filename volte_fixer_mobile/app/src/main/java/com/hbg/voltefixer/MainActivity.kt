package com.hbg.voltefixer

import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.hbg.voltefixer.databinding.ActivityMainBinding
import kotlinx.coroutines.launch
import rikka.shizuku.Shizuku

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val SHIZUKU_PERMISSION_REQUEST_CODE = 1001

    private val binderReceivedListener = Shizuku.OnBinderReceivedListener {
        checkShizukuStatus()
    }

    private val binderDeadListener = Shizuku.OnBinderDeadListener {
        log("⚠ Shizuku Server ngắt kết nối.")
    }

    private val requestPermissionResultListener = Shizuku.OnRequestPermissionResultListener { requestCode, grantResult ->
        if (requestCode == SHIZUKU_PERMISSION_REQUEST_CODE) {
            if (grantResult == PackageManager.PERMISSION_GRANTED) {
                log("🎉 ĐÃ ĐƯỢC CẤP QUYỀN SHIZUKU THÀNH CÔNG!")
                binding.tvStatus.text = "● Trạng thái: Đã kết nối ADB Shell (UID 2000)"
            } else {
                log("⚠ Bạn đã từ chối cấp quyền Shizuku.")
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        Shizuku.addBinderReceivedListener(binderReceivedListener)
        Shizuku.addBinderDeadListener(binderDeadListener)
        Shizuku.addRequestPermissionResultListener(requestPermissionResultListener)

        setupListeners()
        checkShizukuStatus()

        log("=== HBG VoLTE & IMS Fixer Mobile v1.0 ===")
        log("Hỗ trợ Android 8.0/8.1 (OPPO A5s) đến Android 14+")
    }

    override fun onDestroy() {
        super.onDestroy()
        Shizuku.removeBinderReceivedListener(binderReceivedListener)
        Shizuku.removeBinderDeadListener(binderDeadListener)
        Shizuku.removeRequestPermissionResultListener(requestPermissionResultListener)
    }

    private fun checkShizukuStatus() {
        try {
            if (Shizuku.pingBinder()) {
                if (Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED) {
                    log("✓ Đã kết nối Shizuku Shell Daemon (UID 2000 - ADB Privileges)!")
                    binding.tvStatus.text = "● Trạng thái: Đã kết nối ADB Shell (UID 2000)"
                } else {
                    log("⚡ Tự động gửi yêu cầu cấp quyền Shizuku...")
                    Shizuku.requestPermission(SHIZUKU_PERMISSION_REQUEST_CODE)
                }
            } else {
                log("⚠ Chưa phát hiện Shizuku Server. Hãy bật ứng dụng Shizuku 1 lần!")
            }
        } catch (e: Throwable) {
            log("⚠ Lưu ý: Bạn có thể bật ứng dụng Shizuku.")
        }
    }

    private fun setupListeners() {
        binding.btnFixAll.setOnClickListener {
            runFixAll()
        }
        binding.btnDonate.setOnClickListener {
            showDonateDialog()
        }
    }

    private fun showDonateDialog() {
        val imageView = android.widget.ImageView(this).apply {
            setImageResource(R.drawable.donate_qr)
            adjustViewBounds = true
            setPadding(32, 24, 32, 24)
        }

        AlertDialog.Builder(this)
            .setTitle("❤️ Hộp Sữa Cho Con Gái Tác Giả 🍼")
            .setMessage("Nếu ứng dụng đã giúp bạn kích hoạt VoLTE thành công và gọi thoại mượt mà, tiếc gì một hộp sữa nho nhỏ cho bé đúng không ạ? 🥰\n\nMọi ủng hộ VietQR MB Bank của bạn là động lực rất lớn để tác giả tiếp tục nâng cấp phần mềm hoàn toàn miễn phí!")
            .setView(imageView)
            .setPositiveButton("Cảm ơn bạn! ❤️") { dialog, _ -> dialog.dismiss() }
            .show()
    }

    private fun runFixAll() {
        binding.btnFixAll.isEnabled = false
        log("⚡ Bắt đầu tiến trình kích hoạt VoLTE 1-Click...")

        lifecycleScope.launch {
            val isVolte = true
            val isVowifi = true
            val isVt = true
            val isCarrierCheck = true

            // Execute Native Java Reflection Fixes first
            val nativeLogs = AdbShellManager.applyNativeJavaReflectionFixes(this@MainActivity)
            for (nativeLog in nativeLogs) {
                log(nativeLog)
            }

            val cmds = ImsOverrideManager.getFixAllCommands(isVolte, isVowifi, isVt, isCarrierCheck)
            AdbShellManager.executeBatchCommands(cmds) { msg ->
                log(msg)
            }

            log("🎉 HOÀN THÀNH: Đã phát bộ lệnh kích hoạt VoLTE siêu mạnh (Root/Shizuku/Reflection)!")
            binding.tvStatus.text = "● Trạng thái: Đã kích hoạt VoLTE thành công!"
            binding.btnFixAll.isEnabled = true
        }
    }

    private fun log(message: String) {
        android.util.Log.d("VoLTEFixer", message)
    }
}
