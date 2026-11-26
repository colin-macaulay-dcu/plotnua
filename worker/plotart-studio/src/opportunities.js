/* PlotArt Studio · Opportunities & delivery (development 13 Nov 2026). NOT DEPLOYED.
   An artist's own expression of interest in future opportunities, where their artwork is based and how it could reach a
   venue. Stored in artist_opportunities (migration 0009), one row per artist; NO row means "not answered yet".
   It is an expression of interest only. This module writes artist_opportunities and the audit trail and nothing else:
   never artists, artworks, artwork_hire, agreements, image permissions, the gallery, the enquiry log or any mailer. */
import { Bad, now } from './lib.js';
import * as R from './opportunities-rules.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
async function audit(env, actor, role, action, artistId, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, role, action, artistId || null, detail ? JSON.stringify(detail).slice(0, 4000) : null).run();
}

export async function installed(env) {
  try { await env.DB.prepare('SELECT 1 FROM artist_opportunities LIMIT 1').all(); return true; } catch { return false; }
}
/* Migration 0010 adds care_condition and the 2,000-character practical_note. Until it has run, the Studio keeps working
   exactly as before (280-character note, no care question). */
export async function careInstalled(env) {
  try { await env.DB.prepare('SELECT care_condition, practical_note FROM artist_opportunities LIMIT 1').all(); return true; } catch { return false; }
}
// The newest note: a Studio from before 0010 writes "note"; this Studio writes "practical_note" and clears "note". So a
// note in "note" is either the one 0010 copied (identical) or a newer one written by the older Studio after 0010 ran.
const parse = r => r ? { interests: JSON.parse(r.interests), artwork_county: r.artwork_county, transport: JSON.parse(r.transport),
  coverage_mode: r.coverage_mode, coverage_counties: JSON.parse(r.coverage_counties), care_condition: r.care_condition === 1,
  note: r.note ?? r.practical_note ?? null, created_at: r.created_at, updated_at: r.updated_at,
  // shown publicly (0015): null = not decided, true = shown, false = private; absent columns (before 0015) read as not decided
  public_display: r.public_display === 1 ? true : r.public_display === 0 ? false : null, public_decided_at: r.public_decided_at ?? null, public_notice: r.public_notice ?? null,
  placement_area: r.placement_area ?? null } : null;

/* Migration 0015 adds public_display, public_decided_at and public_notice. Until it has run, nothing can be shown publicly
   and the Studio works exactly as before. */
/* Migration 0027 (Report 36): placement_area and the separate specialist-transport answer. */
export async function placementInstalled(env) {
  try { await env.DB.prepare('SELECT placement_area FROM artist_opportunities LIMIT 1').all(); return true; } catch { return false; }
}
export async function publicInstalled(env) {
  try { await env.DB.prepare('SELECT public_display, public_decided_at, public_notice FROM artist_opportunities LIMIT 1').all(); return true; } catch { return false; }
}
/* The kinds of opportunity this artist has chosen to show (empty unless they chose to show them). The ONLY part of their
   answers that ever leaves the Studio, and only inside their approved gallery. */
export async function publicFor(env, artistId) {
  if (!(await installed(env)) || !(await publicInstalled(env))) return [];
  return R.publicKeys(parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artistId)));
}

const OPTIONS = { interests: R.INTERESTS, transport: R.TRANSPORT, transport_clash: R.TRANSPORT_CLASH, provinces: R.PROVINCES, coverage: R.COVERAGE, note_max: R.NOTE_MAX };
const options = (care, pub, v27 = false) => ({ ...(care ? { ...OPTIONS, care: R.CARE } : { ...OPTIONS, note_max: R.NOTE_MAX_BEFORE_0010, care: null }),
  public: pub ? { ...R.PUBLIC, keys: R.PUBLIC_KEYS, notice: R.PUBLIC_NOTICE } : null,
  ...(v27 ? { transport: R.TRANSPORT_27, transport_clash: R.TRANSPORT_CLASH_27, placement_area: R.PLACEMENT_AREA, v27: true } : { v27: false }) });

/* The artist's own record only. "suggested_county" is the county on their own profile, offered as a starting point for
   "Where is your artwork based?" until they first save: it is never stored unless they save it. */
/* For the Studio dashboard's discreet prompt: 'unanswered', 'answered', or null before migration 0009 has run. */
export async function status(env, artist) {
  if (!(await installed(env))) return null;
  const row = parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id));
  if (!row) return 'unanswered';
  // 'confirm': answers saved before 0015 that include something that could be shown, and no choice made yet
  if ((await publicInstalled(env)) && row.public_display === null && R.PUBLIC_KEYS.some(k => row.interests.includes(k))) return 'confirm';
  return 'answered';
}
export async function artistView(env, artist) {
  if (!(await installed(env))) return { installed: false };
  const row = parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id));
  const prof = await one(env, 'SELECT county FROM artists WHERE id = ?', artist.id);
  return { installed: true, saved: row, suggested_county: !row && prof && R.COUNTIES.includes(prof.county) ? prof.county : null,
    options: options(await careInstalled(env), await publicInstalled(env), await placementInstalled(env)), shown: R.publicKeys(row) };
}

export async function save(env, artist, body) {
  if (!(await installed(env))) throw new Bad('This section isn’t available yet', 409);
  const care = await careInstalled(env), pub = await publicInstalled(env), v27 = await placementInstalled(env);
  const v = R.validate(body, { ...(care ? {} : { noteMax: R.NOTE_MAX_BEFORE_0010, care: false }), publicOn: pub, v27 });
  if (v.error) throw new Bad(v.error);
  const p = v.prefs, at = now();
  const had = await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id);
  // "Same as my general delivery" needs a general delivery area to follow (any area, including an artist abroad's own
  // country); "No delivery" or "By arrangement" has none.
  if (p.placement_area === 'general') {
    const g = await one(env, 'SELECT scope FROM artist_delivery WHERE artist_id = ?', artist.id).catch(() => null);
    if (!g || g.scope === 'none') throw new Bad('“Same as my general delivery” needs a delivery area in your Profile first (“Delivering to buyers and hirers”).');
  }
  // With 'general' the artist's own placement area is kept exactly as stored (restored if they choose 'own' again).
  const keepOwn = p.placement_area === 'general';
  // Shown publicly: only an explicit true/false from the form that explained it changes the choice. Absent keeps what is
  // there (a new answer without it stays "not decided", so nothing is ever shown that the artist wasn't told about).
  const chose = pub && p.public_display !== undefined;
  const cols = ['artist_id', 'interests', 'artwork_county', 'transport', ...(keepOwn && had ? [] : ['coverage_mode', 'coverage_counties']), 'note', ...(care ? ['practical_note', 'care_condition'] : []),
    ...(v27 && p.placement_area !== undefined ? ['placement_area'] : []),
    ...(chose ? ['public_display', 'public_decided_at', 'public_notice'] : []), 'created_at', 'updated_at', 'updated_by'];
  const vals = [artist.id, JSON.stringify(p.interests), p.artwork_county, JSON.stringify(p.transport), ...(keepOwn && had ? [] : [p.coverage_mode, JSON.stringify(p.coverage_counties)]),
    care ? null : p.note, ...(care ? [p.note, p.care_condition ? 1 : 0] : []), ...(v27 && p.placement_area !== undefined ? [p.placement_area] : []), ...(chose ? [p.public_display ? 1 : 0, at, R.PUBLIC_NOTICE] : []),
    had ? had.created_at : at, at, artist.email];
  const upd = cols.filter(c => !['artist_id', 'created_at'].includes(c)).map(c => `${c}=excluded.${c}`).join(', ');
  await env.DB.prepare(`INSERT INTO artist_opportunities (${cols.join(', ')}) VALUES (${cols.map(() => '?').join(',')}) ON CONFLICT(artist_id) DO UPDATE SET ${upd}`)
    .bind(...vals).run();
  // The audit trail records that preferences were saved and which options, never the free-text note.
  await audit(env, artist.email, 'artist', had ? 'opportunities_updated' : 'opportunities_saved', artist.id,
    { interests: p.interests, artwork_county: p.artwork_county, transport: p.transport, coverage: keepOwn ? 'general' : p.coverage_mode, ...(p.placement_area !== undefined ? { placement_area: p.placement_area } : {}), counties: p.coverage_counties.length, care_condition: p.care_condition, note: !!p.note,
      ...(chose ? { public_display: p.public_display, notice: R.PUBLIC_NOTICE } : {}) });
  const saved = parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id));
  return { saved, shown: R.publicKeys(saved) };
}

/* The one-click choice (an artist who answered before 0015, or anyone changing their mind later): show or keep private.
   Changes public_display only; every answer is kept exactly as it is. */
export async function setVisibility(env, artist, show) {
  if (!(await installed(env)) || !(await publicInstalled(env))) throw new Bad('This choice isn’t available yet', 409);
  if (typeof show !== 'boolean') throw new Bad('Choose to show your opportunities or keep them private');
  const row = await one(env, 'SELECT public_display FROM artist_opportunities WHERE artist_id = ?', artist.id);
  if (!row) throw new Bad('Save your opportunities first', 409);
  const at = now();
  await env.DB.prepare('UPDATE artist_opportunities SET public_display=?, public_decided_at=?, public_notice=? WHERE artist_id=?').bind(show ? 1 : 0, at, R.PUBLIC_NOTICE, artist.id).run();
  await audit(env, artist.email, 'artist', show ? 'opportunities_shown' : 'opportunities_kept_private', artist.id, { notice: R.PUBLIC_NOTICE, before: row.public_display });
  const saved = parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id));
  return { saved, shown: R.publicKeys(saved), changed: row.public_display !== (show ? 1 : 0) };
}

/* The founder confirms an agreement obtained in person (see R.FOUNDER_NOTICE). Only for answers still "not confirmed"
   (NULL); only the visibility columns change; the interests sent must equal the saved ones, so nothing stale is shown. */
export async function founderConfirm(env, founder, b) {
  if (!(await installed(env)) || !(await publicInstalled(env))) throw new Bad('This choice isn’t available yet', 409);
  if (!b || typeof b !== 'object' || Object.keys(b).sort().join() !== 'artist_id,confirm,interests' || b.confirm !== true
    || typeof b.artist_id !== 'string' || !Array.isArray(b.interests)) throw new Bad('Refused');
  const a = await one(env, 'SELECT id, display_name FROM artists WHERE id = ?', b.artist_id);
  const row = await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', b.artist_id);
  if (!a || !row) throw new Bad('No saved answers for this artist', 404);
  if (row.public_display !== null) throw new Bad('The artist has already made this choice themselves', 409);
  const saved = parse(row);
  if (JSON.stringify(saved.interests) !== JSON.stringify(b.interests)) throw new Bad('Their answers have changed since this page loaded. Reload and check again.', 409);
  const keys = R.publicKeys({ ...saved, public_display: true });
  if (!keys.length) throw new Bad('Nothing they chose can be shown publicly', 409);
  const at = now();
  const r = await env.DB.prepare('UPDATE artist_opportunities SET public_display=1, public_decided_at=?, public_notice=? WHERE artist_id=? AND public_display IS NULL')
    .bind(at, R.FOUNDER_NOTICE, a.id).run();
  if (!r.meta || r.meta.changes !== 1) throw new Bad('The artist has already made this choice themselves', 409);
  await audit(env, founder, 'founder', 'opportunities_shown_founder_confirmed', a.id, { notice: R.FOUNDER_NOTICE, statement: R.founderStatement(a.display_name), shown: keys, interests: saved.interests });
  return { artist_id: a.id, shown: keys };
}

/* The founder's read-only view: every invited or active artist, answered or not, plus any ended artist whose answers are
   still held. Filtering happens in the Review Desk; nothing here can change an artist's answers. */
export async function adminView(env) {
  if (!(await installed(env))) return { installed: false, items: [] };
  const rows = await all(env, `SELECT a.id, a.display_name, a.slug, a.account_status, a.founding, a.founding_number, o.*
    FROM artists a LEFT JOIN artist_opportunities o ON o.artist_id = a.id
    WHERE a.account_status IN ('invited', 'active') OR o.artist_id IS NOT NULL
    ORDER BY a.display_name COLLATE NOCASE`);
  const items = rows.map(r => ({ id: r.id, display_name: r.display_name, slug: r.slug, account_status: r.account_status, founding_number: r.founding_number,
    prefs: r.artist_id ? parse(r) : null }));
  const answered = items.filter(i => i.prefs), online = answered.filter(i => i.prefs.interests.includes('online_only'));
  const by = Object.fromEntries(Object.keys(R.INTERESTS).map(k => [k, answered.filter(i => i.prefs.interests.includes(k)).length]));
  const pub = await publicInstalled(env);
  return { installed: true, items, totals: { artists: items.length, answered: answered.length, unanswered: items.length - answered.length, online_only: online.length,
      care_condition: answered.filter(i => i.prefs.care_condition).length, by_interest: by,
      ...(pub ? { shown: answered.filter(i => i.prefs.public_display === true).length, kept_private: answered.filter(i => i.prefs.public_display === false).length,
        undecided: answered.filter(i => i.prefs.public_display === null).length } : {}) },
    options: { ...options(await careInstalled(env), pub, await placementInstalled(env)), interest_short: R.INTEREST_SHORT,
      transport_short: (await placementInstalled(env)) ? R.TRANSPORT_SHORT_27 : R.TRANSPORT_SHORT, counties: R.COUNTIES } };
}

/* Retention: the answers are the artist's own profile content, so they go with the first-stage deletion (12 months after
   participation ends, or sooner on request) and, as a backstop, with the six-year deletion. */
export async function eraseFor(env, artistId) {
  if (!(await installed(env))) return 0;
  const r = await env.DB.prepare('DELETE FROM artist_opportunities WHERE artist_id = ?').bind(artistId).run();
  return r.meta?.changes || 0;
}
export async function recordTables(env) { return (await installed(env)) ? ['artist_opportunities'] : []; }
