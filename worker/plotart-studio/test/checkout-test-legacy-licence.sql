-- PlotArt checkout pilot · TEST DATABASE ONLY (plotart-checkout-test) · 19 Nov 2026
-- Migration 0005 step 6 for the two synthetic TEST artists. The TEST seed gives them artists.licence_version
-- 'PA-GPIL-2026-10-29' (as production artists have), but it is applied AFTER schema.sql, so 0005's own copy of that
-- label into agreement_acceptances never ran for them. Without the migrated row Studio refuses the Gallery Artist
-- Agreement ("can't be accepted just yet"). This is that same statement, limited to the synthetic IDs and written so it
-- adds nothing if the row already exists. It creates no agreement acceptance: the table's checks allow a migrated row
-- only for the legacy licence label PA-GPIL-2026-10-29. Applied by plotart-checkout-test-setup.yml mode d1_legacy_licence
-- and appended to every new TEST seed by test/checkout-test-env-seed.mjs.
INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, legal_name,
                                   method, statement, note, created_at)
SELECT 'acc-mig-' || a.id, 'evt-mig-' || a.id, a.id, a.licence_version, NULL, NULL, a.licence_accepted_at, NULL, a.display_name, NULL,
       'migrated_from_artists_table',
       'I approve my PlotArt gallery preview and accept the Gallery Publication and Image Licence, version ' || a.licence_version || '.',
       'Copied by migration 0005 from artists.licence_version and licence_accepted_at. Studio showed a one-sentence summary and this version label; no fixed full text existed for this version, and none is attributed.',
       strftime('%Y-%m-%dT%H:%M:%SZ','now')
FROM artists a
WHERE a.id IN ('atestfnd', 'atestgal') AND a.licence_version = 'PA-GPIL-2026-10-29' AND a.licence_accepted_at IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM agreement_acceptances x WHERE x.artist_id = a.id AND x.method = 'migrated_from_artists_table');
