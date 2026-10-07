/* G3 · THE DEPLOYED ROUND TRIP
 * ===========================================================================
 * WHY THIS IS A SEPARATE SCRIPT, AND WHAT IT CAN AND CANNOT PROVE.
 *
 * The page's journey cannot be driven end to end from a local preview server,
 * and saying otherwise would be a fiction. The deployed Worker matches Origin
 * EXACTLY against https://plotnua.ie: a page served from localhost sends
 * Origin: http://localhost:PORT, which the Worker answers 403 with no CORS
 * header — correctly, and before it ever reaches the write switch. So a
 * localhost preview can never produce 503 not_open, and a 403 would prove
 * nothing about the closed state.
 *
 * The honest decomposition is therefore two steps, and both are run here:
 *
 *   STEP A  Take the payload the REAL PAGE builds, captured by running the
 *           shipped page in jsdom with fetch intercepted. Nothing is
 *           hand-written: the bytes are the page's own.
 *   STEP B  Send exactly those bytes to the DEPLOYED Worker with the headers
 *           a real browser on https://plotnua.ie would send, and assert the
 *           answer is 503 not_open.
 *
 * Together these establish what matters: the page builds a payload the
 * deployed Worker accepts as well-formed, and the deployed Worker then
 * REFUSES TO STORE IT because WRITES_ENABLED is false. A refusal on a
 * malformed payload would prove nothing, so step B also asserts the
 * well-formedness positively, by showing that the SAME request with one
 * field broken returns 400 refused instead of 503 — i.e. the 503 is the
 * write switch talking, not the validator.
 *
 * THIS SCRIPT CANNOT CREATE A RECORD. Writes are off at the Worker; every
 * assertion below is a refusal; and the Airtable check is the backstop.
 *
 *   node test/prove-g3-deployed.mjs
 * ========================================================================= */

import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

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
const ORIGIN = 'https://plotnua.ie';

let pass = 0, fail = 0;
function check(name, cond, detail) {
  if (cond) { pass++; console.log('  [PASS] ' + name); }
  else { fail++; console.log('  [FAIL] ' + name + (detail ? '   ' + detail : '')); }
}

/* ============================================ STEP A · capture the payload */

const HTML = fs.readFileSync(PAGE, 'utf8');
let captured = null;

{
  const dom = new JSDOM(HTML, {
    url: ORIGIN + '/disc025-borrowed-garden-check.html?interest=preview',
    runScripts: 'dangerously', pretendToBeVisual: true,
    beforeParse(w) {
      w.scrollTo = function () {};
      w.fetch = function (url, opts) {
        captured = { url: String(url), opts };
        /* Answer nothing useful: this step only captures. */
        return Promise.reject(new TypeError('captured, not sent'));
      };
    }
  });
  const w = dom.window, $ = (id) => w.document.getElementById(id);
  w.__disc025.answer({
    tenure: 'own', spare_corner: 'yes_a_clear_corner',
    way_in: 'side_or_rear_access', your_own_use: 'now_and_then'
  });
  $('bgIntOpen').click();
  /* A deliberately non-routable mailbox on a reserved TLD. Even if the write
     switch were somehow on, this address cannot receive mail. */
  $('bgIntName').value = 'G3Probe';
  $('bgIntEmail').value = 'g3probe@plotnua.invalid';
  $('bgIntDistrict').value = 'raheny';
  $('bgIntWater').value = 'outside_tap';
  $('bgIntSize').value = 'small';
  $('bgIntTiming').value = 'flexible';
  $('bgIntConsent').checked = true;
  $('bgIntForm').dispatchEvent(new w.Event('submit', { cancelable: true, bubbles: true }));
  await new Promise((r) => setTimeout(r, 20));
  w.close();
}

console.log('\n  G3 · DEPLOYED ROUND TRIP\n');
console.log('  STEP A · the payload the shipped page built\n');

check('A1 the page produced a request', !!captured);
if (!captured) { console.log('\n  cannot continue\n'); process.exit(1); }
console.log('    url  ' + captured.url);
console.log('    body ' + captured.opts.body);
console.log();

const body = JSON.parse(captured.opts.body);
check('A2 it targets the deployed garden route',
  captured.url === 'https://plotnua-garden-register.colin-a41.workers.dev' +
                   '/v1/garden-register/garden', captured.url);
check('A3 the probe address is non-routable (.invalid)',
  /@plotnua\.invalid$/.test(body.email), body.email);

/* ============================================ STEP B · send it for real === */

async function send(payload, extra = {}) {
  const headers = Object.assign({
    'content-type': 'application/json',
    origin: ORIGIN,
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'cors'
  }, extra);
  let r;
  try {
    r = await fetch(captured.url, {
      method: 'POST', headers, body: JSON.stringify(payload)
    });
  } catch (e) {
    /* UNREACHABLE IS NOT A RESULT. An environment that cannot resolve the
       hostname tells us nothing about the Worker, and must never be scored
       as a pass OR as a failure of the Worker. */
    const code = (e.cause && e.cause.code) || e.message;
    return { unreachable: code };
  }
  let j = null;
  try { j = await r.json(); } catch { /* non-JSON is a finding, not a crash */ }
  return { status: r.status, json: j,
           acao: r.headers.get('access-control-allow-origin') };
}

console.log('  STEP B · the deployed Worker’s answer\n');

/* Probe once before asserting anything, so an unreachable network produces a
   clear instruction rather than a misleading red failure. */
{
  const probe = await send(body);
  if (probe.unreachable) {
    console.log('  STEP B NOT RUN — the deployed Worker is unreachable from');
    console.log('  this environment (' + probe.unreachable + '). That is an');
    console.log('  ENVIRONMENT fact, not a Worker fact, and it is not reported');
    console.log('  as a pass or as a failure.\n');
    console.log('  Run step B from a machine with ordinary outbound access:');
    console.log('    node test/prove-g3-deployed.mjs\n');
    console.log('  Step A passed: the payload above is the shipped page’s own.');
    console.log('\n  ' + pass + ' passed, ' + fail +
                ' failed, STEP B UNAVAILABLE\n');
    process.exit(2);
  }
}

const real = await send(body);
console.log('    -> ' + real.status + ' ' + JSON.stringify(real.json));
check('B1 the deployed Worker answers 503 not_open',
  real.status === 503 && real.json && real.json.state === 'not_open',
  real.status + ' ' + JSON.stringify(real.json));
check('B2 nothing in the reply mentions mail, a token, confirm or verify',
  !/mail|token|confirm|verify/i.test(JSON.stringify(real.json)),
  JSON.stringify(real.json));
check('B3 the reply carries the CORS header for plotnua.ie only',
  real.acao === ORIGIN, 'acao=' + real.acao);

/* THE ESSENTIAL POSITIVE CONTROL. A 503 would be worthless as evidence if the
   Worker answered 503 to anything: it must be reachable PAST the validator,
   which means a broken field has to come back 400 refused instead. */
const broken = await send(Object.assign({}, body, { district: 'narnia' }));
console.log('    -> (district broken) ' + broken.status + ' ' +
            JSON.stringify(broken.json));
check('B4 POSITIVE CONTROL: the same request with a bad district is 400 refused',
  broken.status === 400 && broken.json && broken.json.state === 'refused' &&
  broken.json.field === 'district',
  broken.status + ' ' + JSON.stringify(broken.json));

const noConsent = await send(Object.assign({}, body, {
  consent_text: 'I agree to the terms'
}));
console.log('    -> (consent wrong)   ' + noConsent.status + ' ' +
            JSON.stringify(noConsent.json));
check('B5 POSITIVE CONTROL: wrong consent wording is 400 refused on consent_text',
  noConsent.status === 400 && noConsent.json &&
  noConsent.json.field === 'consent_text',
  noConsent.status + ' ' + JSON.stringify(noConsent.json));

/* So: the page's own payload passes every validator the Worker has, and is
   stopped only by the write switch. That is exactly the state G3 ships in. */
check('B6 the 503 is the WRITE SWITCH, not the validator',
  real.status === 503 && broken.status === 400 && noConsent.status === 400);

/* And the gate that would have mattered if the page were served elsewhere. */
const wrongOrigin = await send(body, { origin: 'http://localhost:8080' });
check('B7 a localhost origin is refused 403 with no CORS header',
  wrongOrigin.status === 403 && !wrongOrigin.acao,
  wrongOrigin.status + ' acao=' + wrongOrigin.acao);
console.log('       (this is why the journey cannot be driven from a local');
console.log('        preview server, and why STEP A/B are separate)');

console.log('\n  ' + pass + ' passed, ' + fail + ' failed');
console.log('\n  STILL TO CHECK BY HAND (Airtable, not this Worker):');
console.log('    Gardens  tbltT83xG6E09PhjW  -> totalRecordCount must be 0');
console.log('    Growers  tblHECGCBXQDz6Kqc  -> totalRecordCount must be 0\n');
process.exit(fail ? 1 : 0);
