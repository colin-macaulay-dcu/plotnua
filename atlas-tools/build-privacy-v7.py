#!/usr/bin/env python3
"""PlotNua · Privacy Notice V7 (2026-10-PHASE2-V7) · bounded builder. PREPARED, NOT APPLIED.

Applies the exact, reversible V7 replacements defined in privacy_v7_layer.py:
the PlotArt Founding 25 sub-section and its lines in Sections 2, 10 and 12; the
business-name sentence in Section 1; firm rights and complaint wording in
Sections 14 and 15; and the PlotNua footer. The WhatsApp subsection is not changed.

REFUSES to touch privacy.html until:
  P0  APPROVAL holds the founder's dated approval of the exact V7 wording, and
  P5  privacy_page_layers.WHATSAPP_CONFIRMATION records the founder's confirmation
      of the existing WhatsApp subsection (founder decision 27 Oct 2026).

  python3 atlas-tools/build-privacy-v7.py --preview OUT.html   write a preview copy only
  python3 atlas-tools/build-privacy-v7.py                      apply (needs P0 and P5)
  python3 atlas-tools/build-privacy-v7.py --check              verify the applied state

Applying also gives artist-register.html (built from the privacy shell) the same PlotNua
footer, in place, so its site header and identity layers are untouched; afterwards
build-artist-register.py --check verifies it byte for byte.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVACY = ROOT / "privacy.html"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from privacy_v7_layer import MARKER, F25_SUB, PAIRS, FOOT_NEW, apply_v7, without_v7, footer_v7  # noqa: E402

ARTIST = ROOT / "artist-register.html"   # built from the privacy shell: carries the same footer

APPROVAL = ""   # founder approval of the exact V7 wording goes here (date and words); empty = refuse


def die(m):
    sys.stderr.write("REFUSED: " + m + "\n"); sys.exit(2)


def apply(text: str) -> str:
    if MARKER in text:
        die("P1 V7 is already applied")
    try:
        out = apply_v7(text)
    except ValueError as e:
        die("P2 " + str(e))
    olds = [o.strip() for o, _ in PAIRS]
    declared = lambda p: any(p in o or o in p for o in olds)
    # P3 · every existing paragraph, item and heading survives, except the declared V7 replacements
    for p in re.findall(r"<(?:p|li|h2|h3)[^>]*>.*?</(?:p|li|h2|h3)>", text, re.S):
        if out.count(p) < text.count(p) and not declared(p):
            die("P3 an undeclared sentence changed: " + p[:60])
    # P4 · nothing outside the bounded V7 replacements changed
    if without_v7(out) != text:
        die("P4 an edit outside the bounded V7 replacements")
    return out


def main():
    text = PRIVACY.read_text(encoding="utf-8")
    if "--check" in sys.argv:
        if MARKER not in text or F25_SUB not in text:
            die("V7 is not applied")
        try:
            without_v7(text)
        except ValueError as e:
            die("V7 drifted: " + str(e))
        if FOOT_NEW not in ARTIST.read_text(encoding="utf-8"):
            die("artist-register.html does not carry the V7 footer")
        print("privacy V7 present"); return
    if "--preview" in sys.argv:
        Path(sys.argv[sys.argv.index("--preview") + 1]).write_text(apply(text), encoding="utf-8")
        print("wrote a V7 preview copy (privacy.html untouched)"); return
    if not APPROVAL:
        die("P0 the founder has not approved the V7 wording (APPROVAL is empty)")
    try:
        import privacy_page_layers as _ppl
    except ImportError:
        die("P5 the privacy verification repair (privacy_page_layers.py) is not installed")
    if _ppl.WHATSAPP_CONFIRMATION is None and _ppl.WHATSAPP_BLOCK in text:
        die("P5 the WhatsApp subsection in Section 5 has only provisional founder confirmation (27 Oct 2026); "
            "record the founder's confirmation in privacy_page_layers.WHATSAPP_CONFIRMATION first")
    out = apply(text)
    artist = ARTIST.read_text(encoding="utf-8")
    try:
        artist_out = footer_v7(artist)
    except ValueError as e:
        die("P6 artist-register.html: " + str(e))
    PRIVACY.write_text(out, encoding="utf-8")
    ARTIST.write_text(artist_out, encoding="utf-8")
    print("privacy.html now carries V7; artist-register.html carries the V7 footer")


if __name__ == "__main__":
    main()
