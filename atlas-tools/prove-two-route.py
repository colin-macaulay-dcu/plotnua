#!/usr/bin/env python3
"""PLOTNUA · TWO ROUTES · Phase 1 guard (founder approval, 2 Nov 2026 · Customer Journey Evolution).

Holds what Phase 1 promised, and nothing more:

  T1  SECTION: index.html carries the two-route section exactly once, fenced by TWO-ROUTE markers,
      after the H6 hero and before the Atlas strip
  T2  HERO LOCKED: the H6 GARDEN COMPONENT block is byte-identical to its recorded hash
  T3  LINKS: every link in the section and on the two reading pages resolves to a file in the
      repository (or is an approved external contact: wa.me, mailto, tel)
  T4  NO INTAKE: no <form>, no input, no fetch/XMLHttpRequest/sendBeacon and no Worker endpoint
      in the section or on the two reading pages; no link to an unbuilt comparison request
  T5  FREE: "Free for homeowners" appears in the section and on both pages; no paid-service
      wording (fee for homeowners, subscription, premium research, price of a comparison) anywhere
  T6  HEADER: pn_header renders "Get help choosing" -> help-choosing.html in the desktop bar and
      the phone Menu
  T7  ATLAS FIGURE: the homepage shows "Makers researched" and no longer shows "Suppliers"

Usage:  python3 atlas-tools/prove-two-route.py            check the repository
        python3 atlas-tools/prove-two-route.py --self-test prove every check can fail
"""
import hashlib, re, sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import pn_header as H  # noqa: E402

PAGES = ["help-choosing.html", "how-plotnua-works-with-makers.html"]
BEGIN, END = "<!-- TWO-ROUTE · BEGIN", "<!-- TWO-ROUTE · END -->"
H6_RX = re.compile(r"<!-- H6 GARDEN COMPONENT · BEGIN.*?<!-- H6 GARDEN COMPONENT · END -->", re.S)
# sha256 of the H6 component as released (production 86ec2dd / a396342); the hero is locked.
H6_SHA = "3e5be3bc334e09ad85daa8f447370ab10a896f7e6c4caa3759b0744b162da42d"
PAID = re.compile(r"(subscription|premium research|paid service|paid comparison|comparison fee|"
                  r"fee for homeowners|homeowners? (?:will )?pay|charge (?:you|homeowners)|€\s?\d|£\s?\d)", re.I)


def section(home):
    i, j = home.find(BEGIN), home.find(END)
    return home[i:j] if 0 <= i < j else ""


def check(files):
    bad = []
    home = files["index.html"]
    # T1
    if home.count(BEGIN) != 1 or home.count(END) != 1:
        bad.append("T1 the two-route section must appear exactly once")
    else:
        hero_end = home.find("<!-- H6 GARDEN COMPONENT · END -->")
        atlas = home.find('id="research"')
        if not (0 <= hero_end < home.find(BEGIN) < home.find(END) < atlas):
            bad.append("T1 the section must sit after the H6 hero and before the Atlas strip")
    sec = section(home)
    # T2
    m = H6_RX.findall(home)
    if len(m) != 1 or hashlib.sha256(m[0].encode("utf-8")).hexdigest() != H6_SHA:
        bad.append("T2 the locked H6 component changed")
    # T3 / T4 / T5
    for name, txt in [("index.html#two-routes", sec)] + [(p, files[p]) for p in PAGES]:
        body = txt[txt.find("<main"):txt.find("</main>") + 7] if name in PAGES else txt
        for h in re.findall(r'href="([^"]+)"', body):
            if h.startswith(("https://wa.me/", "mailto:", "tel:", "#")):
                continue
            if h.startswith(("http://", "https://")):
                bad.append("T3 %s: unexpected external link %s" % (name, h)); continue
            f = h.split("#")[0].split("?")[0] or "index.html"
            if f not in files["__exists__"]:
                bad.append("T3 %s: link to a missing page %s" % (name, h))
        if re.search(r"<form\b|<input\b|<textarea\b|\bfetch\s*\(|XMLHttpRequest|sendBeacon|workers\.dev", body, re.I):
            bad.append("T4 %s: carries a form, input or network call (intake is not approved)" % name)
        if re.search(r"comparison[-_]?request|request-comparison|compare-request", body, re.I):
            bad.append("T4 %s: links to an unbuilt comparison request" % name)
        if "Free for homeowners" not in re.sub(r"<[^>]+>", "", body) and "free for homeowners" not in body:
            bad.append("T5 %s: the free-to-homeowners statement is missing" % name)
        if PAID.search(re.sub(r"<[^>]+>", " ", body)):
            bad.append("T5 %s: paid-service wording appeared: %r" % (name, PAID.search(re.sub(r"<[^>]+>", " ", body)).group(0)))
    # T6
    want = '<a class="pn-hdr-help" href="help-choosing.html">'
    if want not in files["__bar__"] or "Get help choosing" not in files["__bar__"]:
        bad.append("T6 the desktop header lacks Get help choosing")
    if 'pn-hdr-pl--help" href="help-choosing.html"' not in files["__row__"]:
        bad.append("T6 the phone Menu lacks Get help choosing")
    # T7
    if "<dd>Makers researched</dd>" not in home or "<dd>Suppliers</dd>" in home:
        bad.append("T7 the homepage Atlas figure must read Makers researched")
    return bad


def load():
    files = {n: (ROOT / n).read_text(encoding="utf-8") for n in ["index.html"] + PAGES}
    files["__exists__"] = {str(p.relative_to(ROOT)) for p in ROOT.glob("*.html")} | {"plotart/", "gridnua/"}
    files["__bar__"] = H.bar("about.html", True, False)
    files["__row__"] = H.row("about.html")
    return files


def self_test():
    base = load()
    if check(base):
        print("SELF-TEST · the real tree must pass first"); return 1
    sec = section(base["index.html"])
    mutations = [
        ("T1 section removed", lambda f: f.__setitem__("index.html", f["index.html"].replace(BEGIN, "<!-- gone"))),
        ("T1 section moved below Atlas", lambda f: f.__setitem__("index.html", f["index.html"].replace(sec + END, "").replace('<section class="discover', sec + END + '<section class="discover'))),
        ("T2 hero edited", lambda f: f.__setitem__("index.html", f["index.html"].replace("<!-- H6 GARDEN COMPONENT · END -->", " <!-- H6 GARDEN COMPONENT · END -->", 1))),
        ("T3 broken link", lambda f: f.__setitem__(PAGES[0], f[PAGES[0]].replace('href="your-plot.html?discovery=garden-room"', 'href="nowhere.html"', 1))),
        ("T4 form added", lambda f: f.__setitem__(PAGES[0], f[PAGES[0]].replace("</main>", "<form action=\"https://x.workers.dev\"></form></main>"))),
        ("T4 comparison link", lambda f: f.__setitem__("index.html", f["index.html"].replace('tr-route--help" href="help-choosing.html"', 'tr-route--help" href="help-choosing.html#comparison-request"', 1))),
        ("T5 free removed", lambda f: f.__setitem__(PAGES[1], f[PAGES[1]].replace("free for homeowners", "available").replace("Free for homeowners", "Available"))),
        ("T5 paid wording", lambda f: f.__setitem__(PAGES[0], f[PAGES[0]].replace("</main>", "<p>A premium research subscription is coming.</p></main>"))),
        ("T6 header link missing", lambda f: f.__setitem__("__bar__", f["__bar__"].replace("pn-hdr-help", "pn-hdr-x"))),
        ("T6 menu link missing", lambda f: f.__setitem__("__row__", f["__row__"].replace("pn-hdr-pl--help", "pn-hdr-pl--x"))),
        ("T7 old figure back", lambda f: f.__setitem__("index.html", f["index.html"].replace("<dd>Makers researched</dd>", "<dd>Suppliers</dd>"))),
    ]
    missed = 0
    for label, mut in mutations:
        f = dict(base); f["__exists__"] = set(base["__exists__"]); mut(f)
        caught = [b for b in check(f) if b.startswith(label[:2])]
        print("  %s  %s" % ("CAUGHT  " if caught else "MISSED  ", label))
        missed += 0 if caught else 1
    print("TWO ROUTES PROOF · %s — %d mutations, %d missed" % ("OK" if not missed else "FAILED", len(mutations), missed))
    return 1 if missed else 0


def main():
    if "--self-test" in sys.argv:
        return self_test()
    bad = check(load())
    if bad:
        for b in bad: print("FAIL " + b)
        print("TWO ROUTES · REFUSED — %d problem(s)" % len(bad)); return 2
    print("TWO ROUTES · OK — T1-T7: section placed once beneath the locked hero, links resolve, no intake, "
          "free-to-homeowners stated, no paid wording, header entry present, Atlas figure defined")
    return 0


if __name__ == "__main__":
    sys.exit(main())
