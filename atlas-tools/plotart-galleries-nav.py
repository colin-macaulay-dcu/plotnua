#!/usr/bin/env python3
"""PlotArt · Galleries menu (three-gallery expansion, Phase A; founder approval 24 Nov 2026).

Replaces the "Artists’ Gallery" and "Mobile Gallery" pills of every PlotArt page under ROOT/plotart with the one
"Galleries" menu that atlas-tools/plotart_shell.py now writes (Contemporary · Spaces · Being · Mobile
Gallery), and makes the same change to the phone Menu and the footer. A page that already has the menu is REFRESHED to the
shell's current markup (final gallery identity, 24 Nov 2026: Contemporary · Spaces · Being):
the menu, its phone Menu links and the footer gallery links are rewritten from the shell, nothing else. Everything else on each page is left byte-for-byte
as it was. The menu's styles and behaviour live between the pa-galleries-nav markers in plotart.css and plotart.js.

  python3 atlas-tools/plotart-galleries-nav.py ROOT            apply
  python3 atlas-tools/plotart-galleries-nav.py ROOT --check    report what would change; change nothing

Strict: a page whose PlotArt navigation does not hold exactly one Artists’ Gallery pill followed by one Mobile Gallery pill,
the same two links once in the phone Menu and at most once in the footer, stops the run with nothing written.
Idempotent: running it twice changes nothing the second time. The markup is the shell's own (galleries_menu, menu_items,
FOOT_GALLERIES), so the pages the publisher writes and the pages patched here cannot drift apart."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plotart_shell as S  # noqa: E402

PILLS = re.compile(r'<a class="pa-pill" href="([^"]*)gallery/"( aria-current="page")? data-pa-track="nav_virtual_gallery">Artists’ Gallery</a>'
                   r'<a class="pa-pill" href="([^"]*)"( aria-current="page")? data-pa-track="nav_mobile_gallery">Mobile Gallery</a>')
MENU = re.compile(r'<a class="pn-sm-link" href="[^"]*gallery/"(?: aria-current="page")? data-pa-track="nav_virtual_gallery_menu">Artists’ Gallery</a>'
                  r'<a class="pn-sm-link" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_mobile_gallery_menu">Mobile Gallery</a>')
FOOT = re.compile(r'<li><a href="([^"]*)gallery/">Artists’ Gallery</a></li><li><a href="[^"]*mobile-gallery/">Mobile Gallery</a></li>')
NAV = re.compile(r'<nav class="pa-pills[^"]*" aria-label="PlotArt">(.*?)</nav>', re.S)

CSS_BEGIN, CSS_END = "/* ==== pa-galleries-nav:begin", "/* ==== pa-galleries-nav:end ==== */"
CSS = CSS_BEGIN + """ · the Galleries menu (three-gallery expansion Phase A, 24 Nov 2026). One header item, a <details>
   menu: Contemporary, Spaces, Being, Mobile Gallery. The summary is styled as a pill; the panel drops below it.
   Scoped to .pa-dd, so nothing else changes. ==== */
.pa-dd{ position:relative; }
.pa-dd > summary{ list-style:none; cursor:pointer; }
.pa-dd > summary::-webkit-details-marker{ display:none; }
:where(body.pa) .pa-pills .pa-pill--dd{ display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:42px; padding:0 18px 0 20px; border-radius:999px; border:1px solid rgba(237,235,231,.24); background:transparent; color:var(--lime); font-family:var(--sans); font-size:14.5px; font-weight:500; letter-spacing:.01em; line-height:1; white-space:nowrap; transition:background .2s, border-color .2s, color .2s; }
:where(body.pa) .pa-pills .pa-pill--dd::after{ content:""; width:6px; height:6px; border-right:1.5px solid currentColor; border-bottom:1.5px solid currentColor; transform:translateY(-2px) rotate(45deg); transition:transform .2s; }
:where(body.pa) .pa-dd[open] > .pa-pill--dd::after{ transform:translateY(1px) rotate(-135deg); }
:where(body.pa) .pa-pills .pa-pill--dd:hover{ border-color:rgba(237,235,231,.5); color:var(--ivory); background:rgba(237,235,231,.04); }
:where(body.pa) .pa-dd.is-current > .pa-pill--dd{ background:rgba(237,235,231,.11); border-color:rgba(237,235,231,.34); color:var(--ivory); }
:where(body.pa) .pa-pills .pa-pill--dd:focus-visible{ outline:2px solid var(--terra-text); outline-offset:3px; }
.pa-dd-panel{ position:absolute; z-index:45; top:calc(100% + 10px); left:50%; transform:translateX(-50%); min-width:264px; display:grid; gap:2px; padding:8px; background:#1B1C1E; border:1px solid rgba(237,235,231,.18); border-radius:16px; box-shadow:0 18px 44px rgba(0,0,0,.45); }
:where(body.pa) a.pa-dd-link{ display:flex; align-items:baseline; justify-content:space-between; gap:14px; padding:11px 14px; border-radius:10px; color:var(--lime); font-size:15px; font-weight:500; text-decoration:none; white-space:nowrap; }
:where(body.pa) a.pa-dd-link:hover{ background:#2E3033; color:var(--ivory); }
:where(body.pa) a.pa-dd-link[aria-current="page"]{ color:var(--ivory); background:rgba(237,235,231,.08); }
:where(body.pa) a.pa-dd-link:focus-visible{ outline:2px solid var(--terra-text); outline-offset:-2px; }
.pa-dd-note{ font-size:11px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--mute); }
.pa-dd-link:last-child{ margin-top:4px; border-top:1px solid rgba(237,235,231,.10); border-radius:0 0 10px 10px; padding-top:13px; }
.pn-sm-link .pa-dd-note{ margin-left:auto; }
@media (max-width:1180px){ .pa-dd{ display:flex; } :where(body.pa) .pa-pills .pa-pill--dd{ width:100%; min-height:44px; padding:0 8px; font-size:14px; }
  .pa-pills.pa-pills--hire{ grid-template-columns:repeat(7, minmax(0, 1fr)); } }   /* seven pills with Mobile Gallery (25 Nov 2026) */
@media (max-width:980px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(4, minmax(0, 1fr)); } }   /* 4 + 3: no pill left alone */
@media (max-width:860px){ :where(body.pa) .pa-pills .pa-pill--dd{ padding:0 4px; font-size:13px; letter-spacing:0; } }
""" + CSS_END + "\n"
JS_BEGIN, JS_END = "/* pa-galleries-nav:begin", "/* pa-galleries-nav:end */"
JS = JS_BEGIN + """ · the Galleries menu closes on Escape, on a click outside it, and when another menu opens (24 Nov 2026). */
(function () {
  var menus = function () { return document.querySelectorAll('details[data-pa-dd]'); };
  document.addEventListener('click', function (e) {
    menus().forEach(function (d) { if (d.open && !d.contains(e.target)) d.open = false; });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    menus().forEach(function (d) { if (d.open) { d.open = false; var s = d.querySelector('summary'); if (s) s.focus(); } });
  });
})();
""" + JS_END + "\n"


def current_of(rel, vg_cur, mg_cur):
    if rel == "gallery/index.html":
        return "contemporary"
    if mg_cur:
        return "mg"
    return "vg" if vg_cur else None


DD = re.compile(r'<details class="pa-dd(?: is-current)?" data-pa-dd><summary class="pa-pill pa-pill--dd">Galleries</summary><div class="pa-dd-panel">(.*?)</div></details>', re.S)
DD_LINK = re.compile(r'<a class="pa-dd-link" href="([^"]*)"( aria-current="page")? data-pa-track="([a-z_]+)">')
MENU_RUN = re.compile(r'<a class="pn-sm-link" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_gallery_contemporary_menu">.*?data-pa-track="nav_gallery_being_menu">.*?</a>'
                      r'(?:<a class="pn-sm-link" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_mobile_gallery_menu">Mobile Gallery</a>)?', re.S)
MG_PILL = re.compile(r'<a class="pa-pill" href="([^"]*)"( aria-current="page")? data-pa-track="nav_mobile_gallery">Mobile Gallery</a>')
MG_MENU = re.compile(r'<a class="pn-sm-link" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_mobile_gallery_menu">Mobile Gallery</a>')
LG_PILL = re.compile(r'<a class="pa-pill" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_living_gallery">Living Gallery</a>')
LG_MENU = re.compile(r'<a class="pn-sm-link" href="[^"]*"(?: aria-current="page")? data-pa-track="nav_living_gallery_menu">Living Gallery</a>')
FOOT_RUN = re.compile(r'<li><a href="([^"]*)gallery/">Contemporary(?: Art)?</a></li>.*?<li><a href="[^"]*mobile-gallery/">Mobile Gallery</a></li>', re.S)
KEY_OF_TRACK = {t: k for k, _h, _l, t in S.GALLERIES}


def refresh(text, rel):
    """A page that already has the Galleries menu: rewrite the menu, Mobile Gallery's own pill (straight after the Galleries
    menu, before Living Gallery: founder decision 25 Nov 2026, the order of the homepage's Beyond the Gallery tiles), their phone Menu links and the footer gallery links from the shell's current markup (same
    base path, same current page, same Mobile Gallery address). Works on the earlier layout (Mobile Gallery inside the
    Galleries menu) and on the current one, so running it twice changes nothing."""
    ms = DD.findall(text)
    if len(ms) != 1:
        raise ValueError("expected one Galleries menu, found %d" % len(ms))
    m = DD.search(text)
    links = DD_LINK.findall(m.group(1))
    if not links or links[0][2] != "nav_gallery_contemporary" or not links[0][0].endswith("gallery/"):
        raise ValueError("the Galleries menu does not start with Contemporary")
    R = links[0][0][:-len("gallery/")]
    pills = MG_PILL.findall(text)
    if links[-1][2] == "nav_mobile_gallery" and not pills:            # earlier layout: Mobile Gallery inside the menu
        mg_href, mg_cur = links[-1][0], bool(links[-1][1])
    elif links[-1][2] != "nav_mobile_gallery" and len(pills) == 1:     # current layout: its own pill
        mg_href, mg_cur = pills[0][0], bool(pills[0][1])
    else:
        raise ValueError("expected Mobile Gallery exactly once: inside the Galleries menu or as its own pill")
    cur = [t for _h, a, t in links if a and t != "nav_mobile_gallery"]
    current = KEY_OF_TRACK.get(cur[0], "vg") if cur else ("vg" if " is-current" in m.group(0) and not mg_cur else None)
    dd = S.galleries_menu(R, current)
    pill = S.mobile_gallery_pill(mg_href, mg_cur)
    if len(MENU_RUN.findall(text)) != 1 or len(FOOT_RUN.findall(text)) > 1 or len(LG_PILL.findall(text)) != 1 or len(LG_MENU.findall(text)) != 1:
        raise ValueError("expected one phone Menu gallery run, one Living Gallery pill and Menu link, and at most one footer gallery run")
    out = MG_PILL.sub("", text)
    out = out.replace(m.group(0), dd + pill, 1)
    out = MG_MENU.sub("", out)
    out = MENU_RUN.sub(lambda _m: "".join(S.menu_items(dd + pill)), out, count=1)
    out = FOOT_RUN.sub(lambda f: S.FOOT_GALLERIES.format(R=f.group(1)), out, count=1)
    return out, ("refreshed" if out != text else "already")


def patch(text, rel):
    if "data-pa-dd" in text:
        return refresh(text, rel)
    navs = NAV.findall(text)
    if len(navs) != 1:
        raise ValueError("expected one PlotArt pill navigation, found %d" % len(navs))
    m = PILLS.search(navs[0])
    if not m or len(PILLS.findall(navs[0])) != 1 or len(MENU.findall(text)) != 1 or len(FOOT.findall(text)) > 1:
        raise ValueError("expected one Artists’ Gallery + Mobile Gallery pill pair, one Menu pair and at most one footer pair")
    R, mg_href = m.group(1), m.group(3)
    dd = S.galleries_menu(R, current_of(rel, bool(m.group(2)), bool(m.group(4))), mg_href=mg_href)
    out = text.replace(m.group(0), dd, 1)
    out = MENU.sub(lambda _m: "".join(S.menu_items(dd)), out, count=1)
    out = FOOT.sub(lambda f: S.FOOT_GALLERIES.format(R=f.group(1)), out, count=1)
    return out, "patched"


def add_block(text, begin, end, block, name):
    if text.count(begin) == 1 and text.count(end) == 1:
        a, b = text.index(begin), text.index(end) + len(end) + 1
        return text[:a] + block + text[b:]
    if begin in text or end in text:
        raise ValueError("%s: the pa-galleries-nav markers are damaged" % name)
    return text + ("" if text.endswith("\n") else "\n") + block


def main(root, check=False):
    base = os.path.join(root, "plotart")
    plan, errors = [], []
    for d, _, files in os.walk(base):
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            path = os.path.join(d, f)
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            text = open(path, encoding="utf-8").read()
            if 'class="pa-pills' not in text:
                continue
            try:
                new, state = patch(text, rel)
                plan.append((path, text, new, state))
            except ValueError as e:
                errors.append("%s: %s" % (rel, e))
    assets = []
    for rel, begin, end, block in (("assets/plotart.css", CSS_BEGIN, CSS_END, CSS), ("assets/plotart.js", JS_BEGIN, JS_END, JS)):
        p = os.path.join(base, rel)
        t = open(p, encoding="utf-8").read()
        try:
            assets.append((p, t, add_block(t, begin, end, block, rel)))
        except ValueError as e:
            errors.append(str(e))
    if errors:
        print("REFUSED (nothing written):\n  " + "\n  ".join(errors))
        return 2
    changed = [p for p in plan if p[3] in ("patched", "refreshed")] + [a for a in assets if a[1] != a[2]]
    if not check:
        for p in plan:
            if p[2] != p[1]:
                open(p[0], "w", encoding="utf-8").write(p[2])
        for p, t, n in assets:
            if n != t:
                open(p, "w", encoding="utf-8").write(n)
    print("%d pages, %d %s; assets %s" % (len(plan), sum(p[3] in ("patched", "refreshed") for p in plan), "would change" if check else "changed",
                                          "up to date" if all(a[1] == a[2] for a in assets) else ("would change" if check else "updated")))
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--check" in sys.argv))
