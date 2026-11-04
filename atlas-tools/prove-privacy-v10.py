#!/usr/bin/env python3
"""PROVE · Privacy Notice V10 and the Terms sub-section: The Borrowed Garden noticeboard (release candidate, 4 Nov 2026).

  V1  privacy.html carries V10 exactly once, on top of V9, and V10 is an exact, reversible edit
  V2  the noticeboard sub-section says what is collected, what is public and what is private (the e-mail is never shown),
      that every listing is moderated, that listings come down after 90 days, how to ask for removal, that contact is not
      available yet, that PlotNua does not arrange agreements, and that the notice changes before any contact starts
  V3  Section 7 says new registrations to both registers are paused and existing records are kept
  V4  terms.html carries the noticeboard sub-section once, with the same limits, and every anchor it links to exists
  V5  the noticeboard page links to both sub-sections
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v10_layer as V  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
terms = (ROOT / "terms.html").read_text(encoding="utf-8")
board = (ROOT / "borrowed-garden-board.html").read_text(encoding="utf-8")
disc = (ROOT / "discovery-the-borrowed-garden.html").read_text(encoding="utf-8")

ok(priv.count(V.MARKER) == 1 and "PLOTNUA-IDEA-BOARD-PRIVACY-V9" in priv, "V1 V10 must be applied once, on top of V9")
try:
    ok(V.apply_v10(V.without_v10(priv)) == priv, "V1 V10 is not exactly reversible")
except ValueError as e:
    bad.append("V1 " + str(e))
sub = priv[priv.find('id="borrowed-garden-noticeboard"'):]
sub = sub[:sub.find("</section>")]
text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", sub))
for need, why in [("email address is never shown", "the e-mail address is private"), ("read by PlotNua before anything is published", "moderation"),
                  ("comes down 90 days after it is approved", "expiry"), ("with your reference number", "removal requests"),
                  ("is not available yet", "no contact between participants yet"), ("does not arrange garden-sharing agreements", "no arrangements"),
                  ("we will update this notice before it starts", "future contact"), ("does not check, visit or verify", "no verification"),
                  ("We do not ask for your name, telephone number, address or Eircode", "no identifying details collected")]:
    ok(need in text, "V2 the privacy sub-section must cover " + why)
ok("New registrations are paused." in priv and "Existing records are kept privately" in priv, "V3 Section 7 must say registrations are paused")
ok(terms.count('id="borrowed-garden-noticeboard"') == 1, "V4 terms.html must carry the noticeboard sub-section once")
t2 = terms[terms.find('id="borrowed-garden-noticeboard"'):]
t2 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t2[:t2.find("</section>")]))
for need in ("is free", "does not arrange, take part in or guarantee", "is not available yet", "come down after 90 days", "reference number"):
    ok(need in t2, "V4 the Terms sub-section must say: " + need)
ok('id="bg-agree"' in disc, "V4 the Terms link to #bg-agree must resolve")
for href in ('privacy.html#borrowed-garden-noticeboard', 'terms.html#borrowed-garden-noticeboard'):
    ok(href in board, "V5 the noticeboard page must link to " + href)
if bad:
    for b in bad: print("FAIL " + b)
    print("PRIVACY V10 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V10 · OK — applied once on V9, exactly reversible; collection, public/private, moderation, expiry, removal, "
      "no contact yet, no arrangements, future contact; registers paused; Terms sub-section and links")
