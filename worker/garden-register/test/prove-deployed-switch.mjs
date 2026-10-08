/* G2 · DEPLOYED SWITCH-DEPENDENT CONTROLS — D1 AND D2
 * ===========================================================================
 * These are the only two deployed assertions whose MEANING depends on
 * WRITES_ENABLED, and the only two that carry a body the Worker would actually
 * write. They were split out of prove-deployed.mjs on 8 October 2026 under
 * founder decision D-G5-3, because that file claimed it could not create a
 * record while carrying two bodies that could.
 *
 * THERE IS NO DEFAULT MODE. You must say which answer you expect, because the
 * two expectations are opposites and one of them writes to Airtable:
 *
 *   --expect-closed   WRITES_ENABLED="false". Both routes must return
 *                     503 { state: 'not_open' }. NOTHING IS WRITTEN.
 *
 *   --expect-open     WRITES_ENABLED="true". Both routes must return
 *                     200 { state: 'received' } — and each one CREATES THREE
 *                     AIRTABLE ROWS: a Gardens/Growers row, a Status log row
 *                     and a Consent proof row. Six rows in total. The script
 *                     prints exactly what it is about to write and pauses, so
 *                     the rows are planned rather than discovered afterwards.
 *
 * Addresses use the reserved .invalid TLD (RFC 2606), which can never be
 * delivered to. They are stored in clear in Gardens/Growers, so they must be
 * synthetic and they must be counted in the G5 clean-up.
 *
 *   node test/prove-deployed-switch.mjs https://<worker>.workers.dev --expect-closed
 *   node test/prove-deployed-switch.mjs https://<worker>.workers.dev --expect-open
 * ========================================================================= */
const BASE = process.argv[2];
const MODE = process.argv.find((a) => a === '--expect-closed' || a === '--expect-open');

if (!BASE || !/^https:\/\//.test(BASE) || !MODE) {
  console.error('\n  usage: node test/prove-deployed-switch.mjs https://<worker>.workers.dev' +
                ' (--expect-closed | --expect-open)');
  console.error('  Refusing to guess. --expect-open WRITES SIX AIRTABLE ROWS.\n');
  process.exit(2);
}
const OPEN = MODE === '--expect-open';
const ORIGIN = 'https://plotnua.ie';

/* Byte-identical to CONSENT_TEXT in src/index.js. The Worker hashes what
   arrives and compares; one character adrift is a 400 on consent_text, which
   would make a closed-state pass look like a switch result when it is not. */
const GARDEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.";
const GROWER_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby.";

const GARDEN_EMAIL = 'deployprobe@plotnua.invalid';
const GROWER_EMAIL = 'deployprobe2@plotnua.invalid';

const gardenBody = {
  first_name: 'Deploy', email: GARDEN_EMAIL, district: 'raheny',
  water: 'outside_tap', size_note: 'small', timing: 'flexible',
  inherited_tenure: 'own', over_18: true, consent_text: GARDEN_CONSENT
};
const growerBody = {
  first_name: 'Deploy', email: GROWER_EMAIL, district: 'raheny',
  travel_radius: 'walking', space_wanted: 'small', timing: 'flexible',
  over_18: true, consent_text: GROWER_CONSENT
};

let pass = 0, fail = 0;
function check(name, cond, detail) {
  if (cond) { pass++; console.log(`  [PASS] ${name}`); }
  else { fail++; console.log(`  [FAIL] ${name}   ${detail || ''}`); }
}

async function call(path, body) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: {
      'content-type': 'application/json', origin: ORIGIN,
      'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors'
    },
    body: JSON.stringify(body)
  });
  let j = null; try { j = await r.json(); } catch { /* non-JSON is a finding */ }
  return { status: r.status, json: j };
}

console.log('\n  DEPLOYED SWITCH-DEPENDENT CONTROLS · ' + BASE);
console.log('  MODE: ' + MODE + '\n');

if (OPEN) {
  console.log('  *** THIS RUN WILL WRITE TO AIRTABLE ***');
  console.log('  Two accepted submissions, three rows each, six rows in total:');
  console.log('    Gardens      <- ' + GARDEN_EMAIL + '  (inherited_tenure: own)');
  console.log('    Growers      <- ' + GROWER_EMAIL);
  console.log('    Status log   <- 2 rows, from_status "" -> interest_submitted');
  console.log('    Consent proofs <- 2 rows, email_hash only, never the address');
  console.log('  Both addresses use the reserved .invalid TLD and are synthetic.');
  console.log('  They must be included in the G5 erasure and clean-up count.\n');
  await new Promise((r) => setTimeout(r, 3000));
}

const g = await call('/v1/garden-register/garden', gardenBody);
const w = await call('/v1/garden-register/grower', growerBody);

if (OPEN) {
  check('D1 garden route accepts: 200 received (writes are ON)',
    g.status === 200 && g.json && g.json.state === 'received',
    'got ' + g.status + ' ' + JSON.stringify(g.json));
  check('D2 grower route accepts: 200 received (writes are ON)',
    w.status === 200 && w.json && w.json.state === 'received',
    'got ' + w.status + ' ' + JSON.stringify(w.json));
} else {
  check('D1 garden route refuses: not_open (writes are off)',
    g.status === 503 && g.json && g.json.state === 'not_open',
    'got ' + g.status + ' ' + JSON.stringify(g.json));
  check('D2 grower route refuses: not_open (writes are off)',
    w.status === 503 && w.json && w.json.state === 'not_open',
    'got ' + w.status + ' ' + JSON.stringify(w.json));
}

/* Holds in BOTH modes. There is no mail adapter in this Worker at all, so a
   reply that mentions any of these would mean the deployment is not the source
   that was read. */
check('D12a no reply mentions mail, token, confirm or verify',
  ![g, w].some((r) => /mail|token|confirm|verify/i.test(JSON.stringify(r.json))),
  JSON.stringify([g.json, w.json]));

console.log(`\n  ${pass} passed, ${fail} failed`);
console.log('\n  AIRTABLE, BY HAND — the only place the truth is:');
if (OPEN) {
  console.log('    Gardens        tbltT83xG6E09PhjW  -> expect +1 (' + GARDEN_EMAIL + ')');
  console.log('    Growers        tblHECGCBXQDz6Kqc  -> expect +1 (' + GROWER_EMAIL + ')');
  console.log('    Status log     tblB61wADVHxJB0b2  -> expect +2');
  console.log('    Consent proofs tblIuSP62HLWg4EYF  -> expect +2, email_hash only');
  console.log('    Incidents      tbl3HiqUivrsnGndl  -> expect 0\n');
} else {
  console.log('    all five tables -> totalRecordCount must be UNCHANGED');
  console.log('    Gardens tbltT83xG6E09PhjW · Growers tblHECGCBXQDz6Kqc');
  console.log('    Status log tblB61wADVHxJB0b2 · Consent proofs tblIuSP62HLWg4EYF');
  console.log('    Incidents tbl3HiqUivrsnGndl\n');
}
process.exit(fail ? 1 : 0);
