#!/usr/bin/env python3
"""
MUTATION CAPABILITY PROOF · build-journey-exit.py
===============================================================================
A guard that has never been seen to fail is not a guard.  "It passed during
development" proves nothing.  This harness builds a throwaway copy of the ten
Property Checks and the builder, applies ONE deliberate mutation per case, and
requires the builder to REFUSE with the expected guard identifier.

TWO KINDS OF MUTATION, labelled, because they prove different things:

  [builder]  the builder itself is mutated — it is made to emit a bad region,
             splice in the wrong place, or drop a destination.  This proves the
             guard catches a defective builder.

  [input]    a Property Check page is mutated.  E0e (the expected-baseline-hash
             pre-flight) fires on ANY input change and would mask every inner
             guard, so for input cases E0e is DISABLED IN THE TEST COPY ONLY and
             the case says so.  Without that bypass these cases would all
             "pass" at E0e and prove nothing — that exact mistake was made
             earlier in this project and is not repeated.

VACUOUS MUTATIONS ARE REJECTED, NOT COUNTED.  A mutation that does not change
the builder's input or output is reported as VACUOUS and fails this harness,
because a guard cannot be credited for catching something that never happened.

    python3 prove-journey-exit-mutations.py
"""

import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
BUILDER = SRC / "build-journey-exit.py"

CHECKS = re.findall(r'"(disc0\d\d[^"]*\.html)"',
                    BUILDER.read_text(encoding="utf-8"))
CHECKS = sorted(set(CHECKS))
assert len(CHECKS) == 10, CHECKS

E0E_BLOCK = '''    if sha(base)[:12] != EXPECTED_BEFORE[f]:'''
E0E_OFF = '''    if False:'''


def mk(tmp):
    """A throwaway repo: the ten checks and the builder, nothing else."""
    (tmp / "atlas-tools").mkdir(parents=True, exist_ok=True)
    for f in CHECKS:
        shutil.copy2(ROOT / f, tmp / f)
    shutil.copy2(BUILDER, tmp / "atlas-tools" / "build-journey-exit.py")
    return tmp / "atlas-tools" / "build-journey-exit.py"


def run(b, write=False):
    r = subprocess.run([sys.executable, str(b)] + ([] if write else ["--check"]),
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def built_output(mutate=None):
    """Build with guards NEUTRALISED and return the written pages.

    Needed to tell a BLIND guard from a VACUOUS mutation. A mutant that the
    builder lets through may have changed nothing at all, and crediting a guard
    for "passing" a mutation that never happened is exactly the self-deception
    this harness exists to prevent. So the mutant's real output is compared
    against the control's real output; identical output means VACUOUS.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        b = mk(tmp)
        # every die() becomes a no-op, so the build always reaches the write
        t = b.read_text(encoding="utf-8").replace(
            "    sys.exit(1)", "    return", 1)
        b.write_text(t, encoding="utf-8")
        if mutate:
            mutate(b, tmp)
        rc, out = run(b, write=True)
        if rc != 0:
            return None
        return {f: (tmp / f).read_text(encoding="utf-8") for f in CHECKS}


def patch(p, old, new, count=1):
    t = p.read_text(encoding="utf-8")
    if old not in t:
        return False
    p.write_text(t.replace(old, new, count), encoding="utf-8")
    return True


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


# ------------------------------------------------------------------ the cases
# (label, kind, expected guard id, mutate(builder_path, tmp) -> bool)

def m_e1(b, t):
    # make the region depend on the page, so it is not canonical any more
    return after_splice(b, 'out = out.replace("More from PlotNua", '
                           '"More from PlotNua " + f, 1)')

SPLICE = 'out = base[:i] + "\\n\\n" + REGION + "\\n" + base[i:]'


def after_splice(b, stmt):
    """Append a statement that rewrites `out` AFTER it has been built.

    Not `SPLICE + '.replace(...)'`. That binds the call to the final operand
    `base[i:]` rather than to the whole expression, so it only ever rewrites
    the tail after </main>. Two cases were silently no-ops that way and were
    reported as BLIND guards when nothing had in fact been mutated.
    """
    return patch(b, SPLICE, SPLICE + "\n    " + stmt)


def m_e2(b, t):
    # A byte outside <main>, outside the region, that is not prose, not an
    # anchor and not a script body — the only shape left for E2 alone.
    return after_splice(b, 'out = out.replace("<body>", "<body >", 1)')

def m_e6(b, t):
    # Change bytes INSIDE the governed decision experience without changing a
    # word of prose, so E4 cannot claim it. Mutating the OUTPUT, not the
    # builder's intermediate: mutating `base` made this case go BLIND, because
    # a base-versus-out comparison then compared two equally corrupt copies.
    return after_splice(b, 'out = re.sub(r\'<main class="(\\w+)-wrap">\', '
                           'r\'<main class="\\1-wrap" >\', out, 1)')

def m_e6b(b, t):
    # splice the region INSIDE <main>
    return patch(b, 'i = base.index("</main>") + len("</main>")',
                 'i = base.index("</main>")')

def m_e3script(b, t):
    # the region brings a <script> with it
    return patch(b, 'REGION = BEGIN + "\\n<style>\\n"',
                 'REGION = BEGIN + "\\n<script>var x=1;</script>\\n<style>\\n"')

def m_e3inline(b, t):
    # A pre-existing inline <script> body altered — outside <main>, and not
    # prose, so E6 and E4 cannot claim it.
    return after_splice(b, 'out = out.replace("</script>", "/*x*/</script>", 1)')

def m_e4(b, t):
    # Editorial prose reworded. "PlotNua does not" occurs both in visible copy
    # and inside engine comments, so the mutation is scoped to <main> to make
    # sure it lands on prose and is claimed by E4, which runs before E6.
    return after_splice(b, 'out = out[:out.index("</main>")]'
                           '.replace("PlotNua does not", "PlotNua will not", 1)'
                           ' + out[out.index("</main>"):]')

def m_e9(b, t):
    # weaken an existing CTA: neuter the My Plot anchor in the result
    return after_splice(b, 'out = out.replace('
                           '\'href="your-plot.html?myplot=1"\', \'href="#"\', 1)')

def m_e7(b, t):
    return patch(b, '.pnx-base a{ color:var(--soft); }',
                 '.pnx-base a{ color:var(--soft); } /* localStorage */')

def m_e8(b, t):
    return patch(b, '<footer class="pnx">',
                 '<link rel="stylesheet" href="search.css">\n<footer class="pnx">')

def m_e11(b, t):
    return patch(b, '.pnx-base{ margin:22px 0 0;',
                 'footer a{ color:red; }\n.pnx-base{ margin:22px 0 0;')

def m_e12(b, t):
    # drop the labelled nav
    return patch(b, '<nav class="pnx-nav" aria-label="PlotNua">',
                 '<div class="pnx-nav">')

def m_e13(b, t):
    # a misleading invitation creeps into site chrome
    return patch(b, 'they are not all about the same part of a property.',
                 'they are not all about the same part of a property. '
                 'People are looking — sign up to be matched.')

def m_e14(b, t):
    # a required destination silently disappears
    return patch(b, '<a class="pnx-go" href="search.html">Search PlotNua</a>',
                 '<a class="pnx-go" href="about.html">About PlotNua</a>')

def m_e5(b, t):
    # inject twice: idempotence broken
    return patch(b, SPLICE,
                 'out = base[:i] + "\\n\\n" + REGION + "\\n" + REGION '
                 '+ "\\n" + base[i:]')

def m_e0b(b, t):
    # [input] a second </main> makes the anchor ambiguous
    p = t / "disc029-hidden-bins-check.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("</main>", "</main>\n<main></main>", 1),
                 encoding="utf-8")
    return True

def m_e0c(b, t):
    # [input] the page already uses the pnx- prefix
    p = t / "disc005-home-exchange.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("<body>", '<body><div class="pnx-go"></div>', 1),
                 encoding="utf-8")
    return True

def m_e0d(b, t):
    # [input] a brand token the region needs is renamed away
    p = t / "disc022-hidden-cars-check.html"
    s = p.read_text(encoding="utf-8")
    i = s.index(":root")
    j = s.index("}", i)
    p.write_text(s[:i] + s[i:j].replace("--soft:", "--softish:", 1) + s[j:],
                 encoding="utf-8")
    return True

def m_e0e(b, t):
    # [input] E0e itself: a page differs from its frozen baseline. This is the
    # ONE case where E0e must NOT be bypassed — it is the guard under test.
    p = t / "disc025-borrowed-garden-check.html"
    s = p.read_text(encoding="utf-8")
    p.write_text(s.replace("</body>", "<!-- x -->\n</body>", 1), encoding="utf-8")
    return True


CASES = [
    ("region made page-dependent",              "builder", "E1",   m_e1),
    ("a byte changed outside the splice point", "builder", "E2",   m_e2),
    ("markup injected inside <main>",           "builder", "E6",   m_e6),
    ("region spliced inside <main>",            "builder", "E6b",  m_e6b),
    ("region brings a <script>",                "builder", "E3",   m_e3script),
    ("a pre-existing inline <script> altered",  "builder", "E3",   m_e3inline),
    ("editorial prose reworded",                "builder", "E4",   m_e4),
    ("existing My Plot CTA neutered",           "builder", "E9",   m_e9),
    ("storage API named in the region",         "builder", "E7",   m_e7),
    ("search.css pulled onto a journey",        "builder", "E8",   m_e8),
    ("unscoped 'footer a' selector added",      "builder", "E11",  m_e11),
    ("labelled <nav> downgraded to <div>",      "builder", "E12",  m_e12),
    ("misleading register invitation added",    "builder", "E13",  m_e13),
    ("Search destination swapped away",         "builder", "E14",  m_e14),
    ("region injected twice",                   "builder", "E5",   m_e5),
    ("a second </main> added",                  "input",   "E0b",  m_e0b),
    ("page already uses the pnx- prefix",       "input",   "E0c",  m_e0c),
    ("a required brand token renamed",          "input",   "E0d",  m_e0d),
    ("page differs from its frozen baseline",   "input",   "E0e",  m_e0e),
]

# E0e is the guard under test in exactly one case; everywhere else it is
# bypassed in the test copy so it cannot mask the guard being proven.
NO_BYPASS = {"E0e"}

print("\n  MUTATION CAPABILITY PROOF · build-journey-exit.py")
print("  %d cases\n" % len(CASES))

# control: the unmutated builder must PASS, or every "caught" below is noise
with tempfile.TemporaryDirectory() as d:
    tmp = pathlib.Path(d)
    b = mk(tmp)
    rc, out = run(b)
    if rc != 0:
        print(out)
        sys.exit("CONTROL FAILED: the unmutated builder does not pass, so no "
                 "mutation result below would mean anything.")
print("  control  unmutated builder passes all guards  OK")

CONTROL_OUT = built_output()
if CONTROL_OUT is None:
    sys.exit("CONTROL FAILED: could not produce a guard-free control build.")
print("  control  guard-free control build captured for vacuity testing  OK\n")

caught = vacuous = blind = wrong = 0
for name, kind, guard, fn in CASES:
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        b = mk(tmp)
        if kind == "input" and guard not in NO_BYPASS:
            assert patch(b, E0E_BLOCK, E0E_OFF), "could not disable E0e"
        if not fn(b, tmp):
            print("  %-42s VACUOUS  mutation did not apply" % name)
            vacuous += 1
            continue
        rc, out = run(b)
        if rc == 0:
            # Did the mutation change anything at all? A mutant whose output
            # equals the control's is vacuous, not a blind guard.
            mo = built_output(fn) if kind == "builder" else None
            if mo is not None and mo == CONTROL_OUT:
                print("  %-42s VACUOUS  output identical to the control" % name)
                vacuous += 1
                continue
            print("  %-42s BLIND    expected %s, builder passed" % (name, guard))
            blind += 1
            continue
        m = re.search(r"REFUSED: (E\d+[a-z]?)", out)
        got = m.group(1) if m else "(no guard id)"
        if got != guard:
            print("  %-42s WRONG    expected %s, got %s" % (name, guard, got))
            wrong += 1
            continue
        note = "" if kind == "builder" else "   [input · E0e bypassed]" \
            if guard not in NO_BYPASS else "   [input]"
        print("  %-42s caught by %-5s%s" % (name, got, note))
        caught += 1

print("\n  %d caught · %d blind · %d vacuous · %d wrong guard"
      % (caught, blind, vacuous, wrong))
if blind or vacuous or wrong:
    sys.exit("\n  FAILED: every case must be caught by its own guard, and no "
             "blind, vacuous or misattributed result counts as a pass.\n")
print("  every guard demonstrated capable of failing.\n")
