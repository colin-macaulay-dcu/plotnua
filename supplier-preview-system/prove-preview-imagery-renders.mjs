#!/usr/bin/env node
/**
 * PROVE SUPPLIER PREVIEW IMAGERY ACTUALLY RENDERS
 * ===============================================
 * Written on 11 October 2026 after an instrument failure, not a page failure.
 *
 * The BIOBUILDS preview hot-links its authorised photographs from
 * www.biobuilds.com. The build sandbox has no egress to that host, so every
 * screenshot taken there showed empty image frames. A failed <img> load fires
 * an `error` event on the element and NOT a `pageerror`, so the existing QA,
 * which only watched for page errors and text, reported a clean pass over a
 * page whose photographs had not loaded. The founder caught it in the
 * screenshots. That is exactly backwards: the instrument should have caught
 * it, and the founder should never have had to.
 *
 * This proof closes that hole. For every <img> on the page it asserts the
 * three things that actually distinguish a rendered photograph from an empty
 * frame:
 *
 *     complete === true, naturalWidth > 0, naturalHeight > 0
 *
 * and, where a credit overlay governs the image, that the overlay is still
 * rendered and still carries the required text.
 *
 * THE CRITICAL RULE. If NO remote image loads at all, that is overwhelmingly
 * an environment with no egress rather than a page where every single asset
 * has rotted. Reporting that as a page defect would be as wrong as reporting
 * it as a pass. The proof exits 2 with INSTRUMENT UNAVAILABLE, says so in
 * plain words, and names the host that could not be reached. Exit 2 is
 * neither a pass nor a failure: it means "not measured here, measure it
 * against the deployed URL in a browser with real network access."
 *
 *   node supplier-preview-system/prove-preview-imagery-renders.mjs \
 *        --page biobuilds-preview.html [--credit "© BIOBUILDS"]
 *   node ... --url https://plotnua.ie/biobuilds-preview.html
 *
 * Exit 0 = every image rendered. 1 = a real defect. 2 = not measurable here.
 */
import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);

function arg(name, dflt) {
  const i = process.argv.indexOf('--' + name);
  return i === -1 ? dflt : process.argv[i + 1];
}

const pageArg = arg('page', null);
const urlArg = arg('url', null);
const credit = arg('credit', null);

if (!pageArg && !urlArg) {
  console.error('REFUSE: pass --page <file> or --url <deployed url>.');
  process.exit(1);
}

let target;
if (urlArg) {
  target = urlArg;
} else {
  const p = resolve(ROOT, pageArg);
  if (!existsSync(p)) {
    console.error(`REFUSE: ${pageArg} does not exist. This is an instrument ` +
                  `failure, not a page failure: do not record it as a pass.`);
    process.exit(1);
  }
  // A page that carries no <img> at all would let every assertion below pass
  // vacuously. Refuse rather than report a meaningless 0 of 0.
  if (!/<img\b/i.test(readFileSync(p, 'utf8'))) {
    console.error('REFUSE: the page carries no <img> element, so this proof ' +
                  'would pass vacuously.');
    process.exit(1);
  }
  target = pathToFileURL(p).href;
}

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.error('INSTRUMENT UNAVAILABLE: Playwright is not importable from ' +
                'this working directory. Run from the directory that holds ' +
                'node_modules. Not a pass and not a failure.');
  process.exit(2);
}

const WIDTHS = [
  { label: 'desktop', width: 1440, height: 1000 },
  { label: 'mobile', width: 390, height: 844 },
];

const browser = await chromium.launch();
let defects = 0;
let measuredAnywhere = false;
const hosts = new Set();
const report = [];

for (const vp of WIDTHS) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
  });
  const page = await ctx.newPage();

  // Record the transport outcome independently of the DOM, so a network
  // refusal can be told apart from a decode failure.
  const failedRequests = [];
  page.on('requestfailed', r => {
    if (r.resourceType() === 'image') {
      failedRequests.push(`${r.failure()?.errorText || 'failed'} ${r.url()}`);
    }
  });

  await page.goto(target, { waitUntil: 'load' });
  // Give lazy and decoding images a fair chance, then settle on the real
  // completion state rather than a snapshot mid-decode.
  await page.evaluate(async () => {
    for (const i of document.querySelectorAll('img')) {
      i.loading = 'eager';
      if (i.getAttribute('data-full') && !i.src) i.src = i.getAttribute('data-full');
    }
    await Promise.all([...document.querySelectorAll('img')].map(i =>
      i.complete ? null : new Promise(r => {
        i.addEventListener('load', r, { once: true });
        i.addEventListener('error', r, { once: true });
        setTimeout(r, 15000);
      })));
  });
  await page.waitForTimeout(500);

  const shot = await page.evaluate((creditText) => {
    const imgs = [...document.querySelectorAll('img')];
    const overlay = document.querySelector('.pn-image-credit');
    const ob = overlay ? overlay.getBoundingClientRect() : null;
    return {
      images: imgs.map(i => ({
        src: i.currentSrc || i.src,
        remote: /^https?:/i.test(i.currentSrc || i.src),
        complete: i.complete,
        nw: i.naturalWidth,
        nh: i.naturalHeight,
      })),
      overlayText: overlay ? overlay.textContent.trim() : null,
      overlayVisible: ob
        ? ob.width > 0 && ob.height > 0 &&
          getComputedStyle(overlay).visibility !== 'hidden' &&
          getComputedStyle(overlay).display !== 'none'
        : false,
      creditPresent: creditText
        ? (document.body.innerText + ' ' + (overlay ? overlay.textContent : ''))
            .includes(creditText)
        : null,
      overflow: document.documentElement.scrollWidth -
                document.documentElement.clientWidth,
    };
  }, credit);

  for (const i of shot.images) {
    try { if (i.remote) hosts.add(new URL(i.src).host); } catch { /* ignore */ }
  }

  const remote = shot.images.filter(i => i.remote);
  const rendered = shot.images.filter(i => i.complete && i.nw > 0 && i.nh > 0);
  const broken = shot.images.filter(i => !(i.complete && i.nw > 0 && i.nh > 0));
  if (remote.length && rendered.some(i => i.remote)) measuredAnywhere = true;

  report.push({ vp, shot, remote, rendered, broken, failedRequests });
  await ctx.close();
}
await browser.close();

console.log('\nSUPPLIER PREVIEW IMAGERY · RENDER PROOF');
console.log(`target: ${target}\n`);

const anyRemote = report.some(r => r.remote.length > 0);
if (anyRemote && !measuredAnywhere) {
  console.log('  INSTRUMENT UNAVAILABLE');
  console.log(`  Not one remote image loaded, at any width. Hosts involved: ` +
              `${[...hosts].join(', ') || 'unknown'}.`);
  console.log('  That pattern means this environment has no network route to ' +
              'the image host,');
  console.log('  not that the page is broken. This is NOT a pass and NOT a ' +
              'failure.');
  console.log('  Measure it against the deployed URL in a browser with real ' +
              'network access');
  console.log('  before drawing any conclusion about the page, and never ' +
              'publish a screenshot');
  console.log('  taken here as evidence that the photographs render.');
  const sample = report[0].failedRequests.slice(0, 3);
  if (sample.length) {
    console.log('\n  sample transport failures:');
    for (const s of sample) console.log(`    ${s}`);
  }
  console.log('');
  process.exit(2);
}

for (const { vp, shot, remote, rendered, broken } of report) {
  const okImgs = broken.length === 0;
  const okOverlay = credit === null ||
                    (shot.overlayVisible && shot.creditPresent);
  const okFlow = shot.overflow <= 0;
  if (!okImgs || !okOverlay || !okFlow) defects++;

  console.log(`  ${vp.label} (${vp.width}px)`);
  console.log(`    ${okImgs ? 'PASS' : 'FAIL'}  ${rendered.length} of ` +
              `${shot.images.length} images rendered ` +
              `(${remote.length} remote)`);
  for (const b of broken) {
    console.log(`          BROKEN  complete=${b.complete} ` +
                `natural=${b.nw}x${b.nh}  ${b.src.slice(-58)}`);
  }
  if (credit !== null) {
    console.log(`    ${okOverlay ? 'PASS' : 'FAIL'}  credit overlay visible ` +
                `and carries ${JSON.stringify(credit)} ` +
                `[${JSON.stringify(shot.overlayText)}]`);
  }
  console.log(`    ${okFlow ? 'PASS' : 'FAIL'}  no horizontal overflow ` +
              `(${shot.overflow}px)`);
}

console.log(defects
  ? `\n${defects} width(s) failed — the imagery is genuinely broken.\n`
  : '\nEvery image rendered at every width, with real pixel dimensions.\n');
process.exit(defects ? 1 : 0);
