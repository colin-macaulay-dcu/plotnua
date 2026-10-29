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
import { artistBody, artworkBody, previewPage, shown } from './render.js';
import * as A from './assets.js';

const { Bad, now, rid } = L;
const SEC = {
  'Content-Security-Policy': "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin', 'Cache-Control': 'no-store',
};
const res = (body, type, status = 200, extra = {}) => new Response(body, { status, headers: { 'Content-Type': type, ...SEC, ...extra } });
const json = (o, status = 200) => res(JSON.stringify(o), 'application/json; charset=utf-8', status);
const html = (h, status = 200) => res(h, 'text/html; charset=utf-8', status);

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
  const licenceOk = d.artist.licence_version === L.LICENCE_VERSION;
  const problems = L.readiness(snap, { founding: !!d.artist.founding, firstPublication: !lv, licenceOk: true, imageBlocks: blocked(d.images) });
  const belowMinimum = !!(lv && d.artist.founding && snap.works.length < L.FOUNDING_MIN_WORKS);
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
    problems, licence_ok: licenceOk, licence_version: L.LICENCE_VERSION, below_minimum: belowMinimum,
    counts: { works: snap.works.length, archived: d.works.filter(w => w.archived).length, min: d.artist.founding ? L.FOUNDING_MIN_WORKS : 0 },
  };
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
  await audit(env, actor, 'artist', 'instant_change', artist.id, { what, version: v });
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
  const licence = d.artist.licence_version === L.LICENCE_VERSION || body.accept_licence === true;
  const problems = L.readiness(snap, { founding: !!d.artist.founding, firstPublication: !lv, licenceOk: licence, imageBlocks: blocked(d.images) });
  if (problems.length) return json({ ok: false, problems }, 422);
  if (d.artist.licence_version !== L.LICENCE_VERSION) {      // recorded only with a successful submission
    await env.DB.prepare('UPDATE artists SET licence_version=?, licence_accepted_at=?, updated_at=? WHERE id=?').bind(L.LICENCE_VERSION, now(), now(), artist.id).run();
    await audit(env, artist.email, 'artist', 'licence_accepted', artist.id, { version: L.LICENCE_VERSION });
  }
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
  const fix = i => i && { ...i, pw: dims[i.id]?.width, ph: dims[i.id]?.height };
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
async function overview(env) {
  const artists = await all(env, 'SELECT id, slug, email, display_name, founding, account_status, licence_version, first_published_at, application_ref, created_at FROM artists ORDER BY created_at');
  const out = [];
  for (const a of artists) {
    const st = await status(env, a);
    out.push({ ...a, state: st.state, works: st.counts.works, min: st.counts.min, problems: st.problems.length, below_minimum: st.below_minimum, live_version: st.live_version, latest_version: st.latest_version });
  }
  const subs = await all(env, `SELECT s.id, s.artist_id, s.created_at, s.tier, s.note, a.display_name FROM submissions s JOIN artists a ON a.id = s.artist_id
    WHERE s.status = 'pending' ORDER BY (s.tier = 'light'), s.created_at`);
  const queue = await all(env, `SELECT q.*, a.display_name FROM publish_queue q JOIN artists a ON a.id = q.artist_id WHERE q.status IN ('awaiting_founder','ready','exporting','failed') ORDER BY q.created_at`);
  const flags = await all(env, `SELECT i.id, i.artist_id, a.display_name, i.sha256 FROM images i JOIN artists a ON a.id=i.artist_id WHERE i.deleted_at IS NULL AND i.checks LIKE '%DUPLICATE_OF_OTHER_ARTIST%'`);
  return { artists: out, submissions: subs, queue, flags, f25: { selected_with_studio: artists.filter(a => a.founding).length, target: 25 },
    instant_autopublish: env.INSTANT_AUTOPUBLISH === 'true' };
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
  const g = L.exportGallery(snap, { version: q.version, approvedAt: v.created_at, licenceVersion: artist.licence_version,
    licenceAcceptedAt: artist.licence_accepted_at, artistId: artist.id, aiDecisions: v.ai_decisions ? JSON.parse(v.ai_decisions) : {} });
  const ids = [...snap.works.flatMap(w => w.images.map(i => i.id)), ...(snap.artist.portrait ? [snap.artist.portrait.id] : [])];
  return { gallery: g, images: ids, kind: q.kind };
}

/* ---------------------------------------------------------------- router */
export default {
  async fetch(req, env) {
    try { return await route(req, env); }
    catch (e) {
      if (e instanceof Bad) return json({ ok: false, error: e.message }, e.status);
      console.error(e);
      return json({ ok: false, error: 'Something went wrong. Your work is saved up to your last successful change.' }, 500);
    }
  },
};

async function route(req, env) {
  const url = new URL(req.url), p = url.pathname, m = req.method;
  // static assets (public, no data)
  const asset = { '/assets/studio.css': [A.STUDIO_CSS, 'text/css'], '/assets/plotart.css': [A.PLOTART_CSS, 'text/css'],
    '/assets/studio.js': [A.STUDIO_JS, 'text/javascript'], '/assets/admin.js': [A.ADMIN_JS, 'text/javascript'],
    '/assets/plotnua-mark.svg': [A.MARK_SVG, 'image/svg+xml'] }[p];
  if (asset && m === 'GET') return res(asset[0], asset[1] + '; charset=utf-8', 200, { 'Cache-Control': 'public, max-age=300' });

  // the publishing pipeline: bearer token, never a browser
  if (p.startsWith('/api/pipeline/')) {
    if (!env.PIPELINE_TOKEN || req.headers.get('Authorization') !== `Bearer ${env.PIPELINE_TOKEN}`) return json({ ok: false }, 401);
    if (p === '/api/pipeline/queue' && m === 'GET') return json({ ok: true, items: await all(env, "SELECT * FROM publish_queue WHERE status='ready' ORDER BY created_at") });
    let mm;
    if ((mm = p.match(/^\/api\/pipeline\/export\/(q[0-9a-z]+)$/)) && m === 'POST') {
      const q = await one(env, "SELECT * FROM publish_queue WHERE id = ? AND status IN ('ready','exporting')", mm[1]);
      if (!q) throw new Bad('Not ready', 409);
      await env.DB.prepare("UPDATE publish_queue SET status='exporting', updated_at=? WHERE id=?").bind(now(), q.id).run();
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
        await env.DB.prepare("UPDATE publish_queue SET status='superseded', updated_at=? WHERE artist_id=? AND status='published' AND version<?").bind(now(), q.artist_id, q.version).run();
        await env.DB.prepare('UPDATE artists SET first_published_at=COALESCE(first_published_at, ?), updated_at=? WHERE id=?').bind(now(), now(), q.artist_id).run();
      }
      await audit(env, 'pipeline', 'pipeline', ok ? 'published' : 'publish_failed', q.artist_id, { queue: q.id, version: q.version, detail: b.detail });
      return json({ ok: true });
    }
    return json({ ok: false }, 404);
  }

  const me = await who(req, env);
  if (me.role === 'none') {
    if (p.startsWith('/api/')) return json({ ok: false, error: me.email ? 'Your PlotArt Studio access isn’t active. Please contact hello@plotnua.ie.' : 'Please sign in.' }, me.email ? 403 : 401);
    return html(A.SIGNED_OUT_HTML.replace('{msg}', me.email ? 'Your PlotArt Studio access isn’t active. If you think this is a mistake, contact hello@plotnua.ie.' : 'Please sign in through PlotArt Studio.'), me.email ? 403 : 401);
  }
  if (m !== 'GET') {
    // same-origin only: a custom header cannot be sent cross-site without a CORS preflight, which this Worker never grants
    if (req.headers.get('X-Studio') !== '1') return json({ ok: false, error: 'Refused' }, 403);
    const o = req.headers.get('Origin');
    if (o && o !== url.origin) return json({ ok: false, error: 'Refused' }, 403);
  }

  /* ---- founder */
  if (p === '/admin' || p.startsWith('/admin/') || p.startsWith('/api/admin/')) {
    if (me.role !== 'founder') return p.startsWith('/api/') ? json({ ok: false, error: 'Not available' }, 403) : html('Not available', 403);
    if (p === '/admin' || p === '/admin/') return html(A.ADMIN_HTML);
    let mm;
    if ((mm = p.match(/^\/admin\/preview\/(s[0-9a-z]+|v-([0-9a-z]+)-(\d+))\/(.*)$/))) {
      let snap, artistId;
      if (mm[1].startsWith('s')) { const s = await one(env, 'SELECT * FROM submissions WHERE id=?', mm[1]); if (!s) return html('Not found', 404); snap = JSON.parse(s.snapshot); artistId = s.artist_id; }
      else { const v = await one(env, 'SELECT * FROM versions WHERE artist_id=? AND version=?', mm[2], Number(mm[3])); if (!v) return html('Not found', 404); snap = JSON.parse(v.snapshot); artistId = mm[2]; }
      const rest = mm[4];
      if (rest.startsWith('img/')) { const img = await one(env, 'SELECT * FROM images WHERE id=? AND artist_id=?', rest.slice(4), artistId); return img ? previewImage(env, img) : html('Not found', 404); }
      const images = await all(env, 'SELECT * FROM images WHERE artist_id=?', artistId);
      return previewRoute(rest, previewPkg(snap, images), 'Founder review preview · <a href="/admin">Back to the review desk</a>');
    }
    if (p === '/api/admin/overview' && m === 'GET') return json({ ok: true, ...(await overview(env)) });
    if (p === '/api/admin/artists' && m === 'POST') {
      const b = await req.json();
      const email = String(b.email || '').trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Bad('Enter the artist’s email address');
      const name = L.text(b.display_name, 2, 80, 'Name');
      const slug = String(b.slug || L.slugify(name));
      if (!L.SLUG.test(slug)) throw new Bad('Gallery address: lower-case words joined by hyphens');
      if (b.application_ref && !/^F25-\d{6}-[0-9A-F]{6}$/.test(b.application_ref)) throw new Bad('Application reference looks like F25-YYMMDD-XXXXXX');
      if (await one(env, 'SELECT id FROM artists WHERE email=? OR slug=?', email, slug)) throw new Bad('An artist with that email or gallery address already exists', 409);
      const id = rid('a');
      await env.DB.prepare('INSERT INTO artists (id, slug, email, display_name, founding, application_ref, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)')
        .bind(id, slug, email, name, b.founding === false ? 0 : 1, b.application_ref || null, now(), now()).run();
      await audit(env, me.email, 'founder', 'invite', id, { slug, founding: b.founding !== false });
      return json({ ok: true, id, slug });
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
      await audit(env, me.email, 'founder', 'unpublish', mm[1]);
      return json({ ok: true });
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
    if ((mm = p.match(/^\/api\/admin\/queue\/(q[0-9a-z]+)\/publish$/)) && m === 'POST') {
      const q = await one(env, "SELECT * FROM publish_queue WHERE id=? AND status='awaiting_founder'", mm[1]);
      if (!q) throw new Bad('Nothing to publish', 409);
      await env.DB.prepare("UPDATE publish_queue SET status='ready', updated_at=? WHERE id=?").bind(now(), q.id).run();
      await audit(env, me.email, 'founder', 'publish', q.artist_id, { queue: q.id, version: q.version });
      return json({ ok: true });
    }
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
  if (p === '/api/me' && m === 'GET') {
    const d = await load(env, artist.id);
    const { email, ...a } = d.artist;
    return json({ ok: true, artist: { ...a, email }, status: await status(env, d.artist), media: L.MEDIA, counties: L.COUNTIES, min_long_edge: minLong(env),
      portrait: (({ checks, ...i }) => i)(d.images.find(i => i.id === d.artist.portrait_image_id) || { checks: null }) });
  }
  if (p === '/api/me/profile' && m === 'PUT') {
    const f = clean(PROFILE, await req.json());
    if (!Object.keys(f).length) return json({ ok: true });
    await env.DB.prepare(`UPDATE artists SET ${Object.keys(f).map(k => `${k}=?`).join(', ')}, updated_at=? WHERE id=?`).bind(...Object.values(f), now(), artist.id).run();
    await audit(env, artist.email, 'artist', 'profile', artist.id, { fields: Object.keys(f) });
    return json({ ok: true, saved_at: now() });
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
      if (Object.keys(f).length) await env.DB.prepare(`UPDATE images SET ${Object.keys(f).map(k => `${k}=?`).join(', ')} WHERE id=? AND artist_id=?`).bind(...Object.values(f), img.id, artist.id).run();
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
  if (p === '/api/submit' && m === 'POST') return submit(env, artist, await req.json());
  if (p === '/api/submit/withdraw' && m === 'POST') {
    await env.DB.prepare("UPDATE submissions SET status='withdrawn', decided_at=? WHERE artist_id=? AND status='pending'").bind(now(), artist.id).run();
    return json({ ok: true });
  }
  return json({ ok: false, error: 'Not found' }, 404);
}
