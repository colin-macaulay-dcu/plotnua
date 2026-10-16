#!/usr/bin/env node
/**
 * PROVE CLUSTER 2 · GUARD CAPABILITY
 * ==================================
 * Every guard in prove-cluster2-garden-retreat.mjs demonstrated capable of
 * failing. One deliberate mutation per guard, each in its own disposable
 * tree, control run first. A guard that passes against its own mutation is a
 * FAILURE of the proof, as is BLIND (nothing caught), VACUOUS (UNREACHABLE)
 * and MISATTRIBUTED (caught only by another guard).
 */
import { readFileSync, writeFileSync, mkdtempSync, copyFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GUARD = join(HERE, 'prove-cluster2-garden-retreat.mjs');
const PAGE = join(ROOT, 'discovery-garden-retreat.html');
const SITEMAP = join(ROOT, 'sitemap.xml');

/** [id, owner, page mutation [from,to] | null, sitemap mutation | null] */
const CASES = [
  ['C-L1a', 'L1', ['It appears to fall\n          outside the rules altogether.', 'A hot tub is not development.'], null],
  ['C-L1b', 'L1', ['It is not a decision by your council, and only a council or', 'This is the settled position, and only a council or'], null],
  ['C-L2', 'L2', ['<li><strong>A cold plunge tub you stand on the ground.</strong> Same as the hot tub. No Irish source we\n          could find deals with it, and neither do the rules.</li>', ''], null],
  ['C-L3a', 'L3', ['<strong>A sauna is\n          not named anywhere in it.</strong>', 'A sauna cabin is a Class 3 structure.'], null],
  ['C-L3b', 'L3', ['picks up anything else only as &ldquo;other similar structure&rdquo;', 'covers a sauna directly'], null],
  ['C-L4a', 'L4', ['<strong>30&nbsp;m&sup2;</strong> total for everything in the garden', '<strong>35&nbsp;m&sup2;</strong> total for everything in the garden'], null],
  ['C-L4b', 'L4', ['but only if it is also standing on its\n        own, within the height limits, and used just for relaxing or storage rather than for a business',
                   'full stop'], null],
  ['C-L4c', 'L4', ['It has to be <strong>for personal use at home</strong>.', 'It can be used however you like.'], null],
  ['C-L5a', 'L5', ['It is also <strong>not a Section&nbsp;5 declaration, and it settles nothing about a private sauna, hot\n        tub or plunge tub at home.</strong>', 'It settles the question.'], null],
  ['C-L5b', 'L5', ['we are not\n        going to read that silence as a yes', 'so you may take it that no permission is needed'], null],
  ['C-L5c', 'L5', ['<strong>we are not saying the paying customers alone are what made\n        permission necessary.</strong> The application covered the caravan, the fencing, the kiosk, the shelter\n        and the site works together, and the decision does not separate them.',
                   'the paying customers are what made permission necessary.'], null],
  ['C-L5d', 'L5', ['<strong>ABP-322192-25</strong>, from J', '<strong>ABP-000000-00</strong>, from J'], null],
  ['C-L6a', 'L6', ['the energy regulator prosecutes people who do this\n          work without being registered',
                   'unregistered work carries penalties up to &euro;50,000 and three years'], null],
  ['C-L6b', 'L6', ['The exact electrical requirements depend on your installation.', 'A sauna heater is always restricted electrical works.'], null],
  ['C-L6c', 'L6', ['Neither body&rsquo;s published material sets out exactly\n        which jobs fall inside it', 'The boundary is clearly published'], null],
  ['C-L6d', 'L6', ['A registered\n          electrical contractor can advise you and carry out the work safely.', 'Any electrician will do.'], null],
  ['C-R1a', 'R1', ['<strong>standing charges\n          belong to your house, not to your sauna.</strong>', 'standing charges are part of it.'], null],
  ['C-R1b', 'R1', ['<strong>We are not going to put a percentage on that and pretend it is\n          precise.</strong>', 'Assume it runs at 40 per cent.'], null],
  ['C-R1c', 'R1', ['the figure on your\n          own bill, not an average', 'the national average'], null],
  ['C-R2a', 'R2', ['<strong>one hour of continuous %(kw)d&nbsp;kW operation at an illustrative rate</strong>,\n          not a forecast of your bill', 'what an hour costs'], null],
  ['C-R2b', 'R2', ['At an illustrative %(rate)dc a unit', 'At the current Irish rate of %(rate)dc a unit'], null],
  ['C-R3', 'R3', ['that hour comes to <strong>&euro;%(ceiling).2f</strong>', 'that hour comes to <strong>&euro;2.10</strong>'], null],
  ['C-P1', 'P1', ['<h3>What it costs to run</h3>', '<h3>What it costs to run</h3>\n        <p>The average cost of a sauna in Ireland is nine thousand euro.</p>'], null],
  ['C-E1', 'E1', ['<a href="discovery-living-in-the-garden.html">Living in the Garden</a>',
                  '<a href="your-plot.html?discovery=garden-retreat">Check your garden</a>'], null],
  ['C-S1', 'S1', ['    {\n      "@type": "BreadcrumbList",', '    { "@type": "FAQPage", "@id": "https://plotnua.ie/x#faq" },\n    {\n      "@type": "BreadcrumbList",'], null],
  // C-S2 anchor re-dated 16 Oct 2026: SEO Phase 1 set lastmod from git evidence (was 2026-10-14).
  ['C-S2', 'S2', null, ['discovery-garden-retreat.html</loc>\n    <lastmod>2026-10-16', 'discovery-garden-retreat.html</loc>\n    <lastmod>2026-09-01']],
  ['C-J1', 'J1', ['<h1>Garden Retreat</h1>', '<h1>Garden Wellness</h1>'], null],
  ['C-J2', 'J2', ["Exactly which\n      electrical jobs need a registered contractor&rsquo;s certificate.", ''], null],
  ['C-J3', 'J3', ['<a href="discovery-living-in-the-garden.html">Living in the Garden</a>', 'Living in the Garden'], null],
];

// The worked-example tokens are substituted so the mutation anchors track the
// builder's own figures rather than hard-coding them a second time.
const FIG = { kw: 9, rate: 35, ceiling: '3.15' };
for (const c of CASES) for (const i of [2, 3]) if (c[i])
  c[i] = c[i].map(t => t.replace(/%\(kw\)d/g, FIG.kw).replace(/%\(rate\)dc/g, FIG.rate + 'c').replace(/%\(ceiling\)\.2f/g, FIG.ceiling));


function run(p, m) {
  try { return { code: 0, out: execFileSync('node', [GUARD, '--page', p, '--sitemap', m], { encoding: 'utf8' }) }; }
  catch (e) { return { code: e.status ?? 1, out: (e.stdout || '') + (e.stderr || '') }; }
}
const failedIds = o => [...o.matchAll(/^ {2}FAIL {2}(\S+)/gm)].map(m => m[1]);
const unreachable = o => [...o.matchAll(/^ {2}FAIL {2}(\S+) {2}UNREACHABLE/gm)].map(m => m[1]);

console.log('\nGUARD-CAPABILITY PROOF · CLUSTER 2\n');

const control = run(PAGE, SITEMAP);
if (control.code !== 0) {
  console.log('CONTROL FAILED — the unmutated page does not pass. Nothing below is meaningful.');
  console.log(control.out); process.exit(1);
}
console.log(`  CONTROL   unmutated page: ${(control.out.match(/(\d+) checks/) || [])[1]} checks, 0 failed\n`);

let good = 0, bad = 0;
for (const [id, owner, pageMut, mapMut] of CASES) {
  const dir = mkdtempSync(join(tmpdir(), 'c2cap-'));
  const p = join(dir, 'page.html'), m = join(dir, 'sitemap.xml');
  copyFileSync(PAGE, p); copyFileSync(SITEMAP, m);
  let applied = true;
  for (const [file, mut] of [[p, pageMut], [m, mapMut]]) {
    if (!mut) continue;
    const s = readFileSync(file, 'utf8');
    const n = s.split(mut[0]).length - 1;
    if (n !== 1) { console.log(`  ERROR   ${id}  anchor appears ${n} times, expected 1 — NOT applied`); applied = false; break; }
    writeFileSync(file, s.replace(mut[0], mut[1]));
  }
  if (applied) {
    const r = run(p, m);
    const fails = failedIds(r.out), vac = unreachable(r.out);
    const collateral = fails.filter(f => f !== owner);
    if (vac.includes(owner)) { console.log(`  VACUOUS ${id}  owner ${owner} reported UNREACHABLE`); bad++; }
    else if (!fails.length) { console.log(`  BLIND   ${id}  NOT CAUGHT (owner ${owner})`); bad++; }
    else if (!fails.includes(owner)) { console.log(`  MISATTR ${id}  owner ${owner} passed; caught by ${fails.join(',')}`); bad++; }
    else {
      const note = [collateral.length ? `also ${collateral.join(',')}` : '',
                    vac.length ? `${vac.join(',')} unreachable` : ''].filter(Boolean).join('; ');
      console.log(`  CAUGHT  ${id}  by ${owner}${note ? `  (${note})` : ''}`); good++;
    }
  } else bad++;
  rmSync(dir, { recursive: true, force: true });
}
console.log(`\n${CASES.length} mutations: ${good} caught by the guard that owns them, ${bad} not.\n`);
process.exit(bad ? 1 : 0);
