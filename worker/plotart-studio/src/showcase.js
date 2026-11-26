/* PlotArt Studio · Gallery Showcase (Report 37, development 26 Nov 2026). NOT DEPLOYED.
   The three opening artworks of each gallery page (left, centre, right), chosen by the founder. Independent of Artists in
   Focus (homepage_features / gallery_features) and of Gallery order (gallery_positions / gallery_order): this module
   reads those never and writes only gallery_showcase and the audit trail.
   - draft and published are separate stages (migration 0028). Saving a draft never publishes; "Publish showcase" copies
     the draft to published and starts the protected publishing workflow. Routine artist publications only READ the
     published stage: nothing but the founder's Publish ever changes it.
   - Eligible: a published, shown artwork with a main photograph, available (not sold, reserved or not for sale), by an
     artist who is a live member of that gallery, placed in it (Spaces and Being) or not taken out of it (Contemporary),
     and never an internal test account. The publishing pipeline receives only the eligible published positions.
   - A published choice that stops being eligible stays on record; the Review Desk names the vacant position, the artwork
     and the reason. Nothing is ever substituted.
   - Spaces and Being can be prepared as drafts, but a showcase is published only while its gallery is open. */
import { Bad, now } from './lib.js';
import * as G from './galleries.js';
import * as T from './test-artists.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
const POS = { 1: 'Left', 2: 'Centre', 3: 'Right' };
export const POSITIONS = POS;
async function audit(env, actor, action, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, 'founder', action, null, JSON.stringify(detail).slice(0, 4000)).run();
}
export async function installed(env) {
  try { await env.DB.prepare('SELECT 1 FROM gallery_showcase LIMIT 1').all(); return (await G.installed(env)); } catch { return false; }
}
async function need(env) { if (!(await installed(env))) throw new Bad('The Gallery Showcase isn’t installed yet (migration 0028)', 503); }
const gallery = g => { if (!G.GALLERIES.includes(g)) throw new Bad('Unknown gallery'); return g; };

/* Every work in the artist's latest published version, with its state, so a vacancy can be explained. */
async function latestPublished(env, artistId) {
  const r = await one(env, `SELECT v.snapshot FROM publish_queue q JOIN versions v ON v.artist_id = q.artist_id AND v.version = q.version
    WHERE q.artist_id = ? AND q.status IN ('exporting','published') ORDER BY q.version DESC LIMIT 1`, artistId);
  if (!r) return null;
  const q = await one(env, "SELECT kind FROM publish_queue WHERE artist_id = ? AND status IN ('exporting','published') ORDER BY version DESC LIMIT 1", artistId);
  return q && q.kind === 'remove' ? null : JSON.parse(r.snapshot);
}

/* Eligible works for one gallery: { artwork_id -> { artist_id, slug, display_name, title, year, availability, image } }. */
export async function eligible(env, g, published) {
  const c = (await G.contents(env, published))[g];
  const inGallery = new Set(c.works.map(w => `${w.artist_id}:${w.artwork_id}`));
  const out = new Map();
  for (const a of published) {
    if (T.isTest(env, a.artist_id)) continue;
    for (const w of a.works) {
      if (w.availability !== 'available' || !w.image || !inGallery.has(`${a.artist_id}:${w.id}`)) continue;
      out.set(w.id, { artist_id: a.artist_id, slug: a.slug, display_name: a.display_name, artwork_id: w.id, title: w.title, year: w.year, image: w.image });
    }
  }
  return out;
}

/* Why a chosen work is not eligible now (plain words for the founder). */
async function reason(env, g, row, published) {
  if (T.isTest(env, row.artist_id)) return 'it belongs to an internal test account';
  const art = await one(env, 'SELECT display_name, account_status FROM artists WHERE id = ?', row.artist_id);
  if (!art || !['active', 'invited'].includes(art.account_status)) return 'the artist is no longer taking part';
  if (!published.some(a => a.artist_id === row.artist_id)) return 'the artist’s gallery is not published';
  const snap = await latestPublished(env, row.artist_id);
  const w = snap && snap.works.find(x => x.id === row.artwork_id);
  if (!w) return 'the artwork has been withdrawn or is not published';
  if (w.availability === 'sold') return 'the artwork has been sold';
  if (w.availability !== 'available') return `the artwork is no longer available (${String(w.availability).replace(/_/g, ' ')})`;
  if (!(w.images || []).some(i => i.role === 'main')) return 'the artwork has no main photograph';
  return g === 'contemporary' ? 'the artist or the artwork is no longer in Contemporary' : `the artist or the artwork is no longer in ${G.TITLES[g]}`;
}

async function stage(env, g, st, published, elig) {
  const rows = await all(env, 'SELECT position, artist_id, artwork_id, updated_at, updated_by FROM gallery_showcase WHERE gallery_id = ? AND stage = ? ORDER BY position', g, st);
  const out = [];
  for (const r of rows) {
    const e = elig.get(r.artwork_id);
    const ok = !!e && e.artist_id === r.artist_id;
    const w = await one(env, 'SELECT title FROM artworks WHERE id = ?', r.artwork_id), a = await one(env, 'SELECT display_name FROM artists WHERE id = ?', r.artist_id);
    out.push({ position: r.position, side: POS[r.position], artist_id: r.artist_id, artwork_id: r.artwork_id, eligible: ok, reason: ok ? null : await reason(env, g, r, published),
      title: ok ? e.title : (w && w.title) || 'Untitled', display_name: ok ? e.display_name : (a && a.display_name) || '', image: ok ? e.image : null, updated_at: r.updated_at, updated_by: r.updated_by });
  }
  return out;
}

/* The founder's view: for each gallery, its status, the draft, the published showcase (with vacancies explained) and the
   eligible works to choose from, grouped by artist. */
export async function view(env, published) {
  if (!(await installed(env))) return { installed: false };
  const s = await G.settings(env), out = [];
  for (const g of G.GALLERIES) {
    const elig = await eligible(env, g, published);
    const draft = await stage(env, g, 'draft', published, elig), pub = await stage(env, g, 'published', published, elig);
    const artists = [];
    for (const e of elig.values()) {
      let a = artists.find(x => x.artist_id === e.artist_id);
      if (!a) artists.push(a = { artist_id: e.artist_id, display_name: e.display_name, works: [] });
      a.works.push({ artwork_id: e.artwork_id, title: e.title, year: e.year, image: e.image });
    }
    artists.sort((x, y) => x.display_name.localeCompare(y.display_name, 'en-IE'));
    const same = JSON.stringify(draft.map(d => [d.position, d.artwork_id])) === JSON.stringify(pub.map(d => [d.position, d.artwork_id]));
    out.push({ gallery_id: g, title: G.TITLES[g], status: s[g].status, draft, published: pub, vacant: pub.filter(p => !p.eligible), unpublished_changes: !same, artists });
  }
  return { installed: true, positions: POS, galleries: out };
}

function items(body) {
  const list = body && Array.isArray(body.items) ? body.items : null;
  if (!list || list.length > 3) throw new Bad('Choose up to three artworks: left, centre and right');
  const seenP = new Set(), seenW = new Set();
  return list.map(it => {
    const position = Number(it && it.position), artist = String(it && it.artist_id || ''), work = String(it && it.artwork_id || '');
    if (!POS[position] || seenP.has(position)) throw new Bad('Each position (left, centre, right) can be used once');
    if (!/^a[0-9a-z]+$/.test(artist) || !/^w[0-9a-z]+$/.test(work)) throw new Bad('Choose an artist and one of their artworks');
    if (seenW.has(work)) throw new Bad('An artwork can appear only once in a showcase');
    seenP.add(position); seenW.add(work);
    return { position, artist_id: artist, artwork_id: work };
  });
}

/* Save the draft (never publishes). Every chosen work must be eligible for that gallery now, and belong to that artist. */
export async function saveDraft(env, founder, g, body, published) {
  await need(env); gallery(g);
  const list = items(body);
  const elig = await eligible(env, g, published);
  for (const it of list) {
    T.refuse(env, it.artist_id, 'it never appears in a Gallery Showcase.');
    const e = elig.get(it.artwork_id);
    if (!e || e.artist_id !== it.artist_id) throw new Bad(`The ${POS[it.position].toLowerCase()} choice isn’t eligible for ${G.TITLES[g]}: choose a published, available artwork by a member of this gallery`, 409);
  }
  const at = now();
  await env.DB.batch([env.DB.prepare("DELETE FROM gallery_showcase WHERE gallery_id = ? AND stage = 'draft'").bind(g),
    ...list.map(it => env.DB.prepare(`INSERT INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      VALUES (?, 'draft', ?, ?, ?, ?, ?)`).bind(g, it.position, it.artist_id, it.artwork_id, at, founder))]);
  await audit(env, founder, 'gallery_showcase_draft_saved', { gallery: g, items: list.map(i => [i.position, i.artwork_id]) });
  return view(env, published);
}

/* Publish: only an open gallery, only a draft whose every position is eligible now; the draft becomes the published
   showcase in one batch. The caller then starts the protected publishing workflow. */
export async function publish(env, founder, g, published) {
  await need(env); gallery(g);
  if ((await G.settings(env))[g].status !== 'open') throw new Bad(`${G.TITLES[g]} is ${(await G.settings(env))[g].status.replace('_', ' ')}: its showcase can be prepared, but it is published only once the gallery is open`, 409);
  const elig = await eligible(env, g, published);
  const draft = await all(env, "SELECT position, artist_id, artwork_id FROM gallery_showcase WHERE gallery_id = ? AND stage = 'draft' ORDER BY position", g);
  if (!draft.length) throw new Bad('Save a showcase first: there is nothing to publish', 409);
  const bad = draft.filter(d => { const e = elig.get(d.artwork_id); return !e || e.artist_id !== d.artist_id || T.isTest(env, d.artist_id); });
  if (bad.length) throw new Bad(`Not published: the ${bad.map(b => POS[b.position].toLowerCase()).join(' and ')} choice${bad.length > 1 ? 's are' : ' is'} no longer eligible. Choose again and save.`, 409);
  const at = now();
  await env.DB.batch([env.DB.prepare("DELETE FROM gallery_showcase WHERE gallery_id = ? AND stage = 'published'").bind(g),
    ...draft.map(d => env.DB.prepare(`INSERT INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      VALUES (?, 'published', ?, ?, ?, ?, ?)`).bind(g, d.position, d.artist_id, d.artwork_id, at, founder))]);
  await audit(env, founder, 'gallery_showcase_published', { gallery: g, items: draft.map(d => [d.position, d.artwork_id]) });
  return view(env, published);
}

/* What the publishing pipeline receives: for each OPEN gallery, its published positions that are eligible now (gallery
   address and artwork id only). An ineligible position is simply absent: the page leaves the place out, never fills it. */
export async function pipeline(env, published) {
  if (!(await installed(env))) return { installed: false };
  const s = await G.settings(env), out = [];
  for (const g of G.GALLERIES) {
    if (s[g].status !== 'open') { out.push({ gallery: g, status: s[g].status, items: [] }); continue; }
    const elig = await eligible(env, g, published);
    const rows = await all(env, "SELECT position, artist_id, artwork_id FROM gallery_showcase WHERE gallery_id = ? AND stage = 'published' ORDER BY position", g);
    out.push({ gallery: g, status: s[g].status, items: rows.filter(r => { const e = elig.get(r.artwork_id); return e && e.artist_id === r.artist_id; })
      .map(r => ({ position: r.position, artist: elig.get(r.artwork_id).slug, work: r.artwork_id })) });
  }
  return { installed: true, galleries: out };
}
