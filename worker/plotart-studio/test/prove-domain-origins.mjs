// Domain migration R1 (26 Nov 2026): the public Workers accept plotart.ie only when EXTRA_ORIGINS names it,
// keep plotnua.ie exactly as before, refuse anything else, and put the configured gallery address in emails.
import enquiry from '../src/enquiry.js';
import { hireEnquiry } from '../src/hire-enquiry.js';
import { handle as basketHandle } from '../src/basket-public.js';
import { __test } from '../../art-space-register/src/index.js';
const { allowedOrigin } = __test;

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log('  PASS ', m); } else { fail++; console.log('  FAIL ', m); } };
const OLD = 'https://plotnua.ie', NEW = 'https://plotart.ie', EVIL = 'https://plotart.ie.evil.example';
const pre = o => new Request('https://plotart-enquiry.colin-a41.workers.dev/v1/enquiry', { method: 'OPTIONS', headers: { Origin: o } });
const acao = r => r.headers.get('Access-Control-Allow-Origin');

const before = { ORIGIN: OLD };
const after = { ORIGIN: OLD, EXTRA_ORIGINS: NEW };
for (const [name, env] of [['unchanged config', before], ['with EXTRA_ORIGINS', after]]) {
  ok(acao(await enquiry.fetch(pre(OLD), env)) === OLD, `enquiry CORS allows plotnua.ie (${name})`);
  ok(acao(await enquiry.fetch(pre(EVIL), env)) === 'null', `enquiry CORS refuses a look-alike origin (${name})`);
  ok(acao(await hireEnquiry(pre(OLD), env, OLD)) === OLD, `hire CORS allows plotnua.ie (${name})`);
}
ok(acao(await enquiry.fetch(pre(NEW), before)) === 'null', 'enquiry refuses plotart.ie until EXTRA_ORIGINS names it');
ok(acao(await enquiry.fetch(pre(NEW), after)) === NEW, 'enquiry allows plotart.ie once named');
ok(acao(await hireEnquiry(pre(NEW), before, NEW)) === 'null', 'hire refuses plotart.ie until named');
ok(acao(await hireEnquiry(pre(NEW), after, NEW)) === NEW, 'hire allows plotart.ie once named');
const post = (o, env) => hireEnquiry(new Request('https://x/v1/hire-enquiry', { method: 'POST', headers: { Origin: o }, body: '{}' }), env, o);
ok((await post(EVIL, after)).status === 403, 'hire POST from an unknown origin is refused (403)');
ok((await post(NEW, after)).status === 503, 'hire POST from plotart.ie reaches the "not open yet" switch (no other change)');

const asr = (o, env) => allowedOrigin(env, new Request('https://x/', { headers: { origin: o } }));
ok(asr(OLD, { ORIGIN: OLD }) === OLD && asr(NEW, { ORIGIN: OLD }) === null, 'applications Worker: unchanged without EXTRA_ORIGINS');
ok(asr(NEW, { ORIGIN: OLD, EXTRA_ORIGINS: NEW }) === NEW && asr(EVIL, { ORIGIN: OLD, EXTRA_ORIGINS: NEW }) === null, 'applications Worker: plotart.ie once named, look-alike refused');

// basket preview (read-only, cross-origin): answers the asking gallery address only if it is one of ours
const fakeEnv = extra => ({ GALLERY_ORIGIN: OLD, ...extra, DB: { prepare: () => ({ bind: () => ({ all: async () => ({ results: [] }), first: async () => null }), all: async () => ({ results: [] }), first: async () => null }) } });
const items = async (o, env) => {
  const req = new Request('https://checkout/api/basket/items?ids=', { headers: o ? { Origin: o } : {} });
  try { return acao(await basketHandle(req, env, new URL(req.url))); } catch (e) { return 'ERR ' + e.message; }
};
const b1 = await items(NEW, fakeEnv({}));
const b2 = await items(NEW, fakeEnv({ EXTRA_GALLERY_ORIGINS: NEW }));
const b3 = await items(EVIL, fakeEnv({ EXTRA_GALLERY_ORIGINS: NEW }));
ok(b1 === OLD, `basket preview: plotnua.ie only by default (${b1})`);
ok(b2 === NEW, `basket preview: plotart.ie once named (${b2})`);
ok(b3 === OLD, `basket preview: look-alike gets plotnua.ie, i.e. blocked by the browser (${b3})`);

console.log(`\nDOMAIN ORIGINS · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
