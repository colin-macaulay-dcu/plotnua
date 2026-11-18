// PROVE · PlotArt Studio · founder SANDBOX mode (18 Nov 2026, proposed; wrangler.sandbox.toml). The same Worker with
// SANDBOX = "true": a banner on every page, no email, no publishing pipeline, no GitHub dispatch, and the founder's Publish
// only simulates the result so the whole artist journey can be walked. Without the flag nothing changes.
//   node test/prove-sandbox.mjs
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
import { acceptAgreement } from './agree.mjs';
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${String(d).slice(0, 300)}]` : ''}`); };
console.log('PROVE · PlotArt Studio · sandbox mode');
async function run(port, env) {
  const S = await start({ port, env });
  S.call = async (method, path, who, body) => {
    const h = { 'X-Studio': '1', 'Content-Type': 'application/json' }; if (who) h['Cf-Access-Jwt-Assertion'] = token(who);
    const r = await S.mf.dispatchFetch(S.url + path, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
    const t = await r.text(); let j = {}; try { j = JSON.parse(t); } catch { /* html */ } return { s: r.status, j, t };
  };
  return S;
}
const S = await run(8850, { SANDBOX: 'true', GITHUB_DISPATCH_TOKEN: 'test-dispatch-token-never-used', GITHUB_API: 'http://127.0.0.1:9/never' });
const studio = await S.call('GET', '/', FOUNDER), desk = await S.call('GET', '/admin', FOUNDER);
check('S1 every Studio and Review Desk page carries the SANDBOX banner', /PlotArt Studio SANDBOX/.test(studio.t) && /PlotArt Studio SANDBOX/.test(desk.t));
const ART = 'colin+artist@example.test';
const id = (await S.call('POST', '/api/admin/artists', FOUNDER, { display_name: 'Sandbox Artist', email: ART, founding: true })).j.id;
const mails = (await S.db.prepare('SELECT COUNT(*) n FROM mail_capture').first()).n;
check('S2 creating a Studio account sends no email in the sandbox', !!id && mails === 0, mails);
const pipe = await S.mf.dispatchFetch(S.url + '/api/pipeline/queue', { headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } });
check('S3 the publishing pipeline is switched off in the sandbox (even with a valid pipeline token)', pipe.status === 404);
// the whole journey through to "live", simulated
await S.call('PUT', '/api/me/profile', ART, { medium: 'painting', bio: 'A synthetic sandbox artist used only to walk the Studio journey from start to finish.' });
const wid = (await S.call('POST', '/api/artworks', ART)).j.id;
await S.call('PUT', `/api/artworks/${wid}`, ART, { title: 'Sandbox Work', medium: 'Oil', h_cm: 30, w_cm: 40, ai_involvement: 'none' });
await S.db.prepare(`INSERT INTO images (id, artist_id, artwork_id, role, r2_key, sha256, bytes, width, height, format, alt, photographer, checks, ord, created_at)
  VALUES ('isb1', ?, ?, 'main', 'orig/isb1.jpg', 'x', 1000, 2400, 1800, 'jpeg', 'A sandbox painting', 'self', '{"blocks":[],"warns":[]}', 0, '2026-11-18T10:00:00.000Z')`).bind(id, wid).run();
await acceptAgreement(S.mf, S.url, ART);
const sub = await S.call('POST', '/api/submit', ART, {});
const sid = (await S.call('GET', '/api/admin/overview', FOUNDER)).j.submissions.find(x => x.artist_id === id).id;
await S.call('POST', `/api/admin/submissions/${sid}/decision`, FOUNDER, { decision: 'approve' });
const q = (await S.call('GET', '/api/admin/overview', FOUNDER)).j.queue.find(x => x.artist_id === id);
const pub = await S.call('POST', `/api/admin/queue/${q.id}/publish`, FOUNDER, {});
const me = (await S.call('GET', '/api/me', ART)).j;
check('S4 the founder\'s Publish only simulates the result ("sandbox"), and the artist then sees "Live"', sub.s === 200 && pub.j.publish === 'sandbox' && me.status.state === 'live', JSON.stringify([sub.j, pub.j, me.status && me.status.state]));
const qrow = await S.db.prepare('SELECT detail FROM publish_queue WHERE id=?').bind(q.id).first();
check('S5 the record says nothing was published', /sandbox: simulated, nothing published/.test(qrow.detail));
await S.mf.dispose();
const P = await run(8851, {});
const ps = await P.call('GET', '/', FOUNDER);
check('S6 without the sandbox flag (production) there is no banner and the pipeline behaves as before', !/SANDBOX/.test(ps.t) && (await P.mf.dispatchFetch(P.url + '/api/pipeline/queue', { headers: { Authorization: 'Bearer ' + PIPELINE_TOKEN } })).status === 200);
await P.mf.dispose();
console.log(`\nPLOTART STUDIO SANDBOX · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
process.exit(results.every(Boolean) ? 0 : 1);
