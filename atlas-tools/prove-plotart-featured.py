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
FA12 Browse All Artworks (21 Nov 2026): one link beside the heading to All Artworks, with that page's own counts, which follow
     publications; no available work -> no link
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
    """The Gallery order as the page shows it (positions from the twenty-five index; galleries without a position in the
    order the wall shows them): the order the Studio sent when the page was last built."""
    reg = doc[slice(*P.vg_region(doc))]
    pos = []
    for n, (st, body) in enumerate(re.findall(r'<li class="pa-vgc-pos is-(pub|res|prep|av)">(.*?)</li>', reg), 1):
        m = re.search(r'artists/([a-z0-9-]+)/', body)
        pos.append({"position": n, "slug": m.group(1) if st == "pub" else None, "reserved": st == "res", "assigned": st == "prep"})
    numbered = {x["slug"] for x in pos if x["slug"]}
    return {"positions": pos, "extra": [x for x in re.findall(r'href="\.\./artists/([a-z0-9-]+)/" data-pa-track="vg_artist"', reg) if x not in numbered]}


LAY = layout_from(LIVE_DOC)


def build(doc, sel, pk, lay=LAY):
    """What the publisher's regrid() makes: Featured Artists, then Explore More Artists without the featured artists."""
    d = FEAT.update(doc, sel, pk)
    a, b = P.vg_region(d)
    return d[:a] + P.vg_collection(P.gallery_order(pk), layout=lay, featured=[x["artist"] for x in FEAT.selection_in(d)]) + d[b:]


wall = lambda d: re.findall(r'href="\.\./artists/([a-z0-9-]+)/" data-pa-track="vg_artist"', d[slice(*P.vg_region(d))])
index = lambda d: re.findall(r'<li class="pa-vgc-pos is-[a-z]+">.*?</li>', d[slice(*P.vg_region(d))])
both_out = lambda d: FEAT.outside(d[:P.vg_region(d)[0]] + P.VG_BEGIN + P.VG_END + d[P.vg_region(d)[1]:])
DOC = build(LIVE_DOC, [], PK)                         # the page with no selection: every published artist on the wall
LIVE = {f: open(f, "rb").read() for f in glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json"))}
by = {p["artist"]["slug"]: p for p in PK}
coll = lambda d: d[slice(*P.vg_region(d))]

print("PROVE · PlotArt Artists' Gallery · Featured Artists")
check("FA1 no selection: the region is empty, every published artist is on the wall, and nothing else on the page differs",
      FEAT.selection_in(DOC) == [] and FEAT.update(DOC, [], PK) == DOC and FEAT.outside(DOC) == DOC and FEAT.content([], PK) == ""
      and sorted(wall(DOC)) == sorted(p["artist"]["slug"] for p in PK) and both_out(DOC) == both_out(LIVE_DOC) and index(DOC) == index(LIVE_DOC))

new = build(DOC, SEL, PK)
reg = FEAT.region(new)
items = re.findall(r'<li class="pa-fa-item" data-pa-featured="([a-z0-9-]+):(w[0-9a-z]+)">(.*?)</li>', reg)
first_nessa = next(w["id"] for w in P.shown(by["nessa-mccormack"]))
ok2, why = (len(items) == 6 and [(s, w) for s, w, _ in items] == [(x["artist"], x["work"]) for x in SEL] and first_nessa != "w6stt966ksq"
            and 'Selected by PlotArt</p><h2 id="featArtH">Featured Artists</h2><p class="pa-fa-lede">A changing selection of artists and their work.</p>' in reg), []
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
            and index(d) == index(DOC) and both_out(d) == both_out(DOC))
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
def _counts(pk):
    region = FEAT.content(SEL, pk)
    m = re.search(r'<p class="pa-fa-browse"><a class="pa-btn pa-btn--ghost" href="\.\./artworks/" data-pa-track="gallery_browse_artworks">'
                  r'Browse All Artworks <span aria-hidden="true">&rarr;</span></a><span class="pa-fa-browse-n">Explore (\d+) original works? by (\d+) artists?\.</span></p>', region)
    coll = re.search(r'>(\d+) original works? by (\d+) artists?<', C.collection(pk))
    return (m and (int(m.group(1)), int(m.group(2)))), (coll and (int(coll.group(1)), int(coll.group(2)))), region
now, coll, reg = _counts(PK)
fewer = copy.deepcopy(PK)
gone = next(p for p in fewer if p["artist"]["slug"] not in [x["artist"] for x in SEL])   # an unfeatured artist's gallery is removed
fewer.remove(gone)
one = copy.deepcopy(PK)
next(w for w in by["karen-ebbs"]["works"] if w["availability"] == "available")       # sanity: Karen has available work
for p in one:
    if p["artist"]["slug"] == "karen-ebbs":
        next(w for w in p["works"] if w["availability"] == "available")["availability"] = "sold"
n2, c2, _ = _counts(fewer)
n3, c3, _ = _counts(one)
check("FA12 Browse All Artworks sits in the Featured Artists heading, links to the All Artworks page, and its counts equal that page's own (%s)" % (now,),
      now is not None and now == coll and reg.count('href="../artworks/"') == 1 and reg.index("pa-fa-browse") < reg.index("pa-fa-list")
      and 'class="pa-fa-head pa-fa-head--browse"' in reg and "pa-rf" not in reg, (now, coll))
check("FA12b the counts follow publications: a removed gallery and a work no longer available change them, always agreeing with All Artworks (%s -> %s, %s)" % (now, n2, n3),
      n2 == c2 and n3 == c3 and n2[1] == now[1] - 1 and n2[0] < now[0] and n3 == (now[0] - 1, now[1]), (n2, c2, n3, c3))
_empty = [dict(copy.deepcopy(p), works=[dict(w, availability="sold") for w in p["works"]]) for p in PK]
check("FA12c with no available work there is no Browse link (and the heading keeps its usual layout)", "pa-fa-browse" not in FEAT.content(SEL, _empty)
      and 'class="pa-fa-head"' in FEAT.content(SEL, _empty))

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
        "homepage": (hp, h.replace("<section class=\"pa-sec pa-sec--deep pa-intro\"", "<!-- pa-home-featured:begin --><!-- pa-home-featured:end -->\n<section class=\"pa-sec pa-sec--deep pa-intro\"", 1)),
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
