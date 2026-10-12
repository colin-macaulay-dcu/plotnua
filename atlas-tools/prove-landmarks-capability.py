#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOB 4 · GUARD-CAPABILITY PROOF
===============================================================================
A guard that has only ever been seen to pass is a comment. This copies the
whole site into a temporary tree, reintroduces each Job 4 defect ONE AT A TIME
-- including the exact pre-fix shapes -- and requires prove-landmarks.mjs to
REFUSE each time, naming the right guard.

Two disciplines carried over from the Job 1 mutation proof:

  VACUOUS MUTATIONS ARE REJECTED, NOT COUNTED. If a mutation does not actually
  change the bytes, it proves nothing, and this says so instead of banking a
  pass.

  THE GUARD MUST BE THE RIGHT ONE. It is not enough that the suite went red:
  the failing line must mention the guard the mutation targets, or it is
  recorded as MISATTRIBUTED. That is how Job 1 found five guards that were
  only ever firing because an earlier, more general guard got there first.

The real repository is hashed before and after: a proof that edits what it
proves has proved nothing.
"""

import hashlib
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SUITE = "atlas-tools/prove-landmarks.mjs"

WATCH = ["index.html", "404.html", "your-plot.html", "about.html",
         "discovery-hidden-bins.html", "discovery-home-exchange.html",
         "disc025-borrowed-garden-check.html", "search.js", "search.css"]


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# (name, guard it must trip, file, mutate(text) -> text)
def m_multi_main(t):
    """The exact pre-fix Discovery shape: sibling mains around full-bleed."""
    t = t.replace('<main id="pn-main">\n', "", 1)
    t = t.replace("\n</main>", "", 1)
    return (t.replace('<div class="article">', '<main class="article">')
             .replace("</div>\n\n<section class=\"imagine-photo",
                      "</main>\n\n<section class=\"imagine-photo"))


MUTATIONS = [
    ("pre-fix Discovery: several sibling <main> landmarks", "L1",
     "discovery-hidden-bins.html", m_multi_main),

    ("pre-fix index.html: no <main> landmark at all", "L1", "index.html",
     lambda t: t.replace('<main id="pn-main">\n', "", 1).replace("</main>\n\n", "", 1)),

    ("pre-fix your-plot.html: no <main> landmark at all", "L1", "your-plot.html",
     lambda t: t.replace('<main id="pn-main">\n', "", 1).replace("</main>\n\n", "", 1)),

    ("a second <main> sneaks back onto 404.html", "L1", "404.html",
     lambda t: t.replace("<footer>", "<main>stray</main>\n<footer>", 1)),

    ("role=\"main\" used as a second landmark", "L1", "about.html",
     lambda t: t.replace("<footer>", '<div role="main">stray</div>\n<footer>', 1)),

    ("pre-fix carousel: the false role=\"tablist\" returns", "L4", "index.html",
     lambda t: t.replace('<div class="d-dots" role="group"',
                         '<div class="d-dots" role="tablist"', 1)),

    ("pre-fix footer: column headings drop back to h4", "L5", "about.html",
     lambda t: re.sub(r"<h2>(Navigation|Company|Social|Contact)</h2>",
                      r"<h4>\1</h4>", t)),

    ("pre-fix footer: the nav landmark reverts to a div", "L6", "contact.html",
     lambda t: t.replace('<nav class="footer-cols" aria-label="Footer">',
                         '<div class="footer-cols">', 1).replace("</nav>", "</div>", 1)),

    ("the skip link is removed", "L7", "discovery-hidden-bins.html",
     lambda t: t.replace('<a class="pn-skip" href="#pn-main">Skip to main content</a>', "", 1)),

    ("the skip link points at a target that does not exist", "L7",
     "discovery-home-exchange.html",
     lambda t: t.replace(' id="pn-main"', "", 1)),

    ("the skip link becomes visible when not focused", "L7", "404.html",
     lambda t: t.replace("left:-9999px", "left:8px", 1)),

    ("the skip link is no longer the first focusable element", "L8",
     "your-plot.html",
     lambda t: re.sub(r"(<body[^>]*>)\n", r'\1\n<a href="#x">first</a>\n', t, count=1)),

    ("a duplicate id is introduced", "L9", "index.html",
     lambda t: t.replace('<footer>', '<div id="pn-main"></div>\n<footer>', 1)),

    ("DISC-025's frozen <main> is edited", "L10",
     "disc025-borrowed-garden-check.html",
     lambda t: t.replace("</main>", "<p>injected</p></main>", 1)),

    ("search.js is modified", "L11", "search.js",
     lambda t: t + "\n/* touched */\n"),

    ("search.css is modified", "L11", "search.css",
     lambda t: t + "\n/* touched */\n"),

    ("a Job 1 journey exit is removed", "L12",
     "disc029-hidden-bins-check.html",
     lambda t: t.replace("PLOTNUA JOURNEY EXIT v1", "REMOVED", 1)),

    ("INTEREST_PUBLIC is flipped to true", "L13",
     "disc025-borrowed-garden-check.html",
     lambda t: t.replace("INTEREST_PUBLIC = false", "INTEREST_PUBLIC = true", 1)),
]


def run_suite(tree):
    r = subprocess.run(["node", str(ROOT / SUITE), "--dir", str(tree)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def main():
    before = {f: sha(ROOT / f) for f in WATCH}

    # control: an unmutated copy must PASS, or every later red is meaningless
    with tempfile.TemporaryDirectory() as td:
        tree = pathlib.Path(td) / "site"
        shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(".git", "node_modules"))
        rc, out = run_suite(tree)
        if rc != 0:
            print("CONTROL FAILED: an unmutated copy does not pass. "
                  "No mutation result below would mean anything.")
            print(out[-1500:])
            return 2
        ctrl = [l for l in out.splitlines() if "passed," in l]
        print("\n  CONTROL: unmutated copy %s\n" % (ctrl[0].strip() if ctrl else "passed"))

    caught = vacuous = blind = misattributed = 0
    print("  %-62s %-5s %s" % ("MUTATION", "GUARD", "RESULT"))
    print("  " + "-" * 92)

    for name, guard, target, fn in MUTATIONS:
        with tempfile.TemporaryDirectory() as td:
            tree = pathlib.Path(td) / "site"
            shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(".git", "node_modules"))
            p = tree / target
            orig = p.read_text(encoding="utf-8")
            mutated = fn(orig)
            if mutated == orig:
                vacuous += 1
                print("  %-62s %-5s VACUOUS -- the mutation changed nothing, so it "
                      "proves nothing" % (name[:62], guard))
                continue
            p.write_text(mutated, encoding="utf-8")
            rc, out = run_suite(tree)
            if rc == 0:
                blind += 1
                print("  %-62s %-5s BLIND -- the suite passed a broken tree"
                      % (name[:62], guard))
                continue
            fails = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
            if any(l.split("]")[1].strip().startswith(guard + " ") for l in fails):
                caught += 1
                print("  %-62s %-5s caught" % (name[:62], guard))
            else:
                misattributed += 1
                print("  %-62s %-5s MISATTRIBUTED -- refused, but by %s"
                      % (name[:62], guard,
                         (fails[0].split("]")[1].strip()[:40] if fails else "?")))

    after = {f: sha(ROOT / f) for f in WATCH}
    drift = [f for f in WATCH if before[f] != after[f]]
    print("\n  %d caught / %d vacuous / %d BLIND / %d MISATTRIBUTED  (of %d)"
          % (caught, vacuous, blind, misattributed, len(MUTATIONS)))
    print("  repository untouched by this proof: %s"
          % ("NO -- " + ", ".join(drift) if drift else "yes, all %d watched files "
             "byte-identical" % len(WATCH)))
    print()
    return 0 if (blind == 0 and misattributed == 0 and vacuous == 0 and not drift) else 1


if __name__ == "__main__":
    sys.exit(main())
