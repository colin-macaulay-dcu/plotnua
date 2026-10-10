/* FIRST LEAD · PHASE A — PAGE-SIDE PROOF
 * ===========================================================================
 * The Worker's own suite proves the server gate. This proves the PAGE: that an
 * ordinary visitor is offered nothing, that the private route offers exactly
 * one supplier and three products, and that no promise is made on the page
 * that the evidence does not support.
 *
 * THE GATE FUNCTION IS NOT RE-IMPLEMENTED HERE. It is lifted verbatim out of
 * your-plot.html and executed, so this measures the shipped code rather than a
 * copy of it that could drift. A test that re-types the logic it is checking
 * proves only that the author can type it twice.
 *
 *     node atlas-tools/prove-first-lead.mjs
 * ========================================================================= */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const PAGE = readFileSync(join(ROOT, 'your-plot.html'), 'utf8');
const PRIVACY = readFileSync(join(ROOT, 'privacy.html'), 'utf8');

let pass = 0, fail = 0;
const rows = [];
function check(id, what, cond, detail) {
  if (cond) { pass++; rows.push(['PASS', id, what, '']); }
  else { fail++; rows.push(['FAIL', id, what, detail || '']); }
}

/* ------------------------------------------------- lift the shipped gate -- */
function liftGate(search) {
  const from = PAGE.indexOf('  const LEAD_SUPPLIERS = Object.freeze({');
  const to = PAGE.indexOf('    return sup;\n  }', from);
  if (from < 0 || to < 0) throw new Error('could not lift the gate from the page');
  const src = PAGE.slice(from, to + '    return sup;\n  }'.length);
  const fn = new Function('location', src + '\n return { leadSupplierFor, LEAD_SUPPLIERS, LEAD_ROUTE_OPEN };');
  return fn({ search });
}

const KEY = '?leadkey=a-sixteen-plus-character-key';
const open = liftGate(KEY);
const shut = liftGate('');

const YB = { organisation: 'Yardbox', productId: 'reckMDqp4tVjAjM7b' };

/* =================================================== the public state ===== */
check('F01', 'with no key in the URL the route is closed',
      shut.LEAD_ROUTE_OPEN === false);
check('F02', 'an ordinary visitor is offered nothing, even for Yard Box',
      shut.leadSupplierFor(YB) === null);
check('F03', 'a short key does not open the route',
      liftGate('?leadkey=short').leadSupplierFor(YB) === null);
check('F04', 'no key, secret or token is present anywhere in the page source',
      !/leadkey\s*[:=]\s*['"][^'"]{8,}/.test(PAGE)
      && !/x-plotnua-lead-preview['"]\s*\]\s*=\s*['"][^'"]+['"]/.test(PAGE),
      'a literal key in page source would make the private route public');

/* =================================================== the private route ==== */
check('F05', 'with a key, Yard Box is recognised',
      open.leadSupplierFor(YB) && open.leadSupplierFor(YB).orgId === 'ORG-000157');
check('F06', 'the homeowner-facing name is Yard Box, not the universe spelling',
      open.leadSupplierFor(YB).displayName === 'Yard Box');
check('F07', 'exactly three products are authorised',
      Object.keys(open.LEAD_SUPPLIERS['Yardbox'].products).length === 3);
check('F08', 'all three Yard Box products pass the gate',
      ['receaph6vCI7xtS5K', 'reckMDqp4tVjAjM7b', 'recLEonLKyhNTUiAt']
        .every(id => !!open.leadSupplierFor({ organisation: 'Yardbox', productId: id })));
check('F09', 'exactly one supplier is on the allow-list',
      Object.keys(open.LEAD_SUPPLIERS).length === 1);

/* ============================================ everything else fails closed = */
const others = [
  ['another supplier (Powersheds)',  { organisation: 'Powersheds', productId: 'recLcmGihJ0mrfdwV' }],
  ['another supplier (Sprout Pod)',  { organisation: 'Sprout Pod', productId: 'recWHATEVER00001' }],
  ['Hutsmith',                       { organisation: 'Hutsmith',   productId: 'recWHATEVER00002' }],
  ['Yard Box with an unknown product',{ organisation: 'Yardbox',   productId: 'recNOTONTHELIST1' }],
  ['Yard Box with no product id',    { organisation: 'Yardbox' }],
  ['a product with no organisation', { productId: 'reckMDqp4tVjAjM7b' }],
  ['nothing at all',                 null]
];
others.forEach(([what, p], i) => {
  check('F1' + i, what + ' is refused even with a key', open.leadSupplierFor(p) === null);
});

/* ================================================== the shipped wiring ==== */
check('F20', 'the CTA consults the gate before it is drawn',
      PAGE.includes('const leadSup = leadSupplierFor(product);'));
check('F21', 'the screen re-checks the gate when it opens',
      PAGE.includes('const sup = leadSupplierFor(product);'));
check('F22', 'the pending status is preserved for everyone else',
      PAGE.includes("rsvEl('div', 'rsv-close-pending')")
      && PAGE.includes("'Enquiry through PlotNua'"));
check('F23', 'the CTA reuses the measured slot class',
      PAGE.includes("rsvEl('button', 'rsv-close-cta',\n          'Ask '"));
check('F24', 'the lead transport is the Worker, not Formspree',
      PAGE.includes("plotnua-garden-lead") && PAGE.includes('LEAD_ENDPOINT'));
check('F25', 'success requires a persisted lead_id, not a resolved fetch',
      PAGE.includes('out.ok !== true || !out.lead_id'));
check('F26', 'the consent sentence is read from the rendered label',
      PAGE.includes("document.querySelector('.enq-consent span')"));
check('F27', 'the test route is unchanged and still test-gated',
      PAGE.includes("const ENQUIRY_TEST_MODE = new URLSearchParams(location.search).get('enquiry') === 'test';"));
check('F28', 'one outbound door still, and it is not the lead route',
      (PAGE.match(/window\.open\(/g) || []).length === 1);

/* ============================================== what travels, and what not = */
/* COMMENTS ARE STRIPPED BEFORE THIS IS SCANNED. The block explains in prose
   that a lead_id is never sent and that nothing from Resolve travels; scanning
   that prose for the very words it uses would fail the file for being clear
   about what it does not do. Only executable text is checked. */
const stripComments = (s) => s.replace(/\/\*[\s\S]*?\*\//g, ' ')
                              .replace(/(^|[^:])\/\/[^\n]*/g, '$1 ');
const payload = stripComments(
  PAGE.slice(PAGE.indexOf('  function leadPayload(){'),
             PAGE.indexOf('  async function leadSubmit(){')));
const banned = ['eircode', 'address', 'coordinate', 'latitude', 'longitude',
                'budget', 'rank', 'score', 'shortlist', 'resolve'];
check('F29', 'the lead payload carries nothing about the property',
      banned.every(k => payload.toLowerCase().indexOf(k) === -1),
      banned.filter(k => payload.toLowerCase().indexOf(k) !== -1).join(','));
check('F30', 'the lead payload does not send a lead_id',
      payload.indexOf('lead_id') === -1);

/* ================================================== homeowner promises ==== */
const cta = PAGE.slice(PAGE.indexOf('const leadSup = leadSupplierFor(product);'),
                       PAGE.indexOf("rsvEl('div', 'rsv-close-pending')"));
check('F31', 'the CTA claims no price, currency, VAT or warranty',
      !/€|\bVAT\b|warrant|GBP|£/i.test(cta), cta.slice(0, 80));
check('F32', 'the CTA does not say groundworks are included',
      !/groundwork|foundation/i.test(cta));
check('F33', 'no response time is promised anywhere in the success wording',
      !/within a working day|within \d+ (hour|day)/i.test(PAGE));
check('F34', 'the live success wording exists and names the supplier',
      PAGE.includes('will pass it to')
      && PAGE.includes("enquiryMode === 'lead'"));

/* ========================================================= the privacy ==== */
check('F35', 'privacy names PlotNua’s own enquiry service, not only Formspree',
      /PlotNua[\u2019']s own enquiry service/.test(PRIVACY));
check('F36', 'privacy says the enquiry is recorded, and what is recorded',
      /records the enquiry in PlotNua[\u2019']s own records/.test(PRIVACY)
      && PRIVACY.includes('the wording of the consent you agreed to'));
check('F37', 'privacy says a person forwards it, not an automated send',
      PRIVACY.includes('A person at PlotNua does this; it is not sent automatically.'));
check('F38', 'privacy still lists what is never sent',
      PRIVACY.includes('your Eircode;') && PRIVACY.includes('any PlotNua ranking or score.'));

/* ============================================================== output ==== */
console.log('\n  FIRST LEAD · PHASE A — PAGE-SIDE PROOF\n');
for (const [s, id, what, detail] of rows) {
  console.log('  [' + s + '] ' + id + '  ' + what + (detail ? '  — ' + detail : ''));
}
console.log('\n  ' + pass + ' passed, ' + fail + ' failed\n');
process.exit(fail ? 1 : 0);
