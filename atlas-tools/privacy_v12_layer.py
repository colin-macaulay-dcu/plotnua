"""PlotNua · Privacy Notice V12 layer (2026-11-PLOTART-OPPORTUNITIES-V12): the artist's Opportunities & delivery answers
in PlotArt Studio (development 13 Nov 2026).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it. Like V7-V11, V12 is a set of EXACT, REVERSIBLE
additions on top of the published page, inside Section 8 (artists):
  P1  "What we hold for your gallery": one new item, the Opportunities & delivery answers, before the agreement record
  P2  a new paragraph (anchor #plotart-opportunities): optional, an expression of interest only, never published, used
      only to consider and contact the artist about opportunities (legitimate interest), editable, and deleted with the
      artist's other Studio details (12 months after leaving, or sooner on request)
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V12.
without_v12() returns the exact page beneath V12, so every earlier verifier keeps reading the text it governs
(privacy_v11_layer.without_v11 takes V12 off first).

    python3 atlas-tools/privacy_v12_layer.py --apply     write V12 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-OPPORTUNITIES-PRIVACY-V12"
VERSION = "2026-11-PLOTART-OPPORTUNITIES-V12"

P1_OLD = "      <li>your artworks' details and photographs, who took each photograph, and your declaration of any meaningful use of AI in making a work; and</li>\n"
P1_NEW = ("      <li>your artworks' details and photographs, who took each photograph, and your declaration of any meaningful use of AI in making a work;</li>\n"
          "      <li>if you choose to answer them, your Opportunities &amp; delivery answers: the kinds of opportunity you would be interested in exploring "
          "(or that you prefer the online gallery only for now), the county where your artwork is based, how your work could reach a venue, where you "
          "could deliver and collect, and any practical note you add; and</li>\n")
P2_OLD = "    <p>Only what you approve is published, as it appears in your gallery."
P2_NEW = (f"    <!-- {MARKER} · PlotArt Studio Opportunities &amp; delivery, privacy notice {VERSION} -->\n"
          "    <p id=\"plotart-opportunities\">Answering the Opportunities &amp; delivery questions is optional. Your answers are an expression of "
          "interest only: they do not enrol you in any programme, change your agreement or give any permission to use your images, and anything "
          "you take part in is agreed with you separately. We use your answers only to consider which future opportunities might suit you and to "
          "contact you about them, because we have a legitimate interest in developing PlotArt's opportunities with the artists who want them. "
          "Your answers are never published. You can change them at any time in PlotArt Studio, and they are deleted with your other Studio "
          "details, 12 months after you leave or sooner if you ask.</p>\n"
          "    <p>Only what you approve is published, as it appears in your gallery.")
PAIRS = [(P1_OLD, P1_NEW), (P2_OLD, P2_NEW)]


def apply_v12(text: str) -> str:
    if MARKER in text:
        raise ValueError("V12 already applied")
    if "PLOTNUA-PLOTART-AGREEMENT-PRIVACY-V11" not in text:
        raise ValueError("V12 applies on top of V11 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V12 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v12(text: str) -> str:
    """The exact page beneath V12. A page without V12 passes through untouched; a page that carries the V12 marker but
    not exactly the governed V12 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V12 marker but not exactly the governed V12 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v12(out) != text:
        raise ValueError("privacy.html V12 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v12(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V12 (PlotArt Studio Opportunities & delivery) applied")
