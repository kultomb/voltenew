"""One-off: extract DEFAULT_BLACKLIST from HBGAdBlocker.py into core/policy/blacklist_defaults.py."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "HBGAdBlocker.py").read_text(encoding="utf-8")
tree = ast.parse(src)
for node in tree.body:
    if not isinstance(node, ast.Assign):
        continue
    for t in node.targets:
        if isinstance(t, ast.Name) and t.id == "BLACKLIST":
            pkgs = ast.literal_eval(node.value)
            out = ROOT / "core" / "policy" / "blacklist_defaults.py"
            out.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                "# Default package blacklist (shipped with app).",
                "",
                "DEFAULT_BLACKLIST = [",
            ]
            for i in range(0, len(pkgs), 4):
                group = pkgs[i : i + 4]
                line = ", ".join(repr(p) for p in group)
                lines.append("    " + line + ("," if i + 4 < len(pkgs) else ""))
            lines.append("]")
            out.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"wrote {len(pkgs)} packages -> {out}")
            raise SystemExit(0)
raise SystemExit("BLACKLIST not found")
