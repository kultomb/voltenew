# AI_CURRENT_CONTEXT.md — CURRENT PROJECT RUNTIME & ARCHITECTURE STATE

> [!NOTE]
> Updated automatically after each major release / fix. Last updated: **Build #053 (2026-09-03)**.

---

## 📌 CURRENT SYSTEM STATE

- **Main Application GUI**: [`volte_fixer_gui.py`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/volte_fixer_gui.py)
  - UI Layout: Rigid 50/50 uniform grid column split (`uniform="col_split"`).
  - Status: FULLY OPERATIONAL.
- **MediaTek BROM Engine**: [`tools/mtk_brom_auto_engine.py`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/tools/mtk_brom_auto_engine.py) + [`tools/mtkclient`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/tools/mtkclient)
  - Instant Handshake: `instant_brom_handshake` locks BROM mode within <1ms of port detection (`COM27`), halting Watchdog timer in-process.
  - Driver Patch: Win32 serial monkey-patch forcing `CLRDTR` / `CLRRTS` to prevent MediaTek SoC Watchdog reboot.
  - Status: FULLY OPERATIONAL.
- **Vendor Patcher Engine**: [`vendor_patcher/vendor_engine.py`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/vendor_patcher/vendor_engine.py)
  - Status: FULLY OPERATIONAL.
- **Release Packaging**: [`build_exe_release.py`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/build_exe_release.py)
  - Security: Cython C-extensions (`.pyd`) + PyArmor AES Bytecode Encryption + PyInstaller Standalone single EXE.
  - Active Executable: [`dist/HBG_VoLTE_Fixer_Tool_v2.0.exe`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/dist/HBG_VoLTE_Fixer_Tool_v2.0.exe) *(Build #053)*.

---

## 🚫 CRITICAL ACTIVE RESTRICTIONS

1. **NEVER ALLOW DTR / RTS VOLTAGE HIGH PULSES**:
   - MediaTek SoCs treat DTR/RTS voltage pulses as hardware reset signals.
   - All COM port openings MUST force `_dtr_state = False` and `_rts_state = False` prior to opening handle.
2. **NEVER USE DYNAMIC PACK SIDE LAYOUT ON MAIN BODY**:
   - Main body uses rigid 50/50 grid layout (`grid(row=0, column=0, sticky="nsew")`).
3. **LOG MESSAGES MUST REMAIN PROFESSIONAL & CONCISE**:
   - Avoid subjective/amateurish log strings (e.g. "cân đối bên phải", "rực rỡ", "hoàn hảo"). Use standard enterprise log prefixes (`✓`, `ℹ`, `⚠`, `❌`).
