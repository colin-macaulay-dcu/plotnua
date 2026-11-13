"""PlotNua · Privacy Notice V14 layer (2026-11-PLOTART-GALLERY-ARTIST-V14): Gallery Artists' sale reports, commission
invoices and payment records under the Gallery Artist Agreement (PA-GAA-2026-11; development 13 Nov 2026).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it, and published BEFORE the first artist can accept the
Gallery Artist Agreement (migration 0013). Like V7-V13, V14 is a set of EXACT, REVERSIBLE replacements on top of the
published page:
  P1  Section 8 (artists), "What we hold": a new item for Gallery Artists' sale reports and commission records
  P2  Section 8 (artists): a new paragraph #plotart-commission (purposes, lawful bases, six-year retention, never published)
  P3  Section 12: the PlotArt retention line names those records among the six-year records
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V14.
without_v14() returns the exact page beneath V14 (privacy_v13_layer.without_v13 takes V14 off first).

    python3 atlas-tools/privacy_v14_layer.py --apply     write V14 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-GALLERY-ARTIST-PRIVACY-V14"
VERSION = "2026-11-PLOTART-GALLERY-ARTIST-V14"

P1_OLD = "and any practical note you add; and</li>\n"
P1_NEW = ("and any practical note you add;</li>\n"
          "      <li>if you join PlotArt under the Gallery Artist Agreement, the sales you report to us under it (the PlotArt reference or the "
          "date a collector told you they found you through PlotArt, the artwork, the dates of the sale and of any negotiations relied on, "
          "the price and any discount, and instalment details, but never a collector's contact details), and the commission invoices and "
          "payment records that follow; and</li>\n")
P2_OLD = "being able to show what was agreed.</p>\n"
P2_NEW = ("being able to show what was agreed.</p>\n"
          f"    <!-- {MARKER} · Gallery Artist commission records, privacy notice {VERSION} -->\n"
          "    <p id=\"plotart-commission\">If you are a Gallery Artist, we use your sale reports, commission invoices and payment records to "
          "calculate, invoice and collect our commission under your agreement, because we need them to perform that agreement, to keep accounts "
          "as the law requires, and because we have a legitimate interest in being able to establish or defend a claim. We keep them for as long "
          "as your agreement lasts and for six years after it ends, and then delete them, unless the law requires us to keep them longer. They are "
          "kept separately from your gallery, are never published, and are not deleted with your other Studio details 12 months after you leave.</p>\n")
P3_OLD = ("the record of what was published and accepted, and a minimal record of enquiries without buyers' details, for six years after an "
          "artist leaves;")
P3_NEW = ("the record of what was published and accepted, a minimal record of enquiries without buyers' details, and Gallery Artists' sale "
          "reports and commission records, for six years after an artist leaves;")
PAIRS = [(P1_OLD, P1_NEW), (P2_OLD, P2_NEW), (P3_OLD, P3_NEW)]


def apply_v14(text: str) -> str:
    if MARKER in text:
        raise ValueError("V14 already applied")
    if "PLOTNUA-PLOTART-OPPORTUNITIES-CARE-PRIVACY-V13" not in text:
        raise ValueError("V14 applies on top of V13 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V14 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v14(text: str) -> str:
    """The exact page beneath V14. A page without V14 passes through untouched; a page that carries the V14 marker but
    not exactly the governed V14 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V14 marker but not exactly the governed V14 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v14(out) != text:
        raise ValueError("privacy.html V14 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v14(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V14 (Gallery Artist commission records) applied")
