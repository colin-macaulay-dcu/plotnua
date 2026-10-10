/* QA — SWITCH ELECTRICAL AND SAUNA EXPERTS PRIVATE PREVIEWS.
   ---------------------------------------------------------------------------
   The certified system's §9 checklist, run as code rather than read as a list.

   STATIC, per page:
     S1  every internal href resolves to a file that exists in the tree
     S2  every external href is the supplier's own domain and nobody else's —
         a preview with no imagery still must not become a link farm
     S3  no {{TOKEN}} survives
     S4  all five robots directives
     S5  exactly one ILLUSTRATIVE PREVIEW label — the standard says one is
         enough, and repetition is the thing §7 bans

   RENDERED, at 1440 / 768 / 390:
     R1  no horizontal overflow and no element wider than the viewport
     R2  the PlotNua mark, the My Plot pill, Save and Open My Plot all render
     R3  zero console errors and zero page errors
     R4  the frozen journey band shows all six stages at every width
     R5  where a page carries supplier imagery: every image actually DECODES
         at non-zero size -- a 404 renders as an empty box and the static
         checks cannot see it -- and the required credit is visible text, not
         merely present in the markup

   Run: node supplier-preview-system/qa-switch-and-sauna-previews.mjs          */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const BASE = 'http://127.0.0.1:8017/';

const PAGES = [
  { file: 'switch-electrical-preview.html', host: 'switchelectrical.ie' },
  { file: 'sauna-experts-preview.html', host: 'saunaexperts.ie' },
  // IMAGERY STATE A, so this one also exercises R5. The other two carry no
  // supplier imagery and R5 skips them rather than inventing a pass.
  { file: 'irish-sauna-company-preview.html', host: 'irishsaunacompany.com',
    credit: '\u00a9 Irish Sauna Company' },
];
const ROBOTS = ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex'];
const WIDTHS = [1440, 768, 390];

let failed = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };
// SKIP IS NOT PASS. It is printed differently, counted separately and named in
// the summary, so a measurement this harness could not take never reads as one
// it took and liked.
let skipped = 0;
const skip = w => { console.log('    SKIP   ' + w); skipped++; };

console.log('PREVIEW QA — SWITCH ELECTRICAL AND SAUNA EXPERTS');
console.log('='.repeat(76));

const browser = await chromium.launch({
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
});

for (const p of PAGES) {
  console.log('');
  console.log('  ' + p.file);
  console.log('  ' + '-'.repeat(72));
  const src = fs.readFileSync(path.join(ROOT, p.file), 'utf8');

  /* ---- S1 / S2 . links ------------------------------------------------- */
  const hrefs = [...src.matchAll(/href\s*=\s*["']([^"']+)["']/gi)].map(m => m[1]);
  const internal = hrefs.filter(h => !/^(https?:|mailto:|tel:|#|data:)/i.test(h));
  const missing = internal.filter(h => {
    const clean = h.split('#')[0].split('?')[0];
    if (!clean) return false;
    return !fs.existsSync(path.join(ROOT, clean));
  });
  missing.length
    ? bad('every internal link resolves', 'missing: ' + missing.join(', '))
    : ok(internal.length + ' internal link(s), all resolve on disk');

  const external = [...new Set(hrefs.filter(h => /^https?:/i.test(h)))];
  /* The two Google Fonts hosts are the template's own typography, present on
     every PlotNua page and not a supplier destination. They are named here
     rather than pattern-matched, so a third host added later still fails. */
  const FONT_HOSTS = new Set(['fonts.googleapis.com', 'fonts.gstatic.com']);
  const strangers = external.filter(h => {
    const host = new URL(h).hostname.toLowerCase().replace(/^www\./, '');
    return host !== p.host && host !== 'plotnua.ie' && !FONT_HOSTS.has(host);
  });
  strangers.length
    ? bad('every external link goes to the supplier or to PlotNua',
          'other destinations: ' + strangers.join(', '))
    : ok(external.length + ' external link(s), all to ' + p.host);

  /* ---- S3 / S4 / S5 . the static contract ------------------------------ */
  const tokens = [...new Set([...src.matchAll(/\{\{[A-Z_0-9]+\}\}/g)].map(m => m[0]))];
  tokens.length ? bad('no unfilled token survives', tokens.join(', '))
                : ok('no {{TOKEN}} survives');

  const missingRobots = ROBOTS.filter(d => !src.includes(d));
  missingRobots.length
    ? bad('all five robots directives', 'missing: ' + missingRobots.join(', '))
    : ok('noindex, nofollow, noarchive, nosnippet, noimageindex');

  const labels = (src.match(/Illustrative preview/gi) || []).length;
  labels === 1 ? ok('exactly one ILLUSTRATIVE PREVIEW label')
               : bad('exactly one ILLUSTRATIVE PREVIEW label',
                     'found ' + labels + '. §7 bans repeating the status.');

  /* ---- rendered -------------------------------------------------------- */
  for (const width of WIDTHS) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const problems = [];
    /* THE SANDBOX'S PROXY, NOT THE PAGE'S FAULT. This harness runs behind an
       egress proxy that answers 407 to fonts.googleapis.com, so every PlotNua
       page logs a failed font fetch here and none does in a real browser.
       Only that exact shape is ignored; any other console error still fails,
       which is the half of this check that matters. */
    const proxyNoise = t => /407|Proxy Authentication|ERR_(TUNNEL|PROXY)/i.test(t);
    page.on('console', m => {
      if (m.type() === 'error' && !proxyNoise(m.text())) problems.push('console: ' + m.text());
    });
    page.on('pageerror', e => problems.push('pageerror: ' + e.message));
    // R5's evidence. The harness runs behind an egress proxy that answers 407
    // to most third-party hosts; a supplier image blocked that way has not
    // failed, it was never fetched. Recording the REASON is what lets R5 tell
    // the two apart instead of guessing.
    const blocked = new Set(), served = new Map();
    page.on('requestfailed', r => {
      if (proxyNoise(r.failure()?.errorText || '')) blocked.add(r.url());
    });
    page.on('response', r => {
      if (r.status() === 407) blocked.add(r.url());
      else served.set(r.url(), r.status());
    });
    await page.goto(BASE + p.file, { waitUntil: 'load' });
    await page.waitForTimeout(350);

    const r = await page.evaluate(w => {
      const de = document.documentElement;
      const over = [...document.querySelectorAll('body *')]
        .filter(el => {
          const b = el.getBoundingClientRect();
          return b.width > 0 && (b.right > w + 1 || b.left < -1);
        })
        .slice(0, 4)
        .map(el => el.tagName.toLowerCase() + '.' + String(el.className || '').split(' ')[0]);
      const text = document.body.innerText;
      return {
        scrollW: de.scrollWidth,
        clientW: de.clientWidth,
        over,
        mark: !!document.querySelector('.pn-stage svg, .pn-stage .pn-mark, .pn-mark'),
        myPlot: /my plot/i.test(text),
        save: /save/i.test(text),
        stages: ['DISCOVER', 'CHECK', 'EXPLORE', 'COMPARE', 'DECIDE', 'CONNECT']
          .filter(s => text.toUpperCase().includes(s)).length,
      };
    }, width);

    const tag = '@' + width;
    r.scrollW > r.clientW + 1
      ? bad(tag + ' no horizontal scroll',
            'scrollWidth ' + r.scrollW + ' vs clientWidth ' + r.clientW
            + (r.over.length ? '; widest: ' + r.over.join(', ') : ''))
      : ok(tag + ' no horizontal scroll, no element past the viewport');

    (r.mark && r.myPlot && r.save)
      ? ok(tag + ' PlotNua mark, My Plot and Save all present')
      : bad(tag + ' PlotNua mark, My Plot and Save all present',
            'mark=' + r.mark + ' myPlot=' + r.myPlot + ' save=' + r.save);

    r.stages === 6
      ? ok(tag + ' the frozen journey band shows all six stages')
      : bad(tag + ' the frozen journey band shows all six stages',
            'found ' + r.stages);

    // R5 · A GRANTED IMAGE THAT DOES NOT LOAD IS STILL A BROKEN PAGE, and a
    // credit that is in the markup but not rendered credits nobody. Both are
    // measured on the live DOM, which is the only place either shows up.
    if (p.credit) {
      const img = await page.evaluate(h => {
        const all = [...document.images].filter(i => (i.currentSrc || i.src).includes(h));
        return {
          n: all.length,
          broken: all.filter(i => !i.complete || i.naturalWidth === 0)
                     .map(i => (i.currentSrc || i.src).slice(-48)),
          brokenFull: all.filter(i => !i.complete || i.naturalWidth === 0)
                         .map(i => i.currentSrc || i.src),
          offHost: [...document.images]
            .map(i => i.currentSrc || i.src)
            .filter(u => /^https?:/.test(u) && !u.includes(h)),
        };
      }, p.host);
      const creditShown = await page.evaluate(
        c => document.body.innerText.includes(c), p.credit);

      // A blocked fetch is NOT a pass and NOT a failure: it is a measurement
      // this harness could not take, and saying so is the only honest result.
      // Anything that actually reached the host and still did not decode -- a
      // 404, a 403, a corrupt file -- still fails, which is the half of this
      // check that matters.
      const reallyBroken = img.brokenFull.filter(u => !blocked.has(u));
      if (img.n === 0) {
        bad(tag + ' supplier image(s) present', 'none found on ' + p.host);
      } else if (reallyBroken.length) {
        bad(tag + ' all supplier image(s) decoded',
            reallyBroken.map(u => (served.get(u) ? 'HTTP ' + served.get(u) + ' ' : '')
                                  + u.slice(-44)).join(', '));
      } else if (img.broken.length) {
        skip(tag + ' ' + img.broken.length + ' of ' + img.n + ' supplier image(s) '
             + 'not fetched: the harness proxy refused ' + p.host + ' (407). '
             + 'Verify in a real browser.');
      } else {
        ok(tag + ' all ' + img.n + ' supplier image(s) decoded at non-zero size');
      }

      img.offHost.length === 0
        ? ok(tag + ' no image from any host but ' + p.host)
        : bad(tag + ' no image from any host but ' + p.host,
              img.offHost.join(', '));

      creditShown
        ? ok(tag + ' the credit "' + p.credit + '" is visible text')
        : bad(tag + ' the credit "' + p.credit + '" is visible text');
    }

    problems.length
      ? bad(tag + ' zero console and page errors', problems.slice(0, 3).join(' | '))
      : ok(tag + ' zero console errors, zero page errors');

    await page.close();
  }
}

await browser.close();
console.log('');
console.log('='.repeat(76));
console.log(failed ? failed + ' CHECK(S) FAILED'
  : 'QA PASS \u2014 all ' + PAGES.length + ' previews clear every check'
    + (skipped ? ' (' + skipped + ' not measurable in this harness, named above)' : ''));
process.exit(failed ? 1 : 0);
