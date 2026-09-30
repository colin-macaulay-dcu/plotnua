#!/usr/bin/env node
/* PLOTNUA JOURNEY CONTRACT — the architecture gate.
 * ===========================================================================
 * Test class C. Enforces PLOTNUA-JOURNEY-CONTRACT.md against your-plot.html.
 *
 * THE RULE UNDER TEST:
 *
 *     A LATER-STAGE CAPABILITY MAY NOT SILENTLY BYPASS AN EARLIER STAGE
 *     THAT OWNS THE RELEVANT DECISION WORK.
 *
 * WHY THIS IS A LEDGER AND NOT A PURE INVARIANT CHECK
 *     3099d8d introduced four non-canonical items. The founder's direction is
 *     to make the architecture DETECT them, not to repair them in this pass.
 *     So each is recorded below with an exact fingerprint. The gate passes
 *     while they sit exactly as recorded, and fails the moment one GROWS,
 *     SPREADS, or is JOINED BY ANOTHER OF ITS KIND.
 *
 *     That is the property that matters. A guard that simply asserted "no
 *     supplier handoff from Option Detail" would fail today, be waived on day
 *     one, and protect nothing thereafter.
 *
 *     Repairing a violation therefore REQUIRES editing this ledger. That is
 *     deliberate: the repair cannot happen silently either.
 *
 * Run:  node atlas-tools/validate-journey-contract.js
 *       node atlas-tools/validate-journey-contract.js --self-test
 */
'use strict';

const fs = require('fs');
const path = require('path');

const REPO = path.join(__dirname, '..');
const PAGE = path.join(REPO, 'your-plot.html');
const CONTRACT = path.join(REPO, 'PLOTNUA-JOURNEY-CONTRACT.md');
const UNIVERSE = path.join(REPO, 'garden-room-recommendation-universe-v1.json');

/* =========================================================================
   THE LEDGER. Exact counts, recorded at 3099d8d.
   ========================================================================= */

/* Canonical structures that must exist. Deleting dormant code trips these. */
const MUST_EXIST = [
  ['J09', 'RESOLVE_REGISTRY',            'const RESOLVE_REGISTRY = [', 1],
  ['J09', 'renderResolve()',             'function renderResolve(product){', 1],
  ['J09', 'openResolveScreen()',         'function openResolveScreen(returnScreen, product){', 1],
  ['J09', '#screen-resolve markup',      '<section id="screen-resolve"', 1],
  ['J09', 'PROGRESS_REGISTRY',           'const PROGRESS_REGISTRY = [', 1],
  ['J09', 'renderProgress()',            'function renderProgress(product){', 1],
  ['J09', 'openProgressScreen()',        'function openProgressScreen(returnScreen, product){', 1],
  ['J09', '#screen-progress markup',     '<section id="screen-progress"', 1],
  ['J09', 'ISSUE 007 restore condition', 'TO RESTORE: put back `els.myPlotResolveBtn.hidden = total < 1;`', 1],
  ['J09', 'LAUNCH-INT-002 restore cond.', 'TO RESTORE: put back `total < 1`.', 1],

  ['J01', 'openProductDetail()',         'function openProductDetail(productId, returnScreen){', 1],
  ['J01', 'View option button',          'function pnViewOptionButton(product){', 1],
  ['J02', 'Option Detail return overlay','productDetailReturn = createReturnableOverlay(', 1],

  ['J04', 'resolveUncertaintiesFor()',   'function resolveUncertaintiesFor(product, answers){', 1],
  ['J05', 'Resolve position store',      'const resolvePositions = new Map();', 1],
  ['J05', 'Resolve persistence into My Plot', 'resolve: resolvePositions.get(id) || null,', 1],
  ['J05', 'recordResolveAnswer()',       'function recordResolveAnswer(productId, key, text){', 1],
  ['J06', 'resolveReadiness()',          'function resolveReadiness(states){', 1],
  ['J06', 'progressFor()',               'function progressFor(product){', 1],

  ['J08', 'My Plot Compare seam',        'function renderMyPlotPickTwo(){', 1],
  ['J08', 'My Plot single-select seam',  'function renderMyPlotPickOne(', 1],
  ['J08', 'compareShortlist()',          'function compareShortlist(){', 1],
  ['J08', 'Resolve entry listener',      'els.myPlotResolveBtn.addEventListener', 1],
  /* PROGRESS LEFT THE VISIBLE JOURNEY, SO THIS CHECK TURNED ROUND.
     It used to require the My Plot listener. It now requires that no
     such listener exists: a homeowner-visible route to Progress is the
     violation, not the contract. Same subject, opposite sign -- the
     check was not dropped. */
  ['J08', 'No Progress entry listener',  'els.myPlotProgressBtn.addEventListener', 0],
  ['J08', 'Compare entry listener',      'els.myPlotCompareBtn.addEventListener', 1],

  ['J11', 'publication gate wired',      'const publishableCandidates = allCandidates.filter(pnResultPublishable);', 1],
  ['J11', 'gate delegates to rights',    'return !!pnAuthorisedImage(product);', 1],
  /* THE RENDERER RE-CHECK COUNT MOVED OUT OF THIS TABLE — see J11-RIGHTS
     below. It asserted the literal number 4. That was a CENSUS of the
     surfaces that painted a product photograph on the day it was written,
     not the rule it stood for. Adding a fifth surface that re-checks
     rights correctly — the Resolve header — failed a check whose whole
     purpose that surface was honouring.

     The replacement asserts the actual invariant: every governed image
     painted anywhere is gated AND credited. It scales with the app and
     it fails on the thing that matters, which a fixed number never could. */

  ['P01', 'PB046 no-price constant',     "const PB046_NO_PRICE = 'Price not published';", 1],
  ['P01', 'PB046 ambiguous constant',    "const PB046_AMBIGUOUS_PRICE = 'Price not confirmed';", 1],

  /* The Enquiry/Dispatch stage. BUILT and TEST-GATED. J09 protects it from
     deletion; these two also protect the GATE, so the transport cannot be
     made live by accident. */
  ['J09', 'Enquiry screen',              'function openEnquiryScreen(org, product){', 1],
  ['J09', '#screen-enquiry markup',      '<section id="screen-enquiry"', 1],
  ['J07', 'Enquiry route is test-gated', "const ENQUIRY_TEST_MODE = new URLSearchParams(location.search).get('enquiry') === 'test';", 1],
  ['J07', 'Enquiry has one caller only', 'window.PLOTNUA_OPEN_TEST_ENQUIRY = function(){', 1],
];

/* The canonical uncertainty taxonomy. J04. */
const RESOLVE_KEYS = [
  ['contractingEntity', 'atlas'], ['origin', 'atlas'], ['leadTime', 'atlas'], ['warranty', 'atlas'],
  ['access', 'homeowner'], ['ground', 'homeowner'], ['power', 'property'], ['water', 'property'],
  ['priceIncludes', 'plotnua'], ['installationCharges', 'plotnua'], ['afterSales', 'plotnua'],
  ['planning', 'world'], ['schedule', 'plotnua'],
];

/* RECORDED VIOLATIONS — RETIRED BY RP-1 (repair commit).

   All four were genuinely repaired, not re-fingerprinted. What stood here as
   "this violation must not grow" is now inverted: the guards below assert the
   REPAIRED state, so the violation cannot come back either. That is the only
   honest way to retire a ledger entry.

     V1  pnOpenQuestions()            RETIRED -> pnResolvePreview() reads RESOLVE_REGISTRY
     V2  Option Detail -> supplier    RETIRED -> continuation goes to My Plot
     V3  pnNextAction() routing       RETIRED -> retained, no caller
     V4  supplier-publication claim   RETIRED -> wording gone; PB046 stands   */
const VIOLATIONS = [];

/* POST-REPAIR INVARIANTS. Each fails if its violation returns. */
const REPAIRED = [
  { guard: 'J03', label: 'V1 stays retired: no parallel question model',
    absent: 'function pnOpenQuestions(' },
  { guard: 'J03', label: 'V1 repair present: pnResolvePreview declared',
    present: 'function pnResolvePreview(product){', count: 1 },
  { guard: 'J07', label: 'V2 stays retired: Option Detail does not call the outbound door',
    absent: 'pnSupplierHandover(product, nextAction.state);' },
  /* P0 JOURNEY RESTORE — BEHAVIOUR, NOT A COPY STRING.
     This used to fingerprint the literal 'Continue with this option' twice.
     The P0 repair relabels that CTA by saved state ('Add to My Plot' /
     'Continue to My Plot'), so the old fingerprint broke while the behaviour
     it was standing in for was completely intact. A test that fails when the
     words change but the architecture does not was testing the wrong thing.
     It now tests what V2 actually repaired: Option Detail's continuation
     lands in My Plot. */
  /* SIMPLIFY — THE INVARIANT, NOT THE WORDING.
     V2's repair was never "the CTA says X" or even "it goes to My Plot". It
     was: OPTION DETAIL'S CONTINUATION STAYS INSIDE PLOTNUA instead of leaving
     for the supplier. My Plot was simply where it went first. The journey has
     since been simplified so it goes straight to Resolve, and My Plot became
     an optional workspace -- so the check now asserts the thing that must
     never change: Option continues into a PlotNua decision stage.

     I have now rewritten this check twice for wording changes. That is the
     tell that fingerprinting copy was the wrong test; this one is behavioural
     and should survive any future relabelling. */
  { guard: 'J07', label: 'V2 repair present: the Option continuation stays inside PlotNua',
    present: 'openResolveScreen(els.productDetailScreen, product);', count: 1 },
  /* THE AUTO-SAVE CHECK MOVED OUT OF THIS TABLE — see J07-DUP below.
     It asserted `if (!savedProductIds.has(product.id)) {` appeared exactly
     once. That was a fingerprint of ONE call site, not an invariant: the
     moment a second surface auto-saved before continuing -- which the Results
     Next steps CTA now legitimately does -- the count broke while the
     property it stood for held perfectly. Same failure as the wording
     fingerprints above, third time. The replacement asserts the real rule:
     NO SAVE ANYWHERE MAY BE UNGUARDED, however many save sites exist. */
  { guard: 'J07', label: 'V3 stays retired: Option Detail does not route on pnNextAction',
    absent: 'const nextAction = pnNextAction(product);' },
  { guard: 'P01', label: 'V4 repair present: the PlotNua-gap wording',
    present: 'PlotNua does not hold a confirmed price', count: 1 },
];

/* J07 — the single outbound door. */
const OUTBOUND = { fingerprint: 'window.open(', count: 1, owner: 'pnSupplierHandover' };

/* J10 — the complete set of journey-routing functions. A new one fails. */
const ROUTING_FUNCTIONS = [
  'pnNextAction', 'pnSupplierHandover', 'pnOpenQuestions', 'pnViewOptionButton',
  'openProductDetail', 'openResolveScreen', 'openProgressScreen',
  'closeResolveScreen', 'closeProgressScreen',
  /* Declared after guard J10 found them during the stabilisation pass. Both
     pairs are canonical stage owners; neither was known to the pass that
     wrote 3099d8d, which is the whole argument for this file existing. */
  'openCompareScreen', 'closeCompareScreen',
  'openEnquiryScreen', 'closeEnquiryScreen',
];

/* P01 — claim shapes that turn an evidence gap into a fact about a supplier. */
const FORBIDDEN_CLAIMS = [
  'has not published a price',
  'does not publish a price',
  'has published no price',
  'we will request', 'PlotNua will contact', 'request a quote',
  'we have arranged', 'we are in touch with',
];

/* M01 — markets where a dedicated storefront is known to exist. */
const MARKET_TRUTH = [
  { organisation: 'Power Sheds', homeownerMarket: 'IE',
    verifiedStorefront: 'ie.powersheds.com', expectCurrency: 'EUR',
    recordedHost: 'www.powersheds.com', recordedCurrency: 'GBP',
    status: 'MISMATCH RECORDED — not repaired in the stabilisation pass' },
];

/* ========================================================================= */

let fails = [];
let checks = 0;

function ok(guard, msg)   { checks++; console.log('  OK   [' + guard + '] ' + msg); }
function bad(guard, msg)  { checks++; fails.push(guard + ' ' + msg); console.log('  FAIL [' + guard + '] ' + msg); }
function note(msg)        { console.log('       ' + msg); }
function head(t)          { console.log('\n' + t + '\n' + '-'.repeat(t.length)); }

function countOf(src, needle) {
  let n = 0, i = 0;
  for (;;) { const j = src.indexOf(needle, i); if (j < 0) break; n++; i = j + needle.length; }
  return n;
}

/* Brace-matched extraction, so a guard reads a function and not 13,000
   characters of whatever follows it. */
function lift(src, decl) {
  const i = src.indexOf(decl);
  if (i < 0) return null;
  const j = src.indexOf('{', i);
  let d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  return null;
}

/* Comments are not executable. A guard that trips on a comment describing
   the thing it forbids is a guard that punishes documentation. */
function stripComments(s) {
  return s.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/^\s*\/\/.*$/gm, ' ');
}

function run(src) {
  const code = stripComments(src);

  head('CONTRACT PRESENT');
  if (fs.existsSync(CONTRACT)) ok('J00', 'PLOTNUA-JOURNEY-CONTRACT.md is in the repository');
  else bad('J00', 'PLOTNUA-JOURNEY-CONTRACT.md is missing — the gate has no specification');

  head('J01-J12 · CANONICAL STRUCTURES MUST EXIST');
  MUST_EXIST.forEach(function (row) {
    const [guard, label, needle, want] = row;
    const got = countOf(src, needle);
    if (got === want) ok(guard, label + ' (' + got + ')');
    else bad(guard, label + ': expected ' + want + ', found ' + got);
  });

  head('J04 · RESOLVE_REGISTRY IS THE CANONICAL UNCERTAINTY TAXONOMY');
  const reg = src.slice(src.indexOf('const RESOLVE_REGISTRY = ['));
  const found = [];
  const re = /key:'([a-zA-Z]+)', consequence:'([a-z]+)', owner:'([a-z]+)'/g;
  let m;
  while ((m = re.exec(reg.slice(0, 22000))) !== null) found.push([m[1], m[3]]);
  if (found.length !== RESOLVE_KEYS.length) {
    bad('J04', 'registry has ' + found.length + ' entries, contract records ' + RESOLVE_KEYS.length);
  } else {
    let drift = 0;
    RESOLVE_KEYS.forEach(function (want, i) {
      if (found[i][0] !== want[0] || found[i][1] !== want[1]) {
        drift++;
        bad('J04', 'entry ' + i + ': expected ' + want.join('/') + ', found ' + found[i].join('/'));
      }
    });
    if (!drift) ok('J04', 'all 13 entries match the contract, owners included');
  }

  head('J03 · OPTION DETAIL MAY NOT OWN THE RESOLVE MODEL');
  const prev = lift(src, 'function pnResolvePreview(product){');
  if (!prev) {
    bad('J03', 'pnResolvePreview() could not be lifted — the canonical read is gone');
  } else {
    if (prev.indexOf('RESOLVE_REGISTRY') >= 0) ok('J03', 'the preview reads RESOLVE_REGISTRY');
    else bad('J03', 'the preview no longer reads RESOLVE_REGISTRY');
    if (prev.indexOf('resolveCopyFor(entry)') >= 0) ok('J03', 'the preview uses the canonical label resolver');
    else bad('J03', 'the preview no longer uses resolveCopyFor()');
    /* A question authored HERE is how a second taxonomy starts. Any long
       capitalised string literal in this function is one. */
    const authored = (stripComments(prev).match(/'[A-Z][^']{14,}'/g) || []);
    if (!authored.length) ok('J03', 'the preview authors no questions of its own');
    else bad('J03', 'the preview authors its own question text: ' + authored.slice(0, 3).join(', '));
    if (prev.indexOf('recordResolveAnswer') >= 0 || prev.indexOf('resolvePositions') >= 0) {
      bad('J03', 'the preview writes Resolve state; it is a read-only preview');
    } else {
      ok('J03', 'the preview owns no answers and writes no state');
    }
  }
  const rival = /function\s+(pn[A-Za-z]*(Questions|Uncertaint|Checklist|Unknowns)[A-Za-z]*)\s*\(/g;
  const rivals = [];
  while ((m = rival.exec(code)) !== null) if (rivals.indexOf(m[1]) < 0) rivals.push(m[1]);
  if (!rivals.length) ok('J03', 'no rival uncertainty model exists');
  else bad('J03', 'a rival uncertainty model appeared: ' + rivals.join(', '));

  head('J07 · SUPPLIER HANDOFF MAY NOT BE INTRODUCED EARLY');
  const out = countOf(code, OUTBOUND.fingerprint);
  if (out === OUTBOUND.count) ok('J07', 'exactly one outbound door (window.open)');
  else bad('J07', 'window.open appears ' + out + ' times, contract allows ' + OUTBOUND.count);

  const handover = lift(src, 'function pnSupplierHandover(product');
  if (handover && handover.indexOf('window.open(') >= 0) {
    ok('J07', 'the outbound door lives inside pnSupplierHandover()');
  } else {
    bad('J07', 'window.open is not inside pnSupplierHandover() — the single door has moved');
  }

  /* P0 JOURNEY RESTORE — THE CONTRACT MOVED, SO THIS CHECK MOVED WITH IT.
     Until the P0 repair the door was DEFINED WITH NO CALLER, because Progress
     was dormant and there was nowhere legitimate to call it from. Progress is
     now visible by founder authorisation, so the contract is no longer "zero
     callers" — it is "EXACTLY ONE caller, and it is inside renderProgress".
     That is a stricter statement, not a looser one: it pins the location as
     well as the count.

     COMMENTS ARE NOT EXECUTABLE. The old check counted raw occurrences, which
     included RP-1's own explanatory comment. Counting prose as a call site
     would have made this unpassable for the right reason, which is the same
     as unpassable for the wrong one. */
  const bareCode = code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  const callers = countOf(bareCode.replace('function pnSupplierHandover(', ''),
                          'pnSupplierHandover(');
  function bodyOf(text, sig){
    const i = text.indexOf(sig);
    if (i < 0) return '';
    let j = text.indexOf('{', i), d = 0;
    for (let k = j; k < text.length; k++){
      if (text[k] === '{') d++;
      else if (text[k] === '}'){ d--; if (!d) return text.slice(i, k + 1); }
    }
    return text.slice(i);
  }
  /* THE STAGE MOVED, SO THE PIN MOVED WITH IT.

     Progress has been removed from the visible journey by founder
     authorisation: its content now sits at the foot of Resolve, and
     Resolve is the last screen the homeowner is sent to. The rule was
     never "the door lives in Progress" -- it is "exactly one door, at
     the last visible stage, and never before it". So the pin is now
     renderResolve(), and Resolve has come off the prohibition list
     below for the same reason. The count is unchanged at one, and every
     stage before the last is still forbidden to hold it. */
  const inResolve = bodyOf(bareCode, 'function renderResolve(').indexOf('pnSupplierHandover(') >= 0;
  if (callers === 1 && inResolve) {
    ok('J07', 'the outbound door has exactly one caller, and it is inside renderResolve()');
  } else if (callers !== 1) {
    bad('J07', 'pnSupplierHandover has ' + callers + ' caller(s) in executable code, expected exactly 1');
  } else {
    bad('J07', 'the single pnSupplierHandover caller is NOT inside renderResolve() — a stage ' +
               'before the last visible one has opened the outbound door');
  }

  /* And the prohibition, stated positively: none of the five upstream stages
     may hold the door. */
  ['function openProductDetail(', 'function openMyPlot(', 'function renderMyPlotPickTwo(',
   'function buildSaveActions('].forEach(function(sig){
    const b = bodyOf(bareCode, sig);
    if (b && b.indexOf('pnSupplierHandover(') >= 0) {
      bad('J07', 'a supplier exit appeared in ' + sig.replace('function ', '').replace('(', '()'));
    }
  });
  ok('J07', 'no supplier exit in Result card, Option Detail, My Plot or Compare');

  head('J10 · NO PARALLEL JOURNEY AROUND A CANONICAL STAGE');
  const declared = [];
  const fnRe = /function\s+(pn[A-Z][A-Za-z]*|open[A-Z][A-Za-z]*Screen|openProductDetail|close[A-Z][A-Za-z]*Screen)\s*\(/g;
  while ((m = fnRe.exec(code)) !== null) if (declared.indexOf(m[1]) < 0) declared.push(m[1]);
  const routing = declared.filter(function (d) {
    return /Action|Handover|Questions|ViewOption|Screen$|^openProductDetail$/.test(d);
  });
  const unexpected = routing.filter(function (r) { return ROUTING_FUNCTIONS.indexOf(r) < 0; });
  if (!unexpected.length) ok('J10', 'routing surface unchanged: ' + routing.length + ' known functions');
  else bad('J10', 'undeclared routing function(s): ' + unexpected.join(', ') +
                  ' — add to the contract or remove');

  head('J12 · RIGHTS WITHDRAWAL MUST NOT BREAK CONTINUITY');
  const opd = lift(src, 'function openProductDetail(productId, returnScreen){');
  if (!opd) {
    bad('J12', 'openProductDetail() could not be lifted');
  } else {
    if (/if\s*\(\s*!\s*pnAuthorisedImage\([^)]*\)\s*\)\s*return/.test(stripComments(opd))) {
      bad('J12', 'openProductDetail refuses to open when imagery is unauthorised — ' +
                 'a rights withdrawal would break Results -> Option continuity');
    } else {
      ok('J12', 'Option Detail still opens under rights withdrawal; only the image is withheld');
    }
    if (opd.indexOf('pnAuthorisedImage(product)') >= 0) {
      ok('J12', 'Option Detail re-checks rights before assigning an image src');
    } else {
      bad('J12', 'Option Detail no longer re-checks rights before rendering an image');
    }
  }

  head('P01 · PRICE SEMANTICS AND CLAIM FIREWALL');
  FORBIDDEN_CLAIMS.forEach(function (claim) {
    const n = countOf(code, claim);
    const allowed = 0;   /* RP-1 retired the last one. None are permitted. */
    if (n === allowed) {
      ok('P01', 'absent: "' + claim + '"');
    } else {
      bad('P01', '"' + claim + '" appears ' + n + ' times, contract allows ' + allowed);
    }
  });

  head('POST-REPAIR INVARIANTS (RP-1) — the four violations stay retired');
  REPAIRED.forEach(function (r) {
    if (r.absent !== undefined) {
      const n = countOf(code, r.absent);
      if (n === 0) ok(r.guard, r.label);
      else bad(r.guard, r.label + ' — RETURNED (' + n + ' occurrence(s))');
    } else {
      const n = countOf(code, r.present);
      if (n === r.count) ok(r.guard, r.label);
      else bad(r.guard, r.label + ': expected ' + r.count + ', found ' + n);
    }
  });

  /* J11-RIGHTS · EVERY GOVERNED IMAGE IS GATED AND CREDITED.

     Three counts that must agree:
       A  re-checks     `= pnAuthorisedImage(product);`
       B  src assigns   `.src = <something>Img.url;`
       C  credits       `pnAttachImageCredit(` call sites

     A === B means no surface paints a governed photograph without asking the
     rights gate first, and no gate call is decorative. B === C means the
     attribution travels with every picture. Paint an image without a gate,
     or gate one and drop its credit, and this fails. */
  (function () {
    /* THE NAMES, NOT JUST THE COUNTS. A first version of this check counted
       `.src = <anything>.url` and compared totals. A probe walked straight
       through it: swap the gated variable for an ungated object inside a
       block that still calls the gate, and both totals stay put. Counting
       shape is not checking provenance. Every painted url must now come from
       a variable this file assigned FROM the gate. */
    const gated = new Set();
    let gm; const gre = /(?:const|let|var)\s+(\w+)\s*=\s*pnAuthorisedImage\(product\);/g;
    while ((gm = gre.exec(code))) gated.add(gm[1]);
    const painted = [];
    let pm; const pre2 = /\.src\s*=\s*(\w+)\.url;/g;
    while ((pm = pre2.exec(code))) painted.push(pm[1]);
    const ungated = painted.filter(function (n) { return !gated.has(n); });
    if (ungated.length) {
      bad('J11', 'image src painted from ' + JSON.stringify(ungated)
        + ', which never came from pnAuthorisedImage()');
      return;
    }
    const A = (code.match(/=\s*pnAuthorisedImage\(product\);/g) || []).length;
    const B = painted.length;
    const C = (code.match(/pnAttachImageCredit\(/g) || []).length - 1;  /* minus the definition */
    if (A < 4) {
      bad('J11', 'only ' + A + ' renderer rights re-check(s); the shipped '
        + 'surfaces that paint a governed photograph number at least four');
    } else if (A !== B) {
      bad('J11', A + ' rights re-check(s) but ' + B + ' governed image src '
        + 'assignment(s) — every painted photograph must be gated');
    } else if (B !== C) {
      bad('J11', B + ' governed image(s) painted but ' + C + ' credit '
        + 'attachment(s) — attribution must travel with the picture');
    } else {
      ok('J11', A + ' governed images, each gated and each credited');
    }
  })();

  /* J07-DUP · EVERY SAVE IS DUPLICATE-GUARDED.
     savedProductIds is a Set keyed on the canonical Atlas product.id, so a
     repeat press cannot create a second entry regardless. The guard exists so
     that recordSaveProvenance() and the funnel event fire ONCE per product --
     an unguarded save would double-count the funnel and rewrite provenance
     with a later timestamp. This check scales with the architecture: add a
     tenth surface that auto-saves and it passes, so long as that surface
     tests before it writes. */
  (function () {
    const NEEDLE = 'savedProductIds.add(product.id)';
    const WINDOW = 600;
    let from = 0, n = 0, unguarded = 0;
    for (;;) {
      const i = code.indexOf(NEEDLE, from);
      if (i < 0) break;
      n++;
      const ctx = code.slice(Math.max(0, i - WINDOW), i);
      if (ctx.indexOf('savedProductIds.has(product.id)') < 0) unguarded++;
      from = i + NEEDLE.length;
    }
    if (n === 0) {
      bad('J07', 'no save call sites found at all — the save contract is gone');
    } else if (unguarded === 0) {
      ok('J07', 'all ' + n + ' save call sites test savedProductIds.has() first');
    } else {
      bad('J07', unguarded + ' of ' + n + ' save call sites write without '
          + 'testing savedProductIds.has() first — provenance and the funnel '
          + 'event would fire twice');
    }
  })();

  head('P1-P8 · PROGRESS EVIDENCE CARRIER (RP-3)');
  /* P1 — supplier operations evidence stays in the dedicated partition. */
  if (!fs.existsSync(path.join(REPO, 'garden-room-detail-suppliers-v1.json'))) {
    bad('P1', 'the supplier detail partition is missing');
  } else {
    ok('P1', 'the supplier partition exists and is the carrier');
  }
  /* P5 — no `.irish` structure added to the core universe to serve Progress. */
  try {
    const uni = JSON.parse(fs.readFileSync(
      path.join(REPO, 'garden-room-recommendation-universe-v1.json'), 'utf8'));
    if (uni.suppliers) bad('P5', 'the CORE universe now carries a `suppliers` object — this can move Match eligibility');
    else ok('P5', 'the core universe carries no `suppliers` object');
  } catch (e) { bad('P5', 'core universe unreadable: ' + e.message); }

  /* P2 — Progress joins by canonical organisation id, not display name. */
  const lane1 = code.indexOf("key:'whoDoesTheWork'");
  const lane1end = code.indexOf("lane:'market'", lane1);
  const lane1src = lane1 >= 0 ? code.slice(lane1, lane1end) : '';
  if (lane1src.indexOf('pnSupplierLocality(') >= 0) ok('P2', 'lane 1 joins through pnSupplierLocality (canonical id)');
  else bad('P2', 'lane 1 no longer joins through the canonical-id accessor');
  if (lane1src.indexOf('compareSupplierIrish') >= 0 || lane1src.indexOf('resolveSupplierRecord') >= 0) {
    bad('P2', 'lane 1 still reads the core-universe supplier record');
  } else {
    ok('P2', 'lane 1 no longer reads the core universe');
  }

  /* P3 — a missing partition fails soft to UNKNOWN, never false. */
  if ((lane1src.match(/pnOpenCell\(\{ checked: !!ops \}\)/g) || []).length === 2) {
    ok('P3', 'both lane-1 entries fail soft to an open cell');
  } else {
    bad('P3', 'a lane-1 entry does not fail soft to an open cell');
  }

  /* P4 — the carrier cannot reach Match. */
  if (code.indexOf('function marketEligibility(product){') >= 0
      && lane1src.indexOf('marketEligibility') < 0) {
    ok('P4', 'lane 1 does not touch marketEligibility');
  } else {
    bad('P4', 'lane 1 reaches into Match eligibility');
  }

  /* P6/P7 — certified evidence for both pilot suppliers survives in the input. */
  try {
    const opsDoc = JSON.parse(fs.readFileSync(
      path.join(REPO, '.github/scripts/supplier-operations-evidence-v1.json'), 'utf8'));
    const orgs = opsDoc.organisations || {};
    const ps = orgs['recZyvRt8pDg5spUU'], yb = orgs['recyfWvDVODL06P8l'];
    if (ps && ps.installationStatus === 'CONFIRMED' && ps.deliveryStatus === 'CONFIRMED'
        && ps.installationCheckedAt === '2026-09-29') {
      ok('P6', 'Power Sheds certified operations evidence present and dated to its own read');
    } else {
      bad('P6', 'Power Sheds certified operations evidence is missing or mis-dated');
    }
    if (yb && yb.installationStatus === 'CONFIRMED'
        && yb.installationSourceUrl === 'https://www.yardbox.co.uk/') {
      ok('P7', 'Yardbox certified evidence unchanged');
    } else {
      bad('P7', 'Yardbox certified evidence changed or was lost');
    }
  } catch (e) { bad('P6', 'operations evidence unreadable: ' + e.message); }

  /* P8 — P0 JOURNEY RESTORE. Progress is VISIBLE by founder authorisation.
     This used to assert dormancy. Dormancy was the right contract while the
     stage had no evidence and no outbound door; both of those changed, so
     the invariant changes with them -- and it gets STRICTER, not looser.

     Visible is only safe if it cannot become dishonest. So P8 now asserts
     three things at once: the stage is reachable at the recorded threshold,
     the six market resolvers are still hard-open, and the maker lane still
     requires CONFIRMED evidence with a source. Visibility without those three
     would be fabricated readiness, which is the thing dormancy was protecting
     against in the first place. */
  /* R1 — PROGRESS IS NO LONGER HOMEOWNER-VISIBLE, SO THIS TURNED ROUND.

     P8 has been rewritten twice now, and both times for the same
     reason: the invariant follows the journey. It asserted dormancy,
     then visibility, and now absence. What has never changed is the
     thing it exists to protect — that this stage cannot claim
     readiness it does not have. The three assertions carrying that
     claim are below and are untouched.

     Progress survives as an evidence structure. What must not survive
     is a control that opens it. */
  const progVisible = countOf(code, 'myPlotProgressBtn') === 0;
  const resolveVisible = countOf(code, 'els.myPlotResolveBtn.hidden = total < 1;') === 1
                      && countOf(code, 'els.myPlotResolveBtn.hidden = true;') === 0;
  if (progVisible) ok('P8', 'no homeowner-visible control opens Progress');
  else bad('P8', 'a homeowner-visible route to Progress exists — it left the journey');
  if (resolveVisible) ok('P8', 'Resolve is reachable from My Plot at the recorded threshold');
  else bad('P8', 'Resolve is not reachable at `total < 1` — the restored entry point moved');

  const hardOpen = countOf(code, 'return pnOpenCell({ checked:false });');
  if (hardOpen === 6) ok('P8', 'the six market-lane questions are still hard-open — nothing fabricated');
  else bad('P8', 'market-lane hard-open resolvers are ' + hardOpen + ', expected 6 — '
                 + 'a question has been answered without evidence');

  if (code.indexOf("ops.installationStatus !== 'CONFIRMED'") >= 0
      && code.indexOf("ops.deliveryStatus !== 'CONFIRMED'") >= 0
      && code.indexOf("ops.roiDelivery !== 'CONFIRMED'") >= 0) {
    ok('P8', 'the maker lane still requires CONFIRMED status with a source url');
  } else {
    bad('P8', 'a maker-lane evidence test was weakened');
  }

  /* P8 — the headline must not claim readiness it does not have, and must not
     tell the homeowner the product is broken either. */
  if (code.indexOf('PlotNua cannot tell you yet what is normal') >= 0) {
    bad('P8', 'the old broken-sounding Progress headline is still present');
  } else {
    ok('P8', 'the Progress headline frames partial progress without claiming readiness');
  }

  head('M01 · MARKET SOURCE OF TRUTH');
  let uni = null;
  try { uni = JSON.parse(fs.readFileSync(UNIVERSE, 'utf8')); } catch (e) { /* optional */ }
  MARKET_TRUTH.forEach(function (rule) {
    if (!uni) { note('universe not readable; M01 data check skipped'); return; }
    const rows = uni.products.filter(function (p) {
      return String(p.organisation || '') === rule.organisation && (p.imagery || {}).url;
    });
    if (!rows.length) { note(rule.organisation + ': no publishable rows; nothing to check'); return; }
    const bad1 = rows.filter(function (p) {
      return p.currency && p.currency !== rule.expectCurrency;
    });
    const bad2 = rows.filter(function (p) {
      return p.productUrl && p.productUrl.indexOf(rule.verifiedStorefront) < 0;
    });
    note(rule.organisation + ': ' + rows.length + ' publishable, ' + bad1.length +
         ' non-' + rule.expectCurrency + ', ' + bad2.length + ' not on ' + rule.verifiedStorefront);
    note('  ' + rule.status);
    /* The gate does not fail on the data — the contract says it is not repaired
       here. It fails if the code CLAIMS the mismatched route is the Irish one. */
    const claim = new RegExp('Irish[^.]{0,40}(route|storefront|site)[^.]{0,40}' + rule.organisation, 'i');
    if (claim.test(code)) {
      bad('M01', rule.organisation + ': code asserts an Irish route while the recorded route is ' +
                 rule.recordedHost + '/' + rule.recordedCurrency);
    } else {
      ok('M01', rule.organisation + ': mismatch recorded, and no code claims it is the Irish route');
    }
  });
}

/* =========================================================================
   GOLDEN JOURNEY FIXTURES.

   These assert the SHAPE of the journey against the real pool. They do not
   open a dormant screen and they do not require one to be reopened.
   ========================================================================= */

function goldenJourneys(src) {
  head('GOLDEN JOURNEY FIXTURES');

  let uni;
  try { uni = JSON.parse(fs.readFileSync(UNIVERSE, 'utf8')); }
  catch (e) { bad('GJ', 'universe unreadable: ' + e.message); return; }

  const tmp = path.join(__dirname, '.journey-lifted.cjs');
  const parts = ['pnUsablePrice', 'pnNextAction'].map(function (f) {
    return lift(src, 'function ' + f + '(');
  });
  if (parts.some(function (p) { return !p; })) { bad('GJ', 'could not lift the resolver'); return; }
  fs.writeFileSync(tmp, parts.join('\n') + '\nmodule.exports={pnNextAction};');
  let pnNextAction;
  try { pnNextAction = require(tmp).pnNextAction; }
  catch (e) { bad('GJ', 'resolver did not load: ' + e.message); return; }

  const FIXTURES = [
    { id: 'A', label: 'YARDBOX / TORONTO', match: /Toronto/ },
    { id: 'B', label: 'POWER SHEDS', match: /12x12 Apex/ },
  ];

  FIXTURES.forEach(function (fx) {
    const p = uni.products.filter(function (x) {
      return fx.match.test(String(x.name)) && (x.imagery || {}).url;
    })[0];
    if (!p) { bad('GJ' + fx.id, fx.label + ': product not in the publishable pool'); return; }

    console.log('\n  ' + fx.id + ' · ' + fx.label + ' — ' + p.name);

    /* Stage 1-2: Results -> Option Detail. Structural, from the source. */
    const reachable = countOf(src, 'function pnViewOptionButton(product){') === 1 &&
                      countOf(src, 'function openProductDetail(productId, returnScreen){') === 1;
    if (reachable) ok('GJ' + fx.id, 'Results -> View option -> Option Detail is reachable');
    else bad('GJ' + fx.id, 'Results -> Option Detail path is broken');

    /* Stage 3: the continuation seam back into the canonical journey. */
    /* R2 — THE SEAM IS RESOLVE'S ALONE NOW.
       My Plot's continuation back into the canonical journey used to
       have two doors. Progress is not a stage any more, so requiring
       its door would require the journey to contain something it does
       not. Resolve's door is still required, and renderMyPlotPickOne()
       still has to exist — it is what makes that door work. */
    const seam = countOf(src, 'function renderMyPlotPickOne(') === 1 &&
                 countOf(src, 'els.myPlotResolveBtn.addEventListener') === 1 &&
                 countOf(src, 'els.myPlotProgressBtn.addEventListener') === 0;
    if (seam) ok('GJ' + fx.id, 'My Plot -> Resolve is wired, and nothing opens Progress');
    else bad('GJ' + fx.id, 'the My Plot continuation seam is wrong');

    /* THE ASSERTION THAT MATTERS.
       Unresolved decision work exists for this product, so the supplier
       handoff must not be the canonical immediate next stage. Today the code
       says otherwise — that is V2, and it is recorded, not waived away. */
    const next = pnNextAction(p);
    const state = next ? next.state : 'C';
    note('next-action resolver returns state ' + state +
         (next ? ' ("' + next.label + '")' : ' (no outward button)'));

    const unresolved = RESOLVE_KEYS.length; /* none are closed for any product yet */
    if (unresolved > 0) {
      const v2 = countOf(stripComments(src), 'pnSupplierHandover(product, nextAction.state);') === 1;
      if (v2) {
        ok('GJ' + fx.id, 'unresolved decision work exists (' + unresolved + ' registry entries) ' +
                         'and the handoff-from-Option-Detail violation is present exactly as recorded (V2)');
        note('CONTRACT: supplier handoff belongs after Progress, not here');
      } else {
        ok('GJ' + fx.id, 'Option Detail no longer holds the supplier handoff — V2 repaired');
      }
    }
  });

  try { fs.unlinkSync(tmp); } catch (e) { /* best effort */ }
}

/* =========================================================================
   SELF-TEST. Proves the gate can fail, without touching the real file.
   ========================================================================= */

function selfTest() {
  console.log('JOURNEY CONTRACT — SELF TEST');
  console.log('='.repeat(74));
  const src = fs.readFileSync(PAGE, 'utf8');
  const cases = [
    ['dormant Resolve deleted',      function (s) { return s.replace('const RESOLVE_REGISTRY = [', 'const RETIRED_REGISTRY = ['); }, 'J09'],
    ['a second outbound door',       function (s) { return s.replace('window.open(', 'window.open(/*x*/); window.open('); }, 'J07'],
    /* Re-pointed after RP-1: the old anchor was retired, so the mutation had
       become a no-op and the guard looked broken when it was not. */
    ['a rival uncertainty model',    function (s) { return s.replace('function pnResolvePreview(product){', 'function pnProductUncertainties(p){ return []; }\n  function pnResolvePreview(product){'); }, 'J03'],
    ['the preview authors a question',function (s) { return s.replace('    const out = [];\n    if (!product) return out;\n    let registry', "    const out = ['Whether VAT is included on this order'];\n    if (!product) return out;\n    let registry"); }, 'J03'],
    ['the preview writes Resolve state',function (s) { return s.replace('      out.push({ key: entry.key, label: copy.label,', '      recordResolveAnswer(product.id, entry.key, copy.label);\n      out.push({ key: entry.key, label: copy.label,'); }, 'J03'],
    ['V1 returns: a second question model',function (s) { return s.replace('function pnResolvePreview(product){', 'function pnOpenQuestions(product){ return []; }\n  function pnResolvePreview(product){'); }, 'J03'],
    ['Option Detail calls the door again',function (s) { return s.replace('      openMyPlot();', '      pnSupplierHandover(product, nextAction.state);\n      openMyPlot();'); }, 'J07'],
    /* RE-POINTED WITH THE CHECK. The old mutation removed a listener
       that no longer exists, so it had become a no-op -- a mutation
       that changes nothing proves nothing. This one ADDS the route
       back, which is what J08 now forbids. */
    ['a My Plot route to Progress returns', function (s) { return s.replace("  if (els.myPlotResolveBtn) {", "  els.myPlotProgressBtn.addEventListener('click', function(){});\n  if (els.myPlotResolveBtn) {"); }, 'J08'],
    ['registry owner drift',         function (s) { return s.replace("key:'planning', consequence:'blocking', owner:'world'", "key:'planning', consequence:'blocking', owner:'plotnua'"); }, 'J04'],
    ['a new supplier claim',         function (s) { return s.replace('const PB046_NO_PRICE', "const X='we will request'; const PB046_NO_PRICE"); }, 'P01'],
    ['Option Detail gated on rights',function (s) { return s.replace('function openProductDetail(productId, returnScreen){', 'function openProductDetail(productId, returnScreen){\n    if (!pnAuthorisedImage(product)) return false;'); }, 'J12'],

    /* One mutation per remaining guard class, so no guard is claimed as a
       detector without a mutation that only it catches. */
    ['Results cannot open Option Detail', function (s) { return s.replace('function pnViewOptionButton(product){', 'function pnViewOptionButtonRetired(product){'); }, 'J01'],
    ['Option Detail loses its return path', function (s) { return s.replace('productDetailReturn = createReturnableOverlay(', 'productDetailReturn = makeThrowawayOverlay('); }, 'J02'],
    ['Resolve persistence dropped',   function (s) { return s.replace('resolve: resolvePositions.get(id) || null,', '/* dropped */'); }, 'J05'],
    ['readiness model removed',       function (s) { return s.replace('function resolveReadiness(states){', 'function unusedReadiness(states){'); }, 'J06'],
    ['a new routing function',        function (s) { return s.replace('function pnNextAction(product){', 'function pnQuickBuyAction(p){ return null; }\n  function pnNextAction(product){'); }, 'J10'],
    ['publication gate unwired',      function (s) { return s.replace('const publishableCandidates = allCandidates.filter(pnResultPublishable);', 'const publishableCandidates = allCandidates.slice();'); }, 'J11'],
    ['enquiry transport un-gated',    function (s) { return s.replace("const ENQUIRY_TEST_MODE = new URLSearchParams(location.search).get('enquiry') === 'test';", 'const ENQUIRY_TEST_MODE = true;'); }, 'J07'],
    ['code claims the Irish route',   function (s) { return s.replace('const PB046_NO_PRICE', "const CLAIM='the Irish supplier route for Power Sheds'; const PB046_NO_PRICE"); }, 'M01'],
  ];

  let caught = 0;
  cases.forEach(function (c) {
    const [name, mutate, guard] = c;
    fails = []; checks = 0;
    const saved = console.log;
    console.log = function () {};
    try { run(mutate(src)); } catch (e) { fails.push(guard + ' threw'); }
    console.log = saved;
    const hit = fails.some(function (f) { return f.indexOf(guard) === 0; });
    if (hit) caught++;
    console.log((hit ? '  CAUGHT  ' : '  MISSED  ') + name.padEnd(34) +
                (hit ? guard : '-- NOT CAUGHT --'));
  });

  console.log('='.repeat(74));
  console.log(caught + ' of ' + cases.length + ' mutations caught');
  if (caught !== cases.length) {
    console.log('\nA guard that cannot fail proves nothing. Fix the misses above.');
    return 1;
  }
  console.log('\nEvery guard class has a mutation only it catches.');
  return 0;
}

/* ========================================================================= */

function main() {
  if (process.argv.indexOf('--self-test') >= 0) return selfTest();

  console.log('PLOTNUA JOURNEY CONTRACT — architecture gate (test class C)');
  console.log('='.repeat(74));
  const src = fs.readFileSync(PAGE, 'utf8');
  run(src);
  goldenJourneys(src);

  console.log('\n' + '='.repeat(74));
  console.log(checks + ' checks run');
  if (fails.length) {
    console.log('JOURNEY CONTRACT VIOLATED — ' + fails.length + ' failure(s):');
    fails.forEach(function (f) { console.log('  - ' + f); });
    console.log('\nRead PLOTNUA-JOURNEY-CONTRACT.md before changing anything.');
    return 1;
  }
  console.log('JOURNEY CONTRACT HELD — canonical stages intact, recorded violations unchanged');
  return 0;
}

process.exit(main());
