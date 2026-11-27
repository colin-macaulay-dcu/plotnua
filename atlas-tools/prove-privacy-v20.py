"""PlotNua · Privacy Notice V20 proof: PlotArt business enquiries, rentals and placements. V20 applies exactly once on V19,
is exactly reversible, leaves every earlier version's governed text intact beneath it, and says what Commercial Studio does
(retention matches commercial.js and migration 0032; sharing limited to the artist involved; no marketing use).
    python3 atlas-tools/prove-privacy-v20.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v20_layer as V  # noqa: E402
import privacy_v19_layer as V19  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
if V.MARKER not in priv:
    try:
        priv = V.apply_v20(priv)
    except ValueError as e:
        bad.append("V0 V20 cannot be applied to the page as it stands: " + str(e))
ok(priv.count(V.MARKER) == 1, "V1 V20 must be applied exactly once")
try:
    beneath = V.without_v20(priv)
    ok(V.apply_v20(beneath) == priv and V.MARKER not in beneath and V19.MARKER in beneath, "V1 V20 is not exactly reversible onto V19")
    ok(V19.without_v19(priv) == V19.without_v19(beneath), "V1 V19 and every earlier verifier read the same governed text beneath V20")
except ValueError as e:
    bad.append("V1 " + str(e))
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<!--.*?-->|<[^>]+>", " ", s, flags=re.S)).replace("&amp;", "&")
a = priv.find('id="plotart-business"')
sec = flat(priv[a:priv.find("<!--", a + 10) if priv.find("<!--", a + 10) > 0 else a + 4000]) if a > 0 else ""
for need, why in [("name, role, work email address and telephone number", "what is collected"),
                  ("replies we choose to file from our email", "Gmail capture described"),
                  ("legitimate interest", "lawful basis"), ("perform that agreement", "contract basis once agreed"),
                  ("only as far as needed to arrange it", "sharing limited to the artist involved"),
                  ("We do not use these details for marketing lists, and we do not sell them", "no marketing use"),
                  ("we do not store your IP address", "form: no IP stored"),
                  ("24 months after our last contact", "retention"), ("31 December of the sixth year", "invoice retention")]:
    ok(need in sec, "V2 the notice must say: " + why)
cm = (ROOT / "worker" / "plotart-studio" / "src" / "commercial.js").read_text(encoding="utf-8")
ok("RETAIN_MONTHS = 24, INVOICE_YEARS = 6" in cm, "V3 the Studio's retention must match the notice (24 months; six years after an invoice)")
ok("PlotArt business enquiries, rentals and placements are kept for 24 months" in priv, "V4 Section 12 must list the retention")
if bad:
    print("PRIVACY V20 · FAILED"); [print("  " + b) for b in bad]; sys.exit(1)
print("PRIVACY V20 · OK — applied once on V19, exactly reversible, matches Commercial Studio's retention and sharing")
