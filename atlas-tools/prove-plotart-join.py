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
sys.path.insert(0, os.path.join(ROOT, "atlas-tools"))
import plotart_opportunities as OPP   # noqa: E402
import plotart_featured as FEAT   # noqa: E402


def pin(man, site, f):
    """Pin one built file as a release would: its full hash and, for a page that carries an artist opportunity list,
    its outside-the-lists hash too (the launch guard requires both to agree; 17 Nov 2026 fix: the closed-state builds
    re-pinned living-gallery.html without it, so the guard refused them for a test-setup reason)."""
    p = os.path.join(site, "plotart", f)
    man["files"][f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if f in man.get("outside_opportunity_lists", {}) and f != "art-for-hire/index.html":
        man["outside_opportunity_lists"][f] = hashlib.sha256(OPP.outside(open(p, encoding="utf-8").read()).encode()).hexdigest()
    if f in man.get("outside_grid", {}):                 # the Artists' Gallery: outside its collection AND Featured Artists regions
        raw = open(p, "rb").read()
        a, b = raw.find(b"<!-- pa-vg-collection:begin -->"), raw.find(b"<!-- pa-vg-collection:end -->")
        raw = raw[:a] + b"<!-- pa-vg-collection:begin --><!-- collection -->" + raw[b:]
        man["outside_grid"][f] = hashlib.sha256(FEAT.outside(raw.decode()).encode()).hexdigest()


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
            pin(man, site, f)
    else:   # a closed state: pinned to that state's build (as a closing release would re-pin it); no recruitment file is pinned
        for f in ("index.html", "founding-25.html", "gallery/index.html", "living-gallery.html"):
            pin(man, site, f)
        for f in ("join.html", "curatorial-policy.html", "assets/pa-apply.js", "assets/plotart-join.css"):
            man["files"].pop(f, None)
    mp = os.path.join(site, "manifest.json"); json.dump(man, open(mp, "w"))
    return site, swp, mp

def guard(site, swp, mp, repin=()):
    if repin:   # a deliberate edit: pin it, so the guard's content rules (not the manifest) must refuse it
        man = json.load(open(mp));
        for f in repin:
            pin(man, site, f)
        json.dump(man, open(mp, "w"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "prove-plotart-launch.py"), site, "--switches", swp, "--manifest", mp], capture_output=True, text=True)
    return r.returncode == 0 and "PLOTART LAUNCH · OK" in r.stdout, r.stdout + r.stderr

def gal_ok(g):
    # the application link (moved 21 Nov 2026, artwork first): once, in the closing section after the collection, never in
    # the introduction
    if g.count("pa-artist-apply-gallery:begin") != 1 or g.index("pa-artist-apply-gallery:begin") < g.index("pa-vg-collection:end"):
        return False
    seg = g[g.index("<!-- pa-artist-apply-gallery:begin -->") + len("<!-- pa-artist-apply-gallery:begin -->"):g.index("<!-- pa-artist-apply-gallery:end -->")]
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", seg))
    sec = lambda c: g[g.index('<section class="%s">' % c):g.index("</section>", g.index('<section class="%s">' % c))] if '<section class="%s">' % c in g else ""
    return ('href="../join.html#your-gallery"' in seg and "pa-artist-apply-gallery:begin" in sec("pa-vg2-close") and "pa-artist-apply" not in sec("pa-vg2-hero")
            and txt.strip() == "Artist submissions →" and not re.search(r"\d|%|commission|fee|exclusiv", txt, re.I) and "plotart-join.css" not in g)

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
# Closed-state baseline (14 Nov 2026, founder approval 18:11). The baseline is the committed page. While the committed state
# is closed, J1 already requires the committed pages to equal main, and a closed build must equal them exactly (as before).
# Since the opening release the committed state is OPEN, so a correct closed build cannot equal it: the closed build must
# then equal the committed page with ONLY the builder-owned recruitment removed (the Join stylesheet link, the Artists'
# Gallery invitation, the Founding 25 pointer), and on the homepage the artist band replaced by the Founding 25 band exactly
# as it was in the last production commit built closed. Any other difference, anywhere on these pages, still fails.
LAST_CLOSED = "2673e5f"   # Phase 3 website release, built closed (released 14 Nov 2026)
_last_closed_home = subprocess.run(["git", "-C", ROOT, "show", LAST_CLOSED + ":plotart/index.html"], capture_output=True, text=True).stdout
def _cut(t, a, b, before="", after=""):
    """t with exactly one marked region (and exactly the given surrounding whitespace) removed; None otherwise."""
    if t is None or t.count(a) != 1 or t.count(b) != 1:
        return None
    i, k = t.index(a), t.index(b) + len(b)
    if i > k or t[i - len(before):i] != before or t[k:k + len(after)] != after:
        return None
    return t[:i - len(before)] + t[k + len(after):]
def _unlink(t, link):
    return t.replace(link, "", 1) if t.count(link) == 1 else None
def closed_matches(built, f, m):
    """True when the closed build `built` of page f is exactly what closing must leave of the committed page m."""
    if not COMMITTED_OPEN:
        return built == m
    if f == "founding-25.html":
        return built == _cut(m, "<!-- pa-artist-apply-pointer:begin -->", "<!-- pa-artist-apply-pointer:end -->", before="\n  ")
    if f == "living-gallery.html":   # the For artists "Artist submissions" link (16 Nov 2026; reworded 20 Nov 2026); the gallery link stays
        return built == _cut(m, "<!-- pa-artist-apply-living:begin -->", "<!-- pa-artist-apply-living:end -->")
    if f == "gallery/index.html":
        return built == _cut(m, "<!-- pa-artist-apply-gallery:begin -->", "<!-- pa-artist-apply-gallery:end -->")   # inline in the closing section (21 Nov 2026)
    if f == "index.html":
        m = _unlink(m, '\n<link rel="stylesheet" href="assets/plotart-join.css">')
        HB, HE = "<!-- pa-artist-apply:begin -->", "<!-- pa-artist-apply:end -->"
        if m is None or m.count(HB) != 1 or m.count(HE) != 1:
            return False
        head, tail = m[:m.index(HB)], m[m.index(HE) + len(HE):]
        if not (built.startswith(head) and built.endswith(tail)) or len(built) <= len(head) + len(tail):
            return False
        band = built[len(head):len(built) - len(tail)]
        return 'aria-labelledby="f25InviteH"' in band and band in _last_closed_home
    return built == m
committed = lambda f: open(os.path.join(ROOT, "plotart", f), encoding="utf-8").read()
closed_same = lambda root, f: closed_matches(open(os.path.join(root, "plotart", f), encoding="utf-8").read(), f, committed(f))
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
    # Artist Submissions (founder brief, 20 Nov 2026): the only differences beyond the renamed hooks are these
    # user-facing messages, reworded from "application" to "submission"/"portfolio"; behaviour is unchanged.
    _AS_WORDING = (("'Please write a short biography of at least 40 characters (up to 1,000).'", "'Please write a brief introduction of at least 40 characters (up to 1,000).'"),
                   ("'Please confirm you have read the privacy notice for applications.'", "'Please confirm you have read the privacy notice for artist submissions.'"),
                   ("on ? 'Sending your application' : 'Send my application';", "on ? 'Sending your portfolio' : 'Submit my portfolio';"),
                   ("\"Applications aren't open at the moment, so your image wasn't sent.\"", "\"Submissions aren't open at the moment, so your image wasn't sent.\""),
                   ("\"Applications aren't open at the moment, so nothing was sent.", "\"Submissions aren't open at the moment, so nothing was sent."),
                   ("\"We're receiving a lot of applications right now.", "\"We're receiving a lot of submissions right now."),
                   ("'Something went wrong on our side, and your application may not have been sent.", "'Something went wrong on our side, and your portfolio may not have been sent."),
                   ("\"We couldn't reach PlotArt, so your application may not have been sent. Your details are still here: check your connection and press Send again.\"",
                    "\"We couldn't reach PlotArt, so your portfolio may not have been sent. Your details are still here: check your connection and press Submit again.\""))
    def _as_words(s):
        for o, n in _AS_WORDING:
            if s.count(o) != 1:
                return None
            s = s.replace(o, n)
        return s
    check("O3 open: the script is the Founding 25 script with only its page hooks renamed and its eight messages reworded for submissions",
          body(js) == _as_words(body(f25js).replace("data-f25-", "data-ap-").replace("'f25-", "'ap-")))
    for st in ("not_open", "paused", "closed"):
        check("N %s: nothing published: homepage, Founding 25 page and Artists' Gallery as committed less only the recruitment (exactly as committed, and so as main, while closed), no recruitment page or script" % st,
              closed_same(S[st][0], "index.html") and closed_same(S[st][0], "founding-25.html") and closed_same(S[st][0], "gallery/index.html") and closed_same(S[st][0], "living-gallery.html") and absent(S[st][0]))
    # the closed-state comparison itself refuses a closed build that differs from main anywhere outside the recruitment
    _c = open(os.path.join(S["closed"][0], "plotart", "index.html"), encoding="utf-8").read()
    _g = open(os.path.join(S["closed"][0], "plotart", "gallery", "index.html"), encoding="utf-8").read()
    _f = open(os.path.join(S["closed"][0], "plotart", "founding-25.html"), encoding="utf-8").read()
    check("N4 the closed-state comparison refuses any other change: a word changed on the closed homepage, Artists' Gallery or Founding 25 page, or the open band left in place, all fail",
          not closed_matches(_c.replace("</main>", "x</main>", 1) if "</main>" in _c else _c + "x", "index.html", committed("index.html"))
          and not closed_matches(_g.replace("<h1", "<h1 data-x", 1), "gallery/index.html", committed("gallery/index.html"))
          and not closed_matches(_f.replace("<h1", "<h1 data-x", 1), "founding-25.html", committed("founding-25.html"))
          and not closed_matches(committed("index.html"), "index.html", committed("index.html")) == COMMITTED_OPEN)
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
                     ("W4 submitting doesn't guarantee an invitation, and invitations are at the gallery's discretion", jv.count("doesn’t guarantee an invitation") >= 2 and "invitations to join are extended at the gallery’s discretion" in jv),
                     ("W5 Founding Artists keep their own agreement; new artists join as Gallery Artists", "Founding Artists keep their own agreement; artists joining now become Gallery Artists." in jv),
                     ("W6 no worked calculation, euro amount, large figure or 'deserves to be discovered' anywhere in the recruitment",
                      "€" not in jv and 'class="big"' not in j and "deserves" not in jv + bv and "€" not in bv),
                     ("W7 the homepage band is the Artist Submissions band: no figures or commercial terms, links to Join PlotArt and the gallery",
                      "Artist Submissions" in bv and not re.search(r"\d|%|commission|fee|exclusiv", bv, re.I) and 'href="join.html"' in band and 'href="gallery/"' in band),
                     ("W9 the Artists' Gallery carries one 'Artist submissions →' button in its introduction, above the collection, linking to Join PlotArt's gallery section",
                      gal_ok(open(os.path.join(site, "plotart", "gallery", "index.html"), encoding="utf-8").read())),
                     ("W10 the Living Gallery For artists section keeps its Artists' Gallery link and, only while open, the one Artist submissions link",
                      (lambda lgo: lgo.count("pa-artist-apply-living:begin") == 1 and 'href="gallery/" data-pa-track="living_artists_gallery"' in lgo
                       and '<!-- pa-artist-apply-living:begin --><a class="pa-btn pa-btn--solid" href="join.html" data-pa-track="living_artists_join">Artist submissions</a><!-- pa-artist-apply-living:end -->' in lgo)(open(os.path.join(site, "plotart", "living-gallery.html"), encoding="utf-8").read())
                      and all('join.html' not in open(os.path.join(S[st][0], "plotart", "living-gallery.html"), encoding="utf-8").read()
                              and 'href="gallery/" data-pa-track="living_artists_gallery"' in open(os.path.join(S[st][0], "plotart", "living-gallery.html"), encoding="utf-8").read()
                              for st in ("not_open", "paused", "closed"))),
                     ("W8 the scoped stylesheet is linked by the homepage only while open (and by no page of the not_open, paused or closed builds)",
                      'href="assets/plotart-join.css"' in home_o and not any('plotart-join.css' in open(os.path.join(S[st][0], "plotart", f), encoding="utf-8").read()
                                                                              for st in ("not_open", "paused", "closed") for f in ("index.html", "gallery/index.html", "founding-25.html")))):
        check(name, ok)
    breaks = [
        ("B1 the join page published while applications are not open", "not_open", None, None, None),
        ("B2 the homepage artist band published while applications are paused", "paused", "index.html", None, None),
        ("B3 a different endpoint", "open", "join.html", "/v1/art-space-register/gallery-application\" data-image", "/v1/art-space-register/founding-25\" data-image"),
        ("B4 a changed privacy confirmation", "open", "join.html", "privacy notice for PlotArt artist applications", "privacy notice"),
        ("B5 a discount line", "open", "join.html", "<dt>Fees</dt>", "<dt>Discounts</dt><dd>Collectors may receive a discount.</dd><dt>Fees</dt>"),
        ("B6 individual terms advertised", "open", "curatorial-policy.html", "<li><h3>Without cost</h3>", "<li><h3>Individual terms may be agreed</h3><p>x</p></li><li><h3>Without cost</h3>"),
        ("B7 a large 15% figure brought back", "open", "join.html", "<h1>Artist Submissions</h1>", "<h1>Artist Submissions</h1><p class=\"big\">15%</p>"),
        ("B8 a worked price example brought back", "open", "join.html", "<dt>Fees</dt>", "<dt>Example</dt><dd>Sold for €1,000, you receive €850.</dd><dt>Fees</dt>"),
        ("B9 commission on every sale through the gallery", "open", "join.html", "sold to a collector PlotArt introduced to you", "sold through your PlotArt gallery"),
        ("B10 the independent-sales sentence removed", "open", "join.html", " It doesn’t apply to your independent sales.", ""),
        ("B11 the 24-month explanation removed", "open", "join.html", "An introduction counts for 24 months.", "Introductions count."),
        ("B12 a selection board mentioned", "open", "join.html", "We review every submission individually and may ask to see a little more.", "Our selection board reads every submission."),
        ("B13 commercial terms on the homepage band", "open", "index.html", "whose work may complement the gallery.", "whose work may complement the gallery. 15% commission. No fees. No exclusivity."),
        ("B14 a criterion dropped from the policy", "open", "curatorial-policy.html", "<h3>Contribution to the gallery</h3>", "<h3>Fit</h3>"),
        ("B15 'deserves to be discovered' brought back", "open", "join.html", "<h2>A gallery of your own.</h2>", "<h2>Your art deserves to be discovered.</h2>"),
        ("B16 the programme distinction removed", "open", "join.html", " Founding Artists keep their own agreement; artists joining now become Gallery Artists.", ""),
        ("B17 opening without the privacy section for artist applications (V15)", "open", "../privacy.html", "PLOTNUA-PLOTART-ARTIST-APPLICATIONS-PRIVACY-V15", "NO-V15"),
        ("B18 the 15% made bold", "open", "join.html", "PlotArt’s commission is 15% of", "PlotArt’s commission is <strong>15%</strong> of"),
        ("B23 commercial terms on the Artists' Gallery link", "open", "gallery/index.html", 'Artist submissions <span aria-hidden="true">→</span></a>', 'Artist submissions <span aria-hidden="true">→</span> 15% commission. No fees.</a>'),
        ("B24 the Artists' Gallery button published while applications are closed", "closed", "gallery/index.html", '<p class="pa-vg2-sub">Discover original Irish art and the artists behind it.</p></div>', '<p class="pa-vg2-sub">Discover original Irish art and the artists behind it.</p></div>\n<!-- pa-artist-apply-gallery:begin --><a href="../join.html#your-gallery">Apply to join →</a><!-- pa-artist-apply-gallery:end -->'),
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
