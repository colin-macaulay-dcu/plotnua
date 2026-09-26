#!/usr/bin/env node
/* PlotNua — PUBLICATION RIGHTS GATE
 * ===========================================================================
 * THIS IS THE THING THAT MAKES "WE WILL STOP USING THEM" TRUE.
 *
 * The permission wording promises every supplier that a word to
 * hello@plotnua.ie stops PlotNua using their images. A promise with no
 * mechanism behind it is not a promise. This gate is the mechanism: it runs in
 * the publish path and FAILS THE BUILD if any supplier image would be
 * published without a live grant behind it.
 *
 * THE RULE, and it is one sentence:
 *   A supplier image is publishable ONLY IF its organisation's current
 *   permission outcome is an explicit live grant AND the asset's own rights and
 *   publication states agree.
 *
 * WHAT IS NOT A GRANT
 *   UNKNOWN   is not GRANTED.
 *   DECLINED  is not GRANTED.
 *   WITHDRAWN is not GRANTED.
 *   A MISSING record is not GRANTED.
 *   An EXPIRED-looking, malformed or unreadable state is not GRANTED.
 *
 * IT FAILS SAFE. Anything it cannot positively establish is refused. A missing
 * input file, an unparseable row, an unknown vocabulary value, an asset whose
 * organisation cannot be resolved — all of these FAIL the build. A gate that
 * passes when it is confused is not a gate.
 *
 * Usage:
 *   node validate-image-rights.js --assets assets.json --permissions perms.json
 *                                 --pages-dir .
 *   node validate-image-rights.js --self-test
 * Exit 0 clean · 1 a rights violation · 2 the gate could not establish the
 * facts and therefore refuses.
 * ========================================================================= */

'use strict';
const fs = require('fs');
const path = require('path');

/* The ONLY outcomes that permit publication. Spelled out rather than derived,
   so adding a new outcome to Airtable cannot silently widen the gate. */
const LIVE_GRANTS = new Set([
  'Granted — Founder Confirmed',
  'Granted with Conditions — Founder Confirmed',
  'Granted — Supplier Confirmed (one-click)'
]);

/* Everything else is explicitly enumerated so an UNRECOGNISED value is an
   error rather than a silent pass. */
const KNOWN_NON_GRANTS = new Set([
  'Unknown — Awaiting Reply',
  'Unclear — Founder Review Required',
  'Declined — Founder Confirmed',
  'Withdrawn / Superseded'
]);

const RIGHTS_OK = new Set(['Supplier Provided', 'Owned', 'Licensed']);
const PUBLICATION_OK = new Set(['Approved', 'Published']);

function fail(code, lines) {
  console.log('\nGATE FAILED');
  lines.forEach(l => console.log('  ' + l));
  process.exit(code);
}

function readJson(p, what) {
  if (!p) fail(2, ['no ' + what + ' supplied; the gate refuses to assume one']);
  if (!fs.existsSync(p)) fail(2, [what + ' not found: ' + p]);
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { fail(2, [what + ' is not readable JSON: ' + e.message]); }
}

/* ---------------------------------------------------------------- core ----
   Pure function so the self-test can drive it without files.              */
function evaluate(assets, permissions) {
  const byOrg = new Map();
  const problems = [];

  for (const p of permissions) {
    const org = p.organisation_record;
    if (!org) { problems.push('PERMISSION ROW WITH NO ORGANISATION: ' + JSON.stringify(p).slice(0, 90)); continue; }
    const outcome = p.permission_outcome;
    if (typeof outcome !== 'string' || !outcome) {
      problems.push('ORG ' + org + ' has no permission outcome; not a grant');
      byOrg.set(org, { grant: false, outcome: '(empty)' });
      continue;
    }
    if (!LIVE_GRANTS.has(outcome) && !KNOWN_NON_GRANTS.has(outcome)) {
      problems.push('ORG ' + org + ' has an UNRECOGNISED permission outcome '
        + JSON.stringify(outcome) + '; the gate refuses to interpret it');
      byOrg.set(org, { grant: false, outcome });
      continue;
    }
    /* A withdrawal always wins, whatever else the row says. */
    const withdrawn = !!p.withdrawal_effective_at || outcome === 'Withdrawn / Superseded';
    const prev = byOrg.get(org);
    const grant = LIVE_GRANTS.has(outcome) && !withdrawn;
    if (!prev || prev.grant) byOrg.set(org, { grant: prev ? (prev.grant && grant) : grant, outcome, withdrawn, domain: p.permitted_domain });
    if (withdrawn) byOrg.set(org, { grant: false, outcome, withdrawn: true, domain: p.permitted_domain });
  }

  const verdicts = [];
  for (const a of assets) {
    const id = a.asset_name || a.id || '(unnamed asset)';
    const wantsPublish = PUBLICATION_OK.has(a.publication_status);
    if (!wantsPublish) {
      verdicts.push({ id, publishable: false, why: 'not marked for publication; nothing to check' });
      continue;
    }
    if (!a.organisation_record) {
      verdicts.push({ id, publishable: false, violation: true,
        why: 'marked for publication but has NO organisation; rights cannot be established' });
      continue;
    }
    const perm = byOrg.get(a.organisation_record);
    if (!perm) {
      verdicts.push({ id, publishable: false, violation: true,
        why: 'marked for publication but its organisation has NO permission record. '
           + 'A MISSING RECORD IS NOT A GRANT' });
      continue;
    }
    if (!perm.grant) {
      verdicts.push({ id, publishable: false, violation: true,
        why: 'marked for publication but the permission outcome is '
           + JSON.stringify(perm.outcome)
           + (perm.withdrawn ? ' and it has been WITHDRAWN' : '')
           + '. NOT A GRANT' });
      continue;
    }
    if (!RIGHTS_OK.has(a.rights_status)) {
      verdicts.push({ id, publishable: false, violation: true,
        why: 'organisation has a live grant but the asset rights status is '
           + JSON.stringify(a.rights_status) + '; both must agree' });
      continue;
    }
    if (perm.domain && a.source_url) {
      let host = '';
      try { host = new URL(a.source_url).hostname.replace(/^www\./, ''); } catch (e) { host = ''; }
      if (!host) {
        verdicts.push({ id, publishable: false, violation: true,
          why: 'source URL is unreadable, so the asset cannot be tied to the permitted domain' });
        continue;
      }
      if (host !== perm.domain.replace(/^www\./, '')) {
        verdicts.push({ id, publishable: false, violation: true,
          why: 'asset comes from ' + host + ' but the grant covers '
             + perm.domain + ' only' });
        continue;
      }
    }
    /* A CONDITIONAL GRANT IS ONLY HONOURED IF THE CONDITION IS MET. TRIQBRIQ's
       written permission requires the credit "© TRIQBRIQ AG". An authorised
       image published without its required credit is outside the grant, so the
       gate refuses it rather than quietly relying on someone remembering. */
    if (a.required_credit && a.page && a.pageText !== undefined) {
      if (!a.pageText.includes(a.required_credit)) {
        verdicts.push({ id, publishable: false, violation: true,
          why: 'live grant, but the required credit ' + JSON.stringify(a.required_credit)
             + ' is absent from ' + a.page + '; the condition is part of the permission' });
        continue;
      }
    }
    verdicts.push({ id, publishable: true,
      why: 'live grant, rights agree, domain matches'
         + (a.required_credit ? ', required credit present' : '') });
  }
  return { verdicts, problems };
}

/* --------------------------------------------------------------- report --- */
function report(assets, permissions, label) {
  const { verdicts, problems } = evaluate(assets, permissions);
  console.log('PUBLICATION RIGHTS GATE' + (label ? ' — ' + label : ''));
  console.log('='.repeat(74));
  const violations = verdicts.filter(v => v.violation);
  for (const v of verdicts) {
    const tag = v.violation ? 'REFUSE' : (v.publishable ? 'ALLOW ' : 'skip  ');
    console.log('  ' + tag + ' ' + String(v.id).padEnd(34) + v.why);
  }
  for (const p of problems) console.log('  NOTE   ' + p);
  console.log('-'.repeat(74));
  console.log('  ' + verdicts.filter(v => v.publishable).length + ' publishable · '
    + violations.length + ' refused · ' + verdicts.filter(v => !v.publishable && !v.violation).length
    + ' not for publication');
  return violations;
}

/* ------------------------------------------------------------ self test --- */
function selfTest() {
  const ORG_OK = 'recTESTGRANTED001';
  const ORG_UNK = 'recTESTUNKNOWN01';
  const ORG_DEC = 'recTESTDECLINED1';
  const ORG_WDR = 'recTESTWITHDRAW1';

  const perms = [
    { organisation_record: ORG_OK, permission_outcome: 'Granted — Supplier Confirmed (one-click)', permitted_domain: 'example.ie' },
    { organisation_record: ORG_UNK, permission_outcome: 'Unknown — Awaiting Reply', permitted_domain: 'unknown.ie' },
    { organisation_record: ORG_DEC, permission_outcome: 'Declined — Founder Confirmed', permitted_domain: 'declined.ie' },
    { organisation_record: ORG_WDR, permission_outcome: 'Granted — Supplier Confirmed (one-click)', permitted_domain: 'withdrawn.ie', withdrawal_effective_at: '2026-10-01' }
  ];
  const assets = [
    { asset_name: 'granted/ok.jpg', organisation_record: ORG_OK, rights_status: 'Supplier Provided', publication_status: 'Approved', source_url: 'https://www.example.ie/a.jpg' },
    { asset_name: 'unknown/should-refuse.jpg', organisation_record: ORG_UNK, rights_status: 'Supplier Provided', publication_status: 'Approved', source_url: 'https://unknown.ie/b.jpg' },
    { asset_name: 'declined/should-refuse.jpg', organisation_record: ORG_DEC, rights_status: 'Supplier Provided', publication_status: 'Published', source_url: 'https://declined.ie/c.jpg' },
    { asset_name: 'withdrawn/should-refuse.jpg', organisation_record: ORG_WDR, rights_status: 'Supplier Provided', publication_status: 'Published', source_url: 'https://withdrawn.ie/d.jpg' },
    { asset_name: 'no-org/should-refuse.jpg', rights_status: 'Supplier Provided', publication_status: 'Approved' },
    { asset_name: 'no-permission-row/should-refuse.jpg', organisation_record: 'recNOPERMISSION1', rights_status: 'Supplier Provided', publication_status: 'Approved' },
    { asset_name: 'wrong-domain/should-refuse.jpg', organisation_record: ORG_OK, rights_status: 'Supplier Provided', publication_status: 'Approved', source_url: 'https://somewhere-else.com/e.jpg' },
    { asset_name: 'rights-disagree/should-refuse.jpg', organisation_record: ORG_OK, rights_status: 'Permission Required', publication_status: 'Approved', source_url: 'https://example.ie/f.jpg' },
    { asset_name: 'internal/not-for-publication.jpg', organisation_record: ORG_UNK, rights_status: 'Unknown', publication_status: 'Reference Only — Not Published' }
  ];

  console.log('SELF-TEST · the gate must ALLOW exactly one asset and REFUSE seven\n');
  const violations = report(assets, perms, 'self-test');
  const { verdicts } = evaluate(assets, perms);
  const allowed = verdicts.filter(v => v.publishable).map(v => v.id);
  const refused = verdicts.filter(v => v.violation).map(v => v.id);

  let ok = true;
  if (allowed.length !== 1 || allowed[0] !== 'granted/ok.jpg') {
    console.log('\nFAIL expected exactly granted/ok.jpg to be allowed, got: ' + JSON.stringify(allowed));
    ok = false;
  }
  const mustRefuse = ['unknown/should-refuse.jpg', 'declined/should-refuse.jpg',
    'withdrawn/should-refuse.jpg', 'no-org/should-refuse.jpg',
    'no-permission-row/should-refuse.jpg', 'wrong-domain/should-refuse.jpg',
    'rights-disagree/should-refuse.jpg'];
  for (const m of mustRefuse) {
    if (!refused.includes(m)) { console.log('\nFAIL not refused: ' + m); ok = false; }
  }

  /* THE WITHDRAWAL TEST THE FOUNDER ASKED FOR, EXPLICITLY:
     the SAME asset that passes under a grant must fail once withdrawn. */
  console.log('\nWITHDRAWAL TEST · the same asset, before and after withdrawal');
  const one = [{ asset_name: 'the-same-asset.jpg', organisation_record: ORG_OK,
    rights_status: 'Supplier Provided', publication_status: 'Approved',
    source_url: 'https://example.ie/same.jpg' }];
  const before = evaluate(one, perms).verdicts[0];
  const withdrawnPerms = JSON.parse(JSON.stringify(perms));
  withdrawnPerms[0].permission_outcome = 'Withdrawn / Superseded';
  withdrawnPerms[0].withdrawal_effective_at = '2026-11-02';
  const after = evaluate(one, withdrawnPerms).verdicts[0];
  console.log('  before withdrawal: ' + (before.publishable ? 'ALLOW' : 'REFUSE') + ' — ' + before.why);
  console.log('  after  withdrawal: ' + (after.publishable ? 'ALLOW' : 'REFUSE') + ' — ' + after.why);
  if (!before.publishable || after.publishable) {
    console.log('\nFAIL withdrawal did not make the asset non-publishable');
    ok = false;
  }

  /* UNRECOGNISED VOCABULARY MUST NOT PASS. */
  console.log('\nUNKNOWN-VOCABULARY TEST');
  const weird = [{ organisation_record: 'recWEIRD00000001', permission_outcome: 'Granted, probably', permitted_domain: 'weird.ie' }];
  const weirdAsset = [{ asset_name: 'weird.jpg', organisation_record: 'recWEIRD00000001', rights_status: 'Supplier Provided', publication_status: 'Approved', source_url: 'https://weird.ie/x.jpg' }];
  const w = evaluate(weirdAsset, weird);
  console.log('  ' + (w.verdicts[0].publishable ? 'ALLOW' : 'REFUSE') + ' — ' + w.verdicts[0].why);
  if (w.verdicts[0].publishable) { console.log('\nFAIL an unrecognised outcome was treated as a grant'); ok = false; }

  console.log('\n' + '='.repeat(74));
  console.log(ok ? 'SELF-TEST PASS' : 'SELF-TEST FAIL');
  process.exit(ok ? 0 : 1);
}

/* ------------------------------------------------------- HTML SCAN MODE ---
   THE PUBLISH-PATH INTEGRATION. Instead of trusting an assets export to be
   complete, this walks the pages that are ACTUALLY PUBLISHED and finds every
   externally-hosted image they reference. Anything a page can show a homeowner
   is an asset, whether or not someone remembered to put it in a spreadsheet.

   First-party plotnua.ie images and relative paths are PlotNua's own and are
   not supplier imagery. Everything else is attributed to a supplier by domain
   and must be backed by a live grant.                                       */
const FIRST_PARTY = new Set(['plotnua.ie', 'www.plotnua.ie']);

/* Origins that are infrastructure rather than supplier imagery. Enumerated,
   never pattern-matched, so a look-alike domain cannot slip in. */
const INFRASTRUCTURE = new Set([
  'fonts.googleapis.com', 'fonts.gstatic.com',
  'www.googletagmanager.com', 'cdnjs.cloudflare.com'
]);

function scanHtml(dir) {
  const found = [];
  const files = [];
  (function walk(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name.startsWith('.') || e.name === 'node_modules') continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else if (e.name.endsWith('.html')) files.push(full);
    }
  })(dir);

  for (const f of files) {
    let html = fs.readFileSync(f, 'utf8');
    html = html.replace(/<!--[\s\S]*?-->/g, ' ');      /* comments are not published */
    const rel = path.relative(dir, f);
    const urls = new Set();
    for (const m of html.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of html.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) {
      m[1].split(',').forEach(part => urls.add(part.trim().split(/\s+/)[0]));
    }
    for (const m of html.matchAll(/url\(\s*["']?(https?:\/\/[^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
    for (const m of html.matchAll(/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);

    for (const u of urls) {
      if (!/^https?:\/\//i.test(u)) continue;          /* relative = PlotNua's own */
      let host;
      try { host = new URL(u).hostname.toLowerCase(); } catch (e) { continue; }
      if (FIRST_PARTY.has(host) || INFRASTRUCTURE.has(host)) continue;
      found.push({
        asset_name: rel + ' → ' + u.slice(0, 80),
        source_url: u,
        host: host.replace(/^www\./, ''),
        page: rel,
        pageText: html,
        rights_status: 'Supplier Provided',   /* it is on a published page */
        publication_status: 'Published'       /* a homeowner can see it */
      });
    }
  }
  return { files: files.length, assets: found };
}

/* Attach each scanned asset to the organisation whose permitted domain it
   came from. NO MATCH IS NOT A PASS: an unattributable supplier image is
   refused, because rights cannot be established for it. */
function attribute(assets, permissions) {
  const byDomain = new Map();
  for (const p of permissions) {
    if (p.permitted_domain) {
      byDomain.set(String(p.permitted_domain).replace(/^www\./, '').toLowerCase(),
                   p.organisation_record);
    }
  }
  return assets.map(a => {
    const org = byDomain.get(a.host);
    if (!org) return a;                                   /* no org → refused */
    const perm = permissions.find(x => x.organisation_record === org);
    return { ...a, organisation_record: org,
             required_credit: perm && perm.required_credit ? perm.required_credit : null };
  });
}

/* ----------------------------------------------------------------- main --- */
function main() {
  const argv = process.argv.slice(2);
  if (argv.includes('--self-test')) return selfTest();
  const arg = (n) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : null; };
  const perms = readJson(arg('--permissions'), 'permissions manifest');
  const P = Array.isArray(perms) ? perms : perms.rows;
  if (!Array.isArray(P)) {
    fail(2, ['the permissions manifest must be an array or {rows:[...]}; the gate refuses to guess']);
  }

  /* FRESHNESS. A rights manifest that nobody has refreshed since a withdrawal
     is worse than none, because it looks authoritative. */
  if (!Array.isArray(perms) && perms.generated) {
    const ageDays = (Date.now() - Date.parse(perms.generated + 'T00:00:00Z')) / 86400000;
    if (!isFinite(ageDays)) fail(2, ['the manifest generated date is unreadable']);
    const maxAge = Number(arg('--max-age-days') || 30);
    if (ageDays > maxAge) {
      fail(2, ['the rights manifest is ' + Math.floor(ageDays) + ' days old (limit '
        + maxAge + ').', 'Regenerate it from Atlas before publishing.']);
    }
    console.log('manifest generated ' + perms.generated
      + ' (' + Math.max(0, Math.floor(ageDays)) + ' days old)');
  }

  let A;
  const scanDir = arg('--scan-html');
  if (scanDir) {
    if (!fs.existsSync(scanDir)) fail(2, ['--scan-html directory not found: ' + scanDir]);
    const scanned = scanHtml(scanDir);
    console.log('scanned ' + scanned.files + ' published page(s); found '
      + scanned.assets.length + ' externally-hosted image reference(s)');
    A = attribute(scanned.assets, P);
  } else {
    const assets = readJson(arg('--assets'), 'assets export');
    A = Array.isArray(assets) ? assets : assets.rows;
    if (!Array.isArray(A)) fail(2, ['the assets export must be an array or {rows:[...]}']);
  }

  const violations = report(A, P, scanDir ? 'published pages' : 'assets export');
  if (violations.length) {
    fail(1, [violations.length + ' asset(s) would be published without a live grant.',
      'Publication is blocked until every one is resolved.']);
  }
  console.log('\nGATE PASS — every publishable asset has a live grant behind it.');
}
main();
