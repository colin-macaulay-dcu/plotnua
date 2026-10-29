// PlotArt Studio · local harness (Phase 2). Runs the real Worker in Miniflare (workerd) with a LOCAL D1 database and a
// LOCAL R2 bucket, and a TEST key pair standing in for Cloudflare Access. Nothing here touches Cloudflare.
//   import { start, token } from './local.mjs'
//   node test/local.mjs --serve 8787     (a local Studio for screenshots and manual testing)
import { createRequire } from 'node:module';
import { generateKeyPairSync, createSign, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const require = createRequire(process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json');
const { Miniflare } = require('miniflare');

const HERE = fileURLToPath(new URL('..', import.meta.url));
export const TEAM = 'https://plotnua-test.cloudflareaccess.com', AUD = 'test-aud-plotart-studio';
export const FOUNDER = 'founder@plotnua.invalid', PIPELINE_TOKEN = 'test-pipeline-' + randomUUID();
const { publicKey, privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const KID = 'test-kid-1';
const jwk = { ...publicKey.export({ format: 'jwk' }), kid: KID, alg: 'RS256', use: 'sig' };
const b64u = b => Buffer.from(b).toString('base64url');

export function token(email, { aud = AUD, iss = TEAM, exp = 3600, kid = KID, key = privateKey } = {}) {
  const t = Math.floor(Date.now() / 1000);
  const h = b64u(JSON.stringify({ alg: 'RS256', kid, typ: 'JWT' })), p = b64u(JSON.stringify({ aud: [aud], iss, email, sub: randomUUID(), iat: t, exp: t + exp, type: 'app' }));
  const s = createSign('RSA-SHA256'); s.update(h + '.' + p);
  return `${h}.${p}.${b64u(s.sign(key))}`;
}
export const otherKey = generateKeyPairSync('rsa', { modulusLength: 2048 }).privateKey;

export async function start({ port, env = {} } = {}) {
  const mf = new Miniflare({
    modules: true, scriptPath: HERE + 'src/index.js', modulesRoot: HERE, modulesRules: [{ type: 'ESModule', include: ['**/*.js'] }],
    compatibilityDate: '2026-08-01', d1Databases: ['DB'], r2Buckets: ['IMAGES'],
    bindings: { ENVIRONMENT: 'local', ACCESS_TEAM_DOMAIN: TEAM, ACCESS_AUD: AUD, ACCESS_JWKS_JSON: JSON.stringify({ keys: [jwk] }),
      FOUNDER_EMAILS: FOUNDER, PIPELINE_TOKEN, INSTANT_AUTOPUBLISH: 'false', ...env },
    ...(port ? { port, host: '127.0.0.1' } : {}),
  });
  const db = await mf.getD1Database('DB');
  for (const stmt of readFileSync(HERE + 'schema.sql', 'utf8').replace(/--[^\n]*/g, '').split(';').map(s => s.trim()).filter(Boolean)) await db.prepare(stmt).run();
  return { mf, db, url: (await mf.ready).toString().replace(/\/$/, '') };
}

if (process.argv.includes('--serve')) {
  const port = Number(process.argv[process.argv.indexOf('--serve') + 1] || 8787);
  const { url } = await start({ port });
  console.log(`STUDIO LOCAL ${url}`);
  console.log(`FOUNDER_TOKEN ${token(FOUNDER, { exp: 86400 })}`);
  console.log(`PIPELINE_TOKEN ${PIPELINE_TOKEN}`);
}
