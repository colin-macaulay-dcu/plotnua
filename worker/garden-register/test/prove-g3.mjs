/* G3 · DISC-025 BORROWED GARDEN EXPRESSION OF INTEREST — GUARD SUITE
 * ===========================================================================
 * Runs the REAL page in jsdom, with fetch stubbed, and asserts the shipped
 * behaviour. Nothing here reaches the network, Airtable, or the deployed
 * Worker: the payload the page builds is captured and inspected locally. The
 * deployed round trip is a separate script (prove-g3-deployed.mjs), because a
 * local DOM cannot prove what a remote Worker answers and must not pretend to.
 *
 * WHAT THIS SUITE IS FOR
 *   1. The three visibility gates, including that a closed page carries NO
 *      dormant form in the DOM at all.
 *   2. The consent string: byte-exact, rendered by textContent, and sent.
 *   3. Every field, with the closed vocabularies matching the Worker's.
 *   4. The G1B tenure rule, driven through the real form.
 *   5. All seven UI states, including the founder-corrected closed-state copy.
 *   6. Independence from Save to My Plot (founder decision Q2).
 *   7. The G6 constraint: no promise of a match.
 *   8. The two funnel events.
 *
 *   node test/prove-g3.mjs
 * ========================================================================= */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

/* fileURLToPath, not .pathname: the repository path contains a space ("04
   Deploy") and .pathname hands back the percent-encoded form, which fs
   cannot open. */
const PAGE = path.resolve(process.argv[2] || findPage());

/* PAGE RESOLUTION, LOCATION-INDEPENDENT.
   This suite used to resolve the journey page at a FIXED relative depth
   ('../../plotnua-github/...'), which was correct only while it sat in a
   sibling directory of the repo. Bringing the Worker under version control at
   plotnua-github/worker/garden-register/ changed that depth and would have
   broken it silently. Candidates are tried in order and the first that exists
   wins, so the suite runs from either location and survives the next move.
   It throws rather than guessing if the page cannot be found. */
function findPage() {
  const tries = [
    '../../../disc025-borrowed-garden-check.html',          // in-repo: worker/garden-register/test/
    '../../plotnua-github/disc025-borrowed-garden-check.html' // legacy sibling directory
  ];
  for (const rel of tries) {
    const p = fileURLToPath(new URL(rel, import.meta.url));
    if (fs.existsSync(p)) return p;
  }
  throw new Error('cannot locate disc025-borrowed-garden-check.html; tried: ' +
                  tries.join(', '));
}

/* The G1B canonical garden consent sentence, 7 October 2026. Written out here
   independently of the page, so a page that drifts fails rather than agrees
   with itself. ASCII apostrophes. */
const CONSENT =
  "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";

const ENDPOINT =
  'https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden';

const CLOSED_COPY =
  'The register isn’t open yet. Your details haven’t been saved. ' +
  'Your Property Check is unchanged.';

/* The deployed Worker's closed vocabularies, copied from src/index.js. */
const WORKER_V = {
  district: ['raheny', 'killester', 'donnycarney', 'artane',
             'elsewhere_in_dublin', 'elsewhere_in_ireland'],
  space_band: ['very_small', 'small', 'medium', 'large', 'not_sure'],
  timing: ['this_season', 'within_3_months', 'next_season', 'flexible'],
  water: ['outside_tap', 'from_the_house', 'none', 'not_sure']
};

let pass = 0, fail = 0;
const results = [];
function check(name, cond, detail) {
  if (cond) { pass++; results.push(['PASS', name, '']); }
  else { fail++; results.push(['FAIL', name, detail === undefined ? '' : String(detail)]); }
}

const HTML = fs.readFileSync(PAGE, 'utf8');

/* EVERY TOP-LEVEL BLOCK RUNS INSIDE scope(). A mutated page can legitimately
   lack a node this suite reads, and the suite must then FAIL that block —
   not throw. A throw prints no report at all, so the mutation harness would
   see no [FAIL] lines and score the mutation as "nothing was caught", which
   is the exact opposite of the truth. Measured: before this wrapper, the
   mutation that made interest depend on a prior Save crashed the runner and
   was recorded as a blind spot. */
async function scope(fn) {
  try { await fn(); }
  catch (e) {
    fail++;
    results.push(['FAIL', 'BLOCK-' + (++blockN) + ' threw', e.message]);
  }
}
let blockN = 0;


/* ------------------------------------------------------------------ setup --
 * One helper builds a page in a chosen state: a query string, a set of
 * answers, and a stubbed fetch whose reply we choose. It returns the window
 * plus everything the assertions need.
 */
function boot({ search = '', answers = null, reply = null } = {}) {
  const sent = [];
  const dom = new JSDOM(HTML, {
    url: 'https://plotnua.ie/disc025-borrowed-garden-check.html' + search,
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    beforeParse(w) {
      /* No Cookiebot, no network.
         ANALYTICS ARE READ FROM dataLayer, NOT FROM A gtag STUB. A stub
         installed here is overwritten: the page's own head script declares
         `function gtag(){dataLayer.push(arguments);}`, and a hoisted function
         declaration wins. Measured, not assumed — an earlier version of this
         suite stubbed gtag, saw an empty array, and two assertions passed
         VACUOUSLY as a result. dataLayer is the real sink, so it is what the
         assertions read. */
      w.fetch = function (url, opts) {
        sent.push({ url: String(url), opts });
        if (!reply) return Promise.reject(new TypeError('network stubbed off'));
        return Promise.resolve({
          status: reply.status,
          json: () => Promise.resolve(reply.body)
        });
      };
      w.scrollTo = function () {};
    }
  });
  const w = dom.window;
  const $ = (id) => w.document.getElementById(id);
  if (answers) w.__disc025.answer(answers);
  /* Only the 'event' pushes, as [name, params]. */
  const events = () => Array.from(w.dataLayer || [])
    .map((a) => Array.from(a))
    .filter((a) => a[0] === 'event')
    .map((a) => [a[1], a[2]]);
  return { w, $, sent, dom, events };
}

const OWN_WORKABLE = {
  tenure: 'own',
  spare_corner: 'yes_a_clear_corner',
  way_in: 'side_or_rear_access',
  your_own_use: 'now_and_then'
};
const RENT_WORKABLE = Object.assign({}, OWN_WORKABLE, { tenure: 'rent' });
const BUYING_WORKABLE = Object.assign({}, OWN_WORKABLE, { tenure: 'buying' });
const NO_GARDEN = {
  tenure: 'own',
  spare_corner: 'no_garden',
  way_in: 'side_or_rear_access',
  your_own_use: 'now_and_then'
};

const tick = () => new Promise((r) => setTimeout(r, 0));

/* Fill the form with values that the Worker would accept. */
function fillValid($, { district = 'raheny' } = {}) {
  $('bgIntName').value = 'Testy';
  $('bgIntEmail').value = 'g3probe@example.com';
  $('bgIntDistrict').value = district;
  $('bgIntWater').value = 'outside_tap';
  $('bgIntSize').value = 'small';
  $('bgIntTiming').value = 'flexible';
  $('bgIntConsent').checked = true;
}

/* ================================================== 1 · THE THREE GATES == */

await scope(async () => {
  /* G1 · SHIPPED CLOSED. No query string, a perfectly eligible homeowner.
     The section must be GONE from the DOM, not merely hidden: a hidden form
     on a public page is still a form on a public page. */
  const { w, $ } = boot({ answers: OWN_WORKABLE });
  check('G1 shipped closed: the section is REMOVED from the DOM',
    $('bgInterest') === null, 'section still present');
  check('G1b no interest form anywhere in the closed DOM',
    $('bgIntForm') === null && $('bgIntConsent') === null &&
    $('bgIntOpen') === null);
  check('G1c the closed DOM contains no endpoint-bearing form control',
    !/id="bgIntEmail"/.test(w.document.body.innerHTML));
  /* And the result itself must be untouched by the removal. */
  check('G1d the result still rendered with the section removed',
    /\S/.test($('bgRevealH').textContent) &&
    $('bgReveal').classList.contains('is-on'));
  check('G1e Save to My Plot survives the removal',
    $('bgSave') !== null && $('bgSaveHead') !== null);
  w.close();
});

await scope(async () => {
  /* G2 · the preview gate is the only way in.
     Each assertion checks the node exists before reading it. A mutated page
     that removes the section must make these FAIL, not crash the runner —
     a crash produces no [FAIL] lines and would be scored as "nothing was
     caught", which is the opposite of the truth. */
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  check('G2 ?interest=preview reveals the section',
    $('bgInterest') !== null && $('bgInterest').hidden === false);
  check('G2b the preview ribbon says it is not public',
    !!$('bgIntPrev') && $('bgIntPrev').hidden === false &&
    /not public/i.test($('bgIntPrev').textContent));
  check('G2c the offer is the first state, not the form',
    !!$('bgIntOffer') && !!$('bgIntForm') &&
    $('bgIntOffer').hidden === false && $('bgIntForm').hidden === true);
  w.close();
});

await scope(async () => {
  /* G2d · a near-miss query string must NOT open the gate. */
  for (const q of ['?interest=previews', '?interest=PREVIEW', '?interest=1',
                   '?preview=interest', '?x=interest%3Dpreview']) {
    const { w, $ } = boot({ search: q, answers: OWN_WORKABLE });
    check('G2d gate stays shut for ' + q, $('bgInterest') === null);
    w.close();
  }
  /* ...but a legitimate second parameter must not break it. */
  for (const q of ['?start=1&interest=preview', '?interest=preview&start=1']) {
    const { w, $ } = boot({ search: q, answers: OWN_WORKABLE });
    check('G2e gate opens for ' + q, $('bgInterest') !== null);
    w.close();
  }
});

await scope(async () => {
  /* G3 · FOUNDER DECISION Q1. spare_corner === 'no_garden' suppresses the
     invitation even in preview. A homeowner who has just told PlotNua there
     is not really a garden here is not asked to offer one. */
  const { w, $ } = boot({ search: '?interest=preview', answers: NO_GARDEN });
  check('G3 no_garden suppresses the invitation even in preview',
    $('bgInterest') === null);
  check('G3b the early-exit result still renders',
    /\S/.test($('bgRevealH').textContent));
  w.close();
});

await scope(async () => {
  /* G3c · every OTHER spare_corner value is still invited, so the
     suppression is specific rather than a blanket. */
  for (const v of ['yes_a_clear_corner', 'maybe_part_of_the_lawn',
                   'no_it_is_all_in_use', 'not_sure']) {
    const { w, $ } = boot({
      search: '?interest=preview',
      answers: Object.assign({}, OWN_WORKABLE, { spare_corner: v })
    });
    check('G3c spare_corner=' + v + ' is still invited',
      $('bgInterest') !== null);
    w.close();
  }
});

/* ================================================= 2 · THE CONSENT TEXT == */

await scope(async () => {
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  const span = $('bgIntConsentText');
  check('G4 the consent label text is byte-exact',
    span.textContent === CONSENT,
    JSON.stringify(span.textContent));
  check('G4b the consent label carries NO child markup (textContent, not HTML)',
    span.children.length === 0 && span.innerHTML === span.textContent
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'));
  check('G4c no typographic apostrophe reached the rendered consent',
    !span.textContent.includes('’'));
  check('G4d the consent sentence states the over-18 confirmation',
    /over 18/.test(span.textContent));
  check('G4e one tick serves both: there is no second over-18 checkbox',
    w.document.querySelectorAll('#bgIntForm input[type=checkbox]').length === 2);
  /* 2 = the consent tick + the conditional permission tick. */
  check('G4f the sha256 of the rendered label matches the Worker constant',
    crypto.createHash('sha256').update(span.textContent).digest('hex') ===
    crypto.createHash('sha256').update(CONSENT).digest('hex'));
  w.close();
});

/* =============================================== 3 · FIELDS AND VOCABULARY */

await scope(async () => {
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  const vals = (id) => Array.from($(id).options)
    .map((o) => o.value).filter((v) => v !== '');
  check('G5 district options are exactly the Worker vocabulary',
    JSON.stringify(vals('bgIntDistrict')) === JSON.stringify(WORKER_V.district),
    vals('bgIntDistrict').join(','));
  check('G5b water options are exactly the Worker vocabulary',
    JSON.stringify(vals('bgIntWater')) === JSON.stringify(WORKER_V.water),
    vals('bgIntWater').join(','));
  check('G5c size options are exactly the Worker space_band vocabulary',
    JSON.stringify(vals('bgIntSize')) === JSON.stringify(WORKER_V.space_band),
    vals('bgIntSize').join(','));
  check('G5d timing options are exactly the Worker vocabulary',
    JSON.stringify(vals('bgIntTiming')) === JSON.stringify(WORKER_V.timing),
    vals('bgIntTiming').join(','));
  check('G5e every select opens on a disabled placeholder',
    ['bgIntDistrict', 'bgIntWater', 'bgIntSize', 'bgIntTiming']
      .every((id) => $(id).options[0].disabled && $(id).value === ''));

  /* THE FIELDS PLOTNUA PROMISED NEVER TO ASK FOR. The notice says so; this
     asserts the FORM agrees, which is the part that could silently drift.
     ASSERTED ON FIELD NAMES AND LABELS, NOT ON A BARE SUBSTRING. The first
     version of this guard matched "address" anywhere and fired on the
     legitimate label "Email address" — the same false-positive class as the
     builder's two comment-matching guards. The prohibited things are named
     precisely instead. */
  const labels = Array.from($('bgIntForm').querySelectorAll('label'))
    .map((l) => l.textContent.toLowerCase()).join(' | ');
  const names = Array.from($('bgIntForm').querySelectorAll('input,select,textarea'))
    .map((e) => (e.getAttribute('name') || '') + ' ' + (e.id || '')).join(' ')
    .toLowerCase();
  for (const [what, re] of [
    ['an Eircode',        /eircode/],
    ['a postal address',  /(postal|home|street|site)\s+address|address line|\baddr\b/],
    ['a surname',         /surname|last name|family name/],
    ['a phone number',    /phone|mobile|telephone/],
    ['a date of birth',   /date of birth|\bdob\b|birthday/],
    ['an exact age',      /\byour age\b|age in years/],
    ['a photograph',      /photo|image|picture|upload/],
    ['anything medical',  /health|medical|disab|condition/],
    ['the owner’s identity', /landlord(?!\s+or the owner)\s*(name|email|phone|number)|owner\s*(name|email|phone)/],
    ['a password',        /password|passcode/]
  ]) {
    check('G6 the form asks for ' + what + ' nowhere',
      !re.test(labels) && !re.test(names),
      re.test(labels) ? 'label: ' + labels : 'name: ' + names);
  }
  /* And the positive control: the one legitimate "address" IS the email. */
  check('G6pre the only address asked for is the email address',
    /email address/.test(labels) && names.includes('email'));
  check('G6b there is no file input anywhere (no photographs)',
    w.document.querySelectorAll('input[type=file]').length === 0);
  check('G6c there is no tel or date input',
    w.document.querySelectorAll('input[type=tel],input[type=date]').length === 0);
  w.close();
});

/* ============================================== 4 · THE G1B TENURE RULE == */

await scope(async () => {
  /* OWN · no conditional block, note optional. */
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  $('bgIntOpen').click();
  check('G7 own: the permission block stays hidden', $('bgIntCond').hidden === true);
  check('G7b own: the note is optional', /Optional/.test($('bgIntNoteHint').textContent));
  w.close();
});

/* G8 · THE PERMISSION BLOCK, NOW RENT-ONLY.
   `buying` was removed from this loop on 8 October 2026 under founder decision
   D-G5-1 = option 1. These five assertions encoded the implementation, which
   was stricter than FROZEN G1B §5: the contract makes `buying` storable with
   no permission and no statement. `buying` now has its own assertions (T1-T6)
   modelled on G7/G7b, the owner case. `rent` is unchanged. */
for (const [label, answers, who] of [
  ['rent', RENT_WORKABLE, 'your landlord or the owner']
]) { await scope(async () => {
  const { w, $ } = boot({ search: '?interest=preview', answers });
  $('bgIntOpen').click();
  check('G8 ' + label + ': the permission block is shown',
    $('bgIntCond').hidden === false);
  check('G8b ' + label + ': the tick names ' + who,
    $('bgIntPermLab').textContent.includes(who),
    $('bgIntPermLab').textContent);
  check('G8c ' + label + ': the note becomes required with a minimum length',
    /twenty characters/i.test($('bgIntNoteHint').textContent),
    $('bgIntNoteHint').textContent);
  /* PlotNua never asks for the document or the landlord's identity. */
  const condText = ($('bgIntCond').textContent + $('bgIntNoteHint').textContent);
  check('G8d ' + label + ': PlotNua says it does not want a deed or a lease',
    /do not ask for a deed, a lease/.test(condText), condText.slice(0, 120));
  check('G8e ' + label + ': no field asks for the owner’s name or contact',
    !/name="landlord/.test($('bgIntForm').innerHTML) &&
    !/id="bgIntLandlord/.test($('bgIntForm').innerHTML));
  w.close();
}); }

/* ============================ T1-T6 · BUYING, UNDER FROZEN G1B §5 ========
   G1B §5: `buying` is storable; permission_confirmed is NOT required merely to
   store it; garden_note is NOT required merely to store it. It remains
   non-promotable, which is a G7 decision and not a form control, so nothing
   here asserts a promotion path — T11 asserts the no-promise wording instead.
   Added 8 October 2026 under founder decision D-G5-1 = option 1. */
await scope(async () => {
  const { w, $ } = boot({ search: '?interest=preview', answers: BUYING_WORKABLE });
  $('bgIntOpen').click();
  check('T1 buying: the permission block is HIDDEN, as for an owner',
    $('bgIntCond').hidden === true);
  check('T2 buying: the note is optional, as for an owner',
    /Optional/.test($('bgIntNoteHint').textContent),
    $('bgIntNoteHint').textContent);
  check('T2b buying: no "somebody else has to agree" hint is shown',
    !/somebody else has to agree/.test($('bgIntCondHint').textContent),
    $('bgIntCondHint').textContent);
  w.close();
});

await scope(async () => {
  /* T3/T4 · a buying homeowner with NO tick and NO note can submit, and the
     payload carries permission_confirmed nowhere — absent, not false, the same
     shape G12b already requires of an owner. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: BUYING_WORKABLE });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('T3 buying with no tick and no note IS sent', sent.length === 1,
    JSON.stringify(sent));
  const body = sent.length ? JSON.parse(sent[0].opts.body) : {};
  check('T4 buying: permission_confirmed is ABSENT, not false',
    !('permission_confirmed' in body), JSON.stringify(Object.keys(body)));
  check('T4b buying: garden_note is absent when nothing was typed',
    !('garden_note' in body), JSON.stringify(Object.keys(body)));
  check('T4c buying: inherited_tenure is buying', body.inherited_tenure === 'buying');
  w.close();
});

await scope(async () => {
  /* T6 · the twenty-character minimum is a RENT rule. A short note from a
     buying homeowner is kept, not refused. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: BUYING_WORKABLE });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntNote').value = 'bought in May';          /* 13 chars, under the rent minimum */
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('T6 buying with a 13-character note IS sent', sent.length === 1,
    JSON.stringify(sent));
  check('T6b buying: the short note is carried as typed',
    sent.length && JSON.parse(sent[0].opts.body).garden_note === 'bought in May');
  w.close();
});

await scope(async () => {
  /* G9 · the tenure rule is enforced, driven through the real form: a
     non-owner with no tick cannot submit, and no request leaves the page. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: RENT_WORKABLE });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntPerm').checked = false;
  $('bgIntNote').value = 'The owner is fine with it, we spoke about it last week.';
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G9 rent with no permission tick: nothing is sent', sent.length === 0,
    JSON.stringify(sent));
  check('G9b rent with no permission tick: the page says what is missing',
    $('bgIntMsg').hidden === false &&
    /permission/i.test($('bgIntMsg').textContent),
    $('bgIntMsg').textContent);
  check('G9c the form stays open, so the homeowner can fix it',
    $('bgIntForm').hidden === false);
  w.close();
});

await scope(async () => {
  /* G9d · the tick without a statement is also refused. The G1B rule is
     BOTH, not either. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: RENT_WORKABLE });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntPerm').checked = true;
  $('bgIntNote').value = 'they said yes';     /* 13 chars, under the minimum */
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G9d rent with a tick but no real statement: nothing is sent',
    sent.length === 0, JSON.stringify(sent));
  check('G9e the page names the statement, not the tick',
    /owner knowing|told us/i.test($('bgIntMsg').textContent),
    $('bgIntMsg').textContent);
  w.close();
});

/* ==================================== 5 · THE PAYLOAD THE PAGE CONSTRUCTS */

await scope(async () => {
  const { w, $, sent } = boot({
    search: '?interest=preview',
    answers: OWN_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } }
  });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntNote').value = 'Happy to try a season and see how it goes.';
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();

  check('G10 exactly one request is made', sent.length === 1, sent.length);
  const req = sent[0];
  check('G10b it goes to the deployed garden route', req.url === ENDPOINT, req.url);
  check('G10c it is a POST with a JSON content type',
    req.opts.method === 'POST' &&
    /application\/json/.test(req.opts.headers['content-type']));
  const body = JSON.parse(req.opts.body);

  check('G11 consent_text is the canonical sentence, byte for byte',
    body.consent_text === CONSENT, JSON.stringify(body.consent_text));
  check('G11b over_18 is boolean true, not a string',
    body.over_18 === true, JSON.stringify(body.over_18));
  check('G11c source is garden_interest',
    body.source === 'garden_interest', body.source);
  check('G11d the four Property Check answers are inherited, not re-asked',
    body.inherited_tenure === 'own' &&
    body.inherited_spare_corner === 'yes_a_clear_corner' &&
    body.inherited_way_in === 'side_or_rear_access' &&
    body.inherited_your_own_use === 'now_and_then',
    JSON.stringify(body));
  check('G11e the result KEY is sent, never the result prose',
    body.inherited_result_key === 'ARRANGEMENT' &&
    !/workable|corner of your garden/i.test(JSON.stringify(body)),
    body.inherited_result_key);

  /* THE PROHIBITION LIST, ASSERTED ON THE REAL PAYLOAD. */
  const keys = Object.keys(body);
  for (const k of ['eircode', 'address', 'phone', 'surname', 'last_name',
                   'dob', 'age', 'lat', 'lng', 'coords', 'photo', 'health',
                   'landlord', 'landlord_name', 'password', 'ip',
                   'permission_confirmed']) {
    check('G12 the owner payload carries no ' + k, !keys.includes(k), k);
  }
  check('G12b permission_confirmed is absent for an owner (not false)',
    !('permission_confirmed' in body));
  check('G12c the payload has no key the Worker does not read',
    keys.every((k) => [
      'first_name', 'email', 'district', 'water', 'size_note', 'timing',
      'over_18', 'consent_text', 'source', 'garden_note',
      'permission_confirmed', 'inherited_tenure', 'inherited_spare_corner',
      'inherited_way_in', 'inherited_your_own_use', 'inherited_result_key',
      'check_saved_at'
    ].includes(k)), keys.join(','));
  w.close();
});

await scope(async () => {
  /* G13 · a non-owner's valid submission DOES carry permission_confirmed. */
  const { w, $, sent } = boot({
    search: '?interest=preview',
    answers: RENT_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } }
  });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntPerm').checked = true;
  $('bgIntNote').value = 'I asked the landlord last month and he is happy with it.';
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  const body = JSON.parse(sent[0].opts.body);
  check('G13 rent: permission_confirmed is true', body.permission_confirmed === true);
  check('G13b rent: the homeowner’s own sentence is sent as garden_note',
    /asked the landlord/.test(body.garden_note), body.garden_note);
  check('G13c rent: inherited_tenure is rent', body.inherited_tenure === 'rent');
  w.close();
});

/* ============================================== 6 · THE SEVEN UI STATES = */

await scope(async () => {
  /* STATE not_open · THE FOUNDER-CORRECTED COPY. The browser necessarily
     sends the request before receiving 503, so the page must not claim
     nothing was sent. */
  const { w, $ } = boot({
    search: '?interest=preview',
    answers: OWN_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } }
  });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  const txt = $('bgIntDone').textContent.replace(/\s+/g, ' ').trim();
  check('G14 not_open shows the founder-corrected sentence verbatim',
    txt.includes(CLOSED_COPY), txt.slice(0, 200));
  check('G14b not_open does NOT claim nothing was sent',
    !/nothing has been sent/i.test(txt) && !/nothing was sent/i.test(txt), txt);
  check('G14c not_open says the details were not SAVED',
    /haven’t been saved/.test(txt));
  check('G14d not_open says the Property Check is unchanged',
    /Property Check is unchanged/.test(txt));
  check('G14e not_open hides the form and the offer',
    $('bgIntForm').hidden === true && $('bgIntOffer').hidden === true &&
    $('bgIntDone').hidden === false);
  w.close();
});

await scope(async () => {
  /* STATE received. */
  const { w, $ } = boot({
    search: '?interest=preview',
    answers: OWN_WORKABLE,
    reply: { status: 200, body: { state: 'received' } }
  });
  $('bgIntOpen').click();
  fillValid($, { district: 'raheny' });
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  const txt = $('bgIntDone').textContent.replace(/\s+/g, ' ').trim();
  check('G15 received confirms the register, not a match',
    /register, not a match/.test(txt), txt.slice(0, 200));
  check('G15b received says we may never find anybody',
    /may never find anybody/.test(txt));
  check('G15c received gives the way off the register',
    /hello@plotnua\.ie/.test(txt) && /nothing to cancel/.test(txt));
  check('G15d received does not add the out-of-pilot line for Raheny',
    !/small part of Dublin 5/.test(txt));
  w.close();
});

await scope(async () => {
  /* G15e · an out-of-pilot district gets the honest extra line. */
  const { w, $ } = boot({
    search: '?interest=preview',
    answers: OWN_WORKABLE,
    reply: { status: 200, body: { state: 'received' } }
  });
  $('bgIntOpen').click();
  fillValid($, { district: 'elsewhere_in_ireland' });
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  check('G15e an out-of-pilot district is told the pilot is small',
    /small part of Dublin 5/.test($('bgIntDone').textContent));
  w.close();
});

await scope(async () => {
  /* STATE refused · a 400 names the field and keeps the form open. */
  const { w, $ } = boot({
    search: '?interest=preview',
    answers: OWN_WORKABLE,
    reply: { status: 400, body: { state: 'refused', field: 'email' } }
  });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  check('G16 refused keeps the form open', $('bgIntForm').hidden === false);
  check('G16b refused names the field in homeowner language',
    /your email address/.test($('bgIntMsg').textContent),
    $('bgIntMsg').textContent);
  check('G16c refused does not leak the internal field identifier',
    !/\bemail\b(?!\s+address)/.test($('bgIntMsg').textContent.replace('email address', 'EA')),
    $('bgIntMsg').textContent);
  check('G16d refused says nothing has been saved',
    /Nothing has been saved/.test($('bgIntMsg').textContent));
  check('G16e the send button is re-enabled so a fix can be submitted',
    $('bgIntSend').disabled === false);
  w.close();
});

await scope(async () => {
  /* STATE unavailable · network failure. */
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick(); await tick();
  const txt = $('bgIntDone').textContent.replace(/\s+/g, ' ').trim();
  check('G17 a network failure lands in the unavailable state',
    $('bgIntDone').hidden === false && /didn’t go through/.test(txt), txt.slice(0, 160));
  check('G17b unavailable says the details were not saved',
    /haven’t been saved/.test(txt));
  check('G17c unavailable says the Property Check is unchanged',
    /Property Check is unchanged/.test(txt));
  check('G17d unavailable gives a human route',
    /hello@plotnua\.ie/.test(txt));
  w.close();
});

await scope(async () => {
  /* STATE sending · and the double-submit guard. */
  let release;
  const held = new Promise((r) => { release = r; });
  const sent = [];
  const dom = new JSDOM(HTML, {
    url: 'https://plotnua.ie/disc025-borrowed-garden-check.html?interest=preview',
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.gtag = function () {};
      w.scrollTo = function () {};
      w.fetch = function (u, o) {
        sent.push(1);
        return held.then(() => ({ status: 503, json: () => Promise.resolve({ state: 'not_open' }) }));
      };
    }
  });
  const w = dom.window, $ = (id) => w.document.getElementById(id);
  w.__disc025.answer(OWN_WORKABLE);
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G18 sending disables the button', $('bgIntSend').disabled === true);
  check('G18b sending says so on the button',
    /Sending/.test($('bgIntSend').textContent), $('bgIntSend').textContent);
  /* A second submit while in flight must not fire a second request. */
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G18c a second submit while in flight sends nothing more',
    sent.length === 1, sent.length);
  release();
  await tick(); await tick();
  check('G18d the button is restored after the reply',
    /Join the register/.test($('bgIntSend').textContent));
  w.close();
});

await scope(async () => {
  /* STATE offer <-> form · "Not now" returns to the offer and clears the
     message, and nothing is sent by either transition. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  $('bgIntOpen').click();
  check('G19 opening shows the form', $('bgIntForm').hidden === false);
  $('bgIntCancel').click();
  check('G19b "Not now" returns to the offer',
    $('bgIntOffer').hidden === false && $('bgIntForm').hidden === true);
  check('G19c neither transition sends anything', sent.length === 0);
  w.close();
});

await scope(async () => {
  /* G20 · an empty form cannot be submitted, and the page says what is
     missing rather than failing silently. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  $('bgIntOpen').click();
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G20 an empty form sends nothing', sent.length === 0);
  check('G20b the page names the first missing field',
    /first name/i.test($('bgIntMsg').textContent), $('bgIntMsg').textContent);
  /* And each field in turn. */
  const order = [
    ['bgIntName', 'Testy', 'email address'],
    ['bgIntEmail', 'a@b.ie', 'district'],
    ['bgIntDistrict', 'artane', 'water'],
    ['bgIntWater', 'none', 'how big'],
    ['bgIntSize', 'small', 'roughly when']
  ];
  for (const [id, val, expectNext] of order) {
    $(id).value = val;
    $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
    await tick();
    check('G20c after filling ' + id + ' it asks for ' + expectNext,
      new RegExp(expectNext, 'i').test($('bgIntMsg').textContent),
      $('bgIntMsg').textContent);
  }
  $('bgIntTiming').value = 'flexible';
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick();
  check('G20d an unticked consent box blocks the submission',
    sent.length === 0 && /over 18/.test($('bgIntMsg').textContent),
    $('bgIntMsg').textContent);
  w.close();
});

/* ============================ 7 · INDEPENDENCE FROM SAVE (FOUNDER Q2) === */

await scope(async () => {
  const { w, $, sent } = boot({ search: '?interest=preview', answers: OWN_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } } });
  /* Nothing has been saved to My Plot. The offer must still be available. */
  check('G21 the offer does not require a prior Save to My Plot',
    $('bgInterest') !== null && $('bgIntOpen') !== null);
  check('G21b the register is reachable with an empty My Plot',
    w.PlotNuaJourneySave.has('disc025-borrowed-garden-check') === false &&
    $('bgIntOffer').hidden === false);
  $('bgIntOpen').click();
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  check('G21c submitting interest does not write to My Plot',
    w.PlotNuaJourneySave.count() === 0, w.PlotNuaJourneySave.count());
  check('G21d submitting interest does not send check_saved_at it never had',
    !('check_saved_at' in JSON.parse(sent[0].opts.body)));
  w.close();
});

await scope(async () => {
  /* G22 · and the reverse: Save still works with the register open, and the
     save payload is unchanged by G3's presence. */
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  $('bgSave').click();
  check('G22 Save to My Plot still saves with the register on screen',
    w.PlotNuaJourneySave.has('disc025-borrowed-garden-check') === true);
  const rec = w.PlotNuaJourneySave.list()
    .find((r) => r.journeyId === 'disc025-borrowed-garden-check');
  check('G22b the saved record keys are unchanged',
    JSON.stringify(Object.keys(rec).sort()) ===
    JSON.stringify(['answers', 'journeyId', 'resultKeys', 'savedAt', 'title']));
  check('G22c the saved record carries no interest fields',
    !JSON.stringify(rec).includes('garden_interest') &&
    !JSON.stringify(rec).includes('@'),
    JSON.stringify(rec).slice(0, 160));
  check('G22d the interest panel is unaffected by the save',
    $('bgInterest') !== null && $('bgIntOffer').hidden === false);
  w.close();
});

/* ========================================= 8 · THE G6 NO-PROMISE RULE === */

await scope(async () => {
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  const offer = $('bgInterest').textContent.replace(/\s+/g, ' ');
  check('G23 the offer states that joining is not a match',
    /not a match and does not guarantee one/.test(offer), offer.slice(0, 200));
  check('G23b the offer states there is no public listing',
    /no public listing/.test(offer));
  check('G23c the offer states nothing is shared until a yes',
    /until you say yes/.test(offer));
  for (const promise of [/we will match you/i, /you will be matched/i,
                         /guaranteed/i, /we'?ll find (you )?someone/i,
                         /we will find (you )?someone/i]) {
    check('G23d the panel does not say ' + promise, !promise.test(offer));
  }
  /* The R5 non-claims must be reachable from the panel, not buried. */
  check('G23e the panel states PlotNua verifies nobody’s identity',
    /does not verify anybody’s identity/.test(offer));
  /* Whitespace-normalised: the notice is wrapped prose, so "maximum of 24
     months" is split across source lines. Normalising is the right test here;
     the byte-exact test that must NOT normalise is the consent sentence (G4),
     because that string is hashed. */
  const notice = $('bgIntNotice').textContent.replace(/\s+/g, ' ');
  check('G23f the privacy notice is reachable before submitting',
    $('bgIntNotice') !== null &&
    /maximum of 24 months/.test(notice) &&
    /one-way digital fingerprint/.test(notice), notice.slice(0, 80));
  check('G23f2 the notice lists what PlotNua never asks for',
    /Your address, your Eircode, your phone number, your surname, your age/
      .test(notice));
  check('G23g the notice names the 2026-10-PHASE2-V2 retention rule verbatim',
    /We keep your record for a maximum of 24 months\. You can ask us to delete it at any time, and we may delete it sooner if it is no longer needed\./
      .test($('bgIntNotice').textContent.replace(/\s+/g, ' ')));
  /* G23f3 · THE DERIVED RESULT IS DISCLOSED.
     The register stores `inherited_result_key` — the result the Property Check
     produced — alongside the answers the homeowner supplied. Under V1 the
     notice described only the answers, so a stored field had no homeowner-
     facing disclosure. Founder decision of 8 October 2026 KEPT the field and
     amended the notice; 2026-10-PHASE2-V2 is that amendment.
     This guard exists because the "What we keep" sentence was previously
     unasserted, which is exactly how the omission survived a freeze. */
  check('G23f3 the notice discloses the stored Property Check result',
    /and whether you own the property . and the result the Property Check produced from those answers\./
      .test(notice), notice.slice(0, 120));
  w.close();
});

/* ================================================== 9 · FUNNEL EVENTS === */

await scope(async () => {
  const { w, $, events } = boot({ search: '?interest=preview', answers: OWN_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } } });
  const names = () => events().map((e) => e[0]);
  /* The suite is only meaningful if the sink is live at all. */
  check('G24pre the analytics sink is live (the existing funnel reached it)',
    names().includes('property_check_complete'), names().join(','));
  check('G24 no interest event fires merely from rendering the offer',
    !names().includes('garden_interest_opened'), names().join(','));
  $('bgIntOpen').click();
  check('G24b opening the form fires garden_interest_opened',
    names().filter((n) => n === 'garden_interest_opened').length === 1,
    names().join(','));
  $('bgIntCancel').click(); $('bgIntOpen').click();
  check('G24c re-opening does not fire it twice (deduped per page load)',
    names().filter((n) => n === 'garden_interest_opened').length === 1,
    names().join(','));
  fillValid($);
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  check('G24d submitting fires garden_interest_submitted once',
    names().filter((n) => n === 'garden_interest_submitted').length === 1,
    names().join(','));
  const evs = events();
  check('G24e there is something to inspect (not a vacuous pass)',
    evs.length >= 3, evs.length);
  check('G24f the events carry only the journey name',
    evs.every((e) => e[1] && Object.keys(e[1]).length === 1 && 'journey' in e[1]),
    JSON.stringify(evs));
  check('G24g every journey value is the page filename',
    evs.every((e) => e[1].journey === 'disc025-borrowed-garden-check'),
    JSON.stringify(evs));
  check('G24h no event carries an answer, a district, a name or an email',
    !/raheny|artane|Testy|@|corner|side_or_rear/.test(JSON.stringify(evs)),
    JSON.stringify(evs));
  w.close();
});

await scope(async () => {
  /* G25 · a closed page fires NO interest event at all, while still firing
     the pre-existing funnel events — so this is a real absence, not a dead
     sink. */
  const { w, events } = boot({ answers: OWN_WORKABLE });
  const evs = events();
  check('G25pre the sink is live on the closed page too',
    evs.some((e) => e[0] === 'property_check_complete'), JSON.stringify(evs));
  check('G25 the shipped-closed page fires no interest event',
    !JSON.stringify(evs).includes('garden_interest'), JSON.stringify(evs));
  w.close();
});

/* ============================================ 10 · IDEMPOTENCE / RE-REVEAL */

await scope(async () => {
  /* G26 · the tenure copy follows a changed answer on a second reveal, and
     the handlers are not bound twice. */
  const { w, $, sent } = boot({ search: '?interest=preview', answers: OWN_WORKABLE,
    reply: { status: 503, body: { state: 'not_open' } } });
  $('bgIntOpen').click();
  check('G26 own first: no permission block', $('bgIntCond').hidden === true);
  w.__disc025.answer(RENT_WORKABLE);          /* re-reveal with a new answer */
  check('G26b after re-reveal as rent: the permission block appears',
    $('bgIntCond').hidden === false);
  fillValid($);
  $('bgIntPerm').checked = true;
  $('bgIntNote').value = 'The owner knows about it and said to go ahead.';
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await tick(); await tick();
  check('G26c handlers are bound once: exactly one request after re-reveal',
    sent.length === 1, sent.length);
  check('G26d the re-revealed payload carries the NEW tenure',
    JSON.parse(sent[0].opts.body).inherited_tenure === 'rent');
  w.close();
});

await scope(async () => {
  /* G27 · a re-reveal that newly hits the suppression rule removes the
     section, so a homeowner who goes Back and changes their answer to
     "no garden" is no longer being invited. */
  const { w, $ } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  check('G27 invited first', $('bgInterest') !== null);
  w.__disc025.answer(NO_GARDEN);
  check('G27b changing the answer to no_garden removes the section',
    $('bgInterest') === null);
  w.close();
});

/* ======================================================== 11 · NO LEAKS = */

await scope(async () => {
  /* G28 · the page as shipped must not contain the endpoint in a form
     action, and must make no request on load. */
  const { w, sent } = boot({ answers: OWN_WORKABLE });
  check('G28 a closed page makes no network request on load', sent.length === 0);
  check('G28b no form has an action attribute pointing anywhere',
    Array.from(w.document.querySelectorAll('form'))
      .every((f) => !f.getAttribute('action')));
  w.close();
});

await scope(async () => {
  const { w, sent } = boot({ search: '?interest=preview', answers: OWN_WORKABLE });
  check('G28c an open page still makes no request until the form is sent',
    sent.length === 0);
  w.close();
});

/* --------------------------------------------------------------- report -- */
console.log('\n  G3 GUARD SUITE\n');
for (const [s, n, d] of results) {
  console.log('  [' + s + '] ' + n + (d ? '   ' + d : ''));
}
console.log('\n  ' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
