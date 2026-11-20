-- PlotArt Studio · migration 0018 · Issue the payment pilot texts (prepared 20 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database. PRODUCTION ONLY, and only after migration 0017.
-- ADDITIVE: inserts two rows into payment_terms (created by 0017) and nothing else. The rows can never change or be removed
-- (0017 triggers). Each fingerprint must equal agreements/payment-issued/fingerprints.json, the file bundled into the Workers
-- (build-assets.mjs refuses a mismatch; the pilot accepts a text only when the installed fingerprint is the bundled one).
-- Not for plotart-checkout-test: the TEST environment keeps its labelled placeholders (PA-PAY-TEST-01, PA-BPT-TEST-01).
-- Rollback: none needed before anyone accepts; payment_terms rows are inert until an artist opts in or a quote is issued.
INSERT INTO payment_terms (doc_id, kind, title, html_sha256, effective_at, created_at) VALUES
  ('PA-PAY-2026-11', 'artist_payment_addendum', 'PlotArt Payment Pilot Addendum', 'ff0a8c87f360a60159d9aa2491d957a207791b656c36ccfa517429f60d4464bd', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  ('PA-BPT-2026-11', 'buyer_purchase_terms', 'PlotArt Buyer Purchase Terms', 'c570c06fe00577db3c5718c2b5b40fc6f834a2a2f2b97678b3a1978d74eb332a', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
