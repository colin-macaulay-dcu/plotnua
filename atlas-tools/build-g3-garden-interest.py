#!/usr/bin/env python3
"""
G3 · DISC-025 BORROWED GARDEN — HOMEOWNER EXPRESSION OF INTEREST
===============================================================================
A BOUNDED BUILDER. It makes five insertions into
disc025-borrowed-garden-check.html and changes nothing else. Every insertion is
located by an anchor string that must appear EXACTLY ONCE; if any anchor is
missing, duplicated, or already carries a G3 marker, the build refuses and
writes nothing.

WHAT THIS DOES NOT TOUCH
  * the certified engine region (PLOTNUA-DISC025-ENGINE-BEGIN/END)
  * PlotNuaJourneySave (shared byte-identically with four other journeys)
  * the four QUESTIONS, the copy tables, decide(), or any result rendering
  * Save to My Plot, in markup or behaviour

SHIPPED CLOSED. THREE INDEPENDENT GATES
  1. INTEREST_PUBLIC = false in source. Nothing renders.
  2. ?interest=preview is the only way to see it while (1) is false.
  3. Suppressed whenever answers.spare_corner === 'no_garden'
     (founder decision Q1).

INDEPENDENT OF SAVE (founder decision Q2). Neither action is a prerequisite
for the other. There is no read of bgSave, PlotNuaJourneySave or localStorage
anywhere in the inserted code.

CONSENT TEXT IS BYTE-EXACT BY CONSTRUCTION. The canonical G1B sentence exists
once, as a JS string literal with ASCII apostrophes, and is BOTH written into
the visible label (via textContent, so no HTML entity can drift it) AND sent
as consent_text. The Worker hashes what arrives and compares against its own
constant; a divergence closes the route rather than recording a consent to
text nobody approved.
"""

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "disc025-borrowed-garden-check.html"

ENDPOINT = ("https://plotnua-garden-register.colin-a41.workers.dev"
            "/v1/garden-register/garden")

# The G1B canonical garden consent sentence, approved verbatim 7 October 2026.
# ASCII apostrophe. Not an entity. Not a typographic quote.
CONSENT = ("I'm over 18, and I'd like PlotNua to keep this and tell me "
           "if someone nearby is looking for growing space.")
CONSENT_SHA = ("a" and hashlib.sha256(CONSENT.encode("utf-8")).hexdigest())

# The founder-corrected closed-state sentence lives in ONE place only: the
# intNotOpen() function inside JS below. A second copy here would be a second
# source of truth for approved wording, which is exactly how approved wording
# drifts, so there is deliberately no constant for it at this level.
# test/prove-g3.mjs holds the sentence independently and asserts the rendered
# page matches it (G14), which is the check that matters.

# ---------------------------------------------------------------- 1 · CSS ----

CSS_ANCHOR = "  .bg-more[open] summary{color:var(--ink);}\n</style>"

CSS = r"""  .bg-more[open] summary{color:var(--ink);}

  /* ---- G3 · EXPRESSION OF INTEREST -------------------------------------
     PLOTNUA-G3-CSS-BEGIN
     Set on --stone, the actions field, so it reads as a continuation of the
     save band rather than a second result. No card, no shadow, no posture
     line, and nothing that could be mistaken for a finding. */
  .bg-int{margin:0 0 30px;padding:30px 28px;background:var(--stone);
    border-top:2px solid rgba(79,107,74,.34);}
  .bg-int-lab{display:block;font-family:'Work Sans',sans-serif;font-size:9.5px;
    font-weight:500;letter-spacing:.22em;text-transform:uppercase;
    color:var(--accent);margin:0 0 14px;}
  .bg-int-h{font-family:'Fraunces',Georgia,serif;font-weight:400;
    font-size:clamp(20px,2.4vw,25px);line-height:1.3;color:var(--ink);
    margin:0 0 12px;max-width:24ch;}
  .bg-int-p{margin:0 0 12px;font-size:15px;line-height:1.65;color:var(--body);}
  .bg-int-p:last-child{margin-bottom:0;}
  /* The three statements a homeowner must not have to dig for. */
  .bg-int-facts{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:9px;}
  .bg-int-facts li{position:relative;padding-left:17px;font-size:14px;
    line-height:1.6;color:var(--body);}
  .bg-int-facts li::before{content:"";position:absolute;left:0;top:9px;
    width:7px;height:1px;background:var(--accent);}
  .bg-int-cta{margin:20px 0 0;}
  .bg-int-notice{margin:18px 0 0;border-top:1px solid rgba(31,59,46,.14);}
  .bg-int-notice summary{cursor:pointer;padding:14px 0 12px;
    font-family:'Work Sans',sans-serif;font-size:13.5px;color:var(--soft);}
  .bg-int-notice summary:hover{color:var(--ink);}
  .bg-int-notice[open] summary{color:var(--ink);}
  .bg-int-noticebody{font-size:14px;line-height:1.7;color:var(--body);
    padding:0 0 8px;}
  .bg-int-noticebody p{margin:0 0 12px;}
  .bg-int-noticebody strong{font-weight:500;color:var(--ink);}

  /* ---- the form ------------------------------------------------------- */
  .bg-int-form{margin:22px 0 0;}
  .bg-int-grid{display:grid;gap:18px;}
  @media(min-width:760px){ .bg-int-grid{grid-template-columns:repeat(2,1fr);} }
  .bg-int-f{display:grid;gap:6px;}
  .bg-int-f.is-wide{grid-column:1/-1;}
  .bg-int-f > label{font-family:'Work Sans',sans-serif;font-size:11px;
    font-weight:500;letter-spacing:.14em;text-transform:uppercase;
    color:var(--ink);}
  .bg-int-f .bg-int-hint{font-size:13px;line-height:1.5;color:var(--muted);}
  .bg-int-f input[type=text],
  .bg-int-f input[type=email],
  .bg-int-f select,
  .bg-int-f textarea{
    width:100%;font-family:'Work Sans',sans-serif;font-size:16px;
    line-height:1.5;color:var(--ink);background:var(--paper);
    border:1px solid var(--rule);border-radius:3px;padding:11px 12px;
    -webkit-appearance:none;appearance:none;}
  .bg-int-f select{background-image:none;}
  .bg-int-f textarea{min-height:92px;resize:vertical;}
  .bg-int-f input:focus,.bg-int-f select:focus,.bg-int-f textarea:focus{
    outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent);}
  /* The tick rows. The consent sentence is the label; nothing is abbreviated
     into a word like "I agree". */
  .bg-int-tick{display:grid;grid-template-columns:20px 1fr;gap:4px 11px;
    align-items:start;margin:20px 0 0;}
  .bg-int-tick input[type=checkbox]{width:18px;height:18px;margin:3px 0 0;
    accent-color:var(--accent);}
  .bg-int-tick label{font-size:14.5px;line-height:1.6;color:var(--body);
    cursor:pointer;}
  .bg-int-cond{margin:20px 0 0;padding:18px 0 0;
    border-top:1px solid rgba(31,59,46,.14);}
  .bg-int-cond[hidden]{display:none;}
  .bg-int-actions{margin:24px 0 0;display:flex;flex-wrap:wrap;gap:12px;
    align-items:center;}
  .bg-int-cancel{background:none;border:0;padding:0;cursor:pointer;
    font-family:'Work Sans',sans-serif;font-size:13.5px;color:var(--soft);
    text-decoration:underline;text-underline-offset:3px;}
  .bg-int-cancel:hover{color:var(--ink);}
  .bg-int-msg{margin:18px 0 0;font-size:14.5px;line-height:1.65;}
  .bg-int-msg[hidden]{display:none;}
  .bg-int-msg.is-bad{color:#7A3B2E;}
  .bg-int-msg.is-flat{color:var(--body);}
  .bg-int-done{margin:0;}
  .bg-int-done-h{font-family:'Fraunces',Georgia,serif;font-weight:400;
    font-size:clamp(19px,2.2vw,23px);line-height:1.3;color:var(--ink);
    margin:0 0 12px;}
  .bg-int-note{margin:18px 0 0;padding:14px 0 0;
    border-top:1px solid rgba(31,59,46,.12);font-size:13px;line-height:1.6;
    color:var(--muted);}
  /* The preview ribbon. Present only in the preview state, and it says so. */
  .bg-int-prev{margin:0 0 16px;font-family:'Work Sans',sans-serif;
    font-size:10px;font-weight:500;letter-spacing:.2em;text-transform:uppercase;
    color:var(--oak);border:1px solid rgba(139,111,78,.4);border-radius:20px;
    padding:5px 12px;display:inline-block;}
  @media(max-width:560px){ .bg-int{padding:26px 20px;} }
  /* PLOTNUA-G3-CSS-END */
</style>"""

# --------------------------------------------------------------- 2 · HTML ----

HTML_ANCHOR = '      </div>\n    </div>\n\n    <details class="bg-drawer">'

HTML = r"""      </div>
    </div>

    <!-- PLOTNUA-G3-HTML-BEGIN
         G3 · HOMEOWNER EXPRESSION OF INTEREST.
         SHIPPED CLOSED: hidden here, and REMOVED FROM THE DOM on load unless
         the journey script's three gates all pass. It sits AFTER the save band
         and depends on none of it.
         The consent label text is written by JS from the single canonical G1B
         constant, so no HTML entity can drift the string that gets hashed. -->
    <section class="bg-int" id="bgInterest" hidden aria-labelledby="bgIntH">
      <p class="bg-int-prev" id="bgIntPrev" hidden>Private preview &middot; not public</p>
      <h2 class="bg-int-h" id="bgIntH">If somebody nearby needed a corner, would you
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
      </div>

      <form class="bg-int-form" id="bgIntForm" hidden novalidate>
        <p class="bg-int-privline">A first name, an email address and a district.
          No surname, no address, no Eircode, no phone number.</p>
        <div class="bg-int-grid">
          <div class="bg-int-f">
            <label for="bgIntName">First name</label>
            <input type="text" id="bgIntName" name="first_name" autocomplete="given-name"
                   maxlength="60" required>
          </div>
          <div class="bg-int-f">
            <label for="bgIntEmail">Email address</label>
            <input type="email" id="bgIntEmail" name="email" autocomplete="email"
                   maxlength="120" required>
          </div>
          <div class="bg-int-f">
            <label for="bgIntDistrict">Which district</label>
            <select id="bgIntDistrict" name="district" required></select>
          </div>
          <div class="bg-int-f">
            <label for="bgIntWater">Water out there</label>
            <select id="bgIntWater" name="water" required></select>
          </div>
          <div class="bg-int-f">
            <label for="bgIntSize">How big a part</label>
            <select id="bgIntSize" name="size_note" required></select>
          </div>
          <div class="bg-int-f">
            <label for="bgIntTiming">Roughly when</label>
            <select id="bgIntTiming" name="timing" required></select>
          </div>
          <div class="bg-int-f is-wide">
            <label for="bgIntNote">Anything else we should know?</label>
            <textarea id="bgIntNote" name="garden_note" maxlength="600"></textarea>
            <span class="bg-int-hint" id="bgIntNoteHint">Optional.</span>
          </div>
        </div>

        <!-- CONDITIONAL · G1B TENURE RULE. Shown only when the homeowner told
             the Property Check they do not own the home. PlotNua never asks for
             a deed, a lease, a landlord's name or a landlord's contact detail:
             the homeowner's own sentence is evidence of what they said, not of
             the fact. -->
        <div class="bg-int-cond" id="bgIntCond" hidden>
          <div class="bg-int-tick">
            <input type="checkbox" id="bgIntPerm">
            <label for="bgIntPerm" id="bgIntPermLab"></label>
          </div>
          <p class="bg-int-hint" id="bgIntCondHint"></p>
        </div>

        <!-- The canonical consent control. ONE tick. The sentence itself
             carries the over-18 statement, so there is no second box asking
             the same thing twice. The text is written by JS from the frozen
             constant. -->
        <div class="bg-int-tick">
          <input type="checkbox" id="bgIntConsent" required>
          <label for="bgIntConsent"><span id="bgIntConsentText"></span></label>
        </div>

        <details class="bg-int-notice" id="bgIntNotice">
          <summary>Before you join the register &mdash; what we keep, and what we never ask for</summary>
          <div class="bg-int-noticebody">
            <p><strong>What we keep about you and your garden.</strong> Your first
              name, your email address, the district you chose, and what you told the
              Property Check about your garden &mdash; its size band, water, how
              someone would get in, and whether you own the property &mdash; and the
              result the Property Check produced from those answers. We also keep
              the administrative records needed to manage your registration, your
              consent and its status.</p>
            <p><strong>What we never ask for.</strong> Your address, your Eircode,
              your phone number, your surname, your age, photographs of your garden,
              or anything about your health. We don&rsquo;t collect them, so we
              can&rsquo;t hold them or lose them.</p>
            <p><strong>Why we keep it.</strong> So that we can tell you if someone
              nearby is looking for growing space.</p>
            <p><strong>Joining the register does not share your details with
              anyone.</strong> No other person sees your record. There is no public
              listing, no public map, no profile page, and no directory. Your record
              is private to PlotNua.</p>
            <p><strong>If we think there&rsquo;s a possible fit, we&rsquo;ll email you
              and ask.</strong> We&rsquo;ll describe the other person in general terms
              only &mdash; a district, how much space they&rsquo;re looking for,
              roughly when. No name, no email, no contact details.</p>
            <p><strong>Nothing is shared until you say yes.</strong> Your email
              address only reaches another person after you have said yes to that
              specific introduction. Saying yes once is yes to that one introduction
              and nothing more. If you don&rsquo;t reply, nothing happens.</p>
            <p><strong>We never sell your information</strong>, and we never pass it
              to anyone for advertising.</p>
            <p><strong>Leaving.</strong> Email hello@plotnua.ie and we will delete
              your record. There&rsquo;s nothing to cancel and no notice period.</p>
            <p><strong>How long we keep it.</strong> We keep your record for a maximum
              of 24 months. You can ask us to delete it at any time, and we may delete
              it sooner if it is no longer needed.</p>
            <p><strong>One thing we keep after deletion.</strong> When we delete your
              record we keep a separate note recording that you gave permission and
              that we honoured your request to remove it. That note holds a one-way
              digital fingerprint made from your email address, not the email address
              itself. It exists so we can prove we did what you asked.</p>
          </div>
        </details>

        <p class="bg-int-msg" id="bgIntMsg" hidden role="status" aria-live="polite"></p>

        <div class="bg-int-actions">
          <button class="pc-cta" type="submit" id="bgIntSend">Join the register</button>
          <button class="bg-int-cancel" type="button" id="bgIntCancel">Not now</button>
        </div>
      </form>

      <div class="bg-int-done" id="bgIntDone" hidden role="status" aria-live="polite">
        <h3 class="bg-int-done-h" id="bgIntDoneH"></h3>
        <div id="bgIntDoneBody"></div>
      </div>

      <p class="bg-int-note">PlotNua does not verify anybody&rsquo;s identity and has
        not met anyone on this register. Nothing is arranged through this page.</p>
    </section>
    <!-- PLOTNUA-G3-HTML-END -->

    <details class="bg-drawer">"""

# ------------------------------------------------------------- 3 · FUNNEL ----

FUNNEL_ANCHOR = "    saved:    function () { track('my_plot_save'); },"

FUNNEL = """    saved:    function () { track('my_plot_save'); },
    /* PLOTNUA-G3-FUNNEL-BEGIN · two anonymous G3 events, same contract as the
       three above: deduped once per page load, consent-gated by Cookiebot, and
       carrying the journey filename and nothing else. No answers, no district,
       no name, no email, no result. */
    interestOpened:    function () { track('garden_interest_opened'); },
    interestSubmitted: function () { track('garden_interest_submitted'); },
    /* PLOTNUA-G3-FUNNEL-END */"""

# ----------------------------------------------------------- 4 · JS MODULE ----

JS_ANCHOR = "  $('bgStart').addEventListener('click', function () { advance(); });"

JS = r"""  /* PLOTNUA-G3-INTEREST-BEGIN
   * ==========================================================================
   * G3 · HOMEOWNER EXPRESSION OF INTEREST
   *
   * THREE GATES, ALL OF WHICH MUST PASS BEFORE ANYTHING RENDERS
   *   1. INTEREST_PUBLIC. Shipped false. Nothing renders in production.
   *   2. ?interest=preview. The only way past (1).
   *   3. spare_corner !== 'no_garden'. Founder decision Q1: a homeowner who
   *      told the check there is not really a garden here is not invited to
   *      offer one.
   * When any gate fails the section is REMOVED FROM THE DOM, not merely
   * hidden, so there is no hidden form on a public page.
   *
   * INDEPENDENT OF SAVE TO MY PLOT. Founder decision Q2. This module reads no
   * part of the save band, PlotNuaJourneySave or localStorage. Grep proves it.
   *
   * IT PROMISES NOTHING. The G6 constraint is founder-set: registration
   * material must not promise or imply that joining guarantees a match or an
   * introduction. The offer says so explicitly, and so does the confirmation.
   *
   * THE CONSENT SENTENCE EXISTS ONCE. CONSENT_TEXT below is the G1B canonical
   * string, approved verbatim 7 October 2026, with ASCII apostrophes. It is
   * written into the visible label with textContent — never innerHTML, so no
   * entity can become a typographic quote — and the SAME constant is sent as
   * consent_text. The Worker hashes what arrives and compares it against its
   * own constant for privacy_version 2026-10-PHASE2-V2. If this page ever
   * drifts from the approved wording it stops working rather than recording a
   * consent to text nobody approved.
   * ======================================================================== */

  var INTEREST_PUBLIC = false;

  var INTEREST_ENDPOINT =
    'https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden';

  var CONSENT_TEXT =
    "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";

  /* Closed vocabularies, copied from the deployed Worker. A value this page
     cannot produce is a value the Worker would refuse, so the two lists are
     kept identical deliberately and a guard asserts it. */
  var INT_OPTS = {
    district: [
      ['', 'Choose a district'],
      ['raheny', 'Raheny'],
      ['killester', 'Killester'],
      ['donnycarney', 'Donnycarney'],
      ['artane', 'Artane'],
      ['elsewhere_in_dublin', 'Elsewhere in Dublin'],
      ['elsewhere_in_ireland', 'Elsewhere in Ireland']
    ],
    water: [
      ['', 'Choose one'],
      ['outside_tap', 'There is an outside tap'],
      ['from_the_house', 'Water would come from the house'],
      ['none', 'No water out there'],
      ['not_sure', 'I am not sure']
    ],
    size_note: [
      ['', 'Choose one'],
      ['very_small', 'Very small — a bed or two'],
      ['small', 'Small — a corner'],
      ['medium', 'Medium — a good patch'],
      ['large', 'Large'],
      ['not_sure', 'I am not sure']
    ],
    timing: [
      ['', 'Choose one'],
      ['this_season', 'This season'],
      ['within_3_months', 'Within three months'],
      ['next_season', 'Next season'],
      ['flexible', 'I am flexible']
    ]
  };

  var PILOT_DISTRICTS = ['raheny', 'killester', 'donnycarney', 'artane'];

  /* Seven states. closed is the absence of the section entirely. */
  var INT_STATE = 'closed';

  function intPreviewRequested() {
    try {
      return /(?:^|[?&])interest=preview(?:&|$)/.test(location.search);
    } catch (e) { return false; }
  }

  function intGatesPass() {
    if (!INTEREST_PUBLIC && !intPreviewRequested()) return false;
    /* Founder decision Q1. */
    if (answers.spare_corner === 'no_garden') return false;
    return true;
  }

  function intFill(sel, rows) {
    sel.innerHTML = '';
    rows.forEach(function (r) {
      var o = document.createElement('option');
      o.value = r[0];
      o.textContent = r[1];
      if (r[0] === '') { o.disabled = true; o.selected = true; }
      sel.appendChild(o);
    });
  }

  function intMsg(text, kind) {
    var m = $('bgIntMsg');
    if (!m) return;
    if (!text) { m.hidden = true; m.textContent = ''; return; }
    m.className = 'bg-int-msg ' + (kind === 'bad' ? 'is-bad' : 'is-flat');
    m.textContent = text;
    m.hidden = false;
  }

  /* Field-name to homeowner-facing name. The Worker's 400 carries the field it
     refused; this turns that into a sentence rather than exposing an internal
     identifier. An unknown key falls back to a sentence that names nothing. */
  var INT_FIELD_NAME = {
    first_name: 'your first name',
    email: 'your email address',
    district: 'the district',
    water: 'water out there',
    size_note: 'how big a part',
    timing: 'roughly when',
    inherited_tenure: 'whether you own the home',
    over_18: 'the confirmation that you are over 18',
    consent_text: 'the permission wording',
    permission_confirmed: 'the owner’s permission',
    garden_note: 'what you told us about the owner knowing'
  };

  function intShow(which) {
    INT_STATE = which;
    var offer = $('bgIntOffer'), form = $('bgIntForm'), done = $('bgIntDone');
    offer.hidden = (which !== 'offer');
    form.hidden  = !(which === 'form' || which === 'sending');
    done.hidden  = !(which === 'received' || which === 'not_open' ||
                     which === 'unavailable');
    var send = $('bgIntSend');
    if (send) {
      send.disabled = (which === 'sending');
      send.textContent = (which === 'sending') ? 'Sending…'
                                               : 'Join the register';
    }
  }

  function intEndState(heading, paras) {
    $('bgIntDoneH').textContent = heading;
    var body = $('bgIntDoneBody');
    body.innerHTML = '';
    paras.forEach(function (t) {
      var p = document.createElement('p');
      p.className = 'bg-int-p';
      p.textContent = t;
      body.appendChild(p);
    });
  }

  /* STATE · not_open. FOUNDER-CORRECTED COPY, and the correction matters: the
     browser necessarily sends the request to the Worker before receiving 503
     not_open, so this must not claim nothing was sent. What is true is that
     nothing was STORED — the write switch stops the Worker before Airtable —
     and that the Property Check itself is untouched. */
  function intNotOpen() {
    intEndState('The register isn’t open yet', [
      'The register isn’t open yet. Your details haven’t been saved. ' +
      'Your Property Check is unchanged.',
      'Nothing is waiting on you. When the register opens, this is where it ' +
      'will happen.'
    ]);
    intShow('not_open');
  }

  function intUnavailable() {
    intEndState('That didn’t go through', [
      'Something went wrong between this page and PlotNua, and your details ' +
      'haven’t been saved. Your Property Check is unchanged.',
      'Trying again in a minute is the whole fix. If it keeps happening, ' +
      'hello@plotnua.ie reaches a person.'
    ]);
    intShow('unavailable');
  }

  function intReceived(district) {
    var out = [
      'We have your first name, your email and what you told us about the ' +
      'corner. Nobody else can see it.',
      'This is a register, not a match. If somebody nearby is looking, we ' +
      'will email you and ask first. We may never find anybody near you.'
    ];
    if (PILOT_DISTRICTS.indexOf(district) === -1) {
      out.push('We are starting in a small part of Dublin 5, so it may be a ' +
               'while before there is anybody near you at all. You are on the ' +
               'register either way.');
    }
    out.push('To come off it, email hello@plotnua.ie. There is nothing to ' +
             'cancel and no notice period.');
    intEndState('You’re on the register', out);
    intShow('received');
  }

  /* The tenure rule, rendered. The wording is the homeowner's own statement,
     never a document: PlotNua asks for neither and stores neither. */
  function intPaintTenure() {
    var cond = $('bgIntCond');
    var tenure = answers.tenure;
    if (tenure === 'rent' || tenure === 'buying') {
      var who = (tenure === 'rent') ? 'your landlord or the owner'
                                    : 'the current owner';
      $('bgIntPermLab').textContent =
        'I have asked ' + who + ', and they know and have agreed.';
      $('bgIntCondHint').textContent =
        'You told the Property Check you do not own this home, so somebody ' +
        'else has to agree. We do not ask for a deed, a lease, or ' + who +
        '’s name or contact details, and we would not store them. Please ' +
        'say in your own words below how you know they are happy with it.';
      $('bgIntNoteHint').textContent =
        'Please tell us here, in your own words, that ' + who + ' knows and ' +
        'has agreed. At least twenty characters.';
      cond.hidden = false;
    } else {
      cond.hidden = true;
      $('bgIntNoteHint').textContent = 'Optional.';
    }
  }

  function intPayload() {
    var body = {
      first_name: $('bgIntName').value,
      email: $('bgIntEmail').value,
      district: $('bgIntDistrict').value,
      water: $('bgIntWater').value,
      size_note: $('bgIntSize').value,
      timing: $('bgIntTiming').value,
      over_18: $('bgIntConsent').checked === true,
      consent_text: CONSENT_TEXT,
      source: 'garden_interest',
      /* INHERITED FROM THE PROPERTY CHECK, not re-asked. These are the four
         answers the homeowner already gave this page. inherited_tenure is the
         one the Worker requires; the other three are context the register is
         allowed to hold. */
      inherited_tenure: answers.tenure || '',
      inherited_spare_corner: answers.spare_corner || '',
      inherited_way_in: answers.way_in || '',
      inherited_your_own_use: answers.your_own_use || ''
    };
    var note = $('bgIntNote').value;
    if (note) body.garden_note = note;
    if (answers.tenure && answers.tenure !== 'own') {
      body.permission_confirmed = $('bgIntPerm').checked === true;
    }
    /* The result KEY, never the result prose — the same rule the save
       component applies, and for the same reason: a stored paragraph would
       keep asserting something PlotNua may have stopped standing over. */
    if (lastEval) {
      var k = (lastEval.kind === 'early_exit')
        ? lastEval.exit.headline
        : (lastEval.results && lastEval.results[0] ? lastEval.results[0].key : '');
      if (k) body.inherited_result_key = k;
    }
    return body;
  }

  /* Local checks only to spare a round trip. The Worker is the authority and
     refuses on its own terms regardless of what passes here. */
  function intLocalProblem() {
    if (!$('bgIntName').value.trim()) return 'first_name';
    var e = $('bgIntEmail').value.trim();
    if (!e || e.indexOf('@') < 1 || e.indexOf('.') < 0) return 'email';
    if (!$('bgIntDistrict').value) return 'district';
    if (!$('bgIntWater').value) return 'water';
    if (!$('bgIntSize').value) return 'size_note';
    if (!$('bgIntTiming').value) return 'timing';
    if (!$('bgIntConsent').checked) return 'over_18';
    if (answers.tenure && answers.tenure !== 'own') {
      if (!$('bgIntPerm').checked) return 'permission_confirmed';
      if ($('bgIntNote').value.trim().length < 20) return 'garden_note';
    }
    return null;
  }

  function intSubmit(ev) {
    ev.preventDefault();
    if (INT_STATE === 'sending') return;

    var bad = intLocalProblem();
    if (bad) {
      intMsg('We still need ' + (INT_FIELD_NAME[bad] || 'one more thing') +
             '.', 'bad');
      return;
    }
    intMsg('', null);
    intShow('sending');

    var body = intPayload();
    try {
      if (window.PlotNuaFunnel && window.PlotNuaFunnel.interestSubmitted) {
        window.PlotNuaFunnel.interestSubmitted();
      }
    } catch (e) {}

    fetch(INTEREST_ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (j) { return { s: r.status, j: j }; },
                           function () { return { s: r.status, j: null }; });
    }).then(function (res) {
      var state = res.j && res.j.state;
      if (res.s === 200 && state === 'received') {
        intReceived(body.district);
        return;
      }
      if (res.s === 503 && state === 'not_open') { intNotOpen(); return; }
      if (res.s === 400 && state === 'refused') {
        intShow('form');
        var f = res.j && res.j.field;
        intMsg('PlotNua could not accept that: ' +
               (INT_FIELD_NAME[f] || 'one of the answers') +
               '. Nothing has been saved.', 'bad');
        return;
      }
      intUnavailable();
    }).catch(function () {
      intUnavailable();
    });
  }

  /* THE ENTRY POINT, called from reveal() after mountSave(). It is called on
     every reveal, including a re-reveal after Back, so it must be idempotent
     and must re-read answers each time. */
  function interestOffer() {
    var sec = $('bgInterest');
    if (!sec) return;

    if (!intGatesPass()) {
      /* REMOVED, not hidden. A public page carries no dormant form. */
      if (sec.parentNode) sec.parentNode.removeChild(sec);
      INT_STATE = 'closed';
      return;
    }

    sec.hidden = false;
    if (!INTEREST_PUBLIC) $('bgIntPrev').hidden = false;

    if (sec.getAttribute('data-g3-wired') === '1') {
      /* Already wired. Only the tenure-dependent copy can have changed. */
      if (INT_STATE === 'offer' || INT_STATE === 'form') intPaintTenure();
      return;
    }
    sec.setAttribute('data-g3-wired', '1');

    intFill($('bgIntDistrict'), INT_OPTS.district);
    intFill($('bgIntWater'), INT_OPTS.water);
    intFill($('bgIntSize'), INT_OPTS.size_note);
    intFill($('bgIntTiming'), INT_OPTS.timing);

    /* textContent, from the single canonical constant. Not innerHTML. */
    $('bgIntConsentText').textContent = CONSENT_TEXT;

    $('bgIntOpen').addEventListener('click', function () {
      intPaintTenure();
      intMsg('', null);
      intShow('form');
      try {
        if (window.PlotNuaFunnel && window.PlotNuaFunnel.interestOpened) {
          window.PlotNuaFunnel.interestOpened();
        }
      } catch (e) {}
      try { $('bgIntName').focus(); } catch (e) {}
    });

    $('bgIntCancel').addEventListener('click', function () {
      intMsg('', null);
      intShow('offer');
    });

    $('bgIntForm').addEventListener('submit', intSubmit);

    intShow('offer');
  }
  /* PLOTNUA-G3-INTEREST-END */

  $('bgStart').addEventListener('click', function () { advance(); });"""

# ------------------------------------------------------------- 5 · THE CALL ----

CALL_ANCHOR = "    mountSave();\n    show('bgReveal');"

CALL = """    mountSave();
    /* PLOTNUA-G3-CALL-BEGIN · G3 runs AFTER the save band is mounted and is
       independent of it: interestOffer() reads no part of the save contract.
       Called on every reveal so the gates and the tenure copy are re-evaluated
       whenever the answers change. */
    interestOffer();
    /* PLOTNUA-G3-CALL-END */
    show('bgReveal');"""


# ------------------------------------------------------------------ driver ----

INSERTS = [
    ("CSS",    CSS_ANCHOR,    CSS),
    ("HTML",   HTML_ANCHOR,   HTML),
    ("FUNNEL", FUNNEL_ANCHOR, FUNNEL),
    ("JS",     JS_ANCHOR,     JS),
    ("CALL",   CALL_ANCHOR,   CALL),
]

MARKERS = [
    "PLOTNUA-G3-CSS-BEGIN", "PLOTNUA-G3-HTML-BEGIN",
    "PLOTNUA-G3-FUNNEL-BEGIN", "PLOTNUA-G3-INTEREST-BEGIN",
    "PLOTNUA-G3-CALL-BEGIN",
]

# Regions this builder must leave byte-identical. Proven after the write.
FROZEN = [
    ("engine", "/* PLOTNUA-DISC025-ENGINE-BEGIN */",
               "/* PLOTNUA-DISC025-ENGINE-END */"),
    ("save",   "/* PLOTNUA-JOURNEY-SAVE-BEGIN */",
               "/* PLOTNUA-JOURNEY-SAVE-END */"),
]


def strip_comments(text):
    """Remove /* ... */ and <!-- ... --> and // line comments.

    Deliberately crude: it is used only to decide whether a NAME appears in
    executable text, so over-removal is safe (it can only make the guard
    stricter about what counts as code) while under-removal is not.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif text.startswith("<!--", i):
            j = text.find("-->", i + 4)
            i = n if j < 0 else j + 3
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def region(text, begin, end):
    i = text.index(begin)
    j = text.index(end) + len(end)
    return text[i:j]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def main():
    check = "--check" in sys.argv

    if not TARGET.exists():
        die("target not found: %s" % TARGET)
    src = TARGET.read_text(encoding="utf-8")
    before_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()

    print("  TARGET  %s" % TARGET.name)
    print("  BEFORE  %d bytes  sha256 %s" % (len(src.encode("utf-8")),
                                             before_sha[:16]))
    print("  CONSENT sha256 %s" % CONSENT_SHA[:16])
    print()

    # --- idempotence -------------------------------------------------------
    for m in MARKERS:
        if m in src:
            die("G3 marker already present: %s. This builder is not "
                "re-runnable over its own output." % m)

    # --- anchor guards: exactly once, every one of them --------------------
    print("  ANCHOR GUARDS")
    for name, anchor, _ in INSERTS:
        n = src.count(anchor)
        print("    %-7s occurrences=%d" % (name, n))
        if n != 1:
            die("anchor %s occurs %d times, expected exactly 1" % (name, n))

    # --- the frozen regions, captured before -------------------------------
    frozen_before = {}
    for name, b, e in FROZEN:
        if b not in src or e not in src:
            die("frozen region markers missing: %s" % name)
        r = region(src, b, e)
        frozen_before[name] = hashlib.sha256(r.encode("utf-8")).hexdigest()
        print("    frozen %-7s %d chars  sha256 %s"
              % (name, len(r), frozen_before[name][:16]))

    # --- the consent sentence must survive verbatim into the JS -----------
    if CONSENT not in JS:
        die("the canonical consent sentence is not present verbatim in the "
            "inserted JS")
    if JS.count(CONSENT) != 1:
        die("the canonical consent sentence appears %d times in the inserted "
            "JS; it must exist exactly once" % JS.count(CONSENT))
    if "’" in CONSENT:
        die("the canonical consent sentence contains a typographic apostrophe")

    # --- the inserted code must not read the save contract ----------------
    #
    # TESTED ON CODE, NOT ON MENTIONS. The first version of this guard matched
    # the raw text and fired on PlotNua's OWN DENIAL — the comment that says
    # this module reads no part of PlotNuaJourneySave. That is precisely the
    # failure class the DISC-025 certified contract records as designed out
    # ("six guards originally fired on PlotNua's own denials"), so the guard
    # is applied to the EXECUTABLE text with comments stripped, and a second
    # guard below asserts the denial is still there to be read.
    code = strip_comments(JS) + strip_comments(HTML) + strip_comments(CALL)
    for forbidden in ("PlotNuaJourneySave", "localStorage", "bgSave",
                      "sessionStorage"):
        if forbidden in code:
            die("inserted G3 CODE references %s; founder decision Q2 makes "
                "interest and Save independent" % forbidden)

    # The denial must survive, or a later reader has no way to know the
    # independence was deliberate rather than accidental.
    if "Founder decision Q2. This module reads no" not in JS:
        die("the Q2 independence denial is missing from the inserted JS")

    # --- the inserted copy must not promise a match -----------------------
    #
    # G6 constraint, founder-set: registration material must not promise or
    # imply that joining the register guarantees a match or an introduction.
    # Tested on COPY with comments stripped, for the same reason as the guard
    # above: the first version fired on the comment that states the constraint.
    low = strip_comments(HTML + JS).lower()
    for phrase in ("we will match you", "you will be matched",
                   "guarantees a match", "guarantee a match",
                   "we'll find you someone", "we will find you someone",
                   "we'll find someone", "we will find someone"):
        if phrase in low:
            die("inserted copy promises a match: %r" % phrase)

    # And the denial must be made positively, in homeowner-facing copy, in
    # both the offer and the confirmation. An absence of a promise is not the
    # same as a statement that there is none.
    if "Joining the register is not a match" not in HTML:
        die("the offer does not state that joining guarantees no match")
    if "This is a register, not a match" not in JS:
        die("the confirmation does not state that this is not a match")

    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    # --- apply --------------------------------------------------------------
    out = src
    for name, anchor, repl in INSERTS:
        if out.count(anchor) != 1:
            die("anchor %s no longer unique after an earlier insertion" % name)
        out = out.replace(anchor, repl, 1)

    after_sha = hashlib.sha256(out.encode("utf-8")).hexdigest()

    # --- prove the frozen regions survived ---------------------------------
    print("\n  FROZEN REGION PROOF")
    for name, b, e in FROZEN:
        r = region(out, b, e)
        sha = hashlib.sha256(r.encode("utf-8")).hexdigest()
        ok = (sha == frozen_before[name])
        print("    %-7s %s  %s" % (name, "IDENTICAL" if ok else "CHANGED",
                                   sha[:16]))
        if not ok:
            die("frozen region %s changed" % name)

    # --- prove every marker landed exactly once ----------------------------
    print("\n  MARKER PROOF")
    for m in MARKERS:
        n = out.count(m)
        print("    %-26s %d" % (m, n))
        if n != 1:
            die("marker %s landed %d times" % (m, n))

    TARGET.write_text(out, encoding="utf-8")

    print("\n  AFTER   %d bytes  sha256 %s" % (len(out.encode("utf-8")),
                                               after_sha[:16]))
    print("  DELTA   +%d bytes" % (len(out.encode("utf-8")) -
                                   len(src.encode("utf-8"))))
    print("  WRITTEN %s" % TARGET.name)
    print("\n  INTEREST_PUBLIC = false. The section is removed from the DOM "
          "on load\n  unless ?interest=preview is present.")


if __name__ == "__main__":
    main()
