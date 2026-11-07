// STAGE 3D-D1 — Rayco's installation wording, proven across every product.
//
//   node atlas-tools/prove-rayco-site-works-wording.mjs <candidate your-plot.html> \
//        <baseline your-plot.html> <universe.json> [--plant <fault>]
//
// Lifts the real cost-note function (bydTrueCostPoint), the real price view
// (pnPriceView) and the real installation label table (PN_LABEL_INSTALL) out of
// both pages with node:vm, runs them over all products in the universe, and
// requires:
//   R1  exactly ONE product's cost note differs from the baseline, and it is Rayco
//   R2  Rayco's note is the approved wording, word for word
//   R3  Rayco's note no longer says foundations are included / calls it turnkey
//   R4  Rayco's label is "Installation included" / "Foundations and site works priced separately"
//   R5  Rayco's price stays withheld: no figure, no 29,500, anywhere this code renders it
//   R6  every other installation label is unchanged
// --plant applies one fault to a COPY in memory and the run must then FAIL.
//
// With no arguments it runs on this repository: the working your-plot.html
// against the page at BASE (b7cb4dd, the last release before Stage 3D-D1).
import fs from 'node:fs'; import vm from 'node:vm'; import os from 'node:os';
import path from 'node:path'; import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BASE = 'b7cb4dd';
// STAGE 3D-D2: with no arguments the proof is pinned to the Stage 3D-D1 release itself
// (the page and universe at RELEASE against BASE), so later, separately approved stages
// that legitimately move other notes do not re-open it. The current page's Rayco wording
// is proven by prove-matching-eligibility.py.
const RELEASE = '34705c4';
const pos = process.argv.slice(2).filter((a, i, all) => a !== '--plant' && all[i - 1] !== '--plant');
let [candPath, basePath, uniPath] = pos;
if (!candPath) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'rayco-'));
  const show = (rev, f, out) => { fs.writeFileSync(out, execFileSync('git', ['show', rev + ':' + f], { cwd: ROOT, maxBuffer: 1 << 28 })); return out; };
  candPath = show(RELEASE, 'your-plot.html', path.join(tmp, 'your-plot.release.html'));
  uniPath = show(RELEASE, 'garden-room-recommendation-universe-v1.json', path.join(tmp, 'universe.release.json'));
  basePath = show(BASE, 'your-plot.html', path.join(tmp, 'your-plot.base.html'));
}
const plant = process.argv.includes('--plant') ? process.argv[process.argv.indexOf('--plant') + 1] : null;
const RAYCO = 'recDIcUb7S6pP8JCx';
const APPROVED = 'Rayco Modular Homes describes its garden rooms as installed, with foundations and site works quoted separately.';
const RAYCO_HEAD = 'TURNKEY INSTALLATION INCLUDED — FOUNDATIONS AND SITE WORKS PRICED SEPARATELY';

let cand = fs.readFileSync(candPath, 'utf8');
const base = fs.readFileSync(basePath, 'utf8');
let U = JSON.parse(fs.readFileSync(uniPath, 'utf8')).products;

if (plant === 'foundations-included') {      // fault 8: the class is lost
  cand = cand.replace(/\n\s*\{ key: 'siteWorksSeparate'[^\n]*\n/, '\n');
} else if (plant === 'unrelated-wording') {   // fault 9: another product's note changes
  cand = cand.replace("' includes installation in this price, but not the base it stands on, '",
                      "' includes installation in this price, but not the base underneath it, '");
} else if (plant === 'price-visible') {       // fault 7: Rayco's hold is lost
  U = JSON.parse(JSON.stringify(U));
  const r = U.find(p => p.productId === RAYCO || p.id === RAYCO);
  delete r.priceEvidence.presentationHold;
} else if (plant === 'turnkey-label') {
  cand = cand.replace("['Installation included', 'Foundations and site works priced separately']",
                      "['Turnkey installation included', 'Foundations and site works priced separately']");
} else if (plant) { console.error('unknown fault ' + plant); process.exit(2); }

function lift(page) {
  const slice = (a, z) => { const i = page.indexOf(a), j = page.indexOf(z, i);
    if (i < 0 || j < 0) throw new Error('slice ' + a); return page.slice(i, j); };
  const labels = slice('const PN_LABEL_INSTALL = {', '\n  };') + '\n  };';
  const code = labels + '\n' + slice('const PB046_NO_PRICE', 'function pnPriceDelta') + '\n' +
    slice('function pnVatPosition', '/* ISSUE 005 PIECE D4b') + '\n' +
    slice('const BYD_INSTALL_CLASS', '/* ---- SELECTION') +
    '\n;globalThis.__note = bydTrueCostPoint; globalThis.__view = pnPriceView; globalThis.__labels = PN_LABEL_INSTALL;';
  const ctx = { window: {} }; vm.createContext(ctx); vm.runInContext(code, ctx); return ctx;
}
const C = lift(cand), B = lift(base);
const note = (ctx, p) => { try { const c = ctx.__note(p); return c ? c.body : null; } catch (e) { return 'ERR ' + e.message; } };

const bad = [], ok = [];
const check = (n, c, d) => (c ? ok : bad).push(n + (c ? '' : ' — ' + String(d).slice(0, 240)));
const changed = [];
for (const p of U) { const id = p.productId || p.id; if (note(C, p) !== note(B, p)) changed.push(id); }
check('R1 exactly one product’s cost note changes, and it is Rayco (' + U.length + ' products tested)',
      changed.length === 1 && changed[0] === RAYCO, JSON.stringify(changed.slice(0, 5)));
const R = U.find(p => (p.productId || p.id) === RAYCO);
const rn = note(C, R);
check('R2 Rayco’s note is the approved wording', rn === APPROVED, rn);
check('R3 Rayco’s note does not say foundations are included or call it turnkey',
      rn && !/including installation and foundations|turnkey/i.test(rn), rn);
const lab = C.__labels[RAYCO_HEAD];
check('R4 Rayco’s label is Installation included / Foundations and site works priced separately',
      lab && lab[0] === 'Installation included' && lab[1] === 'Foundations and site works priced separately', JSON.stringify(lab));
const v = C.__view(R);
const shown = JSON.stringify(v) + ' ' + (rn || '');
check('R5 Rayco’s price stays withheld (no figure, no 29,500)',
      v && v.known === false && v.figure === null && v.amount === null && !/29[,.]?500/.test(shown), shown.slice(0, 200));
const lc = Object.keys(B.__labels).filter(k => k !== RAYCO_HEAD && JSON.stringify(B.__labels[k]) !== JSON.stringify(C.__labels[k]));
const added = Object.keys(C.__labels).filter(k => !(k in B.__labels));
check('R6 every other installation label is unchanged', lc.length === 0 && added.length === 0, JSON.stringify([lc, added]));

console.log(ok.map(x => 'PASS  ' + x).join('\n'));
if (bad.length) console.log(bad.map(x => 'FAIL  ' + x).join('\n'));
console.log('\nRAYCO WORDING' + (plant ? ' [planted: ' + plant + ']' : '') + ' · ' + ok.length + ' passed, ' + bad.length + ' failed');
process.exit(bad.length ? 1 : 0);
