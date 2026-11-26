/* PlotArt Studio · Unified gallery curation (founder approval for development, 26 Nov 2026; migration 0029).
   One manually curated arrangement per gallery (Contemporary, Spaces, Being), replacing the three separate controls
   (Gallery Showcase, Artists in Focus, Gallery order) in the founder's Studio:
     - positions 1-3 are the opening row (stored in gallery_showcase, migration 0028: an artwork is always chosen);
     - positions 4 onwards are everyone else (stored in gallery_curation, migration 0029: the artwork is optional;
       none chosen = the artist's first eligible published artwork).
   Each artist appears once per gallery. Draft and published are separate stages: saving writes the draft rows of BOTH
   tables in one database batch, Publish copies both drafts to published in one batch, so a move between the opening row
   and the rest is never half-saved. Routine artist publications only READ the published stage.
   Rules (founder decisions 26 Nov 2026):
     - opening row: an ineligible choice leaves the place empty on the public page, with a prominent notice (no
       substitution), exactly as the Gallery Showcase;
     - positions 4+: the artist keeps their place; a sold or withdrawn choice shows the artist's first eligible
       alternative instead, with a notice; with no eligible work, the card is shown without an artwork image;
     - a newly published member who is not in the arrangement is added at the end (never in the opening row, never
       displacing anyone), with a notice;
     - an internal test account never appears; Spaces and Being are published only while open.
   Historical data (homepage_features, gallery_features, gallery_positions, gallery_order) is kept and never written here. */
import { Bad, now } from './lib.js';
import * as G from './galleries.js';
import * as SC from './showcase.js';
import * as T from './test-artists.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();
const OPEN = 3;
async function audit(env, actor, action, detail) {
  await env.DB.prepare('INSERT INTO audit (at, actor, role, action, artist_id, detail) VALUES (?,?,?,?,?,?)')
    .bind(now(), actor, 'founder', action, null, JSON.stringify(detail).slice(0, 4000)).run();
}
export async function installed(env) {
  try { await env.DB.prepare('SELECT 1 FROM gallery_curation LIMIT 1').all(); return await SC.installed(env); } catch { return false; }
}
async function need(env) { if (!(await installed(env))) throw new Bad('Gallery curation isn’t installed yet (migration 0029)', 503); }
const gallery = g => { if (!G.GALLERIES.includes(g)) throw new Bad('Unknown gallery'); return g; };

/* The gallery's members who can appear (published, live members, never a test account), each with their works in that
   gallery and which of them are eligible as a representative artwork (published, shown, available, main photograph). */
async function members(env, g, published) {
  const c = (await G.contents(env, published))[g];
  const inGallery = new Set(c.works.map(w => `${w.artist_id}:${w.artwork_id}`));
  const out = new Map();
  for (const m of c.artists) {
    if (T.isTest(env, m.artist_id)) continue;
    const p = published.find(x => x.artist_id === m.artist_id);
    if (!p) continue;
    const works = p.works.filter(w => inGallery.has(`${p.artist_id}:${w.id}`))
      .map(w => ({ artwork_id: w.id, title: w.title, year: w.year, image: w.image, availability: w.availability, eligible: w.availability === 'available' && !!w.image }));
    out.set(p.artist_id, { artist_id: p.artist_id, slug: p.slug, display_name: p.display_name, practice: p.practice, works });
  }
  return out;
}

async function stored(env, g, stage) {
  const open = await all(env, 'SELECT position, artist_id, artwork_id FROM gallery_showcase WHERE gallery_id = ? AND stage = ? ORDER BY position', g, stage);
  const rest = await all(env, 'SELECT position, artist_id, artwork_id FROM gallery_curation WHERE gallery_id = ? AND stage = ? ORDER BY position', g, stage);
  return [...open.map(r => ({ ...r, opening: true })), ...rest.map(r => ({ ...r, opening: false }))];
}

/* One stored row explained for the founder: what the public page shows for it, and why. */
async function explain(env, g, r, mem, published) {
  const m = mem.get(r.artist_id);
  const named = m ? m.display_name : ((await one(env, 'SELECT display_name FROM artists WHERE id = ?', r.artist_id)) || {}).display_name || '';
  const base = { position: r.position, opening: r.opening, artist_id: r.artist_id, artwork_id: r.artwork_id || null, display_name: named };
  const chosen = m && r.artwork_id ? m.works.find(w => w.artwork_id === r.artwork_id) : null;
  const chosenTitle = chosen ? chosen.title : r.artwork_id ? ((await one(env, 'SELECT title FROM artworks WHERE id = ?', r.artwork_id)) || {}).title || 'Untitled' : null;
  if (r.opening) {
    const ok = !!(chosen && chosen.eligible);
    return { ...base, title: chosenTitle, shown: ok ? chosen : null, notice: ok ? null : await SC.reason(env, g, r, published) };
  }
  if (!m) return { ...base, title: chosenTitle, shown: null, hidden: true, notice: T.isTest(env, r.artist_id) ? 'an internal test account is never shown' : 'not shown: the artist’s gallery is not published in this gallery' };
  if (chosen && chosen.eligible) return { ...base, title: chosen.title, shown: chosen, notice: null };
  const first = m.works.find(w => w.eligible) || null;
  const why = r.artwork_id ? `“${chosenTitle}” is ${chosen ? String(chosen.availability).replace(/_/g, ' ') : 'withdrawn or not published'}` : null;
  return { ...base, title: chosenTitle, shown: first, automatic: !r.artwork_id,
    notice: why ? (first ? `${why}: showing “${first.title}” instead until you choose again` : `${why} and no other work is available: shown without an artwork image`)
      : first ? null : 'no available work: shown without an artwork image' };
}

/* The arrangement for one stage as the page would show it: stored rows explained, then members not yet placed (added at
   the end, never in the opening row). */
async function arrangement(env, g, stage, mem, published) {
  const rows = await stored(env, g, stage), out = [];
  for (const r of rows) out.push(await explain(env, g, r, mem, published));
  const placed = new Set(rows.map(r => r.artist_id));
  let next = Math.max(OPEN, ...rows.map(r => r.position)) + 1;
  for (const m of mem.values()) if (!placed.has(m.artist_id))
    out.push({ ...(await explain(env, g, { position: next++, artist_id: m.artist_id, artwork_id: null, opening: false }, mem, published)), new: true,
      notice: 'newly published: added at the end until you place them' });
  return out;
}

export async function view(env, published) {
  if (!(await installed(env))) return { installed: false };
  const s = await G.settings(env), out = [];
  for (const g of G.GALLERIES) {
    const mem = await members(env, g, published);
    const draft = await arrangement(env, g, 'draft', mem, published), pub = await arrangement(env, g, 'published', mem, published);
    const key = a => JSON.stringify(a.filter(x => !x.new).map(x => [x.artist_id, x.artwork_id, x.opening]));
    out.push({ gallery_id: g, title: G.TITLES[g], status: s[g].status, draft, published: pub, unpublished_changes: key(draft) !== key(pub),
      notices: s[g].status === 'open' ? pub.filter(x => x.notice && !x.hidden).map(x => ({ position: x.position, opening: x.opening, display_name: x.display_name, title: x.title, notice: x.notice })) : [],
      artists: [...mem.values()].sort((a, b) => a.display_name.localeCompare(b.display_name, 'en-IE')) });
  }
  return { installed: true, opening: OPEN, galleries: out };
}

/* Save the founder's arrangement as the draft: an ordered list of { artist_id, artwork_id | null }. The first three are
   the opening row and need an eligible artwork; the rest may leave the artwork to the default. Never publishes. */
export async function saveDraft(env, founder, g, body, published) {
  await need(env); gallery(g);
  const list = body && Array.isArray(body.items) ? body.items : null;
  if (!list || list.length > 2000) throw new Bad('Send the arrangement as a list of artists');
  const mem = await members(env, g, published), elig = await SC.eligible(env, g, published), seen = new Set();
  // a choice already on record for that artist (now sold or withdrawn) may be kept as it is: the page shows their first
  // available work meanwhile, and the founder chooses again when she wishes
  const kept = new Set((await all(env, 'SELECT artist_id, artwork_id FROM gallery_curation WHERE gallery_id = ? AND artwork_id IS NOT NULL', g)).map(r => `${r.artist_id}:${r.artwork_id}`));
  const items = list.map((it, i) => {
    const artist = String(it && it.artist_id || ''), work = it && it.artwork_id ? String(it.artwork_id) : null;
    if (!/^a[0-9a-z]+$/.test(artist) || (work && !/^w[0-9a-z]+$/.test(work))) throw new Bad('Each place needs an artist (and, optionally, one of their artworks)');
    if (seen.has(artist)) throw new Bad('Each artist can appear only once in a gallery');
    seen.add(artist);
    T.refuse(env, artist, 'it never appears in a gallery.');
    const m = mem.get(artist);
    if (!m) throw new Bad(`An artist in position ${i + 1} isn’t a published member of ${G.TITLES[g]}`, 409);
    if (i < OPEN) {
      const e = work && elig.get(work);
      if (!e || e.artist_id !== artist) throw new Bad(`Position ${i + 1} is in the opening row: choose an available artwork by ${m.display_name}`, 409);
    } else if (work) {
      const w = m.works.find(x => x.artwork_id === work);
      if ((!w || !w.eligible) && !kept.has(`${artist}:${work}`)) throw new Bad(`The artwork chosen for ${m.display_name} isn’t available in ${G.TITLES[g]}: choose another, or leave it to their first available work`, 409);
    }
    return { position: i + 1, artist_id: artist, artwork_id: work };
  });
  const at = now();
  // one batch: both drafts are replaced together (a move between the opening row and the rest is never half-saved)
  await env.DB.batch([
    env.DB.prepare("DELETE FROM gallery_curation WHERE gallery_id = ? AND stage = 'draft'").bind(g),
    env.DB.prepare("DELETE FROM gallery_showcase WHERE gallery_id = ? AND stage = 'draft'").bind(g),
    ...items.filter(x => x.position <= OPEN).map(x => env.DB.prepare(`INSERT INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      VALUES (?, 'draft', ?, ?, ?, ?, ?)`).bind(g, x.position, x.artist_id, x.artwork_id, at, founder)),
    ...items.filter(x => x.position > OPEN).map(x => env.DB.prepare(`INSERT INTO gallery_curation (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      VALUES (?, 'draft', ?, ?, ?, ?, ?)`).bind(g, x.position, x.artist_id, x.artwork_id, at, founder))]);
  await audit(env, founder, 'gallery_curation_draft_saved', { gallery: g, items: items.map(x => [x.position, x.artist_id, x.artwork_id]) });
  return view(env, published);
}

/* Publish: only an open gallery; every opening-row choice must be eligible now (positions 4+ never block: their default
   applies). Both published stages are replaced from the drafts in one batch; the caller then starts publishing. */
export async function publish(env, founder, g, published) {
  await need(env); gallery(g);
  const st = (await G.settings(env))[g].status;
  if (st !== 'open') throw new Bad(`${G.TITLES[g]} is ${st.replace('_', ' ')}: its arrangement can be prepared, but it is published only once the gallery is open`, 409);
  const elig = await SC.eligible(env, g, published);
  const open = await all(env, "SELECT position, artist_id, artwork_id FROM gallery_showcase WHERE gallery_id = ? AND stage = 'draft' ORDER BY position", g);
  if (!open.length) throw new Bad('Save the arrangement first: the opening row is empty', 409);
  const bad = open.filter(d => { const e = elig.get(d.artwork_id); return !e || e.artist_id !== d.artist_id || T.isTest(env, d.artist_id); });
  if (bad.length) throw new Bad(`Not published: opening position${bad.length > 1 ? 's' : ''} ${bad.map(b => b.position).join(' and ')} ${bad.length > 1 ? 'are' : 'is'} no longer eligible. Choose again and save.`, 409);
  const at = now();
  await env.DB.batch([
    env.DB.prepare("DELETE FROM gallery_curation WHERE gallery_id = ? AND stage = 'published'").bind(g),
    env.DB.prepare("DELETE FROM gallery_showcase WHERE gallery_id = ? AND stage = 'published'").bind(g),
    env.DB.prepare(`INSERT INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      SELECT gallery_id, 'published', position, artist_id, artwork_id, ?, ? FROM gallery_showcase WHERE gallery_id = ? AND stage = 'draft'`).bind(at, founder, g),
    env.DB.prepare(`INSERT INTO gallery_curation (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
      SELECT gallery_id, 'published', position, artist_id, artwork_id, ?, ? FROM gallery_curation WHERE gallery_id = ? AND stage = 'draft'`).bind(at, founder, g)]);
  await audit(env, founder, 'gallery_curation_published', { gallery: g, opening: open.map(d => [d.position, d.artwork_id]) });
  return view(env, published);
}

/* What the publishing pipeline receives, for each OPEN gallery: the opening row (eligible published positions only: an
   ineligible place is absent, never filled) and the rest in order, each with the founder's chosen artwork when it is
   eligible, else null (the page then shows the artist's first eligible work). Gallery addresses and artwork ids only.
   Published members not named here are appended by the page at the end. */
export async function pipeline(env, published) {
  if (!(await installed(env))) return { installed: false };
  const s = await G.settings(env), out = [];
  for (const g of G.GALLERIES) {
    if (s[g].status !== 'open') { out.push({ gallery: g, status: s[g].status, opening: [], rest: [], held: [] }); continue; }
    const mem = await members(env, g, published), elig = await SC.eligible(env, g, published);
    const rows = await stored(env, g, 'published');
    const opening = rows.filter(r => r.opening).filter(r => { const e = elig.get(r.artwork_id); return e && e.artist_id === r.artist_id && mem.has(r.artist_id); })
      .map(r => ({ position: r.position, artist: mem.get(r.artist_id).slug, work: r.artwork_id }));
    const rest = rows.filter(r => !r.opening && mem.has(r.artist_id)).map(r => {
      const m = mem.get(r.artist_id), w = r.artwork_id && m.works.find(x => x.artwork_id === r.artwork_id && x.eligible);
      return { artist: m.slug, work: w ? w.artwork_id : null };
    });
    // artists who hold an opening place whose work is not eligible now: their place stays empty and they are not
    // appended below either (the founder decides; nothing moves automatically)
    const held = rows.filter(r => r.opening && mem.has(r.artist_id) && !opening.some(o => o.position === r.position)).map(r => mem.get(r.artist_id).slug);
    out.push({ gallery: g, status: s[g].status, opening, rest, held });
  }
  return { installed: true, galleries: out };
}
