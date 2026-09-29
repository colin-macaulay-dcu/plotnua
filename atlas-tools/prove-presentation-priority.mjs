#!/usr/bin/env node
/* NON-DISTORTION PROOF — the presentation-priority layer.
 * ===========================================================================
 * Drives the ACTUAL functions shipped in your-plot.html (lifted verbatim, not
 * reimplemented) against rows built from the REAL universe artefact.
 *
 * The claim under test is narrow and total:
 *
 *     PRESENTATION PRIORITY CHANGES THE ORDER PEOPLE SEE.
 *     IT CHANGES NOTHING ABOUT WHAT IS SUITABLE.
 *
 * So every test below either (a) shows imagery moving an ELIGIBLE candidate
 * up, or (b) shows that it cannot move anything that was not already in the
 * eligible, comparable set the engine handed over.
 *
 * Run:  node atlas-tools/prove-presentation-priority.mjs
 */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const PAGE = join(REPO, 'your-plot.html');
const UNI = join(REPO, 'garden-room-recommendation-universe-v1.json');

/* LIFT THE REAL CODE. Testing a copy would prove only that the copy works. */
const src = readFileSync(PAGE, 'utf8');
const a = src.indexOf('  function pnPresentationTier(product){');
const b = src.indexOf('  function rankCandidates(decisionProfile){');
if (a < 0 || b < 0 || b <= a) {
  console.log('ABORT: could not lift the presentation functions from the page');
  process.exit(1);
}
const lifted = join(HERE, '.pp-lifted.cjs');
writeFileSync(lifted,
  src.slice(a, b) + '\nmodule.exports={pnPresentationTier,pnApplyPresentationPriority};\n');
const require = createRequire(import.meta.url);
const { pnPresentationTier, pnApplyPresentationPriority } = require(lifted);

const uni = JSON.parse(readFileSync(UNI, 'utf8'));
const P = (name) => {
  const p = uni.products.find(x => x.name === name);
  if (!p) { console.log('ABORT: product not in universe: ' + name); process.exit(1); }
  return p;
};
const rows = (...ps) => ps.map(p => ({ product: p, _id: p.productId }));
const names = (rs) => rs.map(r => r.product.name);

let ok = true;
function check(name, pass, detail) {
  if (!pass) ok = false;
  console.log('  ' + (pass ? 'ok  ' : 'FAIL') + '  ' + name + (detail ? '   ' + detail : ''));
}

console.log('NON-DISTORTION PROOF — presentation priority');
console.log('='.repeat(76));

/* Real products. Three carry authorised imagery, the rest do not. */
const PS12 = P('12x12 Apex Classic Log Cabin');      // imagery
const PS16 = P('16x12 Apex Log Cabin');              // imagery
const YBW  = P('Yardbox The Whistler');              // imagery
const noImg = uni.products.filter(p => !p.imagery).slice(0, 6);

console.log('\nTIER RESOLUTION');
console.log('-'.repeat(76));
check('a product with a resolved grant-backed image is tier A',
      pnPresentationTier(PS12) === 'A');
check('a product with no imagery block is tier B',
      pnPresentationTier(noImg[0]) === 'B', '(' + noImg[0].name + ')');
check('UNKNOWN permission can never be tier A — no block, no tier A',
      pnPresentationTier({ name: 'x' }) === 'B');
/* THE CREDIT IS PART OF THE TEST. An image whose attribution went missing is
   not publishable, so it must not be presentable either. */
const stripped = JSON.parse(JSON.stringify(PS12));
delete stripped.imagery.credit;
check('an image whose required credit is missing is NOT tier A',
      pnPresentationTier(stripped) === 'B');
const noUrl = JSON.parse(JSON.stringify(PS12));
delete noUrl.imagery.url;
check('an imagery block with no url is NOT tier A',
      pnPresentationTier(noUrl) === 'B');

console.log('\nWORKED EXAMPLE 1 — two equally eligible candidates, one with imagery');
console.log('-'.repeat(76));
/* Both are in `rows`, so the engine has already ruled them comparable. The
   head is held fixed; the imagery-bearing candidate rises within the tail. */
const e1 = rows(noImg[0], noImg[1], PS12, noImg[2]);
const before1 = names(e1);
pnApplyPresentationPriority(e1);
const after1 = names(e1);
console.log('    before: ' + before1.join('  |  '));
console.log('    after : ' + after1.join('  |  '));
check('the imagery-authorised candidate moves up',
      after1.indexOf(PS12.name) < before1.indexOf(PS12.name),
      'position ' + before1.indexOf(PS12.name) + ' -> ' + after1.indexOf(PS12.name));
check('it surfaces immediately after the headline recommendation',
      after1[1] === PS12.name);
check('no candidate is dropped or duplicated',
      after1.length === before1.length
      && new Set(after1).size === new Set(before1).size
      && before1.every(n => after1.includes(n)));
check('the non-imagery candidates keep their order relative to each other',
      after1.filter(n => n !== PS12.name).join('|')
      === before1.filter(n => n !== PS12.name).join('|'));

console.log('\nWORKED EXAMPLE 2 — the stronger factual match has no imagery');
console.log('-'.repeat(76));
/* rows[0] is Best Overall: the product PlotNua says it would start with. It
   is a MATCH claim, so imagery must not be able to take it. */
const e2 = rows(noImg[0], PS12, PS16, noImg[1]);
const before2 = names(e2);
pnApplyPresentationPriority(e2);
const after2 = names(e2);
console.log('    before: ' + before2.join('  |  '));
console.log('    after : ' + after2.join('  |  '));
check('the image-free strongest match KEEPS position 1',
      after2[0] === noImg[0].name, '(' + noImg[0].name + ')');
check('image-rich candidates still cannot displace it',
      after2[0] !== PS12.name && after2[0] !== PS16.name);

console.log('\nINELIGIBILITY — imagery cannot manufacture a candidate');
console.log('-'.repeat(76));
/* The decisive structural fact: this function only ever reorders the array it
   is given. A product the engine excluded is not in that array, so no amount
   of imagery can put it there. Proven by construction, not by assertion. */
const excluded = PS12;
const e3 = rows(noImg[0], noImg[1], noImg[2]);
const before3 = names(e3);
pnApplyPresentationPriority(e3);
check('an excluded image-rich product does not appear in the results',
      !names(e3).includes(excluded.name));
check('an all-tier-B set is returned completely unchanged',
      names(e3).join('|') === before3.join('|'));

console.log('\nWITHDRAWAL — rich presentation disappears, order returns to factual');
console.log('-'.repeat(76));
const wdrawn = JSON.parse(JSON.stringify(PS12));
delete wdrawn.imagery;
const e4 = rows(noImg[0], noImg[1], wdrawn, noImg[2]);
const before4 = names(e4);
pnApplyPresentationPriority(e4);
check('with the grant withdrawn the candidate stops being promoted',
      names(e4).join('|') === before4.join('|'));
check('and it is still present — eligibility was never touched',
      names(e4).includes(wdrawn.name));

console.log('\nTHE EFFECT SHRINKS AS THE ESTATE GROWS');
console.log('-'.repeat(76));
/* When every eligible candidate has imagery, a stable partition is the
   identity. The boost is loud now precisely because the estate is small, and
   becomes invisible as it widens — which is what the brief asks for. */
const allA = rows(PS12, PS16, YBW);
const beforeAll = names(allA);
pnApplyPresentationPriority(allA);
check('when every candidate has imagery the order is unchanged',
      names(allA).join('|') === beforeAll.join('|'));

console.log('\nSHAPE SAFETY');
console.log('-'.repeat(76));
const tiny = rows(PS12, noImg[0]);
const beforeTiny = names(tiny);
pnApplyPresentationPriority(tiny);
check('a two-row set is left alone (nothing meaningful to reorder)',
      names(tiny).join('|') === beforeTiny.join('|'));
check('a non-array input is returned without throwing',
      pnApplyPresentationPriority(null) === null);

/* The non-enumerable contracts other consumers depend on must survive an
   in-place reorder. */
const e5 = rows(noImg[0], noImg[1], PS12, noImg[2]);
Object.defineProperty(e5, '__scored', { value: ['sentinel'], enumerable: false });
Object.defineProperty(e5, '__eligible', { value: ['sentinel2'], enumerable: false });
pnApplyPresentationPriority(e5);
check('__scored survives the in-place reorder',
      e5.__scored && e5.__scored[0] === 'sentinel');
check('__eligible survives the in-place reorder',
      e5.__eligible && e5.__eligible[0] === 'sentinel2');
check('the presentation trace is recorded for audit',
      !!e5.__presentationPriority && e5.__presentationPriority.headUntouched === true);

console.log('\n' + '='.repeat(76));
console.log(ok ? 'PROOF COMPLETE — presentation reordered, suitability untouched'
                : 'PROOF INCOMPLETE — see FAIL above');
process.exit(ok ? 0 : 1);
