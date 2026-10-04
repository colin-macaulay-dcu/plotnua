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
/* The static-mark rules live outside the old ATLAS A MOTION block, so that
   section reads the whole stylesheet rather than the scoped extract. */
const rulesAll = (src.match(/<style[^>]*>[\s\S]*?<\/style>/g) || []).join('\n')
                   .replace(/\/\*[\s\S]*?\*\//g, '');
if (!css) cannot('could not find the Atlas A motion CSS');
else {
  /* ------------------------------------------------------------------------
     THE MOTION CONTRACT, AS AMENDED. The entrance settle plays once
     EVERYWHERE. Continuous ambient drift is permitted on the primary 60x54
     lockup and on NOTHING ELSE. These checks encode the exception as an
     exception: the loop must be reachable only through .pn-atlas-mark--60.
     --------------------------------------------------------------------- */
  /animation-iteration-count:1;/.test(rules)
    ? ok('the entrance settle still plays once (iteration-count 1)')
    : bad('the entrance settle no longer pins iteration-count to 1');

  /* LOOPING IS SCOPED, NOT PERMITTED. Every declaration carrying a looping
     keyword must belong to a selector naming the 60px lockup. This is the
     check that stops the exception widening: a loop added to
     `.pn-atlas-a .pn-am-field` would reach the popover and panel marks, and
     it fails here. */
  {
    const blocks = rules.split('}');
    const leaks = [];
    for (const b of blocks) {
      if (!/infinite|alternate/.test(b)) continue;
      const sel = (b.split('{')[0] || '').trim().split('\n').pop().trim();
      if (!sel.includes('pn-atlas-mark--60')) leaks.push(sel || '(unknown selector)');
    }
    leaks.length
      ? bad('looping motion escapes the 60px lockup', 'reachable via: ' + leaks.join(' | '))
      : ok('looping is reachable ONLY through .pn-atlas-mark--60 — no other mark inherits it');
  }
  /* ===== THE APPROVED STATIC ATLAS MARK ==========================
     Founder decision: the primary Atlas placement is a supplied STATIC raster.
     The SVG-motion contract this section used to assert is retired along with
     the animation it described. What is asserted now is that the supplied
     asset is used as supplied and that nothing anywhere makes it move. */
  {
    const IMG = 'assets/brand/atlas-final-static-approved-transparent.png';
    (src.split(IMG).length - 1) === 1
      ? ok('the approved static mark is referenced exactly once')
      : bad('the approved static mark reference count is wrong');
    fs.existsSync(path.join(ROOT, IMG))
      ? ok('the supplied asset is present on disk')
      : bad('the supplied asset is missing from the repo');

    /* THE ANIMATION IS GONE FROM THIS PRESENTATION POINT. */
    const retired = [
      ['<video', 'a video tag'],
      /* A tag search alone misses the JS route, which is how the retired
         implementation actually built its player. */
      ["createElement('video')", 'a video element built in JS'],
      ['video/webm', 'a webm source type'],
      ['video/mp4', 'an mp4 source type'],
      ['atlas-final-living-loop-transparent.webm', 'the transparent webm'],
      ['atlas-final-living-loop.mp4', 'the mp4'],
      ['atlas-final-static-fallback-transparent.png', 'the animation fallback'],
      ['pn-atlas-loop', 'the video wrapper'],
      ['pn-atlas-mark--60', 'the retired 60px SVG box'],
      ['pn-atlas-a-drift', 'the retired SVG ambient drift'],
    ].filter(([s]) => src.includes(s));
    retired.length === 0
      ? ok('no video, no webm/mp4, no retired SVG motion survives at the masthead')
      : bad('a retired implementation survives', retired.map(r => r[1]).join(', '));

    /* AND NOTHING MAKES THE STATIC MARK MOVE. */
    const still = rulesAll.split('}').filter(b2 => b2.includes('pn-atlas-still')).join('}');
    const moves = ['@keyframes', 'animation', 'transition', 'transform',
                   'mix-blend-mode', 'filter:', 'rotate', 'scale(']
      .filter(k => still.includes(k));
    moves.length === 0
      ? ok('the static mark carries no animation, transition, transform, blend or filter')
      : bad('the static mark is not inert', moves.join(', '));

    /* SIZING, POSITION AND RESPONSIVE BEHAVIOUR CARRIED OVER. */
    /\.pn-atlas-still\{[^}]*width:60px; height:60px;/.test(rulesAll)
      ? ok('60px box preserved')
      : bad('the 60px box was not preserved');
    /@media \(max-width:360px\)\{\s*\.pn-atlas-still\{ width:48px; height:48px; \}/.test(rulesAll)
      ? ok('48px at <=360 preserved')
      : bad('the narrow-width box was not preserved');
    /aspect-ratio:1 \/ 1/.test(rulesAll)
      ? ok('1:1 intrinsic ratio declared — no layout shift before load')
      : bad('the 1:1 ratio is not declared');
    /const mastImg = document\.createElement\('img'\);/.test(src)
      ? ok('the mark is an <img> — a plain image, not a player')
      : bad('the masthead mark is not built as an <img>');
    (/mastImg\.width = 60; mastImg\.height = 60;/.test(src)
     && /mastImg\.setAttribute\('aria-hidden', 'true'\)/.test(src)
     && /mastImg\.alt = '';/.test(src))
      ? ok('decorative: empty alt, aria-hidden, explicit 60x60 box')
      : bad('the image is not correctly declared decorative');
    /mastLead\.appendChild\(aaEl\('span', 'aa-mast-l', 'Atlas assessment'\)\)/.test(src)
      ? ok('still sits in the masthead lead beside the Atlas assessment heading')
      : bad('the masthead placement changed');

    /* THE SMALL PLACEMENTS KEEP THE INLINED SVG — unchanged by this decision. */
    (/viewBox="0 0 1157 1038"/.test(src) && /\.pn-atlas-mark--24\{/.test(src)
     && /\.pn-atlas-mark--20\{/.test(src) && /\.pn-atlas-mark--16\{/.test(src))
      ? ok('the 24px, 20px and 16px SVG placements are untouched')
      : bad('a small SVG placement changed');
  }

  /\.pn-atlas-mark--60[^{]*\{[^}]*animation[^}]*!important/.test(rules)
    ? bad('an ambient rule uses !important', 'it would survive the reduced-motion override')
    : ok('no ambient rule uses !important — reduced motion always wins');

  /* THE HOUSE. Kept fixed by omission, now twice over: no stylesheet rule
     names it, and the hydrator gives it no class for a selector to find. */
  (rules.includes('#atlas-house') || rules.includes('pn-am-house'))
    ? bad('the house is targeted by a motion rule')
    : ok('the house carries no motion rule — it cannot move');
  /g\.classList\.add\(id === "atlas-dark-field" \? "pn-am-dark" : "pn-am-sage"\)/.test(src)
    ? ok('the hydrator distinguishes the two fields after stripping their ids')
    : bad('the hydrator does not distinguish dark from sage', 'opposing drift would be inexpressible');
  /DELAYS = \{ "atlas-dark-field"[^}]*"atlas-sage-field"[^}]*\}/.test(src)
    && !/DELAYS[^;]*atlas-house/.test(src)
    ? ok('the house is not in DELAYS, so it never receives a field class')
    : bad('the house may receive a field class');
  /h\.removeAttribute\("id"\)/.test(src) && !/atlas-house[^\n]*pn-am-field/.test(src)
    ? ok('the hydrator never tags the house as an animated field')
    : bad('the hydrator may tag the house as animated');
}

/* ---- A8 . THE ATLAS IDENTITY LOCKUP, AND ITS SIZE.

   Two failures are encoded here, so neither can recur silently.

   FIRST, REACHABILITY. Phase 1 passed every other check in this file and the
   founder could not find the mark: all three placements sat behind an
   interaction. Existing is not the same as visible.

   SECOND, SIZE. The correction then put marks at 16-20px, which failed on
   sight. The geometry says why: the viewBox is 1157x1038, so a SQUARE box
   letterboxes the art and loses 10.3% of its height, and the house is only
   18.1% of the mark's width -- 3.6 x 4.2px at 20px nominal. The finest sage
   ribbon does not clear the 2px floor until about 53px.

   THIRD, AND CURRENT: the masthead placement is no longer the SVG at all.
   The founder approved a supplied STATIC raster for it, so the reachability
   and aspect requirements above are now carried by the static asset section
   near the top of this file, and this section asserts that the retired 60x54
   SVG lockup left nothing behind. The 24/20/16px placements are still the SVG
   and the house assertions above still govern them.

   So the assertions are: ONE visible mark, in the masthead, supplied as a
   static raster and inert, reachable without interaction; no leftovers from
   the retired SVG lockup; no mark on the two retired labels; the gated micro
   signature untouched; one source copy of the geometry. ---------------- */
console.log('');
console.log('  THE ATLAS IDENTITY LOCKUP');
console.log('  ' + '-'.repeat(72));
{
  /* (1) THE MASTHEAD'S SVG LOCKUP IS RETIRED.
     The founder approved a supplied STATIC raster for this one placement, so
     the masthead no longer clones the SVG template at 60x54. The positive
     assertions for what IS there now live in THE APPROVED STATIC ATLAS MARK
     section above; what this block asserts is that the retired lockup left
     nothing behind -- no 60px class, no size attributes, no orphan slot. */
  const mastBlock = /const mast = aaEl\('div', 'aa-mast'\);[\s\S]{0,4000}?mast\.appendChild\(aaEl\('span', 'aa-mast-r', org\)\);/.exec(src);
  if (!mastBlock) cannot('could not isolate the Atlas assessment masthead block');
  else {
    const b = mastBlock[0];
    const left = [
      ["data-atlas-size', '60'", 'the 60px size attribute'],
      ["data-atlas-height', '54'", 'the 54px height attribute'],
      ['pn-atlas-slot', 'an SVG slot'],
      ['pn-atlas-mark--60', 'the 60px mark class'],
    ].filter(([s]) => b.includes(s));
    left.length === 0
      ? ok('the retired SVG lockup left nothing behind in the masthead')
      : bad('the retired SVG lockup partly survives', left.map(r => r[1]).join(', '));
    /pn-atlas-still/.test(b)
      ? ok('the masthead carries the approved static mark')
      : bad('the masthead carries no static mark');
    const upToMark = b.split('const mastMark')[0] || '';
    /\bif\s*\(/.test(upToMark.replace(/\/\*[\s\S]*?\*\//g, ''))
      ? bad('the masthead mark is built conditionally')
      : ok('the masthead mark is unconditional — every assessment carries it');
  }
  /* And the retired class is gone from the stylesheet too, so no rule is left
     styling a box nothing requests any more. */
  !/\.pn-atlas-mark--60\b/.test(src)
    ? ok('the retired .pn-atlas-mark--60 rule is gone from the stylesheet')
    : bad('.pn-atlas-mark--60 is still declared', 'nothing requests it any more');
  /* The hydrator must honour the declared height, or the attribute geometry
     and the stylesheet disagree. */
  /data-atlas-height"\), 10\) \|\| px/.test(src)
    ? ok('the hydrator reads the declared aspect-correct height')
    : bad('the hydrator ignores data-atlas-height');

  /* (2) THE ALTERNATIVES HEADING CARRIES NO MARK. */
  const altH = /<div class="results-gallery-heading"[^>]*id="matchAlternativesHeading"[^>]*>[\s\S]{0,200}?<\/div>/.exec(src);
  if (!altH) cannot('could not isolate the alternatives heading');
  else if (/pn-atlas-slot|atlas-mark|has-atlas-mark/.test(altH[0]))
    bad('"Atlas looked at this in other ways." still carries a mark',
        'the full mark is illegible at heading scale; it was removed deliberately');
  else ok('"Atlas looked at this in other ways." carries no Atlas mark');
  /results-gallery-heading\.has-atlas-mark/.test(src)
    ? bad('the retired alternatives-heading CSS survives')
    : ok('the retired alternatives-heading CSS is gone');

  /* (3) THE MAKER-BAND LABEL CARRIES NO MARK. */
  const mkr = /const blab = aaEl\('p', 'aa-find-lab',[\s\S]{0,900}?band\.appendChild\(blab\);/.exec(src);
  if (!mkr) cannot('could not isolate the maker band label block');
  else if (/pn-atlas-slot|atlas-mark-micro|aa-find-lab-mark/.test(mkr[0]))
    bad('"What Atlas holds on <org>" still carries a mark');
  else ok('"What Atlas holds on <org>" carries no Atlas mark');
  /aa-find-lab-mark/.test(src)
    ? bad('the retired maker-band CSS survives')
    : ok('the retired maker-band CSS is gone');

  /* (4) THE GATED EVIDENCE-ROW MICRO MARK IS EXACTLY AS BEFORE. */
  {
    const p3 = /if \(row\.state === 'established' && !row\.scope && !row\.conflict\)\{[\s\S]{0,520}?\n      \}/.exec(src);
    if (!p3) cannot('could not isolate the gated evidence-row block');
    else if (!/am\.src = 'assets\/brand\/atlas-mark-micro\.svg'/.test(p3[0]))
      bad('the evidence row no longer uses the supplied micro file');
    else if (!/am\.className = 'pn-atlas-mark pn-atlas-mark--16 am-ev-atlas'/.test(p3[0]))
      bad('the evidence-row micro mark changed class');
    else if (/pn-atlas-slot|pn-am-field|pn-am-play/.test(p3[0]))
      bad('the evidence-row micro mark gained an animation hook');
    else ok('the gated evidence-row micro signature is unchanged, still three-condition gated');
    const uses = (src.match(/assets\/brand\/atlas-mark-micro\.svg/g) || []).length;
    uses === 1 ? ok('the micro file has exactly 1 consumer — the gated evidence row')
               : bad('the micro file has ' + uses + ' consumer(s), expected 1');
  }

  /* (5) ONE SOURCE COPY OF THE SUPPLIED FULL GEOMETRY. */
  {
    const t = (src.match(/id="pn-atlas-a-template"/g) || []).length;
    const v = (src.match(/viewBox="0 0 1157 1038"/g) || []).length;
    (t === 1 && v === 1)
      ? ok('exactly one source copy of the supplied full geometry')
      : bad('the supplied geometry is duplicated', t + ' template(s), ' + v + ' viewBox(es)');
  }

  /* (6) THE VISIBLE MARK IS REACHABLE WITHOUT INTERACTION. */
  /mast\.appendChild|host\.appendChild\(mast\)/.test(src)
    ? ok('the masthead is appended directly to the visible assessment host')
    : bad('could not confirm the masthead reaches the assessment host');
  /* The MAIN masthead rule, identified by its hairline — not the
     <=360px override, which sits earlier in the sheet and also starts
     `.aa-mast{`. */
  const mastCss = /\.aa-mast\{[^}]*border-top[^}]*\}/.exec(src);
  if (!mastCss) cannot('could not read the .aa-mast CSS');
  else if (/display:\s*none|visibility:\s*hidden|opacity:\s*0\b/.test(mastCss[0]))
    bad('.aa-mast is hidden by its own CSS', mastCss[0]);
  else if (!/align-items:center/.test(mastCss[0]))
    bad('.aa-mast is not centre-aligned', 'a 54px mark cannot share a baseline with a 10px label');
  else ok('.aa-mast renders on sight, centre-aligned for the lockup');
  {
    const re = /<p class="match-atlas-popover-title[\s\S]{0,8000}?match-atlas-popover-confidence"[^<]*<\/p>/g;
    let m, regions = 0, leaked = false;
    while ((m = re.exec(src)) !== null) { regions++; if (m[0].includes('aa-mast-lead')) leaked = true; }
    if (!regions) cannot('could not isolate any popover body to search');
    else if (leaked) bad('the lockup sits inside the hidden popover');
    else ok('the lockup is not inside the popover (' + regions + ' bodies searched)');
  }
  {
    const d = src.match(/<details[\s\S]*?<\/details>/g) || [];
    d.some(x => x.includes('aa-mast-lead'))
      ? bad('the lockup sits inside a <details> disclosure')
      : ok('the lockup is not inside a <details> (' + d.length + ' searched)');
  }

  /* (6b) THE MASTHEAD STACKS ON PURPOSE UNDER 360px. Incidental flex wrapping
         left the organisation wherever space-between happened to put it; under
         360px the masthead blocks so the organisation takes its own line,
         aligned to the masthead's left edge. The lockup must not shrink. */
  {
    const mq = /@media \(max-width:360px\)\{([\s\S]*?)\n  \}/.exec(src);
    if (!mq) bad('there is no <=360px masthead rule', 'long organisation names would wrap by accident');
    else {
      const b = mq[1];
      /\.aa-mast\{ display:block; \}/.test(b)
        ? ok('under 360px .aa-mast stacks deliberately (display:block)')
        : bad('the <=360px rule does not block the masthead');
      /\.aa-mast-r\{ display:block; margin-top:10px; \}/.test(b)
        ? ok('under 360px the organisation takes its own line with 10px above')
        : bad('the organisation line is not deliberately placed under 360px');
      /pn-atlas-mark--60|width:|height:/.test(b.replace(/margin-top:10px;/, ''))
        ? bad('the <=360px rule resizes something', b.trim())
        : ok('the <=360px rule resizes nothing — the lockup stays 60x54');
    }
  }

  /* (7) PHASE 1 AND THE GOVERNANCE NOTE. */
  const kept = [
    [2, (src.match(/<span class="pn-atlas-slot" data-atlas-size="24"><\/span>/g) || []).length, 'the 2 popover 24px slots'],
    [1, (src.match(/akMark\.setAttribute\('data-atlas-size', '20'\)/g) || []).length, 'the "What Atlas Knows" 20px slot'],
  ];
  let keptOk = true;
  for (const [w, g, what] of kept) if (w !== g) { bad('Phase 1 changed: ' + what); keptOk = false; }
  if (keptOk) ok('the explanatory Phase 1 placements survive unchanged');
  /no pills and no icons — except the Atlas identity lockup in the masthead/.test(src)
    ? ok('the AA-001 note names the lockup as the single brand exception')
    : bad('the AA-001 note still forbids what the masthead now does',
          'code and the rule it states about itself must agree');
  /* No container. The lockup must stay typographic. */
  const leadCss = /\.aa-mast-lead\{[^}]*\}/.exec(src);
  if (!leadCss) cannot('could not read the .aa-mast-lead CSS');
  else if (/background|border|box-shadow|border-radius/.test(leadCss[0]))
    bad('the lockup gained a container', leadCss[0]);
  else ok('the lockup carries no fill, border, radius or shadow');
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
  + 'the masthead mark is inert, the house never moves in the SVG placements, '
  + 'and the mark never claims model-level verification '
  + 'Atlas did not establish.');
process.exit(0);
