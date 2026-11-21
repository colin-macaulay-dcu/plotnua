/* PlotArt · multi-artist basket · PRIVATE STAGING GALLERY (21 Nov 2026). STAGING ONLY.
   Served by the checkout Worker only when STAGING_GALLERY = "true", ENVIRONMENT = "staging" and Stripe is in TEST mode
   (basket-public.js stagingGallery). Lets testers browse SYNTHETIC artworks by the synthetic staging artists, see price and
   delivery, and add them to the basket, exactly as the published gallery's "Add to basket" button would. Images are
   generated here as abstract SVGs from the artwork id: no real artwork, artist or photograph is shown.
     GET /, /gallery                the synthetic gallery (every artwork with its live basket status)
     GET /gallery/<artwork id>      one artwork page
     GET /staging-img/<id>.svg      its synthetic image */
import * as B from './basket.js';

const all = async (env, sql, ...b) => (await env.DB.prepare(sql).bind(...b).all()).results;
const one = (env, sql, ...b) => env.DB.prepare(sql).bind(...b).first();

/* A deterministic abstract composition per artwork (no randomness at request time; the same id always looks the same). */
function hash(s) { let h = 2166136261; for (const c of String(s)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
const PALETTES = [['#1f2a33', '#c26d3a', '#e9e2cf', '#6c8a9b'], ['#2b1d1a', '#d9a066', '#7a3e2a', '#f1e3c6'], ['#18252b', '#9fb8ad', '#e4d5b7', '#2f4f5f'],
  ['#232323', '#b5893f', '#ede3cc', '#8c4a2f'], ['#1c2230', '#7d8fb3', '#e8dfd0', '#c9a24e'], ['#26201c', '#a3b18a', '#dad7cd', '#588157']];
export function svg(id, { w = 900, h = 1100 } = {}) {
  let x = hash(id); const r = () => ((x = Math.imul(x ^ (x >>> 15), 2246822519) >>> 0) / 4294967296);
  const p = PALETTES[x % PALETTES.length], shapes = [];
  for (let i = 0; i < 7; i++) {
    const c = p[1 + (i % 3)], o = (0.35 + r() * 0.5).toFixed(2);
    if (r() < 0.5) shapes.push(`<circle cx="${(r() * w) | 0}" cy="${(r() * h) | 0}" r="${(60 + r() * 320) | 0}" fill="${c}" opacity="${o}"/>`);
    else shapes.push(`<rect x="${(r() * w * 0.8) | 0}" y="${(r() * h * 0.8) | 0}" width="${(80 + r() * 420) | 0}" height="${(40 + r() * 380) | 0}" fill="${c}" opacity="${o}" transform="rotate(${((r() - 0.5) * 30).toFixed(1)} ${w / 2} ${h / 2})"/>`);
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}"><defs><filter id="g"><feTurbulence baseFrequency="0.9" numOctaves="2" seed="${x % 97}"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.06 0"/></filter></defs><rect width="100%" height="100%" fill="${p[0]}"/>${shapes.join('')}<rect width="100%" height="100%" filter="url(#g)"/></svg>`;
}

const STYLE = `<style>
.gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:clamp(18px,3vw,36px);margin-top:28px}
.card{display:block;text-decoration:none;color:inherit}.card .im{background:var(--anth);border-radius:12px;aspect-ratio:4/5;display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:var(--shadow-art)}
.card img{width:100%;height:100%;object-fit:cover;display:block}.card h3{margin:14px 0 2px;font-size:24px}.card p{margin:0;font-size:14.5px;color:var(--stone)}
.aw{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,1fr);gap:clamp(24px,5vw,64px);align-items:start;margin-top:18px}@media (max-width:860px){.aw{grid-template-columns:1fr}}
.aw .im{background:var(--anth);border-radius:14px;overflow:hidden;box-shadow:var(--shadow-art)}.aw .im img{width:100%;display:block}
dl.d{display:grid;grid-template-columns:120px 1fr;gap:6px 14px;font-size:15px;margin:18px 0}dl.d dt{color:var(--stone)}dl.d dd{margin:0}
.price{font-family:var(--serif);font-size:34px;color:var(--ivory);margin:6px 0}.badge{display:inline-block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line-2);border-radius:999px;padding:3px 10px;color:var(--stone);margin-left:8px}
</style>`;

async function works(env) {
  return all(env, `SELECT w.id, w.title, w.year, w.medium, w.h_cm, w.w_cm, w.d_cm, w.price_eur, w.availability, w.description, a.display_name AS artist, a.founding
    FROM artworks w JOIN artists a ON a.id = w.artist_id WHERE w.archived = 0 AND a.account_status = 'active' ORDER BY a.display_name, w.ord`);
}

/* `at` places the pages: on the checkout Worker (local and staging) they are /gallery…; in the TEST Studio (behind Cloudflare
   Access, founder only) they are /admin/basket-gallery…, with images and the basket on the checkout Worker. */
export function places(env, url, where = 'checkout') {
  if (where === 'studio') {
    const co = String(env.CHECKOUT_ORIGIN || '').replace(/\/$/, '');
    return { list: '/admin/basket-gallery', item: id => `/admin/basket-gallery/${id}`, img: id => `${co}/staging-img/${id}.svg`, basket: `${co}/basket`, prefix: /^\/admin\/basket-gallery/ };
  }
  return { list: '/gallery', item: id => `/gallery/${id}`, img: id => `${url.origin}/staging-img/${id}.svg`, basket: '/basket', prefix: /^\/gallery/ };
}
export async function route(env, url, { page, esc, eur }, where = 'checkout') {
  const P = places(env, url, where);
  const p = url.pathname.replace(P.prefix, '/gallery');
  let mm;
  if (where === 'checkout' && url.pathname === '/') return new Response(null, { status: 302, headers: { Location: '/gallery' } });
  if (where === 'checkout' && (mm = url.pathname.match(/^\/staging-img\/([A-Za-z0-9_-]{1,64})\.svg$/))) {
    if (!(await one(env, 'SELECT 1 AS x FROM artworks WHERE id = ?', mm[1]))) return new Response('Not found', { status: 404 });
    return new Response(svg(mm[1]), { headers: { 'Content-Type': 'image/svg+xml', 'Cache-Control': 'public, max-age=3600', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'" } });
  }
  if (p === '/gallery') {
    const ws = await works(env), pv = await B.preview(env, ws.map(w => w.id).slice(0, B.MAX_LINES));
    const more = ws.length > B.MAX_LINES ? await B.preview(env, ws.map(w => w.id).slice(B.MAX_LINES, 2 * B.MAX_LINES)) : { items: [] };
    const ok = Object.fromEntries([...pv.items, ...more.items].map(i => [i.id, i]));
    const cards = ws.map(w => `<a class="card" href="${esc(P.item(w.id))}"><div class="im"><img src="${esc(P.img(w.id))}" alt="Synthetic abstract image for “${esc(w.title)}”" loading="lazy"></div>
<h3>${esc(w.title)}</h3><p>${esc(w.artist)}${w.founding ? ' · Founding Artist' : ''}</p><p>${ok[w.id] && ok[w.id].ok ? eur(ok[w.id].price_cents) + ' · can be bought online' : w.availability === 'sold' ? 'Sold' : 'Enquire'}</p></a>`).join('');
    return page(env, 'Staging gallery', `${STYLE}<p class="eyebrow">Private staging</p><h1>Artists’ Gallery</h1>
<p class="lede">Synthetic works by two synthetic artists, set up exactly as real artists would be for online purchase. Add works by both artists to one basket and pay once.</p><div class="gal">${cards}</div>`);
  }
  if ((mm = p.match(/^\/gallery\/([A-Za-z0-9_-]{1,64})$/))) {
    const w = (await works(env)).find(x => x.id === mm[1]);
    if (!w) return page(env, 'Not found', '<h1>Not found</h1>', { status: 404 });
    const it = (await B.preview(env, [w.id])).items[0] || {};
    const size = w.h_cm ? `${w.h_cm} × ${w.w_cm}${w.d_cm ? ' × ' + w.d_cm : ''} cm` : '';
    const img = P.img(w.id);
    const cta = it.ok
      ? `<p><a class="btn" href="${esc(`${P.basket}?add=${encodeURIComponent(w.id)}&img=${encodeURIComponent(img)}`)}">Add to basket</a></p><p class="small muted">One secure card payment for works from several artists. ${esc(w.artist)} is the seller and is paid directly.</p>`
      : `<p class="note">${esc(it.reason || 'This artwork can’t be bought online.')}</p>`;
    return page(env, w.title, `${STYLE}<p class="eyebrow"><a href="${esc(P.list)}">Gallery</a> / ${esc(w.artist)}</p><div class="aw"><div class="im"><img src="${esc(P.img(w.id))}" alt="Synthetic abstract image for “${esc(w.title)}”"></div>
<div><p>${esc(w.artist)}${w.founding ? '<span class="badge">Founding Artist</span>' : ''}</p><h1>${esc(w.title)}</h1><p class="price">${it.ok ? eur(it.price_cents) : w.availability === 'sold' ? 'Sold' : w.price_eur ? eur(w.price_eur * 100) : 'Price on request'}</p>
<dl class="d"><dt>Medium</dt><dd>${esc(w.medium || '')}</dd>${size ? `<dt>Size</dt><dd>${esc(size)}</dd>` : ''}${w.year ? `<dt>Year</dt><dd>${esc(w.year)}</dd>` : ''}
${it.ok ? `<dt>Delivery</dt><dd>${eur(it.delivery_cents)} · ${esc(it.delivery.window)} with ${esc(it.delivery.transporter)}; ${esc(it.delivery.tracking)}. Insured: ${esc(it.delivery.cover)}.</dd><dt>Returns</dt><dd>${esc(it.delivery.returns)}</dd><dt>Seller</dt><dd>${esc(it.seller)} (the artist)</dd>` : ''}</dl>
${w.description ? `<p>${esc(w.description)}</p>` : ''}${cta}</div></div>`);
  }
  return null;
}
