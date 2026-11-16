"""PlotNua · Privacy Notice V17 proof: PlotArt opportunities are shown only by the artist's own choice. V17 is applied
exactly once on V16, is exactly reversible, no longer describes a default or legitimate interests for showing them, names
consent and one-click withdrawal, keeps the earlier-answers confirmation sentence, and matches what PlotArt Studio does
(box unticked for new answers, the V17 notice recorded, nothing shown without an explicit true).
    python3 atlas-tools/prove-privacy-v17.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v17_layer as V  # noqa: E402
import privacy_v16_layer as V16  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
APPLIED = V.MARKER in priv
if not APPLIED:
    try:
        priv = V.apply_v17(priv)
    except ValueError as e:
        bad.append("V0 V17 cannot be applied to the page as it stands: " + str(e))
ok(priv.count(V.MARKER) == 1, "V1 V17 must be applied exactly once")
try:
    beneath = V.without_v17(priv)
    ok(V.apply_v17(beneath) == priv and V.MARKER not in beneath and beneath.count(V.P1_OLD) == 1 and V16.MARKER in beneath,
       "V1 V17 is not exactly reversible onto V16")
except ValueError as e:
    bad.append("V1 " + str(e))
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<!--.*?-->|<[^>]+>", " ", s, flags=re.S)).replace("&amp;", "&")
a = priv.find('id="plotart-opportunities"')
sec = flat(priv[a:priv.find("</p>", a)])
for need, why in [("They are shown only if you choose to show them", "showing is the artist's own choice"),
                  ("the box for this is unticked until you tick it", "no preselected box"),
                  ("We rely on your consent to show them", "the lawful basis (consent)"),
                  ("withdraw it at any time with one click in PlotArt Studio", "one-click withdrawal"),
                  ("If you saved your answers before this choice was offered, nothing is shown unless you confirm it", "earlier answers need confirmation (V16 kept)"),
                  ("Your practical answers are never published", "the practical answers stay private (V16 kept)"),
                  ("only while your gallery is published", "only published artists (V16 kept)")]:
    ok(need in sec, "V2 the sub-section must cover " + why)
ok(not re.search(r"shown by default|legitimate interest in helping visitors", sec, re.I),
   "V2 the sub-section must no longer describe showing them by default or on legitimate interests (V13's internal-use basis is unaffected)")
studio = ROOT / "worker" / "plotart-studio"
rules = (studio / "src" / "opportunities-rules.js").read_text(encoding="utf-8")
ok("export const PUBLIC_NOTICE = '%s'" % V.STUDIO_NOTICE in rules, "V3 the Studio records the notice version this text describes")
ok(len(V.STUDIO_NOTICE) <= 40, "V3 the notice id fits migration 0015's public_notice column (8-40 characters)")
ok("If you tick this" in rules and "Leave it unticked to keep everything private" in rules and "leave this ticked" not in rules,
   "V3 the Studio's explanation describes an unticked box")
ui = (studio / "ui" / "studio.js").read_text(encoding="utf-8")
ok("note: '', pub: false };" in ui and "pub: true }" not in ui, "V3 the Studio form starts the box unticked for new answers")
ok("public_display: !!st.pub" in ui, "V3 the form sends the artist's choice")
ok("p && p.public_display === true ?" in rules and "typeof pub !== 'boolean'" in rules,
   "V3 only an explicit true shows anything; anything that is not true/false is refused")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V17 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V17 · OK — " + ("applied" if APPLIED else "prepared, applies") + " once on V16, exactly reversible; shown only by the "
      "artist's own choice (box unticked), consent with one-click withdrawal, earlier answers only on confirmation; matches the Studio")
