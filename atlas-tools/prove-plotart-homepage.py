#!/usr/bin/env python3
"""PROVE · PlotArt homepage featured artworks (founder brief 17 Nov 2026; development).

  python3 atlas-tools/prove-plotart-homepage.py [--shots DIR]

HP1  no selection: the region is empty and the homepage is byte-for-byte the page it was
HP2  a selection of real published works renders in the founder's order, at most six, each with the artist's own published
     image (approved alt text), the title and artist name, and a link to its existing artwork page; a featured artist shows
     the artwork the founder chose (not their first work) and links to their gallery
HP3  malformed selections are refused (seven items, a repeat, the same artist twice, an artist without a chosen artwork,
     unexpected fields or values)
HP4  only published, shown work appears: an unknown work, an unpublished artist, a withdrawn work, a removed gallery and an
     artist whose chosen work is withdrawn drop out (nothing is substituted)
HP5  every publication re-renders the region from the page's own selection, so withdrawn work drops out by itself
HP6  the content boundary accepts a homepage change only inside the region and only as its selection renders; it refuses a
     change outside the region and an invented or unpublished item inside it
HP7  the launch guard (L20) passes a real selection and refuses a tampered region
HP8  in a browser at 1440 and 390 px: six images load, no sideways scrolling, every link resolves (--shots saves previews)
Real artist data is only READ (and changed only inside throwaway copies); nothing is written to the live tree.
"""
import copy, functools, glob, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plotart_homepage as HOME   # noqa: E402

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


# A preview selection of six REAL published works (one per artist), read from the published galleries
# (five artworks, and one featured ARTIST shown with the work the founder chose: not that artist's first work)
A = lambda s, w: {"kind": "artwork", "artist": s, "work": w}
SEL = [A("karen-ebbs", "wxurdauu8yk"), A("ciaran-mccoy", "w1yt3pkcsxk"), A("leah-hewson", "w45csc49r34"), A("daniel-chester", "wychp9cm2em"),
       A("anna-marie-savage", "wx8gh81e5bu"), {"kind": "artist", "artist": "nessa-mccormack", "work": "w6stt966ksq"}]
PK = packages()
DOC = open(os.path.join(ROOT, "plotart", "index.html"), encoding="utf-8").read()
LIVE = {f: open(f, "rb").read() for f in glob.glob(os.path.join(ROOT, "plotart", "artists", "*", "gallery.json"))}

print("PROVE · PlotArt homepage featured artworks")
check("HP1 no selection: the region is empty and the page is unchanged (selection [], update and outside are identity)",
      HOME.selection_in(DOC) == [] and HOME.update(DOC, [], PK) == DOC and HOME.outside(DOC) == DOC and HOME.content([], PK) == "")

new = HOME.update(DOC, SEL, PK)
reg = HOME.region(new)
items = re.findall(r'<li class="pa-hf-item" data-pa-home-item="(artwork|artist):([a-z0-9-]+):(w[0-9a-z]+)">(.*?)</li>', reg)
by = {p["artist"]["slug"]: p for p in PK}
first_nessa = next(w["id"] for w in HOME.P.shown(by["nessa-mccormack"]))
ok2, why = len(items) == 6 and [(k, s, w) for k, s, w, _ in items] == [(x["kind"], x["artist"], x["work"]) for x in SEL] and first_nessa != "w6stt966ksq", []
for k, s, w, body in items:
    work = next(x for x in by[s]["works"] if x["id"] == w)
    im = next(i for i in work["images"] if i["role"] == "main")
    src = re.search(r'src="artists/%s/img/([^"]+)"' % s, body)
    alt = re.search(r'alt="([^"]*)"', body)
    href = re.search(r'href="(artists/%s/%s)"' % (s, re.escape(work["slug"] + ".html") if k == "artwork" else ""), body)
    words = (HOME.E(work["title"]), HOME.E(by[s]["artist"]["display_name"])) if k == "artwork" else (HOME.E(by[s]["artist"]["display_name"]), "View the gallery")
    if not (src and os.path.exists(os.path.join(ROOT, "plotart", "artists", s, "img", src.group(1)))
            and src.group(1) in {d["file"] for d in im["derivatives"]} and alt and alt.group(1) == HOME.E(im["alt"])
            and href and os.path.exists(os.path.join(ROOT, "plotart", href.group(1) + ("index.html" if k == "artist" else "")))
            and all(x in body for x in words)):
        ok2 = False
        why.append(s)
check("HP2 six real published works render in the founder's order with their own published images and approved alt text; artworks link to their pages; the featured artist shows the chosen work (not their first) and links to the gallery",
      ok2 and HOME.selection_in(new) == SEL and HOME.outside(new) == DOC, why)


def refused(sel):
    try:
        HOME.check_selection(sel)
        return False
    except ValueError:
        return True


check("HP3 refused: seven items, a repeated item, the same artist featured twice, an artist without a chosen artwork, an extra field, a bad kind, address or artwork id, a non-list",
      all(refused(s) for s in [SEL + [A("fintan-whelan", "wi2ggh2x2rt")], [SEL[0], SEL[0]], [SEL[5], dict(SEL[5], work="w43yzxe0fk8")],
                               [{"kind": "artist", "artist": "karen-ebbs", "work": None}], [{"kind": "artist", "artist": "karen-ebbs"}], [dict(SEL[0], price=1)],
                               [dict(SEL[0], kind="gallery")], [A("../etc", "wxurdauu8yk")], [A("karen-ebbs", "x<script>")], {"artist": "karen-ebbs"}]))

pk4 = copy.deepcopy(PK)
leah = next(p for p in pk4 if p["artist"]["slug"] == "leah-hewson")
for p_, wid in ((leah, "w45csc49r34"), (next(p for p in pk4 if p["artist"]["slug"] == "nessa-mccormack"), "w6stt966ksq")):
    for w in p_["works"]:
        if w["id"] == wid:
            w["availability"] = "withdrawn"       # as an artwork no longer shown publicly (Nessa: the work chosen to represent her)
pk4 = [p for p in pk4 if p["artist"]["slug"] != "anna-marie-savage"]   # as a gallery taken down
sel4 = SEL + []
sel4[4] = {"artist": "anna-marie-savage", "work": "wx8gh81e5bu"}
r4 = HOME.resolve([SEL[0], A("karen-ebbs", "wnotreal00"), {"kind": "artist", "artist": "not-published-artist", "work": "wabcdef"}, SEL[2], SEL[4], SEL[5], ], pk4)
r4b = HOME.resolve([A("nessa-mccormack", "w43yzxe0fk8")], pk4)
check("HP4 only published, shown work appears: an unknown work, an unpublished artist, a withdrawn work, a removed gallery and an artist whose chosen work is withdrawn drop out (no other work is substituted)",
      [(k, p["artist"]["slug"], w["id"]) for k, p, w, _ in r4] == [("artwork", "karen-ebbs", "wxurdauu8yk")] and len(r4b) == 1)

tmp = tempfile.mkdtemp(prefix="pa-home-")
try:
    os.makedirs(os.path.join(tmp, "plotart"))
    open(os.path.join(tmp, "plotart", "index.html"), "w", encoding="utf-8").write(new)
    ch = HOME.refresh(tmp, pk4)
    after = open(os.path.join(tmp, "plotart", "index.html"), encoding="utf-8").read()
    same = HOME.refresh(tmp, pk4)
    check("HP5 a later publication keeps the founder's selection and order and drops the withdrawn work, the removed gallery and the artist whose chosen work was withdrawn, by itself",
          ch and not same and [x["artist"] for x in HOME.selection_in(after)] == ["karen-ebbs", "ciaran-mccoy", "daniel-chester"]
          and HOME.outside(after) == DOC)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("— HP6/HP7 the content boundary and the launch guard (throwaway worktree)")
wt = tempfile.mkdtemp(prefix="pa-home-wt-")
shutil.rmtree(wt)
run(["git", "worktree", "add", "-q", "--detach", wt, "HEAD"])
gitc = lambda *a: run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid"] + list(a), cwd=wt)
bnd = lambda b, r: run([sys.executable, os.path.join(wt, "atlas-tools", "release", "plotart-content-boundary.py"), b, r], cwd=wt)
guard = lambda: run([sys.executable, "atlas-tools/prove-plotart-launch.py", ".", "--switches", "atlas-tools/release/plotart-launch-switches.json",
                     "--manifest", "atlas-tools/release/plotart-launch-manifest.json"], cwd=wt)
try:
    base = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    hp = os.path.join(wt, "plotart", "index.html")
    HOME.refresh(wt, packages(wt), SEL)
    gitc("commit", "-qam", "test: homepage featured artworks")
    c1, o1 = bnd(base, "HEAD")
    g1, go1 = guard()
    good = run(["git", "rev-parse", "HEAD"], cwd=wt)[1].strip()
    check("HP6a a homepage-only change (six featured works) passes the content boundary", c1 == 0 and "CONTENT BOUNDARY · OK" in o1, o1[-400:])
    check("HP7a the launch guard passes the page with six featured works (L20)", g1 == 0 and "PLOTART LAUNCH · OK" in go1, go1[-400:])
    d = open(hp, encoding="utf-8").read()
    tampers = {
        "outside": d.replace(HOME.HOME_END, HOME.HOME_END + "<p>Extra</p>", 1),
        "invented": d.replace('<ul class="pa-hf-grid">', '<ul class="pa-hf-grid"><li class="pa-hf-item" data-pa-home-item="artwork:invented-artist:wabcdef">x</li>', 1),
        "unpublished": d.replace("w45csc49r34", "wnotpublished", 1),
        "image": d.replace("blowout-series-ii-1-1-", "blowout-series-ii-2-1-", 1),
    }
    outs = {}
    for k, t in tampers.items():
        gitc("reset", "-q", "--hard", good)
        open(hp, "w", encoding="utf-8").write(t)
        gitc("commit", "-qam", "tamper " + k)
        outs[k] = (bnd(base, "HEAD"), guard())
    check("HP6b the content boundary refuses a change outside the region, an invented item, an unpublished work and a swapped image",
          all(v[0][0] == 1 for v in outs.values()) and "outside the homepage featured region" in outs["outside"][0][1]
          and "at most 6 items" in outs["invented"][0][1] and all("differs from what its selection renders" in outs[k][0][1] for k in ("unpublished", "image")),
          {k: v[0][1][-160:] for k, v in outs.items()})
    check("HP7b the launch guard refuses the same tampered pages (L3 pin outside the region, L20 inside it)",
          all(v[1][0] != 0 for v in outs.values()) and all("L20" in outs[k][1][1] for k in ("invented", "unpublished", "image")),
          {k: v[1][1][-160:] for k, v in outs.items()})
finally:
    run(["git", "worktree", "remove", "--force", wt])

print("— HP8 in a browser")
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
site = tempfile.mkdtemp(prefix="pa-home-site-")
try:
    shutil.copytree(os.path.join(ROOT, "plotart"), os.path.join(site, "plotart"))
    open(os.path.join(site, "plotart", "index.html"), "w", encoding="utf-8").write(new)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=os.path.join(site, "plotart")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base_url = "http://127.0.0.1:%d/" % srv.server_address[1]
    problems = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for w, h, tag in ((1440, 900, "desktop"), (390, 844, "mobile")):
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2 if SHOTS else 1)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base_url, wait_until="networkidle")
            sec = pg.locator(".pa-home-feat")
            sec.scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            pg.evaluate("document.querySelectorAll('.pa-home-feat img').forEach(i => i.loading = 'eager')")
            pg.wait_for_function("[...document.querySelectorAll('.pa-home-feat img')].every(i => i.complete && i.naturalWidth > 0)", timeout=20000)
            info = pg.evaluate("""() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
                imgs: [...document.querySelectorAll('.pa-home-feat img')].map(i => i.naturalWidth),
                links: [...document.querySelectorAll('.pa-home-feat a')].map(a => a.href),
                order: [...document.querySelectorAll('main > section, body > section, .pa-sec')].map(s => s.id || s.className).slice(0, 4)})""")
            if info["sw"] > info["cw"] or len(info["imgs"]) != 6 or min(info["imgs"]) == 0 or errs:
                problems.append((tag, info, errs))
            for l in info["links"]:
                r = pg.request.get(l)
                if r.status != 200:
                    problems.append((tag, l, r.status))
            if SHOTS:
                os.makedirs(SHOTS, exist_ok=True)
                sec.screenshot(path=os.path.join(SHOTS, "homepage-featured-%s.png" % tag))
                pg.screenshot(path=os.path.join(SHOTS, "homepage-context-%s.png" % tag), clip=None, full_page=False)
            pg.close()
        b.close()
    srv.shutdown()
    check("HP8 at 1440 and 390 px: six images load, no sideways scrolling, no script errors, every link resolves", sync_playwright and not problems, problems)
finally:
    shutil.rmtree(site, ignore_errors=True)

check("HP9 the published galleries were only read: every gallery.json is byte-for-byte unchanged",
      all(open(f, "rb").read() == b for f, b in LIVE.items()) and open(os.path.join(ROOT, "plotart", "index.html"), encoding="utf-8").read() == DOC)

print("\nPLOTART HOMEPAGE FEATURED · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
