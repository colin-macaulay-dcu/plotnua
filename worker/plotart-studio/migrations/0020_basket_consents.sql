-- PlotArt · multi-artist basket · the artist's separate basket consents (22 Nov 2026). NEW TABLE ONLY: nothing existing changes.
-- Requires 0019. Append-only: a consent is withdrawn by a later 'withdrawn' row, never by editing or deleting.
--
--   processing_fees    the optional Founding 25 / commission-free consent (PA-BAA cl. 4): PlotArt takes 0% commission and no
--                      fee; the artist bears Stripe's actual processing fee. Bound to the exact basket addendum (doc_id + its
--                      fingerprint) the artist accepted; valid only while that is the artist's current accepted addendum.
--   seller_disclosure  the artist's confirmation that their seller information (legal name, address where established,
--                      contact details, VAT number if any) may be shown to buyers on the basket page BEFORE payment. Bound to
--                      a fingerprint of that information: any change to it needs a new confirmation.
-- Each row records the artist, the account that acted, the exact statement shown (and its fingerprint), Stripe mode and time.
CREATE TABLE IF NOT EXISTS basket_consents (
  id               TEXT PRIMARY KEY,
  artist_id        TEXT NOT NULL,
  topic            TEXT NOT NULL CHECK (topic IN ('processing_fees', 'seller_disclosure')),
  kind             TEXT NOT NULL CHECK (kind IN ('given', 'withdrawn')),
  doc_id           TEXT REFERENCES basket_terms(doc_id),
  doc_sha256       TEXT,
  subject_sha256   TEXT,
  statement        TEXT,
  statement_sha256 TEXT,
  account_email    TEXT NOT NULL,
  livemode         INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  at               TEXT NOT NULL,
  CHECK (kind = 'withdrawn' OR (statement IS NOT NULL AND length(statement_sha256) = 64)),
  CHECK (topic <> 'processing_fees' OR kind = 'withdrawn' OR (doc_id IS NOT NULL AND length(doc_sha256) = 64)),
  CHECK (topic <> 'seller_disclosure' OR kind = 'withdrawn' OR length(subject_sha256) = 64)
);
CREATE INDEX IF NOT EXISTS basket_consents_artist ON basket_consents(artist_id, topic, at);
CREATE TRIGGER IF NOT EXISTS basket_consents_valid_doc BEFORE INSERT ON basket_consents
WHEN NEW.topic = 'processing_fees' AND NEW.kind = 'given' AND NOT EXISTS (SELECT 1 FROM basket_terms t WHERE t.doc_id = NEW.doc_id
  AND t.kind = 'artist_basket_addendum' AND t.html_sha256 = NEW.doc_sha256 AND julianday(NEW.at) >= julianday(t.effective_at))
BEGIN SELECT RAISE(ABORT, 'basket consent refused: not an installed basket addendum, wrong fingerprint, or dated before it took effect'); END;
CREATE TRIGGER IF NOT EXISTS basket_consents_no_update BEFORE UPDATE ON basket_consents
BEGIN SELECT RAISE(ABORT, 'basket_consents is append-only'); END;
