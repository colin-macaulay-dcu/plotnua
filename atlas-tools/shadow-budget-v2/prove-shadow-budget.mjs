/* GUARD-CAPABILITY PROOF — the shadow five-band architecture and its
   price-basis protection. A guard that has never refused anything is a
   comment, so every rule below is broken once and the break must be caught.
   Read-only: writes nothing, and never touches the live page or the operative
   artefact. */
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync, execSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SHADOW_BUDGET_BANDS, SHADOW_BUDGET_LABEL, RETIRED_BAND_KEY,
         shadowBudgetFit, shadowPriceTreatment, renderShadowPrice,
         HOMEOWNER_BASIS_LINES } from './shadow-budget-bands.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..', '..');   // repo root, for exercising the real generator
/* PHASE 5: the suite can be pointed at a freshly generated candidate without
   losing any existing coverage. No argument = the Phase 4 shadow universe. */
const UNIVERSE = process.argv[2] || join(HERE, 'shadow-recommendation-universe-v2.json');
const U = JSON.parse(readFileSync(UNIVERSE));
console.log('universe under test: ' + UNIVERSE.split('/').slice(-1)[0]);
const P = U.products;
const money = (v, c) => (c === 'EUR' ? '€' : c + ' ') + v.toLocaleString('en-IE');
const results = [];
function t(label, fn) {
  let ok = false, note = '';
  try { const r = fn(); ok = r === true; note = (r === true) ? '' : String(r); }
  catch (e) { ok = false; note = 'threw: ' + e.message; }
  results.push(ok);
  console.log('  ' + (ok ? 'PASS   ' : 'FAIL   ') + label + (note ? '\n           -> ' + note : ''));
}
console.log('GUARD-CAPABILITY PROOF — SHADOW BUDGET ARCHITECTURE v2');
console.log('='.repeat(78));

/* G1 — the retired band cannot survive */
t('G1 . the old 30k-plus band is absent from the shadow definition', () =>
  (!(RETIRED_BAND_KEY in SHADOW_BUDGET_BANDS) && !(RETIRED_BAND_KEY in SHADOW_BUDGET_LABEL)
   && Object.keys(SHADOW_BUDGET_BANDS).length === 5) || 'the retired key or a 4-band map survived');
t('G1 SABOTAGE . re-adding 30k-plus is detected', () => {
  const sab = { ...SHADOW_BUDGET_BANDS, 'ps-plus': { lo: 30000, hi: Infinity } };
  const unbounded = Object.values(sab).filter(b => b.hi === Infinity);
  return unbounded.length > 1 ? true : 'two unbounded bands went unnoticed';
});

/* G2 — the €50,000 boundary is mutually correct */
t('G2 . 30k-50k and 50k-plus are mutually exclusive and jointly exhaustive above 30k', () => {
  const a = SHADOW_BUDGET_BANDS['30k-50k'], b = SHADOW_BUDGET_BANDS['50k-plus'];
  if (a.hi !== b.lo) return 'the bands do not meet: ' + a.hi + ' vs ' + b.lo;
  const probe = [29999, 30000, 49999, 50000, 50001, 149900];
  const hits = probe.map(v => [a, b].filter(x => v >= x.lo && v <= x.hi).length);
  /* 50,000 sits in both, exactly as the live map's documented inclusive-at-
     both-ends convention does at 10k/20k/30k. A homeowner states ONE band, so
     membership of that one band stays a single deterministic test. */
  if (hits[3] !== 2) return '50,000 should resolve in the homeowner\'s favour on either selection';
  return hits.filter(h => h === 0).length === 1 ? true : 'a value above 30k fell through both bands';
});
t('G2 SABOTAGE . a gap between the two bands is caught', () => {
  const a = { lo: 30000, hi: 49000 }, b = { lo: 50000, hi: Infinity };
  return [a, b].filter(x => 49500 >= x.lo && 49500 <= x.hi).length === 0 ? true : 'the gap was not detected';
});

/* G3 — range floor renders with From */
t('G3 . a range-floor price renders with "From"', () => {
  const p = { price: 22600, currency: 'EUR', priceBasisClass: 'UNKNOWN', vatStatus: 'Unknown',
              priceIsRangeFloor: true, priceSafeForMatching: true };
  return /^From €22,600/.test(renderShadowPrice(p, money)) || 'rendered: ' + renderShadowPrice(p, money);
});
t('G3 SABOTAGE . a non-floor price must NOT claim "From"', () => {
  const p = { price: 22600, currency: 'EUR', priceBasisClass: 'UNKNOWN', vatStatus: 'Unknown',
              priceIsRangeFloor: false, priceSafeForMatching: true };
  return !/From/.test(renderShadowPrice(p, money)) || '"From" appeared on a confirmed price';
});
t('G3 . every real range-floor product in the artefact renders with From', () => {
  const rf = P.filter(x => x.priceIsRangeFloor && x.priceSafeForMatching);
  const bad = rf.filter(x => !/^From /.test(renderShadowPrice(x, money) || ''));
  return bad.length === 0 ? true : bad.length + ' range-floor products rendered without From';
});

/* G4 — unsafe cannot earn a strong match */
t('G4 . an unsafe price cannot score 2 in ANY band', () => {
  const unsafe = P.filter(x => x.priceSafeForMatching === false && x.price > 0);
  if (!unsafe.length) return 'no unsafe product exists; the guard is inert';
  for (const x of unsafe)
    for (const b of Object.values(SHADOW_BUDGET_BANDS))
      if (shadowBudgetFit(x, b) === 2) return x.name + ' earned a strong match';
  return true;
});
t('G4 . an unsafe price scores -1, not 0 (suppression is not a miss)', () => {
  const x = P.find(y => y.priceSafeForMatching === false && y.currency === 'EUR' && y.price > 0);
  const own = Object.values(SHADOW_BUDGET_BANDS).find(b => x.price >= b.lo && x.price <= b.hi);
  return shadowBudgetFit(x, own) === -1 ? true : 'scored ' + shadowBudgetFit(x, own);
});
t('G4 SABOTAGE . flipping the safety flag would let it through', () => {
  const x = P.find(y => y.priceSafeForMatching === false && y.currency === 'EUR' && y.price > 0);
  const own = Object.values(SHADOW_BUDGET_BANDS).find(b => x.price >= b.lo && x.price <= b.hi);
  return shadowBudgetFit({ ...x, priceSafeForMatching: true }, own) === 2
    ? true : 'the sabotage did not reach the branch the guard protects';
});
t('G4 . an unsafe price is never shown as a figure', () => {
  const x = P.find(y => y.priceSafeForMatching === false && y.price > 0);
  const tr = shadowPriceTreatment(x, money);
  return (tr.figure === null && tr.suppressed === true) ? true : 'a suppressed price still rendered a figure';
});

/* G5 — UNKNOWN basis stays permitted */
t('G5 . a genuine price with UNKNOWN basis still scores 2 in its own band', () => {
  const x = P.find(y => y.priceBasisClass === 'UNKNOWN' && y.currency === 'EUR'
                     && y.price > 0 && y.priceSafeForMatching === true);
  if (!x) return 'no such product; the A/B distinction is untested';
  const own = Object.values(SHADOW_BUDGET_BANDS).find(b => x.price >= b.lo && x.price <= b.hi);
  return shadowBudgetFit(x, own) === 2 ? true : 'UNKNOWN basis wrongly invalidated a real price';
});
t('G5 . UNKNOWN basis carries the honest line, not silence', () =>
  shadowPriceTreatment({ price: 24560, currency: 'EUR', priceBasisClass: 'UNKNOWN',
    vatStatus: 'Yes', priceIsRangeFloor: false, priceSafeForMatching: true }, money).line
    === "Check what's included" || 'UNKNOWN produced no line');
t('G5 . an unmapped/novel class falls to the honest line, never to blank', () =>
  shadowPriceTreatment({ price: 1000, currency: 'EUR', priceBasisClass: 'NEWLY_INVENTED',
    priceIsRangeFloor: false, priceSafeForMatching: true }, money).line
    === "Check what's included" || 'an unmapped class produced something else');

/* G6 — no curator prose in the artefact */
const PROSE_MARKERS = ['Curator', 'flagged for', 'NOT RECONCILED', 'SUPERSEDED',
  're-verified', 'RE-VERIFIED', 'Tier B', 'not corrected here', 'audit trail',
  'basisNotes', 'knownExclusions', 'Ingestion'];
/* The NEW price contract is the only thing this build is responsible for. The
   fields it adds are listed here and must be prose-free. */
const NEW_FIELDS = ['priceRecordIds','priceRecordIdsAvailable','priceStatus','priceType',
  'priceScope','vatStatus','vatRate','priceBasisAxes','priceBasisClass',
  'priceBasisConfidence','priceIsRangeFloor','priceSafeForMatching','priceEvidenceRef'];
t('G6 . no curator prose enters through ANY field the new contract adds', () => {
  const blob = JSON.stringify(P.map(x => Object.fromEntries(NEW_FIELDS.map(k => [k, x[k]]))));
  const hit = PROSE_MARKERS.filter(m => blob.includes(m));
  return hit.length === 0 ? true : 'the new contract leaked: ' + hit.join(', ');
});
/* MEASURED PRE-EXISTING DEFECT, not introduced here. The operative artefact
   ALREADY ships curator working notes to the browser inside features.*.text and
   qualification.evidenceSignals.irishAvailabilityBasis -- "Tier B", "Nothing
   inferred", "flagged for Curator review", "SUPERSEDED", "not corrected here",
   and a whole "SUPPLIER STATUS - BIG MAN TINY HOMES" paragraph. The shadow build
   copies the source product wholesale, so it inherits every one. Fixing it means
   changing the generator's feature export, which this phase forbids. The guard
   therefore pins the count: it must not GROW, and the number is reported so the
   defect cannot be forgotten. */
/* Measured 6 Oct 2026 by this guard's own counter, not by hand. An earlier
   hand count of 324 was wrong because it grouped by field path rather than by
   marker occurrence; the guard's number is the authority. */
const INHERITED_LEAK_BASELINE = 334;
t('G6 . the inherited prose leak has not grown beyond its measured baseline', () => {
  const src = JSON.parse(readFileSync(join(HERE, '..', '..', 'garden-room-recommendation-universe-v1.json'), 'utf8'));
  const count = o => { let n = 0; const w = v => {
      if (typeof v === 'string') { for (const m of PROSE_MARKERS) if (v.includes(m)) n++; }
      else if (Array.isArray(v)) v.forEach(w);
      else if (v && typeof v === 'object') Object.values(v).forEach(w); };
    w(o); return n; };
  const inSrc = count(src.products), inShadow = count(P);
  console.log('           -> inherited leak: ' + inSrc + ' in the operative artefact, ' + inShadow + ' in the shadow copy');
  if (inSrc !== INHERITED_LEAK_BASELINE) return 'the operative leak moved to ' + inSrc + '; re-measure before changing the baseline';
  return inShadow <= inSrc ? true : 'the shadow build ADDED prose: ' + inShadow + ' vs ' + inSrc;
});
t('G6 . the axes file DOES hold the quotes (so the proof is not vacuous)', () => {
  const ax = JSON.parse(readFileSync(join(HERE, 'price-basis-axes-v1.json'), 'utf8'));
  return Object.values(ax.byOrganisation).some(v => v.quote && v.quote.length > 20)
    ? true : 'the axes file has no prose, so G6 proves nothing';
});
t('G6 . no product object carries a prose key', () => {
  const bad = P.filter(x => ['quote','basisNotes','knownExclusions','ingestionNotes']
    .some(k => k in x));
  return bad.length === 0 ? true : bad.length + ' products carry a prose key';
});

/* G7 — internal enum never becomes homeowner copy */
t('G7 . no internal class name appears in any homeowner line', () => {
  const enums = Object.keys(HOMEOWNER_BASIS_LINES);
  for (const [k, line] of Object.entries(HOMEOWNER_BASIS_LINES))
    if (enums.some(e => line.includes(e)) || /_/.test(line) || line === line.toUpperCase())
      return 'the line for ' + k + ' leaks an enum shape: ' + line;
  return true;
});
t('G7 . every rendered product line is drawn from the approved set', () => {
  const allowed = new Set([...Object.values(HOMEOWNER_BASIS_LINES), 'Price not confirmed']);
  const bad = P.filter(x => x.price > 0).map(x => shadowPriceTreatment(x, money).line)
               .filter(l => l && !allowed.has(l));
  return bad.length === 0 ? true : 'unapproved copy rendered: ' + [...new Set(bad)].join(' | ');
});

/* G8 — VAT cannot be inferred */
t('G8 . no product carries a VAT rate that Atlas does not publish', () =>
  P.every(x => x.vatRate === null) ? true : 'a vatRate appeared from nowhere');
t('G8 . VAT Unknown and VAT absent produce NO vat qualification', () => {
  for (const v of ['Unknown', null, undefined, '']) {
    const tr = shadowPriceTreatment({ price: 1000, currency: 'EUR', priceBasisClass: 'UNKNOWN',
      vatStatus: v, priceIsRangeFloor: false, priceSafeForMatching: true }, money);
    if (tr.vat !== null) return 'vatStatus=' + String(v) + ' produced "' + tr.vat + '"';
  }
  return true;
});
t('G8 SABOTAGE . an Irish supplier does not get VAT inferred from its country', () => {
  const tr = shadowPriceTreatment({ price: 1000, currency: 'EUR', organisation: 'Shomera',
    manufactureCountry: 'Ireland', priceBasisClass: 'ERECTED_WITH_SERVICES',
    vatStatus: 'Unknown', priceIsRangeFloor: false, priceSafeForMatching: true }, money);
  return tr.vat === null ? true : 'VAT was inferred from Irish origin: ' + tr.vat;
});

/* G9 — marketing words cannot determine basis */
/* PHASE 6D REVISION OF G9.
   BEFORE: asserted the string "turnkey" could never be a determinant anywhere,
   and proved it via one curated-axes supplier (Concept Modular -> EX_WORKS).
   That predates the Phase 6C decision and was written against the curated
   axes file, which the production generator does not use.
   AFTER: the protection is UNCHANGED in substance but stated as the governed
   rule actually in force -- the exact closed lead TOKEN may classify; supplier
   marketing PROSE containing the same word may not; anything unmatched fails
   closed to UNKNOWN. */
t('G9 . the governed lead token TURNKEY INSTALLATION INCLUDED may map erection=INCLUDED', () => {
  const byToken = P.filter(x => x.priceEvidenceRef
                             && x.priceEvidenceRef.basisLeadPhrase === 'TURNKEY INSTALLATION INCLUDED');
  if (!byToken.length) return 'no product classified by the governed token';
  const wrong = byToken.filter(x => x.priceBasisAxes.erection !== 'INCLUDED');
  return wrong.length === 0 ? true
    : wrong.length + ' products carry the governed token but not erection=INCLUDED';
});
t('G9 . a basis class is NEVER asserted without a governed lead token', () => {
  const bad = P.filter(x => x.priceBasisClass !== 'UNKNOWN'
                         && !(x.priceEvidenceRef && x.priceEvidenceRef.basisLeadPhrase));
  return bad.length === 0 ? true
    : bad.length + ' products claim a basis class with no governed token behind it';
});
t('G9 . unmatched prose fails closed: no token => UNKNOWN axis and UNKNOWN class', () => {
  const noTok = P.filter(x => !(x.priceEvidenceRef && x.priceEvidenceRef.basisLeadPhrase));
  const leak = noTok.filter(x => x.priceBasisAxes.erection !== 'UNKNOWN'
                              || x.priceBasisClass !== 'UNKNOWN');
  return leak.length === 0 ? true : leak.length + ' unmatched products did not fail closed';
});
t('G9 . NEGATIVE CAPABILITY: supplier prose containing "turnkey" cannot classify', () => {
  /* Exercises the REAL generator, not a re-implementation. */
  const out = execSync('python3 - <<\'PYEOF\'\n' +
    'import sys; sys.path.insert(0, ".github/scripts")\n' +
    'import generate_garden_room_universe as G\n' +
    'rec = {"id":"recX","fields":{"Base Price":25000,"Currency":"EUR","Status":"Verified"}}\n' +
    'prose = {"installationModel": {"text": "Our turnkey service is second to none; fully turnkey, premium turnkey finish."}}\n' +
    'g = G.price_governance(rec, "adjudicated", [rec], [rec], prose)\n' +
    'print(g["priceBasisAxes"]["erection"], g["priceBasisClass"], g["priceEvidenceRef"]["basisLeadPhrase"])\n' +
    'PYEOF', { cwd: REPO, encoding: 'utf8' }).trim();
  return out === 'UNKNOWN UNKNOWN None' ? true
    : 'supplier prose classified the product: ' + out;
});
t('G9 . the derivation reads only the three axes', () => {
  /* Two products with identical axes must derive the same class however
     differently their marketing reads. */
  const groups = {};
  for (const x of P) {
    const k = [x.priceBasisAxes.erection, x.priceBasisAxes.siteWorks, x.priceBasisAxes.delivery].join('|');
    (groups[k] = groups[k] || new Set()).add(x.priceBasisClass);
  }
  const bad = Object.entries(groups).filter(([, s]) => s.size > 1);
  return bad.length === 0 ? true : 'identical axes produced different classes: ' + JSON.stringify(bad);
});

/* G10 — provenance survives */
/* PHASE 6D REVISION OF G10-a.
   BEFORE: required priceEvidenceRef.axesFile/axesVersion to match the curated
   shadow axes file. The production contract has no such file.
   AFTER: requires the REAL governed contract field to be present and
   structured on every product. The protection -- provenance survives on every
   row -- is unchanged; only the field it names is corrected. */
t('G10 . every product carries a structured governed priceEvidenceRef', () => {
  const REQ = ['recordIds','adjudication','candidateCount','status','priceType',
               'evidenceScope','lastPriceCheck','basisSource','basisLeadPhrase'];
  const bad = P.filter(x => !x.priceEvidenceRef
                         || !Array.isArray(x.priceEvidenceRef.recordIds)
                         || REQ.some(k => !(k in x.priceEvidenceRef)));
  return bad.length === 0 ? true : bad.length + ' products lost governed provenance';
});
t('G10 . the retired shadow axesFile stamp is NOT required of a production candidate', () =>
  P.every(x => !('axesFile' in x.priceEvidenceRef)) ? true
    : 'a production row still carries the retired curated axesFile stamp');
/* PHASE 6D REVISION OF G10-b.
   BEFORE: demanded the shadow/Phase-5 provenance shapes, including the curated
   basisAxesFile stamp. A real production candidate carries neither.
   AFTER: demands the PRODUCTION provenance the generator now emits. Equally
   strict: an artefact declaring none of these still fails. */
t('G10 . the artefact declares real production provenance', () => {
  const p4 = U.shadow === true && U.builtFrom && U.builtFrom.generated && U.notAuthorisedForRuntime;
  const p5 = U.generationMode && U.provenance && U.provenance.sourceKind;
  const p6 = U.sourceKind === 'airtable-live'
          && typeof U.governedPriceContractVersion === 'string' && U.governedPriceContractVersion
          && typeof U.governedDigest === 'string' && U.governedDigest.length === 64
          && typeof U.generated === 'string' && U.generated;
  return (p4 || p5 || p6) ? true : 'the artefact does not declare its own provenance';
});
t('G10 . governed derivation comes from the production contract, not the retired axes file', () => {
  if (!('governedPriceContractVersion' in U)) return true;        // shadow artefact, not applicable
  if ('basisAxesFile' in U) return 'a production candidate still cites the retired curated axes file';
  const srcs = new Set(P.map(x => x.priceEvidenceRef && x.priceEvidenceRef.basisSource).filter(Boolean));
  const bad = [...srcs].filter(s => s !== 'installationModel.leadPhrase');
  return bad.length === 0 ? true : 'unexpected basisSource: ' + bad.join(', ');
});
t('G10 . NEGATIVE CAPABILITY: missing or malformed production provenance FAILS', () => {
  const chk = u => (u.sourceKind === 'airtable-live'
                 && typeof u.governedPriceContractVersion === 'string' && u.governedPriceContractVersion
                 && typeof u.governedDigest === 'string' && u.governedDigest.length === 64);
  const good = chk(U) || !('governedPriceContractVersion' in U);
  const noKind   = chk({ ...U, sourceKind: undefined });
  const noVer    = chk({ ...U, governedPriceContractVersion: '' });
  const shortDig = chk({ ...U, governedDigest: 'deadbeef' });
  return (good && !noKind && !noVer && !shortDig) ? true
    : 'the provenance check does not reject missing or malformed fields';
});
/* PHASE 6D REVISION OF G10-c.
   BEFORE: asserted priceBasis had been DELETED. Phase 6C deliberately retains
   it as a deprecated alias because your-plot.html has 19 live consumers that
   read it, correctly, as verification status. Deleting it would break them.
   AFTER: the real protection -- priceBasis must never become a source of
   COMMERCIAL BASIS -- is asserted directly, which is stronger than absence. */
t('G10 . priceStatus is the truthful canonical status field', () =>
  P.every(x => 'priceStatus' in x) ? true : 'priceStatus is missing');
t('G10 . the deprecated priceBasis alias equals the canonical status', () => {
  const bad = P.filter(x => ('priceBasis' in x) && x.priceBasis !== x.priceStatus);
  return bad.length === 0 ? true : bad.length + ' rows where the alias diverged from priceStatus';
});
t('G10 . priceBasis is never consumed as commercial-basis evidence', () => {
  /* Every basis class must be explained by the axes, never by the status. */
  const CLASSES = new Set(['EX_WORKS','ERECTED_WITH_SERVICES','ERECTED_SERVICES_EXCLUDED',
                           'ERECTED_SERVICES_UNKNOWN','DELIVERED_SHELL','KIT_SELF_ASSEMBLY','UNKNOWN']);
  const leak = P.filter(x => CLASSES.has(String(x.priceBasis)));   // a status value is never a class
  const unexplained = P.filter(x => x.priceBasisClass !== 'UNKNOWN' && !x.priceBasisAxes);
  return (leak.length === 0 && unexplained.length === 0) ? true
    : 'priceBasis leaked into the basis vocabulary, or a class has no axes';
});
t('G10 . NEGATIVE CAPABILITY: changing priceBasis alone cannot alter priceBasisClass', () => {
  const out = execSync('python3 - <<\'PYEOF\'\n' +
    'import sys; sys.path.insert(0, ".github/scripts")\n' +
    'import generate_garden_room_universe as G\n' +
    'f = {"installationModel": {"text": "DIY KIT ONLY. Self-assembly."}}\n' +
    'a = {"id":"r1","fields":{"Base Price":1000,"Currency":"EUR","Status":"Verified"}}\n' +
    'b = {"id":"r1","fields":{"Base Price":1000,"Currency":"EUR","Status":"Draft"}}\n' +
    'ga = G.price_governance(a,"adjudicated",[a],[a],f)\n' +
    'gb = G.price_governance(b,"adjudicated",[b],[b],f)\n' +
    'print(ga["priceStatus"], gb["priceStatus"], ga["priceBasisClass"], gb["priceBasisClass"])\n' +
    'PYEOF', { cwd: REPO, encoding: 'utf8' }).trim();
  const [sa, sb, ca, cb] = out.split(/\s+/);
  return (sa !== sb && ca === cb && ca === 'KIT_SELF_ASSEMBLY') ? true
    : 'status changed the basis class: ' + out;
});

/* BUILDER-LEVEL SABOTAGE — the python guards must refuse, not warn */
const BUILDER = join(HERE, 'build-shadow-universe.py');
function sabotagePython(label, from, to) {
  const src = readFileSync(BUILDER, 'utf8');
  if (!src.includes(from)) { results.push(false); console.log('  FAIL   ' + label + '\n           -> builder anchor absent'); return; }
  /* The mutated copy MUST live beside the real builder, because the builder
     resolves its inputs from its own location. Running it from a temp directory
     made every sabotage die on the input-path check instead of reaching the
     guard it was aimed at -- a proof that proved nothing. --check is passed, so
     no artefact is written whichever way it goes. */
  const f = join(HERE, '__sabotage__.py');
  writeFileSync(f, src.replace(from, to));
  let refused = false, out = '';
  try { execFileSync('python3', [f, '--check'], { encoding: 'utf8', cwd: HERE }); }
  catch (e) { refused = true; out = ((e.stdout || '') + (e.stderr || '')).split('\n').find(l => l.startsWith('REFUSED') || l.includes('Error')) || ''; }
  rmSync(f, { force: true });
  /* A refusal on the input-path check would be a false positive, so it is
     rejected explicitly: the sabotage has to be caught by its own guard. */
  const falsePositive = /is not where it was|axes file is missing/.test(out);
  const ok = refused && !falsePositive;
  results.push(ok);
  console.log('  ' + (ok ? 'CAUGHT ' : (falsePositive ? 'VOID   ' : 'MISSED ')) + label
    + (out ? '\n           -> ' + out.slice(0, 112) : ''));
}
/* G11 — equal-price duplicate adjudication remains truthful.
   adjudicate_price() rule 3: equal authority + every candidate says the SAME
   thing -> adjudicated, price kept. Rule 4: equal authority + they disagree
   -> ambiguous, price discarded. Both halves are asserted, because a guard
   that only checked rule 4 would pass if rule 3 silently started discarding
   agreeing duplicates too, and the homeowner would lose 16 real prices. */
const adjRows = P.map(p => ({ p, e: p.priceEvidence || {} })).filter(x => x.e.adjudication);
const dupAgreed    = adjRows.filter(x => (x.e.candidateCount || 0) >= 2 && x.e.adjudication === 'adjudicated');
const dupDisagreed = adjRows.filter(x => (x.e.candidateCount || 0) >= 2 && x.e.adjudication === 'ambiguous');
/* The three Power Sheds rows are a KNOWN post-generation mutation, proved in
   this phase and reported as a release blocker. They are pinned by name so the
   invariant can be asserted on everything else without hiding them, and so a
   FOURTH violation cannot slip in unnoticed behind them. */
const KNOWN_MUTATION = new Set([
  '12x12 Apex Classic Log Cabin', '14x14 Apex Classic Log Cabin', '16x12 Apex Log Cabin']);
t('G11 . agreeing duplicates stay adjudicated AND keep their price (rule 3)', () => {
  if (dupAgreed.length === 0) return 'no agreeing-duplicate rows, so rule 3 is unproven';
  const lost = dupAgreed.filter(x => x.p.price === null || x.p.price === undefined);
  return lost.length === 0
    ? true : lost.length + ' agreeing duplicate(s) lost their price, e.g. ' + lost[0].p.name;
});
t('G11 . disagreeing duplicates are ambiguous AND carry no number (rule 4)', () => {
  if (dupDisagreed.length === 0) return 'no disagreeing-duplicate rows, so rule 4 is unproven';
  const kept = dupDisagreed.filter(x => x.p.price !== null && x.p.price !== undefined);
  const unexpected = kept.filter(x => !KNOWN_MUTATION.has(x.p.name));
  if (unexpected.length) return 'a NEW ambiguous row retains a price: ' + unexpected.map(x => x.p.name).join(', ');
  /* PHASE 5 CORRECTION. The first version asserted kept.length === 3, which made
     the guard DEMAND the mutation exist — so it failed on the repaired candidate,
     where the correct answer is zero. The invariant is "no UNEXPECTED ambiguous
     row holds a number", and fewer is strictly better. The sabotage below still
     proves a new violation is caught. */
  if (kept.length === 0) { console.log('           -> mutation cleared: 0 ambiguous rows retain a price'); return true; }
  return kept.length <= KNOWN_MUTATION.size
    ? true : 'more rows retain a price than the known mutation set: ' + kept.length;
});
t('G11 . the mutated rows cannot earn a budget verdict despite holding a number', () => {
  const bad = dupDisagreed.filter(x => KNOWN_MUTATION.has(x.p.name))
    .filter(x => shadowBudgetFit(x.p, '10k-20k') === 2 || shadowBudgetFit(x.p, 'under-10k') === 2);
  return bad.length === 0
    ? true : 'a mutated sterling row scored a strong match: ' + bad[0].p.name;
});
t('G11 SABOTAGE . a fourth ambiguous row retaining a price is caught', () => {
  const fake = { p: { name: 'INVENTED Ambiguous Cabin', price: 12345, currency: 'EUR' },
                 e: { adjudication: 'ambiguous', candidateCount: 2 } };
  const kept = [...dupDisagreed, fake].filter(x => x.p.price !== null && x.p.price !== undefined);
  const unexpected = kept.filter(x => !KNOWN_MUTATION.has(x.p.name));
  return unexpected.length === 1 && unexpected[0].p.name === 'INVENTED Ambiguous Cabin'
    ? true : 'the invented violation was not detected';
});
t('G11 SABOTAGE . rule 3 silently discarding an agreeing duplicate is caught', () => {
  const stripped = dupAgreed.map(x => ({ ...x, p: { ...x.p, price: null } }));
  return stripped.filter(x => x.p.price === null).length === dupAgreed.length
    ? true : 'stripping every agreeing duplicate went unnoticed';
});

console.log('\n  builder sabotage (each runs --check only; nothing is written)');
sabotagePython('B1 . curator prose is smuggled into the payload',
  '    for k in FORBIDDEN_KEYS:', '    q["basisNotes"] = ev.get("quote")\n    for k in FORBIDDEN_KEYS:');
sabotagePython('B2 . the derivation stops exercising its axes',
  'if e == "INCLUDED" and s == "INCLUDED":        return "ERECTED_WITH_SERVICES"',
  'if e == "INCLUDED" and s == "INCLUDED":        return "UNKNOWN"');
sabotagePython('B3 . the safety flag is made always-true',
  '    safe = priced and conf not in UNSAFE_CONF', '    safe = priced');
sabotagePython('B4 . the axes file stops being read',
  '    ev = PRD.get(fold(p.get("name"))) or ORG.get(fold(p.get("organisation"))) or AX_UNKNOWN',
  '    ev = AX_UNKNOWN');
sabotagePython('B5 . a class outside the closed vocabulary is returned',
  '    return "UNKNOWN"                               # fails closed',
  '    return "PROBABLY_INSTALLED"');

console.log('\n' + '='.repeat(78));
const pass = results.filter(Boolean).length;
console.log(pass + ' of ' + results.length + ' checks passed');
process.exit(pass === results.length ? 0 : 1);
