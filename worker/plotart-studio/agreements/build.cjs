/* PlotArt Studio · agreement texts (Founding Artist Agreement PA-FAA-2026-11 and Gallery Publication and Image Licence
   PA-GPIL-2026-11). Builds the ISSUE FORM of each approved text from source/*.cjs, the same clause text as the founder's
   approved package of 6 November 2026, with only the review status note removed and the sub-title line shortened:
     issued/<ID>.html  the exact page PlotArt Studio shows (and fingerprints)
     issued/<ID>.docx  Word copy (not served; for the founder's records)
     issued/<ID>.pdf   the download PlotArt Studio serves (and fingerprints), made from the .docx by LibreOffice
     issued/fingerprints.json   SHA-256 of each served file
   Run ONLY when a text changes (it needs the docx package and LibreOffice):  node agreements/build.cjs
   A changed text is a NEW identifier, never a rebuild of an existing one, once an identifier has been accepted by anyone:
   its files must never change. (PA-GPIL-2026-11 clause 6.4 gained one sentence on 6 Nov 2026, founder decision W1, before
   anyone had accepted it, so it keeps its identifier.) build-assets.mjs refuses to bundle a file whose fingerprint does not match. */
const fs = require('fs'), path = require('path'), crypto = require('crypto'), { execFileSync } = require('child_process');
const HERE = __dirname, OUT = path.join(HERE, 'issued');
const { build } = require('./source/docx.cjs');
const ALL = [require('./source/PA-FAA-2026-11.cjs'), require('./source/PA-GPIL-2026-11.cjs')];
// node agreements/build.cjs [ID ...]: rebuild only the named documents; every other document's files and fingerprints are
// kept byte for byte (a PDF rebuilt from unchanged text would still get new bytes, so it is never rebuilt needlessly).
const ONLY = process.argv.slice(2);
const DOCS = ONLY.length ? ALL.filter(d => ONLY.includes(d.id)) : ALL;
const DATE = '6 November 2026';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const inline = s => esc(s).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function html(doc) {
  const out = [];
  let list = null;
  const flush = () => { if (list) { out.push(`<ul>${list.join('')}</ul>`); list = null; } };
  for (const [kind, a, b] of doc.blocks) {
    if (kind !== 'b') flush();
    if (kind === 'h' || kind === 'hpb') out.push(`<h2 id="${slug(a)}">${esc(a)}</h2>`);
    else if (kind === 'c') out.push(`<p class="cl" id="c${esc(a)}"><span class="n">${esc(a)}</span><span>${inline(b)}</span></p>`);
    else if (kind === 'p') out.push(`<p>${inline(a)}</p>`);
    else if (kind === 'b') (list ||= []).push(`<li>${inline(a)}</li>`);
    else if (kind === 'quote') out.push(`<blockquote>${inline(a)}</blockquote>`);
    else if (kind === 't') out.push(`<table><thead><tr>${a[0].map(c => `<th scope="col">${inline(c)}</th>`).join('')}</tr></thead><tbody>${a.slice(1).map(r => `<tr>${r.map((c, i) => i ? `<td>${inline(c)}</td>` : `<th scope="row">${inline(c)}</th>`).join('')}</tr>`).join('')}</tbody></table>`);
  }
  flush();
  return `<!DOCTYPE html>
<html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PlotArt ${esc(doc.title)} · ${esc(doc.id)}</title><meta name="robots" content="noindex, nofollow">
<style>
:root{color-scheme:light}body{margin:0;background:#F4F1EC;color:#1B1C1E;font:16px/1.6 Arial,Helvetica,sans-serif}
main{max-width:46rem;margin:0 auto;padding:2.5rem 1rem 4rem}.eyebrow{margin:0;color:#AE6245;font-weight:700;letter-spacing:.18em;font-size:.8rem}
h1{font:400 2.1rem/1.15 Georgia,serif;margin:.3rem 0 .4rem}.sub{margin:0 0 2rem;color:#5E5A55;font-size:.95rem}
h2{font:400 1.3rem/1.3 Georgia,serif;margin:2.2rem 0 .7rem}p{margin:0 0 .8rem}.cl{display:grid;grid-template-columns:3rem minmax(0,1fr)}
.cl .n{font-weight:700}ul{margin:0 0 .9rem 3rem;padding-left:1.1rem}li{margin:0 0 .35rem}
blockquote{margin:.6rem 0 1.1rem 3rem;padding:.2rem 0 .2rem 1rem;border-left:3px solid #C9C2B8;font-style:italic}
table{width:100%;border-collapse:collapse;margin:.6rem 0 1.4rem;font-size:.92rem}th,td{text-align:left;vertical-align:top;border:1px solid #D8D1C7;padding:.55rem .65rem}
thead th{background:#EFEBE5}tbody th{font-weight:700;width:34%}footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #C9C2B8;color:#5E5A55;font-size:.85rem}
@media (max-width:30rem){.cl{grid-template-columns:2.6rem minmax(0,1fr)}ul,blockquote{margin-left:2.6rem}h1{font-size:1.75rem}}
@media print{body{background:#fff}main{padding:0}}
</style></head>
<body><main><article data-doc="${esc(doc.id)}">
<p class="eyebrow">PLOTART</p>
<h1>${esc(doc.title)}</h1>
<p class="sub">Identifier ${esc(doc.id)} · Text of ${DATE}</p>
${out.join('\n')}
</article>
<footer>${esc(doc.footer)} · plotnua.ie · hello@plotnua.ie</footer></main></body></html>
`;
}

(async () => {
  const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
  const prev = fs.existsSync(path.join(OUT, 'fingerprints.json')) ? JSON.parse(fs.readFileSync(path.join(OUT, 'fingerprints.json'), 'utf8')).documents : {};
  const prints = { note: 'SHA-256 of the exact files PlotArt Studio serves. Once anyone has accepted an identifier, changing any of its files needs a new identifier.', documents: { ...prev } };
  for (const d of DOCS) {
    const issue = { ...d, status: null, sub: `Identifier ${d.id}  ·  Text of ${DATE}` };
    fs.writeFileSync(path.join(OUT, `${d.id}.html`), html(issue));
    const docx = path.join(OUT, `${d.id}.docx`);
    await build(issue, docx);
    execFileSync('soffice', ['--headless', '--convert-to', 'pdf', '--outdir', OUT, docx], { stdio: 'ignore' });
    prints.documents[d.id] = { title: `PlotArt ${d.title}`, html_sha256: sha(path.join(OUT, `${d.id}.html`)), pdf_sha256: sha(path.join(OUT, `${d.id}.pdf`)) };
  }
  fs.writeFileSync(path.join(OUT, 'fingerprints.json'), JSON.stringify(prints, null, 2) + '\n');
  console.log(JSON.stringify(prints, null, 2));
})();
