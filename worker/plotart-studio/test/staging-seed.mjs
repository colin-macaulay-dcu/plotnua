// PlotArt · three galleries (Phase B) · the STAGING copy of the live galleries, built from the published packages in this
// repository. Used by test/prove-galleries-staging.mjs (Miniflare D1) and test/cf-gallery-test.mjs (a real, temporary
// Cloudflare D1 database). db is anything with D1's prepare().bind().run()/first()/all() API. Artists' email addresses are not
// public: each gets a synthetic @staging.invalid address.
import { readFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

export async function seedStaging(db, { ROOT, snapshot }) {
  const nn = (...v) => v.map(x => x === undefined ? null : x);   // public records omit some fields
  const SHOWN = new Set(['available', 'reserved', 'sold', 'not_for_sale']);
  const id = (p, s) => p + createHash('sha256').update(s).digest('hex').slice(0, 10);
  const packages = readdirSync(join(ROOT, 'plotart/artists')).sort().map(s => JSON.parse(readFileSync(join(ROOT, 'plotart/artists', s, 'gallery.json'), 'utf8')));
  const vg = readFileSync(join(ROOT, 'plotart/gallery/index.html'), 'utf8');
  // position 01 used to sit outside the list on the page; since the 26 Nov 2026 Gallery order publication (main 538b264) it
  // is a list item like the others, so it is added only when the page does not already carry it
  const listed = [...vg.matchAll(/<li class="pa-vgc-work" data-pa-position="(\d\d)">[\s\S]*?href="\.\.\/artists\/([a-z0-9-]+)\/"/g)].map(m => [m[1], m[2]]);
  const positions = [...(listed.some(([p]) => p === '01') ? [] : [['01', 'leah-hewson']]), ...listed];
  // One curated gallery (26 Nov 2026): the page no longer carries founding positions or a separate Artists in Focus. When
  // it carries the unified arrangement, the staging positions follow its order (opening row first) and the Artists in
  // Focus records are the cards whose artwork the founder chose (as migration 0029 set them up from those records).
  const arr = JSON.parse(execFileSync('python3', ['-c', 'import sys,json; sys.path.insert(0,"atlas-tools"); import plotart_featured as F; d=open("plotart/gallery/index.html").read(); print(json.dumps(F.arrangement_in(d) if "data-pa-curated" in d else None))'], { cwd: ROOT, encoding: 'utf8' }));
  if (arr && !listed.length) { positions.length = 0; [...arr.opening, ...arr.rest].slice(0, 25).forEach((x, i) => positions.push([String(i + 1).padStart(2, '0'), x.artist])); }
  const featured = arr ? arr.rest.filter(x => x.work).slice(0, 6) : JSON.parse(execFileSync('python3', ['-c', 'import sys,json; sys.path.insert(0,"atlas-tools"); import plotart_featured as F; print(json.dumps(F.selection_in(open("plotart/gallery/index.html").read())))'], { cwd: ROOT, encoding: 'utf8' }));

  const L = { snapshot };
  let shownWorks = 0;
  for (const pkg of packages) {
    const a = pkg.artist, aid = id('a', a.slug), pub = pkg.publication, t = pub.approved_at || pub.first_approved_at || "2026-11-05T00:00:00.000Z", first = pub.first_approved_at || t;
    await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, practice, medium, county, county_public, statement, bio, website, instagram, account_status,
      licence_version, licence_accepted_at, first_published_at, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,1,?,?,?,?, 'active', ?,?,?,?,?)`)
      .bind(...nn(aid, a.slug, `${a.slug}@staging.invalid`, a.display_name, a.founding ? 1 : 0, a.practice || null, a.medium || null, a.county || null, a.statement || null, a.bio || null,
        a.website || null, a.instagram || null, pub.licence_version, pub.licence_accepted_at, first, first, t)).run();
    let ord = 0;
    for (const w of pkg.works) {
      ord++; if (SHOWN.has(w.availability)) shownWorks++;
      await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, materials, h_cm, w_cm, d_cm, price_eur, price_on_request, availability, description, ord,
        ai_involvement, ai_note, archived, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?)`)
        .bind(...nn(w.id, aid, w.slug, w.title, w.year || null, w.medium || null, w.materials || null, w.h_cm || null, w.w_cm || null, w.d_cm || null, w.price_eur ?? null,
          w.price_on_request ? 1 : 0, w.availability, w.description || null, ord, w.ai_involvement || 'none', w.ai_note || null, t, t)).run();
      let n = 0;
      for (const im of w.images || []) {
        n++;
        await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
          VALUES (?,?,?,?,?,?,?,1000,?,?,'jpeg',?, 'self', '{"blocks":[],"warns":[]}', ?, ?)`)
          .bind(...nn(id('i', w.id + n), aid, w.id, im.role === 'main' ? 'main' : 'view', `originals/${aid}/${w.id}-${n}.jpg`, `previews/${aid}/${w.id}-${n}.jpg`,
            id('', w.id + n).padEnd(64, '0'), (im.pixels || [2000, 1500])[0], (im.pixels || [2000, 1500])[1], im.alt || '', n - 1, t)).run();
      }
    }
    const ar = await db.prepare('SELECT * FROM artists WHERE id=?').bind(aid).first();
    const ws = (await db.prepare('SELECT * FROM artworks WHERE artist_id=? ORDER BY ord').bind(aid).all()).results, ims = (await db.prepare('SELECT * FROM images WHERE artist_id=?').bind(aid).all()).results;
    await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'staging', ?)").bind(...nn(aid, JSON.stringify(L.snapshot(ar, ws, ims)), t)).run();
    await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?, ?, 1, 'reviewed', 'published', ?, ?)").bind(...nn(id('q', aid), aid, t, t)).run();
  }
  const T = '2026-11-24T12:00:00.000Z';
  for (const [p, slug] of positions) await db.prepare('INSERT INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (?,?,0,NULL,?)').bind(...nn(Number(p), id('a', slug), T)).run();
  let fp = 0; for (const f of featured) await db.prepare("INSERT INTO homepage_features (position, kind, artist_id, artwork_id, updated_at) VALUES (?, 'artist', ?, ?, ?)").bind(...nn(++fp, id('a', f.artist), f.work, T)).run();
  return { packages, positions, featured, shownWorks };
}
