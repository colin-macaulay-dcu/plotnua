#!/usr/bin/env python3
"""Proof for Privacy V9, the Idea Board (privacy_v9_layer.py, 1 Nov 2026). Read-only: never writes privacy.html.
    python3 atlas-tools/prove-privacy-v9.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import privacy_v9_layer as L  # noqa: E402
import privacy_v8_layer as V8  # noqa: E402
import privacy_v7_layer as V7  # noqa: E402
import privacy_page_layers as PPL  # noqa: E402

ok = bad = 0
def check(name, cond):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)

live = (HERE.parent / "privacy.html").read_text(encoding="utf-8")
base = L.without_v9(live)
v9 = L.apply_v9(base)
vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", L.IDEA_SUB))
check("X1 V9 applies to the published V8 notice", L.MARKER in v9 and 'id="idea-board"' in v9)
check("X2 without_v9 is the exact inverse", L.without_v9(v9) == base)
check("X3 a page without V9 passes through untouched", L.without_v9(base) == base)
check("X4 the V8 layer still reads its governed text beneath V9", V8.without_v8(v9) == V8.without_v8(base))
check("X5 V7 and the governed V3-V6 reading are unchanged by V9", V7.without_v7(v9) == V7.without_v7(base) and PPL.read_governed(v9) == PPL.read_governed(base))
for label, mut in (("a word changed", lambda t: t.replace("deleted 90 days after they arrive", "deleted 120 days after they arrive")),
                   ("the sub-section anchor removed", lambda t: t.replace('id="idea-board"', 'id="ideas"')),
                   ("the Section 12 line removed", lambda t: t.replace(L.S12_NEW, L.S12_OLD))):
    try:
        L.without_v9(mut(v9)); res = False
    except ValueError:
        res = True
    check("X6 a drifted V9 cannot hide behind the layer: " + label, res)
need = {"what is collected": "we collect the idea you write", "anonymous": "Ideas are anonymous",
        "no IP address or cookies": "We do not store your IP address, and the form does not use cookies",
        "optional county, shown only with permission": 'shown only if you ticked "Show my county"',
        "moderation before publication": "Every idea is read by PlotNua before anything is published",
        "month and year only": "month and year an idea was published, never the exact date or time",
        "may become a Discovery": "Now a PlotNua Discovery",
        "lawful basis and right to object": "legitimate interests",
        "90-day pending retention": "deleted 90 days after they arrive",
        "30-day deletion after decline or removal": "deleted 30 days after that decision",
        "removal requests by reference": "with your reference number"}
for k, s in need.items():
    check("X7 covers " + k, s in vis)
check("X8 the Idea Board form links to this sub-section", 'href="privacy.html#idea-board"' in (HERE / "build-idea-board.py").read_text(encoding="utf-8"))
print("\nPRIVACY V9 · %s · %d checks, %d passed, %d failed · %s" % ("OK" if not bad else "FAIL", ok + bad, ok, bad,
      "APPLIED to privacy.html" if L.MARKER in live else "prepared, not applied"))
sys.exit(1 if bad else 0)
