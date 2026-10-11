/**
 * GUARD-CAPABILITY PROOF — THE RIGHTS GATE'S PUBLISH-PATH SCAN
 * ============================================================
 * The image-rights workflow has carried a step called "Prove the image-rights
 * gate still catches what it is for" since 11 October 2026, written like this:
 *
 *     test -f atlas-tools/prove-image-rights-gate-capability.mjs \
 *       && node atlas-tools/prove-image-rights-gate-capability.mjs \
 *       || echo "no image-rights capability proof in this repo yet"
 *
 * The file did not exist. The step printed a notice and passed on every run,
 * which is the SECOND time that defect has been introduced: the comment
 * directly above it records the first, when the step pointed at a path in
 * another repository and ended in the same `|| echo`. Fixed once, reintroduced
 * in the next edit.
 *
 * WHAT WAS AND WAS NOT ALREADY COVERED. Running `validate-image-rights.js
 * --self-test` shows it already drives the six scenarios the workflow comment
 * claims: unknown vocabulary, missing permission, wrong domain, a live grant,
 * the same asset after withdrawal, rights disagreement, and the scoped
 * delivery-host rule. So the missing file was not missing coverage of THOSE.
 *
 * It was missing coverage of the thing CI actually runs. --self-test feeds the
 * gate a synthetic asset list. Production runs `--scan-html .`, which walks the
 * published pages and attributes every externally hosted image by domain. That
 * path -- the one that catches a page which GAINS a supplier image when the
 * manifest was never touched, which is the case a path filter would miss and
 * the reason the workflow runs on every publish -- had nothing proving it.
 *
 * This proves it, both ways round, by mutating pages in a disposable copy.
 *
 *   node atlas-tools/prove-image-rights-gate-capability.mjs
 *
 * Exit 0 = the scan path proved capable. Exit 2 = nothing was measured.
 */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync, copyFileSync,
         existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const GATE = join(HERE, 'validate-image-rights.js');
const MANIFEST = join(ROOT, 'image-rights-manifest.json');

function refuse(why) {
  console.log('\nRIGHTS GATE CAPABILITY · THE PUBLISH-PATH SCAN');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was measured. This is not a pass.');
  process.exit(2);
}
for (const f of [GATE, MANIFEST]) {
  if (!existsSync(f)) refuse(f + ' is missing');
}

const manifestDoc = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const rows = Array.isArray(manifestDoc) ? manifestDoc
  : Object.values(manifestDoc).find(v => Array.isArray(v) && v[0]
                                         && typeof v[0] === 'object');
if (!rows || !rows.length) refuse('the manifest holds no rows');

/* A domain nobody has granted anything for, and one that is granted. */
const granted = rows.find(r => r.permitted_domain
  && /grant/i.test(String(r.permission_outcome || '')));
if (!granted) refuse('no live grant in the manifest to build the control on');
const UNGRANTED = 'images.an-unknown-supplier-nobody-granted.example';

let proved = 0, broken = 0;
const log = s => console.log(s);

function tree(pageHtml, { manifestEdit = null } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'pn-rights-'));
  mkdirSync(join(dir, 'atlas-tools'), { recursive: true });
  copyFileSync(GATE, join(dir, 'atlas-tools', 'validate-image-rights.js'));
  let m = JSON.parse(readFileSync(MANIFEST, 'utf8'));
  if (manifestEdit) manifestEdit(m);
  writeFileSync(join(dir, 'image-rights-manifest.json'),
                JSON.stringify(m, null, 2));
  writeFileSync(join(dir, 'page.html'), pageHtml);
  return dir;
}
function run(dir) {
  try {
    return { code: 0, out: execFileSync('node',
      [join(dir, 'atlas-tools', 'validate-image-rights.js'),
       '--scan-html', dir, '--permissions',
       join(dir, 'image-rights-manifest.json'), '--max-age-days', '36500'],
      { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }) };
  } catch (e) {
    return { code: e.status === undefined ? -1 : e.status,
             out: (e.stdout || '') + (e.stderr || '') };
  }
}
const page = (host, extra = '') => `<!doctype html><html><head>
<title>t</title></head><body>
<img src="https://${host}/some/product-photo.jpg" alt="A building.">
${extra}
</body></html>`;

console.log('\nRIGHTS GATE CAPABILITY · THE PUBLISH-PATH SCAN');
console.log('='.repeat(74));
console.log(`  control grant: ${granted.organisation_name} `
            + `(${granted.permitted_domain})`);
console.log('-'.repeat(74));

/* ── CONTROL · a granted image on a page passes ───────────────────────── */
{
  const credit = granted.required_credit || '';
  const r = run(tree(page(granted.permitted_domain,
    credit ? `<p>${credit}</p><p><a href="https://${granted.permitted_domain}/">Visit</a></p>` : '')));
  if (r.code !== 0) {
    log('  CONTROL FAILED — a granted image does not pass the scan path:');
    log('    ' + r.out.split('\n').filter(l => /REFUSE|error/i.test(l))
                   .slice(0, 3).join('\n    '));
    log('  Every result after this would be meaningless. Stopping.');
    process.exit(1);
  }
  log('  CONTROL  a page carrying a GRANTED supplier image passes the scan');
}

const CASES = [
  { id: 'C-SCAN1',
    why: 'a published page gains an image from a domain nobody granted',
    html: page(UNGRANTED),
    expect: /REFUSE|GATE FAIL|no live grant/i },

  { id: 'C-SCAN2',
    why: 'the granted supplier’s image is served from a DIFFERENT domain',
    html: page('cdn.not-' + String(granted.permitted_domain).replace(/\W/g, '')
               + '.example'),
    expect: /REFUSE|GATE FAIL/i },

  { id: 'C-SCAN3',
    why: 'the grant is downgraded to a non-grant while the page is unchanged',
    html: page(granted.permitted_domain,
               granted.required_credit ? `<p>${granted.required_credit}</p>` : ''),
    manifestEdit: m => {
      const list = Array.isArray(m) ? m
        : Object.values(m).find(v => Array.isArray(v) && v[0]);
      const row = list.find(r => r.organisation_code === granted.organisation_code);
      row.permission_outcome = 'Withdrawn / Superseded';
    },
    expect: /REFUSE|WITHDRAWN|GATE FAIL/i },

  { id: 'C-SCAN4',
    why: 'a conditional grant’s required credit disappears from the page',
    skipUnless: () => !!granted.required_credit,
    html: page(granted.permitted_domain),      // no credit anywhere
    expect: /REFUSE|credit|GATE FAIL/i },

  { id: 'C-SCAN5',
    why: 'the manifest is removed entirely',
    html: page(granted.permitted_domain),
    manifestEdit: m => {
      const list = Array.isArray(m) ? m
        : Object.values(m).find(v => Array.isArray(v) && v[0]);
      list.length = 0;                          // no grants at all
    },
    expect: /REFUSE|GATE FAIL|no live grant/i }
];

for (const c of CASES) {
  if (c.skipUnless && !c.skipUnless()) {
    log(`  BLIND         ${c.id}  ${c.why}`);
    log('                the control grant carries no required credit, so '
        + 'this case cannot be built');
    broken++;
    continue;
  }
  const r = run(tree(c.html, { manifestEdit: c.manifestEdit }));
  if (r.code === 0) {
    log(`  VACUOUS       ${c.id}  ${c.why}`);
    log('                the gate PASSED against this defect. The scan path '
        + 'cannot see it.');
    broken++;
    continue;
  }
  if (!c.expect.test(r.out)) {
    log(`  MISATTRIBUTED ${c.id}  ${c.why}`);
    log(`                the gate failed (exit ${r.code}) but not for the `
        + 'expected reason');
    broken++;
    continue;
  }
  log(`  PROVED        ${c.id}  ${c.why}`);
  log(`                the gate REFUSED (exit ${r.code}), as required`);
  proved++;
}

console.log('-'.repeat(74));
console.log(`${CASES.length} mutations, ${proved} proved capable, `
            + `${broken} not proved`);
console.log('The scan path is what CI runs. It is now proved, not assumed.\n');
process.exit(broken ? 1 : 0);
