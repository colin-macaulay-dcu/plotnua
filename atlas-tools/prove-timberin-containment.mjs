/* TIMBERIN CONTAINMENT PROOF — TWO GRANTS, THREE PHOTOGRAPHS, ONE COMPOSITE, NO HOT-LINK.
   ---------------------------------------------------------------------------
   WHY THIS EXISTS (H2, 20 October 2026).

   TimberIN granted, in writing, the use of two photographs -- the hot tub
   from Photograph A and the chimney smoke from Photograph B -- ADAPTED into
   PlotNua's garden illustration (Possibility Reveal L6), credited
   "Hot tub: TimberIN". It granted nothing else.

   On 22 October 2026 TimberIN granted, in writing, a SECOND and separate
   licence: one photograph -- the Nordic Cube sauna -- adapted into the same
   Garden Retreat illustration, credited TimberIN with a link ("Sauna:
   TimberIN"). The two grants stay two records (each with its own Atlas ref and
   evidence); this proof pins BOTH, exactly, and refuses any other TimberIN
   licence.

   The rights manifest scopes a live grant by host, and the generator requires
   a permitted_domain for every live grant. So on its own the TimberIN row
   would let the rights gate pass ANY timberin.com image hot-linked on ANY page
   that carries the credit. TimberIN granted two photographs, adapted. This
   file is the difference between the manifest row and the grant -- the same
   role prove-ognyx-imagery-containment.mjs plays for OGNYX.

   WHERE THE LICENCE LIVES. In image-adaptation-licences.json, NOT in
   image-rights-records.json. A record there is a HOST grant (the rights gate
   would pass any hot-linked timberin.com image carrying the credit) and a
   LISTING record (it would move TimberIN's six Results products off the
   public-information basis). This licence is neither, so T4 keeps it out.

   WHAT IT CHECKS
     T1  No published page (HTML, or a script configuration's "src") references
         an externally hosted image on any TimberIN host: timberin.com,
         timberin.co.uk, woodenhottubsale.co.uk, or a subdomain of them.
     T2  No file in the published tree is a byte copy of any of the three
         source photographs (by SHA-256): unmodified re-hosting is not the grant.
     T4  No TimberIN record is in image-rights-records.json.
     T5  The licence file is public, so it carries no email address, mail
         identifier, Atlas internal id or quoted correspondence, and points at
         the private evidence only through a PN-EVID evidence_ref.
     T3  The records still say what was granted, for EACH pinned grant:
         modification permitted, hot-linking not permitted, no delivery hosts,
         exactly the enumerated photographs (two for the hot tub, one for the
         sauna), each 'adapted-into-composite' and bound to the one composite
         possibility-reveal-L6, credit exactly "Hot tub: TimberIN" / "Sauna:
         TimberIN", linked to timberin.com, default for anything unlisted
         NOT_AUTHORISED -- and no TimberIN licence exists beyond the two.

   Then it proves itself: each check is broken in a temporary tree and must
   refuse. The first case also runs the rights gate on the hot-linked image,
   which must refuse it too while no host grant exists.

   Exit 0 = contained and proved. 1 = breach or a check not proved. 2 = could
   not establish the facts.

   Run: node atlas-tools/prove-timberin-containment.mjs [--root PATH]        */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argRoot = (() => { const i = process.argv.indexOf('--root'); return i < 0 ? null : process.argv[i + 1]; })();
const ROOT = argRoot || path.resolve(HERE, '..');
const SELF_ONLY = process.argv.includes('--check-only');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');

const HOSTS = ['timberin.com', 'timberin.co.uk', 'woodenhottubsale.co.uk'];
const COMPOSITE = 'possibility-reveal-L6';
const CREDIT = 'Hot tub: TimberIN';
/* The pinned grants: anything else TimberIN in the licence file is refused (T3). */
const GRANTS = [
  { ref: 'L6-TIMBERIN-TWO-PHOTOS-20261019', credit: 'Hot tub: TimberIN', count: 2 },
  { ref: 'TIMBERIN-NORDIC-CUBE-SAUNA-20261022', credit: 'Sauna: TimberIN', count: 1 },
];
const SKIP = new Set(['.git', 'node_modules', '.github', 'atlas-tools', 'outputs', '__pycache__']);

function check(root) {
  const fails = [];
  let row, all;
  try {
    all = JSON.parse(fs.readFileSync(path.join(root, 'image-adaptation-licences.json'), 'utf8')).licences;
    row = all.find(r => r.atlas_permission_ref === GRANTS[0].ref);
  } catch (e) { return { error: 'image-adaptation-licences.json could not be read: ' + e.message }; }
  if (!row) return { error: 'no TimberIN L6 adaptation licence' };
  const rows = GRANTS.map(g => all.find(r => r.atlas_permission_ref === g.ref));
  /* The licence must stay OUT of the rights records: there it would become a
     hot-link host grant and change TimberIN's Results listing basis. */
  try {
    const rr = JSON.parse(fs.readFileSync(path.join(root, 'image-rights-records.json'), 'utf8')).records;
    if (rr.some(r => r.organisation_code === row.organisation_code || /timberin/i.test(r.organisation_name || '')))
      fails.push(['T4', 'a TimberIN record is in image-rights-records.json']);
  } catch (e) { return { error: 'image-rights-records.json could not be read: ' + e.message }; }

  /* T5 the licence file is PUBLIC (founder review, 20 Oct 2026): it carries
     only what establishes and validates the permission. No contact address,
     no mail-message or thread identifier, no Atlas internal id, no quoted
     correspondence. The private evidence is reached through evidence_ref. */
  {
    const text = fs.readFileSync(path.join(root, 'image-adaptation-licences.json'), 'utf8');
    const t5 = [];
    const strip = text.replace(/\b[0-9a-f]{64}\b/g, ' ');          // content hashes are not identifiers
    if (/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/.test(text)) t5.push('an email address');
    if (/mailto:|gmail|\bthread\b|message id/i.test(text)) t5.push('a mail reference');
    if (/\b[0-9a-f]{16}\b/.test(strip)) t5.push('a 16-hex mail identifier');
    if (/\b(rec|tbl|app|fld|sel)[A-Za-z0-9]{14}\b/.test(text)) t5.push('an Atlas internal id');
    const keys = new Set();
    (function walk(v) { if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) { keys.add(k); walk(x); } })(JSON.parse(text));
    for (const k of ['evidence', 'correspondence', 'permission', 'asked', 'answered', 'received_as',
                     'organisation_record', 'atlas_permission_record', 'contact', 'email'])
      if (keys.has(k)) t5.push('field "' + k + '"');
    for (const r of rows) if (r && !/^PN-EVID-[A-Z0-9-]+$/.test(String(r.evidence_ref || ''))) t5.push('no PN-EVID evidence_ref on ' + r.atlas_permission_ref);
    if (t5.length) fails.push(['T5', t5.join('; ')]);
  }

  /* T3 the records: each pinned grant exactly, and no other TimberIN licence */
  const t3 = [];
  const A = [];
  GRANTS.forEach((g, i) => {
    const r = rows[i];
    if (!r) { t3.push('the grant ' + g.ref + ' is missing'); return; }
    const As = Array.isArray(r.approved_assets) ? r.approved_assets : [];
    A.push(...As);
    const tag = g.ref + ': ';
    if (r.organisation_name !== 'TimberIN' || r.organisation_code !== row.organisation_code) t3.push(tag + 'organisation');
    if (r.modification_permitted !== true) t3.push(tag + 'modification_permitted');
    if (r.hotlinking_permitted !== false) t3.push(tag + 'hotlinking_permitted is not false');
    if ('permitted_delivery_hosts' in r || 'permitted_domain' in r) t3.push(tag + 'a host grant is declared');
    if (r.required_credit !== g.credit) t3.push(tag + 'credit is ' + JSON.stringify(r.required_credit));
    if (!/^https:\/\/(www\.)?timberin\.com\/?$/.test(String(r.credit_link || ''))) t3.push(tag + 'credit link');
    if (As.length !== g.count) t3.push(tag + As.length + ' enumerated photographs, not ' + g.count);
    for (const a of As) {
      if (a.use !== 'adapted-into-composite') t3.push(a.id + ' use ' + a.use);
      if (a.bound_composite !== COMPOSITE) t3.push(a.id + ' bound to ' + a.bound_composite);
      if (!/^[0-9a-f]{64}$/.test(String(a.sha256 || ''))) t3.push(a.id + ' has no sha256');
    }
    const ap = r.asset_approval || {};
    if (ap.default_for_unlisted !== 'NOT_AUTHORISED' || ap.approved_count !== g.count) t3.push(tag + 'asset_approval');
  });
  const extra = all.filter(r => (r.organisation_code === row.organisation_code || /timberin/i.test(r.organisation_name || ''))
                               && !GRANTS.some(g => g.ref === r.atlas_permission_ref));
  if (extra.length) t3.push(extra.length + ' unlisted TimberIN licence(s): ' + extra.map(r => r.atlas_permission_ref).join(', '));
  if (t3.length) fails.push(['T3', t3.join('; ')]);

  /* T1 / T2 the published tree */
  const shas = new Set(A.map(a => a.sha256));
  const t1 = [], t2 = [];
  (function walk(d, rel) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (SKIP.has(e.name) || e.name.startsWith('.')) continue;
      const full = path.join(d, e.name), r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) { walk(full, r); continue; }
      const buf = fs.readFileSync(full);
      if (shas.has(sha(buf))) t2.push(r);
      if (!/\.(html|webmanifest|json)$/i.test(e.name)) continue;
      const body = buf.toString('utf8').replace(/<!--[\s\S]*?-->/g, ' ');
      const urls = new Set();
      for (const m of body.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
      for (const m of body.matchAll(/\b(?:srcset|imagesrcset|poster|data-src|data-bg)\s*=\s*["']([^"']+)["']/gi))
        m[1].split(',').forEach(p => urls.add(p.trim().split(/\s+/)[0]));
      for (const m of body.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
      for (const m of body.matchAll(/<meta[^>]+content=["'](https?:[^"']+)["']/gi)) urls.add(m[1]);
      for (const m of body.matchAll(/"(?:src|img|image|image_url)"\s*:\s*"([^"]+)"/gi)) urls.add(m[1]);
      for (const u of urls) {
        let host;
        try { host = new URL(u.replace(/&amp;/g, '&'), 'https://plotnua.ie/').hostname.toLowerCase(); } catch { continue; }
        if (HOSTS.some(h => host === h || host.endsWith('.' + h))) t1.push(r + ' → ' + u.slice(0, 90));
      }
    }
  })(root, '');
  if (t1.length) fails.push(['T1', t1.slice(0, 4).join('; ')]);
  if (t2.length) fails.push(['T2', t2.slice(0, 4).join('; ')]);
  return { fails };
}

console.log('TIMBERIN CONTAINMENT PROOF');
console.log('='.repeat(76));
const real = check(ROOT);
if (real.error) { console.log('  INSTRUMENT UNAVAILABLE: ' + real.error); process.exit(2); }
const realIds = real.fails.map(f => f[0]);
for (const [id, what] of [['T5', 'the public licence carries no private correspondence details, only a PN-EVID evidence reference'],
                          ['T4', 'no TimberIN record in image-rights-records.json (no host grant, no listing change)'],
                          ['T1', 'no externally hosted TimberIN image on any published page'],
                          ['T2', 'no byte copy of any of the three source photographs in the published tree'],
                          ['T3', 'the two grants: two hot-tub photographs and one sauna photograph, adapted, bound to ' + COMPOSITE + ', and nothing else']]) {
  const f = real.fails.find(x => x[0] === id);
  console.log(`  ${f ? 'FAIL' : 'PASS'}  ${id} ${what}${f ? '\n        ' + f[1] : ''}`);
}
if (SELF_ONLY) process.exit(realIds.length ? 1 : 0);

/* ── capability: every check must be seen to refuse ──────────────────── */
console.log('-'.repeat(76));
const records = fs.readFileSync(path.join(ROOT, 'image-adaptation-licences.json'), 'utf8');
const recs = JSON.parse(records);
const rightsText = fs.readFileSync(path.join(ROOT, 'image-rights-records.json'), 'utf8');
function mini({ page = '<!doctype html><title>t</title><p>ok</p>', files = {}, edit = null, edit2 = null, rightsEdit = null } = {}) {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'pn-tbn-'));
  const r = JSON.parse(records);
  if (edit) edit(r.licences.find(x => x.atlas_permission_ref === 'L6-TIMBERIN-TWO-PHOTOS-20261019'));
  if (edit2) edit2(r.licences.find(x => x.atlas_permission_ref === 'TIMBERIN-NORDIC-CUBE-SAUNA-20261022'), r);
  fs.writeFileSync(path.join(d, 'image-adaptation-licences.json'), JSON.stringify(r, null, 2));
  const rr = JSON.parse(rightsText);
  if (rightsEdit) rightsEdit(rr, r.licences[0]);
  fs.writeFileSync(path.join(d, 'image-rights-records.json'), JSON.stringify(rr, null, 2));
  fs.writeFileSync(path.join(d, 'index.html'), page);
  for (const [k, v] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(d, k)), { recursive: true });
    fs.writeFileSync(path.join(d, k), v);
  }
  return d;
}
const hot = u => `<!doctype html><title>t</title><figure><img src="${u}" alt="Hot tub">`
  + `<figcaption><a href="https://www.timberin.com/">${CREDIT}</a></figcaption></figure>`;
const planted = Buffer.from('a stand-in for a source photograph');
let proved = 0, notProved = 0;
const CASES = [
  ['C-T1a', 'T1', 'a timberin.com image hot-linked WITH the credit', { page: hot('https://www.timberin.com/wp-content/uploads/tub.jpg') }, true],
  ['C-T1b', 'T1', 'Photograph A hot-linked from woodenhottubsale.co.uk', { page: hot(recs.licences.find(r => r.organisation_name === 'TimberIN').approved_assets[0].url) }],
  ['C-T1c', 'T1', 'a TimberIN image in a script configuration', { page: '<script class="pn-mx-config" type="application/json">{"p":[{"src":"https://timberin.co.uk/x.jpg"}]}</script>' }],
  ['C-T1d', 'T1', 'a TimberIN image as a CSS background', { page: '<div style="background:url(https://shop.timberin.com/a.webp)"></div>' }],
  ['C-T2', 'T2', 'a source photograph re-hosted unmodified', { files: { 'assets/img/tub.jpg': planted },
      edit: r => { r.approved_assets[0].sha256 = sha(planted); } }],
  ['C-T3a', 'T3', 'hot-linking permitted', { edit: r => { r.hotlinking_permitted = true; } }],
  ['C-T3b', 'T3', 'a third photograph enumerated', { edit: r => { r.approved_assets.push({ ...r.approved_assets[0], id: 'C', sha256: sha('c') }); } }],
  ['C-T3c', 'T3', 'a photograph granted for unmodified use', { edit: r => { r.approved_assets[1].use = 'hotlink-unmodified'; } }],
  ['C-T3d', 'T3', 'a photograph bound to a different image', { edit: r => { r.approved_assets[0].bound_composite = 'homepage-hero'; } }],
  ['C-T3e', 'T3', 'a host grant declared on the licence', { edit: r => { r.permitted_domain = 'woodenhottubsale.co.uk'; } }],
  ['C-T4', 'T4', 'the licence copied into the rights records as a host grant', { rightsEdit: (rr, l) => {
      rr.records.push({ ...l, permitted_domain: 'timberin.com' }); } }],
  ['C-T3f', 'T3', 'the credit reworded', { edit: r => { r.required_credit = 'Photo: TimberIN'; } }],
  ['C-T5a', 'T5', 'a supplier email address in the public licence', { edit: r => { r.conditions.push('Send the link to someone@example.com'); } }],
  ['C-T5b', 'T5', 'a mail-message identifier in the public licence', { edit: r => { r.note = 'see message 0123456789abcdef'; } }],
  ['C-T5c', 'T5', 'an Atlas internal record id in the public licence', { edit: r => { r.organisation_record = 'recAAAAAAAAAAAAAA'; } }],
  ['C-T5d', 'T5', 'quoted correspondence in the public licence', { edit: r => { r.correspondence = { answered: 'We are happy ...' }; } }],
  ['C-T5e', 'T5', 'free-text evidence instead of a PN-EVID reference', { edit: r => { delete r.evidence_ref; r.evidence = 'the supplier replied on 20 Oct'; } }],
  ['C-T3g', 'T3', 'unlisted TimberIN images authorised by default', { edit: r => { r.asset_approval.default_for_unlisted = 'AUTHORISED'; } }],
  /* 22 Oct 2026 · the second grant (Nordic Cube sauna) */
  ['C-T2b', 'T2', 'the sauna photograph re-hosted unmodified', { files: { 'assets/img/sauna.jpg': planted },
      edit2: r => { r.approved_assets[0].sha256 = sha(planted); } }],
  ['C-T3h', 'T3', 'a second photograph enumerated in the sauna grant', { edit2: r => { r.approved_assets.push({ ...r.approved_assets[0], id: 'D', sha256: sha('d') }); } }],
  ['C-T3i', 'T3', 'the sauna credit reworded', { edit2: r => { r.required_credit = 'Sauna by TimberIN'; } }],
  ['C-T3j', 'T3', 'the sauna grant permits hot-linking', { edit2: r => { r.hotlinking_permitted = true; } }],
  ['C-T3k', 'T3', 'a third, unlisted TimberIN licence added', { edit2: (r, all) => { all.licences.push({ ...r, atlas_permission_ref: 'TIMBERIN-HOBBITON-1' }); } }],
  ['C-T3l', 'T3', 'the sauna photograph bound to a different image', { edit2: r => { r.approved_assets[0].bound_composite = 'homepage-hero'; } }],
  ['C-T5f', 'T5', 'free-text evidence on the sauna grant', { edit2: r => { r.evidence_ref = 'email from the CEO, 22 Oct'; } }],
];
for (const [id, want, why, opts, gateToo] of CASES) {
  const dir = mini(opts);
  const res = check(dir);
  const ids = res.error ? [] : res.fails.map(f => f[0]);
  if (ids.includes(want)) { proved++; console.log(`  PROVED      ${id.padEnd(6)} ${why}  [${want}]`); }
  else { notProved++; console.log(`  ${res.error ? 'BLIND  ' : 'VACUOUS'}     ${id.padEnd(6)} ${why}  (failed: ${ids.join(',') || 'nothing'})`); }
  if (gateToo) {
    /* Show the gap this file closes: the rights gate alone, given the real
       manifest, passes the hot-linked timberin.com image with its credit. */
    let gateCode = 0;
    try {
      execFileSync('node', [path.join(HERE, 'validate-image-rights.js'), '--scan-html', dir,
        '--permissions', path.join(ROOT, 'image-rights-manifest.json'), '--max-age-days', '30'],
        { encoding: 'utf8', stdio: 'pipe' });
    } catch (e) { gateCode = e.status; }
    console.log(`              the rights gate alone on the same page: exit ${gateCode}`
      + (gateCode === 0 ? ' (PASSES it: a TimberIN host grant has appeared)' : ' (refuses it too: no host grant)'));
    if (gateCode === 0) notProved++;
  }
  fs.rmSync(dir, { recursive: true, force: true });
}
console.log('-'.repeat(76));
console.log(`real tree: ${realIds.length ? 'BREACH ' + realIds.join(',') : 'contained'} · `
  + `${CASES.length} mutations, ${proved} proved, ${notProved} not proved`);
process.exit(realIds.length || notProved ? 1 : 0);
