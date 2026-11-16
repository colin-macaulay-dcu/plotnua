/* PlotArt Gallery Artist application decisions — isolated, fail-closed Airtable adapter.
 * NOT connected to routes until review and deployment approval.
 * Required secret: GALLERY_AIRTABLE_TOKEN (restricted to Gallery Artist applications).
 * Required secret: GALLERY_AIRTABLE_BASE_ID. No token or base ID is sent to browsers.
 * This module never sends email or creates Studio invitations.
 */
const TABLE = 'Gallery Artist applications';
const REF = /^PA-AP-\d{6}-[0-9A-F]{6}$/;
const STATES = new Set(['received','under_review','info_requested','accepted','declined','withdrawn']);
const DECISIONS = new Set(['under_review','info_requested','accepted','declined']);
const enc = encodeURIComponent;
const fail = (message, status = 400) => Object.assign(new Error(message), { status });
function credentials(env) {
  const token = env.GALLERY_AIRTABLE_TOKEN, base = env.GALLERY_AIRTABLE_BASE_ID;
  if (!token || !/^app[A-Za-z0-9]{14}$/.test(base || '')) throw fail('Gallery review integration is not configured', 503);
  return { token, url: 'https://api.airtable.com/v0/' + enc(base) + '/' + enc(TABLE) };
}
async function airtable(env, suffix = '', options = {}) {
  const { token, url } = credentials(env);
  const response = await fetch(url + suffix, {
    ...options, headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(8000),
  });
  if (!response.ok) throw fail('Application register request failed', 502);
  return response.json();
}
export async function findGalleryApplication(env, reference) {
  if (!REF.test(reference || '')) throw fail('Invalid Gallery Artist application reference');
  // Fixed allow-listed field and escaped string literal: no arbitrary Airtable formulas.
  const literal = reference.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  const qs = '?maxRecords=2&filterByFormula=' + enc('{application_ref}="' + literal + '"');
  const data = await airtable(env, qs);
  if (data.records.length !== 1) throw fail(data.records.length ? 'Duplicate application reference' : 'Application not found', data.records.length ? 409 : 404);
  return data.records[0];
}
export async function updateGalleryDecision(env, { reference, status, expectedStatus, reason, notes }) {
  if (!DECISIONS.has(status)) throw fail('Invalid review decision');
  if (!STATES.has(expectedStatus)) throw fail('Invalid expected status');
  if (typeof reason !== 'string' || reason.length > 1500 || typeof notes !== 'string' || notes.length > 4000)
    throw fail('Invalid review text');
  if (status === 'declined' && !reason.trim()) throw fail('Decline reason required');
  const record = await findGalleryApplication(env, reference);
  if (record.fields.status !== expectedStatus) throw fail('Application status changed: refresh before deciding', 409);
  if (['accepted','declined','withdrawn'].includes(expectedStatus)) throw fail('Finalised application cannot be changed here', 409);
  // No message is sent. info_requested is not enabled as a send action until a reviewed mail pathway exists.
  if (status === 'info_requested') throw fail('Information requests require an approved email workflow', 503);
  const fields = {
    status, status_changed_at: new Date().toISOString(),
    review_notes: notes.trim(),
    ...(status === 'accepted' || status === 'declined'
      ? { decided_at: new Date().toISOString(), decision_reason: reason.trim() } : {}),
  };
  // Airtable has no compare-and-swap PATCH; caller must also guard duplicate submissions.
  return airtable(env, '/' + enc(record.id), { method: 'PATCH', body: JSON.stringify({ fields, typecast: false }) });
}
