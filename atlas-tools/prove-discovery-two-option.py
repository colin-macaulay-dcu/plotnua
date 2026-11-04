#!/usr/bin/env python3
"""PLOTNUA · DISCOVERY TWO-OPTION COMPONENT · guard (founder approval, 2 Nov 2026: Living in the Garden pilot).

  D1 SCOPE      exactly the Discoveries listed in atlas-tools/discovery-two-option/two-option.json carry
                the component, once each; no other page carries it (the homepage included)
  D2 ELIGIBLE   a listed Discovery has a supplier gallery and a Maker Explorer (explore yourself), and every
                homework link is an EXISTING Your Plot Journey route that your-plot.html already handles
  D3 PLACEMENT  inside the gallery head: after the figures, before the carousel (#sg-track)
  D4 NO INTAKE  the component carries no form, input, script or network call, and no external link
  D5 TARGET     the "explore yourself" link points to an element that exists on the same page
  D6 GENERATED  the page region equals what build-supplier-gallery.py renders (builder --check)

Usage:  python3 atlas-tools/prove-discovery-two-option.py [--self-test]
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "atlas-tools" / "discovery-two-option" / "two-option.json"
COMP = re.compile(r'<div class="pn-two" role="group".*?</ul></div></div>', re.S)


def check(pages, cfg, yp):
    bad = []
    listed = cfg["discoveries"]
    for name, txt in pages.items():
        n = len(COMP.findall(txt))
        if name in listed and n != 1:
            bad.append("D1 %s must carry the component exactly once (found %d)" % (name, n))
        if name not in listed and ('class="pn-two"' in txt):
            bad.append("D1 %s carries the component but is not listed" % name)
    for name, c in listed.items():
        txt = pages.get(name, "")
        if "data-pn-supplier-gallery" not in txt or "data-pn-maker-explorer" not in txt:
            bad.append("D2 %s has no supplier gallery and Maker Explorer to explore" % name)
        for j in c["homework"]["journeys"]:
            m = re.fullmatch(r"your-plot\.html\?discovery=([a-z-]+)", j["href"])
            if not m or ("discovery=" + m.group(1)) not in yp and ("'" + m.group(1) + "'") not in yp:
                bad.append("D2 %s: %s is not an existing Your Plot Journey route" % (name, j["href"]))
        comp = COMP.findall(txt)
        if not comp:
            continue
        comp = comp[0]
        i, figs, track = txt.find(comp), txt.find('class="pn-sg-figs"'), txt.find('id="sg-track"')
        if not (0 <= figs < i < track):
            bad.append("D3 %s: the component must sit after the figures and before the carousel" % name)
        if re.search(r"<form\b|<input\b|<textarea\b|<script\b|fetch\s*\(|XMLHttpRequest|sendBeacon|workers\.dev", comp, re.I):
            bad.append("D4 %s: the component carries a form, input, script or network call" % name)
        if re.search(r'href="(?:https?:)?//', comp):
            bad.append("D4 %s: the component carries an external link" % name)
        tgt = c["explore"]["target"]
        if not tgt.startswith("#") or ('id="%s"' % tgt[1:]) not in txt or ('href="%s"' % tgt) not in comp:
            bad.append("D5 %s: the explore link target %s is missing" % (name, tgt))
        for j in c["homework"]["journeys"]:
            if ('href="%s"' % j["href"]) not in comp:
                bad.append("D2 %s: the Journey link %s is not rendered" % (name, j["href"]))
    return bad


def load():
    pages = {p.name: p.read_text(encoding="utf-8") for p in ROOT.glob("*.html")}
    return pages, json.loads(CFG.read_text(encoding="utf-8")), (ROOT / "your-plot.html").read_text(encoding="utf-8")


def self_test():
    pages, cfg, yp = load()
    if check(pages, cfg, yp):
        print("SELF-TEST · the real tree must pass first"); return 1
    L = "discovery-living-in-the-garden.html"
    if L not in cfg["discoveries"]:
        # DISC-008 Phase 2 (3 Nov 2026) retired the card on its pilot page (consolidated into the page's closing
        # decision). The mutations still run, on a fixture: the retired configuration rendered by the builder's
        # own function and placed where the builder places it, so the guard keeps its proven reach.
        import importlib.util, tempfile
        retired = cfg.get("_retired", {}).get(L, {}).get("config")
        if not retired:
            print("SELF-TEST · no listed Discovery and no retired configuration to build a fixture from"); return 1
        cfg = json.loads(json.dumps(cfg)); cfg["discoveries"][L] = retired
        spec = importlib.util.spec_from_file_location("sg", ROOT / "atlas-tools" / "build-supplier-gallery.py")
        sg = importlib.util.module_from_spec(spec); spec.loader.exec_module(sg)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as t:
            json.dump(cfg, t, ensure_ascii=False)
        sg.TWO_OPTION = Path(t.name)
        rendered = sg.two_option_html(L)
        pages = dict(pages)
        pages[L] = pages[L].replace('<ul class="pn-sg-track"', rendered.strip() + '<ul class="pn-sg-track"', 1)
        if check(pages, cfg, yp):
            print("SELF-TEST · the fixture must pass first: " + "; ".join(check(pages, cfg, yp))); return 1
    comp = COMP.findall(pages[L])[0]
    def mut(fn):
        p = dict(pages); c = json.loads(json.dumps(cfg)); y = yp; return fn(p, c, y) or (p, c, y)
    cases = [
        ("D1", lambda p, c, y: p.__setitem__("discovery-garden-retreat.html", p["discovery-garden-retreat.html"] + comp)),
        ("D1", lambda p, c, y: p.__setitem__("index.html", p["index.html"] + comp)),
        ("D1", lambda p, c, y: p.__setitem__(L, p[L].replace(comp, ""))),
        ("D2", lambda p, c, y: c["discoveries"][L]["homework"]["journeys"].append({"label": "x", "href": "your-plot.html?discovery=sauna"})),
        ("D2", lambda p, c, y: p.__setitem__(L, p[L].replace("data-pn-maker-explorer", "data-x"))),
        ("D3", lambda p, c, y: p.__setitem__(L, p[L].replace(comp, "").replace('id="sg-track"', 'id="sg-track"', 1).replace("</ul>{sites}", "") .replace('<ul class="pn-sg-track"', comp + '<ul class="pn-sg-track"').replace('class="pn-sg-figs"', 'class="pn-sg-figs-x"') )),
        ("D4", lambda p, c, y: p.__setitem__(L, p[L].replace(comp, comp.replace('<ul class="pn-two-btns"', '<form action="https://x.workers.dev"></form><ul class="pn-two-btns"')))),
        ("D4", lambda p, c, y: p.__setitem__(L, p[L].replace(comp, comp.replace('href="your-plot.html?discovery=garden-room"', 'href="https://example.com/"')))),
        ("D5", lambda p, c, y: p.__setitem__(L, p[L].replace('id="%s"' % c["discoveries"][L]["explore"]["target"][1:], 'id="sg-x"'))),
    ]
    missed = 0
    for code, fn in cases:
        p, c, y = mut(fn)
        hit = [b for b in check(p, c, y) if b.startswith(code)]
        print("  %s  %s mutation" % ("CAUGHT" if hit else "MISSED", code)); missed += 0 if hit else 1
    print("DISCOVERY TWO-OPTION PROOF · %s — %d mutations, %d missed" % ("OK" if not missed else "FAILED", len(cases), missed))
    return 1 if missed else 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    bad = check(*load())
    r = subprocess.run([sys.executable, str(ROOT / "atlas-tools/build-supplier-gallery.py"), "--check"], capture_output=True, text=True)
    if r.returncode != 0:
        bad.append("D6 the gallery regions differ from build-supplier-gallery.py's rendering")
    if bad:
        for b in bad: print("FAIL " + b)
        print("DISCOVERY TWO-OPTION · REFUSED — %d problem(s)" % len(bad)); return 2
    print("DISCOVERY TWO-OPTION · OK — D1-D6: listed Discoveries only, existing Journey routes, placed beneath the "
          "figures and above the carousel, no intake, explore target present, generated region current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
