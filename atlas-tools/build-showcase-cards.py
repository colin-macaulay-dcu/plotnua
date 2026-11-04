#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAKER SHOWCASE CARDS - reusable component builder (founder approval, 4 Nov 2026).

Renders a small set of image-led cards, each linking to an existing PlotNua supplier showcase
(suppliers/<slug>.html), into a Discovery page between the PN-SHOWCASE-CARDS markers, placed
immediately before the configured anchor. Separate from the supplier gallery and the Maker
Explorer, and never counted in their figures.

Data: atlas-tools/showcase-cards/showcase-cards.json. Each card reuses one photograph already
published on that supplier's showcase (same origin, alt, size and credit), so no new image
enters the site. Styling: assets/components/pn-showcase-cards.css.

Run: python3 atlas-tools/build-showcase-cards.py [--check]
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "atlas-tools" / "showcase-cards" / "showcase-cards.json").read_text(encoding="utf-8"))
SHOWCASES = ROOT / "supplier-preview-system" / "showcases"
CSS = "assets/components/pn-showcase-cards.css?v=1"
START, END = "<!-- PN-SHOWCASE-CARDS v1 · built by atlas-tools/build-showcase-cards.py from atlas-tools/showcase-cards/showcase-cards.json · do not hand-edit -->", "<!-- /PN-SHOWCASE-CARDS -->"
E_ = lambda s: html.escape(str(s), quote=True)


def card(c):
    data = json.loads((SHOWCASES / c["showcase"] / "showcase.json").read_text(encoding="utf-8"))
    s = data["supplier"]
    page = f"suppliers/{s['slug']}.html"
    if not (ROOT / page).is_file():
        sys.exit(f"FAIL: showcase page {page} does not exist")
    if 'content="noindex' in (ROOT / page).read_text(encoding="utf-8"):
        sys.exit(f"FAIL: {page} is still a private preview; it cannot be linked from a Discovery")
    img = next((i for i in data["images"] if i["id"] == c["image"]), None)
    if not img or img.get("kind") != "Photograph":
        sys.exit(f"FAIL: {c['showcase']}: card image {c['image']} is not a photograph on its showcase")
    rec = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
           if r["organisation_name"] == s["name"]]
    if len(rec) != 1 or not rec[0]["permission_outcome"].startswith("Granted") or rec[0]["required_credit"] != s["credit"]:
        sys.exit(f"FAIL: {s['name']}: no live rights record with the page credit")
    hid = "pn-sc-" + s["slug"]
    return (f'<li><article class="pn-sc-card" aria-labelledby="{hid}">'
            f'<a class="pn-sc-media" href="{E_(page)}" tabindex="-1" aria-hidden="true">'
            f'<img src="{E_(img["origin"])}" alt="" width="{img["w"]}" height="{img["h"]}" loading="lazy" decoding="async" referrerpolicy="no-referrer"></a>'
            f'<div class="pn-sc-body"><p class="pn-sc-cap"><span class="pn-sc-kind">Photograph</span> {E_(s["credit"])}</p>'
            f'<h3 class="pn-sc-name" id="{hid}">{E_(s["name"])}</h3>'
            f'<p class="pn-sc-desc">{E_(c["description"])}</p>'
            f'<p class="pn-sc-go"><a href="{E_(page)}" aria-label="Explore the {E_(s["name"])} showcase on PlotNua">'
            f'<span>Explore showcase</span> <span aria-hidden="true">&rarr;</span></a></p></div></article></li>')


def block(d):
    cards = "".join(card(c) for c in d["cards"])
    return (f'{START}\n<link rel="stylesheet" href="{CSS}">\n'
            f'<section class="pn-sc" aria-labelledby="pn-sc-k"><div class="pn-sc-wrap">'
            f'<p class="pn-sc-k" id="pn-sc-k">{E_(d["kicker"])}</p>'
            f'<ul class="pn-sc-grid" role="list">{cards}</ul></div></section>\n{END}\n')


def main():
    ok = True
    for name, d in CFG.items():
        if name.startswith("_"):
            continue
        p = ROOT / name
        src = p.read_text(encoding="utf-8")
        base = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n\n?", "", src, flags=re.S)
        if base.count(d["anchor"]) != 1:
            sys.exit(f"FAIL: {name}: anchor not found exactly once")
        out = base.replace(d["anchor"], block(d) + "\n" + d["anchor"], 1)
        if "--check" in sys.argv:
            same = out == src
            ok &= same
            print(("SHOWCASE CARDS · CHECK OK — " if same else "STALE: ") + name)
        else:
            p.write_text(out, encoding="utf-8")
            print("wrote", name)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
