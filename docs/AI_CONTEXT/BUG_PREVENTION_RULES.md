# BUG_PREVENTION_RULES.md — MANDATORY FAILURE PREVENTION RULES

## 🛡️ CORE GOVERNANCE RULES

1. **ONE WINDOW TYPE = ONE INSTANCE**:
   - Never create duplicate `ctk.CTk()` root windows.
   - All secondary dialogs must verify if an existing instance is active before instantiating.

2. **NO HARDWARE RESET PULSES ON MEDIATEK PORTS**:
   - Never open MediaTek COM ports with standard `serial.Serial(port)`.
   - Always instantiate `ser = serial.Serial()`, set `ser._dtr_state = False`, `ser._rts_state = False`, `ser.dtr = False`, `ser.rts = False` BEFORE calling `ser.open()`.

3. **NO BARE EXCEPT PASS**:
   - Never swallow exceptions silently using `except: pass` without logging the exception details.

4. **NO EMOTIONAL / AMATEURISH LOG MESSAGES**:
   - Log output displayed to the user must be clear, concise, and professional enterprise-grade strings.

5. **ALWAYS VERIFY SOURCE CODE DEFINITIONS**:
   - Never infer variable names, API parameters, or file paths without viewing the exact source definition.
