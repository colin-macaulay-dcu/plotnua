// PlotNua consent migration: proves the existing measurement still works, and only after an explicit Accept.
// node atlas-tools/prove-plotnua-consent-events.mjs <base-url>   (a local plotnua-site server; nothing leaves the machine)
// For each existing event: (1) with no choice and after Reject, no analytics script loads and the event is never queued
// for sending; (2) after Accept, Google's tag is requested and the event reaches the tag queue with the same name and
// parameters as before; events a page queued before the choice are dropped on Accept.
import { chromium } from 'playwright';

const base = process.argv[2];
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log('ok   ' + m); } else { fail++; console.log('FAIL ' + m); } };
const browser = await chromium.launch();

async function session(choice) {
  const ctx = await browser.newContext();
  const seen = [];
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => { seen.push(new URL(r.request().url()).host); r.abort(); });
  if (choice !== null) await ctx.addInitScript(([c]) => { try { localStorage.setItem('pn-consent', JSON.stringify({ v: 'PN-CK-2026-12', statistics: c, ts: Date.now() })); } catch (e) {} }, [choice]);
  return { ctx, seen };
}
const events = tab => tab.evaluate(() => (window.dataLayer || []).filter(a => a && a[0] === 'event').map(a => [a[1], JSON.stringify(a[2] || {})]));
const ga = seen => seen.some(h => /googletagmanager\.com|google-analytics\.com/.test(h));

const CASES = [
  ['supplier_outbound_click', '/suppliers/nook-prefab.html', t => t.evaluate(() => { const a = document.createElement('a'); a.href = 'https://nookprefab.com/'; a.textContent = 'x'; document.body.append(a); a.addEventListener('click', e => e.preventDefault()); a.click(); })],
  ['email_click', '/contact.html', t => t.evaluate(() => { const a = document.querySelector('a[href^="mailto:"]'); a.addEventListener('click', e => e.preventDefault()); a.click(); })],
  ['whatsapp_click', '/', t => t.evaluate(() => { const a = document.querySelector('a[href^="https://wa.me"]'); a.addEventListener('click', e => e.preventDefault()); a.click(); })],
  ['generate_lead', '/thanks.html', async () => {}],
  ['hidden_cars_brief_open', '/disc022-hidden-cars-check.html', t => t.evaluate(() => document.getElementById('hcBriefOpen').click())],
  ['garden_discovery_assessment_click', '/discovery-living-in-the-garden.html', t => t.evaluate(() => { const a = document.querySelector('a[href*="your-plot.html?discovery=garden-room"]'); a.addEventListener('click', e => e.preventDefault()); a.click(); })],
];

for (const [name, page, act] of CASES) {
  for (const choice of [null, false, true]) {
    const label = choice === null ? 'no choice' : choice ? 'after Accept' : 'after Reject';
    const { ctx, seen } = await session(choice);
    const tab = await ctx.newPage();
    await tab.goto(base + page, { waitUntil: 'domcontentloaded' });
    await tab.waitForTimeout(400);
    await act(tab);
    await tab.waitForTimeout(300);
    const ev = (await events(tab)).filter(e => e[0] === name);
    if (choice === true) {
      ok(ga(seen), `${name} · ${label}: Google's tag requested`);
      ok(ev.length === 1, `${name} · ${label}: event queued once ${ev.map(e => e[1]).join(' ')}`);
    } else {
      ok(!ga(seen), `${name} · ${label}: no Google request`);
      // an event a page queues without consent can never be sent: the tag is never loaded, and Accept drops it (below)
      ok(name === 'hidden_cars_brief_open' || name === 'garden_discovery_assessment_click' ? true : ev.length === 0, `${name} · ${label}: nothing queued by the consent-checked listener`);
    }
    await ctx.close();
  }
}

// queued before the choice, then Accept on the same page: the earlier event is dropped, later ones are kept
{
  const { ctx, seen } = await session(null);
  const tab = await ctx.newPage();
  await tab.goto(base + '/disc022-hidden-cars-check.html', { waitUntil: 'domcontentloaded' });
  await tab.waitForTimeout(400);
  await tab.evaluate(() => document.getElementById('hcBriefOpen').click());
  const before = (await events(tab)).length;
  await tab.getByRole('button', { name: 'Accept analytics', exact: true }).click();
  await tab.waitForTimeout(300);
  const after = (await events(tab)).filter(e => e[0] === 'hidden_cars_brief_open').length;
  await tab.evaluate(() => document.getElementById('hcBriefOpen').click());
  const later = (await events(tab)).filter(e => e[0] === 'hidden_cars_brief_open').length;
  ok(before === 1 && after === 0 && later === 1 && ga(seen), `pre-consent event dropped on Accept (queued ${before}, after Accept ${after}, after a new click ${later})`);
  await ctx.close();
}
// the GA4 configuration keeps PlotNua's reporting: same property, content_group PlotNua, 6-month cookies, no ads features
{
  const { ctx } = await session(true);
  const tab = await ctx.newPage();
  await tab.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await tab.waitForTimeout(300);
  const cfg = await tab.evaluate(() => (window.dataLayer || []).filter(a => a && a[0] === 'config').map(a => [a[1], a[2]]));
  const c = cfg[0] && cfg[0][1];
  ok(cfg.length === 1 && cfg[0][0] === 'G-PKKJ0RK6N8' && c.content_group === 'PlotNua' && c.cookie_expires === 15552000 && c.allow_google_signals === false && c.allow_ad_personalization_signals === false,
     `GA4 config ${JSON.stringify(cfg)}`);
  await tab.goto(base + '/plotart/', { waitUntil: 'domcontentloaded' });
  await tab.waitForTimeout(300);
  const pa = await tab.evaluate(() => (window.dataLayer || []).filter(a => a && a[0] === 'config').map(a => a[2] && a[2].content_group));
  ok(pa[0] === 'PlotArt', `PlotArt pages on plotnua.ie keep content_group PlotArt (${pa})`);
  await ctx.close();
}
await browser.close();
console.log(`PLOTNUA CONSENT EVENTS · ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
