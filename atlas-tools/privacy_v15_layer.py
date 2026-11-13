"""PlotNua · Privacy Notice V15 layer (2026-11-PLOTART-ARTIST-APPLICATIONS-V15): applications to join the PlotArt
Artists' Gallery under the Gallery Artist terms (Gallery Artist Programme Phase 3, development 13 Nov 2026).

PREPARED FOR RELEASE. NOT PUBLISHED until the founder authorises it, and published BEFORE the application route
(/v1/art-space-register/gallery-application) is opened: its APP_PRIVACY_VERSION names this version. Like V7-V14, V15 is
an EXACT, REVERSIBLE insertion on top of the published page:
  P1  Section 8: a new sub-section #plotart-artist-applications, placed after the Founding 25 applications sub-section
      it builds on (what is collected, images, lawful basis, who can see an application and your rights are the same).
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V15.
without_v15() returns the exact page beneath V15 (privacy_v14_layer.without_v14 takes V15 off first).

    python3 atlas-tools/privacy_v15_layer.py --apply     write V15 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15"
VERSION = "2026-11-PLOTART-ARTIST-APPLICATIONS-V15"

P1_OLD = "  <!-- PLOTNUA-PLOTART-PRIVACY-V8 · PlotArt artist galleries"
P1_NEW = (f"  <!-- {MARKER} · PlotArt artist applications, privacy notice {VERSION} -->\n"
          "    <h3 class=\"pv5-sub\" id=\"plotart-artist-applications\">PlotArt artist applications (artists)</h3>\n"
          "    <p>PlotArt welcomes applications from artists based or working on the island of Ireland who would like to join the "
          "PlotArt Artists’ Gallery. Every application is read and decided individually by a person; selection is curatorial, not "
          "first-come, first-served, and we do not use automated decision-making or profiling to select artists.</p>\n"
          "    <p>We handle these applications in the same way as Founding 25 applications, described above: we collect the same "
          "details and confirmations, with the same choice of images or a portfolio link, store images privately in the European "
          "Union and never publish them, rely on the same reasons for using your information, give access only to the person who "
          "reviews applications and our service providers, and you have the same rights. The differences are these:</p>\n"
          "    <ul>\n"
          "      <li>your application is kept in its own table, separate from Founding 25 applications and from the Artist Register, "
          "and has its own reference, beginning PA-AP;</li>\n"
          "      <li>there is no waiting list;</li>\n"
          "      <li>if you are selected, we invite you to PlotArt Studio. You read and accept the PlotArt Gallery Artist Agreement there "
          "before your gallery is first published, and from then on the sections below on artist galleries and PlotArt Studio apply. "
          "With your invitation, we may start your private Studio profile from your application (your biography, medium, county, "
          "website and Instagram, never your images or anything else), and you can change any of it before you submit your gallery; and</li>\n"
          "      <li>how long we keep your application: if it is not selected or is withdrawn, for 12 months after that decision; if it "
          "has not been decided, for no more than 12 months after you applied; if you join PlotArt, for as long as you take part and "
          "for 12 months afterwards.</li>\n"
          "    </ul>\n"
          "    <p>Applying is only a request to be considered. It does not give you a place, create a PlotArt Studio account or give us "
          "permission to publish anything. You can withdraw your application, correct it, or ask us to delete it at any time by emailing "
          "<a href=\"mailto:hello@plotnua.ie\">hello@plotnua.ie</a>.</p>\n"
          + P1_OLD)
PAIRS = [(P1_OLD, P1_NEW)]


def apply_v15(text: str) -> str:
    if MARKER in text:
        raise ValueError("V15 already applied")
    if "PLOTNUA-PLOTART-GALLERY-ARTIST-PRIVACY-V14" not in text:
        raise ValueError("V15 applies on top of V14 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V15 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v15(text: str) -> str:
    """The exact page beneath V15. A page without V15 passes through untouched; a page that carries the V15 marker but
    not exactly the governed V15 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V15 marker but not exactly the governed V15 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v15(out) != text:
        raise ValueError("privacy.html V15 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v15(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V15 (PlotArt artist applications) applied")
