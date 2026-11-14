#!/usr/bin/env python3
"""PROVE · Join PlotArt (Gallery Artist Programme Phase 3, development 13 Nov 2026). Read-only on the repository.

Builds the PlotArt pages into temporary copies of the site in each of the four application states, runs the launch
guard on each (with a manifest pinned to that build), and then breaks a copy in the ways that matter, expecting the
guard to refuse every one: a form outside "open", a different endpoint, a changed confirmation, the script outside
"open", a discount or individual-terms line, another percentage or price, a stray "Applications are open", a missing
link between the pages, and the Founding 25 pointer in the wrong state. Also checks the open page against the
Founding 25 form it reuses (same fields, the Worker's own sentences) and the committed state.

    python3 atlas-tools/prove-plotart-join.py
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SW = os.path.join(ROOT, "atlas-tools", "release", "plotart-launch-switches.json")
MAN = os.path.join(ROOT, "atlas-tools", "release", "plotart-launch-manifest.json")
results = []
def check(name, ok, detail=""):
    results.append(bool(ok)); print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok or not detail else "  [%s]" % str(detail)[-300:]))

def build(tmp, state):
    site = os.path.join(tmp, state)
    shutil.copytree(os.path.join(ROOT, "plotart"), os.path.join(site, "plotart"))
    shutil.copy(os.path.join(ROOT, "image-provenance-records.json"), site)   # L14 reads it beside plotart/
    sw = json.load(open(SW, encoding="utf-8")); sw["gallery_application_state"] = state
    swp = os.path.join(site, "switches.json"); json.dump(sw, open(swp, "w"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-plotart-join.py"), "--out", site, "--switches", swp], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    man = json.load(open(MAN, encoding="utf-8"))
    if state == "open":   # the opening release also applies privacy V15 (prepared, not applied while closed)
        sys.path.insert(0, os.path.join(ROOT, "atlas-tools")); import privacy_v15_layer as V15
        _p = open(os.path.join(ROOT, "privacy.html"), encoding="utf-8").read()
        open(os.path.join(site, "privacy.html"), "w", encoding="utf-8").write(_p if V15.MARKER in _p else V15.apply_v15(_p))
        for f in ("index.html", "founding-25.html", "join.html", "curatorial-policy.html", "assets/pa-apply.js", "assets/plotart-join.css", "gallery/index.html"):
            man["files"][f] = hashlib.sha256(open(os.path.join(site, "plotart", f), "rb").read()).hexdigest()
    else:   # a closed state: pinned to that state's build (as a closing release would re-pin it); no recruitment file is pinned
        for f in ("index.html", "founding-25.html", "gallery/index.html"):
            man["files"][f] = hashlib.sha256(open(os.path.join(site, "plotart", f), "rb").read()).hexdigest()
        for f in ("join.html", "curatorial-policy.html", "assets/pa-apply.js", "assets/plotart-join.css"):
            man["files"].pop(f, None)
    mp = os.path.join(site, "manifest.json"); json.dump(man, open(mp, "w"))
    return site, swp, mp

def guard(site, swp, mp, repin=()):
    if repin:   # a deliberate edit: pin it, so the guard's content rules (not the manifest) must refuse it
        man = json.load(open(mp));
        for f in repin:
            man["files"][f] = hashlib.sha256(open(os.path.join(site, "plotart", f), "rb").read()).hexdigest()
        json.dump(man, open(mp, "w"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "prove-plotart-launch.py"), site, "--switches", swp, "--manifest", mp], capture_output=True, text=True)
    return r.returncode == 0 and "PLOTART LAUNCH · OK" in r.stdout, r.stdout + r.stderr

def gal_ok(g):
    if g.count("pa-artist-apply-gallery:begin") != 1 or g.index("pa-artist-apply-gallery:begin") < g.index("pa-vg-collection:end"):
        return False
    seg = g[g.index("pa-artist-apply-gallery:begin"):g.index("pa-artist-apply-gallery:end")]
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg))
    return 'href="../join.html"' in seg and "pa-jn-band--compact" in seg and not re.search(r"\d|%|commission|fee|exclusiv", txt, re.I)

def edit(site, f, old, new, count=1):
    p = os.path.join(site, "plotart", f); s = open(p, encoding="utf-8").read()
    assert s.count(old) >= 1, (f, old[:60]); open(p, "w", encoding="utf-8").write(s.replace(old, new, count))

print("PROVE · Join PlotArt (artist applications)")
sw = json.load(open(SW, encoding="utf-8"))
# The committed state is not_open, or "open" in the founder-approved opening release, which must carry privacy V15 (14 Nov 2026).
_priv_root = open(os.path.join(ROOT, "privacy.html"), encoding="utf-8").read()
COMMITTED_OPEN = sw.get("gallery_application_state") == "open"
check("J0 committed: gallery_application_state is not_open (or open with privacy V15 applied), the endpoint is the approved route, and the Founding 25 stays closed",
      (sw.get("gallery_application_state") == "not_open" or (COMMITTED_OPEN and "PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15" in _priv_root))
      and sw.get("f25_application_state") == "closed"
      and sw.get("gallery_application_endpoint") == "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/gallery-application")
r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-plotart-join.py"), "--check"], capture_output=True, text=True)
# "production" = the main commit this branch is built on (its merge base), so the proof stays true when main moves on
BASE = subprocess.run(["git", "-C", ROOT, "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
main = lambda f: subprocess.run(["git", "-C", ROOT, "show", BASE + ":plotart/" + f], capture_output=True, text=True).stdout
same = lambda root, f: open(os.path.join(root, "plotart", f), encoding="utf-8").read() == main(f)
absent = lambda root: not any(os.path.exists(os.path.join(root, "plotart", f)) for f in ("join.html", "curatorial-policy.html", "assets/pa-apply.js", "assets/plotart-join.css"))
if COMMITTED_OPEN:
    check("J1 committed (open): the pages are exactly the builder's open build", r.returncode == 0 and "open build" in r.stdout, r.stdout + r.stderr)
else:
    check("J1 committed (closed): nothing of the recruitment is published: the homepage, Artists' Gallery and Founding 25 page are exactly main's, and no join page, policy page or script exists",
          r.returncode == 0 and same(ROOT, "index.html") and same(ROOT, "founding-25.html") and same(ROOT, "gallery/index.html") and absent(ROOT), r.stdout + r.stderr)

tmp = tempfile.mkdtemp(prefix="pa-join-")
try:
    S = {st: build(tmp, st) for st in ("not_open", "open", "paused", "closed")}
    for st, (site, swp, mp) in S.items():
        ok, out = guard(site, swp, mp)
        check("S %s: the launch guard passes on that state's build" % st, ok, out)
    site, swp, mp = S["open"]
    j = open(os.path.join(site, "plotart", "join.html"), encoding="utf-8").read()
    f25o = subprocess.run(["git", "-C", ROOT, "show", "43655d8^:plotart/founding-25.html"], capture_output=True, text=True).stdout
    names = lambda s: sorted(set(re.findall(r'name="([a-z_]+)"', s)))
    check("O1 open: the form asks for exactly the Founding 25 form's fields (no more)", names(j) == names(f25o), (names(j), names(f25o)))
    check("O2 open: one form, posting only to the approved route and its /image address", j.count("<form") == 1 and 'data-endpoint="https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/gallery-application"' in j)
    js = open(os.path.join(site, "plotart", "assets", "pa-apply.js"), encoding="utf-8").read()
    f25js = subprocess.run(["git", "-C", ROOT, "show", "43655d8^:plotart/assets/f25-apply.js"], capture_output=True, text=True).stdout
    body = lambda t: t[t.index("(function () {"):]
    check("O3 open: the script is the Founding 25 script with only its page hooks renamed", body(js) == body(f25js).replace("data-f25-", "data-ap-").replace("'f25-", "'ap-"))
    for st in ("not_open", "paused", "closed"):
        check("N %s: nothing published: homepage and Founding 25 page as on main, no recruitment page or script" % st,
              same(S[st][0], "index.html") and same(S[st][0], "founding-25.html") and same(S[st][0], "gallery/index.html") and absent(S[st][0]))
    jv = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", j))
    home_o = open(os.path.join(site, "plotart", "index.html"), encoding="utf-8").read()
    band = home_o[home_o.index("<!-- pa-artist-apply:begin -->"):home_o.index("<!-- pa-artist-apply:end -->")]
    bv = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", band))
    for name, ok in (("W1 the 15% appears once, only in The practical details, in plain regular type",
                      j.count("15%") == 1 and "The practical details" in jv and not re.search(r"<(?:h\d|strong|b)[^>]*>[^<]*15%", j)),
                     ("W2 commission is described as applying only to sales to collectors PlotArt introduced, and not to independent sales",
                      "sold to a collector PlotArt introduced to you" in jv and "It doesn’t apply to your independent sales." in jv),
                     ("W3 the 24-month principle in one plain sentence, with the particular-work rule", "An introduction counts for 24 months." in jv and "only the sale of a particular work you were already discussing in writing within those 24 months carries commission." in jv),
                     ("W3b introductions are defined as in PA-GAA r5 5.3 and 7.1: a PlotArt reference, or told before the sale is agreed; collectors already known are independent; original work or signed limited-edition print only",
                      "through an enquiry carrying a PlotArt reference, or tell you before the sale is agreed that they found you through PlotArt." in jv and "Collectors you already knew, or who found you another way, are independent." in jv and "an original work or signed limited-edition print" in jv),
                     ("W4 applying doesn't guarantee a place", jv.count("applying doesn’t guarantee a place") + jv.count("Applying doesn’t guarantee a place") >= 2),
                     ("W5 Founding Artists keep their own agreement; new artists join as Gallery Artists", "Founding Artists keep their own agreement; artists joining now become Gallery Artists." in jv),
                     ("W6 no worked calculation, euro amount, large figure or 'deserves to be discovered' anywhere in the recruitment",
                      "€" not in jv and 'class="big"' not in j and "deserves" not in jv + bv and "€" not in bv),
                     ("W7 the homepage band is an invitation: no figures or commercial terms, links to Join PlotArt and the gallery",
                      "An invitation to join PlotArt." in bv and not re.search(r"\d|%|commission|fee|exclusiv", bv, re.I) and 'href="join.html"' in band and 'href="gallery/"' in band),
                     ("W9 the Artists' Gallery carries the compact invitation after the collection: no figures or commercial terms, linking to Join PlotArt",
                      gal_ok(open(os.path.join(site, "plotart", "gallery", "index.html"), encoding="utf-8").read())),
                     ("W8 the scoped stylesheet is linked by the homepage only while open", 'href="assets/plotart-join.css"' in home_o and 'plotart-join.css' not in main("index.html"))):
        check(name, ok)
    breaks = [
        ("B1 the join page published while applications are not open", "not_open", None, None, None),
        ("B2 the homepage artist band published while applications are paused", "paused", "index.html", None, None),
        ("B3 a different endpoint", "open", "join.html", "/v1/art-space-register/gallery-application\" data-image", "/v1/art-space-register/founding-25\" data-image"),
        ("B4 a changed privacy confirmation", "open", "join.html", "privacy notice for PlotArt artist applications", "privacy notice"),
        ("B5 a discount line", "open", "join.html", "<dt>Fees</dt>", "<dt>Discounts</dt><dd>Collectors may receive a discount.</dd><dt>Fees</dt>"),
        ("B6 individual terms advertised", "open", "curatorial-policy.html", "<li><h3>Without cost</h3>", "<li><h3>Individual terms may be agreed</h3><p>x</p></li><li><h3>Without cost</h3>"),
        ("B7 a large 15% figure brought back", "open", "join.html", "<h1>An invitation to join PlotArt.</h1>", "<h1>An invitation to join PlotArt.</h1><p class=\"big\">15%</p>"),
        ("B8 a worked price example brought back", "open", "join.html", "<dt>Fees</dt>", "<dt>Example</dt><dd>Sold for €1,000, you receive €850.</dd><dt>Fees</dt>"),
        ("B9 commission on every sale through the gallery", "open", "join.html", "sold to a collector PlotArt introduced to you", "sold through your PlotArt gallery"),
        ("B10 the independent-sales sentence removed", "open", "join.html", " It doesn’t apply to your independent sales.", ""),
        ("B11 the 24-month explanation removed", "open", "join.html", "An introduction counts for 24 months.", "Introductions count."),
        ("B12 a selection board mentioned", "open", "join.html", "We read every application and may ask to see a little more.", "Our selection board reads every application."),
        ("B13 commercial terms on the homepage band", "open", "index.html", "Independent artists, distinctive work and new connections with collectors.", "15% commission. No fees. No exclusivity."),
        ("B14 a criterion dropped from the policy", "open", "curatorial-policy.html", "<h3>Contribution to the gallery</h3>", "<h3>Fit</h3>"),
        ("B15 'deserves to be discovered' brought back", "open", "join.html", "<h2>A gallery of your own.</h2>", "<h2>Your art deserves to be discovered.</h2>"),
        ("B16 the programme distinction removed", "open", "join.html", " Founding Artists keep their own agreement; artists joining now become Gallery Artists.", ""),
        ("B17 opening without the privacy section for artist applications (V15)", "open", "../privacy.html", "PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15", "NO-V15"),
        ("B18 the 15% made bold", "open", "join.html", "PlotArt’s commission is 15% of", "PlotArt’s commission is <strong>15%</strong> of"),
        ("B23 commercial terms on the Artists' Gallery invitation", "open", "gallery/index.html", "Independent artists, distinctive work and new connections with collectors.</p>\n  <div class=\"pa-jn-acts\"><a class=\"pa-jn-btn\" href=\"../join.html\"", "15% commission. No fees.</p>\n  <div class=\"pa-jn-acts\"><a class=\"pa-jn-btn\" href=\"../join.html\""),
        ("B24 the Artists' Gallery invitation published while applications are closed", "closed", "gallery/index.html", '<section class="pa-vg2-close">', '<!-- pa-artist-apply-gallery:begin --><a href="../join.html">Apply</a><!-- pa-artist-apply-gallery:end -->\n\n<section class="pa-vg2-close">'),
        ("B19 a Direct Approach no longer needs to come before the sale is agreed", "open", "join.html", " before the sale is agreed that they found you", " that they found you"),
        ("B20 commission widened from original work to any work", "open", "join.html", "an original work or signed limited-edition print sold", "any work or product sold"),
        ("B21 collectors already known no longer independent", "open", "join.html", " Collectors you already knew, or who found you another way, are independent.", ""),
        ("B22 delivery, insurance, installation and VAT brought into the commission", "open", "join.html", ", and excluding delivery, insurance, installation and any VAT you charge.", ", including delivery and insurance."),
    ]
    for b in breaks:
        name, st, f, old, new = b[:5]
        site2 = os.path.join(tmp, "b" + str(len(results)))
        shutil.copytree(S[st][0], site2)
        if old is None:   # publish the open build's file(s) into a closed site
            for g in (["join.html", "curatorial-policy.html"] if f is None else [f]):
                shutil.copy(os.path.join(S["open"][0], "plotart", g), os.path.join(site2, "plotart", g))
            f = "join.html" if f is None else f
            rp = ("join.html", "curatorial-policy.html") if f == "join.html" else (f,)
        else:
            edit(site2, f, old, new); rp = (f,) if not f.startswith("../") else ()
        ok, out = guard(site2, os.path.join(site2, "switches.json"), os.path.join(site2, "manifest.json"), repin=rp)
        fails = [l.strip() for l in out.splitlines() if l.startswith("  L")]
        check(name + " is refused (" + ", ".join(sorted({x.split()[0] for x in fails})) + ")", not ok and fails and all(x.split()[0] in ("L1", "L2", "L3", "L4", "L18", "L8", "L9") for x in fails) and any(x.split()[0] in ("L3", "L4", "L18") for x in fails), out)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
fail = results.count(False)
print("\nJOIN PLOTART · %d checks, %d passed, %d failed" % (len(results), len(results) - fail, fail))
sys.exit(1 if fail else 0)
