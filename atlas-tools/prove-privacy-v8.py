#!/usr/bin/env python3
"""Proof for Privacy V8 (privacy_v8_layer.py, 29 Oct 2026). Read-only: never writes privacy.html.

    python3 atlas-tools/prove-privacy-v8.py
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import privacy_v8_layer as L  # noqa: E402
import privacy_v7_layer as V7  # noqa: E402
import privacy_page_layers as PPL  # noqa: E402

ok = bad = 0
def check(name, cond):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)

live = (HERE.parent / "privacy.html").read_text(encoding="utf-8")
applied = L.MARKER in live
base = L.without_v8(live)
v8 = L.apply_v8(base)
vis = re.sub(r"<[^>]+>", " ", L.GALLERIES_SUB)
check("W1 V8 applies to the published V7 notice", L.MARKER in v8 and 'id="plotart-galleries"' in v8 and 'id="plotart-enquiries"' in v8)
check("W2 without_v8 is the exact inverse", L.without_v8(v8) == base)
check("W3 a page without V8 passes through untouched", L.without_v8(base) == base)
check("W4 the V7 layer and every earlier verifier still read their governed text beneath V8", V7.without_v7(v8) == V7.without_v7(base))
check("W5 the governed V3-V6 reading is unchanged by V8", PPL.read_governed(v8) == PPL.read_governed(base))
for label, mut in (("a word changed", lambda t: t.replace("24 months and then delete it", "36 months and then delete it")),
                   ("the enquiries sub-section removed", lambda t: t.replace('<h3 class="pv5-sub" id="plotart-enquiries">', "<h3>")),
                   ("the Section 12 line removed", lambda t: t.replace(L.S12_NEW, L.S12_OLD))):
    try:
        L.without_v8(mut(v8)); res = False
    except ValueError:
        res = True
    check("W6 a drifted V8 cannot hide behind the layer: " + label, res)
check("W7 states what is published, location data removal and that email is never published",
      "hidden file information" in vis and "Your email address is never published" in vis)
check("W8 names the lawful bases (contract, consent for county and portrait, legitimate interests)",
      "artist agreement" in vis and "consent" in vis and "legitimate interest" in vis)
check("W9 enquiries: what is passed to the artist, no IP address stored, 24-month retention",
      "pass your name, email address and message to the artist" in vis and "do not store your IP address" in vis and "24 months" in vis)
check("W10 photographs stored in the European Union; removed photographs deleted within 30 days",
      "stored in the European Union" in vis and "deleted within 30 days" in vis)
check("W11 no commission figure, no home address, no personal phone number", "%" not in vis and "Stillorgan" not in v8.split(L.MARKER, 1)[1][:6000] and "083" not in vis)
print(f"\n  {ok} passed, {bad} failed · V8 {'APPLIED (preview branch)' if applied else 'NOT APPLIED (prepared)'}")
sys.exit(1 if bad else 0)
