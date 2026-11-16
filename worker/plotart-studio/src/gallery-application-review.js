/* PlotArt Gallery Artist review data access. Founder routes only; never expose credentials to browsers.
   This module does not send mail, invite artists, or touch Founding 25. */
const REF = /^PA-AP-\d{6}-[0-9A-F]{6}$/;
const TABLE = 'tblEQ8CiXFWMlWqsE';
const BASE = 'appS4gWOxuZqJyWvU';
const ALLOWED = new Set(['received','under_review','info_requested','accepted','declined','withdrawn']);
const FINAL = new Set(['accepted','declined','withdrawn']);
const url = () => `https://api.airtable.com/v0/${BASE}/${TABLE}`;
function configured(env) { return Boolean(env.PLOTART_REVIEW_AIRTABLE_TOKEN); }
async function request(env, path, options={}) {
  if (!configured(env)) throw new Error('Review integration is not configured');
  const res = await fetch(url()+path, { ...options, headers: {
    Authorization: `Bearer ${env.PLOTART_REVIEW_AIRTABLE_TOKEN}`,
    'Content-Type':'application/json', ...(options.headers||{}) } });
  if (!res.ok) throw new Error(`Application register request failed (${res.status})`);
  return res.json();
}
function assertRef(ref) { if (!REF.test(ref)) throw new Error('Invalid Gallery Artist application reference'); }
export async function getReview(env, ref) {
  assertRef(ref);
  const formula = `{application_ref}='${ref}'`;
  const data = await request(env, `?filterByFormula=${encodeURIComponent(formula)}&maxRecords=2`);
  if (data.records.length !== 1) throw new Error('Application not found or ambiguous');
  const row = data.records[0], f = row.fields || {};
  if (!ALLOWED.has(f.status)) throw new Error('Unknown application status');
  return { id:row.id, ref, status:f.status, artist_name:f.artist_name || '',
    email:f.email || '', review_notes:f.review_notes || '',
    decision_reason:f.decision_reason || '', status_changed_at:f.status_changed_at || null,
    decision_emailed_at:f.decision_emailed_at || null, studio_invited_at:f.studio_invited_at || null };
}
export async function saveReview(env, ref, { expectedStatus, status, notes, reason }) {
  assertRef(ref);
  if (!ALLOWED.has(expectedStatus) || !ALLOWED.has(status)) throw new Error('Invalid review status');
  const existing = await getReview(env, ref);
  if (existing.status !== expectedStatus) throw new Error('Application status changed; reload before deciding');
  if (FINAL.has(existing.status)) throw new Error('Finalised applications cannot be changed here');
  if (!['under_review','info_requested','accepted','declined'].includes(status)) throw new Error('Invalid transition');
  if (typeof notes !== 'string' || notes.length > 4000) throw new Error('Review notes exceed limit');
  if (typeof reason !== 'string' || reason.length > 2000) throw new Error('Decision reason exceeds limit');
  const timestamp = new Date().toISOString();
  const fields = {status,review_notes:notes,status_changed_at:timestamp};
  if (FINAL.has(status)) { fields.decided_at=timestamp; fields.decision_reason=reason; }
  await request(env, `/${existing.id}`, {method:'PATCH',body:JSON.stringify({fields})});
  // Airtable has no compare-and-swap API: caller must serialize decisions and audit separately.
  return { ref, status, status_changed_at:timestamp };
}
export { configured as reviewConfigured };
