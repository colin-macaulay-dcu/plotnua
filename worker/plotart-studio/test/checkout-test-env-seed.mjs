// PlotArt · managed checkout pilot · SQL to seed the separate TEST database (plotart-checkout-test) with synthetic records.
// Prints SQL only; it never connects to anything. Refuses unless the target name says "test". Use with Colin's own test
// addresses (e.g. plus-addresses of hello@plotnua.ie), never a real artist's.
//   node test/checkout-test-env-seed.mjs --target plotart-checkout-test --founding colin+f1@plotnua.ie --gallery colin+g1@plotnua.ie > seed.sql
//   npx wrangler d1 execute plotart-checkout-test --remote --file seed.sql        (TEST database only)
import { readFileSync } from 'node:fs';
import { snapshot } from '../src/lib.js';
const arg = k => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : null; };
const target = arg('target'), F = arg('founding'), G = arg('gallery');
if (target !== 'plotart-checkout-test') { console.error('REFUSED: --target must be plotart-checkout-test'); process.exit(2); }
if (![F, G].every(e => /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(e || ''))) { console.error('REFUSED: give --founding and --gallery test email addresses'); process.exit(2); }
const HERE = new URL('..', import.meta.url).pathname;
const q = v => v === null || v === undefined ? 'NULL' : typeof v === 'number' ? String(v) : `'${String(v).replace(/'/g, "''")}'`;
const now = new Date().toISOString(), ago = d => new Date(Date.now() - d * 86400_000).toISOString();
const out = ['-- PlotArt checkout pilot · TEST DATABASE SEED (synthetic; plotart-checkout-test only)'];
const fp = JSON.parse(readFileSync(HERE + 'agreements/payment-test/fingerprints.json', 'utf8')).documents;
for (const [id, d] of Object.entries(fp))
  out.push(`INSERT OR IGNORE INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES (${[id, d.kind, d.title, d.html_sha256, '2026-01-01T00:00:00Z', now].map(q).join(', ')});`);
function artist(id, slug, email, name, founding, publishedDaysAgo) {
  const t = ago(publishedDaysAgo);
  const a = { id, slug, email, display_name: name, founding, founding_number: null, practice: 'Painter', medium: 'painting', county: 'Dublin', county_public: 0,
    bio: `${name} is a synthetic TEST artist for the payment pilot test environment.`, account_status: 'invited', licence_version: 'PA-GPIL-2026-10-29', licence_accepted_at: t,
    first_published_at: t, created_at: t, updated_at: t };
  out.push(`INSERT INTO artists (${Object.keys(a).join(', ')}) VALUES (${Object.values(a).map(q).join(', ')});`);
  const works = [1, 2, 3].map(i => ({ id: `w${id}${i}`, artist_id: id, slug: `test-work-${i}`, title: `Test Work ${i}`, year: 2026, medium: 'Oil on board', materials: null,
    h_cm: 40, w_cm: 50, d_cm: 3, price_eur: 400 * i, price_on_request: 0, availability: 'available', description: 'A synthetic test work.', ord: i, ai_involvement: 'none', ai_note: null, archived: 0, created_at: t, updated_at: t }));
  for (const w of works) out.push(`INSERT INTO artworks (${Object.keys(w).join(', ')}) VALUES (${Object.values(w).map(q).join(', ')});`);
  out.push(`INSERT INTO versions (artist_id, version, snapshot, source, created_at) VALUES (${[id, 1, JSON.stringify(snapshot(a, works, [])), 'test-seed', t].map(q).join(', ')});`);
  out.push(`INSERT INTO publish_queue (id, artist_id, version, kind, status, created_at, updated_at) VALUES (${[`q${id}seed`, id, 1, 'reviewed', 'published', t, t].map(q).join(', ')});`);
  return t;
}
artist('atestfnd', 'test-founding', F, 'Test Founding Artist', 1, 30);
artist('atestgal', 'test-gallery', G, 'Test Gallery Artist', 0, 30);
// introductions: a Founding Enquiry (0% permanently) and a Gallery Artist introduction (15% once the agreement is accepted)
out.push(`INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at) VALUES ('ltest1', 'PA-E-261116-TEST01', 'atestfnd', NULL, 'relay', ${q(ago(5))}, 1, NULL, 'test-seed', ${q(ago(5))});`);
out.push(`INSERT INTO artist_terms (artist_id, track, commission_bp, set_by, created_at, updated_at) VALUES ('atestgal', 'gallery_artist', 1500, 'test-seed', ${q(now)}, ${q(now)});`);
out.push(`-- The Gallery Artist accepts PA-GAA in the test Studio (Agreement tab) BEFORE this second introduction is logged, so 15% applies:`);
out.push(`-- INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, logged_by, logged_at) VALUES ('ltest2', 'PA-E-261116-TEST02', 'atestgal', NULL, 'relay', <now>, 0, 'test-seed', <now>);`);
console.log(out.join('\n'));
