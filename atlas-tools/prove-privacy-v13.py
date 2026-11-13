"""PlotNua · Privacy Notice V13 proof: the care, handling and insurance wording is applied exactly once on V12, is exactly
reversible, says what the Studio does, and matches the Studio's code.
    python3 atlas-tools/prove-privacy-v13.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v13_layer as V  # noqa: E402
import privacy_v14_layer as V14  # noqa: E402  (V14, 13 Nov 2026, may sit on top of V13: V13 is checked beneath it)

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
ok(priv.count(V.MARKER) == 1, "V1 V13 must be applied exactly once")
ok("PLOTNUA-PLOTART-OPPORTUNITIES-PRIVACY-V12" in priv, "V1 V13 sits on top of V12")
try:
    beneath = V.without_v13(priv)
    ok(V.apply_v13(beneath) == V14.without_v14(priv), "V1 V13 is not exactly reversible")
    ok(V.MARKER not in beneath and all(beneath.count(o) == 1 for o, _ in V.PAIRS), "V1 the page beneath V13 must be the V12 page exactly")
except ValueError as e:
    bad.append("V1 " + str(e))
a, b = priv.find('id="plotart-galleries"'), priv.find('id="plotart-enquiries"')
art = re.sub(r"\s+", " ", re.sub(r"<[^>]+>|<!--.*?-->", " ", priv[a:b], flags=re.S)).replace("&amp;", "&")
for need, why in [("whether your interest depends on agreeing care, handling and insurance arrangements", "what is held"),
                  ("discussed with you for every placement, whether or not you tick the box about them", "that an unticked box waives nothing")]:
    ok(need in art, "V2 the artists' text must cover " + why)
studio = ROOT / "worker" / "plotart-studio"
rules = (studio / "src" / "opportunities-rules.js").read_text(encoding="utf-8")
ok("whether or not you tick this box" in rules, "V3 the Studio form says the same beside the box")
ok((studio / "migrations" / "0010_opportunities_care.sql").exists(), "V3 the Studio stores the care condition (migration 0010)")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V13 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V13 · OK — applied once on V12, exactly reversible; care, handling and insurance condition named; discussed for every "
      "placement whether or not ticked; matches the Studio")
