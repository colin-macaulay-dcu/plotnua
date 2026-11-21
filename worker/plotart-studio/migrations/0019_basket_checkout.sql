-- PlotArt Studio · migration 0019 · Multi-artist basket checkout: records design (Phase 1, revised after review, 21 Nov 2026).
-- PROPOSAL FOR FOUNDER REVIEW. NOT APPLIED to any real database (production or TEST). Not mirrored into schema.sql yet:
-- that follows only once this exact file is approved.
-- Model: one buyer payment on PlotArt's platform account ("separate charges and transfers"), then Stripe transfers to each
-- artist. Amounts come from src/basket-rules.js; these tables record them and refuse anything the rules would never produce.
-- All money is integer euro cents. Every provider-facing row records livemode (0 test, 1 live) and must match its basket.
--
-- WHAT THIS CHANGES OUTSIDE ITS OWN TABLES (needs the founder's explicit approval of this exact file, and both production
-- backups, before it runs; migration-check classes any trigger as non-automatic):
--   Four refusal-only BEFORE triggers on EXISTING tables (artwork_reservations, artwork_sales, checkout_orders). They refuse
--   a single-artist hold, sale, sale reinstatement or new quote ONLY while a basket holds or has sold the same artwork, so
--   with no basket rows they never fire and the existing checkout behaves exactly as before. Their messages begin
--   "UNIQUE constraint failed:" on purpose: checkout.js already turns such an error into "someone else is completing a
--   purchase" (startCheckout) or "paid, but already sold: refund the buyer" (recordPaid), so the single-artist checkout
--   fails closed and cleanly without a code change. This departs from the 6 Nov 2026 convention (triggers on new tables
--   only); it is the only way the database itself can stop one original being sold through both checkouts.
--   No existing table, column, index, trigger definition or row is otherwise changed.
--
-- Integrity rules enforced here (independent of the application):
--   · one original, one active hold and one active sale across BOTH checkouts, on insert AND update, including expiry,
--     reinstatement after a failed refund, and open single-artist quotes;
--   · a basket's lines, shipments and allocations are written only while it is a draft, and it cannot leave draft unless
--     its totals reconcile; afterwards price, commission, identifiers, fee and settlement are write-once;
--   · transfers, reversals and refunds use deterministic idempotency keys, at most one in flight per purpose, match the
--     basket's charge, mode and the artist's account, and are capped: net transfers ≤ what is due, reversals ≤ the
--     transfer, refunds ≤ what was paid less lost disputes, and per line/shipment ≤ its price;
--   · no transfer while a dispute is open; no refund while a dispute is open;
--   · financial rows are never deleted; amounts never change; statuses move only forward (a succeeded refund may still
--     fail later, as Stripe reports);
--   · the basket must name new basket terms: the issued PA-PAY-2026-11 / PA-BPT-2026-11 exclude multi-artwork orders, and
--     only TEST placeholders (*-TEST-*) are accepted in test mode. Live terms do not exist yet.
-- Retention/erasure of basket records is not designed yet: these rows are kept (no deletion path) until it is.
-- No foreign keys to artists/artworks: order and accounting records follow their own retention.

-- 1 · Basket orders ------------------------------------------------------------------------------------------------------
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
  artist_terms_doc    TEXT NOT NULL,
  buyer_terms_doc     TEXT NOT NULL,
  transfer_group      TEXT NOT NULL UNIQUE CHECK (transfer_group = 'plotart-basket-' || id),
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
  -- the issued single-artist texts exclude multi-artwork orders; TEST placeholders only in test mode, never in live mode
  CHECK (artist_terms_doc <> 'PA-PAY-2026-11' AND buyer_terms_doc <> 'PA-BPT-2026-11'),
  CHECK ((livemode = 0) = (artist_terms_doc GLOB '*-TEST-*') AND (livemode = 0) = (buyer_terms_doc GLOB '*-TEST-*'))
);
CREATE INDEX IF NOT EXISTS basket_orders_buyer ON basket_orders(buyer_email, created_at);
CREATE INDEX IF NOT EXISTS basket_orders_status ON basket_orders(status, updated_at);
CREATE TRIGGER IF NOT EXISTS basket_orders_fixed BEFORE UPDATE ON basket_orders
WHEN NEW.id <> OLD.id OR NEW.reference <> OLD.reference OR NEW.total_cents <> OLD.total_cents OR NEW.commission_cents <> OLD.commission_cents
  OR NEW.plan_version <> OLD.plan_version OR NEW.plan_sha256 <> OLD.plan_sha256 OR NEW.decisions <> OLD.decisions
  OR NEW.artist_terms_doc <> OLD.artist_terms_doc OR NEW.buyer_terms_doc <> OLD.buyer_terms_doc OR NEW.transfer_group <> OLD.transfer_group
  OR NEW.livemode <> OLD.livemode OR NEW.currency <> OLD.currency OR NEW.created_at <> OLD.created_at OR NEW.created_by <> OLD.created_by
BEGIN SELECT RAISE(ABORT, 'a basket''s plan, terms, decisions, money and mode never change: start a new basket'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_ids_once BEFORE UPDATE ON basket_orders
WHEN (OLD.checkout_session_id IS NOT NULL AND NEW.checkout_session_id IS NOT OLD.checkout_session_id)
  OR (OLD.payment_intent_id IS NOT NULL AND NEW.payment_intent_id IS NOT OLD.payment_intent_id)
  OR (OLD.charge_id IS NOT NULL AND NEW.charge_id IS NOT OLD.charge_id)
BEGIN SELECT RAISE(ABORT, 'a basket''s Stripe identifiers are written once and never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_settlement_once BEFORE UPDATE ON basket_orders
WHEN OLD.fee_cents IS NOT NULL AND (NEW.fee_cents IS NOT OLD.fee_cents OR NEW.fee_vat_cents IS NOT OLD.fee_vat_cents OR NEW.settled_at IS NOT OLD.settled_at)
BEGIN SELECT RAISE(ABORT, 'the processing fee and settlement are recorded once and never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_no_return_to_draft BEFORE UPDATE OF status ON basket_orders
WHEN OLD.status <> 'draft' AND NEW.status = 'draft'
BEGIN SELECT RAISE(ABORT, 'a basket never returns to draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_leave_draft_reconciled BEFORE UPDATE OF status ON basket_orders
WHEN OLD.status = 'draft' AND NEW.status NOT IN ('draft','cancelled') AND (
     NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.id)
  OR NEW.total_cents <> (SELECT COALESCE(SUM(artwork_cents), 0) FROM basket_lines WHERE basket_id = NEW.id)
                      + (SELECT COALESCE(SUM(delivery_cents + insurance_cents), 0) FROM basket_shipments WHERE basket_id = NEW.id)
  OR NEW.commission_cents <> (SELECT COALESCE(SUM(commission_cents), 0) FROM basket_lines WHERE basket_id = NEW.id)
  OR NEW.total_cents <> (SELECT COALESCE(SUM(gross_cents), 0) FROM basket_artist_allocations WHERE basket_id = NEW.id)
  OR NEW.commission_cents <> (SELECT COALESCE(SUM(commission_cents), 0) FROM basket_artist_allocations WHERE basket_id = NEW.id)
  OR EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.id AND NOT EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.id AND a.artist_id = l.artist_id))
  OR EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.id AND a.gross_cents <>
       (SELECT COALESCE(SUM(artwork_cents), 0) FROM basket_lines WHERE basket_id = NEW.id AND artist_id = a.artist_id)
     + (SELECT COALESCE(SUM(delivery_cents + insurance_cents), 0) FROM basket_shipments WHERE basket_id = NEW.id AND artist_id = a.artist_id)))
BEGIN SELECT RAISE(ABORT, 'the basket does not reconcile: total, commission and artist allocations must equal its lines and shipments'); END;
CREATE TRIGGER IF NOT EXISTS basket_orders_no_delete BEFORE DELETE ON basket_orders
WHEN OLD.status <> 'draft' OR OLD.payment_status <> 'none'
BEGIN SELECT RAISE(ABORT, 'a basket that left draft is kept with its records'); END;

-- 2 · Shipments: each belongs to ONE artist; delivery and insurance are itemised and never carry commission --------------
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
  CHECK (method = 'delivery' OR delivery_cents = 0),       -- nothing is delivered on a collection
  CHECK (insurance_cents = 0 OR cover IS NOT NULL)         -- an insurance charge needs recorded cover
);
CREATE TRIGGER IF NOT EXISTS basket_shipments_draft_only_insert BEFORE INSERT ON basket_shipments
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'shipments are added only while the basket is a draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_charges_fixed BEFORE UPDATE ON basket_shipments
WHEN NEW.basket_id <> OLD.basket_id OR NEW.shipment_id <> OLD.shipment_id OR NEW.artist_id <> OLD.artist_id OR NEW.method <> OLD.method
  OR NEW.delivery_cents <> OLD.delivery_cents OR NEW.insurance_cents <> OLD.insurance_cents OR NEW.cover IS NOT OLD.cover
BEGIN SELECT RAISE(ABORT, 'a shipment''s artist, method, charges and cover never change once recorded'); END;
CREATE TRIGGER IF NOT EXISTS basket_shipments_no_delete BEFORE DELETE ON basket_shipments
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'shipments are removed only while the basket is a draft'); END;

-- 3 · Artwork lines: commission per artwork from the existing entitlement rule, bound to its artist, artwork and enquiry --
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
  enquiry_ref          TEXT NOT NULL,                                   -- the logged introduction (basket_introduction)
  processing_consent   INTEGER NOT NULL DEFAULT 0 CHECK (processing_consent IN (0, 1)),   -- as RECORDED, never as supplied
  processing_consent_at TEXT,
  PRIMARY KEY (basket_id, line_id),
  UNIQUE (basket_id, artwork_id),
  FOREIGN KEY (basket_id, shipment_id, artist_id) REFERENCES basket_shipments(basket_id, shipment_id, artist_id),
  CHECK (commission_cents = (artwork_cents * commission_bp) / 10000),   -- integer division: floor, as checkout-rules
  CHECK ((processing_consent = 1) = (processing_consent_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS basket_lines_artwork ON basket_lines(artwork_id);
CREATE TRIGGER IF NOT EXISTS basket_lines_draft_only_insert BEFORE INSERT ON basket_lines
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'lines are added only while the basket is a draft'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_fixed BEFORE UPDATE ON basket_lines
BEGIN SELECT RAISE(ABORT, 'a basket line never changes once recorded'); END;
CREATE TRIGGER IF NOT EXISTS basket_lines_no_delete BEFORE DELETE ON basket_lines
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'lines are removed only while the basket is a draft'); END;

-- 4 · Artist allocations: fixed when the basket is built; the settlement (processing share, transfer due) written once ----
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
  CHECK (transfer_due_cents IS NULL OR transfer_due_cents = transfer_before_fees_cents - processing_share_cents)
);
CREATE TRIGGER IF NOT EXISTS basket_allocations_draft_only_insert BEFORE INSERT ON basket_artist_allocations
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.status = 'draft') OR NEW.transfer_due_cents IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'allocations are added only while the basket is a draft, before settlement'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_fixed BEFORE UPDATE ON basket_artist_allocations
WHEN NEW.basket_id <> OLD.basket_id OR NEW.artist_id <> OLD.artist_id OR NEW.account_id <> OLD.account_id OR NEW.gross_cents <> OLD.gross_cents
  OR NEW.commission_cents <> OLD.commission_cents OR NEW.delivery_cents <> OLD.delivery_cents OR NEW.insurance_cents <> OLD.insurance_cents
  OR NEW.transfer_before_fees_cents <> OLD.transfer_before_fees_cents OR NEW.release <> OLD.release
  OR (OLD.transfer_due_cents IS NOT NULL AND (NEW.transfer_due_cents IS NOT OLD.transfer_due_cents OR NEW.processing_share_cents IS NOT OLD.processing_share_cents))
BEGIN SELECT RAISE(ABORT, 'an allocation never changes; its settlement is written once'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_settle_after_fee BEFORE UPDATE ON basket_artist_allocations
WHEN OLD.transfer_due_cents IS NULL AND NEW.transfer_due_cents IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.settled_at IS NOT NULL)
BEGIN SELECT RAISE(ABORT, 'an allocation is settled only after the basket''s processing fee is recorded'); END;
CREATE TRIGGER IF NOT EXISTS basket_allocations_no_delete BEFORE DELETE ON basket_artist_allocations
WHEN NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = OLD.basket_id AND o.status = 'draft')
BEGIN SELECT RAISE(ABORT, 'allocations are removed only while the basket is a draft'); END;

-- 5 · Disputes (Stripe debits the whole basket payment from PlotArt's balance) -------------------------------------------
CREATE TABLE IF NOT EXISTS basket_disputes (
  id                 TEXT PRIMARY KEY,
  basket_id          TEXT NOT NULL REFERENCES basket_orders(id),
  stripe_dispute_id  TEXT NOT NULL UNIQUE CHECK (stripe_dispute_id GLOB 'du_*' OR stripe_dispute_id GLOB 'dp_*'),
  amount_cents       INTEGER NOT NULL CHECK (amount_cents > 0),
  fee_cents          INTEGER CHECK (fee_cents IS NULL OR fee_cents >= 0),
  status             TEXT NOT NULL CHECK (status IN ('open','won','lost')),
  reason             TEXT,
  attribution        TEXT CHECK (attribution IS NULL OR json_valid(attribution)),
  allocation         TEXT CHECK (allocation IS NULL OR json_valid(allocation)),
  livemode           INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  opened_at          TEXT NOT NULL,
  closed_at          TEXT,
  CHECK ((status = 'open') = (closed_at IS NULL)),
  CHECK (status = 'lost' OR (attribution IS NULL AND allocation IS NULL))
);
CREATE TRIGGER IF NOT EXISTS basket_disputes_insert_valid BEFORE INSERT ON basket_disputes
WHEN NEW.status <> 'open' OR NOT EXISTS (SELECT 1 FROM basket_orders o WHERE o.id = NEW.basket_id AND o.charge_id IS NOT NULL
  AND o.livemode = NEW.livemode AND NEW.amount_cents <= o.total_cents)
BEGIN SELECT RAISE(ABORT, 'a dispute opens on a paid basket of the same mode, for no more than its total'); END;
-- what can be disputed is what the buyer paid and was not refunded (refunds in flight count), less disputes already lost
CREATE TRIGGER IF NOT EXISTS basket_disputes_cap BEFORE INSERT ON basket_disputes
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_refunds WHERE basket_id = NEW.basket_id AND status IN ('requested','pending','requires_action','succeeded'))
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_disputes WHERE basket_id = NEW.basket_id AND status = 'lost')
   > (SELECT total_cents FROM basket_orders WHERE id = NEW.basket_id)
BEGIN SELECT RAISE(ABORT, 'the dispute exceeds what remains of the payment after refunds and lost disputes'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_update_valid BEFORE UPDATE ON basket_disputes
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.stripe_dispute_id <> OLD.stripe_dispute_id OR NEW.amount_cents <> OLD.amount_cents
  OR NEW.livemode <> OLD.livemode OR NEW.opened_at <> OLD.opened_at OR (OLD.status <> 'open' AND NEW.status <> OLD.status)
  OR (OLD.fee_cents IS NOT NULL AND NEW.fee_cents IS NOT OLD.fee_cents)
  OR (OLD.attribution IS NOT NULL AND NEW.attribution IS NOT OLD.attribution) OR (OLD.allocation IS NOT NULL AND NEW.allocation IS NOT OLD.allocation)
BEGIN SELECT RAISE(ABORT, 'a dispute only moves from open to won or lost; its amount and identifiers never change'); END;
CREATE TRIGGER IF NOT EXISTS basket_disputes_no_delete BEFORE DELETE ON basket_disputes
BEGIN SELECT RAISE(ABORT, 'basket disputes are never deleted'); END;

-- 6 · Buyer refunds: deterministic key, capped by what was paid, allocated per line and per shipment ----------------------
--     Active = requested, pending, requires_action or succeeded. A succeeded refund may later fail (Stripe reports it).
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
   + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_disputes WHERE basket_id = NEW.basket_id AND status = 'lost')
   > (SELECT total_cents FROM basket_orders WHERE id = NEW.basket_id)
BEGIN SELECT RAISE(ABORT, 'refunds would exceed what the buyer paid, less lost disputes'); END;
CREATE TRIGGER IF NOT EXISTS basket_refunds_update_valid BEFORE UPDATE ON basket_refunds
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.idempotency_key <> OLD.idempotency_key OR NEW.amount_cents <> OLD.amount_cents
  OR NEW.commission_returned_cents <> OLD.commission_returned_cents OR NEW.livemode <> OLD.livemode OR NEW.created_at <> OLD.created_at
  OR (OLD.stripe_refund_id IS NOT NULL AND NEW.stripe_refund_id IS NOT OLD.stripe_refund_id)
  OR (NEW.status <> OLD.status AND NOT (
       (OLD.status = 'requested' AND NEW.status IN ('pending','requires_action','succeeded','failed','canceled'))
    OR (OLD.status = 'pending' AND NEW.status IN ('requires_action','succeeded','failed','canceled'))
    OR (OLD.status = 'requires_action' AND NEW.status IN ('pending','succeeded','failed','canceled'))
    OR (OLD.status = 'succeeded' AND NEW.status = 'failed')))
BEGIN SELECT RAISE(ABORT, 'a refund''s amount and identifiers never change; its status only moves forward'); END;
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
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_while_requested BEFORE INSERT ON basket_refund_parts
WHEN NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.refund_id AND r.status = 'requested')
BEGIN SELECT RAISE(ABORT, 'refund parts are recorded with the request, before it is sent'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_line_valid BEFORE INSERT ON basket_refund_parts
WHEN NEW.kind = 'line' AND (
     NOT EXISTS (SELECT 1 FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref AND l.artist_id = NEW.artist_id)
  OR NEW.amount_cents + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'line' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
     > (SELECT l.artwork_cents FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref)
  OR NEW.commission_returned_cents + (SELECT COALESCE(SUM(p.commission_returned_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'line' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
     > (SELECT l.commission_cents FROM basket_lines l JOIN basket_refunds r ON r.basket_id = l.basket_id WHERE r.id = NEW.refund_id AND l.line_id = NEW.ref))
BEGIN SELECT RAISE(ABORT, 'a line refund must name a line of this basket and its artist, and stay within its price and commission'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_shipment_valid BEFORE INSERT ON basket_refund_parts
WHEN NEW.kind = 'shipment' AND (
     NOT EXISTS (SELECT 1 FROM basket_shipments s JOIN basket_refunds r ON r.basket_id = s.basket_id WHERE r.id = NEW.refund_id AND s.shipment_id = NEW.ref AND s.artist_id = NEW.artist_id)
  OR NEW.amount_cents + (SELECT COALESCE(SUM(p.amount_cents), 0) FROM basket_refund_parts p JOIN basket_refunds r2 ON r2.id = p.refund_id
        WHERE p.kind = 'shipment' AND p.ref = NEW.ref AND r2.basket_id = (SELECT basket_id FROM basket_refunds WHERE id = NEW.refund_id)
          AND r2.status IN ('requested','pending','requires_action','succeeded'))
     > (SELECT s.delivery_cents + s.insurance_cents FROM basket_shipments s JOIN basket_refunds r ON r.basket_id = s.basket_id WHERE r.id = NEW.refund_id AND s.shipment_id = NEW.ref))
BEGIN SELECT RAISE(ABORT, 'a shipment refund must name a shipment of this basket and its artist, and stay within its charges'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_update BEFORE UPDATE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_delete BEFORE DELETE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;

-- 7 · Transfers to artists. kind 'allocation' pays the settled amount; kind 'recredit' repays an artist whose transfer was
--     reversed for a refund that later failed (cause_key = that refund). One in flight per purpose; deterministic keys.
CREATE TABLE IF NOT EXISTS basket_transfers (
  id                    TEXT PRIMARY KEY,
  basket_id             TEXT NOT NULL,
  artist_id             TEXT NOT NULL,
  kind                  TEXT NOT NULL CHECK (kind IN ('allocation','recredit')),
  cause_key             TEXT NOT NULL DEFAULT '-',
  attempt               INTEGER NOT NULL CHECK (attempt >= 1),
  destination           TEXT NOT NULL CHECK (destination GLOB 'acct_*'),
  idempotency_key       TEXT NOT NULL UNIQUE CHECK (idempotency_key = 'plotart-basket-tr:' || basket_id || ':' || artist_id || ':' || kind || ':' || cause_key || ':' || attempt),
  stripe_transfer_id    TEXT UNIQUE CHECK (stripe_transfer_id IS NULL OR stripe_transfer_id GLOB 'tr_*'),
  source_charge_id      TEXT NOT NULL CHECK (source_charge_id GLOB 'ch_*' OR source_charge_id GLOB 'py_*'),
  amount_cents          INTEGER NOT NULL CHECK (amount_cents > 0),
  livemode              INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  status                TEXT NOT NULL CHECK (status IN ('requested','created','failed')),
  failure               TEXT,
  created_at            TEXT NOT NULL,
  updated_at            TEXT NOT NULL,
  FOREIGN KEY (basket_id, artist_id) REFERENCES basket_artist_allocations(basket_id, artist_id),
  UNIQUE (basket_id, artist_id, kind, cause_key, attempt),
  CHECK ((kind = 'allocation') = (cause_key = '-')),
  CHECK ((status = 'created') = (stripe_transfer_id IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS basket_transfers_one_in_flight ON basket_transfers(basket_id, artist_id, kind, cause_key) WHERE status IN ('requested','created');
CREATE INDEX IF NOT EXISTS basket_transfers_basket ON basket_transfers(basket_id, artist_id);
CREATE TRIGGER IF NOT EXISTS basket_transfers_insert_matches_basket BEFORE INSERT ON basket_transfers
WHEN NEW.status <> 'requested' OR NOT EXISTS (SELECT 1 FROM basket_orders o JOIN basket_artist_allocations a ON a.basket_id = o.id
  WHERE o.id = NEW.basket_id AND a.artist_id = NEW.artist_id AND o.charge_id = NEW.source_charge_id AND o.livemode = NEW.livemode
    AND a.account_id = NEW.destination AND o.settled_at IS NOT NULL AND a.transfer_due_cents IS NOT NULL
    AND o.payment_status IN ('paid','partially_refunded'))
BEGIN SELECT RAISE(ABORT, 'a transfer starts as requested and must match the basket''s charge, mode, settlement and the artist''s account'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_held_during_dispute BEFORE INSERT ON basket_transfers
WHEN EXISTS (SELECT 1 FROM basket_disputes d WHERE d.basket_id = NEW.basket_id AND d.status = 'open')
BEGIN SELECT RAISE(ABORT, 'transfers are held while a dispute on this basket is open'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_released BEFORE INSERT ON basket_transfers
WHEN NEW.kind = 'allocation' AND NOT EXISTS (SELECT 1 FROM basket_artist_allocations a WHERE a.basket_id = NEW.basket_id AND a.artist_id = NEW.artist_id
  AND a.release_ready_at IS NOT NULL AND julianday(a.release_ready_at) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'this artist''s allocation is not released yet'); END;
-- net money sent to the artist (transfers in flight or made, less reversals in flight or made) never exceeds what is due
-- less the reductions applied to a transfer not yet made
CREATE TRIGGER IF NOT EXISTS basket_transfers_cap BEFORE INSERT ON basket_transfers
WHEN NEW.amount_cents
   + (SELECT COALESCE(SUM(t.amount_cents), 0) FROM basket_transfers t WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND t.status IN ('requested','created'))
   - (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND v.status IN ('requested','created'))
   + (SELECT COALESCE(SUM(CASE kind WHEN 'pending_reduction' THEN amount_cents WHEN 'pending_restored' THEN -amount_cents ELSE 0 END), 0)
        FROM basket_allocation_adjustments WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id)
   > (SELECT transfer_due_cents FROM basket_artist_allocations WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'this transfer would pay the artist more than is due'); END;
-- a recredit repays exactly what was reversed for a refund that then failed, and nothing else
CREATE TRIGGER IF NOT EXISTS basket_transfers_recredit_cap BEFORE INSERT ON basket_transfers
WHEN NEW.kind = 'recredit' AND (
     NOT EXISTS (SELECT 1 FROM basket_refunds r WHERE r.id = NEW.cause_key AND r.basket_id = NEW.basket_id AND r.status = 'failed')
  OR NEW.amount_cents + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfers WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id
        AND kind = 'recredit' AND cause_key = NEW.cause_key AND status IN ('requested','created'))
     > (SELECT COALESCE(SUM(v.amount_cents), 0) FROM basket_transfer_reversals v JOIN basket_transfers t ON t.id = v.transfer_id
        WHERE t.basket_id = NEW.basket_id AND t.artist_id = NEW.artist_id AND v.cause_kind = 'refund' AND v.cause_id = NEW.cause_key AND v.status = 'created'))
BEGIN SELECT RAISE(ABORT, 'a recredit repays only what was reversed for a refund that failed'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_update_valid BEFORE UPDATE ON basket_transfers
WHEN NEW.id <> OLD.id OR NEW.basket_id <> OLD.basket_id OR NEW.artist_id <> OLD.artist_id OR NEW.kind <> OLD.kind OR NEW.cause_key <> OLD.cause_key
  OR NEW.attempt <> OLD.attempt OR NEW.destination <> OLD.destination OR NEW.idempotency_key <> OLD.idempotency_key
  OR NEW.source_charge_id <> OLD.source_charge_id OR NEW.amount_cents <> OLD.amount_cents OR NEW.livemode <> OLD.livemode OR NEW.created_at <> OLD.created_at
  OR (OLD.stripe_transfer_id IS NOT NULL AND NEW.stripe_transfer_id IS NOT OLD.stripe_transfer_id)
  OR (NEW.status <> OLD.status AND NOT (OLD.status = 'requested' AND NEW.status IN ('created','failed')))
BEGIN SELECT RAISE(ABORT, 'a transfer''s amount, destination, source and key never change; requested moves once to created or failed'); END;
CREATE TRIGGER IF NOT EXISTS basket_transfers_no_delete BEFORE DELETE ON basket_transfers
BEGIN SELECT RAISE(ABORT, 'basket transfers are never deleted'); END;

-- 8 · Transfer reversals, each tied to the refund or lost dispute that caused it -----------------------------------------
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
        WHERE t.id = NEW.transfer_id AND r.id = NEW.cause_id AND r.status IN ('requested','pending','requires_action','succeeded')))
  OR (NEW.cause_kind = 'dispute' AND NOT EXISTS (SELECT 1 FROM basket_disputes d JOIN basket_transfers t ON t.basket_id = d.basket_id
        WHERE t.id = NEW.transfer_id AND d.id = NEW.cause_id AND d.status = 'lost'))
BEGIN SELECT RAISE(ABORT, 'a reversal starts as requested, on a made transfer, for an active refund or a lost dispute of the same basket'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_cap BEFORE INSERT ON basket_transfer_reversals
WHEN NEW.amount_cents + (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_transfer_reversals WHERE transfer_id = NEW.transfer_id AND status IN ('requested','created'))
   > (SELECT amount_cents FROM basket_transfers WHERE id = NEW.transfer_id)
BEGIN SELECT RAISE(ABORT, 'reversals would exceed the transfer'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_update_valid BEFORE UPDATE ON basket_transfer_reversals
WHEN NEW.id <> OLD.id OR NEW.transfer_id <> OLD.transfer_id OR NEW.cause_kind <> OLD.cause_kind OR NEW.cause_id <> OLD.cause_id
  OR NEW.attempt <> OLD.attempt OR NEW.idempotency_key <> OLD.idempotency_key OR NEW.amount_cents <> OLD.amount_cents OR NEW.created_at <> OLD.created_at
  OR (OLD.stripe_reversal_id IS NOT NULL AND NEW.stripe_reversal_id IS NOT OLD.stripe_reversal_id)
  OR (NEW.status <> OLD.status AND NOT (OLD.status = 'requested' AND NEW.status IN ('created','failed')))
BEGIN SELECT RAISE(ABORT, 'a reversal''s amount and key never change; requested moves once to created or failed'); END;
CREATE TRIGGER IF NOT EXISTS basket_reversals_no_delete BEFORE DELETE ON basket_transfer_reversals
BEGIN SELECT RAISE(ABORT, 'basket transfer reversals are never deleted'); END;

-- 9 · Adjustments outside a Stripe transfer: reductions of a transfer not yet made (and their restoration when the refund
--     that caused them fails), and shortfalls Stripe cannot recover (and their clearance). Append-only; one per cause.
CREATE TABLE IF NOT EXISTS basket_allocation_adjustments (
  id           TEXT PRIMARY KEY,
  basket_id    TEXT NOT NULL,
  artist_id    TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('pending_reduction','pending_restored','shortfall','shortfall_cleared')),
  cause_kind   TEXT NOT NULL CHECK (cause_kind IN ('refund','dispute','reversal')),
  cause_id     TEXT NOT NULL,
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  note         TEXT,
  at           TEXT NOT NULL,
  FOREIGN KEY (basket_id, artist_id) REFERENCES basket_artist_allocations(basket_id, artist_id),
  UNIQUE (basket_id, artist_id, kind, cause_kind, cause_id)
);
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
CREATE TRIGGER IF NOT EXISTS basket_adjustments_reverse_cap BEFORE INSERT ON basket_allocation_adjustments
WHEN NEW.kind IN ('pending_restored','shortfall_cleared') AND NEW.amount_cents > (SELECT COALESCE(SUM(amount_cents), 0) FROM basket_allocation_adjustments
  WHERE basket_id = NEW.basket_id AND artist_id = NEW.artist_id AND cause_kind = NEW.cause_kind AND cause_id = NEW.cause_id
    AND kind = CASE NEW.kind WHEN 'pending_restored' THEN 'pending_reduction' ELSE 'shortfall' END)
BEGIN SELECT RAISE(ABORT, 'only a recorded reduction or shortfall can be restored or cleared, and not beyond it'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_no_update BEFORE UPDATE ON basket_allocation_adjustments
BEGIN SELECT RAISE(ABORT, 'basket_allocation_adjustments is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_adjustments_no_delete BEFORE DELETE ON basket_allocation_adjustments
BEGIN SELECT RAISE(ABORT, 'basket_allocation_adjustments is append-only'); END;

-- 10 · One original: one active hold and one active sale across BOTH checkouts -------------------------------------------
--      A work is "taken by the single-artist checkout" when it has an active single sale, an unexpired single hold, or an
--      open single quote. It is "taken by a basket" when it has an active basket sale or an unexpired basket hold.
CREATE TABLE IF NOT EXISTS basket_artwork_reservations (
  artwork_id  TEXT PRIMARY KEY,
  basket_id   TEXT NOT NULL REFERENCES basket_orders(id),
  expires_at  TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS basket_hold_in_basket_insert BEFORE INSERT ON basket_artwork_reservations
WHEN NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.basket_id AND l.artwork_id = NEW.artwork_id)
BEGIN SELECT RAISE(ABORT, 'a basket can hold only an artwork that is one of its lines'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_in_basket_update BEFORE UPDATE ON basket_artwork_reservations
WHEN NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.basket_id AND l.artwork_id = NEW.artwork_id)
BEGIN SELECT RAISE(ABORT, 'a basket can hold only an artwork that is one of its lines'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_not_single_insert BEFORE INSERT ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
  OR EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artwork_id = NEW.artwork_id AND o.status IN ('quoted','checkout_open','payment_failed')
             AND (o.quote_expires_at IS NULL OR julianday(o.quote_expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold, held or quoted through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_not_single_update BEFORE UPDATE ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
  OR EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artwork_id = NEW.artwork_id AND o.status IN ('quoted','checkout_open','payment_failed')
             AND (o.quote_expires_at IS NULL OR julianday(o.quote_expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold, held or quoted through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_not_sold_insert BEFORE INSERT ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'this artwork has already been sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS basket_hold_not_sold_update BEFORE UPDATE ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'this artwork has already been sold through a basket'); END;
-- another basket may take over a hold only once it has expired; the artwork never moves to a different row
CREATE TRIGGER IF NOT EXISTS basket_hold_takeover BEFORE UPDATE ON basket_artwork_reservations
WHEN NEW.artwork_id <> OLD.artwork_id OR (NEW.basket_id <> OLD.basket_id AND julianday(OLD.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'a basket hold can be taken over only after it expires, and never moved to another artwork'); END;

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
CREATE TRIGGER IF NOT EXISTS basket_sale_needs_own_hold BEFORE INSERT ON basket_artwork_sales
WHEN NOT EXISTS (SELECT 1 FROM basket_artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND r.basket_id = NEW.basket_id
  AND julianday(NEW.sold_at) <= julianday(r.expires_at) AND julianday('now') <= julianday(r.expires_at))
  OR NOT EXISTS (SELECT 1 FROM basket_lines l WHERE l.basket_id = NEW.basket_id AND l.artwork_id = NEW.artwork_id)
  OR NEW.released_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'a basket sale needs this basket''s own unexpired hold on one of its lines'); END;
CREATE TRIGGER IF NOT EXISTS basket_sale_not_single_insert BEFORE INSERT ON basket_artwork_sales
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold or held through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_sale_update_valid BEFORE UPDATE ON basket_artwork_sales
WHEN NEW.basket_id <> OLD.basket_id OR NEW.artwork_id <> OLD.artwork_id OR NEW.sold_at <> OLD.sold_at
BEGIN SELECT RAISE(ABORT, 'a basket sale''s basket, artwork and time never change'); END;
-- reinstating a released sale (a refund that later failed) only while no other checkout holds or has sold the work
CREATE TRIGGER IF NOT EXISTS basket_sale_reinstate BEFORE UPDATE ON basket_artwork_sales
WHEN OLD.released_at IS NOT NULL AND NEW.released_at IS NULL AND (
     EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND b.basket_id <> NEW.basket_id AND julianday(b.expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'this artwork is sold or held elsewhere: the basket sale cannot be reinstated (resolve with the buyer)'); END;
CREATE TRIGGER IF NOT EXISTS basket_artwork_sales_no_delete BEFORE DELETE ON basket_artwork_sales
BEGIN SELECT RAISE(ABORT, 'basket_artwork_sales rows are kept with their basket; release them with a reason'); END;

-- 10b · The single-artist checkout's side of the same rule (triggers on EXISTING tables; see the header) -----------------
CREATE TRIGGER IF NOT EXISTS single_hold_not_basket_insert BEFORE INSERT ON artwork_reservations
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS single_hold_not_basket_update BEFORE UPDATE ON artwork_reservations
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS single_sale_not_basket_insert BEFORE INSERT ON artwork_sales
WHEN EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now'))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS single_sale_reinstate_not_basket BEFORE UPDATE ON artwork_sales
WHEN OLD.released_at IS NOT NULL AND NEW.released_at IS NULL AND (
     EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket'); END;
CREATE TRIGGER IF NOT EXISTS single_quote_not_basket BEFORE UPDATE OF status ON checkout_orders
WHEN NEW.status = 'quoted' AND OLD.status <> 'quoted' AND (
     EXISTS (SELECT 1 FROM basket_artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
  OR EXISTS (SELECT 1 FROM basket_artwork_reservations b WHERE b.artwork_id = NEW.artwork_id AND julianday(b.expires_at) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'UNIQUE constraint failed: this artwork is held or sold through a basket; no quote can be issued'); END;

-- 11 · Signed platform-account events (the basket's own webhook endpoint), recorded once each ----------------------------
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

-- 12 · Audit trail for every basket change. Append-only ------------------------------------------------------------------
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

-- Rollback (only before any basket data exists). The triggers on EXISTING tables go first: they read basket tables.
-- DROP TRIGGER IF EXISTS single_quote_not_basket;
-- DROP TRIGGER IF EXISTS single_sale_reinstate_not_basket;
-- DROP TRIGGER IF EXISTS single_sale_not_basket_insert;
-- DROP TRIGGER IF EXISTS single_hold_not_basket_update;
-- DROP TRIGGER IF EXISTS single_hold_not_basket_insert;
-- DROP TABLE IF EXISTS basket_events;
-- DROP TABLE IF EXISTS basket_payment_events;
-- DROP TABLE IF EXISTS basket_artwork_sales;
-- DROP TABLE IF EXISTS basket_artwork_reservations;
-- DROP TABLE IF EXISTS basket_allocation_adjustments;
-- DROP TABLE IF EXISTS basket_transfer_reversals;
-- DROP TABLE IF EXISTS basket_transfers;
-- DROP TABLE IF EXISTS basket_refund_parts;
-- DROP TABLE IF EXISTS basket_refunds;
-- DROP TABLE IF EXISTS basket_disputes;
-- DROP TABLE IF EXISTS basket_artist_allocations;
-- DROP TABLE IF EXISTS basket_lines;
-- DROP TABLE IF EXISTS basket_shipments;
-- DROP TABLE IF EXISTS basket_orders;
