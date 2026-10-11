/**
 * GUARD-CAPABILITY PROOF — THE CONFIGURATION GUARDS CAN ACTUALLY FAIL
 * ===================================================================
 * A guard that has never failed is a claim, not a guarantee. Each case below
 * breaks ONE thing the suites assert, in a DISPOSABLE copy, and requires the
 * named check to fail. Three outcomes count as a failure of the PROOF, not
 * of the mutation:
 *
 *   VACUOUS       the suite passed anyway — the guard cannot see this defect
 *   BLIND         the suite errored or refused — it measured nothing
 *   MISATTRIBUTED something failed, but not the check that should have
 *
 * The control runs first, unmutated. If the control does not pass, every
 * result after it is meaningless and the proof stops.
 *
 * NOTHING IN THE REPOSITORY IS MUTATED. The page mutations are written to
 * /tmp and passed with --plot; the generator mutations go into a /tmp tree
 * holding a copy of .github/scripts. The real artefacts are read, never
 * written.
 *
 *   node atlas-tools/prove-results-configurations-capability.mjs
 *
 * Exit 0 = every guard proved capable.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, cpSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const PLOT = join(ROOT, 'your-plot.html');
const QUAL = join(ROOT, '.github', 'scripts', 'additional_home_qualification.py');

const plotSrc = readFileSync(PLOT, 'utf8');
const qualSrc = readFileSync(QUAL, 'utf8');

let proved = 0, broken = 0;
const log = (s) => console.log(s);

function run(cmd, args) {
  try {
    return { code: 0, out: execFileSync(cmd, args, { encoding: 'utf8',
             maxBuffer: 32 * 1024 * 1024, cwd: ROOT }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const failedIds = (o) =>
  [...o.matchAll(/^ {2}FAIL {2}(PC\d+[a-z]?|C\d+[a-z]?)/gm)].map(m => m[1]);

/* ── The three suites, each runnable against a replaced file ──────────── */
const SUITES = {
  reader: (plot) => run('node',
    [join(HERE, 'prove-results-configurations.mjs'), '--plot', plot]),
  equivalence: (plot) => run('node',
    [join(HERE, 'prove-price-presentation-unchanged.mjs'),
     '--plot', plot, '--baseline', PLOT]),
  generator: (treeRoot) => run('python3',
    [join(treeRoot, 'atlas-tools', 'prove-price-configurations.py')])
};

/* A mutated page in /tmp. The repository file is never touched. */
function mutatedPlot(find, replace) {
  if (!plotSrc.includes(find)) {
    return { error: 'the mutation target is not in your-plot.html: '
                    + find.slice(0, 70) };
  }
  const dir = mkdtempSync(join(tmpdir(), 'pn-cap-'));
  const p = join(dir, 'your-plot.html');
  writeFileSync(p, plotSrc.replace(find, replace));
  return { plot: p };
}

/* A disposable tree holding the generator and its suite. */
function mutatedTree(find, replace) {
  if (!qualSrc.includes(find)) {
    return { error: 'the mutation target is not in the qualification module: '
                    + find.slice(0, 70) };
  }
  const dir = mkdtempSync(join(tmpdir(), 'pn-gen-'));
  mkdirSync(join(dir, '.github', 'scripts'), { recursive: true });
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  cpSync(join(ROOT, '.github', 'scripts'), join(dir, '.github', 'scripts'),
         { recursive: true });
  cpSync(join(HERE, 'prove-price-configurations.py'),
         join(dir, 'atlas-tools', 'prove-price-configurations.py'));
  writeFileSync(join(dir, '.github', 'scripts',
                     'additional_home_qualification.py'),
                qualSrc.replace(find, replace));
  return { root: dir };
}

console.log('\nGUARD-CAPABILITY PROOF · PRICE CONFIGURATIONS');
console.log('='.repeat(74));

/* ── CONTROL ─────────────────────────────────────────────────────────── */
{
  const r = SUITES.reader(PLOT);
  const e = SUITES.equivalence(PLOT);
  const g = SUITES.generator(ROOT);
  if (r.code !== 0 || e.code !== 0 || g.code !== 0) {
    log('  CONTROL FAILED — the unmutated suites do not all pass:');
    log(`    reader=${r.code} equivalence=${e.code} generator=${g.code}`);
    log('  Every result after this would be meaningless. Stopping.');
    process.exit(1);
  }
  log('  CONTROL  all three suites pass unmutated — the instrument works');
  log('-'.repeat(74));
}

/* ── The cases ───────────────────────────────────────────────────────── */
const CASES = [
  // 1 · the central defect: the scalar printed bare.
  { id: 'C-PC3', suite: 'reader', expect: ['PC3', 'PC4', 'PC12'],
    why: 'the configuration name is stripped off the scalar',
    find: '    const display = display0 + suffix;\n    const tail = tail0 + suffix;',
    with: '    const display = display0;\n    const tail = tail0;' },

  // 2 · only one of the two prices shown.
  { id: 'C-PC2', suite: 'reader', expect: ['PC2'],
    why: 'the both-prices line drops the second configuration',
    find: "      ? configs.map(function(c){ return c.figure + pnConfigSuffix(c.label); })\n               .join(' \\u00B7 ')",
    with: "      ? configs.slice(0, 1).map(function(c){ return c.figure + pnConfigSuffix(c.label); })\n               .join(' \\u00B7 ')" },

  // 3 · the dangerous VAT default.
  { id: 'C-PC8', suite: 'reader', expect: ['PC8'],
    why: 'an unknown VAT basis is given the common-case sentence',
    find: "    EXCLUDES_VAT: 'excluding VAT'\n  };",
    with: "    EXCLUDES_VAT: 'excluding VAT',\n    VAT_UNKNOWN: 'including VAT'\n  };" },

  // 4 · a shell ranked against a finished home.
  { id: 'C-PC13', suite: 'reader', expect: ['PC13'],
    why: 'the multi-configuration refusal is removed from pnPriceDelta',
    find: '    if (ga.length > 1 || gb.length > 1) return null;',
    with: '    if (false) return null;' },

  // 5 · unlike single configurations ranked against each other.
  { id: 'C-PC14', suite: 'reader', expect: ['PC14'],
    why: 'the unlike-label refusal is removed',
    find: '    if (la !== lb) return null;',
    with: '    if (false) return null;' },

  // 6 · a price including VAT ranked against one excluding it.
  { id: 'C-PC15', suite: 'reader', expect: ['PC15'],
    why: 'the unlike-VAT-basis refusal is removed',
    find: "    if (bA && bB && bA !== 'VAT_UNKNOWN' && bB !== 'VAT_UNKNOWN' && bA !== bB)\n      return null;",
    with: '    if (false) return null;' },

  // 7 · an unlabelled configuration printed as a bare figure.
  { id: 'C-PC18', suite: 'reader', expect: ['PC18'],
    why: 'a configuration with no governed label is accepted',
    find: '      if (amount == null || !label) continue;',
    with: '      if (amount == null) continue;' },

  // 8 · an exclusion quietly dropped from the homeowner copy.
  { id: 'C-PC9', suite: 'reader', expect: ['PC9'],
    why: 'the kitchen-and-appliances exclusion sentence is removed',
    find: "    KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED:\n      'Kitchen furniture and appliances are not included.',",
    with: '' },

  // 9 · the publication gate weakened by a presentation change.
  { id: 'C-PC17', suite: 'reader', expect: ['PC17'],
    why: 'the fail-closed publication test is softened',
    find: "      if (gateEnforced ? p.publicVisibility !== 'PUBLISHABLE'",
    with: "      if (gateEnforced ? p.publicVisibility === 'HOLD'" },

  // 10 · the Additional Home journey back on its own bare reader.
  { id: 'C-PC19a', suite: 'reader', expect: ['PC19'],
    why: 'the journey stops using the one published contract',
    find: "      ? window.__PN_PRICE_VIEW__(pnAdditionalHomeView(p)) : null;",
    with: '      ? null : null;' },

  // 11 · the degradation made unsafe: a bare figure instead of silence.
  { id: 'C-PC19b', suite: 'reader', expect: ['PC19'],
    why: 'the no-handle fallback prints a bare figure for a multi-configuration product',
    find: '      : (pnConfigCount(p) > 1 ? null : pnMoney(p));',
    with: '      : pnMoney(p);' },

  // 12 · the bridge stops carrying the governed configurations at all.
  { id: 'C-PC19c', suite: 'reader', expect: ['PC19'],
    why: 'the Additional Home bridge drops the configurations',
    find: "        configurations: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&",
    with: "        configurations: (false &&" },

  // 13 · THE REGRESSION CASE. 619 products' prices must not move.
  { id: 'C-EQ', suite: 'equivalence', expect: ['equivalence'],
    why: 'every price gains an invented label, including single-price products',
    find: '    const suffix = mine ? pnConfigSuffix(mine.label) : \'\';',
    with: "    const suffix = mine ? pnConfigSuffix(mine.label) : ' (Standard)';" },

  // 14 · the union instead of the intersection: a turnkey term published
  //      as covering the shell price too.
  { id: 'C-C14', suite: 'generator', expect: ['C14'],
    why: 'the product-level term list becomes a union',
    find: '            common = t if common is None else (common & t)',
    with: '            common = t if common is None else (common | t)' },

  // 15 · the curator's research note piped to a homeowner.
  { id: 'C-C17', suite: 'generator', expect: ['C17'],
    why: 'the governed prose is returned instead of tokens',
    find: '    return [tok for tok, needles in COMMERCIAL_TERM_ANCHORS\n            if all(n in blob for n in needles)]',
    with: '    return [blob]' },

  // 16 · an anchor loosened until it matches evidence it should not.
  { id: 'C-C15', suite: 'generator', expect: ['C15'],
    why: 'the delivery anchor is loosened to the bare word "delivery"',
    find: '    ("DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED",\n     ("delivery, installation and foundation", "not included")),',
    with: '    ("DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED",\n     ("delivery",)),' }
];

for (const c of CASES) {
  const made = c.suite === 'generator'
    ? mutatedTree(c.find, c.with)
    : mutatedPlot(c.find, c.with);
  if (made.error) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log(`                ${made.error}`);
    broken++;
    continue;
  }
  const r = c.suite === 'generator'
    ? SUITES.generator(made.root)
    : SUITES[c.suite](made.plot);

  if (r.code === 2 || /INSTRUMENT UNAVAILABLE/.test(r.out)) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log(`                the suite refused: ${r.out.split('\n').filter(Boolean).slice(-2).join(' / ').slice(0, 150)}`);
    broken++;
    continue;
  }
  if (r.code === 0) {
    log(`  VACUOUS       ${c.id}  ${c.why}`);
    log('                the suite PASSED against this defect. The guard '
        + 'cannot see it.');
    broken++;
    continue;
  }

  if (c.suite === 'equivalence') {
    // This suite reports products, not check ids.
    const sawMove = /product\(s\) changed how their price reads/.test(r.out);
    if (sawMove) {
      const n = (r.out.match(/FAIL\s+(\d+) product\(s\)/) || [])[1] || '?';
      log(`  PROVED        ${c.id}  ${c.why}`);
      log(`                ${n} products reported as moved`);
      proved++;
    } else {
      log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
      log('                the suite failed, but not by reporting moved '
          + 'products');
      broken++;
    }
    continue;
  }

  const ids = failedIds(r.out);
  const wanted = c.expect;
  const hit = wanted.filter(w => ids.includes(w));
  if (!hit.length) {
    log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
    log(`                expected ${wanted.join('/')} to fail; what failed `
        + `was ${ids.join(',') || '(nothing named)'}`);
    broken++;
  } else {
    log(`  PROVED        ${c.id}  ${c.why}`);
    log(`                ${hit.join(', ')} failed, as required`);
    proved++;
  }
}

console.log('-'.repeat(74));
console.log(`${CASES.length} mutations, ${proved} proved capable, `
            + `${broken} not proved\n`);
process.exit(broken ? 1 : 0);
