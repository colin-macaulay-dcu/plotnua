#!/usr/bin/env node
/**
 * PROVE CLUSTER 1 · GUARD CAPABILITY
 * ==================================
 * Every guard in prove-cluster1-garden-authority.mjs is demonstrated capable
 * of failing. One deliberate mutation per guard, each in its own disposable
 * tree, with a control run first.
 *
 * A guard that passes against its own mutation is counted a FAILURE of the
 * proof — as is a mutation caught only by some other guard (MISATTRIBUTED),
 * and a guard that reports UNREACHABLE (VACUOUS).
 *
 *   node atlas-tools/prove-cluster1-capability.mjs
 */
import { readFileSync, writeFileSync, mkdtempSync, copyFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GUARD = join(HERE, 'prove-cluster1-garden-authority.mjs');
const PAGE = join(ROOT, 'discovery-living-in-the-garden.html');
const SITEMAP = join(ROOT, 'sitemap.xml');

/** [id, owning guard, page mutation (from -> to), sitemap mutation] */
const CASES = [
  ['C-L1', 'L1', ['45&nbsp;m&sup2; counting anything already built', '47&nbsp;m&sup2; counting anything already built'], null],
  ['C-L2a', 'L2', ['but only if it also meets the rest of the conditions attached to it &mdash;\n      detached', 'and that is that &mdash;\n      detached'], null],
  ['C-L2b', 'L2', ['a detached garden building of\n      no more than 25&nbsp;m&sup2; can fall inside the Building Regulations exemption',
                   'under 25&nbsp;m&sup2; a garden building is outside the Building Regulations altogether'], null],
  ['C-L3', 'L3', ['That is why a council and a supplier can give you different answers',
                  'In practice the total area is measured internally. That is why a council and a supplier can give you different answers'], null],
  ['C-L4', 'L4', ['Permanent, too &mdash; the regulations rule out a caravan',
                  'The regulations call it a habitable dwelling. Permanent, too &mdash; the regulations rule out a caravan'], null],
  ['C-L5', 'L5', ['count the period from 16&nbsp;July&nbsp;2026', 'count the period from 17&nbsp;July&nbsp;2026'], null],
  ['C-L6', 'L6', ['Those are\n          not the same thing, and the regulations do not reconcile them.',
                  'The council will treat them as the same thing.'], null],
  ['C-L7', 'L7', ['It does not make the building lawful, it produces no certificate',
                  'It does not make the building lawful, but after seven years the building is lawful in practice'], null],
  ['C-L8', 'L8', ['and it has\n          twelve weeks to answer', 'and it has\n          four weeks to answer'], null],
  ['C-L9', 'L9', ['The\n          protection can reach into the grounds as well, but only where the',
                  'The protection extends to the land in its curtilage and to other structures on that land, but only where the'], null],
  ['C-P1a', 'P1', ['That can make a substantial difference to the price',
                   'Expect about &euro;20,400. That can make a substantial difference to the price'], null],
  ['C-P1b', 'P1', ['A kit you assemble, a building delivered and erected', 'On average, a kit you assemble, a building delivered and erected'], null],
  // C-P2 anchor re-dated 20 Oct 2026 (SEO-C1): the corrected evidence publishes 245 (was 247).
  ['C-P2', 'P2', ['245 garden-room products with a euro price', '250 garden-room products with a euro price'], null],
  ['C-P3', 'P3', ['and we are\n      certainly not going to tell you what a garden home costs: the market has not\n      published enough for anyone to say honestly.', 'The market has not published enough for anyone to say honestly.'], null],
  ['C-P4', 'P4', ['Is VAT included?', 'Is delivery included?'], null],
  ['C-S1', 'S1', ['    {\n      "@type": "BreadcrumbList",', '    { "@type": "FAQPage", "@id": "https://plotnua.ie/x#faq" },\n    {\n      "@type": "BreadcrumbList",'], null],
  // C-S2 anchor re-dated for the 26 Oct buying-guidance revision.
  ['C-S2', 'S2', null, ['discovery-living-in-the-garden.html</loc><lastmod>2026-10-26', 'discovery-living-in-the-garden.html</loc><lastmod>2026-09-01']],
  ['C-J1', 'J1', ["'garden_discovery_assessment_click'", "'garden_assessment_click'"], null],
  ['C-J2', 'J2', ['<p>Exempted development means no planning application. For a garden home, it does\n      not mean nothing to file.</p>',
                  '<p>Exempted development means no planning application. A garden room files nothing. For a garden home, it does\n      not mean nothing to file.</p>'], null],
];

function run(pagePath, mapPath) {
  try {
    const out = execFileSync('node', [GUARD, '--page', pagePath, '--sitemap', mapPath], { encoding: 'utf8' });
    return { code: 0, out };
  } catch (e) {
    return { code: e.status ?? 1, out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = out => [...out.matchAll(/^ {2}FAIL {2}(\S+)/gm)].map(m => m[1]);
const unreachable = out => [...out.matchAll(/^ {2}FAIL {2}(\S+) {2}UNREACHABLE/gm)].map(m => m[1]);

console.log('\nGUARD-CAPABILITY PROOF · CLUSTER 1\n');

// --- control -----------------------------------------------------------------
const control = run(PAGE, SITEMAP);
if (control.code !== 0) {
  console.log('CONTROL FAILED — the unmutated page does not pass. Nothing below is meaningful.');
  console.log(control.out);
  process.exit(1);
}
const controlTotal = (control.out.match(/(\d+) checks/) || [])[1];
console.log(`  CONTROL   unmutated page: ${controlTotal} checks, 0 failed\n`);

let good = 0, bad = 0;
for (const [id, owner, pageMut, mapMut] of CASES) {
  const dir = mkdtempSync(join(tmpdir(), 'c1cap-'));
  const p = join(dir, 'page.html'), m = join(dir, 'sitemap.xml');
  copyFileSync(PAGE, p); copyFileSync(SITEMAP, m);

  let applied = true;
  for (const [file, mut] of [[p, pageMut], [m, mapMut]]) {
    if (!mut) continue;
    const s = readFileSync(file, 'utf8');
    const n = s.split(mut[0]).length - 1;
    if (n !== 1) {
      console.log(`  ERROR   ${id}  mutation anchor appears ${n} times, expected 1 — mutation NOT applied`);
      applied = false; break;
    }
    writeFileSync(file, s.replace(mut[0], mut[1]));
  }

  if (applied) {
    const r = run(p, m);
    const fails = failedIds(r.out);
    const vac = unreachable(r.out);
    const collateral = fails.filter(f => f !== owner);
    if (vac.length) {
      console.log(`  VACUOUS ${id}  guard(s) ${vac.join(',')} reported UNREACHABLE`); bad++;
    } else if (!fails.length) {
      console.log(`  BLIND   ${id}  mutation NOT CAUGHT by any guard (owner ${owner})`); bad++;
    } else if (!fails.includes(owner)) {
      console.log(`  MISATTR ${id}  owner ${owner} passed; caught instead by ${fails.join(',')}`); bad++;
    } else {
      console.log(`  CAUGHT  ${id}  by ${owner}${collateral.length ? `  (also ${collateral.join(',')})` : ''}`);
      good++;
    }
  } else bad++;

  rmSync(dir, { recursive: true, force: true });
}

console.log(`\n${CASES.length} mutations: ${good} caught by the guard that owns them, ${bad} not.\n`);
process.exit(bad ? 1 : 0);
