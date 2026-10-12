#!/usr/bin/env python3
"""
G6 OPENING · INTEREST_PUBLIC -> true — BOUNDED BUILDER  (PREPARED, NOT APPLIED
TO THE RELEASE BRANCH)
===============================================================================
Lives on branch opening/g6-register. It flips exactly ONE line of
disc025-borrowed-garden-check.html and nothing else:

    var INTEREST_PUBLIC = false;   ->   var INTEREST_PUBLIC = true;

It REFUSES unless every G6 precondition the opening depends on is present,
so it cannot be applied to a tree that lacks the release:
  - the page carries the G6 wording, tenure-only payload and honeypot
  - the canonical consent sentence and the PS-1 register-aware footer
  - privacy.html carries Section 7, The Garden Owner Register
  - the Worker refuses the four deprecated keys
  - wrangler.toml declares PRIVACY_VERSION 2026-10-PHASE2-V3

It does NOT change wrangler.toml. WRITES_ENABLED is a deploy-time decision
taken in the runbook, in its own step, BEFORE this page change is published,
so that no homeowner ever meets "The register isn't open yet".

Post-gates: the page differs from its input in exactly one line, that line is
the switch, and the frozen <main> region is byte-identical.

  python3 atlas-tools/build-g6-open-register.py --check | --apply
"""
import hashlib, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
PRIVACY = ROOT / "privacy.html"
WORKER = ROOT / "worker" / "garden-register" / "src" / "index.js"
WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"

OFF = "  var INTEREST_PUBLIC = false;"
ON = "  var INTEREST_PUBLIC = true;"

PAGE_REQUIRES = [
    ("G6 prep marker", "PLOTNUA-G6-PREP-2026-10-12"),
    ("D3 heading", 'id="bgIntH">Could you see yourself sharing part of'),
    ("D3 not-live statement", "<strong>Matching isn&rsquo;t live yet.</strong>"),
    ("D2 tenure-only payload", "      inherited_tenure: answers.tenure || ''\n    };"),
    ("D4 honeypot", 'id="bgIntWebsite" name="website" tabindex="-1"'),
    ("canonical consent", "\"I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.\";"),
    ("PS-1 register-aware footer", "you can choose to join the register."),
    ("no_garden suppression", "if (answers.spare_corner === 'no_garden') return false;"),
]
PRIVACY_REQUIRES = [("privacy Section 7", "<h2>7. The Garden Owner Register</h2>")]
WORKER_REQUIRES = [("deprecated-key refusal", "if (deprecated) return REFUSED(cors, deprecated);"),
                   ("status ceiling", "const SUBMIT_STATUS = 'interest_submitted';")]
WRANGLER_REQUIRES = [("privacy V3", 'PRIVACY_VERSION = "2026-10-PHASE2-V3"')]


def refuse(msg):
    print("REFUSED: " + msg); sys.exit(2)


def main_region(t):
    i, j = t.find("<main"), t.find("</main>")
    if i < 0 or j < 0:
        refuse("GATE: <main> region not found")
    return t[i:j + 7]


def build(page, privacy, worker, wrangler):
    if page.count(ON) and not page.count(OFF):
        refuse("the register is already open (INTEREST_PUBLIC is true)")
    if page.count(OFF) != 1:
        refuse(f"switch line expected exactly once, found {page.count(OFF)}")
    for text, reqs, where in ((page, PAGE_REQUIRES, "page"), (privacy, PRIVACY_REQUIRES, "privacy.html"),
                              (worker, WORKER_REQUIRES, "Worker"), (wrangler, WRANGLER_REQUIRES, "wrangler.toml")):
        for lab, s in reqs:
            if text.count(s) != 1:
                refuse(f"PRECONDITION: {where} lacks {lab} — the G6 release is not present")
    out = page.replace(OFF, ON)
    a, b = page.splitlines(), out.splitlines()
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(a) != len(b) or len(diff) != 1 or b[diff[0]] != ON:
        refuse("GATE: the change is not exactly the one switch line")
    if main_region(out) != main_region(page):
        refuse("GATE: the frozen <main> region changed")
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    page = PAGE.read_text(encoding="utf-8")
    out = build(page, PRIVACY.read_text(encoding="utf-8"),
                WORKER.read_text(encoding="utf-8"), WRANGLER.read_text(encoding="utf-8"))
    h = lambda t: hashlib.sha256(t.encode()).hexdigest()[:16]
    print(f"  disc025-borrowed-garden-check.html  {h(page)} -> {h(out)}  (one line)")
    if mode == "--apply":
        PAGE.write_text(out, encoding="utf-8"); print("APPLIED")
    else:
        print("CHECK OK (nothing written)")


if __name__ == "__main__":
    main()
