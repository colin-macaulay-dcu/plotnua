/* PACKAGE N · INTRODUCTION REQUESTS · BEHAVIOUR PROOF
 * ===========================================================================
 * Asserts what POST /v1/introduction does. prove-introduction-mutations.mjs
 * asserts that these assertions can fail. Nothing reaches the network: both
 * Airtable and Resend are stubs, and every case asserts what the stubs were
 * asked to do as well as what the Worker answered.
 *
 *     node test/prove-introduction.mjs
 * ========================================================================= */
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import worker from '../src/index.js';
import * as I from '../src/introduction.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const ORIGIN = 'https://plotnua.ie';
const KEY = 'phase-a-preview-key-not-the-real-one';

let pass = 0, fail = 0;
const rows = [];
const check = (id, what, ok, d = '') => { ok ? pass++ : fail++; rows.push([ok ? 'PASS' : 'FAIL', id, what, ok ? '' : String(d).slice(0, 300)]); };

/* --------------------------------------------------------------- stubs ---- */
let calls = [], atMode = 'ok', mailOk = true;
globalThis.fetch = async (url, init) => {
  const u = String(url);
  calls.push({ url: u, headers: init.headers, body: JSON.parse(init.body) });
  if (u.startsWith('https://api.resend.com/')) return { ok: mailOk, status: mailOk ? 200 : 500, json: async () => ({}) };
  if (atMode === 'error') return { ok: false, status: 422, json: async () => ({}) };
  if (atMode === 'norec') return { ok: true, status: 200, json: async () => ({ records: [] }) };
  return { ok: true, status: 200, json: async () => ({ records: [{ id: 'recSTUB0000000001' }] }) };
};
const at = () => calls.filter(c => c.url.startsWith('https://api.airtable.com/'));
const mail = () => calls.filter(c => c.url.startsWith('https://api.resend.com/'));

const env = (o = {}) => ({
  ORIGIN, LEAD_PUBLIC_ENABLED: 'false', WRITES_ENABLED: 'false', EMAIL_ENABLED: 'false',
  INTRO_PUBLIC_ENABLED: 'false', INTRO_WRITES_ENABLED: 'true', INTRO_NOTIFY_ENABLED: 'false',
  INTRO_PRIVACY_VERSION: '2026-12-INTRODUCTIONS-V1',
  LEAD_PREVIEW_KEY: KEY, AIRTABLE_BASE: 'appSTUB', AIRTABLE_TOKEN: 'patSTUB', ...o
});
const NAME = 'Róisín Testperson', EMAIL = 'roisin.private@example.com', DESC = 'A small studio at the end of a long private garden';
const good = (o = {}) => ({
  name: NAME, email: EMAIL, county: 'Cork', timeframe: '3-6-months', description: DESC,
  page: '/suppliers/nook-prefab.html', consent: true, consent_text: I.GENERAL_CONSENT,
  elapsed_ms: 9000, gotcha: '', ...o
});
function req(body, o = {}) {
  const h = new Map(Object.entries({ origin: ORIGIN, 'sec-fetch-site': 'cross-site', 'sec-fetch-mode': 'cors',
    'content-type': 'application/json', 'x-plotnua-lead-preview': KEY, ...(o.headers || {}) }));
  return { method: 'POST', url: 'https://w.example' + (o.path || I.INTRO_PATH),
    headers: { get: k => (h.has(k.toLowerCase()) ? h.get(k.toLowerCase()) : null) },
    text: async () => (typeof body === 'string' ? body : JSON.stringify(body)) };
}
async function call(body, o = {}, e = {}, w = worker) {
  calls = []; I.resetIntroRateLimit();
  const res = await w.fetch(req(body, o), env(e));
  let j = null, t = '';
  try { t = await res.text(); j = JSON.parse(t); } catch { /* no body */ }
  return { s: res.status, j, t };
}
const noKey = { headers: { 'x-plotnua-lead-preview': '' } };

/* ===================================================== shipped state ==== */
const toml = readFileSync(join(HERE, '..', 'wrangler.toml'), 'utf8');
check('I01', 'INTRO_SUPPLIERS ships empty: no supplier-specific introduction is possible without a code change',
  Object.keys(I.INTRO_SUPPLIERS).length === 0 && Object.isFrozen(I.INTRO_SUPPLIERS));
check('I02', 'wrangler.toml ships INTRO_PUBLIC_ENABLED, INTRO_WRITES_ENABLED and INTRO_NOTIFY_ENABLED as "false", no key in it',
  /INTRO_PUBLIC_ENABLED\s*=\s*"false"/.test(toml) && /INTRO_WRITES_ENABLED\s*=\s*"false"/.test(toml) &&
  /INTRO_NOTIFY_ENABLED\s*=\s*"false"/.test(toml) && !/RESEND_API_KEY\s*=/.test(toml));
check('I03', 'the approved supplier sentence is used verbatim, with only the supplier name substituted',
  I.supplierConsent('Example Maker') === 'I agree that PlotNua may share my enquiry and contact details with Example Maker so they can contact me about this project.');

/* ============================================================== gates ==== */
{ const r = await call(good(), noKey);
  check('I04', 'closed by default: public off + no preview key -> not_open, nothing written or sent', r.s === 503 && r.j.state === 'not_open' && calls.length === 0, r.t); }
{ const r = await call(good(), { headers: { 'x-plotnua-lead-preview': 'wrong-key-wrong-key-xx' } });
  check('I05', 'a wrong preview key is not_open, nothing written', r.s === 503 && calls.length === 0, r.t); }
{ const r = await call(good(), noKey, { LEAD_PUBLIC_ENABLED: 'true', WRITES_ENABLED: 'true' });
  check('I06', "opening the Yard Box route's switches does not open introductions", r.s === 503 && r.j.state === 'not_open' && calls.length === 0, r.t); }
{ const r = await call({}, { path: '/v1/garden-lead/enquiry', headers: { 'x-plotnua-lead-preview': '' } }, { INTRO_PUBLIC_ENABLED: 'true' });
  check('I07', 'opening introductions does not open the Yard Box route', r.s === 503 && r.j.state === 'not_open' && calls.length === 0, r.t); }
{ const r = await call(good(), {}, { INTRO_WRITES_ENABLED: 'false', WRITES_ENABLED: 'true' });
  check('I08', 'INTRO_WRITES_ENABLED off -> not_open and nothing written, even with the Yard Box writes switch on', r.s === 503 && calls.length === 0, r.t); }

/* ============================================== a general request ======= */
const NOW = Date.now();
{ const r = await call(good());
  const a = at(), f = a[0] && a[0].body.records[0].fields;
  check('I09', 'a valid general request -> 200 received with a PNI- reference, one Airtable write and no email',
    r.s === 200 && r.j.ok === true && /^PNI-\d{8}-[0-9A-F]{8}$/.test(r.j.reference) && a.length === 1 && mail().length === 0, r.t);
  check('I10', 'written to "Introduction Requests" with typecast:false, status RECEIVED, kind general, no supplier',
    a[0] && a[0].url.endsWith('/' + encodeURIComponent('Introduction Requests')) && a[0].body.typecast === false &&
    f.status === 'RECEIVED' && f.kind === 'general' && f.supplier_slug === '' && f.supplier_name === '', JSON.stringify(f));
  const exp = new Date(NOW); exp.setUTCMonth(exp.getUTCMonth() + 12);
  check('I11', 'every record carries delete_after = created + 12 months', f && f.delete_after === exp.toISOString().slice(0, 10), f && f.delete_after);
  check('I12', 'the record keeps the approved fields only: no phone, Eircode or address field exists',
    f && Object.keys(f).sort().join() === ['request_id','created_at','kind','supplier_slug','supplier_name','homeowner_name','homeowner_email','county','timeframe','description','page','consent_text_hash','consent_at','privacy_version','status','delete_after','test_record'].sort().join(), f && Object.keys(f).join());
  check('I13', 'while the public route is closed every record is marked test_record:true', f && f.test_record === true);
  check('I14', 'the reply carries the reference only: none of the homeowner\'s details are echoed', !r.t.includes(EMAIL) && !r.t.includes('Testperson') && !r.t.includes('private garden'), r.t);
  check('I15', 'the consent hash recorded is the hash of the approved general sentence', f && f.consent_text_hash === await I.sha256Hex(I.GENERAL_CONSENT)); }
{ const r = await call(good({ description: undefined }));
  check('I16', 'the project description is optional', r.s === 200 && at()[0].body.records[0].fields.description === '', r.t); }
{ const r = await call(good(), {}, { INTRO_PUBLIC_ENABLED: 'true' }, worker);
  check('I17', 'public route open -> no preview key needed and test_record:false', r.s === 200 && at()[0].body.records[0].fields.test_record === false, r.t); }

/* ======================================================== refusals ====== */
const refusals = [
  ['I18', 'a named supplier not on the written-agreement list is refused, nothing written', good({ supplier: 'nook-prefab' }), 'supplier'],
  ['I19', 'a phone number field is refused (closed payload)', good({ phone: '0871234567' }), 'unexpected_field'],
  ['I20', 'an Eircode or address field is refused (closed payload)', good({ eircode: 'T12 X3Y4' }), 'unexpected_field'],
  ['I21', 'the honeypot is refused', good({ gotcha: 'http://spam.example' }), 'gotcha'],
  ['I22', 'a form completed in under 3 seconds is refused', good({ elapsed_ms: 1200 }), 'timing'],
  ['I23', 'a missing timing value is refused', good({ elapsed_ms: undefined }), 'timing'],
  ['I24', 'no consent tick -> refused (nothing preselected server-side either)', good({ consent: 'true' }), 'consent'],
  ['I25', 'consent wording that drifts from the approved sentence is refused', good({ consent_text: I.GENERAL_CONSENT.replace('reply to me', 'contact me') }), 'consent_text'],
  ['I26', 'the supplier sentence cannot be used for a general request', good({ consent_text: I.supplierConsent('Anyone') }), 'consent_text'],
  ['I27', 'a county outside the island-of-Ireland list is refused', good({ county: 'Narnia' }), 'county'],
  ['I28', 'a timeframe outside the five options is refused', good({ timeframe: 'yesterday' }), 'timeframe'],
  ['I29', 'an invalid email is refused', good({ email: 'not-an-email' }), 'email'],
  ['I30', 'a missing name is refused', good({ name: '  ' }), 'name'],
  ['I31', 'a page that is not a plotnua.ie path is refused', good({ page: 'https://evil.example/x.html' }), 'page']
];
for (const [id, what, body, field] of refusals) {
  const r = await call(body);
  check(id, what, r.s === 400 && r.j.field === field && calls.length === 0, r.t);
}
{ const r = await call('x'.repeat(7000));
  check('I32', 'a body over the size cap is refused before parsing', r.s === 400 && r.j.field === 'body' && calls.length === 0, r.t); }

/* ======================================================== failures ====== */
atMode = 'error';
{ const r = await call(good(), {}, { INTRO_NOTIFY_ENABLED: 'true', RESEND_API_KEY: 're_stub', NOTIFY_TO: 'founder@example.test', NOTIFY_FROM: 'n@example.test' });
  check('I33', 'Airtable refuses -> unavailable, nothing claimed, and NO founder email for a request that was not stored', r.s === 503 && r.j.state === 'unavailable' && mail().length === 0, r.t); }
atMode = 'norec';
{ const r = await call(good());
  check('I34', 'Airtable answers without a record id -> unavailable (success requires a persisted row)', r.s === 503 && r.j.state === 'unavailable', r.t); }
atMode = 'ok';

/* =================================================== founder notice ===== */
const N = { INTRO_NOTIFY_ENABLED: 'true', RESEND_API_KEY: 're_stub', NOTIFY_TO: 'founder@example.test', NOTIFY_FROM: 'notify@example.test' };
{ const r = await call(good(), {}, { ...N, INTRO_NOTIFY_ENABLED: 'false' });
  check('I35', 'notify switch off -> no email, even with the Resend key present', r.s === 200 && mail().length === 0); }
{ const r = await call(good(), {}, { ...N, RESEND_API_KEY: '' });
  check('I36', 'notify switch on but no Resend key -> no email', r.s === 200 && mail().length === 0); }
{ const r = await call(good(), {}, N);
  const m = mail(), body = m[0] ? JSON.stringify(m[0].body) : '';
  check('I37', 'notify on -> exactly one email, to the founder address only, sent after the row exists',
    r.s === 200 && m.length === 1 && JSON.stringify(m[0].body.to) === '["founder@example.test"]' && calls[0].url.startsWith('https://api.airtable.com/'), JSON.stringify(m.map(x => x.body)));
  check('I38', 'the founder email carries reference, county and timeframe',
    body.includes(r.j.reference) && body.includes('Cork') && body.includes('3 to 6 months'), body);
  check('I39', "the founder email carries none of the homeowner's name, email or description",
    !body.includes(EMAIL) && !body.includes('Testperson') && !body.includes('private garden') && !body.includes('@example.com'), body);
  check('I40', 'no email is ever addressed to a supplier: the only recipient is NOTIFY_TO',
    m.every(x => x.body.to.length === 1 && x.body.to[0] === N.NOTIFY_TO)); }
mailOk = false;
{ const r = await call(good(), {}, N);
  check('I41', 'a failed founder email does not fail the request (the row exists)', r.s === 200 && r.j.state === 'received', r.t); }
mailOk = true;

/* ================================================ supplier-specific ===== */
/* The shipped allow-list is empty, so the supplier path is exercised on a copy
   of this same source with one FIXTURE supplier. Mutations to the source reach
   the copy too. */
{
  const dir = mkdtempSync(join(tmpdir(), 'pn-intro-'));
  try {
    const src = readFileSync(join(HERE, '..', 'src', 'introduction.js'), 'utf8');
    const anchor = 'export const INTRO_SUPPLIERS = Object.freeze({});';
    if (!src.includes(anchor)) throw new Error('allow-list anchor missing');
    writeFileSync(join(dir, 'introduction.mjs'),
      src.replace(anchor, "export const INTRO_SUPPLIERS = Object.freeze({ 'fixture-maker': { name: 'Fixture Maker', agreement: 'TEST' } });"));
    const F = await import(pathToFileURL(join(dir, 'introduction.mjs')).href);
    const json = (status, obj) => ({ status, text: async () => JSON.stringify(obj) });
    const fcall = async (b, e = {}) => { calls = []; F.resetIntroRateLimit();
      const res = await F.handleIntroduction(req(b), env(e), new Date(), ORIGIN, json); const t = await res.text(); return { s: res.status, j: JSON.parse(t), t }; };
    const sup = good({ supplier: 'fixture-maker', consent_text: F.supplierConsent('Fixture Maker') });
    let r = await fcall(sup, N);
    const f = at()[0] && at()[0].body.records[0].fields, mb = mail()[0] ? JSON.stringify(mail()[0].body) : '';
    check('I42', 'an allow-listed supplier with its exact named sentence -> received, kind supplier, supplier recorded',
      r.s === 200 && f && f.kind === 'supplier' && f.supplier_slug === 'fixture-maker' && f.supplier_name === 'Fixture Maker' &&
      f.consent_text_hash === await F.sha256Hex(F.supplierConsent('Fixture Maker')), r.t);
    check('I43', 'the founder email names the supplier but still carries no homeowner details, and goes to the founder only',
      mb.includes('Fixture Maker') && !mb.includes(EMAIL) && !mb.includes('Testperson') && mail()[0].body.to[0] === N.NOTIFY_TO, mb);
    r = await fcall(good({ supplier: 'fixture-maker' }));
    check('I44', 'the general sentence cannot be used to consent to a named supplier', r.s === 400 && r.j.field === 'consent_text' && calls.length === 0, r.t);
    r = await fcall(good({ supplier: 'fixture-maker', consent_text: F.supplierConsent('Another Maker') }));
    check('I45', 'the sentence must name THIS supplier', r.s === 400 && r.j.field === 'consent_text', r.t);
  } finally { rmSync(dir, { recursive: true, force: true }); }
}

/* ======================================================= rate limit ===== */
{ calls = []; I.resetIntroRateLimit(); let last;
  for (let i = 0; i < 11; i++) last = await worker.fetch(req(good()), env());
  check('I46', 'the 11th request in a minute from one isolate -> slow_down', last.status === 429); I.resetIntroRateLimit(); }

for (const [v, id, w, d] of rows) console.log(`  ${v}  ${id} ${w}${d ? '  [' + d + ']' : ''}`);
console.log(`\nINTRODUCTIONS · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
