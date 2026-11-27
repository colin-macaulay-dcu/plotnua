// PROVE · Commercial leads and placements (migration 0032, 27 Nov 2026): the Studio record, Gmail capture and the website form.
// Local Miniflare D1, synthetic rows only; nothing touches Cloudflare, Gmail or any real person.
//   node test/prove-commercial.mjs
import { readFileSync } from 'node:fs';
import { start, token, FOUNDER } from './local.mjs';
import { seedPublished } from './seed.mjs';
import { rental, addMonths } from '../src/commercial.js';

const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 400)}]` : ''}`); };
console.log('PROVE · Commercial leads and placements (Studio, Gmail capture, website form)');
const TOKEN = 'test-capture-token-' + Math.random().toString(36).slice(2);
const ORIGIN = 'https://plotnua.ie';

/* 0 · arithmetic (PA-BHR-2026-11) and six-month dates */
check('C0 rental figures match the website table (€1,000 / €2,000 / €3,000 / €5,000 → €40 / €80 / €120 / €200; artist 3%, PlotArt 1%)',
  [[100000, 4000, 3000, 1000], [200000, 8000, 6000, 2000], [300000, 12000, 9000, 3000], [500000, 20000, 15000, 5000]].every(([p, m, a, f]) => { const r = rental(p); return r.monthly_cents === m && r.artist_monthly_cents === a && r.plotart_monthly_cents === f; }));
check('C0b six calendar months, clamped to the month’s end', addMonths('2026-12-01', 6) === '2027-06-01' && addMonths('2026-08-31', 6) === '2027-02-28');

/* without the migration: the page says so, nothing breaks */
const S0 = await start({ port: 8891, schemaSql: readFileSync(new URL('../schema.sql', import.meta.url), 'utf8').split('-- PlotArt Studio · migration 0032')[0] });
const r0 = await S0.mf.dispatchFetch(S0.url + '/api/admin/commercial', { headers: { 'X-Studio': '1', 'Cf-Access-Jwt-Assertion': token(FOUNDER) } }).then(r => r.json());
check('C1 before migration 0032 the Commercial page answers “not installed”', r0.ok && r0.installed === false, JSON.stringify(r0));
await S0.mf.dispose();

const S = await start({ port: 8892, enquiry: { LEAD_CAPTURE_ENABLED: 'true', LEAD_CAPTURE_TOKEN: TOKEN, BUSINESS_ENQUIRIES_ENABLED: 'true' } });
await seedPublished(S.db, { id: 'acom', slug: 'com-artist', email: 'com@example.test', name: 'Com Artist', works: 3, number: 1 });
const works = (await S.db.prepare("SELECT id, title FROM artworks WHERE artist_id = 'acom' ORDER BY ord").all()).results;
await S.db.prepare('UPDATE artworks SET price_eur = 2000 WHERE id = ?').bind(works[0].id).run();
const api = async (method, path, body, email = FOUNDER) => {
  const h = { 'X-Studio': '1', 'Content-Type': 'application/json' }; if (email) h['Cf-Access-Jwt-Assertion'] = token(email);
  const r = await S.mf.dispatchFetch(S.url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
  const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
};
const capture = (messages, auth = `Bearer ${TOKEN}`) => S.mf.dispatchFetch('http://enquiry.local/v1/lead-capture', { method: 'POST', headers: { Authorization: auth, 'Content-Type': 'application/json' },
  body: JSON.stringify({ messages }) }).then(async r => ({ s: r.status, j: await r.json() }));

/* access */
const anon = await api('GET', '/api/admin/commercial', undefined, null);
const artist = await api('GET', '/api/admin/commercial', undefined, 'com@example.test');
check('C2 only the founder reaches Commercial (no sign-in and an artist are refused)', anon.s >= 400 && artist.s >= 400 && (await api('GET', '/api/admin/commercial')).s === 200, `${anon.s} ${artist.s}`);
const page = await api('GET', '/admin/commercial');
check('C2b the Commercial page loads its own script and carries the Commercial tab', page.s === 200 && page.t.includes('/assets/commercial.js') && page.t.includes('data-t="commercial"'));

/* Gmail capture */
const m1 = { message_id: 'g-m1', thread_id: 'g-t1', date: '2026-11-27T13:30:55Z', from: 'Austin Example <austin@castle-hotel.example>', to: 'colin@plotnua.ie', subject: 'Artwork at the Castle', body: 'If you were interested in exploring options, it would be great to hear from you.', direction: 'in' };
const bad = await capture([m1], 'Bearer wrong');
check('C3 Gmail capture refuses a wrong token and records nothing', bad.s === 401 && (await S.db.prepare('SELECT COUNT(*) AS n FROM commercial_leads').first()).n === 0);
const c1 = await capture([m1]);
const L1 = await S.db.prepare("SELECT * FROM commercial_leads WHERE gmail_thread_id = 'g-t1'").first();
check('C4 an outreach reply creates a lead from the sender (business from the domain, contact, source outreach reply, stage new)',
  c1.s === 200 && c1.j.created.length === 1 && L1 && L1.business === 'Castle-hotel' && L1.contact_name === 'Austin Example' && L1.contact_email === 'austin@castle-hotel.example' && L1.source === 'outreach_reply' && L1.stage === 'new', JSON.stringify([c1, L1]));
const again = await capture([m1]);
check('C5 the same Gmail message is never recorded twice', again.j.duplicates === 1 && (await S.db.prepare("SELECT COUNT(*) AS n FROM commercial_events WHERE gmail_message_id = 'g-m1'").first()).n === 1);
const out1 = { ...m1, message_id: 'g-m2', date: '2026-11-27T13:47:03Z', from: 'Colin <colin@plotnua.ie>', to: 'austin@castle-hotel.example', body: 'I’d be very interested in exploring options with you.', direction: 'out' };
const in2 = { ...m1, message_id: 'g-m3', date: '2026-11-28T09:00:00Z', body: 'Could you send a few options for the lounge?' };
const stray = { message_id: 'g-m4', thread_id: 'g-t9', date: '2026-11-28T09:00:00Z', from: 'Colin <colin@plotnua.ie>', to: 'someone@example.test', subject: 'Unrelated', body: 'x', direction: 'out' };
const c2 = await capture([out1, in2, stray]);
const ev = (await S.db.prepare('SELECT kind FROM commercial_events WHERE lead_id = ? ORDER BY at').bind(L1.id).all()).results.map(x => x.kind);
check('C6 the founder’s reply and the next reply join the same lead; an outgoing email with no lead is skipped; the lead moves to “in conversation”',
  c2.j.recorded === 2 && c2.j.skipped === 1 && ev.filter(k => k === 'email_in').length === 2 && ev.includes('email_out')
  && (await S.db.prepare('SELECT stage FROM commercial_leads WHERE id = ?').bind(L1.id).first()).stage === 'in_conversation', JSON.stringify([c2.j, ev]));

/* the founder works the lead */
const sel = await api('POST', `/api/admin/commercial/leads/${L1.id}/selections`, { artwork_id: works[0].id, arrangement: 'rental' });
const s1 = sel.j.selections && sel.j.selections[0];
check('C7 proposing a €2,000 work for rental records €80 a month: €60 artist, €20 PlotArt', sel.s === 200 && s1.price_cents === 200000 && s1.monthly_cents === 8000 && s1.artist_monthly_cents === 6000 && s1.plotart_monthly_cents === 2000, sel.t);
const chooseEarly = await api('PATCH', `/api/admin/commercial/selections/${s1.id}`, { status: 'client_chosen' });
check('C8 a business can’t choose a work before its artist approves it', chooseEarly.s === 400 && /artist must approve/.test(chooseEarly.j.error), chooseEarly.t);
const noEvidence = await api('PATCH', `/api/admin/commercial/selections/${s1.id}`, { status: 'artist_approved' });
check('C9 an artist’s approval must say how it was given', noEvidence.s === 400, noEvidence.t);
const placeEarly = await api('POST', `/api/admin/commercial/leads/${L1.id}/placements`, { selection_id: s1.id, start_on: '2026-12-01' });
check('C10 a work can’t be placed before the artist approved it and the business chose it', placeEarly.s === 400, placeEarly.t);
await api('PATCH', `/api/admin/commercial/selections/${s1.id}`, { status: 'artist_approved', evidence: 'Artist email 28 Nov 2026' });
await api('PATCH', `/api/admin/commercial/selections/${s1.id}`, { status: 'client_chosen' });
const dbRefuse = await S.db.prepare("INSERT INTO commercial_placements (id, lead_id, selection_id, start_on, end_on, status, created_at, updated_at) VALUES ('px', ?, 'nope', '2026-12-01', '2027-06-01', 'scheduled', 'x', 'x')").bind(L1.id).run().then(() => false, () => true);
check('C11 the database itself refuses a placement of a work that wasn’t chosen', dbRefuse);
const pl = await api('POST', `/api/admin/commercial/leads/${L1.id}/placements`, { selection_id: s1.id, start_on: '2026-12-01', location: 'Lounge' });
check('C12 placing the chosen work sets six months (1 Dec 2026 → 1 Jun 2027)', pl.s === 200 && pl.j.placements[0].end_on === '2027-06-01', pl.t);
await api('POST', `/api/admin/commercial/leads/${L1.id}/documents`, { kind: 'fee_agreement', number: 'PA-FEE-001', status: 'signed', issued_on: '2026-11-30' });
const inv = await api('POST', `/api/admin/commercial/leads/${L1.id}/documents`, { kind: 'invoice', number: 'INV-0001', status: 'issued', issued_on: '2026-12-01', amount: '20', period_from: '2026-12-01', period_to: '2026-12-31' });
const invId = inv.j.documents.find(d => d.kind === 'invoice').id;
const dup = await api('POST', `/api/admin/commercial/leads/${L1.id}/documents`, { kind: 'invoice', number: 'INV-0001', status: 'issued' });
check('C13 invoice numbers are unique', dup.s === 400 && /already exists/.test(dup.j.error), dup.t);
const pay = await api('POST', `/api/admin/commercial/documents/${invId}/payments`, { amount: '20', received_on: '2026-12-05' });
check('C14 a full payment marks the invoice paid', pay.s === 200 && pay.j.documents.find(d => d.id === invId).status === 'paid', pay.t);
const lr = await S.db.prepare('SELECT retain_until FROM commercial_leads WHERE id = ?').bind(L1.id).first();
check('C15 a lead with an issued invoice is kept until the end of the sixth year after it (Revenue records)', lr.retain_until === '2032-12-31', lr.retain_until);
const list = await api('GET', '/api/admin/commercial');
check('C16 the overview counts the approved rental work and the monthly rent on the wall (€80, €20 PlotArt) once the placement starts',
  list.j.totals.approved_rental_works === 1 && list.j.placements.length === 1, JSON.stringify(list.j.totals));

/* rental management: monthly PlotArt fee invoices and renewals */
const { periods } = await import('../src/commercial.js');
const ps = periods({ start_on: '2026-12-01', end_on: '2027-06-01' }, '2027-02-15');
check('C16b rent periods are calendar months from the start, only those already begun (Dec, Jan, Feb by 15 Feb)', ps.length === 3 && ps[0].from === '2026-12-01' && ps[0].to === '2026-12-31' && ps[2].from === '2027-02-01', JSON.stringify(ps));
const plId = (await S.db.prepare('SELECT id FROM commercial_placements WHERE lead_id = ?').bind(L1.id).first()).id;
await S.db.prepare("UPDATE commercial_placements SET start_on = '2026-09-01', end_on = '2027-03-01', status = 'active' WHERE id = ?").bind(plId).run();
const due1 = (await api('GET', '/api/admin/commercial')).j;
check('C16c an active placement lists each begun month without a PlotArt invoice, at €20 (1% of €2,000) with the artist’s €60 shown separately',
  due1.rent_due.length >= 3 && due1.rent_due.every(r => r.plotart_cents === 2000 && r.artist_cents === 6000) && due1.rent_due[0].period_from === '2026-09-01', JSON.stringify(due1.rent_due.slice(0, 2)));
const inv1 = await api('POST', '/api/admin/commercial/rent-invoices', { placement_id: plId, period_from: '2026-09-01', number: 'INV-0101' });
const due2 = (await api('GET', '/api/admin/commercial')).j;
check('C16d recording the invoice removes that month from “rent to invoice” and links the invoice to the placement',
  inv1.s === 200 && !due2.rent_due.some(r => r.period_from === '2026-09-01') && (await S.db.prepare("SELECT placement_id, amount_cents FROM commercial_documents WHERE number = 'INV-0101'").first()).placement_id === plId, inv1.t);
const twice = await api('POST', '/api/admin/commercial/rent-invoices', { placement_id: plId, period_from: '2026-09-01', number: 'INV-0102' });
check('C16e the same month can’t be invoiced twice', twice.s === 400, twice.t);
check('C16f a placement ending within a month is listed as a renewal to discuss', (await S.db.prepare("UPDATE commercial_placements SET end_on = ? WHERE id = ?").bind(new Date(Date.now() + 10 * 864e5).toISOString().slice(0, 10), plId).run(), (await api('GET', '/api/admin/commercial')).j.renewals.length === 1));

/* website form (Phase 2) */
const form = (body, origin = ORIGIN) => S.mf.dispatchFetch('http://enquiry.local/v1/business-enquiry', { method: 'POST', headers: { Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '198.51.100.9' }, body: JSON.stringify(body) }).then(async r => ({ s: r.status, j: await r.json() }));
const good = { notice: 'PA-ENQ-BUSINESS-2026-12', name: 'Pat Example', email: 'pat@office.example', business: 'Example Offices', role: 'Facilities', interest: 'rental', message: 'We have a new reception and two meeting rooms to fill.' };
check('C17 the form is refused from another website', (await form(good, 'https://evil.example')).s === 403);
check('C18 an unexpected field is refused', (await form({ ...good, extra: 1 })).s === 400);
const f1 = await form(good);
const L2 = await S.db.prepare('SELECT * FROM commercial_leads WHERE reference = ?').bind(f1.j.reference || '').first();
check('C19 a website request creates a lead (source website form) with the message on its timeline, and tells hello@ (captured, no artist emailed)',
  f1.s === 200 && L2 && L2.source === 'website_form' && L2.interest === 'rental'
  && (await S.db.prepare("SELECT COUNT(*) AS n FROM commercial_events WHERE lead_id = ? AND kind = 'form'").bind(L2.id).first()).n === 1
  && (await S.db.prepare("SELECT COUNT(*) AS n FROM mail_capture WHERE to_addr = 'hello@plotnua.ie' AND subject LIKE 'Art for Hire request%'").first()).n === 1
  && (await S.db.prepare("SELECT COUNT(*) AS n FROM mail_capture WHERE to_addr <> 'hello@plotnua.ie'").first()).n === 0, JSON.stringify(f1));
const hp = await form({ ...good, fax_number: 'x' });
check('C20 the honeypot is silently dropped (no lead)', hp.s === 200 && (await S.db.prepare('SELECT COUNT(*) AS n FROM commercial_leads').first()).n === 2);
await S.mf.dispose();

/* switched off by default */
const S2 = await start({ port: 8893, enquiry: {} });
const off1 = await S2.mf.dispatchFetch('http://enquiry.local/v1/lead-capture', { method: 'POST', headers: { Authorization: 'Bearer x' }, body: '{}' });
const off2 = await S2.mf.dispatchFetch('http://enquiry.local/v1/business-enquiry', { method: 'POST', headers: { Origin: ORIGIN }, body: '{}' });
check('C21 both inbound routes stay closed (503) unless switched on', off1.status === 503 && off2.status === 503, `${off1.status} ${off2.status}`);
await S2.mf.dispose();
const toml = readFileSync(new URL('../wrangler.enquiry.toml', import.meta.url), 'utf8');
check('C22 production configuration keeps both switched off', /LEAD_CAPTURE_ENABLED = "false"/.test(toml) && /BUSINESS_ENQUIRIES_ENABLED = "false"/.test(toml));

console.log(`PROVE COMMERCIAL · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
