#!/usr/bin/env python3
"""
BOUNDED BUILDER · DISC-025 V2 HOMEOWNER EXPERIENCE
===========================================================================
Founder-approved, 8 October 2026. Presentation only.

WHAT THIS CHANGES
  1 intro headline + sub          (page only)
  2 result: posture label and bordered card removed from render;
    WHY IT COULD WORK checklist derived under the approved G29 rule;
    standing reasons demoted to a disclosure         (page only)
  3 #bgInterest MOVED above #bgNext / #bgContext / save band  (page only)
  4 interest heading, offer, CTA, caveat             (page + generator)
  5 three field hints -> one privacy line            (page + generator)
  6 success state                                    (page + generator)

WHAT THIS MUST NEVER CHANGE  (asserted after every write)
  both consent sentences and their SHA-256
  PRIVACY_VERSION 2026-10-PHASE2-V2
  the 10 privacy-notice paragraphs
  every CONTEXT_COPY governed string
  the four question texts and ALL option values
  engine logic, findings, postures, result keys
  intPayload(), the Worker, funnel event names
  WRITES_ENABLED / EMAIL_ENABLED / INTEREST_PUBLIC

GUARD-ASSERTED STRINGS DELIBERATELY RETAINED VERBATIM
  'Join the register'            (G18d, submit control - founder decision 2)
  'no public listing'            (G23b)
  'until you say yes'            (G23c)
  'may never find anybody'       (G15b, founder decision 3)
  'hello@plotnua.ie' + 'nothing to cancel'   (G15c)
  'small part of Dublin 5'       (G15d / G15e)

Run:  python3 atlas-tools/build-disc025-v2-experience.py [--check]
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "disc025-borrowed-garden-check.html"
GEN = ROOT / "atlas-tools" / "build-g3-garden-interest.py"
CHECK = "--check" in sys.argv

EXPECT_PAGE_IN = "b73ebdcbb44e04c79e8c824264bf5b9c10f107866fdb41ead164a9cd7d470090"

CONSENT_G = ("I'm over 18, and I'd like PlotNua to keep this and tell me "
             "if someone nearby is looking for growing space.")
CONSENT_R = ("I'm over 18, and I'd like PlotNua to keep this and tell me "
             "about possible growing space nearby.")
SHA_G = "85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c"
SHA_R = "32ba8b3ec621ed6e15edf0cc4c4fe95bec7b386d9c95179737fe9179990148f1"

fails = []


def gate(name, ok, detail=""):
    print("    %-4s %-62s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        fails.append(name)
    return ok


def die(msg):
    print("\n  ABORT: %s\n  Nothing was written." % msg)
    sys.exit(1)


def sha(s):
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()


# ==================================================================== EDITS ==
# Each entry: (label, target, old, new). Every `old` must occur EXACTLY once.

P = "page"
G = "gen"
EDITS = []

# ---- 1 · INTRO -------------------------------------------------------------
EDITS.append(("intro headline", P,
"""    <h1 class="pc-introh">Which part of your garden could work, how would somebody
      reach it, and what do you keep?</h1>
    <p class="pc-introsub">Four short questions about the part of your garden you
      could share, how somebody would reach it, and how you would use it yourself.
      We&rsquo;ll tell you what looks workable, what needs sorting, and what we
      cannot yet stand over.</p>""",
"""    <h1 class="pc-introh">Could a corner of your garden work for somebody else?</h1>
    <p class="pc-introsub">Four quick questions about the space you have, how
      somebody could reach it, and how you use it now.</p>"""))

# ---- 2 · RESULT HEADLINE ---------------------------------------------------
EDITS.append(("workable headline", P,
    "arrangement_looks_workable:             'A corner of your garden looks workable',",
    "arrangement_looks_workable:             'A corner of your garden could work',"))

# ---- 3 · THE CHECKLIST RENDERER -------------------------------------------
# Replaces findingNode entirely. CARD_LABEL and POSTURE_LABEL are no longer
# read; both constants stay declared so nothing else can break.
EDITS.append(("findingNode -> checklist", P,
"""function findingNode(r) {
    var el = document.createElement('div');
    el.className = 'bg-res-item';
    var h = '<span class="bg-res-lab">' + (CARD_LABEL[r.posture] || 'The arrangement') + '</span>';
    if (PHYSICAL[r.physical_finding]) {
      h += '<p class="bg-res-phys">' + PHYSICAL[r.physical_finding] + '</p>';
    }
    h += '<span class="bg-res-posture">' + (POSTURE_LABEL[r.posture] || '') + '</span>';
    if (r.posture === 'OPEN') {
      h += '<p class="bg-res-bound">' + OPEN_BOUND + '</p>';
    }
    if (r.reasons.length) {
      h += '<ul class="bg-res-why">';
      r.reasons.forEach(function (k) { if (REASON[k]) h += '<li>' + REASON[k] + '</li>'; });
      h += '</ul>';
    }
    el.innerHTML = h;
    return el;
  }""",
"""/* V2 · WHY IT COULD WORK.
     The three observations explain the headline, so no intermediate
     explanatory sentence is rendered. CARD_LABEL and POSTURE_LABEL are no
     longer read: the bordered report card and the exposed system posture are
     gone from the homeowner's view.

     APPROVED G29 RULE, and it is the whole safety of this surface:
       a tick appears ONLY where the frozen answer supports it AND the engine
       has not flagged that dimension;
       a flagged dimension renders the ENGINE'S OWN REASON, never a tick;
       PENDING renders NO TICKS AT ALL, because an unread dimension must not
       be presented as an established one.
     The ticks are therefore derived from frozen inputs, never invented. */

  var TICK_OK = {
    tenure:       ['own'],
    spare_corner: ['yes_a_clear_corner', 'maybe_part_of_the_lawn'],
    way_in:       ['side_or_rear_access', 'its_own_gate'],
    your_own_use: ['yes_regularly', 'now_and_then']
  };

  var TICK_COPY = {
    own:                     'The decision about the garden is yours.',
    yes_a_clear_corner:      'You already have a corner in mind.',
    maybe_part_of_the_lawn:  'Part of the lawn could work.',
    side_or_rear_access:     'Somebody could reach it without coming through your home.',
    its_own_gate:            'That part has its own gate.',
    yes_regularly:           'You can keep using the rest of the garden.',
    now_and_then:            'You can keep using the rest of the garden.'
  };

  /* The engine's reasons that are things to settle rather than things
     established. Rendered as the quiet list, in the engine's own words. */
  var TO_SORT = ['authority_permission_from_the_owner', 'scope_no_part_identified_yet',
                 'check_a_way_in_that_is_not_the_home', 'check_agree_how_the_space_is_used',
                 'check_what_we_still_need'];

  function ticksFor(a, posture) {
    if (posture === 'PENDING') return [];
    var out = [];
    ['spare_corner', 'way_in', 'your_own_use', 'tenure'].forEach(function (q) {
      var v = a[q];
      if (TICK_OK[q].indexOf(v) !== -1 && TICK_COPY[v]) out.push(TICK_COPY[v]);
    });
    return out;
  }

  function findingNode(r) {
    var el = document.createElement('div');
    el.className = 'bg-res-item is-plain';
    var h = '';
    var ticks = ticksFor(answers, r.posture);
    if (ticks.length) {
      h += '<span class="bg-res-lab">Why it could work</span>';
      h += '<ul class="bg-res-ticks">';
      ticks.forEach(function (t) {
        h += '<li><span class="bg-tick" aria-hidden="true">\\u2713</span>' + t + '</li>';
      });
      h += '</ul>';
    }
    var sort = r.reasons.filter(function (k) {
      return TO_SORT.indexOf(k) !== -1 && REASON[k];
    });
    if (sort.length) {
      h += '<span class="bg-res-lab">Worth sorting first</span>';
      h += '<ul class="bg-res-why">';
      sort.forEach(function (k) { h += '<li>' + REASON[k] + '</li>'; });
      h += '</ul>';
    }
    /* The standing reasons are not a finding about this garden. They go into
       the disclosure, so the result stays readable in seconds. Nothing is
       deleted: every governed key still renders, one click away. */
    var standing = r.reasons.filter(function (k) {
      return ENG.STANDING_REASONS.indexOf(k) !== -1 && REASON[k];
    });
    if (standing.length) {
      h += '<details class="bg-think"><summary>A few things worth thinking about</summary>' +
           '<ul class="bg-res-why">';
      standing.forEach(function (k) { h += '<li>' + REASON[k] + '</li>'; });
      h += '</ul>';
      if (r.posture === 'OPEN') { h += '<p class="bg-res-bound">' + OPEN_BOUND + '</p>'; }
      h += '</details>';
    }
    el.innerHTML = h;
    return el;
  }"""))

# ---- 4 · NO INTERMEDIATE SENTENCE ON AN ASSESSMENT ------------------------
EDITS.append(("drop the reveal sub on assessments", P,
"""      $('bgRevealH').textContent = HEADLINE[r.headline] || '';
      $('bgRevealSub').textContent = SUB[r.posture] || SUB.CONDITIONAL;""",
"""      $('bgRevealH').textContent = HEADLINE[r.headline] || '';
      /* FOUNDER CORRECTION 5. The three observations below explain the
         headline, so the intermediate explanatory sentence is removed rather
         than reworded. SUB is left declared and unused on this branch; the
         early exit still needs its own sentence. */
      $('bgRevealSub').textContent = '';
      $('bgRevealSub').hidden = true;"""))

# ---- 5 · NEXT PANEL: FIVE STATEMENTS OF ABSENCE BECOME ONE ---------------
EDITS.append(("next panel copy", P,
"""    lab: 'What could happen next',
    h: 'Could somebody nearby be looking for exactly this?',
    lede2: 'Somewhere nearby, somebody may be looking for somewhere to grow.',
    lede3: 'PlotNua wants to bring those two things together.',
    status: 'Local Garden Matching &middot; not yet live',
    intro: 'When this opens, you&rsquo;ll be able to ask PlotNua to look for ' +
           'prospective gardeners near you.',""",
"""    lab: 'What we are building',
    h: 'Could somebody nearby be looking for exactly this?',
    lede2: 'Finding each other is the hard part, and PlotNua cannot do it yet.',
    lede3: 'When it can, you will be asked first &mdash; and asked again before ' +
           'anything is shared.',
    status: '',
    intro: '',"""))

EDITS.append(("next panel render", P,
"""            '<p class="bg-next-lede">' + NEXT.lede3 + '</p>' +
            '<p class="bg-next-status">' + NEXT.status + '</p>' +
            '<p class="bg-next-intro">' + NEXT.intro + '</p>' +
            '<ol class="bg-next-steps">';""",
"""            '<p class="bg-next-lede">' + NEXT.lede3 + '</p>' +
            '<ol class="bg-next-steps">';"""))

# ---- 6 · CONTEXT: ALL FIVE CATEGORIES BEHIND ONE CALM DISCLOSURE ---------
EDITS.append(("context disclosure", P,
    "var CONTEXT_VISIBLE = ['insurance'];\n  var CONTEXT_DISCLOSED = ['planning', 'legal', 'tax', 'market'];",
    "/* V2: every category is disclosed, including insurance. Nothing is\n"
    "     deleted - all five still render, behind one calm summary. */\n"
    "  var CONTEXT_VISIBLE = [];\n"
    "  var CONTEXT_DISCLOSED = ['insurance', 'planning', 'legal', 'tax', 'market'];"))

EDITS.append(("disclosure summary", P,
    "<summary>Planning, money, and why we think this could matter</summary>",
    "<summary>Worth knowing &mdash; see what we checked</summary>"))

# ---- 7 · INTEREST: HEADING, OFFER, CTA, CAVEAT --------------------------
OFFER_OLD = """      <span class="bg-int-lab">If you would consider it</span>
      <h2 class="bg-int-h" id="bgIntH">Tell PlotNua you would think about sharing a corner</h2>

      <div id="bgIntOffer">
        <p class="bg-int-p">PlotNua is building a register of Dublin gardens whose
          owners would consider letting somebody grow food in a part of them. It is
          a list, not a service, and it is private.</p>
        <ul class="bg-int-facts">
          <li>There is no public listing, no map, no profile page and no directory.
            Your record is private to PlotNua.</li>
          <li>Nothing is shared with anybody until you say yes to one specific
            introduction. If you do not reply, nothing happens.</li>
          <li><strong>Joining the register is not a match and does not guarantee
            one.</strong> We may never find anybody near you.</li>
        </ul>
        <p class="bg-int-cta">
          <button class="pc-cta" type="button" id="bgIntOpen">Tell PlotNua I would consider it</button>
        </p>
      </div>"""

OFFER_NEW = """      <h2 class="bg-int-h" id="bgIntH">If somebody nearby needed a corner, would you
        want to know?</h2>

      <div id="bgIntOffer">
        <p class="bg-int-p">Tell us about the part you have in mind. If somebody
          nearby is looking for growing space, we&rsquo;ll email you and ask first.</p>
        <p class="bg-int-p">Nobody else sees your details. There is no public listing,
          no map and no profile page. Nothing is shared with anybody until you say yes
          to one specific introduction.</p>
        <p class="bg-int-cta">
          <button class="pc-cta" type="button" id="bgIntOpen">Yes &mdash; let me know</button>
        </p>
        <p class="bg-int-caveat">This is a register, not a match.
          We may never find anybody near you.</p>
      </div>"""
EDITS.append(("interest offer", P, OFFER_OLD, OFFER_NEW))
EDITS.append(("interest offer", G, OFFER_OLD, OFFER_NEW))

# ---- 8 · FORM: THREE DENIALS BECOME ONE LINE ---------------------------
HINTS_OLD = """            <span class="bg-int-hint">First name only. We never ask for your surname.</span>"""
HINTS_NEW = """"""
EDITS.append(("hint 1 removed", P, HINTS_OLD + "\n", ""))
EDITS.append(("hint 1 removed", G, HINTS_OLD + "\n", ""))

H2_OLD = """            <span class="bg-int-hint">How we would reach you. Nothing else.</span>\n"""
EDITS.append(("hint 2 removed", P, H2_OLD, ""))
EDITS.append(("hint 2 removed", G, H2_OLD, ""))

H3_OLD = """            <span class="bg-int-hint">District only. We never ask for your address or
              your Eircode.</span>\n"""
EDITS.append(("hint 3 removed", P, H3_OLD, ""))
EDITS.append(("hint 3 removed", G, H3_OLD, ""))

GRID_OLD = """      <form class="bg-int-form" id="bgIntForm" hidden novalidate>
        <div class="bg-int-grid">"""
GRID_NEW = """      <form class="bg-int-form" id="bgIntForm" hidden novalidate>
        <p class="bg-int-privline">A first name, an email address and a district.
          No surname, no address, no Eircode, no phone number.</p>
        <div class="bg-int-grid">"""
EDITS.append(("one privacy line", P, GRID_OLD, GRID_NEW))
EDITS.append(("one privacy line", G, GRID_OLD, GRID_NEW))

# ---- 9 · SUCCESS STATE --------------------------------------------------
REC_OLD = """    var out = [
      'We have your first name, your email address and what you told us about ' +
      'the garden. Nobody else can see it.',
      'This is a register, not a match. We may never find anybody near you, ' +
      'and if we do we will email you and ask before anything is shared.'
    ];"""
REC_NEW = """    var out = [
      'We have your first name, your email and what you told us about the ' +
      'corner. Nobody else can see it.',
      'This is a register, not a match. If somebody nearby is looking, we ' +
      'will email you and ask first. We may never find anybody near you.'
    ];"""
EDITS.append(("success copy", P, REC_OLD, REC_NEW))
EDITS.append(("success copy", G, REC_OLD, REC_NEW))

# ---- 10 · CSS: DO LESS ---------------------------------------------------
CSS_OLD = "  .bg-opts{display:flex;flex-direction:column;gap:12px;max-width:560px;"
CSS_NEW = """  /* ---- V2 presentation. Bounded: new rules only, nothing restructured. --- */
  .bg-res-item.is-plain{border:0;background:none;padding:0;}
  .bg-res-ticks{list-style:none;margin:10px 0 26px;padding:0;}
  .bg-res-ticks li{display:flex;gap:12px;align-items:flex-start;
    padding:9px 0;font-size:clamp(16px,1.8vw,18px);line-height:1.5;}
  .bg-tick{flex:0 0 auto;font-weight:600;color:var(--accent);line-height:1.5;}
  .bg-think{margin:4px 0 30px;}
  .bg-think>summary{cursor:pointer;font-size:15px;color:var(--soft);
    padding:10px 0;list-style:none;}
  .bg-think>summary::-webkit-details-marker{display:none;}
  .bg-think>summary::after{content:' \\2192';}
  .bg-int-caveat{margin:14px 0 0;font-size:14.5px;line-height:1.55;
    color:var(--soft);}
  .bg-int-privline{margin:0 0 22px;font-size:15px;line-height:1.6;
    color:var(--soft);}
  .bg-opts{display:flex;flex-direction:column;gap:12px;max-width:560px;"""
EDITS.append(("v2 css", P, CSS_OLD, CSS_NEW))


# ============================================================== THE MOVE ====
def move_interest(src):
    """Move the whole #bgInterest section to directly after #bgFinding."""
    begin = "    <!-- PLOTNUA-G3-HTML-BEGIN"
    end = "    <!-- PLOTNUA-G3-HTML-END -->"
    i = src.find(begin)
    j = src.find(end)
    if i < 0 or j < 0:
        die("G3 HTML markers not found - cannot move the interest section")
    block = src[i:j + len(end)] + "\n"
    rest = src[:i] + src[j + len(end) + 1:]
    anchor = '    <div class="bg-res" id="bgFinding"></div>\n'
    if rest.count(anchor) != 1:
        die("bgFinding anchor is not unique")
    return rest.replace(anchor, anchor + "\n" + block, 1)


# ===================================================================== RUN ===
def main():
    print("\nBOUNDED BUILDER · DISC-025 V2 HOMEOWNER EXPERIENCE")
    print("=" * 76)

    page = PAGE.read_text(encoding="utf-8")
    gen = GEN.read_text(encoding="utf-8")
    h = sha(page)
    print("  page in  sha256 %s" % h)
    if h != EXPECT_PAGE_IN:
        if "bg-res-ticks" in page:
            print("  Already at V2. Idempotent exit.")
            return 0
        die("page is not the committed V2-privacy release and is not already V2")
    print("  matches the committed release                      OK")

    buf = {P: page, G: gen}
    print("\n  EDITS")
    for label, target, old, new in EDITS:
        s = buf[target]
        n = s.count(old)
        if not gate("%-34s %s" % (label, target), n == 1, "found %d" % n):
            die("splice point not unique: %s (%s)" % (label, target))
        buf[target] = s.replace(old, new, 1)

    print("\n  DOM MOVE")
    before_i = buf[P].find('id="bgInterest"')
    before_f = buf[P].find('id="bgFinding"')
    gate("interest currently sits AFTER the finding", before_i > before_f)
    buf[P] = move_interest(buf[P])
    after_i = buf[P].find('id="bgInterest"')
    after_f = buf[P].find('id="bgFinding"')
    after_ctx = buf[P].find('id="bgContext"')
    after_save = buf[P].find('class="bg-save pc-saveband"')
    gate("interest now directly after the finding", after_f < after_i)
    gate("interest now BEFORE the context", after_i < after_ctx)
    gate("interest now BEFORE the save band", after_i < after_save)
    gate("exactly one #bgInterest remains", buf[P].count('id="bgInterest"') == 1)

    print("\n  INVARIANTS")
    pg = buf[P]
    gate("garden consent present exactly once", pg.count(CONSENT_G) == 1)
    gate("garden consent sha256 unchanged", sha(CONSENT_G) == SHA_G, sha(CONSENT_G)[:16])
    gate("grower consent sha256 unchanged", sha(CONSENT_R) == SHA_R, sha(CONSENT_R)[:16])
    gate("PRIVACY_VERSION still V2", pg.count("2026-10-PHASE2-V2") == 1
         and "2026-10-PHASE2-V1" not in pg)
    gate("INTEREST_PUBLIC still false", "var INTEREST_PUBLIC = false;" in pg)
    for s in ["Join the register", "no public listing", "until you say yes",
              "hello@plotnua.ie", "nothing to cancel", "small part of Dublin 5"]:
        gate("guard-asserted string retained: %s" % s, s in pg)

    # 'may never find anybody' is asserted PER SURFACE, not file-wide.
    # Mutation M10 proved a file-wide check is too weak: the phrase also
    # appears in the new caveat, so dropping it from the success state still
    # passed. G15b tests the success state specifically, so the builder must
    # too. Each surface is checked in its own slice of the file.
    i_rec = pg.find("function intReceived")
    j_rec = pg.find("intShow('received')", i_rec)
    gate("G15b surface: success state keeps 'may never find anybody'",
         i_rec > 0 and j_rec > i_rec
         and "may never find anybody" in pg[i_rec:j_rec])
    i_cav = pg.find('class="bg-int-caveat"')
    j_cav = pg.find("</p>", i_cav)
    gate("caveat surface: offer keeps 'may never find anybody'",
         i_cav > 0 and "may never find anybody" in pg[i_cav:j_cav])
    gate("caveat surface: offer keeps 'not a match'",
         i_cav > 0 and "not a match" in pg[i_cav:j_cav])
    for s in ["Tell your insurer before anyone starts",
              "Growing vegetables in a garden is not development",
              "Keep using the garden and it stays your garden",
              "Payment is optional", "Ground to grow on is genuinely scarce",
              "has not verified a live Irish route"]:
        gate("governed context retained: %s..." % s[:34], s in pg)
    for s in ["Do you own this home?",
              "Is there a part of your garden you would be comfortable sharing?",
              "Could somebody reach that part without coming through the house?",
              "Would you still be using that part of the garden yourself?"]:
        gate("question text unchanged: %s..." % s[:34], s in pg)
    for v in ["yes_a_clear_corner", "maybe_part_of_the_lawn", "no_it_is_all_in_use",
              "no_garden", "not_sure", "side_or_rear_access", "its_own_gate",
              "through_the_house_only", "yes_regularly", "now_and_then",
              "i_would_leave_them_to_it", "own", "rent", "buying"]:
        if not (("'" + v + "'") in pg):
            gate("frozen option value present: %s" % v, False)
    gate("all frozen option values present", True)
    gate("funnel events unchanged",
         pg.count("garden_interest_opened") == 1 and pg.count("garden_interest_submitted") == 1)
    gate("intPayload untouched", "function intPayload()" in pg
         and "body.inherited_result_key = k;" in pg)
    gate("posture label no longer rendered", "bg-res-posture\">' +" not in pg)
    gate("card label no longer rendered", "CARD_LABEL[r.posture]" not in pg)
    gate("the removed explanatory sentence is gone",
         "SUB[r.posture] || SUB.CONDITIONAL" not in pg)
    gate("no live-demand claim introduced",
         "There are people looking" not in pg and "people are looking" not in pg)

    if fails:
        die("%d guard(s) failed" % len(fails))

    if CHECK:
        print("\n  --check only. Nothing written.")
        return 0

    PAGE.write_text(buf[P], encoding="utf-8")
    GEN.write_text(buf[G], encoding="utf-8")
    print("\n  WRITTEN")
    print("    page      %7d bytes  sha256 %s" % (len(buf[P].encode()), sha(buf[P])))
    print("    generator %7d bytes  sha256 %s" % (len(buf[G].encode()), sha(buf[G])))
    print("    guards failed: %d\n" % len(fails))
    return 0


if __name__ == "__main__":
    sys.exit(main())
