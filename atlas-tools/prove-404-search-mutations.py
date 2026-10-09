#!/usr/bin/env python3
"""
MUTATION CAPABILITY PROOF · build-404-search.py
===============================================================================
Same discipline as prove-journey-exit-mutations.py: one deliberate mutation per
case against a throwaway copy, and the builder must REFUSE with the expected
guard identifier.  Blind, vacuous and misattributed results all fail.

F0 (the expected-baseline-hash pre-flight) fires on any input change and would
mask every inner guard, so for [input] cases it is disabled IN THE TEST COPY
ONLY — except in the one case where F0 is itself the guard under test.

    python3 prove-404-search-mutations.py
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
BUILDER = SRC / "build-404-search.py"
NEEDED = ["404.html", "index.html", "sitemap.xml", "search.css", "search.js"]

F0_BLOCK = "if sha(base)[:12] != EXPECTED_BEFORE:"
F0_OFF = "if False:"
SPLICE = 'out = base[:m.end()] + "\\n" + REGION + base[m.end():]'


def mk(tmp):
    (tmp / "atlas-tools").mkdir(parents=True, exist_ok=True)
    for f in NEEDED:
        shutil.copy2(ROOT / f, tmp / f)
    # the other rail-carrying pages, so F3's comparison set is real
    for p in ROOT.glob("*.html"):
        if p.name not in NEEDED and "SEARCH RAIL v1" in \
                p.read_text(encoding="utf-8"):
            shutil.copy2(p, tmp / p.name)
    shutil.copy2(BUILDER, tmp / "atlas-tools" / "build-404-search.py")
    return tmp / "atlas-tools" / "build-404-search.py"


def run(b):
    r = subprocess.run([sys.executable, str(b), "--check"],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def patch(p, old, new):
    t = p.read_text(encoding="utf-8")
    if old not in t:
        return False
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    return True


def after_splice(b, stmt):
    return patch(b, SPLICE, SPLICE + "\n" + stmt)


# ------------------------------------------------------------------ the cases
def m_f0(b, t):
    p = t / "404.html"
    p.write_text(p.read_text(encoding="utf-8")
                 .replace("</body>", "<!-- x -->\n</body>", 1), encoding="utf-8")
    return True

def m_f1(b, t):
    p = t / "404.html"
    s = p.read_text(encoding="utf-8")
    i = s.index('class="brand-mark"')
    j = s.index("</a>", i) + 4
    a = s[s.rfind("<a", 0, i):j]
    p.write_text(s[:j] + a + s[j:], encoding="utf-8")   # two mark anchors
    return True

def m_f2(b, t):
    # point the donor at a page that does not carry the rail
    (t / "donorless.html").write_text("<html></html>", encoding="utf-8")
    return patch(b, 'DONOR = "index.html"', 'DONOR = "donorless.html"')

def m_f2b(b, t):
    (t / "search.js").unlink()
    return True

def m_f3(b, t):
    # author a near-copy instead of copying: the region drifts
    return after_splice(b, 'out = out.replace("Search PlotNua", '
                           '"Search the site")')

def m_f4(b, t):
    return after_splice(b, 'out = out.replace("<body>", "<body >", 1)')

def m_f5(b, t):
    # redesign the 404's copy — exactly what this job must not do
    return after_splice(b, 'out = out.replace("Page Not Found", '
                           '"Nothing Here", 1)')

def m_f6(b, t):
    # drop a pre-existing recovery route
    return after_splice(b, 'out = out.replace('
                           '\'href="your-plot.html"\', \'href="#"\', 1)')

def m_f7(b, t):
    p = t / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("</urlset>",
                           "<url><loc>https://plotnua.ie/404.html</loc></url>"
                           "</urlset>", 1), encoding="utf-8")
    return True

def m_f8(b, t):
    return after_splice(b, 'out = out.replace("noindex", "index", 1)')

def m_f9(b, t):
    return patch(b, SPLICE,
                 'out = base[:m.end()] + "\\n" + REGION + "\\n" + REGION '
                 '+ base[m.end():]')

def m_f10(b, t):
    return patch(b, 'if \'href="search.html"\' not in REGION:',
                 'REGION = REGION.replace(\'href="search.html"\', \'href="#"\')\n'
                 'if \'href="search.html"\' not in REGION:')


CASES = [
    ("page differs from its frozen baseline",  "input",   "F0",  m_f0),
    ("a second .brand-mark anchor",            "input",   "F1",  m_f1),
    ("donor page carries no rail",             "builder", "F2",  m_f2),
    ("a shared Search asset is missing",       "input",   "F2b", m_f2b),
    ("region authored instead of copied",      "builder", "F3",  m_f3),
    ("a byte changed outside the splice",      "builder", "F4",  m_f4),
    ("the 404's own copy redesigned",          "builder", "F5",  m_f5),
    ("an existing recovery route neutered",    "builder", "F6",  m_f6),
    ("the 404 added to sitemap.xml",           "input",   "F7",  m_f7),
    ("noindex flipped to index",               "builder", "F8",  m_f8),
    ("region injected twice",                  "builder", "F9",  m_f9),
    ("search.html href replaced with #",       "builder", "F10", m_f10),
]
NO_BYPASS = {"F0"}

print("\n  MUTATION CAPABILITY PROOF · build-404-search.py")
print("  %d cases\n" % len(CASES))

with tempfile.TemporaryDirectory() as d:
    b = mk(pathlib.Path(d))
    rc, out = run(b)
    if rc != 0:
        print(out)
        sys.exit("CONTROL FAILED: the unmutated builder does not pass.")
print("  control  unmutated builder passes all guards  OK\n")

caught = blind = vacuous = wrong = 0
for name, kind, guard, fn in CASES:
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        b = mk(tmp)
        if kind == "input" and guard not in NO_BYPASS:
            assert patch(b, F0_BLOCK, F0_OFF), "could not disable F0"
        snap = b.read_text(encoding="utf-8") + \
            "".join(p.read_text(encoding="utf-8", errors="replace")
                    for p in sorted(tmp.glob("*.*")))
        if not fn(b, tmp):
            print("  %-40s VACUOUS  mutation did not apply" % name)
            vacuous += 1
            continue
        snap2 = b.read_text(encoding="utf-8") + \
            "".join(p.read_text(encoding="utf-8", errors="replace")
                    for p in sorted(tmp.glob("*.*")))
        if snap == snap2:
            print("  %-40s VACUOUS  nothing changed" % name)
            vacuous += 1
            continue
        rc, out = run(b)
        if rc == 0:
            print("  %-40s BLIND    expected %s, builder passed" % (name, guard))
            blind += 1
            continue
        m = re.search(r"REFUSED: (F\d+[a-z]?)", out)
        got = m.group(1) if m else "(none)"
        if got != guard:
            print("  %-40s WRONG    expected %s, got %s" % (name, guard, got))
            wrong += 1
            continue
        tag = "" if kind == "builder" else \
            "   [input · F0 bypassed]" if guard not in NO_BYPASS else "   [input]"
        print("  %-40s caught by %-4s%s" % (name, got, tag))
        caught += 1

print("\n  %d caught · %d blind · %d vacuous · %d wrong guard"
      % (caught, blind, vacuous, wrong))
if blind or vacuous or wrong:
    sys.exit("\n  FAILED.\n")
print("  every guard demonstrated capable of failing.\n")
