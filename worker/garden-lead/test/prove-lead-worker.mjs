/* GARDEN ROOM LEAD WORKER · BEHAVIOUR PROOF
 * ===========================================================================
 * Asserts what the Worker does. prove-lead-mutations.mjs asserts that these
 * assertions can fail.
 *
 * Nothing here reaches the network: Airtable is a stub, and every case states
 * what the stub was asked to do as well as what the Worker answered. A case
 * that passes because the Worker never got as far as Airtable is a case that
 * proves nothing, so the stub's call count is asserted too.
 *
 *     node test/prove-lead-worker.mjs
 * ========================================================================= */

import worker, { __test } from '../src/index.js';

const ORIGIN = 'https://plotnua.ie';
const KEY = 'phase-a-preview-key-not-the-real-one';

const ORG = 'ORG-000157';
const PRODUCT = 'reckMDqp4tVjAjM7b';            /* The Vancouver */
const CONSENT = __test.SUPPLIERS[ORG].consentText;

let pass = 0, fail = 0;
const results = [];
function check(id, what, cond, detail) {
  if (cond) { pass++; results.push(['PASS', id, what, '']); }
  else { fail++; results.push(['FAIL', id, what, detail || '']); }
}

/* ---------------------------------------------------------- airtable stub -- */
let atCalls = [];
let atMode = 'ok';          /* ok | norec | error */
function installFetchStub() {
  globalThis.fetch = async (url, init) => {
    atCalls.push({ url: String(url), body: JSON.parse(init.body) });
    if (atMode === 'error') return { ok: false, status: 422, json: async () => ({}) };
    if (atMode === 'norec') return { ok: true, status: 200, json: async () => ({ records: [] }) };
    return { ok: true, status: 200, json: async () => ({ records: [{ id: 'recSTUB0000000001' }] }) };
  };
}
installFetchStub();

/* -------------------------------------------------------------- env/req ---- */
function env(over = {}) {
  return {
    ORIGIN,
    PRIVACY_VERSION: '2026-10-FIRSTLEAD-V1',
    LEAD_PUBLIC_ENABLED: 'false',
    WRITES_ENABLED: 'true',
    EMAIL_ENABLED: 'false',
    LEAD_PREVIEW_KEY: KEY,
    AIRTABLE_BASE: 'appSTUB',
    AIRTABLE_TOKEN: 'patSTUB',
    ...over
  };
}

function goodBody(over = {}) {
  return {
    supplier_org_id: ORG,
    product_id: PRODUCT,
    homeowner_name: 'Test Person',
    homeowner_email: 'test@example.com',
    county: 'Dublin',
    message: 'Hello, I found this through PlotNua and would like to ask about it.',
    consent: true,
    consent_text: CONSENT,
    gotcha: '',
    ...over
  };
}

function req(body, over = {}) {
  const headers = new Map(Object.entries({
    origin: ORIGIN,
    'sec-fetch-site': 'cross-site',
    'sec-fetch-mode': 'cors',
    'content-type': 'application/json',
    'x-plotnua-lead-preview': KEY,
    ...(over.headers || {})
  }));
  return {
    method: over.method || 'POST',
    url: over.url || 'https://w.example/v1/garden-lead/enquiry',
    headers: { get: (k) => (headers.has(k.toLowerCase()) ? headers.get(k.toLowerCase()) : null) },
    text: async () => JSON.stringify(body)
  };
}

async function call(body, over = {}, e = {}) {
  atCalls = [];
  __test.resetRateLimit();   /* each case measures itself, not the limiter */
  const res = await worker.fetch(req(body, over), env(e));
  let json = null;
  try { json = JSON.parse(await res.text()); } catch { /* 204/403 have no body */ }
  return { status: res.status, json, calls: atCalls.slice() };
}

/* ======================================================= the release gate == */
{
  const r = await call(goodBody(), { headers: { 'x-plotnua-lead-preview': '' } });
  check('L01', 'public closed + no preview key -> not_open, nothing written',
        r.status === 503 && r.json.state === 'not_open' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  const r = await call(goodBody(), { headers: { 'x-plotnua-lead-preview': 'wrong-key-wrong-key-xx' } });
  check('L02', 'public closed + wrong preview key -> not_open, nothing written',
        r.status === 503 && r.json.state === 'not_open' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  /* The header MATCHES the short secret, so only the length floor can refuse
     this. Sending the long key here would be refused by the comparison and the
     case would pass without ever exercising the floor. */
  const r = await call(goodBody(), { headers: { 'x-plotnua-lead-preview': 'tooshort' } },
                       { LEAD_PREVIEW_KEY: 'tooshort' });
  check('L03', 'a too-short preview secret closes the private route even when it matches',
        r.status === 503 && r.json.state === 'not_open' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  const r = await call(goodBody());
  check('L04', 'public closed + correct preview key -> accepted',
        r.status === 200 && r.json.ok === true, JSON.stringify(r.json));
}
{
  /* the public switch opens it without any key at all — which is exactly why
     it must stay 'false' until the founder flips it */
  const r = await call(goodBody(), { headers: { 'x-plotnua-lead-preview': '' } },
                       { LEAD_PUBLIC_ENABLED: 'true' });
  check('L05', 'LEAD_PUBLIC_ENABLED=true opens the route (and is why it ships false)',
        r.status === 200 && r.json.ok === true, JSON.stringify(r.json));
}

/* ========================================================== the allow-list == */
{
  const r = await call(goodBody({ supplier_org_id: 'ORG-000195' }));   /* TRIQBRIQ */
  check('L06', 'a supplier not on the allow-list is refused, nothing written',
        r.status === 400 && r.json.field === 'supplier_org_id' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  const r = await call(goodBody({ product_id: 'recLcmGihJ0mrfdwV' })); /* Powersheds */
  check('L07', 'another supplier’s product is refused, nothing written',
        r.status === 400 && r.json.field === 'product_id' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  const ids = Object.keys(__test.SUPPLIERS[ORG].products);
  let allOk = ids.length === 3;
  for (const id of ids) {
    const r = await call(goodBody({ product_id: id }));
    if (!(r.status === 200 && r.json.ok)) allOk = false;
  }
  check('L08', 'exactly the three authorised Yard Box products are accepted',
        allOk, 'ids=' + ids.join(','));
}
{
  const r = await call(goodBody({ product_id: 'recDOESNOTEXIST01' }));
  check('L09', 'an invented product id is refused', r.status === 400 && r.json.field === 'product_id');
}

/* ============================================================== validation == */
const badCases = [
  ['L10', 'missing name',    { homeowner_name: '' },            'homeowner_name'],
  ['L11', 'missing email',   { homeowner_email: '' },           'homeowner_email'],
  ['L12', 'malformed email', { homeowner_email: 'not-an-email' }, 'homeowner_email'],
  ['L13', 'missing county',  { county: '' },                    'county'],
  ['L14', 'empty message',   { message: '   ' },                'message'],
  ['L15', 'honeypot filled', { gotcha: 'http://spam.example' }, 'gotcha'],
  ['L16', 'consent not given', { consent: false },              'consent'],
  ['L17', 'consent sentence altered', { consent_text: CONSENT.replace('Yard Box', 'Someone Else') }, 'consent_text'],
  ['L18', 'source tampered', { source: 'plotnua.injected' },    'source']
];
for (const [id, what, over, field] of badCases) {
  const r = await call(goodBody(over));
  check(id, what + ' -> refused, nothing written',
        r.status === 400 && r.json.field === field && r.calls.length === 0,
        JSON.stringify(r.json));
}

/* =============================================================== transport == */
{
  const r = await call(goodBody(), {}, { WRITES_ENABLED: 'false' });
  check('L19', 'WRITES_ENABLED=false -> not_open, nothing written',
        r.status === 503 && r.json.state === 'not_open' && r.calls.length === 0,
        JSON.stringify(r.json));
}
{
  const r = await call(goodBody(), {}, { AIRTABLE_TOKEN: '' });
  check('L20', 'a missing Airtable token closes the route',
        r.status === 503 && r.json.state === 'not_open' && r.calls.length === 0);
}
{
  atMode = 'error';
  const r = await call(goodBody());
  atMode = 'ok';
  check('L21', 'an Airtable failure is unavailable, never success',
        r.status === 503 && r.json.state === 'unavailable' && r.json.ok === false,
        JSON.stringify(r.json));
}
{
  atMode = 'norec';
  const r = await call(goodBody());
  atMode = 'ok';
  check('L22', 'a write with NO returned record id is NOT success',
        r.status === 503 && r.json.ok === false && r.json.state === 'unavailable'
        && !r.json.lead_id, JSON.stringify(r.json));
}

/* ============================================================ the lead row == */
{
  const r = await call(goodBody());
  const f = r.calls[0] && r.calls[0].body.records[0].fields;
  check('L23', 'success returns ok + a minted lead_id',
        r.json.ok === true && typeof r.json.lead_id === 'string'
        && /^PNL-\d{8}-[0-9A-F]{8}$/.test(r.json.lead_id), JSON.stringify(r.json));
  check('L24', 'the row carries the right supplier attribution',
        f && f.supplier_org_id === ORG && f.supplier_name === 'Yard Box',
        JSON.stringify(f && { a: f.supplier_org_id, b: f.supplier_name }));
  check('L25', 'the row carries the right product attribution',
        f && f.product_id === PRODUCT && f.product_name === 'Yardbox The Vancouver',
        JSON.stringify(f && { a: f.product_id, b: f.product_name }));
  check('L26', 'the row carries source + status ceiling',
        f && f.source === __test.SOURCE && f.status === 'RECEIVED');
  check('L27', 'the row carries consent hash, consent time and privacy version',
        f && /^[0-9a-f]{64}$/.test(f.consent_text_hash) && !!f.consent_at
        && f.privacy_version === '2026-10-FIRSTLEAD-V1');
  check('L28', 'lead_id in the row equals the lead_id returned',
        f && f.lead_id === r.json.lead_id);
  check('L29', 'typecast is false on the write',
        r.calls[0] && r.calls[0].body.typecast === false);
  check('L30', 'the write goes to the Garden Room Leads table only',
        r.calls.length === 1 && /Garden%20Room%20Leads$/.test(r.calls[0].url),
        r.calls.map(c => c.url).join(' | '));

  /* NOTHING ABOUT THE PROPERTY TRAVELS. */
  const forbidden = ['eircode', 'address', 'lat', 'lon', 'latitude', 'longitude',
                     'coordinate', 'budget', 'rank', 'score', 'shortlist'];
  const blob = JSON.stringify(f).toLowerCase();
  check('L31', 'no eircode, address, coordinate, budget, rank or score in the row',
        forbidden.every(k => blob.indexOf(k) === -1),
        forbidden.filter(k => blob.indexOf(k) !== -1).join(','));

  check('L32', 'exactly the 15 agreed fields, no CRM extras',
        f && Object.keys(f).length === 15, f ? Object.keys(f).join(',') : 'none');
}

{
  const r = await call(goodBody({ lead_id: 'PNL-19700101-DEADBEEF' }));
  const f = r.calls[0] && r.calls[0].body.records[0].fields;
  check('L43', 'a caller-supplied lead_id is ignored and a fresh one minted',
        r.json.lead_id !== 'PNL-19700101-DEADBEEF'
        && f && f.lead_id !== 'PNL-19700101-DEADBEEF'
        && f.lead_id === r.json.lead_id,
        JSON.stringify({ returned: r.json.lead_id, row: f && f.lead_id }));
}

/* ===================================================== the Phase A marker == */
{
  const r = await call(goodBody());
  const f = r.calls[0].body.records[0].fields;
  check('L33', 'while the public route is closed, every lead is marked a Phase A test',
        /^\[PLOTNUA PHASE A TEST LEAD/.test(f.message), f.message.slice(0, 48));
}
{
  const r = await call(goodBody(), { headers: { 'x-plotnua-lead-preview': '' } },
                       { LEAD_PUBLIC_ENABLED: 'true' });
  const f = r.calls[0].body.records[0].fields;
  check('L34', 'a genuinely public lead carries no test marker',
        !/PHASE A TEST LEAD/.test(f.message), f.message.slice(0, 48));
}

/* ============================================================ the surface == */
{
  const r = await call(goodBody(), { method: 'GET' });
  check('L35', 'there is no GET handler', r.status === 405);
}
{
  const r = await call(goodBody(), { url: 'https://w.example/v1/garden-lead/list' });
  check('L36', 'no other path exists', r.status === 404 && r.calls.length === 0);
}
{
  const r = await call(goodBody(), { headers: { origin: 'https://evil.example' } });
  check('L37', 'a foreign origin is refused with no CORS headers',
        r.status === 403 && r.calls.length === 0);
}
{
  const r = await call(goodBody(), { headers: { 'sec-fetch-site': 'same-origin' } });
  check('L38', 'fetch metadata that is not a real cross-site cors call is refused',
        r.status === 400 && r.calls.length === 0);
}
{
  atCalls = [];
  __test.resetRateLimit();
  let last = null;
  for (let i = 0; i < 25; i++) last = await worker.fetch(req(goodBody()), env());
  const body = JSON.parse(await last.text());
  check('L39', 'the rate limit engages', body.state === 'slow_down', JSON.stringify(body));
}

/* ========================================================= no mail adapter == */
{
  const src = await (await import('node:fs/promises')).readFile(
    new URL('../src/index.js', import.meta.url), 'utf8');
  check('L40', 'EMAIL_ENABLED is declared and never used to send anything',
        src.indexOf('EMAIL_ENABLED') !== -1
        && !/sendEmail|nodemailer|ses\.|mailchannels|smtp/i.test(src));
  check('L41', 'no supplier email address appears anywhere in the Worker',
        !/@(yardbox|weareyardbox)\./i.test(src));
  check('L42', 'the status ceiling is the only status the Worker can write',
        !/FORWARDED|SUPPLIER_ACKNOWLEDGED|OUTCOME_KNOWN|NOT_FORWARDED/.test(
          src.replace(/\/\*[\s\S]*?\*\//g, '')));
}

/* ==================================================================== out == */
console.log('\n  GARDEN ROOM LEAD WORKER · BEHAVIOUR PROOF\n');
for (const [state, id, what, detail] of results) {
  console.log('  [' + state + '] ' + id + '  ' + what + (detail ? '  — ' + detail : ''));
}
console.log('\n  ' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
