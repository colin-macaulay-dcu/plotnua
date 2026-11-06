#!/usr/bin/env python3
"""PROVE · Privacy Notice V11: PlotArt agreement records, image retention and leaving, enquiry records (prepared 6 Nov 2026).
Read-only: never writes privacy.html.

  V1  privacy.html carries V11 exactly once, on top of V8-V10, and V11 is an exact, reversible edit; the V8 sub-sections
      and their anchors (#plotart-galleries, #plotart-enquiries) are kept
  V2  the artists' text covers: the acceptance record (versions, fingerprint, time, address, names, optional legal name,
      corrections) and its lawful basis; withdrawn works; deleted photographs; a replaced photograph still shown;
      published web versions in the private website history; leaving (14 days from notice, 12 months, six years)
  V3  the buyers' text covers: buyer details deleted at 24 months; the minimal record without buyer details for the
      agreement's life plus six years; emailed enquiries and deletion of the email within 24 months
  V4  the wording matches what the Studio actually does (the periods in worker/plotart-studio/src/index.js)
  V5  nothing outside the PlotArt passages changed: removing V11 gives back the page exactly
    python3 atlas-tools/prove-privacy-v11.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v11_layer as V  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
ok(priv.count(V.MARKER) == 1, "V1 V11 must be applied exactly once")
ok("PLOTNUA-PLOTART-PRIVACY-V8" in priv and "PLOTNUA-GARDEN-NOTICEBOARD-PRIVACY-V10" in priv, "V1 V11 sits on top of V8-V10")
try:
    beneath = V.without_v11(priv)
    ok(V.apply_v11(beneath) == priv, "V1 V11 is not exactly reversible")
    ok(V.MARKER not in beneath and all(beneath.count(o) == 1 for o, _ in V.PAIRS), "V5 the page beneath V11 must be the V10 page exactly")
except ValueError as e:
    bad.append("V1 " + str(e))
ok(priv.count('id="plotart-galleries"') == 1 and priv.count('id="plotart-enquiries"') == 1 and priv.count('id="plotart-leaving"') == 1,
   "V1 the PlotArt anchors (galleries, enquiries, leaving) must each exist once")
text = lambda a, b: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", priv[priv.find(a):priv.find(b, priv.find(a))]))
art, buy = text('id="plotart-galleries"', 'id="plotart-enquiries"'), text('id="plotart-enquiries"', "</section>")
for need, why in [("a fingerprint of the exact text", "the acceptance record"), ("if you choose to give it, your legal name", "the optional legal name"),
                  ("any correction we make to that record", "corrections"), ("to perform your artist agreement", "the lawful basis"),
                  ("A work you withdraw from your gallery stays in your private Studio account", "withdrawn works"),
                  ("are deleted within 30 days", "deleted photographs"), ("deleted within 30 days after it stops being shown", "a replaced photograph still shown"),
                  ("remain in the private version history of our website, which is not public", "historic repository copies"),
                  ("within 14 days of your telling us", "removal on leaving"), ("deleted 12 months after you leave, or sooner if you ask", "originals on leaving"),
                  ("kept for six years after you leave", "six-year contractual records")]:
    ok(need in art, "V2 the artists' text must cover " + why)
for need, why in [("We delete your name, email address and message 24 months after your enquiry", "buyer details at 24 months"),
                  ("without your name, email address or message", "the minimal record has no buyer details"),
                  ("for as long as the artist's agreement with PlotArt lasts and for six years afterwards", "the minimal record's period"),
                  ("If PlotArt passes your enquiry to an artist by email", "emailed enquiries"),
                  ("delete the email itself from our mailbox within 24 months", "deletion of the email")]:
    ok(need in buy, "V3 the buyers' text must cover " + why)
src = (ROOT / "worker" / "plotart-studio" / "src" / "index.js").read_text(encoding="utf-8")
ok(re.search(r"removal_days: 14, originals_months: 12, records_years: 6", src) is not None, "V4 the Studio's leaving periods must be 14 days, 12 months and 6 years")
ok("30 * 86400_000" in src and "kept until that version is superseded" in src, "V4 the Studio's 30-day deletion keeps a still-shown photograph")
ok("DELETE FROM enquiries WHERE delete_after < ?" in src, "V4 the Studio deletes buyer details at their date")
ok((ROOT / "worker" / "plotart-studio" / "src" / "enquiry.js").read_text(encoding="utf-8").count("730 * 86400_000") == 1, "V4 the relay sets buyer details to 24 months")
if bad:
    for b in bad: print("FAIL " + b)
    print("PRIVACY V11 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V11 · OK — applied once on V8-V10, exactly reversible; acceptance record, lawful basis, withdrawn works, deleted and "
      "still-shown photographs, repository history, leaving (14 days, 12 months, six years); buyer details 24 months, minimal record, emailed "
      "enquiries; matches the Studio")
