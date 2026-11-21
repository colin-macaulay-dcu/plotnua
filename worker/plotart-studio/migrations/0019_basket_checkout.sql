-- PlotArt Studio · migration 0019 · Multi-artist basket checkout: records design (Phase 1, revision 3 after two reviews,
-- 21 Nov 2026). PROPOSAL FOR FOUNDER REVIEW. NOT APPLIED to any real database (production or TEST). Not mirrored into
-- schema.sql yet: that follows only once this exact file is approved.
-- Model: one buyer payment on PlotArt's platform account ("separate charges and transfers"), then Stripe transfers to each
-- artist. Amounts come from src/basket-rules.js; these tables record them and refuse anything the rules would never produce.
-- All money is integer euro cents. Every provider-facing row records livemode (0 test, 1 live) and must match its basket.
--
-- POLICY (migration-check.py, 6 Nov 2026): every trigger here is a refusal-only BEFORE trigger on a table THIS migration
-- creates. No existing table, column, index, trigger or row is changed. The only writes are to new tables: the seeded TEST
-- basket terms, and a backfill of artwork claims for single-artist holds and sales that already exist.
--
-- ONE ORIGINAL, ONE SALE, ACROSS BOTH CHECKOUTS (artwork_claims). Every hold and sale of an original, by either checkout,
-- takes the artwork's single claim row (PRIMARY KEY artwork_id) in the SAME transaction (one D1 batch) as the hold or sale
-- itself. D1 runs all writes to a database one at a time and a batch as one transaction, so two checkouts can never both
-- take the claim: the second statement fails and its whole batch rolls back. The single-artist checkout (checkout.js) takes
-- claims once this migration exists and asserts it holds the claim (artwork_claim_assertions) in the same batch as its
-- hold, sale or reinstatement; the basket tables refuse any hold or sale without the basket's own claim, and also check the
-- single-artist tables directly. A basket claim is refused until the claims-aware single-artist checkout has recorded
-- itself (checkout_capabilities), so baskets cannot run beside an older checkout that does not take claims.
-- Cross-checkout decisions use ONE clock: the database's (julianday('now')). A hold stays valid while it has not expired OR
-- its checkout is still open (a payment may be in flight; a delayed webhook never loses a buyer their priority).
-- ROLLBACK SAFETY: every basket hold and sale must also mark the artwork reserved / sold in artworks.availability in the SAME
-- transaction (enforced on artwork_claims). Every version of checkout.js, including those older than this migration, refuses
-- an artwork that is not 'available' when quoting, opening checkout and recording a payment, so a rolled-back or mixed
-- deployment cannot sell a basket-held or basket-sold original (see the PR for the residual race and artist-edit cases).
-- REPLACE: SQLite's INSERT OR REPLACE deletes conflicting rows without firing DELETE triggers. Every financial and claim table
-- therefore refuses an INSERT that conflicts with any of its unique keys (the *_no_replace triggers).
--
-- Other integrity rules: strict basket status machine (created only as a draft; reconciled once on leaving draft; no
-- reopening; no backwards moves except those a failed refund requires); approved basket terms and commission-free
-- eligibility enforced here (basket_terms: TEST placeholders only; live terms only by a later reviewed migration);
-- deterministic idempotency keys; caps on transfers, reversals, refunds and disputes; reversals and adjustments bound to the
-- refund or dispute that caused them and capped by that artist's liability for it; every non-standard payment or adjustment
-- carries a written reason; financial rows are never deleted and their amounts never change.
-- Retention/erasure of basket records is not designed yet: these rows are kept (no deletion path) until it is.
-- No foreign keys to artists/artworks or to the single-artist tables.

-- 0 · Approved basket terms. TEST placeholders only (livemode 0). No live terms exist: adding them needs new artist and
--     buyer terms approved by the founder AND a later reviewed migration (this table refuses every other insert).
CREATE TABLE IF NOT EXISTS basket_terms (
  doc_id               TEXT PRIMARY KEY,
  buyer_terms_doc      TEXT NOT NULL UNIQUE,
  livemode             INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  commission_free_lines INTEGER NOT NULL CHECK (commission_free_lines IN (0, 1)),
  permits              TEXT NOT NULL CHECK (json_valid(permits)),
  note                 TEXT NOT NULL,
  CHECK ((livemode = 0) = (doc_id GLOB '*-TEST-*') AND (livemode = 0) = (buyer_terms_doc GLOB '*-TEST-*')),
  CHECK (doc_id NOT IN ('PA-PAY-2026-11', 'PA-BPT-2026-11') AND buyer_terms_doc NOT IN ('PA-PAY-2026-11', 'PA-BPT-2026-11'))
);
INSERT OR IGNORE INTO basket_terms (doc_id, buyer_terms_doc, livemode, commission_free_lines, permits, note) VALUES
  ('PA-BASKET-TEST-01', 'PA-BASKET-BPT-TEST-01', 0, 0, '{"processing_fee_bearer":["plotart","artists_pro_rata"],"transfer_timing":["on_payment","after_delivery","after_cancellation_window"],"dispute_loss_bearer":["plotart","artists_by_line"],"dispute_fee_bearer":["plotart","artists_by_line"],"basket_introduction":["logged_enquiry_only"]}', 'TEST placeholder: synthetic, not real terms'),
  ('PA-BASKET-TEST-02', 'PA-BASKET-BPT-TEST-02', 0, 1, '{"processing_fee_bearer":["plotart","artists_pro_rata"],"transfer_timing":["on_payment","after_delivery","after_cancellation_window"],"dispute_loss_bearer":["plotart","artists_by_line"],"dispute_fee_bearer":["plotart","artists_by_line"],"basket_introduction":["logged_enquiry_only"]}', 'TEST placeholder permitting commission-free lines: synthetic, not real terms'),
  ('PA-BASKET-TEST-03', 'PA-BASKET-BPT-TEST-03', 0, 0, '{"processing_fee_bearer":["plotart"],"transfer_timing":["on_payment"],"dispute_loss_bearer":["plotart"],"dispute_fee_bearer":["plotart"],"basket_introduction":["logged_enquiry_only"]}', 'TEST placeholder permitting only some decisions: synthetic, not real terms');
CREATE TRIGGER IF NOT EXISTS basket_terms_seed_only BEFORE INSERT ON basket_terms
WHEN NEW.livemode <> 0 OR NEW.doc_id NOT IN ('PA-BASKET-TEST-01', 'PA-BASKET-TEST-02', 'PA-BASKET-TEST-03')
BEGIN SELECT RAISE(ABORT, 'basket terms are added only by a reviewed migration after the founder approves them'); END;
CREATE TRIGGER IF NOT EXISTS basket_terms_fixed BEFORE UPDATE ON basket_terms
BEGIN SELECT RAISE(ABORT, 'basket terms never change: a new text gets a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS basket_terms_no_delete BEFORE DELETE ON basket_terms
BEGIN SELECT RAISE(ABORT, 'basket terms are never removed'); END;

-- 1 · Basket orders --------------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS basket_orders (
  id                  TEXT PRIMARY KEY,
  reference           TEXT NOT NULL UNIQUE CHECK (reference GLOB 'PA-B-*'),
  status              TEXT NOT NULL CHECK (status IN ('draft','checkout_open','paid','payment_failed','expired','cancelled',
                                                      'partially_refunded','refunded','disputed','closed')),
  payment_status      TEXT NOT NULL DEFAULT 'none' CHECK (payment_status IN ('none','open','paid','failed','partially_refunded','refunded')),
  dispute_status      TEXT NOT NULL DEFAULT 'none' CHECK (dispute_status IN ('none','open','won','lost')),
  buyer_email         TEXT COLLATE NOCASE,
  livemode            INTEGER NOT NULL DEFAULT 0 CHECK (livemode IN (0, 1)),
  currency            TEXT NOT NULL DEFAULT 'eur' CHECK (currency = 'eur'),
  total_cents         INTEGER NOT NULL CHECK (total_cents > 0 AND total_cents < 1000000),   -- below EUR 10,000 (pilot AML scope)
  commission_cents    INTEGER NOT NULL CHECK (commission_cents >= 0 AND commission_cents <= total_cents),
  plan_version        TEXT NOT NULL,
  plan_sha256         TEXT NOT NULL CHECK (length(plan_sha256) = 64),
  decisions           TEXT NOT NULL CHECK (json_valid(decisions)),
  artist_terms_doc    TEXT NOT NULL REFERENCES basket_terms(doc_id),
  buyer_terms_doc     TEXT NOT NULL,
  transfer_group      TEXT NOT NULL UNIQUE CHECK (transfer_group = 'plotart-basket-' || id),
  reconciled_at       TEXT,                    -- set once, when the basket leaves draft and its totals reconcile
  checkout_session_id TEXT UNIQUE,
  payment_intent_id   TEXT UNIQUE CHECK (payment_intent_id IS NULL OR payment_intent_id GLOB 'pi_*'),
  charge_id           TEXT UNIQUE CHECK (charge_id IS NULL OR charge_id GLOB 'ch_*' OR charge_id GLOB 'py_*'),
  fee_cents           INTEGER CHECK (fee_cents IS NULL OR fee_cents >= 0),
  fee_vat_cents       INTEGER CHECK (fee_vat_cents IS NULL OR fee_vat_cents >= 0),
  paid_at             TEXT,
  settled_at          TEXT,
  needs_resolution    TEXT,
  created_by          TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  CHECK ((fee_cents IS NULL) = (fee_vat_cents IS NULL)),
  CHECK ((settled_at IS NULL) = (fee_cents IS NULL)),
  CHECK (fee_cents IS NULL OR charge_id IS NOT NULL),
  CHECK (checkout_session_id IS NULL OR (livemode = 0 AND checkout_session_id GLOB 'cs_test_*') OR (livemode = 1 AND checkout_session_id GLOB 'cs_live_*')),
  CHECK (status <> 'draft' OR reconciled_at IS NULL),                          -- a draft is never reconciled
  CHECK (status IN ('draft', 'cancelled') OR reconciled_at IS NOT NULL),       -- every other status needs reconciliation
  CHECK (payment_status NOT IN ('paid', 'partially_refunded', 'refunded') OR charge_id IS NOT NULL),
  CHECK ((status IN ('paid','partially_refunded','refunded','disputed','closed')) = (payment_status IN ('paid','partially_refunded','refunded')))
);
CREATE INDEX IF NOT EXISTS basket_orders_buyer ON basket_orders(buyer_email, created_at);
CREATE INDEX IF NOT EXISTS basket_orders_status ON basket_orders(status, updated_at);
-- created only as an empty draft, under approved basket terms whose permitted decisions include this basket's
CREATE TRIGGER IF NOT EXISTS basket_orders_insert_draft BEFORE INSERT ON basket_orders
WHEN NEW.status <> 'draft' OR NEW.payment_status <> 'none' OR NEW.dispute_status <> 'none' OR NEW.reconciled_at IS NOT NULL
  OR NEW.checkout_session_id IS NOT NULL OR NEW.payment_intent_id IS NOT NULL OR NEW.charge_id IS NOT NULL OR NEW.fee_cents IS NOT NULL
  OR NEW.paid_at IS NOT NULL OR NEW.settled_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'a basket is created only as an unpaid draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_insert_terms BEFORE INSERT ON basket_orders
WHEN NOT EXISTS (SELECT 1 FROM basket_terms t WHERE t.doc_id = NEW.artist_terms_doc AND t.buyer_terms_doc = NEW.buyer_terms_doc AND t.livemode = NEW.livemode
  AND EXISTS (SELECT 1 FROM json_each(t.permits, '$.processing_fee_bearer') WHERE value = json_extract(NEW.decisions, '$.processing_fee_bearer'))
  AND EXISTS (SELECT 1 FROM json_each(t.permits, '$.transfer_timing') WHERE value = json_extract(NEW.decisions, '$.transfer_timing'))
  AND EXISTS (SELECT 1 FROM json_each(t.permits, '$.dispute_loss_bearer') WHERE value = json_extract(NEW.decisions, '$.dispute_loss_bearer'))
  AND EXISTS (SELECT 1 FROM json_each(t.permits, '$.dispute_fee_bearer') WHERE value = json_extract(NEW.decisions, '$.dispute_fee_bearer'))
  AND EXISTS (SELECT 1 FROM json_each(t.permits, '$.basket_introduction') WHERE value = json_extract(NEW.decisions, '$.basket_introduction')))
BEGIN SELECT RAISE(ABORT, 'a basket needs approved basket terms of its mode that permit every one of its founder decisions'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_fixed BEFORE UPDATE ON basket_orders
WHEN NEW.id <> OLD.id OR NEW.reference <> OLD.reference OR NEW.total_cents <> OLD.total_cents OR NEW.commission_cents <> OLD.commission_cents
  OR NEW.plan_version <> OLD.plan_version OR NEW.plan_sha256 <> OLD.plan_sha256 OR NEW.decisions <> OLD.decisions
  OR NEW.artist_terms_doc <> OLD.artist_terms_doc OR NEW.buyer_terms_doc <> OLD.buyer_terms_doc OR NEW.transfer_group <> OLD.transfer_group
  OR NEW.livemode <> OLD.livemode OR NEW.currency <> OLD.currency OR NEW.created_at <> OLD.created_at OR NEW.created_by <> OLD.created_by
BEGIN SELECT RAISE(ABORT, 'a basket''s plan, terms, decisions, money and mode never change: start a new basket'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_buyer_fixed BEFORE UPDATE OF buyer_email ON basket_orders
WHEN OLD.status <> 'draft' AND NEW.buyer_email IS NOT OLD.buyer_email
BEGIN SELECT RAISE(ABORT, 'the buyer''s email address is fixed once checkout opens'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_ids_once BEFORE UPDATE ON basket_orders
WHEN (OLD.checkout_session_id IS NOT NULL AND NEW.checkout_session_id IS NOT OLD.checkout_session_id)
  OR (OLD.payment_intent_id IS NOT NULL AND NEW.payment_intent_id IS NOT OLD.payment_intent_id)
  OR (OLD.charge_id IS NOT NULL AND NEW.charge_id IS NOT OLD.charge_id)
  OR (OLD.paid_at IS NOT NULL AND NEW.paid_at IS NOT OLD.paid_at)
BEGIN SELECT RAISE(ABORT, 'a basket''s Stripe identifiers and payment time are written once and never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_settlement_once BEFORE UPDATE ON basket_orders
WHEN OLD.fee_cents IS NOT NULL AND (NEW.fee_cents IS NOT OLD.fee_cents OR NEW.fee_vat_cents IS NOT OLD.fee_vat_cents OR NEW.settled_at IS NOT OLD.settled_at)
BEGIN SELECT RAISE(ABORT, 'the processing fee and settlement are recorded once and never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_reconciled_once BEFORE UPDATE OF reconciled_at ON basket_orders
WHEN (OLD.reconciled_at IS NOT NULL AND NEW.reconciled_at IS NOT OLD.reconciled_at) OR (OLD.reconciled_at IS NULL AND NEW.reconciled_at IS NOT NULL AND OLD.status <> 'draft')
BEGIN SELECT RAISE(ABORT, 'a basket is reconciled once, as it leaves draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_reconcile BEFORE UPDATE OF reconciled_at ON basket_orders
WHEN OLD.reconciled_at IS NULL AND NEW.reconciled_at IS NOT NULL AND (
     NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.id)
  OR NEW.total_cents <> (SELECT COALESCE(SUM(artwork_cents), 0) FROM basket_lines WHERE basket_id = NEW.id)
                      + (SELECT COALESCE(SUM(delivery_cents + insurance_cents), 0) FROM basket_shipments WHERE basket_id = NEW.id)
  OR NEW.commission_cents <> (SELECT COALESCE(SUM(commission_cents), 0) FROM basket_lines WHERE basket_id = NEW.id)
  OR NEW.total_cents <> (SELECT COALESCE(SUM(gross_cents), 0) FROM basket_artist_allocations WHERE basket_id = NEW.id)
  OR NEW.commission_cents <> (SELECT COALESCE(SUM(commission_cents), 0) FROM basket_artist_allocations WHERE basket_id = NEW.id)
  OR EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.id AND NOT EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.id AND a.artist_id = l.artist_id))
  OR EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.id AND (a.gross_cents <>
       (SELECT COALESCE(SUM(artwork_cents), 0) FROM basket_lines WHERE basket_id = NEW.id AND artist_id = a.artist_id)
     + (SELECT COALESCE(SUM(delivery_cents + insurance_cents), 0) FROM basket_shipments WHERE basket_id = NEW.id AND artist_id = a.artist_id)
     OR a.commission_cents <> (SELECT COALESCE(SUM(commission_cents), 0) FROM basket_lines WHERE basket_id = NEW.id AND artist_id = a.artist_id))))
BEGIN SELECT RAISE(ABORT, 'the basket does not reconcile: total, commission and artist allocations must equal its lines and shipments'); END;
-- the status machine: only these moves. Backwards moves exist only for a refund that later failed (checked below).
CREATE TRIGGER IF NOT EXISTS basket_orders_status_moves BEFORE UPDATE OF status ON basket_orders
WHEN NEW.status <> OLD.status AND NOT (
     (OLD.status = 'draft' AND NEW.status IN ('checkout_open','cancelled'))
  OR (OLD.status = 'checkout_open' AND NEW.status IN ('paid','payment_failed','expired','cancelled'))
  OR (OLD.status = 'payment_failed' AND NEW.status IN ('checkout_open','paid','expired','cancelled'))
  OR (OLD.status = 'expired' AND NEW.status IN ('paid','cancelled'))
  OR (OLD.status = 'cancelled' AND NEW.status = 'paid' AND OLD.checkout_session_id IS NOT NULL)
  OR (OLD.status = 'paid' AND NEW.status IN ('partially_refunded','refunded','disputed','closed'))
  OR (OLD.status = 'partially_refunded' AND NEW.status IN ('refunded','disputed','closed','paid'))
  OR (OLD.status = 'refunded' AND NEW.status IN ('paid','partially_refunded','disputed','closed'))
  OR (OLD.status = 'disputed' AND NEW.status IN ('paid','partially_refunded','refunded','closed')))
BEGIN SELECT RAISE(ABORT, 'that basket status change is not allowed'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_status_back_needs_failed_refund BEFORE UPDATE OF status ON basket_orders
WHEN OLD.status IN ('partially_refunded','refunded') AND NEW.status IN ('paid','partially_refunded') AND NEW.status <> OLD.status
  AND NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.basket_id = NEW.id AND r.status IN ('failed','canceled'))
BEGIN SELECT RAISE(ABORT, 'a refunded basket returns to paid only when a refund failed or was cancelled'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_payment_moves BEFORE UPDATE OF payment_status ON basket_orders
WHEN NEW.payment_status <> OLD.payment_status AND NOT (
     (OLD.payment_status = 'none' AND NEW.payment_status IN ('open','paid'))
  OR (OLD.payment_status = 'open' AND NEW.payment_status IN ('paid','failed','none'))
  OR (OLD.payment_status = 'failed' AND NEW.payment_status IN ('open','paid'))
  OR (OLD.payment_status = 'paid' AND NEW.payment_status IN ('partially_refunded','refunded'))
  OR (OLD.payment_status = 'partially_refunded' AND NEW.payment_status IN ('refunded','paid'))
  OR (OLD.payment_status = 'refunded' AND NEW.payment_status IN ('partially_refunded','paid')))
BEGIN SELECT RAISE(ABORT, 'that payment status change is not allowed'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_payment_back_needs_failed_refund BEFORE UPDATE OF payment_status ON basket_orders
WHEN OLD.payment_status IN ('partially_refunded','refunded') AND NEW.payment_status IN ('paid','partially_refunded') AND NEW.payment_status <> OLD.payment_status
  AND NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.basket_id = NEW.id AND r.status IN ('failed','canceled'))
BEGIN SELECT RAISE(ABORT, 'refunded money returns to paid only when a refund failed or was cancelled'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_dispute_moves BEFORE UPDATE OF dispute_status ON basket_orders
WHEN NEW.dispute_status <> OLD.dispute_status AND NOT (
     (OLD.dispute_status IN ('none','won','lost') AND NEW.dispute_status = 'open')
  OR (OLD.dispute_status = 'open' AND NEW.dispute_status IN ('won','lost')))
BEGIN SELECT RAISE(ABORT, 'that dispute status change is not allowed'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_no_delete BEFORE DELETE ON basket_orders
WHEN OLD.status <> 'draft'
BEGIN SELECT RAISE(ABORT, 'a basket that left draft is kept with its records'); END;

-- 2 · Shipments: each belongs to ONE artist; delivery and insurance are itemised and never carry commission ---------------
CREATE TABLE IF NOT EXISTS basket_shipments (
  basket_id          TEXT NOT NULL REFERENCES basket_orders(id),
  shipment_id        TEXT NOT NULL,
  artist_id          TEXT NOT NULL,
  method             TEXT NOT NULL CHECK (method IN ('delivery','collection')),
  delivery_cents     INTEGER NOT NULL CHECK (delivery_cents >= 0),
  insurance_cents    INTEGER NOT NULL CHECK (insurance_cents >= 0),
  delivery           TEXT CHECK (delivery IS NULL OR json_valid(delivery)),
  cover              TEXT CHECK (cover IS NULL OR json_valid(cover)),
  fulfilment_status  TEXT NOT NULL DEFAULT 'none' CHECK (fulfilment_status IN ('none','dispatched','delivered','collected')),
  fulfilled_at       TEXT,
  cancellation_ends_at TEXT,
  PRIMARY KEY (basket_id, shipment_id),
  UNIQUE (basket_id, shipment_id, artist_id),
  CHECK (method = 'collection' OR cover IS NOT NULL),
  CHECK (method = 'delivery' OR delivery_cents = 0),
  CHECK (insurance_cents = 0 OR cover IS NOT NULL),
  CHECK (fulfilment_status <> 'collected' OR method = 'collection'),
  CHECK ((fulfilment_status IN ('delivered','collected')) = (fulfilled_at IS NOT NULL)),
  CHECK (cancellation_ends_at IS NULL OR fulfilled_at IS NOT NULL)
);
CREATE TRIGGER IF NOT EXISTS basket_shipments_draft_only_insert BEFORE INSERT ON basket_shipments
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'shipments are added only while the basket is a draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_charges_fixed BEFORE UPDATE ON basket_shipments
WHEN NEW.basket_id <> OLD.basket_id OR NEW.shipment_id <> OLD.shipment_id OR NEW.artist_id <> OLD.artist_id OR NEW.method <> OLD.method
  OR NEW.delivery_cents <> OLD.delivery_cents OR NEW.insurance_cents <> OLD.insurance_cents OR NEW.cover IS NOT OLD.cover
  OR (OLD.fulfilled_at IS NOT NULL AND NEW.fulfilled_at IS NOT OLD.fulfilled_at)
  OR (OLD.cancellation_ends_at IS NOT NULL AND NEW.cancellation_ends_at IS NOT OLD.cancellation_ends_at)
BEGIN SELECT RAISE(ABORT, 'a shipment''s artist, method, charges, cover, delivery time and cancellation deadline never change once recorded'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_fulfilment_forward BEFORE UPDATE OF fulfilment_status ON basket_shipments
WHEN NEW.fulfilment_status <> OLD.fulfilment_status AND NOT (
     (OLD.fulfilment_status = 'none' AND NEW.fulfilment_status IN ('dispatched','delivered','collected'))
  OR (OLD.fulfilment_status = 'dispatched' AND NEW.fulfilment_status = 'delivered'))
BEGIN SELECT RAISE(ABORT, 'fulfilment only moves forward'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_no_delete BEFORE DELETE ON basket_shipments
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'shipments are removed only while the basket is a draft'); END;

-- 3 · Artwork lines: commission per artwork from the existing entitlement rule, bound to its artist, artwork and enquiry ---
CREATE TABLE IF NOT EXISTS basket_lines (
  basket_id            TEXT NOT NULL REFERENCES basket_orders(id),
  line_id              TEXT NOT NULL,
  artist_id            TEXT NOT NULL,
  artwork_id           TEXT NOT NULL,
  shipment_id          TEXT NOT NULL,
  title                TEXT,
  artwork_cents        INTEGER NOT NULL CHECK (artwork_cents BETWEEN 100 AND 999999),
  commission_bp        INTEGER NOT NULL CHECK (commission_bp BETWEEN 0 AND 1500),
  commission_cents     INTEGER NOT NULL CHECK (commission_cents >= 0),
  commission_basis     TEXT NOT NULL,
  entitlement_evidence TEXT NOT NULL CHECK (json_valid(entitlement_evidence)
                         AND json_extract(entitlement_evidence, '$.binding.artist_id') = artist_id
                         AND json_extract(entitlement_evidence, '$.binding.artwork_id') = artwork_id
                         AND json_extract(entitlement_evidence, '$.binding.enquiry_ref') = enquiry_ref),
  enquiry_ref          TEXT NOT NULL,
  processing_consent   INTEGER NOT NULL DEFAULT 0 CHECK (processing_consent IN (0, 1)),   -- as RECORDED, never as supplied
  processing_consent_at TEXT,
  PRIMARY KEY (basket_id, line_id),
  UNIQUE (basket_id, artwork_id),
  UNIQUE (basket_id, enquiry_ref),
  FOREIGN KEY (basket_id, shipment_id, artist_id) REFERENCES basket_shipments(basket_id, shipment_id, artist_id),
  CHECK (commission_cents = (artwork_cents * commission_bp) / 10000),
  CHECK ((processing_consent = 1) = (processing_consent_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS basket_lines_artwork ON basket_lines(artwork_id);
CREATE TRIGGER IF NOT EXISTS basket_lines_draft_only_insert BEFORE INSERT ON basket_lines
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'lines are added only while the basket is a draft'); END;
-- a commission-free line (Founding 25 and other 0% sales) only under basket terms that expressly permit it
CREATE TRIGGER IF NOT EXISTS basket_lines_commission_free_gate BEFORE INSERT ON basket_lines
WHEN NEW.commission_bp = 0 AND NOT EXISTS (SELECT 1 FROM basket_orders o JOIN basket_terms t ON t.doc_id = o.artist_terms_doc
  WHERE o.id = NEW.basket_id AND t.commission_free_lines = 1)
BEGIN SELECT RAISE(ABORT, 'commission-free lines stay on direct payment unless approved basket terms expressly permit them'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_processing_consent BEFORE INSERT ON basket_lines
WHEN NEW.commission_bp = 0 AND NEW.processing_consent = 0 AND EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id
  AND json_extract(o.decisions, '$.processing_fee_bearer') = 'artists_pro_rata')
BEGIN SELECT RAISE(ABORT, 'a commission-free line bearing processing fees needs the artist''s recorded consent'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_fixed BEFORE UPDATE ON basket_lines
BEGIN SELECT RAISE(ABORT, 'a basket line never changes once recorded'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_no_delete BEFORE DELETE ON basket_lines
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'lines are removed only while the basket is a draft'); END;

-- 4 · Artist allocations --------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS basket_artist_allocations (
  basket_id                 TEXT NOT NULL REFERENCES basket_orders(id),
  artist_id                 TEXT NOT NULL,
  account_id                TEXT NOT NULL CHECK (account_id GLOB 'acct_*'),
  gross_cents               INTEGER NOT NULL CHECK (gross_cents >= 0),
  commission_cents          INTEGER NOT NULL CHECK (commission_cents >= 0),
  delivery_cents            INTEGER NOT NULL CHECK (delivery_cents >= 0),
  insurance_cents           INTEGER NOT NULL CHECK (insurance_cents >= 0),
  transfer_before_fees_cents INTEGER NOT NULL CHECK (transfer_before_fees_cents >= 0),
  processing_share_cents    INTEGER CHECK (processing_share_cents IS NULL OR processing_share_cents >= 0),
  transfer_due_cents        INTEGER CHECK (transfer_due_cents IS NULL OR transfer_due_cents >= 0),
  release                   TEXT NOT NULL CHECK (release IN ('on_payment','after_delivery','after_cancellation_window')),
  release_ready_at          TEXT,
  status                    TEXT NOT NULL DEFAULT 'awaiting_settlement' CHECK (status IN ('awaiting_settlement','held','ready','transferred','closed')),
  updated_at                TEXT NOT NULL,
  PRIMARY KEY (basket_id, artist_id),
  CHECK (gross_cents = commission_cents + transfer_before_fees_cents),
  CHECK ((processing_share_cents IS NULL) = (transfer_due_cents IS NULL)),
  CHECK (transfer_due_cents IS NULL OR transfer_due_cents = transfer_before_fees_cents - processing_share_cents),
  CHECK (release_ready_at IS NULL OR transfer_due_cents IS NOT NULL)
);
CREATE TRIGGER IF NOT EXISTS basket_allocations_draft_only_insert BEFORE INSERT ON basket_artist_allocations
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft') OR NEW.transfer_due_cents IS NOT NULL OR NEW.release_ready_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'allocations are added only while the basket is a draft, before settlement and release'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_fixed BEFORE UPDATE ON basket_artist_allocations
WHEN NEW.basket_id <> OLD.basket_id OR NEW.artist_id <> OLD.artist_id OR NEW.account_id <> OLD.account_id OR NEW.gross_cents <> OLD.gross_cents
  OR NEW.commission_cents <> OLD.commission_cents OR NEW.delivery_cents <> OLD.delivery_cents OR NEW.insurance_cents <> OLD.insurance_cents
  OR NEW.transfer_before_fees_cents <> OLD.transfer_before_fees_cents OR NEW.release <> OLD.release
  OR (OLD.transfer_due_cents IS NOT NULL AND (NEW.transfer_due_cents IS NOT OLD.transfer_due_cents OR NEW.processing_share_cents IS NOT OLD.processing_share_cents))
  OR (OLD.release_ready_at IS NOT NULL AND NEW.release_ready_at IS NOT OLD.release_ready_at)
BEGIN SELECT RAISE(ABORT, 'an allocation never changes; its settlement and release are written once'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_settle_after_fee BEFORE UPDATE ON basket_artist_allocations
WHEN OLD.transfer_due_cents IS NULL AND NEW.transfer_due_cents IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.settled_at IS NOT NULL)
BEGIN SELECT RAISE(ABORT, 'an allocation is settled only after the basket''s processing fee is recorded'); END;
-- release only when its condition is met: paid; and delivered/collected, or the cancellation period ended, as decided
CREATE TRIGGER IF NOT EXISTS basket_allocations_release_earned BEFORE UPDATE OF release_ready_at ON basket_artist_allocations
WHEN OLD.release_ready_at IS NULL AND NEW.release_ready_at IS NOT NULL AND (
     NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.payment_status IN ('paid','partially_refunded') AND o.paid_at IS NOT NULL
                 AND julianday(NEW.release_ready_at) >= julianday(o.paid_at))
  OR (NEW.release IN ('after_delivery','after_cancellation_window') AND EXISTS (SELECT 1 FROM basket_shipments s WHERE s.basket_id = NEW.basket_id
        AND s.artist_id = NEW.artist_id AND (s.fulfilled_at IS NULL OR julianday(NEW.release_ready_at) < julianday(s.fulfilled_at))))
  OR (NEW.release = 'after_cancellation_window' AND EXISTS (SELECT 1 FROM basket_shipments s WHERE s.basket_id = NEW.basket_id
        AND s.artist_id = NEW.artist_id AND (s.cancellation_ends_at IS NULL OR julianday(NEW.release_ready_at) < julianday(s.cancellation_ends_at)))))
BEGIN SELECT RAISE(ABORT, 'this allocation''s release condition (payment, delivery or the cancellation period) is not met'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_no_delete BEFORE DELETE ON basket_artist_allocations
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'allocations are removed only while the basket is a draft'); END;

-- 5 · Disputes (Stripe debits the whole basket payment from PlotArt's balance) --------------------------------------------
CREATE TABLE IF NOT EXISTS basket_disputes (
  id                 TEXT PRIMARY KEY,
  basket_id          TEXT NOT NULL REFERENCES basket_orders(id),
  stripe_dispute_id  TEXT NOT NULL UNIQUE CHECK (stripe_dispute_id GLOB 'du_*' OR stripe_dispute_id GLOB 'dp_*'),
  amount_cents       INTEGER NOT NULL CHECK (amount_cents > 0),
  fee_cents          INTEGER CHECK (fee_cents IS NULL OR fee_cents >= 0),
  status             TEXT NOT NULL CHECK (status IN ('open','won','lost')),
  reason             TEXT,
  attribution        TEXT CHECK (attribution IS NULL OR json_valid(attribution)),
  livemode           INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  opened_at          TEXT NOT NULL,
  closed_at          TEXT,
  CHECK ((status = 'open') = (closed_at IS NULL)),
  CHECK ((status = 'lost') = (attribution IS NOT NULL))   -- a lost dispute always names the lines/shipments it was for
);
CREATE TRIGGER IF NOT EXISTS basket_disputes_insert_valid BEFORE INSERT ON basket_disputes
WHEN NEW.status <> 'open' OR NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.charge_id IS NOT NULL
  AND o.livemode = NEW.livemode AND NEW.amount_cents <= o.total_cents)
BEGIN SELECT RAISE(ABORT, 'a dispute opens on a paid basket of the same mode, for no more than its total'); END;
-- what can be disputed is what was paid and not refunded, less every dispute still open or lost
CREATE TRIGGER IF NOT EXISTS basket_disputes_cap BEFORE INSERT ON basket_disputes
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_refunds WHERE basket_id = NEW.basket_id AND status IN ('requested','pending','requires_action','succeeded'))
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_disputes WHERE basket_id = NEW.basket_id AND status IN ('open','lost'))
   > (SELECT total_cents FROM basket_orders WHERE id = NEW.basket_id)
BEGIN SELECT RAISE(ABORT, 'the dispute exceeds what remains of the payment after refunds and other disputes'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_update_valid BEFORE UPDATE ON basket_disputes
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.stripe_dispute_id <> OLD.stripe_dispute_id OR NEW.amount_cents <> OLD.amount_cents
  OR NEW.livemode <> OLD.livemode OR NEW.opened_at <> OLD.opened_at OR (OLD.status <> 'open' AND NEW.status <> OLD.status)
  OR (OLD.fee_cents IS NOT NULL AND NEW.fee_cents IS NOT OLD.fee_cents)
  OR (OLD.attribution IS NOT NULL AND NEW.attribution IS NOT OLD.attribution) OR (OLD.closed_at IS NOT NULL AND NEW.closed_at IS NOT OLD.closed_at)
BEGIN SELECT RAISE(ABORT, 'a dispute only moves from open to won or lost; its amount and identifiers never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_attribution_valid BEFORE UPDATE OF status ON basket_disputes
WHEN NEW.status = 'lost' AND OLD.status <> 'lost' AND (
     EXISTS (SELECT 1 FROM json_each(NEW.attribution, '$.lines') j WHERE json_type(j.value, '$.artwork_cents') <> 'integer' OR json_extract(j.value, '$.artwork_cents') <= 0
             OR NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.basket_id AND l.line_id = json_extract(j.value, '$.line_id')))
  OR EXISTS (SELECT 1 FROM json_each(NEW.attribution, '$.shipments') j WHERE json_type(j.value, '$.cents') <> 'integer' OR json_extract(j.value, '$.cents') <= 0
             OR NOT EXISTS (SELECT 1 FROM basket_shipments s WHERE s.basket_id = NEW.basket_id AND s.shipment_id = json_extract(j.value, '$.shipment_id')))
  OR (SELECT COALESCE(SUM(json_extract(value, '$.artwork_cents')), 0) FROM json_each(NEW.attribution, '$.lines'))
   + (SELECT COALESCE(SUM(json_extract(value, '$.cents')), 0) FROM json_each(NEW.attribution, '$.shipments')) <> NEW.amount_cents)
BEGIN SELECT RAISE(ABORT, 'a lost dispute is attributed to lines and shipments of its basket, adding up to the disputed amount'); END;
-- what a line or shipment can still be recovered for: its price, less active refunds of it and other lost disputes of it
CREATE TRIGGER IF NOT EXISTS basket_disputes_attribution_within_lines BEFORE UPDATE OF status ON basket_disputes
WHEN NEW.status = 'lost' AND OLD.status <> 'lost' AND (
     EXISTS (SELECT 1 FROM (SELECT json_extract(value, '$.line_id') AS lid, SUM(json_extract(value, '$.artwork_cents')) AS amt FROM json_each(NEW.attribution, '$.lines') GROUP BY lid) a
       JOIN basket_lines l ON l.basket_id = NEW.basket_id AND l.line_id = a.lid
       WHERE a.amt
         + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r ON r.id = p.refund_id
              WHERE r.basket_id = NEW.basket_id AND p.kind = 'line' AND p.ref = a.lid AND r.status IN ('requested','pending','requires_action','succeeded'))
         + (SELECT COALESCE(SUM(json_extract(j2.value, '$.artwork_cents')), 0) FROM basket_disputes d2, json_each(d2.attribution, '$.lines') j2
              WHERE d2.basket_id = NEW.basket_id AND d2.id <> NEW.id AND d2.status = 'lost' AND json_extract(j2.value, '$.line_id') = a.lid)
         > l.artwork_cents)
  OR EXISTS (SELECT 1 FROM (SELECT json_extract(value, '$.shipment_id') AS sid, SUM(json_extract(value, '$.cents')) AS amt FROM json_each(NEW.attribution, '$.shipments') GROUP BY sid) a
       JOIN basket_shipments s ON s.basket_id = NEW.basket_id AND s.shipment_id = a.sid
       WHERE a.amt
         + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r ON r.id = p.refund_id
              WHERE r.basket_id = NEW.basket_id AND p.kind = 'shipment' AND p.ref = a.sid AND r.status IN ('requested','pending','requires_action','succeeded'))
         + (SELECT COALESCE(SUM(json_extract(j2.value, '$.cents')), 0) FROM basket_disputes d2, json_each(d2.attribution, '$.shipments') j2
              WHERE d2.basket_id = NEW.basket_id AND d2.id <> NEW.id AND d2.status = 'lost' AND json_extract(j2.value, '$.shipment_id') = a.sid)
         > s.delivery_cents + s.insurance_cents))
BEGIN SELECT RAISE(ABORT, 'a lost dispute cannot recover a line or shipment beyond what is left after refunds and other disputes'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_no_delete BEFORE DELETE ON basket_disputes
BEGIN SELECT RAISE(ABORT, 'basket disputes are never deleted'); END;
-- what each artist carries of a LOST dispute (basket-rules dispute()); recorded once, within the dispute's amount and fee
CREATE TABLE IF NOT EXISTS basket_dispute_allocations (
  dispute_id   TEXT NOT NULL REFERENCES basket_disputes(id),
  artist_id    TEXT NOT NULL,
  loss_cents   INTEGER NOT NULL CHECK (loss_cents >= 0),
  fee_cents    INTEGER NOT NULL CHECK (fee_cents >= 0),
  recorded_by  TEXT NOT NULL,
  recorded_at  TEXT NOT NULL,
  PRIMARY KEY (dispute_id, artist_id),
  CHECK (loss_cents + fee_cents > 0)
);
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_valid BEFORE INSERT ON basket_dispute_allocations
WHEN NOT EXISTS (SELECT 1 FROM basket_disputes d JOIN basket_artist_allocations a ON a.basket_id = d.basket_id
                 WHERE d.id = NEW.dispute_id AND d.status = 'lost' AND a.artist_id = NEW.artist_id)
  OR NEW.loss_cents + (SELECT COALESCE(SUM(loss_cents), 0) FROM basket_dispute_allocations WHERE dispute_id = NEW.dispute_id)
     > (SELECT amount_cents FROM basket_disputes WHERE id = NEW.dispute_id)
  OR NEW.fee_cents + (SELECT COALESCE(SUM(fee_cents), 0) FROM basket_dispute_allocations WHERE dispute_id = NEW.dispute_id)
     > (SELECT COALESCE(fee_cents, 0) FROM basket_disputes WHERE id = NEW.dispute_id)
BEGIN SELECT RAISE(ABORT, 'an artist''s share of a lost dispute must be for an artist of that basket and within the dispute''s amount and fee'); END;
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_by_decision BEFORE INSERT ON basket_dispute_allocations
WHEN (NEW.loss_cents > 0 AND EXISTS (SELECT 1 FROM basket_disputes d JOIN basket_orders o ON o.id = d.basket_id WHERE d.id = NEW.dispute_id
        AND json_extract(o.decisions, '$.dispute_loss_bearer') <> 'artists_by_line'))
  OR (NEW.fee_cents > 0 AND EXISTS (SELECT 1 FROM basket_disputes d JOIN basket_orders o ON o.id = d.basket_id WHERE d.id = NEW.dispute_id
        AND json_extract(o.decisions, '$.dispute_fee_bearer') <> 'artists_by_line'))
BEGIN SELECT RAISE(ABORT, 'the founder decisions for this basket put that part of a lost dispute on PlotArt, not the artist'); END;
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_within_share BEFORE INSERT ON basket_dispute_allocations
WHEN NEW.loss_cents > (SELECT COALESCE(SUM(json_extract(j.value, '$.artwork_cents')), 0) FROM basket_disputes d, json_each(d.attribution, '$.lines') j
       JOIN basket_lines l ON l.basket_id = d.basket_id AND l.line_id = json_extract(j.value, '$.line_id') WHERE d.id = NEW.dispute_id AND l.artist_id = NEW.artist_id)
   + (SELECT COALESCE(SUM(json_extract(j.value, '$.cents')), 0) FROM basket_disputes d, json_each(d.attribution, '$.shipments') j
       JOIN basket_shipments s ON s.basket_id = d.basket_id AND s.shipment_id = json_extract(j.value, '$.shipment_id') WHERE d.id = NEW.dispute_id AND s.artist_id = NEW.artist_id)
  OR (NEW.fee_cents > 0 AND NOT EXISTS (SELECT 1 FROM basket_disputes d, json_each(d.attribution, '$.lines') j
       JOIN basket_lines l ON l.basket_id = d.basket_id AND l.line_id = json_extract(j.value, '$.line_id') WHERE d.id = NEW.dispute_id AND l.artist_id = NEW.artist_id)
     AND NOT EXISTS (SELECT 1 FROM basket_disputes d, json_each(d.attribution, '$.shipments') j
       JOIN basket_shipments s ON s.basket_id = d.basket_id AND s.shipment_id = json_extract(j.value, '$.shipment_id') WHERE d.id = NEW.dispute_id AND s.artist_id = NEW.artist_id))
BEGIN SELECT RAISE(ABORT, 'an artist carries no more of a lost dispute than the lines and shipments of theirs it was attributed to'); END;
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_no_update BEFORE UPDATE ON basket_dispute_allocations
BEGIN SELECT RAISE(ABORT, 'basket_dispute_allocations is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_no_delete BEFORE DELETE ON basket_dispute_allocations
BEGIN SELECT RAISE(ABORT, 'basket_dispute_allocations is append-only'); END;

-- 6 · Buyer refunds -------------------------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS basket_refunds (
  id                        TEXT PRIMARY KEY,
  basket_id                 TEXT NOT NULL REFERENCES basket_orders(id),
  idempotency_key           TEXT NOT NULL UNIQUE CHECK (idempotency_key = 'plotart-basket-re:' || basket_id || ':' || id),
  stripe_refund_id          TEXT UNIQUE CHECK (stripe_refund_id IS NULL OR stripe_refund_id GLOB 're_*' OR stripe_refund_id GLOB 'pyr_*'),
  amount_cents              INTEGER NOT NULL CHECK (amount_cents > 0),
  commission_returned_cents INTEGER NOT NULL CHECK (commission_returned_cents >= 0 AND commission_returned_cents <= amount_cents),
  status                    TEXT NOT NULL CHECK (status IN ('requested','pending','requires_action','succeeded','failed','canceled')),
  reason                    TEXT NOT NULL,
  requested_by              TEXT NOT NULL,
  livemode                  INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  failure                   TEXT,
  created_at                TEXT NOT NULL,
  updated_at                TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS basket_refunds_insert_valid BEFORE INSERT ON basket_refunds
WHEN NEW.status <> 'requested' OR NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.charge_id IS NOT NULL
  AND o.payment_status IN ('paid','partially_refunded') AND o.livemode = NEW.livemode)
BEGIN SELECT RAISE(ABORT, 'a refund starts as requested, on a paid basket of the same mode'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_not_during_dispute BEFORE INSERT ON basket_refunds
WHEN EXISTS (SELECT 1 FROM basket_disputes d WHERE d.basket_id = NEW.basket_id AND d.status = 'open')
BEGIN SELECT RAISE(ABORT, 'no refund while a dispute on this basket is open'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_cap BEFORE INSERT ON basket_refunds
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_refunds WHERE basket_id = NEW.basket_id AND status IN ('requested','pending','requires_action','succeeded'))
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_disputes WHERE basket_id = NEW.basket_id AND status IN ('open','lost'))
   > (SELECT total_cents FROM basket_orders WHERE id = NEW.basket_id)
BEGIN SELECT RAISE(ABORT, 'refunds would exceed what the buyer paid, less disputes'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_update_valid BEFORE UPDATE ON basket_refunds
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.idempotency_key <> OLD.idempotency_key OR NEW.amount_cents <> OLD.amount_cents
  OR NEW.commission_returned_cents <> OLD.commission_returned_cents OR NEW.livemode <> OLD.livemode OR NEW.created_at <> OLD.created_at
  OR NEW.reason <> OLD.reason OR NEW.requested_by <> OLD.requested_by
  OR (OLD.stripe_refund_id IS NOT NULL AND NEW.stripe_refund_id IS NOT OLD.stripe_refund_id)
  OR (NEW.status <> OLD.status AND NOT (
       (OLD.status = 'requested' AND NEW.status IN ('pending','requires_action','succeeded','failed','canceled'))
    OR (OLD.status = 'pending' AND NEW.status IN ('requires_action','succeeded','failed','canceled'))
    OR (OLD.status = 'requires_action' AND NEW.status IN ('pending','succeeded','failed','canceled'))
    OR (OLD.status = 'succeeded' AND NEW.status = 'failed')))
BEGIN SELECT RAISE(ABORT, 'a refund''s amount, reason and identifiers never change; its status only moves forward'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_parts_complete BEFORE UPDATE OF status ON basket_refunds
WHEN OLD.status = 'requested' AND NEW.status <> 'requested' AND (
     NEW.amount_cents <> (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_refund_parts WHERE refund_id = NEW.id)
  OR NEW.commission_returned_cents <> (SELECT COALESCE(SUM(commission_returned_cents), 0) FROM basket_refund_parts WHERE refund_id = NEW.id))
BEGIN SELECT RAISE(ABORT, 'a refund is sent only when its line and shipment parts add up to it'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_no_delete BEFORE DELETE ON basket_refunds
BEGIN SELECT RAISE(ABORT, 'basket refunds are never deleted'); END;

CREATE TABLE IF NOT EXISTS basket_refund_parts (
  refund_id                 TEXT NOT NULL REFERENCES basket_refunds(id),
  kind                      TEXT NOT NULL CHECK (kind IN ('line','shipment')),
  ref                       TEXT NOT NULL,
  artist_id                 TEXT NOT NULL,
  amount_cents              INTEGER NOT NULL CHECK (amount_cents > 0),
  commission_returned_cents INTEGER NOT NULL DEFAULT 0 CHECK (commission_returned_cents >= 0),
  artist_debit_cents        INTEGER NOT NULL CHECK (artist_debit_cents >= 0),
  PRIMARY KEY (refund_id, kind, ref),
  CHECK (amount_cents = artist_debit_cents + commission_returned_cents),
  CHECK (kind = 'line' OR commission_returned_cents = 0)
);
CREATE INDEX IF NOT EXISTS basket_refund_parts_artist ON basket_refund_parts(refund_id, artist_id);
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_while_requested BEFORE INSERT ON basket_refund_parts
WHEN NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.refund_id AND r.status = 'requested')
BEGIN SELECT RAISE(ABORT, 'refund parts are recorded with the request, before it is sent'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_line_valid BEFORE INSERT ON basket_refund_parts
WHEN NEW.kind = 'line' AND (
     NOT EXISTS (SELECT 1 FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref AND l.artist_id = NEW.artist_id)
  OR NEW.amount_cents + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'line' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
       + (SELECT COALESCE(SUM(json_extract(j.value, '$.artwork_cents')), 0) FROM basket_disputes d, json_each(d.attribution, '$.lines') j
            WHERE d.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id) AND d.status = 'lost' AND json_extract(j.value, '$.line_id') = NEW.ref)
     > (SELECT l.artwork_cents FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref)
  OR NEW.commission_returned_cents + (SELECT COALESCE(SUM(p.commission_returned_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'line' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
     > (SELECT l.commission_cents FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref))
BEGIN SELECT RAISE(ABORT, 'a line refund must name a line of this basket and its artist, and stay within what is left of its price (after refunds and lost disputes) and commission'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_shipment_valid BEFORE INSERT ON basket_refund_parts
WHEN NEW.kind = 'shipment' AND (
     NOT EXISTS (SELECT 1 FROM basket_shipments s JOIN basket_refunds r ON r.basket_id = s.basket_id WHERE r.id = NEW.refund_id AND s.shipment_id = NEW.ref AND s.artist_id = NEW.artist_id)
  OR NEW.amount_cents + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'shipment' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
       + (SELECT COALESCE(SUM(json_extract(j.value, '$.cents')), 0) FROM basket_disputes d, json_each(d.attribution, '$.shipments') j
            WHERE d.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id) AND d.status = 'lost' AND json_extract(j.value, '$.shipment_id') = NEW.ref)
     > (SELECT s.delivery_cents + s.insurance_cents FROM basket_shipments s JOIN basket_refunds r ON r.basket_id = s.basket_id WHERE r.id = NEW.refund_id AND s.shipment_id = NEW.ref))
BEGIN SELECT RAISE(ABORT, 'a shipment refund must name a shipment of this basket and its artist, and stay within its charges'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_update BEFORE UPDATE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_delete BEFORE DELETE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;

-- 7 · Transfers to artists ----------------------------------------------------------------------------------------------
--     allocation   the settled amount (cause_key '-')
--     recredit     repays what was REVERSED for a refund that then failed (cause_key = that refund)
--     restoration  repays a REDUCTION applied before payout and restored because its refund failed (cause_key = that refund)
--     Every recredit and restoration carries a written reason and who requested it.
CREATE TABLE IF NOT EXISTS basket_transfers (
  id                    TEXT PRIMARY KEY,
  basket_id             TEXT NOT NULL,
  artist_id             TEXT NOT NULL,
  kind                  TEXT NOT NULL CHECK (kind IN ('allocation','recredit','restoration')),
  cause_key             TEXT NOT NULL DEFAULT '-',
  attempt               INTEGER NOT NULL CHECK (attempt >= 1),
  destination           TEXT NOT NULL CHECK (destination GLOB 'acct_*'),
  idempotency_key       TEXT NOT NULL UNIQUE CHECK (idempotency_key = 'plotart-basket-tr:' || basket_id || ':' || artist_id || ':' || kind || ':' || cause_key || ':' || attempt),
  stripe_transfer_id    TEXT UNIQUE CHECK (stripe_transfer_id IS NULL OR stripe_transfer_id GLOB 'tr_*'),
  source_charge_id      TEXT NOT NULL CHECK (source_charge_id GLOB 'ch_*' OR source_charge_id GLOB 'py_*'),
  amount_cents          INTEGER NOT NULL CHECK (amount_cents > 0),
  livemode              INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  status                TEXT NOT NULL CHECK (status IN ('requested','created','failed')),
  reason                TEXT,
  requested_by          TEXT,
  failure               TEXT,
  created_at            TEXT NOT NULL,
  updated_at            TEXT NOT NULL,
  FOREIGN KEY (basket_id, artist_id) REFERENCES basket_artist_allocations(basket_id, artist_id),
  UNIQUE (basket_id, artist_id, kind, cause_key, attempt),
  CHECK ((kind = 'allocation') = (cause_key = '-')),
  CHECK (kind = 'allocation' OR (length(trim(COALESCE(reason, ''))) >= 10 AND length(trim(COALESCE(requested_by, ''))) > 0)),
  CHECK ((status = 'created') = (stripe_transfer_id IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS basket_transfers_one_in_flight ON basket_transfers(basket_id, artist_id, kind, cause_key) WHERE status IN ('requested','created');
CREATE INDEX IF NOT EXISTS basket_transfers_basket ON basket_transfers(basket_id, artist_id);
CREATE TRIGGER IF NOT EXISTS basket_transfers_insert_matches_basket BEFORE INSERT ON basket_transfers
WHEN NEW.status <> 'requested' OR NOT EXISTS (SELECT 1 FROM basket_orders o JOIN basket_artist_allocations a ON a.basket_id = o.id
  WHERE o.id = NEW.basket_id AND a.artist_id = NEW.artist_id AND o.charge_id = NEW.source_charge_id AND o.livemode = NEW.livemode
    AND a.account_id = NEW.destination AND o.settled_at IS NOT NULL AND a.transfer_due_cents IS NOT NULL
    AND o.payment_status IN ('paid','partially_refunded','refunded'))
BEGIN SELECT RAISE(ABORT, 'a transfer starts as requested and must match the basket''s charge, mode, settlement and the artist''s account'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_held_during_dispute BEFORE INSERT ON basket_transfers
WHEN EXISTS (SELECT 1 FROM basket_disputes d WHERE d.basket_id = NEW.basket_id AND d.status = 'open')
BEGIN SELECT RAISE(ABORT, 'transfers are held while a dispute on this basket is open'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_released BEFORE INSERT ON basket_transfers
WHEN NEW.kind = 'allocation' AND NOT EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.basket_id AND a.artist_id = NEW.artist_id
  AND a.release_ready_at IS NOT NULL AND julianday(a.release_ready_at) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'this artist''s allocation is not released yet'); END;
-- net money sent to the artist (transfers in flight or made, less reversals in flight or made) never exceeds what is due,
-- less reductions not restored
CREATE TRIGGER IF NOT EXISTS basket_transfers_cap BEFORE INSERT ON basket_transfers
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(t.amount_cents), 0) FROM basket_transfers t WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND t.status IN ('requested','created'))
   - (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND v.status IN ('requested','created'))
   + (SELECT COALESCE(SUM(CASE kind WHEN 'pending_reduction' THEN amount_cents WHEN 'pending_restored' THEN -amount_cents ELSE 0 END), 0)
        FROM basket_allocation_adjustments WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id)
   > (SELECT transfer_due_cents FROM basket_artist_allocations WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'this transfer would pay the artist more than is due'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_recredit_cap BEFORE INSERT ON basket_transfers
WHEN NEW.kind = 'recredit' AND (
     NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.cause_key AND r.basket_id = NEW.basket_id AND r.status IN ('failed','canceled'))
  OR NEW.amount_cents + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfers WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id
        AND kind = 'recredit' AND cause_key = NEW.cause_key AND status IN ('requested','created'))
     > (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND v.cause_kind = 'refund' AND v.cause_id = NEW.cause_key AND v.status = 'created'))
BEGIN SELECT RAISE(ABORT, 'a recredit repays only what was reversed for a refund that failed or was cancelled'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_restoration_cap BEFORE INSERT ON basket_transfers
WHEN NEW.kind = 'restoration' AND (
     NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.cause_key AND r.basket_id = NEW.basket_id AND r.status IN ('failed','canceled'))
  OR NOT EXISTS (SELECT 1 FROM basket_transfers t WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND t.kind = 'allocation' AND t.status = 'created')
  OR NEW.amount_cents + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfers WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id
        AND kind = 'restoration' AND cause_key = NEW.cause_key AND status IN ('requested','created'))
     > (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_allocation_adjustments WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id
        AND kind = 'pending_restored' AND cause_kind = 'refund' AND cause_id = NEW.cause_key))
BEGIN SELECT RAISE(ABORT, 'a restoration repays only a reduction restored for a failed or cancelled refund, after the allocation was paid'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_update_valid BEFORE UPDATE ON basket_transfers
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.artist_id <> OLD.artist_id OR NEW.kind <> OLD.kind OR NEW.cause_key <> OLD.cause_key
  OR NEW.attempt <> OLD.attempt OR NEW.destination <> OLD.destination OR NEW.idempotency_key <> OLD.idempotency_key
  OR NEW.source_charge_id <> OLD.source_charge_id OR NEW.amount_cents <> OLD.amount_cents OR NEW.livemode <> OLD.livemode OR NEW.created_at <> OLD.created_at
  OR NEW.reason IS NOT OLD.reason OR NEW.requested_by IS NOT OLD.requested_by
  OR (OLD.stripe_transfer_id IS NOT NULL AND NEW.stripe_transfer_id IS NOT OLD.stripe_transfer_id)
  OR (NEW.status <> OLD.status AND NOT (OLD.status = 'requested' AND NEW.status IN ('created','failed')))
BEGIN SELECT RAISE(ABORT, 'a transfer''s amount, destination, source, reason and key never change; requested moves once to created or failed'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_no_delete BEFORE DELETE ON basket_transfers
BEGIN SELECT RAISE(ABORT, 'basket transfers are never deleted'); END;

-- 8 · Transfer reversals: each tied to the refund or lost dispute that caused it, and capped by THAT artist's liability ---
CREATE TABLE IF NOT EXISTS basket_transfer_reversals (
  id                  TEXT PRIMARY KEY,
  transfer_id         TEXT NOT NULL REFERENCES basket_transfers(id),
  cause_kind          TEXT NOT NULL CHECK (cause_kind IN ('refund','dispute')),
  cause_id            TEXT NOT NULL,
  attempt             INTEGER NOT NULL CHECK (attempt >= 1),
  idempotency_key     TEXT NOT NULL UNIQUE CHECK (idempotency_key = 'plotart-basket-trr:' || transfer_id || ':' || cause_kind || ':' || cause_id || ':' || attempt),
  stripe_reversal_id  TEXT UNIQUE CHECK (stripe_reversal_id IS NULL OR stripe_reversal_id GLOB 'trr_*'),
  amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),
  status              TEXT NOT NULL CHECK (status IN ('requested','created','failed')),
  failure             TEXT,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  UNIQUE (transfer_id, cause_kind, cause_id, attempt),
  CHECK ((status = 'created') = (stripe_reversal_id IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS basket_reversals_one_in_flight ON basket_transfer_reversals(transfer_id, cause_kind, cause_id) WHERE status IN ('requested','created');
CREATE INDEX IF NOT EXISTS basket_transfer_reversals_cause ON basket_transfer_reversals(cause_kind, cause_id);
CREATE TRIGGER IF NOT EXISTS basket_reversals_insert_valid BEFORE INSERT ON basket_transfer_reversals
WHEN NEW.status <> 'requested'
  OR NOT EXISTS (SELECT 1 FROM basket_transfers t WHERE t.id = NEW.transfer_id AND t.status = 'created')
  OR (NEW.cause_kind = 'refund' AND NOT EXISTS (SELECT 1 FROM basket_refunds r JOIN basket_transfers t ON t.basket_id = r.basket_id
        WHERE t.id = NEW.transfer_id AND r.id = NEW.cause_id AND r.status = 'succeeded'))
  OR (NEW.cause_kind = 'dispute' AND NOT EXISTS (SELECT 1 FROM basket_disputes d JOIN basket_transfers t ON t.basket_id = d.basket_id
        WHERE t.id = NEW.transfer_id AND d.id = NEW.cause_id AND d.status = 'lost'))
BEGIN SELECT RAISE(ABORT, 'a reversal starts as requested, on a made transfer, for a SUCCEEDED refund or a lost dispute of the same basket'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_cap BEFORE INSERT ON basket_transfer_reversals
WHEN NEW.amount_cents + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfer_reversals WHERE transfer_id = NEW.transfer_id AND status IN ('requested','created'))
   > (SELECT amount_cents FROM basket_transfers WHERE id = NEW.transfer_id)
BEGIN SELECT RAISE(ABORT, 'reversals would exceed the transfer'); END;
-- the artist's liability for a cause: their debit in that refund (its parts), or their share of that lost dispute.
-- Everything recovered from them for it (reversals in flight or made, reductions, shortfalls) stays within it.
CREATE TRIGGER IF NOT EXISTS basket_reversals_within_liability BEFORE INSERT ON basket_transfer_reversals
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE v.cause_kind = NEW.cause_kind AND v.cause_id = NEW.cause_id AND v.status IN ('requested','created')
          AND t.artist_id = (SELECT artist_id FROM basket_transfers WHERE id = NEW.transfer_id) AND t.basket_id = (SELECT basket_id FROM basket_transfers WHERE id = NEW.transfer_id))
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_allocation_adjustments WHERE kind IN ('pending_reduction','shortfall')
        AND cause_kind = NEW.cause_kind AND cause_id = NEW.cause_id
        AND artist_id = (SELECT artist_id FROM basket_transfers WHERE id = NEW.transfer_id) AND basket_id = (SELECT basket_id FROM basket_transfers WHERE id = NEW.transfer_id))
   > CASE NEW.cause_kind
       WHEN 'refund' THEN (SELECT COALESCE(SUM(p.artist_debit_cents), 0) FROM basket_refund_parts p WHERE p.refund_id = NEW.cause_id
                             AND p.artist_id = (SELECT artist_id FROM basket_transfers WHERE id = NEW.transfer_id))
       ELSE (SELECT COALESCE(SUM(a.loss_cents + a.fee_cents), 0) FROM basket_dispute_allocations a WHERE a.dispute_id = NEW.cause_id
                             AND a.artist_id = (SELECT artist_id FROM basket_transfers WHERE id = NEW.transfer_id))
     END
BEGIN SELECT RAISE(ABORT, 'this reversal exceeds what this artist owes for that refund or dispute'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_update_valid BEFORE UPDATE ON basket_transfer_reversals
WHEN NEW.id <> OLD.id OR NEW.transfer_id <> OLD.transfer_id OR NEW.cause_kind <> OLD.cause_kind OR NEW.cause_id <> OLD.cause_id
  OR NEW.attempt <> OLD.attempt OR NEW.idempotency_key <> OLD.idempotency_key OR NEW.amount_cents <> OLD.amount_cents OR NEW.created_at <> OLD.created_at
  OR (OLD.stripe_reversal_id IS NOT NULL AND NEW.stripe_reversal_id IS NOT OLD.stripe_reversal_id)
  OR (NEW.status <> OLD.status AND NOT (OLD.status = 'requested' AND NEW.status IN ('created','failed')))
BEGIN SELECT RAISE(ABORT, 'a reversal''s amount and key never change; requested moves once to created or failed'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_no_delete BEFORE DELETE ON basket_transfer_reversals
BEGIN SELECT RAISE(ABORT, 'basket transfer reversals are never deleted'); END;

-- 9 · Adjustments outside a Stripe transfer, each with a written reason and who recorded it. Append-only; one per cause.
--     pending_reduction  lowers a transfer not yet made, for a refund or dispute (within that artist's liability for it)
--     pending_restored   gives a reduction back because its refund failed (paid by the allocation, or a 'restoration')
--     shortfall          what Stripe could not recover from the artist for a cause (within that liability)
--     shortfall_cleared  a shortfall settled outside Stripe or no longer owed
CREATE TABLE IF NOT EXISTS basket_allocation_adjustments (
  id           TEXT PRIMARY KEY,
  basket_id    TEXT NOT NULL,
  artist_id    TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('pending_reduction','pending_restored','shortfall','shortfall_cleared')),
  cause_kind   TEXT NOT NULL CHECK (cause_kind IN ('refund','dispute')),
  cause_id     TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  reason       TEXT NOT NULL CHECK (length(trim(reason)) >= 10),
  recorded_by  TEXT NOT NULL CHECK (length(trim(recorded_by)) > 0),
  at           TEXT NOT NULL,
  FOREIGN KEY (basket_id, artist_id) REFERENCES basket_artist_allocations(basket_id, artist_id),
  UNIQUE (basket_id, artist_id, kind, cause_kind, cause_id)
);
CREATE TRIGGER IF NOT EXISTS basket_adjustments_cause_exists BEFORE INSERT ON basket_allocation_adjustments
WHEN (NEW.cause_kind = 'refund' AND NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.cause_id AND r.basket_id = NEW.basket_id))
  OR (NEW.cause_kind = 'dispute' AND NOT EXISTS (SELECT 1 FROM basket_disputes d WHERE d.id = NEW.cause_id AND d.basket_id = NEW.basket_id AND d.status = 'lost'))
  OR (NEW.kind = 'pending_restored' AND NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.cause_id AND NEW.cause_kind = 'refund' AND r.status IN ('failed','canceled')))
BEGIN SELECT RAISE(ABORT, 'an adjustment names a refund or lost dispute of this basket; a restoration needs that refund to have failed or been cancelled'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_reduction_cap BEFORE INSERT ON basket_allocation_adjustments
WHEN NEW.kind = 'pending_reduction' AND (
     (SELECT transfer_due_cents FROM basket_artist_allocations WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id) IS NULL
  OR NEW.amount_cents
   + (SELECT COALESCE(SUM(CASE kind WHEN 'pending_reduction' THEN amount_cents WHEN 'pending_restored' THEN -amount_cents ELSE 0 END), 0)
        FROM basket_allocation_adjustments WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id)
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfers WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id
        AND kind = 'allocation' AND status IN ('requested','created'))
   > (SELECT transfer_due_cents FROM basket_artist_allocations WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id))
BEGIN SELECT RAISE(ABORT, 'a reduction cannot exceed the part of the transfer not yet made'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_within_liability BEFORE INSERT ON basket_allocation_adjustments
WHEN NEW.kind IN ('pending_reduction','shortfall') AND NEW.amount_cents
   + (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE v.cause_kind = NEW.cause_kind AND v.cause_id = NEW.cause_id AND v.status IN ('requested','created') AND t.artist_id = NEW.artist_id AND t.basket_id = NEW.basket_id)
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_allocation_adjustments WHERE kind IN ('pending_reduction','shortfall')
        AND cause_kind = NEW.cause_kind AND cause_id = NEW.cause_id AND artist_id = NEW.artist_id AND basket_id = NEW.basket_id)
   > CASE NEW.cause_kind
       WHEN 'refund' THEN (SELECT COALESCE(SUM(p.artist_debit_cents), 0) FROM basket_refund_parts p WHERE p.refund_id = NEW.cause_id AND p.artist_id = NEW.artist_id)
       ELSE (SELECT COALESCE(SUM(a.loss_cents + a.fee_cents), 0) FROM basket_dispute_allocations a WHERE a.dispute_id = NEW.cause_id AND a.artist_id = NEW.artist_id)
     END
BEGIN SELECT RAISE(ABORT, 'this adjustment exceeds what this artist owes for that refund or dispute'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_reverse_cap BEFORE INSERT ON basket_allocation_adjustments
WHEN NEW.kind IN ('pending_restored','shortfall_cleared') AND NEW.amount_cents > (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_allocation_adjustments
  WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id AND cause_kind = NEW.cause_kind AND cause_id = NEW.cause_id
    AND kind = CASE NEW.kind WHEN 'pending_restored' THEN 'pending_reduction' ELSE 'shortfall' END)
BEGIN SELECT RAISE(ABORT, 'only a recorded reduction or shortfall can be restored or cleared, and not beyond it'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_no_update BEFORE UPDATE ON basket_allocation_adjustments
BEGIN SELECT RAISE(ABORT, 'basket_allocation_adjustments is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_no_delete BEFORE DELETE ON basket_allocation_adjustments
BEGIN SELECT RAISE(ABORT, 'basket_allocation_adjustments is append-only'); END;

-- 10 · One original: the shared claim, taken by BOTH checkouts in the same transaction as their hold or sale ---------------
--      checkout_capabilities: the claims-aware single-artist checkout records itself here (checkout.js); until it has,
--      no basket can claim an artwork. The migration does not write it.
CREATE TABLE IF NOT EXISTS checkout_capabilities (
  name     TEXT PRIMARY KEY CHECK (name = 'single_checkout_claims'),
  version  INTEGER NOT NULL CHECK (version = 1),
  at       TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS checkout_capabilities_fixed BEFORE UPDATE ON checkout_capabilities
BEGIN SELECT RAISE(ABORT, 'checkout_capabilities rows never change'); END;
CREATE TRIGGER IF NOT EXISTS checkout_capabilities_no_delete BEFORE DELETE ON checkout_capabilities
BEGIN SELECT RAISE(ABORT, 'checkout_capabilities rows are never removed'); END;

CREATE TABLE IF NOT EXISTS artwork_claims (
  artwork_id   TEXT PRIMARY KEY,
  holder_kind  TEXT NOT NULL CHECK (holder_kind IN ('single','basket')),
  holder_id    TEXT NOT NULL,                     -- checkout_orders.id or basket_orders.id
  kind         TEXT NOT NULL CHECK (kind IN ('hold','sale')),
  expires_at   TEXT,
  claimed_at   TEXT NOT NULL,
  CHECK ((kind = 'hold') = (expires_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS artwork_claims_holder ON artwork_claims(holder_kind, holder_id);
CREATE TRIGGER IF NOT EXISTS artwork_claims_single_not_basket BEFORE INSERT ON artwork_claims
WHEN NEW.holder_kind = 'single' AND (
     EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_basket_needs_claims_checkout BEFORE INSERT ON artwork_claims
WHEN NEW.holder_kind = 'basket' AND NOT EXISTS (SELECT 1 FROM checkout_capabilities WHERE name = 'single_checkout_claims' AND version = 1)
BEGIN SELECT RAISE(ABORT, 'baskets are refused until the claims-aware single-artist checkout is deployed'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_basket_not_single BEFORE INSERT ON artwork_claims
WHEN NEW.holder_kind = 'basket' AND (
     EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
  -- a single-artist hold whose checkout is still open keeps priority past its expiry (payment may be in flight: review M-2)
  OR EXISTS (SELECT 1 FROM artwork_reservations r JOIN checkout_sessions cs ON cs.order_id = r.order_id WHERE r.artwork_id = NEW.artwork_id AND cs.status = 'open')
  OR EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artwork_id = NEW.artwork_id AND o.status IN ('quoted','checkout_open','payment_failed')
             AND (o.quote_expires_at IS NULL OR julianday(o.quote_expires_at) > julianday('now'))))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold, held or quoted through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_basket_own_line BEFORE INSERT ON artwork_claims
WHEN NEW.holder_kind = 'basket' AND (
     NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.holder_id AND l.artwork_id = NEW.artwork_id)
  OR (NEW.kind = 'hold' AND NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.holder_id AND o.status IN ('checkout_open','payment_failed')))
  OR (NEW.kind = 'sale' AND NOT EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.basket_id = NEW.holder_id AND s.artwork_id = NEW.artwork_id)))
BEGIN SELECT RAISE(ABORT, 'a basket claims only its own lines: a hold while its checkout is open, a sale only to reinstate its own sale'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_update_valid BEFORE UPDATE ON artwork_claims
WHEN NEW.artwork_id <> OLD.artwork_id OR NEW.holder_kind <> OLD.holder_kind OR NEW.holder_id <> OLD.holder_id
  OR (OLD.kind = 'sale' AND NEW.kind = 'hold')
  -- an expired hold becomes a sale only if its checkout was still payable and nobody took the work over (review M-2: a
  -- buyer who paid in time is never refused because Stripe's notification was late)
  OR (OLD.kind = 'hold' AND NEW.kind = 'sale' AND julianday(OLD.expires_at) <= julianday('now') AND NOT (
       (OLD.holder_kind = 'single' AND EXISTS (SELECT 1 FROM checkout_sessions s WHERE s.order_id = OLD.holder_id AND s.status = 'open')
          AND EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.order_id = OLD.holder_id AND r.artwork_id = OLD.artwork_id))
    OR (OLD.holder_kind = 'basket' AND EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.holder_id AND o.payment_status = 'paid' AND o.checkout_session_id IS NOT NULL)
          AND EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.basket_id = OLD.holder_id AND b.artwork_id = OLD.artwork_id))))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: a claim never changes holder or artwork; a lapsed hold no longer payable cannot become a sale; a sale never becomes a hold'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_sale_kept BEFORE DELETE ON artwork_claims
WHEN OLD.kind = 'sale' AND (
     (OLD.holder_kind = 'single' AND EXISTS (SELECT 1 FROM artwork_sales s WHERE s.order_id = OLD.holder_id AND s.artwork_id = OLD.artwork_id AND s.released_at IS NULL))
  OR (OLD.holder_kind = 'basket' AND EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.basket_id = OLD.holder_id AND s.artwork_id = OLD.artwork_id AND s.released_at IS NULL)))
BEGIN SELECT RAISE(ABORT, 'a sale''s claim is released only after the sale is released'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_hold_kept BEFORE DELETE ON artwork_claims
WHEN OLD.kind = 'hold' AND julianday(OLD.expires_at) > julianday('now') AND (
     (OLD.holder_kind = 'single' AND EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.order_id = OLD.holder_id AND r.artwork_id = OLD.artwork_id))
  OR (OLD.holder_kind = 'basket' AND EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.basket_id = OLD.holder_id AND b.artwork_id = OLD.artwork_id)))
BEGIN SELECT RAISE(ABORT, 'a live hold''s claim is released only after the hold itself'); END;
-- priority (review M-2): a hold whose checkout is still open is never taken away, even past its expiry: the buyer may
-- already have paid and Stripe's notification may simply be late
-- (the holder itself releases by deleting its reservation first, in the same transaction; nobody else can)
CREATE TRIGGER IF NOT EXISTS artwork_claims_open_checkout_kept BEFORE DELETE ON artwork_claims
WHEN OLD.kind = 'hold' AND (
     (OLD.holder_kind = 'single' AND EXISTS (SELECT 1 FROM checkout_sessions s WHERE s.order_id = OLD.holder_id AND s.status = 'open')
        AND EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.order_id = OLD.holder_id AND r.artwork_id = OLD.artwork_id))
  OR (OLD.holder_kind = 'basket' AND EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.holder_id AND o.status = 'checkout_open')
        AND EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.basket_id = OLD.holder_id AND b.artwork_id = OLD.artwork_id)))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork''s hold belongs to a checkout that is still open'); END;
-- rollback safety (review H-1): a basket's hold or sale is visible to every version of checkout.js through artworks.availability
CREATE TRIGGER IF NOT EXISTS artwork_claims_basket_marks_artwork BEFORE INSERT ON artwork_claims
WHEN NEW.holder_kind = 'basket' AND NOT EXISTS (SELECT 1 FROM artworks a WHERE a.id = NEW.artwork_id
  AND a.availability = CASE NEW.kind WHEN 'hold' THEN 'reserved' ELSE 'sold' END)
BEGIN SELECT RAISE(ABORT, 'a basket hold or sale marks the artwork reserved or sold in the same transaction (rollback safety)'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claims_basket_sale_marks_artwork BEFORE UPDATE ON artwork_claims
WHEN NEW.holder_kind = 'basket' AND OLD.kind = 'hold' AND NEW.kind = 'sale'
  AND NOT EXISTS (SELECT 1 FROM artworks a WHERE a.id = NEW.artwork_id AND a.availability = 'sold')
BEGIN SELECT RAISE(ABORT, 'a basket sale marks the artwork sold in the same transaction (rollback safety)'); END;
-- REPLACE (review M-1): a claim is never overwritten by another holder, and a sale is never turned back into a hold
CREATE TRIGGER IF NOT EXISTS artwork_claims_no_replace BEFORE INSERT ON artwork_claims
WHEN EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id
  AND (c.holder_kind <> NEW.holder_kind OR c.holder_id <> NEW.holder_id OR (c.kind = 'sale' AND NEW.kind = 'hold')))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is claimed by another holder'); END;
-- the assertion each checkout makes, in the same transaction as its hold, sale or reinstatement: "I hold this claim".
-- A refused assertion rolls the whole transaction back; an accepted one is kept as an audit record.
CREATE TABLE IF NOT EXISTS artwork_claim_assertions (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  artwork_id   TEXT NOT NULL,
  holder_kind  TEXT NOT NULL CHECK (holder_kind IN ('single','basket')),
  holder_id    TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('hold','sale')),
  purpose      TEXT NOT NULL,
  at           TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS artwork_claim_assertions_held BEFORE INSERT ON artwork_claim_assertions
WHEN NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id AND c.holder_kind = NEW.holder_kind AND c.holder_id = NEW.holder_id
  AND c.kind = NEW.kind AND (c.kind = 'sale' OR julianday(c.expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is claimed through the other checkout'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claim_assertions_no_update BEFORE UPDATE ON artwork_claim_assertions
BEGIN SELECT RAISE(ABORT, 'artwork_claim_assertions is append-only'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claim_assertions_no_delete BEFORE DELETE ON artwork_claim_assertions
BEGIN SELECT RAISE(ABORT, 'artwork_claim_assertions is append-only'); END;

-- 11 · The basket's own holds and sales; each needs the basket's claim -------------------------------------------------
CREATE TABLE IF NOT EXISTS basket_artwork_reservations (
  artwork_id  TEXT PRIMARY KEY,
  basket_id   TEXT NOT NULL REFERENCES basket_orders(id),
  expires_at  TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS basket_hold_needs_claim_insert BEFORE INSERT ON basket_artwork_reservations
WHEN NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id AND c.holder_kind = 'basket' AND c.holder_id = NEW.basket_id
  AND c.kind = 'hold' AND julianday(c.expires_at) > julianday('now') AND julianday(NEW.expires_at) <= julianday(c.expires_at))
BEGIN SELECT RAISE(ABORT, 'a basket holds an artwork only with its own live claim, and not beyond it'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_needs_claim_update BEFORE UPDATE ON basket_artwork_reservations
WHEN NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id AND c.holder_kind = 'basket' AND c.holder_id = NEW.basket_id
  AND c.kind = 'hold' AND julianday(c.expires_at) > julianday('now') AND julianday(NEW.expires_at) <= julianday(c.expires_at))
BEGIN SELECT RAISE(ABORT, 'a basket holds an artwork only with its own live claim, and not beyond it'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_not_single_insert BEFORE INSERT ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold or held through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_artwork_fixed BEFORE UPDATE ON basket_artwork_reservations
WHEN NEW.artwork_id <> OLD.artwork_id
BEGIN SELECT RAISE(ABORT, 'a basket hold never moves to another artwork'); END;

CREATE TABLE IF NOT EXISTS basket_artwork_sales (
  basket_id       TEXT NOT NULL REFERENCES basket_orders(id),
  artwork_id      TEXT NOT NULL,
  sold_at         TEXT NOT NULL,
  released_at     TEXT,
  released_reason TEXT,
  PRIMARY KEY (basket_id, artwork_id),
  CHECK ((released_at IS NULL) = (released_reason IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS basket_artwork_sales_one_active ON basket_artwork_sales(artwork_id) WHERE released_at IS NULL;
CREATE TRIGGER IF NOT EXISTS basket_sale_needs_claim BEFORE INSERT ON basket_artwork_sales
WHEN NEW.released_at IS NOT NULL
  OR NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id AND c.holder_kind = 'basket' AND c.holder_id = NEW.basket_id AND c.kind = 'sale')
  OR NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.charge_id IS NOT NULL)
BEGIN SELECT RAISE(ABORT, 'a basket sale needs a paid basket and its own sale claim (converted from its live hold)'); END;
CREATE TRIGGER IF NOT EXISTS basket_sale_not_single_insert BEFORE INSERT ON basket_artwork_sales
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold or held through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_sale_update_valid BEFORE UPDATE ON basket_artwork_sales
WHEN NEW.basket_id <> OLD.basket_id OR NEW.artwork_id <> OLD.artwork_id OR NEW.sold_at <> OLD.sold_at
BEGIN SELECT RAISE(ABORT, 'a basket sale''s basket, artwork and time never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_sale_reinstate_needs_claim BEFORE UPDATE ON basket_artwork_sales
WHEN OLD.released_at IS NOT NULL AND NEW.released_at IS NULL
  AND NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = NEW.artwork_id AND c.holder_kind = 'basket' AND c.holder_id = NEW.basket_id AND c.kind = 'sale')
BEGIN SELECT RAISE(ABORT, 'this artwork is claimed elsewhere: the basket sale cannot be reinstated (resolve with the buyer)'); END;
CREATE TRIGGER IF NOT EXISTS basket_artwork_sales_no_delete BEFORE DELETE ON basket_artwork_sales
BEGIN SELECT RAISE(ABORT, 'basket_artwork_sales rows are kept with their basket; release them with a reason'); END;

-- 12 · Signed platform-account events, and the audit trail --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS basket_payment_events (
  event_id     TEXT PRIMARY KEY CHECK (event_id GLOB 'evt_*'),
  type         TEXT NOT NULL,
  livemode     INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  basket_id    TEXT,
  object_id    TEXT,
  created      INTEGER NOT NULL,
  status       TEXT NOT NULL CHECK (status IN ('received','processed','ignored','failed')),
  detail       TEXT,
  received_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS basket_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  basket_id   TEXT NOT NULL REFERENCES basket_orders(id),
  actor       TEXT NOT NULL,
  kind        TEXT NOT NULL,
  from_status TEXT,
  to_status   TEXT,
  detail      TEXT CHECK (detail IS NULL OR json_valid(detail)),
  at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS basket_events_basket ON basket_events(basket_id, id);
CREATE TRIGGER IF NOT EXISTS basket_events_no_update BEFORE UPDATE ON basket_events
BEGIN SELECT RAISE(ABORT, 'basket_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_events_no_delete BEFORE DELETE ON basket_events
BEGIN SELECT RAISE(ABORT, 'basket_events is append-only'); END;

-- 14 · No REPLACE (review M-1). INSERT OR REPLACE deletes the conflicting row without firing DELETE triggers; each of these
--      tables refuses an INSERT that conflicts with any of its unique keys, so "never changes / never deleted" holds.
CREATE TRIGGER IF NOT EXISTS basket_terms_no_replace BEFORE INSERT ON basket_terms
WHEN EXISTS (SELECT 1 FROM basket_terms t WHERE (t.doc_id = NEW.doc_id AND (t.buyer_terms_doc <> NEW.buyer_terms_doc OR t.livemode <> NEW.livemode
    OR t.commission_free_lines <> NEW.commission_free_lines OR t.permits <> NEW.permits OR t.note <> NEW.note)) OR (t.buyer_terms_doc = NEW.buyer_terms_doc AND t.doc_id <> NEW.doc_id))
BEGIN SELECT RAISE(ABORT, 'basket terms are never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_no_replace BEFORE INSERT ON basket_orders
WHEN EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.id OR o.reference = NEW.reference OR o.transfer_group = NEW.transfer_group
    OR o.checkout_session_id = NEW.checkout_session_id OR o.payment_intent_id = NEW.payment_intent_id OR o.charge_id = NEW.charge_id)
BEGIN SELECT RAISE(ABORT, 'a basket is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_no_replace BEFORE INSERT ON basket_shipments
WHEN EXISTS (SELECT 1 FROM basket_shipments s WHERE s.basket_id = NEW.basket_id AND s.shipment_id = NEW.shipment_id)
BEGIN SELECT RAISE(ABORT, 'a shipment is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_no_replace BEFORE INSERT ON basket_lines
WHEN EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.basket_id AND (l.line_id = NEW.line_id OR l.artwork_id = NEW.artwork_id OR l.enquiry_ref = NEW.enquiry_ref))
BEGIN SELECT RAISE(ABORT, 'a basket line is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_no_replace BEFORE INSERT ON basket_artist_allocations
WHEN EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.basket_id AND a.artist_id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'an allocation is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_no_replace BEFORE INSERT ON basket_disputes
WHEN EXISTS (SELECT 1 FROM basket_disputes d WHERE d.id = NEW.id OR d.stripe_dispute_id = NEW.stripe_dispute_id)
BEGIN SELECT RAISE(ABORT, 'a dispute is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_dispute_allocations_no_replace BEFORE INSERT ON basket_dispute_allocations
WHEN EXISTS (SELECT 1 FROM basket_dispute_allocations a WHERE a.dispute_id = NEW.dispute_id AND a.artist_id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'an artist''s share of a dispute is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_no_replace BEFORE INSERT ON basket_refunds
WHEN EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.id OR r.idempotency_key = NEW.idempotency_key OR r.stripe_refund_id = NEW.stripe_refund_id)
BEGIN SELECT RAISE(ABORT, 'a refund is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_replace BEFORE INSERT ON basket_refund_parts
WHEN EXISTS (SELECT 1 FROM basket_refund_parts p WHERE p.refund_id = NEW.refund_id AND p.kind = NEW.kind AND p.ref = NEW.ref)
BEGIN SELECT RAISE(ABORT, 'a refund part is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_no_replace BEFORE INSERT ON basket_transfers
WHEN EXISTS (SELECT 1 FROM basket_transfers t WHERE t.id = NEW.id OR t.idempotency_key = NEW.idempotency_key OR t.stripe_transfer_id = NEW.stripe_transfer_id
    OR (t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND t.kind = NEW.kind AND t.cause_key = NEW.cause_key
        AND (t.attempt = NEW.attempt OR t.status IN ('requested','created'))))
BEGIN SELECT RAISE(ABORT, 'a transfer is never replaced, and never sent twice for one purpose'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_no_replace BEFORE INSERT ON basket_transfer_reversals
WHEN EXISTS (SELECT 1 FROM basket_transfer_reversals v WHERE v.id = NEW.id OR v.idempotency_key = NEW.idempotency_key OR v.stripe_reversal_id = NEW.stripe_reversal_id
    OR (v.transfer_id = NEW.transfer_id AND v.cause_kind = NEW.cause_kind AND v.cause_id = NEW.cause_id AND (v.attempt = NEW.attempt OR v.status IN ('requested','created'))))
BEGIN SELECT RAISE(ABORT, 'a reversal is never replaced, and never made twice for one cause'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_no_replace BEFORE INSERT ON basket_allocation_adjustments
WHEN EXISTS (SELECT 1 FROM basket_allocation_adjustments j WHERE j.id = NEW.id OR (j.basket_id = NEW.basket_id AND j.artist_id = NEW.artist_id
    AND j.kind = NEW.kind AND j.cause_kind = NEW.cause_kind AND j.cause_id = NEW.cause_id))
BEGIN SELECT RAISE(ABORT, 'an adjustment is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS checkout_capabilities_no_replace BEFORE INSERT ON checkout_capabilities
WHEN EXISTS (SELECT 1 FROM checkout_capabilities c WHERE c.name = NEW.name AND c.version <> NEW.version)
BEGIN SELECT RAISE(ABORT, 'checkout_capabilities rows are never replaced'); END;
CREATE TRIGGER IF NOT EXISTS artwork_claim_assertions_no_replace BEFORE INSERT ON artwork_claim_assertions
WHEN NEW.id IS NOT NULL AND EXISTS (SELECT 1 FROM artwork_claim_assertions a WHERE a.id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'artwork_claim_assertions rows are never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_no_replace BEFORE INSERT ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id)
BEGIN SELECT RAISE(ABORT, 'a basket hold is never replaced: an expired one is released first'); END;
CREATE TRIGGER IF NOT EXISTS basket_sales_no_replace BEFORE INSERT ON basket_artwork_sales
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE (s.basket_id = NEW.basket_id AND s.artwork_id = NEW.artwork_id) OR (s.artwork_id = NEW.artwork_id AND s.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'a basket sale is never replaced'); END;
CREATE TRIGGER IF NOT EXISTS basket_events_no_replace BEFORE INSERT ON basket_events
WHEN NEW.id IS NOT NULL AND EXISTS (SELECT 1 FROM basket_events e WHERE e.id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'basket_events rows are never replaced'); END;
-- basket_payment_events is deliberately left out: its webhook deduplication relies on INSERT ... ON CONFLICT DO NOTHING
-- (as payment_events does), and it records no money.

-- 13 · Backfill: claims for single-artist sales and live holds that already exist (pilot data, if any). Reads the
--      single-artist tables; writes only artwork_claims. Running it twice changes nothing (INSERT OR IGNORE).
INSERT OR IGNORE INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at)
  SELECT artwork_id, 'single', order_id, 'sale', NULL, sold_at FROM artwork_sales WHERE released_at IS NULL;
INSERT OR IGNORE INTO artwork_claims (artwork_id, holder_kind, holder_id, kind, expires_at, claimed_at)
  SELECT r.artwork_id, 'single', r.order_id, 'hold', r.expires_at, r.created_at FROM artwork_reservations r WHERE julianday(r.expires_at) > julianday('now')
    AND NOT EXISTS (SELECT 1 FROM artwork_claims c WHERE c.artwork_id = r.artwork_id);

-- Rollback (only before any basket data exists):
-- DROP TABLE IF EXISTS basket_events;
-- DROP TABLE IF EXISTS basket_payment_events;
-- DROP TABLE IF EXISTS basket_artwork_sales;
-- DROP TABLE IF EXISTS basket_artwork_reservations;
-- DROP TABLE IF EXISTS artwork_claim_assertions;
-- DROP TABLE IF EXISTS artwork_claims;
-- DROP TABLE IF EXISTS checkout_capabilities;
-- DROP TABLE IF EXISTS basket_allocation_adjustments;
-- DROP TABLE IF EXISTS basket_transfer_reversals;
-- DROP TABLE IF EXISTS basket_transfers;
-- DROP TABLE IF EXISTS basket_refund_parts;
-- DROP TABLE IF EXISTS basket_refunds;
-- DROP TABLE IF EXISTS basket_dispute_allocations;
-- DROP TABLE IF EXISTS basket_disputes;
-- DROP TABLE IF EXISTS basket_artist_allocations;
-- DROP TABLE IF EXISTS basket_lines;
-- DROP TABLE IF EXISTS basket_shipments;
-- DROP TABLE IF EXISTS basket_orders;
-- DROP TABLE IF EXISTS basket_terms;
