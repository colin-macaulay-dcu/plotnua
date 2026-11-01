#!/usr/bin/env python3
"""
PROVE THE IDEA BOARD (Phase 1, 1 Nov 2026).

  Part 1  the repository as it stands: the builder's --check passes; ideas.html is noindex, has no structured data,
          shows exactly the approved ideas (or the honest empty board); the Library card shows the latest three
          (or the invitation), carries the "not yet researched" caption, links to ideas.html and has no photograph.
  Part 2  planted faults, each built in a throw-away copy, each of which the builder must REFUSE:
          a non-public field, a name/e-mail/phone/link in the text, markup, an unknown area or county, a day-level
          date, an internal id, an exact timestamp, a submission reference, a Discovery link to a page that does not exist,
          the wrong order, an over-long text.
  Part 3  planted faults in the BUILT output, each of which Part 1's checks must catch: noindex removed, a fourth
          note on the card, the caption removed, an idea on the page that is not approved (a fictional idea), an
          unescaped tag, an e-mail address shown. (A change to the Library outside the card block is refused by the
          pipeline's boundary check against main: see plotnua-ideas-publish.py and the end-to-end test.)

  python3 atlas-tools/prove-idea-board.py
"""
import html, json, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
B = HERE / "build-idea-board.py"
fails = []


def ok(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond: fails.append(msg)


def checks(root, ideas):
    """Return a list of problems with the built output in `root` for the approved `ideas`."""
    bad = []
    pg = (root / "ideas.html").read_text(encoding="utf-8")
    lib = (root / "discoveries.html").read_text(encoding="utf-8")
    if '<meta name="robots" content="noindex, follow">' not in pg: bad.append("page is not noindex")
    if "ld+json" in pg: bad.append("page carries structured data")
    wall = re.search(r'<ul class="ib-wall">(.*?)</ul>', pg, re.S).group(1)
    shown = [html.unescape(t) for t in re.findall(r'<li class="ib-n"><p>(.*?)</p>', wall, re.S)]
    if shown != [i["text"] for i in ideas]: bad.append("page notes are not exactly the approved ideas")
    if not ideas and "Your idea could be the first on the board." not in wall: bad.append("empty page lacks the invitation")
    glimpse = re.search(r'<section class="ib-glimpse"[^>]*><ul[^>]*>(.*?)</ul>', pg, re.S).group(1)
    if [html.unescape(t) for t in re.findall(r'<li>(.*?)</li>', glimpse)] != [i["text"] for i in ideas[:3]]: bad.append("mobile glimpse is not the latest three approved ideas")
    m = re.search(r"<!-- PLOTNUA IDEA BOARD CARD · BEGIN.*?<!-- PLOTNUA IDEA BOARD CARD · END -->", lib, re.S)
    if not m: bad.append("Library has no Idea Board card"); return bad
    c = m.group(0)
    for part in (wall, glimpse, c):
        if set(re.findall(r"</?([a-z]+)", part.replace("<!--", ""))) - {"a", "p", "li", "ul", "span"}: bad.append("an unexpected tag in the ideas"); break
    notes = [html.unescape(t) for t in re.findall(r'<li class="ib-note">(.*?)</li>', c)]
    if notes != [i["text"] for i in ideas[:3]]: bad.append("card notes are not the latest three approved ideas")
    if not ideas and "Your idea could be the first on the board." not in c: bad.append("empty card lacks the invitation")
    if "Homeowner ideas · not yet researched" not in c: bad.append("card caption missing")
    if 'href="ideas.html"' not in c or "<img" in c: bad.append("card link or no-photo rule broken")
    if 'class="lib-next"' in lib: bad.append("teaser card still present")
    if lib.count("/* PLOTNUA IDEA BOARD CARD v1 · BEGIN") != 1: bad.append("card styles missing or repeated")
    if re.search(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", wall + c, flags=re.S)):
        bad.append("an e-mail address is shown")
    return bad


def build(root, data, endpoint=None):
    p = root / "data.json"; p.write_text(json.dumps(data), encoding="utf-8")
    cmd = [sys.executable, str(B), "--root", str(root), "--data", str(p)] + (["--endpoint", endpoint] if endpoint else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def tree():
    t = pathlib.Path(tempfile.mkdtemp(prefix="ib-proof-"))
    shutil.copy(ROOT / "discoveries.html", t / "discoveries.html")
    for d in sorted(ROOT.glob("discovery-*.html"))[:3]: shutil.copy(d, t / d.name)
    return t


def idea(n, **kw):
    d = {"text": "PROOF TEST %d: a quiet corner of the garden for a reading bench" % n, "area": "Garden", "month": "2026-%02d" % (12 - n)}
    d.update(kw); return d


print("PART 1 · the repository")
r = subprocess.run([sys.executable, str(B), "--check"], capture_output=True, text=True)
ok(r.returncode == 0, "builder --check: " + r.stdout.strip())
snap = json.loads((HERE / "idea-board" / "approved-ideas.json").read_text(encoding="utf-8"))["ideas"]
probs = checks(ROOT, snap)
ok(not probs, "built page and card match the approved snapshot (%d ideas) %s" % (len(snap), probs or ""))

print("PART 2 · the builder refuses bad input")
disc = sorted(p.name for p in ROOT.glob("discovery-*.html"))[0]
good = [idea(1), idea(2, county="Cork", became_discovery=disc), idea(3, area="Art"), idea(4)]
t = tree()
rc, out = build(t, {"ideas": good})
ok(rc == 0, "four valid test ideas build")
probs = checks(t, good)
ok(not probs, "page shows all four; card shows the latest three %s" % (probs or ""))
pg = (t / "ideas.html").read_text(encoding="utf-8")
ok("Now a PlotNua Discovery" in pg and 'href="%s"' % disc in pg, "the 'Now a Discovery' link is shown")
ok("Co. Cork" in pg and "October 2026" in pg and not re.search(r"\b\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December)", pg), "county (when chosen) and month and year only are shown")
rc, _ = build(t, {"ideas": []})
ok(rc == 0 and not checks(t, []), "the empty board builds with the invitation")
rc, _ = build(t, {"ideas": good}, "http://127.0.0.1:8799/v1/ideas")
ok(rc == 0 and 'action="http://127.0.0.1:8799/v1/ideas"' in (t / "ideas.html").read_text(encoding="utf-8"), "with an endpoint, the form appears")
rc, _ = build(t, {"ideas": good}, "https://evil.example.com/collect")
ok(rc != 0, "REFUSED: a form endpoint other than the Idea Board Worker")
faults = {
    "a non-public field (e-mail)": [idea(1, email="a@b.ie")],
    "a non-public field (ip)": [idea(1, ip="1.2.3.4")],
    "an e-mail address in the text": [idea(1, text="Write to me at someone@example.ie about it")],
    "a phone number in the text": [idea(1, text="Ring me on 087 123 4567 about the hedge")],
    "a link in the text": [idea(1, text="See my plans at www.example.ie for the hedge")],
    "markup in the text": [idea(1, text="A garden <script>alert(1)</script> bench")],
    "an unknown area": [idea(1, area="Crypto")],
    "an unknown county": [idea(1, county="Atlantis")],
    "a day-level date": [idea(1, month="2026-11-01")],
    "a Discovery link to a page that does not exist": [idea(1, became_discovery="discovery-imaginary.html")],
    "an internal id": [idea(1, id="i0000000000000001")],
    "an exact timestamp": [idea(1, published_at="2026-11-01T10:00:00Z")],
    "a submission reference": [idea(1, ref="PN-I-261101-AB12")],
    "the wrong order": [idea(2), idea(1)],
    "an over-long text": [idea(1, text="x" * 161)],
    "a too-short text": [idea(1, text="tiny")],
}
for name, data in faults.items():
    rc, out = build(t, {"ideas": data})
    ok(rc != 0 and "REFUSED" in out, "REFUSED: " + name)

print("PART 3 · the checks catch tampered output")
build(t, {"ideas": good})
P, L = t / "ideas.html", t / "discoveries.html"
pg0, lib0 = P.read_text(encoding="utf-8"), L.read_text(encoding="utf-8")
tamper = {
    "noindex removed": (P, lambda s: s.replace("noindex, follow", "index, follow")),
    "a fourth note on the card": (L, lambda s: s.replace('</ul><span class="ib-cap">', '<li class="ib-note">PROOF extra</li></ul><span class="ib-cap">', 1)),
    "the caption removed": (L, lambda s: s.replace("Homeowner ideas · not yet researched", "", 1)),
    "a fictional idea on the page": (P, lambda s: s.replace('<ul class="ib-wall">', '<ul class="ib-wall"><li class="ib-n"><p>Invented idea</p></li>', 1)),
    "an unescaped tag": (P, lambda s: s.replace("<p>PROOF TEST 1", "<p><marquee>x</marquee>PROOF TEST 1", 1)),
    "an e-mail address shown": (L, lambda s: s.replace("PROOF TEST 1:", "PROOF TEST 1: me@example.ie", 1)),
}
for name, (f, fn) in tamper.items():
    P.write_text(pg0, encoding="utf-8"); L.write_text(lib0, encoding="utf-8")
    f.write_text(fn(f.read_text(encoding="utf-8")), encoding="utf-8")
    ok(bool(checks(t, good)), "CAUGHT: " + name)
shutil.rmtree(t)

print("\nIDEA BOARD PROOF · %s" % ("PASS" if not fails else "FAIL (%d)" % len(fails)))
sys.exit(1 if fails else 0)
