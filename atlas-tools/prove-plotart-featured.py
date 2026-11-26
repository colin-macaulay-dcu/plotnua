#!/usr/bin/env python3
"""PROVE · PlotArt Artists' Gallery · Featured Artists (founder brief 17 Nov 2026: consolidate the artist showcase into the
Artists' Gallery; the homepage curation of the same day, moved). Development only.

  python3 atlas-tools/prove-plotart-featured.py [--shots DIR]

FA1  no selection: the region is empty and the page is the collection page only (identity)
FA2  six real published artists render in the founder's order, each ONCE, each with the artwork the founder chose (not
     their first), the artist's own published image and approved alt text, the artwork title, year and any photo credit,
     the artist's name and practice line, a short introduction taken verbatim from their published biography, and a
     "View Gallery" link to their existing gallery
FA3  malformed selections are refused (seven items, the same artist twice, a missing artwork, unexpected fields or values)
     and earlier homepage records (kind "artwork") are accepted as the artist they belong to
FA4  only published, shown work appears: an unknown work, an unpublished artist, a withdrawn chosen work and a removed
     gallery drop out (nothing is substituted)
FA5  every publication re-renders the region from the page's own selection, so withdrawn work drops out by itself
FA6  each published artist appears exactly once: in Featured Artists or in Explore More Artists below (17 Nov 2026);
     featuring or unfeaturing moves them between the two, everyone else keeps their order, and the positions index and the
     rest of the page never change
FA7  the introduction is the artist's own published wording only (verbatim, never invented): whole sentences, a typed
     heading line skipped, an over-long sentence shortened at a word with an ellipsis, no biography -> no introduction
FA8  the content boundary accepts a gallery-page change only inside the region and only as its selection renders; it
     refuses a change outside it, an invented or unpublished item, a swapped image and ANY change to the homepage
FA9  the launch guard (L11, L20, L6) passes the real page and refuses the same tampered pages, a returned homepage
     section, a restored 25-gallery counter and Featured Artists placed below the collection
FA10 in a browser at 1440, 820 and 390 px: images load whole (never cropped), no sideways scrolling, no script errors,
     every link resolves (--shots saves previews)
FA11 the published galleries were only read
FA12 Browse All Artworks (21 Nov 2026): one button beside the heading to All Artworks, none under the artwork row, no
     count line; no available work -> no opening row
FA13 the opening artworks (artwork first, 21 Nov 2026): the curated three from published galleries, never repeating a
     featured artwork; an ineligible curated work is replaced deterministically (founder refinement 21 Nov 2026)
Real artist data is only READ (and changed only inside throwaway copies); nothing is written to the live tree.
"""
import copy, functools, glob, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_featured as FEAT          # noqa: E402
import plotart_gallery_pages as P        # noqa: E402

ARGS = sys.argv[1:]
SHOTS = ARGS[ARGS.index("--shots") + 1] if "--shots" in ARGS else None
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [%s]" % str(detail)[:500]) if not ok and detail else ""))


def run(cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def packages(root=ROOT):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(root, "plotart", "artists", "*", "gallery.json")))]


A = lambda s, w: {"artist": s, "work": w}
# six REAL published artists, each shown with a work chosen for them (for Nessa McCormack, not her first work)
SEL = [A("karen-ebbs", "wxurdauu8yk"), A("ciaran-mccoy", "w1yt3pkcsxk"), A("leah-hewson", "w45csc49r34"), A("daniel-chester", "wychp9cm2em"),
       A("anna-marie-savage", "wx8gh81e5bu"), A("nessa-mccormack", "w6stt966ksq")]
PK = packages()
PAGE = os.path.join(ROOT, "plotart", "gallery", "index.html")
HOMEPAGE = os.path.join(ROOT, "plotart", "index.html")
LIVE_DOC = open(PAGE, encoding="utf-8").read()


def layout_from(doc):
    """A Gallery order rebuilt from the page (test only). The public founding positions index was removed on 21 Nov 2026,
    so the positions come from the wall's own numerals; the featured artists (whose numerals the page does not show)
    and any gallery without a numeral follow without a position, in the order the page names them."""
    reg = doc[slice(*P.vg_region(doc))]
    pos = [{"position": int(n), "slug": sl, "reserved": False} for sl, n in P.wall_positions(reg).items()]   # data-pa-position (23 Nov 2026)
    numbered = {x["slug"] for x in pos}
    extra = [x for x in re.findall(r'href="\.\./artists/([a-z0-9-]+)/" data-pa-track="vg_artist"', reg) if x not in numbered]
    return {"positions": pos, "extra": extra + [x["artist"] for x in FEAT.selection_in(doc) if x["artist"] not in extra]}


LAY = layout_from(LIVE_DOC)


def build(doc, sel, pk, lay=LAY):
    """What the publisher's regrid() makes: Featured Artists, then Explore More Artists without the featured artists."""
    d = FEAT.update(doc, sel, pk)
    a, b = P.vg_region(d)
    return d[:a] + P.vg_collection(P.gallery_order(pk), layout=lay, featured=[x["artist"] for x in FEAT.selection_in(d)]) + d[b:]


wall = lambda d: re.findall(r'href="\.\./artists/([a-z0-9-]+)/" data-pa-track="vg_artist"', d[slice(*P.vg_region(d))])
# the wall's position numerals (the public positions index was removed 21 Nov 2026): artist -> numeral
index = lambda d: P.wall_positions(d[slice(*P.vg_region(d))])   # data-pa-position since 23 Nov 2026 (no visible numeral)
same_nums = lambda a, b: all(b.get(k, v) == v for k, v in a.items())
both_out = lambda d: FEAT.outside(d[:P.vg_region(d)[0]] + P.VG_BEGIN + P.VG_END + d[P.vg_region(d)[1]:])
DOC = build(LIVE_DOC, [], PK)                         # the page with no selection: every published artist on the wall
LIVE = {f: open(f, "rb").read() for f in glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json"))}
by = {p["artist"]["slug"]: p for p in PK}
coll = lambda d: d[slice(*P.vg_region(d))]

print("PROVE · PlotArt Artists' Gallery · Featured Artists")
check("FA1 no selection: no Featured Artists section (the region holds only the opening artworks, 21 Nov 2026), every published artist is on the wall, and nothing else on the page differs",
      FEAT.selection_in(DOC) == [] and FEAT.update(DOC, [], PK) == DOC and "pa-fa" not in FEAT.content([], PK) and FEAT.content([], PK).startswith('<section class="pa-op"')
      and FEAT.content([], []) == ""
      and sorted(wall(DOC)) == sorted(p["artist"]["slug"] for p in PK) and both_out(DOC) == both_out(LIVE_DOC) and index(DOC) == index(LIVE_DOC))

new = build(DOC, SEL, PK)
reg = FEAT.region(new)
items = re.findall(r'<li class="pa-fa-item" data-pa-featured="([a-z0-9-]+):(w[0-9a-z]+)">(.*?)</li>', reg)
first_nessa = next(w["id"] for w in P.shown(by["nessa-mccormack"]))
ok2, why = (len(items) == 6 and [(s, w) for s, w, _ in items] == [(x["artist"], x["work"]) for x in SEL] and first_nessa != "w6stt966ksq"
            and 'Selected by PlotArt</p><h2 id="featArtH">Artists in Focus</h2><p class="pa-fa-lede">A changing selection of artists and their work.</p>' in reg), []
for s, w, body in items:
    a, work = by[s]["artist"], next(x for x in by[s]["works"] if x["id"] == w)
    im = next(i for i in work["images"] if i["role"] == "main")
    src = re.search(r'src="\.\./artists/%s/img/([^"]+)"' % s, body)
    alt = re.search(r'alt="([^"]*)"', body)
    intro = re.search(r'<p class="pa-fa-intro">([^<]*)</p>', body)
    want = [FEAT.E(work["title"]), FEAT.E(a["display_name"]), 'href="../artists/%s/%s.html"' % (s, work["slug"]),
            'class="pa-fa-cta" href="../artists/%s/"' % s, "View Gallery"] + ([FEAT.E(P.meta_line(a))] if P.meta_line(a) else []) \
        + (["Photo: " + FEAT.E(im["photo_credit"])] if im.get("photo_credit") else [])
    if not (src and os.path.exists(os.path.join(ROOT, "plotart", "artists", s, "img", src.group(1)))
            and src.group(1) in {d["file"] for d in im["derivatives"]} and alt and alt.group(1) == FEAT.E(im["alt"])
            and all(x in body for x in want) and intro and intro.group(1) == FEAT.E(FEAT.intro(a.get("bio")))):
        ok2 = False
        why.append(s)
check("FA2 six real published artists render in the founder's order, each once, with the chosen work (not the first), its published image, approved alt text, title and credit, the name, practice, a biography introduction and View Gallery",
      ok2 and FEAT.selection_in(new) == SEL and both_out(new) == both_out(DOC), why)


def refused(sel):
    try:
        FEAT.check_selection(sel)
        return False
    except ValueError:
        return True


check("FA3 refused: seven items, the same artist twice, a missing or null artwork, an extra field, a bad kind, address or artwork id, a non-list; an earlier homepage record (kind artwork) is accepted as its artist",
      all(refused(s) for s in [SEL + [A("fintan-whelan", "wi2ggh2x2rt")], [SEL[0], SEL[0]], [SEL[5], A("nessa-mccormack", "w43yzxe0fk8")],
                               [{"artist": "karen-ebbs", "work": None}], [{"artist": "karen-ebbs"}], [dict(SEL[0], price=1)],
                               [dict(SEL[0], kind="gallery")], [A("../etc", "wxurdauu8yk")], [A("karen-ebbs", "x<script>")], {"artist": "karen-ebbs"}])
      and FEAT.check_selection([dict(SEL[0], kind="artwork"), dict(SEL[1], kind="artist")]) == SEL[:2])

pk4 = copy.deepcopy(PK)
for slug, wid in (("leah-hewson", "w45csc49r34"), ("nessa-mccormack", "w6stt966ksq")):
    for w in next(p for p in pk4 if p["artist"]["slug"] == slug)["works"]:
        if w["id"] == wid:
            w["availability"] = "withdrawn"       # the chosen work is no longer shown publicly
pk4 = [p for p in pk4 if p["artist"]["slug"] != "anna-marie-savage"]   # a gallery taken down
r4 = FEAT.resolve([SEL[0], A("fintan-whelan", "wnotreal00"), A("not-published-artist", "wabcdef"), SEL[2], SEL[4], SEL[5]], pk4)
check("FA4 only published, shown work appears: an unknown work, an unpublished artist, a withdrawn chosen work and a removed gallery drop out (no other work is substituted)",
      [(p["artist"]["slug"], w["id"]) for p, w, _ in r4] == [("karen-ebbs", "wxurdauu8yk")])

tmp = tempfile.mkdtemp(prefix="pa-feat-")
try:
    os.makedirs(os.path.join(tmp, "plotart", "gallery"))
    open(os.path.join(tmp, "plotart", "gallery", "index.html"), "w", encoding="utf-8").write(new)
    ch = FEAT.refresh(tmp, pk4)
    after = open(os.path.join(tmp, "plotart", "gallery", "index.html"), encoding="utf-8").read()
    same = FEAT.refresh(tmp, pk4)
    check("FA5 a later publication keeps the founder's selection and order and drops the withdrawn work, the removed gallery and the artist whose chosen work was withdrawn, by itself",
          ch and not same and [x["artist"] for x in FEAT.selection_in(after)] == ["karen-ebbs", "ciaran-mccoy", "daniel-chester"]
          and both_out(after) == both_out(DOC))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# FA6 Explore More Artists (17 Nov 2026): each published artist appears exactly once, in Featured Artists or in the wall
# below; featuring or unfeaturing someone moves them between the two; everyone else keeps their order and numeral; the
# twenty-five positions index and everything outside the two regions never change
ALL = [p["artist"]["slug"] for p in PK]
FULL = wall(DOC)
ok6, why6 = True, []
for sel in ([], SEL, SEL[:1], SEL[::-1], SEL[2:4], [A("lena-fawaz", next(w["id"] for w in P.shown(by["lena-fawaz"])))]):
    d = build(DOC, sel, PK)
    f, w = [x["artist"] for x in FEAT.selection_in(d)], wall(d)
    good = (not set(f) & set(w) and sorted(f + w) == sorted(ALL) and w == [x for x in FULL if x not in f]
            and same_nums(index(d), index(DOC)) and both_out(d) == both_out(DOC))
    ok6 &= good
    if not good:
        why6.append((f, w))
check("FA6 every published artist appears exactly once (featured or in Explore More Artists), the rest keep their order, and the positions index and the rest of the page never change",
      ok6 and FEAT.FEAT_END in new and new.index(FEAT.FEAT_END) < new.index(P.VG_BEGIN), why6)
d_add = build(new, SEL[:5] + [A("olivia-jones", next(w["id"] for w in P.shown(by["olivia-jones"])))], PK)   # replace Nessa with Olivia
d_rm = build(new, SEL[1:], PK)                                                                            # unfeature Karen Ebbs
check("FA6b featuring an artist removes them from Explore More Artists and unfeaturing one returns them to their own place (Review Desk changes)",
      "olivia-jones" not in wall(d_add) and "nessa-mccormack" in wall(d_add) and "karen-ebbs" in wall(d_rm)
      and wall(d_rm) == [x for x in FULL if x not in [y["artist"] for y in SEL[1:]]], (wall(d_add), wall(d_rm)))

norm = lambda t: re.sub(r"\s+", " ", t or "").strip()
intros = {p["artist"]["slug"]: FEAT.intro(p["artist"].get("bio")) for p in PK}
check("FA7 introductions are verbatim published biography text: whole sentences within %d characters, a typed heading skipped (Karen Ebbs: 'Statement'), an over-long sentence shortened with an ellipsis, no biography gives none" % FEAT.INTRO_MAX,
      all(t and (t in norm(by[s]["artist"]["bio"]) or (t.endswith("…") and t[:-1] in norm(by[s]["artist"]["bio"]))) and len(t) <= FEAT.INTRO_MAX + 1 for s, t in intros.items())
      and not intros["karen-ebbs"].startswith("Statement") and intros["karen-ebbs"].startswith("My name is Karen Ebbs")
      and FEAT.intro(None) == "" and FEAT.intro("  ") == "" and FEAT.intro("word " * 80).endswith("…") and len(FEAT.intro("word " * 80)) <= FEAT.INTRO_MAX + 1,
      intros)

# FA12 Browse All Artworks (21 Nov 2026): beside the heading, one link to the All Artworks page, its counts exactly that
# page's own (same rows, same published galleries), changing with publications; no published work -> no link
import plotart_search_content as C       # noqa: E402
BROWSE = ('<p class="pa-vg2-act pa-vg2-browse"><a class="pa-btn pa-btn--ghost" href="../artworks/" data-pa-track="gallery_browse_artworks">'
          'Browse All Artworks <span aria-hidden="true">→</span></a></p>')
reg = FEAT.content(SEL, PK)
_hero = re.search(r'<section class="pa-vg2-hero">.*?</section>', LIVE_DOC, re.S)
check("FA12 Browse All Artworks is one button beside the heading (visual refinements 21 Nov 2026), above the opening artworks, linking to the All Artworks page; nothing under the artwork row, no count line",
      _hero is not None and _hero.group(0).count(BROWSE) == 1 and LIVE_DOC.count('data-pa-track="gallery_browse_artworks"') == 1
      and LIVE_DOC.index(BROWSE) < LIVE_DOC.index('<section class="pa-op"') and 'href="../artworks/"' not in reg and "pa-op-browse" not in reg
      and "original works by" not in LIVE_DOC and 'class="pa-fa-head"' in reg and "pa-rf" not in reg)
_empty = [dict(copy.deepcopy(p), works=[dict(w, availability="sold") for w in p["works"]]) for p in PK]
check("FA12c with no available work there is no Browse link and no opening row (Featured Artists, which shows sold work too, stays)",
      "pa-op" not in FEAT.content(SEL, _empty) and 'class="pa-fa-head"' in FEAT.content(SEL, _empty))

# FA13 the opening artworks (artwork first, 21 Nov 2026): the three curated works, from their published galleries, uncropped,
# with title and artist linking to the existing pages; never an artwork featured below; withdrawn/sold/unpublished drop out
op = re.findall(r'<li class="pa-op-item" data-pa-opening="([a-z0-9-]+):(w[0-9a-z]+)">(.*?)</li>', reg)
def _op_ok(slug, wid, body):
    pkg = by[slug]; w = next(x for x in pkg["works"] if x["id"] == wid); im = FEAT._main(w)
    return (w["availability"] == "available" and 'alt="%s"' % FEAT.E(im["alt"]) in body and 'src="../artists/%s/img/' % slug in body
            and 'href="../artists/%s/%s.html"' % (slug, w["slug"]) in body and ">%s</a>" % FEAT.E(w["title"]) in body
            and 'href="../artists/%s/"' % slug in body and ">%s</a>" % FEAT.E(pkg["artist"]["display_name"]) in body
            and os.path.exists(os.path.join(ROOT, "plotart", "artists", slug, "%s.html" % w["slug"])))
check("FA13 the opening row shows the three curated published works, in order, each from its own gallery with its approved alt text, title and artist, linking to the existing artwork and gallery pages",
      [(a, b) for a, b, _ in op] == FEAT.OPENING and all(_op_ok(a, b, body) for a, b, body in op) and 'class="pa-op-row n-3"' in reg, op)
# FA13b fallback (founder refinement 21 Nov 2026): a place whose curated work is sold, withdrawn, unpublished or featured
# below is filled deterministically from other eligible published work; the curated works keep priority and their places
def _ops(sel, pk):
    return [(p["artist"]["slug"], w["id"]) for p, w, _ in FEAT.opening_items(sel, pk)]
def _with(pk, slug, wid, **change):
    q = copy.deepcopy(pk)
    for p in q:
        if p["artist"]["slug"] == slug:
            for w in p["works"]:
                if w["id"] == wid:
                    w.update(change)
    return q
# FA13b no substitution (founder instruction 26 Nov 2026, Report 37): a place whose work is sold, withdrawn or unpublished
# is LEFT OUT; the other works keep their order; nothing else is put in its place (the Studio names the vacancy)
_fx_ok, _fx_why = True, []
for i, (sl, wid) in enumerate(FEAT.OPENING):
    for label, pk2 in (("sold", _with(PK, sl, wid, availability="sold")), ("withdrawn", _with(PK, sl, wid, availability="withdrawn")),
                       ("unpublished", [p for p in PK if p["artist"]["slug"] != sl])):
        got = _ops(SEL, pk2)
        good = got == [x for j, x in enumerate(FEAT.OPENING) if j != i] and got == _ops(SEL, pk2)
        _fx_ok &= good
        if not good:
            _fx_why.append((i, label, got))
_two = FEAT.opening(SEL, _with(PK, *FEAT.OPENING[1], availability="sold"))
check("FA13b no substitution: a sold, withdrawn or unpublished work's place is left out, the other two keep their order, and the row closes up into the balanced two-work layout",
      _fx_ok and 'class="pa-op-row n-2"' in _two and _two.count('data-pa-opening=') == 2, _fx_why)
_all_gone = PK
for sl, wid in FEAT.OPENING:
    _all_gone = _with(_all_gone, sl, wid, availability="sold")
_g = _ops(SEL, _all_gone)
check("FA13d all three unavailable: no opening row at all (no broken image, nothing substituted); a founder's showcase keeps its marker so the old default is never re-seeded",
      _g == [] and FEAT.opening(SEL, _all_gone) == "" and FEAT.opening(SEL, _all_gone, choice=FEAT.OPENING, managed=True) == FEAT.SHOWCASE_MARK, _g)
# FA14 Gallery Showcase (Report 37): the founder's published showcase from the Studio sets the row; a routine publication
# (no showcase passed) keeps what the page shows; an ineligible place is left out and comes back only from the Studio
_sc = [{"artist": FEAT.OPENING[2][0], "work": FEAT.OPENING[2][1]}, {"artist": FEAT.OPENING[0][0], "work": FEAT.OPENING[0][1]}]
_d1 = FEAT.update(new, SEL, PK, _sc)
_d2 = FEAT.update(_d1, SEL, PK)                                         # a routine publication: no showcase from the Studio
_d3 = FEAT.update(_d1, SEL, _with(PK, *FEAT.OPENING[2], availability="sold"))   # the first work is sold
_d4 = FEAT.update(_d3, SEL, PK, _sc)                                     # the Studio still names it and it is available again
_bad = []
for b in ([{"artist": "x", "work": "nope"}], [{"artist": FEAT.OPENING[0][0], "work": FEAT.OPENING[0][1]}] * 2, [{"artist": "a-b", "work": "w1234", "kind": "x"}], [{}] * 4):
    try:
        FEAT.check_showcase(b); _bad.append("accepted %r" % (b,))
    except ValueError:
        pass
check("FA14 the founder's showcase sets the row (order and works); a routine publication keeps it; a sold work drops out with nothing substituted and returns when the Studio's showcase is eligible again; malformed showcases are refused",
      FEAT.showcase_in(_d1) == [tuple(FEAT.OPENING[2]), tuple(FEAT.OPENING[0])] and _d2 == _d1 and FEAT.showcase_in(_d3) == [tuple(FEAT.OPENING[0])]
      and FEAT.showcase_in(_d4) == FEAT.showcase_in(_d1) and FEAT.selection_in(_d1) == FEAT.selection_in(new) and FEAT.outside(_d1) == FEAT.outside(new) and not _bad,
      (FEAT.showcase_in(_d1), FEAT.showcase_in(_d3), _bad))
check("FA13c no opening work repeats a Featured Artists artwork on the live page, and the opening row sits directly after the introduction",
      not ({(a, b) for a, b, _ in re.findall(r'data-pa-opening="([a-z0-9-]+):(w[0-9a-z]+)"()', LIVE_DOC)} & {(x["artist"], x["work"]) for x in FEAT.selection_in(LIVE_DOC)})
      and re.search(r'</div></section>\n\n<!-- pa-featured-artists:begin -->\n<section class="pa-op"', LIVE_DOC) is not None)

print("— FA8/FA9 the content boundary and the launch guard (throwaway worktree)")
wt = tempfile.mkdtemp(prefix="pa-feat-wt-")
shutil.rmtree(wt)
run(["git", "worktree", "add", "-q", "--detach", wt, "HEAD"])
gitc = lambda *a: run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid"] + list(a), cwd=wt)
bnd = lambda b, r: run([sys.executable, os.path.join(wt, "atlas-tools", "release", "plotart-content-boundary.py"), b, r], cwd=wt)
guard = lambda: run([sys.executable, "atlas-tools/prove-plotart-launch.py", ".", "--switches", "atlas-tools/release/plotart-launch-switches.json",
                     "--manifest", "atlas-tools/release/plotart-launch-manifest.json"], cwd=wt)
try:
    gp = os.path.join(wt, "plotart", "gallery", "index.html")
    _blank = build(open(gp, encoding="utf-8").read(), [], packages(wt))
    open(gp, "w", encoding="utf-8").write(_blank)
    gitc("commit", "-qam", "test: no featured artists")
    base = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    g0, go0 = guard()
    _six = build(open(gp, encoding="utf-8").read(), SEL, packages(wt))
    open(gp, "w", encoding="utf-8").write(_six)
    gitc("commit", "-qam", "test: six featured artists")
    c1, o1 = bnd(base, "HEAD")
    g1, go1 = guard()
    good = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    check("FA8a a Featured Artists-only change (six artists) passes the content boundary", c1 == 0 and "CONTENT BOUNDARY · OK" in o1, o1[-400:])
    check("FA9a the launch guard passes the page with no featured artists and with six (L11, L20)", g0 == 0 and g1 == 0 and "PLOTART LAUNCH · OK" in go1, (go0 + go1)[-400:])
    d = open(gp, encoding="utf-8").read()
    hp = os.path.join(wt, "plotart", "index.html")
    h = open(hp, encoding="utf-8").read()
    tampers = {
        "outside": (gp, d.replace(FEAT.FEAT_END, FEAT.FEAT_END + "<p>Extra</p>", 1)),
        "invented": (gp, d.replace('<ol class="pa-fa-list n-6">', '<ol class="pa-fa-list n-6"><li class="pa-fa-item" data-pa-featured="invented-artist:wabcdef">x</li>', 1)),
        "unpublished": (gp, d.replace("w45csc49r34", "wnotpublished", 1)),
        "image": (gp, d.replace("blowout-series-ii-1-1-", "blowout-series-ii-2-1-", 1)),
        "biography": (gp, d.replace("Hewson has a First-Class", "Hewson has an award-winning First-Class", 1)),
        "counter": (gp, d.replace('<ol class="pa-vgc-hang', '<p class="pa-vgc-count">10 of 25 galleries open</p>\n  <ol class="pa-vgc-hang', 1)),
        "below": (gp, (lambda r: d.replace(r, "", 1).replace("</main>", r + "\n</main>", 1))(FEAT.region(d))),
        # anchored on the artist band since the three-gallery homepage (24 Nov 2026) retired the introduction section
        "homepage": (hp, h.replace("<!-- pa-artist-apply:begin -->", "<!-- pa-home-featured:begin --><!-- pa-home-featured:end -->\n<!-- pa-artist-apply:begin -->", 1)),
    }
    outs = {}
    for k, (f, t) in tampers.items():
        gitc("reset", "-q", "--hard", good)
        open(f, "w", encoding="utf-8").write(t)
        gitc("commit", "-qam", "tamper " + k)
        outs[k] = (bnd(good, "HEAD"), guard())
    check("FA8b the content boundary refuses a change outside the region, an invented item, an unpublished work, a swapped image, altered biography text, the region moved below the collection and any homepage change (a counter inside the generated collection region is the guard's to refuse, L11)",
          all(v[0][0] == 1 for k, v in outs.items() if k != "counter") and "outside the collection and Featured Artists regions" in outs["outside"][0][1]
          and "at most 6 items" in outs["invented"][0][1] and all("differs from what its selection renders" in outs[k][0][1] for k in ("unpublished", "image", "biography"))
          and "plotart/index.html (M): outside the content-only boundary" in outs["homepage"][0][1],
          {k: (v[0][0], v[0][1][-110:]) for k, v in outs.items() if v[0][0] != 1 or k in ("homepage", "outside")})
    check("FA9b the launch guard refuses the same tampered pages (L3 pins outside the regions, L11 counter, L20 inside the region and its position, L6 homepage)",
          all(v[1][0] != 0 for v in outs.values()) and all("L20" in outs[k][1][1] for k in ("invented", "unpublished", "image", "biography"))
          and "25-gallery counter" in outs["counter"][1][1] and "above the complete collection" in outs["below"][1][1] and "L6" in outs["homepage"][1][1],
          {k: (v[1][0], v[1][1][-150:]) for k, v in outs.items() if k in ("counter", "below", "homepage", "biography")})
finally:
    run(["git", "worktree", "remove", "--force", wt])

print("— FA10 in a browser")
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
site = tempfile.mkdtemp(prefix="pa-feat-site-")
try:
    shutil.copytree(os.path.join(ROOT, "plotart"), os.path.join(site, "plotart"))
    open(os.path.join(site, "plotart", "gallery", "index.html"), "w", encoding="utf-8").write(new)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=os.path.join(site, "plotart")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base_url = "http://127.0.0.1:%d/gallery/" % srv.server_address[1]
    problems = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for w, h, tag in ((1440, 900, "desktop"), (820, 1180, "tablet"), (390, 844, "mobile")):
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if SHOTS else 1)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base_url, wait_until="networkidle")
            sec = pg.locator(".pa-fa")
            sec.scroll_into_view_if_needed()
            pg.evaluate("document.querySelectorAll('.pa-fa img').forEach(i => i.loading = 'eager')")
            pg.wait_for_function("[...document.querySelectorAll('.pa-fa img')].every(i => i.complete && i.naturalWidth > 0)", timeout=20000)
            info = pg.evaluate("""() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
                imgs: [...document.querySelectorAll('.pa-fa img')].map(i => {const r = i.getBoundingClientRect(), f = i.parentElement.getBoundingClientRect();
                  return {n: i.naturalWidth, ratio: Math.abs(r.width / r.height - i.naturalWidth / i.naturalHeight), inside: r.left >= f.left - 0.5 && r.right <= f.right + 0.5 && r.top >= f.top - 0.5 && r.bottom <= f.bottom + 0.5,
                          fit: getComputedStyle(i).objectFit}}),
                links: [...document.querySelectorAll('.pa-fa a')].map(a => a.href)})""")
            bad_img = [x for x in info["imgs"] if x["n"] == 0 or x["ratio"] > 0.02 or not x["inside"] or x["fit"] not in ("contain", "fill")]
            if info["sw"] > info["cw"] or len(info["imgs"]) != 6 or bad_img or errs:
                problems.append((tag, info["sw"], info["cw"], bad_img, errs))
            for l in sorted(set(info["links"])):
                r = pg.request.get(l)
                if r.status != 200:
                    problems.append((tag, l, r.status))
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True)
                sec.screenshot(path=os.path.join(SHOTS, "gallery-featured-%s.png" % tag))
            pg.close()
        b.close()
    srv.shutdown()
    check("FA10 at 1440, 820 and 390 px: six whole, undistorted images inside their frames, no sideways scrolling, no script errors, every link resolves", sync_playwright and not problems, problems)
finally:
    shutil.rmtree(site, ignore_errors=True)

check("FA11 the published galleries were only read: every gallery.json, the gallery page and the homepage are byte-for-byte unchanged",
      all(open(f, "rb").read() == b for f, b in LIVE.items()) and open(PAGE, encoding="utf-8").read() == LIVE_DOC)

print("\nPLOTART FEATURED ARTISTS · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
