/* PlotArt payment pilot texts: builds the ISSUE FORM of the payment addendum (PA-PAY) and buyer purchase terms (PA-BPT)
   from the founder-reviewed drafts in payment-drafts/, into payment-ready/ with their fingerprints.

   payment-ready/ is NOT bundled by build-assets.mjs (it reads only payment-issued/). Issuing is a separate, founder-approved
   step: move the two files and fingerprints.json to payment-issued/ unchanged, then install them with migration
   0018_payment_terms_issue.sql. Once anyone has accepted an identifier, its file must never change (a changed text gets a
   new identifier), exactly as for PA-GAA (agreements/build.cjs).

   The issue form differs from the draft only by: the review status line and draft footer are removed; the draft heading
   suffix is removed; {issue date} becomes ISSUE_DATE. The texts are the same for every order: the quote and the purchase
   confirmation carry each order's own details, so no other placeholder is allowed.
     node agreements/build-payment.cjs */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const HERE = __dirname, SRC = path.join(HERE, 'payment-drafts'), OUT = path.join(HERE, 'payment-ready');
const ISSUE_DATE = '20 November 2026';
const DOCS = [
  { id: 'PA-PAY-2026-11', kind: 'artist_payment_addendum', title: 'Payment Pilot Addendum', file: 'PA-PAY-2026-11-DRAFT.md',
    footer: 'PlotArt Payment Pilot Addendum · PA-PAY-2026-11 · PlotArt, an initiative of PlotNua, operated by Colin MacAulay (registered as Colin Macaulay), CRO business name no. 794392' },
  { id: 'PA-BPT-2026-11', kind: 'buyer_purchase_terms', title: 'Buyer Purchase Terms', file: 'PA-BPT-2026-11-DRAFT.md',
    footer: 'PlotArt Buyer Purchase Terms · PA-BPT-2026-11 · PlotArt, an initiative of PlotNua, operated by Colin MacAulay (registered as Colin Macaulay), CRO business name no. 794392' },
];

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const inline = s => esc(s).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function issueText(d) {
  let t = fs.readFileSync(path.join(SRC, d.file), 'utf8');
  t = t.split('\n').filter(l => !l.startsWith('**Status:')).join('\n');
  t = t.replace(/\n---\n[\s\S]*$/, '\n');                         // draft footer
  t = t.replace(/^# .*$/m, '');                                    // heading (rebuilt below)
  t = t.replace(/\{issue date\}/g, ISSUE_DATE);
  if (/\{[^}]+\}/.test(t)) throw new Error(`${d.id}: unfilled placeholder ${t.match(/\{[^}]+\}/)[0]}`);
  if (/DRAFT|For professional review|\[for review/i.test(t)) throw new Error(`${d.id}: draft wording left in the issue form`);
  return t.trim();
}

function toHtml(d, md) {
  const out = []; let list = null, table = null;
  const flushList = () => { if (list) { out.push(`<ul>${list.map(i => `<li>${inline(i)}</li>`).join('')}</ul>`); list = null; } };
  const flushTable = () => {
    if (!table) return;
    const rows = table.filter(r => !/^\|[-\s|]+\|$/.test(r)).map(r => r.replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
    const [head, ...body] = rows, hasHead = head.some(c => c);
    out.push(`<table>${hasHead ? `<thead><tr>${head.map(c => `<th scope="col">${inline(c)}</th>`).join('')}</tr></thead>` : ''}<tbody>${body.map(r => `<tr>${r.map((c, i) => i ? `<td>${inline(c)}</td>` : `<th scope="row">${inline(c)}</th>`).join('')}</tr>`).join('')}</tbody></table>`);
    table = null;
  };
  for (const raw of md.split('\n')) {
    const l = raw.replace(/\s+$/, '');
    if (l.startsWith('|')) { flushList(); (table ||= []).push(l); continue; }
    flushTable();
    if (!l.trim()) { flushList(); continue; }
    let m;
    if ((m = l.match(/^## (.*)$/))) { flushList(); out.push(`<h2 id="${slug(m[1])}">${esc(m[1])}</h2>`); }
    else if ((m = l.match(/^(\d+\.\d+) (.*)$/))) { flushList(); out.push(`<p class="cl" id="c${m[1]}"><span class="n">${m[1]}</span><span>${inline(m[2])}</span></p>`); }
    else if ((m = l.match(/^\s+(.*)$/))) (list ||= []).push(m[1]);
    else { flushList(); out.push(`<p>${inline(l)}</p>`); }
  }
  flushList(); flushTable();
  return `<!DOCTYPE html>
<html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PlotArt ${esc(d.title)} · ${esc(d.id)}</title><meta name="robots" content="noindex, nofollow">
<style>
:root{color-scheme:light}body{margin:0;background:#F4F1EC;color:#1B1C1E;font:16px/1.6 Arial,Helvetica,sans-serif}
main{max-width:46rem;margin:0 auto;padding:2.5rem 1rem 4rem}.eyebrow{margin:0;color:#AE6245;font-weight:700;letter-spacing:.18em;font-size:.8rem}
h1{font:400 2.1rem/1.15 Georgia,serif;margin:.3rem 0 .4rem}.sub{margin:0 0 2rem;color:#5E5A55;font-size:.95rem}
h2{font:400 1.3rem/1.3 Georgia,serif;margin:2.2rem 0 .7rem}p{margin:0 0 .8rem}.cl{display:grid;grid-template-columns:3rem minmax(0,1fr)}
.cl .n{font-weight:700}ul{margin:0 0 .9rem 3rem;padding-left:0;list-style:none}li{margin:0 0 .35rem}
table{width:100%;border-collapse:collapse;margin:.6rem 0 1.4rem;font-size:.92rem}th,td{text-align:left;vertical-align:top;border:1px solid #D8D1C7;padding:.55rem .65rem}
thead th{background:#EFEBE5}tbody th{font-weight:400;width:60%}footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #C9C2B8;color:#5E5A55;font-size:.85rem}
@media (max-width:30rem){.cl{grid-template-columns:2.6rem minmax(0,1fr)}ul{margin-left:2.6rem}h1{font-size:1.75rem}}
@media print{body{background:#fff}main{padding:0}}
</style></head>
<body><main><article data-doc="${esc(d.id)}">
<p class="eyebrow">PLOTART</p>
<h1>${esc(d.title)}</h1>
<p class="sub">Identifier ${esc(d.id)} · Text of ${ISSUE_DATE}</p>
${out.join('\n')}
</article>
<footer>${esc(d.footer)} · plotnua.ie · hello@plotnua.ie</footer></main></body></html>
`;
}

fs.mkdirSync(OUT, { recursive: true });
const prints = { note: 'Ready for issue, NOT issued. Founder approval moves these files unchanged to payment-issued/ and migration 0018 installs them. Once anyone has accepted an identifier, its file must never change.', documents: {} };
for (const d of DOCS) {
  const h = toHtml(d, issueText(d));
  fs.writeFileSync(path.join(OUT, `${d.id}.html`), h);
  prints.documents[d.id] = { title: `PlotArt ${d.title}`, kind: d.kind, html_sha256: crypto.createHash('sha256').update(h).digest('hex') };
}
fs.writeFileSync(path.join(OUT, 'fingerprints.json'), JSON.stringify(prints, null, 1) + '\n');
console.log(JSON.stringify(prints, null, 1));
