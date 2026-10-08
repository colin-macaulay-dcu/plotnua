/* G2 · DEPLOYED NEGATIVE CONTROLS — SWITCH-INDEPENDENT ONLY
 * ===========================================================================
 * Run this AFTER deploying, against the real workers.dev hostname. It proves
 * the deployed Worker refuses, rather than proving the local source refuses —
 * a distinction that matters, because a deployment can carry different vars
 * than the file on disk.
 *
 * SAFE WITH WRITES ON. Every assertion here is a refusal that holds in BOTH
 * switch states: wrong method, wrong origin, wrong Fetch Metadata, unknown
 * path, preflight. Not one of them carries a body that could be written, so
 * this file can be run with WRITES_ENABLED=true without creating a record.
 *
 * THE TWO SWITCH-DEPENDENT CONTROLS ARE NOT HERE. A valid garden POST and a
 * valid grower POST return 503 not_open with writes off and 200 received with
 * writes ON, creating three Airtable rows each. They live in
 * prove-deployed-switch.mjs, which requires an explicit expected mode.
 *
 * CORRECTED 8 October 2026 (founder decision D-G5-3). This file previously
 * claimed: "This script cannot create a record even if the Worker were wide
 * open: it sends no valid consent text for a write it expects to succeed."
 * That was FALSE. Both consent strings were byte-identical to the Worker's
 * CONSENT_TEXT and both bodies were complete and valid, so D1 and D2 were
 * valid writes that happened to be stopped by the switch. With writes on they
 * would have created two records and reported them as FAILURES.
 *
 *   node test/prove-deployed.mjs https://plotnua-garden-register.<sub>.workers.dev
 * ========================================================================= */
const BASE = process.argv[2];
if (!BASE || !/^https:\/\//.test(BASE)) {
  console.error('usage: node test/prove-deployed.mjs https://<worker>.workers.dev');
  process.exit(2);
}
const ORIGIN = 'https://plotnua.ie';

let pass = 0, fail = 0;
const line = (s, n, d) => { console.log(`  [${s}] ${n}${d ? '   ' + d : ''}`); };
function check(name, cond, detail) {
  if (cond) { pass++; line('PASS', name); } else { fail++; line('FAIL', name, detail); }
}

async function call(path, body, opts = {}) {
  const { origin = ORIGIN, site = 'cross-site', mode = 'cors', method = 'POST' } = opts;
  const headers = { 'content-type': 'application/json' };
  if (origin) headers.origin = origin;
  if (site) headers['sec-fetch-site'] = site;
  if (mode) headers['sec-fetch-mode'] = mode;
  const r = await fetch(BASE + path, {
    method, headers,
    body: method === 'GET' ? undefined : JSON.stringify(body || {})
  });
  let j = null; try { j = await r.json(); } catch { /* non-JSON is fine here */ }
  return { status: r.status, json: j, acao: r.headers.get('access-control-allow-origin') };
}

/* A DELIBERATELY INVALID body, used only to exercise routing, methods, origin
   and Fetch Metadata. It carries no consent text, so even if every other guard
   were removed and the write switch were on, the Worker refuses it on
   `consent_text` before composing an Airtable request. The valid bodies that
   used to live here have moved to prove-deployed-switch.mjs. */
const growerBody = {
  first_name: 'Deploy', email: 'deployprobe2@plotnua.invalid', district: 'raheny',
  travel_radius: 'walking', space_wanted: 'small', timing: 'flexible',
  over_18: true
};

console.log('\n  DEPLOYED NEGATIVE CONTROLS (switch-independent) · ' + BASE + '\n');

/* 1-2 · D1 and D2 HAVE MOVED to prove-deployed-switch.mjs. They are the only
   two assertions in this file that inverted when the write switch flipped, and
   the only two that carried a writable body. Keeping them here made the whole
   file unsafe to run with writes on. */

/* 3 · GET remains unavailable -------------------------------------------- */
const gGet = await call('/v1/garden-register/garden', null, { method: 'GET' });
check('D3 GET on the garden route is 405', gGet.status === 405, 'got ' + gGet.status);
const wGet = await call('/v1/garden-register/grower', null, { method: 'GET' });
check('D4 GET on the grower route is 405', wGet.status === 405, 'got ' + wGet.status);
const rootGet = await call('/', null, { method: 'GET' });
check('D5 GET on the root is refused', rootGet.status === 405 || rootGet.status === 404,
  'got ' + rootGet.status);

/* 4 · disallowed origins remain refused ---------------------------------- */
const noOrigin = await call('/v1/garden-register/grower', growerBody, { origin: null });
check('D6 no Origin header => 403 and NO CORS header',
  noOrigin.status === 403 && !noOrigin.acao, 'got ' + noOrigin.status + ' acao=' + noOrigin.acao);
const evil = await call('/v1/garden-register/grower', growerBody,
  { origin: 'https://plotnua.ie.evil.example' });
check('D7 lookalike origin => 403 and NO CORS header',
  evil.status === 403 && !evil.acao, 'got ' + evil.status + ' acao=' + evil.acao);
const sameSite = await call('/v1/garden-register/grower', growerBody, { site: 'same-origin' });
check('D8 sec-fetch-site same-origin is refused', sameSite.status === 400,
  'got ' + sameSite.status);

/* D9 · THE NAVIGATE BRANCH, AND WHY IT CANNOT BE PROBED WITH fetch()
   ---------------------------------------------------------------------------
   `Sec-Fetch-Mode` is a FORBIDDEN REQUEST HEADER under the Fetch standard, so
   it is browser-controlled by design: a page must not be able to forge it.
   Node's fetch (undici) implements that rule. MEASURED, not assumed:

     undici fetch, 'sec-fetch-mode: navigate' requested -> ARRIVES AS 'cors'
     raw socket,   'Sec-Fetch-Mode: navigate' sent      -> ARRIVES AS 'navigate'

   `Sec-Fetch-Site` is NOT on that list and passes through verbatim, which is
   why D8 works over fetch() and D9 could not.

   The original D9 therefore never reached the navigate branch at all. Its
   request arrived well-formed with mode=cors, passed fetchMetadataOk, passed
   validation, and was stopped by the WRITE SWITCH — a 503 'not_open', which is
   the CORRECT answer. The 400 it expected was never reachable. Confirmed
   locally against the Worker module:

     mode=cors     (what really arrived) -> 503 not_open
     mode=navigate (what D9 intended)    -> 400 refused

   So the branch IS externally observable — just not through a Fetch-spec
   client. This replacement uses a raw TLS socket, which is bound by no such
   rule, exactly as curl is not. node:tls is built in, so no new dependency.
   Local G20 remains the direct unit proof of fetchMetadataOk(). */
import tls from 'node:tls';

function rawRequest(urlStr, extraHeaders) {
  const u = new URL(urlStr);
  const payload = JSON.stringify(growerBody);
  const head =
    `POST ${u.pathname} HTTP/1.1\r\n` +
    `Host: ${u.hostname}\r\n` +
    Object.entries(extraHeaders).map(([k, v]) => `${k}: ${v}`).join('\r\n') + '\r\n' +
    `Content-Type: application/json\r\n` +
    `Content-Length: ${Buffer.byteLength(payload)}\r\n` +
    `Connection: close\r\n\r\n`;
  return new Promise((resolve) => {
    let buf = '';
    const s = tls.connect({ host: u.hostname, port: 443, servername: u.hostname }, () => {
      s.write(head + payload);
    });
    s.setEncoding('utf8');
    s.on('data', (d) => { buf += d; });
    const done = () => {
      const m = /^HTTP\/1\.[01] (\d{3})/.exec(buf);
      resolve({ status: m ? Number(m[1]) : null, raw: buf.slice(0, 200) });
    };
    s.on('end', done);
    s.on('error', (e) => resolve({ status: null, error: e.message }));
    setTimeout(() => { try { s.destroy(); } catch {} done(); }, 10000);
  });
}

const nav = await rawRequest(BASE + '/v1/garden-register/grower', {
  'Origin': ORIGIN,
  'Sec-Fetch-Site': 'cross-site',
  'Sec-Fetch-Mode': 'navigate'
});
if (nav.status === null) {
  /* Could not establish the raw connection at all. That is an environment
     fact, not a Worker fact, and it must not be reported as a pass. */
  line('N/A ', 'D9 navigate mode — RAW SOCKET UNAVAILABLE in this environment',
    nav.error || 'no status line; the branch stays proven LOCAL-ONLY by G20');
} else {
  check('D9 navigate mode is refused (raw socket, header not stripped)',
    nav.status === 400, 'got ' + nav.status + ' ' + nav.raw);
}

/* 5 · preflight answers only for the allowed origin ---------------------- */
const pre = await fetch(BASE + '/v1/garden-register/grower', {
  method: 'OPTIONS', headers: { origin: ORIGIN }
});
check('D10 preflight 204 for the allowed origin, echoing only that origin',
  pre.status === 204 && pre.headers.get('access-control-allow-origin') === ORIGIN,
  'got ' + pre.status + ' acao=' + pre.headers.get('access-control-allow-origin'));
const preEvil = await fetch(BASE + '/v1/garden-register/grower', {
  method: 'OPTIONS', headers: { origin: 'https://evil.example' }
});
check('D11 preflight 403 with no CORS header for anyone else',
  preEvil.status === 403 && !preEvil.headers.get('access-control-allow-origin'),
  'got ' + preEvil.status);

/* 7 · unknown routes ----------------------------------------------------- */
const nope = await call('/v1/garden-register/anything', growerBody);
check('D13 unknown path is 404', nope.status === 404, 'got ' + nope.status);

/* 6 · no email capability ------------------------------------------------ */
/* Re-sourced from refusal replies, since the two valid-body probes have moved
   out. These four write nothing in either switch state, so the assertion is
   switch-independent — and it means MORE with writes on, not less. */
check('D12 no reply mentions mail, token, confirm or verify',
  ![noOrigin, evil, sameSite, nope].some(
    (r) => /mail|token|confirm|verify/i.test(JSON.stringify(r.json))),
  JSON.stringify([noOrigin.json, evil.json, sameSite.json, nope.json]));

console.log(`\n  ${pass} passed, ${fail} failed`);
console.log('\n  STILL TO CHECK BY HAND (Airtable, not this Worker):');
console.log('    Gardens  tbltT83xG6E09PhjW  -> totalRecordCount must be 0');
console.log('    Growers  tblHECGCBXQDz6Kqc  -> totalRecordCount must be 0\n');
process.exit(fail ? 1 : 0);
