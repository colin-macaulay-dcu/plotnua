#!/usr/bin/env python3
"""PlotNua — build-honour-candidate-lead.py

A BOUNDED BUILDER. Two one-line changes in your-plot.html, both making the
same signal authoritative: pnCandidateSplit's own decision about whether a
lead candidate exists.

FOUNDER DECISION: OPTION 1, 11 October 2026.

THE DEFECT, MEASURED against the regenerated artefact.

  pnCandidateSplit() names a lead ONLY when exactly one candidate is
  caveat-free. All four Class 3A candidates carry `caveats: []`, so
  clear.length === 4 and it deliberately returns { lead: null }.

  Two places then ignored that:

    pnResidentialResults   isPreferred: i === 0
    __PN_RENDER_RESIDENTIAL__   const lead = results[0]

  So the first product BY PRODUCT CODE became the apparent lead. That is
  PROD-000425 Van XL, which carries no price at all (EVIDENCED_POA_QUOTE) and
  no imagery, while PROD-000523 BIOBUILDS Wanderlust — verified area, two
  named configurations, three authorised images — sat below it. A preference
  Atlas has not established, produced by a sort order.

WHAT EACH CHANGE DOES.

  1. `isPreferred` now carries `lead`, the value three lines above it that
     already combines position AND the split's verdict:
         var lead = (i === 0) && !!split.lead;
     With no lead, no candidate is marked preferred. The field was inert
     today — nothing in the residential path reads it — but a data field that
     states something untrue is a defect waiting for its first consumer.

  2. The renderer treats results[0] as the lead only when that candidate's own
     ctx says it is preferred. With no lead, `lk` is empty and the existing
     line `leadWrap.hidden = !lk.length` hides the panel headed "What Atlas
     has established about this building" — which is lead-specific and was
     being attributed to whichever product sorted first. The renderer's own
     comment already promised this: "Hidden entirely when there is no lead."
     It now does what it says.

WHAT IS DELIBERATELY NOT CHANGED.

  * NO NEW RANKING. Order is untouched. Nothing is scored, weighted or
    re-sorted, and BIOBUILDS is not promoted — Wanderlust stays exactly where
    the artefact puts it.
  * ALL FOUR CANDIDATES STILL RENDER. The hero slot and the alternatives rail
    both still receive their products; only the lead ASSERTION is withdrawn.
  * `ev.say` is untouched. It already gives every non-lead candidate the
    neutral sentence, so with no lead all four now get it — which is the
    honest wording, and was already reached because `lead` was already
    computed correctly for that purpose.
  * Eligibility and publication gates are untouched. This builder refuses if
    publicVisibility, class3a or the qualification state appear in its diff.
  * additional-home-universe-v1.json is NEVER written. Hashed before and
    after; the builder refuses if it moved.

HONEST LIMIT, worth stating because my earlier note overstated it. I described
Option 1 as "four peer cards, no implied winner". After this change no card
CLAIMS preference and the lead panel is gone, but the first candidate still
occupies the visually dominant hero slot. Removing the hero entirely is a
layout change — Scenes 3 and 4 read primaryResult — and was not what was
approved. Position still implies something that no text now asserts.

IDEMPOTENT. Run twice and the second run reports nothing to do.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "your-plot.html"
ARTEFACT = ROOT / "additional-home-universe-v1.json"

# ── 1 · the ctx stops claiming a preference the split did not make ─────────
A_OLD = """          isPreferred: i === 0,"""
A_NEW = """          /* HONOURS THE CANDIDATE SPLIT. `lead` three lines above already
             combines position with the split's own verdict:
                 var lead = (i === 0) && !!split.lead;
             and the split returns a null lead whenever it cannot name one —
             which is every case where more than one candidate is caveat-free.
             This field used to read `i === 0`, so the first product BY
             PRODUCT CODE was marked preferred. Measured 11 October 2026: that
             was PROD-000425, which publishes no price and no imagery. Nothing
             in the residential path reads this field today, but a datum that
             states an unestablished preference is a defect waiting for its
             first consumer. Founder decision, Option 1. */
          isPreferred: lead,"""

# ── 2 · the renderer's lead panel appears only for a real lead ─────────────
B_OLD = """      const lead = results && results.length ? results[0] : null;"""
B_NEW = """      /* THE LEAD IS THE CANDIDATE THAT SAYS IT IS ONE, not whichever
         arrived first. The comment above has always promised "Hidden
         entirely when there is no lead"; it read results[0] unconditionally,
         so the panel headed "What Atlas has established about this building"
         was attributed to whichever product sorted first by Product Code.
         The residential ctx builder sets ctx.isPreferred from the candidate
         split, so reading it here makes one signal authoritative on both
         sides. With no lead, `lk` is empty and the existing hidden test below
         removes the panel. The products themselves are untouched: all four
         still render, with their own facts, prices, imagery and links. */
      const lead = (results && results.length
                    && results[0] && results[0].ctx
                    && results[0].ctx.isPreferred) ? results[0] : null;"""


def die(msg: str) -> None:
    print(f"REFUSING: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    if not PAGE.exists():
        die(f"{PAGE} does not exist.")
    src = PAGE.read_text(encoding="utf-8")
    bak = PAGE.with_suffix(PAGE.suffix + ".bak-leadhonour")
    before = hashlib.sha256(ARTEFACT.read_bytes()).hexdigest() if ARTEFACT.exists() else None

    if args.revert:
        if not bak.exists():
            die(f"no sidecar at {bak}.")
        shutil.copyfile(bak, PAGE)
        print(f"reverted. sha256 {hashlib.sha256(PAGE.read_bytes()).hexdigest()[:16]}")
        return

    if "HONOURS THE CANDIDATE SPLIT" in src:
        print("already applied — nothing to do.")
        return

    for label, anchor in (("the residential ctx", A_OLD),
                          ("the renderer's lead", B_OLD)):
        n = src.count(anchor)
        if n != 1:
            die(f"the {label} anchor appears {n} times, expected exactly 1. "
                "your-plot.html has changed; re-read it before editing.")

    out = src.replace(A_OLD, A_NEW).replace(B_OLD, B_NEW)

    # NO RANKING, NO PROMOTION, NO GATE CHANGE. Every one of these must be
    # bit-for-bit identical in count, or the builder has strayed.
    for name, token in (
        ("the candidate split", "pnCandidateSplit"),
        ("the candidate list", "pnResidentialCandidateList"),
        ("the evidence builder", "pnCandidateEvidence"),
        ("the publication gate read", "publicVisibility"),
        ("the Class 3A read", "class3a"),
        ("the qualification read", "qualification"),
        ("the hero builder", "buildResultsHero"),
        ("the alternatives render", "matchAlternatives"),
        ("the primary/rest split", "const [primaryResult, ...alternativeResults] = results;"),
        ("the lead-panel hidden test", "leadWrap.hidden = !lk.length;"),
        ("BIOBUILDS", "BIOBUILDS"),
        ("any sort call", ".sort("),
    ):
        if out.count(token) != src.count(token):
            die(f"{name} changed ({token}). Refusing.")
    # The only two lines that may differ.
    if out.count("isPreferred: lead,") != 1:
        die("the ctx field was not set exactly once. Refusing.")
    if out.count("results[0].ctx.isPreferred") != 1:
        die("the renderer does not read the signal exactly once. Refusing.")

    if args.check:
        print(f"--check: your-plot.html "
              f"{len(out.splitlines()) - len(src.splitlines()):+d} lines, "
              "two expressions changed, no ranking introduced.")
        return

    if not bak.exists():
        shutil.copyfile(PAGE, bak)
    PAGE.write_text(out, encoding="utf-8")

    # SYNTAX CHECK. `node --check` refuses a .html path outright, so each
    # inline script is extracted to its own temporary .js and checked there.
    # The first attempt ran node --check on the page itself and died on
    # ERR_UNKNOWN_FILE_EXTENSION — a tooling error reported as if the page
    # were broken, which is worse than no check at all.
    import re as _re
    import tempfile
    blocks = _re.findall(r"<script(?![^>]*\bsrc=)(?![^>]*application/json)[^>]*>"
                         r"(.*?)</script>", out, _re.S | _re.I)
    if not blocks:
        die("no inline script blocks found — the extraction is wrong, not the page.")
    checked = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, body in enumerate(blocks):
            if not body.strip():
                continue
            f = Path(tmp) / f"block{i}.js"
            f.write_text(body, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                die(f"inline script block {i} does not parse: "
                    f"{r.stderr.strip().splitlines()[-1][:200]}")
            checked += 1
    if not checked:
        die("no non-empty script block was checked.")
    print(f"  syntax: {checked} inline script block(s) parse")

    if out.replace(A_NEW, A_OLD).replace(B_NEW, B_OLD) != src:
        die("the edit is not reversible byte for byte.")

    after = hashlib.sha256(ARTEFACT.read_bytes()).hexdigest() if ARTEFACT.exists() else None
    if before != after:
        die("additional-home-universe-v1.json CHANGED. Investigate before "
            "doing anything else.")

    print("applied.")
    print(f"  your-plot.html   sha256 {hashlib.sha256(PAGE.read_bytes()).hexdigest()[:16]}")
    print(f"  artefact untouched, sha256 still {(after or '')[:16]}")


if __name__ == "__main__":
    main()
