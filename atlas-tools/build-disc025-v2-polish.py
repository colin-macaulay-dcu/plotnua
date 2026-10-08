#!/usr/bin/env python3
"""
BOUNDED BUILDER · DISC-025 V2 FINAL POLISH
===========================================================================
Founder visual verdict: PASS WITH FINAL POLISH, 8 October 2026.
Four bounded changes. No new components, no restructure, no redesign.

  1 the ownership reassurance leaves the POSITIVE checklist.
    'The decision about the garden is yours.' is reassurance, not evidence
    for why the arrangement could work. The clean case now shows three
    reasons. The engine reason authority_the_decision_is_yours is NOT
    deleted - it is demoted into the disclosure, so nothing governed
    silently disappears. The G29 invariant is unchanged in strength: the
    tenure dimension can no longer tick at all, which is stricter.

  2 the 'What we are building' panel goes behind a quiet disclosure,
    'How would this work?'. It is collapsed, so it is never expanded
    beneath the invitation, the completed form or the success state.
    Every governed sentence still renders, one click away.

  3 journey-owned label: 'Anything you want to tell us' ->
    'Anything else we should know?'. Verified journey-owned: it appears
    only in the page and its generator, and no guard asserts it. The
    field id, name, maxlength and payload key are untouched.

  4 success content unchanged - already correct.

UNTOUCHED: consent sentences and hashes · PRIVACY_VERSION · the privacy
notice · governed CONTEXT_COPY · question texts · all option values ·
intPayload() · the Worker · funnel events · all three switches.

Run:  python3 atlas-tools/build-disc025-v2-polish.py [--check]
"""

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
GEN = ROOT / "atlas-tools" / "build-g3-garden-interest.py"
TEST = ROOT / "worker" / "garden-register" / "test" / "prove-g3.mjs"
CHECK = "--check" in sys.argv

EXPECT_IN = "57277df63ed627e6fe33f49a11faab3c15755f5a042285ce9c7f27761a765960"
CONSENT_G = ("I'm over 18, and I'd like PlotNua to keep this and tell me "
             "if someone nearby is looking for growing space.")
SHA_G = "85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c"

fails = []


def gate(n, ok, d=""):
    print("    %-4s %-60s %s" % ("PASS" if ok else "FAIL", n, d))
    if not ok:
        fails.append(n)


def die(m):
    print("\n  ABORT: %s\n  Nothing written." % m)
    sys.exit(1)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


P, G, T = "page", "gen", "test"
EDITS = []

# ---- 1 · ownership reassurance out of the positive checklist --------------
EDITS.append(("tick vocab: drop tenure", P,
"""  var TICK_OK = {
    tenure:       ['own'],
    spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn'],
    way_in:       ['side_or_rear_access', 'its_own_gate'],
    your_own_use: ['yes_regularly', 'now_and_then']
  };

  var TICK_COPY = {
    own:                     'The decision about the garden is yours.',
    yes_a_clear_corner:      'You already have a corner in mind.',""",
"""/* FOUNDER POLISH 1, 8 October 2026. The tenure dimension no longer ticks at
     all. 'The decision about the garden is yours' is reassurance, not evidence
     for why the arrangement could work, so the clean case shows three reasons
     rather than four. The engine reason is demoted, not deleted - see
     DEMOTED_REASONS below. This is STRICTER than before, not weaker: a
     dimension that cannot appear in TICK_OK can never produce a tick. */
  var TICK_OK = {
    spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn'],
    way_in:       ['side_or_rear_access', 'its_own_gate'],
    your_own_use: ['yes_regularly', 'now_and_then']
  };

  var TICK_COPY = {
    yes_a_clear_corner:      'You already have a corner in mind.',"""))

EDITS.append(("tick order: drop tenure", P,
    "    ['spare_corner', 'way_in', 'your_own_use', 'tenure'].forEach(function (q) {",
    "    ['spare_corner', 'way_in', 'your_own_use'].forEach(function (q) {"))

# The ownership reason still has to render somewhere. It joins the disclosure.
EDITS.append(("demote the ownership reason", P,
"""  var TO_SORT = ['authority_permission_from_the_owner', 'scope_no_part_identified_yet',""",
"""  /* Reasons that are true and governed but are not evidence for the finding.
     They render inside the disclosure so nothing is deleted. */
  var DEMOTED_REASONS = ['authority_the_decision_is_yours'];

  var TO_SORT = ['authority_permission_from_the_owner', 'scope_no_part_identified_yet',"""))

EDITS.append(("disclosure carries the demoted reason", P,
"""    var standing = r.reasons.filter(function (k) {
      return ENG.STANDING_REASONS.indexOf(k) !== -1 && REASON[k];
    });""",
"""    var standing = r.reasons.filter(function (k) {
      return (ENG.STANDING_REASONS.indexOf(k) !== -1 ||
              DEMOTED_REASONS.indexOf(k) !== -1) && REASON[k];
    });"""))

# ---- 2 · the next panel behind a quiet disclosure -------------------------
EDITS.append(("next panel becomes a disclosure", P,
"""  function nextNode(r) {
    var el = document.createElement('section');
    el.className = 'bg-next';
    var h = '<span class="bg-next-lab">' + NEXT.lab + '</span>' +
            '<h3 class="bg-next-h">' + NEXT.h + '</h3>' +""",
"""  function nextNode(r) {
    /* FOUNDER POLISH 2. Collapsed by default, so it is never expanded beneath
       the invitation, the completed form or the success state. Every governed
       sentence still renders, one click away. */
    var el = document.createElement('details');
    el.className = 'bg-next';
    var h = '<summary class="bg-next-sum">How would this work?</summary>' +
            '<h3 class="bg-next-h">' + NEXT.h + '</h3>' +"""))

EDITS.append(("next disclosure styling", P,
    "  .bg-int-caveat{margin:14px 0 0;font-size:14.5px;line-height:1.55;",
    """  .bg-next>.bg-next-sum{cursor:pointer;font-size:15px;color:var(--soft);
    padding:12px 0;list-style:none;}
  .bg-next>.bg-next-sum::-webkit-details-marker{display:none;}
  .bg-next>.bg-next-sum::after{content:' \\2192';}
  details.bg-next{border:0;background:none;padding:0;margin:4px 0 28px;}
  .bg-int-caveat{margin:14px 0 0;font-size:14.5px;line-height:1.55;"""))

# ---- 3 · journey-owned label --------------------------------------------
LBL_OLD = '<label for="bgIntNote">Anything you want to tell us</label>'
LBL_NEW = '<label for="bgIntNote">Anything else we should know?</label>'
EDITS.append(("note label", P, LBL_OLD, LBL_NEW))
EDITS.append(("note label", G, LBL_OLD, LBL_NEW))

# ---- 4 · G29 restated rule follows the change ---------------------------
EDITS.append(("G29 restated rule: drop tenure", T,
"""  const QUALIFY = {
    spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn'],
    way_in:       ['side_or_rear_access', 'its_own_gate'],
    your_own_use: ['yes_regularly', 'now_and_then'],
    tenure:       ['own']
  };
  const COPY = {
    own:                    'The decision about the garden is yours.',
    yes_a_clear_corner:     'You already have a corner in mind.',""",
"""  /* POLISH 1: tenure no longer qualifies for a tick. The invariant is
     STRICTER - the dimension is absent from QUALIFY, so G29c now fails if a
     tenure tick appears at all, where before it only failed if the wrong
     tenure ticked. FLAG.tenure is retained below so G29b still proves a
     flagged owner-permission case cannot tick. */
  const QUALIFY = {
    spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn'],
    way_in:       ['side_or_rear_access', 'its_own_gate'],
    your_own_use: ['yes_regularly', 'now_and_then']
  };
  const COPY = {
    yes_a_clear_corner:     'You already have a corner in mind.',"""))

EDITS.append(("G29 order: drop tenure", T,
    "  const ORDER = ['spare_corner', 'way_in', 'your_own_use', 'tenure'];",
    "  const ORDER = ['spare_corner', 'way_in', 'your_own_use'];"))

# FLAG still references tenure; QUALIFY no longer does. Keep G29b meaningful
# by guarding the lookup.
EDITS.append(("G29b tolerates a dimension with no tick vocabulary", T,
"""      if (r.reasons.indexOf(FLAG[q]) !== -1) {
        const dimCopy = QUALIFY[q].map((v) => COPY[v]);""",
"""      if (r.reasons.indexOf(FLAG[q]) !== -1) {
        const dimCopy = (QUALIFY[q] || []).map((v) => COPY[v]);"""))

EDITS.append(("G29b iterates every flagged dimension, not just ticking ones", T,
    "    for (const q of ORDER) {",
    "    for (const q of ['spare_corner', 'way_in', 'your_own_use', 'tenure']) {"))


def main():
    print("\nBOUNDED BUILDER · DISC-025 V2 FINAL POLISH")
    print("=" * 74)
    page = PAGE.read_text(encoding="utf-8")
    h = sha(page)
    print("  page in  sha256 %s" % h)
    if h != EXPECT_IN:
        if "DEMOTED_REASONS" in page:
            print("  Already polished. Idempotent exit.")
            return 0
        die("page is not the accepted V2 experience candidate")
    print("  matches the accepted V2 candidate                       OK")

    buf = {P: page, G: GEN.read_text(encoding="utf-8"), T: TEST.read_text(encoding="utf-8")}
    print("\n  EDITS")
    for label, target, old, new in EDITS:
        n = buf[target].count(old)
        gate("%-42s %s" % (label, target), n == 1, "found %d" % n)
        if n != 1:
            die("splice point not unique: %s (%s)" % (label, target))
        buf[target] = buf[target].replace(old, new, 1)

    pg = buf[P]
    print("\n  INVARIANTS")
    gate("ownership reassurance gone from the tick vocabulary",
         "own:                     'The decision about the garden is yours.'" not in pg)
    gate("the ownership REASON still exists (demoted, not deleted)",
         "'You own the home, so the decision about the garden is yours to make.'" in pg)
    gate("DEMOTED_REASONS renders inside the disclosure",
         "DEMOTED_REASONS.indexOf(k) !== -1" in pg)
    gate("next panel is a collapsed <details>", "createElement('details')" in pg
         and 'How would this work?' in pg)
    gate("next panel no longer a bare section",
         "el.className = 'bg-next';" in pg and "createElement('section');\n    el.className = 'bg-next'" not in pg)
    gate("note label changed", LBL_NEW in pg and LBL_OLD not in pg)
    gate("note field id / name / payload untouched",
         'id="bgIntNote" name="garden_note"' in pg or
         ('id="bgIntNote"' in pg and 'name="garden_note"' in pg))
    gate("garden consent present exactly once", pg.count(CONSENT_G) == 1)
    gate("garden consent hash unchanged", sha(CONSENT_G) == SHA_G)
    gate("PRIVACY_VERSION still V2", pg.count("2026-10-PHASE2-V2") == 1
         and "2026-10-PHASE2-V1" not in pg)
    gate("INTEREST_PUBLIC still false", "var INTEREST_PUBLIC = false;" in pg)
    gate("preview badge still gated on the switch",
         "if (!INTEREST_PUBLIC) $('bgIntPrev').hidden = false;" in pg)
    for s in ["Join the register", "no public listing", "until you say yes",
              "may never find anybody", "hello@plotnua.ie", "nothing to cancel",
              "small part of Dublin 5", "register, not a match"]:
        gate("retained: %s" % s, s in pg)
    for s in ["Tell your insurer before anyone starts",
              "Ground to grow on is genuinely scarce",
              "has not verified a live Irish route"]:
        gate("governed context retained: %s..." % s[:30], s in pg)
    gate("no live-demand claim", "There are people looking" not in pg
         and "people are looking" not in pg)
    gate("intPayload untouched", "body.garden_note = note;" in pg)

    if fails:
        die("%d guard(s) failed" % len(fails))
    if CHECK:
        print("\n  --check only. Nothing written.")
        return 0

    PAGE.write_text(buf[P], encoding="utf-8")
    GEN.write_text(buf[G], encoding="utf-8")
    TEST.write_text(buf[T], encoding="utf-8")
    print("\n  WRITTEN")
    print("    page       sha256 %s" % sha(buf[P]))
    print("    generator  sha256 %s" % sha(buf[G])[:16])
    print("    prove-g3   sha256 %s" % sha(buf[T])[:16])
    print("    guards failed: %d\n" % len(fails))
    return 0


if __name__ == "__main__":
    sys.exit(main())
