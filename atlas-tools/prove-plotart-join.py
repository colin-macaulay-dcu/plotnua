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
        open(os.path.join(site, "privacy.html"), "w", encoding="utf-8").write(V15.apply_v15(open(os.path.join(ROOT, "privacy.html"), encoding="utf-8").read()))
        for f in ("index.html", "founding-25.html", "join.html", "curatorial-policy.html", "assets/pa-apply.js"):
            man["files"][f] = hashlib.sha256(open(os.path.join(site, "plotart", f), "rb").read()).hexdigest()
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

def edit(site, f, old, new, count=1):
    p = os.path.join(site, "plotart", f); s = open(p, encoding="utf-8").read()
    assert s.count(old) >= 1, (f, old[:60]); open(p, "w", encoding="utf-8").write(s.replace(old, new, count))

print("PROVE · Join PlotArt (artist applications)")
sw = json.load(open(SW, encoding="utf-8"))
check("J0 committed: gallery_application_state is not_open, the endpoint is the approved route, and the Founding 25 stays closed",
      sw.get("gallery_application_state") == "not_open" and sw.get("f25_application_state") == "closed"
      and sw.get("gallery_application_endpoint") == "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/gallery-application")
r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-plotart-join.py"), "--check"], capture_output=True, text=True)
main = lambda f: subprocess.run(["git", "-C", ROOT, "show", "origin/main:plotart/" + f], capture_output=True, text=True).stdout
same = lambda root, f: open(os.path.join(root, "plotart", f), encoding="utf-8").read() == main(f)
absent = lambda root: not any(os.path.exists(os.path.join(root, "plotart", f)) for f in ("join.html", "curatorial-policy.html", "assets/pa-apply.js"))
check("J1 committed (closed): nothing of the recruitment is published: the homepage and Founding 25 page are exactly main's, and no join page, policy page or script exists",
      r.returncode == 0 and same(ROOT, "index.html") and same(ROOT, "founding-25.html") and absent(ROOT), r.stdout + r.stderr)

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
              same(S[st][0], "index.html") and same(S[st][0], "founding-25.html") and absent(S[st][0]))
    jv = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", j))
    for name, t in (("W1 commission only on introduced sales (hero, terms, homepage)", "only on sales to collectors PlotArt introduces"),
                    ("W2 independent sales stay the artist's own", "Your own sales stay yours."),
                    ("W3 the 24-month principle in plain words", "An introduction counts for 24 months."),
                    ("W4 applying doesn't guarantee a place", "applying doesn’t guarantee a place"),
                    ("W5 Founding Artists keep their own terms; new artists join as Gallery Artists", "Founding Artists keep their own terms. Artists who join now become Gallery Artists")):
        check(name, t in jv, t)
    check("W6 no line implies every sale through the artist's gallery attracts commission", "commission on sales through PlotArt" not in jv and "15% on sales through PlotArt" not in jv)

    # breaks: each must be refused by the guard's content rules (the edited file is re-pinned first)
    breaks = [
        ("B1 the join page published while applications are not open", "not_open", None, None, None),
        ("B2 the homepage artist band published while applications are paused", "paused", "index.html", None, None),
        ("B3 a different endpoint", "open", "join.html", "/v1/art-space-register/gallery-application\" data-image", "/v1/art-space-register/founding-25\" data-image"),
        ("B4 a changed privacy confirmation", "open", "join.html", "privacy notice for PlotArt artist applications", "privacy notice"),
        ("B5 a discount line", "open", "join.html", "<li><strong>No upfront fees.</strong>", "<li>Collectors may receive a discount.</li><li><strong>No upfront fees.</strong>"),
        ("B6 individual terms advertised", "open", "curatorial-policy.html", "<li><strong>Applying costs nothing,</strong>", "<li>Individual terms may be agreed.</li><li><strong>Applying costs nothing,</strong>"),
        ("B7 another percentage", "open", "join.html", "No upfront fees.</strong>", "No upfront fees, and a 10% bonus.</strong>"),
        ("B8 a price outside the worked example", "open", "join.html", "Shipping, insurance and handling", "Prices from €200. Shipping, insurance and handling"),
        ("B9 commission on every sale through the gallery", "open", "join.html", "15% on sales PlotArt introduces.", "15% on every sale through your gallery."),
        ("B10 the independent-sales line removed", "open", "join.html", "<strong>Your own sales stay yours.</strong>", "<strong>Sales.</strong>"),
        ("B11 the 24-month explanation removed", "open", "join.html", "An introduction counts for 24 months.", "Introductions count."),
        ("B12 a selection board mentioned", "open", "join.html", "We confirm we’ve received your application, then read it", "Our selection board reads it"),
        ("B13 the homepage band lost its curatorial-policy link", "open", "index.html", 'href="curatorial-policy.html" data-pa-track="home_curatorial_policy"', 'href="about.html" data-pa-track="home_curatorial_policy"'),
        ("B14 a criterion dropped from the policy", "open", "curatorial-policy.html", "<h3>Contribution to the gallery</h3>", "<h3>Fit</h3>"),
        ("B15 the homepage band no longer says the artist's own sales stay theirs", "open", "index.html", "; your own sales stay yours.", "."),
        ("B16 the programme distinction removed", "open", "join.html", " Founding Artists keep their own terms.", ""),
        ("B17 opening without the privacy section for artist applications (V15)", "open", "../privacy.html", "PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15", "NO-V15"),
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
