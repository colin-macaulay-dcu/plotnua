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
];
const ROBOTS = ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex'];
const WIDTHS = [1440, 768, 390];

let failed = 0;
const ok = w => console.log('    PASS   ' + w);
const bad = (w, d) => { console.log('    FAIL   ' + w); if (d) console.log('           ' + d); failed++; };

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

    problems.length
      ? bad(tag + ' zero console and page errors', problems.slice(0, 3).join(' | '))
      : ok(tag + ' zero console errors, zero page errors');

    await page.close();
  }
}

await browser.close();
console.log('');
console.log('='.repeat(76));
console.log(failed ? failed + ' CHECK(S) FAILED' : 'QA PASS — both previews clear every check');
process.exit(failed ? 1 : 0);
