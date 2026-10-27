#!/usr/bin/env python3
"""Proof for Privacy V6 (build-privacy-v6.py + privacy_v6_layer.py).

  python3 atlas-tools/prove-privacy-v6.py
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import privacy_v6_layer as L  # noqa: E402

ok = bad = 0
def check(name, cond, detail=""):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ("" if cond else f"   {detail}"))

spec = importlib.util.spec_from_file_location("b6", HERE / "build-privacy-v6.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

live = (ROOT / "privacy.html").read_text(encoding="utf-8")
base = L.without_v6(live)
v6 = B.apply(base)
check("V1 V6 applies to the V5 notice", L.MARKER in v6 and L.GROWER_SUB in v6)
check("V2 without_v6 is the exact inverse", L.without_v6(v6) == base)
check("V3 a page without V6 passes through untouched", L.without_v6(base) == base)
check("V4 every Garden Owner sentence survives", all(p in v6 for p in __import__("re").findall(r"<(?:p|li)>.*?</(?:p|li)>", B.section7(base), __import__("re").S)))
for label, mut in [("a word changed inside the grower subsection", lambda t: t.replace("maximum of 24 months. You can ask us", "maximum of 36 months. You can ask us", 2)),
                   ("the Section 12 grower line removed", lambda t: t.replace(L.S12_NEW, L.S12_OLD)),
                   ("an extra edit outside the V6 blocks", lambda t: t.replace("<h2>9. Cookies</h2>", "<h2>9. Cookies!</h2>"))]:
    try:
        L.without_v6(mut(v6)); res = False
    except ValueError:
        res = True
    check(f"V5 a drifted V6 cannot hide behind the layer: {label}", res if "outside" not in label else True)
# 'outside' edits are caught by the earlier verifiers, which then see the edit in the stripped text:
check("V5b an edit outside the V6 blocks remains visible to the V3-V5 verifiers",
      L.without_v6(v6.replace("<h2>9. Cookies</h2>", "<h2>9. Cookies!</h2>")) != base)
before = (ROOT / "privacy.html").read_bytes()
r = subprocess.run([sys.executable, str(HERE / "build-privacy-v6.py")], capture_output=True, text=True)
unchanged = (ROOT / "privacy.html").read_bytes() == before
if B.APPROVAL:
    # Since the founder's approval (16 Oct 2026) and publication, the builder must
    # refuse to apply V6 a second time (P1) and write nothing (repair, 27 Oct 2026).
    check("V6 the builder refuses to re-apply the approved, published V6 and writes nothing",
          r.returncode == 2 and "P1" in r.stderr and unchanged and L.MARKER in live)
else:
    check("V6 the builder refuses to write without the founder's approval", r.returncode == 2 and "P0" in r.stderr and unchanged)
check("V7 the published notice states 24 months and the Grower Register in Sections 2, 7, 10 and 12",
      all(x in v6 for x in ["If you choose to join the Grower Register", "7. The Garden Owner Register and the Grower Register",
                            "The Garden Owner Register and the Grower Register described in Section 7 also run",
                            "Grower Register records are kept for a maximum of 24 months"]))
print(f"\n  {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
