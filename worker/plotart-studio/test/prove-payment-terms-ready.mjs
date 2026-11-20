// PlotArt payment pilot texts, issued (20 Nov 2026): PA-PAY-2026-11 and PA-BPT-2026-11 in agreements/payment-issued.
//   node test/prove-payment-terms-ready.mjs
// Read-only apart from a rebuild into a temporary copy. Checks the issue form, its fingerprints, the rules build-assets.mjs
// applies to issued texts, the founder-protection and consumer wording, and migration 0018 against migration 0017.
import { readFileSync, cpSync, mkdtempSync, rmSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = join(dirname(fileURLToPath(import.meta.url)), '..') + '/';
let pass = 0, fail = 0;
const check = (name, ok, info) => { ok ? pass++ : fail++; console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${name}${ok || info === undefined ? '' : '  ' + JSON.stringify(info).slice(0, 300)}`); };
const sha = b => createHash('sha256').update(b).digest('hex');
const READY = HERE + 'agreements/payment-issued/';
const APPROVED = { 'PA-PAY-2026-11': 'ff0a8c87f360a60159d9aa2491d957a207791b656c36ccfa517429f60d4464bd', 'PA-BPT-2026-11': 'c570c06fe00577db3c5718c2b5b40fc6f834a2a2f2b97678b3a1978d74eb332a' };
const F = JSON.parse(readFileSync(READY + 'fingerprints.json', 'utf8')).documents;
const text = id => readFileSync(READY + id + '.html', 'utf8');
const plain = id => text(id).replace(/<style[\s\S]*?<\/style>/, '').replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/\s+/g, ' ');

console.log('— R1 fingerprints and the build-assets rules for issued texts');
check('R1a exactly the two pilot texts, with the right kinds', JSON.stringify(Object.entries(F).map(([k, v]) => [k, v.kind]).sort()) === JSON.stringify([['PA-BPT-2026-11', 'buyer_purchase_terms'], ['PA-PAY-2026-11', 'artist_payment_addendum']]), F);
for (const id of Object.keys(F)) {
  check(`R1b ${id}: the file matches its recorded fingerprint`, sha(readFileSync(READY + id + '.html')) === F[id].html_sha256);
  check(`R1c ${id}: not a test placeholder (build-assets refuses TEST ids and "TEST ONLY" text in payment-issued)`, !id.includes('TEST') && !text(id).includes('TEST ONLY'));
  check(`R1d ${id}: no draft wording, review brackets or unfilled placeholders`, !/DRAFT|professional review|\[for review|Founder decision|\{[^}]*\}/i.test(plain(id)), plain(id).match(/DRAFT|professional review|\[for review|Founder decision|\{[^}]*\}/i));
  check(`R1e ${id}: carries its identifier and issue date`, plain(id).includes(`Identifier ${id} · Text of 20 November 2026`));
}
check('R1f the approved fingerprints are unchanged (PR #36 approval: ff0a8c87…, c570c06f…)', Object.keys(APPROVED).every(id => F[id] && F[id].html_sha256 === APPROVED[id] && sha(readFileSync(READY + id + '.html')) === APPROVED[id]));
check('R1g issued, not duplicated: payment-ready/ no longer exists', !existsSync(HERE + 'agreements/payment-ready'));
const BUNDLE = readFileSync(HERE + 'src/payment-terms.js', 'utf8');
const B = JSON.parse(BUNDLE.slice(BUNDLE.indexOf('{'), BUNDLE.lastIndexOf('}') + 1));
check('R1h the committed Worker bundle (src/payment-terms.js) carries exactly these two texts, byte for byte, and nothing marked TEST',
  JSON.stringify(Object.keys(B).sort()) === JSON.stringify(Object.keys(APPROVED).sort()) && Object.keys(APPROVED).every(id => B[id].html === text(id) && sha(B[id].html) === APPROVED[id] && B[id].kind === F[id].kind) && !BUNDLE.includes('TEST ONLY'));

console.log('— R2 the build is reproducible');
const tmp = mkdtempSync(join(tmpdir(), 'pa-terms-'));
cpSync(HERE + 'agreements', tmp + '/agreements', { recursive: true });
execFileSync(process.execPath, [tmp + '/agreements/build-payment.cjs'], { stdio: 'ignore' });
const F2 = JSON.parse(readFileSync(tmp + '/agreements/payment-ready/fingerprints.json', 'utf8')).documents;
check('R2 rebuilding from the drafts gives byte-identical files to the issued ones', Object.keys(F).every(id => F2[id] && F2[id].html_sha256 === F[id].html_sha256));
rmSync(tmp, { recursive: true, force: true });

console.log('— R3 Founding Artist rights and the agreement link (PA-PAY)');
const PAY = plain('PA-PAY-2026-11');
check('R3a Founding Enquiries stay commission-free permanently and are not taken through the pilot', PAY.includes('Every Founding Enquiry stays commission-free permanently') && PAY.includes('including every sale arising from a Founding Enquiry'));
check('R3b PA-FAA is unchanged by the addendum', PAY.includes('this addendum changes nothing in PA-FAA'));
check('R3c the addendum is a written variation under PA-GAA clause 13, for pilot orders only', PAY.includes('written variation under PA-GAA clause 13') && PAY.includes('It applies only to pilot orders'));
check('R3d the artist agreement prevails over anything that would reduce a right', PAY.includes("the artist's agreement prevails on that point"));
check('R3e commission: 15% of the artwork only, never on delivery; combined deduction never more than the commission', PAY.includes('Commission is never charged on delivery') && PAY.includes('is no more than the commission'));
check('R3f international card example uses 3.15% + €0.25 (€34.11 + €7.85) and example 4 nets €485.00', PAY.includes('international cards 3.15% + €0.25') && PAY.includes('€34.11 + €7.85') && PAY.includes('€4.68 directly') && PAY.includes('€485.00'));

console.log('— R4 consumer disclosures (PA-BPT), against CCPC guidance and CRA 2022');
const BPT = plain('PA-BPT-2026-11');
check('R4a trader status on the basis of the seller\'s declaration (CRA 2022 s.107)', BPT.includes('The seller has declared to PlotArt that they sell as a trader'));
check('R4b how obligations are shared between PlotArt and the seller (CCPC marketplace duty)', BPT.includes('The seller is responsible for the artwork, its delivery, cancellations, returns and refunds') && BPT.includes('PlotArt is responsible for the accuracy of the information it presents'));
check('R4c how artists and works are ordered; no paid placement (CCPC ranking information)', BPT.includes('No seller pays for placement'));
check('R4d commission disclosed and not added to the price', BPT.includes("PlotArt's commission") && BPT.includes('It is not added to what you pay'));
check('R4e contract confirmation sent by email (durable medium)', BPT.includes('PlotArt also emails it to you at the address you gave, as your confirmation of the contract'));
check('R4f 14-day cancellation from receipt; refund within 14 days; return cost stated in advance', BPT.includes('within 14 days from the day you') && BPT.includes('no later than 14 days after being told') && BPT.includes('Your quote states that cost'));
check('R4g 30-day short-term right: full refund including delivery to the same card; repair or replacement instead (CRA 2022 s.24)', BPT.includes('within 30 days of receiving it') && BPT.includes('including the delivery charge, to the card you paid with') && BPT.includes('repair or a replacement'));
check('R4h model cancellation form present, with no per-order placeholder left', BPT.includes('Model cancellation form') && BPT.includes('[artwork title], order reference [order reference]'));
check('R4i consumers keep the mandatory protection of their own country', BPT.includes('you keep the protection of the mandatory rules of your own country'));

console.log('— R5 migration 0018 installs exactly these fingerprints (applied to a scratch SQLite database after 0017)');
const py = `
import sqlite3,sys,json
db=sqlite3.connect(':memory:')
db.executescript(open(sys.argv[1]).read()); db.executescript(open(sys.argv[2]).read())
rows=db.execute("select doc_id,kind,html_sha256 from payment_terms order by doc_id").fetchall()
errs=[]
for sql in ["update payment_terms set title='x'","delete from payment_terms"]:
  try: db.execute(sql); errs.append('allowed: '+sql)
  except Exception as e: pass
print(json.dumps({'rows':rows,'errs':errs}))`;
const out = JSON.parse(execFileSync('python3', ['-c', py, HERE + 'migrations/0017_managed_checkout_pilot.sql', HERE + 'migrations/0018_payment_terms_issue.sql'], { encoding: 'utf8' }));
check('R5a 0018 inserts the two texts with the fingerprints of the files', JSON.stringify(out.rows) === JSON.stringify([['PA-BPT-2026-11', 'buyer_purchase_terms', F['PA-BPT-2026-11'].html_sha256], ['PA-PAY-2026-11', 'artist_payment_addendum', F['PA-PAY-2026-11'].html_sha256]]), out.rows);
check('R5b the installed rows can never change or be removed (0017 triggers)', out.errs.length === 0, out.errs);

console.log(`PAYMENT TERMS ISSUED · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
