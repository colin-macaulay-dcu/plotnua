/* PLOTART FOUNDING 25 · ISOLATED END-TO-END TEST HARNESS (28 Oct 2026)
 * ===========================================================================
 * LOCAL ONLY. Nothing here reaches Cloudflare, Airtable or plotnua.ie.
 *
 *   node test/f25-e2e-harness.mjs <test-site-dir> <production-tree-dir>
 *
 *   http://localhost:8790   the test build of the Founding 25 page (made with
 *                           build-plotart.py --launch --test-endpoint ...), other
 *                           site assets served from the production tree
 *   http://127.0.0.1:8791   THE REAL WORKER CODE (src/index.js), env = the
 *                           [env.test] block of wrangler.toml, with fetch()
 *                           pointed at a STRICT IN-MEMORY AIRTABLE (below)
 *   http://127.0.0.1:8792   test controls: /reset, /records, /fail?status=,
 *                           /hang?ms=, /drop (close the next connection)
 *
 * The in-memory Airtable enforces what the real one does with typecast:false:
 * unknown field -> 422, a select value that is not an option -> 422, wrong
 * types -> 422, and it supports exactly the two filter formulas the route
 * uses. Its tables come from airtable-schema-founding-25.proposed.json and
 * airtable-schema.json, with the planned 'founding_25' register option.
 * ========================================================================= */
import http from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, extname, normalize } from 'node:path';
import worker, { __test as T } from '../src/index.js';

const [, , SITE, PROD] = process.argv;
if (!SITE || !PROD) { console.error('usage: f25-e2e-harness.mjs <test-site-dir> <production-tree-dir>'); process.exit(2); }

/* ---- env: the [env.test] block, plus fake secrets ---- */
const toml = readFileSync(new URL('../wrangler.toml', import.meta.url), 'utf8');
const testBlock = toml.split('[env.test.vars]')[1].split('[env.test.observability]')[0];
const ENV = { ...Object.fromEntries([...testBlock.matchAll(/^([A-Z0-9_]+)\s*=\s*"([^"]*)"/gm)].map(m => [m[1], m[2]])),
              AIRTABLE_BASE: 'appTESTHARNESS001', AIRTABLE_TOKEN: 'patTEST_HARNESS_ONLY' };
if (ENV.ORIGIN !== 'http://localhost:8790' || ENV.WRITES_ENABLED !== 'false' || ENV.ARTIST_WRITES_ENABLED !== 'false') {
  console.error('REFUSED: [env.test] must be local-only with the Host and Artist routes off'); process.exit(2);
}

/* ---- strict in-memory Airtable ---- */
const f25 = JSON.parse(readFileSync(new URL('../airtable-schema-founding-25.proposed.json', import.meta.url), 'utf8'));
const live = JSON.parse(readFileSync(new URL('../airtable-schema.json', import.meta.url), 'utf8'));
const REG = ['host', 'artist', 'founding_25'];
function tableDef(name, fields) {
  return { name, fields: Object.fromEntries(fields.filter(f => f.type !== 'formula').map(f => {
    let opts = f.options && (Array.isArray(f.options) ? f.options : (f.options.choices || []).map(c => c.name || c));
    if (f.name === 'register') opts = REG;
    return [f.name, { type: f.type, options: opts }];
  })) };
}
const DEFS = {
  'Founding 25 applications': tableDef('Founding 25 applications', f25.new_table.fields),
  'Status log': tableDef('Status log', live.tables.find(t => t.name === 'Status log').fields),
  'Consent proofs': tableDef('Consent proofs', live.tables.find(t => t.name === 'Consent proofs').fields)
};
let DB, ctl;
const reset = () => { DB = Object.fromEntries(Object.keys(DEFS).map(k => [k, []])); ctl = { fail: 0, hang: 0, drop: false, calls: [] }; };
reset();
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;
function validate(def, fields) {
  for (const [k, v] of Object.entries(fields)) {
    const f = def.fields[k];
    if (!f) return 'UNKNOWN_FIELD_NAME: ' + k;
    const t = f.type;
    if (['singleLineText', 'multilineText'].includes(t) && typeof v !== 'string') return 'INVALID_VALUE_FOR_COLUMN ' + k;
    if (t === 'singleLineText' && /\n/.test(v)) return 'INVALID_VALUE_FOR_COLUMN (newline) ' + k;
    if (t === 'email' && (typeof v !== 'string' || !/^[^\s@]+@[^\s@]+$/.test(v))) return 'INVALID_VALUE_FOR_COLUMN ' + k;
    if (t === 'url' && (typeof v !== 'string' || !/^https?:\/\//.test(v))) return 'INVALID_VALUE_FOR_COLUMN ' + k;
    if (t === 'checkbox' && typeof v !== 'boolean') return 'INVALID_VALUE_FOR_COLUMN ' + k;
    if (t === 'dateTime' && (typeof v !== 'string' || !ISO.test(v))) return 'INVALID_VALUE_FOR_COLUMN ' + k;
    if (t === 'singleSelect' && !(f.options || []).includes(v)) return 'INVALID_MULTIPLE_CHOICE_OPTIONS ' + k + '=' + v;
  }
  return null;
}
const jr = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { 'content-type': 'application/json' } });
async function airtable(url, init) {
  const u = new URL(url);
  ctl.calls.push({ method: init.method, path: decodeURIComponent(u.pathname) + (u.search ? '?…' : '') });
  if (init.headers.authorization !== 'Bearer ' + ENV.AIRTABLE_TOKEN) return jr(401, { error: 'AUTHENTICATION_REQUIRED' });
  if (ctl.hang) await new Promise(r => setTimeout(r, ctl.hang));
  if (ctl.fail) { const s = ctl.fail; ctl.fail = 0; return jr(s, { error: 'TEST_FAILURE' }); }
  const parts = decodeURIComponent(u.pathname).split('/');
  if (parts[2] !== ENV.AIRTABLE_BASE) return jr(404, { error: 'NOT_FOUND' });
  const table = parts[3], def = DEFS[table];
  if (!def) return jr(404, { error: 'TABLE_NOT_FOUND ' + table });
  if (init.method === 'GET') {
    const f = u.searchParams.get('filterByFormula') || '';
    const max = Number(u.searchParams.get('maxRecords') || 100);
    let rows = DB[table];
    let m;
    if ((m = /^OR\(\{email_key\}='((?:[^'\\]|\\.)*)',\{submission_id\}='((?:[^'\\]|\\.)*)'\)$/.exec(f))) {
      const un = (s) => s.replace(/\\(.)/g, '$1');
      rows = rows.filter(r => r.fields.email_key === un(m[1]) || r.fields.submission_id === un(m[2]));
    } else if (f === "IS_AFTER({submitted_at}, DATEADD(NOW(), -1, 'days'))") {
      rows = rows.filter(r => Date.parse(r.fields.submitted_at) > Date.now() - 864e5);
    } else return jr(422, { error: 'INVALID_FILTER_BY_FORMULA (harness supports only the route\'s two formulas)' });
    return jr(200, { records: rows.slice(0, max).map(r => ({ id: r.id, fields: {} })) });
  }
  if (init.method === 'POST') {
    const body = JSON.parse(init.body);
    if (body.typecast !== false) return jr(422, { error: 'HARNESS: typecast must be false' });
    const created = [];
    for (const rec of body.records) {
      const err = validate(def, rec.fields);
      if (err) return jr(422, { error: err });
    }
    for (const rec of body.records) {
      const row = { id: 'rec' + Math.random().toString(36).slice(2, 16).padEnd(14, '0'), createdTime: new Date().toISOString(), fields: rec.fields };
      DB[table].push(row); created.push(row);
    }
    return jr(200, { records: created });
  }
  return jr(405, { error: 'METHOD' });
}
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, init = {}) => {
  if (String(url).startsWith('https://api.airtable.com/')) return airtable(String(url), init);
  throw new Error('HARNESS: outbound network refused: ' + url);   /* nothing leaves this process */
};

/* ---- servers ---- */
const read = (req) => new Promise(r => { const c = []; req.on('data', d => c.push(d)); req.on('end', () => r(Buffer.concat(c))); });
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png',
               '.jpg': 'image/jpeg', '.webp': 'image/webp', '.json': 'application/json', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
http.createServer((req, res) => {
  let p = normalize(decodeURIComponent(new URL(req.url, 'http://x').pathname)).replace(/^(\.\.[\/\\])+/, '');
  if (p.endsWith('/')) p += 'index.html';
  for (const root of [SITE, PROD]) {
    const f = join(root, p);
    if (f.startsWith(root) && existsSync(f) && statSync(f).isFile()) {
      res.writeHead(200, { 'content-type': MIME[extname(f)] || 'application/octet-stream' });
      return res.end(readFileSync(f));
    }
  }
  res.writeHead(404); res.end('not found');
}).listen(8790, 'localhost');

http.createServer(async (req, res) => {
  if (ctl.drop) { ctl.drop = false; req.socket.destroy(); return; }
  const body = await read(req);
  const headers = new Headers();
  for (const [k, v] of Object.entries(req.headers)) if (typeof v === 'string') headers.set(k, v);
  const r = new Request('http://127.0.0.1:8791' + req.url, { method: req.method, headers,
    body: ['GET', 'HEAD', 'OPTIONS'].includes(req.method) ? undefined : body });
  const out = await worker.fetch(r, ENV);
  const h = {}; out.headers.forEach((v, k) => { h[k] = v; });
  res.writeHead(out.status, h);
  res.end(Buffer.from(await out.arrayBuffer()));
}).listen(8791, '127.0.0.1');

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  const send = (o) => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(o, null, 1)); };
  if (u.pathname === '/reset') { reset(); T.resetRateLimit(); return send({ ok: true }); }
  if (u.pathname === '/records') return send({ tables: DB, calls: ctl.calls });
  if (u.pathname === '/fail') { ctl.fail = Number(u.searchParams.get('status') || 500); return send({ ok: true }); }
  if (u.pathname === '/hang') { ctl.hang = Number(u.searchParams.get('ms') || 0); return send({ ok: true }); }
  if (u.pathname === '/drop') { ctl.drop = true; return send({ ok: true }); }
  if (u.pathname === '/rate-reset') { T.resetRateLimit(); return send({ ok: true }); }
  if (u.pathname === '/env') return send({ ...ENV, AIRTABLE_TOKEN: '(fake)', AIRTABLE_BASE: '(fake)' });
  res.writeHead(404); res.end();
}).listen(8792, '127.0.0.1');

console.log('F25 E2E HARNESS · page http://localhost:8790/plotart/founding-25.html · worker http://127.0.0.1:8791 · controls http://127.0.0.1:8792');
