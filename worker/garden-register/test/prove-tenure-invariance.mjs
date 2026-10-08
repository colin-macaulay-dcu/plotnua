/* T5 · PAYLOAD INVARIANCE ACROSS THE PRE-G5 TENURE CORRECTION
 * ===========================================================================
 * The correction is supposed to change ONE tenure and nothing else. The
 * builder's region hashes prove no OTHER FILE REGION moved; this proves the
 * thing a homeowner actually sends.
 *
 * It boots BOTH pages — the committed pre-correction page read from git, and
 * the corrected page on disk — drives the real form through the real
 * intPayload(), and compares the JSON byte for byte:
 *
 *   own     MUST be byte-identical        (the correction must not touch it)
 *   rent    MUST be byte-identical        (the correction must not touch it)
 *   buying  MUST differ, in exactly one way: permission_confirmed, which was
 *           present before, is now absent. Nothing else may move.
 *
 * Asserting "own and rent are unchanged" is the only check that can catch the
 * correction leaking sideways. Asserting buying's diff EXACTLY is what stops
 * the correction being broader than approved.
 *
 *   node test/prove-tenure-invariance.mjs
 * ========================================================================= */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../..');
const LIVE = path.join(REPO, 'disc025-borrowed-garden-check.html');
const BASE_REF = '057bb81:disc025-borrowed-garden-check.html';

let pass = 0, fail = 0;
const check = (name, cond, detail) => {
  if (cond) { pass++; console.log(`  [PASS] ${name}`); }
  else { fail++; console.log(`  [FAIL] ${name}   ${detail ?? ''}`); }
};

/* The pre-correction page comes from git, not from a copy kept on disk, so
   this proof cannot drift out of step with what was actually shipped. */
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'tenure-inv-'));
const BEFORE = path.join(tmp, 'before.html');
fs.writeFileSync(BEFORE, execFileSync('git', ['show', BASE_REF], {
  cwd: REPO, maxBuffer: 1 << 28
}));

const ANSWERS = (tenure) => ({
  tenure,
  spare_corner: 'yes_a_clear_corner',
  way_in: 'side_or_rear_access',
  your_own_use: 'now_and_then'
});

const tickMicro = () => new Promise((r) => setTimeout(r, 0));

/* Drive the REAL page through its OWN entry point, exactly as prove-g3 does:
   __disc025.answer() feeds the Property Check, the page's own result path
   reveals the register, and intPayload() builds the body. An earlier version
   of this file assigned to w.answers and called intPaintTenure() by eval —
   w.answers does not exist (the page's state is inside an IIFE), and reaching
   past the page would have proved a harness rather than the product. */
async function payloadFor(pageFile, tenure, note) {
  const html = fs.readFileSync(pageFile, 'utf8');
  const sent = [];
  const dom = new JSDOM(html, {
    url: 'https://plotnua.ie/disc025-borrowed-garden-check.html?interest=preview',
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.fetch = function (url, opts) {
        sent.push({ url: String(url), opts });
        return Promise.resolve({ status: 200,
          json: () => Promise.resolve({ ok: true, state: 'received' }) });
      };
      w.scrollTo = function () {};
    }
  });
  const w = dom.window;
  const $ = (id) => w.document.getElementById(id);
  await new Promise((r) => w.addEventListener('load', r));

  w.__disc025.answer(ANSWERS(tenure));
  $('bgIntOpen').click();

  $('bgIntName').value = 'Testy';
  $('bgIntEmail').value = 'g3probe@example.com';
  $('bgIntDistrict').value = 'raheny';
  $('bgIntWater').value = 'outside_tap';
  $('bgIntSize').value = 'small';
  $('bgIntTiming').value = 'flexible';
  $('bgIntConsent').checked = true;
  /* The tick is set for every non-owner so the BEFORE page can submit at all:
     pre-correction it was mandatory for buying too. Setting it is what makes
     the buying comparison meaningful — it is the page, not the test, that
     decides whether the value reaches the payload. */
  if (tenure !== 'own' && $('bgIntPerm')) { $('bgIntPerm').checked = true; }
  if (note) { $('bgIntNote').value = note; }

  $('bgIntForm').dispatchEvent(new w.Event('submit',
    { cancelable: true, bubbles: true }));
  await tickMicro();
  const body = sent.length ? sent[0].opts.body : null;
  w.close();
  return body;
}

const RENT_NOTE = 'My landlord knows and has said it is fine with her.';

console.log('\n  T5 · PAYLOAD INVARIANCE ACROSS THE TENURE CORRECTION');
console.log('  before: ' + BASE_REF);
console.log('  after : disc025-borrowed-garden-check.html (on disk)\n');

/* ---- own: must be byte-identical ---------------------------------------- */
const ownA = await payloadFor(BEFORE, 'own');
const ownB = await payloadFor(LIVE, 'own');
check('T5a an OWNER payload is produced at all', !!ownA && !!ownB);
check('T5b the OWNER payload is byte-identical before and after',
  ownA === ownB, '\n    before ' + ownA + '\n    after  ' + ownB);

/* ---- rent: must be byte-identical --------------------------------------- */
const rentA = await payloadFor(BEFORE, 'rent', RENT_NOTE);
const rentB = await payloadFor(LIVE, 'rent', RENT_NOTE);
check('T5c a RENT payload is produced at all', !!rentA && !!rentB);
check('T5d the RENT payload is byte-identical before and after',
  rentA === rentB, '\n    before ' + rentA + '\n    after  ' + rentB);
check('T5e the RENT payload still carries permission_confirmed true',
  rentB && JSON.parse(rentB).permission_confirmed === true, rentB);

/* ---- buying: must differ in EXACTLY one key ----------------------------- */
/* A note is supplied on BOTH sides, and it has to be. Pre-correction a buying
   homeowner could not submit at all without a tick AND a >=20-character note,
   so a no-note comparison has nothing to compare: the BEFORE page produces no
   payload. Supplying the note on both sides isolates the one difference the
   correction is allowed to make. That buying no longer NEEDS the note is
   proved separately, through the real form, by prove-g3 T3/T4/T6. */
const BUY_NOTE = 'We complete the purchase at the end of next month.';
const buyA = await payloadFor(BEFORE, 'buying', BUY_NOTE);
const buyB = await payloadFor(LIVE, 'buying', BUY_NOTE);
check('T5f a BUYING payload is produced at all', !!buyA && !!buyB);
if (buyA && buyB) {
  const a = JSON.parse(buyA), b = JSON.parse(buyB);
  const keysA = Object.keys(a).sort(), keysB = Object.keys(b).sort();
  const dropped = keysA.filter((k) => !keysB.includes(k));
  const added = keysB.filter((k) => !keysA.includes(k));
  check('T5g BUYING drops exactly one key, and it is permission_confirmed',
    dropped.length === 1 && dropped[0] === 'permission_confirmed',
    JSON.stringify(dropped));
  check('T5h BUYING adds no key', added.length === 0, JSON.stringify(added));
  const changed = keysB.filter((k) => JSON.stringify(a[k]) !== JSON.stringify(b[k]));
  check('T5i every other BUYING value is unchanged',
    changed.length === 0, JSON.stringify(changed));
  check('T5j BUYING previously carried permission_confirmed (so the drop is real)',
    'permission_confirmed' in a, JSON.stringify(keysA));
}

fs.rmSync(tmp, { recursive: true, force: true });
console.log(`\n  ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
