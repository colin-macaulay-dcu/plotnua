/* PROVE THE ATLAS HYDRATION BOOTSTRAP SURVIVES SOURCE ORDER.

   THE GAP THIS CLOSES. prove-atlas-a.mjs reads the page as TEXT. It verified
   that the bootstrap existed, cloned the template, stripped the ids, tagged the
   fields and matched the CSS -- all true, all passing, while not one hydrated
   Atlas mark rendered in a browser. The bootstrap's first act was

       var tpl = document.getElementById("pn-atlas-a-template");
       if (!tpl) return;

   and the template sits AFTER the script, so at execution time it was null, the
   function returned on its second line, window.pnAtlasHydrate was never
   assigned, and every `if (window.pnAtlasHydrate)` call silently did nothing.

   A proof that only reads source cannot catch that. So this one EXECUTES the
   shipped bootstrap, lifted verbatim out of your-plot.html, against a minimal
   DOM that models the one thing that matters: getElementById returns null until
   the parser has reached the template.

   HONEST ABOUT WHAT THIS IS. The DOM here is a purpose-built shim, not a
   browser and not jsdom. It models exactly four behaviours -- element lookup by
   id, a template's .content, class and attribute handling, and a
   DOMContentLoaded event -- because those are what the bug turned on. The
   control case below is what makes that trustworthy: the OLD bootstrap is run
   through the SAME harness and must FAIL. A harness that cannot reproduce the
   bug proves nothing about the fix.

   Run: node atlas-tools/prove-atlas-hydration-order.mjs                      */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PAGE = path.join(HERE, '..', 'your-plot.html');

let failed = 0, confused = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };
const cannot = (w, d) => { console.log('    ERROR  ' + w); if (d) console.log('           ' + d); confused++; };

console.log('ATLAS HYDRATION — RUNTIME ORDER');
console.log('='.repeat(76));
const src = fs.readFileSync(PAGE, 'utf8');

/* ---- lift the shipped bootstrap, verbatim ------------------------------- */
const BOOT_RE = /\/\* ATLAS A HYDRATION[\s\S]*?\n\}\)\(\);/;
const boot = (BOOT_RE.exec(src) || [''])[0];
if (!boot) { cannot('could not lift the hydration bootstrap from the page'); process.exit(2); }

/* The old, broken bootstrap, reconstructed by putting the install-time capture
   back. This is the control: the harness must catch it. */
const brokenBoot = boot
  .replace(/  var DELAYS = /, '  var tpl0 = document.getElementById("pn-atlas-a-template");\n  if (!tpl0) return;\n  var DELAYS = ')
  .replace(/    var tpl = template\(\);\n[\s\S]*?if \(!tpl\) return;\n/, '    var tpl = tpl0;\n');

/* ---- a minimal DOM, modelling parse order ------------------------------- */
function makeDom() {
  const ids = Object.create(null);
  let listeners = [];
  const el = (tag, attrs = {}) => {
    const e = {
      tagName: tag, children: [], attrs: { ...attrs }, classes: new Set(), style: {},
      appendChild(c) { this.children.push(c); return c; },
      setAttribute(k, v) { this.attrs[k] = String(v); },
      getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
      removeAttribute(k) { delete this.attrs[k]; },
      querySelector(sel) {
        const want = sel.replace('#', '');
        const walk = n => {
          for (const c of n.children) {
            if (c.attrs.id === want) return c;
            const d = walk(c); if (d) return d;
          }
          return null;
        };
        return walk(this);
      },
      cloneNode() {
        const c = el(this.tagName, { ...this.attrs });
        c.classes = new Set(this.classes);
        for (const k of this.children) c.children.push(k.cloneNode());
        return c;
      },
    };
    e.classList = {
      add: (...cs) => cs.forEach(c => e.classes.add(c)),
      remove: c => e.classes.delete(c),
      contains: c => e.classes.has(c),
    };
    e.style.setProperty = (k, v) => { e.style[k] = v; };
    return e;
  };

  /* the template and its artwork, NOT yet registered */
  const house = el('g', { id: 'atlas-house' });
  const dark = el('g', { id: 'atlas-dark-field' });
  const sage = el('g', { id: 'atlas-sage-field' });
  const svg = el('svg', { viewBox: '0 0 1157 1038' });
  svg.appendChild(dark); svg.appendChild(sage); svg.appendChild(house);
  const tplEl = el('template', { id: 'pn-atlas-a-template' });
  tplEl.content = { firstElementChild: svg };

  /* the masthead slot, present from the start (it is built by JS above the
     bootstrap in the real page, and by hand here) */
  const slot = el('span', { 'data-atlas-size': '60', 'data-atlas-height': '54' });
  slot.classes.add('pn-atlas-slot');
  const slots = [slot];

  const document_ = {
    readyState: 'loading',
    getElementById: id => ids[id] || null,
    querySelectorAll: () => slots,
    addEventListener: (ev, fn) => { if (ev === 'DOMContentLoaded') listeners.push(fn); },
  };
  return {
    document: document_, slot, tplEl, house,
    /* the parser reaches the template */
    parseTemplate() { ids['pn-atlas-a-template'] = tplEl; },
    fireReady() { document_.readyState = 'interactive'; listeners.forEach(f => f()); },
    listenerCount: () => listeners.length,
  };
}

function run(code, dom, { parseBeforeScript = false } = {}) {
  if (parseBeforeScript) dom.parseTemplate();
  const g = {
    document: dom.document,
    window: {},
    requestAnimationFrame: fn => fn(),
  };
  g.window.document = dom.document;
  // eslint-disable-next-line no-new-func
  new Function('document', 'window', 'requestAnimationFrame', code)
    (g.document, g.window, g.requestAnimationFrame);
  return g.window;
}

/* ---- 1 . THE CONTROL. The old bootstrap must FAIL in this harness. ------ */
console.log('');
console.log('  THE HARNESS CATCHES THE REAL BUG (control)');
console.log('  ' + '-'.repeat(72));
{
  const dom = makeDom();                 // template NOT parsed when script runs
  let win;
  try { win = run(brokenBoot, dom); } catch (e) { cannot('control bootstrap threw: ' + e.message); }
  if (win) {
    typeof win.pnAtlasHydrate === 'undefined'
      ? ok('the OLD bootstrap never installs pnAtlasHydrate — the bug is reproduced')
      : bad('the control did not reproduce the bug', 'this harness cannot be trusted');
    dom.parseTemplate(); dom.fireReady();
    dom.slot.children.length === 0
      ? ok('the OLD bootstrap leaves the 60x54 slot EMPTY even after DOMContentLoaded')
      : bad('the control filled the slot', 'the harness is not modelling the failure');
  }
}

/* ---- 2 . THE FIX, in source order: script first, template later. -------- */
console.log('');
console.log('  THE SHIPPED BOOTSTRAP, RUN IN REAL SOURCE ORDER');
console.log('  ' + '-'.repeat(72));
{
  const dom = makeDom();
  let win;
  try { win = run(boot, dom); } catch (e) { cannot('bootstrap threw: ' + e.message); }
  if (win) {
    typeof win.pnAtlasHydrate === 'function'
      ? ok('(2) pnAtlasHydrate IS installed even though the template is not parsed yet')
      : bad('(2) pnAtlasHydrate is not installed', 'the ordering bug is still present');
    dom.listenerCount() === 1
      ? ok('(1) the DOMContentLoaded listener IS registered — the bootstrap cannot return permanently')
      : bad('(1) no DOMContentLoaded listener was registered');

    /* A hydrate call BEFORE the template exists must be a no-op that does not
       poison the slot. */
    try { win.pnAtlasHydrate(); } catch (e) { bad('early hydrate threw: ' + e.message); }
    dom.slot.children.length === 0 && dom.slot.getAttribute('data-atlas-done') === null
      ? ok('an early hydrate is a harmless no-op — the slot is NOT marked done')
      : bad('an early hydrate poisoned the slot', 'a later pass could never fill it');

    /* Now the parser reaches the template and DOMContentLoaded fires. */
    dom.parseTemplate();
    dom.fireReady();
    const kid = dom.slot.children[0];
    kid
      ? ok('(3) DOMContentLoaded hydration resolves the template and fills the slot')
      : bad('(3) the slot is still empty after DOMContentLoaded');
    if (kid) {
      kid.tagName === 'svg' ? ok('the 60x54 masthead slot received an <svg>')
                            : bad('the slot received a ' + kid.tagName + ', not an svg');
      (kid.getAttribute('width') === '60' && kid.getAttribute('height') === '54')
        ? ok('the SVG is sized 60 x 54 — aspect-correct, from data-atlas-height')
        : bad('the SVG is ' + kid.getAttribute('width') + ' x ' + kid.getAttribute('height'));
      kid.classes.has('pn-atlas-mark--60')
        ? ok('the SVG carries .pn-atlas-mark--60') : bad('the SVG has no --60 class');
      kid.classes.has('pn-am-play')
        ? ok('the entrance settle is armed (.pn-am-play)') : bad('.pn-am-play was never added');
      const groups = kid.children;
      const dark = groups.find(g => g.classes.has('pn-am-dark'));
      const sage = groups.find(g => g.classes.has('pn-am-sage'));
      (dark && sage) ? ok('both fields are distinguishable: .pn-am-dark and .pn-am-sage')
                     : bad('the two fields were not distinguished');
      const housey = groups.find(g => !g.classes.has('pn-am-field'));
      housey && housey.classes.size === 0
        ? ok('the house carries NO class — no selector can reach it')
        : bad('the house gained a class', housey ? [...housey.classes].join(' ') : '(house not found)');
      groups.every(g => g.getAttribute('id') === null)
        ? ok('every contract id was stripped — ids stay unique in the page')
        : bad('an id survived the clone');
      dom.slot.getAttribute('data-atlas-done') === '1'
        ? ok('the slot is marked done, so it is not filled twice')
        : bad('the slot was not marked done');
    }
  }
}

/* ---- 3 . LOCAL HYDRATION AFTER THE LAZY REPAINT ------------------------- */
console.log('');
console.log('  LOCAL HYDRATION, AS aaRenderAssessment() CALLS IT');
console.log('  ' + '-'.repeat(72));
{
  const dom = makeDom();
  let win;
  try { win = run(boot, dom); } catch (e) { cannot('bootstrap threw: ' + e.message); }
  if (win) {
    dom.parseTemplate();          // document fully parsed, as at repaint time
    dom.document.readyState = 'complete';
    /* aaRenderAssessment() empties its host and rebuilds, then calls
       pnAtlasHydrate(subtree). Model a FRESH slot, as a repaint produces. */
    const fresh = { ...dom.slot, children: [], attrs: { 'data-atlas-size': '60', 'data-atlas-height': '54' } };
    fresh.classes = new Set(['pn-atlas-slot']);
    fresh.classList = { add: c => fresh.classes.add(c), remove: c => fresh.classes.delete(c), contains: c => fresh.classes.has(c) };
    fresh.getAttribute = k => (k in fresh.attrs ? fresh.attrs[k] : null);
    fresh.setAttribute = (k, v) => { fresh.attrs[k] = String(v); };
    fresh.appendChild = c => { fresh.children.push(c); return c; };
    dom.document.querySelectorAll = () => [fresh];
    try { win.pnAtlasHydrate({ querySelectorAll: () => [fresh] }); }
    catch (e) { bad('local hydrate threw: ' + e.message); }
    fresh.children.length === 1 && fresh.children[0].tagName === 'svg'
      ? ok('(4) local hydration after a repaint resolves the template and fills the fresh slot')
      : bad('(4) local hydration did not fill the repainted slot');
  }
}

/* ---- 4 . AND THE STATIC GUARANTEE -------------------------------------- */
console.log('');
console.log('  SOURCE-LEVEL GUARANTEES');
console.log('  ' + '-'.repeat(72));
{
  const head = boot.split('window.pnAtlasHydrate = function')[0].replace(/\/\*[\s\S]*?\*\//g, '');
  const topReturn = head.split('\n').some(l => /^  return\b/.test(l));
  topReturn ? bad('a top-level return still precedes the pnAtlasHydrate install')
            : ok('nothing can return before pnAtlasHydrate is installed');
  /function template\(\)\{/.test(boot)
    ? ok('the template is resolved through a function, at hydration time')
    : bad('the template is not resolved lazily');
  /if \(!tpl\) return;/.test(boot) && !/data-atlas-done", "1"\);[\s\S]{0,40}if \(!tpl\)/.test(boot)
    ? ok('a missing template returns BEFORE the slot is marked done')
    : bad('a missing template may mark the slot done and strand it');
  const tplIdx = src.indexOf('<template id="pn-atlas-a-template"');
  const bootIdx = src.indexOf('/* ATLAS A HYDRATION');
  console.log('           (for the record: bootstrap at byte ' + bootIdx
    + ', template at byte ' + tplIdx + ' — script still precedes template, and that is now safe)');
  tplIdx > bootIdx
    ? ok('the fix is proved in the ACTUAL shipped order, not a rearranged one')
    : ok('the template now precedes the script; the lazy lookup makes order irrelevant either way');
}

console.log('');
console.log('='.repeat(76));
if (confused) { console.log('NOT ESTABLISHED — ' + confused + ' check(s) could not run.'); process.exit(2); }
if (failed) { console.log('FAILED — ' + failed + ' check(s).'); process.exit(1); }
console.log('HYDRATION ORDER VERIFIED — the bootstrap installs unconditionally, resolves the '
  + 'template when it hydrates, and fills the 60x54 masthead slot in the real source order. '
  + 'The old bootstrap fails this same harness.');
process.exit(0);
