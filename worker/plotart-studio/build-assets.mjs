// Bundles the Studio interface and the approved PlotArt stylesheet into src/assets.js (run before tests and deploys).
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const here = new URL('.', import.meta.url).pathname, root = here + '../../';
const r = p => readFileSync(here + p, 'utf8');
const shell = r('ui/shell.html');
const fill = (o) => Object.entries(o).reduce((s, [k, v]) => s.replaceAll(`{${k}}`, v), shell);
const STUDIO_HTML = fill({ title: 'PlotArt Studio', home: '#/', label: 'Studio', script: '/assets/studio.js',
  tabs: '<a href="#/">Gallery</a><a href="#/works">Works</a><a href="#/profile">Profile</a><a href="#/opportunities">Opportunities</a><a href="#/enquiries">Enquiries</a><a href="#/agreement">Agreement</a><a href="/preview/" target="_blank" rel="noopener">Preview ↗</a>' });
const ADMIN_HTML = fill({ title: 'PlotArt Studio · Review desk', home: '#/', label: 'Review desk', script: '/assets/admin.js', tabs: '<a href="/admin" data-t="desk">Review desk</a><a href="/admin/applications" data-t="apps">Applications</a><a href="/admin/gallery" data-t="order">Gallery order</a><a href="/admin/ideas" data-t="ideas">Ideas</a><a href="/admin/garden" data-t="garden">Garden</a><a href="/admin/agreements" data-t="agree">Agreements</a><a href="/admin/leaving" data-t="leave">Leaving</a><a href="/admin/hire" data-t="hire">Art for Hire</a><a href="/admin/opportunities" data-t="opps">Opportunities</a>' })
  .replace('<div class="st-who" id="who"></div>', '<div class="st-who" id="who">Founder<br><a href="/cdn-cgi/access/logout">Sign out</a></div>');
// PLOTART-STUDIO-ACCESS-002: shown when Cloudflare Access has verified an email that has no invited or active artist
// account. {email} is the person's OWN verified address (HTML-escaped by the Worker). Same text for every reason.
const REFUSED_HTML = `<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PlotArt Studio · Signed in with a different email</title><meta name="robots" content="noindex, nofollow"><link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png"><link rel="stylesheet" href="/assets/plotart.css"><link rel="stylesheet" href="/assets/studio.css"></head><body class="pa st"><main class="st-refused"><img class="st-so-logo" src="/assets/brand/plotart-p-96.webp" width="64" height="64" alt=""><h1>PlotArt Studio</h1><p class="st-refused-who">You’re signed in as</p><p class="st-refused-email" data-signed-in-as>{email}</p><p>We couldn’t find an active PlotArt Studio account associated with this email address.</p><p>If you’ve already been invited, please sign in using the email address shown in your invitation.</p><a class="st-refused-out" href="/cdn-cgi/access/logout" data-signout>Sign out and use a different email</a><p class="st-refused-help">After signing out, open PlotArt Studio again and enter the address from your invitation. Still stuck? Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p></main></body></html>`;
const SIGNED_OUT_HTML = `<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PlotArt Studio</title><meta name="robots" content="noindex, nofollow"><link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32"><link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png"><link rel="stylesheet" href="/assets/plotart.css"><link rel="stylesheet" href="/assets/studio.css"></head><body class="pa st"><div class="st-signedout"><img class="st-so-logo" src="/assets/brand/plotart-p-96.webp" width="64" height="64" alt=""><h1>PlotArt</h1><p>{msg}</p></div></body></html>`;
// The approved PlotArt logo (founder approval 31 Oct 2026): the same web files the public site serves, carried as base64.
const b64 = p => readFileSync(root + p).toString('base64');
const out = { STUDIO_HTML, ADMIN_HTML, SIGNED_OUT_HTML, REFUSED_HTML, STUDIO_JS: r('ui/studio.js'), ADMIN_JS: r('ui/admin.js'), STUDIO_CSS: r('ui/studio.css'),
  PLOTART_CSS: readFileSync(root + 'plotart/assets/plotart.css', 'utf8'), MARK_SVG: readFileSync(root + 'assets/brand/plotnua-mark-master.svg', 'utf8'),
  LOGO_48_B64: b64('assets/brand/plotart-p-48.webp'), LOGO_96_B64: b64('assets/brand/plotart-p-96.webp'),
  FAVICON_32_B64: b64('assets/brand/plotart-favicon-32.png'), TOUCH_180_B64: b64('assets/brand/plotart-apple-touch-180.png') };
// The agreement texts PlotArt Studio shows and serves (agreements/build.cjs). Each served file must match the fingerprint
// recorded for it; a mismatch stops the build, so a text can never change silently under an identifier.
const AG = JSON.parse(r('agreements/issued/fingerprints.json')).documents;
const AGREEMENTS = {};
for (const [id, d] of Object.entries(AG)) {
  const h = readFileSync(here + `agreements/issued/${id}.html`), p = readFileSync(here + `agreements/issued/${id}.pdf`);
  const sha = b => createHash('sha256').update(b).digest('hex');
  if (sha(h) !== d.html_sha256 || sha(p) !== d.pdf_sha256) throw new Error(`Agreement ${id}: a served file does not match its recorded fingerprint. Refusing to build.`);
  AGREEMENTS[id] = { title: d.title, html: h.toString('utf8'), pdf_b64: p.toString('base64'), html_sha256: d.html_sha256, pdf_sha256: d.pdf_sha256 };
}
out.AGREEMENTS = AGREEMENTS;
// The Art for Hire Artist Terms (PA-AFH), once issued after legal review, live in agreements/hire-issued with the same
// fingerprint rule. Until then there is no folder and the Studio carries no text, so no artist can accept (Stage 3B-2).
const HIRE_TERMS = {};
const hf = here + 'agreements/hire-issued/fingerprints.json';
if (existsSync(hf)) for (const [id, d] of Object.entries(JSON.parse(readFileSync(hf, 'utf8')).documents)) {
  const h = readFileSync(here + `agreements/hire-issued/${id}.html`), p = readFileSync(here + `agreements/hire-issued/${id}.pdf`);
  const sha = b => createHash('sha256').update(b).digest('hex');
  if (sha(h) !== d.html_sha256 || sha(p) !== d.pdf_sha256) throw new Error(`Hire terms ${id}: a served file does not match its recorded fingerprint. Refusing to build.`);
  HIRE_TERMS[id] = { title: d.title, html: h.toString('utf8'), pdf_b64: p.toString('base64'), html_sha256: d.html_sha256, pdf_sha256: d.pdf_sha256 };
}
out.HIRE_TERMS = HIRE_TERMS;
writeFileSync(here + 'src/assets.js', '// GENERATED by build-assets.mjs. Do not edit.\n' + Object.entries(out).map(([k, v]) => `export const ${k} = ${JSON.stringify(v)};`).join('\n') + '\n');
console.log('assets.js written:', Object.keys(out).join(', '));
