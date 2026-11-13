/* PlotArt Studio · Worker (Phase 2, 29 Oct 2026). NOT DEPLOYED. Local tests only until the founder approves
   the Cloudflare resources (D1 database, EU R2 bucket, Access application).

   /              the artist's Studio (single page app)          /admin   the founder's review and publishing desk
   /preview/...   the artist's private gallery preview           /admin/preview/<submission>/...  a submission
   /api/...       JSON API (artist and founder)                  /api/pipeline/...  the publishing pipeline (bearer token)

   Security: Cloudflare Access signs people in; every request is re-verified here (auth.js). An artist can only ever
   reach rows WHERE artist_id = their own id, taken from the verified token. State changes need same-origin requests
   with the X-Studio header. Images are private (R2) and served only to their artist and the founder. */
import { verifyAccess, who } from './auth.js';
import * as L from './lib.js';
import * as AG from './agreement.js';
import * as H from './hire.js';
import * as O from './opportunities.js';   // Opportunities & delivery (development 13 Nov 2026): expressions of interest only
import { artistBody, artworkBody, previewPage, shown } from './render.js';
import * as A from './assets.js';
import { send } from './mailer.js';
import { AREAS as IDEA_AREAS, clean as ideaClean, problem as ideaProblem } from './ideas-rules.js';
import { KINDS as G_KINDS, SPACE_TYPES as G_SPACE, AVAILABILITY as G_AVAIL, LISTING_DAYS as G_DAYS, clean as gClean, textProblem as gTextProblem, areaProblem as gAreaProblem } from './garden-rules.js';

const { Bad, now, rid } = L;
const SEC = {
  'Content-Security-Policy': "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin', 'Cache-Control': 'no-store',
};
// the approved PlotArt logo files (decoded once; public, no data)
const bin = b => Uint8Array.from(atob(b), c => c.charCodeAt(0));
const LOGO = { '/assets/brand/plotart-p-48.webp': [bin(A.LOGO_48_B64), 'image/webp'], '/assets/brand/plotart-p-96.webp': [bin(A.LOGO_96_B64), 'image/webp'],
  '/assets/brand/plotart-favicon-32.png': [bin(A.FAVICON_32_B64), 'image/png'], '/assets/brand/plotart-apple-touch-180.png': [bin(A.TOUCH_180_B64), 'image/png'] };
const res = (body, type, status = 200, extra = {}) => new Response(body, { status, headers: { 'Content-Type': type, ...SEC, ...extra } });
const json = (o, status = 200) => res(JSON.stringify(o), 'application/json; charset=utf-8', status);
const html = (h, status = 200) => res(h, 'text/html; charset=utf-8', status);

const escHtml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
const founderEmails = env => String(env.FOUNDER_EMAILS || '').toLowerCase().split(',').map(s => s.trim()).filter(Boolean);
// audit entries keep a recognisable but partial address (le…@gmail.com), so the log does not hold a second full copy
const maskEmail = e => { const [u, d] = String(e).split('@'); return (u.length <= 2 ? u[0] + '…' : u.slice(0, 2) + '…') + '@' + (d || ''); };

async function audit(env, actor, role, action, artistId, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, role, action, artistId || null, detail ? JSON.stringify(detail).slice(0, 4000) : null).run();
}

/* ---------------------------------------------------------------- data access (always scoped by artist id) */
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
async function load(env, artistId) {
  const artist = await one(env, 'SELECT * FROM artists WHERE id = ?', artistId);
  const works = await all(env, 'SELECT * FROM artworks WHERE artist_id = ? ORDER BY ord', artistId);
  const images = await all(env, 'SELECT * FROM images WHERE artist_id = ? AND deleted_at IS NULL ORDER BY ord', artistId);
  return { artist, works, images };
}
/* Open for Commissions (founder approval 13 Nov 2026). Migration 0011 adds artists.open_for_commissions. Until it has run,
   Studio keeps working exactly as before and the switch is reported as not available yet. */
async function commissionsInstalled(env) {
  try { await env.DB.prepare('SELECT open_for_commissions FROM artists LIMIT 1').all(); return true; } catch { return false; }
}
async function latestVersion(env, artistId) {
  const v = await one(env, 'SELECT * FROM versions WHERE artist_id = ? ORDER BY version DESC LIMIT 1', artistId);
  return v ? { ...v, snap: JSON.parse(v.snapshot) } : null;
}
async function liveVersion(env, artistId) {
  const q = await one(env, "SELECT version FROM publish_queue WHERE artist_id = ? AND status = 'published' ORDER BY version DESC LIMIT 1", artistId);
  return q ? q.version : 0;
}
/* The artwork photo minimum (2,000 px). A LOWER value is honoured ONLY in the local test environment, so the founder's
   existing small test photographs can be shown in local screenshots; anywhere else it is refused. */
function minLong(env) {
  if (env.TEST_MIN_LONG_EDGE === undefined) return L.MIN_LONG_EDGE;
  if (env.ENVIRONMENT !== 'local') throw new Bad('Studio configuration error', 500);
  return Number(env.TEST_MIN_LONG_EDGE);
}
const blocked = images => new Set(images.filter(i => JSON.parse(i.checks).blocks.length).map(i => i.id));

async function status(env, artist) {
  const d = await load(env, artist.id);
  const snap = L.snapshot(d.artist, d.works, d.images);
  const lv = await latestVersion(env, artist.id);
  const cs = L.changes(lv && lv.snap, snap);
  const pending = await one(env, "SELECT id, created_at, tier, note FROM submissions WHERE artist_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1", artist.id);
  const last = await one(env, "SELECT id, status, founder_message, decided_at FROM submissions WHERE artist_id = ? AND status IN ('changes_requested','declined','approved') ORDER BY decided_at DESC LIMIT 1", artist.id);
  const queue = await all(env, "SELECT id, version, kind, status, updated_at FROM publish_queue WHERE artist_id = ? AND status IN ('awaiting_founder','ready','exporting') ORDER BY version", artist.id);
  const live = await liveVersion(env, artist.id);
  const ag = await agreementState(env, d.artist);
  const unsubmittedTier = L.tierOf(cs.filter(c => c.tier !== 'instant'));
  // the agreement item appears only when it is needed now: a first publication, or full-review changes waiting to be submitted
  const needAgreement = !ag.accepted && (!lv || unsubmittedTier === 'full');
  const list = L.checklist(snap, { founding: !!d.artist.founding, programme: ag.programme, firstPublication: !lv, licenceOk: !needAgreement, imageBlocks: blocked(d.images) });
  const problems = list.map(i => i.text);
  let state;
  if (pending) state = 'in_review';
  else if (queue.length) state = 'publishing';
  else if (last && last.status === 'changes_requested' && (!lv || last.decided_at > lv.created_at)) state = 'changes_requested';
  else if (live) state = 'live';
  else if (lv) state = 'approved';
  else state = 'draft';
  return {
    state, live_version: live, latest_version: lv ? lv.version : 0, pending, last_decision: last, queue,
    changes: cs, unsubmitted: cs.filter(c => c.tier !== 'instant'), tier: L.tierOf(cs.filter(c => c.tier !== 'instant')),
    problems, checklist: list, licence_ok: ag.accepted, licence_version: ag.licence ? ag.licence.version : null,
    agreement: agreementSummary(ag),
    counts: { works: snap.works.length, archived: d.works.filter(w => w.archived).length },
  };
}

/* ---------------------------------------------------------------- Founding Artist Agreement (development 6 Nov 2026)
   The texts are bundled (assets.js, fingerprint-checked at build). They can be accepted only once migration 0005 has
   installed the same fingerprints in agreement_documents; until then Studio works exactly as before for everything else. */
async function agreementDocs(env) {
  let docs;
  try { docs = await all(env, 'SELECT doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at FROM agreement_documents ORDER BY effective_at, doc_id'); }
  catch { return null; }   // migration 0005 not applied
  // Gallery Artist Agreement texts (migration 0012; the approved text is installed by 0013). Absent: nothing added.
  try { docs = docs.concat(await all(env, 'SELECT doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at FROM gallery_agreement_documents ORDER BY effective_at, doc_id')); } catch { /* 0012 not applied */ }
  return docs;
}
/* Gallery Artist terms (migration 0012). null when the artist has none (every Founding Artist) or 0012 has not run. */
async function termsFor(env, artistId) {
  try { return await one(env, 'SELECT * FROM artist_terms WHERE artist_id = ?', artistId); } catch { return null; }
}
async function termsInstalled(env) {
  try { await env.DB.prepare('SELECT 1 FROM artist_terms LIMIT 1').all(); return true; } catch { return false; }
}
async function acceptanceRows(env, artistId) {
  const rows = await all(env, 'SELECT * FROM agreement_acceptances WHERE artist_id = ? ORDER BY accepted_at, id', artistId);
  let gaa = [];
  try { gaa = await all(env, 'SELECT * FROM gallery_agreement_acceptances WHERE artist_id = ? ORDER BY accepted_at, id', artistId); } catch { /* 0012 not applied */ }
  return gaa.length ? rows.concat(gaa).sort((x, y) => String(x.accepted_at).localeCompare(String(y.accepted_at)) || String(x.id).localeCompare(String(y.id))) : rows;
}
async function agreementState(env, artist) {
  const docs = await agreementDocs(env);
  const terms = await termsFor(env, artist.id);
  const req = AG.required(artist, terms);
  const installed = !!docs && req.every(id => { const r = docs.find(d => d.doc_id === id), b = AG.doc(id);
    return r && b && r.text_status === 'fixed' && r.html_sha256 === b.html_sha256 && r.pdf_sha256 === b.pdf_sha256; });
  const rows = docs ? await acceptanceRows(env, artist.id) : [];
  const current = id => rows.filter(r => r.doc_id === id && r.method === 'studio_checkbox' && AG.doc(id) && r.doc_sha256 === AG.doc(id).html_sha256).pop();
  const accepted = installed && req.every(id => current(id));
  const last = accepted ? current(req[0]) : null;
  const newest = rows.filter(r => r.method === 'studio_checkbox' && r.doc_id.startsWith('PA-GPIL-')).pop();
  return {
    installed, required: req, accepted, accepted_at: last ? last.accepted_at : null, event_id: last ? last.event_id : null, legal_name: last ? last.legal_name : null,
    statement: AG.statementFor(artist, terms), history: rows, programme: AG.programmeOf(artist, terms),
    legacy: artist.licence_version && artist.licence_accepted_at ? { version: artist.licence_version, accepted_at: artist.licence_accepted_at, migrated: rows.some(r => r.method === 'migrated_from_artists_table' && r.doc_id === artist.licence_version) } : null,
    // the licence the publishing pipeline carries: the newest Studio acceptance, else the label recorded before 0005
    licence: newest ? { version: newest.doc_id, accepted_at: newest.accepted_at } : artist.licence_version ? { version: artist.licence_version, accepted_at: artist.licence_accepted_at } : null,
    founding_year: artist.founding ? AG.foundingYear(artist.first_published_at) : null,
    first_published_at: artist.first_published_at || null, founding: !!artist.founding,
  };
}
const agreementSummary = ag => ({ installed: ag.installed, required: ag.required, accepted: ag.accepted, accepted_at: ag.accepted_at, legal_name_given: !!ag.legal_name, programme: ag.programme,
  statement: ag.statement, legacy: ag.legacy, licence: ag.licence, founding_year: ag.founding_year, first_published_at: ag.first_published_at, founding: ag.founding,
  status: ag.accepted ? 'accepted' : ag.legacy ? 'legacy_licence_only' : 'not_accepted' });

async function acceptAgreement(env, artist, body) {
  const a = await one(env, 'SELECT * FROM artists WHERE id=?', artist.id);
  const ag = await agreementState(env, a);
  if (!ag.installed) throw new Bad('The agreement can’t be accepted just yet. Please try again later, or email hello@plotnua.ie.', 503);
  if (ag.accepted) throw new Bad('You have already accepted these documents.', 409);
  if (body.accept !== true) throw new Bad('Tick the box to accept.');
  const shown = body.documents && typeof body.documents === 'object' ? body.documents : {};
  if (Object.keys(shown).length !== ag.required.length || ag.required.some(id => shown[id] !== AG.doc(id).html_sha256) || body.statement !== ag.statement)
    throw new Bad('The documents have changed since you opened this page. Please reload it and read them again.', 409);
  const legal = body.legal_name === undefined || body.legal_name === null || String(body.legal_name).trim() === '' ? null : L.text(body.legal_name, 2, 120, 'Legal name');
  // an earlier licence acceptance must already be held in the permanent record before anything new is added beside it
  if (ag.legacy && !ag.legacy.migrated) throw new Bad('The agreement can’t be accepted just yet. Please try again later, or email hello@plotnua.ie.', 503);
  const event = rid('evt'), at = now();
  // one tick, one event: each document in its own record table (PA-GAA in gallery_agreement_acceptances, 0012), same event_id
  await env.DB.batch(ag.required.map(id => env.DB.prepare(`INSERT INTO ${AG.acceptanceTable(id)} (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at,
      account_email, display_name, legal_name, method, statement, note, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`)
    .bind(rid('acc'), event, a.id, id, AG.doc(id).html_sha256, AG.doc(id).pdf_sha256, at, artist.email, a.display_name, legal, 'studio_checkbox', ag.statement, null, at)));
  await audit(env, artist.email, 'artist', 'agreement_accepted', a.id, { event, documents: ag.required, legal_name_given: !!legal });
  return { event_id: event, accepted_at: at, documents: ag.required };
}

/* ---------------------------------------------------------------- enquiry log (founder; agreement 5.4)
   Relay enquiries are logged by the relay itself (enquiry.js). "Log enquiry" records an enquiry PlotArt introduced by
   email: artist, optional artwork, the Irish date it was introduced, an optional short note. Never buyer contact details.
   Nothing is edited or deleted: a correction is a new row that points at the row it corrects. */
const ENQ_FLOOR = '2026-10-01';      // PlotArt was not introducing enquiries before October 2026
async function enquiryLog(env) {
  if (!(await agreementDocs(env))) return { installed: false, items: [], artists: [] };
  const items = await all(env, `SELECT l.*, a.display_name, w.title AS artwork_title FROM enquiry_log l JOIN artists a ON a.id = l.artist_id
    LEFT JOIN artworks w ON w.id = l.artwork_id ORDER BY l.introduced_at DESC, l.logged_at DESC LIMIT 500`);
  const artists = await all(env, "SELECT id, display_name, founding, first_published_at FROM artists WHERE account_status <> 'ended' ORDER BY display_name");
  const works = await all(env, 'SELECT id, artist_id, title FROM artworks WHERE title IS NOT NULL ORDER BY artist_id, ord');
  return { installed: true, today: AG.dublinToday(), floor: ENQ_FLOOR, late_after_days: 7,
    items: items.map(i => ({ ...i, logged_by: i.logged_by === 'relay' || i.logged_by.startsWith('migration') ? i.logged_by : 'founder' })),
    artists: artists.map(a => ({ id: a.id, display_name: a.display_name, founding: !!a.founding, founding_year: a.founding ? AG.foundingYear(a.first_published_at) : null,
      works: works.filter(w => w.artist_id === a.id).map(w => ({ id: w.id, title: w.title })) })) };
}
async function logEnquiry(env, founder, b) {
  if (!(await agreementDocs(env))) throw new Bad('The enquiry log isn’t installed yet (migration 0005).', 503);
  const a = await one(env, 'SELECT * FROM artists WHERE id=?', String(b.artist_id || ''));
  if (!a) throw new Bad('Choose the artist');
  let work = null;
  if (b.artwork_id) { work = await one(env, 'SELECT id, title FROM artworks WHERE id=? AND artist_id=?', String(b.artwork_id), a.id); if (!work) throw new Bad('That artwork isn’t one of this artist’s'); }
  const day = String(b.introduced_on || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || AG.addDays(day, 0) !== day) throw new Bad('Enter the date the enquiry was introduced');
  const today = AG.dublinToday();
  if (day > today) throw new Bad('The date can’t be in the future');
  if (day < ENQ_FLOOR) throw new Bad('PlotArt wasn’t introducing enquiries before October 2026: check the date');
  let note = null;
  if (b.note !== undefined && b.note !== null && String(b.note).trim()) {
    note = String(b.note).trim();
    if (note.length > 280) throw new Bad('Keep the note to 280 characters');
    if (/[<>]/.test(note) || /@/.test(note) || L.privateHint(note)) throw new Bad('The note looks as if it contains an email address, phone number or Eircode. Never record a buyer’s contact details here.');
  }
  let corrects = null;
  if (b.corrects) { const c = await one(env, 'SELECT id, artist_id FROM enquiry_log WHERE id=?', String(b.corrects)); if (!c) throw new Bad('The entry being corrected wasn’t found'); corrects = c.id; }
  if (!corrects && b.confirm !== true) throw new Bad('Confirm that PlotArt introduced this enquiry to the artist');
  const introducedAt = AG.dublinMidnightUtc(day);
  const f = AG.foundingAt(a, introducedAt);
  const late = day < AG.addDays(today, -7) ? 1 : 0;
  const ref = `PA-EM-${today.slice(2).replace(/-/g, '')}-${[...crypto.getRandomValues(new Uint8Array(3))].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
  const id = rid('l'), at = now();
  await env.DB.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry, corrects, note)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, ref, a.id, work ? work.id : null, 'email', introducedAt, f.founding, f.year_end, founder, at, late, corrects, note).run();
  await audit(env, founder, 'founder', corrects ? 'enquiry_log_correction' : 'enquiry_logged', a.id, { reference: ref, introduced_on: day, founding: f.founding, late_entry: late, corrects });
  return { reference: ref, founding: f.founding, founding_year_end: f.year_end, late_entry: late, ...(await enquiryLog(env)) };
}

/* Any relay enquiry the enquiry Worker did not log (for example one received before the relay was updated, or between
   migration 0005 and the Studio deployment) is logged by the Studio's daily run, from the relay record, BEFORE that record
   can reach its 24-month deletion. Reference, artist, artwork and time only; never buyer details. */
async function logMissingRelayEnquiries(env) {
  if (!(await agreementDocs(env))) return 0;
  const miss = await all(env, `SELECT e.id, e.reference, e.artist_id, e.artwork_id, e.created_at FROM enquiries e
    WHERE NOT EXISTS (SELECT 1 FROM enquiry_log l WHERE l.reference = e.reference)`);
  let n = 0;
  for (const e of miss) {
    const a = await one(env, 'SELECT id, founding, first_published_at FROM artists WHERE id = ?', e.artist_id);
    if (!a) continue;
    const f = AG.foundingAt(a, e.created_at);
    await env.DB.prepare(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind('l' + e.id.slice(1), e.reference, a.id, e.artwork_id, 'relay', e.created_at, f.founding, f.year_end, 'studio daily check', now(), 0).run();
    n++;
  }
  return n;
}

/* ---------------------------------------------------------------- acceptance record corrections (founder, 6 Nov 2026)
   A mistyped legal name, professional name or address in a recorded acceptance is corrected by SEPARATE linked rows
   (acceptance_corrections), one per document row of the acceptance, with a reason and a time. The acceptance itself
   (documents, versions, fingerprints, time, statement) is never changed, and a correction is never an acceptance. */
const CORR_FIELDS = { legal_name: 'Legal name', display_name: 'Professional name', account_email: 'Studio email address' };
function effectiveRows(rows, corr) {
  return rows.map(r => {
    const mine = corr.filter(c => c.acceptance_id === r.id).sort((a, b) => a.corrected_at.localeCompare(b.corrected_at));
    const out = { ...r, corrections: mine, original: { legal_name: r.legal_name, display_name: r.display_name, account_email: r.account_email } };
    for (const c of mine) out[c.field] = c.corrected_value;
    out.corrected = mine.length > 0;
    return out;
  });
}
async function corrections(env, artistId) {
  try { return await all(env, 'SELECT * FROM acceptance_corrections WHERE artist_id = ? ORDER BY corrected_at, id', artistId); } catch { return []; }
}
async function correctAcceptance(env, founder, artistId, b) {
  if (!(await agreementDocs(env))) throw new Bad('Acceptance records aren’t installed yet (migration 0005).', 503);
  const rows = await all(env, 'SELECT * FROM agreement_acceptances WHERE artist_id = ? AND event_id = ? ORDER BY doc_id', artistId, String(b.event_id || ''));
  if (!rows.length) throw new Bad('That acceptance wasn’t found for this artist', 404);
  const field = String(b.field || '');
  if (!CORR_FIELDS[field]) throw new Bad('Choose what to correct: legal name, professional name or Studio email address');
  if (rows[0].method !== 'studio_checkbox' && field !== 'display_name') throw new Bad('This earlier record was carried over as a label only: it never held a legal name or an address, so none can be added to it.');
  let value = b.value === undefined || b.value === null ? '' : String(b.value).trim();
  if (field === 'legal_name') value = value ? L.text(value, 2, 120, 'Legal name') : null;
  else if (field === 'display_name') value = L.text(value, 2, 80, 'Professional name');
  else value = L.artistEmail(value);
  const reason = String(b.reason || '').trim();
  if (reason.length < 10 || reason.length > 280) throw new Bad('Give the reason for the correction (10–280 characters)');
  if (L.privateHint(reason) && field !== 'account_email') throw new Bad('Keep contact details out of the reason');
  if (!['artist', 'founder'].includes(b.requested_by)) throw new Bad('Say who asked for the correction: the artist or you');
  if (b.confirm !== true) throw new Bad('Confirm the correction before saving');
  const eff = effectiveRows(rows, await corrections(env, artistId));
  if (eff.every(r => (r[field] ?? null) === value)) throw new Bad('That is already the recorded value');
  const group = rid('cg'), at = now();
  await env.DB.batch(eff.map(r => env.DB.prepare(`INSERT INTO acceptance_corrections (id, acceptance_id, artist_id, correction_group, field, previous_value, corrected_value, reason,
      requested_by, corrected_by, corrected_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(rid('cor'), r.id, artistId, group, field, r[field] ?? null, value, reason, b.requested_by, founder, at)));
  await audit(env, founder, 'founder', 'acceptance_corrected', artistId, { event: b.event_id, field, group, requested_by: b.requested_by });
  return { correction_group: group, corrected_at: at, rows: eff.length };
}

/* ---------------------------------------------------------------- ending participation (founder decision 6 Nov 2026)
   The artist may ask to leave at any time (Studio or email). The founder ends participation: from that moment the
   artist's pending submissions are withdrawn, nothing of theirs waits to publish, their gallery is queued for removal from
   plotnua.ie (licence 6.1: within 14 days), sign-in and enquiries stop, and the deletion dates are fixed:
     12 months after ending  original photographs, Studio account details, works and drafts (licence 6.5; privacy notice)
     6 years after ending    acceptance records, corrections, the enquiry log and the publication record (agreement 11.2)
   Deletion runs only when PARTICIPATION_DELETION is 'on' (off by default: switching it on is a release step). Every step
   is scoped to the one artist and recorded in participation_events and the audit log. Published web images remain in the
   private repository history and its audit branches (licence 6.6): listed for the founder, never touched automatically. */
const ENDING = { removal_days: 14, originals_months: 12, records_years: 6 };
const plusMonths = (iso, n) => { const d = new Date(iso); d.setUTCMonth(d.getUTCMonth() + n); return d.toISOString(); };
async function participationEvents(env, artistId) {
  try { return await all(env, 'SELECT * FROM participation_events WHERE artist_id = ? ORDER BY at, id', artistId); } catch { return null; }
}
async function participation(env, a) {
  const ev = await participationEvents(env, a.id);
  if (!ev) return { installed: false };
  const ended = ev.find(e => e.kind === 'ended') || null;
  const reqs = ev.filter(e => e.kind === 'leave_requested'), wd = ev.filter(e => e.kind === 'leave_request_withdrawn');
  const lastReq = reqs[reqs.length - 1], lastWd = wd[wd.length - 1];
  const request = lastReq && (!lastWd || lastWd.at < lastReq.at) ? { at: lastReq.at, actor: lastReq.actor, reason: lastReq.reason, due: new Date(Date.parse(lastReq.at) + ENDING.removal_days * 86400_000).toISOString() } : null;
  const out = { installed: true, request: ended ? null : request, ended: null, events: ev };
  if (!ended) return out;
  const d = JSON.parse(ended.detail || '{}');
  const from = d.notice_at || ended.at;   // agreement 10.1: the 14 days, the 12 months and the six years run from when the artist told PlotArt
  const rq = d.removal_queue ? await one(env, 'SELECT id, status, updated_at FROM publish_queue WHERE id = ?', d.removal_queue) : null;
  const ret = await one(env, 'SELECT * FROM record_retention WHERE artist_id = ?', a.id);
  const orig = ev.find(e => e.kind === 'originals_deleted');
  const stored = await one(env, "SELECT COUNT(*) AS n FROM images WHERE artist_id = ? AND r2_key <> 'erased'", a.id);
  const counts = { images: stored.n, works: (await one(env, 'SELECT COUNT(*) AS n FROM artworks WHERE artist_id = ?', a.id)).n,
    acceptances: (await one(env, 'SELECT COUNT(*) AS n FROM agreement_acceptances WHERE artist_id = ?', a.id)).n,
    enquiry_log: (await one(env, 'SELECT COUNT(*) AS n FROM enquiry_log WHERE artist_id = ?', a.id)).n,
    versions: (await one(env, 'SELECT COUNT(*) AS n FROM versions WHERE artist_id = ?', a.id)).n };
  const nowIso = now(), removalDue = new Date(Date.parse(from) + ENDING.removal_days * 86400_000).toISOString();
  out.ended = { at: ended.at, notice_at: from, by: ended.actor, reason: ended.reason, source: d.source || null, counts, schedule: [
    { key: 'gallery', what: 'Public gallery, artwork pages and Virtual Gallery card on plotnua.ie', rule: `Removed within ${ENDING.removal_days} days (licence 6.1)`, due: removalDue,
      state: !d.removal_queue ? 'not_published' : rq && rq.status === 'published' ? 'done' : nowIso > removalDue ? 'overdue' : 'pending', done_at: rq && rq.status === 'published' ? rq.updated_at : null, queue: rq },
    { key: 'originals', what: `Original photographs in Studio storage (${counts.images} now), Studio profile and contact details, works and drafts`, rule: `${ENDING.originals_months} months after ending (licence 6.5; privacy notice), or sooner on request`,
      due: plusMonths(from, ENDING.originals_months), state: orig ? 'done' : nowIso >= plusMonths(from, ENDING.originals_months) ? (env.PARTICIPATION_DELETION === 'on' ? 'due' : 'due_job_off') : 'scheduled', done_at: orig ? orig.at : null },
    { key: 'records', what: `Acceptance records and corrections (${counts.acceptances}), enquiry log (${counts.enquiry_log}), publication record (${counts.versions} versions), this ending record`, rule: `${ENDING.records_years} years after ending (agreement 11.2 and 5.5)`,
      due: ret ? ret.delete_after : null, state: ret && nowIso >= ret.delete_after ? (env.PARTICIPATION_DELETION === 'on' ? 'due' : 'due_job_off') : 'scheduled', done_at: null },
    { key: 'history', what: 'Web versions of published photographs in the private website repository history', rule: 'Kept, not public and not used (licence 6.6); removing them would need a history rewrite your release rules forbid', due: null, state: 'manual',
      branches: `content/plotart-${a.id}-v*` },
    { key: 'others', what: 'Copies made by others (search engine caches, screenshots, shares)', rule: 'Outside PlotArt’s control (licence 6.8): ask search engines to refresh', due: null, state: 'manual' },
    ...(a.application_ref ? [{ key: 'application', what: `Founding 25 application images (${a.application_ref})`, rule: 'Erase from Applications when no longer needed', due: null, state: 'manual' }] : []),
  ] };
  return out;
}
async function requestLeave(env, artist, b) {
  const a = await one(env, 'SELECT * FROM artists WHERE id = ?', artist.id);
  const pt = await participation(env, a);
  if (!pt.installed) throw new Bad('Please email hello@plotnua.ie to leave PlotArt.', 503);
  if (pt.request) throw new Bad('Your request to leave has already been received.', 409);
  if (b.confirm !== true) throw new Bad('Tick the box to confirm that you want to leave PlotArt');
  const reason = b.reason ? L.text(b.reason, 2, 280, 'Your reason', { optional: true }) : null;
  await env.DB.prepare('INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?,?,?,?,?,?,?)').bind(rid('pe'), a.id, 'leave_requested', now(), artist.email, reason, null).run();
  await audit(env, artist.email, 'artist', 'leave_requested', a.id, {});
  return { requested: true };
}
async function withdrawLeave(env, artist) {
  const a = await one(env, 'SELECT * FROM artists WHERE id = ?', artist.id);
  const pt = await participation(env, a);
  if (!pt.installed || !pt.request) throw new Bad('There is no request to withdraw', 409);
  await env.DB.prepare('INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?,?,?,?,?,?,?)').bind(rid('pe'), a.id, 'leave_request_withdrawn', now(), artist.email, null, null).run();
  await audit(env, artist.email, 'artist', 'leave_request_withdrawn', a.id, {});
  return { withdrawn: true };
}
async function endParticipation(env, founder, artistId, b) {
  const a = await one(env, 'SELECT * FROM artists WHERE id = ?', artistId);
  if (!a) throw new Bad('Artist not found', 404);
  const pt = await participation(env, a);
  if (!pt.installed) throw new Bad('Ending participation needs migration 0005.', 503);
  if (pt.ended) throw new Bad('Participation has already ended for this artist', 409);
  if (String(b.confirm_name || '').trim() !== a.display_name) throw new Bad(`Type the artist’s name exactly (${a.display_name}) to confirm`);
  const source = b.source === 'artist_request' ? 'artist_request' : b.source === 'founder' ? 'founder' : null;
  if (!source) throw new Bad('Say whether the artist asked to leave or you are ending it');
  const reason = String(b.reason || '').trim();
  if (reason.length < 10 || reason.length > 280) throw new Bad('Give the reason (10–280 characters)');
  const at = now();
  // When the artist told PlotArt (agreement 10.1): their Studio request, or the date of their email (Irish date), never
  // later than now. The founder ending it is the moment itself.
  let noticeAt = at;
  if (source === 'artist_request') {
    if (b.told_on) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(String(b.told_on)) || AG.addDays(String(b.told_on), 0) !== String(b.told_on)) throw new Bad('Enter the date the artist told PlotArt');
      noticeAt = AG.dublinMidnightUtc(String(b.told_on));
      if (noticeAt > at) throw new Bad('That date is in the future');
      if (Date.parse(at) - Date.parse(noticeAt) > 90 * 86400_000) throw new Bad('That date is more than 90 days ago: check it');
    } else if (pt.request) noticeAt = pt.request.at;
  }
  const lv = await latestVersion(env, a.id);
  const visible = (await all(env, VISIBLE_SQL)).some(r => r.artist_id === a.id);
  const pending = (await all(env, "SELECT id FROM publish_queue WHERE artist_id = ? AND status IN ('awaiting_founder','ready')", a.id)).length;
  const stmts = [
    env.DB.prepare("UPDATE submissions SET status='withdrawn', decided_at=? WHERE artist_id=? AND status='pending'").bind(at, a.id),
    env.DB.prepare("UPDATE publish_queue SET status='superseded', updated_at=? WHERE artist_id=? AND status IN ('awaiting_founder','ready')").bind(at, a.id),
  ];
  let removal = null;
  if (lv && (visible || pending || await one(env, "SELECT id FROM publish_queue WHERE artist_id=? AND status IN ('exporting','published') AND kind<>'remove' LIMIT 1", a.id))) {
    const v = lv.version + 1; removal = rid('q');
    stmts.push(env.DB.prepare('INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?,?,?,?,?)').bind(a.id, v, JSON.stringify({ ...lv.snap, works: [] }), 'ended', at),
      env.DB.prepare('INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)').bind(removal, a.id, v, 'remove', 'ready', at, at));
  }
  stmts.push(
    env.DB.prepare("UPDATE artists SET account_status='ended', updated_at=? WHERE id=?").bind(at, a.id),
    env.DB.prepare('INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?,?,?,?,?,?,?)')
      .bind(rid('pe'), a.id, 'ended', at, founder, reason, JSON.stringify({ source, notice_at: noticeAt, removal_queue: removal, pending_superseded: pending })),
    env.DB.prepare('INSERT INTO record_retention (artist_id, ended_at, delete_after, recorded_by, recorded_at) VALUES (?,?,?,?,?)')
      .bind(a.id, noticeAt, plusMonths(noticeAt, ENDING.records_years * 12), founder, at));
  await env.DB.batch(stmts);
  const publish = removal ? await requestGalleryPublish(env) : 'none';
  await audit(env, founder, 'founder', 'participation_ended', a.id, { source, removal_queue: removal, publish });
  return { ended_at: at, notice_at: noticeAt, removal_queue: removal, publish };
}
/* Stage 1 (12 months, or sooner on request): originals and the Studio account's personal content. Only for an ENDED artist. */
async function eraseOriginals(env, artistId, actor, why) {
  const a = await one(env, "SELECT * FROM artists WHERE id = ? AND account_status = 'ended'", artistId);
  const ev = await participationEvents(env, artistId);
  if (!a || !ev || !ev.some(e => e.kind === 'ended')) throw new Bad('Only an artist whose participation has ended', 409);
  if (ev.some(e => e.kind === 'originals_deleted')) throw new Bad('Already deleted', 409);
  const imgs = await all(env, 'SELECT id, r2_key, preview_key FROM images WHERE artist_id = ?', artistId);
  let objects = 0;
  for (const i of imgs) {
    if (i.r2_key && i.r2_key !== 'erased') { await env.IMAGES.delete(i.r2_key); objects++; }
    if (i.preview_key) { await env.IMAGES.delete(i.preview_key); objects++; }
  }
  const works = (await one(env, 'SELECT COUNT(*) AS n FROM artworks WHERE artist_id = ?', artistId)).n;
  const ofc = await commissionsInstalled(env);
  await env.DB.batch([
    env.DB.prepare('DELETE FROM images WHERE artist_id = ?').bind(artistId),
    env.DB.prepare('DELETE FROM artworks WHERE artist_id = ?').bind(artistId),
    env.DB.prepare('DELETE FROM submissions WHERE artist_id = ?').bind(artistId),
    env.DB.prepare(`UPDATE artists SET email=?, practice=NULL, medium=NULL, county=NULL, county_public=0, statement=NULL, bio=NULL, website=NULL, instagram=NULL,
      portrait_image_id=NULL, below_min_since=NULL, application_ref=NULL, updated_at=? WHERE id=? AND account_status='ended'`).bind(`ended-${artistId}@deleted.invalid`, now(), artistId),
    // Open for Commissions resets with the other profile details (only once migration 0011 has added the column)
    ...(ofc ? [env.DB.prepare("UPDATE artists SET open_for_commissions=0 WHERE id=? AND account_status='ended'").bind(artistId)] : []),
    env.DB.prepare('INSERT INTO participation_events (id, artist_id, kind, at, actor, reason, detail) VALUES (?,?,?,?,?,?,?)')
      .bind(rid('pe'), artistId, 'originals_deleted', now(), actor, why, JSON.stringify({ images: imgs.length, storage_objects: objects, works })),
  ]);
  const opportunities = await O.eraseFor(env, artistId);   // the artist's own Opportunities & delivery answers (absent table: skipped)
  await audit(env, actor, actor === 'scheduler' ? 'system' : 'founder', 'originals_deleted', artistId, { images: imgs.length, storage_objects: objects, works, opportunities, why });
  return { images: imgs.length, storage_objects: objects, works, opportunities };
}
/* Stage 2 (6 years): every remaining record of the artist, then the artist row. The append-only guards allow this only
   once record_retention.delete_after has passed. */
async function deleteRecords(env, artistId) {
  const ret = await one(env, 'SELECT * FROM record_retention WHERE artist_id = ?', artistId);
  if (!ret || now() < ret.delete_after) throw new Bad('The retention period has not ended', 409);
  const ev = await participationEvents(env, artistId);
  if (!ev.some(e => e.kind === 'originals_deleted')) await eraseOriginals(env, artistId, 'scheduler', 'with the six-year deletion');
  // Art for Hire records (migration 0007) go BEFORE record_retention: their append-only guards allow deletion only while
  // the artist's retention row still shows the period has ended (Stage 3B-1 finding). Absent tables are skipped.
  const t = [...(await O.recordTables(env)), ...((await termsInstalled(env)) ? ['gallery_agreement_acceptances', 'artist_terms'] : []), 'acceptance_corrections', 'agreement_acceptances', 'enquiry_log', 'enquiries', 'versions', 'publish_queue', 'gallery_positions', 'participation_events',
    ...(await H.recordTables(env)), 'record_retention'];
  await env.DB.batch([...t.map(x => env.DB.prepare(`DELETE FROM ${x} WHERE artist_id = ?`).bind(artistId)), env.DB.prepare("DELETE FROM artists WHERE id = ? AND account_status = 'ended'").bind(artistId),
    env.DB.prepare('DELETE FROM audit WHERE artist_id = ?').bind(artistId)]);   // the artist's audit trail goes with their records
  await audit(env, 'scheduler', 'system', 'records_deleted', artistId, { tables: t.length + 1 });
  return true;
}
async function runDeletionSchedule(env) {
  const out = { originals: 0, records: 0, enabled: env.PARTICIPATION_DELETION === 'on' };
  if (!out.enabled) return out;
  let ended;
  try { ended = await all(env, "SELECT e.artist_id, COALESCE(json_extract(e.detail, '$.notice_at'), e.at) AS at FROM participation_events e WHERE e.kind = 'ended'"); } catch { return out; }
  for (const e of ended) {
    const done = await one(env, "SELECT id FROM participation_events WHERE artist_id = ? AND kind = 'originals_deleted'", e.artist_id);
    if (!done && now() >= plusMonths(e.at, ENDING.originals_months)) { await eraseOriginals(env, e.artist_id, 'scheduler', `${ENDING.originals_months} months after ending`); out.originals++; }
  }
  for (const r of await all(env, 'SELECT artist_id, delete_after FROM record_retention')) {
    if (now() >= r.delete_after) { await deleteRecords(env, r.artist_id); out.records++; }
  }
  return out;
}
async function participationAdmin(env) {
  const artists = await all(env, 'SELECT * FROM artists ORDER BY display_name');
  const rows = [];
  for (const a of artists) {
    const pt = await participation(env, a);
    if (!pt.installed) return { installed: false, items: [], deletion_enabled: env.PARTICIPATION_DELETION === 'on' };
    rows.push({ id: a.id, display_name: a.display_name, account_status: a.account_status, founding: !!a.founding, founding_number: a.founding_number, request: pt.request, ended: pt.ended,
      events: pt.events.map(e => ({ kind: e.kind, at: e.at, actor: e.kind === 'leave_requested' || e.kind === 'leave_request_withdrawn' ? 'artist' : e.actor, reason: e.reason })) });
  }
  return { installed: true, deletion_enabled: env.PARTICIPATION_DELETION === 'on', rules: ENDING, items: rows };
}

/* ---------------------------------------------------------------- artist: profile and artworks */
const PROFILE = {
  display_name: v => L.text(v, 2, 80, 'Your name'),
  practice: v => L.text(v, 2, 60, 'Your practice', { optional: true }),
  medium: v => { if (v && !L.MEDIA.includes(v)) throw new Bad('Choose a medium from the list'); return v || null; },
  county: v => { if (v && !L.COUNTIES.includes(v)) throw new Bad('Choose a county from the list'); return v || null; },
  county_public: v => (v ? 1 : 0),
  statement: v => L.text(v, 10, 400, 'Your statement', { optional: true }),
  bio: v => L.text(v, 40, 2400, 'Your biography', { optional: true }),
  website: v => { if (!v) return null; if (!/^https:\/\/[^\s<>"']{4,200}$/.test(v)) throw new Bad('Your website must be a full https:// link'); return v; },
  instagram: v => { if (!v) return null; const h = String(v).replace(/^@/, ''); if (!/^[A-Za-z0-9._]{1,30}$/.test(h)) throw new Bad('Your Instagram name can use letters, numbers, dots and underscores'); return h; },
};
const WORK = {
  title: v => L.text(v, 1, 120, 'Title', { optional: true }),
  year: v => L.num(v, 1900, 2100, 'Year', { optional: true, int: true }),
  medium: v => L.text(v, 2, 120, 'Medium', { optional: true }),
  materials: v => L.text(v, 2, 160, 'Materials', { optional: true }),
  h_cm: v => L.num(v, 1, 2000, 'Height (cm)', { optional: true }),
  w_cm: v => L.num(v, 1, 2000, 'Width (cm)', { optional: true }),
  d_cm: v => L.num(v, 0.1, 2000, 'Depth (cm)', { optional: true }),
  price_eur: v => L.num(v, 1, 1000000, 'Price (€)', { optional: true, int: true }),
  price_on_request: v => (v ? 1 : 0),
  description: v => L.text(v, 10, 1200, 'Description', { optional: true }),
  ai_involvement: v => { if (v && !L.AI.includes(v)) throw new Bad('Answer the AI question'); return v || null; },
  ai_note: v => L.text(v, 10, 400, 'AI disclosure', { optional: true }),
};
function clean(spec, body) {
  const out = {};
  for (const [k, v] of Object.entries(body || {})) {
    if (!(k in spec)) throw new Bad(`Unknown field ${k}`);
    out[k] = spec[k](v);
  }
  return out;
}
async function ownWork(env, artist, id) {
  const w = await one(env, 'SELECT * FROM artworks WHERE id = ? AND artist_id = ?', id, artist.id);
  if (!w) throw new Bad('Not found', 404);
  return w;
}
async function ownImage(env, artist, id) {
  const i = await one(env, 'SELECT * FROM images WHERE id = ? AND artist_id = ? AND deleted_at IS NULL', id, artist.id);
  if (!i) throw new Bad('Not found', 404);
  return i;
}

/* Instant changes (availability, removal, order) reach the live gallery without review: a new version is made from the
   latest version with ONLY those fields applied, and queued (auto-published when INSTANT_AUTOPUBLISH is on). */
async function instant(env, artist, actor, what) {
  const lv = await latestVersion(env, artist.id);
  if (!lv) return null;
  const d = await load(env, artist.id);
  const next = L.applyInstant(lv.snap, L.snapshot(d.artist, d.works, d.images));
  if (JSON.stringify(next) === JSON.stringify(lv.snap)) return null;
  const v = lv.version + 1;
  await env.DB.batch([
    env.DB.prepare('INSERT INTO versions (artist_id, version, snapshot, source, created_at, ai_decisions) VALUES (?,?,?,?,?,?)')
      .bind(artist.id, v, JSON.stringify(next), 'instant', now(), lv.ai_decisions || null),
    env.DB.prepare("UPDATE publish_queue SET status='superseded', updated_at=? WHERE artist_id=? AND kind='instant' AND status='awaiting_founder'").bind(now(), artist.id),
    env.DB.prepare('INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)')
      .bind(rid('q'), artist.id, v, 'instant', env.INSTANT_AUTOPUBLISH === 'true' ? 'ready' : 'awaiting_founder', now(), now()),
  ]);
  // publish at once only when the founder has switched this on (instant updates are pre-authorised; default: the schedule)
  const publish = env.INSTANT_AUTOPUBLISH === 'true' && env.INSTANT_PUBLISH_DISPATCH === 'true' ? await requestGalleryPublish(env) : 'scheduled';
  await audit(env, actor, 'artist', 'instant_change', artist.id, { what, version: v, publish });
  return v;
}

async function upload(req, env, artist, { artworkId = null, role }) {
  const buf = await req.arrayBuffer();
  if (buf.byteLength > L.MAX_BYTES) throw new Bad('The file is over 30 MB.', 413);
  const u8 = new Uint8Array(buf);
  const c = L.checkImage(u8, { portrait: role === 'portrait', minLong: minLong(env) });
  if (!c.fmt || c.blocks.length) return json({ ok: false, blocks: c.blocks, warns: c.warns }, 422);
  const sha = await L.sha256(buf);
  const same = await all(env, 'SELECT artist_id, artwork_id FROM images WHERE sha256 = ? AND deleted_at IS NULL', sha);
  const mine = same.filter(x => x.artist_id === artist.id);
  if (mine.some(x => x.artwork_id === artworkId && role !== 'portrait')) return json({ ok: false, blocks: ['You have already uploaded this exact photograph for this artwork.'], warns: [] }, 422);
  if (mine.length) c.warns.push('You have used this exact photograph for another artwork too.');
  const flags = same.some(x => x.artist_id !== artist.id) ? ['DUPLICATE_OF_OTHER_ARTIST'] : [];   // never revealed to the artist
  const id = rid('i');
  const key = `originals/${artist.id}/${id}`;
  await env.IMAGES.put(key, buf, { httpMetadata: { contentType: `image/${c.fmt}` }, customMetadata: { sha256: sha } });
  if (role === 'main' || role === 'portrait') {
    const old = role === 'portrait' ? await all(env, "SELECT id FROM images WHERE artist_id=? AND role='portrait' AND deleted_at IS NULL", artist.id)
      : await all(env, "SELECT id FROM images WHERE artist_id=? AND artwork_id=? AND role='main' AND deleted_at IS NULL", artist.id, artworkId);
    for (const o of old) await env.DB.prepare('UPDATE images SET deleted_at=? WHERE id=?').bind(now(), o.id).run();
  } else {
    const n = await one(env, "SELECT COUNT(*) AS n FROM images WHERE artist_id=? AND artwork_id=? AND role='view' AND deleted_at IS NULL", artist.id, artworkId);
    if (n.n >= L.MAX_VIEWS) { await env.IMAGES.delete(key); throw new Bad('Up to 3 extra views per artwork'); }
  }
  const prev = role === 'portrait' ? null : await one(env, "SELECT alt, photographer, photo_credit FROM images WHERE artist_id=? AND artwork_id=? AND deleted_at IS NOT NULL AND role=? ORDER BY deleted_at DESC LIMIT 1", artist.id, artworkId, role);
  await env.DB.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, photo_credit, checks, ord, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`).bind(id, artist.id, artworkId, role, key, sha, buf.byteLength, c.dims.w, c.dims.h, c.fmt,
    prev?.alt || null, prev?.photographer || null, prev?.photo_credit || null, JSON.stringify({ blocks: [], warns: c.warns, flags }), Date.now() % 1e9, now()).run();
  if (role === 'portrait') await env.DB.prepare('UPDATE artists SET portrait_image_id=?, updated_at=? WHERE id=?').bind(id, now(), artist.id).run();
  await audit(env, artist.email, 'artist', 'image_upload', artist.id, { id, role, artworkId, bytes: buf.byteLength, w: c.dims.w, h: c.dims.h, flags });
  return json({ ok: true, id, warns: c.warns, width: c.dims.w, height: c.dims.h });
}

async function submit(env, artist, body) {
  const d = await load(env, artist.id);
  const snap = L.snapshot(d.artist, d.works, d.images);
  const lv = await latestVersion(env, artist.id);
  const cs = L.changes(lv && lv.snap, snap).filter(c => c.tier !== 'instant');
  if (!cs.length) throw new Bad('There are no changes to submit');
  // Founding Artist Agreement (development 6 Nov 2026): a FULL submission (always the case for a first publication) needs
  // the current texts accepted in Studio first (POST /api/agreement/accept). A quick-check submission from an artist who
  // already holds a licence the publishing pipeline accepts is never blocked. Nothing is accepted on submission any more.
  const ag = await agreementState(env, d.artist);
  const licence = ag.accepted || (L.tierOf(cs) !== 'full' && !!ag.licence && AG.PUBLISHABLE_LICENCES.includes(ag.licence.version));
  const problems = L.readiness(snap, { founding: !!d.artist.founding, programme: ag.programme, firstPublication: !lv, licenceOk: licence, imageBlocks: blocked(d.images) });
  if (problems.length) return json({ ok: false, problems }, 422);
  await env.DB.prepare("UPDATE submissions SET status='withdrawn', decided_at=? WHERE artist_id=? AND status='pending'").bind(now(), artist.id).run();
  const id = rid('s');
  const note = L.text(body.note, 2, 600, 'Your note', { optional: true });
  await env.DB.prepare('INSERT INTO submissions (id, artist_id, created_at, tier, status, note, snapshot, changes, base_version) VALUES (?,?,?,?,?,?,?,?,?)')
    .bind(id, artist.id, now(), L.tierOf(cs), 'pending', note, JSON.stringify(snap), JSON.stringify(cs), lv ? lv.version : 0).run();
  await audit(env, artist.email, 'artist', 'submit', artist.id, { id, tier: L.tierOf(cs), changes: cs.length });
  return json({ ok: true, id, tier: L.tierOf(cs) });
}

/* ---------------------------------------------------------------- preview */
function previewPkg(snap, images) {
  const dims = Object.fromEntries(images.map(i => [i.id, i]));
  // The preview serves the browser-made preview copy (long side at most 1600 px, made in ui/studio.js with exactly this
  // rounding) when there is one, otherwise the original. The srcset width must describe THAT file: describing the
  // original's width made browsers shrink the picture by original/1600 (Uisce Salach V, 7200 px, showed at ~22%; 12 Nov 2026).
  const served = d => { if (!d) return [undefined, undefined]; if (!d.preview_key) return [d.width, d.height];
    const s = Math.min(1, 1600 / Math.max(d.width, d.height)); return [Math.round(d.width * s), Math.round(d.height * s)]; };
  const fix = i => { if (!i) return i; const [pw, ph] = served(dims[i.id]); return { ...i, pw, ph }; };
  return {
    artist: { ...snap.artist, county: snap.artist.county_public ? snap.artist.county : null, portrait: fix(snap.artist.portrait) },
    works: snap.works.filter(w => w.images.some(i => i.role === 'main')).map(w => ({ ...w, title: w.title || 'Untitled', medium: w.medium || '', images: w.images.map(fix) })),
  };
}
function previewRoute(path, pkg, bar) {
  const works = shown(pkg);
  if (path === '' || path === 'index.html') return html(previewPage(`${pkg.artist.display_name} · preview`, artistBody(pkg), bar));
  const i = works.findIndex(w => `${w.slug}.html` === path);
  if (i < 0) return html('Not found', 404);
  return html(previewPage(`${works[i].title} · preview`, artworkBody(pkg, works[i], works[i - 1], works[i + 1]), bar));
}
async function previewImage(env, img) {
  const o = await env.IMAGES.get(img.preview_key || img.r2_key);
  if (!o) return res('Not found', 'text/plain', 404);
  return new Response(o.body, { headers: { 'Content-Type': img.preview_key ? 'image/jpeg' : `image/${img.format}`, ...SEC, 'Cache-Control': 'private, max-age=300' } });
}

/* ---------------------------------------------------------------- founder */
/* ---- Gallery order (founder decision 31 Oct 2026). Display positions 01-25 in the public Virtual Gallery, set only by
   the founder. A position holds an artist or a reservation (with a private note that is never exported). An artist's
   permanent Founding 25 number (artists.founding_number) is separate and never changes when the order changes. */
const POSITIONS = 25;
// An artist is visible to the pipeline only while a gallery is published or being published (not removed).
const VISIBLE_SQL = `SELECT q.artist_id FROM publish_queue q WHERE q.status IN ('exporting','published')
  AND q.version = (SELECT MAX(q2.version) FROM publish_queue q2 WHERE q2.artist_id = q.artist_id AND q2.status IN ('exporting','published'))
  AND q.kind <> 'remove'`;
async function galleryOrder(env) {
  const rows = await all(env, `SELECT g.position, g.artist_id, g.reserved, g.note, g.updated_at, a.display_name, a.slug, a.founding, a.founding_number, a.account_status
    FROM gallery_positions g LEFT JOIN artists a ON a.id = g.artist_id ORDER BY g.position`);
  const visible = new Set((await all(env, VISIBLE_SQL)).map(r => r.artist_id));
  const by = new Map(rows.map(r => [r.position, r]));
  const positions = [];
  for (let n = 1; n <= POSITIONS; n++) {
    const r = by.get(n);
    positions.push(!r ? { position: n, state: 'open' } : r.reserved ? { position: n, state: 'reserved', note: r.note || '' }
      : { position: n, state: 'artist', artist_id: r.artist_id, display_name: r.display_name, slug: r.slug, founding: !!r.founding,
          founding_number: r.founding_number, live: visible.has(r.artist_id) });
  }
  const placed = new Set(rows.filter(r => r.artist_id).map(r => r.artist_id));
  const artists = (await all(env, `SELECT id, display_name, slug, founding, founding_number, account_status, first_published_at FROM artists
    WHERE account_status IN ('invited','active') ORDER BY founding DESC, display_name`))
    .map(a => ({ ...a, founding: !!a.founding, live: visible.has(a.id), placed: placed.has(a.id) }));
  return { positions, artists };
}
// What the publishing pipeline sees: position, the gallery address of a published (or publishing) artist, or reserved.
async function pipelineOrder(env) {
  const rows = await all(env, 'SELECT g.position, g.artist_id, g.reserved, a.slug FROM gallery_positions g LEFT JOIN artists a ON a.id = g.artist_id ORDER BY g.position');
  const visible = new Set((await all(env, VISIBLE_SQL)).map(r => r.artist_id));
  const positions = rows.map(r => ({ position: r.position, slug: r.artist_id && visible.has(r.artist_id) ? r.slug : null, reserved: !!r.reserved }));
  const placed = new Set(rows.map(r => r.artist_id).filter(Boolean));
  const extra = (await all(env, `SELECT id, slug FROM artists WHERE id IN (${VISIBLE_SQL}) ORDER BY COALESCE(first_published_at, '9999'), created_at, id`))
    .filter(a => !placed.has(a.id)).map(a => a.slug);
  return { positions, extra };
}
// First publication of a Founding Artist with no position: the lowest position that is neither taken nor reserved.
// Never moves anyone; never takes a reserved position; does nothing when all 25 are taken.
// Founding Artist Agreement (development 6 Nov 2026), shared by Publish and Retry publishing. Availability, withdrawal,
// order and removal are never held up. Reviewed content: a FIRST publication needs the current texts accepted; an artist
// who is already published and has not accepted yet is published only after the founder confirms the warning.
async function agreementGate(env, q, req) {
  if (q.kind !== 'reviewed') return { warned: false };
  const a = await one(env, 'SELECT * FROM artists WHERE id=?', q.artist_id);
  const ag = await agreementState(env, a);
  const first = !a.first_published_at && !(await one(env, "SELECT id FROM publish_queue WHERE artist_id=? AND status IN ('published','superseded') AND kind<>'remove' LIMIT 1", a.id));
  if (!ag.accepted && first) throw new Bad(`${a.display_name} has not accepted the ${AG.PROGRAMME_NAME[ag.programme]} yet, so their gallery can’t be published for the first time. They accept it in PlotArt Studio.`, 409);
  if (ag.accepted) return { warned: false };
  const b = await req.json().catch(() => ({}));
  if (b.confirm_without_agreement !== true) return { response: json({ ok: false, needs_confirmation: true, error: `${a.display_name} is already published but hasn’t accepted the ${ag.programme === 'licence_only' ? 'current licence' : AG.PROGRAMME_NAME[ag.programme]} yet. Their existing licence (${ag.licence ? ag.licence.version : 'none'}) still applies. Publish anyway?` }, 409) };
  return { warned: true };
}

// Retry publishing (development 12 Nov 2026). A FAILED job goes back to 'ready' unchanged: same queue record, same
// approved version (snapshot, AI decisions, approval), so the protected publishing workflow and every image-provenance
// check run again exactly as for Publish. Refused unless: the job failed; the artist is active or invited; for reviewed
// content the submission behind the version is still approved; no newer version exists or is published; and nothing
// else for that artist is ready or exporting. The switch itself is one conditional UPDATE, so two presses (or two
// tabs) can never queue it twice. The earlier failure stays in the audit log.
async function retryPublication(env, founder, id, req) {
  const q = await one(env, 'SELECT * FROM publish_queue WHERE id=?', id);
  if (!q) throw new Bad('That publication job doesn’t exist', 404);
  if (q.status === 'ready' || q.status === 'exporting') throw new Bad('This publication is already being published: it can’t be retried until it finishes', 409);
  if (q.status === 'published') throw new Bad('This version is already published: there is nothing to retry', 409);
  if (q.status !== 'failed') throw new Bad('Only a publication that failed can be retried', 409);
  const a = await one(env, 'SELECT id, display_name, account_status FROM artists WHERE id=?', q.artist_id);
  if (!a || !['invited', 'active'].includes(a.account_status)) throw new Bad('This artist’s account isn’t active, so their gallery can’t be published', 409);
  if (q.kind === 'reviewed') {
    const v = await one(env, 'SELECT source FROM versions WHERE artist_id=? AND version=?', q.artist_id, q.version);
    const s = v && await one(env, 'SELECT status FROM submissions WHERE id=?', v.source);
    if (!s || s.status !== 'approved') throw new Bad('The submission behind this version is no longer approved, so it can’t be published', 409);
  }
  if (await one(env, "SELECT id FROM publish_queue WHERE artist_id=? AND id<>? AND version>=? AND status<>'superseded' LIMIT 1", q.artist_id, q.id, q.version))
    throw new Bad('A newer version of this gallery exists, so this older version can’t be retried', 409);
  if (await one(env, "SELECT id FROM publish_queue WHERE artist_id=? AND id<>? AND status IN ('ready','exporting') LIMIT 1", q.artist_id, q.id))
    throw new Bad('Another publication for this artist is already in progress: try again once it has finished', 409);
  const gate = await agreementGate(env, q, req);
  if (gate.response) return gate.response;
  const r = await env.DB.prepare(`UPDATE publish_queue SET status='ready', updated_at=? WHERE id=? AND status='failed'
    AND NOT EXISTS (SELECT 1 FROM publish_queue o WHERE o.artist_id=publish_queue.artist_id AND o.id<>publish_queue.id
      AND (o.status IN ('ready','exporting') OR (o.version>=publish_queue.version AND o.status<>'superseded')))`).bind(now(), q.id).run();
  if (!r.meta || r.meta.changes !== 1) throw new Bad('This publication has already been retried', 409);
  const attempt = 1 + (await one(env, "SELECT COUNT(*) AS n FROM audit WHERE action='publish_retry' AND artist_id=? AND detail LIKE ?", q.artist_id, `%"queue":"${q.id}"%`)).n;
  const publish = await requestGalleryPublish(env);
  await audit(env, founder, 'founder', 'publish_retry', q.artist_id, { queue: q.id, version: q.version, attempt, publish,
    previous_failure: String(q.detail || '').slice(0, 2000), ...(gate.warned ? { without_current_agreement: true } : {}) });
  return json({ ok: true, publish, attempt });
}

async function placeOnFirstPublication(env, artistId) {
  const a = await one(env, 'SELECT id, founding FROM artists WHERE id = ?', artistId);
  if (!a || !a.founding || await one(env, 'SELECT position FROM gallery_positions WHERE artist_id = ?', artistId)) return null;
  const used = new Set((await all(env, 'SELECT position FROM gallery_positions')).map(r => r.position));
  for (let n = 1; n <= POSITIONS; n++) {
    if (used.has(n)) continue;
    await env.DB.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(n, artistId, now()).run();
    await audit(env, 'pipeline', 'pipeline', 'position_assigned', artistId, { position: n, rule: 'lowest open position on first publication' });
    return n;
  }
  return null;
}
async function saveGalleryOrder(env, founder, body) {
  const list = Array.isArray(body && body.positions) ? body.positions : null;
  if (!list || list.length > POSITIONS) throw new Bad('Send the positions to save');
  const seenPos = new Set(), seenArt = new Set(), rows = [];
  for (const e of list) {
    const n = Number(e && e.position);
    if (!Number.isInteger(n) || n < 1 || n > POSITIONS || seenPos.has(n)) throw new Bad('Each position is a number from 1 to 25, used once');
    seenPos.add(n);
    if (e.state === 'reserved') {
      const note = e.note == null || String(e.note).trim() === '' ? null : L.text(e.note, 1, 140, 'Reservation note');
      rows.push({ position: n, artist_id: null, reserved: 1, note });
    } else if (e.state === 'artist') {
      const id = String(e.artist_id || '');
      if (!/^a[0-9a-z]+$/.test(id) || seenArt.has(id)) throw new Bad('Each artist can hold one position');
      if (!(await one(env, "SELECT id FROM artists WHERE id = ? AND account_status IN ('invited','active')", id))) throw new Bad('That artist can’t be placed', 409);
      seenArt.add(id);
      rows.push({ position: n, artist_id: id, reserved: 0, note: null });
    } else if (e.state !== 'open') throw new Bad('Each position is open, reserved or an artist');
  }
  // Artists who keep a position but are no longer active (suspended or ended) keep it unless the founder releases it.
  const kept = await all(env, "SELECT g.position, g.artist_id FROM gallery_positions g JOIN artists a ON a.id = g.artist_id WHERE a.account_status NOT IN ('invited','active')");
  for (const k of kept) if (!seenPos.has(k.position) && !seenArt.has(k.artist_id)) rows.push({ position: k.position, artist_id: k.artist_id, reserved: 0, note: null });
  const before = await all(env, 'SELECT position, artist_id, reserved, note FROM gallery_positions ORDER BY position');
  const t = now();
  await env.DB.batch([env.DB.prepare('DELETE FROM gallery_positions'),
    ...rows.map(r => env.DB.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,?,?,?)').bind(r.position, r.artist_id, r.reserved, r.note, t))]);
  const brief = rs => rs.slice().sort((a, b) => a.position - b.position).map(r => r.reserved ? `${r.position}:reserved` : `${r.position}:${r.artist_id}`);
  const moved = JSON.stringify(brief(before)) !== JSON.stringify(brief(rows));   // a move, reservation or release changes the public grid
  const publish = moved ? await requestGalleryPublish(env) : 'none';
  await audit(env, founder, 'founder', 'gallery_order', null, { before: brief(before), after: brief(rows), publish,
    notes_changed: JSON.stringify(before.filter(r => r.reserved).map(r => [r.position, r.note])) !== JSON.stringify(rows.filter(r => r.reserved).sort((a, b) => a.position - b.position).map(r => [r.position, r.note])) });
  return { ...(await galleryOrder(env)), publish };
}

async function overview(env) {
  const artists = await all(env, 'SELECT id, slug, email, display_name, founding, founding_number, account_status, licence_version, licence_accepted_at, first_published_at, application_ref, created_at FROM artists ORDER BY created_at');
  const out = [];
  for (const a of artists) {
    const st = await status(env, a);
    const pt = await participation(env, a);
    out.push({ ...a, programme: AG.programmeOf(a, await termsFor(env, a.id)), state: st.state, works: st.counts.works, problems: st.problems.length, live_version: st.live_version, latest_version: st.latest_version, agreement: st.agreement,
      leave_requested_at: pt.request ? pt.request.at : null, ended_at: pt.ended ? pt.ended.at : null });
  }
  const subs = await all(env, `SELECT s.id, s.artist_id, s.created_at, s.tier, s.note, a.display_name FROM submissions s JOIN artists a ON a.id = s.artist_id
    WHERE s.status = 'pending' ORDER BY (s.tier = 'light'), s.created_at`);
  // a failed job is shown only while it is the artist's newest version: once a newer version exists (waiting, publishing
  // or live), the old failure is history (it stays in the audit log and the record) and could never be retried anyway
  const queue = await all(env, `SELECT q.*, a.display_name FROM publish_queue q JOIN artists a ON a.id = q.artist_id WHERE (q.status IN ('awaiting_founder','ready','exporting')
    OR (q.status = 'failed' AND NOT EXISTS (SELECT 1 FROM publish_queue n WHERE n.artist_id = q.artist_id AND n.version > q.version AND n.status <> 'superseded'))) ORDER BY q.created_at`);
  const flags = await all(env, `SELECT i.id, i.artist_id, a.display_name, i.sha256 FROM images i JOIN artists a ON a.id=i.artist_id WHERE i.deleted_at IS NULL AND i.checks LIKE '%DUPLICATE_OF_OTHER_ARTIST%'`);
  return { artists: out, submissions: subs, queue, flags, agreement_installed: !!(await agreementDocs(env)), f25: { selected_with_studio: artists.filter(a => a.founding).length, target: 25 },
    instant_autopublish: env.INSTANT_AUTOPUBLISH === 'true', terms_installed: await termsInstalled(env) };
}
async function decide(env, founder, id, body) {
  const s = await one(env, "SELECT * FROM submissions WHERE id = ? AND status = 'pending'", id);
  if (!s) throw new Bad('That submission is no longer waiting for a decision', 409);
  const decision = body.decision;
  if (!['approve', 'changes', 'decline'].includes(decision)) throw new Bad('Choose approve, request changes or decline');
  const msg = decision === 'approve' ? L.text(body.message, 2, 1200, 'Message', { optional: true }) : L.text(body.message, 5, 1200, 'Message to the artist');
  if (decision !== 'approve') {
    await env.DB.prepare('UPDATE submissions SET status=?, founder_message=?, decided_at=? WHERE id=?').bind(decision === 'changes' ? 'changes_requested' : 'declined', msg, now(), id).run();
    await audit(env, founder, 'founder', `submission_${decision}`, s.artist_id, { id });
    return json({ ok: true });
  }
  const snap = JSON.parse(s.snapshot);
  const ai = body.ai_decisions || {};
  for (const w of snap.works) if (w.ai_involvement === 'generated' && !['approved', 'declined'].includes(ai[w.id])) throw new Bad(`Decide whether “${w.title}” (entirely prompt-generated) is eligible`);
  if (snap.works.some(w => ai[w.id] === 'declined')) throw new Bad('A declined artwork can’t be published: request changes instead');
  const d = await load(env, s.artist_id);
  const merged = L.applyInstant(snap, L.snapshot(d.artist, d.works, d.images));       // later availability / removals win
  merged.works.push(...[]);                                                               // (no new works ever added here)
  const lv = await latestVersion(env, s.artist_id);
  const v = (lv ? lv.version : 0) + 1;
  const prevAi = lv && lv.ai_decisions ? JSON.parse(lv.ai_decisions) : {};
  await env.DB.batch([
    env.DB.prepare("UPDATE submissions SET status='approved', founder_message=?, decided_at=? WHERE id=?").bind(msg, now(), id),
    env.DB.prepare('INSERT INTO versions (artist_id, version, snapshot, source, created_at, ai_decisions) VALUES (?,?,?,?,?,?)')
      .bind(s.artist_id, v, JSON.stringify(merged), id, now(), JSON.stringify({ ...prevAi, ...ai })),
    env.DB.prepare("UPDATE publish_queue SET status='superseded', updated_at=? WHERE artist_id=? AND status='awaiting_founder'").bind(now(), s.artist_id),
    env.DB.prepare('INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)')
      .bind(rid('q'), s.artist_id, v, 'reviewed', 'awaiting_founder', now(), now()),
  ]);
  await audit(env, founder, 'founder', 'submission_approve', s.artist_id, { id, version: v });
  return json({ ok: true, version: v });
}

/* ---------------------------------------------------------------- pipeline */
async function exportFor(env, q) {
  const artist = await one(env, 'SELECT * FROM artists WHERE id = ?', q.artist_id);
  const v = await one(env, 'SELECT * FROM versions WHERE artist_id = ? AND version = ?', q.artist_id, q.version);
  const snap = JSON.parse(v.snapshot);
  const lic = (await agreementState(env, artist)).licence || {};   // the most recent licence acceptance (new record first, then the legacy label)
  const g = L.exportGallery(snap, { version: q.version, approvedAt: v.created_at, licenceVersion: lic.version || null,
    licenceAcceptedAt: lic.accepted_at || null, artistId: artist.id, aiDecisions: v.ai_decisions ? JSON.parse(v.ai_decisions) : {} });
  const ids = [...snap.works.flatMap(w => w.images.map(i => i.id)), ...(snap.artist.portrait ? [snap.artist.portrait.id] : [])];
  return { gallery: g, images: ids, kind: q.kind };
}

/* ---------------------------------------------------------------- PlotNua Idea Board (Phase 1, 1 Nov 2026)
   The founder's moderation of homeowner ideas. The public intake Worker (ideas.js) only ever inserts 'received' ideas;
   nothing is public until the founder approves it here, and only the content pipeline publishes approved ideas.
   Declined and removed ideas are deleted 30 days after the decision. Until migration 0003 is applied these routes
   say so (503) instead of failing. */
const IDEA_PURGE_DAYS = 30;          // declined or removed: deleted 30 days after the decision
const IDEA_PENDING_DAYS = 90;        // waiting for review: deleted 90 days after it arrived (founder decision 1 Nov 2026)
const IDEA_WARN_DAYS = 14;           // the Ideas tab warns this many days before a waiting idea is deleted
async function ideasReady(env) {
  const t = await env.DB.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='ideas'").first();
  if (!t) throw new Bad('The Idea Board isn’t installed yet (migration 0003 has not been applied).', 503);
}
async function purgeIdeas(env) {
  // Retention. Each DELETE names the statuses it may touch; an approved idea is never deleted here (only a founder's
  // "Remove from the board" can take it down, and it is then deleted 30 days later).
  const ago = d => new Date(Date.now() - d * 86400_000).toISOString();
  const a = await env.DB.prepare("DELETE FROM ideas WHERE status IN ('not_approved','removed') AND COALESCE(removed_at, decided_at) < ?").bind(ago(IDEA_PURGE_DAYS)).run();
  const b = await env.DB.prepare("DELETE FROM ideas WHERE status = 'received' AND created_at < ?").bind(ago(IDEA_PENDING_DAYS)).run();
  await env.DB.prepare('DELETE FROM idea_intake_days WHERE day < ?').bind(ago(IDEA_PURGE_DAYS).slice(0, 10)).run();
  return ((a.meta && a.meta.changes) || 0) + ((b.meta && b.meta.changes) || 0);
}
async function ideasAdmin(env) {
  await ideasReady(env); await purgeIdeas(env);
  const cols = 'id, ref, text, public_text, area, county, show_county, status, became_discovery, edited, created_at, decided_at, decided_by, published_at, removed_at';
  const waiting = (await all(env, `SELECT ${cols} FROM ideas WHERE status='received' ORDER BY created_at`)).map(i => {
    const expires = new Date(Date.parse(i.created_at) + IDEA_PENDING_DAYS * 86400_000);
    return { ...i, expires_at: expires.toISOString(), days_left: Math.max(0, Math.ceil((expires - Date.now()) / 86400_000)) };
  });
  return {
    waiting, expiring_soon: waiting.filter(i => i.days_left <= IDEA_WARN_DAYS).length, pending_days: IDEA_PENDING_DAYS, warn_days: IDEA_WARN_DAYS,
    approved: await all(env, `SELECT ${cols} FROM ideas WHERE status='approved' ORDER BY published_at DESC, id DESC`),
    decided: await all(env, `SELECT ${cols} FROM ideas WHERE status IN ('not_approved','removed') ORDER BY COALESCE(removed_at, decided_at) DESC LIMIT 50`),
    areas: IDEA_AREAS, purge_days: IDEA_PURGE_DAYS,
  };
}
async function decideIdea(env, actor, id, b) {
  await ideasReady(env);
  const i = await one(env, 'SELECT * FROM ideas WHERE id = ?', id);
  if (!i) throw new Bad('That idea no longer exists.', 404);
  const action = String(b && b.action || '');
  const at = now();
  if (action === 'not_approve') {
    if (i.status !== 'received') throw new Bad('Only an idea waiting for review can be declined.', 409);
    await env.DB.prepare("UPDATE ideas SET status='not_approved', decided_at=?, decided_by=? WHERE id=?").bind(at, actor, id).run();
  } else if (action === 'remove') {
    if (i.status !== 'approved') throw new Bad('Only an idea on the board can be removed.', 409);
    await env.DB.prepare("UPDATE ideas SET status='removed', removed_at=?, decided_by=? WHERE id=?").bind(at, actor, id).run();
  } else if (action === 'approve' || action === 'save') {
    if (action === 'approve' && i.status !== 'received') throw new Bad('Only an idea waiting for review can be approved.', 409);
    if (action === 'save' && i.status !== 'approved') throw new Bad('Only an idea on the board can be updated.', 409);
    const text = ideaClean(b.public_text === undefined || b.public_text === null ? (i.public_text || i.text) : b.public_text);
    const why = ideaProblem(text);
    if (why) throw new Bad(why);
    const area = b.area === undefined ? i.area : (ideaClean(b.area) || null);
    if (area && !IDEA_AREAS.includes(area)) throw new Bad('Please choose an area from the list.');
    const disc = b.became_discovery === undefined ? i.became_discovery : (ideaClean(b.became_discovery) || null);
    if (disc && !/^discovery-[a-z0-9-]+\.html$/.test(disc)) throw new Bad('A Discovery link must be a PlotNua Discovery page, e.g. discovery-hidden-cars.html.');
    const show = b.hide_county ? 0 : i.show_county;       // the founder may hide a county, never show one the visitor kept private
    const pub = text === i.text ? null : text;
    await env.DB.prepare("UPDATE ideas SET status='approved', public_text=?, area=?, became_discovery=?, show_county=?, edited=?, decided_at=COALESCE(decided_at, ?), decided_by=?, published_at=COALESCE(published_at, ?) WHERE id=?")
      .bind(pub, area, disc, show, pub ? 1 : 0, at, actor, at, id).run();
  } else if (action === 'delete') {
    // Erasure now (e.g. a visitor's removal request quoting their reference). An idea on the board must be removed first.
    if (i.status === 'approved') throw new Bad('Remove it from the board first; it is then deleted on the next publish.', 409);
    await env.DB.prepare("DELETE FROM ideas WHERE id = ? AND status <> 'approved'").bind(id).run();
  } else throw new Bad('Unknown action');
  await audit(env, actor, 'founder', 'idea_' + action, null, { ref: i.ref });
  // Publish on approval (founder decision 2 Nov 2026): an action that changes what the public board shows starts the
  // Idea Board publishing workflow at once. Declining or deleting a waiting idea changes nothing public. Only this
  // founder-only route can start it; the public intake Worker holds no GitHub credential.
  const publicChange = action === 'approve' || action === 'remove' || action === 'save';
  const publish = publicChange ? await requestIdeasPublish(env) : 'none';
  return { ...(await ideasAdmin(env)), publish };
}
// Starts .github/workflows/plotnua-ideas-publish.yml on main through GitHub's workflow_dispatch API, with a
// fine-grained token limited to this repository and "Actions: read and write" (Worker secret GITHUB_DISPATCH_TOKEN).
// Returns 'requested', 'scheduled' (no token configured: the scheduled run publishes later) or 'failed' (the decision
// is saved either way; the schedule remains the fallback). Never logs or returns the token.
async function requestIdeasPublish(env, workflow = 'plotnua-ideas-publish.yml') {
  if (!env.GITHUB_DISPATCH_TOKEN) return 'scheduled';
  const api = (env.GITHUB_API || 'https://api.github.com').replace(/\/$/, '');
  try {
    const r = await fetch(api + '/repos/' + (env.GITHUB_REPO || 'colin-macaulay-dcu/plotnua') + '/actions/workflows/' + workflow + '/dispatches', {
      method: 'POST', signal: AbortSignal.timeout(8000),
      headers: { Authorization: 'Bearer ' + env.GITHUB_DISPATCH_TOKEN, Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'PlotArt-Studio/1.0 (+https://plotnua.ie)', 'Content-Type': 'application/json' },
      body: JSON.stringify({ ref: 'main' }),
    });
    return r.status === 204 ? 'requested' : 'failed';
  } catch { return 'failed'; }
}
// PlotArt galleries · publish on approval (founder decision 6 Nov 2026): a FOUNDER action that makes gallery content ready
// (Publish in the Review desk, Unpublish, ending an artist's participation, a change to the gallery order) starts the
// content publishing workflow at once, through the same founder-only link as the Idea Board and the noticeboard. The
// workflow itself is unchanged: one run at a time, every item rebuilt on the latest main, content-only boundary, launch
// guard, provenance and image rights, the release gate, fast-forward only, live check and automatic rollback, and a
// failure marked on the item in the Review desk. The scheduled run stays as the fallback. An artist's own instant
// updates (sold, availability, withdrawal, order) start it only when INSTANT_PUBLISH_DISPATCH is "true" (off by default).
const requestGalleryPublish = env => requestIdeasPublish(env, 'plotart-content-publish.yml');
async function pipelineIdeas(env) {
  // Public fields only (founder decision 1 Nov 2026): wording, area, county where the visitor allowed it, month and
  // year, and a "Now a PlotNua Discovery" link. No reference, id, exact time, status or moderation detail.
  await ideasReady(env); await purgeIdeas(env);
  const rows = await all(env, "SELECT text, public_text, area, county, show_county, became_discovery, published_at FROM ideas WHERE status='approved' ORDER BY published_at DESC, id DESC");
  return { ideas: rows.map(r => ({ text: r.public_text || r.text, area: r.area || null, county: r.show_county ? r.county : null,
    month: String(r.published_at).slice(0, 7), became_discovery: r.became_discovery || null })) };
}

/* ---------------------------------------------------------------- The Borrowed Garden noticeboard (MVP, 4 Nov 2026)
   The founder's moderation of noticeboard listings, on the Idea Board pattern. The public intake Worker (garden.js)
   only ever inserts 'received' listings; nothing is public until the founder approves it here, and only the content
   pipeline publishes approved listings. Approve / Reject / Remove / Expire, plus tidying the wording and the area.
   An approved listing expires LISTING_DAYS after approval. The contact e-mail is shown to the founder only (to answer
   a removal request); it is never in the pipeline. Monetisation fields are never set or read for ordering here.
   Until migration 0004 is applied these routes say so (503) instead of failing. */
const G_PURGE_DAYS = 30, G_PENDING_DAYS = 90;
async function gardenReady(env) {
  const t = await env.DB.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='garden_listings'").first();
  if (!t) throw new Bad('The Borrowed Garden noticeboard isn’t installed yet (migration 0004 has not been applied).', 503);
}
async function sweepGarden(env) {
  const at = now(), ago = d => new Date(Date.now() - d * 86400_000).toISOString();
  // Expiry: an approved listing past its expiry date leaves the board (the founder can still see it under "Closed").
  const x = await env.DB.prepare("UPDATE garden_listings SET status='expired', removed_at=? WHERE status='approved' AND expires_at < ?").bind(at, at).run();
  // Retention. Each DELETE names the statuses it may touch; an approved listing is never deleted here.
  await env.DB.prepare("DELETE FROM garden_listings WHERE status IN ('rejected','removed','expired') AND COALESCE(removed_at, decided_at) < ?").bind(ago(G_PURGE_DAYS)).run();
  await env.DB.prepare("DELETE FROM garden_listings WHERE status = 'received' AND created_at < ?").bind(ago(G_PENDING_DAYS)).run();
  await env.DB.prepare('DELETE FROM garden_intake_days WHERE day < ?').bind(ago(G_PURGE_DAYS).slice(0, 10)).run();
  return (x.meta && x.meta.changes) || 0;
}
async function gardenAdmin(env) {
  await gardenReady(env); await sweepGarden(env);
  const cols = 'id, ref, kind, county, area, space_type, availability, description, public_text, photo_key, contact_email, status, edited, created_at, decided_at, published_at, expires_at, removed_at';
  return {
    waiting: await all(env, `SELECT ${cols} FROM garden_listings WHERE status='received' ORDER BY created_at`),
    approved: await all(env, `SELECT ${cols} FROM garden_listings WHERE status='approved' ORDER BY published_at DESC, id DESC`),
    closed: await all(env, `SELECT ${cols} FROM garden_listings WHERE status IN ('rejected','removed','expired') ORDER BY COALESCE(removed_at, decided_at) DESC LIMIT 50`),
    kinds: G_KINDS, space_types: G_SPACE, availability: G_AVAIL, listing_days: G_DAYS, purge_days: G_PURGE_DAYS, pending_days: G_PENDING_DAYS,
  };
}
async function decideListing(env, actor, id, b) {
  await gardenReady(env);
  const l = await one(env, 'SELECT * FROM garden_listings WHERE id = ?', id);
  if (!l) throw new Bad('That listing no longer exists.', 404);
  const action = String(b && b.action || '');
  const at = now();
  if (action === 'reject') {
    if (l.status !== 'received') throw new Bad('Only a listing waiting for review can be rejected.', 409);
    await env.DB.prepare("UPDATE garden_listings SET status='rejected', decided_at=?, decided_by=? WHERE id=?").bind(at, actor, id).run();
  } else if (action === 'remove' || action === 'expire') {
    if (l.status !== 'approved') throw new Bad('Only a listing on the noticeboard can be ' + (action === 'remove' ? 'removed.' : 'expired.'), 409);
    await env.DB.prepare(`UPDATE garden_listings SET status=?, removed_at=?, decided_by=? WHERE id=?`).bind(action === 'remove' ? 'removed' : 'expired', at, actor, id).run();
  } else if (action === 'approve' || action === 'save') {
    if (action === 'approve' && l.status !== 'received') throw new Bad('Only a listing waiting for review can be approved.', 409);
    if (action === 'save' && l.status !== 'approved') throw new Bad('Only a listing on the noticeboard can be updated.', 409);
    const text = gClean(b.public_text === undefined || b.public_text === null ? (l.public_text || l.description) : b.public_text);
    const why = gTextProblem(text);
    if (why) throw new Bad(why);
    const area = b.area === undefined ? l.area : gClean(b.area);
    const whyA = gAreaProblem(area);
    if (whyA) throw new Bad(whyA);
    const pub = text === l.description ? null : text;
    const expires = action === 'approve' ? new Date(Date.now() + G_DAYS * 86400_000).toISOString() : l.expires_at;
    await env.DB.prepare("UPDATE garden_listings SET status='approved', public_text=?, area=?, edited=?, decided_at=COALESCE(decided_at, ?), decided_by=?, published_at=COALESCE(published_at, ?), expires_at=? WHERE id=?")
      .bind(pub, area, pub || area !== l.area ? 1 : 0, at, actor, at, expires, id).run();
  } else if (action === 'delete') {
    // Erasure now (e.g. a removal request quoting the reference). A listing on the board must be removed first.
    if (l.status === 'approved') throw new Bad('Remove it from the noticeboard first; it is then deleted on the next publish.', 409);
    await env.DB.prepare("DELETE FROM garden_listings WHERE id = ? AND status <> 'approved'").bind(id).run();
  } else throw new Bad('Unknown action');
  await audit(env, actor, 'founder', 'garden_' + action, null, { ref: l.ref });
  // Publish on a public change, as the Idea Board does: start .github/workflows/plotnua-garden-publish.yml at once
  // (the schedule is the fallback). Rejecting or deleting a waiting listing changes nothing public.
  const publicChange = ['approve', 'save', 'remove', 'expire'].includes(action);
  const publish = publicChange ? await requestIdeasPublish(env, 'plotnua-garden-publish.yml') : 'none';
  return { ...(await gardenAdmin(env)), publish };
}
async function pipelineGarden(env) {
  // Public fields only: the reference, kind, county, general area, type of space, availability, the approved wording,
  // an approved photograph if any, the date posted and the expiry date. Never the e-mail, id, moderation detail,
  // or any monetisation field. Ordered by date posted, newest first: no field changes the order.
  await gardenReady(env); await sweepGarden(env);
  const rows = await all(env, "SELECT ref, kind, county, area, space_type, availability, description, public_text, photo_key, published_at, expires_at FROM garden_listings WHERE status='approved' ORDER BY published_at DESC, id DESC");
  return { listings: rows.map(r => ({ ref: r.ref, kind: r.kind, county: r.county, area: r.area, space_type: r.space_type, availability: r.availability,
    text: r.public_text || r.description, photo: r.photo_key || null, posted: String(r.published_at).slice(0, 10), expires: String(r.expires_at).slice(0, 10) })) };
}

/* ---------------------------------------------------------------- router */
export default {
  /* Daily clean-up (cron trigger): enquiries past their 24-month limit are deleted, and photographs removed more than
     30 days ago are erased from storage (Gallery Publication and Image Licence 6.3). */
  async scheduled(_event, env) {
    let enquiries_logged = 0;
    try { enquiries_logged = await logMissingRelayEnquiries(env); } catch { /* enquiry log not installed */ }
    await env.DB.prepare('DELETE FROM enquiries WHERE delete_after < ?').bind(now()).run();
    const cut = new Date(Date.now() - 30 * 86400_000).toISOString();
    const due = await all(env, "SELECT id, artist_id, r2_key, preview_key FROM images WHERE deleted_at IS NOT NULL AND deleted_at < ? AND r2_key <> 'erased'", cut);
    // A photograph still shown in the artist's newest version (e.g. replaced, with the replacement still waiting for review)
    // is kept until that version is superseded: later updates to the live gallery are built from it (release review, 6 Nov 2026).
    const shown = new Map();
    for (const aid of new Set(due.map(i => i.artist_id))) {
      const lv = await latestVersion(env, aid);
      shown.set(aid, new Set(lv ? [...lv.snap.works.flatMap(w => (w.images || []).map(x => x.id)), ...(lv.snap.artist && lv.snap.artist.portrait ? [lv.snap.artist.portrait.id] : [])] : []));
    }
    const gone = due.filter(i => !shown.get(i.artist_id).has(i.id));
    for (const i of gone) {
      await env.IMAGES.delete(i.r2_key); if (i.preview_key) await env.IMAGES.delete(i.preview_key);
      await env.DB.prepare("UPDATE images SET r2_key='erased', preview_key=NULL WHERE id=?").bind(i.id).run();
    }
    let ideas_deleted = 0;
    try { await ideasReady(env); ideas_deleted = await purgeIdeas(env); } catch { /* Idea Board not installed */ }
    let garden_expired = 0;
    try { await gardenReady(env); garden_expired = await sweepGarden(env); } catch { /* noticeboard not installed */ }
    let hire = null;
    try { hire = await H.sweep(env); } catch (e) { hire = { error: String(e.message || e).slice(0, 120) }; }   // Art for Hire retention (0007)
    let participation_deletion = null;
    try { participation_deletion = await runDeletionSchedule(env); } catch (e) { participation_deletion = { error: String(e.message || e).slice(0, 120) }; }
    await audit(env, 'scheduler', 'system', 'cleanup', null, { images_erased: gone.length, images_kept_while_shown: due.length - gone.length, ideas_deleted, garden_expired, participation_deletion, enquiries_logged, hire });
  },
  async fetch(req, env) {
    try { return await route(req, env); }
    catch (e) {
      if (e instanceof Bad) return json({ ok: false, error: e.message }, e.status);
      console.error(e);
      return json({ ok: false, error: 'Something went wrong. Your work is saved up to your last successful change.' }, 500);
    }
  },
};

/* Founding 25 applications that came with artwork images (the review copy the application route writes). */
const airtableLink = (env, rec) => env.F25_AIRTABLE_TABLE_URL && /^rec[A-Za-z0-9]{14}$/.test(rec || '') ? `${env.F25_AIRTABLE_TABLE_URL.replace(/\/$/, '')}/${rec}` : null;
async function application(env, ref) {
  if (!env.APPLICATIONS) return null;
  const o = await env.APPLICATIONS.get(`applications/${ref}/application.json`);
  if (!o) return null;
  const a = JSON.parse(await o.text());
  const pick = k => (typeof a[k] === 'string' ? a[k] : null);
  const link = u => (typeof u === 'string' && /^https:\/\//.test(u) ? u : null);
  return { ref, artist_name: pick('artist_name'), medium: pick('medium'), region: pick('region'), bio: pick('bio'), additional_info: pick('additional_info'),
    portfolio: link(a.portfolio), website: link(a.website), social_link: pick('social_link'), submitted_at: pick('submitted_at'),
    images: (a.images || []).filter(i => /^[1-5]\.(jpg|png|webp)$/.test(i.file)).map(i => ({ src: `/admin/applications/${ref}/img/${i.file}`, w: i.w, h: i.h })),
    airtable: airtableLink(env, a.airtable_record) };
}
async function applications(env) {
  if (!env.APPLICATIONS) return { connected: false, items: [] };
  const items = [];
  let cursor;
  do {
    const l = await env.APPLICATIONS.list({ prefix: 'applications/', delimiter: '/', cursor });
    for (const pre of l.delimitedPrefixes || []) {
      const ref = pre.split('/')[1];
      if (!/^F25-\d{6}-[0-9A-F]{6}$/.test(ref)) continue;
      const a = await application(env, ref);
      if (a) items.push({ ref, artist_name: a.artist_name, medium: a.medium, region: a.region, submitted_at: a.submitted_at, images: a.images.slice(0, 5) });
    }
    cursor = l.truncated ? l.cursor : null;
  } while (cursor);
  items.sort((x, y) => String(y.submitted_at).localeCompare(String(x.submitted_at)));
  return { connected: true, items };
}

/* ---- Profile pre-fill from a Founding 25 application (founder decision 11 Nov 2026).
   When the founder creates an account with an application reference, the artist's working profile is started from the
   private review copy of that application, so a selected artist doesn't type the same things twice.
   · Only five fields: biography, medium, county, website, Instagram. Never the statement, practice, portrait,
     "additional information", the public-county switch (county_public stays 0) or any application image.
   · Each value goes through the same validator the artist's own Profile form uses (PROFILE); a value it refuses is
     skipped, never altered to fit.
   · Empty fields only: the UPDATE re-checks emptiness in SQL, so nothing the artist (or anyone) has written is replaced.
   · It is the working copy only: nothing is public until the artist submits and the founder approves, as always.
   · Safeguards against the wrong person's details: the application's name must match the name the founder entered,
     and an application already linked to another account is never used again.
   · The audit log records which fields were filled and why any were skipped (field names only, never values). */
const PREFILL_FIELDS = ['bio', 'medium', 'county', 'website', 'instagram'];
const PREFILL_LABEL = { bio: 'biography', medium: 'medium', county: 'county', website: 'website', instagram: 'Instagram' };
const sameName = (a, b) => {
  const n = s => String(s ?? '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  return !!n(a) && n(a) === n(b);
};
function prefillValues(app) {
  const out = {}, skipped = {};
  const take = (field, raw) => {
    if (raw === undefined || raw === null || raw === '') { skipped[field] = 'not in application'; return; }
    try { const v = PROFILE[field](raw); if (v === null || v === undefined || v === '') skipped[field] = 'empty after checks'; else out[field] = v; }
    catch (e) { skipped[field] = e instanceof Bad ? 'did not pass Studio checks' : 'could not be read'; }
  };
  take('bio', typeof app.bio === 'string' ? app.bio : null);
  // the application form's "digital" is the Studio's "digital_new_media"; every other medium has the same name
  take('medium', typeof app.medium === 'string' ? (app.medium === 'digital' ? 'digital_new_media' : app.medium) : null);
  // the application stores counties in lower case ("wicklow"); the Studio list is capitalised ("Wicklow")
  take('county', typeof app.region === 'string' ? (L.COUNTIES.find(c => c.toLowerCase() === app.region.toLowerCase()) || app.region) : null);
  take('website', typeof app.website === 'string' ? app.website : null);
  // social_link is either an @handle or a link; only an Instagram handle or instagram.com profile link is used
  let ig = null;
  if (typeof app.social_link === 'string') {
    const s = app.social_link.trim(), m = s.match(/^https:\/\/(?:www\.)?instagram\.com\/([A-Za-z0-9._]{1,30})\/?(?:\?.*)?$/i);
    if (/^@?[A-Za-z0-9._]{1,30}$/.test(s)) ig = s; else if (m) ig = m[1]; else { skipped.instagram = 'not an Instagram handle'; }
  }
  if (!skipped.instagram) take('instagram', ig);
  return { out, skipped };
}
async function prefillFromApplication(env, artistId, ref, displayName) {
  const done = (r) => ({ fields: [], skipped: {}, ...r });
  if (!ref) return done({ reason: 'no application reference' });
  if (!env.APPLICATIONS) return done({ reason: 'application storage not connected' });
  let app = null;
  try { const o = await env.APPLICATIONS.get(`applications/${ref}/application.json`); if (o) app = JSON.parse(await o.text()); } catch { app = null; }
  if (!app || typeof app !== 'object') return done({ reason: 'no Studio copy of this application' });
  if (app.application_ref && app.application_ref !== ref) return done({ reason: 'application copy does not match the reference' });
  if (!sameName(app.artist_name, displayName)) return done({ reason: 'name on the application does not match the name entered' });
  if (await one(env, 'SELECT id FROM artists WHERE application_ref=? AND id<>?', ref, artistId)) return done({ reason: 'application already linked to another account' });
  const { out, skipped } = prefillValues(app);
  const cur = await one(env, `SELECT ${PREFILL_FIELDS.join(', ')} FROM artists WHERE id=?`, artistId);
  if (!cur) return done({ reason: 'account not found' });
  const empty = v => v === null || v === undefined || String(v).trim() === '';
  for (const k of Object.keys(out)) if (!empty(cur[k])) { skipped[k] = 'already filled in'; delete out[k]; }
  const keys = Object.keys(out);
  if (keys.length) {
    await env.DB.prepare(`UPDATE artists SET ${keys.map(k => `${k}=CASE WHEN ${k} IS NULL OR trim(${k})='' THEN ? ELSE ${k} END`).join(', ')}, updated_at=? WHERE id=?`)
      .bind(...keys.map(k => out[k]), now(), artistId).run();
  }
  return done({ fields: keys, skipped });
}

/* Founder system check: the Worker's own D1 and R2 bindings, written, read back and removed. No personal data. */
async function selftest(env, me) {
  const out = {}, id = 'selftest-' + crypto.randomUUID();
  try {
    const n = await env.DB.prepare('SELECT COUNT(*) AS n FROM artists').first();
    await audit(env, me.email, 'founder', 'system_check', null, { id });
    const back = await env.DB.prepare("SELECT id FROM audit WHERE action='system_check' AND detail LIKE ? LIMIT 1").bind('%' + id + '%').first();
    out.database = back ? `working (${n.n} artist account${n.n === 1 ? '' : 's'})` : 'FAILED: write not read back';
  } catch (e) { out.database = 'FAILED: ' + String(e.message || e).slice(0, 120); }
  try {
    const key = 'system-check/' + id + '.txt', body = 'PlotArt Studio system check ' + id;
    await env.IMAGES.put(key, body);
    const got = await env.IMAGES.get(key), text = got ? await got.text() : null;
    await env.IMAGES.delete(key);
    const gone = !(await env.IMAGES.head(key));
    out.image_storage = text === body && gone ? 'working (written, read back and deleted)' : 'FAILED: ' + (text !== body ? 'read-back mismatch' : 'not deleted');
  } catch (e) { out.image_storage = 'FAILED: ' + String(e.message || e).slice(0, 120); }
  out.publishing = env.INSTANT_AUTOPUBLISH === 'true' ? 'automatic updates ON' : 'automatic updates off';
  out.email = env.MAILER === 'resend' ? 'Resend' : 'not sending';
  out.passed = !/FAILED/.test(out.database + out.image_storage);
  return out;
}

async function route(req, env) {
  const url = new URL(req.url), p = url.pathname, m = req.method;
  // static assets (public, no data)
  const asset = { '/assets/studio.css': [A.STUDIO_CSS, 'text/css'], '/assets/plotart.css': [A.PLOTART_CSS, 'text/css'],
    '/assets/studio.js': [A.STUDIO_JS, 'text/javascript'], '/assets/admin.js': [A.ADMIN_JS, 'text/javascript'],
    '/assets/plotnua-mark.svg': [A.MARK_SVG, 'image/svg+xml'] }[p];
  if (asset && m === 'GET') return res(asset[0], asset[1] + '; charset=utf-8', 200, { 'Cache-Control': 'public, max-age=300' });
  if (LOGO[p] && m === 'GET') return res(LOGO[p][0], LOGO[p][1], 200, { 'Cache-Control': 'public, max-age=86400' });

  // the publishing pipeline: bearer token, never a browser
  if (p.startsWith('/api/pipeline/')) {
    if (!env.PIPELINE_TOKEN || req.headers.get('Authorization') !== `Bearer ${env.PIPELINE_TOKEN}`) return json({ ok: false }, 401);
    if (p === '/api/pipeline/queue' && m === 'GET') return json({ ok: true, items: await all(env, "SELECT * FROM publish_queue WHERE status='ready' ORDER BY created_at") });
    if (p === '/api/pipeline/gallery-order' && m === 'GET') return json({ ok: true, ...(await pipelineOrder(env)) });
    if (p === '/api/pipeline/ideas' && m === 'GET') return json({ ok: true, ...(await pipelineIdeas(env)) });   // Idea Board: approved, public fields only
    if (p === '/api/pipeline/garden' && m === 'GET') return json({ ok: true, ...(await pipelineGarden(env)) });   // Borrowed Garden noticeboard: approved, public fields only
    if (p === '/api/pipeline/hire-catalogue' && m === 'GET') {   // Art for Hire: separate from the gallery export; listed works only
      if (!(await H.installed(env))) return json({ ok: true, generated_at: now(), items: [] });
      return json({ ok: true, ...(await H.catalogue(env)) });
    }
    if (p === '/api/pipeline/gallery-order/result' && m === 'POST') {
      const b = await req.json();
      await audit(env, 'pipeline', 'pipeline', b.status === 'published' ? 'gallery_order_published' : 'gallery_order_failed', null, { detail: String(b.detail || '').slice(0, 2000) });
      return json({ ok: true });
    }
    let mm;
    if ((mm = p.match(/^\/api\/pipeline\/export\/(q[0-9a-z]+)$/)) && m === 'POST') {
      const q = await one(env, "SELECT * FROM publish_queue WHERE id = ? AND status IN ('ready','exporting')", mm[1]);
      if (!q) throw new Bad('Not ready', 409);
      await env.DB.prepare("UPDATE publish_queue SET status='exporting', updated_at=? WHERE id=?").bind(now(), q.id).run();
      if (q.kind !== 'remove') await placeOnFirstPublication(env, q.artist_id);
      return json({ ok: true, ...(await exportFor(env, q)) });
    }
    if ((mm = p.match(/^\/api\/pipeline\/image\/(q[0-9a-z]+)\/(i[0-9a-z]+)$/)) && m === 'GET') {
      const q = await one(env, "SELECT * FROM publish_queue WHERE id = ? AND status = 'exporting'", mm[1]);
      if (!q) throw new Bad('Not exporting', 409);
      const ex = await exportFor(env, q);
      if (!ex.images.includes(mm[2])) throw new Bad('Not part of this export', 403);
      const img = await one(env, 'SELECT * FROM images WHERE id = ? AND artist_id = ?', mm[2], q.artist_id);
      const o = await env.IMAGES.get(img.r2_key);
      return new Response(o.body, { headers: { 'Content-Type': `image/${img.format}`, 'X-Sha256': img.sha256 } });
    }
    if ((mm = p.match(/^\/api\/pipeline\/result\/(q[0-9a-z]+)$/)) && m === 'POST') {
      const b = await req.json();
      const q = await one(env, "SELECT * FROM publish_queue WHERE id = ? AND status = 'exporting'", mm[1]);
      if (!q) throw new Bad('Not exporting', 409);
      const ok = b.status === 'published';
      await env.DB.prepare('UPDATE publish_queue SET status=?, detail=?, updated_at=? WHERE id=?').bind(ok ? 'published' : 'failed', String(b.detail || '').slice(0, 2000), now(), q.id).run();
      if (ok) {
        await env.DB.prepare("UPDATE publish_queue SET status='superseded', updated_at=? WHERE artist_id=? AND status IN ('published','failed') AND version<?").bind(now(), q.artist_id, q.version).run();
        await env.DB.prepare('UPDATE artists SET first_published_at=COALESCE(first_published_at, ?), updated_at=? WHERE id=?').bind(now(), now(), q.artist_id).run();
      }
      await audit(env, 'pipeline', 'pipeline', ok ? 'published' : 'publish_failed', q.artist_id, { queue: q.id, version: q.version, detail: b.detail });
      return json({ ok: true });
    }
    return json({ ok: false }, 404);
  }

  const me = await who(req, env);
  let mm0;
  if (me.role === 'none') {
    // PLOTART-STUDIO-ACCESS-002: a verified email with no invited or active artist account sees who they are signed in
    // as (their OWN verified address only) and a way to sign out and use another address. The wording is identical for
    // unknown, suspended and ended accounts, so the page never says whether any account exists for any address.
    if (p.startsWith('/api/')) return json({ ok: false, error: me.email ? `You're signed in as ${me.email}. We couldn't find an active PlotArt Studio account associated with this email address. If you've already been invited, please sign in using the email address shown in your invitation.` : 'Please sign in.', signout: me.email ? '/cdn-cgi/access/logout' : undefined }, me.email ? 403 : 401);
    if (me.email) return html(A.REFUSED_HTML.replace('{email}', () => escHtml(me.email)), 403);
    return html(A.SIGNED_OUT_HTML.replace('{msg}', 'Please sign in through PlotArt Studio.'), 401);
  }
  if (m !== 'GET') {
    // same-origin only: a custom header cannot be sent cross-site without a CORS preflight, which this Worker never grants
    if (req.headers.get('X-Studio') !== '1') return json({ ok: false, error: 'Refused' }, 403);
    const o = req.headers.get('Origin');
    if (o && o !== url.origin) return json({ ok: false, error: 'Refused' }, 403);
  }

  /* ---- agreement texts: the exact fingerprinted files, to any signed-in artist or the founder (read and download) */
  if ((mm0 = p.match(/^\/agreements\/(PA-(?:FAA|GPIL|GAA)-\d{4}-\d{2}(?:-\d{2})?)\.(html|pdf)$/)) && m === 'GET') {
    const d = AG.doc(mm0[1]);
    if (!d) return html('Not found', 404);
    // the Gallery Artist Agreement is served to artists only once its approved text is installed (0013); the founder can
    // read the bundled text before that, to review exactly what will be installed
    if (mm0[1].startsWith('PA-GAA-') && me.role !== 'founder') {
      const inst = ((await agreementDocs(env)) || []).find(x => x.doc_id === mm0[1]);
      if (!inst || inst.html_sha256 !== d.html_sha256 || inst.pdf_sha256 !== d.pdf_sha256) return html('Not found', 404);
    }
    if (mm0[2] === 'html') return res(d.html, 'text/html; charset=utf-8', 200, { 'X-Document-SHA256': d.html_sha256 });
    return new Response(Uint8Array.from(atob(d.pdf_b64), c => c.charCodeAt(0)), { headers: { ...SEC, 'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="PlotArt-${mm0[1]}.pdf"`, 'X-Document-SHA256': d.pdf_sha256 } });
  }

  /* ---- founder */
  if (p === '/admin' || p.startsWith('/admin/') || p.startsWith('/api/admin/')) {
    if (me.role !== 'founder') return p.startsWith('/api/') ? json({ ok: false, error: 'Not available' }, 403) : html('Not available', 403);
    if (p === '/admin' || p === '/admin/') return html(A.ADMIN_HTML);
    let mm;
    if (p === '/admin/gallery') return html(A.ADMIN_HTML);
    if (p === '/admin/ideas') return html(A.ADMIN_HTML);
    if (p === '/api/admin/ideas' && m === 'GET') return json({ ok: true, ...(await ideasAdmin(env)) });
    if ((mm = p.match(/^\/api\/admin\/ideas\/(i[0-9a-z]+)$/)) && m === 'POST') return json({ ok: true, ...(await decideIdea(env, me.email, mm[1], await req.json())) });
    if (p === '/admin/garden') return html(A.ADMIN_HTML);
    if (p === '/admin/agreements') return html(A.ADMIN_HTML);
    if (p === '/admin/leaving') return html(A.ADMIN_HTML);
    if (p === '/admin/hire') return html(A.ADMIN_HTML);
    if (p === '/admin/opportunities') return html(A.ADMIN_HTML);
    if (p === '/api/admin/opportunities' && m === 'GET') return json({ ok: true, ...(await O.adminView(env)) });   // read-only: the founder never edits an artist's answers
    if (p.startsWith('/api/admin/hire') && !(await H.installed(env))) return json({ ok: false, error: 'Art for Hire is not installed' }, 409);
    if (p === '/api/admin/hire' && m === 'GET') return json({ ok: true, ...(await H.adminView(env)) });
    if ((mm = p.match(/^\/api\/admin\/hire\/artwork\/(w[0-9a-z]+)\/decision$/)) && m === 'POST') return json({ ok: true, ...(await H.decide(env, me.email, mm[1], await req.json())) });
    if (p === '/api/admin/hire/permissions' && m === 'POST') return json({ ok: true, ...(await H.recordPermission(env, me.email, await req.json())) });
    // Hire reports (migration 0008, PA-AFH r5 6.5–6.6): the founder's manual invoice and payment records, and a CSV for them
    if (p === '/api/admin/hire/reports' && m === 'GET') return json({ ok: true, ...(await H.adminReports(env)) });
    if (p === '/api/admin/hire/reports.csv' && m === 'GET') return res(await H.reportsCsv(env, me.email), 'text/csv; charset=utf-8', 200,
      { 'Content-Disposition': `attachment; filename="plotart-hire-reports-${now().slice(0, 10)}.csv"`, 'Cache-Control': 'no-store' });
    if ((mm = p.match(/^\/api\/admin\/hire\/reports\/(hr[0-9a-z]+)\/record$/)) && m === 'POST') return json({ ok: true, ...(await H.setRecord(env, me.email, mm[1], await req.json())) });
    if (p === '/api/admin/garden' && m === 'GET') return json({ ok: true, ...(await gardenAdmin(env)) });
    if ((mm = p.match(/^\/api\/admin\/garden\/(g[0-9a-z]+)$/)) && m === 'POST') return json({ ok: true, ...(await decideListing(env, me.email, mm[1], await req.json())) });
    if (p === '/api/admin/gallery-order' && m === 'GET') return json({ ok: true, ...(await galleryOrder(env)) });
    if (p === '/api/admin/gallery-order' && m === 'PUT') return json({ ok: true, ...(await saveGalleryOrder(env, me.email, await req.json())) });
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/founding-number$/)) && m === 'PUT') {
      const b = await req.json(), a = await one(env, 'SELECT id, founding, founding_number FROM artists WHERE id = ?', mm[1]);
      if (!a) throw new Bad('Not found', 404);
      const n = b.founding_number == null || b.founding_number === '' ? null : Number(b.founding_number);
      if (n !== null && (!Number.isInteger(n) || n < 1 || n > 25)) throw new Bad('A Founding 25 number is from 1 to 25');
      if (n !== null && !a.founding) throw new Bad('Only a Founding Artist has a Founding 25 number');
      if (n !== null && await one(env, 'SELECT id FROM artists WHERE founding_number = ? AND id <> ?', n, a.id)) throw new Bad(`No. ${n} is already held by another artist`, 409);
      await env.DB.prepare('UPDATE artists SET founding_number=?, updated_at=? WHERE id=?').bind(n, now(), a.id).run();
      await audit(env, me.email, 'founder', 'founding_number', a.id, { from: a.founding_number, to: n });
      return json({ ok: true, founding_number: n });
    }
    /* ---- Founding 25 applications with artwork images (private bucket plotart-applications; founder only) */
    if (p === '/admin/applications' || /^\/admin\/applications\/F25-\d{6}-[0-9A-F]{6}$/.test(p)) return html(A.ADMIN_HTML);
    if ((mm = p.match(/^\/admin\/applications\/(F25-\d{6}-[0-9A-F]{6})\/img\/([1-5]\.(?:jpg|png|webp))$/)) && m === 'GET') {
      if (!env.APPLICATIONS) return html('Not found', 404);
      const o = await env.APPLICATIONS.get(`applications/${mm[1]}/${mm[2]}`);
      if (!o) return html('Not found', 404);
      return new Response(o.body, { headers: { 'Content-Type': (o.httpMetadata && o.httpMetadata.contentType) || 'image/jpeg', 'Cache-Control': 'private, no-store',
        'Content-Disposition': 'inline', 'X-Content-Type-Options': 'nosniff', 'Cross-Origin-Resource-Policy': 'same-origin' } });
    }
    if (p === '/api/admin/applications' && m === 'GET') return json({ ok: true, ...(await applications(env)) });
    if ((mm = p.match(/^\/api\/admin\/applications\/(F25-\d{6}-[0-9A-F]{6})$/)) && m === 'GET') {
      const a = await application(env, mm[1]);
      return a ? json({ ok: true, application: a }) : json({ ok: false, error: 'Not found' }, 404);
    }
    if ((mm = p.match(/^\/api\/admin\/applications\/(F25-\d{6}-[0-9A-F]{6})\/erase$/)) && m === 'POST') {
      if (!env.APPLICATIONS) throw new Bad('Image storage is not connected', 500);
      const l = await env.APPLICATIONS.list({ prefix: `applications/${mm[1]}/` });
      await Promise.all(l.objects.map(o => env.APPLICATIONS.delete(o.key)));
      await audit(env, me.email, 'founder', 'application_images_erased', null, { ref: mm[1], objects: l.objects.length });
      return json({ ok: true, erased: l.objects.length });
    }
    if ((mm = p.match(/^\/admin\/preview\/(s[0-9a-z]+|v-([0-9a-z]+)-(\d+))\/(.*)$/))) {
      let snap, artistId;
      if (mm[1].startsWith('s')) { const s = await one(env, 'SELECT * FROM submissions WHERE id=?', mm[1]); if (!s) return html('Not found', 404); snap = JSON.parse(s.snapshot); artistId = s.artist_id; }
      else { const v = await one(env, 'SELECT * FROM versions WHERE artist_id=? AND version=?', mm[2], Number(mm[3])); if (!v) return html('Not found', 404); snap = JSON.parse(v.snapshot); artistId = mm[2]; }
      const rest = mm[4];
      if (rest.startsWith('img/')) { const img = await one(env, 'SELECT * FROM images WHERE id=? AND artist_id=?', rest.slice(4), artistId); return img ? previewImage(env, img) : html('Not found', 404); }
      const images = await all(env, 'SELECT * FROM images WHERE artist_id=?', artistId);
      return previewRoute(rest, previewPkg(snap, images), 'Founder review preview · <a href="/admin">Back to the review desk</a>');
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/checklist$/)) && m === 'GET') {
      // PLOTART-STUDIO-SUBMISSION-002: the founder's read-only view of one artist's submission checklist. Same rules
      // and wording as the artist sees; nothing here can change, waive or bypass an item.
      const a = await one(env, 'SELECT * FROM artists WHERE id=?', mm[1]);
      if (!a) return json({ ok: false, error: 'Artist not found' }, 404);
      const st = await status(env, a);
      return json({ ok: true, artist: { id: a.id, display_name: a.display_name }, state: st.state, works: st.counts.works, count: st.checklist.length, items: st.checklist });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/agreement$/)) && m === 'GET') {
      const a = await one(env, 'SELECT * FROM artists WHERE id=?', mm[1]);
      if (!a) return json({ ok: false, error: 'Artist not found' }, 404);
      const ag = await agreementState(env, a);
      const log = (await agreementDocs(env)) ? await all(env, 'SELECT reference, route, introduced_at, founding, founding_year_end, late_entry, corrects, logged_at FROM enquiry_log WHERE artist_id=? ORDER BY introduced_at DESC', a.id) : [];
      return json({ ok: true, artist: { id: a.id, display_name: a.display_name, founding: !!a.founding, founding_number: a.founding_number, first_published_at: a.first_published_at, account_status: a.account_status },
        agreement: { ...agreementSummary(ag), history: effectiveRows(ag.history, await corrections(env, a.id)) }, documents: (await agreementDocs(env)) || [], enquiries: log,
        participation: await participation(env, a), terms: await termsFor(env, a.id), terms_installed: await termsInstalled(env) });
    }
    /* Gallery Artist terms (Phase 2, 13 Nov 2026; agreement clause 13). Founder only. The rate is 15% unless a written
       individual variation says otherwise (never higher); the date of that written variation is recorded; the note is
       private to the founder and never shown to the artist, published or exported. Every change is audited. */
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/terms$/)) && m === 'PUT') {
      const t = await termsFor(env, mm[1]);
      if (!t) throw new Bad('Only an artist invited as a Gallery Artist has Gallery Artist terms', 404);
      const b = await req.json();
      const bp = Number(b.commission_bp);
      if (!Number.isInteger(bp) || bp < 0 || bp > 1500) throw new Bad('The commission rate is a whole number of basis points from 0 to 1500 (15%)');
      const day = b.variation_agreed_on === null || b.variation_agreed_on === '' || b.variation_agreed_on === undefined ? null : String(b.variation_agreed_on);
      if (day !== null && (!/^\d{4}-\d{2}-\d{2}$/.test(day) || AG.addDays(day, 0) !== day || day > AG.dublinToday())) throw new Bad('Enter the date the variation was agreed in writing (not in the future)');
      if (bp !== 1500 && !day) throw new Bad('A rate other than 15% needs the date of the written variation (agreement clause 13)');
      const note = b.variation_note === null || b.variation_note === undefined || String(b.variation_note).trim() === '' ? null : String(b.variation_note).trim();
      if (note && note.length > 1000) throw new Bad('Keep the private note to 1,000 characters');
      await env.DB.prepare('UPDATE artist_terms SET commission_bp=?, variation_agreed_on=?, variation_note=?, set_by=?, updated_at=? WHERE artist_id=?')
        .bind(bp, day, note, me.email, now(), mm[1]).run();
      await audit(env, me.email, 'founder', 'terms_changed', mm[1], { from_bp: t.commission_bp, to_bp: bp, variation_agreed_on: day, note_changed: (t.variation_note || null) !== note });
      return json({ ok: true, terms: await termsFor(env, mm[1]) });
    }
    if (p === '/api/admin/enquiry-log' && m === 'GET') return json({ ok: true, ...(await enquiryLog(env)) });
    if (p === '/api/admin/participation' && m === 'GET') return json({ ok: true, ...(await participationAdmin(env)) });
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/end$/)) && m === 'POST') return json({ ok: true, ...(await endParticipation(env, me.email, mm[1], await req.json())) });
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/erase-originals$/)) && m === 'POST') {
      const b = await req.json();
      if (b.confirm !== true) throw new Bad('Confirm the deletion before continuing');
      const why = String(b.reason || '').trim();
      if (why.length < 10 || why.length > 280) throw new Bad('Give the reason (10–280 characters), e.g. the artist asked for earlier deletion');
      return json({ ok: true, ...(await eraseOriginals(env, mm[1], me.email, 'early, on request: ' + why)) });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/acceptance-corrections$/)) && m === 'POST') return json({ ok: true, ...(await correctAcceptance(env, me.email, mm[1], await req.json())) });
    if (p === '/api/admin/enquiry-log' && m === 'POST') return json({ ok: true, ...(await logEnquiry(env, me.email, await req.json())) });
    if (p === '/api/admin/overview' && m === 'GET') return json({ ok: true, ...(await overview(env)) });
    if (p === '/api/admin/selftest' && m === 'POST') return json({ ok: true, ...(await selftest(env, me)) });
    if (p === '/api/admin/artists' && m === 'POST') {
      const b = await req.json();
      const email = L.artistEmail(b.email);
      if (founderEmails(env).includes(email)) throw new Bad('That is a founder address and can’t be used for an artist account', 409);
      const name = L.text(b.display_name, 2, 80, 'Name');
      const slug = String(b.slug || L.slugify(name));
      if (!L.SLUG.test(slug)) throw new Bad('Gallery address: lower-case words joined by hyphens');
      if (b.application_ref && !/^F25-\d{6}-[0-9A-F]{6}$/.test(b.application_ref)) throw new Bad('Application reference looks like F25-YYMMDD-XXXXXX');
      if (await one(env, 'SELECT id FROM artists WHERE email=? OR slug=?', email, slug)) throw new Bad('An artist with that email or gallery address already exists', 409);
      /* Phase 2 (13 Nov 2026): the programme is an explicit choice, never a default. "founding" keeps PA-FAA exactly as today;
         "gallery_artist" invites on the standard 15% commission terms (PA-GAA, artist_terms row, migration 0012). The older
         explicit founding: true/false is still accepted (false = licence only, as before). Anything else is refused. */
      const programme = b.programme === 'founding' || b.programme === 'gallery_artist' ? b.programme
        : b.programme === undefined && b.founding === true ? 'founding' : b.programme === undefined && b.founding === false ? 'licence_only' : null;
      if (!programme) throw new Bad('Choose the programme for this invitation: Founding Artist or Gallery Artist');
      if (programme === 'gallery_artist' && !(await termsInstalled(env))) throw new Bad('Gallery Artist invitations become available once the Gallery Artist records are installed (migration 0012).', 503);
      const id = rid('a'), at = now();
      await env.DB.batch([
        env.DB.prepare('INSERT INTO artists (id, slug, email, display_name, founding, application_ref, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)')
          .bind(id, slug, email, name, programme === 'founding' ? 1 : 0, b.application_ref || null, at, at),
        ...(programme === 'gallery_artist' ? [env.DB.prepare(`INSERT INTO artist_terms (artist_id, track, commission_bp, variation_agreed_on, variation_note, set_by, created_at, updated_at)
          VALUES (?,'gallery_artist',1500,NULL,NULL,?,?,?)`).bind(id, me.email, at, at)] : [])]);
      await audit(env, me.email, 'founder', 'invite', id, { slug, founding: programme === 'founding', programme });
      // Start the artist's private working profile from their Founding 25 application, where there is one (11 Nov 2026).
      let prefill = { fields: [], skipped: {}, reason: 'no application reference' };
      if (b.application_ref) {
        prefill = await prefillFromApplication(env, id, b.application_ref, name).catch(() => ({ fields: [], skipped: {}, reason: 'pre-fill failed' }));
        await audit(env, me.email, 'founder', prefill.fields.length ? 'profile_prefilled_from_application' : 'profile_prefill_not_applied', id,
          { ref: b.application_ref, fields: prefill.fields, skipped: prefill.skipped, ...(prefill.reason ? { reason: prefill.reason } : {}) });
      }
      // Invitation email (sent only when email is switched on; otherwise the desk says to send it by hand).
      const studio = url.origin, first = name.split(' ')[0];
      const started = prefill.fields.map(k => PREFILL_LABEL[k]);
      const startedList = started.length > 1 ? `${started.slice(0, -1).join(', ')} and ${started[started.length - 1]}` : started[0];
      const prefillPara = started.length
        ? `To save you time, we've started your profile using the details from your Founding 25 application: your ${startedList}. Please review these when you sign in, and change anything you'd like before you submit your gallery. Your profile stays private until then. Your county is not shown publicly unless you choose to show it, and the images you sent with your application aren't used: you'll add your artworks in the Studio.\n\n`
        : '';
      // Gallery Artists only (Phase 2): one paragraph naming their agreement. The Founding Artist email is unchanged.
      const galleryPara = programme === 'gallery_artist'
        ? `You're joining PlotArt as a Gallery Artist. Before your gallery is first published, the Studio will ask you to read and accept the PlotArt Gallery Artist Agreement, which sets out PlotArt's 15% commission on sales introduced through PlotArt. There are no fees to join or to stay.\n\n`
        : '';
      const r = await send(env, { to: email, replyTo: 'hello@plotnua.ie', subject: 'Your PlotArt Studio is ready',
        text: `Hello ${first},\n\nWelcome to PlotArt. Your PlotArt Studio is ready: it's where you build your artist gallery, add your works and keep them up to date.\n\nSign in here: ${studio}\n\nYour PlotArt Studio is registered to:\n\n${email}\n\nPlease use this exact email address when signing in. If you sign in with a different address, even another one of your own, the Studio won't recognise you and you won't be able to reach your gallery. Each time you sign in, you'll be emailed a one-time code; there's no password.\n\n${prefillPara}${galleryPara}Your gallery will only be published once you've submitted it and PlotArt has approved it.\n\nIf you have any questions, just reply to this email.\n\nColin\nPlotArt · part of PlotNua` }).catch(() => ({ sent: false }));
      await audit(env, me.email, 'founder', r.sent ? 'invitation_sent' : 'invitation_not_sent', id, {});
      return json({ ok: true, id, slug, invitation_sent: !!r.sent, prefill: { fields: prefill.fields, skipped: prefill.skipped, reason: prefill.reason || null } });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/prefill$/)) && m === 'POST') {
      // "Start profile from application" (founder decision 11 Nov 2026): the account-creation pre-fill, for an account
      // that already exists. Same rules and safeguards (prefillFromApplication); it links the reference only once every
      // safeguard has passed, never replaces a different reference, never sends an email, and touches nothing but the
      // five empty profile fields and (when it was empty) the application reference.
      const b = await req.json();
      const ref = String(b.application_ref || '').trim();
      if (!/^F25-\d{6}-[0-9A-F]{6}$/.test(ref)) throw new Bad('Application reference looks like F25-YYMMDD-XXXXXX');
      const a = await one(env, 'SELECT id, display_name, account_status, application_ref FROM artists WHERE id=?', mm[1]);
      if (!a) throw new Bad('Artist not found', 404);
      const refuse = async (msg, reason) => {
        await audit(env, me.email, 'founder', 'profile_prefill_not_applied', a.id, { ref, via: 'existing_account', reason });
        throw new Bad(msg, 409);
      };
      if (a.account_status === 'ended') await refuse('This account has ended, so its profile can’t be started from an application.', 'account ended');
      if (a.application_ref && a.application_ref !== ref) await refuse(`This account is already linked to application ${a.application_ref}. A different application can’t be used.`, 'account linked to a different application');
      const r = await prefillFromApplication(env, a.id, ref, a.display_name);
      if (r.reason) await refuse(`Nothing was filled in: ${r.reason}.`, r.reason);
      let linked = false;
      if (!a.application_ref) linked = (await env.DB.prepare('UPDATE artists SET application_ref=?, updated_at=? WHERE id=? AND application_ref IS NULL').bind(ref, now(), a.id).run()).meta.changes === 1;
      await audit(env, me.email, 'founder', r.fields.length ? 'profile_prefilled_from_application' : 'profile_prefill_not_applied', a.id,
        { ref, via: 'existing_account', linked, fields: r.fields, skipped: r.skipped, ...(r.fields.length ? {} : { reason: 'no empty field to fill' }) });
      return json({ ok: true, application_ref: ref, linked, fields: r.fields, skipped: r.skipped, email_sent: false });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/email$/)) && m === 'POST') {
      // PLOTART-STUDIO-ACCESS-002: the founder corrects an artist's sign-in email. Founder-only (this whole block is
      // behind the founder check), same-origin only (X-Studio header), and it changes ONLY the email column: the
      // artist id, status, Founding status, artwork, drafts and audit history all stay as they are. Access follows the
      // email at the next request (auth.js looks the artist up by the verified address), so the old address stops
      // working and the new one starts working at once. No email is sent.
      const b = await req.json();
      const a = await one(env, 'SELECT id, email, account_status FROM artists WHERE id=?', mm[1]);
      if (!a) throw new Bad('Artist not found', 404);
      const email = L.artistEmail(b.email);
      if (b.confirm_email === undefined || String(b.confirm_email).replace(/^[ \t\r\n]+|[ \t\r\n]+$/g, '').toLowerCase() !== email)
        throw new Bad('Type the new email address twice. The two entries must match exactly.');
      if (b.confirm !== true) throw new Bad('Confirm the change before saving');
      if (email === String(a.email).toLowerCase()) throw new Bad('That is already this artist’s email address');
      if (founderEmails(env).includes(email)) throw new Bad('That is a founder address and can’t be used for an artist account', 409);
      if (await one(env, 'SELECT id FROM artists WHERE email=? AND id<>?', email, a.id)) throw new Bad('Another artist account already uses that email address', 409);
      const r = await env.DB.prepare('UPDATE artists SET email=?, updated_at=? WHERE id=? AND email=?').bind(email, now(), a.id, a.email).run()
        .catch(e => { if (/UNIQUE/i.test(String(e && e.message))) throw new Bad('Another artist account already uses that email address', 409); throw e; });
      if (!r.meta || r.meta.changes !== 1) throw new Bad('The account changed while you were editing it. Reload the review desk and try again.', 409);
      await audit(env, me.email, 'founder', 'email_changed', a.id, { from: maskEmail(a.email), to: maskEmail(email), status: a.account_status });
      return json({ ok: true, id: a.id, email, account_status: a.account_status, email_sent: false });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/(suspend|reactivate)$/)) && m === 'POST') {
      await env.DB.prepare('UPDATE artists SET account_status=?, updated_at=? WHERE id=?').bind(mm[2] === 'suspend' ? 'suspended' : 'active', now(), mm[1]).run();
      await audit(env, me.email, 'founder', mm[2], mm[1]);
      return json({ ok: true });
    }
    if ((mm = p.match(/^\/api\/admin\/artists\/(a[0-9a-z]+)\/unpublish$/)) && m === 'POST') {
      const lv = await latestVersion(env, mm[1]);
      if (!lv) throw new Bad('Nothing is published');
      const v = lv.version + 1;
      await env.DB.batch([
        env.DB.prepare('INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?,?,?,?,?)').bind(mm[1], v, JSON.stringify({ ...lv.snap, works: [] }), 'unpublish', now()),
        env.DB.prepare('INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)').bind(rid('q'), mm[1], v, 'remove', 'ready', now(), now()),
      ]);
      const publish = await requestGalleryPublish(env);
      await audit(env, me.email, 'founder', 'unpublish', mm[1], { publish });
      return json({ ok: true, publish });
    }
    if ((mm = p.match(/^\/api\/admin\/submissions\/(s[0-9a-z]+)$/)) && m === 'GET') {
      const s = await one(env, 'SELECT * FROM submissions WHERE id=?', mm[1]);
      if (!s) throw new Bad('Not found', 404);
      const a = await one(env, 'SELECT id, slug, display_name, founding, licence_version, licence_accepted_at, application_ref FROM artists WHERE id=?', s.artist_id);
      const snap = JSON.parse(s.snapshot);
      const ids = snap.works.flatMap(w => w.images.map(i => i.id)).concat(snap.artist.portrait ? [snap.artist.portrait.id] : []);
      const imgs = ids.length ? await all(env, `SELECT id, width, height, bytes, format, checks, sha256 FROM images WHERE id IN (${ids.map(() => '?').join(',')})`, ...ids) : [];
      return json({ ok: true, submission: { ...s, snapshot: undefined, changes: JSON.parse(s.changes) }, artist: a, works: snap.works.map(w => ({ id: w.id, title: w.title, ai_involvement: w.ai_involvement, ai_note: w.ai_note })),
        images: imgs.map(i => ({ ...i, checks: JSON.parse(i.checks) })) });
    }
    if ((mm = p.match(/^\/api\/admin\/submissions\/(s[0-9a-z]+)\/decision$/)) && m === 'POST') return decide(env, me.email, mm[1], await req.json());
    if ((mm = p.match(/^\/api\/admin\/queue\/(q[0-9a-z]+)\/retry$/)) && m === 'POST') return retryPublication(env, me.email, mm[1], req);
    if ((mm = p.match(/^\/api\/admin\/queue\/(q[0-9a-z]+)\/publish$/)) && m === 'POST') {
      const q = await one(env, "SELECT * FROM publish_queue WHERE id=? AND status='awaiting_founder'", mm[1]);
      if (!q) throw new Bad('Nothing to publish', 409);
      const gate = await agreementGate(env, q, req);
      if (gate.response) return gate.response;
      const warned = gate.warned;
      await env.DB.prepare("UPDATE publish_queue SET status='ready', updated_at=? WHERE id=?").bind(now(), q.id).run();
      const publish = await requestGalleryPublish(env);
      await audit(env, me.email, 'founder', 'publish', q.artist_id, { queue: q.id, version: q.version, publish, ...(warned ? { without_current_agreement: true } : {}) });
      return json({ ok: true, publish });
    }
    if (p === '/api/admin/enquiries' && m === 'GET') return json({ ok: true, items: await all(env, `SELECT e.reference, e.created_at, e.status, e.artwork_title, a.display_name,
      CASE WHEN e.reference LIKE 'PA-H-%' THEN 'hire' ELSE 'purchase' END AS kind
      FROM enquiries e JOIN artists a ON a.id = e.artist_id ORDER BY e.created_at DESC LIMIT 200`) });
    if (p === '/api/admin/audit' && m === 'GET') return json({ ok: true, items: await all(env, 'SELECT * FROM audit ORDER BY id DESC LIMIT 200') });
    return json({ ok: false }, 404);
  }

  /* ---- artist (founder may also use the founder desk only) */
  if (me.role !== 'artist') return p.startsWith('/api/') ? json({ ok: false, error: 'This is an artist’s Studio. Use /admin.' }, 403) : Response.redirect(url.origin + '/admin', 302);
  const artist = { ...me.artist, email: me.email };
  if (p === '/' || p === '/index.html') return html(A.STUDIO_HTML);
  if (p.startsWith('/preview/')) {
    const rest = p.slice('/preview/'.length);
    if (rest.startsWith('img/')) return previewImage(env, await ownImage(env, artist, rest.slice(4)));
    const d = await load(env, artist.id);
    return previewRoute(rest, previewPkg(L.snapshot(d.artist, d.works, d.images), d.images), 'Your private preview · only you can see this · <a href="/">Back to Studio</a>');
  }
  let mm;
  if ((mm = p.match(/^\/hire-terms\/(PA-AFH-[0-9]{4}-[0-9]{2})\.(pdf|html)$/)) && m === 'GET') {   // the issued PA-AFH text, only once installed
    const t = (await H.installed(env)) ? await H.currentTerms(env) : null, d = t && t.doc_id === mm[1] ? (A.HIRE_TERMS || {})[mm[1]] : null;
    if (!d) return html('Not available', 404);
    return mm[2] === 'html' ? res(d.html, 'text/html; charset=utf-8', 200, { 'X-Document-SHA256': d.html_sha256 })
      : res(Uint8Array.from(atob(d.pdf_b64), c => c.charCodeAt(0)), 'application/pdf', 200, { 'Content-Disposition': `inline; filename="${mm[1]}.pdf"`, 'X-Document-SHA256': d.pdf_sha256 });
  }
  /* Art for Hire (separate and optional; never touches the gallery, its versions or the Founding Artist agreement) */
  if (p.startsWith('/api/hire')) {
    if (!(await H.installed(env))) return json({ ok: false, error: 'Art for Hire is not available' }, 404);
    if (p === '/api/hire' && m === 'GET') return json({ ok: true, ...(await H.artistView(env, artist)) });
    if (p === '/api/hire/accept' && m === 'POST') return json({ ok: true, ...(await H.accept(env, artist, await req.json())) });
    if (p === '/api/hire/leave' && m === 'POST') return json({ ok: true, ...(await H.leave(env, artist, await req.json())) });
    if ((mm = p.match(/^\/api\/hire\/artwork\/([0-9a-z]+)$/)) && m === 'PUT') return json({ ok: true, ...(await H.saveWork(env, artist, mm[1], await req.json())) });
    if (p === '/api/hire/reports' && m === 'GET') return json({ ok: true, ...(await H.myReports(env, artist)) });       // the artist's own only
    if (p === '/api/hire/reports' && m === 'POST') return json({ ok: true, ...(await H.reportHire(env, artist, await req.json())) });
    return json({ ok: false }, 404);
  }
  /* Opportunities & delivery: the artist's OWN expression of interest. Writes artist_opportunities only. */
  if (p === '/api/opportunities' && m === 'GET') return json({ ok: true, ...(await O.artistView(env, artist)) });
  if (p === '/api/opportunities' && m === 'PUT') return json({ ok: true, ...(await O.save(env, artist, await req.json())) });
  if (p === '/api/me' && m === 'GET') {
    const d = await load(env, artist.id);
    const { email, ...a } = d.artist;
    // the artist's own commercial terms (Phase 2): programme, rate and the date of any written variation; never the founder's note
    const tm = await termsFor(env, artist.id);
    const myTerms = { programme: AG.programmeOf(d.artist, tm), ...(tm ? { commission_bp: tm.commission_bp, variation_agreed_on: tm.variation_agreed_on || null } : {}) };
    return json({ ok: true, artist: { ...a, email }, terms: myTerms, status: await status(env, d.artist), opportunities: await O.status(env, artist), commissions_available: await commissionsInstalled(env), media: L.MEDIA, counties: L.COUNTIES, min_long_edge: minLong(env),
      portrait: (({ checks, ...i }) => i)(d.images.find(i => i.id === d.artist.portrait_image_id) || { checks: null }) });
  }
  if (p === '/api/me/profile' && m === 'PUT') {
    const f = clean(PROFILE, await req.json());
    if (!Object.keys(f).length) return json({ ok: true });
    await env.DB.prepare(`UPDATE artists SET ${Object.keys(f).map(k => `${k}=?`).join(', ')}, updated_at=? WHERE id=?`).bind(...Object.values(f), now(), artist.id).run();
    await audit(env, artist.email, 'artist', 'profile', artist.id, { fields: Object.keys(f) });
    return json({ ok: true, saved_at: now() });
  }
  /* Open for Commissions: the artist's own switch. It changes only this one field, is audited, and reaches a live gallery
     as an instant update (the founder's one-click Publish while automatic updates are off), never as content review.
     It changes no agreement and applies no PlotArt commission: bespoke work is agreed directly with the client. */
  if (p === '/api/me/commissions' && m === 'PUT') {
    if (!(await commissionsInstalled(env))) throw new Bad('Open for commissions isn’t available just yet. Please try again later.', 503);
    const b = await req.json().catch(() => null);
    if (!b || typeof b.open !== 'boolean' || Object.keys(b).length !== 1) throw new Bad('Refused');
    const want = b.open ? 1 : 0;
    const cur = await one(env, 'SELECT open_for_commissions FROM artists WHERE id = ?', artist.id);
    if (cur && cur.open_for_commissions === want) return json({ ok: true, open: !!want, changed: false });
    await env.DB.prepare('UPDATE artists SET open_for_commissions=?, updated_at=? WHERE id=?').bind(want, now(), artist.id).run();
    await audit(env, artist.email, 'artist', want ? 'commissions_on' : 'commissions_off', artist.id, {});
    const v = await instant(env, artist, artist.email, want ? 'commissions_on' : 'commissions_off');
    return json({ ok: true, open: !!want, changed: true, instant_version: v });
  }
  if (p === '/api/me/portrait' && m === 'PUT') return upload(req, env, artist, { role: 'portrait' });
  if (p === '/api/me/portrait' && m === 'DELETE') {
    await env.DB.prepare("UPDATE images SET deleted_at=? WHERE artist_id=? AND role='portrait' AND deleted_at IS NULL").bind(now(), artist.id).run();
    await env.DB.prepare('UPDATE artists SET portrait_image_id=NULL, updated_at=? WHERE id=?').bind(now(), artist.id).run();
    return json({ ok: true });
  }
  if (p === '/api/artworks' && m === 'GET') {
    const d = await load(env, artist.id);
    const lv = await latestVersion(env, artist.id);
    const liveIds = new Set(lv ? lv.snap.works.map(w => w.id) : []);
    const blk = blocked(d.images);
    return json({ ok: true, works: d.works.map(w => ({ ...w, in_version: liveIds.has(w.id),
      images: d.images.filter(i => i.artwork_id === w.id).map(i => { const c = JSON.parse(i.checks); return { ...i, checks: { blocks: c.blocks, warns: c.warns } }; }), blocked: d.images.some(i => i.artwork_id === w.id && blk.has(i.id)) })) });
  }
  if (p === '/api/artworks' && m === 'POST') {
    const max = await one(env, 'SELECT COALESCE(MAX(ord),0) AS m FROM artworks WHERE artist_id=?', artist.id);
    const taken = new Set((await all(env, 'SELECT slug FROM artworks WHERE artist_id=?', artist.id)).map(r => r.slug));
    const id = rid('w');
    await env.DB.prepare('INSERT INTO artworks (id, artist_id, slug, ord, created_at, updated_at) VALUES (?,?,?,?,?,?)').bind(id, artist.id, L.slugify('untitled-' + id.slice(1, 5), taken), max.m + 1, now(), now()).run();
    await audit(env, artist.email, 'artist', 'artwork_new', artist.id, { id });
    return json({ ok: true, id });
  }
  if (p === '/api/artworks/order' && m === 'POST') {
    const ids = (await req.json()).ids;
    const mine = await all(env, 'SELECT id FROM artworks WHERE artist_id=?', artist.id);
    if (!Array.isArray(ids) || ids.length !== mine.length || !ids.every(i => mine.some(r => r.id === i))) throw new Bad('Reorder refused');
    await env.DB.batch(ids.map((id, i) => env.DB.prepare('UPDATE artworks SET ord=?, updated_at=? WHERE id=? AND artist_id=?').bind(i + 1, now(), id, artist.id)));
    const v = await instant(env, artist, artist.email, 'order');
    return json({ ok: true, instant_version: v });
  }
  if ((mm = p.match(/^\/api\/artworks\/(w[0-9a-z]+)$/))) {
    const w = await ownWork(env, artist, mm[1]);
    if (m === 'PUT') {
      const f = clean(WORK, await req.json());
      if ('title' in f && f.title) {
        const lv = await latestVersion(env, artist.id);
        if (!(lv && lv.snap.works.some(x => x.id === w.id))) {   // the address is fixed once published
          const taken = new Set((await all(env, 'SELECT slug FROM artworks WHERE artist_id=? AND id<>?', artist.id, w.id)).map(r => r.slug));
          f.slug = L.slugify(f.title, taken);
        }
      }
      if (!Object.keys(f).length) return json({ ok: true });
      await env.DB.prepare(`UPDATE artworks SET ${Object.keys(f).map(k => `${k}=?`).join(', ')}, updated_at=? WHERE id=? AND artist_id=?`).bind(...Object.values(f), now(), w.id, artist.id).run();
      await audit(env, artist.email, 'artist', 'artwork_edit', artist.id, { id: w.id, fields: Object.keys(f) });
      return json({ ok: true, saved_at: now() });
    }
    if (m === 'DELETE') {
      const lv = await latestVersion(env, artist.id);
      if (lv && lv.snap.works.some(x => x.id === w.id)) throw new Bad('A published artwork is removed with “Remove from gallery”, not deleted');
      await env.DB.batch([env.DB.prepare('UPDATE images SET deleted_at=? WHERE artwork_id=? AND artist_id=?').bind(now(), w.id, artist.id),
        env.DB.prepare('DELETE FROM artworks WHERE id=? AND artist_id=?').bind(w.id, artist.id)]);
      await audit(env, artist.email, 'artist', 'artwork_delete', artist.id, { id: w.id });
      return json({ ok: true });
    }
  }
  if ((mm = p.match(/^\/api\/artworks\/(w[0-9a-z]+)\/(availability|archive)$/)) && m === 'POST') {
    const w = await ownWork(env, artist, mm[1]);
    const b = await req.json();
    if (mm[2] === 'availability') {
      if (!L.AVAILABILITY.includes(b.availability)) throw new Bad('Choose available, reserved, sold or not for sale');
      await env.DB.prepare('UPDATE artworks SET availability=?, updated_at=? WHERE id=? AND artist_id=?').bind(b.availability, now(), w.id, artist.id).run();
    } else {
      await env.DB.prepare('UPDATE artworks SET archived=?, updated_at=? WHERE id=? AND artist_id=?').bind(b.archived ? 1 : 0, now(), w.id, artist.id).run();
    }
    const v = await instant(env, artist, artist.email, `${mm[2]}:${w.id}`);
    return json({ ok: true, instant_version: v });
  }
  if ((mm = p.match(/^\/api\/artworks\/(w[0-9a-z]+)\/images$/)) && m === 'PUT') {
    await ownWork(env, artist, mm[1]);
    const role = url.searchParams.get('role') === 'view' ? 'view' : 'main';
    return upload(req, env, artist, { artworkId: mm[1], role });
  }
  if ((mm = p.match(/^\/api\/images\/(i[0-9a-z]+)$/))) {
    const img = await ownImage(env, artist, mm[1]);
    if (m === 'PATCH') {
      const b = await req.json(), f = {};
      if ('alt' in b) f.alt = L.text(b.alt, 5, 300, 'Photo description', { optional: true });
      if ('photographer' in b) { if (!['self', 'other_with_permission'].includes(b.photographer)) throw new Bad('Who took the photograph?'); f.photographer = b.photographer; }
      if ('photo_credit' in b) f.photo_credit = L.text(b.photo_credit, 2, 80, 'Photographer’s name', { optional: true });
      if (Object.keys(f).length) {
        await env.DB.prepare(`UPDATE images SET ${Object.keys(f).map(k => `${k}=?`).join(', ')} WHERE id=? AND artist_id=?`).bind(...Object.values(f), img.id, artist.id).run();
        // 11 Nov 2026: photograph-detail saves are recorded, field names only (never the description or a name)
        await audit(env, artist.email, 'artist', 'image_details', artist.id, { image: img.id, artwork: img.artwork_id, role: img.role, fields: Object.keys(f) });
      }
      return json({ ok: true, saved_at: now() });
    }
    if (m === 'DELETE') {
      if (img.role === 'main') throw new Bad('Replace the main photograph instead of deleting it');
      await env.DB.prepare('UPDATE images SET deleted_at=? WHERE id=? AND artist_id=?').bind(now(), img.id, artist.id).run();
      return json({ ok: true });
    }
  }
  if ((mm = p.match(/^\/api\/images\/(i[0-9a-z]+)\/preview$/)) && m === 'PUT') {
    const img = await ownImage(env, artist, mm[1]);
    const buf = await req.arrayBuffer();
    if (buf.byteLength > L.MAX_PREVIEW_BYTES || L.sniff(new Uint8Array(buf)) !== 'jpeg') throw new Bad('Preview refused');
    const key = `previews/${artist.id}/${img.id}.jpg`;
    await env.IMAGES.put(key, buf, { httpMetadata: { contentType: 'image/jpeg' } });
    await env.DB.prepare('UPDATE images SET preview_key=? WHERE id=? AND artist_id=?').bind(key, img.id, artist.id).run();
    return json({ ok: true });
  }
  if ((mm = p.match(/^\/api\/images\/(i[0-9a-z]+)\/view$/)) && m === 'GET') return previewImage(env, await ownImage(env, artist, mm[1]));
  if (p === '/api/enquiries' && m === 'GET') return json({ ok: true, items: (await H.installed(env))   // purchase and hire enquiries, told apart (Art for Hire 3B-3)
    ? await all(env, `SELECT e.reference, e.created_at, e.artwork_title, e.buyer_name, e.buyer_email, e.message, e.status,
        CASE WHEN h.enquiry_id IS NULL THEN 'purchase' ELSE 'hire' END AS kind, h.business, h.role, h.business_url
        FROM enquiries e LEFT JOIN hire_enquiries h ON h.enquiry_id = e.id WHERE e.artist_id = ? ORDER BY e.created_at DESC LIMIT 200`, artist.id)
    : await all(env, 'SELECT reference, created_at, artwork_title, buyer_name, buyer_email, message, status FROM enquiries WHERE artist_id = ? ORDER BY created_at DESC LIMIT 200', artist.id) });
  if (p === '/api/agreement' && m === 'GET') {
    const a = await one(env, 'SELECT * FROM artists WHERE id=?', artist.id);
    const ag = await agreementState(env, a);
    const pt = await participation(env, a);
    return json({ ok: true, ...agreementSummary(ag), history: effectiveRows(ag.history, await corrections(env, a.id)).map(r => ({ doc_id: r.doc_id, accepted_at: r.accepted_at, method: r.method, statement: r.statement,
      doc_sha256: r.doc_sha256, pdf_sha256: r.pdf_sha256, legal_name: r.legal_name, account_email: r.account_email, display_name: r.display_name, note: r.note,
      corrections: r.corrections.map(c => ({ field: c.field, corrected_at: c.corrected_at, reason: c.reason })) })),
      leave: pt.installed ? { request: pt.request } : null,
      documents: ag.required.map(id => ({ id, title: AG.doc(id).title, html_sha256: AG.doc(id).html_sha256, pdf_sha256: AG.doc(id).pdf_sha256 })) });
  }
  if (p === '/api/agreement/accept' && m === 'POST') return json({ ok: true, ...(await acceptAgreement(env, artist, await req.json())) });
  if (p === '/api/leave' && m === 'POST') return json({ ok: true, ...(await requestLeave(env, artist, await req.json())) });
  if (p === '/api/leave/withdraw' && m === 'POST') return json({ ok: true, ...(await withdrawLeave(env, artist)) });
  if (p === '/api/submit' && m === 'POST') return submit(env, artist, await req.json());
  if (p === '/api/submit/withdraw' && m === 'POST') {
    await env.DB.prepare("UPDATE submissions SET status='withdrawn', decided_at=? WHERE artist_id=? AND status='pending'").bind(now(), artist.id).run();
    return json({ ok: true });
  }
  return json({ ok: false, error: 'Not found' }, 404);
}
