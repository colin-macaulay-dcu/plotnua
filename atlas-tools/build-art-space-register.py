#!/usr/bin/env python3
"""Place the Art Space Register — a private, CLOSED homeowner
expression-of-interest register — on the DISC-024 Open Your Home to Art
Property Check.

Founder approval for BUILD: 13 October 2026. Ships CLOSED (INTEREST_PUBLIC =
false). Expressions of interest only: no matching, introductions, bookings,
payments, automatic emails or promises of income. Technical reference: the
Borrowed Garden G3 register, which this builder never touches.

Writes ONE file: disc024-open-your-home-to-art.html. Four bounded insertions:
  1. a scoped stylesheet block at the end of the page's own <style>;
  2. the register section inside #hoReveal, after the My Plot save band;
  3. ONE call at the end of reveal(), after the save band is mounted, passing
     only the three answers the form pre-fills (space, level, money);
  4. the register script, as its own <script> before </body>.

GUARDS
  R1  the rest of the page is byte-identical to git HEAD (questions, outcomes,
      engine, save band, save keys, journey exit — everything)
  R2  ships closed: INTEREST_PUBLIC is false. Opening is refused unless
      privacy.html carries the Art Space Register section (it does not yet)
  R3  the consent sentence on the page equals the Worker's, character for
      character, and equals the founder-approved text
  R4  the page's vocabularies equal the Worker's (county, ways, space, money)
  R5  the payload keys are exactly the Worker's ALLOWED_KEYS; the honeypot is
      never among them
  R6  no field for surname, address, Eircode, town, phone, photograph, tenure
      or artwork value; no file or tel input
  R7  the founder-approved invitation, heading and CTA are present verbatim;
      the assurances are present; no affirmative promise words
  R8  scope: no studio, residency, workshop, class or general creative use
  R9  the honeypot is present, off-screen, aria-hidden, out of the tab order
  R10 no tenure question and no read of answers.tenure
  R11 the mount call passes only space, level and money
  R12 the register script reads no My Plot / localStorage / save contract and
      calls only the art Worker endpoint — never the garden one
  R13 journey exit, save band and Garden Owner Register files are untouched

Usage:
  python3 atlas-tools/build-art-space-register.py --apply
  python3 atlas-tools/build-art-space-register.py --check
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE_NAME = "disc024-open-your-home-to-art.html"
PAGE = ROOT / PAGE_NAME
WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
PRIVACY = ROOT / "privacy.html"

INTEREST_PUBLIC = False          # founder decision: ships CLOSED
ENDPOINT = "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/host"
CONSENT = ("I'm over 18 and agree that PlotNua may keep my registration details and contact me about "
           "the Open Your Home to Art pilot. I understand I can withdraw my consent at any time.")

INVITATION = [
    "Imagine an original artwork displayed in your living room, a spare room becoming a temporary "
    "exhibition space, or an artist&rsquo;s work finding a new audience through your home.",
    "PlotNua is exploring whether Irish homeowners would be interested in offering space for "
    "artists&rsquo; finished work.",
    "You could simply display a piece privately, offer somewhere to store it, or potentially welcome "
    "visitors by arrangement. It&rsquo;s entirely up to you.",
    "Would you be interested in hearing more?",
    "Register your interest and help us explore whether this idea could work in Ireland.",
    "There&rsquo;s no commitment, no payment and no matching service operating at this stage. Your "
    "details remain private, and nothing will be arranged without your agreement.",
]
# Founder-approved invitation (13 Oct 2026), pinned so an edit to the list above
# cannot also edit the thing it is checked against.
INVITATION_SHA256 = "f704a644935f5fd8ad2f228598671617ac87d2f016b2a3ed4ae474433caa031a"
COUNTIES_ROI = ["carlow", "cavan", "clare", "cork", "donegal", "dublin", "galway", "kerry", "kildare",
                "kilkenny", "laois", "leitrim", "limerick", "longford", "louth", "mayo", "meath", "monaghan",
                "offaly", "roscommon", "sligo", "tipperary", "waterford", "westmeath", "wexford", "wicklow"]
HEADING = "Could your home become a home for art?"
CTA = "Register my interest"

M = {
    "css_b": "/* PLOTNUA-ART-REGISTER-CSS-BEGIN",
    "css_e": "/* PLOTNUA-ART-REGISTER-CSS-END */\n",
    "html_b": "    <!-- PLOTNUA-ART-REGISTER-HTML-BEGIN",
    "html_e": "    <!-- PLOTNUA-ART-REGISTER-HTML-END -->\n",
    "call_b": "    /* PLOTNUA-ART-REGISTER-CALL-BEGIN",
    "call_e": "    /* PLOTNUA-ART-REGISTER-CALL-END */\n",
    "js_b": "<script>\n/* PLOTNUA-ART-REGISTER-JS-BEGIN",
    "js_e": "/* PLOTNUA-ART-REGISTER-JS-END */\n</script>\n",
}
A_CSS = "  .ho-partbody{ margin:0; }\n</style>\n</head>"
A_HTML = ("          <a class=\"pc-savelink\" id=\"hoSaveLink\" href=\"your-plot.html?myplot=1\" hidden>View in My Plot "
          "<span class=\"pc-arrow\" aria-hidden=\"true\">&rarr;</span></a>\n        </div>\n      </div>\n    </div>\n")
A_CALL = "    hoPaintClose();\n    hoUpdatePlotPill();\n"
A_CALL_NEXT = "  }\n\n  $('hoStart').addEventListener('click', function(){ advance(); });"
A_JS = "</body>\n</html>"

CSS = """/* PLOTNUA-ART-REGISTER-CSS-BEGIN · Art Space Register (DISC-024), founder-approved
   for build 13 Oct 2026. Generated by atlas-tools/build-art-space-register.py.
   Prefix asr- (no other journey uses it). Same field as the save band: --stone. */
  .asr{margin:0 0 30px;padding:30px 28px;background:var(--stone);
    border-top:2px solid rgba(79,107,74,.34);}
  .asr[hidden]{display:none;}
  .asr-h{font-family:'Fraunces',Georgia,serif;font-weight:400;
    font-size:clamp(20px,2.4vw,25px);line-height:1.3;color:var(--ink);margin:0 0 14px;max-width:26ch;}
  .asr-h:focus{outline:none;}
  .asr-p{margin:0 0 12px;font-size:15px;line-height:1.65;color:var(--body);max-width:68ch;}
  .asr-assure{margin:16px 0 0;padding:14px 0 0;border-top:1px solid rgba(31,59,46,.14);
    font-size:14.5px;line-height:1.65;color:var(--ink);max-width:68ch;}
  .asr-cta{margin:20px 0 0;}
  .asr-prev{margin:0 0 16px;font-family:'Work Sans',sans-serif;font-size:10px;font-weight:500;
    letter-spacing:.2em;text-transform:uppercase;color:#6E5639;
    border:1px solid rgba(139,111,78,.4);border-radius:20px;padding:5px 12px;display:inline-block;}
  .asr-prev[hidden]{display:none;}
  .asr-form{margin:22px 0 0;}
  .asr-form[hidden],.asr-done[hidden],#asrOffer[hidden]{display:none;}
  .asr-privline{margin:0 0 18px;font-size:14px;line-height:1.6;color:var(--muted);}
  .asr-grid{display:grid;gap:18px;}
  @media(min-width:760px){ .asr-grid{grid-template-columns:repeat(2,1fr);} }
  .asr-f{display:grid;gap:6px;align-content:start;}
  .asr-f.is-wide{grid-column:1/-1;}
  .asr-f > label,.asr-ways legend{font-family:'Work Sans',sans-serif;font-size:11px;font-weight:500;
    letter-spacing:.14em;text-transform:uppercase;color:var(--ink);}
  .asr-opt{font-weight:400;letter-spacing:.06em;text-transform:none;color:var(--muted);}
  .asr-hint{font-size:13px;line-height:1.5;color:var(--muted);}
  .asr-f input[type=text],.asr-f input[type=email],.asr-f select,.asr-f textarea{
    width:100%;font-family:'Work Sans',sans-serif;font-size:16px;line-height:1.5;color:var(--ink);
    background:var(--paper);border:1px solid var(--rule);border-radius:3px;padding:11px 12px;
    -webkit-appearance:none;appearance:none;}
  .asr-f textarea{min-height:92px;resize:vertical;}
  .asr-f input:focus,.asr-f select:focus,.asr-f textarea:focus{
    outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent);}
  .asr-f [aria-invalid=true]{border-color:#7A3B2E;}
  .asr-ways{margin:0;padding:0;border:0;min-width:0;}
  .asr-ways legend{padding:0;margin:0 0 10px;}
  .asr-ways .asr-tick{margin:8px 0 0;}
  .asr-tick{display:grid;grid-template-columns:20px 1fr;gap:4px 11px;align-items:start;margin:20px 0 0;}
  .asr-tick input[type=checkbox]{width:18px;height:18px;margin:3px 0 0;accent-color:var(--accent);}
  .asr-tick label{font-size:14.5px;line-height:1.6;color:var(--body);cursor:pointer;}
  .asr-notice{margin:18px 0 0;border-top:1px solid rgba(31,59,46,.14);}
  .asr-notice summary{cursor:pointer;padding:14px 0 12px;font-family:'Work Sans',sans-serif;
    font-size:13.5px;color:var(--soft);}
  .asr-notice summary:hover,.asr-notice[open] summary{color:var(--ink);}
  .asr-noticebody{font-size:14px;line-height:1.7;color:var(--body);padding:0 0 8px;max-width:68ch;}
  .asr-noticebody p{margin:0 0 12px;}
  .asr-noticebody strong{font-weight:500;color:var(--ink);}
  .asr-actions{margin:24px 0 0;display:flex;flex-wrap:wrap;gap:12px;align-items:center;}
  .asr-cancel{background:none;border:0;padding:0;cursor:pointer;font-family:'Work Sans',sans-serif;
    font-size:13.5px;color:var(--soft);text-decoration:underline;text-underline-offset:3px;}
  .asr-cancel:hover{color:var(--ink);}
  .asr-cancel:focus-visible{outline:2px solid var(--accent);outline-offset:3px;}
  .asr-msg{margin:18px 0 0;font-size:14.5px;line-height:1.65;}
  .asr-msg[hidden]{display:none;}
  .asr-msg.is-bad{color:#7A3B2E;}
  .asr-done-h{font-family:'Fraunces',Georgia,serif;font-weight:400;font-size:clamp(19px,2.2vw,23px);
    line-height:1.3;color:var(--ink);margin:0 0 12px;}
  .asr-done-h:focus{outline:none;}
  .asr-note{margin:18px 0 0;padding:14px 0 0;border-top:1px solid rgba(31,59,46,.12);
    font-size:13px;line-height:1.6;color:var(--muted);}
  .asr-hp{position:absolute !important;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;}
  @media(max-width:560px){ .asr{padding:26px 20px;} }
"""

NOTICE = [
    ("What we keep.",
     "Your first name, your email address, your county, and which of storing, displaying, opening "
     "to visitors or helping to sell you would consider &mdash; and, if you choose to tell us, the "
     "kind of space, whether money is part of it for you, and anything you add in the note. We "
     "also keep a record that you gave your consent, which version of our privacy notice applied, "
     "and when you registered."),
    ("From your Property Check.",
     "Nothing is sent automatically. The form starts with three of your answers filled in, and only "
     "what is in the form when you press the button is sent. Your other answers and your result "
     "are not."),
    ("What we never ask for.",
     "Your address, your Eircode, your town, your phone number, your surname, your age, "
     "photographs of your home, or the value of anything in it."),
    ("Why we keep it.",
     "So that we can contact you about the Open Your Home to Art pilot &mdash; for example to ask a "
     "few questions about what you would consider, or to let you know if the pilot develops."),
    ("Your details stay private.",
     "Registering does not share them with anyone. There is no public listing, no map, no profile "
     "and no directory, no artist sees your record, and nothing will be arranged without your "
     "agreement. We never sell your information or pass it to anyone for advertising."),
    ("Leaving.",
     "You can withdraw your consent at any time. Email hello@plotnua.ie and we will delete your "
     "record. There is nothing to cancel and no notice period."),
    ("How long we keep it.",
     "A maximum of 24 months. You can ask us to delete it at any time, and we may delete it sooner "
     "if it is no longer needed."),
    ("One thing we keep after deletion.",
     "A separate note that you gave permission and that we honoured your request to remove it. It "
     "holds a one-way digital fingerprint made from your email address, not the address itself, so "
     "that we can show we did what you asked."),
]


def html_section():
    paras = "\n".join('        <p class="asr-p">%s</p>' % p for p in INVITATION[:-1])
    notice = "\n".join('          <p><strong>%s</strong> %s</p>' % (h, b) for h, b in NOTICE)
    return (
        M["html_b"] + "\n"
        "         ART SPACE REGISTER · homeowner expression of interest (DISC-024). Founder-approved for\n"
        "         build 13 Oct 2026. SHIPPED CLOSED: hidden here and REMOVED FROM THE DOM on reveal\n"
        "         unless the register is public or ?interest=preview is present. Generated by\n"
        "         atlas-tools/build-art-space-register.py — do not hand-edit. -->\n"
        '    <section class="asr" id="asrSection" hidden aria-labelledby="asrH">\n'
        '      <p class="asr-prev" id="asrPrev" hidden>Private preview &middot; not public</p>\n'
        '      <h2 class="asr-h" id="asrH" tabindex="-1">%s</h2>\n' % HEADING +
        '      <div id="asrOffer">\n' + paras + "\n"
        '        <p class="asr-assure">%s</p>\n' % INVITATION[-1] +
        '        <p class="asr-cta"><button class="pc-cta" type="button" id="asrOpen">%s</button></p>\n' % CTA +
        '      </div>\n'
        '      <form class="asr-form" id="asrForm" hidden novalidate>\n'
        '        <p class="asr-privline">A first name, an email address and a county. No surname, no address, no Eircode, no phone number.</p>\n'
        '        <div class="asr-grid">\n'
        '          <div class="asr-f"><label for="asrName">First name</label>\n'
        '            <input type="text" id="asrName" name="first_name" autocomplete="given-name" maxlength="40" required></div>\n'
        '          <div class="asr-f"><label for="asrEmail">Email address</label>\n'
        '            <input type="email" id="asrEmail" name="email" autocomplete="email" maxlength="120" required></div>\n'
        '          <div class="asr-f"><label for="asrCounty">County</label>\n'
        '            <select id="asrCounty" name="county" required></select></div>\n'
        '          <div class="asr-f is-wide">\n'
        '            <fieldset class="asr-ways" id="asrWays"><legend>Which would you consider?</legend>\n'
        '              <span class="asr-hint" id="asrWaysHint">Tick any that apply.</span>\n'
        '              <div id="asrWaysList"></div>\n'
        '            </fieldset></div>\n'
        '          <div class="asr-f"><label for="asrSpace">What kind of space? <span class="asr-opt">(optional)</span></label>\n'
        '            <select id="asrSpace" name="space"></select></div>\n'
        '          <div class="asr-f"><label for="asrMoney">Is money part of it for you? <span class="asr-opt">(optional)</span></label>\n'
        '            <select id="asrMoney" name="money" aria-describedby="asrMoneyHint"></select>\n'
        '            <span class="asr-hint" id="asrMoneyHint">This helps us understand what people expect. It isn&rsquo;t an offer.</span></div>\n'
        '          <div class="asr-f is-wide"><label for="asrNote">Anything else we should know? <span class="asr-opt">(optional)</span></label>\n'
        '            <textarea id="asrNote" name="host_note" maxlength="400" aria-describedby="asrNoteHint"></textarea>\n'
        '            <span class="asr-hint" id="asrNoteHint">Please don&rsquo;t include your address, Eircode, phone number, or details of anything valuable in your home.</span></div>\n'
        '        </div>\n'
        '        <div class="asr-hp" aria-hidden="true"><label for="asrWebsite">Leave this field empty</label>\n'
        '          <input type="text" id="asrWebsite" name="website" tabindex="-1" autocomplete="off" value=""></div>\n'
        '        <div class="asr-tick"><input type="checkbox" id="asrConsent" required>\n'
        '          <label for="asrConsent"><span id="asrConsentText"></span></label></div>\n'
        '        <details class="asr-notice" id="asrNotice">\n'
        '          <summary>Before you register &mdash; what we keep, and what we never ask for</summary>\n'
        '          <div class="asr-noticebody">\n' + notice + "\n"
        '          </div>\n'
        '        </details>\n'
        '        <p class="asr-msg" id="asrMsg" hidden role="status" aria-live="polite"></p>\n'
        '        <div class="asr-actions">\n'
        '          <button class="pc-cta" type="submit" id="asrSend">%s</button>\n' % CTA +
        '          <button class="asr-cancel" type="button" id="asrCancel">Not now</button>\n'
        '        </div>\n'
        '      </form>\n'
        '      <div class="asr-done" id="asrDone" hidden role="status" aria-live="polite">\n'
        '        <h3 class="asr-done-h" id="asrDoneH" tabindex="-1"></h3>\n'
        '        <div id="asrDoneBody"></div>\n'
        '      </div>\n'
        '      <p class="asr-note">PlotNua does not verify anybody&rsquo;s identity and has not met anyone on this register. Nothing is arranged through this page.</p>\n'
        '    </section>\n' + M["html_e"])


CALL = (M["call_b"] + " · Art Space Register, after the save band and independent of it.\n"
        "       Only the three answers the form pre-fills are passed; nothing else from the check. */\n"
        "    if (window.PlotNuaArtRegister) {\n"
        "      window.PlotNuaArtRegister.mount({ space: answers.space, level: answers.level, money: answers.money });\n"
        "    }\n" + M["call_e"])


def js_block():
    return M["js_b"] + """
 * ==========================================================================
 * ART SPACE REGISTER · DISC-024 · homeowner expression of interest
 * Founder-approved for build, 13 October 2026. Generated by
 * atlas-tools/build-art-space-register.py — do not hand-edit.
 *
 * SHIPS CLOSED. Two gates: INTEREST_PUBLIC (false) or ?interest=preview. When
 * neither passes the section is REMOVED from the DOM — a public page carries
 * no dormant form. Offered to every result; the check's answers never decide
 * eligibility.
 *
 * IT PROMISES NOTHING. Expressions of interest only: no matching,
 * introductions, bookings, payments, automatic emails or income.
 *
 * INDEPENDENT. Reads no part of My Plot, the save band or localStorage, and
 * calls one endpoint only: the separate Art Space Register Worker.
 *
 * THE CONSENT SENTENCE EXISTS ONCE, written into the label with textContent
 * and sent verbatim as consent_text; the Worker hashes and compares it.
 * ======================================================================== */
window.PlotNuaArtRegister = (function () {
  'use strict';

  var INTEREST_PUBLIC = %(public)s;
  var ENDPOINT = %(endpoint)s;
  var CONSENT_TEXT = %(consent)s;

  /* Closed vocabularies — identical to the Worker's (guard R4). */
  var OPTS = {
    county: %(county)s,
    ways: [
      ['store', 'Storing finished work'],
      ['display', 'Displaying work where you live'],
      ['open', 'Opening the space to visitors, by arrangement'],
      ['help_sell', 'Helping work find a buyer']
    ],
    space: [
      ['', 'Choose one (optional)'],
      ['a_wall', 'A wall in a room I use'],
      ['a_room', 'A spare room, or one I rarely use'],
      ['dry_store', 'Storage only (an attic, a garage, under the stairs)'],
      ['not_sure', 'I\\u2019m not sure yet']
    ],
    money: [
      ['', 'Choose one (optional)'],
      ['no_money', 'No, I\\u2019d be happy to help'],
      ['fee_for_space', 'Something for the space'],
      ['share_if_sells', 'A share if a piece sells'],
      ['not_decided', 'I haven\\u2019t decided']
    ]
  };

  /* Property Check answer -> form value. Pre-fill only; the homeowner sees and
     can change every value before anything is sent. */
  var FROM_CHECK = {
    space: { a_wall: 'a_wall', a_room: 'a_room', dry_store: 'dry_store', not_sure_space: 'not_sure' },
    level: { store: 'store', display: 'display', open: 'open', help_sell: 'help_sell' },
    money: { no_money: 'no_money', fee_for_space: 'fee_for_space', share_if_sells: 'share_if_sells',
             not_decided_money: 'not_decided' }
  };

  var FIELD_NAME = {
    first_name: 'your first name', email: 'your email address', county: 'your county',
    ways: 'at least one thing you would consider', space: 'the kind of space',
    money: 'whether money is part of it', host_note: 'the note',
    over_18: 'the confirmation that you are over 18 and agree', consent_text: 'the permission wording'
  };
  var FIELD_EL = { first_name: 'asrName', email: 'asrEmail', county: 'asrCounty', ways: 'asrWays',
                   space: 'asrSpace', money: 'asrMoney', host_note: 'asrNote', over_18: 'asrConsent' };

  var STATE = 'closed';
  function $(id) { return document.getElementById(id); }

  function previewRequested() {
    try { return /(?:^|[?&])interest=preview(?:&|$)/.test(location.search); } catch (e) { return false; }
  }

  function fill(sel, rows, chosen) {
    sel.innerHTML = '';
    rows.forEach(function (r) {
      var o = document.createElement('option');
      o.value = r[0];
      o.textContent = r[1];
      sel.appendChild(o);
    });
    sel.value = chosen || '';
  }

  function msg(text) {
    var m = $('asrMsg');
    if (!text) { m.hidden = true; m.textContent = ''; return; }
    m.className = 'asr-msg is-bad';
    m.textContent = text;
    m.hidden = false;
  }

  function clearInvalid() {
    Object.keys(FIELD_EL).forEach(function (k) {
      var el = $(FIELD_EL[k]);
      if (el) el.removeAttribute('aria-invalid');
    });
  }

  function flag(field) {
    msg('We still need ' + (FIELD_NAME[field] || 'one more thing') + '.');
    var el = $(FIELD_EL[field]);
    if (!el) return;
    el.setAttribute('aria-invalid', 'true');
    var focusEl = field === 'ways' ? el.querySelector('input') : el;
    try { focusEl.focus(); } catch (e) {}
  }

  function show(which) {
    STATE = which;
    $('asrOffer').hidden = (which !== 'offer');
    $('asrForm').hidden = !(which === 'form' || which === 'sending');
    $('asrDone').hidden = !(which === 'received' || which === 'not_open' || which === 'unavailable');
    var send = $('asrSend');
    send.disabled = (which === 'sending');
    send.textContent = (which === 'sending') ? 'Sending\\u2026' : %(cta)s;
  }

  function endState(which, heading, paras) {
    $('asrDoneH').textContent = heading;
    var body = $('asrDoneBody');
    body.innerHTML = '';
    paras.forEach(function (t) {
      var p = document.createElement('p');
      p.className = 'asr-p';
      p.textContent = t;
      body.appendChild(p);
    });
    show(which);
    try { $('asrDoneH').focus(); } catch (e) {}
  }

  function received() {
    endState('received', 'You\\u2019re on the register', [
      'We have your first name, your email, your county and what you told us about the space. ' +
      'Nobody else can see it.',
      'This is a register of interest, not a matching service. No artist will contact you, and ' +
      'nothing will be arranged without your agreement. If the pilot develops, we will email you.',
      'To come off it, email hello@plotnua.ie. There is nothing to cancel and no notice period.'
    ]);
  }

  function notOpen() {
    endState('not_open', 'The register isn\\u2019t open yet', [
      'Your details haven\\u2019t been saved. Your Property Check is unchanged.',
      'Nothing is waiting on you. When the register opens, this is where it will happen.'
    ]);
  }

  function unavailable() {
    endState('unavailable', 'That didn\\u2019t go through', [
      'Something went wrong between this page and PlotNua, and your details haven\\u2019t been ' +
      'saved. Your Property Check is unchanged.',
      'Trying again in a minute is the whole fix. If it keeps happening, hello@plotnua.ie reaches a person.'
    ]);
  }

  function chosenWays() {
    var out = [];
    OPTS.ways.forEach(function (w) {
      var box = $('asrWay_' + w[0]);
      if (box && box.checked) out.push(w[0]);
    });
    return out;
  }

  /* The payload. These keys are the Worker's ALLOWED_KEYS exactly (guard R5).
     Optional fields are sent only when the homeowner chose a value. */
  function payload() {
    var body = {
      first_name: $('asrName').value,
      email: $('asrEmail').value,
      county: $('asrCounty').value,
      ways: chosenWays(),
      over_18: $('asrConsent').checked === true,
      consent_text: CONSENT_TEXT,
      source: 'property_check'
    };
    if ($('asrSpace').value) body.space = $('asrSpace').value;
    if ($('asrMoney').value) body.money = $('asrMoney').value;
    if ($('asrNote').value.trim()) body.host_note = $('asrNote').value;
    return body;
  }

  function localProblem() {
    if (!$('asrName').value.trim()) return 'first_name';
    var e = $('asrEmail').value.trim();
    if (!e || e.indexOf('@') < 1 || e.lastIndexOf('.') < e.indexOf('@')) return 'email';
    if (!$('asrCounty').value) return 'county';
    if (!chosenWays().length) return 'ways';
    if (!$('asrConsent').checked) return 'over_18';
    return null;
  }

  function submit(ev) {
    ev.preventDefault();
    if (STATE === 'sending') return;
    clearInvalid();
    var bad = localProblem();
    if (bad) { flag(bad); return; }
    msg('');
    /* Honeypot: checked after ordinary validation. Filled -> nothing is sent,
       and the truthful 'didn't go through' state is shown. */
    if ($('asrWebsite').value !== '') { unavailable(); return; }
    show('sending');
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload())
    }).then(function (r) {
      return r.json().then(function (j) { return { s: r.status, j: j }; },
                           function () { return { s: r.status, j: null }; });
    }).then(function (res) {
      var state = res.j && res.j.state;
      if (res.s === 200 && state === 'received') { received(); return; }
      if (res.s === 503 && state === 'not_open') { notOpen(); return; }
      if (res.s === 400 && state === 'refused') {
        show('form');
        var f = res.j && res.j.field;
        msg('PlotNua could not accept that: ' + (FIELD_NAME[f] || 'one of the answers') +
            '. Nothing has been saved.');
        return;
      }
      unavailable();
    }).catch(function () { unavailable(); });
  }

  function seed(answers) {
    answers = answers || {};
    fill($('asrSpace'), OPTS.space, FROM_CHECK.space[answers.space]);
    fill($('asrMoney'), OPTS.money, FROM_CHECK.money[answers.money]);
    var lvl = FROM_CHECK.level[answers.level];
    OPTS.ways.forEach(function (w) { $('asrWay_' + w[0]).checked = (w[0] === lvl); });
  }

  /* Called from reveal() on every reveal, after the save band. Idempotent. */
  function mount(answers) {
    var sec = $('asrSection');
    if (!sec) return;
    if (!INTEREST_PUBLIC && !previewRequested()) {
      if (sec.parentNode) sec.parentNode.removeChild(sec);
      STATE = 'closed';
      return;
    }
    sec.hidden = false;
    if (!INTEREST_PUBLIC) $('asrPrev').hidden = false;

    if (sec.getAttribute('data-asr-wired') === '1') {
      if (STATE === 'offer') seed(answers);
      return;
    }
    sec.setAttribute('data-asr-wired', '1');

    fill($('asrCounty'), OPTS.county, '');
    var list = $('asrWaysList');
    OPTS.ways.forEach(function (w) {
      var row = document.createElement('div');
      row.className = 'asr-tick';
      var box = document.createElement('input');
      box.type = 'checkbox';
      box.id = 'asrWay_' + w[0];
      box.value = w[0];
      var lab = document.createElement('label');
      lab.htmlFor = box.id;
      lab.textContent = w[1];
      row.appendChild(box);
      row.appendChild(lab);
      list.appendChild(row);
    });
    $('asrConsentText').textContent = CONSENT_TEXT;
    seed(answers);

    $('asrOpen').addEventListener('click', function () {
      msg('');
      clearInvalid();
      show('form');
      try { $('asrName').focus(); } catch (e) {}
    });
    $('asrCancel').addEventListener('click', function () {
      msg('');
      show('offer');
      try { $('asrOpen').focus(); } catch (e) {}
    });
    $('asrForm').addEventListener('submit', submit);
    /* A correction clears the message it answered; nothing is re-validated here. */
    $('asrForm').addEventListener('change', function () { if (STATE === 'form') { msg(''); clearInvalid(); } });
    show('offer');
  }

  /* Closed: remove the section at load too, so the public page never carries a
     dormant form, not even before a result. */
  function removeIfClosed() {
    if (INTEREST_PUBLIC || previewRequested()) return;
    var sec = $('asrSection');
    if (sec && sec.parentNode) sec.parentNode.removeChild(sec);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', removeIfClosed);
  else removeIfClosed();

  return { mount: mount };
})();
""" % {
        "public": "true" if INTEREST_PUBLIC else "false",
        "endpoint": json.dumps(ENDPOINT),
        "consent": json.dumps(CONSENT),
        "cta": json.dumps(CTA),
        "county": json.dumps([["", "Choose a county"]] + [[c, c.capitalize()] for c in COUNTIES_ROI],
                             ensure_ascii=False),
    } + M["js_e"]


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def worker_src():
    return WORKER.read_text(encoding="utf-8")


def worker_vocab():
    src = worker_src()
    m = re.search(r"const V = \{([\s\S]*?)\n\};", src)
    out = {}
    for key, body in re.findall(r"(\w+): \[([^\]]*)\]", m.group(1)):
        out[key] = re.findall(r"'([a-z_]+)'", body)
    return out


def worker_consent():
    m = re.search(r'const CONSENT_TEXT =\s*"([^"]*)";', worker_src())
    return m.group(1) if m else None


def worker_allowed():
    m = re.search(r"const ALLOWED_KEYS = Object\.freeze\(\[([\s\S]*?)\]\)", worker_src())
    return sorted(re.findall(r"'([a-z_0-9]+)'", m.group(1)))


def strip(html):
    for b, e in (("css_b", "css_e"), ("html_b", "html_e"), ("call_b", "call_e"), ("js_b", "js_e")):
        html = re.sub(re.escape(M[b]) + r"[\s\S]*?" + re.escape(M[e]), "", html)
    return html


def build(current):
    html = strip(current)
    for a, label in ((A_CSS, "head style end"), (A_HTML, "save band end"), (A_JS, "</body>")):
        if html.count(a) != 1:
            die("R1 anchor not found exactly once: " + label)
    if html.count(A_CALL + A_CALL_NEXT) != 1:
        die("R1 anchor not found exactly once: end of reveal()")
    html = html.replace(A_CSS, A_CSS.replace("</style>", CSS + M["css_e"] + "</style>"))
    html = html.replace(A_HTML, A_HTML + html_section())
    html = html.replace(A_CALL + A_CALL_NEXT, A_CALL + CALL + A_CALL_NEXT)
    html = html.replace(A_JS, js_block() + A_JS)
    return html


def region(html, b, e):
    i = html.index(M[b]); j = html.index(M[e], i)
    return html[i:j + len(M[e])]


def visible_text(fragment):
    t = re.sub(r"<!--[\s\S]*?-->", " ", fragment)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def guards(html):
    sec = region(html, "html_b", "html_e")
    js = region(html, "js_b", "js_e")
    call = region(html, "call_b", "call_e")
    code_js = re.sub(r"/\*[\s\S]*?\*/", "", js)
    # R1
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + PAGE_NAME],
                              capture_output=True, text=True, check=True).stdout
        if strip(head) != strip(html):
            die("R1 the rest of the page differs from git HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  R1 skipped: git HEAD not available")
    # R2
    if code_js.count("var INTEREST_PUBLIC = false;") != 1 or "INTEREST_PUBLIC = true" in code_js:
        if 'id="art-space-register"' not in PRIVACY.read_text(encoding="utf-8"):
            die("R2 the register may not open: privacy.html has no Art Space Register section")
        die("R2 opening is a separate, founder-authorised step; this builder ships the register closed")
    # R3
    if worker_consent() != CONSENT:
        die("R3 the Worker's consent sentence differs from the founder-approved text")
    if json.dumps(CONSENT) not in js:
        die("R3 the page's consent sentence differs from the founder-approved text")
    if "asrConsentText').textContent = CONSENT_TEXT" not in js:
        die("R3 the consent label is not written from the canonical constant with textContent")
    # R4
    wv = worker_vocab()
    page_ways = re.findall(r"\['(store|display|open|help_sell)', '", js)
    if page_ways != wv["ways"]:
        die("R4 ways differ from the Worker: %r" % page_ways)
    for key in ("space", "money"):
        block = re.search(key + r": \[\n([\s\S]*?)\n    \]", js).group(1)
        vals = [v for v in re.findall(r"\['([a-z_]*)', '", block) if v]
        if vals != wv[key]:
            die("R4 %s differs from the Worker: %r" % (key, vals))
    county_vals = [c for c, _ in json.loads(re.search(r"county: (\[\[.*?\]\]),", js).group(1)) if c]
    if county_vals != wv["county"] or wv["county"] != COUNTIES_ROI:
        die("R4 county list is not exactly the 26 counties of the Republic, on both page and Worker")
    # R5
    pf = re.search(r"function payload\(\) \{([\s\S]*?)\n  \}\n", js).group(1)
    pb = re.search(r"var body = \{([\s\S]*?)\};", pf).group(1)
    keys = re.findall(r"^\s*(\w+):", pb, re.M) + re.findall(r"body\.(\w+) =", pf)
    if sorted(set(keys)) != worker_allowed():
        die("R5 payload keys %r differ from the Worker's ALLOWED_KEYS %r" % (sorted(set(keys)), worker_allowed()))
    if "website" in keys:
        die("R5 the honeypot is in the payload")
    # R6
    for bad in re.findall(r'name="([^"]+)"', sec):
        if re.search(r"surname|last_name|address|eircode|town|phone|photo|image|tenure|value|price", bad, re.I):
            die("R6 forbidden field: " + bad)
    if re.search(r'type="(file|tel|date|number)"', sec):
        die("R6 a file, tel, date or number input is present")
    # R7
    if HEADING not in sec or sec.count('id="asrOpen">%s<' % CTA) != 1:
        die("R7 the approved heading or CTA is missing")
    import hashlib
    if hashlib.sha256("\n".join(INVITATION).encode("utf-8")).hexdigest() != INVITATION_SHA256:
        die("R7 the invitation differs from the founder-approved wording")
    for p in INVITATION:
        if p not in sec:
            die("R7 approved invitation text missing: " + p[:50])
    strings = [a or b for a, b in re.findall(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"", code_js)]
    vis = visible_text(sec).lower() + " " + visible_text(" ".join(strings)).lower()
    for need in ("no matching service", "nothing will be arranged without your agreement", "no payment",
                 "not a matching service"):
        if need not in vis:
            die("R7 assurance missing: " + need)
    bad = re.search(r"\b(guarantee[ds]?|earn(ings)?|income|bookings?|book a|matched|we will introduce|"
                    r"you will be paid|you'll be paid|get paid|commission)\b", vis)
    if bad:
        die("R7 promise wording in the register: %r" % bad.group(0))
    # R8
    scope = re.search(r"\b(studio|residenc\w*|workshops?|classes|rehears\w*|make work|making work|"
                      r"creative activit\w*)\b", vis)
    if scope:
        die("R8 out-of-scope wording: %r" % scope.group(0))
    # R9
    if not re.search(r'<div class="asr-hp" aria-hidden="true">[\s\S]*?tabindex="-1"', sec):
        die("R9 honeypot missing, visible or in the tab order")
    # R10
    if re.search(r"tenure|rent|landlord|owner of", visible_text(sec), re.I) or "answers.tenure" in html:
        die("R10 a tenure question or read is present")
    # R11
    if not re.search(r"mount\(\{ space: answers\.space, level: answers\.level, money: answers\.money \}\)", call) \
            or len(re.findall(r"answers\.\w+", call)) != 3:
        die("R11 the mount call passes more than space, level and money")
    # R12
    for bad in ("localStorage", "sessionStorage", "PlotNuaJourneySave", "plotnua.myplot", "document.cookie",
                "gtag", "dataLayer", "garden-register", "XMLHttpRequest", "sendBeacon"):
        if bad in code_js:
            die("R12 the register script references %r" % bad)
    if code_js.count("fetch(") != 1 or ENDPOINT not in js:
        die("R12 the register script must call only the art Worker endpoint")
    # R13
    if (html.count("PLOTNUA JOURNEY EXIT v1") != 3 or html.count("journeyId: 'disc024-open-your-home-to-art'") != 1
            or 'id="hoSave"' not in html):
        die("R13 journey exit or save band changed")
    try:
        d = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", "HEAD", "--",
                            "disc025-borrowed-garden-check.html", "worker/garden-register", "privacy.html"],
                           capture_output=True, text=True, check=True).stdout.strip()
        if d:
            die("R13 Garden Owner Register or privacy files changed: " + d)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def main(argv):
    if "--apply" not in argv and "--check" not in argv:
        print(__doc__); sys.exit(1)
    current = PAGE.read_text(encoding="utf-8")
    html = build(current)
    guards(html)
    if "--check" in argv:
        if html != current:
            print("CHECK FAILED: %s is out of date; run --apply" % PAGE_NAME); sys.exit(1)
        print("%s: Art Space Register present, CLOSED · CHECK OK — R1-R13 pass" % PAGE_NAME); return
    PAGE.write_text(html, encoding="utf-8")
    print("%s: Art Space Register placed, CLOSED · APPLIED — R1-R13 pass" % PAGE_NAME)


if __name__ == "__main__":
    main(sys.argv[1:])
