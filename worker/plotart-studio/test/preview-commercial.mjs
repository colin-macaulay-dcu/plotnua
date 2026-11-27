// Screenshots of Studio → Commercial with SYNTHETIC data (local only): node test/preview-commercial.mjs <outdir>
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { createRequire } from 'node:module';
const require = createRequire('/tmp/claude-0/studio-tools/package.json');
const out = process.argv[2] || '/tmp';
const TOK = 'preview-token';
const S = await start({ port: 8895, enquiry: { LEAD_CAPTURE_ENABLED: 'true', LEAD_CAPTURE_TOKEN: TOK } });
await seedPublished(S.db, { id: 'apv1', slug: 'sample-painter', email: 'p1@example.test', name: 'Sample Painter', works: 3, number: 1 });
await seedPublished(S.db, { id: 'apv2', slug: 'example-artist', email: 'p2@example.test', name: 'Example Artist', works: 3, number: 2 });
await S.db.prepare("UPDATE artworks SET price_eur = 2000 WHERE artist_id = 'apv1'").run();
await S.db.prepare("UPDATE artworks SET price_eur = 3000 WHERE artist_id = 'apv2'").run();
const cap = msgs => S.mf.dispatchFetch('http://enquiry.local/v1/lead-capture', { method: 'POST', headers: { Authorization: 'Bearer ' + TOK }, body: JSON.stringify({ messages: msgs }) });
await cap([{ message_id: 'p1', thread_id: 't1', date: '2026-11-27T13:30:00Z', from: 'Alex Sample <alex@sample-hotel.example>', to: 'colin@plotnua.ie', subject: 'Artwork at the Sample Hotel', body: 'There are some fantastic pieces there. If you were interested in exploring options, it would be great to hear from you.', direction: 'in' },
  { message_id: 'p2', thread_id: 't1', date: '2026-11-27T13:47:00Z', from: 'Colin <colin@plotnua.ie>', to: 'alex@sample-hotel.example', subject: 'Re: Artwork at the Sample Hotel', body: 'I’d be very interested in exploring options with you.', direction: 'out' },
  { message_id: 'p3', thread_id: 't2', date: '2026-11-24T13:00:00Z', from: 'Jordan Example <jordan@example-interiors.example>', to: 'hello@plotnua.ie', subject: 'RE: Working with Irish artists', body: 'We do have clients looking for artwork from time to time.', direction: 'in' }]);
const H = { 'X-Studio': '1', 'Content-Type': 'application/json', 'Cf-Access-Jwt-Assertion': token(FOUNDER) };
const api = (m, p, b) => S.mf.dispatchFetch(S.url + p, { method: m, headers: H, body: b ? JSON.stringify(b) : undefined }).then(r => r.json());
const L = (await S.db.prepare("SELECT id FROM commercial_leads WHERE gmail_thread_id='t1'").first()).id;
const w = (await S.db.prepare("SELECT id FROM artworks ORDER BY artist_id, ord").all()).results;
await api('PATCH', '/api/admin/commercial/leads/' + L, { business: 'The Sample Hotel', sector: 'hotel', stage: 'artist_approval', next_action: 'Send the selection of four works', next_action_on: '2026-12-02', location: 'Co. Kildare' });
for (const id of [w[0].id, w[1].id, w[3].id]) await api('POST', `/api/admin/commercial/leads/${L}/selections`, { artwork_id: id, arrangement: 'rental' });
const sel = (await api('GET', '/api/admin/commercial/leads/' + L)).selections;
await api('PATCH', '/api/admin/commercial/selections/' + sel[0].id, { status: 'artist_approved', evidence: 'Email from the artist, 28 Nov' });
await api('PATCH', '/api/admin/commercial/selections/' + sel[1].id, { status: 'artist_asked' });
await api('POST', `/api/admin/commercial/leads/${L}/documents`, { kind: 'proposal', number: 'PA-PR-001', status: 'draft' });
const { chromium } = require('playwright');
const b = await chromium.launch(), ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, extraHTTPHeaders: { 'Cf-Access-Jwt-Assertion': token(FOUNDER) } });
const p = await ctx.newPage();
await p.goto(S.url + '/admin/commercial', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
await p.screenshot({ path: out + '/studio-commercial-list.png', fullPage: true });
await p.goto(S.url + '/admin/commercial#/lead/' + L, { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
await p.screenshot({ path: out + '/studio-commercial-lead.png', fullPage: true });
await b.close(); await S.mf.dispose(); console.log('ok');
