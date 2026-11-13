"""PlotNua · Privacy Notice V11 layer (2026-11-PLOTART-AGREEMENT-V11): PlotArt Founding Artist Agreement records,
image retention and leaving, and enquiry records.

PREPARED FOR RELEASE (founder approval of wording W2, 6 Nov 2026). NOT PUBLISHED until the founder authorises release
step C1. Like V7-V10, V11 is a set of EXACT, REVERSIBLE replacements and additions on top of the published page. It
rewords four V8 passages and one V8 Section 12 line:
  P1  Section 8 (artists): what we hold, the acceptance record (versions, fingerprints, time, address, names, the
      optional legal name) instead of "the version and date of the gallery licence you accepted"
  P2  Section 8 (artists): the lawful basis for keeping the acceptance record
  P3  Section 8 (artists): retention: withdrawn works, deleted and replaced photographs, published web versions in the
      private website history, leaving (14 days from the artist's notice; 12 months; six-year contractual records)
  P4  Section 8 (buyers): buyer details deleted at 24 months; the minimal enquiry record without buyer details; enquiries
      passed on by email (the email itself deleted from the mailbox within 24 months)
  P5  Section 12: the retention summary for PlotArt
  The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V11.
without_v11() returns the exact page beneath V11, so every earlier verifier keeps reading the text it governs
(privacy_v10_layer.without_v10 takes V11 off first).

    python3 atlas-tools/privacy_v11_layer.py --apply     write V11 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-AGREEMENT-PRIVACY-V11"
VERSION = "2026-11-PLOTART-AGREEMENT-V11"

P1_OLD = "      <li>the version and date of the gallery licence you accepted, and a record of the changes you and we make to your gallery and of our review decisions.</li>\n"
P1_NEW = ("      <li>a record of each agreement or licence you accept in PlotArt Studio: which documents and versions, a fingerprint of the exact text, "
          "the date and time, the Studio email address you used, the name you work under and, if you choose to give it, your legal name, together "
          "with any correction we make to that record at your request; and a record of the changes you and we make to your gallery and of our review decisions.</li>\n")
P2_OLD = "We keep sign-in and change records, and a record of what was published and when, because we have a legitimate interest in keeping accounts and the gallery secure and accountable.</p>\n"
P2_NEW = ("We keep sign-in and change records, and a record of what was published and when, because we have a legitimate interest in keeping accounts and the gallery secure and accountable. "
          "We keep the record of what you accepted to perform your artist agreement and because we have a legitimate interest in being able to show what was agreed.</p>\n")
P3_OLD = ("    <p>We keep your account, your gallery records and your original photographs while you take part and for 12 months afterwards. "
          "Photographs you remove are deleted within 30 days. We keep a record of what was published and when, without images, for the records "
          "of the founding programme and of enquiries.</p>\n")
P3_NEW = (f"    <!-- {MARKER} · PlotArt agreement records, image retention and leaving, privacy notice {VERSION} -->\n"
          "    <p>We keep your account, your gallery records and your original photographs while you take part and for 12 months afterwards. "
          "A work you withdraw from your gallery stays in your private Studio account, with its photographs, until you delete it. Photographs you "
          "delete, works you delete before they are shown, and portraits you replace are deleted within 30 days; a photograph that is still shown "
          "on your gallery at that point, for example while its replacement is being reviewed, is deleted within 30 days after it stops being shown. "
          "We keep a record of what was published and when, without images, for the records of the founding programme and of enquiries. "
          "The web versions of published photographs also remain in the private version history of our website, which is not public and is not "
          "used for anything else.</p>\n"
          "    <p id=\"plotart-leaving\">If you leave PlotArt, your gallery is removed from plotnua.ie within 14 days of your telling us, and you can no "
          "longer sign in. Your original photographs and Studio details are deleted 12 months after you leave, or sooner if you ask. Your name, "
          "your Founding Artist number, the record of what was published (without images), the record of what you accepted and any corrections "
          "to it, and the enquiry log are kept for six years after you leave, so that what was agreed can be shown, and then deleted.</p>\n")
P4_OLD = ("    <p>We keep the record of each enquiry for 24 months and then delete it. You can ask us to delete it sooner by emailing "
          "<a href=\"mailto:hello@plotnua.ie\">hello@plotnua.ie</a>; the artist you contacted keeps any email you exchange with them under "
          "their own responsibility.</p>\n")
P4_NEW = ("    <p>We delete your name, email address and message 24 months after your enquiry. We keep a minimal record of the enquiry (its "
          "reference, the date, the artwork and the artist, without your name, email address or message) for as long as the artist's agreement "
          "with PlotArt lasts and for six years afterwards, because we have a legitimate interest in honouring the commission-free terms we agreed "
          "with the artist. You can ask us to delete your details sooner by emailing <a href=\"mailto:hello@plotnua.ie\">hello@plotnua.ie</a>; "
          "the artist you contacted keeps any email you exchange with them under their own responsibility.</p>\n"
          "    <p>If PlotArt passes your enquiry to an artist by email, we record the same minimal details, never your contact details, and we "
          "delete the email itself from our mailbox within 24 months.</p>\n")
P5_OLD = "    <p>PlotArt gallery records are kept while an artist takes part and for 12 months afterwards, and enquiries to artists for 24 months, as described in Section 8.</p>\n"
P5_NEW = ("    <p>PlotArt gallery records are kept while an artist takes part and for 12 months afterwards; the record of what was published and "
          "accepted, and a minimal record of enquiries without buyers' details, for six years after an artist leaves; and buyers' details in "
          "enquiries for 24 months, as described in Section 8.</p>\n")
PAIRS = [(P1_OLD, P1_NEW), (P2_OLD, P2_NEW), (P3_OLD, P3_NEW), (P4_OLD, P4_NEW), (P5_OLD, P5_NEW)]


def apply_v11(text: str) -> str:
    if MARKER in text:
        raise ValueError("V11 already applied")
    if "PLOTNUA-PLOTART-PRIVACY-V8" not in text or "PLOTNUA-GARDEN-NOTICEBOARD-PRIVACY-V10" not in text:
        raise ValueError("V11 applies on top of V8-V10 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V11 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v11(text: str) -> str:
    """The exact page beneath V11. A page without V11 passes through untouched; a page that carries the V11 marker but
    not exactly the governed V11 text raises."""
    from privacy_v12_layer import without_v12       # V12 (Opportunities & delivery, prepared 13 Nov 2026) sits on top of V11: take it off first
    text = without_v12(text)
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V11 marker but not exactly the governed V11 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v11(out) != text:
        raise ValueError("privacy.html V11 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v11(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V11 (PlotArt agreement records, image retention and leaving, enquiry records) applied")
