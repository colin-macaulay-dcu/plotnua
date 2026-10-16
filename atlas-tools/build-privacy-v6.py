#!/usr/bin/env python3
"""PlotNua · Privacy Notice V6 (2026-10-PHASE2-V6) · bounded builder.

Adds the Grower Register to Section 7, plus one line each in Sections 2, 10
and 12. The Garden Owner Register text is NOT changed: every existing sentence
of Section 7 must survive byte-for-byte (guard P3).

REFUSES to touch privacy.html until APPROVAL is filled in with the founder's
approval of the exact wording below.

  python3 atlas-tools/build-privacy-v6.py --preview OUT.html   write a preview copy only
  python3 atlas-tools/build-privacy-v6.py                      apply (needs APPROVAL)
  python3 atlas-tools/build-privacy-v6.py --check              verify applied state
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVACY = ROOT / "privacy.html"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacy_v6_layer import (MARKER, H7_OLD, H7_NEW, GROWER_SUB, S7_END_OLD, S2_OLD, S2_NEW,  # noqa: E402
                              S10_OLD, S10_NEW, S12_OLD, S12_NEW, apply_v6, without_v6)

APPROVAL = None   # e.g. "Founder approved the V6 wording verbatim, 16 Oct 2026 HH:MM"


def die(m):
    sys.stderr.write("REFUSED: " + m + "\n"); sys.exit(2)


def section7(text):
    i = text.index("<h2>7.")
    return text[i:text.index("</section>", i)]


def apply(text: str) -> str:
    if MARKER in text:
        die("P1 V6 is already applied")
    for old, what in [(H7_OLD, "Section 7 heading"), (S7_END_OLD, "end of Section 7"), (S2_OLD, "Section 2 line"),
                      (S10_OLD, "Section 10 line"), (S12_OLD, "Section 12 line")]:
        if text.count(old) != 1:
            die(f"P2 anchor not found exactly once: {what}")
    before7 = section7(text)
    out = apply_v6(text)
    # P3 · every Garden Owner sentence survives unchanged
    for p in re.findall(r"<(?:p|li)>.*?</(?:p|li)>", before7, re.S):
        if p not in section7(out):
            die("P3 a Garden Owner Register sentence changed: " + p[:60])
    # P4 · nothing outside the five bounded edits changed
    if without_v6(out) != text:
        die("P4 an edit outside the bounded V6 blocks")
    return out


def main():
    text = PRIVACY.read_text()
    if "--check" in sys.argv:
        if MARKER not in text or GROWER_SUB not in text:
            die("V6 is not applied");
        print("privacy V6 present"); return
    if "--preview" in sys.argv:
        Path(sys.argv[sys.argv.index("--preview") + 1]).write_text(apply(text))
        print("wrote a V6 preview copy (privacy.html untouched)"); return
    if not APPROVAL:
        die("P0 the founder has not approved the V6 wording (APPROVAL is empty)")
    PRIVACY.write_text(apply(text))
    print("privacy.html now carries V6")


if __name__ == "__main__":
    main()
