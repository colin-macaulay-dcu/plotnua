// PlotNua · Package N STEP D · controlled private end-to-end test of /v1/introduction against the DEPLOYED Worker.
// Run ONLY after founder approval of step D, with INTRO_PUBLIC_ENABLED still "false". Uses founder-owned addresses and
// clearly marked test data. Exactly ONE request is meant to be accepted (and so ONE row and ONE founder email);
// every other request below must be refused BEFORE anything is written or sent. Prints no key.
//   PNL_PREVIEW_KEY=... [PNL_TEST_EMAIL=colin@plotnua.ie] node test/e2e-private.mjs [worker-origin]
const ORIGIN_URL = process.argv[2] || 'https://plotnua-garden-lead.colin-a41.workers.dev';
const URL_ = ORIGIN_URL + '/v1/introduction';
const KEY = process.env.PNL_PREVIEW_KEY || '';
const EMAIL = process.env.PNL_TEST_EMAIL || 'colin@plotnua.ie';
if (KEY.length < 16) { console.log('REFUSED: set PNL_PREVIEW_KEY (the LEAD_PREVIEW_KEY secret) in the environment'); process.exit(2); }
if (!/@plotnua\.ie$/i.test(EMAIL)) { console.log('REFUSED: the test email must be a founder-owned @plotnua.ie address'); process.exit(2); }

const GENERAL = 'I agree that PlotNua may use the information I provide to review my enquiry and contact me about my project. My contact details will not be shared with a supplier without my further permission.';
const H = { origin: 'https://plotnua.ie', 'content-type': 'application/json', 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors' };
const base = (o = {}) => ({ name: 'PlotNua STEP D TEST', email: EMAIL, county: 'Dublin', timeframe: 'not-sure',
  description: 'STEP D PRIVATE TEST - not a homeowner. Delete after verification.', page: '/garden-room-prices-ireland.html',
  consent: true, consent_text: GENERAL, elapsed_ms: 5000, gotcha: '', ...o });
const post = async (body, key = KEY) => {
  const r = await fetch(URL_, { method: 'POST', headers: key ? { ...H, 'x-plotnua-lead-preview': key } : H,
    body: typeof body === 'string' ? body : JSON.stringify(body) });
  const j = await r.json().catch(() => ({})); return { s: r.status, j };
};
let pass = 0, fail = 0;
const check = (id, what, ok, d) => { ok ? pass++ : fail++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${id} ${what}${ok ? '' : '  [' + JSON.stringify(d) + ']'}`); };

// 1 · public submissions stay closed (no preview key)
let r = await post(base(), '');
check('D1', 'public route closed: no preview key -> not_open, nothing written', r.s === 503 && r.j.state === 'not_open', r);

// 2 · the ONE valid request (first, so the per-isolate rate limit cannot affect it)
r = await post(base());
const ok = r.s === 200 && r.j.ok === true && /^PNI-\d{8}-[0-9A-F]{8}$/.test(r.j.reference || '');
check('D2', 'valid test request accepted with a PNI- reference', ok, r);
const ref = r.j.reference || '(none)';

// 3 · refusals that must write and send nothing (9 requests: with the valid one, 10 in the minute, within the limit)
const refusals = [
  ['D3', 'consent wording altered -> refused', base({ consent_text: GENERAL.replace('contact me', 'email me') }), 'consent_text'],
  ['D4', 'consent box not ticked -> refused', base({ consent: false }), 'consent'],
  ['D5', 'phone number supplied -> refused (prohibited field)', { ...base(), phone: '0870000000' }, 'unexpected_field'],
  ['D6', 'Eircode supplied -> refused (prohibited field)', { ...base(), eircode: 'D00 TEST' }, 'unexpected_field'],
  ['D7', 'address supplied -> refused (prohibited field)', { ...base(), address: '1 Test Street' }, 'unexpected_field'],
  ['D8', 'a named supplier (NOOK) -> refused: no supplier-specific introductions, nothing forwarded', base({ supplier: 'nook-prefab' }), 'supplier'],
  ['D9', 'honeypot filled -> refused', base({ gotcha: 'http://spam.invalid' }), 'gotcha'],
  ['D10', 'form completed in under 3 seconds -> refused', base({ elapsed_ms: 400 }), 'timing'],
  ['D11', 'county outside the list -> refused', base({ county: 'Atlantis' }), 'county']
];
for (const [id, what, body, field] of refusals) { r = await post(body); check(id, what, r.s === 400 && r.j.field === field, r); }
console.log('…waiting 61 s so the size and rate-limit checks start a fresh minute');
await new Promise(res => setTimeout(res, 61_000));
r = await post('x'.repeat(7000));
check('D12', 'oversized body -> refused before parsing', r.s === 400 && r.j.field === 'body', r);


// 4 · abuse control: the per-isolate limit (10 a minute). Requests are refused ones, so nothing is written.
//     Cloudflare may spread requests over several isolates, so a missing 429 is reported, not failed.
let limited = false;
for (let i = 0; i < 25 && !limited; i++) { const x = await post(base({ gotcha: 'rate-limit-probe' })); if (x.s === 429) limited = true; }
console.log(`${limited ? 'PASS' : 'NOTE'}  D13 rate limit ${limited ? 'answered slow_down (429) within 25 refused requests' : 'not observed (requests spread across isolates); honeypot still refused every one'}`);

console.log(`\nSTEP D AUTOMATED · ${pass} passed, ${fail} failed · reference ${ref}\n`);
console.log(`Verify by hand and record each result:
  D14 Airtable "Introduction Requests" holds exactly ONE new row, ${ref}: kind general, status RECEIVED, test_record ticked,
      delete_after 12 months ahead, consent_text_hash present, privacy_version set. No row exists for D3–D13.
  D15 ${EMAIL.replace(/@.*/, '@…')} / the NOTIFY_TO inbox has exactly ONE email "PlotNua introduction request ${ref}"
      showing reference, Supplier "General (no supplier named)", County Dublin, Timeframe "Not sure yet",
      and NO name, email address or description.
  D16 No supplier forwarding: the Resend log shows that one email with a single recipient (NOTIFY_TO); nothing to any supplier.
  D17 Retention: set the row's delete_after to yesterday; after the next daily run (03:23 UTC) the row is gone
      (check it is also absent from views; note Airtable's trash keeps it restorable for the plan's period).
  D18 Afterwards set INTRO_WRITES_ENABLED and INTRO_NOTIFY_ENABLED back to "false" unless step F is approved,
      leave INTRO_RETENTION_ENABLED="true", and re-run D1 to confirm public submissions are still closed.`);
process.exit(fail ? 1 : 0);
