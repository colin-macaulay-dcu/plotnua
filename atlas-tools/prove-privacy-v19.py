"""PlotNua · Privacy Notice V19 proof: PlotArt location and delivery. V19 applies exactly once on V18, is exactly reversible,
leaves every earlier version's governed text intact beneath it, and says what the Studio does (Track C, Reports 35-36).
    python3 atlas-tools/prove-privacy-v19.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v19_layer as V  # noqa: E402
import privacy_v18_layer as V18  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
import privacy_v20_layer as V20  # noqa: E402  (V20 sits on top of V19: V19 is proved on the page beneath it)
priv = V20.without_v20(priv)
if V.MARKER not in priv:
    try:
        priv = V.apply_v19(priv)
    except ValueError as e:
        bad.append("V0 V19 cannot be applied to the page as it stands: " + str(e))
ok(priv.count(V.MARKER) == 1, "V1 V19 must be applied exactly once")
try:
    beneath = V.without_v19(priv)
    ok(V.apply_v19(beneath) == priv and V.MARKER not in beneath and V18.MARKER in beneath, "V1 V19 is not exactly reversible onto V18")
    ok(V18.without_v18(priv) == V18.without_v18(beneath), "V1 V18 and every earlier verifier read the same governed text beneath V19")
except ValueError as e:
    bad.append("V1 " + str(e))
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<!--.*?-->|<[^>]+>", " ", s, flags=re.S)).replace("&amp;", "&")
a = priv.find('id="plotart-location-delivery"')
sec = flat(priv[a:priv.find("</p>", a)]) if a > 0 else ""
for need, why in [("never an address", "no address"), ("shown on your gallery only if you choose", "location public only by choice"),
                  ("You can withdraw your consent at any time. PlotArt will process the withdrawal promptly through its publication system.", "the founder's approved withdrawal wording"),
                  ("This stays private", "general delivery private"), ("we will ask you separately at that time; an earlier choice will not be used", "fresh consent for any future public delivery"),
                  ("or that it is the same as your general delivery", "inheritance described"), ("These stay private", "placement logistics private")]:
    ok(need in sec, "V2 the notice must say: " + why)
ok("published straight away" not in flat(priv), "V3 the notice must not promise immediate publication of a withdrawal")
if bad:
    print("PRIVACY V19 · FAILED"); [print("  " + b) for b in bad]; sys.exit(1)
print("PRIVACY V19 · OK — applied once on V18, exactly reversible, wording as approved")
