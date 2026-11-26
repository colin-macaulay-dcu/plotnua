// PlotNua · Package N STEP D · private end-to-end test of /v1/introduction against the DEPLOYED Worker.
// Run ONLY after founder approval of step D, with the public route still closed. Sends exactly ONE clearly-marked test
// request through the preview gate, then tells you what to verify by hand. Prints no key.
//   PNL_PREVIEW_KEY=... node test/e2e-private.mjs [https://plotnua-garden-lead.colin-a41.workers.dev]
const URL_ = (process.argv[2] || 'https://plotnua-garden-lead.colin-a41.workers.dev') + '/v1/introduction';
const KEY = process.env.PNL_PREVIEW_KEY || '';
if (KEY.length < 16) { console.log('REFUSED: set PNL_PREVIEW_KEY (the LEAD_PREVIEW_KEY secret) in the environment'); process.exit(2); }
const GENERAL = 'I agree that PlotNua may use the information I provide to review my enquiry and contact me about my project. My contact details will not be shared with a supplier without my further permission.';
const H = { origin: 'https://plotnua.ie', 'content-type': 'application/json', 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors' };
const body = { name: 'PlotNua Step D Test', email: process.env.PNL_TEST_EMAIL || 'colin@plotnua.ie', county: 'Dublin', timeframe: 'not-sure',
  description: 'STEP D PRIVATE TEST - not a homeowner. Delete after verification.', page: '/garden-room-prices-ireland.html',
  consent: true, consent_text: GENERAL, elapsed_ms: 5000, gotcha: '' };
const closed = await fetch(URL_, { method: 'POST', headers: H, body: JSON.stringify(body) }).then(r => r.json());
console.log((closed.state === 'not_open' ? 'PASS' : 'FAIL') + '  without the preview key the public route is closed (' + closed.state + ')');
const r = await fetch(URL_, { method: 'POST', headers: { ...H, 'x-plotnua-lead-preview': KEY }, body: JSON.stringify(body) });
const j = await r.json().catch(() => ({}));
const ok = r.status === 200 && j.ok === true && /^PNI-\d{8}-[0-9A-F]{8}$/.test(j.reference || '');
console.log((ok ? 'PASS' : 'FAIL') + `  preview request -> ${r.status} ${j.state}${j.reference ? ' ' + j.reference : ''}${j.field ? ' field=' + j.field : ''}`);
if (ok) console.log(`
Verify by hand, then record the results:
  1. Airtable "Introduction Requests" has ONE row ${j.reference}: kind general, status RECEIVED, test_record ticked,
     delete_after 12 months ahead, consent_text_hash present, no phone/Eircode/address field.
  2. The founder inbox has ONE email "PlotNua introduction request ${j.reference}" with reference, supplier
     "General", county Dublin, timeframe "Not sure yet" and NO name, email or description.
  3. Delete the row (or set its delete_after to yesterday and wait for the 03:23 UTC purge to prove retention).`);
process.exit(ok && closed.state === 'not_open' ? 0 : 1);
