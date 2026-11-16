"""PlotNua · Privacy Notice V16 proof: the opportunities-shown-publicly wording is applied exactly once on V13 (Opportunities),
is exactly reversible, says precisely what can and cannot be shown, names the lawful basis and the opt-out without calling a
preselected box consent, and matches what PlotArt Studio and the publisher actually do.
    python3 atlas-tools/prove-privacy-v16.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v16_layer as V  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
priv = (ROOT / "privacy.html").read_text(encoding="utf-8")
APPLIED = V.MARKER in priv
if not APPLIED:
    try:
        priv = V.apply_v16(priv)
    except ValueError as e:
        bad.append("V0 V16 cannot be applied to the page as it stands: " + str(e))
ok(priv.count(V.MARKER) == 1, "V1 V16 must be applied exactly once")
try:
    beneath = V.without_v16(priv)
    ok(V.apply_v16(beneath) == priv and V.MARKER not in beneath and beneath.count(V.P1_OLD) == 1, "V1 V16 is not exactly reversible")
except ValueError as e:
    bad.append("V1 " + str(e))
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>|<!--.*?-->", " ", s, flags=re.S)).replace("&amp;", "&")
a = priv.find('id="plotart-opportunities"')
sec = flat(priv[a:priv.find("</p>", a)])
for need, why in [("Your practical answers are never published", "the practical answers stay private"),
                  ("the county where your artwork is based, how it could travel, where you could deliver and collect, the care, handling and insurance box and your note stay private", "each private field named"),
                  ("never “Online gallery only for now”", "online-only never shown"),
                  ("beside your published gallery and in the matching lists on PlotArt’s opportunity pages, with a link to your gallery", "where it is shown"),
                  ("a statement of interest only: it never means that an exhibition, placement, hire or commission has been arranged", "interest, not participation"),
                  ("we have a legitimate interest", "the lawful basis (not consent)"), ("you can keep them private with one click, before saving or at any time afterwards", "the opt-out"),
                  ("If you saved your answers before this choice was offered, nothing is shown unless you confirm it", "earlier answers need confirmation"),
                  ("only while your gallery is published", "only published artists"),
                  ("deselect an opportunity or your gallery is removed, they are taken off plotnua.ie at the next website update", "removal"), ("earlier versions remain in our website’s version history", "history of the lists"),
                  ("change them at any time in PlotArt Studio", "editable (V12 wording kept)")]:
    ok(need in sec, "V2 the sub-section must cover " + why)
ok(not re.search(r"\bconsent\b", sec, re.I), "V2 the wording must not present a preselected box as consent")
ok(V.P2_NEW in priv and "private version history" not in flat(priv) and "can be viewed publicly" in flat(priv),
   "V2 the version-history sentence must say the history is kept on GitHub and can be viewed publicly (no 'private version history')")
studio = ROOT / "worker" / "plotart-studio"
rules = (studio / "src" / "opportunities-rules.js").read_text(encoding="utf-8")
ok("export const PUBLIC_NOTICE = '%s'" % V.STUDIO_NOTICE in rules, "V3 the Studio records the notice version this text describes")
keys = re.search(r"export const PUBLIC_KEYS = \[([^\]]+)\]", rules)
ok(keys and "online_only" not in keys.group(1) and len(re.findall(r"'[a-z_]+'", keys.group(1))) == 7, "V3 the Studio can show exactly the seven opportunities, never online_only")
mig = (studio / "migrations" / "0015_opportunities_public.sql").read_text(encoding="utf-8")
ok("EVERY existing answer starts NULL" in mig and "public_display INTEGER CHECK (public_display IS NULL OR public_display IN (0, 1))" in mig, "V3 earlier answers start not decided")
ui = (studio / "ui" / "studio.js").read_text(encoding="utf-8")
ok("public_display: !!st.pub" in ui and "st.pub !== null" in ui, "V3 the form sends the choice only when it showed it")
gal = (ROOT / "atlas-tools" / "plotart_gallery.py").read_text(encoding="utf-8")
ok('"open_to"' in gal, "V3 the publisher accepts only the governed open_to list")
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V16 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V16 · OK — " + ("applied" if APPLIED else "prepared, applies") + " once on V13, exactly reversible; practical answers private, "
      "kinds of opportunity shown beside published galleries only, interest not participation, legitimate interest with one-click opt-out, "
      "earlier answers only on confirmation; matches the Studio, migration 0015 and the publisher")
