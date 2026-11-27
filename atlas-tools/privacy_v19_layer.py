"""PlotNua · Privacy Notice V19 layer (2026-11-PLOTART-LOCATION-DELIVERY-V19): where PlotArt artists are based, their delivery
to buyers and hirers, and temporary-placement logistics (Track C, founder approval 26 Nov 2026, Report 36 section E item 8,
with the founder's amendment on withdrawal).
V19 is an EXACT, REVERSIBLE edit on V18: one paragraph added to the PlotArt Studio section, after the paragraph on how
gallery information is used. Nothing else changes. The "Last updated" label is governed by the V4/V5 verifiers.
without_v19() returns the exact page beneath V19 (privacy_v18_layer.without_v18 takes V19 off first).

    python3 atlas-tools/privacy_v19_layer.py --apply     write V19 into privacy.html (founder authorisation, 26 Nov 2026)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-LOCATION-DELIVERY-PRIVACY-V19"
VERSION = "2026-11-PLOTART-LOCATION-DELIVERY-V19"

P1_OLD = '<p>We use this information to run your gallery under your artist agreement. We show your county and your portrait only if you choose to, on the basis of your consent, which you can withdraw at any time in PlotArt Studio or by emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. We keep sign-in and change records, and a record of what was published and when, because we have a legitimate interest in keeping accounts and the gallery secure and accountable. We keep the record of what you accepted to perform your artist agreement and because we have a legitimate interest in being able to show what was agreed.</p>'
P1_NEW = P1_OLD + (
    "\n    <!-- " + MARKER + " · PlotArt location and delivery, privacy notice " + VERSION + " -->"
    "\n    <p id=\"plotart-location-delivery\"><strong>Where you're based.</strong> Your country, county and, if you give it, your town or "
    "city (never an address). It is shown on your gallery only if you choose. You can withdraw your consent at any time. PlotArt "
    "will process the withdrawal promptly through its publication system. <strong>Delivery to buyers and hirers.</strong> Where "
    "and how you can get a sold or hired work to someone. This stays private. If PlotArt ever offers to show delivery areas "
    "publicly, we will ask you separately at that time; an earlier choice will not be used. <strong>Temporary placements.</strong> "
    "Where your artwork is kept, where and how you could deliver and collect for a placement (or that it is the same as your "
    "general delivery), care, handling and insurance, and your note. These stay private.</p>")

PAIRS = [(P1_OLD, P1_NEW)]


def apply_v19(text: str) -> str:
    if MARKER in text:
        raise ValueError("V19 already applied")
    if "PLOTNUA-PLOTART-PAYMENT-PILOT-PRIVACY-V18" not in text:
        raise ValueError("V19 applies on top of V18 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V19 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v19(text: str) -> str:
    """The exact page beneath V19. A page without V19 passes through untouched; a page that carries the V19 marker but
    not exactly the governed V19 text raises."""
    from privacy_v20_layer import without_v20       # V20 (PlotArt business enquiries, 27 Nov 2026) sits on top of V19: take it off first
    text = without_v20(text)
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V19 marker but not exactly the governed V19 text")
    out = text
    for old, new in reversed(PAIRS):
        out = out.replace(new, old)
    if MARKER in out or apply_v19(out) != text:
        raise ValueError("privacy.html V19 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v19(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V19 (PlotArt location and delivery) applied")
