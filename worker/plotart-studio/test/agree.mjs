// Test helper (Founding Artist Agreement, development 6 Nov 2026): the artist reads both texts exactly as Studio serves
// them, fingerprints what was read, and ticks the one box. Used by every proof that takes an artist to publication.
import { createHash } from 'node:crypto';
import { token } from './local.mjs';
export async function acceptAgreement(mf, url, email, { legal_name = null, tamper = false, statement = null } = {}) {
  const H = { 'Cf-Access-Jwt-Assertion': token(email), 'X-Studio': '1', 'Content-Type': 'application/json' };
  const g = await (await mf.dispatchFetch(url + '/api/agreement', { headers: H })).json();
  const documents = {};
  for (const d of g.documents || []) {
    const body = Buffer.from(await (await mf.dispatchFetch(url + `/agreements/${d.id}.html`, { headers: H })).arrayBuffer());
    documents[d.id] = createHash('sha256').update(tamper ? Buffer.concat([body, Buffer.from(' ')]) : body).digest('hex');
  }
  const r = await mf.dispatchFetch(url + '/api/agreement/accept', { method: 'POST', headers: H, body: JSON.stringify({ accept: true, documents, statement: statement || g.statement, legal_name }) });
  return { s: r.status, j: await r.json().catch(() => ({})), documents, statement: g.statement };
}
