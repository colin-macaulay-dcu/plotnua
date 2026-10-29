/* PlotArt Studio · shared rules (Phase 2, 29 Oct 2026).
   The validation mirrors atlas-tools/plotart_gallery.py (Phase 1) so an export the Studio accepts is one the
   publishing pipeline accepts; test/prove-studio.mjs runs every export through the Python ingest to prove it. */

export const LICENCE_VERSION = 'PA-GPIL-2026-10-29';
export const FOUNDING_MIN_WORKS = 10;
export const MAX_BYTES = 30 * 1024 * 1024;
export const MAX_PREVIEW_BYTES = 4 * 1024 * 1024;
export const MIN_LONG_EDGE = 2000, GOOD_LONG_EDGE = 3000, MAX_SIDE = 12000, MAX_PIXELS = 60_000_000, MAX_VIEWS = 3;
export const AVAILABILITY = ['available', 'reserved', 'sold', 'not_for_sale'];
export const AI = ['none', 'assisted', 'generated'];
export const MEDIA = ['painting', 'drawing', 'works_on_paper', 'printmaking', 'photography', 'sculpture',
  'ceramics_craft', 'textiles', 'mixed_media', 'digital_new_media', 'other'];
export const COUNTIES = ['Antrim', 'Armagh', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal', 'Down', 'Dublin',
  'Fermanagh', 'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo',
  'Meath', 'Monaghan', 'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Tyrone', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow'];
export const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,6}$/;

export const now = () => new Date().toISOString();
export const rid = (p = '', n = 10) => p + [...crypto.getRandomValues(new Uint8Array(n))].map(b => (b % 36).toString(36)).join('');

export class Bad extends Error { constructor(msg, status = 400) { super(msg); this.status = status; } }

/* ---- the same privacy hint as plotart_gallery.py ---- */
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]/;
const EIRCODE = /\b[ACDEFHKNPRTVWXY]\d[0-9W]\s?[0-9ACDEFHKNPRTVWXY]{4}\b/;
const DIGITRUN = /\+?\d[\d \-().]{6,}\d/g;
export function privateHint(s) {
  return EMAIL.test(s) || EIRCODE.test(s) || /\beircode\b/i.test(s) ||
    [...s.matchAll(DIGITRUN)].some(m => [...m[0]].filter(c => c >= '0' && c <= '9').length >= 9);
}
export function text(v, lo, hi, what, { optional = false } = {}) {
  if (v === null || v === undefined || (typeof v === 'string' && v.trim() === '')) {
    if (optional) return null;
    throw new Bad(`${what} is needed`);
  }
  if (typeof v !== 'string') throw new Bad(`${what} must be text`);
  const t = v.trim();
  if (t.length < lo || t.length > hi) throw new Bad(`${what} must be ${lo}–${hi} characters (now ${t.length})`);
  if (/[<>]/.test(t)) throw new Bad(`${what} can't contain < or >`);
  if (privateHint(t)) throw new Bad(`${what} looks as if it contains an email address, phone number or Eircode. Contact details are never published; buyers reach you through PlotArt.`);
  return t;
}
export const num = (v, lo, hi, what, { optional = false, int = false } = {}) => {
  if (v === null || v === undefined || v === '') { if (optional) return null; throw new Bad(`${what} is needed`); }
  const n = Number(v);
  if (!Number.isFinite(n) || n < lo || n > hi || (int && !Number.isInteger(n))) throw new Bad(`${what} must be ${int ? 'a whole number ' : ''}between ${lo} and ${hi}`);
  return n;
};
export function slugify(s, taken = new Set()) {
  let base = String(s || 'untitled').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').split('-').slice(0, 6).join('-') || 'untitled';
  if (base === 'index') base = 'index-work';
  let s2 = base, i = 2;
  while (taken.has(s2)) { s2 = `${base.split('-').slice(0, 5).join('-')}-${i++}`; }
  return s2;
}

/* ---- image headers: format by content, pixel size without decoding ---- */
export function sniff(u8) {
  if (u8[0] === 0xFF && u8[1] === 0xD8 && u8[2] === 0xFF) return 'jpeg';
  if (u8[0] === 0x89 && u8[1] === 0x50 && u8[2] === 0x4E && u8[3] === 0x47) return 'png';
  if (String.fromCharCode(...u8.slice(0, 4)) === 'RIFF' && String.fromCharCode(...u8.slice(8, 12)) === 'WEBP') return 'webp';
  return null;
}
export function dimensions(u8, fmt) {
  const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  if (fmt === 'png') return u8.length > 24 ? { w: dv.getUint32(16), h: dv.getUint32(20) } : null;
  if (fmt === 'webp') {
    const chunk = String.fromCharCode(...u8.slice(12, 16));
    if (chunk === 'VP8X') return { w: 1 + (u8[24] | u8[25] << 8 | u8[26] << 16), h: 1 + (u8[27] | u8[28] << 8 | u8[29] << 16) };
    if (chunk === 'VP8 ') return { w: dv.getUint16(26, true) & 0x3FFF, h: dv.getUint16(28, true) & 0x3FFF };
    if (chunk === 'VP8L') { const b = dv.getUint32(21, true); return { w: 1 + (b & 0x3FFF), h: 1 + ((b >> 14) & 0x3FFF) }; }
    return null;
  }
  if (fmt === 'jpeg') {
    let i = 2;
    while (i + 9 < u8.length) {
      if (u8[i] !== 0xFF) { i++; continue; }
      const m = u8[i + 1];
      if (m === 0xD8 || m === 0x01 || (m >= 0xD0 && m <= 0xD7)) { i += 2; continue; }
      const len = dv.getUint16(i + 2);
      if (m >= 0xC0 && m <= 0xCF && ![0xC4, 0xC8, 0xCC].includes(m)) return { h: dv.getUint16(i + 5), w: dv.getUint16(i + 7) };
      i += 2 + len;
    }
    return null;
  }
  return null;
}
/* Server-side checks (the browser runs the same rules first, for instant feedback). BLOCK = cannot be used. */
export function checkImage(u8, { portrait = false, minLong = MIN_LONG_EDGE } = {}) {
  const blocks = [], warns = [];
  const fmt = sniff(u8);
  if (!fmt) return { fmt, blocks: ['This isn’t a JPEG, PNG or WebP image (checked by its content, not its name).'], warns, dims: null };
  if (u8.length > MAX_BYTES) blocks.push(`The file is ${(u8.length / 1048576).toFixed(1)} MB; the limit is 30 MB.`);
  const d = dimensions(u8, fmt);
  if (!d || !d.w || !d.h) blocks.push('The image size couldn’t be read; the file may be damaged.');
  else {
    const long = Math.max(d.w, d.h);
    if (d.w * d.h > MAX_PIXELS || long > MAX_SIDE) blocks.push(`The image is ${d.w} × ${d.h} px; the limit is 60 megapixels and 12,000 px a side.`);
    const min = portrait ? 800 : minLong;
    if (long < min) blocks.push(`The photograph is ${long} px on its long edge; at least ${min.toLocaleString('en-IE')} px is needed. Upload the full-size original, not a screenshot or a copy from social media.`);
    else if (!portrait && long < Math.max(GOOD_LONG_EDGE, minLong)) warns.push(`${long} px on the long edge is acceptable; 3,000 px or more looks better on large screens.`);
    if (Math.max(d.w, d.h) / Math.min(d.w, d.h) > 4) warns.push('A very long format: check it reads well as a thumbnail.');
  }
  return { fmt, blocks, warns, dims: d };
}
export async function sha256(buf) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map(b => b.toString(16).padStart(2, '0')).join('');
}

/* ---- snapshots, changes and tiers ---- */
const imgRef = i => i && ({ id: i.id, sha256: i.sha256, role: i.role, alt: i.alt || null, photographer: i.photographer || null,
  photo_credit: i.photographer === 'other_with_permission' ? (i.photo_credit || null) : null, width: i.width, height: i.height, format: i.format });
export function snapshot(artist, works, images) {
  const byWork = {};
  for (const i of images) if (i.artwork_id && !i.deleted_at) (byWork[i.artwork_id] ||= []).push(i);
  const portrait = artist.portrait_image_id ? images.find(i => i.id === artist.portrait_image_id && !i.deleted_at) : null;
  return {
    artist: {
      slug: artist.slug, display_name: artist.display_name, founding: !!artist.founding, practice: artist.practice || null,
      medium: artist.medium || null, county: artist.county || null, county_public: !!artist.county_public,
      statement: artist.statement || null, bio: artist.bio || null, website: artist.website || null, instagram: artist.instagram || null,
      portrait: imgRef(portrait),
    },
    works: works.filter(w => !w.archived).sort((a, b) => a.ord - b.ord).map(w => ({
      id: w.id, slug: w.slug, title: w.title || null, year: w.year ?? null, medium: w.medium || null, materials: w.materials || null,
      h_cm: w.h_cm ?? null, w_cm: w.w_cm ?? null, d_cm: w.d_cm ?? null, price_eur: w.price_eur ?? null,
      price_on_request: !!w.price_on_request, availability: w.availability, description: w.description || null,
      ai_involvement: w.ai_involvement || null, ai_note: w.ai_note || null,
      images: (byWork[w.id] || []).sort((a, b) => (a.role === 'main' ? -1 : 0) - (b.role === 'main' ? -1 : 0) || a.ord - b.ord).map(imgRef),
    })),
  };
}

const FULL_ARTIST = ['display_name', 'statement', 'bio', 'practice', 'medium'];
const LIGHT_ARTIST = ['county', 'county_public', 'website', 'instagram'];
const LIGHT_WORK = ['title', 'year', 'medium', 'materials', 'h_cm', 'w_cm', 'd_cm', 'description', 'price_eur', 'price_on_request'];
const FULL_WORK = ['ai_involvement', 'ai_note'];
const LABEL = { display_name: 'name', h_cm: 'height', w_cm: 'width', d_cm: 'depth', price_eur: 'price', price_on_request: 'price on request',
  county_public: 'show county', ai_involvement: 'AI declaration', ai_note: 'AI disclosure' };
const lab = f => LABEL[f] || f.replace(/_/g, ' ');
const eq = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
const imgSig = w => (w.images || []).map(i => `${i.role}:${i.sha256}`).join('|');
const imgMeta = w => (w.images || []).map(i => `${i.alt}|${i.photographer}|${i.photo_credit}`).join('||');

/* Every difference between the live snapshot and the working snapshot, each with its tier. */
export function changes(live, work) {
  if (!live) return [{ tier: 'full', what: 'First publication of your gallery' }];
  const out = [];
  for (const f of FULL_ARTIST) if (!eq(live.artist[f], work.artist[f])) out.push({ tier: 'full', what: `Profile: ${lab(f)}`, from: live.artist[f], to: work.artist[f] });
  for (const f of LIGHT_ARTIST) if (!eq(live.artist[f], work.artist[f])) out.push({ tier: 'light', what: `Profile: ${lab(f)}`, from: live.artist[f], to: work.artist[f] });
  if ((live.artist.portrait?.sha256 || null) !== (work.artist.portrait?.sha256 || null)) out.push({ tier: 'full', what: work.artist.portrait ? 'Portrait (new or replaced)' : 'Portrait removed' });
  const L = Object.fromEntries(live.works.map(w => [w.id, w]));
  const W = Object.fromEntries(work.works.map(w => [w.id, w]));
  for (const w of work.works) {
    const o = L[w.id];
    if (!o) { out.push({ tier: 'full', what: `New artwork: ${w.title || 'untitled'}`, work: w.id }); continue; }
    for (const f of LIGHT_WORK) if (!eq(o[f], w[f])) out.push({ tier: 'light', what: `${w.title}: ${lab(f)}`, work: w.id, from: o[f], to: w[f] });
    for (const f of FULL_WORK) if (!eq(o[f], w[f])) out.push({ tier: 'full', what: `${w.title}: ${lab(f)}`, work: w.id, from: o[f], to: w[f] });
    if (imgSig(o) !== imgSig(w)) out.push({ tier: 'full', what: `${w.title}: photographs added or replaced`, work: w.id });
    else if (imgMeta(o) !== imgMeta(w)) out.push({ tier: 'light', what: `${w.title}: photo description or credit`, work: w.id });
    if (o.availability !== w.availability) out.push({ tier: 'instant', what: `${w.title}: ${o.availability} → ${w.availability}`, work: w.id });
  }
  for (const o of live.works) if (!W[o.id]) out.push({ tier: 'instant', what: `Removed: ${o.title}`, work: o.id });
  const lo = live.works.map(w => w.id).filter(id => W[id]), wo = work.works.map(w => w.id).filter(id => L[id]);
  if (!eq(lo, wo)) out.push({ tier: 'instant', what: 'Order of works' });
  return out;
}
export const tierOf = cs => cs.some(c => c.tier === 'full') ? 'full' : cs.some(c => c.tier === 'light') ? 'light' : null;

/* Apply ONLY instant fields (availability, removal, order) from the working copy onto a version snapshot. */
export function applyInstant(base, work) {
  const W = Object.fromEntries(work.works.map(w => [w.id, w]));
  const kept = base.works.filter(w => W[w.id]).map(w => ({ ...w, availability: W[w.id].availability }));
  const pos = Object.fromEntries(work.works.map((w, i) => [w.id, i]));
  kept.sort((a, b) => pos[a.id] - pos[b.id]);
  return { ...base, works: kept };
}

/* Everything that must be true before a gallery (or a change) can be submitted. */
export function readiness(snap, { founding, firstPublication = true, licenceOk, imageBlocks }) {
  const p = [];
  const a = snap.artist;
  const t = (v, lo, hi, w) => { try { text(v, lo, hi, w); } catch (e) { p.push(e.message); } };
  t(a.display_name, 2, 80, 'Your name');
  t(a.bio, 40, 2400, 'Your biography');
  if (a.statement) t(a.statement, 10, 400, 'Your statement');
  if (!MEDIA.includes(a.medium)) p.push('Choose your main medium in your profile');
  if (a.portrait && !a.portrait.alt) p.push('Describe your portrait photograph (for people using screen readers)');
  if (!snap.works.length) p.push('Add at least one artwork');
  // The minimum is enforced when a Founding gallery FIRST opens; afterwards a sale or removal is never blocked
  // (the artist is asked to top up within 30 days: Founding Artist Agreement 3.3(c)).
  if (founding && firstPublication && snap.works.length < FOUNDING_MIN_WORKS) p.push(`Founding galleries open with at least ${FOUNDING_MIN_WORKS} artworks: you have ${snap.works.length}`);
  for (const w of snap.works) {
    const n = w.title || 'An untitled artwork', q = [];
    if (!w.title) q.push('a title');
    if (!w.medium) q.push('the medium');
    if (!w.h_cm || !w.w_cm) q.push('its size');
    if (!w.ai_involvement) q.push('the AI question');
    else if (w.ai_involvement !== 'none' && !w.ai_note) q.push('a short AI disclosure');
    if (!w.images.some(i => i.role === 'main')) q.push('a main photograph');
    if (w.images.some(i => !i.alt)) q.push('a description of each photograph');
    if (w.images.some(i => !i.photographer)) q.push('who took each photograph');
    if (w.images.some(i => i.photographer === 'other_with_permission' && !i.photo_credit)) q.push('the photographer’s name');
    if (w.images.some(i => imageBlocks.has(i.id))) q.push('a photograph that passes the checks');
    if (q.length) p.push(`${n} needs ${q.join(', ')}`);
  }
  if (!licenceOk) p.push('Accept the Gallery Publication and Image Licence');
  return p;
}

/* The gallery export the publishing pipeline ingests (schema plotnua.plotart.gallery.v1, see plotart_gallery.py). */
export function exportGallery(snap, { version, approvedAt, licenceVersion, licenceAcceptedAt, artistId, aiDecisions = {} }) {
  const ext = f => ({ jpeg: 'jpg', png: 'png', webp: 'webp' }[f]);
  const img = (i, role) => ({ file: `${i.id}.${ext(i.format)}`, role, alt: i.alt, photographer: i.photographer,
    photo_credit: i.photographer === 'other_with_permission' ? i.photo_credit : null });
  const a = snap.artist;
  return {
    schema: 'plotnua.plotart.gallery.v1',
    artist: { slug: a.slug, display_name: a.display_name, founding: a.founding, practice: a.practice, medium: a.medium,
      county: a.county, county_public: a.county_public, statement: a.statement, bio: a.bio, website: a.website,
      instagram: a.instagram, portrait: a.portrait ? img(a.portrait, 'portrait') : null },
    works: snap.works.map((w, i) => ({
      id: w.id, slug: w.slug, title: w.title, year: w.year, medium: w.medium, materials: w.materials, h_cm: w.h_cm, w_cm: w.w_cm,
      d_cm: w.d_cm, price_eur: w.price_eur, price_on_request: w.price_on_request, availability: w.availability,
      description: w.description, order: i + 1, ai_involvement: w.ai_involvement, ai_note: w.ai_note,
      ai_founder_decision: aiDecisions[w.id] || null,
      images: w.images.map(m => img(m, m.role)) })),
    publication: { state: 'approved', version: `v${version}`, approved_by: 'founder', approved_at: approvedAt,
      licence_version: licenceVersion, licence_accepted_at: licenceAcceptedAt, permission_ref: `PA-PERM-${artistId}`, test_note: null },
  };
}
