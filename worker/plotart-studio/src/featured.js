/* PlotArt Studio · Featured Artists (founder brief 17 Nov 2026: the curated showcase moves from the PlotArt homepage into
   the Artists' Gallery). Reuses the homepage curation of the same day and its migration 0016 (table homepage_features)
   unchanged: no new table, no data migration.

   The founder chooses up to six published ARTISTS, each represented by one of their published artworks that the founder
   chooses (never picked automatically), and their order. Each artist appears once. Founder-only editorial data: this
   module writes the homepage_features table and the audit trail and NOTHING else. It never changes an artwork, image,
   price, availability, an artist's own order of works, the gallery order, a Founding position or any permission.
   Only what is already published can be chosen: an artist whose latest publication is live, and a work in that published
   version whose availability is shown publicly and which has a main photograph. Anything that stops being published drops
   out by itself, here and (independently) on the website, which renders the section only from published galleries.

   Earlier homepage records: rows saved with kind 'artwork' (a single featured artwork) are read as the artist they belong
   to, shown with that artwork; if an artist appears in more than one earlier row, only the first (lowest position) is
   used. Nothing is rewritten until the founder saves; every new save stores kind 'artist'. */
import { Bad, now } from './lib.js';

export const MAX = 6;
export const INTRO_MAX = 240;   // as atlas-tools/plotart_featured.INTRO_MAX
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

/* The short introduction the gallery page shows (atlas-tools/plotart_featured.intro, mirrored for the founder's preview):
   whole sentences from the start of the published biography, verbatim, up to INTRO_MAX characters. */
export function intro(bio) {
  if (typeof bio !== 'string' || !bio.trim()) return '';
  const paras = bio.trim().split(/\n\s*\n/).map(p => p.replace(/\s+/g, ' ').trim()).filter(Boolean);
  while (paras.length > 1 && paras[0].split(' ').length <= 3 && !/[.!?]$/.test(paras[0])) paras.shift();
  const para = paras[0];
  let out = '';
  for (const s of para.split(/(?<=[.!?])\s+(?=[A-ZÀ-ɏ"'‘“(])/)) {
    if (out.length + s.length + (out ? 1 : 0) > INTRO_MAX) break;
    out = out ? out + ' ' + s : s;
  }
  if (out) return out;
  return para.slice(0, INTRO_MAX).replace(/\s+\S*$/, '').replace(/[,;:—–\- ]+$/, '') + '…';
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
      return main ? { id: w.id, slug: w.slug, title: w.title || 'Untitled', year: w.year || null, availability: w.availability,
        image: { id: main.id, width: main.width, height: main.height, alt: main.alt || '' } } : null;
    }).filter(Boolean);
    const a = s.artist || {};
    return { artist_id: r.id, slug: r.slug, display_name: r.display_name, practice: a.practice || null, intro: intro(a.bio), works };
  }).filter(a => a.works.length);
}

// Every item names the artist and the artwork shown; it must still be in the artist's published gallery, or it is not shown.
function resolve(item, galleries) {
  const g = galleries.find(x => x.artist_id === item.artist_id);
  const w = g && g.works.find(x => x.id === item.artwork_id);
  return w ? { artist_id: g.artist_id, artwork_id: w.id, slug: g.slug, display_name: g.display_name, practice: g.practice, intro: g.intro, work: w } : null;
}

export async function view(env, visibleSql) {
  if (!(await installed(env))) return { installed: false, max: MAX, items: [], galleries: [] };
  const galleries = await published(env, visibleSql);
  const saved = await all(env, 'SELECT position, kind, artist_id, artwork_id, updated_at FROM homepage_features ORDER BY position');
  const seen = new Set();
  const items = saved.map(s => {
    const repeat = seen.has(s.artist_id); seen.add(s.artist_id);
    // an earlier homepage record naming an artist already featured above is not shown again (each artist appears once)
    return { position: s.position, artist_id: s.artist_id, artwork_id: s.artwork_id, updated_at: s.updated_at, earlier_kind: s.kind,
      repeat, shown: repeat ? null : resolve(s, galleries) };
  });
  return { installed: true, max: MAX, items, galleries };
}

/* Replace the whole selection (the founder arranges it in the Review Desk, previews it, then saves once). */
export async function save(env, founder, body, visibleSql) {
  if (!(await installed(env))) throw new Bad('Featured Artists isn’t set up yet', 409);
  if (!body || typeof body !== 'object' || Object.keys(body).join() !== 'items' || !Array.isArray(body.items)) throw new Bad('Refused');
  if (body.items.length > MAX) throw new Bad(`Up to ${MAX} featured artists`);
  const galleries = await published(env, visibleSql);
  const seen = new Set();
  const items = body.items.map((it, n) => {
    if (!it || typeof it !== 'object') throw new Bad('Refused');
    const keys = Object.keys(it).sort().join();
    if (!['artist_id,artwork_id', 'artist_id,artwork_id,kind'].includes(keys) || ('kind' in it && it.kind !== 'artist')
        || typeof it.artist_id !== 'string' || typeof it.artwork_id !== 'string') throw new Bad('Refused');
    const r = resolve(it, galleries);
    if (!r) throw new Bad(`Artist ${n + 1} or the chosen artwork isn’t in a published gallery any more. Reload and choose again.`, 409);
    if (seen.has(it.artist_id)) throw new Bad(`${r.display_name} is chosen twice. Each artist can be featured once.`);
    seen.add(it.artist_id);
    return { position: n + 1, kind: 'artist', artist_id: it.artist_id, artwork_id: it.artwork_id };
  });
  const before = await all(env, 'SELECT position, kind, artist_id, artwork_id FROM homepage_features ORDER BY position');
  const brief = rows => rows.map(r => `${r.kind}:${r.artist_id}/${r.artwork_id}`);
  if (JSON.stringify(brief(before)) === JSON.stringify(brief(items))) return { changed: false };
  const at = now();
  await env.DB.batch([env.DB.prepare('DELETE FROM homepage_features'),
    ...items.map(i => env.DB.prepare('INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?,?,?,?,?)')
      .bind(i.position, i.kind, i.artist_id, i.artwork_id, at))]);
  await audit(env, founder, 'featured_artists', { before: brief(before), after: brief(items) });
  return { changed: true };
}

/* For the publishing pipeline: public identifiers only (gallery address and artwork id), each artist once, and only items
   still published. The website renders Featured Artists in the Artists' Gallery from these. */
export async function pipeline(env, visibleSql) {
  if (!(await installed(env))) return { installed: false, items: [] };
  const v = await view(env, visibleSql);
  return { installed: true, items: v.items.filter(i => i.shown).map(i => ({ artist: i.shown.slug, work: i.artwork_id })) };
}

/* The founder's preview may load ONLY the main photograph of a work that can be featured. */
export async function previewable(env, imageId, visibleSql) {
  const galleries = await published(env, visibleSql);
  if (!galleries.some(g => g.works.some(w => w.image.id === imageId))) return null;
  return one(env, 'SELECT * FROM images WHERE id = ? AND deleted_at IS NULL', imageId);
}
