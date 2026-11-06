// Test helper: an artist who is ALREADY published, as production holds one (synthetic data only). Optionally stores
// placeholder bytes in the local R2 bucket for each original, so deletion can be proven object by object.
import { snapshot } from '../src/lib.js';
import { createHash } from 'node:crypto';
const sha = s => createHash('sha256').update(s).digest('hex');
export async function seedPublished(db, { id, slug, email, name, works = 3, licence = 'PA-GPIL-2026-10-29', publishedAt = '2026-11-05T17:05:00.000Z', bucket = null, number = null }) {
  const t = publishedAt;
  await db.prepare(`INSERT INTO artists (id, slug, email, display_name, founding, founding_number, practice, medium, county, county_public, bio, account_status,
    licence_version, licence_accepted_at, first_published_at, created_at, updated_at) VALUES (?,?,?,?,1,?, 'Painter', 'painting', 'Dublin', 1, ?, 'active', ?, ?, ?, ?, ?)`)
    .bind(id, slug, email, name, number, `${name} is a synthetic test artist who is already published.`, licence, licence ? t : null, t, t, t).run();
  for (let i = 1; i <= works; i++) {
    await db.prepare(`INSERT INTO artworks (id, artist_id, slug, title, year, medium, h_cm, w_cm, price_eur, availability, description, ord, ai_involvement, archived, created_at, updated_at)
      VALUES (?,?,?,?,2026,'Oil on board',40,50,600,'available','A synthetic test work.',?, 'none', 0, ?, ?)`).bind(`w${id}${i}`, id, `work-${i}`, `Work ${i}`, i, t, t).run();
    const key = `originals/${id}/${i}.jpg`, pkey = `previews/${id}/${i}.jpg`;
    await db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, preview_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
      VALUES (?,?,?,'main',?,?,?,1000,2400,1800,'jpeg','A test painting','self','{"blocks":[],"warns":[]}',0,?)`).bind(`i${id}${i}`, id, `w${id}${i}`, key, pkey, sha(`${id}-${i}`), t).run();
    if (bucket) { await bucket.put(key, `original ${id} ${i}`); await bucket.put(pkey, `preview ${id} ${i}`); }
  }
  const a = await db.prepare('SELECT * FROM artists WHERE id=?').bind(id).first();
  const w = (await db.prepare('SELECT * FROM artworks WHERE artist_id=?').bind(id).all()).results, im = (await db.prepare('SELECT * FROM images WHERE artist_id=?').bind(id).all()).results;
  await db.prepare("INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (?, 1, ?, 'seed', ?)").bind(id, JSON.stringify(snapshot(a, w, im)), t).run();
  await db.prepare("INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (?, ?, 1, 'reviewed', 'published', ?, ?)").bind(`q${id}seed`, id, t, t).run();
  return a;
}
// Everything one artist has, table by table (to prove that nothing of another artist changes).
export async function artistRows(db, id) {
  const o = {};
  for (const [t, c] of [['artists', 'id'], ['artworks', 'artist_id'], ['images', 'artist_id'], ['submissions', 'artist_id'], ['versions', 'artist_id'], ['publish_queue', 'artist_id'],
    ['enquiries', 'artist_id'], ['gallery_positions', 'artist_id'], ['agreement_acceptances', 'artist_id'], ['acceptance_corrections', 'artist_id'], ['enquiry_log', 'artist_id'],
    ['participation_events', 'artist_id'], ['record_retention', 'artist_id']]) o[t] = (await db.prepare(`SELECT * FROM ${t} WHERE ${c} = ? ORDER BY rowid`).bind(id).all()).results;
  return o;
}
