"""PlotNua · Privacy Notice V15 proof: the PlotArt artist applications sub-section is applied exactly once on V14, is
exactly reversible, says what the application route, the application page and PlotArt Studio do, and is the version the
route must name before it opens.
    python3 atlas-tools/prove-privacy-v15.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v15_layer as V  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
ok(priv.count(V.MARKER) == 1, "V1 V15 must be applied exactly once")
ok("PLOTNUA-PLOTART-GALLERY-ARTIST-PRIVACY-V14" in priv, "V1 V15 sits on top of V14")
try:
    beneath = V.without_v15(priv)
    ok(V.apply_v15(beneath) == priv, "V1 V15 is not exactly reversible")
    ok(V.MARKER not in beneath and all(beneath.count(o) == 1 for o, _ in V.PAIRS), "V1 the page beneath V15 must be the V14 page exactly")
except ValueError as e:
    bad.append("V1 " + str(e))
ok(priv.count('id="plotart-artist-applications"') == 1, "V1 the #plotart-artist-applications anchor must exist once")
a, b, c = priv.find('id="founding-25-applications"'), priv.find('id="plotart-artist-applications"'), priv.find('id="plotart-galleries"')
ok(0 < a < b < c, "V1 the sub-section follows the Founding 25 applications sub-section, in Section 8")
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>|<!--.*?-->", " ", s, flags=re.S)).replace("&amp;", "&")
sec = flat(priv[b:c])
for need, why in [("read and decided individually by a person", "human decision"), ("we do not use automated decision-making or profiling", "no profiling"),
                  ("never publish them", "images never published"), ("its own reference, beginning PA-AP", "the PA-AP reference"), ("there is no waiting list", "no waiting list"),
                  ("accept the PlotArt Gallery Artist Agreement there before your gallery is first published", "agreement in Studio"),
                  ("never your images or anything else", "what pre-fill carries"), ("for 12 months after that decision", "retention: decided"),
                  ("no more than 12 months after you applied", "retention: undecided"), ("does not give you a place, create a PlotArt Studio account or give us permission to publish anything", "what applying is not")]:
    ok(need in sec, "V2 the sub-section must cover " + why)
w = (ROOT / "worker" / "art-space-register" / "src" / "index.js").read_text(encoding="utf-8")
m = re.search(r'const GA_PRIVACY_TEXT =\s*"([^"]+)";', w)
ok(m is not None and "privacy notice for PlotArt artist applications" in m.group(1), "V3 the route's privacy confirmation names this sub-section")
ok("'PA-AP-' + f25Ref(now).slice(4)" in w, "V3 the route issues PA-AP references")
j = (ROOT / "plotart" / "join.html").read_text(encoding="utf-8") if (ROOT / "plotart" / "join.html").exists() else ""
ok('href="../privacy.html#plotart-artist-applications"' in j, "V3 the application page links this sub-section")
ix = (ROOT / "worker" / "plotart-studio" / "src" / "index.js").read_text(encoding="utf-8")
ok("PA-AP-" in ix, "V3 PlotArt Studio recognises PA-AP references (pre-fill and review)")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V15 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V15 · OK — applied once on V14, exactly reversible; PlotArt artist applications: human decision, PA-AP reference, no waiting list, "
      "agreement accepted in Studio, pre-fill limits, retention; matches the route, the page and Studio")
