"""PlotNua · Privacy Notice V16 layer (2026-11-PLOTART-OPPORTUNITIES-PUBLIC-V16): the kinds of opportunity a PlotArt artist
chooses in PlotArt Studio can be shown publicly beside their published gallery and on PlotArt's opportunity pages
(development 16 Nov 2026).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it, and published BEFORE migration 0015 runs and before
PlotArt Studio offers the choice: the Studio records PA-OPP-PUBLIC-2026-11, the wording this version describes. Like V7-V15,
V16 is an EXACT, REVERSIBLE edit on top of the published page:
  P1  Section 8, #plotart-opportunities (V12/V13): "Your answers are never published." becomes the precise rule: the
      practical answers stay private; the kinds of opportunity chosen may be shown, by default for answers saved once the
      choice exists (legitimate interests, explained before saving, one-click opt-out), and only after the artist's own
      confirmation for answers saved before it.
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V16.
without_v16() returns the exact page beneath V16 (privacy_v15_layer.without_v15 takes V16 off first).

    python3 atlas-tools/privacy_v16_layer.py --apply     write V16 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-OPPORTUNITIES-PUBLIC-PRIVACY-V16"
VERSION = "2026-11-PLOTART-OPPORTUNITIES-PUBLIC-V16"
STUDIO_NOTICE = "PA-OPP-PUBLIC-2026-11"     # recorded by PlotArt Studio with each artist's choice (migration 0015)

P1_OLD = "Your answers are never published. You can change them at any time in PlotArt Studio"
P1_NEW = (f"<!-- {MARKER} · opportunities shown publicly, privacy notice {VERSION} -->"
          "Your practical answers are never published: the county where your artwork is based, how it could travel, where you "
          "could deliver and collect, the care, handling and insurance box and your note stay private. The kinds of opportunity "
          "you choose (for example exhibitions, the Living Gallery or commissions, but never “Online gallery only for now”) can be "
          "shown beside your published gallery and in the matching lists on PlotArt’s opportunity pages, with a link to your "
          "gallery, so that visitors can see you would welcome a conversation. Being listed is a statement of interest only: it "
          "never means that an exhibition, placement, hire or commission has been arranged. If you save your answers once PlotArt "
          "Studio offers this choice, they are shown by default, because we have a legitimate interest in helping visitors find "
          "artists who are open to these opportunities, and showing them is a small, expected part of a public artist gallery. "
          "PlotArt Studio explains this before you save, and you can keep them private with one click, before saving or at any "
          "time afterwards. If you saved your answers before this choice was offered, nothing is shown unless you confirm it in "
          "PlotArt Studio. They are shown only while your gallery is published; if you keep them private, deselect an opportunity "
          "or your gallery is removed, they are taken off plotnua.ie at the next website update. "
          "You can change them at any time in PlotArt Studio")
PAIRS = [(P1_OLD, P1_NEW)]


def apply_v16(text: str) -> str:
    if MARKER in text:
        raise ValueError("V16 already applied")
    if "PLOTNUA-PLOTART-OPPORTUNITIES-CARE-PRIVACY-V13" not in text:
        raise ValueError("V16 applies on top of V13 (the Opportunities wording) only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V16 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v16(text: str) -> str:
    """The exact page beneath V16. A page without V16 passes through untouched; a page that carries the V16 marker but
    not exactly the governed V16 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V16 marker but not exactly the governed V16 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v16(out) != text:
        raise ValueError("privacy.html V16 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v16(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V16 (PlotArt opportunities shown publicly) applied")
