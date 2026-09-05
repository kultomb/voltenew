# VALIDATION_RULES.md — CODE VERIFICATION & BUILD CHECKS

## 🧪 MANDATORY VALIDATION STEPS

Before declaring any task or bug fix complete:

1. **Syntax & Import Check**:
   ```bash
   python -m py_compile <modified_file.py>
   ```

2. **Release Build Check**:
   ```bash
   python build_exe_release.py
   ```
   Verify that executable [`dist/HBG_VoLTE_Fixer_Tool_v2.0.exe`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/dist/HBG_VoLTE_Fixer_Tool_v2.0.exe) is generated cleanly without errors.

3. **Git Versioning Check**:
   ```bash
   git add -u
   git commit -m "<concise commit message>"
   git push origin main
   ```
