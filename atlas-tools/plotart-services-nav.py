#!/usr/bin/env python3
"""PlotArt · Services tab (founder brief 19 Nov 2026, "Art Services & Providers").

Adds "Services" as the last PlotArt tab, after Art for Hire and before PlotNua ↗, to every PlotArt page under ROOT/plotart:
the header pill, the phone Menu link and the footer link, exactly as atlas-tools/plotart_shell.py writes them for the pages
it builds. Everything else on each page is left byte-for-byte as it was. The stylesheet's pa-hire-nav block is widened to
seven pills.

  python3 atlas-tools/plotart-services-nav.py ROOT            apply
  python3 atlas-tools/plotart-services-nav.py ROOT --check    report what would change; change nothing

Strict: a page whose PlotArt navigation does not have exactly one Art for Hire pill and one Menu link stops the run with
nothing written. Idempotent: a page that already has the tab is left alone."""
import os
import re
import sys

PILL = '<a class="pa-pill" href="{p}services.html"{cur} data-pa-track="nav_services">Services</a>'
MENU = '<a class="pn-sm-link" href="{p}services.html"{cur} data-pa-track="nav_services_menu">Services</a>'
FOOT = '<li><a href="{p}services.html">Services</a></li>'
H_PILL = re.compile(r'<a class="pa-pill" href="([^"]*)art-for-hire/"[^>]*>Art for Hire</a>')
H_MENU = re.compile(r'<a class="pn-sm-link" href="([^"]*)art-for-hire/"[^>]*>Art for Hire</a>')
H_FOOT = re.compile(r'<li><a href="([^"]*)art-for-hire/">Art for Hire</a></li>')
NAV = re.compile(r'<nav class="pa-pills[^"]*" aria-label="PlotArt">(.*?)</nav>', re.S)
CSS_OLD = ("@media (max-width:1180px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(6, minmax(0, 1fr)); } }",
           "@media (min-width:1181px) and (max-width:1420px){ .pa-head--pills .pa-pills--hire{ gap:6px; } :where(body.pa) .pa-pills--hire a.pa-pill{ padding:0 12px; font-size:14px; } .pa-head--pills:has(.pa-pills--hire) .pa-part{ display:none; } }")
CSS_NEW = ("@media (max-width:1180px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(7, minmax(0, 1fr)); } }",
           "@media (min-width:1181px) and (max-width:1500px){ .pa-head--pills .pa-pills--hire{ gap:6px; } :where(body.pa) .pa-pills--hire a.pa-pill{ padding:0 12px; font-size:14px; } .pa-head--pills:has(.pa-pills--hire) .pa-part{ display:none; } }")
CSS_980 = "@media (max-width:980px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(3, minmax(0, 1fr)); }"
CSS_980_NEW = "@media (max-width:980px){ .pa-pills.pa-pills--hire{ grid-template-columns:repeat(4, minmax(0, 1fr)); }"


def patch(text, current):
    if 'data-pa-track="nav_services"' in text:
        return text, "already"
    navs = NAV.findall(text)
    if len(navs) != 1:
        raise ValueError("expected one PlotArt pill navigation, found %d" % len(navs))
    if len(H_PILL.findall(navs[0])) != 1 or len(H_MENU.findall(text)) != 1 or len(H_FOOT.findall(text)) > 1:
        raise ValueError("expected one Art for Hire pill, one Menu link and at most one footer link")
    cur = ' aria-current="page"' if current else ""
    out = text
    for rx, tpl in ((H_PILL, PILL), (H_MENU, MENU), (H_FOOT, FOOT)):
        m = rx.search(out)
        if m:
            out = out[:m.end()] + tpl.format(p=m.group(1), cur=cur) + out[m.end():]
    return out, "patched"


def css(text):
    if CSS_NEW[0] in text:
        return text
    for a, b in list(zip(CSS_OLD, CSS_NEW)) + [(CSS_980, CSS_980_NEW)]:
        if text.count(a) != 1:
            raise ValueError("plotart.css: expected the pa-hire-nav rule once: " + a[:60])
        text = text.replace(a, b)
    return text


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
                new, state = patch(text, rel == "services.html")
                plan.append((path, rel, text, new, state))
            except ValueError as e:
                errors.append("%s: %s" % (rel, e))
    cpath = os.path.join(base, "assets", "plotart.css")
    ctext = open(cpath, encoding="utf-8").read()
    try:
        cnew = css(ctext)
    except ValueError as e:
        errors.append(str(e))
    if errors:
        print("REFUSED (nothing written):\n  " + "\n  ".join(errors))
        return 2
    for path, rel, text, new, state in plan:
        if not check and new != text:
            open(path, "w", encoding="utf-8").write(new)
    if not check and cnew != ctext:
        open(cpath, "w", encoding="utf-8").write(cnew)
    print("%d pages, %d patched, %d already; stylesheet %s" % (len(plan), sum(p[4] == "patched" for p in plan), sum(p[4] == "already" for p in plan),
                                                             "unchanged" if cnew == ctext else ("would change" if check else "widened to seven pills")))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--check" in sys.argv))
