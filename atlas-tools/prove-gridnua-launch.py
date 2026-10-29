#!/usr/bin/env python3
"""GRIDNUA LIMITED LAUNCH GUARD (founder design approval, 29 Oct 2026).

  python3 atlas-tools/prove-gridnua-launch.py [--manifest atlas-tools/release/gridnua-launch-manifest.json] [--prove]

Proves, on the tree as it would be published:
  GL1  exactly the approved files under gridnua/, byte-identical to the manifest
  GL2  index, follow and a self-canonical on both pages (indexing approved 29 Oct 2026); no preview ribbon
  GL3  the standing statement on both pages
  GL4  no form, script, endpoint, analytics or Interest Register on GridNua pages
  GL5  no money, earnings or savings claims (only the two disclaimers may use the words)
  GL6  no endorsement or partnership wording in PlotNua's own copy
  GL7  GridNua Sites material stays out (no Tandem, Zai Node, host sites, GridNua Sites)
  GL8  images: the PlotNua mark and the labelled conceptual illustration only
  GL9  every internal link resolves
  GL10 no "Here today" label (nothing qualifies, 29 Oct 2026)
  GL11 the sitemap lists exactly the two GridNua pages
  GL12 DISC-026: exactly one GridNua link, inside its markers; the article matches its latest freeze record
  GL13 the Readiness Check is byte-identical to its pin, its scripts (questions, engine, results) are unchanged,
       both return buttons are present, and the register stays closed
--prove plants one fault per guard in a scratch copy and requires every one to be caught.
"""
import hashlib, json, re, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAN = ROOT / "atlas-tools/release/gridnua-launch-manifest.json"
PAGES = ["gridnua/index.html", "gridnua/technology/index.html"]
STANDING = "No residential computing installation or programme is currently available through PlotNua in Ireland."
ARTICLE = "discovery-house-as-power-station.html"
CHECK = "disc026-compute-readiness-check.html"


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def text(h):
    h = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", h)
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r'(href|src)="[^"]*"', " ", h)
    return re.sub(r"<[^>]+>", " ", h)


def run(root):
    man = json.loads((root / "atlas-tools/release/gridnua-launch-manifest.json").read_text())
    fails = []
    def f(code, msg): fails.append(f"{code} {msg}")
    files = sorted(str(p.relative_to(root)) for p in (root / "gridnua").rglob("*") if p.is_file())
    if files != sorted(man["files"]): f("GL1", f"file list differs: {files}")
    for p, h in man["files"].items():
        if (root / p).exists() and sha(root / p) != h: f("GL1", f"{p} differs from its pin")
    pages = {p: (root / p).read_text(encoding="utf-8") for p in PAGES if (root / p).exists()}
    for p, h in pages.items():
        # indexing approved by the founder, 29 Oct 2026: index, follow and a self-canonical
        want = "https://plotnua.ie/" + p.replace("index.html", "")
        if '<meta name="robots" content="index, follow">' not in h: f("GL2", f"{p} not index, follow")
        if h.count('rel="canonical"') != 1 or f'<link rel="canonical" href="{want}">' not in h: f("GL2", f"{p} canonical is not {want}")
        if re.search(r"gn-preview|Local preview", h): f("GL2", f"{p} carries the preview ribbon")
        if not re.search(r'<p class="gn-standing"[^>]*>[\s\S]*?<strong>' + re.escape(STANDING) + '</strong>', h): f("GL3", f"{p} lacks the standing statement")
        if re.search(r"<form|<script|<input|workers\.dev|fetch\(|gtag|googletagmanager|cookiebot", h, re.I): f("GL4", f"{p} has a form, script or endpoint")
        if re.search(r"interest register|register your|join the register|waiting list", text(h), re.I): f("GL4", f"{p} mentions the register")
        t = text(h)
        for m in re.finditer(r"[€£$]\s?\d|\d\s?(euro|pounds|dollars)\b|\b(earn|earns|earning|earnings|income|savings?|paid|pays? you|per year|a year)\b", t, re.I):
            ctx = t[max(0, m.start() - 90): m.end() + 70]
            if not re.search(r"no promises of payment, savings or income|do not publish earnings, savings or payment figures|no company has paid to appear|no paid places|Would I be paid for hosting it\? GridNua makes no promises", re.sub(r"\s+", " ", ctx)):
                f("GL5", f"{p}: {ctx.strip()!r}"); break
        own = re.sub(r'<details class="gn-ev">[\s\S]*?</details>', " ", h)
        hits = re.findall(r"\b(partner(?:s|ship)?|recommended|best|approved|certified|trusted|endorsed)\b", text(own), re.I)
        if hits: f("GL6", f"{p}: {hits}")
        if re.search(r"tandem|zai ?node|gridnua sites|host sites?|site origination", text(h), re.I): f("GL7", f"{p} names GridNua Sites material")
        for src in re.findall(r'<img[^>]+src="([^"]+)"', h):
            if not (src.endswith("plotnua-mark-master.svg") or src.endswith("gridnua-utility-room-concept.svg")): f("GL8", f"{p} image {src}")
        if "gridnua-utility-room-concept.svg" in h and not ('<span class="gn-fig-tag">Conceptual illustration</span>' in h and "Not a real installation" in h): f("GL8", f"{p} illustration not labelled")
        if "gn-label--here" in h: f("GL10", f"{p} shows a Here today label")
        base = (root / p).parent
        for href in re.findall(r'href="([^"#?]+)', h):
            if href.startswith(("http", "mailto:", "/")): continue
            tgt = (base / href).resolve()
            if tgt.is_dir(): tgt = tgt / "index.html"
            if not tgt.exists(): f("GL9", f"{p} → {href}")
    svg = root / "gridnua/assets/gridnua-utility-room-concept.svg"
    if svg.exists() and "CONCEPTUAL ILLUSTRATION" not in svg.read_text(): f("GL8", "illustration lost its in-image label")
    sm = (root / "sitemap.xml").read_text(encoding="utf-8") if (root / "sitemap.xml").exists() else ""
    locs = sorted(re.findall(r"<loc>(https://plotnua\.ie/gridnua/[^<]*)</loc>", sm))
    if locs != ["https://plotnua.ie/gridnua/", "https://plotnua.ie/gridnua/technology/"]: f("GL11", f"sitemap GridNua entries are {locs}")
    art = (root / ARTICLE).read_text(encoding="utf-8")
    # the PlotNua header carries its own GridNua destination (29 Oct 2026); count the article's links outside it
    art_body = re.sub(r"<!-- PLOTNUA HEADER v2 · (BAR|ROW) · BEGIN[\s\S]*?PLOTNUA HEADER v2 · \1 · END -->", " ", art)
    links = re.findall(r'href="gridnua/[^"]*"', art_body)
    block = re.search(r"<!-- GRIDNUA-HANDOFF:BEGIN[\s\S]*?<!-- GRIDNUA-HANDOFF:END -->", art)
    if len(links) != 1 or not block or 'href="gridnua/"' not in block.group(0): f("GL12", "DISC-026 must hold exactly one GridNua link, inside its markers")
    recs = sorted((root / "governance").glob("disc-026-house-as-power-station-FREEZE-RECORD-V*.md"),
                  key=lambda q: int(re.search(r"-V(\d+)\.md$", q.name).group(1)))
    if not recs or sha(root / ARTICLE) not in recs[-1].read_text(encoding="utf-8"):
        f("GL12", "the DISC-026 article differs from the hash in its latest freeze record (same-commit rule)")
    if sha(root / CHECK) != man["readiness_check_sha256"]: f("GL13", "Readiness Check differs from its pin")
    chk = (root / CHECK).read_text(encoding="utf-8")
    if hashlib.sha256("\n".join(re.findall(r"<script[\s\S]*?</script>", chk)).encode()).hexdigest() != man["readiness_check_scripts_sha256"]:
        f("GL13", "Readiness Check logic (scripts) changed")
    intro = re.sub(r"\s+", " ", text(chk))
    if "paying the households" in intro or "Some emerging residential computing models offer households useful heat or other benefits. How these arrangements work varies by provider, and no residential computing installation programme is currently offered through PlotNua in Ireland." not in intro:
        f("GL13", "Readiness Check introduction is not the approved wording (29 Oct 2026)")
    nav = re.search(r"<!-- GRIDNUA-NAV:BEGIN[\s\S]*?<!-- GRIDNUA-NAV:END -->", chk)
    if not nav or 'href="discovery-house-as-power-station.html"' not in nav.group(0) or 'href="gridnua/"' not in nav.group(0):
        f("GL13", "Readiness Check return buttons missing")
    if '"writes_enabled": false' not in (root / CHECK).read_text(encoding="utf-8"): f("GL13", "register no longer closed")
    return fails


def prove():
    faults = {
        "GL1": lambda r: (r / "gridnua/notes.md").write_text("research"),
        "GL2": lambda r: sub(r, PAGES[0], 'content="index, follow"', 'content="noindex, follow"'),
        "GL3": lambda r: sub(r, PAGES[1], STANDING, "Available soon."),
        "GL4": lambda r: sub(r, PAGES[0], "</main>", "<form action=x></form></main>"),
        "GL5": lambda r: sub(r, PAGES[0], "Computers make heat.", "Hosts earn €300 a year. Computers make heat."),
        "GL6": lambda r: sub(r, PAGES[1], "Two separate labels", "Our recommended partners. Two separate labels"),
        "GL7": lambda r: sub(r, PAGES[0], "Large sites, not homes.", "Large sites, not homes. Tandem Compute."),
        "GL8": lambda r: sub(r, PAGES[0], "Conceptual illustration</span>", "Illustration</span>"),
        "GL9": lambda r: sub(r, PAGES[0], 'href="technology/"', 'href="techno/"'),
        "GL10": lambda r: sub(r, PAGES[1], 'class="gn-label gn-label--ie"', 'class="gn-label gn-label--ie gn-label--here"'),
        "GL11": lambda r: sub(r, "sitemap.xml", "<loc>https://plotnua.ie/gridnua/technology/</loc>", "<loc>https://plotnua.ie/gridnua/tech/</loc>"),
        "GL12": lambda r: sub(r, ARTICLE, "</main>", '<a href="gridnua/technology/">x</a></main>'),
        "GL13": lambda r: sub(r, CHECK, '"writes_enabled": false', '"writes_enabled": true'),
        "GL13c": lambda r: sub(r, CHECK, "Some emerging residential\n      computing models offer households useful heat or other benefits.", "The companies doing it are paying the households that host it."),
        "GL13b": lambda r: sub(r, CHECK, 'href="gridnua/"><span aria-hidden="true">&larr;</span> Back to GridNua', 'href="index.html">Home'),
    }
    caught = 0
    for code, plant in faults.items():
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            for p in ["gridnua", "atlas-tools/release/gridnua-launch-manifest.json", ARTICLE, CHECK, "sitemap.xml", "search-index-v1.json",
                      "governance", "assets/brand/plotnua-mark-master.svg"]:
                s, t = ROOT / p, r / p
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(s, t) if s.is_dir() else shutil.copy2(s, t)
            for p in re.findall(r'href="\.\./(?:\.\./)?([^"#?]+\.html)"', (ROOT / PAGES[0]).read_text() + (ROOT / PAGES[1]).read_text()):
                (r / p).parent.mkdir(parents=True, exist_ok=True); (r / p).exists() or (r / p).write_text("stub")
            plant(r)
            hit = any(x.startswith(code.rstrip("bc") + " ") for x in run(r))
            caught += hit
            print(("  caught " if hit else "  MISSED ") + code)
    print(f"GRIDNUA LAUNCH CAPABILITY · {caught}/{len(faults)} planted faults caught")
    return caught == len(faults)


def sub(r, p, a, b):
    q = r / p; s = q.read_text(encoding="utf-8")
    assert a in s, (p, a); q.write_text(s.replace(a, b, 1), encoding="utf-8")


if __name__ == "__main__":
    if "--prove" in sys.argv:
        sys.exit(0 if prove() else 1)
    fails = run(ROOT)
    for x in fails: print("FAIL", x)
    print("GRIDNUA LAUNCH · OK — GL1-GL13 on 2 pages · register closed" if not fails else f"GRIDNUA LAUNCH · {len(fails)} FAILURE(S)")
    sys.exit(1 if fails else 0)
