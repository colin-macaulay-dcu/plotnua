/* PlotArt Studio · Art for Hire (Stage 3B-2, development 10 Nov 2026). NOT DEPLOYED.
   A separate layer BESIDE the gallery: it never writes versions, submissions, publish_queue, gallery files, artworks or any
   agreement table. Hire details live in artwork_hire (migration 0007); acceptances of the separate, optional Art for Hire
   Artist Terms (PA-AFH) live in hire_terms_acceptances.

   A work is LISTED for hire only when all three gates hold, checked in one place (listedRows):
     1. the artist holds the current PA-AFH text (and has not left Art for Hire);
     2. the artist has switched that work on (offered = 1);
     3. the founder has approved it (approved_public is set).
   …and the work is in the artist's PUBLISHED gallery, available, not archived, and the artist's account is active.

   Screen and photo choices record the artist's WILLINGNESS TO DISCUSS permission. They are never a licence: any permission
   is agreed in writing between the artist and the hirer (Artist Terms 2.4–2.5). */
import { Bad, now, rid } from './lib.js';
import * as A from './assets.js';
import * as R from './hire-rules.js';
import { dublinDate, dublinToday } from './founding.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
async function audit(env, actor, role, action, artistId, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, role, action, artistId || null, detail ? JSON.stringify(detail).slice(0, 4000) : null).run();
}

export const { SCREEN_NOTICE, PILOT_NOTICE } = R;
export const STATEMENT = (doc) => `I have read and accept the PlotArt Art for Hire Artist Terms ${doc}. I understand that taking part is optional, that PlotArt only introduces hirers to me, and that any hire, fee, replacement value or screen-use permission is agreed between me and the hirer.`;

/* The switch: acceptance (and therefore any new offer) is possible only when the founder turns HIRE_TERMS_ENABLED on AND
   an issued, fingerprinted PA-AFH text is both bundled with the Studio and installed in hire_terms (D10: legal review first). */
export const enabled = env => env.HIRE_TERMS_ENABLED === 'true';
export async function installed(env) {
  try { await env.DB.prepare('SELECT 1 FROM artwork_hire LIMIT 1').all(); return true; } catch { return false; }
}
export async function currentTerms(env) {
  const d = await one(env, 'SELECT * FROM hire_terms WHERE effective_at <= ? ORDER BY effective_at DESC LIMIT 1', now());
  const text = d && (A.HIRE_TERMS || {})[d.doc_id];
  return d && text && text.html_sha256 === d.html_sha256 && text.pdf_sha256 === d.pdf_sha256 ? d : null;
}

const { SCREEN, PHOTO, REVIEWED, pick } = R;
const PUBLIC = ['availability', 'available_from', 'county', 'screen_use', 'photo_use', 'framing', 'glazed', 'weight_band', 'collection', 'deliver_km'];
const DEFAULTS = { offered: 0, availability: 'now', available_from: null, county: null, screen_use: 'none', photo_use: 'none', framing: null, glazed: null,
  weight_band: null, handling_note: null, collection: 'ask', deliver_km: null, review_state: 'draft', approved_public: null };
const day = () => now().slice(0, 10);

/* Field rules (values from the Stage 3A design; no price, fee or value field exists). */
const one_of = (k, set) => v => { if (!set.includes(v)) throw new Bad(`Choose a valid ${k}`); return v; };
const SPEC = {
  offered: v => { if (v !== true && v !== false && v !== 0 && v !== 1) throw new Bad('offered must be on or off'); return v ? 1 : 0; },
  availability: one_of('availability', ['now', 'from', 'not_now']),
  available_from: v => { if (v === null || v === '') return null; if (!/^\d{4}-\d{2}-\d{2}$/.test(v) || isNaN(Date.parse(v))) throw new Bad('Give the date as YYYY-MM-DD'); return v; },
  county: v => { if (v === null || v === '') return null; const s = String(v).trim(); if (!/^[A-Za-z' .-]{2,40}$/.test(s)) throw new Bad('Give a county name'); return s; },
  screen_use: one_of('screen use', ['none', 'background', 'featured']),
  photo_use: one_of('photography', ['none', 'yes']),
  framing: v => v === null || v === '' ? null : one_of('framing', ['framed', 'unframed', 'ready_to_hang'])(v),
  glazed: v => v === null || v === '' ? null : (v === true || v === 1 ? 1 : v === false || v === 0 ? 0 : (() => { throw new Bad('glazed must be yes or no'); })()),
  weight_band: v => v === null || v === '' ? null : one_of('weight', ['under_5kg', '5_15kg', 'over_15kg'])(v),
  handling_note: v => { if (v === null || v === '') return null; const s = String(v).trim(); if (s.length > 280) throw new Bad('Handling note: 280 characters at most'); return s; },
  collection: one_of('collection', ['collect', 'deliver_local', 'ask']),
  deliver_km: v => { if (v === null || v === '') return null; const n = Number(v); if (!Number.isInteger(n) || n < 1 || n > 500) throw new Bad('Delivery distance: 1 to 500 km'); return n; },
};
function clean(body) {
  const out = {};
  for (const [k, v] of Object.entries(body || {})) { if (!(k in SPEC)) throw new Bad(`Unknown field ${k}`); out[k] = SPEC[k](v); }
  return out;
}

/* ---------------------------------------------------------------- the artist's standing */
async function latestEvent(env, artistId) {
  return one(env, 'SELECT kind FROM hire_participation_events WHERE artist_id = ? ORDER BY at DESC, rowid DESC LIMIT 1', artistId);
}
export async function standing(env, artistId) {
  const terms = await currentTerms(env);
  const acc = terms ? await one(env, 'SELECT accepted_at FROM hire_terms_acceptances WHERE artist_id = ? AND doc_id = ? ORDER BY accepted_at DESC LIMIT 1', artistId, terms.doc_id) : null;
  const ev = await latestEvent(env, artistId);
  const left = !!ev && ev.kind === 'left';
  return { enabled: enabled(env), terms: terms ? { doc_id: terms.doc_id, title: terms.title } : null, accepted: !!acc, accepted_at: acc ? acc.accepted_at : null,
    left, active: enabled(env) && !!terms && !!acc && !left };
}
const published = R.published;

/* ---------------------------------------------------------------- the artist's own hire records (always scoped) */
export async function artistView(env, artist) {
  const st = await standing(env, artist.id);
  const snap = await published(env, artist.id);
  const pub = new Map((snap ? snap.works : []).map(w => [w.id, w]));
  const works = await all(env, 'SELECT id, title, availability, archived FROM artworks WHERE artist_id = ? ORDER BY ord', artist.id);
  const rows = new Map((await all(env, 'SELECT * FROM artwork_hire WHERE artist_id = ?', artist.id)).map(r => [r.artwork_id, r]));
  const listed = new Set((await listedRows(env, { artistId: artist.id })).map(r => r.artwork_id));
  return { ...st, notice: SCREEN_NOTICE, pilot_notice: PILOT_NOTICE, statement: st.terms ? STATEMENT(st.terms.doc_id) : null,
    works: works.filter(w => !w.archived).map(w => {
      const r = rows.get(w.id) || DEFAULTS;
      return { artwork_id: w.id, title: w.title, published: pub.has(w.id), gallery_availability: w.availability,
        hire: { ...pick(r, ['offered', ...PUBLIC, 'handling_note', 'review_state']), decline_reason: r.decline_reason || null }, listed: listed.has(w.id) };
    }) };
}

export async function accept(env, artist, body) {
  if (!enabled(env)) throw new Bad('Art for Hire is not open yet', 409);
  const t = await currentTerms(env);
  if (!t) throw new Bad('The Art for Hire Artist Terms are not available yet', 409);
  if (!body || body.confirm !== true || body.doc_id !== t.doc_id) throw new Bad('Tick to accept the current Art for Hire Artist Terms');
  const st = await standing(env, artist.id);
  if (st.accepted && !st.left) return { accepted_at: st.accepted_at, already: true };      // nothing to record twice
  const at = now();
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO hire_terms_acceptances (id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, statement, method, created_at)
      VALUES (?,?,?,?,?,?,?,?,?, 'studio_checkbox', ?)`).bind(rid('ha'), artist.id, t.doc_id, t.html_sha256, t.pdf_sha256, at, artist.email, artist.display_name, STATEMENT(t.doc_id), at),
  ]);
  const ev = await latestEvent(env, artist.id);
  if (ev && ev.kind === 'left') await env.DB.prepare("INSERT INTO hire_participation_events (id, artist_id, kind, at, actor, created_at) VALUES (?,?,'rejoined',?,?,?)").bind(rid('hp'), artist.id, at, artist.email, at).run();
  await audit(env, artist.email, 'artist', 'hire_terms_accepted', artist.id, { doc: t.doc_id });
  return { accepted_at: at };
}

/* Leaving Art for Hire: every work comes off at once (immediately unlisted; gallery untouched). Always possible. */
export async function leave(env, artist, body) {
  if (!body || body.confirm !== true) throw new Bad('Tick to confirm');
  const at = now();
  const ev = await latestEvent(env, artist.id);
  const st = [env.DB.prepare('UPDATE artwork_hire SET offered = 0, withdrawn_at = COALESCE(withdrawn_at, ?), review_state = CASE WHEN approved_public IS NULL THEN \'draft\' ELSE review_state END, updated_at = ? WHERE artist_id = ? AND offered = 1').bind(at, at, artist.id)];
  if (!ev || ev.kind !== 'left') st.push(env.DB.prepare("INSERT INTO hire_participation_events (id, artist_id, kind, at, actor, created_at) VALUES (?,?,'left',?,?,?)").bind(rid('hp'), artist.id, at, artist.email, at));
  await env.DB.batch(st);
  await audit(env, artist.email, 'artist', 'hire_left', artist.id, null);
  return { left_at: at };
}

/* One artwork's hire panel. Narrowing and withdrawal take effect at once; anything that widens what is public waits for
   the founder, and the live listing keeps its last approved details meanwhile. */
export async function saveWork(env, artist, artworkId, body) {
  const w = await one(env, 'SELECT id, availability, archived FROM artworks WHERE id = ? AND artist_id = ?', artworkId, artist.id);
  if (!w) throw new Bad('Not found', 404);                                             // another artist's work: as if it did not exist
  const f = clean(body);
  const prev = (await one(env, 'SELECT * FROM artwork_hire WHERE artwork_id = ? AND artist_id = ?', artworkId, artist.id)) || null;
  const cur = { ...DEFAULTS, ...(prev || {}) };
  const next = { ...cur, ...f };
  if (next.availability !== 'from') next.available_from = null;
  if (next.availability === 'from' && !next.available_from) throw new Bad('Give the date the work is available from');
  if (next.collection !== 'deliver_local') next.deliver_km = null;
  const turningOff = cur.offered === 1 && next.offered === 0;
  const onlyNarrowing = Object.keys(f).every(k => k === 'offered' ? next.offered <= cur.offered
    : k === 'screen_use' ? SCREEN[next.screen_use] <= SCREEN[cur.screen_use] : k === 'photo_use' ? PHOTO[next.photo_use] <= PHOTO[cur.photo_use]
    : ['availability', 'available_from', 'handling_note'].includes(k));
  const st = await standing(env, artist.id);
  if (!st.active && !onlyNarrowing) throw new Bad(!st.enabled || !st.terms ? 'Art for Hire is not open yet' : st.left ? 'You have left Art for Hire. Accept the terms again to rejoin.' : 'Accept the Art for Hire Artist Terms first', 409);
  if (next.offered === 1 && cur.offered === 0) {
    if (w.archived || w.availability !== 'available') throw new Bad('Only a work that is available in your gallery can be offered for hire', 409);
    const snap = await published(env, artist.id);
    if (!snap || !snap.works.some(x => x.id === artworkId)) throw new Bad('Only a work already published in your gallery can be offered for hire', 409);
  }
  const at = now();
  let review = cur.review_state, approved = cur.approved_public ? JSON.parse(cur.approved_public) : null, withdrawn = cur.withdrawn_at;
  if (next.offered === 1 && cur.offered === 0) { review = 'pending'; approved = null; withdrawn = null; }        // a new offer: full review
  if (turningOff) { withdrawn = at; if (!approved) review = 'draft'; }
  if (approved) {
    // narrowing applies to the approved listing at once, so widening back always needs the founder again
    if (SCREEN[next.screen_use] < SCREEN[approved.screen_use]) approved.screen_use = next.screen_use;
    if (PHOTO[next.photo_use] < PHOTO[approved.photo_use]) approved.photo_use = next.photo_use;
    const widened = SCREEN[next.screen_use] > SCREEN[approved.screen_use] || PHOTO[next.photo_use] > PHOTO[approved.photo_use];
    const changed = REVIEWED.some(k => (next[k] ?? null) !== (approved[k] ?? null));
    if (next.offered === 1 && (widened || changed)) review = 'pending';
    else if (next.offered === 1 && review === 'pending' && !widened && !changed) review = 'approved';   // back to what was approved
  }
  await env.DB.prepare(`INSERT INTO artwork_hire (artwork_id, artist_id, offered, availability, available_from, county, screen_use, photo_use, framing, glazed, weight_band,
      handling_note, collection, deliver_km, review_state, approved_public, approved_at, approved_by, decline_reason, withdrawn_at, updated_at, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(artwork_id) DO UPDATE SET offered=excluded.offered, availability=excluded.availability, available_from=excluded.available_from, county=excluded.county,
      screen_use=excluded.screen_use, photo_use=excluded.photo_use, framing=excluded.framing, glazed=excluded.glazed, weight_band=excluded.weight_band,
      handling_note=excluded.handling_note, collection=excluded.collection, deliver_km=excluded.deliver_km, review_state=excluded.review_state,
      approved_public=excluded.approved_public, approved_at=excluded.approved_at, approved_by=excluded.approved_by, decline_reason=excluded.decline_reason,
      withdrawn_at=excluded.withdrawn_at, updated_at=excluded.updated_at
    WHERE artwork_hire.artist_id = excluded.artist_id`)
    .bind(artworkId, artist.id, next.offered, next.availability, next.available_from, next.county, next.screen_use, next.photo_use, next.framing, next.glazed, next.weight_band,
      next.handling_note, next.collection, next.deliver_km, review, approved ? JSON.stringify(approved) : null, approved ? cur.approved_at : null, approved ? cur.approved_by : null,
      review === 'pending' ? null : cur.decline_reason || null, withdrawn, at, prev ? prev.created_at : at).run();
  await audit(env, artist.email, 'artist', turningOff ? 'hire_withdrawn' : 'hire_saved', artist.id, { artwork: artworkId, fields: Object.keys(f), review });
  return { review_state: review, listed: (await listedRows(env, { artworkId })).length === 1 };
}

/* ---------------------------------------------------------------- the three gates (shared with the enquiry relay: hire-rules.js) */
export async function listedRows(env, { artistId = null, artworkId = null } = {}) {
  if (!enabled(env)) return [];
  const terms = await currentTerms(env);
  if (!terms) return [];
  return R.listedFor(env, { docId: terms.doc_id, artistId, artworkId });
}
export const isListed = async (env, artworkId) => (await listedRows(env, { artworkId })).length === 1;
export async function catalogue(env) {
  const items = await listedRows(env);
  return { generated_at: now(), notice: SCREEN_NOTICE, pilot_notice: PILOT_NOTICE, items };
}

/* ---------------------------------------------------------------- founder */
export async function adminView(env) {
  const terms = await currentTerms(env);
  const pending = await all(env, `SELECT h.*, a.display_name, a.slug AS artist_slug, w.title FROM artwork_hire h JOIN artworks w ON w.id = h.artwork_id AND w.artist_id = h.artist_id
    JOIN artists a ON a.id = h.artist_id WHERE h.offered = 1 AND h.review_state = 'pending' ORDER BY h.updated_at`);
  const permissions = await all(env, 'SELECT p.*, a.display_name FROM hire_use_permissions p LEFT JOIN artists a ON a.id = p.artist_id ORDER BY p.answered_at DESC LIMIT 200');
  return { enabled: enabled(env), terms: terms ? { doc_id: terms.doc_id, title: terms.title } : null, notice: SCREEN_NOTICE,
    pending: pending.map(r => ({ artwork_id: r.artwork_id, artist_id: r.artist_id, artist: r.display_name, title: r.title, proposed: pick(r, PUBLIC),
      approved: r.approved_public ? JSON.parse(r.approved_public) : null, updated_at: r.updated_at })),
    listed: await listedRows(env), permissions };
}
export async function decide(env, founder, artworkId, body) {
  const r = await one(env, 'SELECT * FROM artwork_hire WHERE artwork_id = ?', artworkId);
  if (!r || r.offered !== 1 || r.review_state !== 'pending') throw new Bad('Nothing waiting for review on this work', 409);
  const at = now();
  if (body && body.decision === 'approve') {
    const st = await standing(env, r.artist_id);
    if (!st.active) throw new Bad('The artist does not currently hold the Art for Hire Artist Terms', 409);
    const w = await one(env, 'SELECT availability, archived FROM artworks WHERE id = ? AND artist_id = ?', artworkId, r.artist_id);
    const snap = await published(env, r.artist_id);
    if (!w || w.archived || w.availability !== 'available' || !snap || !snap.works.some(x => x.id === artworkId)) throw new Bad('The work is not published and available in the gallery', 409);
    const ap = pick(r, PUBLIC);
    await env.DB.prepare("UPDATE artwork_hire SET review_state='approved', approved_public=?, approved_at=?, approved_by=?, decline_reason=NULL, updated_at=? WHERE artwork_id=? AND review_state='pending' AND offered=1 AND updated_at=?")
      .bind(JSON.stringify(ap), at, founder, at, artworkId, r.updated_at).run();
    await audit(env, founder, 'founder', 'hire_approved', r.artist_id, { artwork: artworkId, public: ap });
    return { approved: true };
  }
  if (body && body.decision === 'decline') {
    const reason = String(body.reason || '').trim();
    if (reason.length < 5 || reason.length > 280) throw new Bad('Give the artist a short reason (5 to 280 characters)');
    const back = r.approved_public ? 'approved' : 'declined';      // a declined CHANGE keeps the earlier approved listing
    if (r.approved_public) {
      const ap = JSON.parse(r.approved_public);
      await env.DB.prepare('UPDATE artwork_hire SET review_state=?, decline_reason=?, county=?, framing=?, glazed=?, weight_band=?, collection=?, deliver_km=?, screen_use=?, photo_use=?, updated_at=? WHERE artwork_id=?')
        .bind(back, reason, ap.county, ap.framing, ap.glazed, ap.weight_band, ap.collection, ap.deliver_km,
          SCREEN[r.screen_use] < SCREEN[ap.screen_use] ? r.screen_use : ap.screen_use, PHOTO[r.photo_use] < PHOTO[ap.photo_use] ? r.photo_use : ap.photo_use, at, artworkId).run();
    } else {
      await env.DB.prepare("UPDATE artwork_hire SET review_state='declined', decline_reason=?, updated_at=? WHERE artwork_id=?").bind(reason, at, artworkId).run();
    }
    await audit(env, founder, 'founder', 'hire_declined', r.artist_id, { artwork: artworkId, reason });
    return { declined: true };
  }
  throw new Bad('Choose approve or decline');
}
/* A separate, recorded permission for ONE specific use (Artist Terms 4.2). Every work must be the artist's own and listed. */
export async function recordPermission(env, founder, b) {
  const kinds = ['lookbook', 'social', 'press', 'other'];
  if (!b || !kinds.includes(b.use_kind)) throw new Bad('Choose the kind of use');
  const purpose = String(b.purpose || '').trim(), recipients = String(b.recipients || '').trim();
  if (purpose.length < 5 || purpose.length > 500) throw new Bad('Describe the specific use (5 to 500 characters)');
  if (recipients.length < 2 || recipients.length > 500) throw new Bad('Name the recipients (businesses or type)');
  if (!['yes', 'no'].includes(b.answer)) throw new Bad('Record the artist’s answer: yes or no');
  const answered = String(b.answered_at || '');
  if (isNaN(Date.parse(answered)) || Date.parse(answered) > Date.now() + 60_000) throw new Bad('Give the date and time of the artist’s answer');
  const a = await one(env, 'SELECT id FROM artists WHERE id = ?', String(b.artist_id || ''));
  if (!a) throw new Bad('Artist not found', 404);
  const ids = Array.isArray(b.artwork_ids) ? [...new Set(b.artwork_ids.map(String))] : [];
  if (!ids.length || ids.length > 50) throw new Bad('List the works the permission covers');
  for (const id of ids) {
    const w = await one(env, 'SELECT id FROM artworks WHERE id = ? AND artist_id = ?', id, a.id);
    if (!w) throw new Bad('A listed work does not belong to this artist', 400);
    if (b.answer === 'yes' && !(await isListed(env, id))) throw new Bad('A “yes” can only cover works currently listed for hire', 409);
  }
  const id = rid('hu'), at = now();
  await env.DB.prepare(`INSERT INTO hire_use_permissions (id, artist_id, use_kind, purpose, recipients, artwork_ids, answer, answered_at, method, recorded_by, created_at)
    VALUES (?,?,?,?,?,?,?,?, 'email_logged_by_founder', ?, ?)`).bind(id, a.id, b.use_kind, purpose, recipients, JSON.stringify(ids), b.answer, new Date(answered).toISOString(), founder, at).run();
  await audit(env, founder, 'founder', 'hire_permission_recorded', a.id, { id, use_kind: b.use_kind, answer: b.answer, works: ids.length });
  return { id };
}

/* ---------------------------------------------------------------- retention (daily schedule) */
export async function sweep(env) {
  if (!(await installed(env))) return { installed: false };
  const at = now(), cut = new Date(Date.now() - 30 * 86400_000).toISOString();
  // a work that is sold, archived or no longer available, or whose artist has ended participation, comes off hire
  const off = await env.DB.prepare(`UPDATE artwork_hire SET offered = 0, withdrawn_at = COALESCE(withdrawn_at, ?), updated_at = ? WHERE offered = 1 AND (
      NOT EXISTS (SELECT 1 FROM artworks w WHERE w.id = artwork_hire.artwork_id AND w.archived = 0 AND w.availability IN ('available', 'reserved'))
      OR EXISTS (SELECT 1 FROM participation_events p WHERE p.artist_id = artwork_hire.artist_id AND p.kind = 'ended'))`).bind(at, at).run();
  // hire details of withdrawn works are deleted 30 days after withdrawal (privacy addendum); the gallery record is unaffected.
  // Stage 3A safeguard 8: DRY RUN until the founder sets HIRE_RETENTION = "on": the daily run only counts what it would delete.
  const DUE_DETAILS = 'FROM artwork_hire WHERE offered = 0 AND withdrawn_at IS NOT NULL AND withdrawn_at < ?', DUE_ENQ = 'FROM hire_enquiries WHERE delete_after < ?';
  if (env.HIRE_RETENTION !== 'on') {
    const d = await env.DB.prepare('SELECT COUNT(*) AS n ' + DUE_DETAILS).bind(cut).first(), e = await env.DB.prepare('SELECT COUNT(*) AS n ' + DUE_ENQ).bind(at).first();
    return { withdrawn: off.meta.changes || 0, dry_run: true, details_due: d.n, enquiry_details_due: e.n };
  }
  const del = await env.DB.prepare('DELETE ' + DUE_DETAILS).bind(cut).run();
  const enq = await env.DB.prepare('DELETE ' + DUE_ENQ).bind(at).run();
  return { withdrawn: off.meta.changes || 0, details_deleted: del.meta.changes || 0, enquiry_details_deleted: enq.meta.changes || 0 };
}
/* The tables the six-year deletion must clear BEFORE record_retention (Stage 3B-1 finding): present only once 0007 has run.
   Hire reports (0008) go first: hire_report_records references hire_reports. */
export async function recordTables(env) {
  const reports = (await reportsInstalled(env)) ? ['hire_report_records', 'hire_reports'] : [];
  return (await installed(env)) ? [...reports, 'hire_use_permissions', 'hire_participation_events', 'hire_terms_acceptances', 'artwork_hire'] : [];
}

/* ---------------------------------------------------------------- hire reports (migration 0008; PA-AFH-2026-11 r5 clauses 6.2–6.6, 10.1)
   The lightweight model (founder decision, 11 Nov 2026): the artist reports a successful hire here; the commission basis is
   worked out ONCE, from the enquiry log (whose founding flag was fixed when PlotArt introduced the enquiry, clause 6.3) and the
   12-month window (6.2(c)); the founder keeps the invoice and payment status by hand. Studio never invoices, takes payment,
   sends reminders or stores anything about the hirer. Reports are append-only: a mistake is corrected by a new report. */
export const RATE_BP = 1000;                                                    // 10% (clause 6.1)
export async function reportsInstalled(env) {
  try { await env.DB.prepare('SELECT 1 FROM hire_reports LIMIT 1').all(); return true; } catch { return false; }
}
const YMD = /^\d{4}-\d{2}-\d{2}$/;
const isYmd = v => typeof v === 'string' && YMD.test(v) && new Date(v + 'T12:00:00Z').toISOString().slice(0, 10) === v;
const shiftYears = (ymd, n) => { const d = new Date(ymd + 'T12:00:00Z'); d.setUTCFullYear(d.getUTCFullYear() + n); return d.toISOString().slice(0, 10); };
/* Clause 6.3 first (the founding flag fixed when PlotArt introduced the enquiry), then 6.2(c) (the hire AGREED more than 12
   months after the introduction), then 6.4 (no fee). Only "commission" carries an amount: 10% of the net hire fee, in cents. */
export function basisFor({ founding, introduced_at, agreed_on, net_fee_cents }) {
  if (founding === 1) return { basis: 'founding_year', commission_cents: 0 };
  if (agreed_on > shiftYears(dublinDate(introduced_at), 1)) return { basis: 'outside_window', commission_cents: 0 };
  if (!net_fee_cents) return { basis: 'no_fee', commission_cents: 0 };
  return { basis: 'commission', commission_cents: Math.round(net_fee_cents * RATE_BP / 10000) };
}
/* The artist's own hire introductions: relay hire enquiries (PA-H-) and email introductions the founder logged (route email),
   using the latest correction of each log entry. Purchase enquiries (PA-E-) are not hire introductions. */
async function introductions(env, artistId) {
  return all(env, `SELECT l.reference, l.introduced_at, l.founding, l.founding_year_end, l.route, l.artwork_id, w.title AS artwork_title
    FROM enquiry_log l LEFT JOIN artworks w ON w.id = l.artwork_id AND w.artist_id = l.artist_id
    WHERE l.artist_id = ? AND (l.reference LIKE 'PA-H-%' OR l.route = 'email') AND NOT EXISTS (SELECT 1 FROM enquiry_log c WHERE c.corrects = l.id)
    ORDER BY l.introduced_at DESC LIMIT 300`, artistId);
}
async function acceptedDoc(env, artistId) {
  const a = await one(env, 'SELECT doc_id FROM hire_terms_acceptances WHERE artist_id = ? ORDER BY accepted_at DESC LIMIT 1', artistId);
  return a ? a.doc_id : null;
}
const REPORT_KEYS = ['reference', 'artwork_ids', 'agreed_on', 'hire_start', 'hire_end', 'net_fee_cents', 'more_to_pay', 'payment_received', 'corrects'];
export async function reportHire(env, artist, body) {
  if (!(await reportsInstalled(env))) throw new Bad('Hire reports are not available yet', 409);
  const b = body || {};
  for (const k of Object.keys(b)) if (!REPORT_KEYS.includes(k)) throw new Bad(`Unknown field ${k}`);
  const doc = await acceptedDoc(env, artist.id);
  if (!doc) throw new Bad('Accept the Art for Hire Artist Terms before reporting a hire', 409);
  if (b.payment_received !== true) throw new Bad('Report a hire once you have received payment of the fee (clause 6.5)');
  const intro = (await introductions(env, artist.id)).find(i => i.reference === b.reference);
  if (!intro) throw new Bad('Choose one of your own hire enquiry references', 400);         // another artist's, a purchase enquiry, or unknown: refused alike
  const ids = Array.isArray(b.artwork_ids) ? [...new Set(b.artwork_ids.map(String))] : [];
  if (!ids.length || ids.length > 20) throw new Bad('Choose the work or works that were hired');
  for (const id of ids) if (!(await one(env, 'SELECT 1 AS x FROM artworks WHERE id = ? AND artist_id = ?', id, artist.id))) throw new Bad('Choose your own works', 400);
  // Dates (11 Nov 2026 review). Refused only when the combination is impossible; an advance booking is fine.
  //  · the hire was agreed on or after the day PlotArt introduced the hirer, and not in the future (it is being reported);
  //  · the hire ends on or after it starts; start and end within a sensible range of today;
  //  · a hire period that STARTS before the introduction is accepted but flagged for the founder (for example a hire
  //    already running that the introduction extended): the commission is decided by the agreement date, not the start.
  if (!isYmd(b.agreed_on)) throw new Bad('Give the date the hire was agreed (YYYY-MM-DD)');
  if (!isYmd(b.hire_start) || !isYmd(b.hire_end)) throw new Bad('Give the hire dates as YYYY-MM-DD');
  const today = dublinToday(), introOn = dublinDate(intro.introduced_at);
  if (b.agreed_on > today) throw new Bad('The date the hire was agreed cannot be in the future');
  if (b.agreed_on < introOn) throw new Bad(`The hire was agreed before PlotArt introduced this hirer (${introOn}), so it did not come from this enquiry. Check the date or the enquiry`);
  if (b.hire_end < b.hire_start) throw new Bad('The hire cannot end before it starts');
  if (b.hire_start < shiftYears(today, -3) || b.hire_start > shiftYears(today, 3)) throw new Bad('Check the hire start date');
  if (b.hire_end > shiftYears(b.hire_start, 5)) throw new Bad('Check the hire end date: the hire period is longer than five years');
  const startsBefore = b.hire_start < introOn ? 1 : 0;
  if (!Number.isInteger(b.net_fee_cents) || b.net_fee_cents < 0 || b.net_fee_cents > 100000000) throw new Bad('Give the hire fee received, excluding VAT and expenses');
  if (b.more_to_pay !== true && b.more_to_pay !== false) throw new Bad('Say whether more of the fee is still to be paid');
  let corrects = null;
  if (b.corrects !== undefined && b.corrects !== null && b.corrects !== '') {
    const c = await one(env, 'SELECT id FROM hire_reports WHERE id = ? AND artist_id = ?', String(b.corrects), artist.id);
    if (!c) throw new Bad('You can correct only your own reports', 400);
    if (await one(env, 'SELECT 1 AS x FROM hire_reports WHERE corrects = ?', c.id)) throw new Bad('That report has already been corrected', 409);
    corrects = c.id;
  }
  const { basis, commission_cents } = basisFor({ founding: intro.founding, introduced_at: intro.introduced_at, agreed_on: b.agreed_on, net_fee_cents: b.net_fee_cents });
  const id = rid('hr'), at = now();
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO hire_reports (id, artist_id, reference, artwork_ids, hire_start, hire_end, agreed_on, starts_before_introduction, net_fee_cents, more_to_pay,
        introduced_at, founding, basis, rate_bp, commission_cents, terms_doc, corrects, reported_at, reported_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`)
      .bind(id, artist.id, intro.reference, JSON.stringify(ids), b.hire_start, b.hire_end, b.agreed_on, startsBefore, b.net_fee_cents, b.more_to_pay ? 1 : 0, intro.introduced_at,
        intro.founding, basis, RATE_BP, commission_cents, doc, corrects, at, artist.email),
    env.DB.prepare(`INSERT INTO hire_report_records (report_id, artist_id, invoice_status, payment_status, updated_at, updated_by) VALUES (?,?,?,?,?,?)`)
      .bind(id, artist.id, basis === 'commission' ? 'not_invoiced' : 'no_commission', basis === 'commission' ? 'unpaid' : 'not_due', at, 'system'),
  ]);
  await audit(env, artist.email, 'artist', 'hire_reported', artist.id, { report: id, reference: intro.reference, basis, corrects, starts_before_introduction: !!startsBefore });   // no amounts
  return { report: { id, reference: intro.reference, basis, commission_cents, net_fee_cents: b.net_fee_cents, starts_before_introduction: !!startsBefore } };
}
const reportView = r => ({ id: r.id, reference: r.reference, artwork_ids: JSON.parse(r.artwork_ids), agreed_on: r.agreed_on, starts_before_introduction: !!r.starts_before_introduction,
  hire_start: r.hire_start, hire_end: r.hire_end, net_fee_cents: r.net_fee_cents,
  more_to_pay: !!r.more_to_pay, introduced_at: r.introduced_at, founding: r.founding, basis: r.basis, commission_cents: r.commission_cents, corrects: r.corrects, reported_at: r.reported_at });
export async function myReports(env, artist) {
  if (!(await reportsInstalled(env))) return { installed: false, introductions: [], reports: [] };
  const intros = await introductions(env, artist.id);
  const reps = await all(env, `SELECT r.*, c.invoice_status, c.payment_status, (SELECT x.id FROM hire_reports x WHERE x.corrects = r.id) AS corrected_by
    FROM hire_reports r LEFT JOIN hire_report_records c ON c.report_id = r.id WHERE r.artist_id = ? ORDER BY r.reported_at DESC LIMIT 200`, artist.id);
  const works = await all(env, 'SELECT id, title FROM artworks WHERE artist_id = ? AND archived = 0 ORDER BY ord', artist.id);
  return { installed: true, accepted: !!(await acceptedDoc(env, artist.id)), rate_bp: RATE_BP, works,
    introductions: intros.map(i => ({ reference: i.reference, introduced_on: dublinDate(i.introduced_at), route: i.route, artwork_id: i.artwork_id, artwork_title: i.artwork_title,
      protected: i.founding === 1, window_ends: shiftYears(dublinDate(i.introduced_at), 1) })),
    reports: reps.map(r => ({ ...reportView(r), invoice_status: r.invoice_status, payment_status: r.payment_status, corrected_by: r.corrected_by })) };   // never the founder's note
}
async function reportRows(env) {
  const rows = await all(env, `SELECT r.*, a.display_name, c.invoice_status, c.invoice_no, c.invoiced_on, c.payment_status, c.paid_on, c.note, c.updated_at AS record_updated_at,
      (SELECT x.id FROM hire_reports x WHERE x.corrects = r.id) AS corrected_by
    FROM hire_reports r LEFT JOIN artists a ON a.id = r.artist_id LEFT JOIN hire_report_records c ON c.report_id = r.id ORDER BY r.reported_at DESC LIMIT 2000`);
  const titles = new Map((await all(env, 'SELECT id, title FROM artworks')).map(w => [w.id, w.title]));
  return rows.map(r => ({ ...reportView(r), artist_id: r.artist_id, artist: r.display_name || r.artist_id, artworks: JSON.parse(r.artwork_ids).map(i => titles.get(i) || i),
    invoice_status: r.invoice_status, invoice_no: r.invoice_no, invoiced_on: r.invoiced_on, payment_status: r.payment_status, paid_on: r.paid_on, note: r.note,
    corrected_by: r.corrected_by, terms_doc: r.terms_doc }));
}
export async function adminReports(env) {
  if (!(await reportsInstalled(env))) return { installed: false, reports: [], totals: null };
  const reports = await reportRows(env);
  const live = reports.filter(r => !r.corrected_by && r.basis === 'commission');
  const sum = f => live.filter(f).reduce((n, r) => n + r.commission_cents, 0);
  return { installed: true, rate_bp: RATE_BP, reports,
    totals: { commission_cents: sum(() => true), invoiced_unpaid_cents: sum(r => r.invoice_status === 'invoiced' && r.payment_status === 'unpaid'),
      not_invoiced_cents: sum(r => r.invoice_status === 'not_invoiced'), paid_cents: sum(r => r.payment_status === 'paid') } };
}
const RECORD = {
  invoice_status: v => { if (!['not_invoiced', 'invoiced', 'no_commission', 'disputed', 'superseded'].includes(v)) throw new Bad('Choose an invoice status'); return v; },
  invoice_no: v => { if (v === null || v === '') return null; const s = String(v).trim(); if (!/^[A-Za-z0-9 ._\/-]{1,40}$/.test(s)) throw new Bad('Invoice number: letters, numbers and - _ . / only, 40 at most'); return s; },
  invoiced_on: v => { if (v === null || v === '') return null; if (!isYmd(v)) throw new Bad('Invoice date as YYYY-MM-DD'); return v; },
  payment_status: v => { if (!['unpaid', 'paid', 'not_due', 'refunded'].includes(v)) throw new Bad('Choose a payment status'); return v; },
  paid_on: v => { if (v === null || v === '') return null; if (!isYmd(v)) throw new Bad('Payment date as YYYY-MM-DD'); return v; },
  note: v => { if (v === null || v === '') return null; const s = String(v).trim(); if (s.length > 280) throw new Bad('Note: 280 characters at most'); return s; },
};
export async function setRecord(env, founder, reportId, body) {
  if (!(await reportsInstalled(env))) throw new Bad('Hire reports are not available yet', 409);
  const cur = await one(env, 'SELECT c.*, r.basis FROM hire_report_records c JOIN hire_reports r ON r.id = c.report_id WHERE c.report_id = ?', reportId);
  if (!cur) throw new Bad('Not found', 404);
  const f = {};
  for (const [k, v] of Object.entries(body || {})) { if (!(k in RECORD)) throw new Bad(`Unknown field ${k}`); f[k] = RECORD[k](v); }
  const next = { ...cur, ...f };
  if (next.invoice_status === 'invoiced' && (!next.invoice_no || !next.invoiced_on)) throw new Bad('An invoiced report needs the invoice number and date');
  if (next.payment_status === 'paid' && !next.paid_on) throw new Bad('A paid report needs the payment date');
  if (cur.basis !== 'commission' && (next.invoice_status === 'invoiced' || next.payment_status === 'paid'))
    throw new Bad('No commission is due on this report (clause 6.3, 6.2(c) or 6.4): it cannot be invoiced', 409);
  const at = now();
  await env.DB.prepare(`UPDATE hire_report_records SET invoice_status=?, invoice_no=?, invoiced_on=?, payment_status=?, paid_on=?, note=?, updated_at=?, updated_by=? WHERE report_id=?`)
    .bind(next.invoice_status, next.invoice_no, next.invoiced_on, next.payment_status, next.paid_on, next.note, at, founder, reportId).run();
  await audit(env, founder, 'founder', 'hire_record_updated', cur.artist_id, { report: reportId, fields: Object.keys(f), invoice_status: next.invoice_status, payment_status: next.payment_status });
  return { report_id: reportId, invoice_status: next.invoice_status, payment_status: next.payment_status };
}
/* CSV for the founder's own records: no hirer details, no private note; cells that a spreadsheet would read as a formula are
   made literal (a leading ' ). */
const cell = v => { let s = v === null || v === undefined ? '' : String(v); if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; return '"' + s.replace(/"/g, '""') + '"'; };
const eur = c => (c / 100).toFixed(2);
export async function reportsCsv(env, founder) {
  if (!(await reportsInstalled(env))) throw new Bad('Hire reports are not available yet', 409);
  const rows = await reportRows(env);
  const head = ['report_id', 'reported_at', 'artist', 'reference', 'introduced_on', 'founding_year_protected', 'artworks', 'agreed_on', 'hire_start', 'hire_end',
    'starts_before_introduction', 'net_hire_fee_eur',
    'more_to_pay', 'basis', 'rate', 'commission_eur', 'corrects', 'corrected_by', 'invoice_status', 'invoice_no', 'invoiced_on', 'payment_status', 'paid_on', 'terms'];
  const lines = [head.map(cell).join(',')].concat(rows.map(r => [r.id, r.reported_at, r.artist, r.reference, dublinDate(r.introduced_at), r.founding ? 'yes' : 'no', r.artworks.join('; '),
    r.agreed_on, r.hire_start, r.hire_end, r.starts_before_introduction ? 'yes' : 'no', eur(r.net_fee_cents), r.more_to_pay ? 'yes' : 'no', r.basis, '10%', eur(r.commission_cents), r.corrects, r.corrected_by, r.invoice_status, r.invoice_no,
    r.invoiced_on, r.payment_status, r.paid_on, r.terms_doc].map(cell).join(',')));
  await audit(env, founder, 'founder', 'hire_reports_exported', null, { rows: rows.length });
  return lines.join('\r\n') + '\r\n';
}
