/* PlotArt Studio · gallery preview (Phase 2). A line-for-line port of atlas-tools/plotart_gallery_pages.py (Phase 1,
   approved design) so the artist previews EXACTLY what will be published. test/prove-studio.mjs renders the same
   gallery through both and requires identical markup (image file names and sizes aside). Images in a preview are
   the Studio's private preview copies, served only to the signed-in artist and the founder. */

const E = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;');
const ENQUIRY_ADDRESS = 'hello@plotnua.ie';
const STATUS = { available: 'Available', reserved: 'Reserved', sold: 'Sold', not_for_sale: 'Not for sale' };
const SHOWN = ['available', 'reserved', 'sold', 'not_for_sale'];
// Python's urllib.parse.quote (safe "/"): JS leaves !'()* alone and escapes "/".
const pyQuote = s => encodeURIComponent(s).replace(/[!'()*]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase()).replace(/%2F/g, '/');
const g6 = v => String(Number(Number(v).toPrecision(6)));

export const shown = p => p.works.filter(w => SHOWN.includes(w.availability));
const euro = n => '€' + Number(n).toLocaleString('en-US');
export function priceLine(w) {
  if (w.availability === 'available') return w.price_eur ? euro(w.price_eur) : 'Price on request';
  return STATUS[w.availability];
}
export function sizeLine(w) {
  if (!w.h_cm || !w.w_cm) return ['', ''];        // an unfinished artwork in a preview
  const dims = [w.h_cm, w.w_cm].concat(w.d_cm ? [w.d_cm] : []);
  return [dims.map(g6).join(' × ') + ' cm', dims.map(v => (v / 2.54).toFixed(1)).join(' × ') + ' in'];
}
// Preview images: one size, served from the Studio ("img/<image id>"), so the markup matches the published page.
const pick = i => ({ file: i.id, pixels: [i.pw || i.width, i.ph || i.height] });
const srcset = i => `img/${i.id} ${i.pw || i.width}w`;
const mainImage = w => w.images.find(i => i.role === 'main');

export function enquiryHref(p, w) {
  const a = p.artist;
  let subj, body;
  if (w) {
    subj = `PlotArt enquiry: ${w.title} by ${a.display_name} [PA-${a.slug}-${w.id}]`;
    body = `Hello,\n\nI'd like to ask about "${w.title}" by ${a.display_name}.\n\n`;
  } else {
    subj = `PlotArt enquiry: ${a.display_name} [PA-${a.slug}]`;
    body = `Hello,\n\nI'd like to ask about work by ${a.display_name}.\n\n`;
  }
  return `mailto:${ENQUIRY_ADDRESS}?subject=${pyQuote(subj)}&body=${pyQuote(body)}`;
}
export const metaLine = a => [a.practice, a.county].filter(Boolean).join(' · ');

export function artistBody(p) {
  const a = p.artist, works = shown(p), name = a.display_name;
  const tiles = works.map(w => {
    const im = mainImage(w), d = pick(im);
    return `\n    <li class="pa-ag-work is-${w.availability.replace(/_/g, '-')}"><a class="pa-ag-tile" href="${E(w.slug)}.html" data-pa-track="artist_artwork">` +
      `<span class="pa-ag-art"><img src="img/${E(d.file)}" srcset="${E(srcset(im))}" sizes="(max-width:639px) 92vw, (max-width:1023px) 46vw, 31vw" ` +
      `width="${d.pixels[0]}" height="${d.pixels[1]}" alt="${E(im.alt)}" loading="lazy" decoding="async"></span>` +
      `<span class="pa-ag-cap"><span class="pa-ag-title">${E(w.title)}</span><span class="pa-ag-sub">${E([w.year ? String(w.year) : null, w.medium, sizeLine(w)[0]].filter(Boolean).join(' · '))}</span>` +
      `<span class="pa-ag-status">${E(priceLine(w))}</span></span></a></li>`;
  });
  let portrait = '';
  if (a.portrait) {
    const d = pick(a.portrait);
    portrait = `<span class="pa-ag-portrait"><img src="img/${E(d.file)}" width="${d.pixels[0]}" height="${d.pixels[1]}" alt="${E(a.portrait.alt)}"></span>`;
  }
  const links = [];
  if (a.website) links.push(`<a href="${E(a.website)}" rel="noopener nofollow" data-pa-track="artist_website">Website <span aria-hidden="true">↗</span></a>`);
  if (a.instagram) links.push(`<a href="https://www.instagram.com/${E(a.instagram)}/" rel="noopener nofollow" data-pa-track="artist_instagram">Instagram <span aria-hidden="true">↗</span></a>`);
  const bio = (a.bio || '').split('\n\n').filter(x => x.trim()).map(x => `<p>${E(x.trim())}</p>`).join('');
  const meta = metaLine(a);
  return `
<section class="pa-ag-hero${portrait ? ' has-portrait' : ''}"><div class="pa-wrap">
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Virtual Gallery</a><span aria-hidden="true">/</span><span aria-current="page">${E(name)}</span></nav>
  <div class="pa-ag-id">${portrait}<div>
    ${a.founding ? '<span class="pa-gcard-badge">Founding Artist</span>' : ''}<h1>${E(name)}</h1>
    ${meta ? `<p class="pa-ag-meta">${E(meta)}</p>` : ''}${a.statement ? `<p class="pa-ag-statement">${E(a.statement)}</p>` : ''}
  </div></div>
</div></section>

<section class="pa-ag-works" aria-labelledby="agWorksH"><div class="pa-wrap">
  <div class="pa-ag-head"><h2 id="agWorksH">Works</h2><p>${works.length} ${works.length === 1 ? 'artwork' : 'artworks'}</p></div>
  <ol class="pa-ag-grid">${tiles.join('')}
  </ol>
</div></section>

<section class="pa-ag-about" aria-labelledby="agAboutH"><div class="pa-wrap pa-ag-about-in">
  <h2 id="agAboutH">About ${E(name.includes(' ') ? name.split(' ')[0] : name)}</h2>
  <div class="pa-ag-bio">${bio}${links.length ? `<p class="pa-ag-links">${links.join('')}</p>` : ''}</div>
</div></section>

<section class="pa-ag-enq"><div class="pa-wrap pa-ag-enq-in">
  <p class="pa-ag-enq-t">Interested in ${E(name)}'s work?</p>
  <p class="pa-ag-enq-l">Send an enquiry through PlotArt and we'll put you in touch with the artist.</p>
  <a class="pa-btn pa-btn--solid" href="${E(enquiryHref(p))}" data-pa-track="artist_enquiry">Enquire through PlotArt</a>
</div></section>
`;
}

export function artworkBody(p, w, prev, next) {
  const a = p.artist, imgs = w.images, im = imgs[0], d = pick(im);
  const [cm, inch] = sizeLine(w);
  const rows = [['Medium', w.medium]];
  if (w.materials) rows.push(['Materials', w.materials]);
  if (cm) rows.push(['Size', `${cm} (${inch})`]);
  if (w.year) rows.push(['Year', String(w.year)]);
  const dl = rows.map(([k, v]) => `<div><dt>${E(k)}</dt><dd>${E(v)}</dd></div>`).join('');
  const views = imgs.length > 1 ? `<ul class="pa-aw-views" aria-label="More views">${imgs.slice(1).map(i =>
    `<li><a href="img/${E(pick(i).file)}"><img src="img/${E(pick(i).file)}" alt="${E(i.alt)}" loading="lazy" decoding="async"></a></li>`).join('')}</ul>` : '';
  const credit = im.photo_credit ? ` <span>Photo: ${E(im.photo_credit)}</span>` : '';
  const av = w.availability;
  const cta = ['available', 'reserved'].includes(av)
    ? `<a class="pa-btn pa-btn--solid" href="${E(enquiryHref(p, w))}" data-pa-track="artwork_enquiry">${av === 'available' ? 'Enquire about this work' : 'Ask to be told if it becomes available'}</a>` +
      `<p class="pa-aw-cta-note">Your enquiry comes to PlotArt and is passed to ${E(a.display_name)}. PlotArt doesn't take payment: the artist arranges any sale with you directly.</p>`
    : `<a class="pa-btn pa-btn--ghost" href="${E(enquiryHref(p))}" data-pa-track="artwork_enquiry_other">Ask about ${E(a.display_name)}'s other work</a>`;
  const ai = w.ai_involvement && w.ai_involvement !== 'none' ? `<p class="pa-aw-ai"><strong>AI disclosure.</strong> ${E(w.ai_note)}</p>` : '';
  const nav = `<nav class="pa-aw-pn" aria-label="More works by ${E(a.display_name)}">${prev ? `<a href="${E(prev.slug)}.html" rel="prev"><span aria-hidden="true">←</span> ${E(prev.title)}</a>` : '<span></span>'}<a href="index.html">All works</a>${next ? `<a href="${E(next.slug)}.html" rel="next">${E(next.title)} <span aria-hidden="true">→</span></a>` : '<span></span>'}</nav>`;
  return `
<section class="pa-aw"><div class="pa-wrap">
  <nav class="pa-crumb" aria-label="Breadcrumb"><a href="../../gallery/">Virtual Gallery</a><span aria-hidden="true">/</span><a href="index.html">${E(a.display_name)}</a><span aria-hidden="true">/</span><span aria-current="page">${E(w.title)}</span></nav>
  <div class="pa-aw-in">
    <figure class="pa-aw-fig"><span class="pa-aw-frame"><img src="img/${E(d.file)}" srcset="${E(srcset(im))}" sizes="(max-width:1023px) 94vw, 62vw" width="${d.pixels[0]}" height="${d.pixels[1]}" alt="${E(im.alt)}" decoding="async" fetchpriority="high"></span>${views}
      <figcaption>${E(a.display_name)}, <i>${E(w.title)}</i>${credit}</figcaption></figure>
    <div class="pa-aw-info">
      <p class="pa-aw-artist"><a href="index.html">${E(a.display_name)}</a>${a.founding ? ' <span class="pa-gcard-badge">Founding Artist</span>' : ''}</p>
      <h1>${E(w.title)}</h1>
      <p class="pa-aw-price is-${av.replace(/_/g, '-')}">${E(priceLine(w))}</p>
      <dl class="pa-aw-dl">${dl}</dl>
      ${w.description ? `<p class="pa-aw-desc">${E(w.description)}</p>` : ''}
      <div class="pa-aw-cta">${cta}</div>
      ${ai}
    </div>
  </div>
  ${nav}
</div></section>
`;
}

const FINE = "Artworks in this gallery are offered by the artist. PlotArt introduces buyers to artists: it doesn't take payment or deliver work. Photographs of artworks are supplied by the artist and credited where taken by someone else.";
export function previewPage(title, body, bar) {
  return `<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${E(title)}</title>
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/assets/plotart.css">
<link rel="stylesheet" href="/assets/studio.css">
</head>
<body class="pa">
<div class="st-pv-bar" role="note">${bar}</div>
<header class="pa-head pa-head--pills">
  <div class="pa-wrap">
    <span class="pa-brand"><span class="pa-word">PLOTART</span><span class="pa-part"><img src="/assets/plotnua-mark.svg" alt="" width="18" height="18"><span>Part of PlotNua</span></span></span>
    <nav class="pa-pills" aria-label="PlotArt (preview: links off)"><a class="pa-pill">Discover PlotArt</a><a class="pa-pill" aria-current="page">Virtual Gallery</a><a class="pa-pill">Living Gallery</a><a class="pa-pill pa-pill--out">PlotNua <span aria-hidden="true">↗</span></a></nav>
  </div>
</header>
<main id="main">
${body}
</main>
<footer class="pa-foot"><div class="pa-wrap"><p class="fine">${E(FINE)}</p></div></footer>
</body>
</html>`;
}
