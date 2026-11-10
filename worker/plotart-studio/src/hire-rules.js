/* PlotArt · Art for Hire listing rules (Stage 3B-3, development 10 Nov 2026). NOT DEPLOYED.
   The ONE definition of "listed for hire", shared by the Studio (catalogue, founder desk, artist panel) and the public
   enquiry relay (hire enquiries and the live listed-works check). No other imports, so the relay stays small and never
   carries the Studio's assets.

   A work is listed only when, at the moment of asking:
     1. the artist holds the current Art for Hire Artist Terms (an acceptance of docId) and has not left Art for Hire;
     2. the artist has switched the work on (offered = 1) and it is not "not available at the moment";
     3. the founder has approved it (approved_public set);
   and the work is in the artist's PUBLISHED gallery, available there and in the Studio, not archived, and the artist's
   account is active with participation not ended. The caller supplies docId only once its own switches are on. */
export const SCREEN_NOTICE = 'Screen and photo use is never included in a hire. Any permission is agreed in writing with the artist.';
export const PILOT_NOTICE = 'Screen-use arrangements are not yet facilitated through PlotArt.';
export const SCREEN = { none: 0, background: 1, featured: 2 }, PHOTO = { none: 0, yes: 1 };
export const REVIEWED = ['county', 'framing', 'glazed', 'weight_band', 'collection', 'deliver_km'];
export const pick = (o, keys) => Object.fromEntries(keys.map(k => [k, o[k] ?? null]));

/* The artist's PUBLISHED gallery (the last version the pipeline published), so a work only waiting for review is never listed. */
export async function published(env, artistId) {
  const q = await env.DB.prepare("SELECT version FROM publish_queue WHERE artist_id = ? AND status = 'published' ORDER BY version DESC LIMIT 1").bind(artistId).first();
  if (!q) return null;
  const v = await env.DB.prepare('SELECT snapshot FROM versions WHERE artist_id = ? AND version = ?').bind(artistId, q.version).first();
  return v ? JSON.parse(v.snapshot) : null;
}

export async function listedFor(env, { docId, artistId = null, artworkId = null }) {
  if (!docId) return [];
  const rows = (await env.DB.prepare(`SELECT h.*, a.slug AS artist_slug, a.display_name, a.email AS artist_email, w.slug AS work_slug, w.title
    FROM artwork_hire h JOIN artworks w ON w.id = h.artwork_id AND w.artist_id = h.artist_id JOIN artists a ON a.id = h.artist_id
    WHERE h.offered = 1 AND h.approved_public IS NOT NULL AND h.availability <> 'not_now' AND w.archived = 0 AND w.availability = 'available'
      AND a.account_status = 'active'
      AND EXISTS (SELECT 1 FROM hire_terms_acceptances x WHERE x.artist_id = h.artist_id AND x.doc_id = ?)
      AND NOT EXISTS (SELECT 1 FROM participation_events p WHERE p.artist_id = h.artist_id AND p.kind = 'ended')
      AND COALESCE((SELECT kind FROM hire_participation_events e WHERE e.artist_id = h.artist_id ORDER BY e.at DESC, e.rowid DESC LIMIT 1), 'none') <> 'left'
      AND (? IS NULL OR h.artist_id = ?) AND (? IS NULL OR h.artwork_id = ?)
    ORDER BY a.display_name, w.ord`).bind(docId, artistId, artistId, artworkId, artworkId).all()).results;
  const out = [], snaps = new Map();
  for (const r of rows) {
    if (!snaps.has(r.artist_id)) snaps.set(r.artist_id, await published(env, r.artist_id));
    const snap = snaps.get(r.artist_id);
    const pw = snap && snap.works.find(x => x.id === r.artwork_id);
    if (!pw || pw.availability !== 'available') continue;                               // published and available in the gallery
    const ap = JSON.parse(r.approved_public);
    const item = { artwork_id: r.artwork_id, artist_id: r.artist_id, artist_slug: r.artist_slug, work_slug: r.work_slug,
      hire: { ...pick(ap, REVIEWED),                                                       // last approved details
        availability: r.availability, available_from: r.available_from,                    // availability: the artist's own, at once
        screen_use: SCREEN[r.screen_use] < SCREEN[ap.screen_use] ? r.screen_use : ap.screen_use,   // never wider than approved
        photo_use: PHOTO[r.photo_use] < PHOTO[ap.photo_use] ? r.photo_use : ap.photo_use,
        price: 'Price on request' } };
    // private fields for the relay's own use only; never part of any public response
    Object.defineProperty(item, 'private', { value: { artist_email: r.artist_email, display_name: r.display_name, title: r.title }, enumerable: false });
    out.push(item);
  }
  return out;
}
