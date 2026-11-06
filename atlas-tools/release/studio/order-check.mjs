// PlotArt Studio · gallery-order check for deployments (31 Oct 2026; corrected 6 Nov 2026). Reads the pipeline's gallery-order
// view (positions, published gallery addresses, reserved flags; never a private note or an unpublished name) and prints only:
// whether position 01 is held by the approved artist, how many positions are filled, and a short fingerprint of the order.
//   node order-check.mjs save <file>      before the deployment: fails unless 01 is held by the approved artist
//   node order-check.mjs compare <file>   after: fails unless every position is identical and 01 is still held by them
// Founder decision 6 Nov 2026: Leah Hewson correctly holds position 01 (the earlier "01 must be empty and reserved" rule
// is withdrawn). Change POSITION_01 only with his approval.
// Needs STUDIO_URL, STUDIO_PIPELINE_TOKEN and (behind Cloudflare Access) STUDIO_ACCESS_CLIENT_ID / _SECRET.
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
const [mode, file] = process.argv.slice(2);
const POSITION_01 = 'leah-hewson';   // the published gallery that holds position 01, by founder decision
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
const held01 = !!(p01 && !p01.reserved && p01.slug === POSITION_01);
const filled = j.positions.filter(p => p.slug).length, reserved = j.positions.filter(p => p.reserved).length;
console.log(`position 01 held by the approved artist: ${held01 ? 'yes' : 'NO'} · positions recorded: ${j.positions.length} (${reserved} reserved, ${filled} with a published gallery) · order fingerprint ${fp.slice(0, 12)}`);
if (mode === 'save') { writeFileSync(file, fp); if (!held01) console.log('FAIL  position 01 is not held by the approved artist: nothing was deployed'); process.exit(held01 ? 0 : 1); }
const before = readFileSync(file, 'utf8').trim();
const ok = before === fp && held01;
console.log(ok ? 'PASS  every gallery position is identical and 01 is still held by the approved artist' : 'FAIL  the gallery order changed during the deployment, or 01 is no longer held by the approved artist');
process.exit(ok ? 0 : 1);
