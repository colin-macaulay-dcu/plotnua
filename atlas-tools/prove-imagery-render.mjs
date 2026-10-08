#!/usr/bin/env node
/* END-TO-END PROOF — governed imagery actually reaches the render.
 * ===========================================================================
 * Drives the REAL pnAuthorisedImage() lifted from your-plot.html against the
 * REAL universe artefact, and simulates normalizePoolProduct's contract.
 *
 * A  Powersheds   : eligible -> imagery resolved -> renders
 * B  Yard Box     : eligible -> imagery resolved -> renders
 * C  no permission: eligible -> image-free treatment
 * D  withdrawal   : same match, photograph gone, no scoring corruption
 *
 * Plus the adversarial cases, because a rights check nobody can fail is not
 * a rights check.
 *
 * Run:  node atlas-tools/prove-imagery-render.mjs
 */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const src = readFileSync(join(REPO, 'your-plot.html'), 'utf8');

const a = src.indexOf('  function pnAuthorisedImage(product){');
const b = src.indexOf('  function normalizePoolProduct(raw){');
if (a < 0 || b <= a) { console.log('ABORT: could not lift the resolver'); process.exit(1); }
const tmp = join(HERE, '.rights-lifted.cjs');
writeFileSync(tmp, src.slice(a, b) + '\nmodule.exports={pnAuthorisedImage};\n');
const require = createRequire(import.meta.url);
const { pnAuthorisedImage } = require(tmp);

const uni = JSON.parse(readFileSync(join(REPO, 'garden-room-recommendation-universe-v1.json'), 'utf8'));

/* THE REAL NORMALISATION CONTRACT, mirrored from normalizePoolProduct so the
   proof tests what the page actually builds rather than the raw artefact. */
const normalise = (raw) => ({
  id: raw.id, name: raw.name, organisation: raw.organisation,
  imagery: raw.imagery || undefined,
  imageUrl: (raw.imagery && raw.imagery.url) || undefined,
  imageCredit: (raw.imagery && raw.imagery.credit) || undefined,
  imageRightsStatus: raw.imagery ? 'authorised' : 'unconfirmed',
});

let ok = true;
const check = (n, pass, d) => { if (!pass) ok = false;
  console.log('  ' + (pass ? 'ok  ' : 'FAIL') + '  ' + n + (d ? '   ' + d : '')); };

console.log('END-TO-END PROOF — governed imagery reaches the render');
console.log('='.repeat(78));

const raws = uni.products;
/* Organisation renamed 2026-10-08 on the supplier's own correction
   (Jack Sutcliffe, Powersheds). This is an ASSERTION on the live
   organisation value, so it had to move with the data — it failed on the
   first guard run after the rename, which is the guard working. */
const ps = raws.filter(p => p.organisation === 'Powersheds' && p.imagery);
const yb = raws.filter(p => p.organisation === 'Yardbox' && p.imagery);
const none = raws.filter(p => !p.imagery);

console.log('\nCOVERAGE');
console.log('-'.repeat(78));
console.log('    universe products          : ' + raws.length);
console.log('    carrying governed imagery  : ' + raws.filter(p => p.imagery).length);
check('Powersheds products with imagery = 3', ps.length === 3);
check('Yard Box products with imagery = 3', yb.length === 3);

console.log('\nA — POWER SHEDS RENDERS');
console.log('-'.repeat(78));
for (const raw of ps) {
  const p = normalise(raw);
  const im = pnAuthorisedImage(p);
  check('renders: ' + p.name, !!im);
  if (im) {
    console.log('        src    ' + im.url.slice(0, 92));
    console.log('        credit ' + im.credit + '   alt "' + im.alt + '"');
    check('  credit present for ' + p.name, !!im.credit);
    check('  url inside the permitted scope', im.url.indexOf(im.permittedPrefix) === 0);
    check('  rights record travels with it', !!im.rightsRecord, im.rightsRecord);
  }
}

console.log('\nB — YARD BOX RENDERS');
console.log('-'.repeat(78));
for (const raw of yb) {
  const p = normalise(raw);
  const im = pnAuthorisedImage(p);
  check('renders: ' + p.name, !!im);
  if (im) {
    console.log('        src    ' + im.url.slice(0, 92));
    console.log('        credit ' + im.credit);
    check('  credit present for ' + p.name, !!im.credit);
    check('  url inside the permitted scope', im.url.indexOf(im.permittedPrefix) === 0);
  }
}

console.log('\nC — NO PERMISSION: eligible, image-free, intentional');
console.log('-'.repeat(78));
const c = normalise(none[0]);
check('a product without a grant resolves no image', pnAuthorisedImage(c) === null,
      '(' + c.name + ')');
check('its rights status reads unconfirmed', c.imageRightsStatus === 'unconfirmed');
check('it is still a complete, usable product record', !!c.name && !!c.organisation);
check('every ungranted product in the universe resolves null',
      none.every(r => pnAuthorisedImage(normalise(r)) === null),
      none.length + ' checked');

console.log('\nD — WITHDRAWAL');
console.log('-'.repeat(78));
const beforeW = normalise(ps[0]);
const wraw = JSON.parse(JSON.stringify(ps[0]));
delete wraw.imagery;                    // exactly what re-running the resolver does
const afterW = normalise(wraw);
check('before withdrawal the photograph renders', !!pnAuthorisedImage(beforeW));
check('after withdrawal it does not', pnAuthorisedImage(afterW) === null);
check('the product is still present and matchable',
      afterW.name === beforeW.name && afterW.organisation === beforeW.organisation);
check('no matching field was altered by losing the image',
      afterW.id === beforeW.id && afterW.name === beforeW.name);

console.log('\nADVERSARIAL — the check must be capable of refusing');
console.log('-'.repeat(78));
const mut = (fn) => { const p = normalise(ps[0]); const c2 = JSON.parse(JSON.stringify(p)); fn(c2); return pnAuthorisedImage(c2); };
check('credit stripped            -> refused', mut(p => delete p.imagery.credit) === null);
check('rights record stripped     -> refused', mut(p => delete p.imagery.rightsRecord) === null);
check('supplier stripped          -> refused', mut(p => delete p.imagery.supplier) === null);
check('scope stripped             -> refused', mut(p => delete p.imagery.permittedPrefix) === null);
check('url moved outside scope    -> refused',
      mut(p => { p.imagery.url = 'https://cdn.example.com/someone-elses/photo.jpg'; }) === null);
check('same host, different tenant-> refused',
      mut(p => { const u = new URL(p.imagery.url); p.imagery.url = u.origin + '/s/files/1/9999/9999/x.jpg'; }) === null);
check('downgraded to http         -> refused',
      mut(p => { p.imagery.url = p.imagery.url.replace('https://', 'http://'); }) === null);
check('UNKNOWN (no imagery block) -> refused', pnAuthorisedImage({ name: 'x' }) === null);
check('legacy bare imageUrl alone -> refused',
      pnAuthorisedImage({ name: 'x', imageUrl: 'https://anywhere.example/p.jpg' }) === null);

try { unlinkSync(tmp); } catch (e) { /* best effort */ }
console.log('\n' + '='.repeat(78));
console.log(ok ? 'PROOF COMPLETE — authorised photographs render, everything else falls back'
              : 'PROOF INCOMPLETE — see FAIL above');
process.exit(ok ? 0 : 1);
