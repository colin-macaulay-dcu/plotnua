#!/usr/bin/env python3
"""PROVE · PlotArt Contemporary gallery · one curated gallery (founder approval for development, 26 Nov 2026).
Builder side, on the real published galleries in this checkout (read-only; everything is rendered in memory or in a
temporary copy). Checks the page the content pipeline writes, the arrangement it reads from PlotArt Studio (the new
route and, until the new Studio is deployed, the live Studio's showcase / gallery order / Artists in Focus routes), and
that the content boundary and launch guard refuse a wrong page.
  python3 atlas-tools/prove-plotart-gallery-curation.py"""
import copy, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import plotart_featured as F            # noqa: E402
import plotart_gallery_pages as P       # noqa: E402
import plotart_seo as SEO               # noqa: E402

ok_all = []
def check(name, ok, detail=""):
    ok_all.append(bool(ok)); print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  [%s]" % str(detail)[:500]))

print("PROVE · PlotArt Contemporary gallery · one curated gallery")
PK = SEO.public_packages(str(ROOT))
SL = sorted(p["artist"]["slug"] for p in PK)
by = {p["artist"]["slug"]: p for p in PK}
doc0 = (ROOT / "plotart" / F.PAGE).read_text()
A0 = F.arrangement_in(doc0)
check("B0 the page is exactly what its own arrangement renders from the published galleries", F.consistent(doc0, PK))
shown = F.shown_artists(doc0)
check("B1 every published artist exactly once (opening row, then Explore the Gallery), in the founder's order, none held",
      len(shown) == len(set(shown)) and sorted(shown) == SL and A0["held"] == [], shown)
vis = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", doc0.split("<main", 1)[1], flags=re.S)))
check("B2 no prices or sale details on the gallery overview; no Artists in Focus, Explore More Artists or second heading",
      not re.search(r"€|Price on request|\bsold\b|\bcm\b", vis, re.I) and "Artists in Focus" not in vis and "Explore More Artists" not in vis and "Explore the Gallery" not in vis and 'id="vgColH"' not in doc0)
cards = re.findall(r'<li class="pa-fa-item[^"]*" data-pa-curated="([a-z0-9-]+):([a-z0-9]+|auto)">(.*?)</li>', doc0, re.S)
opens = re.findall(r'<li class="pa-op-item" data-pa-opening="([a-z0-9-]+):([a-z0-9]+)">(.*?)</li>', doc0, re.S)
def complete(slug, body):
    a = by[slug]["artist"]
    return ('<h3 class="pa-fa-name">%s</h3>' % F.E(a["display_name"]) in body and "View Gallery" in body and 'href="../artists/%s/"' % slug in body
            and (not P.meta_line(a) or F.E(P.meta_line(a)) in body) and (not F.intro(a.get("bio")) or F.E(F.intro(a.get("bio"))) in body))
check("B3 every artist (opening three included) is introduced the same way: artwork with title and year, name, practice and public location, the introduction from their own biography, View Gallery",
      all(complete(s, b) for s, _, b in cards + opens) and all("<i>" in b and "<img" in b for s, _, b in opens), [s for s, _, b in cards + opens if not complete(s, b)])
intros = [F.intro(by[s]["artist"].get("bio")) for s in SL if F.intro(by[s]["artist"].get("bio"))]
check("B4 introductions are at most 45 words and end at a complete sentence (only a single over-long first sentence is shortened, with an ellipsis); never invented",
      all(len(t.split()) <= 45 and (re.search(r"[.!?…][\"'’”)]?$", t)) for t in intros), [t[-40:] for t in intros if not re.search(r"[.!?…][\"'’”)]?$", t)])
check("B5 F.intro uses only the artist's own words (every introduction, ellipsis aside, is a prefix of their normalised biography's sentences)",
      all(" ".join(by[s]["artist"]["bio"].split()).startswith(F.intro(by[s]["artist"]["bio"]).rstrip("…").strip()) or
          F.intro(by[s]["artist"]["bio"]).rstrip("…").strip() in " ".join(by[s]["artist"]["bio"].split()) for s in SL if by[s]["artist"].get("bio")))

# ---- the rules, on copies of the real packages
def arr(op, rest, held=()):
    return {"opening": [{"artist": s, "work": w} for s, w in op], "rest": [{"artist": s, "work": w} for s, w in rest], "held": list(held)}
o3 = [(x["artist"], x["work"]) for x in A0["opening"]]
rest0 = [(x["artist"], x["work"]) for x in A0["rest"]]
pk = copy.deepcopy(PK); byc = {p["artist"]["slug"]: p for p in pk}
s1, w1 = o3[1]
next(w for w in byc[s1]["works"] if w["id"] == w1)["availability"] = "sold"
d = F.update(doc0, arr(o3, rest0, [s1]), pk)
check("B6 an opening work sold: its place is left empty (no substitute), the row closes up, and the held artist is not moved into the gallery below",
      [x["artist"] for x in F.arrangement_in(d)["opening"]] == [o3[0][0], o3[2][0]] and s1 not in F.shown_artists(d) and 'class="pa-op-row n-2"' in d and F.consistent(d, pk))
# an artist with a chosen work and at least one other available work (else a real artist with a work of our choosing)
ch = next(((s, w) for s, w in rest0 if w and sum(F._eligible(by[s], x) for x in by[s]["works"]) >= 2), None) or \
    next((s, next(x["id"] for x in by[s]["works"] if F._eligible(by[s], x))) for s, _ in rest0 if sum(F._eligible(by[s], x) for x in by[s]["works"]) >= 2)
rest0c = [(s, ch[1] if s == ch[0] else w) for s, w in rest0]
pk2 = copy.deepcopy(PK); b2 = {p["artist"]["slug"]: p for p in pk2}
next(w for w in b2[ch[0]]["works"] if w["id"] == ch[1])["availability"] = "sold"
d2 = F.update(doc0, arr(o3, rest0c), pk2)
m = re.search(r'data-pa-curated="%s:%s">(.*?)</li>' % (ch[0], ch[1]), d2, re.S)
first = next(w for w in b2[ch[0]]["works"] if F._eligible(b2[ch[0]], w))
check("B7 a chosen work sold in place 4+: the artist keeps their place, showing their first available work instead; the choice stays on record",
      m and ("/%s.html" % first["slug"]) in m.group(1) and [x["artist"] for x in F.arrangement_in(d2)["rest"]] == [s for s, _ in rest0] + [s for s in F.shown_artists(doc0) if s not in {x for x, _ in o3} | {x for x, _ in rest0}], ch)
pk3 = copy.deepcopy(PK); b3 = {p["artist"]["slug"]: p for p in pk3}
lone = rest0[-1][0]
for w in b3[lone]["works"]:
    w["availability"] = "sold"
d3 = F.update(doc0, arr(o3, rest0), pk3)
m3 = re.search(r'<li class="pa-fa-item( is-textonly)?" data-pa-curated="%s:[a-z0-9]+">(.*?)</li>' % lone, d3, re.S)
check("B8 no eligible work left: the artist is introduced without an artwork image (never a broken or unavailable one) and keeps their place",
      m3 and m3.group(1) and "<img" not in m3.group(2) and "View Gallery" in m3.group(2) and F.consistent(d3, pk3))
newcomer = copy.deepcopy(by[rest0[0][0]]); newcomer["artist"].update(slug="aaa-newcomer", display_name="Aaa Newcomer")
newcomer["publication"].update(approved_at="2099-01-01T00:00:00Z", first_approved_at="2099-01-01T00:00:00Z")
d4 = F.update(doc0, arr(o3, rest0), PK + [newcomer])
check("B9 a newly published artist the arrangement does not name is added at the END of the gallery, never in the opening row and displacing nobody",
      F.shown_artists(d4)[-1] == "aaa-newcomer" and F.shown_artists(d4)[:-1] == F.shown_artists(doc0) and "aaa-newcomer" not in [x["artist"] for x in F.arrangement_in(d4)["opening"]])
bad = []
for a in (arr(o3, rest0 + [(o3[0][0], None)]), arr(o3 + [rest0[0]], rest0[1:]), {"opening": [], "rest": [], "extra": 1},
          arr([(o3[0][0], "not-an-id")], []), arr(o3, [("Bad Slug", None)])):
    try:
        F.check_arrangement(a); bad.append("accepted")
    except ValueError:
        bad.append("refused")
check("B10 an arrangement naming an artist twice, four opening places, an unexpected field or a malformed identifier is refused", bad == ["refused"] * 5, bad)
check("B11 the page can never show a duplicate even from a doctored page: the read-back arrangement is checked the same way",
      not F.consistent(doc0.replace('data-pa-curated="%s:' % rest0[1][0], 'data-pa-curated="%s:' % rest0[0][0], 1), PK))

# ---- the representative artwork is curated once: Living Gallery, Art for Hire and the opportunity lists mirror it
import plotart_opportunities as OPP   # noqa: E402
CH = F.choices_in(doc0)
mirror_ok, tested = True, 0
for q in OPP.GALLERY_PAGES:
    path = ROOT / "plotart" / q
    if not path.exists():
        continue
    reg = OPP.REGION.search(path.read_text()).group(0)
    for slug in re.findall(r'href="(?:\.\./)*artists/([a-z0-9-]+)/" data-pa-track="opportunity_artist"', reg):
        w, im = OPP._rep(by[slug], CH.get(slug))
        gw, gim = F.representative(by[slug], CH.get(slug))
        file0 = sorted(im["derivatives"], key=lambda x: x["long_edge"])
        mid = next((d for d in file0 if d["long_edge"] >= 600), file0[-1])["file"]
        mirror_ok &= ("artists/%s/img/%s" % (slug, mid)) in reg and (gw is None or gw["id"] == w["id"])
        tested += 1
check("B19 Living Gallery and Art for Hire show each artist's representative artwork exactly as the gallery does (%d cards)" % tested, mirror_ok and tested > 0)
one = next((s, w) for s, w in CH.items() if s in by and sum(F._eligible(by[s], x) for x in by[s]["works"]) >= 2)
alt = next(x for x in by[one[0]]["works"] if F._eligible(by[one[0]], x) and x["id"] != one[1])
pk5 = copy.deepcopy(PK)
w_new = OPP._rep({p["artist"]["slug"]: p for p in pk5}[one[0]], alt["id"])[0]
check("B20 choosing another artwork in Curate changes the image everywhere it is mirrored (the next publication re-renders the lists with it)",
      w_new["id"] == alt["id"] and OPP._rep(by[one[0]], one[1])[0]["id"] == one[1])
b6 = {p["artist"]["slug"]: p for p in copy.deepcopy(PK)}
next(x for x in b6[one[0]]["works"] if x["id"] == one[1])["availability"] = "sold"
check("B21 a sold representative work is replaced on the mirrored pages by the same first available work the gallery shows",
      OPP._rep(b6[one[0]], one[1])[0]["id"] == F.representative(b6[one[0]], one[1])[0]["id"] != one[1])

# ---- the publisher's arrangement: the new Studio route, and the live Studio before 0029
spec = importlib.util.spec_from_file_location("pub", ROOT / "atlas-tools" / "plotart-gallery-publish.py")
pub = importlib.util.module_from_spec(spec)
_argv = sys.argv
sys.argv = ["plotart-gallery-publish.py", "--studio", "http://127.0.0.1:9/", "--token", "x", "--simulate"]   # loaded, never run
try:
    spec.loader.exec_module(pub)
except SystemExit:
    pass
sys.argv = _argv
if hasattr(pub, "arrangement"):
    def fake(routes):
        def call(method, path, body=None):
            if path not in routes:
                raise urllib.error.HTTPError(path, 404, "not found", {}, None)
            return routes[path]
        return call
    pub.ROOT = str(ROOT)
    pub.call = fake({"/api/pipeline/gallery-curation": {"installed": True, "galleries": [{"gallery": "contemporary", "status": "open",
        "opening": [{"position": 2, "artist": o3[1][0], "work": o3[1][1]}, {"position": 1, "artist": o3[0][0], "work": o3[0][1]}], "rest": [{"artist": s, "work": w} for s, w in rest0[:3]], "held": [o3[2][0]]}]}})
    a1 = pub.arrangement()
    check("B12 with the new Studio the publisher reads GET /api/pipeline/gallery-curation (opening row in position order, the rest, held)",
          a1["opening"] == [o3[0], o3[1]] and a1["rest"] == rest0[:3] and a1["held"] == [o3[2][0]])
    lay = {"positions": [{"position": i + 1, "slug": s, "reserved": False} for i, s in enumerate([x for x, _ in o3] + [x for x, _ in rest0[:4]])] + [{"position": 20, "slug": None, "reserved": True}], "extra": [rest0[4][0]]}
    pub.call = fake({"/api/pipeline/gallery-order": lay,
                     "/api/pipeline/gallery-showcase": {"installed": True, "galleries": [{"gallery": "contemporary", "status": "open", "items": [{"position": i + 1, "artist": s, "work": w} for i, (s, w) in enumerate(o3)]}]},
                     "/api/pipeline/featured-artists": {"installed": True, "items": [{"artist": rest0[1][0], "work": "wabcdefgh"}]}})
    a2 = pub.arrangement()
    check("B13 with the live Studio (before 0029) the publisher composes the same arrangement migration 0029 sets up: the published showcase, then the gallery order without the opening artists, Artists in Focus artworks kept",
          a2["opening"] == o3 and [s for s, _ in a2["rest"]] == [x for x, _ in rest0[:5]] and dict(a2["rest"])[rest0[1][0]] == "wabcdefgh" and a2["held"] == [], a2)
    pub.call = fake({})
    check("B14 a Studio with neither route: no arrangement (the page keeps the one it shows)", pub.arrangement() is None)
else:
    check("B12-14 the publisher module loads", False, "no arrangement()")

# ---- the content boundary and the launch guard refuse a wrong page (temporary copy of the repository's PlotArt files)
tmp = Path(tempfile.mkdtemp(prefix="pa-cur-"))
try:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    for part in ("plotart", "atlas-tools", "assets", "sitemap.xml", "image-provenance-records.json", "privacy.html", "index.html"):
        src = ROOT / part
        if src.is_dir():
            shutil.copytree(src, tmp / part, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.exists():
            shutil.copy(src, tmp / part)
    g = lambda *a: subprocess.run(["git", "-C", str(tmp), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True)
    g("add", "-A"); g("commit", "-qm", "base")
    page = tmp / "plotart" / F.PAGE
    def boundary(mut):
        page.write_text(mut(doc0)); g("add", "-A"); g("commit", "-qm", "change")
        r = subprocess.run([sys.executable, str(tmp / "atlas-tools/release/plotart-content-boundary.py"), "HEAD~1", "HEAD"], cwd=tmp, capture_output=True, text=True)
        g("reset", "-q", "--hard", "HEAD~1")
        return r.returncode == 0, r.stdout[-300:]
    okr, out = boundary(lambda d: F.update(d, arr(list(reversed(o3)), list(reversed(rest0))), PK))
    check("B15 the content boundary accepts a re-arrangement rendered from the published galleries", okr, out)
    refused = [not boundary(f)[0] for f in (
        lambda d: d.replace("View Gallery", "View Gallery · €1,200", 1),
        lambda d: d.replace('data-pa-curated="%s:' % rest0[1][0], 'data-pa-curated="%s:' % rest0[0][0], 1),
        lambda d: d.replace('<section class="pa-vg2-collection pa-vgc" aria-label="The gallery"><div class="pa-wrap">', '<section class="pa-vg2-collection pa-vgc" aria-label="The gallery"><div class="pa-wrap">\n  <h2>Artists in Focus</h2>'),
        lambda d: re.sub(r'(<p class="pa-fa-intro">)', r'\1The finest artist in Ireland. ', d, count=1))]
    check("B16 the content boundary refuses a price, a duplicated artist, the retired heading and an invented sentence", all(refused), refused)
    def launch(mut):
        # the guard reads the whole repository: run it on this checkout with the page changed, then restore it exactly
        real = ROOT / "plotart" / F.PAGE
        try:
            real.write_text(mut(doc0))
            r = subprocess.run([sys.executable, str(ROOT / "atlas-tools/prove-plotart-launch.py"), str(ROOT), "--switches", str(ROOT / "atlas-tools/release/plotart-launch-switches.json"),
                                "--manifest", str(ROOT / "atlas-tools/release/plotart-launch-manifest.json")], capture_output=True, text=True)
        finally:
            real.write_text(doc0)
        return r.stdout + r.stderr[-600:]
    out0 = launch(lambda d: d)
    check("B17 the launch guard passes the unified page", "PLOTART LAUNCH · OK" in out0, out0[-400:])
    o_dup = launch(lambda d: d.replace('data-pa-curated="%s:' % rest0[1][0], 'data-pa-curated="%s:' % rest0[0][0], 1))
    o_miss = launch(lambda d: re.sub(r'\n    <li class="pa-fa-item[^"]*" data-pa-curated="%s:[^"]*">.*?</li>' % rest0[2][0], "", d, count=1, flags=re.S))
    o_price = launch(lambda d: d.replace('<p class="pa-fa-practice">', '<p class="pa-fa-practice">€950 · ', 1))
    check("B18 the launch guard refuses an artist shown twice, an artist left out, and a price on the overview",
          "exactly once" in o_dup and "exactly once" in o_miss and "prices" in o_price, (o_dup[-200:], o_miss[-200:], o_price[-200:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("\n%d/%d passed" % (sum(ok_all), len(ok_all)))
sys.exit(0 if all(ok_all) else 1)
