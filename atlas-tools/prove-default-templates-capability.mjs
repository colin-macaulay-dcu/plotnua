/* DEFAULT-TEMPLATE GUARD · CAPABILITY PROOF FOR THE FIRST LEAD EXCEPTION
 * ===========================================================================
 * prove-default-templates.js asserts that no supplier is named in the default
 * product journey, with two recorded exceptions: the frozen supplier-county
 * data, and -- added under RECORDED EXCEPTION · FIRST LEAD PHASE A -- the one
 * exact `LEAD_SUPPLIERS` allow-list literal.
 *
 * AN EXCEPTION IS A HOLE IN A GUARD. This proves the hole is the exact shape
 * it was authorised to be: that the guard still fails when a supplier is named
 * in markup, in CSS, in executable presentation logic, or in a second copy of
 * the allow-list structure -- and that the exception cannot be widened from
 * the inside by growing the literal into something that is not data.
 *
 * Each case copies the page, the universe and the guard to a disposable tree,
 * breaks exactly one thing, re-runs the guard against the copy, and requires
 * the SPECIFIC assertions that own the defect to be the ones that fail.
 *
 * Counted as FAILURES, not successes:
 *   VACUOUS        the mutation did not change the file, so nothing was tested
 *   BLIND          the mutation was real and the guard still passed
 *   MISATTRIBUTED  the guard failed, but not on the assertions that own it
 *
 *     node atlas-tools/prove-default-templates-capability.mjs
 * ========================================================================= */

import { mkdtempSync, rmSync, mkdirSync, copyFileSync, readFileSync, writeFileSync }
  from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const PAGE = join(REPO, 'your-plot.html');
const UNI = join(REPO, 'garden-room-recommendation-universe-v1.json');
const GUARD = join(HERE, 'prove-default-templates.js');

/* The authorised literal, verbatim out of the page, so a copy of it in a test
   is the real thing and not an approximation of it. */
const PAGE_SRC = readFileSync(PAGE, 'utf8');
const DECL = 'const LEAD_SUPPLIERS = Object.freeze({';
function authorisedLiteral() {
  const at = PAGE_SRC.indexOf(DECL);
  if (at < 0) throw new Error('the allow-list declaration is not in the page');
  const open = PAGE_SRC.indexOf('{', at);
  let d = 0;
  for (let k = open; k < PAGE_SRC.length; k++) {
    if (PAGE_SRC[k] === '{') d++;
    else if (PAGE_SRC[k] === '}') { d--; if (d === 0) return PAGE_SRC.slice(at, k + 2); }
  }
  throw new Error('the allow-list literal is not brace-balanced');
}
const LITERAL = authorisedLiteral();

function disposable() {
  const t = mkdtempSync(join(tmpdir(), 'deftpl-'));
  mkdirSync(join(t, 'atlas-tools'));
  copyFileSync(PAGE, join(t, 'your-plot.html'));
  copyFileSync(UNI, join(t, 'garden-room-recommendation-universe-v1.json'));
  copyFileSync(GUARD, join(t, 'atlas-tools', 'prove-default-templates.js'));
  return t;
}

function patch(tree, find, replace, count = 1) {
  const p = join(tree, 'your-plot.html');
  const t = readFileSync(p, 'utf8');
  const n = t.split(find).length - 1;
  if (n !== count) throw new Error('anchor found ' + n + ' times, expected ' + count);
  const out = t.replace(find, replace);
  if (out === t) throw new Error('replacement produced no change');
  writeFileSync(p, out);
}

/* -------------------------------------------------------------- the cases */
const NAME_YB = 'no "Yardbox" outside';
const NAME_SP = 'no "Yard Box" outside';
const CSS_FORK = 'no supplier-named CSS class anywhere';
const ONCE = 'declared exactly once';
const DATA_ONLY = 'data only';
const CARRIES = 'carries the names it is exempted for';

const CASES = [
  ['C1', 'a supplier named in ordinary template markup', [NAME_SP], (t) =>
    patch(t, '</body>', '<p class="ok">Yard Box</p></body>')],

  ['C2', 'a supplier named in CSS / class architecture', [CSS_FORK, NAME_YB], (t) =>
    patch(t, '</body>', '<style>.pn-yardbox-card{color:red}</style></body>')],

  ['C3', 'a supplier named in executable presentation logic', [NAME_YB], (t) =>
    patch(t, '  const LEAD_ROUTE_KEY =',
             "  if (product.organisation === 'Yardbox') { el.className = 'special'; }\n"
             + '  const LEAD_ROUTE_KEY =')],

  ['C4', 'a renamed duplicate of the allow-list structure', [NAME_YB, NAME_SP], (t) =>
    patch(t, DECL,
             "const LEAD_SUPPLIERS_ALT = Object.freeze({\n"
             + "    'Yardbox': Object.freeze({ orgId: 'ORG-000157',\n"
             + "      displayName: 'Yard Box', products: Object.freeze({}) })\n"
             + '  });\n  ' + DECL)],

  ['C5', 'the authorised literal declared a second time, verbatim',
   [ONCE, NAME_YB, NAME_SP], (t) => patch(t, LITERAL, LITERAL + '\n  ' + LITERAL)],

  ['C6', 'executable logic grown inside the authorised literal',
   [DATA_ONLY], (t) =>
    patch(t, "      displayName: 'Yard Box',",
             "      displayName: (function(){ return 'Yard Box'; })(),")],

  ['C7', 'a name moved out of the literal, leaving the exemption hollow',
   [CARRIES, NAME_SP], (t) => {
     patch(t, "      displayName: 'Yard Box',", '      displayName: YB_NAME,');
     patch(t, DECL, "const YB_NAME = 'Yard Box';\n  " + DECL);
   }]
];

/* -------------------------------------------------------------------- run */
function failedLabels(out) {
  return [...out.matchAll(/^\s*FAIL\s+(.+?)(?:\s{3}|$)/gm)].map(m => m[1].trim());
}

console.log('\n  DEFAULT-TEMPLATE GUARD · CAPABILITY PROOF');
console.log('  ' + CASES.length + ' mutations · authorised literal is '
            + LITERAL.length + ' chars\n');

/* CONTROL. The unmutated guard must pass, or every verdict below is noise. */
{
  const t = disposable();
  let out = '', code = 0;
  try {
    out = execFileSync(process.execPath,
      [join(t, 'atlas-tools', 'prove-default-templates.js')], { encoding: 'utf8' });
  } catch (e) { out = (e.stdout || '') + (e.stderr || ''); code = 1; }
  rmSync(t, { recursive: true, force: true });
  if (code !== 0) {
    console.log(out);
    console.log('\n  CONTROL FAILED — the unmutated guard does not pass.\n');
    process.exit(1);
  }
  console.log('  control  unmutated guard passes, allow-list exempted  OK');
  console.log('           (case 5 of the brief: the legitimate names do not fail)\n');
}

let caught = 0, blind = 0, vacuous = 0, wrong = 0;
for (const [id, label, owners, mutate] of CASES) {
  const t = disposable();
  let verdict, detail;
  try {
    const before = readFileSync(join(t, 'your-plot.html'), 'utf8');
    try { mutate(t); } catch (e) { throw new Error('VACUOUS:' + e.message); }
    const after = readFileSync(join(t, 'your-plot.html'), 'utf8');
    if (before === after) throw new Error('VACUOUS:file unchanged');

    let out = '', code = 0;
    try {
      out = execFileSync(process.execPath,
        [join(t, 'atlas-tools', 'prove-default-templates.js')], { encoding: 'utf8' });
    } catch (e) { out = (e.stdout || '') + (e.stderr || ''); code = 1; }

    const got = failedLabels(out);
    if (code === 0 || !got.length) { verdict = 'BLIND'; detail = 'mutation real, guard passed'; }
    else if (!owners.some(o => got.some(g => g.indexOf(o) >= 0))) {
      verdict = 'MISATTRIBUTED';
      detail = 'expected one of [' + owners.join(' | ') + '], got [' + got.join(' | ') + ']';
    } else {
      verdict = 'CAUGHT';
      detail = got.length + ' assertion(s) failed: ' + got.join(' | ');
    }
  } catch (e) {
    if (String(e.message).startsWith('VACUOUS:')) { verdict = 'VACUOUS'; detail = e.message.slice(8); }
    else { verdict = 'MISATTRIBUTED'; detail = e.message; }
  } finally {
    rmSync(t, { recursive: true, force: true });
  }

  if (verdict === 'CAUGHT') caught++;
  else if (verdict === 'BLIND') blind++;
  else if (verdict === 'VACUOUS') vacuous++;
  else wrong++;

  console.log('  ' + id + '  ' + verdict.padEnd(14) + label);
  console.log('      ' + detail);
}

console.log('\n  ' + caught + '/' + CASES.length + ' caught by the assertions that own them.');
console.log('  blind          ' + blind);
console.log('  vacuous        ' + vacuous);
console.log('  misattributed  ' + wrong + '\n');
process.exit(caught === CASES.length ? 0 : 1);
