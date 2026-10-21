#!/usr/bin/env python3
"""DISC-026 · The House as a Power Station · SEO Approach A (bounded builder, REVISED 1b).

Founder approval, 20 October 2026: "SEO APPROACH A · APPROVED FOR PREPARATION",
revised the same evening: Decision 1 = Option 1b. Title, description and the
four missing section anchors only. The seven editorial headings are NOT
labelled; prove-disc026-discovery.mjs G18 is preserved, not narrowed.
The change itself is defined once, in atlas-tools/disc026_seo_a_layer.py.

  python3 atlas-tools/build-disc026-seo-a.py --apply   base state -> approved state (refuses otherwise)
  python3 atlas-tools/build-disc026-seo-a.py --check   verify the approved state, guards S1-S8
  python3 atlas-tools/build-disc026-seo-a.py --prove   break each guard in memory; each must fire

GUARDS
  S1  every governed string is present exactly once, and the page reverses
      exactly to a base that carries every original string exactly once
  S2  the H1 and the flagship subtitle are byte-identical to the base
  S3  the section order is unchanged: the sequence of H2 texts and of
      energy-anatomy positions is identical to the base
  S4  the seven editorial headings are untouched, bare <h3>s, each exactly
      once; the seven kickers are untouched; no category phrase leads any
      h2/h3 (the same pattern as prove-disc026-discovery.mjs G18)
  S5  outside the governed strings, the page is byte-identical to production
      as approved: read back through every later governed layer (the
      October 2026 factual corrections), the reversed page must hash to
      BASE_SHA (the page at 18a9afd), and re-applying the change must give
      exactly the current page.
  S6  Open Graph and Twitter title/description are unchanged (the flagship
      line stays the Discovery's social identity)
  S7  the export explorer configuration (#px-data) is byte-identical
  S8  no supplier name, rate, ranking word or price was introduced by the change
"""
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from disc026_seo_a_layer import (with_seo_a, without_seo_a, edits, HEADINGS, KICKERS,  # noqa: E402
                                 TITLE_NEW)
try:  # a later governed layer on the same page; absent before it exists
    from disc026_facts_oct2026_layer import without_facts, without_section_fact  # noqa: E402
except ImportError:  # fail-closed: any un-layered edit still breaks the S5 hash
    def without_facts(t):
        return t

    def without_section_fact(t):
        return t
try:  # the Stage 2 bridge layer (21 Oct 2026); absent before it exists
    from disc026_bridge_oct2026_layer import without_bridge  # noqa: E402
except ImportError:  # fail-closed: any un-layered edit still breaks the S5 hash
    def without_bridge(t):
        return t

ROOT = HERE.parent
# The page at production 18a9afd, before this change (sha256 of its bytes).
BASE_SHA = "68774dc8a6ad1a9bd49a2457f68add87927eaff263b2249da5898c5e975b6d54"
PAGE = ROOT / "discovery-house-as-power-station.html"
H1 = '<h1>The House as a Power Station</h1>'
SUBTITLE = ('<p class="subtitle">What if your house could one day do some of the work of a\n'
            '      data centre &mdash; and use the heat it creates?</p>')
SOCIAL = re.compile(r'<meta (?:property="og:(?:title|description)"|name="twitter:(?:title|description)")[^>]*>')
# The same pattern as prove-disc026-discovery.mjs G18, widened to every label
# the founder's 20 Oct review considered: none may lead a heading.
G18 = re.compile(r'<h[23][^>]*>\s*(Solar energy|Battery storage|Small wind|EV energy|Solar panels|'
                 r'Home batteries|Air-source|Ground-source|Electric cars|Electricity exports)\b')
BANNED = ("best", "cheapest", "top-rated", "recommended", "ranking", "%", "€", "&euro;", "per kWh",
          "Electric Ireland", "Bord G", "Energia", "SSE", "Flogas", "Pinergy")


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def h2s(t):
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"<h2[^>]*>(.*?)</h2>", t, re.S)]


def positions(t):
    return re.findall(r'<span class="pos-where">([^<]*)</span>', t)


def px(t):
    m = re.search(r'<script type="application/json" class="pn-px-config" id="px-data">.*?</script>', t, re.S)
    return m.group(0) if m else None


def pinned(base):
    """Read the reversed page back through the later governed layers."""
    return without_section_fact(without_facts(without_bridge(base)))


def guards(page):
    fails = []
    try:
        base = without_seo_a(page)
    except ValueError as e:
        return ["S1 " + str(e)]
    for old, new in edits():
        if page.count(new) != 1:
            fails.append("S1 governed string not present exactly once: " + new[:60])
        if base.count(old) != 1:
            fails.append("S1 base string not present exactly once: " + old[:60])
    if page.count(H1) != 1 or base.count(H1) != 1:
        fails.append("S2 the H1 changed")
    if page.count(SUBTITLE) != 1 or base.count(SUBTITLE) != 1:
        fails.append("S2 the flagship subtitle changed")
    if h2s(page) != h2s(base) or positions(page) != positions(base):
        fails.append("S3 the section order or the position sequence changed")
    for h in HEADINGS:
        if page.count("<h3>%s</h3>" % h) != 1:
            fails.append("S4 an editorial heading is not present exactly once, unlabelled: " + h[:40])
    if positions(page) != KICKERS:
        fails.append("S4 a position kicker changed")
    if G18.search(page):
        fails.append("S4 a category label leads a heading (G18)")
    try:
        if hashlib.sha256(pinned(base).encode("utf-8")).hexdigest() != BASE_SHA:
            fails.append("S5 outside the governed strings the page is not the approved base (18a9afd)")
    except ValueError as e:
        fails.append("S5 " + str(e))
    try:
        if with_seo_a(base) != page:
            fails.append("S5 the page differs from its base outside the governed strings")
    except ValueError as e:
        fails.append("S5 " + str(e))
    if SOCIAL.findall(page) != SOCIAL.findall(base):
        fails.append("S6 Open Graph or Twitter text changed")
    if px(page) is None or px(page) != px(base):
        fails.append("S7 the export explorer configuration changed")
    added = " ".join(new for _, new in edits())
    for w in BANNED:
        if w.lower() in added.lower():
            fails.append("S8 the change introduces %r" % w)
    return fails


def main(argv):
    mode = argv[1] if len(argv) > 1 else "--check"
    page = PAGE.read_text(encoding="utf-8")
    if mode == "--apply":
        if TITLE_NEW in page:
            die("already applied; run --check")
        try:
            new = with_seo_a(page)
        except ValueError as e:
            die(str(e))
        f = guards(new)
        if f:
            die("; ".join(f))
        PAGE.write_text(new, encoding="utf-8")
        print("DISC-026 SEO-A · APPLIED — %d governed edits · S1-S8 pass" % len(edits()))
        return
    if mode == "--check":
        f = guards(page)
        if f:
            print("CHECK FAILED\n  " + "\n  ".join(f))
            sys.exit(1)
        print("DISC-026 SEO-A · CHECK OK — S1-S8 pass · sha256 %s"
              % hashlib.sha256(page.encode("utf-8")).hexdigest()[:16])
        return
    if mode == "--prove":
        if guards(page):
            die("the page does not pass its own check; nothing to prove against")
        h_roof = "<h3>%s</h3>" % HEADINGS[0]
        h_wind = "<h3>%s</h3>" % HEADINGS[4]
        cases = [
            ("S1", lambda t: t.replace(TITLE_NEW, TITLE_NEW + TITLE_NEW, 1)),
            ("S2", lambda t: t.replace(H1, '<h1>Solar, Batteries &amp; Energy</h1>', 1)),
            ("S2", lambda t: t.replace(SUBTITLE, SUBTITLE.replace("use the heat it creates?", "save on your bills?"), 1)),
            ("S3", lambda t: t.replace("<h2>The energy anatomy of your property</h2>", "<h2>Solar and batteries</h2>", 1)),
            ("S4", lambda t: t.replace(h_roof, "<h3>Solar panels &mdash; " + HEADINGS[0] + "</h3>", 1)),
            ("S4", lambda t: t.replace(h_wind, "<h3>Small wind turbines &mdash; " + HEADINGS[4] + "</h3>", 1)),
            ("S4", lambda t: t.replace(KICKERS[4], "5 &middot; The open garden &middot; Wind turbines", 1)),
            ("S5", lambda t: t.replace("No\n          moving parts", "No moving parts at all", 1)),
            ("S6", lambda t: t.replace('<meta property="og:title" content="The House as a Power Station', '<meta property="og:title" content="Solar Panels Ireland', 1)),
            ("S7", lambda t: t.replace('"label":"Electricity suppliers"', '"label":"Best electricity suppliers"', 1)),
        ]
        ok = 0
        for code, mut in cases:
            t2 = mut(page)
            if t2 == page:
                print("  NOT APPLIED %s" % code); continue
            f = guards(t2)
            hit = any(x.startswith(code) for x in f) or (code not in ("S1", "S4") and any(x.startswith("S5") for x in f))
            ok += hit
            print("  %s %s -> %s" % ("CAUGHT" if hit else "MISSED", code, " | ".join(f)[:120] if f else "no failure"))
        print("%d/%d guards caught their break%s" % (ok, len(cases), " — PROVEN" if ok == len(cases) else ""))
        sys.exit(0 if ok == len(cases) else 1)
    die("usage: --apply | --check | --prove")


if __name__ == "__main__":
    main(sys.argv)
