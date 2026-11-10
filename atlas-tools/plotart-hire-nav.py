#!/usr/bin/env python3
"""PlotArt · Art for Hire navigation (Stage 3B-4, development 10 Nov 2026). NOT RUN ON THE PUBLIC SITE.

Adds "Art for Hire" as the fourth gallery tab (Artists' Gallery · Mobile Gallery · Living Gallery · Art for Hire) to every
PlotArt page under ROOT/plotart: the header pill, the phone Menu link and the footer link, plus a small, scoped stylesheet
block for six pills. Everything else on each page is left byte-for-byte as it was.

  python3 atlas-tools/plotart-hire-nav.py ROOT            apply (ROOT is a copy of the site, e.g. the private preview)
  python3 atlas-tools/plotart-hire-nav.py ROOT --check    report what would change; change nothing

Strict: a page whose PlotArt navigation does not have exactly the expected shape stops the run with nothing written.
Idempotent: a page that already has the tab is left alone. Used now for the private preview only; at release the founder
approves running it on the site (with plotart_shell.HIRE_NAV switched on for pages the pipeline writes)."""
import os
import re
import sys

PILL = '<a class="pa-pill" href="{p}art-for-hire/"{cur} data-pa-track="nav_art_for_hire">Art for Hire</a>'
MENU = '<a class="pn-sm-link" href="{p}art-for-hire/"{cur} data-pa-track="nav_art_for_hire_menu">Art for Hire</a>'
FOOT = '<li><a href="{p}art-for-hire/">Art for Hire</a></li>'
CSS_BEGIN, CSS_END = "/* ==== pa-hire-nav:begin", "/* ==== pa-hire-nav:end ==== */"
CSS = CSS_BEGIN + """ · Art for Hire (Stage 3B-4): six pills, the fourth gallery tab. Scoped to .pa-pills--hire, so a page
   without the tab is unaffected. Desktop: one row. Tablets: one row of six, then two rows of three. Phones: the shared Menu. ==== */
@media (min-width:1181px) and (max-width:1420px){ .pa-head--pills .pa-pills--hire{ gap:6px; } :where(body.pa) .pa-pills--hire a.pa-pill{ padding:0 12px; font-size:14px; } .pa-head--pills:has(.pa-pills--hire) .pa-part{ display:none; } }
@media (max-width:1180px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(6, minmax(0, 1fr)); } }
@media (max-width:980px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(3, minmax(0, 1fr)); } :where(body.pa) .pa-pills--hire a.pa-pill{ font-size:13.5px; } }
""" + CSS_END + "\n"

NAV = re.compile(r'<nav class="pa-pills" aria-label="PlotArt">(.*?)</nav>', re.S)
LG_PILL = re.compile(r'<a class="pa-pill" href="([^"]*)living-gallery\.html"[^>]*>Living Gallery</a>')
LG_MENU = re.compile(r'<a class="pn-sm-link" href="([^"]*)living-gallery\.html"[^>]*>Living Gallery</a>')
LG_FOOT = re.compile(r'<li><a href="([^"]*)living-gallery\.html">Living Gallery</a></li>')


def patch(text, current):
    if 'data-pa-track="nav_art_for_hire"' in text:
        return text, "already"
    navs = NAV.findall(text)
    if len(navs) != 1:
        raise ValueError("expected one PlotArt pill navigation, found %d" % len(navs))
    pills = LG_PILL.findall(navs[0])
    menus = LG_MENU.findall(text)
    if len(pills) != 1 or len(menus) != 1:
        raise ValueError("expected one Living Gallery pill and one Menu link (found %d, %d)" % (len(pills), len(menus)))
    cur = ' aria-current="page"' if current else ""
    out = text.replace('<nav class="pa-pills" aria-label="PlotArt">', '<nav class="pa-pills pa-pills--hire" aria-label="PlotArt">', 1)
    m = LG_PILL.search(out)
    out = out[:m.end()] + PILL.format(p=m.group(1), cur=cur) + out[m.end():]
    m = LG_MENU.search(out)
    out = out[:m.end()] + MENU.format(p=m.group(1), cur=cur) + out[m.end():]
    feet = LG_FOOT.findall(out)
    if len(feet) > 1:
        raise ValueError("more than one Living Gallery footer link")
    if feet:
        m = LG_FOOT.search(out)
        out = out[:m.end()] + FOOT.format(p=m.group(1)) + out[m.end():]
    return out, "patched"


def css(text):
    if CSS_BEGIN in text:
        a, b = text.index(CSS_BEGIN), text.index(CSS_END) + len(CSS_END) + 1
        return text[:a] + CSS + text[b:]
    return text.rstrip("\n") + "\n\n" + CSS


def main(root, check=False):
    base = os.path.join(root, "plotart")
    plan, errors = [], []
    for d, _, files in os.walk(base):
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            path = os.path.join(d, f)
            rel = os.path.relpath(path, base)
            text = open(path, encoding="utf-8").read()
            if 'class="pa-pills' not in text:
                continue
            try:
                new, state = patch(text, rel.startswith("art-for-hire/"))
                plan.append((path, rel, text, new, state))
            except ValueError as e:
                errors.append("%s: %s" % (rel, e))
    if errors:
        print("REFUSED (nothing written):\n  " + "\n  ".join(errors))
        return 2
    cpath = os.path.join(base, "assets", "plotart.css")
    ctext = open(cpath, encoding="utf-8").read()
    for path, rel, text, new, state in plan:
        print("%-9s %s" % (state, rel))
        if not check and new != text:
            open(path, "w", encoding="utf-8").write(new)
    if not check:
        open(cpath, "w", encoding="utf-8").write(css(ctext))
    print("%d pages, %d patched; stylesheet block %s" % (len(plan), sum(1 for p in plan if p[4] == "patched"), "checked" if check else "written"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--check" in sys.argv))
