/* PlotArt Studio · Homepage curation (founder brief 17 Nov 2026; migration 0016). The founder chooses up to six featured
   artworks or artists for the PlotArt homepage and their order. A featured artist is always represented by one of their
   published artworks that the founder chooses (never picked automatically); the card links to the artist's gallery. Founder-only editorial data: this module writes the
   homepage_features table and the audit trail and NOTHING else. It never changes an artwork, image, price, availability,
   an artist's own order of works, the gallery order or any permission.
   Only what is already published can be chosen: an artist whose latest publication is live, and a work in that published
   version whose availability is shown publicly and which has a main photograph. Anything that stops being published drops
   out by itself, here and (independently) on the website, which renders the section only from published galleries. */
import { Bad, now } from './lib.js';

export const MAX = 6;
const SHOWN = new Set(['available', 'reserved', 'sold', 'not_for_sale']);   // as atlas-tools/plotart_gallery_pages.SHOWN
const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
async function audit(env, actor, action, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, 'founder', action, null, JSON.stringify(detail)).run();
}

export async function installed(env) {
  return !!(await one(env, "SELECT name FROM sqlite_master WHERE type='table' AND name='homepage_features'"));
}

/* The published galleries: for each visible artist (index.js VISIBLE_SQL), the works of their latest published version that
   the public gallery shows, each with its main photograph. */
export async function published(env, visibleSql) {
  const rows = await all(env, `SELECT a.id, a.slug, a.display_name, v.snapshot FROM artists a
    JOIN publish_queue q ON q.artist_id = a.id AND q.status IN ('exporting','published') AND q.kind <> 'remove'
      AND q.version = (SELECT MAX(q2.version) FROM publish_queue q2 WHERE q2.artist_id = a.id AND q2.status IN ('exporting','published'))
    JOIN versions v ON v.artist_id = a.id AND v.version = q.version
    WHERE a.id IN (${visibleSql}) ORDER BY a.display_name COLLATE NOCASE`);
  return rows.map(r => {
    const s = JSON.parse(r.snapshot);
    const works = (s.works || []).filter(w => SHOWN.has(w.availability)).map(w => {
      const main = (w.images || []).find(i => i.role === 'main');
      return main ? { id: w.id, slug: w.slug, title: w.title || 'Untitled', availability: w.availability,
        image: { id: main.id, width: main.width, height: main.height, alt: main.alt || '' } } : null;
    }).filter(Boolean);
    return { artist_id: r.id, slug: r.slug, display_name: r.display_name, practice: (s.artist || {}).practice || null, works };
  }).filter(a => a.works.length);
}

// Both kinds name the artwork shown; it must still be in the artist's published gallery, or the item is not shown.
function resolve(item, galleries) {
  const g = galleries.find(x => x.artist_id === item.artist_id);
  const w = g && g.works.find(x => x.id === item.artwork_id);
  return w ? { kind: item.kind, artist_id: g.artist_id, artwork_id: w.id, slug: g.slug, display_name: g.display_name, practice: g.practice, work: w } : null;
}

export async function view(env, visibleSql) {
  if (!(await installed(env))) return { installed: false, max: MAX, items: [], galleries: [] };
  const galleries = await published(env, visibleSql);
  const saved = await all(env, 'SELECT position, kind, artist_id, artwork_id, updated_at FROM homepage_features ORDER BY position');
  const items = saved.map(s => ({ position: s.position, kind: s.kind, artist_id: s.artist_id, artwork_id: s.artwork_id, updated_at: s.updated_at,
    shown: resolve(s, galleries) }));
  return { installed: true, max: MAX, items, galleries };
}

/* Replace the whole selection (the founder arranges it in the Review Desk, then saves once). */
export async function save(env, founder, body, visibleSql) {
  if (!(await installed(env))) throw new Bad('Homepage curation isn’t set up yet', 409);
  if (!body || typeof body !== 'object' || Object.keys(body).join() !== 'items' || !Array.isArray(body.items)) throw new Bad('Refused');
  if (body.items.length > MAX) throw new Bad(`Up to ${MAX} featured items`);
  const galleries = await published(env, visibleSql);
  const seen = new Set();
  const items = body.items.map((it, n) => {
    if (!it || typeof it !== 'object') throw new Bad('Refused');
    const keys = Object.keys(it).sort().join();
    if (!['artwork', 'artist'].includes(it.kind) || keys !== 'artist_id,artwork_id,kind' || typeof it.artist_id !== 'string' || typeof it.artwork_id !== 'string') throw new Bad('Refused');
    const r = resolve({ kind: it.kind, artist_id: it.artist_id, artwork_id: it.artwork_id }, galleries);
    if (!r) throw new Bad(`Item ${n + 1} isn’t in a published gallery any more. Reload and choose again.`, 409);
    const key = it.kind === 'artist' ? 'artist:' + it.artist_id : 'artwork:' + it.artist_id + ':' + it.artwork_id;   // an artist is featured once
    if (seen.has(key)) throw new Bad(`Item ${n + 1} is chosen twice`);
    seen.add(key);
    return { position: n + 1, kind: it.kind, artist_id: it.artist_id, artwork_id: it.artwork_id };
  });
  const before = await all(env, 'SELECT position, kind, artist_id, artwork_id FROM homepage_features ORDER BY position');
  const brief = rows => rows.map(r => `${r.kind}:${r.artist_id}/${r.artwork_id}`);
  if (JSON.stringify(brief(before)) === JSON.stringify(brief(items))) return { changed: false };
  const at = now();
  await env.DB.batch([env.DB.prepare('DELETE FROM homepage_features'),
    ...items.map(i => env.DB.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?,?,?,?,?)')
      .bind(i.position, i.kind, i.artist_id, i.artwork_id, at))]);
  await audit(env, founder, 'homepage_features', { before: brief(before), after: brief(items) });
  return { changed: true };
}

/* For the publishing pipeline: public identifiers only (kind, gallery address and artwork id), and only items still published. */
export async function pipeline(env, visibleSql) {
  if (!(await installed(env))) return { installed: false, items: [] };
  const v = await view(env, visibleSql);
  return { installed: true, items: v.items.filter(i => i.shown).map(i => ({ kind: i.kind, artist: i.shown.slug, work: i.artwork_id })) };
}

/* The founder's preview may load ONLY the main photograph of a work that can be featured. */
export async function previewable(env, imageId, visibleSql) {
  const galleries = await published(env, visibleSql);
  if (!galleries.some(g => g.works.some(w => w.image.id === imageId))) return null;
  return one(env, 'SELECT * FROM images WHERE id = ? AND deleted_at IS NULL', imageId);
}
