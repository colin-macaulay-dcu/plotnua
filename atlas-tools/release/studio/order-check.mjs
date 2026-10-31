// PlotArt Studio · gallery-order check for deployments (31 Oct 2026). Reads the pipeline's gallery-order view (positions,
// published gallery addresses, reserved flags; never a private note or an unpublished name) and prints only:
// whether position 01 is reserved, how many positions are filled, and a short fingerprint of the order.
//   node order-check.mjs save <file>      before the deployment
//   node order-check.mjs compare <file>   after: fails unless the order is identical and 01 is still reserved
// Needs STUDIO_URL, STUDIO_PIPELINE_TOKEN and (behind Cloudflare Access) STUDIO_ACCESS_CLIENT_ID / _SECRET.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const [mode, file] = process.argv.slice(2);
const E = process.env;
if (!['save', 'compare'].includes(mode) || !file) { console.log('usage: node order-check.mjs save|compare <file>'); process.exit(2); }
if (!E.STUDIO_URL || !E.STUDIO_PIPELINE_TOKEN) { console.log('REFUSED: the pipeline secrets are not available'); process.exit(1); }
const h = { Authorization: 'Bearer ' + E.STUDIO_PIPELINE_TOKEN, 'User-Agent': 'PlotArt-studio-deploy/1.0 (+https://plotnua.ie)' };
if (E.STUDIO_ACCESS_CLIENT_ID && E.STUDIO_ACCESS_CLIENT_SECRET) { h['CF-Access-Client-Id'] = E.STUDIO_ACCESS_CLIENT_ID; h['CF-Access-Client-Secret'] = E.STUDIO_ACCESS_CLIENT_SECRET; }
let j;
for (let i = 1; i <= 6; i++) {               // a freshly deployed Worker can take a few seconds everywhere
  try { const r = await fetch(E.STUDIO_URL.replace(/\/$/, '') + '/api/pipeline/gallery-order', { headers: h }); if (r.ok) { j = await r.json(); break; } console.log(`attempt ${i}: HTTP ${r.status}`); }
  catch (e) { console.log(`attempt ${i}: no response`); }
  await new Promise(r => setTimeout(r, 5000));
}
if (!j || !Array.isArray(j.positions)) { console.log('FAIL  the Studio did not return the gallery order'); process.exit(1); }
for (const p of j.positions) if (Object.keys(p).some(k => !['position', 'slug', 'reserved'].includes(k))) { console.log('FAIL  the gallery order carries an unexpected field'); process.exit(1); }
const state = JSON.stringify({ positions: j.positions.map(p => [p.position, p.slug || null, !!p.reserved]), extra: j.extra || [] });
const fp = createHash('sha256').update(state).digest('hex');
const p01 = j.positions.find(p => p.position === 1);
const reserved01 = !!(p01 && p01.reserved && !p01.slug);
const filled = j.positions.filter(p => p.slug).length;
console.log(`position 01 reserved: ${reserved01 ? 'yes' : 'NO'} · positions with a published gallery: ${filled} · order fingerprint ${fp.slice(0, 12)}`);
if (mode === 'save') { writeFileSync(file, fp); process.exit(reserved01 ? 0 : 1); }
const before = readFileSync(file, 'utf8').trim();
const ok = before === fp && reserved01;
console.log(ok ? 'PASS  the gallery order is unchanged and 01 is still reserved' : 'FAIL  the gallery order changed during the deployment, or 01 is not reserved');
process.exit(ok ? 0 : 1);
