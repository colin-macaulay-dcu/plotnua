"""PlotNua · Privacy Notice V17 layer (2026-11-PLOTART-OPPORTUNITIES-OPT-IN-V17): the kinds of opportunity a PlotArt artist
chooses are shown publicly ONLY if the artist actively chooses it (founder decision, 16 Nov 2026, before the Studio release).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it, and published BEFORE PlotArt Studio offers the choice
(Stage 3): the Studio records PA-OPP-PUBLIC-2026-11-R2, the wording this version describes. V16's wording (live since
Stage 1, while no artist could yet make the choice) said new answers would be shown by default on legitimate interests.
V17 is an EXACT, REVERSIBLE edit of that one passage inside V16's sub-section; nothing else in V16 changes:
  P1  "If you save your answers once PlotArt Studio offers this choice, they are shown by default ... at any time
      afterwards." becomes: shown only if you choose (the box is unticked until you tick it), consent, withdrawable with
      one click at any time. The sentence about answers saved before the choice existed is kept word for word.
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V17.
without_v17() returns the exact page beneath V17 (privacy_v16_layer.without_v16 takes V17 off first).

    python3 atlas-tools/privacy_v17_layer.py --apply     write V17 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-OPPORTUNITIES-OPT-IN-PRIVACY-V17"
VERSION = "2026-11-PLOTART-OPPORTUNITIES-OPT-IN-V17"
STUDIO_NOTICE = "PA-OPP-PUBLIC-2026-11-R2"   # recorded by PlotArt Studio with each artist's choice from Stage 3

P1_OLD = ("If you save your answers once PlotArt Studio offers this choice, they are shown by default, because we have a "
          "legitimate interest in helping visitors find artists who are open to these opportunities, and showing them is a "
          "small, expected part of a public artist gallery. PlotArt Studio explains this before you save, and you can keep "
          "them private with one click, before saving or at any time afterwards. ")
P1_NEW = (f"<!-- {MARKER} · shown only by the artist's own choice, privacy notice {VERSION} -->"
          "They are shown only if you choose to show them: in PlotArt Studio the box for this is unticked until you tick it. "
          "We rely on your consent to show them. You can withdraw it at any time with one click in PlotArt Studio; this does "
          "not affect anything shown before you withdrew it. ")
PAIRS = [(P1_OLD, P1_NEW)]


def apply_v17(text: str) -> str:
    if MARKER in text:
        raise ValueError("V17 already applied")
    if "PLOTNUA-PLOTART-OPPORTUNITIES-PUBLIC-PRIVACY-V16" not in text:
        raise ValueError("V17 applies on top of V16 (opportunities shown publicly) only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V17 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v17(text: str) -> str:
    """The exact page beneath V17. A page without V17 passes through untouched; a page that carries the V17 marker but
    not exactly the governed V17 text raises."""
    from privacy_v18_layer import without_v18       # V18 (PlotArt payment pilot, prepared 20 Nov 2026) sits on top: take it off first
    text = without_v18(text)
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V17 marker but not exactly the governed V17 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v17(out) != text:
        raise ValueError("privacy.html V17 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v17(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V17 (PlotArt opportunities shown only by the artist's choice) applied")
