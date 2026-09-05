# ARCHITECTURE_DECISIONS.md — TECHNICAL DECISIONS RECORD (ADR)

## Decision #001: Win32 Native C++ BROM Engine
- **Date**: 2026-09-03
- **Status**: APPROVED & ACTIVE
- **Context**: MediaTek SoCs (MT6765, MT6771, MT6853) reboot after ~4.7s if DTR/RTS voltage pulses are sent or if COM initialization takes longer than 4s.
- **Decision**: Implemented [`tools/mtk_brom_fast_engine.cpp`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/tools/mtk_brom_fast_engine.cpp) compiled with MSVC `cl.exe` + `setupapi.lib`.
- **Reason**: Sub-millisecond port detection and instant handshake (`0xA0 0x0A 0x50 0x05`) with `DTR_CONTROL_DISABLE` and `RTS_CONTROL_DISABLE`.

---

## Decision #002: Monkey-Patch Win32 Serial Driver in Python
- **Date**: 2026-09-03
- **Status**: APPROVED & ACTIVE
- **Context**: `pyserial.Serial()` on Windows defaults `_dtr_state = True` during `__init__()`, causing `SetCommState` to toggle DTR High before `dtr=False` is set.
- **Decision**: Monkey-patched `serial.serialwin32.Serial._update_dtr_state` and `_update_rts_state` in [`tools/mtkclient/mtkclient/Library/Connection/seriallib.py`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/tools/mtkclient/mtkclient/Library/Connection/seriallib.py) to force `CLRDTR` and `CLRRTS`.
- **Reason**: Guarantees zero DTR/RTS voltage pulses when Python connects to MediaTek COM ports.

---

## Decision #003: 50/50 Uniform Grid Column Layout
- **Date**: 2026-09-03
- **Status**: APPROVED & ACTIVE
- **Context**: Changing action button text dynamically caused dynamic `pack()` column width recalculation, making the log console panel shift width.
- **Decision**: Configured `grid(row=0, column=0, sticky="nsew")` on `body_frame` with `columnconfigure(0, weight=1, uniform="col_split")` and `columnconfigure(1, weight=1, uniform="col_split")`.
- **Reason**: Locks panel widths to exactly 50/50 ratio regardless of text length changes.

---

## Decision #004: Anti-Decompilation Release Pipeline
- **Date**: 2026-09-03
- **Status**: APPROVED & ACTIVE
- **Context**: Protect intellectual property and prevent decompile of core Python engines.
- **Decision**: Three-stage build pipeline: (1) Cython C-Extensions (`.pyd`), (2) PyArmor AES Bytecode Encryption, (3) PyInstaller standalone 1-file EXE.
