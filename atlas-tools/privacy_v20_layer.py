"""PlotNua · Privacy Notice V20 layer (2026-11-PLOTART-COMMERCIAL-V20): PlotArt business enquiries, rentals and placements
(Commercial Studio, founder approval in principle 27 Nov 2026, including its privacy requirements).
V20 is an EXACT, REVERSIBLE edit on V19:
  S8   Section 8: a new sub-section "Business enquiries, rentals and placements (PlotArt)" (id="plotart-business") at the
       end of the PlotArt section: what is kept, why (legitimate interests; contract once agreed), who it is shared with
       (only the artist whose work is involved), the Art for Hire request form, and how long it is kept.
  S12  Section 12: one line on retention (24 months after the last contact; invoices until 31 December of the sixth year).
The "Last updated" label is governed by the V4/V5 verifiers. without_v20() returns the exact page beneath V20
(privacy_v19_layer.without_v19 takes V20 off first).

    python3 atlas-tools/privacy_v20_layer.py --apply     write V20 into privacy.html (with the founder's release approval)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-COMMERCIAL-PRIVACY-V20"
VERSION = "2026-11-PLOTART-COMMERCIAL-V20"

SUB = f"""    <!-- {MARKER} · PlotArt business enquiries and placements, privacy notice {VERSION} -->
    <h3 class="pv5-sub" id="plotart-business">Business enquiries, rentals and placements (PlotArt)</h3>
    <p>When a business asks PlotArt about renting or buying art, or replies to PlotArt's own approach, we keep the contact person's name, role, work email address and telephone number, the business's name and location, the messages exchanged with us (including replies we choose to file from our email), and the record of what follows: the works proposed, each artist's approval, proposals, agreements, invoices, payments and placements.</p>
    <p>We use this to answer the enquiry and to arrange and administer any rental or sale, because we have a legitimate interest in responding to business enquiries and, once something is agreed, to perform that agreement. We share the relevant details with the artist whose work is involved, only as far as needed to arrange it. We do not use these details for marketing lists, and we do not sell them.</p>
    <p>If you send a request through the Art for Hire page, the same applies to what you write in it. A simple hidden form field and limits on repeated requests keep the form free of spam; they do not use cookies, and we do not store your IP address.</p>
    <p>These records are kept for 24 months after our last contact or, where an invoice was issued, until 31 December of the sixth year after it, as Irish tax law requires, and are then deleted.</p>
"""
S8_OLD = "Your seller information is shown on the basket page, which anyone can open, only after you confirm it.</p>\n"
S8_NEW = S8_OLD + SUB
S12_OLD = "    <p>Information will be deleted or anonymised when it is no longer reasonably required, subject to legal or administrative obligations.</p>\n"
S12_NEW = ("    <p>PlotArt business enquiries, rentals and placements are kept for 24 months after the last contact or, where an invoice was "
           "issued, until 31 December of the sixth year after it, as described in Section 8.</p>\n") + S12_OLD
PAIRS = [(S8_OLD, S8_NEW), (S12_OLD, S12_NEW)]


def apply_v20(text: str) -> str:
    if MARKER in text:
        raise ValueError("V20 already applied")
    if "PLOTNUA-PLOTART-LOCATION-DELIVERY-PRIVACY-V19" not in text:
        raise ValueError("V20 applies on top of V19 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V20 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v20(text: str) -> str:
    """The exact page beneath V20. A page without V20 passes through untouched; a page that carries the V20 marker but
    not exactly the governed V20 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V20 marker but not exactly the governed V20 text")
    out = text
    for old, new in reversed(PAIRS):
        out = out.replace(new, old)
    if MARKER in out or apply_v20(out) != text:
        raise ValueError("privacy.html V20 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v20(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V20 (PlotArt business enquiries and placements) applied")
