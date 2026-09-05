# 00_READ_FIRST.md — MANDATORY AI GOVERNANCE & PROJECT MEMORY ENTRY POINT

> [!IMPORTANT]
> **CRITICAL RULE FOR ANTIGRAVITY AI AGENT:**
> Before analyzing, modifying, creating, deleting, or refactoring ANY code in this repository, you MUST:
> 1. Read [`00_READ_FIRST.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/00_READ_FIRST.md) (this file).
> 2. Read [`AI_CURRENT_CONTEXT.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/AI_CURRENT_CONTEXT.md).
> 3. Read [`BUG_PREVENTION_RULES.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/BUG_PREVENTION_RULES.md).
> 4. Read [`ARCHITECTURE_DECISIONS.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/ARCHITECTURE_DECISIONS.md).

---

## 🧭 PROJECT MEMORY MAP

| Document | Purpose |
| :--- | :--- |
| [`00_READ_FIRST.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/00_READ_FIRST.md) | Entry point & mandatory governance rules |
| [`AI_CURRENT_CONTEXT.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/AI_CURRENT_CONTEXT.md) | Active state, active modules, current restrictions |
| [`PROJECT_ARCHITECTURE.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/PROJECT_ARCHITECTURE.md) | Full system topology, thread model, module responsibilities |
| [`ARCHITECTURE_DECISIONS.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/ARCHITECTURE_DECISIONS.md) | Technical decisions & rationale (DTR/RTS, C++ engine, Grid layout) |
| [`BUG_PREVENTION_RULES.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/BUG_PREVENTION_RULES.md) | Anti-duplication, lifecycle rules, hardware watchdog rules |
| [`KNOWN_ISSUES.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/KNOWN_ISSUES.md) | Historical bugs, root causes, and verified solutions |
| [`VALIDATION_RULES.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/VALIDATION_RULES.md) | Compilation, testing, build, and git release verification |
| [`CHANGELOG_AI.md`](file:///c:/Users/CMD/Desktop/volte_fixer_tool/docs/AI_CONTEXT/CHANGELOG_AI.md) | Chronological AI work log (Builds #042–#051) |

---

## 🛡️ AGENT WORKFLOW PROTOCOL

```
[1. READ MEMORY]  ➔  [2. SEARCH EXISTING]  ➔  [3. MINIMAL SAFE FIX]  ➔  [4. VERIFY BUILD]  ➔  [5. UPDATE MEMORY]
```

1. **Read Memory**: Always inspect `00_READ_FIRST.md` and `AI_CURRENT_CONTEXT.md`.
2. **Search Existing**: Never recreate existing classes, scripts, or helpers. Reuse or extend existing utilities.
3. **Minimal Safe Fix**: Apply minimal targeted edits. Do not refactor unrelated files.
4. **Verify Build**: Always run `python -m py_compile` and `build_exe_release.py` after editing code.
5. **Update Memory**: After finishing work, update `AI_CURRENT_CONTEXT.md` and `CHANGELOG_AI.md`.
