/* ATLAS A PROOF — Phase 1 on the supplied production pack.
   ---------------------------------------------------------------------------
   The Atlas mark is a claim: "Atlas established this." What is guarded here is
   not that the icon renders, but that it NEVER renders over something Atlas did
   not establish for the exact item on screen -- and, new in this release, that
   the SUPPLIED ARTWORK IS USED AS SUPPLIED.

   THE SUBTLE EVIDENCE CASE. pnEvidenceState() returning 'established' is not
   enough. pnScopeNote() is computed separately and attached to the SAME row, so
   a read can be established AND scope-limited -- Atlas verified the supplier's
   range, not this model. Measured over the real universe by lifting the shipped
   functions verbatim: 1,783 established · 552 model-level · 1,231 scope-limited.
   A gate on state alone would make 1,231 false model-level claims.

   A1  The three placements exist, at 24 / 20 / 16px, wired the approved way.
   A2  THE ARTWORK IS THE SUPPLIED ARTWORK. The inlined template is byte-
       identical to assets/brand/atlas-mark-motion-ready.svg, and the pack's
       files still carry the supplied viewBox and group ids.
   A3  The P3 gate requires established AND no scope AND no conflict.
   A4  Driven over the REAL universe with the REAL lifted functions.
   A5  PlotNua P, Property Brain, navigation and the existing search-mark
       animation are untouched.
   A6  Accessibility and the motion contract, including that the house is
       never animated.
   A7  No Atlas mark outside your-plot.html.

   Run: node atlas-tools/prove-atlas-a.mjs                                   */

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const PAGE = path.join(ROOT, 'your-plot.html');
const BRAND = path.join(ROOT, 'assets', 'brand');

let failed = 0, confused = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };
const cannot = (w, d) => { console.log('    ERROR  ' + w); if (d) console.log('           ' + d); confused++; };

console.log('ATLAS A PROOF — PHASE 1 ON THE SUPPLIED PACK');
console.log('='.repeat(76));
const src = fs.readFileSync(PAGE, 'utf8');

/* ---- A1 . placements ---------------------------------------------------- */
console.log('');
console.log('  PLACEMENTS');
console.log('  ' + '-'.repeat(72));
const slots24 = (src.match(/<span class="pn-atlas-slot" data-atlas-size="24"><\/span>/g) || []).length;
slots24 === 2 ? ok('P1 — 2 popover headings carry a 24px Atlas slot')
              : bad('P1 — expected 2 24px slots, found ' + slots24);
/akMark\.setAttribute\('data-atlas-size', '20'\)/.test(src)
  ? ok('P2 — "What Atlas Knows" heading carries a 20px Atlas slot')
  : bad('P2 — the 20px slot is missing');
/am\.src = 'assets\/brand\/atlas-mark-micro\.svg'/.test(src)
  ? ok('P3 — evidence row uses the supplied atlas-mark-micro.svg')
  : bad('P3 — the 16px mark does not point at the supplied micro file');
/* The micro mark must stay an <img> and must never be hydrated/animated. */
/am\.className = 'pn-atlas-mark pn-atlas-mark--16 am-ev-atlas'/.test(src)
  ? ok('P3 — the 16px mark is a plain <img>, not a hydrated slot')
  : bad('P3 — the 16px mark is no longer a plain <img>');
const p3 = /if \(row\.state === 'established'[\s\S]{0,460}?\n      \}/.exec(src);
if (!p3) cannot('could not isolate the P3 block');
else if (/pn-atlas-slot|pn-am-field|pn-am-play/.test(p3[0]))
  bad('the 16px evidence-row mark is animated', 'the supplied contract says micro is static only');
else ok('P3 — the 16px mark carries no animation hook');
/* The retired Open Field geometry must be gone from the page entirely. */
/pn-am-anchor|pn-am-bar|PN_AM_SVG|pn-am-anim/.test(src)
  ? bad('retired Open Field geometry survives in the page')
  : ok('no retired Atlas geometry remains in the page');
for (const [cls, px] of [['--24', 24], ['--20', 20], ['--16', 16]]) {
  const re = new RegExp('\\.pn-atlas-mark' + cls + '\\{ width:' + px + 'px; height:' + px + 'px; \\}');
  re.test(src) ? ok('CSS .pn-atlas-mark' + cls + ' is a ' + px + 'px square')
               : bad('CSS for .pn-atlas-mark' + cls + ' is missing or not ' + px + 'px');
}

/* ---- A2 . THE SUPPLIED ARTWORK, USED AS SUPPLIED ------------------------ */
console.log('');
console.log('  THE SUPPLIED ARTWORK');
console.log('  ' + '-'.repeat(72));
const VB = '0 0 1157 1038';
for (const f of ['atlas-mark.svg', 'atlas-mark-reversed.svg', 'atlas-mark-mono.svg',
                 'atlas-mark-mono-reversed.svg', 'atlas-mark-motion-ready.svg',
                 'atlas-mark-micro.svg']) {
  let s = '';
  try { s = fs.readFileSync(path.join(BRAND, f), 'utf8'); }
  catch (e) { bad('missing supplied file ' + f); continue; }
  if (!s.includes('viewBox="' + VB + '"')) bad(f + ' is not on the supplied ' + VB + ' viewBox');
  else if (/<image|base64|<text|<tspan/.test(s)) bad(f + ' contains raster or text content');
  else ok(f + ' — supplied viewBox, clean vector');
}
/* The motion file must keep the three contract ids. */
const motion = fs.readFileSync(path.join(BRAND, 'atlas-mark-motion-ready.svg'), 'utf8');
['atlas-house', 'atlas-dark-field', 'atlas-sage-field'].every(i => motion.includes('id="' + i + '"'))
  ? ok('atlas-mark-motion-ready.svg keeps the three contract group ids')
  : bad('atlas-mark-motion-ready.svg has lost a contract group id');
/* THE DECISIVE CHECK: the page's inlined copy is the file, character for
   character. If anyone "improves" the mark in the page, this fails. */
const tpl = /<template id="pn-atlas-a-template"><svg[^>]*>([\s\S]*?)<\/svg><\/template>/.exec(src);
if (!tpl) cannot('could not find the inlined Atlas template');
else {
  let want = /<svg[^>]*>([\s\S]*)<\/svg>/.exec(motion)[1];
  want = want.replace(/<title[^>]*>[\s\S]*?<\/title>\s*/g, '')
             .replace(/<desc[^>]*>[\s\S]*?<\/desc>\s*/g, '').trim();
  tpl[1] === want
    ? ok('the inlined artwork is byte-identical to the supplied motion file')
    : bad('the inlined artwork DIFFERS from the supplied file',
          'page ' + tpl[1].length + ' bytes vs file ' + want.length
          + ' — the supplied mark must not be redrawn or restyled in the page');
  tpl[1].includes('id="atlas-house"')
    ? ok('the template carries #atlas-house')
    : bad('the template has lost the house group');
}
/* One copy only: the geometry must not be duplicated across placements. */
const houseCopies = (src.match(/id="atlas-house"/g) || []).length;
houseCopies === 1 ? ok('exactly one copy of the artwork in the page (template only)')
                  : bad('the artwork appears ' + houseCopies + ' times; it should be inlined once');

/* ---- A3 . the gate ------------------------------------------------------ */
console.log('');
console.log('  THE GATE');
console.log('  ' + '-'.repeat(72));
/if \(row\.state === 'established' && !row\.scope && !row\.conflict\)\{/.test(src)
  ? ok("P3 requires established AND no scope note AND no conflict")
  : bad('the P3 gate is not the three-condition form');
(src.match(/state: state/g) || []).length >= 2
  ? ok('the reconciliation layer carries the state it already computed')
  : bad('knows rows do not carry state, so the gate cannot read it');

/* ---- A4 . the real universe --------------------------------------------- */
console.log('');
console.log('  DRIVEN OVER THE REAL UNIVERSE');
console.log('  ' + '-'.repeat(72));
const L = src.split('\n');
const slice = (a, b) => L.slice(a - 1, b - 1).join('\n');
const find = n => { const i = L.findIndex(l => l.includes(n)); return i < 0 ? -1 : i + 1; };
const anchors = ['const PN_EV_LABELS =', 'function pnEvSegment(text, label){',
  'function pnEvTrim(s, max){', 'function atlasFeatureRead(product, key){',
  'function atlasFeatureShort(read, max){', 'const PN_DEFER_RE =',
  'ISSUE 005 PIECE C2 — THE CLOSED-VOCABULARY LABEL MAP',
  'function pnEvidenceState(key, read){', 'function pnScopeNote(read){',
  '/* THE ROW MODEL.'].map(find);
if (anchors.some(x => x < 0)) cannot('could not lift the shipped evidence functions; anchors have moved');
else {
  const [lMark, lSeg, lTrim, lRead, lShort, lDefer, lLabelMap, lState, lScopeNote, lRowModel] = anchors;
  const lifted = path.join(HERE, '.atlas-a-lift.cjs');
  fs.writeFileSync(lifted,
    slice(lMark, lSeg) + '\n' + slice(lSeg, lTrim) + '\n' + slice(lTrim, lRead) + '\n' +
    slice(lRead, lShort) + '\n' + slice(lDefer, lLabelMap) + '\n' +
    slice(lState, lScopeNote - 2) + '\n' + slice(lScopeNote, lRowModel) + '\n' +
    'module.exports={atlasFeatureRead,pnEvidenceState,pnScopeNote};\n');
  const require = createRequire(import.meta.url);
  let M = null;
  try { M = require(lifted); } catch (e) { cannot('the lifted module did not load', e.message); }
  if (M) {
    const uni = JSON.parse(fs.readFileSync(path.join(ROOT, 'garden-room-recommendation-universe-v1.json'), 'utf8'));
    const prods = uni.products || uni.rows || uni;
    const marked = r => r.state === 'established' && !r.scope && !r.conflict;
    let allowed = 0, refused = 0, leak = 0, byScope = {};
    for (const p of prods) {
      for (const key of Object.keys((p && p.features) || {})) {
        const read = M.atlasFeatureRead(p, key);
        if (!read) continue;
        const row = { state: M.pnEvidenceState(key, read), scope: M.pnScopeNote(read), conflict: null };
        if (row.state !== 'established') { if (marked(row)) leak++; continue; }
        if (row.scope) { byScope[read.scope] = (byScope[read.scope] || 0) + 1; marked(row) ? leak++ : refused++; }
        else if (marked(row)) allowed++;
      }
    }
    fs.unlinkSync(lifted);
    leak ? bad(leak + ' row(s) would be marked that must not be')
         : ok('0 rows marked that must not be, across ' + prods.length + ' products');
    refused === 1231 ? ok('1,231 scope-limited established reads REFUSED ' + JSON.stringify(byScope))
                     : bad('expected 1,231 scope-limited refusals, measured ' + refused);
    allowed === 552 ? ok('552 model-level established reads allowed')
                    : bad('expected 552 model-level marks, measured ' + allowed);
    const none = ['none', 'stated', 'deferred', 'negative', 'flat']
      .filter(s => marked({ state: s, scope: null, conflict: null }));
    none.length ? bad('states that must never be marked are: ' + none.join(', '))
                : ok('none / stated / deferred / negative / flat all refused');
    marked({ state: 'established', scope: null, conflict: { a: 1, b: 2 } })
      ? bad('a conflicting row would be marked') : ok('a conflicting row is refused');
  }
}

/* ---- A5 . protected systems --------------------------------------------- */
console.log('');
console.log('  PROTECTED SYSTEMS, ACCESSIBILITY AND MOTION');
console.log('  ' + '-'.repeat(72));
let headPage = '';
try { headPage = execFileSync('git', ['show', 'HEAD:your-plot.html'],
  { cwd: ROOT, maxBuffer: 64 * 1024 * 1024 }).toString(); }
catch (e) { cannot('could not read your-plot.html from HEAD', e.message); }
if (headPage) {
  const drift = [];
  for (const m of ['plotnua-mark-master.svg', 'plotnua-mark-myplot-saved.svg',
                   'plotnua-icon-transparent.svg', 'PN_HOUSE_PATH', 'PN_P_PATH',
                   'Property Brain', 'PROPERTY BRAIN', 'property-brain',
                   'atlas-search-mark', 'pn-atlas-mark-breathe', 'pn-atlas-mark-arrive']) {
    const esc = m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const a = (headPage.match(new RegExp(esc, 'g')) || []).length;
    const b = (src.match(new RegExp(esc, 'g')) || []).length;
    if (a !== b) drift.push(m + ' ' + a + '->' + b);
  }
  drift.length ? bad('a protected reference changed', drift.join('; '))
               : ok('PlotNua P, saved mark, Property Brain, navigation and the '
                    + 'existing search-mark animation all unchanged from HEAD');
}
/* A6 — accessibility and the motion contract. */
/<template id="pn-atlas-a-template"><svg[^>]*aria-hidden="true"[^>]*focusable="false"/.test(src)
  ? ok('the inlined mark is decorative (aria-hidden, not focusable)')
  : bad('the inlined mark is not aria-hidden="true" focusable="false"');
/am\.alt = 'Atlas established evidence';/.test(src)
  ? ok('the standalone 16px mark carries an accessible name')
  : bad('the standalone 16px mark has no accessible name');
/* Start at the comment's OPENING delimiter, not at its text. The first
   version anchored on "ATLAS A MOTION", which sits inside the comment, so the
   extracted block had no opening slash-star and the comment-stripper found
   nothing to strip -- leaving the prose in and failing on the sentence that
   explains the house is never targeted. */
const css = (/\/\* ATLAS A MOTION[\s\S]*?prefers-reduced-motion[\s\S]*?\n  \}\n/.exec(src) || [''])[0];
const rules = css.replace(/\/\*[\s\S]*?\*\//g, '');
if (!css) cannot('could not find the Atlas A motion CSS');
else {
  /animation-iteration-count:1/.test(rules) ? ok('motion plays once (iteration-count 1)')
                                            : bad('the motion does not pin iteration-count to 1');
  const loops = ['infinite', 'alternate', 'animation-direction'].filter(k => rules.includes(k));
  loops.length ? bad('the motion can loop or reverse: ' + loops.join(', '))
               : ok('nothing loops, alternates or reverses');
  const spin = ['rotate(', 'translate(', 'box-shadow', 'drop-shadow', 'filter:']
    .filter(k => rules.includes(k));
  spin.length ? bad('the motion spins, travels or glows: ' + spin.join(', '))
              : ok('no rotation, travel, shadow or filter — only opacity and scale');
  /to\{ opacity:1; transform:scale\(1\) \}/.test(rules)
    ? ok('the keyframe ends settled at opacity 1, scale 1 — nothing pulses after')
    : bad('the motion keyframe does not end at the settled state');
  /@media \(prefers-reduced-motion: reduce\)\{\s*\.pn-atlas-a \.pn-am-field\{ animation:none !important; \}/.test(rules)
    ? ok('prefers-reduced-motion removes the animation entirely')
    : bad('reduced motion does not disable the Atlas animation');
  /* THE HOUSE. The contract says it stays stable, and it is kept stable by
     carrying no rule at all rather than by a rule that could be edited away. */
  (rules.includes('#atlas-house') || rules.includes('pn-am-house'))
    ? bad('the house is targeted by a motion rule')
    : ok('the house carries no motion rule — it cannot move');
  /h\.removeAttribute\("id"\)/.test(src) && !/atlas-house[^\n]*pn-am-field/.test(src)
    ? ok('the hydrator never tags the house as an animated field')
    : bad('the hydrator may tag the house as animated');
}

/* ---- A8 . REACHABILITY -- the check whose absence let the mark ship unseen.

   Phase 1 passed every other check in this file and the founder still could not
   find the mark anywhere. All three placements were wired, sized and gated
   correctly, and all three sat behind an interaction: a popover at
   visibility:hidden, and a closed <details> on a secondary screen. This file
   verified that each placement EXISTED. It never verified that any of them
   could be SEEN.

   So: at least one placement must be on a surface that renders without a
   click, and specifically the "Atlas assessment" masthead must be one of them.
   A placement is unreachable if it is inside the popover, inside the
   collapsed intelligence panel, or carries its own hidden / display:none /
   visibility:hidden. ------------------------------------------------------- */
console.log('');
console.log('  REACHABILITY WITHOUT INTERACTION');
console.log('  ' + '-'.repeat(72));
{
  /* (1) The masthead placement exists and is built where the masthead is. */
  const mastBlock = /const mast = aaEl\('div', 'aa-mast'\);[\s\S]{0,4000}?mast\.appendChild\(aaEl\('span', 'aa-mast-r', org\)\);/.exec(src);
  if (!mastBlock) cannot('could not isolate the Atlas assessment masthead block');
  else {
    /pn-atlas-slot/.test(mastBlock[0]) && /data-atlas-size', '20'/.test(mastBlock[0])
      ? ok('the "Atlas assessment" masthead carries a 20px Atlas slot')
      : bad('the "Atlas assessment" masthead carries no Atlas slot',
            'this is the placement the founder must be able to see on Results');
    /pnAtlasHydrate/.test(mastBlock[0])
      ? ok('the masthead slot hydrates its own subtree — it survives the repaint')
      : bad('the masthead slot is not hydrated locally',
            'aaRenderAssessment() empties and repaints its host, so a slot that '
            + 'waits for DOMContentLoaded renders empty after the repaint');
    /* The masthead mark must not be made conditional: no branch may stand
       between the masthead being created and the mark being appended to it.
       (The pnAtlasHydrate call that follows is itself guarded, which is a
       feature-detect, not a condition on the mark existing.) */
    const upToMark = mastBlock[0].split('const mastMark')[0] || '';
    /\bif\s*\(|\?\s*[^:]*:/.test(upToMark.replace(/\/\*[\s\S]*?\*\//g, ''))
      ? bad('the masthead mark is built conditionally',
            'every assessment must carry it, not some of them')
      : ok('the masthead mark is unconditional — every assessment carries it');
  }

  /* (2) The masthead itself must not be hidden, display:none or inside a
         <details>. aa-mast is appended straight to the assessment host. */
  /mast\.appendChild|host\.appendChild\(mast\)/.test(src)
    ? ok('the masthead is appended directly to the visible assessment host')
    : bad('could not confirm the masthead reaches the assessment host');
  const mastCss = /\.aa-mast\{[^}]*\}/.exec(src);
  if (!mastCss) cannot('could not read the .aa-mast CSS');
  else if (/display:\s*none|visibility:\s*hidden|opacity:\s*0\b/.test(mastCss[0]))
    bad('.aa-mast is hidden by its own CSS', mastCss[0]);
  else ok('.aa-mast carries no hiding rule — it renders on sight');

  /* (3) The two static placements must exist and must NOT animate. */
  const altHeading = /<div class="results-gallery-heading has-atlas-mark"[^>]*>[\s\S]{0,320}?<\/div>/.exec(src);
  if (!altHeading) bad('"Atlas looked at this in other ways." carries no Atlas mark');
  else if (!/data-atlas-motion="static"/.test(altHeading[0]))
    bad('the alternatives heading mark is not marked static');
  else ok('"Atlas looked at this in other ways." carries a static 20px mark');

  /* THE MAKER BAND USES THE SUPPLIED MICRO DERIVATIVE, NOT THE FULL MARK.

     The pack draws a separate file for 16px and the two are not the same
     picture, so scaling the full geometry down would ship artwork the founder
     did not approve for that size. This placement must therefore be the micro
     file, delivered the way the evidence rows deliver it: a plain <img>, which
     is also what makes it unanimatable -- an <img> is never hydrated, so it
     can never pick up a motion class. */
  const mkrBlock = /const blab = aaEl\('p', 'aa-find-lab',[\s\S]{0,2200}?band\.appendChild\(blab\);/.exec(src);
  if (!mkrBlock) cannot('could not isolate the maker band label block');
  else {
    const b = mkrBlock[0];
    if (/pn-atlas-slot|data-atlas-size|pnAtlasHydrate/.test(b))
      bad('the maker band mark is still a hydrated slot of the FULL mark',
          'at 16px it must be assets/brand/atlas-mark-micro.svg');
    else if (!/blabMark\.src = 'assets\/brand\/atlas-mark-micro\.svg'/.test(b))
      bad('the maker band mark does not point at the supplied micro file');
    else if (!/blabMark = document\.createElement\('img'\)/.test(b))
      bad('the maker band micro mark is not a plain <img>');
    else if (!/pn-atlas-mark--16/.test(b))
      bad('the maker band mark is not in the 16px box');
    else if (!/aa-find-lab-mark/.test(b))
      bad('the maker band mark lost its approved spacing class');
    else if (/pn-am-field|pn-am-play|animation/.test(b))
      bad('the maker band micro mark carries an animation hook',
          'the supplied contract says micro is static only');
    else ok('"What Atlas holds on <org>" uses the supplied micro file, '
            + 'static, 16px, spacing intact');
  }

  /* AND THE MICRO FILE IS NOW USED BY TWO PLACEMENTS, BOTH AS <img>. If a
     third mechanism ever reaches it, this count moves and says so. */
  {
    const uses = (src.match(/assets\/brand\/atlas-mark-micro\.svg/g) || []).length;
    uses === 2
      ? ok('the micro file has exactly 2 consumers — evidence row and maker band')
      : bad('the micro file has ' + uses + ' consumer(s), expected 2');
  }

  /* (4) The hydrator must HONOUR static, or "static" is a label with no
         mechanism behind it. */
  /data-atlas-motion"\) === "static"\)\s*return/.test(src)
    ? ok('the hydrator refuses to play a slot marked static')
    : bad('nothing in the hydrator honours data-atlas-motion="static"',
          'the static placements would animate anyway');

  /* (5) AND THE NEGATIVE. None of the three new placements may sit inside the
         popover that hid Phase 1. The popover body runs from its title to its
         confidence paragraph, which is its documented last element, so that
         span is the region to search. */
  {
    /* Anchored on the real ELEMENTS, not the CSS selectors of the same name:
       a selector-anchored search spans everything between the stylesheet and
       the markup, which is most of the file. */
    const re = /<p class="match-atlas-popover-title[\s\S]{0,8000}?match-atlas-popover-confidence"[^<]*<\/p>/g;
    let m, regions = 0, leaked = [];
    while ((m = re.exec(src)) !== null) {
      regions++;
      for (const marker of ['aa-mast-lead', 'aa-find-lab-mark',
                            'results-gallery-heading has-atlas-mark']) {
        if (m[0].includes(marker)) leaked.push(marker);
      }
    }
    if (!regions) cannot('could not isolate any popover body to search');
    else if (leaked.length)
      bad('a visible placement sits inside the hidden popover',
          'found: ' + [...new Set(leaked)].join(', '));
    else ok('none of the 3 new placements sits inside the popover ('
            + regions + ' popover bodies searched)');
  }

  /* (6) NOR INSIDE A CLOSED DISCLOSURE. The <details> wrapper is the other
         thing that hid Phase 1. Each new marker must appear outside every
         <details> block in the page. */
  {
    const details = src.match(/<details[\s\S]*?<\/details>/g) || [];
    const inside = [];
    for (const d of details) {
      for (const marker of ['aa-mast-lead', 'aa-find-lab-mark',
                            'results-gallery-heading has-atlas-mark']) {
        if (d.includes(marker)) inside.push(marker);
      }
    }
    inside.length
      ? bad('a visible placement sits inside a <details> disclosure',
            'found: ' + [...new Set(inside)].join(', '))
      : ok('no new placement sits inside a <details> (' + details.length
           + ' disclosures searched)');
  }

  /* (7) Phase 1 is intact. A visibility fix that moved an existing placement
         would be a worse outcome than the defect. */
  const kept = [
    [2, (src.match(/<span class="pn-atlas-slot" data-atlas-size="24"><\/span>/g) || []).length,
     'the 2 popover 24px slots'],
    [1, (src.match(/akMark\.setAttribute\('data-atlas-size', '20'\)/g) || []).length,
     'the "What Atlas Knows" 20px slot'],
    [1, (src.match(/am\.src = 'assets\/brand\/atlas-mark-micro\.svg'/g) || []).length,
     'the 16px evidence-row micro mark'],
  ];
  let keptOk = true;
  for (const [want, got, what] of kept) {
    if (want !== got) { bad('Phase 1 changed: ' + what + ' (expected ' + want + ', found ' + got + ')'); keptOk = false; }
  }
  if (keptOk) ok('all four Phase 1 placements survive unchanged');

  /* (8) STILL ONE COPY OF THE SUPPLIED GEOMETRY. Three new placements must be
         three more clones, not three more copies of the artwork. */
  const tplCount = (src.match(/id="pn-atlas-a-template"/g) || []).length;
  const vbCount = (src.match(/viewBox="0 0 1157 1038"/g) || []).length;
  (tplCount === 1 && vbCount === 1)
    ? ok('still exactly one copy of the supplied geometry in the page')
    : bad('the supplied geometry is duplicated',
          tplCount + ' template(s), ' + vbCount + ' viewBox occurrence(s)');
}

/* ---- A7 . containment ---------------------------------------------------- */
const stray = fs.readdirSync(ROOT).filter(f => f.endsWith('.html') && f !== 'your-plot.html')
  .filter(f => fs.readFileSync(path.join(ROOT, f), 'utf8').includes('assets/brand/atlas-mark'));
stray.length ? bad('Phase 1 is three placements in one file', 'also found in: ' + stray.join(', '))
             : ok('no Atlas mark on any other page');

console.log('');
console.log('='.repeat(76));
if (confused) { console.log('NOT ESTABLISHED — ' + confused + ' check(s) could not run.'); process.exit(2); }
if (failed) { console.log('FAILED — ' + failed + ' check(s).'); process.exit(1); }
console.log('ATLAS A PHASE 1 VERIFIED — the supplied artwork is used as supplied, '
  + 'the house never moves, and the mark never claims model-level verification '
  + 'Atlas did not establish.');
process.exit(0);
