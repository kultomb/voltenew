# PROJECT_ARCHITECTURE.md — SYSTEM TOPOLOGY & MODULE ARCHITECTURE

## 🏢 ARCHITECTURE OVERVIEW

```
volte_fixer_tool/
├── volte_fixer_gui.py           # Main GUI Application (CustomTkinter, 50/50 Uniform Grid)
├── volte_engine.py              # ADB VoLTE Patch & Diagnostics Engine
├── vendor_patcher/
│   ├── vendor_engine.py         # EXT4 Vendor Image Unpacker, IMS Config Injector & Repacker
│   └── restore_engine.py        # Stock Factory Vendor Restore Engine
├── tools/
│   ├── mtk_brom_auto_engine.py  # Hybrid MediaTek BROM 1-Click Pipeline
│   ├── mtk_brom_fast_engine.cpp # Win32 C++ SetupAPI MediaTek COM Scanner & 1ms Handshake
│   ├── mtk_brom_fast_engine.exe # Compiled MSVC 64-bit Binary
│   └── mtkclient/               # Integrated MediaTek Hardware Library
└── build_exe_release.py         # Anti-decompilation Release Build Pipeline (Cython + PyArmor + PyInstaller)
```

---

## 🧵 THREAD & PROCESS LIFECYCLE MODEL

1. **GUI Main Thread**: Handles CustomTkinter event loop, UI updates, log rendering.
2. **ThreadPoolExecutor**: Executes background ADB & BROM tasks without freezing UI.
3. **Subprocess Isolation**: External binaries (`mtk_brom_fast_engine.exe`, `scrcpy`, `adb`) are executed in subprocesses with stdout pipe redirection.
