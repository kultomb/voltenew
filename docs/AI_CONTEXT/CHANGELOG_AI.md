# CHANGELOG_AI.md — CHRONOLOGICAL AI CHANGE LOG

## [Build #053] — 2026-09-03
- **Root Cause Identified**: The Preloader BROM window on MediaTek devices (like MT6765/MT6762) is active for as little as 0.3s to 1.0s. Subprocess Python startup delay (800ms-1200ms) caused `mtk.py` handshake to arrive after Watchdog reboot.
- **Fix**: Added `instant_brom_handshake` directly inside `scan_mtk_com_port_fast`. Opens `COM27` in < 1ms upon detection, sends `0xA0 0x0A 0x50 0x05` BROM handshake in-process with DTR/RTS resets disabled, locking BROM mode and pausing Watchdog before spawning `mtk.py`.

## [Build #052] — 2026-09-03
- **Root Cause Discovered via Real-Time Trace**: Device connected as `MediaTek USB Port (COM27)` (VID:0E8D PID:0003) and stayed connected for 4.69 seconds before hardware watchdog reboot.
- **Fix**: Added ultra-high speed (10ms sampling) Python MediaTek BROM COM Port Detector `scan_mtk_com_port_fast` to `mtk_brom_auto_engine.py`. Locks `COM27` within 10ms and invokes `mtk.py --serialport COM27` immediately before watchdog timeout.
- **Fix**: Updated `run_brom_1click_all_in_one` to pass locked `port_found` parameter across all dump, patch, flash, and reboot stages.

## [Build #051] — 2026-09-03
- **Feature**: Patched `seriallib.py` win32 driver methods (`_update_dtr_state`, `_update_rts_state`) to force `CLRDTR` and `CLRRTS`.
- **Fix**: Prevented DTR/RTS voltage high reset pulse during port open.
- **Git Commit**: `77d3faa`.

## [Build #050] — 2026-09-03
- **Feature**: Standardized professional enterprise log strings across `volte_fixer_gui.py` and `mtk_brom_auto_engine.py`.
- **Fix**: Removed informal phrasing ("cân đối bên phải", "rực rỡ", "hoàn hảo").
- **Git Commit**: `a22bebd`.

## [Build #048] — 2026-09-03
- **Feature**: Integrated Native C++ Win32 SetupAPI BROM Engine into 1-Click execution pipeline.
- **Git Commit**: `a7e9f11`.

## [Build #047] — 2026-09-03
- **Fix**: Fixed log console panel width shift by converting `body_frame` layout from `pack()` to rigid 50/50 uniform grid.
- **Git Commit**: `d1a3ddd`.
