#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOB 4 · DOCUMENT STRUCTURE — LANDMARKS AND SEMANTICS
===============================================================================
STRUCTURE ONLY. Not one visible pixel, not one word of homeowner copy, not one
colour, size, space or transition. Every edit here is a tag name, an ARIA
attribute, or a wrapper element that renders as a plain block.

WHY THIS BUILDER EXISTS RATHER THAN A TEMPLATE EDIT. Job 4 began by looking for
the governed source of truth, because hand-patching 14 propagated pages is how
a defect comes back. There isn't one. Every historical Discovery builder is a
spent one-shot that REFUSES on its own anchors against today's pages:

    build-disc026-discovery-rebuild.py   REFUSED: anchor 'meta description'
    build-disc026-correction-01.py       REFUSED: anchor 'Read those figures...'
    build-disc026-correction-02.py       REFUSED: anchor 'drawer summary'
    build-disc026-editorial-pass.py      REFUSED: anchor 'S9 governance language'
    build-disc026-residential-compute.py REFUSED: anchor 'S3 heata tile note'

and the shared footer is not generated at all -- it is one 1727-byte block
duplicated byte-identically across 18 pages. So the pages ARE the source of
truth, and this builder is the governed instrument that edits them. The guard
suite (prove-landmarks.mjs) is what stops a future rebuild reintroducing the
defect silently: it turns a regression into a red tick.

WHAT IT FIXES, and nothing else:

  A1  index.html, your-plot.html, 404.html have no <main> at all. Content sits
      in sections directly under <body>, so a screen reader has nothing to jump
      to and a skip link has no target.

  A2  Eleven of the thirteen public Discoveries carry TWO TO SIX sibling <main>
      elements. The template closes </main> and reopens <main class="article">
      around each full-bleed section so the image can escape the article
      column. The visual device is good; the landmark cost is not. The fix
      keeps the DOM shape -- the full-bleed sections stay exactly where they
      are, as siblings of the article blocks -- and only renames the repeated
      <main class="article"> to <div class="article"> inside ONE outer <main>.
      main and div are both display:block and every rule is keyed on the class,
      so the rendered box tree is unchanged. That claim is not asserted, it is
      measured: shots.py captures all 25 surfaces at 1440 and 390 before and
      after and the comparison must be pixel-identical.

  H   .d-dots declares role="tablist" while its children are plain buttons --
      no role="tab", no aria-selected. AT announces a tab list containing no
      tabs. It becomes role="group", which is what it actually is: a labelled
      set of related controls. The carousel itself is untouched; there is no
      CSS or JS anywhere keyed on role="tablist" (verified: the string appears
      exactly once per page, in the markup).

  I   The shared footer jumps H2 -> H4. The four column headings become <h2>,
      which is the correct level for headings inside a <footer> landmark, and
      the ONE selector that styles them moves with them.

  J   The footer's link columns have no navigation landmark. The <div
      class="footer-cols"> becomes <nav class="footer-cols" aria-label="Footer">
      -- a tag swap with no CSS consequence, because every footer rule is keyed
      on the class, never the tag.

  SKIP LINK, permitted only as a consequence of A1 establishing a reliable
      target. One <a class="pn-skip" href="#pn-main"> as the first body child,
      visually hidden until focused.

NOT IN SCOPE AND NOT TOUCHED. Search V1 in any form, the Search aria-modal
focus-containment finding, colour, type, spacing, motion, dot sizing, contrast,
prefers-reduced-motion, the My Plot pulse, Discovery JS/opacity resilience,
homeowner copy, DISC-025's frozen <main>, Garden Register switches.

DISC-025. disc025-borrowed-garden-check.html is NOT in any target list. Its
frozen <main> must hash 05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29
and guard S0 asserts exactly that before anything is written.

    python3 atlas-tools/build-landmarks.py            apply
    python3 atlas-tools/build-landmarks.py --check    verify, write nothing
    python3 atlas-tools/build-landmarks.py --revert   undo
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

MARK = "PLOTNUA LANDMARKS v1"

DISC025 = "disc025-borrowed-garden-check.html"
DISC025_MAIN_SHA = "05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29"

# The thirteen public Discoveries, from sitemap.xml scope.
DISCOVERIES = [
    "discovery-living-in-the-garden.html", "discovery-a-home-for-art.html",
    "discovery-open-your-home-to-art.html", "discovery-the-borrowed-garden.html",
    "discovery-house-as-power-station.html", "discovery-neighbourhood-parcel-house.html",
    "discovery-hidden-cars.html", "discovery-hidden-bins.html",
    "discovery-garden-retreat.html", "discovery-above-and-beyond.html",
    "discovery-your-home-on-screen.html", "discovery-driveway-income.html",
    "discovery-home-exchange.html",
]

# Every page carrying the shared footer (NOT the ten Job 1 journey-exit footers).
FOOTER_PAGES = [
    "index.html", "404.html", "about.html", "contact.html", "privacy.html",
    "terms.html", "cookie-policy.html",
] + DISCOVERIES

TABLIST_PAGES = ["index.html", "404.html"]

# A1 · the three main-less pages, each with the exact span that becomes <main>.
# start  = the opening tag of the first content element
# end    = the first element AFTER the last content element (exclusive bound)
MAIN_WRAP = {
    "index.html":     ('<section class="hero" id="hero">',
                       '<div id="discover-your-property" aria-hidden="true"></div>'),
    "404.html":       ('<section class="scene scene-hero">', '<footer>'),
    "your-plot.html": ('<h1 class="pn-page-title">Your Plot</h1>',
                       '<div class="pn-fallback-note" id="fallbackNote"></div>'),
}

SKIP_HTML = (
    '<a class="pn-skip" href="#pn-main">Skip to main content</a>'
)
SKIP_CSS = (
    "\n/* " + MARK + " -- skip link. Off-screen until it takes keyboard focus;\n"
    "   it is the one affordance a reliable single main landmark makes\n"
    "   possible. No other rule on the page is touched. */\n"
    ".pn-skip{position:absolute;left:-9999px;top:0;width:1px;height:1px;"
    "overflow:hidden;z-index:9999;}\n"
    ".pn-skip:focus{left:8px;top:8px;width:auto;height:auto;padding:10px 14px;"
    "background:#1F3B2E;color:#F2EFE6;font:500 14px/1.2 sans-serif;"
    "border-radius:4px;text-decoration:none;outline:2px solid #8FAF8A;"
    "outline-offset:2px;}\n"
)


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read(f):
    return (ROOT / f).read_text(encoding="utf-8")


def main_hash(text):
    i = text.find("<main")
    j = text.rfind("</main>")
    if i < 0 or j < 0:
        return None
    return sha(text[i:j + 7])


# ---------------------------------------------------------------- transforms
def t_discovery_main(t, f):
    """A2 · collapse N sibling <main class="article"> into ONE <main>."""
    opens = re.findall(r'<main[^>]*>', t)
    if len(opens) == 1:
        # Already compliant (driveway-income, home-exchange). Restructuring a
        # page that is already correct would be change for its own sake, so it
        # gets the one attribute the skip link needs and nothing else.
        if 'id="pn-main"' in t:
            return t, "already one main, already targetable"
        if 'id=' in opens[0]:
            die("%s: its single <main> already carries an id: %s" % (f, opens[0]))
        return t.replace(opens[0], opens[0][:-1] + ' id="pn-main">', 1), \
            "already one main; skip target added"
    if len(opens) == 0:
        die("%s: a Discovery with no <main> at all" % f)
    if set(opens) != {'<main class="article">'}:
        die("%s has unexpected <main> variants %s" % (f, sorted(set(opens))))
    i = t.find('<main class="article">')
    j = t.rfind("</main>")
    span = t[i:j + 7]
    if "<main" in span.replace('<main class="article">', ""):
        die("%s: an unexpected <main> hides inside the span" % f)
    inner = span.replace('<main class="article">', '<div class="article">')
    inner = inner.replace("</main>", "</div>")
    if "<main" in inner or "</main>" in inner:
        die("%s: a main tag survived the demotion" % f)
    out = t[:i] + '<main id="pn-main">\n' + inner + "\n</main>" + t[j + 7:]
    return out, "%d mains -> 1" % len(opens)


def t_wrap_main(t, f):
    """A1 · wrap the content span of a main-less page in <main id="pn-main">."""
    if "<main" in t:
        return t, "already has a main"
    start, end = MAIN_WRAP[f]
    if t.count(start) != 1:
        die("%s: start anchor %r matched %d times" % (f, start[:46], t.count(start)))
    if t.count(end) != 1:
        die("%s: end anchor %r matched %d times" % (f, end[:46], t.count(end)))
    i = t.index(start)
    j = t.index(end)
    if j <= i:
        die("%s: end anchor precedes start anchor" % f)
    out = t[:i] + '<main id="pn-main">\n' + t[i:j] + '</main>\n\n' + t[j:]
    return out, "wrapped %d bytes" % (j - i)


def t_skip(t, f):
    """Skip link as the first body child, plus its own scoped CSS."""
    if SKIP_HTML in t:
        return t, "skip link already present"
    # The REAL <body> tag, not a mention of one. your-plot.html carries a CSS
    # comment -- inside <style>, not an HTML comment -- reading "script sets at
    # the top of <body>", and a naive regex spliced the skip link into the
    # middle of it, where it was inert. The runtime acceptance pass caught it;
    # masking HTML comments alone did not, because this one is CSS. Comments,
    # <style> and <script> are all blanked length-preservingly (so offsets stay
    # valid) before the search.
    blank = lambda m0: " " * len(m0.group(0))
    masked = re.sub(r"<!--.*?-->", blank, t, flags=re.S)
    masked = re.sub(r"<style[^>]*>.*?</style>", blank, masked, flags=re.S | re.I)
    masked = re.sub(r"<script[^>]*>.*?</script>", blank, masked, flags=re.S | re.I)
    m = re.search(r'<body[^>]*>', masked)
    if not m:
        die("%s: no <body> tag outside a comment" % f)
    out = t[:m.end()] + "\n" + SKIP_HTML + t[m.end():]
    k = out.rfind("</style>")
    if k < 0:
        die("%s: no </style> to attach the skip-link rule to" % f)
    out = out[:k] + SKIP_CSS + out[k:]
    return out, "skip link + css"


def t_tablist(t, f):
    """H · role="tablist" over non-tab children becomes role="group"."""
    old = '<div class="d-dots" role="tablist" aria-label="Discovery Library position">'
    new = '<div class="d-dots" role="group" aria-label="Discovery Library position">'
    if new in t and old not in t:
        return t, "already group"
    if t.count(old) != 1:
        die("%s: tablist anchor matched %d times" % (f, t.count(old)))
    if re.search(r'role="tab"', t):
        die("%s: a real role=tab exists; this is not the false-tablist case" % f)
    return t.replace(old, new), "tablist -> group"


def t_footer(t, f):
    """I + J · heading level and the navigation landmark, in one shared block."""
    changed = []
    if '<div class="footer-cols">' in t:
        if t.count('<div class="footer-cols">') != 1:
            die("%s: footer-cols matched %d times" % (f, t.count('<div class="footer-cols">')))
        t = t.replace('<div class="footer-cols">',
                      '<nav class="footer-cols" aria-label="Footer">')
        # close the matching </div>: it is the one immediately before footer-base
        anchor = '\n\n    <div class="footer-base">'
        if t.count(anchor) != 1:
            die("%s: footer-base anchor matched %d times" % (f, t.count(anchor)))
        k = t.index(anchor)
        back = t.rfind("</div>", 0, k)
        if back < 0:
            die("%s: no </div> closing footer-cols" % f)
        t = t[:back] + "</nav>" + t[back + 6:]
        changed.append("nav landmark")
    n_h4 = len(re.findall(r'<h4>(Navigation|Company|Social|Contact)</h4>', t))
    if n_h4:
        if n_h4 != 4:
            die("%s: expected 4 footer h4 headings, found %d" % (f, n_h4))
        t = re.sub(r'<h4>(Navigation|Company|Social|Contact)</h4>',
                   r'<h2>\1</h2>', t)
        if ".footer-col h4{" not in t:
            die("%s: the .footer-col h4 rule is missing" % f)
        t = t.replace(".footer-col h4{", ".footer-col h2{")
        changed.append("h4 -> h2")
    return t, " + ".join(changed) if changed else "no footer change"


# ------------------------------------------------------------------- plan
def plan():
    jobs = []
    for f in DISCOVERIES:
        jobs.append((f, t_discovery_main))
    for f in MAIN_WRAP:
        jobs.append((f, t_wrap_main))
    for f in TABLIST_PAGES:
        jobs.append((f, t_tablist))
    for f in FOOTER_PAGES:
        jobs.append((f, t_footer))
    # the skip link only goes where a reliable #pn-main now exists
    for f in sorted(set(DISCOVERIES) | set(MAIN_WRAP)):
        jobs.append((f, t_skip))
    byfile = {}
    for f, fn in jobs:
        byfile.setdefault(f, []).append(fn)
    return byfile


def build(write=True):
    # ---- S0 · DISC-025 is frozen and is not a target -------------------
    d25 = read(DISC025)
    if main_hash(d25) != DISC025_MAIN_SHA:
        die("S0 DISC-025 frozen <main> hash is %s, expected %s"
            % (main_hash(d25), DISC025_MAIN_SHA))
    if DISC025 in plan():
        die("S0 DISC-025 appears in the target plan; it must never be a target")

    results = []
    for f, fns in plan().items():
        p = ROOT / f
        if not p.exists():
            die("target %s does not exist" % f)
        base = p.read_text(encoding="utf-8")
        out = base
        notes = []
        for fn in fns:
            out, note = fn(out, f)
            notes.append(note)
        results.append({"file": f, "base": base, "out": out, "notes": notes,
                        "delta": len(out) - len(base)})

    # ---- GUARDS, specific before general -------------------------------
    for r in results:
        f, out, base = r["file"], r["out"], r["base"]

        # S1 · exactly one <main> on every touched page
        n = len(re.findall(r'<main[^>]*>', out))
        if n != 1:
            die("S1 %s ends with %d <main> elements; exactly one is required" % (f, n))
        if out.count("</main>") != 1:
            die("S1 %s has %d </main>; exactly one is required"
                % (f, out.count("</main>")))

        # S2 · wherever this job put a skip link, it must reach a real target,
        #      and exactly one. The five footer-only pages (about, contact,
        #      privacy, terms, cookie-policy) already had a single sound <main>
        #      before Job 4 and get no skip link, because the founder scoped it
        #      to "a direct consequence of establishing a reliable single main
        #      landmark" -- theirs was not established here.
        has_skip = 'class="pn-skip"' in out
        if has_skip and out.count('id="pn-main"') != 1:
            die("S2 %s carries a skip link but %d pn-main targets; exactly one "
                "is required" % (f, out.count('id="pn-main"')))
        if not has_skip and 'id="pn-main"' in out:
            die("S2 %s has a skip target but no skip link" % f)

        # S3 · the AUTHORISED false tablist is gone. Scoped deliberately to
        #      .d-dots, which is what Job 3 measured and Job 4 authorised.
        #      A SECOND instance of the identical defect exists on
        #      your-plot.html -- <div class="season-tabs" role="tablist"> whose
        #      three children are plain buttons with no role="tab" and no
        #      aria-selected. It is NOT in this job's scope, so it is reported
        #      to the founder rather than quietly fixed, and S3b below asserts
        #      this builder left it exactly as it found it.
        if re.search(r'<div class="d-dots"[^>]*role="tablist"', out):
            die("S3 %s still declares role=\"tablist\" on the carousel dots" % f)

        # S3b · and nothing outside that authorisation moved. The expected
        #      delta is one ONLY where the carousel-dot tablist was still in
        #      the base; on a re-run it has already gone and the delta is zero.
        expect = 1 if re.search(r'<div class="d-dots"[^>]*role="tablist"', base) else 0
        if base.count('role="tablist"') - out.count('role="tablist"') != expect:
            die("S3b %s changed a role=\"tablist\" outside the authorised "
                "carousel-dot scope" % f)

        # S4 · the footer heading jump is gone wherever the footer exists
        if "<h4>Navigation</h4>" in out:
            die("S4 %s still heads its footer columns at h4" % f)

        # S5 · the footer nav landmark exists wherever the shared footer does
        if '<div class="footer-cols">' in out:
            die("S5 %s still has an unlandmarked footer-cols" % f)

        # S6 · tag/attribute work only: homeowner copy must not move. Text is
        #      compared with ALL tags stripped, so a wrapper is invisible to it
        #      and a copy edit is not. The ONE authorised new string is the
        #      skip link, which is removed from the comparison by its exact
        #      literal -- so a changed or extra word anywhere still refuses.
        #      <style> and <script> bodies are removed first: their contents are
        #      never homeowner copy, and leaving them in made this guard refuse
        #      over a CSS selector rename, which is not what it is for.
        def strip(s):
            s = re.sub(r"<style[^>]*>.*?</style>", " ", s, flags=re.S | re.I)
            s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.S | re.I)
            s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
        #      The removal is SYMMETRIC -- base and out are both stripped of the
        #      skip link -- so that a re-run, where the link is already in the
        #      base, compares like with like. Without that, this guard refused
        #      on the second run and the builder was not idempotent.
        cmp_out = out.replace(SKIP_HTML, "", 1) if SKIP_HTML in out else out
        cmp_base = base.replace(SKIP_HTML, "", 1) if SKIP_HTML in base else base
        if SKIP_HTML in cmp_out:
            die("S6 %s carries more than one skip link" % f)
        if strip(cmp_base) != strip(cmp_out):
            die("S6 %s: visible text changed. This job may not touch copy." % f)

        # S7 · element balance. Every rename this builder performs swaps one
        #      opening tag for exactly one opening tag, so the ONLY elements it
        #      may add are the skip-link anchor and the one <main> wrapper. The
        #      count regex matches opening tags only, which is why a closing
        #      </main> -> </div> rename contributes nothing here.
        count = lambda s: len(re.findall(r'<[a-zA-Z][^>]*>', s))
        added = 0
        if 'class="pn-skip"' in out and 'class="pn-skip"' not in base:
            added += 1
        if '<main id="pn-main">' in out and '<main id="pn-main">' not in base:
            added += 1
        if count(out) - count(base) != added:
            die("S7 %s: element count moved by %+d, expected exactly %+d "
                "(the skip link and the main wrapper are the only additions "
                "this job may make)" % (f, count(out) - count(base), added))

        # S8 · no duplicate ids INTRODUCED. Two corrections the first version
        #      of this guard needed: HTML comments are stripped first (a
        #      comment on your-plot.html quotes <ul id="evidAsks"> while
        #      describing it, which is prose, not a second element), and the
        #      result is compared against the base rather than asserted
        #      absolutely -- this job may not ADD a duplicate, but it is not
        #      licensed to go fixing pre-existing ones either.
        nocomments = lambda s: re.sub(r"<!--.*?-->", " ", s, flags=re.S)
        dups = lambda s: (lambda ids: sorted({i for i in ids if ids.count(i) > 1}))(
            re.findall(r'\sid="([^"]+)"', nocomments(s)))
        new_dups = sorted(set(dups(out)) - set(dups(base)))
        if new_dups:
            die("S8 %s introduces duplicate ids %s" % (f, new_dups))

        # S9 · Search V1 markup on the page is byte-identical
        for frag in ['<a class="pns-pill"', 'id="pnsInput"', 'id="pnsPanel"',
                     'src="search.js"']:
            if base.count(frag) != out.count(frag):
                die("S9 %s changed Search V1 markup (%s)" % (f, frag))

        # S10 · Job 1 journey exits untouched
        if base.count("PLOTNUA JOURNEY EXIT v1") != out.count("PLOTNUA JOURNEY EXIT v1"):
            die("S10 %s changed the Job 1 journey exit region" % f)

    # ---- S11 · DISC-025 still frozen AFTER the plan ran ----------------
    if read(DISC025) != d25:
        die("S11 DISC-025 changed during the build")

    if not write:
        print("\n  --check: %d files would change, nothing written.\n" % len(results))
        for r in results:
            print("    %-44s %+6d  %s" % (r["file"], r["delta"], "; ".join(r["notes"])))
        print("\n  11 guard families passed.\n")
        return results

    for r in results:
        (ROOT / r["file"]).write_text(r["out"], encoding="utf-8")
    print("\n  wrote %d files.\n" % len(results))
    for r in results:
        print("    %-44s %+6d  %s" % (r["file"], r["delta"], "; ".join(r["notes"])))
    print("\n  11 guard families passed.\n")
    return results


def revert():
    import subprocess
    files = sorted(plan())
    subprocess.run(["git", "checkout", "--"] + files, cwd=str(ROOT), check=True)
    print("reverted %d files" % len(files))


if __name__ == "__main__":
    if "--revert" in sys.argv:
        revert()
    else:
        build(write="--check" not in sys.argv)
