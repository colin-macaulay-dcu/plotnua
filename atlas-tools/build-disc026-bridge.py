#!/usr/bin/env python3
"""DISC-026 · The House as a Power Station · Stage 2 bridge section (bounded builder).

Founder approval, 21 Oct 2026: "STAGE 2 BRIDGE · APPROVED FOR LOCAL BUILD".
The change is defined once, in atlas-tools/disc026_bridge_oct2026_layer.py.
Built on top of Stage 1 (title, description, anchors; corrections F1-F5),
which it reads through and does not change.

  python3 atlas-tools/build-disc026-bridge.py --apply   Stage 1 page -> bridged (refuses otherwise)
  python3 atlas-tools/build-disc026-bridge.py --check   guards B1-B9
  python3 atlas-tools/build-disc026-bridge.py --prove   break each guard in memory; each must fire

GUARDS
  B1  the governed section and the corrected physics sentence are present
      exactly once, with their markers; the superseded "2024 it was 22%" is gone
  B2  placement: directly after "Computing and heat" (S2) and before the
      "Not here yet" transition into Home compute, inside the same article block
  B3  outside the bridge, the page is byte-identical to Stage 1 as reviewed
      (STAGE1_SHA), and read back through every governed layer it is
      production 18a9afd (BASE_SHA); re-applying gives exactly the page
  B4  every figure in the new text is on the sourced list (CSO, CRU, Fortum,
      Fjernvarme Fyn, EU Directive 2023/1791) and nothing else
  B5  evidence states: Tallaght and Odense TODAY, Espoo EMERGING, the home
      NOT YET (the page's three .ev weights, no fourth); the home is stated as
      not available to an Irish homeowner today
  B6  no commercial or promotional claim: no partnership, ranking, price,
      income or call to action; distributed computing is never said to
      replace or solve anything except in the approved negation; Tandem
      Compute named once; the bridge carries no links at all
  B7  identity: H1, flagship subtitle, the seven editorial headings and
      kickers, title and description unchanged; exactly one H2 added, in the
      stated position; G18 (no category label leads a heading)
  B8  the Tallaght section the bridge refers to exists below it, exactly once
  B9  the EU sentence carries the directive's own condition ("technically or
      economically feasible") and its 1 MW threshold
"""
import hashlib
import html as htmlmod
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from disc026_bridge_oct2026_layer import (with_bridge, without_bridge, edits, SECTION,  # noqa: E402
                                          BEGIN, END, PHYS_OLD, PHYS_NEW)
from disc026_seo_a_layer import without_seo_a, HEADINGS, KICKERS, TITLE_NEW, DESC_NEW  # noqa: E402
from disc026_facts_oct2026_layer import without_facts, without_section_fact  # noqa: E402

ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"
BASE_SHA = "68774dc8a6ad1a9bd49a2457f68add87927eaff263b2249da5898c5e975b6d54"    # page at 18a9afd
STAGE1_SHA = "d7a6fe6fee14a10edf1ebcddbf64b1c98a551ae2bd3ebe4b65c7a9dedb946d38"  # page at Stage 1 (16054fd)
H1 = '<h1>The House as a Power Station</h1>'
SUBTITLE = ('<p class="subtitle">What if your house could one day do some of the work of a\n'
            '      data centre &mdash; and use the heat it creates?</p>')
S2_H2 = "Computers produce heat. Homes need heat. What if one could help supply the other?"
NEW_H2 = "Almost a quarter of Ireland’s electricity now goes to data centres. Nearly all of it ends up as heat."
G18 = re.compile(r'<h[23][^>]*>\s*(Solar energy|Battery storage|Small wind|EV energy|Solar panels|'
                 r'Home batteries|Air-source|Ground-source|Electric cars|Electricity exports)\b')
# every number allowed in the new visible text, with where it comes from
SOURCED = {
    "23%": "CSO 2025 share", "7,663": "CSO 2025 GWh", "10%": "CSO growth", "2%": "CSO all other users",
    "18%": "CSO urban households", "2026": "CSO release date (July 2026); Fortum (May 2026)",
    "2025": "CRU decision (December 2025); EU deadline (October 2025)", "80%": "CRU renewables",
    "2023": "SEAI Tallaght", "2019": "Ramboll / Fjernvarme Fyn Odense", "11,000": "Dansk Fjernvarme / Fjernvarme Fyn",
    "2027": "Fortum (next year)", "40%": "Fortum share", "1": "Directive 2023/1791 Art. 26(6), 1 MW",
}
PHYS_SOURCED = {"5%", "2015", "2025", "23%", "31%", "2034"}
BANNED = [r"\bpartner", r"\bbest\b", r"\bleading\b", r"\brecommend", r"\bcheapest\b", r"\bearn", r"\bincome\b",
          r"\bpaid\b", r"\bprice", r"&euro;|€|£", r"\bsign up\b", r"\bcontact\b", r"\bsolves?\b", r"\bsolution\b",
          r"\breplaces?\b", r"\bwill replace\b", r"\bcan replace\b", r"\bguarantee", r"\bper kWh\b", r"\bc/kWh\b"]


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def visible(fragment):
    t = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", htmlmod.unescape(t)).strip()


def h2s(t):
    return [re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", m))).strip()
            for m in re.findall(r"<h2[^>]*>(.*?)</h2>", t, re.S)]


def section_of(page):
    a, b = page.find(BEGIN), page.find(END)
    return page[a:b + len(END)] if a >= 0 and b > a else ""


def guards(page, section_def=None):
    section_def = SECTION if section_def is None else section_def
    fails = []
    sec = section_of(page)
    # B1
    if page.count(BEGIN) != 1 or page.count(END) != 1:
        fails.append("B1 the bridge markers are not present exactly once")
    if sec != section_def:
        fails.append("B1 the bridge section differs from its governed definition")
    if page.count(PHYS_NEW) != 1 or PHYS_OLD in page or "2024 it was 22%" in page:
        fails.append("B1 the physics sentence is not the corrected 2025 figure")
    # B2
    i_s2 = page.find('<div class="kicker">Computing and heat</div>')
    i_sec = page.find(BEGIN)
    i_spark = page.find('<section class="spark reveal">\n  <p>Not here yet. But not hypothetical either.</p>')
    i_home = page.find('<div class="kicker">Home compute &middot; useful heat</div>')
    if not (0 <= i_s2 < i_sec < i_spark < i_home):
        fails.append("B2 the bridge is not between Computing and heat and Home compute")
    if not page[:i_sec].endswith("  </section>\n\n") or not page[i_sec:].startswith(BEGIN) \
            or not page.find(END + "</div>\n\n<section class=\"spark reveal\">") >= 0:
        fails.append("B2 the bridge is not directly after S2 and directly before the article close and the spark")
    # B3
    try:
        stage1 = without_bridge(page)
        if hashlib.sha256(stage1.encode("utf-8")).hexdigest() != STAGE1_SHA:
            fails.append("B3 outside the bridge the page is not Stage 1 as reviewed")
        base = without_section_fact(without_facts(without_seo_a(stage1)))
        if hashlib.sha256(base.encode("utf-8")).hexdigest() != BASE_SHA:
            fails.append("B3 read through every layer the page is not production 18a9afd")
        if with_bridge(stage1) != page:
            fails.append("B3 re-applying the bridge does not give the page")
    except ValueError as e:
        fails.append("B3 " + str(e))
        stage1 = None
    # B4
    vis = visible(sec)
    nums = set(re.findall(r"\d{1,3}(?:,\d{3})+%?|\d+%?", vis))
    stray = sorted(n for n in nums if n not in SOURCED)
    if stray:
        fails.append("B4 unsourced figure(s) in the bridge: " + ", ".join(stray))
    pnums = set(re.findall(r"\d{1,3}(?:,\d{3})+%?|\d+%?", visible(PHYS_NEW if PHYS_NEW in page else "")))
    if pnums != PHYS_SOURCED:
        fails.append("B4 the physics sentence figures are not the sourced set")
    # B5
    def ev_before(label):
        k = sec.find('<span class="dq-adv-label">' + label + "</span>")
        m = re.search(r'<span class="(ev(?: ev-[a-z]+)?)">([^<]*)</span>', sec[k:]) if k >= 0 else None
        return (m.group(1), m.group(2)) if m else (None, None)
    if ev_before("Tallaght, Dublin") != ("ev", "Today &mdash; since 2023"):
        fails.append("B5 Tallaght is not marked Today")
    if ev_before("Odense, Denmark") != ("ev", "Today &mdash; since 2019"):
        fails.append("B5 Odense is not marked Today")
    if ev_before("Espoo and Kirkkonummi, Finland") != ("ev ev-emerging", "Emerging &mdash; from 2027"):
        fails.append("B5 Espoo is not marked Emerging")
    evs = re.findall(r'<span class="(ev(?: ev-[a-z]+)?)">', sec)
    if set(evs) - {"ev", "ev ev-emerging", "ev ev-future"}:
        fails.append("B5 an evidence state other than the page's three")
    if '<span class="ev ev-future">Not yet</span>' not in sec or "Not available to an Irish homeowner today." not in sec:
        fails.append("B5 the home is not stated as Not yet / not available today")
    # B6
    approved_negation = "It is not a replacement for large data centres, and it is not an answer to Ireland’s data-centre demand."
    if approved_negation not in vis:
        fails.append("B6 the approved negation is missing")
    for pat in BANNED:
        if re.search(pat, vis.replace(approved_negation, ""), re.I):
            fails.append("B6 promotional or overclaiming language: " + pat)
    if vis.count("Tandem Compute") != 1:
        fails.append("B6 Tandem Compute is not named exactly once")
    hrefs = re.findall(r'href="([^"]*)"', sec)
    if hrefs:
        fails.append("B6 the bridge carries a link")
    # B7
    if page.count(H1) != 1 or page.count(SUBTITLE) != 1:
        fails.append("B7 the H1 or the flagship subtitle changed")
    for h in HEADINGS:
        if page.count("<h3>%s</h3>" % h) != 1:
            fails.append("B7 an editorial heading changed: " + h[:40])
    if re.findall(r'<span class="pos-where">([^<]*)</span>', page) != KICKERS:
        fails.append("B7 a position kicker changed")
    if page.count(TITLE_NEW) != 1 or page.count(DESC_NEW) != 1:
        fails.append("B7 the Stage 1 title or description changed")
    if stage1 is not None:
        a, b = h2s(stage1), h2s(page)
        k = a.index(S2_H2) + 1 if S2_H2 in a else -1
        if k < 0 or b != a[:k] + [NEW_H2] + a[k:]:
            fails.append("B7 the H2 sequence is not Stage 1 plus the one bridge H2 after Computing and heat")
    if G18.search(page):
        fails.append("B7 a category label leads a heading (G18)")
    # B8
    if page.count('id="data-centre-heat"') != 1 or page.find('id="data-centre-heat"') < page.find(END):
        fails.append("B8 the Tallaght section is not present exactly once below the bridge")
    # B9
    if "not technically or economically feasible" not in vis or "1 MW" not in vis.replace(" ", " "):
        fails.append("B9 the EU sentence lost the directive's condition or threshold")
    return fails


def main(argv):
    mode = argv[1] if len(argv) > 1 else "--check"
    page = PAGE.read_text(encoding="utf-8")
    if mode == "--apply":
        if BEGIN in page:
            die("already applied; run --check")
        if hashlib.sha256(page.encode("utf-8")).hexdigest() != STAGE1_SHA:
            die("the page is not Stage 1 as reviewed")
        try:
            new = with_bridge(page)
        except ValueError as e:
            die(str(e))
        f = guards(new)
        if f:
            die("; ".join(f))
        PAGE.write_text(new, encoding="utf-8")
        print("DISC-026 BRIDGE · APPLIED — %d governed edits · B1-B9 pass" % len(edits()))
        return
    if mode == "--check":
        f = guards(page)
        if f:
            print("CHECK FAILED\n  " + "\n  ".join(f))
            sys.exit(1)
        print("DISC-026 BRIDGE · CHECK OK — B1-B9 pass · sha256 %s" % hashlib.sha256(page.encode("utf-8")).hexdigest()[:16])
        return
    if mode == "--prove":
        if guards(page):
            die("the page does not pass its own check; nothing to prove against")
        sec = section_of(page)

        def in_sec(old, new):
            # break the page AND the definition together, so B1/B3 cannot be what fires
            return (lambda p: p.replace(sec, sec.replace(old, new, 1), 1),
                    SECTION.replace(old, new, 1))
        cases = [
            ("B1", lambda p: p.replace(PHYS_NEW, PHYS_OLD, 1), None),
            ("B2", lambda p: p.replace(sec, "", 1).replace('<section class="spark reveal">',
                                                           sec + '<section class="spark reveal">', 1), None),
            ("B3", lambda p: p.replace("No\n          moving parts", "No moving parts at all", 1), None),
            ("B4",) + in_sec("up 10% in a single year", "up 12% in a single year"),
            ("B5",) + in_sec('<span class="ev ev-emerging">Emerging &mdash; from 2027</span>',
                             '<span class="ev">Today &mdash; from 2027</span>'),
            ("B5",) + in_sec('<span class="ev ev-future">Not yet</span>', '<span class="ev ev-emerging">Not yet</span>'),
            ("B6",) + in_sec("in Ireland, Tandem Compute is exploring", "in Ireland, our partner Tandem Compute is exploring"),
            ("B6",) + in_sec("It is not a replacement for large", "It can replace large"),
            ("B6",) + in_sec("SEAI. The detail is in the Tallaght section", 'SEAI. The detail is in <a href="https://tandemcompute.ai">the Tallaght section</a>'),
            ("B7", lambda p: p.replace("<h3>%s</h3>" % HEADINGS[0], "<h3>Solar panels &mdash; %s</h3>" % HEADINGS[0], 1), None),
            ("B8", lambda p: p.replace('id="data-centre-heat"', 'id="data-centre-heat-x"', 1), None),
            ("B9",) + in_sec("not technically or\n      economically feasible", "not technically\n      feasible"),
        ]
        ok = 0
        for code, mut, sdef in cases:
            p2 = mut(page)
            if p2 == page:
                print("  NOT APPLIED %s" % code); continue
            f = guards(p2, sdef)
            hit = any(x.startswith(code) for x in f) or (code in ("B3",) and any(x.startswith("B3") for x in f))
            ok += hit
            print("  %s %s -> %s" % ("CAUGHT" if hit else "MISSED", code, " | ".join(f)[:130] if f else "no failure"))
        print("%d/%d guards caught their break%s" % (ok, len(cases), " — PROVEN" if ok == len(cases) else ""))
        sys.exit(0 if ok == len(cases) else 1)
    die("usage: --apply | --check | --prove")


if __name__ == "__main__":
    main(sys.argv)
