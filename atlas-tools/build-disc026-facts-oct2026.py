#!/usr/bin/env python3
"""DISC-026 · The House as a Power Station · factual corrections F1-F5 (bounded builder).

Founder review, 20 October 2026, Decision 2: "Prepare factual corrections F1-F5."
The corrections are defined once, in atlas-tools/disc026_facts_oct2026_layer.py,
with the official source for each. F5a (the balcony line) is carried by the
look-again fragment, the source that section is generated from.

  python3 atlas-tools/build-disc026-facts-oct2026.py --apply   base -> corrected (refuses otherwise)
  python3 atlas-tools/build-disc026-facts-oct2026.py --check   guards T1-T7
  python3 atlas-tools/build-disc026-facts-oct2026.py --prove   break each guard in memory; each must fire

GUARDS
  T1  every corrected passage is present exactly once and its original is gone,
      on the page and (F5a) in the look-again fragment, which must agree
  T2  outside the corrected passages the page is byte-identical to production
      as approved: read back through the SEO Approach A layer, the reversed
      page hashes to BASE_SHA (the page at 18a9afd); re-applying gives the page
  T3  no stale claim survives anywhere on the page: the solar "before 2021",
      "a different year from the solar grant", "claimed retrospectively",
      "still working out whether to allow them"
  T4  current law is kept and proposed law is marked as proposed: the EUR 400
      exemption is still stated in both places; the Finance (No. 2) Bill 2026
      appears exactly twice, each time in a sentence that says "propos" and in
      a passage that says it is not yet law / until it is enacted; nothing
      states EUR 600 as the current exemption
  T5  the heat pump eligibility ("before 2021", correct per seai.ie) is untouched
  T6  identity untouched: the H1, the flagship subtitle, the H2 order, the seven
      editorial headings and kickers, the export explorer config
  T7  supplier neutrality: no supplier name, export rate, ranking word or
      percentage introduced by any corrected passage
"""
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from disc026_facts_oct2026_layer import (ARTICLE_EDITS, SECTION_OLD, SECTION_NEW,  # noqa: E402
                                         with_facts, without_facts, without_section_fact)
from disc026_seo_a_layer import without_seo_a, HEADINGS, KICKERS  # noqa: E402

ROOT = HERE.parent
BASE_SHA = "68774dc8a6ad1a9bd49a2457f68add87927eaff263b2249da5898c5e975b6d54"  # page at 18a9afd
PAGE = ROOT / "discovery-house-as-power-station.html"
FRAG = ROOT / "atlas-tools" / "disc026-look-again" / "look-again.html"
H1 = '<h1>The House as a Power Station</h1>'
SUBTITLE = ('<p class="subtitle">What if your house could one day do some of the work of a\n'
            '      data centre &mdash; and use the heat it creates?</p>')
HEAT_PUMP = ["establishes the position. The home must have been built and occupied\n            before 2021.</div>",
             "the position. Built and occupied before 2021.<br><br>"]
STALE = [(r"occupied before 2021\. The grant is not open where solar", "solar drawer still says before 2021"),
         (r"occupied before 2021\. The\s+grant can be claimed once", "solar detail still says before 2021"),
         (r"a\s+different year from the\s+solar grant", "the grants are still said to use different years"),
         (r"claimed retrospectively", "the retrospective question is still open on the page"),
         (r"still working out whether to allow", "plug-in solar is still framed as whether to allow")]
BILL = "Finance (No.&nbsp;2) Bill 2026"
SUPPLIERS = ("Electric Ireland", "Bord G", "Energia", "SSE", "Flogas", "Pinergy", "Yuno", "Community Power",
             "best", "cheapest", "top-rated", "recommended", "%", "c/kWh", "per kWh")


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def h2s(t):
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"<h2[^>]*>(.*?)</h2>", t, re.S)]


def px(t):
    m = re.search(r'<script type="application/json" class="pn-px-config" id="px-data">.*?</script>', t, re.S)
    return m.group(0) if m else None


def bill_passages(page):
    """Each passage on the page that names the Finance Bill: from the nearest
    preceding <strong> label to the next <br><br> or </div>."""
    out = []
    for m in re.finditer(re.escape(BILL), page):
        a = page.rfind("<strong>", 0, m.start())
        ends = [e for e in (page.find("<br><br>", m.end()), page.find("</div>", m.end())) if e >= 0]
        out.append(re.sub(r"\s+", " ", page[a:min(ends)]))
    return out


def guards(page, frag, edits_def=None):
    edits_def = ARTICLE_EDITS if edits_def is None else edits_def
    fails = []
    try:
        base = without_facts(page)
    except ValueError as e:
        fails.append("T1 " + str(e))
        base = None
    for code, old, new in ARTICLE_EDITS:
        if page.count(new) != 1 or old in page:
            fails.append("T1 %s not present exactly once, or its original survives" % code)
    if page.count(SECTION_NEW) != 1 or SECTION_OLD in page:
        fails.append("T1 F5a not present exactly once on the page")
    if frag.count(SECTION_NEW) != 1 or SECTION_OLD in frag:
        fails.append("T1 F5a not present exactly once in the look-again fragment")
    if base is not None:
        try:
            full_base = without_section_fact(without_seo_a(base))
            if hashlib.sha256(full_base.encode("utf-8")).hexdigest() != BASE_SHA:
                fails.append("T2 outside the corrected passages the page is not the approved base (18a9afd)")
            if with_facts(base) != page:
                fails.append("T2 re-applying the corrections does not give the page")
        except ValueError as e:
            fails.append("T2 " + str(e))
    for pat, msg in STALE:
        if re.search(pat, page):
            fails.append("T3 " + msg)
    if page.count("&euro;400 a year") != 2:
        fails.append("T4 the current EUR 400 exemption is no longer stated in both places")
    if page.count(BILL) != 2:
        fails.append("T4 the Finance Bill is not mentioned exactly twice")
    for flat in bill_passages(page):
        if "propos" not in flat:
            fails.append("T4 the Finance Bill is not described as a proposal")
        if "not yet law" not in flat and "until it is enacted" not in flat:
            fails.append("T4 the proposed EUR 600 is not marked as not yet law")
    if re.search(r"first &euro;600|&euro;600 a year of microgeneration|&euro;600 a year from exporting", page):
        fails.append("T4 EUR 600 is stated as the current exemption")
    for s in HEAT_PUMP:
        if page.count(s) != 1:
            fails.append("T5 the heat pump eligibility passage changed")
    if page.count(H1) != 1 or page.count(SUBTITLE) != 1:
        fails.append("T6 the H1 or the flagship subtitle changed")
    if base is not None and h2s(page) != h2s(base):
        fails.append("T6 the H2 order changed")
    for h in HEADINGS:
        if page.count("<h3>%s</h3>" % h) != 1:
            fails.append("T6 an editorial heading changed: " + h[:40])
    if re.findall(r'<span class="pos-where">([^<]*)</span>', page) != KICKERS:
        fails.append("T6 a position kicker changed")
    if px(page) is None or (base is not None and px(page) != px(base)):
        fails.append("T6 the export explorer configuration changed")
    added = " ".join(new for _, _, new in edits_def) + " " + SECTION_NEW
    for w in SUPPLIERS:
        if w.lower() in added.lower():
            fails.append("T7 a corrected passage introduces %r" % w)
    return fails


def main(argv):
    mode = argv[1] if len(argv) > 1 else "--check"
    page = PAGE.read_text(encoding="utf-8")
    frag = FRAG.read_text(encoding="utf-8")
    if mode == "--apply":
        if any(new in page for _, _, new in ARTICLE_EDITS):
            die("already applied; run --check")
        if page.count(SECTION_OLD) != 1 or frag.count(SECTION_OLD) != 1:
            die("the balcony line is not present exactly once on the page and in the fragment")
        try:
            new_page = with_facts(page).replace(SECTION_OLD, SECTION_NEW, 1)
        except ValueError as e:
            die(str(e))
        new_frag = frag.replace(SECTION_OLD, SECTION_NEW, 1)
        f = guards(new_page, new_frag)
        if f:
            die("; ".join(f))
        PAGE.write_text(new_page, encoding="utf-8")
        FRAG.write_text(new_frag, encoding="utf-8")
        print("DISC-026 FACTS OCT 2026 · APPLIED — %d article edits + F5a · T1-T7 pass" % len(ARTICLE_EDITS))
        return
    if mode == "--check":
        f = guards(page, frag)
        if f:
            print("CHECK FAILED\n  " + "\n  ".join(f))
            sys.exit(1)
        print("DISC-026 FACTS OCT 2026 · CHECK OK — T1-T7 pass · sha256 %s"
              % hashlib.sha256(page.encode("utf-8")).hexdigest()[:16])
        return
    if mode == "--prove":
        if guards(page, frag):
            die("the page does not pass its own check; nothing to prove against")
        f3a_new = ARTICLE_EDITS[4][2]
        f4a_new = ARTICLE_EDITS[6][2]
        cases = [
            ("T1", lambda p, f: (p, f.replace(SECTION_NEW, SECTION_OLD, 1))),
            ("T2", lambda p, f: (p.replace("No\n          moving parts", "No moving parts at all", 1), f)),
            ("T3", lambda p, f: (p.replace("<p>Four things are moving at once.",
                                           "<p>Older homes built and occupied before 2021. The grant is not open where solar. Four things are moving at once.", 1), f)),
            ("T3", lambda p, f: (p.replace("<p>Four things are moving at once.",
                                           "<p>Ireland is still working out whether to allow them. Four things are moving at once.", 1), f)),
            ("T4", lambda p, f: (p.replace(f4a_new, f4a_new.replace(", and is not yet law", "")
                                                          .replace("proposes raising", "raises"), 1), f)),
            ("T4", lambda p, f: (p.replace("<p>Four things are moving at once.",
                                           "<p>The first &euro;600 a year is tax-free. Four things are moving at once.", 1), f)),
            ("T5", lambda p, f: (p.replace(HEAT_PUMP[1], HEAT_PUMP[1].replace("2021", "2025"), 1), f)),
            ("T6", lambda p, f: (p.replace("<h3>%s</h3>" % HEADINGS[2], "<h3>Air-source heat pumps</h3>", 1), f)),
            # T7 guards the DEFINITION of the corrections: break the layer, not the page
            ("T7", "layer"),
        ]
        ok = 0
        for code, mut in cases:
            if mut == "layer":
                bad = [(c, o, n.replace("SEAI.</div>", "SEAI. Energia pays best.</div>") if c == "F3a" else n)
                       for c, o, n in ARTICLE_EDITS]
                fl = guards(page, frag, bad)
            else:
                p2, f2 = mut(page, frag)
                if (p2, f2) == (page, frag):
                    print("  NOT APPLIED %s" % code); continue
                fl = guards(p2, f2)
            hit = any(x.startswith(code) for x in fl) or (code not in ("T1", "T4", "T7") and any(x.startswith("T2") for x in fl))
            ok += hit
            print("  %s %s -> %s" % ("CAUGHT" if hit else "MISSED", code, " | ".join(fl)[:120] if fl else "no failure"))
        print("%d/%d guards caught their break%s" % (ok, len(cases), " — PROVEN" if ok == len(cases) else ""))
        sys.exit(0 if ok == len(cases) else 1)
    die("usage: --apply | --check | --prove")


if __name__ == "__main__":
    main(sys.argv)
