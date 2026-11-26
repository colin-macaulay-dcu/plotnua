// PROVE · supplier referral attribution in Your Plot (Package N, founder-approved principles, 26 Nov 2026).
// Extracts pnReferralUrl() and pnSupplierHandover() from your-plot.html and proves: the four utm_* tags are added and
// nothing else; a supplier's own query is kept; only https links are touched; the stage label cannot smuggle data; the
// single outbound door sends the origin only (noopener, no noreferrer) and stays the only window.open in the page.
//   node atlas-tools/prove-referral-attribution.mjs
import { readFileSync } from 'node:fs';
const PAGE = readFileSync(new URL('../your-plot.html', import.meta.url), 'utf8');
const results = [];
const check = (id, what, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${id} ${what}${!ok && d ? `  [${d}]` : ''}`); };
const grab = name => { const i = PAGE.indexOf(`function ${name}(`); let depth = 0, j = PAGE.indexOf('{', i);
  for (let k = j; k < PAGE.length; k++) { if (PAGE[k] === '{') depth++; else if (PAGE[k] === '}' && --depth === 0) return PAGE.slice(i, k + 1); } return null; };
const src = grab('pnReferralUrl');
check('R0', 'pnReferralUrl() exists once', src && PAGE.split('function pnReferralUrl(').length === 2);
const fn = new Function(src + '; return pnReferralUrl;')();
const u = new URL(fn('https://maker.example/garden-rooms/12?colour=oak', 'resolve'));
check('R1', 'adds utm_source=plotnua, utm_medium=referral, utm_campaign=your-plot, utm_content=<stage>',
  u.searchParams.get('utm_source') === 'plotnua' && u.searchParams.get('utm_medium') === 'referral' && u.searchParams.get('utm_campaign') === 'your-plot' && u.searchParams.get('utm_content') === 'resolve');
check('R2', "keeps the supplier's own path and query", u.pathname === '/garden-rooms/12' && u.searchParams.get('colour') === 'oak');
check('R3', 'adds nothing else (no homeowner data of any kind)', [...u.searchParams.keys()].sort().join() === 'colour,utm_campaign,utm_content,utm_medium,utm_source');
check('R4', 'a stage label that is not a plain word cannot carry data', new URL(fn('https://m.example/', 'D02 X2Y3 Cork €30k')).searchParams.get('utm_content') === 'option');
check('R5', 'only https links are changed; anything unparsable is passed through untouched', fn('http://m.example/', 'x') === 'http://m.example/' && fn('not a url', 'x') === 'not a url');
const door = grab('pnSupplierHandover');
check('R6', "the single outbound door uses the referral URL and 'noopener' only (origin-only referrer)",
  /window\.open\(pnReferralUrl\(next\.href, action\), '_blank', 'noopener'\)/.test(door) && !/noreferrer/.test(door));
check('R7', 'window.open( still appears exactly once in your-plot.html (contract J07)', PAGE.split('window.open(').length === 2);
const fail = results.filter(x => !x).length;
console.log(`\nREFERRAL ATTRIBUTION · ${results.length} checks, ${results.length - fail} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
