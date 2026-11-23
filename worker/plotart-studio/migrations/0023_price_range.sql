-- PlotArt · price range: the database part (prepared 23 Nov 2026). NOT APPLIED. Founder decision needed before it runs.
-- The pilot's EUR 9,999.99 per-artwork ceiling lives in two places: the code (rules.MAX_ARTWORK_CENTS, which stays the
-- default) and this column check on checkout_orders.artwork_cents. This migration changes ONLY that check, to Stripe's largest
-- single EUR payment (EUR 999,999.99). On its own it changes no behaviour: the code still applies EUR 9,999.99 unless
-- PRICE_RANGE=open AND new texts without the limit are issued, and the EUR 10,000 linked-purchase safeguard is separate.
--
-- SQLite cannot change a column check in place, so the table is rebuilt: every row is copied aside, the table is dropped and
-- created again UNDER ITS OWN NAME with the identical definition except that one check, every row is copied back unchanged
-- (same columns, same order; copying back into the parent table is what settles the deferred foreign keys; a rename would
-- not), the copy is dropped, and we recreate its three indexes and two triggers exactly as in 0017, and the nine triggers of other tables that read it. Twelve tables reference checkout_orders(id); foreign keys
-- are checked at the end (defer_foreign_keys), when the rebuilt table again holds every id. Class: destructive (DROP TABLE):
-- the workflow takes the Time Travel restore point and the encrypted full export first. Running it again is harmless (tested).
PRAGMA defer_foreign_keys = on;
-- nine triggers on OTHER tables read checkout_orders (they protect records from deletion while an order is kept). SQLite
-- refuses to rename a table while such a trigger points at a missing one, so they are dropped here and recreated,
-- word for word from their own migrations, at the end of this same transaction.
DROP TRIGGER payment_pilot_events_no_delete;
DROP TRIGGER artwork_sales_no_delete;
DROP TRIGGER order_ledger_no_delete;
DROP TRIGGER order_fulfilment_events_no_delete;
DROP TRIGGER order_events_no_delete;
DROP TRIGGER checkout_holds_no_delete;
DROP TRIGGER checkout_hold_events_no_delete;
DROP TRIGGER quote_snapshots_no_delete;
DROP TRIGGER basket_events_no_delete;
CREATE TABLE checkout_orders_0023_copy AS SELECT * FROM checkout_orders;
DROP TABLE checkout_orders;
CREATE TABLE checkout_orders (
  id                 TEXT PRIMARY KEY,
  reference          TEXT NOT NULL UNIQUE CHECK (reference GLOB 'PA-O-*'),
  artist_id          TEXT NOT NULL,
  artwork_id         TEXT NOT NULL,
  enquiry_ref        TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('draft','awaiting_artist','quoted','checkout_open','paid','dispatched','delivered','closed',
                                                      'expired','cancelled','payment_failed','refund_pending','refunded','disputed')),
  payment_status     TEXT NOT NULL DEFAULT 'none' CHECK (payment_status IN ('none','open','paid','failed','partially_refunded','refunded')),
  fulfilment_status  TEXT NOT NULL DEFAULT 'none' CHECK (fulfilment_status IN ('none','dispatched','delivered')),
  dispute_status     TEXT NOT NULL DEFAULT 'none' CHECK (dispute_status IN ('none','open','won','lost')),
  needs_resolution   TEXT,                                   -- set when a payment arrives that cannot complete a sale (e.g. already sold)
  processing         TEXT,                                   -- JSON (Model B): Stripe's actual processing fee + VAT on it, what PlotArt reimbursed, any shortfall owed outside Stripe
  dispute_fees       TEXT,                                   -- JSON: per dispute, whether Stripe supplied its fee lines ('recorded') or not ('unavailable')
  quote_sha256       TEXT,                                   -- fingerprint of the issued quote snapshot (quote_snapshots)
  currency           TEXT NOT NULL DEFAULT 'eur' CHECK (currency = 'eur'),
  artwork_cents      INTEGER CHECK (artwork_cents IS NULL OR artwork_cents BETWEEN 100 AND 99999999),   -- 0023: up to Stripe's largest single EUR payment
  delivery_cents     INTEGER CHECK (delivery_cents IS NULL OR delivery_cents BETWEEN 0 AND 200000),
  commission_bp      INTEGER CHECK (commission_bp IS NULL OR commission_bp BETWEEN 0 AND 1500),
  commission_cents   INTEGER,
  commission_basis   TEXT,
  entitlement        TEXT,                                   -- JSON evidence for the commission decision
  exclusion          TEXT,
  negotiation_note   TEXT CHECK (negotiation_note IS NULL OR length(negotiation_note) <= 1000),
  delivery           TEXT,                                   -- JSON: packing, transport, cover, receipt, returns (rules.cleanDelivery)
  artwork_snapshot   TEXT,                                   -- JSON: title, dimensions, medium as quoted
  seller             TEXT,                                   -- JSON: the seller's identity as shown to the buyer
  quote_version      INTEGER NOT NULL DEFAULT 1,
  artist_approved_version INTEGER,
  artist_approved_at TEXT,
  artist_confirmations TEXT,                                 -- JSON: availability, location, condition, framing, dimensions, packing
  quote_issued_at    TEXT,
  quote_expires_at   TEXT,
  addendum_doc_id    TEXT,
  buyer_terms_doc_id TEXT,
  buyer_terms_accepted_at TEXT,
  buyer_token_hash   TEXT UNIQUE,
  buyer_email        TEXT,
  provider_account   TEXT,
  payment_intent     TEXT UNIQUE,
  charge_id          TEXT UNIQUE,
  application_fee_id TEXT,
  amount_received_cents INTEGER,
  paid_at            TEXT,
  linked_order_check TEXT,                                   -- JSON: linked-order safeguard result and founder's confirmation (operational only; not an AML assessment)
  retain_until       TEXT,                                   -- fixed when the order ends: 31 Dec of the 6th year after the last money movement, or +2 years if none
  livemode           INTEGER NOT NULL DEFAULT 0 CHECK (livemode IN (0, 1)),
  created_by         TEXT NOT NULL,
  created_at         TEXT NOT NULL,
  updated_at         TEXT NOT NULL,
  CHECK (commission_cents IS NULL OR (commission_cents >= 0 AND commission_cents <= artwork_cents))
);
INSERT INTO checkout_orders (id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, fulfilment_status, dispute_status, needs_resolution, processing, dispute_fees, quote_sha256, currency, artwork_cents, delivery_cents, commission_bp, commission_cents, commission_basis, entitlement, exclusion, negotiation_note, delivery, artwork_snapshot, seller, quote_version, artist_approved_version, artist_approved_at, artist_confirmations, quote_issued_at, quote_expires_at, addendum_doc_id, buyer_terms_doc_id, buyer_terms_accepted_at, buyer_token_hash, buyer_email, provider_account, payment_intent, charge_id, application_fee_id, amount_received_cents, paid_at, linked_order_check, retain_until, livemode, created_by, created_at, updated_at)
  SELECT id, reference, artist_id, artwork_id, enquiry_ref, status, payment_status, fulfilment_status, dispute_status, needs_resolution, processing, dispute_fees, quote_sha256, currency, artwork_cents, delivery_cents, commission_bp, commission_cents, commission_basis, entitlement, exclusion, negotiation_note, delivery, artwork_snapshot, seller, quote_version, artist_approved_version, artist_approved_at, artist_confirmations, quote_issued_at, quote_expires_at, addendum_doc_id, buyer_terms_doc_id, buyer_terms_accepted_at, buyer_token_hash, buyer_email, provider_account, payment_intent, charge_id, application_fee_id, amount_received_cents, paid_at, linked_order_check, retain_until, livemode, created_by, created_at, updated_at FROM checkout_orders_0023_copy;
DROP TABLE checkout_orders_0023_copy;
CREATE INDEX IF NOT EXISTS checkout_orders_artist ON checkout_orders(artist_id, created_at);
CREATE INDEX IF NOT EXISTS checkout_orders_artwork ON checkout_orders(artwork_id);
CREATE INDEX IF NOT EXISTS checkout_orders_buyer ON checkout_orders(buyer_email COLLATE NOCASE, created_at);
CREATE TRIGGER IF NOT EXISTS checkout_orders_no_delete BEFORE DELETE ON checkout_orders
WHEN OLD.retain_until IS NULL OR julianday(OLD.retain_until) > julianday('now')
  OR EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.id AND h.released_at IS NULL)
  OR OLD.dispute_status = 'open'
BEGIN SELECT RAISE(ABORT, 'an order is kept until its retention period has ended, no legal hold is active and no dispute is open'); END;
-- a retention date is fixed once set: never shortened, never extended (keeping records longer is done by a reviewed hold)
CREATE TRIGGER IF NOT EXISTS checkout_orders_retention_fixed BEFORE UPDATE OF retain_until ON checkout_orders
WHEN OLD.retain_until IS NOT NULL AND (NEW.retain_until IS NULL OR NEW.retain_until <> OLD.retain_until)
BEGIN SELECT RAISE(ABORT, 'a retention date is fixed once set; place a reviewed legal hold instead'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_no_delete BEFORE DELETE ON payment_pilot_events
WHEN EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artist_id = OLD.artist_id)
  OR NOT EXISTS (SELECT 1 FROM payment_pilot_events e WHERE e.artist_id = OLD.artist_id AND e.kind = 'left' AND julianday(e.at) <= julianday('now', '-6 years')
    AND e.at = (SELECT MAX(x.at) FROM payment_pilot_events x WHERE x.artist_id = OLD.artist_id))
BEGIN SELECT RAISE(ABORT, 'payment_pilot_events is kept until six years after the artist left and their orders are gone'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS artwork_sales_no_delete BEFORE DELETE ON artwork_sales
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'artwork_sales rows are kept with their order (retention and legal holds); release them with a reason'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS order_ledger_no_delete BEFORE DELETE ON order_ledger
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_ledger is append-only until its order''s retention period has ended and no legal hold is active'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS order_fulfilment_events_no_delete BEFORE DELETE ON order_fulfilment_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_fulfilment_events is append-only until its order''s retention period has ended and no legal hold is active'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS order_events_no_delete BEFORE DELETE ON order_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_events is append-only until its order''s retention period has ended and no legal hold is active'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS checkout_holds_no_delete BEFORE DELETE ON checkout_holds
WHEN OLD.released_at IS NULL OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'a hold is deleted only after release, with its order, once retention has ended'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS checkout_hold_events_no_delete BEFORE DELETE ON checkout_hold_events
WHEN EXISTS (SELECT 1 FROM checkout_holds h WHERE h.id = OLD.hold_id AND h.released_at IS NULL)
  OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hold history is kept with its order'); END;
-- recreated exactly as in 0017_managed_checkout_pilot.sql
CREATE TRIGGER IF NOT EXISTS quote_snapshots_no_delete BEFORE DELETE ON quote_snapshots
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'quote_snapshots are kept with their order'); END;
-- recreated exactly as in 0019_multi_artist_basket.sql
CREATE TRIGGER IF NOT EXISTS basket_events_no_delete BEFORE DELETE ON basket_events
WHEN EXISTS (SELECT 1 FROM basket_lines l JOIN checkout_orders o ON o.id = l.order_id WHERE l.basket_id = OLD.basket_id
  AND (o.retain_until IS NULL OR julianday(o.retain_until) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'basket history is kept with its orders'); END;
