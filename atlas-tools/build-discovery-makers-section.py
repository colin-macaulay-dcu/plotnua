#!/usr/bin/env python3
"""
DISCOVERY SUPPLIER INTEGRATION · PHASE 1 — BOUNDED BUILDER (13 October 2026)

Founder decision, 13 October 2026, on
09 Commercial/DISCOVERY-SUPPLIER-SECTION-PROPOSAL-2026-10-13.md:
"Approve Phase 1 only." Pilot page: discovery-living-in-the-garden.html.

Adds ONE compact section, "Explore makers and products", directly after the
garden-room pricing section ("Garden room prices are hard to compare.") and
before the Property Check. Nothing else on the page changes.

WHAT IT IS
  * an introduction (founder wording);
  * one primary link into PlotNua's existing product exploration surface,
    search.html, which reaches every indexed garden room and garden home and,
    from each product, its Option Detail;
  * one "Manufacturer information" panel listing the published supplier
    information pages. Today that is TRIQ QUBE only -> triq-cube.html (product name corrected 13 Oct 2026).

THE "9 m2" WAS LEFT OFF THIS PAGE, DELIBERATELY. The founder's copy reads
"9 m2 timber garden office." On this page that figure trips Cluster 1 guard
L1 (prove-cluster1-garden-authority.mjs), which allows only the verified
planning figures {2, 12, 13, 20, 25, 30, 32, 40, 45, 50, 300} m2 on the
planning-authority page, so no product size can be read as a planning
threshold. The guard was kept and the figure dropped here; it stays on the
TRIQ page and in Search. Re-adding it means widening L1 by founder decision.

WHAT IT IS NOT (each enforced below)
  * no featured supplier shortlist: no product, maker or organisation is
    selected, ranked or named except the published information page;
  * no external link: every href is a PlotNua page (Journey Contract: no
    supplier handoff before Progress);
  * no new CSS: it reuses the page's existing, previously unused
    `.handoff-pair` / `.handoff` panel ("hand-off pair, as DISC-004") and the
    existing `.kicker` and `.dq-cat` labels;
  * no Atlas, ranking, eligibility, Search, Results or TRIQ page change.

The manufacturer panel lists exactly the pages declared in
SUPPLIER_INFO_PAGES in build-search-index.py, so the Discovery page and
Search cannot drift apart about which information pages are published.

  python3 atlas-tools/build-discovery-makers-section.py --check | --apply
"""
import pathlib, re, sys, difflib, ast

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "discovery-living-in-the-garden.html"
SEARCH_BUILDER = ROOT / "atlas-tools" / "build-search-index.py"
SITEMAP = ROOT / "sitemap.xml"
MARK = "PLOTNUA-DISCOVERY-MAKERS-PHASE1"

def die(m): print("REFUSED: " + m); sys.exit(2)

# ── the anchor: the end of the pricing section, the start of "The Detail" ──
ANCHOR = '''      differ, the prices were never comparable in the first place.</p>
  </section>

  <!-- 7 · THE EVIDENCE LAYER.'''

SECTION = '''      differ, the prices were never comparable in the first place.</p>
  </section>

  <!-- 6c · ''' + MARK + ''' · Founder decision 13 Oct 2026, Phase 1 only.
       No supplier is selected or ranked; every link is a PlotNua page; the
       manufacturer panel mirrors SUPPLIER_INFO_PAGES in build-search-index.py.
       Built by atlas-tools/build-discovery-makers-section.py. -->
  <section class="article-section reveal" id="explore-makers">
    <div class="kicker">Makers and Products</div>
    <h2>Explore makers and products</h2>
    <p>Discover real garden rooms and garden homes researched by PlotNua. Explore
      product details, published specifications and availability information before
      deciding what might work for your property.</p>

    <div class="handoff-pair">
      <div class="handoff">
        <span class="dq-cat">Researched by PlotNua</span>
        <a href="search.html">Explore garden rooms and garden homes&nbsp;&rarr;</a>
      </div>
      <div class="handoff">
        <span class="dq-cat">Manufacturer information</span>
        <h3>TRIQ QUBE by TRIQBRIQ AG</h3>
        <p>Timber garden office. Irish availability not yet confirmed.</p>
        <a href="triq-cube.html">Explore TRIQ QUBE&nbsp;&rarr;</a>
      </div>
    </div>
  </section>

  <!-- 7 · THE EVIDENCE LAYER.'''

GENERIC_CATEGORY_NAMES = {"garden rooms"}

BANNED = ("vetted", "approved", "certified", "recommended", "preferred", "best ",
          "partner", "featured", "top pick", "trusted", "endorse")

def info_pages():
    """SUPPLIER_INFO_PAGES, read from the Search builder without executing it."""
    src = SEARCH_BUILDER.read_text(encoding="utf-8")
    m = re.search(r"^SUPPLIER_INFO_PAGES = (\{.*?^\})", src, re.S | re.M)
    if not m: die("SUPPLIER_INFO_PAGES not found in build-search-index.py")
    return ast.literal_eval(m.group(1))

def build(src):
    if MARK in src: die("already applied")
    if src.count(ANCHOR) != 1: die(f"anchor found {src.count(ANCHOR)} times")
    out = src.replace(ANCHOR, SECTION)

    added = SECTION[len(ANCHOR) - len("  <!-- 7 · THE EVIDENCE LAYER."):]
    block = out[out.index("<!-- 6c · " + MARK):out.index("<!-- 7 · THE EVIDENCE LAYER.")]
    visible = re.sub(r"<!--.*?-->", " ", block, flags=re.S)
    visible_text = re.sub(r"<[^>]+>", " ", visible).lower()

    # G1 every href is a PlotNua page that exists; no external link at all
    hrefs = re.findall(r'href="([^"]+)"', visible)
    if not hrefs: die("G1 no links")
    for h in hrefs:
        if re.match(r"[a-z]+:", h) or h.startswith("//"):
            die("G1 external link on the Discovery page: " + h)
        if not (ROOT / h.split("?")[0].split("#")[0]).exists():
            die("G1 link target does not exist: " + h)
    # G2 the manufacturer panel lists exactly the published information pages
    ip = info_pages()
    listed = {h for h in hrefs if h != "search.html"}
    if listed != set(ip): die(f"G2 manufacturer panel {sorted(listed)} != SUPPLIER_INFO_PAGES {sorted(ip)}")
    sitemap = SITEMAP.read_text(encoding="utf-8")
    for f, spec in ip.items():
        if f"https://plotnua.ie/{f}" not in sitemap: die("G2 information page not in sitemap: " + f)
        if spec["title"] not in re.sub(r"&nbsp;", " ", re.sub(r"<[^>]+>", "", visible)):
            die("G2 panel title does not match the published record: " + spec["title"])
        if "Irish availability not yet confirmed" in spec["standfirst"] and \
           "irish availability not yet confirmed" not in visible_text:
            die("G2 the availability status was dropped for " + f)
    # G3 no supplier shortlist: no Atlas product/organisation is named
    for src_name in ("garden-room-recommendation-universe-v1.json", "additional-home-universe-v1.json"):
        import json
        U = json.loads((ROOT / src_name).read_text(encoding="utf-8"))
        orgs = {str(p.get("organisation") or "").strip() for p in U.get("products", [])}
        for o in orgs:
            # One Atlas organisation is literally called "Garden Rooms"; the
            # category phrase is not a supplier name and is exempted by name.
            if o.lower() in GENERIC_CATEGORY_NAMES: continue
            if len(o) > 3 and re.search(r"\b" + re.escape(o.lower()) + r"\b", visible_text):
                die("G3 an Atlas supplier is named on the Discovery page: " + o)
    if "your-plot.html?product=" in visible: die("G3 a product deep link would be a selection")
    # G4 no endorsement vocabulary in what the homeowner reads
    for w in BANNED:
        if w in visible_text: die("G4 banned word in the section: " + w.strip())
    # G5 the only change is the inserted section
    changed = [l for l in difflib.unified_diff(src.splitlines(), out.splitlines(), lineterm="", n=0)
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    if any(l.startswith("-") for l in changed): die("G5 an existing line was removed or altered")
    if len(changed) != SECTION.count("\n") - ANCHOR.count("\n"):
        die("G5 unexpected number of added lines")
    # G6 no new CSS, no script, no analytics
    if "<style" in block or "<script" in block or "gtag" in block: die("G6 style/script added")
    for cls in set(re.findall(r'class="([^"]+)"', visible)):
        for c in cls.split():
            if not re.search(r"\." + re.escape(c) + r"\b", src.split("</style>")[0]) and c != "reveal":
                die("G6 class without an existing rule on this page: " + c)
    # G7 the Property Check and the pricing section are untouched, and order is right
    i_price = out.index("Garden room prices are hard to compare.")
    i_new = out.index('id="explore-makers"')
    i_check = out.index("What would you like PlotNua to check?")
    if not (i_price < i_new < i_check): die("G7 section is not between pricing and the Property Check")
    for keep in ('href="your-plot.html?discovery=residential"', 'href="your-plot.html?discovery=garden-room"'):
        if out.count(keep) != src.count(keep): die("G7 Property Check link changed: " + keep)
    return out

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = PAGE.read_text(encoding="utf-8")
    out = build(src)
    if mode == "--apply":
        PAGE.write_text(out, encoding="utf-8"); print("APPLIED")
    else:
        print("CHECK OK — G1-G7 pass")

if __name__ == "__main__":
    main()
