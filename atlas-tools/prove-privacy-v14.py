"""PlotNua · Privacy Notice V14 proof: the Gallery Artist commission-records wording is applied exactly once on V13, is
exactly reversible, says what the agreement and Studio do, and is in place before the agreement text can be installed.
    python3 atlas-tools/prove-privacy-v14.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v14_layer as V  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
ok(priv.count(V.MARKER) == 1, "V1 V14 must be applied exactly once")
ok("PLOTNUA-PLOTART-OPPORTUNITIES-CARE-PRIVACY-V13" in priv, "V1 V14 sits on top of V13")
try:
    beneath = V.without_v14(priv)
    ok(V.apply_v14(beneath) == priv, "V1 V14 is not exactly reversible")
    ok(V.MARKER not in beneath and all(beneath.count(o) == 1 for o, _ in V.PAIRS), "V1 the page beneath V14 must be the V13 page exactly")
except ValueError as e:
    bad.append("V1 " + str(e))
ok(priv.count('id="plotart-commission"') == 1, "V1 the #plotart-commission anchor must exist once")
a, b = priv.find('id="plotart-galleries"'), priv.find('id="plotart-enquiries"')
ok(0 < a < priv.find('id="plotart-commission"') < b, "V1 the new paragraph sits in the artists' part of Section 8")
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>|<!--.*?-->", " ", s, flags=re.S)).replace("&amp;", "&")
art = flat(priv[a:b])
for need, why in [("the sales you report to us under it", "what is held"), ("but never a collector's contact details", "no collector contact details"),
                  ("the commission invoices and payment records", "invoices and payments"), ("to perform that agreement", "contract basis"),
                  ("to keep accounts as the law requires", "legal obligation"), ("legitimate interest in being able to establish or defend a claim", "legitimate interest"),
                  ("for six years after it ends", "retention"), ("are never published", "never published"),
                  ("not deleted with your other Studio details 12 months after you leave", "separate from the 12-month deletion")]:
    ok(need in art, "V2 the artists' text must cover " + why)
ok("and Gallery Artists' sale reports and commission records, for six years after an artist leaves" in flat(priv), "V2 Section 12 names the records")
studio = ROOT / "worker" / "plotart-studio"
mig = (studio / "migrations" / "0013_gallery_artist_agreement_text.sql").read_text(encoding="utf-8")
ok("privacy" in mig.lower() and "V14" in mig, "V3 the agreement-text migration (0013) names privacy V14 as its precondition")
src = (studio / "agreements" / "source" / "PA-GAA-2026-11.cjs").read_text(encoding="utf-8")
ok("six years" in src, "V3 the agreement's record-keeping clause matches the six-year period")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V14 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V14 · OK — applied once on V13, exactly reversible; Gallery Artist sale reports and commission records named, lawful "
      "bases and six-year retention stated, never published; precedes the agreement text")
