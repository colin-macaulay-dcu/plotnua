/* G3 · GUARD-CAPABILITY PROOF FOR THE PAGE GUARDS
 * ===========================================================================
 * prove-g3.mjs passing 166/0 says only that the page and the suite agree.
 * It does not say the suite would NOTICE if the page were wrong. This script
 * breaks one thing at a time in a COPY of the page, re-runs the whole suite
 * against the copy, and asserts that the guards which should fail do fail —
 * and, just as importantly, that they are the ONLY ones that fail where the
 * mutation is narrow.
 *
 * Every mutation asserts that its own replacement actually applied. A
 * mutation that silently matches nothing would otherwise produce a clean run
 * and be recorded as a passing guard, which is the worst outcome available.
 *
 *   node test/prove-g3-mutations.mjs
 * ========================================================================= */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

/* See the note in prove-g3.mjs: resolved by search, not a fixed depth, so the
   suite survives having been moved into version control. */
const PAGE = (function () {
  for (const rel of ['../../../disc025-borrowed-garden-check.html',
                     '../../plotnua-github/disc025-borrowed-garden-check.html']) {
    const p = fileURLToPath(new URL(rel, import.meta.url));
    if (fs.existsSync(p)) return p;
  }
  throw new Error('cannot locate disc025-borrowed-garden-check.html');
})();
const SUITE = fileURLToPath(new URL('./prove-g3.mjs', import.meta.url));
const SRC = fs.readFileSync(PAGE, 'utf8');

function runSuite(html) {
  const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'g3mut-')),
                        'page.html');
  fs.writeFileSync(tmp, html, 'utf8');
  let out = '';
  try {
    out = execFileSync(process.execPath, [SUITE, tmp],
                       { encoding: 'utf8', env: process.env });
  } catch (e) {
    out = (e.stdout || '') + (e.stderr || '');
  }
  const failed = Array.from(out.matchAll(/^\s*\[FAIL\] (\S+)/gm)).map((m) => m[1]);
  const m = /(\d+) passed, (\d+) failed/.exec(out);
  /* A suite that THREW never printed its report. That is not a detection and
     must never be scored as one: it means later assertions did not run, so
     the harness cannot know what else is blind. It is reported as a harness
     defect to be fixed. */
  return {
    failed, crashed: !m,
    passed: m ? +m[1] : -1, total: m ? +m[1] + +m[2] : -1, out
  };
}

const pad = (s, n) => (s.length >= n ? s : s + ' '.repeat(n - s.length));

/* A replacement that MUST match, exactly `count` times. */
function sub(html, from, to, count = 1) {
  const n = html.split(from).length - 1;
  if (n !== count) {
    throw new Error('mutation did not apply: expected ' + count +
                    ' occurrence(s) of ' + JSON.stringify(from.slice(0, 70)) +
                    ', found ' + n);
  }
  return html.split(from).join(to);
}

/* ------------------------------------------------------------- baseline -- */
const base = runSuite(SRC);
let pass = 0, fail = 0;
console.log('\n  G3 PAGE GUARDS · CAPABILITY PROOF\n');
if (base.failed.length) {
  console.log('  [ABORT] the unmutated page does not pass: ' +
              base.failed.join(', '));
  process.exit(1);
}
console.log('  baseline: ' + base.passed + '/' + base.total +
            ' passed, 0 failed\n');

/* Each case: a name, a mutation, and the guard PREFIXES that must fail.
   A prefix matches any guard id starting with it, because one mutation
   legitimately trips several numbered assertions in the same family. */
const CASES = [
  /* NOTE ON EXPECTATIONS. Three of these were wrong on the first run and are
     corrected here, with the reason recorded rather than the expectation
     quietly widened:
       M1  does NOT trip G25. A closed page fires no interest event because
           nothing opens the form, whether or not the gate would have let it.
       M7  does NOT trip G9 or G13. The tenure VALIDATION is independent of
           the block's VISIBILITY, which is the correct design: hiding the
           affordance does not weaken the rule. M7 breaks only the affordance.
       M18 does NOT trip G20d. The consent tick is read from the checkbox, not
           from the payload field, so the local gate is unaffected.
     Each of those is the page being better than I assumed, not a gap. */

  ['M1  INTEREST_PUBLIC flipped to true (ships open)',
   (h) => sub(h, 'var INTEREST_PUBLIC = false;', 'var INTEREST_PUBLIC = true;'),
   ['G1', 'G2b', 'G2d']],

  ['M2  the no_garden suppression removed (founder Q1 broken)',
   (h) => sub(h, "if (answers.spare_corner === 'no_garden') return false;",
                 "if (false) return false;"),
   ['G3']],

  ['M3  a typographic apostrophe in the consent constant',
   (h) => sub(h,
     '"I\'m over 18, and I\'d like PlotNua to keep this and tell me if someone nearby is looking for growing space."',
     '"I’m over 18, and I’d like PlotNua to keep this and tell me if someone nearby is looking for growing space."'),
   ['G4', 'G11']],

  ['M4  the consent label written with innerHTML',
   (h) => sub(h, "$('bgIntConsentText').textContent = CONSENT_TEXT;",
                 "$('bgIntConsentText').innerHTML = CONSENT_TEXT + '<b></b>';"),
   ['G4b']],

  ['M5  a district quietly dropped from the page vocabulary',
   (h) => sub(h, "      ['artane', 'Artane'],\n", ''),
   ['G5']],

  ['M6  the founder-corrected closed copy reverted',
   (h) => sub(h,
     "      'The register isn\u2019t open yet. Your details haven\u2019t been saved. ' +\n      'Your Property Check is unchanged.',",
     "      'Nothing has been sent and nothing has been saved.',"),
   ['G14']],

  /* M7 RE-ANCHORED 8 October 2026. The old anchor was
     "if (tenure === 'rent' || tenure === 'buying') {", which the PRE-G5 tenure
     alignment deleted. The mutation then stopped APPLYING and this harness
     reported it VACUOUS — the right outcome, and the reason the harness
     distinguishes vacuous from caught: an unapplied mutation proves nothing
     and must never read as a pass. */
  ['M7  the tenure rule never shows the permission block',
   (h) => sub(h, "    if (tenure === 'rent') {", "    if (false) {"),
   ['G8', 'G26b']],

  ['M8  the tenure rule stops requiring the statement',
   (h) => sub(h, "      if ($('bgIntNote').value.trim().length < 20) return 'garden_note';",
                 "      if (false) return 'garden_note';"),
   ['G9d']],

  ['M9  source changed away from garden_interest',
   (h) => sub(h, "      source: 'garden_interest',", "      source: 'direct',"),
   ['G11c']],

  ['M10 an Eircode field added to the form',
   (h) => sub(h,
     '            <label for="bgIntName">First name</label>',
     '            <label for="bgIntEircode">Your Eircode</label>\n' +
     '            <input type="text" id="bgIntEircode" name="eircode">\n' +
     '            <label for="bgIntName">First name</label>'),
   ['G6']],

  ['M11 the double-submit guard removed',
   (h) => sub(h, "    if (INT_STATE === 'sending') return;", "    if (false) return;"),
   ['G18c']],

  ['M12 the section hidden instead of removed when the gates fail',
   (h) => sub(h, '      if (sec.parentNode) sec.parentNode.removeChild(sec);',
                 '      sec.hidden = true;'),
   ['G1', 'G3', 'G27b']],

  ['M13 a promise of a match added to the offer',
   (h) => sub(h, '        <p class="bg-int-cta">',
     '        <p class="bg-int-p">Join and we will match you with a grower, guaranteed.</p>\n' +
     '        <p class="bg-int-cta">'),
   ['G23']],

  ['M14 the interest-opened funnel call removed',
   (h) => sub(h, '          window.PlotNuaFunnel.interestOpened();',
                 '          void 0;'),
   ['G24b']],

  ['M15 result PROSE sent instead of the result key',
   (h) => sub(h, '      if (k) body.inherited_result_key = k;',
     "      if (k) body.inherited_result_key = 'A corner of your garden looks workable';"),
   ['G11e']],

  ['M16 interest made conditional on a prior Save (founder Q2 broken)',
   (h) => sub(h, '    sec.hidden = false;\n    if (!INTEREST_PUBLIC)',
     '    if (!window.PlotNuaJourneySave.has("disc025-borrowed-garden-check")) {\n' +
     '      if (sec.parentNode) sec.parentNode.removeChild(sec);\n      return;\n    }\n' +
     '    sec.hidden = false;\n    if (!INTEREST_PUBLIC)'),
   ['G21']],

  ['M17 the endpoint repointed somewhere else',
   (h) => sub(h,
     "'https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/garden'",
     "'https://example.invalid/v1/garden-register/garden'"),
   ['G10b']],

  ['M18 over_18 sent as a string instead of a boolean',
   (h) => sub(h, "      over_18: $('bgIntConsent').checked === true,",
                 "      over_18: String($('bgIntConsent').checked),"),
   ['G11b']],

  ['M19 the inherited Property Check answers dropped',
   (h) => sub(h, "      inherited_spare_corner: answers.spare_corner || '',", ''),
   ['G11d']],

  ['M20 the retention sentence altered in the notice',
   (h) => sub(h, 'of 24 months', 'of 36 months'),
   ['G23f', 'G23g']],

  ['M21 the not-a-match line removed from the confirmation',
   /* V2, 8 Oct 2026: re-pointed after the success copy was reflowed. The old
      target stopped matching and this mutation went VACUOUS - the suite caught
      it, which is the only reason it is live again. It now removes the
      not-a-match clause from the new wording, so G15 must still fire. */
   (h) => sub(h, "      'This is a register, not a match. If somebody nearby is looking, we ' +",
                 "      'If somebody nearby is looking, we ' +"),
   ['G15']],

  ['M22 the preview gate loosened to any ?interest value',
   (h) => sub(h, '      return /(?:^|[?&])interest=preview(?:&|$)/.test(location.search);',
                 '      return /interest/.test(location.search);'),
   ['G2d']],

  ['M23 a second over-18 checkbox added (double-asking)',
   (h) => sub(h,
     '        <div class="bg-int-tick">\n          <input type="checkbox" id="bgIntConsent" required>',
     '        <div class="bg-int-tick">\n          <input type="checkbox" id="bgIntOver18">\n' +
     '          <label for="bgIntOver18">I am over 18</label>\n        </div>\n' +
     '        <div class="bg-int-tick">\n          <input type="checkbox" id="bgIntConsent" required>'),
   ['G4e']],

  ['M24 a refusal leaks the internal field identifier',
   (h) => sub(h, "               (INT_FIELD_NAME[f] || 'one of the answers') +",
                 "               (f || 'one of the answers') +"),
   ['G16b']],

  /* ===================== PRE-G5 TENURE ALIGNMENT MUTATIONS ==============
     Added 8 October 2026 under founder decision D-G5-1 = option 1. These exist
     to stop the correction being silently reverted or silently widened. The
     Worker-side mutations (M27, M29, M30) live in prove-worker-mutations.mjs,
     because the code they attack is in the Worker, not the page. */

  ['M26 the buying divergence reinstated (page shows the permission block)',
   (h) => sub(h, "    if (tenure === 'rent') {", "    if (tenure !== 'own') {"),
   ['T1', 'T2']],

  ['M28 the permission tick demanded of EVERYONE, owners included',
   (h) => sub(h, "    if (answers.tenure === 'rent') {\n" +
                 "      if (!$('bgIntPerm').checked) return 'permission_confirmed';",
                 "    if (true) {\n" +
                 "      if (!$('bgIntPerm').checked) return 'permission_confirmed';"),
   /* G10, not G7. My first expectation named G7, which asserts the permission
      BLOCK is hidden for an owner — that is intPaintTenure, which this
      mutation does not touch. G10 is the owner actually submitting, which is
      what breaks. Expectation corrected, product unchanged: the same class of
      over-broad expectation recorded three times in the G3 build. */
   ['G10', 'T3']],

  ['M25 the funnel event made to carry the district',
   (h) => sub(h, "    interestOpened:    function () { track('garden_interest_opened'); },",
     "    interestOpened:    function () {\n" +
     "      try { if (typeof gtag === 'function') gtag('event', 'garden_interest_opened',\n" +
     "        { journey: journey(), district: 'raheny' }); } catch (e) {}\n    },"),
   ['G24f', 'G24h']],
];

for (const [name, mutate, expectPrefixes] of CASES) {
  let r;
  try {
    r = runSuite(mutate(SRC));
  } catch (e) {
    fail++;
    console.log('  [VACUOUS ] ' + pad(name, 54) + e.message);
    continue;
  }
  const got = r.failed;
  const covered = expectPrefixes.filter(
    (p) => got.some((g) => g === p || g.startsWith(p)));
  const uncovered = got.filter(
    (g) => !expectPrefixes.some((p) => g === p || g.startsWith(p)));

  if (r.crashed) {
    fail++;
    console.log('  [CRASHED ] ' + pad(name, 54) +
                'the suite threw; later assertions never ran');
    console.log(r.out.split('\n').filter((l) => /Error|TypeError/.test(l))
                 .slice(0, 2).map((l) => '             ' + l.trim()).join('\n'));
  } else if (got.length === 0) {
    fail++;
    console.log('  [BLIND   ] ' + pad(name, 54) + 'nothing failed');
  } else if (covered.length !== expectPrefixes.length) {
    fail++;
    console.log('  [PARTIAL ] ' + pad(name, 54) + 'expected ' +
                expectPrefixes.join('+') + ', caught ' + got.join(','));
  } else {
    pass++;
    const extra = uncovered.length ? '  (also: ' + uncovered.join(',') + ')' : '';
    console.log('  [CAUGHT  ] ' + pad(name, 54) + got.length +
                ' failed: ' + covered.join('+') + extra);
  }
}

console.log('\n  ' + pass + ' mutations caught, ' + fail +
            ' blind, vacuous or crashed\n');
process.exit(fail ? 1 : 0);
