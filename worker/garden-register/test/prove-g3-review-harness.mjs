/* G3 REVIEW HARNESS · PROOF THAT THE GENERATED FILES ACTUALLY WORK
 * ===========================================================================
 * The previous harness was reported as "generated successfully" and then
 * failed in the founder's browser with three errors. Generation succeeding is
 * not evidence. This script OPENS each generated state file, runs it, and
 * asserts the state marker the driver sets.
 *
 * It also proves the harness FAILS CLOSED: a copy opened WITHOUT
 * ?interest=preview must paint a specific harness failure, not throw a null
 * error, and must not leave a clickable form behind.
 *
 *   node test/prove-g3-review-harness.mjs <harness-dir>
 * ========================================================================= */

import fs from 'node:fs';
import path from 'node:path';
import { JSDOM } from 'jsdom';

const DIR = process.argv[2];
if (!DIR) {
  console.error('usage: node test/prove-g3-review-harness.mjs <harness-dir>');
  process.exit(2);
}

const CLOSED_HEADING = 'The register isn’t open yet';
const CLOSED_P1 = 'The register isn’t open yet. Your details haven’t ' +
                  'been saved. Your Property Check is unchanged.';

let pass = 0, fail = 0;
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  [PASS] ' + name); }
  else { fail++; console.log('  [FAIL] ' + name + (detail ? '\n         ' + detail : '')); }
}

/* Load a generated state file and let its driver run to completion. */
async function boot(file, search) {
  const html = fs.readFileSync(path.join(DIR, file), 'utf8');
  const errors = [];
  const sent = [];
  const dom = new JSDOM(html, {
    url: 'https://plotnua.ie/' + file + (search === undefined
      ? '?interest=preview' : search),
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    beforeParse(w) {
      w.scrollTo = function () {};
      /* Catch anything the driver throws, so a null-dereference shows up as a
         FAILURE here rather than being swallowed. */
      w.addEventListener('error', (e) => errors.push(String(e.message || e)));
      /* A tripwire: if the driver's fetch replacement were ever removed, this
         records the attempt. */
      const guard = () => { sent.push('fetch'); return Promise.reject(new Error('blocked')); };
      w.fetch = guard;
    }
  });
  const w = dom.window;
  /* The driver polls at 25ms; give it room past its 3s budgets. */
  for (let i = 0; i < 60; i++) await new Promise((r) => setTimeout(r, 25));
  return { w, $: (id) => w.document.getElementById(id), errors, sent, dom };
}

console.log('\n  G3 REVIEW HARNESS · PROOF\n');
console.log('  dir: ' + DIR + '\n');

/* ------------------------------------------- the three expected states --- */

const EXPECT = [
  ['state-1-invitation.html', 'OK-INVITATION'],
  ['state-2-form.html',       'OK-FORM'],
  ['state-3-closed.html',     'OK-CLOSED']
];

const booted = {};
for (const [file, marker] of EXPECT) {
  const b = await boot(file);
  booted[file] = b;
  const m = b.w.__g3marker || '(none)';
  check(file + ' reaches ' + marker, m.indexOf('OK:') === 0 && m.includes(marker), 'marker: ' + m);
  check(file + ' threw no uncaught error', b.errors.length === 0,
    b.errors.join(' | '));
  const banner = b.w.document.querySelector('[data-g3-marker]');
  check(file + ' painted a visible OK banner',
    !!banner && banner.getAttribute('data-g3-marker') === 'OK',
    banner ? banner.textContent.slice(0, 110) : 'no banner');
  check(file + ' title carries the marker',
    /^G3-OK /.test(b.w.document.title), b.w.document.title);
}

/* ------------------------------------- the states are genuinely distinct -- */

{
  const inv = booted['state-1-invitation.html'];
  check('state 1 shows the invitation, not the form',
    inv.$('bgInterest') && !inv.$('bgInterest').hidden &&
    !inv.$('bgIntOffer').hidden && inv.$('bgIntForm').hidden);
  check('state 1 shows the preview ribbon (the page’s own rule, flag not flipped)',
    inv.$('bgIntPrev') && inv.$('bgIntPrev').hidden === false);
  check('state 1 invitation carries the no-guarantee sentence',
    /not a match and does not guarantee one/
      .test(inv.$('bgIntOffer').textContent.replace(/\s+/g, ' ')));
}

{
  const f = booted['state-2-form.html'];
  check('state 2 shows the form', f.$('bgIntForm') && !f.$('bgIntForm').hidden);
  const vals = ['bgIntName', 'bgIntEmail', 'bgIntDistrict', 'bgIntWater',
                'bgIntSize', 'bgIntTiming'].map((id) => f.$(id).value);
  check('state 2 is filled, every field non-empty',
    vals.every((v) => v && v.length), JSON.stringify(vals));
  check('state 2 consent is ticked', f.$('bgIntConsent').checked === true);
  check('state 2 consent label is the exact G1B sentence',
    f.$('bgIntConsentText').textContent ===
    "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.",
    JSON.stringify(f.$('bgIntConsentText').textContent));
  check('state 2 has not submitted (no closed state showing)',
    f.$('bgIntDone').hidden === true);
}

{
  const c = booted['state-3-closed.html'];
  check('state 3 shows the closed state', !c.$('bgIntDone').hidden);
  check('state 3 heading is the approved wording exactly',
    c.$('bgIntDoneH').textContent.trim() === CLOSED_HEADING,
    JSON.stringify(c.$('bgIntDoneH').textContent.trim()));
  const ps = Array.from(c.$('bgIntDoneBody').querySelectorAll('p'))
    .map((p) => p.textContent.replace(/\s+/g, ' ').trim());
  check('state 3 first paragraph is the founder-corrected sentence',
    ps[0] === CLOSED_P1, JSON.stringify(ps[0]));
  check('state 3 does NOT claim nothing was sent',
    !/nothing has been sent|nothing was sent/i.test(ps.join(' ')));
  check('state 3 hides both the invitation and the form',
    c.$('bgIntOffer').hidden && c.$('bgIntForm').hidden);

  /* CORRECTION 2 · the capture must be positioned on the closed response, not
     on the top of the panel. jsdom reports 0 for every rect, so the scroll
     OFFSET cannot be verified here — but the TARGET can, and the target was
     the actual defect: the old harness scrolled to #bgInterest and left the
     closed state below the fold. */
  check('state 3 positions the capture on #bgIntDone, not #bgInterest',
    c.w.__g3scroll && c.w.__g3scroll.target === 'bgIntDone',
    JSON.stringify(c.w.__g3scroll));
  check('state 3 exposes all three approved lines in the closed component',
    (function () {
      const t = (c.$('bgIntDoneH').textContent + ' ' +
                 c.$('bgIntDoneBody').textContent).replace(/\s+/g, ' ');
      return t.includes(CLOSED_HEADING) && t.includes(CLOSED_P1) &&
             t.includes('Nothing is waiting on you. When the register opens, ' +
                        'this is where it will happen.');
    })(),
    c.$('bgIntDoneBody').textContent.replace(/\s+/g, ' ').slice(0, 160));
}

/* states 1 and 2 must still position on the panel itself */
{
  const inv = booted['state-1-invitation.html'];
  const frm = booted['state-2-form.html'];
  check('state 1 positions on #bgInterest',
    inv.w.__g3scroll && inv.w.__g3scroll.target === 'bgInterest',
    JSON.stringify(inv.w.__g3scroll));
  check('state 2 positions on #bgInterest',
    frm.w.__g3scroll && frm.w.__g3scroll.target === 'bgInterest',
    JSON.stringify(frm.w.__g3scroll));
}

/* ------------------------------------------------ nothing left the browser */

for (const [file] of EXPECT) {
  check(file + ' made no real network call',
    booted[file].sent.length === 0, booted[file].sent.join(','));
}

/* ----------------------------------------------------- FAIL-CLOSED PROOF -- */
/* The whole point of the repair. Opened without the query string, the page
   correctly withholds the section — and the harness must say so precisely
   instead of dereferencing null. This is the exact condition that broke the
   previous harness. */

{
  const b = await boot('state-3-closed.html', '');
  const m = b.w.__g3marker || '(none)';
  check('FAIL-CLOSED: no query string yields a HARNESS FAILURE marker',
    m.indexOf('FAIL:') === 0, 'marker: ' + m);
  check('FAIL-CLOSED: the message names the missing query string',
    /interest=preview/.test(m), m);
  check('FAIL-CLOSED: it does NOT throw a null-click error',
    b.errors.length === 0 &&
    !/Cannot read properties of null/.test(m), b.errors.join(' | ') + ' ' + m);
  const banner = b.w.document.querySelector('[data-g3-marker]');
  check('FAIL-CLOSED: a red failure banner is painted',
    !!banner && banner.getAttribute('data-g3-marker') === 'FAIL',
    banner ? banner.textContent.slice(0, 140) : 'no banner');
  /* CORRECTED ASSERTION. I first asserted #bgInterest was ABSENT here, and it
     failed — because the driver stops at step 2 BEFORE calling
     __disc025.answer(), so reveal() never runs, interestOffer() never runs,
     and the removal branch is never reached. The section is still in the DOM
     in its AUTHORED state: hidden, with the reveal screen not shown at all.
     That is the page shipping correctly; my expectation was the wrong
     property. What matters is that nothing is REACHABLE, which is what is
     asserted now. (Removal is a separate guarantee, proven by G1/G1b in
     prove-g3.mjs for the case where the homeowner does complete the check.) */
  const sec = b.$('bgInterest');
  check('FAIL-CLOSED: the panel is not reachable (present but hidden, as authored)',
    sec !== null && sec.hidden === true,
    sec ? 'hidden=' + sec.hidden : 'absent');
  check('FAIL-CLOSED: the reveal screen was never shown, so nothing was driven',
    b.$('bgReveal').classList.contains('is-on') === false);
  check('FAIL-CLOSED: no interest state was entered',
    b.$('bgIntDone').hidden === true && b.$('bgIntForm').hidden === true);
  check('FAIL-CLOSED: title marks the failure',
    /^G3-FAIL /.test(b.w.document.title), b.w.document.title);
}

/* --------------------------------- the parent files must carry no script -- */

for (const parent of ['review-390.html', 'review-1440.html']) {
  const html = fs.readFileSync(path.join(DIR, parent), 'utf8');
  check(parent + ' contains no <script> at all',
    !/<script/i.test(html));
  check(parent + ' loads all three state files by src with the query string',
    EXPECT.every(([f]) =>
      html.includes('src="' + f + '?interest=preview"')),
    html.match(/src="[^"]*"/g));
  check(parent + ' uses no srcdoc (the defect that caused this)',
    !/srcdoc/i.test(html));
}

console.log('\n  ' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
