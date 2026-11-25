/* PlotArt Studio · Three galleries: the gallery data model (Phase B, development 24 Nov 2026; migration 0023).
   One artist account, one Studio, one artwork inventory; an artist and individual works can belong to more than one of the
   three galleries: Contemporary, Spaces, Being (final curatorial identity, 25 Nov 2026; migration 0024).

   The rules, in one place:
   - Membership of a gallery needs BOTH the founder's approval and the artist's acceptance before it is live. It can begin
     as a founder invitation, an application, the founder's curation or the artist's own request (the request counts as
     the artist's acceptance; the founder's invitation or curation counts as the founder's approval).
   - Contemporary keeps today's behaviour: an artist with NO membership rows at all is a live Contemporary member,
     and every work of a live Contemporary member is in Contemporary unless an explicit 'withdrawn' placement row takes
     it out. Nothing is ever written for existing artists or artworks; the first time an artist who has no rows is given
     any membership row, their Contemporary membership is first written down as it already was (live, 'existing_contemporary').
   - Spaces and Being start empty. Nobody is assigned to them automatically. A work is placed there only with
     the founder's approval and the artist's acceptance, and only while the artist is a live member of that gallery.
   - Order: unlimited per gallery. Contemporary keeps positions 01-25 in gallery_positions (unchanged and still guarded
     by its own checks); gallery_order holds Contemporary positions from 26 and every position of the other two galleries.
   - Artists in Focus: Spaces and Being each have their own selection of up to six (gallery_features);
     Contemporary keeps homepage_features (featured.js), unchanged.
   - Image-use consent: per use, recorded, optional (licence PA-GPIL §3.2, no standing opt-in). image_use_consents is
     append-only: this module never updates or deletes a consent row; a withdrawal is a new 'no'.
   - Readiness targets are editable and advisory; opening a gallery is the founder's explicit act (typed confirmation).
     Contemporary is always open. Opening here changes the Studio's record only: the public site shows a gallery as
     open only when its own launch switch is changed in a separate, approved release (Phase E).
   This module writes only the seven migration-0023 tables and the audit log. It never changes an artist, artwork, image,
   price, agreement, commission term, payment record, gallery position (01-25) or Featured Artists selection. */
import { Bad, now, rid } from './lib.js';

export const GALLERIES = ['contemporary', 'spaces', 'being'];
export const TITLES = { contemporary: 'Contemporary', spaces: 'Spaces', being: 'Being' };
export const DEFAULTS = {
  contemporary: { status: 'open', target_artists: 0, target_works: 0 },
  spaces: { status: 'in_preparation', target_artists: 6, target_works: 30 },
  being: { status: 'in_preparation', target_artists: 6, target_works: 30 },
};
export const SCOPES = ['homepage_feature', 'promotional_campaign', 'social_media', 'editorial_feature', 'video_feature'];
export const SOURCES = ['founder_invitation', 'application', 'founder_curation', 'artist_request'];
export const FEATURE_MAX = 6;
const OPEN_STATES = ['proposed', 'founder_approved', 'artist_accepted'];
const APP_REF = /^(F25|PA-AP)-\d{6}-[A-Z0-9]{6}$/;
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
async function audit(env, actor, role, action, artistId, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, role, action, artistId || null, JSON.stringify(detail).slice(0, 4000)).run();
}
const gallery = g => { if (!GALLERIES.includes(g)) throw new Bad('Unknown gallery', 404); return g; };
const newGallery = g => { if (gallery(g) === 'contemporary') throw new Bad('Contemporary keeps its existing order and Artists in Focus', 409); return g; };

export async function installed(env) {
  return !!(await one(env, "SELECT name FROM sqlite_master WHERE type='table' AND name='gallery_memberships'"));
}
async function need(env) { if (!(await installed(env))) throw new Bad('The three-gallery records aren’t installed yet (migration 0023)', 503); }

/* ---- settings and readiness ------------------------------------------------------------------------------------------ */
export async function settings(env) {
  const rows = await all(env, 'SELECT * FROM gallery_settings');
  return Object.fromEntries(GALLERIES.map(g => {
    const r = rows.find(x => x.gallery_id === g);
    return [g, { gallery_id: g, title: TITLES[g], ...DEFAULTS[g], opened_at: null, opened_by: null, ...(r || {}), saved: !!r }];
  }));
}
async function writeSettings(env, g, s, founder) {
  await env.DB.prepare(`INSERT INTO gallery_settings (gallery_id, status, target_artists, target_works, opened_at, opened_by, updated_at, updated_by)
    VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(gallery_id) DO UPDATE SET status=excluded.status, target_artists=excluded.target_artists,
    target_works=excluded.target_works, opened_at=excluded.opened_at, opened_by=excluded.opened_by, updated_at=excluded.updated_at, updated_by=excluded.updated_by`)
    .bind(g, s.status, s.target_artists, s.target_works, s.opened_at, s.opened_by, now(), founder).run();
}
export async function setTargets(env, founder, g, body) {
  await need(env); newGallery(g);
  const ints = k => { const v = body && body[k]; if (!Number.isInteger(v) || v < 0 || v > (k === 'target_artists' ? 500 : 5000)) throw new Bad(`${k} must be a whole number`); return v; };
  if (!body || Object.keys(body).sort().join() !== 'target_artists,target_works') throw new Bad('Refused');
  const s = (await settings(env))[g], before = { target_artists: s.target_artists, target_works: s.target_works };
  s.target_artists = ints('target_artists'); s.target_works = ints('target_works');
  await writeSettings(env, g, s, founder);
  await audit(env, founder, 'founder', 'gallery_targets', null, { gallery: g, before, after: { target_artists: s.target_artists, target_works: s.target_works } });
  return (await readiness(env, null))[g];
}
export async function setStatus(env, founder, g, body, visibleSql) {
  await need(env); newGallery(g);
  if (!body || !['open', 'in_preparation', 'paused'].includes(body.status)) throw new Bad('Choose open, in preparation or paused');
  const s = (await settings(env))[g], want = body.status;
  if (s.status === want) return { changed: false, gallery: (await readiness(env, visibleSql))[g] };
  if (want === 'open') {
    if (body.confirm !== `OPEN ${TITLES[g].toUpperCase()}`) throw new Bad(`To open it, type OPEN ${TITLES[g].toUpperCase()}`, 409);
    const r = (await readiness(env, visibleSql))[g];
    if (!r.ready && body.below_target !== true) throw new Bad(`${TITLES[g]} has ${r.live_artists} of ${r.target_artists} artists and ${r.live_works} of ${r.target_works} works. Confirm opening below the target to continue.`, 409);
    s.opened_at = now(); s.opened_by = founder;
  }
  if (want === 'in_preparation') { s.opened_at = null; s.opened_by = null; }
  const before = s.status; s.status = want;
  await writeSettings(env, g, s, founder);
  await audit(env, founder, 'founder', 'gallery_status', null, { gallery: g, before, after: want });
  return { changed: true, gallery: (await readiness(env, visibleSql))[g] };
}

/* ---- safe state changes --------------------------------------------------------------------------------------------------
   Every change of state is a compare-and-set: the write names the state (and the updated_at) it was decided on, and changes
   nothing if another request got there first; the caller then gets a 409 and nothing half-done. Writes that belong together
   (the default Contemporary row, the change itself, and what a closed membership takes with it) go in one D1 batch, which D1
   runs as a single transaction. Follow-on statements are written so that they are correct whichever request won. */
export const CONFLICT = 'This changed at the same moment somewhere else. Reload and try again.';
async function commit(env, stmts, guard) {
  const res = await env.DB.batch(stmts);
  if (!(res[guard] && res[guard].meta && res[guard].meta.changes > 0)) throw new Bad(CONFLICT, 409);
  return res;
}
const NOT_LIVE = 'NOT EXISTS (SELECT 1 FROM gallery_memberships m WHERE m.artist_id = ? AND m.gallery_id = ? AND m.state = \'live\')';
const LIVE = 'EXISTS (SELECT 1 FROM gallery_memberships m WHERE m.artist_id = ? AND m.gallery_id = ? AND m.state = \'live\')';

/* ---- memberships ------------------------------------------------------------------------------------------------------ */
async function rowsFor(env, artistId) { return all(env, 'SELECT * FROM gallery_memberships WHERE artist_id = ?', artistId); }
// The effective membership of one artist in one gallery: the explicit row, or Contemporary by default (no rows at all).
export function effective(rows, g) {
  const r = rows.find(x => x.gallery_id === g);
  if (r) return r;
  if (g === 'contemporary' && rows.length === 0) return { gallery_id: 'contemporary', state: 'live', source: 'existing_contemporary', implicit: true };
  return null;
}
// The default Contemporary membership, written down as it already was, in the same batch as an artist's first explicit row
// (a no-op once the artist has any row), so it can never change by accident.
function settleStmt(env, a, by, at) {
  return env.DB.prepare(`INSERT OR IGNORE INTO gallery_memberships (artist_id, gallery_id, state, source, application_ref, proposed_by, proposed_at,
    founder_approved_by, founder_approved_at, artist_accepted_at, updated_at) SELECT ?, 'contemporary', 'live', 'existing_contemporary', NULL, ?, ?, 'existing', ?, ?, ?
    WHERE NOT EXISTS (SELECT 1 FROM gallery_memberships WHERE artist_id = ?)`)
    .bind(a.id, by, at, a.created_at || at, a.licence_accepted_at || a.created_at || at, at, a.id);
}
// What a membership that is no longer live takes with it: the artist's order position in that gallery, their Artists in
// Focus entry there, and their works' placements there (closed as withdrawn, so a later re-joining starts afresh and no old
// acceptance is reused). Contemporary take-outs and gallery positions 01-25 are left exactly as they are.
function closeStmts(env, g, artistId, by, at) {
  const s = [env.DB.prepare(`DELETE FROM gallery_order WHERE gallery_id = ? AND artist_id = ? AND ${NOT_LIVE}`).bind(g, artistId, artistId, g)];
  if (g !== 'contemporary') s.push(
    env.DB.prepare(`DELETE FROM gallery_features WHERE gallery_id = ? AND artist_id = ? AND ${NOT_LIVE}`).bind(g, artistId, artistId, g),
    env.DB.prepare(`UPDATE artwork_placements SET state = 'withdrawn', closed_by = ?, closed_at = ?, updated_at = ? WHERE gallery_id = ? AND artist_id = ?
      AND state IN ('proposed', 'founder_approved', 'artist_accepted', 'live') AND ${NOT_LIVE}`).bind(by, at, at, g, artistId, artistId, g));
  return s;
}
// Compare-and-set on one membership row: the state and updated_at it was read with (updated_at null: the implicit default).
const MEMBER_CAS = 'artist_id = ? AND gallery_id = ? AND state = ? AND (? IS NULL OR updated_at = ?)';
const memberCas = (artistId, g, cur) => [artistId, g, cur.state, cur.implicit ? null : cur.updated_at, cur.implicit ? null : cur.updated_at];
function memberUpsert(env, row, cur) {
  // Inserts the row, or (if one exists) replaces it only while it is still exactly what this request read.
  return env.DB.prepare(`INSERT INTO gallery_memberships (artist_id, gallery_id, state, source, application_ref, proposed_by, proposed_at, founder_approved_by,
    founder_approved_at, artist_accepted_at, closed_by, closed_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL,?)
    ON CONFLICT(artist_id, gallery_id) DO UPDATE SET state=excluded.state, source=excluded.source, application_ref=excluded.application_ref,
    proposed_by=excluded.proposed_by, proposed_at=excluded.proposed_at, founder_approved_by=excluded.founder_approved_by,
    founder_approved_at=excluded.founder_approved_at, artist_accepted_at=excluded.artist_accepted_at, closed_by=NULL, closed_at=NULL, updated_at=excluded.updated_at
    WHERE gallery_memberships.state = ? AND gallery_memberships.updated_at = ?`)
    .bind(row.artist_id, row.gallery_id, row.state, row.source, row.application_ref, row.proposed_by, row.proposed_at, row.founder_approved_by,
      row.founder_approved_at, row.artist_accepted_at, row.updated_at, cur ? cur.state : '', cur ? cur.updated_at : '');
}
async function artistById(env, id) {
  const a = await one(env, "SELECT id, slug, display_name, account_status, created_at, licence_accepted_at FROM artists WHERE id = ?", id);
  if (!a) throw new Bad('No such artist', 404);
  if (!['invited', 'active'].includes(a.account_status)) throw new Bad('That artist’s account isn’t active', 409);
  return a;
}

/* The founder proposes (invitation, application, curation): this is the founder's approval; the artist then accepts. */
export async function founderPropose(env, founder, g, body) {
  await need(env); gallery(g);
  if (!body || typeof body.artist_id !== 'string') throw new Bad('Choose an artist');
  const source = body.source || 'founder_curation';
  if (!['founder_invitation', 'application', 'founder_curation'].includes(source)) throw new Bad('Unknown source');
  if (source === 'application' && !APP_REF.test(String(body.application_ref || ''))) throw new Bad('An application needs its reference (PA-AP-… or F25-…)');
  const a = await artistById(env, body.artist_id), rows = await rowsFor(env, a.id), cur = rows.find(r => r.gallery_id === g), eff = effective(rows, g);
  if (eff && ['live', 'founder_approved'].includes(eff.state)) throw new Bad(`${a.display_name} is already ${eff.state === 'live' ? 'a member of' : 'invited to'} ${TITLES[g]}`, 409);
  // Only a CURRENT request from the artist counts as their acceptance; a declined, refused or withdrawn row starts afresh.
  const at = now(), accepted = cur && cur.state === 'artist_accepted' ? cur.artist_accepted_at : null;
  const state = accepted ? 'live' : 'founder_approved';
  await commit(env, [settleStmt(env, a, founder, at), memberUpsert(env, { artist_id: a.id, gallery_id: g, state, source: accepted ? cur.source : source,
    application_ref: source === 'application' ? body.application_ref : (cur && cur.application_ref) || null, proposed_by: founder, proposed_at: at,
    founder_approved_by: founder, founder_approved_at: at, artist_accepted_at: accepted, updated_at: at }, cur)], 1);
  await audit(env, founder, 'founder', 'gallery_membership_' + (accepted ? 'approved' : 'proposed'), a.id, { gallery: g, source, state });
  return membershipView(env, a.id);
}
/* The founder approves an artist's own request. */
export async function founderApprove(env, founder, g, artistId) {
  await need(env); gallery(g);
  await artistById(env, artistId);
  const cur = (await rowsFor(env, artistId)).find(r => r.gallery_id === g);
  if (!cur || !['proposed', 'artist_accepted'].includes(cur.state)) throw new Bad('There is no request to approve', 409);
  const at = now(), live = cur.state === 'artist_accepted' && !!cur.artist_accepted_at;
  await commit(env, [env.DB.prepare(`UPDATE gallery_memberships SET state=?, founder_approved_by=?, founder_approved_at=?, updated_at=? WHERE ${MEMBER_CAS}`)
    .bind(live ? 'live' : 'founder_approved', founder, at, at, ...memberCas(artistId, g, cur))], 0);
  await audit(env, founder, 'founder', 'gallery_membership_approved', artistId, { gallery: g, live });
  return membershipView(env, artistId);
}
export async function founderClose(env, founder, g, artistId, how) {
  await need(env); gallery(g);
  if (!['refused', 'withdrawn'].includes(how)) throw new Bad('Refused');
  const a = await one(env, 'SELECT id, created_at, licence_accepted_at FROM artists WHERE id = ?', artistId);
  if (!a) throw new Bad('No such artist', 404);
  const cur = effective(await rowsFor(env, artistId), g);
  if (!cur || !(how === 'refused' ? ['proposed', 'artist_accepted'] : [...OPEN_STATES, 'live']).includes(cur.state)) throw new Bad('Nothing to ' + (how === 'refused' ? 'refuse' : 'withdraw'), 409);
  const at = now();
  await commit(env, [settleStmt(env, a, founder, at),
    env.DB.prepare(`UPDATE gallery_memberships SET state=?, closed_by=?, closed_at=?, updated_at=? WHERE ${MEMBER_CAS}`).bind(how, founder, at, at, ...memberCas(artistId, g, cur)),
    ...closeStmts(env, g, artistId, founder, at)], 1);
  await audit(env, founder, 'founder', 'gallery_membership_' + how, artistId, { gallery: g, was: cur.state });
  return membershipView(env, artistId);
}
/* The artist's side: request to join (counts as acceptance), accept the founder's invitation, decline it, or leave. */
export async function artistAct(env, artist, g, action) {
  await need(env); gallery(g);
  const a = await one(env, 'SELECT id, created_at, licence_accepted_at FROM artists WHERE id = ?', artist.id);
  const rows = await rowsFor(env, artist.id), cur = rows.find(r => r.gallery_id === g), eff = effective(rows, g), at = now();
  if (action === 'request') {
    if (eff && [...OPEN_STATES, 'live'].includes(eff.state)) throw new Bad(eff.state === 'live' ? 'You’re already in this gallery' : 'This is already in progress', 409);
    if (cur && cur.state === 'refused') throw new Bad('PlotArt has decided on this gallery; please get in touch if your work has changed', 409);
    // A request is always a fresh acceptance: any earlier founder approval on a closed row is cleared, never reused.
    await commit(env, [settleStmt(env, a, artist.email, at), memberUpsert(env, { artist_id: artist.id, gallery_id: g, state: 'artist_accepted', source: 'artist_request',
      application_ref: null, proposed_by: artist.email, proposed_at: at, founder_approved_by: null, founder_approved_at: null, artist_accepted_at: at, updated_at: at }, cur)], 1);
  } else if (action === 'accept') {
    if (!cur || cur.state !== 'founder_approved') throw new Bad('There is no invitation to accept', 409);
    await commit(env, [env.DB.prepare(`UPDATE gallery_memberships SET state='live', artist_accepted_at=?, updated_at=? WHERE ${MEMBER_CAS}`).bind(at, at, ...memberCas(artist.id, g, cur))], 0);
  } else if (action === 'decline' || action === 'withdraw') {
    if (action === 'decline' ? !cur || cur.state !== 'founder_approved' : !eff || ![...OPEN_STATES, 'live'].includes(eff.state)) throw new Bad('Nothing to ' + action, 409);
    const was = action === 'decline' ? cur : eff;
    await commit(env, [settleStmt(env, a, artist.email, at),
      env.DB.prepare(`UPDATE gallery_memberships SET state=?, closed_by=?, closed_at=?, updated_at=? WHERE ${MEMBER_CAS}`)
        .bind(action === 'decline' ? 'declined' : 'withdrawn', artist.email, at, at, ...memberCas(artist.id, g, was)),
      ...closeStmts(env, g, artist.id, artist.email, at)], 1);
  } else throw new Bad('Refused');
  await audit(env, artist.email, 'artist', 'gallery_membership_' + action, artist.id, { gallery: g });
  return membershipView(env, artist.id);
}
export async function membershipView(env, artistId) {
  const rows = await rowsFor(env, artistId);
  return { artist_id: artistId, galleries: GALLERIES.map(g => { const e = effective(rows, g); return { gallery_id: g, title: TITLES[g], state: e ? e.state : 'none', source: e ? e.source : null, implicit: !!(e && e.implicit) }; }) };
}
async function isLive(env, artistId, g) { const e = effective(await rowsFor(env, artistId), g); return !!(e && e.state === 'live'); }
/* At invitation (the founder creates Studio access): validate the optional galleries (absent = Contemporary by default, as
   today) and return the membership rows as statements, so the caller writes them in the SAME batch as the new artist: either
   the artist and their galleries are both created, or neither is. */
export function validInviteGalleries(galleries) {
  return Array.isArray(galleries) && galleries.length > 0 && galleries.every(g => GALLERIES.includes(g)) && new Set(galleries).size === galleries.length;
}
export function inviteStatements(env, founder, artistId, galleries, applicationRef, at) {
  if (galleries === undefined) return [];
  if (!validInviteGalleries(galleries)) throw new Bad('Choose one or more galleries');
  const source = applicationRef ? 'application' : 'founder_invitation';
  return galleries.map(g => env.DB.prepare(`INSERT INTO gallery_memberships (artist_id, gallery_id, state, source, application_ref, proposed_by, proposed_at,
    founder_approved_by, founder_approved_at, artist_accepted_at, updated_at) VALUES (?,?,'founder_approved',?,?,?,?,?,?,NULL,?)`)
    .bind(artistId, g, source, applicationRef || null, founder, at, founder, at, at));
}

/* ---- artwork placement ------------------------------------------------------------------------------------------------ */
async function workOf(env, artworkId) {
  const w = await one(env, 'SELECT id, artist_id, slug, title, archived FROM artworks WHERE id = ?', artworkId);
  if (!w || w.archived) throw new Bad('No such artwork', 404);
  return w;
}
async function placement(env, artworkId, g) { return one(env, 'SELECT * FROM artwork_placements WHERE artwork_id = ? AND gallery_id = ?', artworkId, g); }
// The artist on a placement is ALWAYS the artwork's own artist (read from artworks, never from the request). Written only while
// the row is still what this request read, and (needLive) only while the artist is a live member of that gallery.
function placementUpsert(env, w, g, fields, cur, needLive) {
  const at = now(), f = { state: null, proposed_by: null, proposed_at: at, founder_approved_by: null, founder_approved_at: null, artist_accepted_at: null, closed_by: null, closed_at: null, ...fields };
  return env.DB.prepare(`INSERT INTO artwork_placements (artwork_id, artist_id, gallery_id, state, proposed_by, proposed_at, founder_approved_by, founder_approved_at,
    artist_accepted_at, closed_by, closed_at, updated_at) SELECT ?,?,?,?,?,?,?,?,?,?,?,? WHERE ${needLive ? LIVE : '1'}
    ON CONFLICT(artwork_id, gallery_id) DO UPDATE SET state=excluded.state,
    proposed_by=excluded.proposed_by, proposed_at=excluded.proposed_at, founder_approved_by=excluded.founder_approved_by, founder_approved_at=excluded.founder_approved_at,
    artist_accepted_at=excluded.artist_accepted_at, closed_by=excluded.closed_by, closed_at=excluded.closed_at, updated_at=excluded.updated_at
    WHERE artwork_placements.state = ? AND artwork_placements.updated_at = ?`)
    .bind(w.id, w.artist_id, g, f.state, f.proposed_by, f.proposed_at, f.founder_approved_by, f.founder_approved_at, f.artist_accepted_at, f.closed_by, f.closed_at, at,
      ...(needLive ? [w.artist_id, g] : []), cur ? cur.state : '', cur ? cur.updated_at : '');
}
const PLACE_CAS = 'artwork_id = ? AND gallery_id = ? AND state = ? AND updated_at = ?';
// A placement that closes takes its Artists in Focus entry in that gallery with it.
const unfeature = (env, w, g) => env.DB.prepare('DELETE FROM gallery_features WHERE gallery_id = ? AND artwork_id = ?').bind(g, w.id);
/* Founder: place (counts as approval; artist then accepts), approve an artist's proposal, refuse, or withdraw. In Contemporary
   Art the only action is to take a work out (withdraw) or put it back (restore). */
export async function founderPlacement(env, founder, g, artworkId, action) {
  await need(env); gallery(g);
  const w = await workOf(env, artworkId), cur = await placement(env, artworkId, g), at = now();
  if (g === 'contemporary') {
    if (action === 'withdraw') {
      if (cur) throw new Bad('Already taken out of Contemporary', 409);
      if (await one(env, 'SELECT position FROM homepage_features WHERE artwork_id = ?', w.id)) throw new Bad('This work is in Contemporaryists in Focus; change that selection first', 409);
      await commit(env, [env.DB.prepare(`INSERT INTO artwork_placements (artwork_id, artist_id, gallery_id, state, proposed_by, proposed_at, closed_by, closed_at, updated_at)
        VALUES (?,?,'contemporary','withdrawn',?,?,?,?,?) ON CONFLICT(artwork_id, gallery_id) DO NOTHING`).bind(w.id, w.artist_id, founder, at, founder, at, at)], 0);
    } else if (action === 'restore') {
      if (!cur) throw new Bad('This work is already in Contemporary', 409);
      await commit(env, [env.DB.prepare("DELETE FROM artwork_placements WHERE artwork_id=? AND gallery_id='contemporary'").bind(w.id)], 0);
    } else throw new Bad('In Contemporary a work can only be taken out or put back', 409);
  } else if (action === 'place') {
    if (!(await isLive(env, w.artist_id, g))) throw new Bad(`The artist isn’t a member of ${TITLES[g]} yet`, 409);
    if (cur && ['founder_approved', 'live'].includes(cur.state)) throw new Bad('Already placed', 409);
    // Only the artist's CURRENT proposal counts as their acceptance; a declined, refused or withdrawn row starts afresh.
    const accepted = cur && cur.state === 'artist_accepted' ? cur.artist_accepted_at : null;
    await commit(env, [placementUpsert(env, w, g, { state: accepted ? 'live' : 'founder_approved', proposed_by: accepted ? cur.proposed_by : founder,
      founder_approved_by: founder, founder_approved_at: at, artist_accepted_at: accepted }, cur, true)], 0);
  } else if (action === 'refuse' || action === 'withdraw') {
    if (!cur || !(action === 'refuse' ? ['proposed', 'artist_accepted'] : [...OPEN_STATES, 'live']).includes(cur.state)) throw new Bad('Nothing to ' + action, 409);
    await commit(env, [env.DB.prepare(`UPDATE artwork_placements SET state=?, closed_by=?, closed_at=?, updated_at=? WHERE ${PLACE_CAS}`)
      .bind(action === 'refuse' ? 'refused' : 'withdrawn', founder, at, at, w.id, g, cur.state, cur.updated_at), unfeature(env, w, g)], 0);
  } else throw new Bad('Refused');
  await audit(env, founder, 'founder', 'artwork_placement_' + action, w.artist_id, { gallery: g, artwork: w.id });
  return placementView(env, w.artist_id);
}
export async function artistPlacement(env, artist, g, artworkId, action) {
  await need(env); newGallery(g);
  const w = await workOf(env, artworkId);
  if (w.artist_id !== artist.id) throw new Bad('No such artwork', 404);
  const cur = await placement(env, artworkId, g), at = now();
  if (action === 'propose') {
    if (!(await isLive(env, artist.id, g))) throw new Bad(`You aren’t a member of ${TITLES[g]} yet`, 409);
    if (cur && [...OPEN_STATES, 'live'].includes(cur.state)) throw new Bad('This is already in progress', 409);
    await commit(env, [placementUpsert(env, w, g, { state: 'artist_accepted', proposed_by: artist.email, artist_accepted_at: at }, cur, true)], 0);
  } else if (action === 'accept') {
    if (!cur || cur.state !== 'founder_approved') throw new Bad('There is nothing to accept', 409);
    await commit(env, [env.DB.prepare(`UPDATE artwork_placements SET state='live', artist_accepted_at=?, updated_at=? WHERE ${PLACE_CAS} AND ${LIVE}`)
      .bind(at, at, w.id, g, cur.state, cur.updated_at, artist.id, g)], 0);
  } else if (action === 'decline' || action === 'withdraw') {
    if (!cur || !(action === 'decline' ? ['founder_approved'] : [...OPEN_STATES, 'live']).includes(cur.state)) throw new Bad('Nothing to ' + action, 409);
    await commit(env, [env.DB.prepare(`UPDATE artwork_placements SET state=?, closed_by=?, closed_at=?, updated_at=? WHERE ${PLACE_CAS}`)
      .bind(action === 'decline' ? 'declined' : 'withdrawn', artist.email, at, at, w.id, g, cur.state, cur.updated_at), unfeature(env, w, g)], 0);
  } else throw new Bad('Refused');
  await audit(env, artist.email, 'artist', 'artwork_placement_' + action, artist.id, { gallery: g, artwork: w.id });
  return placementView(env, artist.id);
}
// Placements are always read through the artwork's own artist: a row whose artist does not match its artwork is ignored.
const PLACEMENTS = 'FROM artwork_placements p JOIN artworks w ON w.id = p.artwork_id AND w.artist_id = p.artist_id';
export async function placementView(env, artistId) {
  return { artist_id: artistId, placements: await all(env, `SELECT p.artwork_id, p.gallery_id, p.state, p.proposed_at, p.founder_approved_at, p.artist_accepted_at, p.closed_at ${PLACEMENTS} WHERE p.artist_id = ? ORDER BY p.gallery_id, p.artwork_id`, artistId) };
}

/* ---- who and what is in each gallery (published galleries only) ------------------------------------------------------ */
// published: [{artist_id, slug, display_name, works:[{id, slug, ...}]}] from featured.js (latest published version, shown works).
export async function contents(env, published) {
  const rows = await all(env, 'SELECT * FROM gallery_memberships');
  const pl = await all(env, `SELECT p.artwork_id, p.artist_id, p.gallery_id, p.state ${PLACEMENTS}`);
  const out = Object.fromEntries(GALLERIES.map(g => [g, { artists: [], works: [] }]));
  for (const a of published) {
    const mine = rows.filter(r => r.artist_id === a.artist_id);
    for (const g of GALLERIES) {
      const e = effective(mine, g);
      if (!e || e.state !== 'live') continue;
      const works = a.works.filter(w => g === 'contemporary'
        ? !pl.some(p => p.artwork_id === w.id && p.artist_id === a.artist_id && p.gallery_id === 'contemporary')
        : pl.some(p => p.artwork_id === w.id && p.artist_id === a.artist_id && p.gallery_id === g && p.state === 'live'));
      out[g].artists.push({ artist_id: a.artist_id, slug: a.slug, display_name: a.display_name, works: works.length });
      out[g].works.push(...works.map(w => ({ artist_id: a.artist_id, artist: a.slug, work: w.slug, artwork_id: w.id })));
    }
  }
  return out;
}
export async function readiness(env, published) {
  const s = await settings(env), c = published ? await contents(env, published) : null;
  return Object.fromEntries(GALLERIES.map(g => {
    const la = c ? c[g].artists.length : null, lw = c ? c[g].works.length : null;
    return [g, { ...s[g], live_artists: la, live_works: lw, ready: c ? la >= s[g].target_artists && lw >= s[g].target_works : null }];
  }));
}

/* ---- unrestricted order --------------------------------------------------------------------------------------------- */
export async function order(env, g) {
  gallery(g);
  return all(env, 'SELECT o.position, o.artist_id, a.slug, a.display_name FROM gallery_order o JOIN artists a ON a.id = o.artist_id WHERE o.gallery_id = ? ORDER BY o.position', g);
}
// Replace a gallery's order with the given artists, in order. Contemporary: positions from 26, and never an artist who
// already holds one of the 25 positions in gallery_positions (those stay exactly where they are).
export async function saveOrder(env, founder, g, body) {
  await need(env); gallery(g);
  if (!body || !Array.isArray(body.artists) || body.artists.length > 5000 || body.artists.some(x => typeof x !== 'string')) throw new Bad('Send the artists in order');
  if (new Set(body.artists).size !== body.artists.length) throw new Bad('Each artist appears once');
  const held = new Set(g === 'contemporary' ? (await all(env, 'SELECT artist_id FROM gallery_positions WHERE artist_id IS NOT NULL')).map(r => r.artist_id) : []);
  for (const id of body.artists) {
    if (held.has(id)) throw new Bad('That artist already holds one of the 25 Contemporary positions; those are set in Gallery order', 409);
    if (!(await isLive(env, id, g))) throw new Bad(`Only live members of ${TITLES[g]} can be ordered`, 409);
  }
  const base = g === 'contemporary' ? 26 : 1, at = now();
  const before = await order(env, g);
  await env.DB.batch([env.DB.prepare('DELETE FROM gallery_order WHERE gallery_id = ?').bind(g),
    ...body.artists.map((id, i) => env.DB.prepare('INSERT INTO gallery_order (gallery_id, position, artist_id, updated_at, updated_by) VALUES (?,?,?,?,?)').bind(g, base + i, id, at, founder))]);
  await audit(env, founder, 'founder', 'gallery_order', null, { gallery: g, before: before.map(r => r.artist_id), after: body.artists });
  return order(env, g);
}

/* ---- Artists in Focus for Spaces and Being --------------------------------------------------------------- */
export async function features(env, g) {
  newGallery(g);
  return all(env, 'SELECT position, artist_id, artwork_id, updated_at FROM gallery_features WHERE gallery_id = ? ORDER BY position', g);
}
export async function saveFeatures(env, founder, g, body, published) {
  await need(env); newGallery(g);
  if (!body || !Array.isArray(body.items) || body.items.length > FEATURE_MAX) throw new Bad(`Up to ${FEATURE_MAX} artists`);
  const c = (await contents(env, published))[g], seen = new Set();
  const items = body.items.map((it, n) => {
    if (!it || Object.keys(it).sort().join() !== 'artist_id,artwork_id') throw new Bad('Refused');
    if (seen.has(it.artist_id)) throw new Bad('Each artist can be featured once'); seen.add(it.artist_id);
    // the artwork must be THIS artist's own published work, placed live in this gallery (never another artist's work)
    if (!c.works.some(w => w.artist_id === it.artist_id && w.artwork_id === it.artwork_id))
      throw new Bad(`Choice ${n + 1} isn’t a published work placed in ${TITLES[g]}`, 409);
    return { position: n + 1, ...it };
  });
  const at = now(), before = await features(env, g);
  await env.DB.batch([env.DB.prepare('DELETE FROM gallery_features WHERE gallery_id = ?').bind(g),
    ...items.map(i => env.DB.prepare(`INSERT INTO gallery_features (gallery_id, position, artist_id, artwork_id, updated_at, updated_by)
      SELECT ?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM artworks w WHERE w.id = ? AND w.artist_id = ?) AND ${LIVE}`)
      .bind(g, i.position, i.artist_id, i.artwork_id, at, founder, i.artwork_id, i.artist_id, i.artist_id, g))]);
  await audit(env, founder, 'founder', 'gallery_features', null, { gallery: g, before: before.map(r => `${r.artist_id}/${r.artwork_id}`), after: items.map(r => `${r.artist_id}/${r.artwork_id}`) });
  return features(env, g);
}
// What is shown: only entries that are still a live member's own published work placed in that gallery.
async function shownFeatures(env, g, c) { return (await features(env, g)).filter(f => c[g].works.some(w => w.artist_id === f.artist_id && w.artwork_id === f.artwork_id)); }
async function shownOrder(env, g, c) { return (await order(env, g)).filter(o => c[g].artists.some(a => a.artist_id === o.artist_id)); }

/* ---- per-use image consent (append-only answers) -------------------------------------------------------------------- */
async function sha256(s) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join(''); }
function requestText(r) { return JSON.stringify({ scope: r.scope, gallery_id: r.gallery_id, artwork_ids: r.artwork_ids, purpose: r.purpose, channels: r.channels, valid_until: r.valid_until }); }
const today = () => now().slice(0, 10);
async function checkUse(env, body) {
  if (!body || !SCOPES.includes(body.scope)) throw new Bad('Choose what the image would be used for');
  if (body.gallery_id != null) gallery(body.gallery_id);
  const ids = body.artwork_ids;
  if (!Array.isArray(ids) || !ids.length || ids.length > 20 || ids.some(x => typeof x !== 'string') || new Set(ids).size !== ids.length) throw new Bad('Choose the artworks');
  const purpose = String(body.purpose || '').trim(), channels = String(body.channels || '').trim();
  if (purpose.length < 10 || purpose.length > 600) throw new Bad('Describe the use (10–600 characters)');
  if (channels.length < 2 || channels.length > 300) throw new Bad('Say where it would appear');
  if (body.valid_until != null && !/^\d{4}-\d{2}-\d{2}$/.test(body.valid_until)) throw new Bad('End date: YYYY-MM-DD');
  const a = await artistById(env, body.artist_id);
  for (const id of ids) { const w = await workOf(env, id); if (w.artist_id !== a.id) throw new Bad('Every artwork must be this artist’s own', 409); }
  return { artist_id: a.id, scope: body.scope, gallery_id: body.gallery_id || null, artwork_ids: JSON.stringify(ids), purpose, channels, valid_until: body.valid_until || null };
}
export async function requestConsent(env, founder, body) {
  await need(env);
  const u = await checkUse(env, body), id = rid('u'), at = now();
  if (u.valid_until && u.valid_until < today()) throw new Bad('The end date has already passed');
  await env.DB.prepare(`INSERT INTO image_use_requests (id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, request_text_sha256, status, requested_by, requested_at)
    VALUES (?,?,?,?,?,?,?,?,?,'open',?,?)`).bind(id, u.artist_id, u.scope, u.gallery_id, u.artwork_ids, u.purpose, u.channels, u.valid_until, await sha256(requestText(u)), founder, at).run();
  await audit(env, founder, 'founder', 'image_use_requested', u.artist_id, { request: id, scope: u.scope });
  return one(env, 'SELECT * FROM image_use_requests WHERE id = ?', id);
}
export async function cancelRequest(env, founder, id) {
  await need(env);
  const r = await one(env, "SELECT * FROM image_use_requests WHERE id = ? AND status = 'open'", id);
  if (!r) throw new Bad('No open request', 409);
  await commit(env, [env.DB.prepare("UPDATE image_use_requests SET status='cancelled', closed_at=? WHERE id=? AND status='open'").bind(now(), id)], 0);
  await audit(env, founder, 'founder', 'image_use_cancelled', r.artist_id, { request: id });
  return { cancelled: id };
}
/* An answer to an OPEN request: the consent row is copied from the request itself (never from what the caller sends), for that
   request's own artist only, and the request is closed in the same transaction. Two answers at once: one wins, the other gets
   a 409 and writes nothing. An expired request can no longer be answered. */
async function answerRequest(env, requestId, artistId, answer, method, by) {
  const r = await one(env, "SELECT * FROM image_use_requests WHERE id = ? AND status = 'open'" + (artistId ? ' AND artist_id = ?' : ''), ...(artistId ? [requestId, artistId] : [requestId]));
  if (!r) throw new Bad('No open request', 404);
  if (r.valid_until && r.valid_until < today()) throw new Bad('This request has expired; PlotArt would need to ask again', 409);
  const id = rid('c'), at = now();
  await commit(env, [
    env.DB.prepare(`INSERT INTO image_use_consents (id, request_id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, answer, method, request_text_sha256, recorded_by, created_at)
      SELECT ?, r.id, r.artist_id, r.scope, r.gallery_id, r.artwork_ids, r.purpose, r.channels, r.valid_until, ?, ?, r.request_text_sha256, ?, ? FROM image_use_requests r
      WHERE r.id = ? AND r.artist_id = ? AND r.status = 'open'`).bind(id, answer, method, by, at, r.id, r.artist_id),
    env.DB.prepare("UPDATE image_use_requests SET status='answered', closed_at=? WHERE id=? AND status='open' AND EXISTS (SELECT 1 FROM image_use_consents WHERE id = ? AND request_id = ?)").bind(at, r.id, id, r.id)], 0);
  return { r, id };
}
/* The artist answers in the Studio (yes or no; optional, nothing changes if they never answer). */
export async function answerConsent(env, artist, requestId, body) {
  await need(env);
  if (!body || !['yes', 'no'].includes(body.answer)) throw new Bad('Answer yes or no');
  const { r, id } = await answerRequest(env, requestId, artist.id, body.answer, 'studio', artist.email);
  await audit(env, artist.email, 'artist', 'image_use_answered', artist.id, { request: r.id, consent: id, answer: body.answer });
  return { consent: id, answer: body.answer };
}
/* The artist withdraws a permission they gave: a new 'no' for exactly the same use (the earlier 'yes' stays on record). */
export async function withdrawConsent(env, artist, consentId) {
  await need(env);
  const c = await one(env, 'SELECT * FROM image_use_consents WHERE id = ? AND artist_id = ?', consentId, artist.id);
  if (!c) throw new Bad('No such permission', 404);
  const id = rid('c');
  await env.DB.prepare(`INSERT INTO image_use_consents (id, request_id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, answer, method, request_text_sha256, recorded_by, created_at)
    VALUES (?,?,?,?,?,?,?,?,?,'no','studio',?,?,?)`).bind(id, c.request_id, c.artist_id, c.scope, c.gallery_id, c.artwork_ids, c.purpose, c.channels, c.valid_until, c.request_text_sha256, artist.email, now()).run();
  await audit(env, artist.email, 'artist', 'image_use_withdrawn', artist.id, { consent: id, withdraws: c.id });
  return { consent: id, answer: 'no' };
}
/* The founder records an answer the artist gave by email (the request is the same per-use request). */
export async function recordEmailConsent(env, founder, body) {
  await need(env);
  if (!body || !['yes', 'no'].includes(body.answer)) throw new Bad('Record yes or no');
  if (body.request_id) {
    if (body.artist_id !== undefined) {   // a stated artist must be the request's own artist
      const r = await one(env, 'SELECT artist_id FROM image_use_requests WHERE id = ?', body.request_id);
      if (r && r.artist_id !== body.artist_id) throw new Bad('That request belongs to another artist', 409);
    }
    const { r, id } = await answerRequest(env, body.request_id, null, body.answer, 'email_logged_by_founder', founder);
    await audit(env, founder, 'founder', 'image_use_recorded', r.artist_id, { request: r.id, consent: id, answer: body.answer });
    return { consent: id, answer: body.answer };
  }
  const u = await checkUse(env, body), id = rid('c');
  if (body.answer === 'yes' && u.valid_until && u.valid_until < today()) throw new Bad('The end date has already passed');
  await env.DB.prepare(`INSERT INTO image_use_consents (id, request_id, artist_id, scope, gallery_id, artwork_ids, purpose, channels, valid_until, answer, method, request_text_sha256, recorded_by, created_at)
    VALUES (?,NULL,?,?,?,?,?,?,?,?,'email_logged_by_founder',?,?,?)`).bind(id, u.artist_id, u.scope, u.gallery_id, u.artwork_ids, u.purpose, u.channels, u.valid_until, body.answer, await sha256(requestText(u)), founder, now()).run();
  await audit(env, founder, 'founder', 'image_use_recorded', u.artist_id, { consent: id, answer: body.answer });
  return { consent: id, answer: body.answer };
}
/* Is this use allowed now? Every condition must hold:
   - the artwork exists and is THIS artist's own, and the artist's account is active;
   - for a use in a gallery, the artist is a live member of that gallery today;
   - among the artist's answers for this scope that cover this artwork (and this gallery, or every gallery), the LATEST is a
     'yes' whose end date has not passed. A later 'no' (a withdrawal) always wins; cancelled or unanswered requests count for
     nothing; a 'yes' for one gallery never covers another. */
export async function consentFor(env, artistId, artworkId, scope, { gallery: g = null, on = today() } = {}) {
  if (!(await installed(env)) || !SCOPES.includes(scope)) return false;
  const w = await one(env, 'SELECT w.artist_id, a.account_status FROM artworks w JOIN artists a ON a.id = w.artist_id WHERE w.id = ?', artworkId);
  if (!w || w.artist_id !== artistId || w.account_status !== 'active') return false;
  if (g !== null && !(GALLERIES.includes(g) && (await isLive(env, artistId, g)))) return false;
  const rows = await all(env, 'SELECT * FROM image_use_consents WHERE artist_id = ? AND scope = ? ORDER BY created_at DESC, rowid DESC', artistId, scope);
  const latest = rows.find(r => JSON.parse(r.artwork_ids).includes(artworkId) && (r.gallery_id === null || r.gallery_id === g));
  return !!latest && latest.answer === 'yes' && (!latest.valid_until || latest.valid_until >= on);
}
export async function consentsView(env, artistId) {
  return { requests: await all(env, 'SELECT * FROM image_use_requests WHERE artist_id = ? ORDER BY requested_at DESC', artistId),
    answers: await all(env, 'SELECT * FROM image_use_consents WHERE artist_id = ? ORDER BY created_at DESC', artistId) };
}

/* ---- views ---------------------------------------------------------------------------------------------------------- */
export async function adminView(env, published) {
  if (!(await installed(env))) return { installed: false, galleries: GALLERIES.map(g => ({ gallery_id: g, title: TITLES[g], ...DEFAULTS[g] })) };
  const c = await contents(env, published), r = await readiness(env, published);
  return { installed: true, galleries: await Promise.all(GALLERIES.map(async g => ({ ...r[g], members: c[g].artists, order: await shownOrder(env, g, c),
    features: g === 'contemporary' ? null : await shownFeatures(env, g, c) }))),
    memberships: await all(env, 'SELECT m.*, a.display_name, a.slug FROM gallery_memberships m JOIN artists a ON a.id = m.artist_id ORDER BY m.gallery_id, a.display_name'),
    placements: await all(env, `SELECT p.* ${PLACEMENTS} ORDER BY p.gallery_id, p.artist_id`),
    open_requests: await all(env, "SELECT * FROM image_use_requests WHERE status = 'open' ORDER BY requested_at") };
}
export async function artistView(env, artist) {
  await need(env);
  return { ...(await membershipView(env, artist.id)), ...(await placementView(env, artist.id)), ...(await consentsView(env, artist.id)) };
}
/* For the publishing pipeline (Phase E): public identifiers only, and only what is valid now. */
export async function pipeline(env, published) {
  if (!(await installed(env))) return { installed: false };
  const c = await contents(env, published), s = await settings(env);
  return { installed: true, galleries: await Promise.all(GALLERIES.map(async g => ({ gallery: g, status: s[g].status,
    artists: c[g].artists.map(a => a.slug), works: c[g].works.map(w => ({ artist: w.artist, work: w.work })),
    order: (await shownOrder(env, g, c)).map(o => ({ position: o.position, artist: o.slug })),
    features: g === 'contemporary' ? null : (await shownFeatures(env, g, c)).map(f => ({ position: f.position, artist_id: f.artist_id, artwork_id: f.artwork_id })) }))) };
}
