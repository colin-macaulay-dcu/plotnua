/* DISC-026 DISCOVERY PROOF.
   ---------------------------------------------------------------------------
   Guards the shipped narrative Discovery, discovery-house-as-power-station.html,
   against the specific ways this page could become untrue. It is not a layout
   test. Every check below exists because a real decision was taken and could be
   silently reversed by a later edit.

     G1   FOUNDER CORRECTION 2. A sentence characterising the air at the exempt
          rotor height was withdrawn on 4 October 2026 -- the evidence does not
          establish it to the required standard. It must not return, in copy or
          in a comment.
     G2   THE HERO PLATE keeps its POTENTIAL-ASSET marker.
          prove-discovery-library-capability.py drives this real page and needs
          that marker present to prove the Library guard still refuses a
          before-plate. Remove it and that proof goes quiet while appearing to
          pass.
     G3   THE GOVERNED LIBRARY IMAGE is present, exactly once, with no
          potential-asset marker in its page-side alt text. That is
          prove-discovery-library-images.mjs P4 and P3 seen from this side.
     G4   THE BATTERY DATE BOUNDARY. The SEAI battery grant is stated in
          ANNOUNCED form with 6 October 2026 on its face, inside the
          PN-DISC026-BATTERY-BOUNDARY markers. A present-tense assertion that
          the scheme is open must not appear while the boundary still stands.
     G5   NO REMOTE IMAGERY. Five image permissions are outstanding and all
          five are UNKNOWN. UNKNOWN fails closed, so not one externally hosted
          photograph may appear -- caught here one step before the rights gate.
     G6   WITHDRAWN CLAIMS STAY WITHDRAWN. Each of these failed first-party
          verification or was removed by decision, and each is the kind of
          specific, attractive claim that creeps back in.
     G7   THE HONESTY BREAK PRECEDES THE ENERGY ANATOMY. If S6 ever slips below
          S7 the argument inverts, and a reader arriving at the solar grant
          would reasonably assume the compute part is purchasable too. This is
          the single most important structural fact about the page.
     G8   THE TWO UNCONDITIONAL RCR FINDINGS, VERBATIM.
     G9   THE SEVEN ANATOMY POSITIONS, present and in order. Founder
          correction 1.
     G10  THE WIND ATLAS may only appear as something that CANNOT answer the
          question. Its lowest height is 50 m; the tallest exempt domestic
          turbine is 13 m.
     G11  EVERY EURO AMOUNT ON THE PAGE IS ON THE GOVERNED WHITELIST. This is
          PLATFORM-EVIDENCE-GOVERNANCE.md 5a enforced at the page: no Irish
          grant or financial-support amount enters PlotNua from a secondary
          source, so a new amount appearing here must fail until it is added
          deliberately, with a first-party source behind it.
     G12  FOUNDER CORRECTION 3. The flagship question is asked in the hero and
          returned to in the closing line.

   Exit 0 = governed. Exit 1 = a divergence. Exit 2 = the proof could not
   establish the facts, which is also a failure.

   Run: node atlas-tools/prove-disc026-discovery.mjs                          */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/* fileURLToPath, not url.pathname: this repository's path contains a space. */
const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const PAGE = path.join(ROOT, 'discovery-house-as-power-station.html');

let failed = 0, confused = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };

console.log('DISC-026 DISCOVERY PROOF');
console.log('='.repeat(76));

let html;
try {
  html = fs.readFileSync(PAGE, 'utf8');
} catch (e) {
  console.log('  ERROR  could not read the Discovery: ' + e.message);
  console.log('NOT ESTABLISHED');
  process.exit(2);
}
if (html.length < 40000) {
  console.log('  ERROR  the page is implausibly short (' + html.length + ' bytes), '
    + 'so these checks would pass without testing anything.');
  console.log('NOT ESTABLISHED');
  process.exit(2);
}

const lower = html.toLowerCase();

/* ---- G1 ----------------------------------------------------------------- */
console.log('');
console.log('  G1 . FOUNDER CORRECTION 2 — the withdrawn wind characterisation');
console.log('  ' + '-'.repeat(72));
if (lower.includes('worst air')) {
  bad('the withdrawn sentence is absent',
      'It is back on the page. The evidence does not establish it. '
      + 'Founder decision, 4 October 2026.');
} else {
  ok('the withdrawn characterisation does not appear');
}

/* ---- G2 + G3 ------------------------------------------------------------ */
console.log('');
console.log('  G2/G3 . THE TWO GUARDED IMAGE ASSETS');
console.log('  ' + '-'.repeat(72));
const HERO = 'assets/img/fec77c3f0bae107a.jpg';
const LIBRARY_IMG = 'assets/img/ce9da2e51c945693.jpg';
const PA_MARKERS = ['potential asset', 'annotated by plotnua',
  'before anything is planted', 'standing completely empty'];

const altOf = asset => {
  const re = new RegExp('<img[^>]*src="' + asset.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    + '"[^>]*alt="([^"]*)"');
  const m = re.exec(html);
  return m ? m[1] : null;
};

if ((html.match(new RegExp(HERO, 'g')) || []).length !== 1) {
  bad('the hero plate appears exactly once', HERO);
} else {
  const a = (altOf(HERO) || '').toLowerCase();
  if (PA_MARKERS.some(k => a.includes(k))) {
    ok('the hero plate keeps a potential-asset marker in its alt text');
  } else {
    bad('the hero plate keeps its potential-asset marker',
        'prove-discovery-library-capability.py drives this page and needs that '
        + 'marker to prove the Library guard still refuses a before-plate. '
        + 'Without it, that proof passes while testing nothing.');
  }
}

if ((html.match(new RegExp(LIBRARY_IMG, 'g')) || []).length !== 1) {
  bad('the governed Library image appears exactly once', LIBRARY_IMG);
} else {
  const a = (altOf(LIBRARY_IMG) || '').toLowerCase();
  const hit = PA_MARKERS.filter(k => a.includes(k));
  if (hit.length) {
    bad('the Library image carries no potential-asset marker',
        'its alt text here says ' + JSON.stringify(hit[0]) + ', which would make '
        + 'prove-discovery-library-images.mjs refuse the Library card.');
  } else {
    ok('the governed Library image is present with a realised description');
  }
}

/* ---- G4 ----------------------------------------------------------------- */
console.log('');
console.log('  G4 . THE BATTERY DATE BOUNDARY');
console.log('  ' + '-'.repeat(72));
const begin = (html.match(/PN-DISC026-BATTERY-BOUNDARY-BEGIN/g) || []).length;
const end = (html.match(/PN-DISC026-BATTERY-BOUNDARY-END/g) || []).length;
if (begin !== 1 || end !== 1) {
  bad('the boundary markers are present exactly once each',
      'BEGIN x' + begin + ', END x' + end + '. They are what makes the '
      + '6 October conversion a bounded, anchored edit.');
} else {
  ok('the boundary markers are present exactly once each');
}
if (/From 6 October 2026 SEAI is to pay a flat/.test(html)) {
  ok('the grant is stated in announced form, with its date on its face');
} else {
  bad('the grant is stated in announced form',
      'The announced sentence is gone. Either the boundary was converted '
      + 'without authorisation, or the figure is now unsourced.');
}
if (/there&rsquo;s an SEAI grant of|there's an SEAI grant of/i.test(html)) {
  bad('no present-tense assertion that the scheme is open',
      'The boundary still stands. A present-tense claim here publishes a '
      + 'scheme as open before it has been confirmed live.');
} else {
  ok('no present-tense assertion that the scheme is already open');
}

/* ---- G5 ----------------------------------------------------------------- */
console.log('');
console.log('  G5 . NO REMOTE IMAGERY — UNKNOWN FAILS CLOSED');
console.log('  ' + '-'.repeat(72));
const remote = [...html.matchAll(/<img[^>]+src="(https?:\/\/[^"]+)"/g)].map(m => m[1]);
if (remote.length) {
  bad(remote.length + ' externally hosted image(s)',
      remote.slice(0, 3).join(', ') + '. All five DISC-026 image permissions '
      + '(Codema, heata, SEAI, Precision Heating, Heverin) are UNKNOWN.');
} else {
  ok('every image is a relative PlotNua asset');
}

/* ---- G6 ----------------------------------------------------------------- */
console.log('');
console.log('  G6 . WITHDRAWN CLAIMS STAY WITHDRAWN');
console.log('  ' + '-'.repeat(72));
const WITHDRAWN = [
  ['Hestiia', 'unverified first-party; removed by decision'],
  ['myEko', 'the Hestiia product; same decision'],
  ['XFRA', 'SPAN/XFRA was never first-party verified for this page'],
  ['Sunrun', 'secondary reporting only'],
  ['Voltus', 'secondary reporting only'],
  ['Zai Node', 'secondary reporting only'],
  ['applications until 2028', 'the Dublin claim that could not be verified'],
];
let back = 0;
for (const [needle, why] of WITHDRAWN) {
  if (html.includes(needle)) { bad('withdrawn: ' + needle, why); back++; }
}
if (!back) ok('none of the ' + WITHDRAWN.length + ' withdrawn claims has returned');

/* ---- G7 ----------------------------------------------------------------- */
console.log('');
console.log('  G7 . THE HONESTY BREAK PRECEDES THE ENERGY ANATOMY');
console.log('  ' + '-'.repeat(72));
const seam = html.indexOf('class="seam reveal"');
const anat = html.indexOf('The energy anatomy of your property');
if (seam < 0 || anat < 0) {
  bad('both sections are present', 'seam@' + seam + ' anatomy@' + anat);
} else if (seam > anat) {
  bad('the break comes first',
      'The energy anatomy now sits above the honesty break. A reader reaching '
      + 'the solar grant would reasonably assume the compute part is '
      + 'purchasable too. This inverts the whole argument.');
} else {
  ok('S6 sits above S7, so the status boundary is read before the grants');
}

/* ---- G8 ----------------------------------------------------------------- */
console.log('');
console.log('  G8 . THE TWO UNCONDITIONAL FINDINGS, VERBATIM');
console.log('  ' + '-'.repeat(72));
const F1 = 'Distributed residential computing is not currently commercially';
const F2 = 'no one can tell you whether a property is technically';
[[F1, 'finding 1 — not commercially available through PlotNua in Ireland'],
 [F2, 'finding 2 — nobody has published the technical requirements']]
  .forEach(([needle, label]) => {
    if (html.includes(needle)) ok(label); else bad(label, 'carried verbatim or not at all');
  });

/* ---- G9 ----------------------------------------------------------------- */
console.log('');
console.log('  G9 . THE SEVEN ANATOMY POSITIONS — founder correction 1');
console.log('  ' + '-'.repeat(72));
const POSITIONS = ['1 &middot; Roof',
  '2 &middot; Utility room, garage or wall space',
  '3 &middot; The air beside the house',
  '4 &middot; The ground beneath the garden',
  '5 &middot; The open garden',
  '6 &middot; The driveway',
  '7 &middot; The grid connection'];
const at = POSITIONS.map(p => html.indexOf(p));
const missing = POSITIONS.filter((p, k) => at[k] < 0);
if (missing.length) {
  bad('all seven positions present', 'missing: ' + missing.join(' | '));
} else if (at.join() !== [...at].sort((a, b) => a - b).join()) {
  bad('the seven positions are in order', 'roof, utility, air, ground, garden, driveway, grid');
} else {
  ok('roof, utility, air, ground, garden, driveway, grid — present and in order');
}

/* ---- G10 ---------------------------------------------------------------- */
console.log('');
console.log('  G10 . THE SEAI WIND ATLAS MAY ONLY APPEAR AS UNUSABLE');
console.log('  ' + '-'.repeat(72));
if (!/Wind Atlas/.test(html)) {
  ok('the Wind Atlas is not mentioned at all, which is also correct');
} else {
  const k = html.indexOf('Wind Atlas');
  const near = html.slice(Math.max(0, k - 300), k + 500);
  if (/cannot answer/.test(near) && /50&nbsp;m|50 m/.test(near)) {
    ok('mentioned only as something that cannot answer the question');
  } else {
    bad('the Wind Atlas is framed as unusable at domestic height',
        'Its lowest height is 50 m. The tallest exempt domestic turbine is '
        + '13 m. It must never appear as evidence of domestic suitability.');
  }
}

/* ---- G11 ---------------------------------------------------------------- */
console.log('');
console.log('  G11 . EVERY EURO AMOUNT IS ON THE GOVERNED WHITELIST');
console.log('  ' + '-'.repeat(72));
/* The governance rule of 4 October 2026: no Irish grant or financial-support
   amount enters PlotNua from a secondary source. Each amount below traces to a
   first-party record. A new amount must fail here until it is added
   deliberately, with its source. */
const ALLOWED = new Set(['700', '200', '1,800', '600', '14,500', '400', '80']);
/* Thousands-grouped only, so a trailing sentence comma is not read as part of
   the figure. "about &euro;80, and warns" is 80, not "80,". */
const amounts = [...html.matchAll(/&euro;(\d{1,3}(?:,\d{3})*)/g)].map(m => m[1]);
const strays = [...new Set(amounts)].filter(a => !ALLOWED.has(a));
if (strays.length) {
  bad('no ungoverned euro amount on the page',
      'found ' + strays.join(', ') + '. Add it to this whitelist only with a '
      + 'first-party source recorded. Governance 5a.');
} else {
  ok(amounts.length + ' euro figure(s), all on the governed whitelist');
}

/* ---- G12 ---------------------------------------------------------------- */
console.log('');
console.log('  G12 . THE FLAGSHIP IS ASKED, AND RETURNED TO — correction 3');
console.log('  ' + '-'.repeat(72));
/* Counted PER SURFACE, not across the document. The phrase also sits in the
   og: and twitter: descriptions, so a document-wide count of two would pass
   with the closing line gutted -- which is exactly how an earlier version of
   this check missed its own capability test. */
const FLAGSHIP = /do some of the work of a\s+data centre/;
const heroBlock = html.slice(html.indexOf('class="d-hero-copy'),
                             html.indexOf('</header>'));
const closeAt = html.indexOf('class="closing-line');
const closeBlock = closeAt < 0 ? '' : html.slice(closeAt, closeAt + 900);

if (closeAt < 0) {
  bad('the closing line is present');
} else {
  ok('the closing line is present');
}
if (FLAGSHIP.test(heroBlock)) ok('the hero asks the flagship question');
else bad('the hero asks the flagship question',
         'it is the subtitle, and it is the whole Discovery.');
if (FLAGSHIP.test(closeBlock)) {
  ok('the closing line returns to the flagship question');
} else {
  bad('the closing line returns to the flagship question',
      'Founder correction 3: the ending returns to the revelation, as a '
      + 'question, not to a watching brief.');
}

/* ---- G13 ---------------------------------------------------------------- */
/* FOUNDER REVIEW, 4 October 2026. The evidence discipline lives in the code
   and the guards. The homeowner reads the limitation, never the machinery --
   and never our correspondence workflow either. */
console.log('');
console.log('  G13 . NO IMPLEMENTATION OR WORKFLOW LANGUAGE IN HOMEOWNER COPY');
console.log('  ' + '-'.repeat(72));
const visible = html
  .replace(/<!--[\s\S]*?-->/g, '')
  .replace(/<(script|style)[\s\S]*?<\/\1>/g, '')
  .toLowerCase();
const MACHINERY = [
  'build gate', 'emitted on every', 'three states and no score',
  'four kinds of finding', 'capability proof', 'fails closed',
  'has asked heata', 'has written to codema', 'permission requests are out',
  'has not had an answer', 'rights manifest', 'guard refuses',
];
const leaked = MACHINERY.filter(p => visible.includes(p));
if (leaked.length) {
  bad('no implementation or workflow language reaches the reader',
      'found: ' + leaked.join(', ') + '. The discipline belongs in the code; '
      + 'the limitation belongs in plain English.');
} else {
  ok('none of the ' + MACHINERY.length + ' machinery phrases reaches the reader');
}
/* And the limitation itself must still be stated, or correction 1 would have
   been satisfied by deleting the honesty rather than rewording it. */
if (/nobody has established what a fully/i.test(html)
    && /will not give you a score/i.test(html)) {
  ok('the no-score limitation is stated in homeowner English');
} else {
  bad('the no-score limitation survives in homeowner English',
      'removing the machinery must not remove the honesty.');
}

/* ---- G14 ---------------------------------------------------------------- */
/* We have DIRECT evidence about Tandem. We have no evidence about every Irish
   operator, and the page must never speak for all of them. */
console.log('');
console.log('  G14 . NO GENERALISATION FROM ONE OPERATOR TO ALL');
console.log('  ' + '-'.repeat(72));
const GENERALISATIONS = [
  'any irish operator', 'no irish operator', 'irish operators',
  'not connected to an irish house by anyone', 'none of the irish operators',
];
const over = GENERALISATIONS.filter(p => html.toLowerCase().includes(p));
if (over.length) {
  bad('the page does not generalise from Tandem to all Irish operators',
      'found: ' + over.join(', ') + '. Direct operator evidence covers Tandem '
      + 'and nobody else.');
} else {
  ok('no generalisation from one operator to the whole Irish market');
}
if (/Tandem has confirmed that individual homes are not part of its current\s+pipeline/.test(html)) {
  ok('the bounded Tandem formulation is present');
} else {
  bad('the bounded Tandem formulation is present',
      'the correction replaces the generalisation with a statement about '
      + 'Tandem and a statement about what PlotNua has not found.');
}

/* ---- G15 ---------------------------------------------------------------- */
/* The seven positions lead, and the detail is demoted rather than deleted. */
console.log('');
console.log('  G15 . THE POSITIONS LEAD AND THE DETAIL IS DEMOTED, NOT DELETED');
console.log('  ' + '-'.repeat(72));
const eqs = (html.match(/class="pos-eq"/g) || []).length;
const drawers = (html.match(/<details class="faq-item is-inline">/g) || []).length;
if (eqs === 7) ok('seven leading position ideas'); else bad('seven leading position ideas', 'found ' + eqs);
if (drawers === 7) ok('one detail drawer per position'); else bad('one detail drawer per position', 'found ' + drawers);
const DEMOTED = ['&euro;700 per kWp', '&euro;1,800', '0% VAT',
  'Architectural Conservation Area', '&euro;14,500', '2.3', 'NC6',
  '13&nbsp;m', '43&nbsp;dB(A)', 'special amenity area order',
  'Section 5 Declaration', 'small wind turbines', '&euro;400 a year',
  'offered and refused', 'EN&nbsp;50549', 'Safe Electric', 'Wind Atlas'];
const dropped = DEMOTED.filter(d => !html.includes(d));
if (dropped.length) {
  bad('every demoted fact is still on the page',
      'missing: ' + dropped.join(', ') + '. Simplifying the surface must not '
      + 'quietly delete the evidence behind it.');
} else {
  ok('all ' + DEMOTED.length + ' sampled demoted facts are still reachable');
}

/* ---- G16 ---------------------------------------------------------------- */
/* The ground-source revelation is back, and it is still bounded. */
console.log('');
console.log('  G16 . GROUND-SOURCE COOLING — RESTORED AS A CONCEPT, NOT A CLAIM');
console.log('  ' + '-'.repeat(72));
if (/The ground can do more than heat a house\./.test(html)
    && /can also use that same ground connection for cooling/.test(html)) {
  ok('the revelation is present');
} else {
  bad('the revelation is present',
      'suppressing the concept entirely was the thing the correction reversed.');
}
if (/depends on the system, the ground\s+conditions and the design/.test(html)) {
  ok('conditioned on system, ground conditions and design');
} else {
  bad('conditioned on system, ground conditions and design');
}
const COOLING_OVERCLAIM = ['will provide cooling', 'gives free cooling',
  'provides passive cooling', 'free cooling in summer', 'delivers cooling'];
const oc = COOLING_OVERCLAIM.filter(p => html.toLowerCase().includes(p));
if (oc.length) {
  bad('no claim that an Irish domestic installation will cool',
      'found: ' + oc.join(', '));
} else {
  ok('no claim that an Irish domestic installation will cool');
}
if (/has not established, from a\s+first-party Irish source/.test(html)) {
  ok('the Irish evidence limitation is kept, in the detail layer');
} else {
  bad('the Irish evidence limitation is kept, in the detail layer');
}

/* ---- G17 ---------------------------------------------------------------- */
console.log('');
console.log('  G17 . IMAGE PLACEHOLDERS ARE QUIET AND EDITORIAL');
console.log('  ' + '-'.repeat(72));
if (/class="rights"/.test(html)) {
  bad('no operational rights block remains',
      'the permission workflow is not homeowner copy.');
} else {
  ok('no operational rights block remains');
}
const notes = (html.match(/class="imgnote"/g) || []).length;
const sentence = (html.replace(/\s+/g, ' ').match(
  /Real installation photography will be added when publication rights are confirmed\./g) || []).length;
if (notes === 4 && sentence === 4) {
  ok('four quiet notes, each carrying the one editorial sentence');
} else {
  bad('four quiet notes, each carrying the one editorial sentence',
      'notes ' + notes + ', sentences ' + sentence);
}

/* ---- G18 ---------------------------------------------------------------- */
/* FOUNDER VISUAL REVIEW, CORRECTION 01. The kicker answers WHAT this is, not
   only WHERE in the story the reader has got to. Geographic and narrative
   labels where a distinct technology is being introduced do not orient
   anybody. CATEGORY -> REVELATION -> STATUS. */
console.log('');
console.log('  G18 . CATEGORY LABELS ANSWER "WHAT IS THIS?"');
console.log('  ' + '-'.repeat(72));
const CATEGORIES = ['Computing and heat', 'Home compute &middot; useful heat',
  'Data centres &middot; useful heat', 'Distributed compute &middot; Ireland'];
const missingCat = CATEGORIES.filter(c => !html.includes('<div class="kicker">' + c + '</div>'));
if (missingCat.length) {
  bad('the four technology categories are present', 'missing: ' + missingCat.join(' | '));
} else {
  ok('four technology categories, in the small uppercase treatment');
}
const RETIRED = ['The mechanism', 'Somewhere else', 'And in Ireland',
  'Who is building it here'];
const revived = RETIRED.filter(c => html.includes('<div class="kicker">' + c + '</div>'));
if (revived.length) {
  bad('the geographic and story labels stay retired', 'back: ' + revived.join(' | '));
} else {
  ok('no geographic or story label has returned in their place');
}
/* and the seven positions carry their technology beside their place */
const POS_TECH = ['Solar energy', 'Battery storage', 'Air-source heat',
  'Ground-source energy', 'Small wind', 'EV energy', 'Export and flexibility'];
const missTech = POS_TECH.filter(t => !html.includes('&middot; ' + t + '</span>'));
if (missTech.length) {
  bad('each anatomy position names its technology', 'missing: ' + missTech.join(', '));
} else {
  ok('all seven positions name both the place and the technology');
}
/* a label is an orientation aid, not a heading. If one ever grows into an h2
   or h3 the taxonomy has become a technical catalogue. */
if (/<h[23][^>]*>\s*(Solar energy|Battery storage|Small wind|EV energy)\b/.test(html)) {
  bad('categories stay as kickers, not headings',
      'a category has been promoted to a heading, which turns the Discovery '
      + 'into a technology catalogue.');
} else {
  ok('no category has been promoted to a heading');
}

/* ---- G19 ---------------------------------------------------------------- */
/* The declared five-level type scale. The review finding was that too many
   sentences carried near-hero authority; these are the rules that fixed it,
   and a later edit that removes one silently restores the problem. */
console.log('');
console.log('  G19 . THE DECLARED TYPE SCALE IS INTACT');
console.log('  ' + '-'.repeat(72));
const SCALE = [
  ['A hero', 'font-size:clamp(32px,5vw,58px)'],
  ['B proof', '.article-section h2.is-proof{ font-size:clamp(26px,3.4vw,40px)'],
  ['B anatomy', 'font-size:clamp(27px,4.4vw,48px)'],
  ['C section', '.article-section h2{ font-size:clamp(23px,2.6vw,31px)'],
  ['E spark', '.spark{ padding:7vh 7vw; }'],
  ['E closing', '.closing-line{ padding:11vh 7vw 10vh; }'],
];
const brokenScale = SCALE.filter(([, rule]) => !html.includes(rule));
if (brokenScale.length) {
  bad('every level of the declared scale is present',
      'missing: ' + brokenScale.map(s => s[0]).join(', '));
} else {
  ok('all six scale rules present — A, B, B, C, E, E');
}
/* exactly one headline may carry proof scale, and it must be the Tallaght one */
const proofs = (html.match(/class="is-proof"/g) || []).length;
if (proofs !== 1) {
  bad('exactly one proof-scale headline', 'found ' + proofs
      + '. If everything is a proof, nothing reads as one.');
} else if (!/<h2 class="is-proof">Waste heat from a data centre/.test(html)) {
  bad('the proof-scale headline is the Tallaght one');
} else {
  ok('one proof-scale headline, and it is the Irish proof');
}

/* ---- G20 ---------------------------------------------------------------- */
/* THE DIAGRAM INVENTORY. Five SVGs and no more: the hero's Potential Asset
   annotation, and four PlotNua drawings. A new drawing appearing here without
   a decision is how a page acquires placeholder art. */
console.log('');
console.log('  G20 . THE DIAGRAM INVENTORY');
console.log('  ' + '-'.repeat(72));
const svgCount = (html.match(/<svg/g) || []).length;
const VIEWBOXES = [
  ['hero Potential Asset annotation', 'viewBox="0 0 1408 768"'],
  ['heat mechanism, compact strip', 'viewBox="0 0 900 132"'],
  ['development-scale model', 'viewBox="0 0 900 420"'],
];
const missingVb = VIEWBOXES.filter(([, vb]) => !html.includes(vb));
const plates = (html.match(/viewBox="0 0 900 470"/g) || []).length;
if (svgCount !== 5) {
  bad('exactly five SVGs', 'found ' + svgCount);
} else if (missingVb.length) {
  bad('each drawing is the one it is meant to be',
      'missing: ' + missingVb.map(v => v[0]).join(', '));
} else if (plates !== 2) {
  bad('two full plates: the anatomy and the wind envelope', 'found ' + plates);
} else {
  ok('five SVGs: the hero annotation and four PlotNua drawings');
}
/* THE WIND ENVELOPE IS ARITHMETIC, NOT TASTE. 1 metre = 24px, so each
   dimension line must span exactly its metres x 24. A drawing captioned
   "to scale" that is not to scale is a false claim about a legal limit. */
const DIMS = [
  ['13 m total height', 'd="M176 88 V400', 312],
  ['6 m rotor', 'd="M424 88 V232', 144],
  ['3 m clearance', 'd="M424 328 V400', 72],
  ['14 m setback', 'd="M300 432 H636', 336],
];
const wrong = DIMS.filter(([, path]) => !html.includes(path));
if (wrong.length) {
  bad('the wind envelope is drawn to its stated scale',
      'missing or altered: ' + wrong.map(d => d[0]).join(', ')
      + '. At 24px to the metre these spans are 312, 144, 72 and 336px.');
} else {
  ok('wind envelope dimensions are exact at 24px to the metre');
}
if (/drawn to the rule&rsquo;s own\s+scale/.test(html)) {
  bad('no caption claims a scale drawing that is not there',
      'this sentence once described the anatomy section, which is not drawn to '
      + 'the 13 m rule.');
} else {
  ok('no caption claims a scale drawing that does not exist');
}
if (html.includes('There is no photograph here because there is nothing to')) {
  bad('the "nothing to photograph" sentence stays removed',
      'the illustration and its caption carry the state honestly.');
} else {
  ok('the "nothing to photograph" sentence stays removed');
}
if (html.includes('How a development-scale model could work. Illustration based')) {
  ok('the development-model caption is the required wording');
} else {
  bad('the development-model caption is the required wording');
}

/* ---- G21 ---------------------------------------------------------------- */
console.log('');
console.log('  G21 . NO INSTRUCTION TO THE READER ABOUT READING THE EVIDENCE');
console.log('  ' + '-'.repeat(72));
const INSTRUCTIONS = ['read those figures carefully', 'read these figures carefully',
  'note carefully', 'read carefully', 'pay close attention to the'];
const instr = INSTRUCTIONS.filter(p => lower.includes(p));
if (instr.length) {
  bad('the page does not instruct the reader how to read it',
      'found: ' + instr.join(', '));
} else {
  ok('no instruction to the reader about interpreting the evidence');
}
if (/Every one of those figures is British or German/.test(html)) {
  ok('the bounding sentence survives on its own');
} else {
  bad('the bounding sentence survives on its own',
      'removing the instruction must not remove the bound it introduced.');
}

/* ---- G22 ---------------------------------------------------------------- */
/* FOUNDER VISUAL REVIEW, CORRECTION 02. A homeowner should not have to know
   what an "exempt envelope" is.

   NARROW BY DESIGN, and the founder asked for it that way. This policies the
   HOMEOWNER SURFACE only -- comments, <script> and <style> are stripped
   first -- and it forbids the two retired phrases, not the word "envelope".
   The word is still correct in internal names, in this file's own prose, in
   the builder that made the change and in the capability case labels, and a
   global prohibition would have fired on all of them and started a rename
   cascade through the geometry proofs. The geometry checks in G20 are
   untouched: this correction moved no coordinate. */
console.log('');
console.log('  G22 . HOMEOWNER LANGUAGE ON THE WIND DRAWING');
console.log('  ' + '-'.repeat(72));
const surface = html
  .replace(/<!--[\s\S]*?-->/g, '')
  .replace(/<(script|style)[\s\S]*?<\/\1>/g, '');
const RETIRED_WORDING = ['The exempt envelope, in full',
  'The exempt envelope, drawn to scale.'];
const backAgain = RETIRED_WORDING.filter(p => surface.includes(p));
if (backAgain.length) {
  bad('the retired planning jargon stays off the homeowner surface',
      'found: ' + backAgain.join(' | ')
      + '. A homeowner should not have to know what an exempt envelope is.');
} else {
  ok('neither retired phrase appears on the homeowner surface');
}
if (/exempt envelope/i.test(surface)) {
  bad('"exempt envelope" does not appear in homeowner-visible copy',
      'the phrase is back somewhere on the surface, including in an alt or '
      + 'aria-label, which a screen-reader user reads.');
} else {
  ok('"exempt envelope" appears nowhere a homeowner can read it');
}
const REPLACEMENTS = [
  ['drawer summary', 'The planning limits, at a glance'],
  ['caption', '<p class="anat-cap">The planning limits, drawn to scale.</p>'],
  ['aria-label', 'aria-label="The planning limits for a domestic wind turbine'],
  ['scale note', 'Drawn to scale. At the maximum exempt size, the turbine can be '
    + 'up to 13 m high and must be at least 14 m from the party boundary.'],
];
const missingRepl = REPLACEMENTS.filter(([, s]) => !html.includes(s));
if (missingRepl.length) {
  bad('all four corrected strings are present',
      'missing: ' + missingRepl.map(r => r[0]).join(', '));
} else {
  ok('drawer summary, caption, aria-label and scale note all corrected');
}
/* The dimensions must stay NAMED on the drawing. Plainer words must not cost
   the homeowner the four numbers that are the whole point of it. */
const SHOWN = ['13 m TOTAL HEIGHT', '6 m ROTOR', '3 m MINIMUM CLEARANCE',
  '14 m SETBACK'];
const unlabelled = SHOWN.filter(s => !html.includes(s));
if (unlabelled.length) {
  bad('every governed dimension is still labelled on the drawing',
      'missing: ' + unlabelled.join(', '));
} else {
  ok('all four governed dimensions still labelled on the drawing');
}

/* ---- structure ---------------------------------------------------------- */
console.log('');
console.log('  STRUCTURE');
console.log('  ' + '-'.repeat(72));
const pair = (a, b, label) => {
  const x = (html.match(new RegExp(a, 'g')) || []).length;
  const y = (html.match(new RegExp(b, 'g')) || []).length;
  if (x === y) ok(label + ' balanced (' + x + ')');
  else bad(label + ' balanced', a + ' x' + x + ' vs ' + b + ' x' + y);
};
pair('<main', '</main>', 'main');
pair('<section', '</section>', 'section');
pair('<svg', '</svg>', 'svg');
pair('<details', '</details>', 'details');

console.log('');
console.log('='.repeat(76));
if (confused) { console.log('NOT ESTABLISHED'); process.exit(2); }
if (failed) {
  console.log('DIVERGED — ' + failed + ' check(s) failed.');
  process.exit(1);
}
console.log('GOVERNED — the DISC-026 Discovery holds every founder correction, '
  + 'the battery date boundary, the status boundary, the image-rights fail-closed '
  + 'position and the governed figure whitelist.');
process.exit(0);
