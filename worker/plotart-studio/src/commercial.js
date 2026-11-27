/* PlotArt Studio · Commercial leads and placements (founder approval in principle 27 Nov 2026; migration 0032).
   NOT DEPLOYED. Studio is the single record of business enquiries and everything that follows them:
     lead → timeline (notes, emails captured from Gmail, website form) → artwork selections, each approved or refused by
     its artist → proposal → PlotArt fee agreement + artist–business hire agreement → placement (six months) → invoices
     and payments → sale notice, replacement or renewal.
   Three ways in, no retyping:
     1. the founder adds or edits a lead on the Commercial page;
     2. captureGmail(): Gmail threads the founder labels "PlotArt Lead" are sent by a small Apps Script in his own Google
        account (integrations/gmail-leads.gs) to the enquiry Worker, which records each message once (by Gmail message id),
        on the lead for that thread or sender, creating the lead when there is none;
     3. websiteEnquiry(): the Art for Hire "Request a selection" form (Phase 2, switched off until approved).
   Business rental amounts follow PA-BHR-2026-11 v1.1: 4% of the work's price per month, 3% to the artist and 1% to
   PlotArt, rounded to the cent exactly as the website table. General hire (PA-AFH) and introducer shares are not modelled. */
import { Bad, now, rid, privateHint } from './lib.js';
import * as T from './test-artists.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();

export const STAGES = ['new', 'in_conversation', 'selecting', 'artist_approval', 'proposal_sent', 'agreed', 'placed', 'renewal_due', 'won', 'not_now', 'lost'];
export const STAGE_LABEL = { new: 'New', in_conversation: 'In conversation', selecting: 'Selecting works', artist_approval: 'Awaiting artist approval',
  proposal_sent: 'Proposal sent', agreed: 'Agreed', placed: 'Placed', renewal_due: 'Renewal due', won: 'Won (sale)', not_now: 'Not now', lost: 'Lost' };
const SOURCES = ['outreach_reply', 'website_form', 'email', 'phone', 'introduction', 'other'];
const INTERESTS = ['rental', 'purchase', 'project', 'unsure'];
const SECTORS = ['hotel', 'office', 'hospitality', 'retail', 'healthcare', 'property', 'interiors', 'production', 'other'];
const DOCS = { proposal: ['draft', 'sent', 'accepted', 'declined', 'void'], fee_agreement: ['draft', 'sent', 'signed', 'void'],
  hire_agreement: ['draft', 'sent', 'signed', 'void'], invoice: ['draft', 'issued', 'paid', 'void'], credit_note: ['issued', 'void'] };
const SEL_STATUS = ['proposed', 'artist_asked', 'artist_approved', 'artist_declined', 'client_chosen', 'client_declined', 'withdrawn'];
const PLACE_STATUS = ['scheduled', 'active', 'sale_notice', 'sold', 'replaced', 'ended', 'renewed'];
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const RETAIN_MONTHS = 24, INVOICE_YEARS = 6;

export async function installed(env) { try { await env.DB.prepare('SELECT 1 FROM commercial_leads LIMIT 1').all(); return true; } catch { return false; } }
async function need(env) { if (!(await installed(env))) throw new Bad('Commercial leads aren’t installed yet (migration 0032)', 503); }

/* ---- small helpers ---------------------------------------------------------------------------------------------- */
const str = (v, max, what, { min = 1, optional = true } = {}) => {
  if (v === undefined || v === null || String(v).trim() === '') { if (optional) return null; throw new Bad(`${what} is needed`); }
  const t = String(v).trim().replace(/\s+/g, ' ');
  if (t.length < min || t.length > max) throw new Bad(`${what} must be ${min}–${max} characters`);
  if (/[<>]/.test(t)) throw new Bad(`${what} can’t contain < or >`);
  return t;
};
const pick = (v, list, what, dflt) => { if (v === undefined || v === null || v === '') { if (dflt !== undefined) return dflt; throw new Bad(`Choose ${what}`); } if (!list.includes(v)) throw new Bad(`Unknown ${what}`); return v; };
const day = (v, what, optional = true) => { if (!v) { if (optional) return null; throw new Bad(`${what} is needed`); } if (!DAY.test(v) || isNaN(Date.parse(v + 'T00:00:00Z'))) throw new Bad(`${what} must be a date`); return v; };
const email = v => { const e = str(v, 200, 'Email', { min: 5 }); if (e && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e)) throw new Bad('That email address doesn’t look right'); return e ? e.toLowerCase() : null; };
const cents = (v, what, optional = true) => {
  if (v === undefined || v === null || v === '') { if (optional) return null; throw new Bad(`${what} is needed`); }
  const n = Math.round(Number(String(v).replace(/[€,\s]/g, '')) * 100);
  if (!Number.isFinite(n) || n <= 0 || n > 100_000_000) throw new Bad(`${what} must be an amount in euro`);
  return n;
};
export function addMonths(d, n) {   // calendar months, clamped to the month's last day
  const [y, m, dd] = d.split('-').map(Number), t = new Date(Date.UTC(y, m - 1 + n, 1));
  const last = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() + 1, 0)).getUTCDate();
  t.setUTCDate(Math.min(dd, last)); return t.toISOString().slice(0, 10);
}
/* PA-BHR-2026-11: 4% of the price per month, 3% to the artist, 1% to PlotArt (same rounding as the website table). */
export function rental(priceCents) {
  const monthly = Math.round(priceCents * 4 / 100), artist = Math.round(priceCents * 3 / 100);
  return { monthly_cents: monthly, artist_monthly_cents: artist, plotart_monthly_cents: monthly - artist };
}
const today = () => new Date().toISOString().slice(0, 10);
const reference = () => `PA-CL-${today().slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(3))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
async function retain(env, leadId) {   // last activity + 24 months; the end of the sixth year after an issued invoice
  const l = await one(env, 'SELECT last_activity_at FROM commercial_leads WHERE id = ?', leadId);
  let until = addMonths(l.last_activity_at.slice(0, 10), RETAIN_MONTHS);
  const inv = await one(env, "SELECT MAX(issued_on) AS d FROM commercial_documents WHERE lead_id = ? AND kind IN ('invoice','credit_note') AND status IN ('issued','paid')", leadId);
  if (inv && inv.d) { const y = `${Number(inv.d.slice(0, 4)) + INVOICE_YEARS}-12-31`; if (y > until) until = y; }
  await env.DB.prepare('UPDATE commercial_leads SET retain_until = ? WHERE id = ?').bind(until, leadId).run();
}
async function touch(env, leadId, at = now()) {
  await env.DB.prepare('UPDATE commercial_leads SET updated_at = ?, last_activity_at = MAX(last_activity_at, ?) WHERE id = ?').bind(now(), at, leadId).run();
  await retain(env, leadId);
}
async function event(env, leadId, kind, summary, actor, { body = null, at = now(), gmail = null } = {}) {
  await env.DB.prepare('INSERT INTO commercial_events (id, lead_id, at, kind, summary, body, gmail_message_id, actor) VALUES (?,?,?,?,?,?,?,?)')
    .bind(rid('ce'), leadId, at, kind, String(summary).slice(0, 300), body ? String(body).slice(0, 8000) : null, gmail, actor).run();
}
async function audit(env, actor, action, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, 'founder', action, null, JSON.stringify(detail).slice(0, 4000)).run();
}
async function lead(env, id) { const l = await one(env, 'SELECT * FROM commercial_leads WHERE id = ?', String(id || '')); if (!l) throw new Bad('That lead wasn’t found', 404); return l; }

/* ---- leads -------------------------------------------------------------------------------------------------------- */
function leadFields(b, partial = false) {
  const f = {};
  const set = (k, v) => { if (!partial || b[k] !== undefined) f[k] = v(); };
  set('business', () => str(b.business, 160, 'Business', { min: 2, optional: false }));
  set('sector', () => b.sector ? pick(b.sector, SECTORS, 'a sector') : null);
  set('contact_name', () => str(b.contact_name, 120, 'Contact name', { min: 2 }));
  set('contact_role', () => str(b.contact_role, 120, 'Role'));
  set('contact_email', () => email(b.contact_email));
  set('contact_phone', () => str(b.contact_phone, 40, 'Phone'));
  set('website', () => str(b.website, 300, 'Website'));
  set('location', () => str(b.location, 120, 'Location'));
  set('interest', () => pick(b.interest, INTERESTS, 'an interest', 'unsure'));
  set('next_action', () => str(b.next_action, 200, 'Next action'));
  set('next_action_on', () => day(b.next_action_on, 'Next action date'));
  set('summary', () => str(b.summary, 600, 'Summary'));
  return f;
}
export async function createLead(env, actor, b, { source, at = now(), thread = null } = {}) {
  await need(env);
  const f = leadFields(b || {});
  const src = pick(source || b.source, SOURCES, 'a source', 'other');
  const id = rid('cl'), ref = reference(), t = now();
  await env.DB.prepare(`INSERT INTO commercial_leads (id, reference, business, sector, contact_name, contact_role, contact_email, contact_phone, website, location,
    source, interest, stage, next_action, next_action_on, gmail_thread_id, summary, created_at, updated_at, last_activity_at, retain_until)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, f.business, f.sector, f.contact_name, f.contact_role, f.contact_email, f.contact_phone,
    f.website, f.location, src, f.interest, 'new', f.next_action, f.next_action_on, thread, f.summary, t, t, at, addMonths(at.slice(0, 10), RETAIN_MONTHS)).run();
  await event(env, id, 'note', `Lead created (${src.replace('_', ' ')})`, actor, { at });
  await audit(env, actor, 'commercial_lead_created', { reference: ref, source: src });
  return { id, reference: ref };
}
export async function updateLead(env, actor, id, b) {
  await need(env); const l = await lead(env, id);
  const f = leadFields(b || {}, true);
  if (b.stage !== undefined) f.stage = pick(b.stage, STAGES, 'a stage');
  const keys = Object.keys(f); if (!keys.length) return view(env, id);
  await env.DB.prepare(`UPDATE commercial_leads SET ${keys.map(k => `${k} = ?`).join(', ')}, updated_at = ? WHERE id = ?`).bind(...keys.map(k => f[k]), now(), l.id).run();
  if (f.stage && f.stage !== l.stage) await event(env, l.id, 'stage', `${STAGE_LABEL[l.stage]} → ${STAGE_LABEL[f.stage]}`, actor);
  await touch(env, l.id);
  return view(env, l.id);
}
export async function note(env, actor, id, b) {
  await need(env); const l = await lead(env, id);
  const t = str(b && b.text, 2000, 'Note', { optional: false });
  await event(env, l.id, 'note', t.slice(0, 120), actor, { body: t.length > 120 ? t : null });
  await touch(env, l.id); return view(env, l.id);
}

/* ---- selections and artist approval ------------------------------------------------------------------------------- */
export async function addSelection(env, actor, id, b) {
  await need(env); const l = await lead(env, id);
  const w = await one(env, 'SELECT w.id, w.title, w.price_eur, w.artist_id, a.display_name FROM artworks w JOIN artists a ON a.id = w.artist_id WHERE w.id = ?', String(b.artwork_id || ''));
  if (!w) throw new Bad('Choose an artwork');
  const arrangement = pick(b.arrangement, ['rental', 'purchase', 'project'], 'an arrangement', l.interest === 'purchase' ? 'purchase' : l.interest === 'project' ? 'project' : 'rental');
  const price = b.price !== undefined && b.price !== '' ? cents(b.price, 'Price') : (w.price_eur ? Math.round(Number(w.price_eur) * 100) : null);
  if (arrangement === 'rental' && !price) throw new Bad('A rental needs the work’s price');
  const r = arrangement === 'rental' ? rental(price) : { monthly_cents: null, artist_monthly_cents: null, plotart_monthly_cents: null };
  const sid = rid('cs'), t = now();
  await env.DB.prepare(`INSERT INTO commercial_selections (id, lead_id, artist_id, artwork_id, artwork_title, arrangement, price_cents, monthly_cents, artist_monthly_cents,
    plotart_monthly_cents, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(sid, l.id, w.artist_id, w.id, w.title, arrangement, price,
    r.monthly_cents, r.artist_monthly_cents, r.plotart_monthly_cents, 'proposed', t, t).run();
  await event(env, l.id, 'selection', `Proposed: ${w.title} by ${w.display_name} (${arrangement})`, actor);
  await touch(env, l.id); return view(env, l.id);
}
export async function setSelection(env, actor, sid, b) {
  await need(env);
  const s = await one(env, 'SELECT s.*, a.display_name FROM commercial_selections s JOIN artists a ON a.id = s.artist_id WHERE s.id = ?', String(sid || ''));
  if (!s) throw new Bad('That selection wasn’t found', 404);
  const status = pick(b.status, SEL_STATUS, 'a status');
  const decision = ['artist_approved', 'artist_declined'].includes(status);
  const evidence = decision ? str(b.evidence, 300, 'How the artist answered (for example “email 28 Nov”)', { optional: false }) : s.artist_decision_evidence;
  const at = decision ? now() : s.artist_decision_at;
  if (status === 'client_chosen' && s.status !== 'artist_approved') throw new Bad('The artist must approve a work before the business can choose it');
  await env.DB.prepare('UPDATE commercial_selections SET status = ?, artist_decision_at = ?, artist_decision_evidence = ?, updated_at = ? WHERE id = ?')
    .bind(status, at, evidence, now(), s.id).run();
  await event(env, s.lead_id, decision ? 'artist_approval' : 'selection', `${s.artwork_title} by ${s.display_name}: ${status.replace(/_/g, ' ')}${decision ? ` (${evidence})` : ''}`, actor);
  await touch(env, s.lead_id); return view(env, s.lead_id);
}

/* ---- documents (proposal, agreements, invoices) and payments ---------------------------------------------------- */
export async function addDocument(env, actor, id, b) {
  await need(env); const l = await lead(env, id);
  const kind = pick(b.kind, Object.keys(DOCS), 'a document type');
  const status = pick(b.status, DOCS[kind], 'a status', DOCS[kind][0]);
  const number = str(b.number, 40, 'Number or reference', { min: 3, optional: false });
  const did = rid('cd'), t = now();
  try {
    const placement = b.placement_id ? await one(env, 'SELECT id FROM commercial_placements WHERE id = ? AND lead_id = ?', String(b.placement_id), l.id) : null;
    if (b.placement_id && !placement) throw new Bad('That placement isn’t part of this lead');
    await env.DB.prepare(`INSERT INTO commercial_documents (id, lead_id, kind, number, status, issued_on, period_from, period_to, placement_id, amount_cents, vat_cents, link, note, created_at, updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(did, l.id, kind, number, status, day(b.issued_on, 'Date'), day(b.period_from, 'Period start'), day(b.period_to, 'Period end'),
      placement ? placement.id : null, cents(b.amount, 'Amount'), cents(b.vat, 'VAT'), str(b.link, 500, 'Link'), str(b.note, 300, 'Note'), t, t).run();
  } catch (e) { if (/UNIQUE/.test(String(e))) throw new Bad(`A ${kind.replace('_', ' ')} numbered ${number} already exists`); throw e; }
  await event(env, l.id, 'document', `${kind.replace('_', ' ')} ${number}: ${status}`, actor);
  await touch(env, l.id); return view(env, l.id);
}
export async function setDocument(env, actor, did, b) {
  await need(env);
  const d = await one(env, 'SELECT * FROM commercial_documents WHERE id = ?', String(did || '')); if (!d) throw new Bad('That document wasn’t found', 404);
  const status = pick(b.status, DOCS[d.kind], 'a status');
  await env.DB.prepare('UPDATE commercial_documents SET status = ?, issued_on = COALESCE(?, issued_on), updated_at = ? WHERE id = ?').bind(status, day(b.issued_on, 'Date'), now(), d.id).run();
  await event(env, d.lead_id, 'document', `${d.kind.replace('_', ' ')} ${d.number}: ${status}`, actor);
  await touch(env, d.lead_id); return view(env, d.lead_id);
}
export async function addPayment(env, actor, did, b) {
  await need(env);
  const d = await one(env, 'SELECT * FROM commercial_documents WHERE id = ?', String(did || '')); if (!d || d.kind !== 'invoice') throw new Bad('Choose an invoice');
  const amount = cents(b.amount, 'Amount', false), on = day(b.received_on, 'Date received', false);
  await env.DB.prepare('INSERT INTO commercial_payments (id, document_id, received_on, amount_cents, method, reference, created_at) VALUES (?,?,?,?,?,?,?)')
    .bind(rid('cp'), d.id, on, amount, pick(b.method, ['bank_transfer', 'card', 'other'], 'a method', 'bank_transfer'), str(b.reference, 80, 'Payment reference'), now()).run();
  const paid = await one(env, 'SELECT SUM(amount_cents) AS s FROM commercial_payments WHERE document_id = ?', d.id);
  if (d.amount_cents && paid.s >= d.amount_cents + (d.vat_cents || 0) && d.status !== 'paid') await env.DB.prepare("UPDATE commercial_documents SET status = 'paid', updated_at = ? WHERE id = ?").bind(now(), d.id).run();
  await event(env, d.lead_id, 'payment', `Payment of €${(amount / 100).toFixed(2)} received for invoice ${d.number}`, actor);
  await touch(env, d.lead_id); return view(env, d.lead_id);
}

/* ---- placements and renewals ------------------------------------------------------------------------------------- */
export async function addPlacement(env, actor, id, b) {
  await need(env); const l = await lead(env, id);
  const s = await one(env, 'SELECT * FROM commercial_selections WHERE id = ? AND lead_id = ?', String(b.selection_id || ''), l.id);
  if (!s) throw new Bad('Choose a selected work');
  if (s.status !== 'client_chosen') throw new Bad('Only a work the artist approved and the business chose can be placed');
  const start = day(b.start_on, 'Start date', false), end = day(b.end_on, 'End date') || addMonths(start, 6);
  const renewal = b.renewal_of ? (await one(env, 'SELECT id FROM commercial_placements WHERE id = ? AND lead_id = ?', String(b.renewal_of), l.id)) : null;
  if (b.renewal_of && !renewal) throw new Bad('The placement being renewed wasn’t found');
  const pid = rid('cpl'), t = now();
  await env.DB.prepare(`INSERT INTO commercial_placements (id, lead_id, selection_id, location, start_on, end_on, status, renewal_of, created_at, updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?)`).bind(pid, l.id, s.id, str(b.location, 160, 'Location'), start, end, start <= today() ? 'active' : 'scheduled', renewal ? renewal.id : null, t, t).run();
  if (renewal) await env.DB.prepare("UPDATE commercial_placements SET status = 'renewed', updated_at = ? WHERE id = ?").bind(t, renewal.id).run();
  await event(env, l.id, renewal ? 'renewal' : 'placement', `${s.artwork_title} placed ${start} to ${end}${renewal ? ' (renewal)' : ''}`, actor);
  await touch(env, l.id); return view(env, l.id);
}
export async function setPlacement(env, actor, pid, b) {
  await need(env);
  const p = await one(env, 'SELECT p.*, s.artwork_title FROM commercial_placements p JOIN commercial_selections s ON s.id = p.selection_id WHERE p.id = ?', String(pid || ''));
  if (!p) throw new Bad('That placement wasn’t found', 404);
  const status = pick(b.status, PLACE_STATUS, 'a status');
  await env.DB.prepare('UPDATE commercial_placements SET status = ?, sale_notice_on = CASE WHEN ? = \'sale_notice\' THEN COALESCE(?, sale_notice_on) ELSE sale_notice_on END, updated_at = ? WHERE id = ?')
    .bind(status, status, day(b.sale_notice_on, 'Notice date') || today(), now(), p.id).run();
  await event(env, p.lead_id, 'placement', `${p.artwork_title}: ${status.replace('_', ' ')}`, actor);
  await touch(env, p.lead_id); return view(env, p.lead_id);
}

/* ---- Gmail capture (Apps Script → enquiry Worker; integrations/gmail-leads.gs) ---------------------------------------
   Each message: { message_id, thread_id, date (ISO), from, to, subject, body, direction: 'in'|'out' }. A message is
   recorded once (UNIQUE gmail_message_id). It goes to the lead for its thread; otherwise, for an incoming message, to the
   open lead with the sender's address; otherwise a new lead is created from the sender (outreach reply). The founder's own
   outgoing messages are recorded only on a thread that already has a lead. */
const OWN = /@plotnua\.ie>?$/i;
function parseFrom(s) { const m = /^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/.exec(s || ''); return m ? { name: m[1].trim() || null, email: m[2].trim().toLowerCase() } : { name: null, email: String(s || '').trim().toLowerCase() }; }
function businessFrom(name, addr) {
  const dom = (addr.split('@')[1] || '').toLowerCase();
  if (!dom || /^(gmail|googlemail|yahoo|hotmail|outlook|icloud|live|eircom|me)\./.test(dom)) return name || addr;
  const core = dom.replace(/^(mail|www)\./, '').split('.')[0];
  return core.charAt(0).toUpperCase() + core.slice(1);
}
export async function captureGmail(env, messages) {
  await need(env);
  if (!Array.isArray(messages) || messages.length > 50) throw new Bad('Send up to 50 messages at a time');
  const out = { recorded: 0, duplicates: 0, created: [], skipped: 0 };
  for (const m of messages) {
    const mid = str(m && m.message_id, 64, 'message_id', { optional: false }), tid = str(m.thread_id, 64, 'thread_id', { optional: false });
    if (await one(env, 'SELECT 1 FROM commercial_events WHERE gmail_message_id = ?', mid)) { out.duplicates++; continue; }
    const at = isNaN(Date.parse(m.date)) ? now() : new Date(m.date).toISOString();
    const from = parseFrom(m.from), dir = m.direction === 'out' || OWN.test(from.email) ? 'out' : 'in';
    const subject = String(m.subject || '(no subject)').slice(0, 200), body = String(m.body || '').replace(/\r/g, '').slice(0, 8000);
    let l = await one(env, 'SELECT id FROM commercial_leads WHERE gmail_thread_id = ?', tid);
    if (!l && dir === 'in') l = await one(env, "SELECT id FROM commercial_leads WHERE contact_email = ? AND stage NOT IN ('won','lost','not_now') ORDER BY last_activity_at DESC LIMIT 1", from.email);
    if (!l && dir === 'out') { out.skipped++; continue; }
    if (!l) {
      const c = await createLead(env, 'gmail capture', { business: businessFrom(from.name, from.email), contact_name: from.name && from.name.length >= 2 ? from.name.slice(0, 120) : null,
        contact_email: from.email, summary: subject.replace(/[<>]/g, '') }, { source: 'outreach_reply', at, thread: tid });
      l = { id: c.id }; out.created.push(c.reference);
    } else await env.DB.prepare('UPDATE commercial_leads SET gmail_thread_id = COALESCE(gmail_thread_id, ?) WHERE id = ?').bind(tid, l.id).run();
    await event(env, l.id, dir === 'in' ? 'email_in' : 'email_out', `${dir === 'in' ? 'From' : 'To'} ${dir === 'in' ? from.email : String(m.to || '').slice(0, 120)}: ${subject}`, 'gmail capture', { body, at, gmail: mid });
    if (dir === 'in') await env.DB.prepare("UPDATE commercial_leads SET stage = CASE WHEN stage = 'new' THEN 'in_conversation' ELSE stage END WHERE id = ? AND (SELECT COUNT(*) FROM commercial_events WHERE lead_id = ? AND kind = 'email_in') > 1").bind(l.id, l.id).run();
    await touch(env, l.id, at); out.recorded++;
  }
  return out;
}

/* ---- the Art for Hire request form (Phase 2: switched off until approved) --------------------------------------- */
export async function websiteEnquiry(env, b) {
  await need(env);
  const message = str(b.message, 2000, 'Message', { min: 10, optional: false });
  const c = await createLead(env, 'website form', { business: b.business, contact_name: b.name, contact_role: b.role, contact_email: b.email,
    contact_phone: b.phone, location: b.location, interest: ['rental', 'purchase', 'project'].includes(b.interest) ? b.interest : 'unsure',
    summary: message.slice(0, 600) }, { source: 'website_form' });
  await event(env, c.id, 'form', 'Request from the Art for Hire page', 'website form', { body: message });
  return c;
}

/* ---- views -------------------------------------------------------------------------------------------------------- */
/* Rental management: every month of an active placement is a period PlotArt invoices its 1% fee for (the artist invoices
   their 3% under the hire agreement). A period is due once it has started and has no PlotArt invoice yet (a void one doesn't
   count). Placements ending within 30 days are renewals to discuss. */
export function periods(p, upto) {
  const out = [];
  for (let i = 0; i < 24; i++) {
    const from = addMonths(p.start_on, i); if (from >= p.end_on || from > upto) break;
    const next = addMonths(p.start_on, i + 1), to = new Date(Date.parse(next + 'T00:00:00Z') - 864e5).toISOString().slice(0, 10);
    out.push({ from, to: to < p.end_on ? to : p.end_on });
  }
  return out;
}
export async function rentDue(env, upto = today()) {
  const ps = await all(env, `SELECT p.id, p.lead_id, p.start_on, p.end_on, p.status, s.artwork_title, s.monthly_cents, s.artist_monthly_cents, s.plotart_monthly_cents,
    a.display_name AS artist, l.business, l.reference FROM commercial_placements p JOIN commercial_selections s ON s.id = p.selection_id JOIN artists a ON a.id = s.artist_id
    JOIN commercial_leads l ON l.id = p.lead_id WHERE p.status IN ('active','sale_notice') AND s.arrangement = 'rental'`);
  const due = [];
  for (const p of ps) {
    const billed = new Set((await all(env, "SELECT period_from FROM commercial_documents WHERE placement_id = ? AND kind = 'invoice' AND status <> 'void'", p.id)).map(d => d.period_from));
    for (const per of periods(p, upto)) if (!billed.has(per.from)) due.push({ placement_id: p.id, lead_id: p.lead_id, reference: p.reference, business: p.business, artwork_title: p.artwork_title,
      artist: p.artist, period_from: per.from, period_to: per.to, plotart_cents: p.plotart_monthly_cents, artist_cents: p.artist_monthly_cents, monthly_cents: p.monthly_cents });
  }
  return due;
}
export async function invoiceRent(env, actor, b) {
  await need(env);
  const due = (await rentDue(env)).find(d => d.placement_id === String(b.placement_id || '') && d.period_from === String(b.period_from || ''));
  if (!due) throw new Bad('That rental month isn’t due for an invoice');
  const number = str(b.number, 40, 'Invoice number', { min: 3, optional: false });
  return addDocument(env, actor, due.lead_id, { kind: 'invoice', number, status: 'issued', issued_on: today(), period_from: due.period_from, period_to: due.period_to,
    placement_id: due.placement_id, amount: (due.plotart_cents / 100).toFixed(2), note: `PlotArt fee (1%) for ${due.artwork_title}, ${due.period_from} to ${due.period_to}` });
}

export async function list(env) {
  if (!(await installed(env))) return { installed: false };
  const leads = await all(env, `SELECT l.id, l.reference, l.business, l.sector, l.contact_name, l.contact_email, l.source, l.interest, l.stage, l.next_action, l.next_action_on,
    l.last_activity_at, (SELECT COUNT(*) FROM commercial_selections s WHERE s.lead_id = l.id AND s.status NOT IN ('withdrawn','artist_declined','client_declined')) AS works,
    (SELECT COUNT(*) FROM commercial_placements p WHERE p.lead_id = l.id AND p.status IN ('scheduled','active','sale_notice')) AS placed
    FROM commercial_leads l ORDER BY CASE WHEN l.stage IN ('won','lost','not_now') THEN 1 ELSE 0 END, COALESCE(l.next_action_on, '9999'), l.last_activity_at DESC`);
  const t = today(), soon = addMonths(t, 1);
  const placements = await all(env, `SELECT p.id, p.lead_id, p.start_on, p.end_on, p.status, s.artwork_title, s.monthly_cents, s.artist_monthly_cents, s.plotart_monthly_cents,
    a.display_name AS artist, l.business FROM commercial_placements p JOIN commercial_selections s ON s.id = p.selection_id JOIN artists a ON a.id = s.artist_id
    JOIN commercial_leads l ON l.id = p.lead_id WHERE p.status IN ('scheduled','active','sale_notice') ORDER BY p.end_on`);
  const approved = await all(env, `SELECT COUNT(DISTINCT artwork_id) AS n FROM commercial_selections WHERE status IN ('artist_approved','client_chosen') AND arrangement = 'rental'`);
  const rent_due = await rentDue(env), renewals = placements.filter(p => ['active', 'sale_notice'].includes(p.status) && p.end_on <= addMonths(t, 1));
  return { installed: true, stages: STAGES, stage_label: STAGE_LABEL, leads, placements, rent_due, renewals,
    totals: { open: leads.filter(l => !['won', 'lost', 'not_now'].includes(l.stage)).length, due: leads.filter(l => l.next_action_on && l.next_action_on <= t).length,
      monthly_cents: placements.filter(p => p.status !== 'scheduled').reduce((s, p) => s + (p.monthly_cents || 0), 0),
      plotart_monthly_cents: placements.filter(p => p.status !== 'scheduled').reduce((s, p) => s + (p.plotart_monthly_cents || 0), 0),
      ending_soon: placements.filter(p => p.end_on <= soon).length, rent_due_cents: rent_due.reduce((x, d) => x + (d.plotart_cents || 0), 0), approved_rental_works: approved[0].n } };
}
export async function view(env, id) {
  await need(env); const l = await lead(env, id);
  const [events, selections, documents, placements] = await Promise.all([
    all(env, 'SELECT id, at, kind, summary, body, actor FROM commercial_events WHERE lead_id = ? ORDER BY at DESC, id DESC', l.id),
    all(env, `SELECT s.*, a.display_name AS artist, a.slug FROM commercial_selections s JOIN artists a ON a.id = s.artist_id WHERE s.lead_id = ? ORDER BY s.created_at`, l.id),
    all(env, `SELECT d.*, (SELECT COALESCE(SUM(amount_cents),0) FROM commercial_payments p WHERE p.document_id = d.id) AS paid_cents FROM commercial_documents d WHERE d.lead_id = ? ORDER BY d.created_at`, l.id),
    all(env, `SELECT p.*, s.artwork_title FROM commercial_placements p JOIN commercial_selections s ON s.id = p.selection_id WHERE p.lead_id = ? ORDER BY p.start_on`, l.id)]);
  return { lead: l, events, selections, documents, placements, stages: STAGES, stage_label: STAGE_LABEL };
}
/* Works the founder can propose: every published, available work of an artist who is open to Art for Hire first. */
export async function catalogue(env) {
  const works = await all(env, `SELECT w.id, w.title, w.price_eur, w.artist_id, a.display_name AS artist FROM artworks w JOIN artists a ON a.id = w.artist_id
    WHERE a.account_status IN ('invited','active') AND w.archived = 0 AND w.availability = 'available' ORDER BY a.display_name, w.title`);
  return { works: works.filter(w => !T.isTest(env, w.artist_id)) };   // never an internal test account
}
/* Daily run: delete leads past their retention date (everything attached goes with them). */
export async function expire(env) {
  if (!(await installed(env))) return 0;
  const r = await env.DB.prepare('DELETE FROM commercial_leads WHERE retain_until < ?').bind(today()).run();
  return r.meta ? r.meta.changes || 0 : 0;
}
export { privateHint };
