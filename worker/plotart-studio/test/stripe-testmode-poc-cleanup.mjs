// CLEAN-UP ONLY · Stripe TEST MODE ONLY · for the isolated two-artist basket POC (founder approval 21 Nov 2026).
// Finds the TEST PaymentIntents a POC run created on the two named artist accounts (metadata poc = the run tag),
// reports amount, status, commission and refunds, then (mode "clean") refunds captured charges still outstanding and
// cancels authorisations still uncaptured, and checks again. It never creates a payment and only ever touches objects
// carrying the exact run tag. Commission is refunded only on charges that carried commission (zero-commission charges are
// refunded without refund_application_fee). Reads its request from test/stripe-cleanup-run.json.
//   node test/stripe-testmode-poc-cleanup.mjs      (needs STRIPE_POC_KEY, a TEST key; never printed)
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { V1_API_VERSION } from '../src/stripe.js';

const req = JSON.parse(readFileSync(new URL('./stripe-cleanup-run.json', import.meta.url), 'utf8'));
const OUT = new URL('../stripe-cleanup-evidence/', import.meta.url).pathname;
const KEY = process.env.STRIPE_POC_KEY || '';
const TAG = req.run_tag, ACCOUNTS = req.accounts, MODE = req.mode;
const log = [], result = { run_tag: TAG, mode: MODE, at: new Date().toISOString(), accounts: {}, platform: {}, actions: [], errors: [] };
const say = s => { log.push(s); console.log(s); };
const eur = c => (c == null ? '—' : '€' + (c / 100).toFixed(2));

if (!/^(sk|rk)_test_[A-Za-z0-9]+$/.test(KEY)) { console.log('STOP  STRIPE_POC_KEY missing or not a TEST key'); process.exit(1); }
if (!/^plotart-poc-[A-Za-z0-9]+$/.test(TAG || '')) { console.log('STOP  run_tag must be a POC run tag'); process.exit(1); }
if (!Array.isArray(ACCOUNTS) || ACCOUNTS.length !== 2 || !ACCOUNTS.every(a => /^acct_[A-Za-z0-9]+$/.test(a))) { console.log('STOP  exactly two artist accounts'); process.exit(1); }
if (!['inspect', 'clean'].includes(MODE)) { console.log('STOP  mode must be "inspect" or "clean"'); process.exit(1); }

async function api(method, path, body = null, { account = null, idem = null } = {}) {
  const h = { Authorization: 'Bearer ' + KEY, 'Stripe-Version': V1_API_VERSION };
  if (account) h['Stripe-Account'] = account;
  if (idem) h['Idempotency-Key'] = idem;
  if (body) h['Content-Type'] = 'application/x-www-form-urlencoded';
  const r = await fetch('https://api.stripe.com' + path, { method, headers: h, body: body ? new URLSearchParams(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (j.livemode === true || (Array.isArray(j.data) && j.data.some(o => o.livemode === true))) { console.log('STOP  a live-mode object was returned'); process.exit(1); }
  const err = j.error ? { http: r.status, type: j.error.type, code: j.error.code ?? null, param: j.error.param ?? null,
    message: String(j.error.message || '').replace(/(?:[rs]k|pk)_(?:test|live)_\S+/g, '[key]').slice(0, 300) } : null;
  return { ok: r.ok, j, err };
}

// every PaymentIntent on one account carrying this run's tag: Search API, plus a list over the run's time window (union)
async function findRunIntents(acct) {
  const found = new Map(), notes = [];
  let page = null;
  do {
    const q = `/v1/payment_intents/search?limit=100&query=${encodeURIComponent(`metadata['poc']:'${TAG}'`)}` + (page ? `&page=${encodeURIComponent(page)}` : '');
    const r = await api('GET', q, null, { account: acct });
    if (!r.ok) { notes.push({ source: 'search', error: r.err }); break; }
    for (const p of r.j.data) if (p.metadata?.poc === TAG) found.set(p.id, 'search');
    page = r.j.has_more ? r.j.next_page : null;
  } while (page);
  let after = null;
  do {
    const q = `/v1/payment_intents?limit=100&created[gte]=${req.window.from}&created[lte]=${req.window.to}` + (after ? `&starting_after=${after}` : '');
    const r = await api('GET', q, null, { account: acct });
    if (!r.ok) { notes.push({ source: 'list', error: r.err }); break; }
    for (const p of r.j.data) if (p.metadata?.poc === TAG) found.set(p.id, found.has(p.id) ? 'search+list' : 'list');
    after = r.j.has_more ? r.j.data.at(-1).id : null;
  } while (after);
  return { ids: [...found.keys()], notes };
}

async function describe(acct, id) {
  const p = await api('GET', `/v1/payment_intents/${id}?expand[]=latest_charge`, null, { account: acct });
  if (!p.ok) return { id, error: p.err };
  const pi = p.j, ch = pi.latest_charge || null;
  if (pi.metadata?.poc !== TAG) return { id, skipped: 'tag mismatch' };
  const rf = await api('GET', `/v1/refunds?payment_intent=${id}&limit=100`, null, { account: acct });
  return {
    id, basket: pi.metadata?.basket, artist: pi.metadata?.artist, amount: pi.amount, currency: pi.currency, status: pi.status,
    capture_method: pi.capture_method, application_fee_amount: pi.application_fee_amount ?? null,
    charge: ch ? { id: ch.id, captured: ch.captured, amount_captured: ch.amount_captured, amount_refunded: ch.amount_refunded,
      refunded: ch.refunded, application_fee: typeof ch.application_fee === 'string' ? ch.application_fee : ch.application_fee?.id ?? null,
      application_fee_amount: ch.application_fee_amount ?? null } : null,
    refunds: rf.ok ? rf.j.data.map(x => ({ id: x.id, amount: x.amount, status: x.status, failure_reason: x.failure_reason ?? null })) : { error: rf.err },
  };
}
const outstanding = d => d.status === 'succeeded' && d.charge && d.charge.amount_refunded < d.charge.amount_captured
  && !(Array.isArray(d.refunds) && d.refunds.some(x => x.status === 'pending' || x.status === 'requires_action'));
const uncaptured = d => d.status === 'requires_capture';

async function survey(label) {
  const snap = {};
  for (const acct of ACCOUNTS) {
    const { ids, notes } = await findRunIntents(acct);
    const items = [];
    for (const id of ids) items.push(await describe(acct, id));
    const bal = await api('GET', '/v1/balance', null, { account: acct });
    snap[acct] = { intents: items, discovery_notes: notes,
      balance: bal.ok ? { available: bal.j.available, pending: bal.j.pending } : { error: bal.err } };
    say(`\n[${label}] ${acct}: ${items.length} PaymentIntent(s) tagged ${TAG}`);
    for (const d of items) {
      if (d.error || d.skipped) { say(`  ${d.id}  ERROR ${JSON.stringify(d.error || d.skipped)}`); continue; }
      const rf = Array.isArray(d.refunds) ? d.refunds.map(x => `${x.id} ${eur(x.amount)} ${x.status}`).join('; ') || 'none' : 'refunds unreadable';
      say(`  ${d.id}  basket ${d.basket} · ${eur(d.amount)} · ${d.status} · commission ${eur(d.application_fee_amount)} · refunded ${eur(d.charge?.amount_refunded)} · refunds: ${rf}`
        + (outstanding(d) ? '  << OUTSTANDING CHARGE' : '') + (uncaptured(d) ? '  << UNCANCELLED AUTHORISATION' : ''));
    }
    for (const n of notes) say(`  discovery note (${n.source}): ${JSON.stringify(n.error)}`);
    // the list over the run's window is the authoritative search: if it could not be read, "nothing found" proves nothing
    if (notes.some(n => n.source === 'list')) result.errors.push({ account: acct, action: `discover (${label})`, error: 'PaymentIntents could not be listed: result not conclusive' });
    say(`  balance: ${bal.ok ? JSON.stringify({ available: bal.j.available.map(b => `${b.currency} ${eur(b.amount)}`), pending: bal.j.pending.map(b => `${b.currency} ${eur(b.amount)}`) }) : JSON.stringify(bal.err)}`);
  }
  return snap;
}

const before = await survey('before');
result.accounts.before = before;

if (MODE === 'clean') {
  say('\n[actions]');
  for (const acct of ACCOUNTS) for (const d of before[acct].intents) {
    if (d.error || d.skipped) continue;
    if (uncaptured(d)) {
      const r = await api('POST', `/v1/payment_intents/${d.id}/cancel`, {}, { account: acct, idem: `${TAG}-cleanup-cancel-${d.id}` });
      const a = { account: acct, intent: d.id, action: 'cancel authorisation', ok: r.ok, status: r.j.status ?? null, error: r.err };
      result.actions.push(a); if (!r.ok) result.errors.push(a);
      say(`  cancel ${d.id} (${eur(d.amount)}) -> ${r.ok ? r.j.status : 'ERROR ' + JSON.stringify(r.err)}`);
    } else if (outstanding(d)) {
      const withFee = (d.charge.application_fee_amount || d.application_fee_amount || 0) > 0;   // never ask for a fee refund on a 0% charge
      const body = { payment_intent: d.id, 'metadata[poc_cleanup]': TAG };
      if (withFee) body.refund_application_fee = 'true';
      const r = await api('POST', '/v1/refunds', body, { account: acct, idem: `${TAG}-cleanup-refund-${d.id}` });
      const a = { account: acct, intent: d.id, action: withFee ? 'refund with commission' : 'refund (no commission on this charge)',
        amount: d.charge.amount_captured - d.charge.amount_refunded, ok: r.ok, refund: r.ok ? { id: r.j.id, amount: r.j.amount, status: r.j.status } : null, error: r.err };
      result.actions.push(a); if (!r.ok) result.errors.push(a);
      say(`  refund ${d.id} ${eur(a.amount)} ${withFee ? '+ commission' : '(no commission)'} -> ${r.ok ? `${r.j.id} ${r.j.status}` : 'ERROR ' + JSON.stringify(r.err)}`);
    }
  }
  if (!result.actions.length) say('  nothing outstanding: no action taken');
  await new Promise(r => setTimeout(r, 5000));
  result.accounts.after = await survey('after');
}

// commission side (platform): each application fee from this run's charges, and whether it was returned
say('\n[platform] application fees on this run\'s charges');
const finalSnap = result.accounts.after || before;
result.platform.application_fees = [];
for (const acct of ACCOUNTS) for (const d of finalSnap[acct].intents) {
  if (!d.charge?.application_fee) continue;
  const f = await api('GET', `/v1/application_fees/${d.charge.application_fee}`);
  const row = f.ok ? { fee: f.j.id, intent: d.id, amount: f.j.amount, amount_refunded: f.j.amount_refunded, refunded: f.j.refunded } : { fee: d.charge.application_fee, intent: d.id, error: f.err };
  result.platform.application_fees.push(row);
  say(`  ${row.fee} on ${d.id}: ${f.ok ? `${eur(row.amount)} · returned ${eur(row.amount_refunded)}` : 'ERROR ' + JSON.stringify(f.err)}`);
}
const cs = await api('GET', `/v1/customers/search?query=${encodeURIComponent(`metadata['poc']:'${TAG}'`)}`);
result.platform.customers_remaining = cs.ok ? cs.j.data.length : { error: cs.err };
say(`[platform] test customers still present with this tag: ${cs.ok ? cs.j.data.length : 'ERROR ' + JSON.stringify(cs.err)} (report only)`);
const pb = await api('GET', '/v1/balance');
result.platform.balance = pb.ok ? { available: pb.j.available, pending: pb.j.pending } : { error: pb.err };

const remaining = ACCOUNTS.flatMap(a => finalSnap[a].intents.filter(d => !d.error && !d.skipped && (outstanding(d) || uncaptured(d))).map(d => ({ account: a, intent: d.id, status: d.status })));
result.remaining = remaining;
say(`\nRESULT  ${MODE === 'clean' ? 'clean-up' : 'inspection'}: ${remaining.length} outstanding charge(s)/authorisation(s) remain · ${result.errors.length} action error(s)`);
mkdirSync(OUT, { recursive: true });
writeFileSync(OUT + 'cleanup.json', JSON.stringify(result, null, 2));
writeFileSync(OUT + 'cleanup.md', '# POC TEST clean-up · ' + TAG + '\n\n```\n' + log.join('\n') + '\n```\n');
process.exit(MODE === 'clean' && (remaining.length || result.errors.length) ? 1 : 0);
