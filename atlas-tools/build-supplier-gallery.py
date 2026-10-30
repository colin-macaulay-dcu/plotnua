#!/usr/bin/env python3
"""
PLOTNUA - PREMIUM SUPPLIER GALLERY - bounded page builder (v1)
Design approved by founder 30 Oct 2026 (prototype v0.2); Garden Retreat
integration approved to prepare 30 Oct 2026. Production needs separate approval.

Writes ONE marker-delimited region into discovery-garden-retreat.html, directly
before the Maker Explorer (which it never touches); its stylesheet sits inside
that region so it never blocks the Discovery's first render. Built from:

  1. the LIVE Garden Retreat maker-explorer config
     (discovery-garden-retreat.html, <script id="mx-data">) -> which makers, their
     published product counts by category, their websites, their lead image and
     any existing commercial relationship;
  2. image-rights-records.json -> whether an image may be shown at all (PUBLISHABLE
     record, APPROVED asset, exact URL enumerated, required credit);
  3. garden-retreat.editorial.json -> PlotNua's own wording, the evidence behind any
     location line, and an optional choice among a maker's ALREADY APPROVED assets;
  4. discovery-headings.json -> the per-Discovery heading and introduction (the
     component itself is identical on every Discovery).

  5. approved_delivery_variants on a rights record -> an approved smaller delivery
     of an approved asset (same frame, supplier's own CDN). Used only when the
     record lists that exact URL for that exact asset.

Nothing about a supplier is typed into this file.

Usage:  python3 atlas-tools/build-supplier-gallery.py            apply (idempotent)
        python3 atlas-tools/build-supplier-gallery.py --check    verify, write nothing
        python3 atlas-tools/build-supplier-gallery.py --remove   take the gallery out again
"""
import html, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas-tools" / "supplier-gallery"
RIGHTS = ROOT / "image-rights-records.json"
# MULTI-DISCOVERY (founder approval 30 Oct 2026, DISC-008). One editorial file per
# Discovery that carries a gallery; the file names its page. The component, the
# rights rules and the guards are identical on every page. Garden Retreat's output
# is unchanged byte for byte (prove-supplier-gallery.py pins it).
EDITORIALS = sorted(DATA.glob("*.editorial.json"))
HEADINGS = DATA / "discovery-headings.json"
ASSET_V = "1"   # bump with any change to assets/components/pn-supplier-gallery.{css,js}

H_START, H_END = "<!-- PN-SUPPLIER-GALLERY:HEAD v1 · atlas-tools/build-supplier-gallery.py · do not hand-edit -->", "<!-- /PN-SUPPLIER-GALLERY:HEAD -->"
B_START, B_END = "<!-- PN-SUPPLIER-GALLERY v1 · Premium Supplier Gallery (founder design approval 30 Oct 2026) · built by atlas-tools/build-supplier-gallery.py from the Maker Explorer config below and image-rights-records.json · do not hand-edit -->", "<!-- /PN-SUPPLIER-GALLERY -->"
ANCHOR = "  <!-- 6c · PLOTNUA-MAKER-EXPLORER-V1"
HEAD_ANCHOR = '<link rel="stylesheet" href="maker-explorer.css">'

E = lambda s: html.escape(str(s), quote=True)

TAB_LABEL = {"saunas": ("sauna", "saunas"), "hotTubs": ("hot tub", "hot tubs"), "coldPlunges": ("cold plunge", "cold plunges")}
DESC_NOUN = {"saunas": "outdoor saunas", "hotTubs": "hot tubs", "coldPlunges": "cold plunges"}  # the live explorer's own product types
# Other Discoveries: the singular/plural come from the live explorer tab's own
# "nouns", and the description noun from the editorial file's "descNouns".
# Candidate mount shapes. The builder picks the one that shows the featured
# images LARGEST on average (whole image always visible, never cropped).
MOUNTS = [(1, 1), (5, 6), (4, 5), (3, 4), (2, 3)]

ARROW_L = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>'
ARROW_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
EXT = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 3h7v7M13 3L4 12"/></svg>'
NEWTAB = '<span class="pn-sg-vh"> (opens in a new tab)</span>'


def load_explorer(discovery):
    s = discovery.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" class="pn-mx-config" id="mx-data">(.*?)</script>', s, re.S)
    if not m:
        sys.exit(f"FAIL: {discovery.name}: explorer config not found")
    return json.loads(m.group(1))


def names_of(r):
    """The names a rights record answers to in a Maker Explorer: its organisation
    name, plus any maker_name_aliases it records (e.g. Yard Box is listed as
    "Yardbox"). The supplier is never renamed; credits stay as recorded."""
    return {r["organisation_name"], *(r.get("maker_name_aliases") or [])}


def approved_index():
    """URL -> (org name, record, asset) for every APPROVED asset of a PUBLISHABLE grant.
    Also VARIANTS[url-of-asset] -> the approved delivery variant for it, if any."""
    idx = {}
    VARIANTS.clear()
    for r in json.loads(RIGHTS.read_text(encoding="utf-8"))["records"]:
        if not r.get("permission_outcome", "").startswith("Granted"):
            continue
        if r.get("public_visibility") != "PUBLISHABLE" or r.get("asset_approval_state") != "APPROVED":
            continue
        for a in r.get("approved_assets") or []:
            idx[a["url"]] = (names_of(r), r, a)
        for v in r.get("approved_delivery_variants") or []:
            if v.get("of") in idx and idx[v["of"]][1] is r and v.get("url", "").startswith(v["of"]):
                VARIANTS[v["of"]] = v
            else:
                sys.exit(f"FAIL: {r['organisation_name']}: delivery variant not tied to one of its own approved assets")
    return idx


VARIANTS = {}


def collect(ed):
    cfg = load_explorer(ROOT / ed["discovery"])
    labels, nouns = dict(TAB_LABEL), dict(DESC_NOUN)
    for tab in cfg["tabs"]:
        if tab["key"] not in labels:
            labels[tab["key"]] = tuple(tab["nouns"])
            nouns[tab["key"]] = (ed.get("descNouns") or {}).get(tab["key"], tab["nouns"][1])
    approved = approved_index()
    makers, live_imgs = {}, {}
    for tab in cfg["tabs"]:
        key = tab["key"]
        for m in tab["makers"]:
            rec = makers.setdefault(m["m"], {"name": m["m"], "products": {}, "cats": {}, "sites": set(), "lead": None, "offer": None})
            for p in m["p"]:
                rec["products"][p[0]] = True
                rec["cats"][key] = rec["cats"].get(key, 0) + 1
                if len(p) > 5 and isinstance(p[5], dict):
                    if p[5].get("site"):
                        rec["sites"].add(p[5]["site"])
                    for i in p[5].get("img") or []:
                        live_imgs[i["src"]] = i
            if m.get("l"):
                live_imgs[m["l"]["src"]] = m["l"]
                rec["lead"] = rec["lead"] or m["l"]
            if m.get("o"):
                rec["offer"] = True

    out = []
    for name in sorted(makers, key=lambda n: n.casefold()):
        rec = makers[name]
        e = ed["makers"].get(name, {})
        cats = [(labels[k][1] if n != 1 else labels[k][0], n) for k, n in rec["cats"].items()]
        site = sorted(rec["sites"])[0] if rec["sites"] else None

        # image: an editorial choice among this maker's approved assets, else the live lead image
        src = e.get("image") or (rec["lead"] or {}).get("src")
        image = None
        if src:
            hit = approved.get(src)
            if e.get("image") and (not hit or name not in hit[0]):
                sys.exit(f"FAIL: editorial image for {name} is not an approved asset of its own publishable grant")
            live = live_imgs.get(src)
            if hit and name in hit[0] and live and live.get("credit") == hit[1].get("required_credit"):
                # The credit links where the live page links it; failing that, where the
                # rights record says the credit links (credit_href). The medium label is the
                # live one unless the approved asset records it as a visualisation.
                kind = "Visualisation" if (hit[2].get("kind") or "").lower() == "visualisation" else live["kind"]
                image = {"src": src, "alt": live["alt"], "kind": kind, "w": live["w"], "h": live["h"],
                         "credit": live["credit"], "creditHref": live.get("creditHref") or hit[1].get("credit_href"), "asset": src}
                v = VARIANTS.get(src)
                if v:   # approved smaller delivery of the same frame
                    if abs(v["width"] / v["height"] - live["w"] / live["h"]) > 0.005:
                        sys.exit(f"FAIL: {name}: delivery variant is not the same frame")
                    image.update(src=v["url"], w=v["width"], h=v["height"])
            elif e.get("image"):
                sys.exit(f"FAIL: {name}: chosen image has no live alt/dimensions/credit to reuse")

        explore = image["creditHref"] if image else (f"https://{site}/" if site else None)
        desc = e.get("description") or (join([nouns[k] for k in rec["cats"]]) + ".")
        rel = ed.get("relationships", {}).get(name)
        if rec["offer"] and not rel:
            sys.exit(f"FAIL: {name} has a commercial offer in the live config but no disclosure in the editorial file")
        out.append({
            "name": name,
            "description": desc,
            "base": e.get("base"),
            "categories": [{"label": c, "count": n} for c, n in cats],
            "productCount": len(rec["products"]),
            "site": site,
            "explore": explore,
            "image": image,
            "logo": None,                 # no logo permission is recorded for any supplier
            "placement": "editorial",     # 'sponsored' is reserved; none exist
            "relationship": rel,
        })
    return ed, out


def join(words):
    words = [w[0].upper() + w[1:] if i == 0 else w for i, w in enumerate(words)]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def best_mount(images):
    """The mount shape that shows the featured images largest on average (contain, no crop)."""
    def fill(mw, mh, w, h):
        r, m = w / h, mw / mh
        return (r / m) if r < m else (m / r)   # share of the mount's area the image covers
    return max(MOUNTS, key=lambda m: (sum(fill(m[0], m[1], i["w"], i["h"]) for i in images), m == (1, 1)))


def tags_html(s):
    t = []
    if s["placement"] == "sponsored":
        t.append('<span class="pn-sg-tag pn-sg-tag--sponsored">Sponsored</span>')
    if s["relationship"]:
        t.append(f'<span class="pn-sg-tag pn-sg-tag--rel">{E(s["relationship"]["label"])}</span>')
    return f'<div class="pn-sg-tags">{"".join(t)}</div>' if t else ""


def credit_html(img):
    return (f'<p class="pn-sg-cap"><span class="pn-sg-kind">{E(img["kind"])}</span>'
            f'<a href="{E(img["creditHref"])}" rel="noopener noreferrer" target="_blank">{E(img["credit"])}{NEWTAB}</a></p>')


def cta_html(s, compact=False):
    if not s["explore"]:
        return ""
    return (f'<p class="pn-sg-cta"><a href="{E(s["explore"])}" rel="noopener noreferrer" target="_blank" '
            f'aria-label="Explore {E(s["name"])} on {E(s["site"] or "its website")} (opens in a new tab)">'
            f'<span>{"Visit website" if compact else "Explore supplier"}</span>{EXT}</a></p>')


def img_tag(img, first):
    prio = ' fetchpriority="high"' if first else ""
    return (f'<img src="{E(img["src"])}" alt="{E(img["alt"])}" width="{img["w"]}" height="{img["h"]}" '
            f'loading="{"eager" if first else "lazy"}"{prio} decoding="async" referrerpolicy="no-referrer">')


def featured_card(s, first):
    """Focused: photograph, name, short description, verified location, Explore. Credit and labels kept."""
    img = s["image"]
    base = (f'<p class="pn-sg-loc"><b>{E(s["base"]["label"])}</b> {E(s["base"]["text"])}</p>') if s["base"] else ""
    rel = f'<p class="pn-sg-rel">{E(s["relationship"]["detail"])}</p>' if s["relationship"] else ""
    return (f'<article class="pn-sg-card" aria-label="{E(s["name"])}">'
            f'<figure class="pn-sg-fig"><div class="pn-sg-mount">{img_tag(img, first)}</div>'
            f'<figcaption>{credit_html(img)}</figcaption></figure>'
            f'<div class="pn-sg-body">{tags_html(s)}<h3 class="pn-sg-name">{E(s["name"])}</h3>'
            f'<p class="pn-sg-desc">{E(s["description"])}</p>{base}{rel}{cta_html(s)}</div></article>')


def index_entry(s):
    """Directory entry. Licensed image -> small mounted thumbnail with its credit.
    No licensed image -> a typographic entry: no frame, no placeholder, no invented visual."""
    img = s["image"]
    media = (f'<figure class="pn-sg-thumb"><div class="pn-sg-mount">{img_tag(img, False)}</div></figure>') if img else ""
    facts = []
    if s["base"]:
        facts.append(f'<div><dt>{E(s["base"]["label"])}</dt><dd>{E(s["base"]["text"])}</dd></div>')
    facts.append('<div><dt>On PlotNua</dt><dd>' + ", ".join(f'{c["count"]} {E(c["label"])}' for c in s["categories"]) + '</dd></div>')
    if s["site"]:
        facts.append(f'<div><dt>Website</dt><dd>{E(s["site"])}</dd></div>')
    rel = f'<p class="pn-sg-rel">{E(s["relationship"]["detail"])}</p>' if s["relationship"] else ""
    cap = credit_html(img) if img else ""
    return (f'<article class="pn-sg-entry{" has-img" if img else " is-text"}" aria-label="{E(s["name"])}">{media}'
            f'<div class="pn-sg-entry-body">{tags_html(s)}<h4 class="pn-sg-name">{E(s["name"])}</h4>'
            f'<p class="pn-sg-desc">{E(s["description"])}</p><dl class="pn-sg-facts">{"".join(facts)}</dl>'
            f'{rel}{cap}{cta_html(s, compact=True)}</div></article>')


def gallery(ed, head, sup):
    featured = [s for s in sup if s["image"]][: ed["featuredMax"]]
    mw, mh = best_mount([s["image"] for s in featured]) if featured else (1, 1)
    total = len(sup)
    more = total > len(featured)
    # all lazy in the page: the gallery sits below the fold, and must never compete with the
    # Discovery's hero image; the JS promotes the first card only if it starts near the screen
    items = "".join(f'<li data-sg-placement="{s["placement"]}">{featured_card(s, False)}</li>' for s in featured)
    if more:
        items += (f'<li data-sg-end><div class="pn-sg-card pn-sg-card--end"><p class="pn-sg-end-n">{total}</p>'
                  f'<p class="pn-sg-end-t">{E(head["endLine"])}</p>'
                  f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="{E(ed.get("gridId", "sg-all-gr"))}" '
                  f'data-sg-open="View all suppliers" data-sg-close="Hide the full list"><span data-sg-label>View all suppliers</span></button></div></li>')
    grid = "".join(f"<li>{index_entry(s)}</li>" for s in sup)
    n_img = sum(1 for s in sup if s["image"])
    view_all = (f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="{E(ed.get("gridId", "sg-all-gr"))}" '
                f'data-sg-open="View all {total} suppliers" data-sg-close="Hide the full list">'
                f'<span data-sg-label>View all {total} suppliers</span></button>') if more else ""
    grid_note = ed["gridNote"] if n_img < total else ed.get("gridNoteAllImaged", "")
    trans = ' data-sg-transition="rule"' if ed.get("transition") == "rule" else ""
    return f'''<section class="pn-sg" id="suppliers" data-pn-supplier-gallery data-discovery="{E(ed["discovery"])}"{trans} aria-labelledby="sg-h" style="--sg-mount-ratio:{mw} / {mh}">
  <div class="pn-sg-wrap">
    <div class="pn-sg-head">
      <div>
        <span class="pn-sg-kicker">{E(head["kicker"])}</span>
        <h2 class="pn-sg-h2" id="sg-h">{E(head["heading"])}</h2>
        <p class="pn-sg-intro">{E(head["intro"])}</p>
        <p class="pn-sg-note">{E(ed["selectionNote"])}</p>
      </div>
      <div class="pn-sg-controls">
        <button type="button" class="pn-sg-arrow" data-sg-prev aria-label="Previous supplier" aria-controls="sg-track">{ARROW_L}</button>
        <button type="button" class="pn-sg-arrow" data-sg-next aria-label="Next supplier" aria-controls="sg-track">{ARROW_R}</button>
        {view_all}
      </div>
    </div>
  </div>
  <ul class="pn-sg-track" id="sg-track" tabindex="0" role="list" aria-label="Featured suppliers, scroll horizontally">{items}</ul>
  <div class="pn-sg-wrap">
    <details class="pn-sg-grid-wrap" id="{E(ed.get("gridId", "sg-all-gr"))}">
      <summary>View all {total} suppliers</summary>
      <div class="pn-sg-grid-head">
        <h3 class="pn-sg-h3" tabindex="-1">All {total} suppliers</h3>
        <p class="pn-sg-note">{E(grid_note)}</p>
      </div>
      <ul class="pn-sg-grid" role="list">{grid}</ul>
    </details>
  </div>
</section>'''


def head_block(sup):
    hosts = sorted({urlparse(x["image"]["src"]).netloc for x in sup if x["image"]})
    lines = [H_START] + [f'<link rel="preconnect" href="https://{h}">' for h in hosts] + \
            [f'<link rel="stylesheet" href="assets/components/pn-supplier-gallery.css?v={ASSET_V}">', H_END]
    return "\n".join(lines) + "\n"


# SECTION TRANSITION (founder, 30 Oct 2026, DISC-008): where a Discovery's editorial
# file asks for it ("transition": "rule"), the Maker Explorer that follows the gallery
# opens with the site's hairline rule and a tighter top, so "Meet the makers." and
# "Explore makers and products" read as two distinct sections without extra space.
# Emitted only on that page; Garden Retreat's output is unchanged.
TRANSITION_CSS = ("<style>/* gallery -> Maker Explorer transition (build-supplier-gallery.py) */\n"
                  ".pn-sg[data-sg-transition=\"rule\"] ~ #explore-makers{ border-top:1px solid var(--rule, #4A4B4F); padding-top:72px; }\n"
                  "@media (max-width:720px){ .pn-sg[data-sg-transition=\"rule\"] ~ #explore-makers{ padding-top:44px; } }\n"
                  "</style>\n")


def body_block(ed, head, sup):
    # The stylesheet sits HERE, not in <head>: in the body it does not block the
    # Discovery's first render (hero and LCP), and the gallery is below the fold.
    return (f"{B_START}\n<link rel=\"stylesheet\" href=\"assets/components/pn-supplier-gallery.css?v={ASSET_V}\">\n"
            + (TRANSITION_CSS if ed.get("transition") == "rule" else "")
            + f"{gallery(ed, head, sup)}\n"
            f'<script src="assets/components/pn-supplier-gallery.js?v={ASSET_V}" defer></script>\n{B_END}\n')


def strip(page):
    page = re.sub(re.escape(H_START) + r".*?" + re.escape(H_END) + r"\n", "", page, flags=re.S)
    page = re.sub(re.escape(B_START) + r".*?" + re.escape(B_END) + r"\n", "", page, flags=re.S)
    return page


def compose(page, ed, head, sup):
    base = strip(page)
    if base.count(ANCHOR) != 1 or base.count(HEAD_ANCHOR) != 1:
        sys.exit("FAIL: page anchors not found exactly once (Maker Explorer comment / maker-explorer.css)")
    # Nothing is written into <head> any more (v1 final): strip() still removes an
    # older head block if one is present.
    return base.replace(ANCHOR, body_block(ed, head, sup) + ANCHOR, 1)


def build_one(edfile):
    ed = json.loads(edfile.read_text(encoding="utf-8"))
    discovery = ROOT / ed["discovery"]
    page = discovery.read_text(encoding="utf-8")
    if "--remove" in sys.argv:
        return discovery, page, strip(page), None
    ed, sup = collect(ed)
    heads = json.loads(HEADINGS.read_text(encoding="utf-8"))["discoveries"]
    head = heads.get(ed["discovery"])
    if not head:
        sys.exit(f"FAIL: no heading set for {ed['discovery']} in discovery-headings.json")
    out = compose(page, ed, head, sup)
    if strip(out) != strip(page):
        sys.exit(f"FAIL: {discovery.name}: integration would change page content outside the gallery regions")
    return discovery, page, out, sup


def main():
    ok_all = True
    for edfile in EDITORIALS:
        discovery, page, out, sup = build_one(edfile)
        title = discovery.name
        if "--remove" in sys.argv:
            discovery.write_text(out, encoding="utf-8")
            print(f"{title}: " + ("removed" if out != page else "nothing to remove"))
            continue
        if "--check" in sys.argv:
            ok = out == page
            ok_all &= ok
            print(f"SUPPLIER GALLERY · CHECK OK — {title} region is current" if ok else f"FAIL: {title} supplier gallery is missing or stale; rebuild")
            continue
        discovery.write_text(out, encoding="utf-8")
        print(f"wrote {title}: {len(sup)} suppliers, {sum(1 for x in sup if x['image'])} with licensed imagery"
              + ("" if out != page else " (unchanged)"))
    if "--check" in sys.argv:
        sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
