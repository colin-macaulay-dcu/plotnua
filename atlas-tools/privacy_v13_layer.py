"""PlotNua · Privacy Notice V13 layer (2026-11-PLOTART-OPPORTUNITIES-CARE-V13): the care, handling and insurance condition
in PlotArt Studio's Opportunities & delivery answers (development 13 Nov 2026, after artist feedback).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it. Like V7-V12, V13 is a set of EXACT, REVERSIBLE
replacements on top of the published page, inside the V12 wording in Section 8 (artists):
  P1  "What we hold": the Opportunities & delivery item also names whether the artist's interest depends on agreeing care,
      handling and insurance arrangements
  P2  the #plotart-opportunities paragraph: those arrangements are discussed for every placement, whether or not the
      artist ticks that box
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V13.
without_v13() returns the exact page beneath V13 (privacy_v12_layer.without_v12 takes V13 off first).

    python3 atlas-tools/privacy_v13_layer.py --apply     write V13 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-OPPORTUNITIES-CARE-PRIVACY-V13"
VERSION = "2026-11-PLOTART-OPPORTUNITIES-CARE-V13"

P1_OLD = "how your work could reach a venue, where you could deliver and collect, and any practical note you add; and</li>\n"
P1_NEW = ("how your work could reach a venue, where you could deliver and collect, whether your interest depends on agreeing care, "
          "handling and insurance arrangements, and any practical note you add; and</li>\n")
P2_OLD = "and anything you take part in is agreed with you separately. "
P2_NEW = ("and anything you take part in is agreed with you separately. Care, handling and insurance arrangements are discussed with "
          "you for every placement, whether or not you tick the box about them. "
          f"<!-- {MARKER} · care, handling and insurance, privacy notice {VERSION} -->")
PAIRS = [(P1_OLD, P1_NEW), (P2_OLD, P2_NEW)]


def apply_v13(text: str) -> str:
    if MARKER in text:
        raise ValueError("V13 already applied")
    if "PLOTNUA-PLOTART-OPPORTUNITIES-PRIVACY-V12" not in text:
        raise ValueError("V13 applies on top of V12 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V13 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v13(text: str) -> str:
    """The exact page beneath V13. A page without V13 passes through untouched; a page that carries the V13 marker but
    not exactly the governed V13 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V13 marker but not exactly the governed V13 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v13(out) != text:
        raise ValueError("privacy.html V13 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v13(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V13 (Opportunities & delivery: care, handling and insurance) applied")
