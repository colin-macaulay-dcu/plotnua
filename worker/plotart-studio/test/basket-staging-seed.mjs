// PlotArt · multi-artist basket · SQL to seed the PRIVATE STAGING database (plotart-basket-staging) with SYNTHETIC records.
// Prints SQL only; it never connects to anything. Refuses unless the target is exactly plotart-basket-staging.
// Two synthetic artists on the two EXISTING Stripe TEST accounts (a Gallery Artist on 15% and a Founding Artist at 0% who
// has given the separate processing consent), each with synthetic works, a standing delivery offer per work, seller
// information, the pilot and basket opt-ins (TEST placeholder texts), as an approved artist would have them.
//   node test/basket-staging-seed.mjs --target plotart-basket-staging --accounts acct_A,acct_B > seed.sql
import { readFileSync } from 'node:fs';
import { snapshot } from '../src/lib.js';
import { createHash } from 'node:crypto';
import { basketDoc, ARTIST_STATEMENT, PROCESSING_CONSENT_STATEMENT, SELLER_DISCLOSURE_STATEMENT } from '../src/basket-terms.js';
import { STATEMENT, PROCESSING_STATEMENT } from '../src/checkout.js';

const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const TARGET = arg('target');
if (!['plotart-basket-staging', 'plotart-checkout-test'].includes(TARGET)) { console.error('REFUSED: --target must be plotart-basket-staging or plotart-checkout-test'); process.exit(2); }
/* plotart-checkout-test (the EXISTING TEST database): ADDITIVE ONLY. --state is a JSON file read from that database just
   before (payment_accounts and artists). Every insert is INSERT OR IGNORE; nothing existing is updated or deleted. If one of
   the two Stripe TEST accounts already belongs to an existing TEST artist, that artist is used for that slot (synthetic works,
   a new published version that keeps their existing works, delivery offers and opt-ins are added); otherwise a synthetic
   staging artist is added for it. */
const STATE = TARGET === 'plotart-checkout-test' ? JSON.parse(readFileSync(arg('state') || '/dev/null', 'utf8') || 'null') : null;
if (TARGET === 'plotart-checkout-test' && !STATE) { console.error('REFUSED: --state <json> (read from the TEST database) is required'); process.exit(2); }
const owner = acct => STATE ? (STATE.payment_accounts || []).find(r => r.account_id === acct) : null;
const HERE = new URL('..', import.meta.url).pathname;
const accounts = (arg('accounts') || (() => { const c = JSON.parse(readFileSync(HERE + 'test/stripe-test-run.json', 'utf8')); return `${c.reuse_account},${c.unfunded_account}`; })()).split(',');
if (accounts.length !== 2 || !accounts.every(a => /^acct_[A-Za-z0-9]+$/.test(a)) || accounts[0] === accounts[1]) { console.error('REFUSED: --accounts needs two distinct Stripe TEST account ids'); process.exit(2); }
const q = v => v === null || v === undefined ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replace(/'/g, "''")}'`;
const ins = (table, o) => `INSERT ${STATE ? 'OR IGNORE ' : ''}INTO ${table} (${Object.keys(o).join(', ')}) VALUES (${Object.values(o).map(q).join(', ')});`;
const now = new Date().toISOString(), ago = d => new Date(Date.now() - d * 86400_000).toISOString(), T0 = '2026-01-01T00:00:00Z';
const sha = t => createHash('sha256').update(t).digest('hex');
const out = ['-- PlotArt multi-artist basket · PRIVATE STAGING SEED (synthetic only; plotart-basket-staging only)'];

// texts: the pilot's TEST placeholders and the basket's TEST placeholders (never a live text)
const fp = JSON.parse(readFileSync(HERE + 'agreements/payment-test/fingerprints.json', 'utf8')).documents;
for (const [id, d] of Object.entries(fp)) out.push(ins('payment_terms', { doc_id: id, kind: d.kind, title: d.title, html_sha256: d.html_sha256, effective_at: T0, created_at: now }));
const BBT = await basketDoc('PA-BBT-TEST-01', false), BAA = await basketDoc('PA-BAA-TEST-01', false);
for (const d of [BBT, BAA]) out.push(ins('basket_terms', { doc_id: d.doc_id, kind: d.kind, title: d.title, html_sha256: d.html_sha256, effective_at: T0, created_at: now }));
const ADD = Object.entries(fp).find(([, d]) => d.kind === 'artist_payment_addendum');

const DELIVERY = { collection_county: 'Dublin', destination: 'Anywhere in the Republic of Ireland (the buyer’s address is given at checkout)', unpacked_cm: 'as listed', packed_cm: 'listed size + 15 cm',
  weight_kg: 5, medium: 'Oil on board', framing: 'Unframed', glazing: 'None', condition: 'Excellent (synthetic staging work)', access_notes: null,
  organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist', transporter_name: 'Synthetic Art Couriers (STAGING)',
  installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: 'Synthetic Underwriting (SIMULATED, staging only)', covered_value_cents: 500000,
  insured_party: 'transporter', cover_confirmation_ref: 'SIM-STAGING-COVER', cover_confirmed_by: 'Synthetic Underwriting', cover_confirmed_on: now.slice(0, 10), valuation_basis: 'Sale price',
  excess_cents: 0, exclusions: null, cover_period: 'Collection to signed delivery', claims_contact: 'claims@example.invalid', delivery_window: '5–8 working days', tracking: 'Tracked, signature on delivery',
  signed_receipt: true, condition_photos: true, return_method: 'Same courier, packed as delivered, insured', return_address: '1 Synthetic Studio Lane, Dublin 8', return_cost_cents: 4500,
  return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer', shipment_confirmation_ref: 'SAC-STAGING-RATE', shipment_confirmed_by: 'Synthetic Art Couriers', shipment_confirmed_on: now.slice(0, 10) };

const ARTISTS = [
  { id: 'astgal', slug: 'aoife-staging', name: 'Aoife Lennon (synthetic)', founding: 0, account: accounts[0], delivery: 3500, works: [
    ['Tidewater Study', 'Oil on linen', 60, 50, 1200], ['North Wall, Evening', 'Oil on board', 40, 50, 850], ['Salt Marsh II', 'Acrylic on canvas', 80, 60, 1650],
    ['Small Harbour', 'Oil on board', 30, 30, 480], ['Field Notes (Price on request)', 'Mixed media', 70, 70, null]] },
  { id: 'astfnd', slug: 'cian-staging', name: 'Cian Doherty (synthetic)', founding: 1, account: accounts[1], delivery: 2500, works: [
    ['Bog Cotton', 'Watercolour on paper', 42, 30, 320], ['Granite Light', 'Oil on board', 50, 40, 760], ['Lough at Dusk', 'Oil on canvas', 70, 90, 1400], ['Hedgerow, May', 'Gouache on paper', 30, 40, 290]] },
];
const created = [];
for (const A0 of ARTISTS) {
  // an account already owned by one of OUR synthetic staging artists (a repeated run) is that artist's: nothing new is added
  const own = owner(A0.account), ex = own && !ARTISTS.some(x => x.id === own.artist_id) && (STATE.artists || []).find(x => x.id === own.artist_id);
  // an existing TEST artist already owns this Stripe TEST account: that artist takes this slot (their own founding status)
  const A = ex ? { ...A0, id: ex.id, slug: ex.slug, name: ex.display_name, founding: ex.founding ? 1 : 0, existing: true, works: A0.works.filter(w => w[4]).slice(0, 3) } : A0;
  if (!ex) created.push(A.id);
  const t = ago(60), email = ex ? ex.email : `${A.slug}@example.invalid`;
  const a = { id: A.id, slug: A.slug, email, display_name: A.name, founding: A.founding, founding_number: A.founding ? 25 : null, practice: 'Painter', medium: 'painting', county: 'Dublin', county_public: 0,
    bio: `${A.name} is a synthetic artist for PlotArt's private basket staging.`, account_status: 'active', licence_version: 'PA-GPIL-2026-10-29', licence_accepted_at: t, first_published_at: t, created_at: t, updated_at: t };
  if (!A.existing) out.push(ins('artists', a));
  const works = A.works.map(([title, medium, h, w, price], i) => ({ id: A.existing ? `wbk${A.id}${i + 1}` : `w${A.id}${i + 1}`, artist_id: A.id, slug: title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''), title, year: 2026, medium, materials: null,
    h_cm: h, w_cm: w, d_cm: 3, price_eur: price, price_on_request: price ? 0 : 1, availability: 'available', description: 'A synthetic work for staging. No real artwork.', ord: i + 1, ai_involvement: 'none', ai_note: null, archived: 0, created_at: t, updated_at: t, ...(A.existing ? { ord: 900 + i } : {}) }));
  for (const w of works) out.push(ins('artworks', w));
  if (!A.existing) {
    out.push(ins('versions', { artist_id: A.id, version: 1, snapshot: JSON.stringify(snapshot(a, works, [])), source: 'staging-seed', created_at: t }));
    out.push(ins('publish_queue', { id: `q${A.id}seed`, artist_id: A.id, version: 1, kind: 'reviewed', status: 'published', created_at: t, updated_at: t }));
  } else {
    // a NEW published version: the artist's latest snapshot with the synthetic basket works appended (their works unchanged); once only
    const add = snapshot({ slug: A.slug, display_name: A.name }, works, []).works.map(w => `'$.works[#]', json(${q(JSON.stringify(w))})`).join(', ');
    out.push(`INSERT INTO versions (artist_id, version, snapshot, source, created_at) SELECT artist_id, version + 1, json_insert(snapshot, ${add}), 'basket-test-seed', ${q(now)}
  FROM versions WHERE artist_id = ${q(A.id)} AND NOT EXISTS (SELECT 1 FROM versions v WHERE v.artist_id = ${q(A.id)} AND v.source = 'basket-test-seed') ORDER BY version DESC LIMIT 1;`);
    out.push(`INSERT OR IGNORE INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) SELECT ${q('qbk' + A.id)}, artist_id, version, 'reviewed', 'published', ${q(now)}, ${q(now)} FROM versions WHERE artist_id = ${q(A.id)} AND source = 'basket-test-seed';`);
  }
  // the payment pilot (TEST addendum), the artist's own Stripe TEST account, seller information
  out.push(ins('payment_pilot_events', { id: `pe${A.id}1`, artist_id: A.id, kind: 'opted_in', doc_id: ADD[0], doc_sha256: ADD[1].html_sha256, account_email: email, display_name: A.name, statement: STATEMENT(ADD[0]), at: ago(30) }));
  if (A.founding) out.push(ins('payment_pilot_events', { id: `pe${A.id}2`, artist_id: A.id, kind: 'processing_consent', doc_id: null, doc_sha256: null, account_email: email, display_name: A.name, statement: PROCESSING_STATEMENT, at: ago(29) }));
  if (!A.existing) out.push(ins('payment_accounts', { artist_id: A.id, account_id: A.account, country: 'IE', livemode: 0, charges_enabled: 1, payouts_enabled: 1, details_submitted: 1, requirements_due: '[]', checked_at: now, created_at: now, updated_at: now }));
  const sp = { artist_id: A.id, legal_name: A.name.replace(' (synthetic)', ''), trading_name: null, address: '1 Synthetic Studio Lane, Dublin 8, Ireland', returns_address: null,
    email: `${A.slug}+seller@example.invalid`, phone: '+353 1 555 0100', trader_status: 'trader', vat_number: null, declared_at: ago(29), declared_by: email, updated_at: ago(29) };
  out.push(ins('seller_profiles', sp));
  // the artist's basket confirmations (migration 0020), TEST only: seller information shown before payment, bound to the
  // information actually held (an existing TEST artist's own profile when they have one), and the Founding processing consent
  const held = (STATE && (STATE.seller_profiles || []).find(r => r.artist_id === A.id)) || sp;
  const subject = sha(JSON.stringify(['legal_name', 'trading_name', 'address', 'returns_address', 'email', 'phone', 'vat_number'].map(k => held[k] ?? null)));
  out.push(ins('basket_consents', { id: `bc${A.id}sd`, artist_id: A.id, topic: 'seller_disclosure', kind: 'given', doc_id: null, doc_sha256: null, subject_sha256: subject,
    statement: SELLER_DISCLOSURE_STATEMENT, statement_sha256: sha(SELLER_DISCLOSURE_STATEMENT), account_email: email, livemode: 0, at: ago(27) }));
  if (A.founding) { const ps = PROCESSING_CONSENT_STATEMENT(BAA.doc_id);
    out.push(ins('basket_consents', { id: `bc${A.id}pf`, artist_id: A.id, topic: 'processing_fees', kind: 'given', doc_id: BAA.doc_id, doc_sha256: BAA.html_sha256, subject_sha256: null,
      statement: ps, statement_sha256: sha(ps), account_email: email, livemode: 0, at: ago(27) })); }
  out.push(ins('basket_artist_events', { id: `be${A.id}1`, artist_id: A.id, kind: 'opted_in', doc_id: BAA.doc_id, doc_sha256: BAA.html_sha256, account_email: email, statement: ARTIST_STATEMENT(BAA.doc_id), at: ago(28) }));
  for (const w of works.filter(x => x.price_eur)) out.push(ins('artwork_delivery_offers', { artwork_id: w.id, artist_id: A.id, region: 'IE', delivery_cents: A.delivery * 1, delivery: JSON.stringify(DELIVERY), version: 1,
    approved_by: 'artist:' + email, approved_at: ago(28), withdrawn_at: null, created_at: ago(28), updated_at: ago(28) }));
}
// the Gallery Artist holds the Gallery Artist Agreement at 15% (synthetic fingerprints), accepted before any online introduction
const FAKE = 'a'.repeat(64);
if (created.includes('astgal')) {
out.push(`INSERT OR IGNORE INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES ('PA-GAA-2026-11', 'gallery_artist_agreement', 'Gallery Artist Agreement (staging record)', 'fixed', ${q(FAKE)}, ${q(FAKE)}, ${q(T0)}, ${q(now)});`);
// the acceptance carries the INSTALLED document's own fingerprints and is dated when the seed runs (0013 makes the text effective
// when it is applied); online introductions come later, so 15% applies
out.push(`INSERT ${STATE ? "OR IGNORE " : ""}INTO gallery_agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, method, statement, created_at)
  SELECT 'gaastgal', 'evstgal', 'astgal', d.doc_id, d.html_sha256, d.pdf_sha256, max(d.effective_at, strftime('%Y-%m-%dT%H:%M:%fZ', 'now')), 'aoife-staging@example.invalid', 'Aoife Lennon (synthetic)', 'studio_checkbox', 'staging seed', strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
  FROM gallery_agreement_documents d WHERE d.doc_id = 'PA-GAA-2026-11';`);
out.push(ins('artist_terms', { artist_id: 'astgal', track: 'gallery_artist', commission_bp: 1500, set_by: 'staging-seed', created_at: ago(40), updated_at: ago(40) }));
}
console.log(out.join('\n'));
console.error(`seed: ${TARGET}; slots: ${ARTISTS.map(A0 => { const o = owner(A0.account); return o ? `existing artist ${o.artist_id} owns ${A0.account}` : `synthetic ${A0.id} on ${A0.account}`; }).join('; ')}`);
