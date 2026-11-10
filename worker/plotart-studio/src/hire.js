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
  // hire details of withdrawn works are deleted 30 days after withdrawal (privacy addendum); the gallery record is unaffected
  const del = await env.DB.prepare('DELETE FROM artwork_hire WHERE offered = 0 AND withdrawn_at IS NOT NULL AND withdrawn_at < ?').bind(cut).run();
  const enq = await env.DB.prepare('DELETE FROM hire_enquiries WHERE delete_after < ?').bind(at).run();
  return { withdrawn: off.meta.changes || 0, details_deleted: del.meta.changes || 0, enquiry_details_deleted: enq.meta.changes || 0 };
}
/* The tables the six-year deletion must clear BEFORE record_retention (Stage 3B-1 finding): present only once 0007 has run. */
export async function recordTables(env) {
  return (await installed(env)) ? ['hire_use_permissions', 'hire_participation_events', 'hire_terms_acceptances', 'artwork_hire'] : [];
}
