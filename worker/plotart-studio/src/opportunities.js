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
const parse = r => r ? { interests: JSON.parse(r.interests), artwork_county: r.artwork_county, transport: JSON.parse(r.transport),
  coverage_mode: r.coverage_mode, coverage_counties: JSON.parse(r.coverage_counties), note: r.note, created_at: r.created_at, updated_at: r.updated_at } : null;

const OPTIONS = { interests: R.INTERESTS, transport: R.TRANSPORT, transport_clash: R.TRANSPORT_CLASH, provinces: R.PROVINCES, coverage: R.COVERAGE, note_max: R.NOTE_MAX };

/* The artist's own record only. "suggested_county" is the county on their own profile, offered as a starting point for
   "Where is your artwork based?" until they first save: it is never stored unless they save it. */
export async function artistView(env, artist) {
  if (!(await installed(env))) return { installed: false };
  const row = parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id));
  const prof = await one(env, 'SELECT county FROM artists WHERE id = ?', artist.id);
  return { installed: true, saved: row, suggested_county: !row && prof && R.COUNTIES.includes(prof.county) ? prof.county : null, options: OPTIONS };
}

export async function save(env, artist, body) {
  if (!(await installed(env))) throw new Bad('This section isn’t available yet', 409);
  const v = R.validate(body);
  if (v.error) throw new Bad(v.error);
  const p = v.prefs, at = now();
  const had = await one(env, 'SELECT created_at FROM artist_opportunities WHERE artist_id = ?', artist.id);
  await env.DB.prepare(`INSERT INTO artist_opportunities (artist_id, interests, artwork_county, transport, coverage_mode, coverage_counties, note, created_at, updated_at, updated_by)
      VALUES (?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(artist_id) DO UPDATE SET interests=excluded.interests, artwork_county=excluded.artwork_county, transport=excluded.transport,
        coverage_mode=excluded.coverage_mode, coverage_counties=excluded.coverage_counties, note=excluded.note, updated_at=excluded.updated_at, updated_by=excluded.updated_by`)
    .bind(artist.id, JSON.stringify(p.interests), p.artwork_county, JSON.stringify(p.transport), p.coverage_mode, JSON.stringify(p.coverage_counties), p.note,
      had ? had.created_at : at, at, artist.email).run();
  // The audit trail records that preferences were saved and which options, never the free-text note.
  await audit(env, artist.email, 'artist', had ? 'opportunities_updated' : 'opportunities_saved', artist.id,
    { interests: p.interests, artwork_county: p.artwork_county, transport: p.transport, coverage: p.coverage_mode, counties: p.coverage_counties.length, note: !!p.note });
  return { saved: parse(await one(env, 'SELECT * FROM artist_opportunities WHERE artist_id = ?', artist.id)) };
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
  return { installed: true, items, totals: { artists: items.length, answered: answered.length, unanswered: items.length - answered.length, online_only: online.length, by_interest: by },
    options: { ...OPTIONS, interest_short: R.INTEREST_SHORT, transport_short: R.TRANSPORT_SHORT, counties: R.COUNTIES } };
}

/* Retention: the answers are the artist's own profile content, so they go with the first-stage deletion (12 months after
   participation ends, or sooner on request) and, as a backstop, with the six-year deletion. */
export async function eraseFor(env, artistId) {
  if (!(await installed(env))) return 0;
  const r = await env.DB.prepare('DELETE FROM artist_opportunities WHERE artist_id = ?').bind(artistId).run();
  return r.meta?.changes || 0;
}
export async function recordTables(env) { return (await installed(env)) ? ['artist_opportunities'] : []; }
