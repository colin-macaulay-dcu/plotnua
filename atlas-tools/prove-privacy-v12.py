"""PlotNua · Privacy Notice V12 proof: the Opportunities & delivery wording is applied exactly once on V11, is exactly
reversible, says what the Studio does, and matches the Studio's code (optional, never published, deleted with the other
Studio details).
    python3 atlas-tools/prove-privacy-v12.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v12_layer as V  # noqa: E402
import privacy_v13_layer as V13  # noqa: E402  (V13, 13 Nov 2026, may sit on top of V12: V12 is checked beneath it)

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
ok(priv.count(V.MARKER) == 1, "V1 V12 must be applied exactly once")
ok("PLOTNUA-PLOTART-AGREEMENT-PRIVACY-V11" in priv, "V1 V12 sits on top of V11")
try:
    beneath = V.without_v12(priv)
    ok(V.apply_v12(beneath) == V13.without_v13(priv), "V1 V12 is not exactly reversible")
    ok(V.MARKER not in beneath and all(beneath.count(o) == 1 for o, _ in V.PAIRS), "V1 the page beneath V12 must be the V11 page exactly")
except ValueError as e:
    bad.append("V1 " + str(e))
ok(priv.count('id="plotart-opportunities"') == 1, "V1 the #plotart-opportunities anchor must exist once")
a, b = priv.find('id="plotart-galleries"'), priv.find('id="plotart-enquiries"')
ok(0 < a < priv.find('id="plotart-opportunities"') < b, "V1 the new wording sits in the artists' part of Section 8")
art = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", priv[a:b])).replace("&amp;", "&")
for need, why in [("your Opportunities & delivery answers", "what is held"), ("the county where your artwork is based", "artwork county"),
                  ("how your work could reach a venue, where you could deliver and collect", "transport and coverage"), ("any practical note you add", "the note"),
                  ("is optional", "that it is optional"), ("do not enrol you in any programme, change your agreement or give any permission to use your images", "no enrolment, contract or image permission"),
                  ("legitimate interest", "the lawful basis"), ("never published", "never published"), ("change them at any time in PlotArt Studio", "editable"),
                  ("deleted with your other Studio details, 12 months after you leave or sooner if you ask", "retention")]:
    ok(need in art, "V2 the artists' text must cover " + why)
studio = ROOT / "worker" / "plotart-studio"
src, idx = (studio / "src" / "opportunities.js").read_text(encoding="utf-8"), (studio / "src" / "index.js").read_text(encoding="utf-8")
ok("const opportunities = await O.eraseFor(env, artistId);" in idx, "V3 the Studio deletes the answers with the 12-month deletion")
ok("...(await O.recordTables(env))" in idx, "V3 the six-year deletion also clears them")
code = re.sub(r"/\*.*?\*/|//[^\n]*", "", src, flags=re.S)
ok(not re.search(r"pipeline|publish|send\(|mailer|import .*mailer", code), "V3 the Studio module neither publishes nor sends the answers")
ok("/api/pipeline" not in src and "artist_opportunities" not in (studio / "src" / "render.js").read_text(encoding="utf-8"), "V3 the answers are not in any published export")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V12 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V12 · OK — applied once on V11, exactly reversible; Opportunities & delivery answers held, optional, expression of interest only, "
      "legitimate interest, never published, editable, deleted with Studio details; matches the Studio")
