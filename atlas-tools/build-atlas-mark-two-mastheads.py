#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PlotNua — build-atlas-mark-two-mastheads.py

TWO GUARDS CARRY STALE ARITHMETIC, NOT A FINDING.

prove-atlas-a.mjs and prove-atlas-transparency.mjs each assert that
your-plot.html references the approved static Atlas mark EXACTLY ONCE.
That was true while the Garden Room Atlas Assessment was the only
masthead on the page. The Additional Home Atlas Assessment now carries
the second, on the founder's instruction to use the exact existing
Garden Room branding rather than a second Atlas template. Measured: both
occurrences are byte-identical constructions — the same asset, the same
.pn-atlas-still span, the same 60x60, the same empty alt and aria-hidden,
the same hydration call.

So the page is right and the count is stale. The correction does NOT
weaken either guard. Each one now asserts:
  (a) the count is exactly 2 — a third reference still fails; and
  (b) EVERY occurrence sits inside the approved lockup — the span, the
      60x60 box, the empty alt and aria-hidden. A reference that escapes
      the lockup fails, which the old `=== 1` could not catch at all.

TEST FILES ONLY. your-plot.html is not opened for writing and its hash
is asserted unchanged. The builder refuses if either guard's count
assertion is softened to an inequality, or if the lockup assertion is
absent from the result.

Usage: python3 atlas-tools/build-atlas-mark-two-mastheads.py [--check|--revert]
"""

import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "your-plot.html")
PAGE_SHA = "ea09ddfb18eda37d"

A = os.path.join(ROOT, "atlas-tools", "prove-atlas-a.mjs")
T = os.path.join(ROOT, "atlas-tools", "prove-atlas-transparency.mjs")

# ---- the shared lockup assertion, injected into both guards ------------
LOCKUP = """
/* EVERY OCCURRENCE IS THE APPROVED LOCKUP, NOT JUST THE RIGHT COUNT.
   The old `exactly once` test could not see HOW the mark was placed. This
   one does: each reference must sit in the .pn-atlas-still span, at the
   approved 60x60, with the empty alt and aria-hidden that keep it out of
   the accessibility tree. A reference that escapes the lockup fails here
   even though the count is right. */
function pnMarkLockups(pageSrc, asset){
  const parts = pageSrc.split(asset);
  const escaped = [];
  for (let i = 1; i < parts.length; i++) {
    const before = parts[i - 1].slice(-600);
    const after = parts[i].slice(0, 400);
    const win = before + asset + after;
    const need = ["aaEl('span', 'pn-atlas-still')",
                  "mastImg.width = 60; mastImg.height = 60;",
                  "mastImg.alt = ''",
                  "aria-hidden"];
    const missing = need.filter(function(n){ return win.indexOf(n) === -1; });
    if (missing.length) escaped.push('occurrence ' + i + ' lacks ' + missing.join(', '));
  }
  return escaped;
}
"""

A_FIND = """    const IMG = 'assets/brand/atlas-final-static-approved-transparent.png';
    (src.split(IMG).length - 1) === 1
      ? ok('the approved static mark is referenced exactly once')
      : bad('the approved static mark reference count is wrong');
"""

A_REPL = """    const IMG = 'assets/brand/atlas-final-static-approved-transparent.png';
    /* TWO MASTHEADS, ONE MARK. The Garden Room Atlas Assessment and the
       Additional Home Atlas Assessment both carry it, on the founder's
       instruction to reuse the exact existing branding rather than clone
       a second Atlas template. Measured: the two constructions are
       byte-identical. A THIRD reference still fails here. */
    const pnMarks = src.split(IMG).length - 1;
    pnMarks === 2
      ? ok('the approved static mark is referenced exactly twice — the two Atlas Assessment mastheads')
      : bad('the approved static mark reference count is wrong',
            'expected 2 (Garden Room + Additional Home), found ' + pnMarks);
    {
      const escaped = pnMarkLockups(src, IMG);
      escaped.length === 0
        ? ok('every occurrence sits in the approved .pn-atlas-still lockup at 60x60, alt empty, aria-hidden')
        : bad('a reference to the approved mark escapes the approved lockup',
              escaped.join(' | '));
    }
"""

T_FIND = """const src = fs.readFileSync(path.join(ROOT, 'your-plot.html'), 'utf8');
(src.split(SHIPPED).length - 1) === 1
  ? ok('your-plot.html references the transparent asset exactly once')
  : bad('the page does not reference the transparent asset exactly once');
"""

T_REPL = """const src = fs.readFileSync(path.join(ROOT, 'your-plot.html'), 'utf8');
/* TWO MASTHEADS CARRY IT — Garden Room and Additional Home — and both are
   the same approved transparent asset in the same approved lockup. */
const pnShipped = src.split(SHIPPED).length - 1;
pnShipped === 2
  ? ok('your-plot.html references the transparent asset exactly twice — the two Atlas Assessment mastheads')
  : bad('the page does not reference the transparent asset exactly twice',
        'found ' + pnShipped);
{
  const escaped = pnMarkLockups(src, SHIPPED);
  escaped.length === 0
    ? ok('both occurrences sit in the approved .pn-atlas-still lockup at 60x60')
    : bad('a reference to the transparent asset escapes the approved lockup',
          escaped.join(' | '));
}
"""


def sha16(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


def place_lockup(txt):
    """Insert the helper once, after the final import line."""
    if "function pnMarkLockups(" in txt:
        return txt
    last = 0
    for m in re.finditer(r"^import .*$", txt, re.M):
        last = m.end()
    if not last:
        raise SystemExit("REFUSED: no import line to anchor the helper to")
    return txt[:last] + "\n" + LOCKUP + txt[last:]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"

    if mode == "--revert":
        n = 0
        for f in (A, T):
            b = f + ".bak-twomast"
            if os.path.exists(b):
                open(f, "w", encoding="utf-8").write(open(b, encoding="utf-8").read())
                n += 1
        print("reverted %d file(s)." % n); return

    page = open(PAGE, encoding="utf-8").read()
    if sha16(page) != PAGE_SHA:
        raise SystemExit("REFUSED: your-plot.html is %s, expected %s"
                         % (sha16(page), PAGE_SHA))

    results = {}
    for f, find, repl in ((A, A_FIND, A_REPL), (T, T_FIND, T_REPL)):
        txt = open(f, encoding="utf-8").read()
        if txt.count(find) != 1:
            raise SystemExit("REFUSED: %s anchor matched %d"
                             % (os.path.basename(f), txt.count(find)))
        out = place_lockup(txt.replace(find, repl, 1))

        # G1 — the count assertion must stay an equality against a literal.
        for lit in ("=== 2",):
            if lit not in repl:
                raise SystemExit("REFUSED: the count assertion in %s is not a "
                                 "strict equality" % os.path.basename(f))
        if re.search(r"(>=|<=|>|<)\s*2\b", repl):
            raise SystemExit("REFUSED: the count assertion in %s was softened "
                             "to an inequality" % os.path.basename(f))

        # G2 — the lockup assertion must be present and reachable.
        if "pnMarkLockups(" not in out or "function pnMarkLockups(" not in out:
            raise SystemExit("REFUSED: %s does not both define and call the "
                             "lockup assertion" % os.path.basename(f))

        # G3 — nothing else in the guard moved.
        if txt.replace(find, "") != out.replace(repl, "").replace("\n" + LOCKUP, ""):
            raise SystemExit("REFUSED: something other than the count "
                             "assertion changed in %s" % os.path.basename(f))

        # G4 — it still parses, before anything is written.
        tmp = os.path.join(ROOT, ".pn-tm-%s" % os.path.basename(f))
        open(tmp, "w", encoding="utf-8").write(out)
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            raise SystemExit("REFUSED: %s does not parse, nothing written:\n%s"
                             % (os.path.basename(f), r.stderr[:400]))
        results[f] = (txt, out)

    # G5 — the shipped page is not touched by this builder at all.
    if sha16(open(PAGE, encoding="utf-8").read()) != PAGE_SHA:
        raise SystemExit("REFUSED: your-plot.html changed during the build")

    if mode == "--check":
        for f, (t, o) in results.items():
            print("CHECK ONLY. %-28s %s -> %s, %+d lines"
                  % (os.path.basename(f), sha16(t), sha16(o),
                     o.count("\n") - t.count("\n")))
        print("5 guards pass. your-plot.html untouched (%s)." % PAGE_SHA)
        return

    for f, (t, o) in results.items():
        b = f + ".bak-twomast"
        if not os.path.exists(b):
            open(b, "w", encoding="utf-8").write(t)
        open(f, "w", encoding="utf-8").write(o)
        print("applied. %-28s %s -> %s" % (os.path.basename(f), sha16(t), sha16(o)))
    print("your-plot.html untouched (%s)." % PAGE_SHA)


if __name__ == "__main__":
    main()
