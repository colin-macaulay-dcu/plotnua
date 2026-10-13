#!/usr/bin/env python3
"""
LIVING IN THE GARDEN · MAKER EXPLORER — BOUNDED BUILDER (13 October 2026)

Founder decisions, 13 October 2026: Maker Explorer concept approved (prototype
reviewed), with twelve refinements. This builder REPLACES the Phase 1 block
("Explore makers and products", PLOTNUA-DISCOVERY-MAKERS-PHASE1) on
discovery-living-in-the-garden.html with the explorer. Nothing else on the
page changes, apart from one scoped CSS block appended to the page's own
<style>.

SOURCE OF TRUTH (read, never written)
  garden-room-recommendation-universe-v1.json  -> every product is eligible
  additional-home-universe-v1.json             -> qualification ELIGIBLE only
  Every count, maker and product on the page is generated from these two
  files at build time. HELD and EXCLUDED products are never read into the
  page (guard G2 proves no held id appears).

WHAT A HOMEOWNER SEES
  * three figures: garden rooms, garden homes, makers researched (the union
    of organisations across both published lists, held-only makers included
    as research, never named);
  * Garden rooms / Garden homes tabs, one availability sentence each;
  * six makers in a fresh random order on every visit (no fixed order can
    favour anyone), "Show all" for the full A-Z directory, maker search and
    Irish availability filters;
  * a maker opens in place to its eligible products, each linking to its
    existing PlotNua product page, your-plot.html?product=<governed id>;
  * (13 Oct 2026, Part 2) NO manufacturer-information box: TRIQ CUBE is not
    placed on this Discovery page; it stays published at triq-cube.html and
    findable through Search (guard G7);
  * (13 Oct 2026, Part 1) "Show fewer makers" at the top and bottom of the
    expanded directory; both, and a tab switch, return to six makers, and
    collapsing scrolls back to the start of the explorer.

WHAT IT NEVER DOES (guards G1-G9)
  no external link, no ranking or featured order, no endorsement vocabulary,
  no held/excluded product, no area figure (Cluster 1 guard L1), no storage,
  fetch, analytics or URL state, no Atlas write, no eligibility logic.

  python3 atlas-tools/build-maker-explorer.py --check | --apply
"""
import ast, difflib, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "discovery-living-in-the-garden.html"
GR = ROOT / "garden-room-recommendation-universe-v1.json"
AH = ROOT / "additional-home-universe-v1.json"
SEARCH_BUILDER = ROOT / "atlas-tools" / "build-search-index.py"
MARK = "PLOTNUA-MAKER-EXPLORER-V1"
CSS_MARK = "PLOTNUA MAKER EXPLORER v1"

def die(m): print("REFUSED: " + m); sys.exit(2)

# A display name is changed in ONE case only: the organisation Atlas records
# literally as "Garden Rooms" (ORG-000001), which reads as a category, not a
# maker. Its own Atlas Website field is gardenrooms.ie, so that is appended.
DISPLAY_ALIAS = {"Garden Rooms": "Garden Rooms (gardenrooms.ie)"}

# PRODUCT DISPLAY NAMES — presentation only, never written back to Atlas.
# Founder review, 13 October 2026: one Atlas product name carries an internal
# data-quality note in its parenthesis. Each entry pins the exact Atlas name it
# corrects, so if Atlas is ever fixed (or changes) the builder REFUSES and the
# entry must be removed rather than silently masking a new name.
DISPLAY_NAME_BY_ID = {
    "recKFWluu0vDEHn81": {
        "atlas": "The Scannal (3-Bedroom Cabin, listed under Two Bed)",
        "display": "The Scannal",
        "evidence": "All In One Cabins two-bed-cabins page, read 13 Oct 2026: the "
                    "product heading is 'The scannal' (navigation tab 'The Scannal'). "
                    "The parenthesis is PlotNua's note of a taxonomy conflict (the "
                    "supplier's copy says '3 bedroom' on its 'Two Bed Cabins' page), "
                    "recorded in the Atlas description. Display uses the supplier's "
                    "own heading only; no bedroom count is asserted.",
    },
}

# A displayed name must not carry research notes. Checked on every name shown.
ANNOTATION_RE = re.compile(r"listed under|unresolved|conflict|taxonomy|vendor|placeholder|"
                           r"\bTBC\b|\bTBD\b|\bunknown\b|\?|\bsee note|\bper atlas", re.I)

BANNED = ("vetted", "approved", "certified", "recommended", "preferred", "best ",
          "top pick", "trusted", "endorse", "featured", "partner", "sponsored")

# ── data ─────────────────────────────────────────────────────────────────────
def load():
    U = json.loads(GR.read_text(encoding="utf-8"))
    A = json.loads(AH.read_text(encoding="utf-8"))
    gr_rows, ah_rows = U["products"], A["products"]
    if len(gr_rows) != U["eligibleCount"]:
        die("garden-room universe product list != its eligibleCount")
    def gr_state(r):
        if r.get("irishAvailabilityConfirmationState") == "Yes": return "c"
        if r.get("noPublishedIrishRoute"): return "r"
        return "u"
    def ah_state(q):
        return "c" if (q.get("irish") or {}).get("state") == "CONFIRMED" else "u"
    rooms, homes = {}, {}
    seen_override = set()
    def name(rec):
        o = DISPLAY_NAME_BY_ID.get(rec["id"])
        if not o: return rec["productName"]
        if rec["productName"] != o["atlas"]:
            die("display-name override for %s is stale: Atlas now says %r" % (rec["id"], rec["productName"]))
        seen_override.add(rec["id"])
        return o["display"]
    for r in gr_rows:
        rooms.setdefault(r["organisation"], []).append(
            [r["id"], name(r), r.get("productType") or "", gr_state(r)])
    ah_eligible = [q for q in ah_rows if (q.get("qualification") or {}).get("state") == "ELIGIBLE"]
    ah_held_ids = {q["id"] for q in ah_rows if (q.get("qualification") or {}).get("state") != "ELIGIBLE"}
    for q in ah_eligible:
        homes.setdefault(q["organisation"], []).append([q["id"], name(q), "", ah_state(q)])
    if seen_override != set(DISPLAY_NAME_BY_ID):
        die("display-name override for a product that is not publicly listed: %s"
            % sorted(set(DISPLAY_NAME_BY_ID) - seen_override))
    def pack(d):
        return [{"m": DISPLAY_ALIAS.get(k, k),
                 "p": sorted(v, key=lambda x: x[1].lower())}
                for k, v in sorted(d.items(), key=lambda kv: kv[0].lower())]
    all_orgs = {r["organisation"] for r in gr_rows} | {q["organisation"] for q in ah_rows}
    shown_orgs = set(rooms) | set(homes)
    figures = {
        "rooms": len(gr_rows), "roomMakers": len(rooms),
        "roomConfirmed": sum(1 for r in gr_rows if gr_state(r) == "c"),
        "roomNoRoute": sum(1 for r in gr_rows if gr_state(r) == "r"),
        "homes": len(ah_eligible), "homeMakers": len(homes),
        "homeConfirmed": sum(1 for q in ah_eligible if ah_state(q) == "c"),
        "makersResearched": len(all_orgs), "makersShown": len(shown_orgs),
    }
    return {"gardenRooms": pack(rooms), "gardenHomes": pack(homes)}, figures, ah_held_ids, all_orgs

def info_pages():
    src = SEARCH_BUILDER.read_text(encoding="utf-8")
    m = re.search(r"^SUPPLIER_INFO_PAGES = (\{.*?^\})", src, re.S | re.M)
    if not m: die("SUPPLIER_INFO_PAGES not found in build-search-index.py")
    return ast.literal_eval(m.group(1))

# ── markup ───────────────────────────────────────────────────────────────────
def section(data, F):
    # PART 2, founder decision 13 Oct 2026: the separate TRIQ CUBE
    # "Manufacturer information" box is removed from this Discovery page as
    # special supplier placement. triq-cube.html, its Search record and its
    # outbound-link exception are untouched (guard G7).
    payload = json.dumps({"data": data, "figures": F}, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    return f'''  <!-- 6c · {MARK} · Founder decisions 13 Oct 2026 (concept approved,
       twelve refinements). Generated from the published garden-room and
       garden-home lists by atlas-tools/build-maker-explorer.py; do not
       hand-edit. Replaces PLOTNUA-DISCOVERY-MAKERS-PHASE1. -->
  <section class="article-section reveal" id="explore-makers">
    <div class="kicker">Makers and Products</div>
    <h2>Explore makers and products</h2>
    <p>Discover real garden rooms and garden homes researched by PlotNua. Explore
      product details, published specifications and availability information before
      deciding what might work for your property.</p>

    <div class="mx-figs">
      <div><span class="mx-fig">{F["rooms"]}</span><span class="mx-fig-l">garden rooms</span></div>
      <div><span class="mx-fig">{F["homes"]}</span><span class="mx-fig-l">garden homes</span></div>
      <div><span class="mx-fig">{F["makersResearched"]}</span><span class="mx-fig-l">makers researched</span></div>
    </div>

    <div class="mx" id="mx">
      <div class="mx-tabs" role="tablist" aria-label="Product type">
        <button type="button" class="mx-tab" role="tab" id="mx-t-rooms" aria-selected="true" aria-controls="mx-pane" data-k="gardenRooms">Garden rooms <span class="mx-n">{F["rooms"]}</span></button>
        <button type="button" class="mx-tab" role="tab" id="mx-t-homes" aria-selected="false" aria-controls="mx-pane" data-k="gardenHomes" tabindex="-1">Garden homes <span class="mx-n">{F["homes"]}</span></button>
      </div>
      <div class="mx-pane" id="mx-pane" role="tabpanel" aria-labelledby="mx-t-rooms">
        <p class="mx-line" id="mx-line"></p>
        <ul class="mx-legend" id="mx-legend"></ul>
        <div class="mx-top" id="mx-top" hidden><button type="button" class="mx-btn" id="mx-less-top">Show fewer makers</button></div>
        <div class="mx-tools" id="mx-tools" hidden>
          <input class="mx-find" id="mx-find" type="search" placeholder="Find a maker" aria-label="Find a maker" autocomplete="off">
          <div class="mx-chips" id="mx-chips" role="group" aria-label="Irish availability">
            <button type="button" class="mx-chip" data-f="all" aria-pressed="true">All</button>
            <button type="button" class="mx-chip" data-f="c" aria-pressed="false">Confirmed</button>
            <button type="button" class="mx-chip" data-f="u" aria-pressed="false">Not yet confirmed</button>
          </div>
        </div>
        <p class="mx-order" id="mx-order"></p>
        <ul class="mx-grid" id="mx-grid"></ul>
        <div class="mx-more"><button type="button" class="mx-btn" id="mx-all"></button><span class="mx-order" id="mx-shown"></span></div>
        <noscript><p class="mx-line">The maker list needs JavaScript. You can still
          <a href="search.html">search PlotNua&rsquo;s garden rooms and garden homes</a>.</p></noscript>
      </div>
    </div>


    <p class="mx-foot">Only products PlotNua&rsquo;s research currently makes public are listed;
      products still being checked are not shown. Makers are not ranked, and PlotNua has no
      commercial arrangement with any maker listed. Product pages open within PlotNua.</p>

    <script type="application/json" id="mx-data">{payload}</script>
    <script>
    /* {MARK}. Reads the JSON above only. No fetch, no storage, no analytics,
       no URL state. Initial makers are shuffled on every visit so no fixed
       order can favour anyone; the full directory is A to Z. */
    (function () {{
      var raw = document.getElementById('mx-data');
      if (!raw) {{ return; }}
      var J = JSON.parse(raw.textContent), DATA = J.data, F = J.figures, INITIAL = 6;
      var $ = function (id) {{ return document.getElementById(id); }};
      function esc(s) {{ return String(s).replace(/[&<>"]/g, function (c) {{
        return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}
      function mstate(m) {{ var c = m.p.filter(function (p) {{ return p[3] === 'c'; }}).length;
        return c === m.p.length ? 'c' : (c ? 's' : 'u'); }}
      function shuffle(a) {{ a = a.slice(); for (var i = a.length - 1; i > 0; i--) {{
        var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }} return a; }}
      var ORDER = {{ gardenRooms: shuffle(DATA.gardenRooms), gardenHomes: shuffle(DATA.gardenHomes) }};
      var NOUN = {{ gardenRooms: ['garden room', 'garden rooms'], gardenHomes: ['garden home', 'garden homes'] }};
      var tab = 'gardenRooms', expanded = false, open = null, filter = 'all', q = '';

      function counts(list) {{
        var o = {{ c: 0, s: 0, u: 0 }}; list.forEach(function (m) {{ o[mstate(m)]++; }}); return o;
      }}
      function line() {{
        var rooms = tab === 'gardenRooms';
        var n = rooms ? F.rooms : F.homes, mk = rooms ? F.roomMakers : F.homeMakers;
        var conf = rooms ? F.roomConfirmed : F.homeConfirmed;
        var s = '<strong>' + n + ' ' + NOUN[tab][1] + '</strong> from <strong>' + mk + ' makers</strong>. ';
        if (conf === n) {{ return s + 'Irish availability is confirmed for all ' + n + '.'; }}
        return s + 'Irish availability is confirmed for ' + conf + ' and not yet confirmed for ' +
          (n - conf) + (rooms && F.roomNoRoute ? ', including ' + F.roomNoRoute +
          ' with no published Irish route' : '') + '.';
      }}
      function label(st) {{ return st === 'c' ? 'Confirmed' : st === 'r' ? 'No published Irish route' : 'Not yet confirmed'; }}
      function drawer(m, id) {{
        var c = m.p.filter(function (p) {{ return p[3] === 'c'; }}).length;
        var h = '<li class="mx-drawer" id="' + id + '"><h3>' + esc(m.m) + '</h3>' +
          '<p class="mx-meta">' + m.p.length + ' ' + NOUN[tab][m.p.length === 1 ? 0 : 1] +
          ' · Irish availability confirmed for ' + c + ' of ' + m.p.length + '</p><ul class="mx-plist">';
        var rooms = tab === 'gardenRooms';
        m.p.forEach(function (p) {{
          h += '<li>' + (rooms
              ? '<a class="mx-pn" href="your-plot.html?product=' + encodeURIComponent(p[0]) + '">' + esc(p[1]) + '</a>'
              : '<span class="mx-pn-text">' + esc(p[1]) + '</span>') +
            (p[2] ? '<span class="mx-pt">' + esc(p[2]) + '</span>' : '') +
            '<span class="mx-st"><span class="mx-dot mx-' + p[3] + '" aria-hidden="true"></span>' + label(p[3]) + '</span></li>';
        }});
        h += '</ul>';
        /* GARDEN HOMES HAVE NO DIRECT PRODUCT PAGE YET. The ?product= deep link
           resolves Garden Room ids only and fails closed for a garden home, so
           a link per product would land on the Eircode screen. The honest route
           is the existing garden-home check, where these products are shown. */
        if (!rooms) {{
          h += '<p class="mx-meta mx-route-note">Garden homes are shown on PlotNua after a short property check.</p>' +
               '<a class="mx-route" href="your-plot.html?discovery=residential">Check garden homes for your property&nbsp;&rarr;</a>';
        }}
        return h + '</li>';
      }}
      function render() {{
        var list = DATA[tab], k = counts(list);
        $('mx-line').innerHTML = line();
        $('mx-legend').innerHTML =
          '<li><span class="mx-dot mx-c" aria-hidden="true"></span>All products confirmed (' + k.c + ')</li>' +
          (k.s ? '<li><span class="mx-dot mx-s" aria-hidden="true"></span>Some products confirmed (' + k.s + ')</li>' : '') +
          (k.u ? '<li><span class="mx-dot mx-u" aria-hidden="true"></span>Not yet confirmed (' + k.u + ')</li>' : '');
        $('mx-tools').hidden = !expanded;
        $('mx-top').hidden = !expanded;
        $('mx-chips').hidden = (k.s + k.u) === 0;
        var rows = expanded ? list : ORDER[tab].slice(0, INITIAL);
        if (expanded) {{
          if (q) {{ rows = rows.filter(function (m) {{ return m.m.toLowerCase().indexOf(q.toLowerCase()) !== -1; }}); }}
          if (filter === 'c') {{ rows = rows.filter(function (m) {{ return mstate(m) !== 'u'; }}); }}
          if (filter === 'u') {{ rows = rows.filter(function (m) {{ return mstate(m) !== 'c'; }}); }}
        }}
        $('mx-order').textContent = expanded
          ? 'All makers, A to Z. Choose one to see its products.'
          : 'A few of the makers PlotNua has researched, in a different random order on every visit. Makers are never ranked.';
        var h = '';
        rows.forEach(function (m, i) {{
          var st = mstate(m), id = 'mx-d-' + tab + '-' + i, isOpen = open === m.m;
          h += '<li><button type="button" class="mx-maker" aria-expanded="' + isOpen + '"' +
            (isOpen ? ' aria-controls="' + id + '"' : '') + ' data-m="' + esc(m.m) + '">' +
            '<span class="mx-dot mx-' + st + '" aria-hidden="true"></span>' +
            '<span class="mx-nm">' + esc(m.m) + '<span class="mx-sr"> — ' +
            (st === 'c' ? 'Irish availability confirmed' : st === 's' ? 'Irish availability confirmed for some products' : 'Irish availability not yet confirmed') +
            '</span></span><span class="mx-ct">' + m.p.length + ' product' + (m.p.length === 1 ? '' : 's') + '</span></button></li>';
          if (isOpen) {{ h += drawer(m, id); }}
        }});
        if (!rows.length) {{ h = '<li class="mx-empty">No maker matches that search.</li>'; }}
        $('mx-grid').innerHTML = h;
        var total = list.length;
        $('mx-all').textContent = expanded ? 'Show fewer makers' : 'Show all ' + total + ' makers';
        $('mx-shown').textContent = (expanded ? rows.length : Math.min(INITIAL, total)) + ' of ' + total + ' shown';
      }}
      /* PART 1, founder decision 13 Oct 2026. Both "Show fewer makers"
         controls, and a tab switch, return the directory to its six-maker
         state: search, filter and any open maker are cleared. Collapsing also
         brings the visitor back to the start of the explorer. */
      function resetDirectory() {{
        expanded = false; open = null; q = ''; filter = 'all'; $('mx-find').value = '';
        [].forEach.call(document.querySelectorAll('.mx-chip'), function (c) {{
          c.setAttribute('aria-pressed', c.getAttribute('data-f') === 'all'); }});
      }}
      function collapse() {{
        resetDirectory(); render();
        var top = $('mx'), reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (top && top.scrollIntoView) {{ top.scrollIntoView({{ behavior: reduce ? 'auto' : 'smooth', block: 'start' }}); }}
        var active = document.querySelector('.mx-tab[aria-selected="true"]');
        if (active) {{ try {{ active.focus({{ preventScroll: true }}); }} catch (e) {{ active.focus(); }} }}
      }}
      var tabs = [$('mx-t-rooms'), $('mx-t-homes')];
      tabs.forEach(function (b) {{
        b.addEventListener('click', function () {{
          tab = b.getAttribute('data-k'); resetDirectory();
          tabs.forEach(function (t) {{ var on = t === b; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; }});
          $('mx-pane').setAttribute('aria-labelledby', b.id);
          render();
        }});
        b.addEventListener('keydown', function (ev) {{
          if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') {{ return; }}
          var other = tabs[tabs[0] === b ? 1 : 0]; other.focus(); other.click();
        }});
      }});
      $('mx-grid').addEventListener('click', function (ev) {{
        var b = ev.target.closest ? ev.target.closest('.mx-maker') : null; if (!b) {{ return; }}
        var name = b.getAttribute('data-m'); open = open === name ? null : name; render();
        var again = document.querySelector('.mx-maker[data-m="' + name.replace(/"/g, '\\\\"') + '"]');
        if (again) {{ again.focus(); }}
      }});
      $('mx-all').addEventListener('click', function () {{
        if (expanded) {{ collapse(); return; }}
        expanded = true; open = null; render(); $('mx-find').focus();
      }});
      $('mx-less-top').addEventListener('click', collapse);
      $('mx-find').addEventListener('input', function (ev) {{ q = ev.target.value.trim(); open = null; render(); }});
      [].forEach.call(document.querySelectorAll('.mx-chip'), function (c) {{
        c.addEventListener('click', function () {{
          filter = c.getAttribute('data-f'); open = null;
          [].forEach.call(document.querySelectorAll('.mx-chip'), function (x) {{ x.setAttribute('aria-pressed', x === c); }});
          render();
        }});
      }});
      render();
    }})();
    </script>
  </section>

'''

CSS = '''
/* ==== ''' + CSS_MARK + ''' · generated by atlas-tools/build-maker-explorer.py ====
   Scoped to #explore-makers. Page tokens only. */
#explore-makers .mx-figs{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin-top:30px;
  border-top:2px solid rgba(31,59,46,.55); }
#explore-makers .mx-figs > div{ padding:16px 16px 4px 0; }
#explore-makers .mx-figs > div + div{ padding-left:16px; border-left:1px solid rgba(31,59,46,.13); }
#explore-makers .mx-fig{ display:block; font-family:'Fraunces',Georgia,serif; font-weight:400;
  font-size:clamp(30px,3.6vw,42px); line-height:1; letter-spacing:-.02em; color:var(--ink);
  font-variant-numeric:tabular-nums; }
#explore-makers .mx-fig-l{ display:block; margin-top:8px; font-size:12.5px; line-height:1.5; color:var(--soft); }
#explore-makers .mx{ margin-top:26px; background:var(--paper); border:1px solid rgba(31,59,46,.12);
  border-radius:3px; box-shadow:0 1px 2px rgba(31,59,46,.05), 0 16px 32px -24px rgba(31,59,46,.32); }
#explore-makers .mx-tabs{ display:flex; border-bottom:1px solid rgba(31,59,46,.12); }
#explore-makers .mx-tab{ flex:1; appearance:none; background:none; border:0; border-bottom:2px solid transparent;
  margin-bottom:-1px; padding:15px 10px 13px; cursor:pointer; font:500 14.5px 'Work Sans',sans-serif;
  color:var(--soft); display:flex; gap:8px; justify-content:center; align-items:baseline; }
#explore-makers .mx-n{ font-size:12px; font-variant-numeric:tabular-nums; }
#explore-makers .mx-tab[aria-selected="true"]{ color:var(--ink); border-bottom-color:var(--ink); }
#explore-makers .mx-tab:focus-visible, #explore-makers .mx-maker:focus-visible,
#explore-makers .mx-chip:focus-visible, #explore-makers .mx-btn:focus-visible,
#explore-makers .mx-find:focus-visible, #explore-makers a:focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
#explore-makers .mx-pane{ padding:18px 20px 20px; }
#explore-makers p.mx-line{ font-size:14px; line-height:1.65; color:var(--soft); margin:0 0 12px; max-width:none; }
#explore-makers .mx-line strong{ color:var(--ink); font-weight:600; }
#explore-makers .mx-legend{ display:flex; flex-wrap:wrap; gap:4px 16px; list-style:none; margin:0 0 14px; padding:0;
  font-size:12.5px; color:var(--soft); }
#explore-makers .mx-dot{ display:inline-block; flex:none; width:9px; height:9px; border-radius:50%; margin-right:6px; }
#explore-makers .mx-c{ background:var(--accent); }
#explore-makers .mx-s{ background:linear-gradient(90deg,var(--accent) 50%,transparent 50%); box-shadow:inset 0 0 0 1.5px var(--accent); }
#explore-makers .mx-u{ box-shadow:inset 0 0 0 1.5px #7A7F78; }
#explore-makers .mx-r{ box-shadow:inset 0 0 0 1.5px var(--oak);
  background:repeating-linear-gradient(45deg,transparent 0 2px,rgba(139,111,78,.55) 2px 3px); }
#explore-makers .mx-tools{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }
#explore-makers .mx-tools[hidden], #explore-makers .mx-chips[hidden]{ display:none; }
#explore-makers .mx-find{ flex:1 1 200px; min-width:0; border:1px solid rgba(31,59,46,.15); background:#fff;
  border-radius:3px; padding:9px 12px; font:400 14px 'Work Sans',sans-serif; color:var(--ink); }
#explore-makers .mx-chips{ display:flex; gap:6px; flex-wrap:wrap; }
#explore-makers .mx-chip{ appearance:none; border:1px solid rgba(31,59,46,.15); background:var(--cream); color:var(--ink);
  border-radius:999px; padding:6px 12px; font:500 12.5px 'Work Sans',sans-serif; cursor:pointer; }
#explore-makers .mx-chip[aria-pressed="true"]{ background:var(--ink); color:var(--cream); border-color:var(--ink); }
#explore-makers .mx-order{ font-size:12px; line-height:1.55; color:var(--soft); margin:0 0 10px; max-width:none; }
#explore-makers .mx-grid{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; }
#explore-makers .mx-maker{ width:100%; text-align:left; appearance:none; cursor:pointer; background:var(--cream);
  border:1px solid rgba(31,59,46,.12); border-radius:3px; padding:11px 13px; display:flex; gap:10px; align-items:center;
  font-family:'Work Sans',sans-serif; color:var(--ink); }
#explore-makers .mx-maker:hover{ border-color:rgba(31,59,46,.35); }
#explore-makers .mx-maker[aria-expanded="true"]{ border-color:var(--ink); }
#explore-makers .mx-nm{ flex:1; min-width:0; font-family:'Fraunces',Georgia,serif; font-weight:600; font-size:15px; line-height:1.25; }
#explore-makers .mx-sr{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }
#explore-makers .mx-ct{ font-size:12px; color:var(--soft); white-space:nowrap; font-variant-numeric:tabular-nums; }
#explore-makers .mx-drawer{ grid-column:1/-1; background:var(--cream); border:1px solid rgba(31,59,46,.12);
  border-left:2px solid var(--accent); border-radius:2px; padding:14px 16px 12px; }
#explore-makers .mx-drawer h3{ font-family:'Fraunces',serif; font-weight:600; font-size:17px; margin:0 0 3px; }
#explore-makers .mx-meta{ font-size:12.5px; color:var(--soft); margin:0 0 8px; }
#explore-makers .mx-plist{ list-style:none; margin:0; padding:0; max-height:300px; overflow:auto;
  border-top:1px solid rgba(31,59,46,.12); }
#explore-makers .mx-plist li{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:2px 12px; padding:9px 2px;
  border-bottom:1px solid rgba(31,59,46,.1); }
#explore-makers .mx-pn{ font-size:14px; line-height:1.4; color:var(--accent); text-decoration:none;
  border-bottom:1px solid rgba(79,107,74,.3); justify-self:start; }
#explore-makers .mx-pn:hover{ border-bottom-color:var(--accent); }
#explore-makers .mx-pn-text{ font-size:14px; line-height:1.4; color:var(--ink); }
#explore-makers .mx-route-note{ margin:10px 0 4px; }
#explore-makers .mx-route{ display:inline-block; font-size:14px; font-weight:500; color:var(--accent); text-decoration:none;
  border-bottom:1px solid rgba(79,107,74,.35); padding-bottom:1px; }
#explore-makers .mx-pt{ grid-column:1; font-size:12px; color:var(--soft); }
#explore-makers .mx-st{ grid-column:2; grid-row:1 / span 2; align-self:center; font-size:11.5px; color:var(--soft);
  white-space:nowrap; display:flex; align-items:center; }
#explore-makers .mx-more{ margin-top:12px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
#explore-makers .mx-more .mx-order{ margin:0; }
#explore-makers .mx-top{ margin:0 0 12px; }
#explore-makers .mx{ scroll-margin-top:96px; }
#explore-makers .mx-btn{ appearance:none; background:none; border:0; padding:0 0 2px; cursor:pointer;
  font:500 14px 'Work Sans',sans-serif; color:var(--accent); border-bottom:1px solid rgba(79,107,74,.35); }
#explore-makers .mx-empty{ font-size:13.5px; color:var(--soft); padding:8px 0; }
#explore-makers p.mx-foot{ margin-top:14px; font-size:12px; line-height:1.6; color:var(--soft); max-width:62ch; }
@media (max-width:720px){
  #explore-makers .mx-figs > div{ padding:14px 10px 4px 0; }
  #explore-makers .mx-figs > div + div{ padding-left:10px; }
  #explore-makers .mx-fig-l{ font-size:11.5px; }
  #explore-makers .mx-grid{ grid-template-columns:1fr; }
  #explore-makers .mx-pane{ padding:14px 14px 16px; }
  #explore-makers .mx-tab{ flex-direction:column; align-items:center; gap:2px; padding:11px 6px; }
}
/* ==== ''' + CSS_MARK + ''' · END ==== */
'''

def build(src):
    # REGENERATION. On a page that already carries the explorer, the existing
    # explorer block and its CSS are the "old block": they are replaced whole,
    # and G9 still proves nothing outside them changed.
    if MARK in src:
        a = src.find("/* ==== " + CSS_MARK + " · generated by")
        b = src.find("/* ==== " + CSS_MARK + " · END ==== */")
        if a < 0 or b < 0: die("existing explorer CSS block not found")
        b += len("/* ==== " + CSS_MARK + " · END ==== */\n")
        if src[a - 1] != "\n": die("existing CSS block shape unexpected")
        src = src[:a - 1] + src[b:]
        start = src.find("  <!-- 6c · " + MARK)
    else:
        start = src.find("  <!-- 6c · PLOTNUA-DISCOVERY-MAKERS-PHASE1")
        if src.count("PLOTNUA-DISCOVERY-MAKERS-PHASE1") != 1:
            die("Phase 1 block anchor not found exactly once")
    end = src.find("  <!-- 7 · THE EVIDENCE LAYER.")
    if start < 0 or end < 0:
        die("explorer block anchor not found")
    old_block = src[start:end]
    if old_block.count("<section") != 1: die("Phase 1 block shape unexpected")

    data, F, held_ids, all_orgs = load()
    ip = info_pages()
    new_block = section(data, F)
    out = src[:start] + new_block + src[end:]
    css_anchor = "/* PLOTNUA A11Y VISUAL v1 · END */\n</style>"
    if out.count(css_anchor) != 1: die("CSS anchor not found exactly once")
    out = out.replace(css_anchor, "/* PLOTNUA A11Y VISUAL v1 · END */\n" + CSS + "</style>")

    blk = new_block
    visible = re.sub(r"<script.*?</script>", " ", blk, flags=re.S)
    visible = re.sub(r"<!--.*?-->", " ", visible, flags=re.S)
    vtext = html.unescape(re.sub(r"<[^>]+>", " ", visible)).lower()
    js = "".join(re.findall(r"<script>(.*?)</script>", blk, re.S))

    # G1 counts are generated and agree with the universes' own headers
    U = json.loads(GR.read_text(encoding="utf-8")); A = json.loads(AH.read_text(encoding="utf-8"))
    if F["rooms"] != U["eligibleCount"] or F["roomMakers"] != U["organisationCount"]:
        die("G1 garden-room counts disagree with the universe header")
    if F["homes"] != A["eligibleCount"]: die("G1 garden-home count disagrees with the universe header")
    if F["roomConfirmed"] != U["confirmedIrishAvailabilityCount"]:
        die("G1 confirmed count disagrees with the universe header")
    if sum(len(m["p"]) for m in data["gardenRooms"]) != F["rooms"]: die("G1 room products not all listed")
    if sum(len(m["p"]) for m in data["gardenHomes"]) != F["homes"]: die("G1 home products not all listed")
    for k in ("rooms", "homes", "makersResearched"):
        if f'<span class="mx-fig">{F[k]}</span>' not in blk: die("G1 headline figure missing: " + k)
    # G2 no held or excluded product anywhere on the page
    for hid in held_ids:
        if hid in out: die("G2 a held garden-home id appears on the page: " + hid)
    listed = {p[0] for t in data.values() for m in t for p in m["p"]}
    gr_ids = {r["id"] for r in U["products"]}
    ah_el = {q["id"] for q in A["products"] if (q.get("qualification") or {}).get("state") == "ELIGIBLE"}
    if listed != gr_ids | ah_el: die("G2 listed products are not exactly the eligible set")
    # G10 no displayed product or maker name carries a research note
    for t in data.values():
        for m in t:
            if ANNOTATION_RE.search(m["m"]): die("G10 maker name carries a note: " + m["m"])
            for p in m["p"]:
                if ANNOTATION_RE.search(p[1]): die("G10 product name carries a research note: " + p[1])
    # G3 no external link; product links are the governed deep link only
    for h in re.findall(r'href="([^"]+)"', blk):
        if re.match(r"[a-z]+:", h) or h.startswith("//"): die("G3 external link: " + h)
        if not (ROOT / h.split("?")[0]).exists(): die("G3 link target missing: " + h)
    if "http" in js or "window.open" in js: die("G3 script can leave PlotNua")
    if js.count("your-plot.html?product=") != 1: die("G3 product link must be the governed deep link")
    # Garden-home ids are NOT deep-linkable (the deep link resolves the Garden
    # Room pool only), so the product link is built for the rooms tab alone.
    if "var rooms = tab === 'gardenRooms'" not in js: die("G3 garden-home products must not get a product link")
    if js.count("your-plot.html?discovery=residential") != 1: die("G3 garden-home route missing")
    # G4 no storage, fetch, analytics or URL state
    for bad in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest",
                "gtag", "dataLayer", "history.", "location.", "document.cookie", "sendBeacon"):
        if bad in js: die("G4 forbidden in the explorer script: " + bad)
    # G5 no ranking: data is alphabetical; the only order at rest is a shuffle
    for t in data.values():
        names = [m["m"].lower() for m in t]
        if names != sorted(names): die("G5 directory is not A to Z")
    if "Math.random" not in js or ".sort(" in js: die("G5 initial order must be a shuffle, never a sort")
    # G6 no endorsement vocabulary in what the homeowner reads, script strings included
    texts = vtext + " " + " ".join(re.findall(r"'([^']*)'", js)).lower()
    for w in BANNED:
        if w in texts: die("G6 banned word: " + w.strip())
    # G7 no special supplier placement: no manufacturer box and no link to a
    # supplier information page on this Discovery page. The information page
    # itself stays published and findable: it must still be in the sitemap and
    # in SUPPLIER_INFO_PAGES (Search), and the file must still exist.
    if "mx-info" in blk or "Manufacturer information" in blk: die("G7 a manufacturer box is back")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for f in ip:
        if f in blk: die("G7 supplier information page linked from the explorer: " + f)
        if not (ROOT / f).exists(): die("G7 supplier information page missing: " + f)
        if "https://plotnua.ie/" + f not in sitemap: die("G7 supplier information page left the sitemap: " + f)
    if "triq-cube.html" not in ip: die("G7 TRIQ CUBE must stay in Search (SUPPLIER_INFO_PAGES)")
    # G8 the planning page's own text carries no area figure from this block
    # (Cluster 1 L1). Static markup only: 94 makers' own PRODUCT NAMES contain
    # a size ("Concept Modular Cabin 17m2") and appear only once a homeowner
    # opens that maker, as an attributed product name, never as page prose.
    if re.search(r"\d\s*(m²|m&sup2;|square metres)", visible): die("G8 an area figure would reach the planning page")
    # G9 only the Phase 1 block and the CSS anchor changed; Property Check untouched
    rest_before = src[:start] + src[end:]
    rest_after = out.replace(new_block, "", 1).replace(CSS, "", 1)
    if rest_before != rest_after: die("G9 something outside the block and CSS changed")
    for keep in ('href="your-plot.html?discovery=residential"', 'href="your-plot.html?discovery=garden-room"'):
        # the Property Check's own links live outside the block and are unchanged
        if rest_before.count(keep) < 1 or out.replace(new_block, "", 1).count(keep) != rest_before.count(keep):
            die("G9 Property Check link changed")
    i_price = out.index("Garden room prices are hard to compare.")
    i_new = out.index('id="explore-makers"'); i_check = out.index("What would you like PlotNua to check?")
    if not (i_price < i_new < i_check): die("G9 placement")
    if out.count('id="explore-makers"') != 1: die("G9 duplicate section id")
    print(f"  figures: {F}")
    return out

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = PAGE.read_text(encoding="utf-8")
    out = build(src)
    if mode == "--apply":
        PAGE.write_text(out, encoding="utf-8"); print("APPLIED — G1-G10 pass")
    else:
        print("CHECK OK — G1-G10 pass")

if __name__ == "__main__":
    main()
