-- PlotArt Studio · migration 0019 · Multi-artist basket checkout: records design (Phase 1, 21 Nov 2026).
-- PROPOSAL FOR FOUNDER REVIEW. NOT APPLIED to any real database (production or TEST). Not mirrored into schema.sql yet:
-- that follows only once this exact file is approved.
-- New tables, indexes and refusal-only BEFORE triggers on these NEW tables only. No existing table, index, trigger or row
-- is changed. The single-artist pilot tables of 0017 are read by two guards below and never written.
-- Triggers make this a non-automatic migration (migration-check policy, 6 Nov 2026): it needs the founder's explicit
-- approval of this exact file, and both production backups, before it runs.
-- Model: one buyer payment on PlotArt's platform account ("separate charges and transfers"), then one Stripe transfer per
-- artist. Amounts come from src/basket-rules.js (plan / settle / refund / dispute); these tables record them. All money is
-- integer euro cents. Every provider-facing row records livemode (0 test, 1 live); the code never mixes modes.
-- The founder decisions that governed a basket (basket-rules.js DECISIONS) are snapshotted on the order, so a later change
-- of decision never alters how an existing basket was allocated.
-- No foreign keys to artists/artworks: order and accounting records follow their own retention, and never block the
-- existing participation-deletion schedule.

-- 1 · Basket orders: one buyer, one payment, several artists.
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
  plan_sha256         TEXT NOT NULL CHECK (length(plan_sha256) = 64),     -- the exact plan the buyer was charged against
  decisions           TEXT NOT NULL CHECK (json_valid(decisions)),        -- founder decisions in force for this basket
  transfer_group      TEXT NOT NULL UNIQUE CHECK (transfer_group GLOB 'plotart-basket-*'),
  checkout_session_id TEXT UNIQUE CHECK (checkout_session_id IS NULL OR checkout_session_id GLOB 'cs_test_*' OR checkout_session_id GLOB 'cs_live_*'),
  payment_intent_id   TEXT UNIQUE CHECK (payment_intent_id IS NULL OR payment_intent_id GLOB 'pi_*'),
  charge_id           TEXT UNIQUE CHECK (charge_id IS NULL OR charge_id GLOB 'ch_*' OR charge_id GLOB 'py_*'),
  fee_cents           INTEGER CHECK (fee_cents IS NULL OR fee_cents >= 0),          -- Stripe's actual processing fee
  fee_vat_cents       INTEGER CHECK (fee_vat_cents IS NULL OR fee_vat_cents >= 0),  -- VAT Stripe charged on it
  paid_at             TEXT,
  settled_at          TEXT,
  needs_resolution    TEXT,
  retain_until        TEXT,
  created_by          TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  CHECK ((fee_cents IS NULL) = (fee_vat_cents IS NULL)),
  CHECK (settled_at IS NULL OR fee_cents IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS basket_orders_buyer ON basket_orders(buyer_email, created_at);
CREATE INDEX IF NOT EXISTS basket_orders_status ON basket_orders(status, updated_at);
CREATE TRIGGER IF NOT EXISTS basket_orders_money_fixed BEFORE UPDATE ON basket_orders
WHEN NEW.total_cents <> OLD.total_cents OR NEW.commission_cents <> OLD.commission_cents OR NEW.plan_sha256 <> OLD.plan_sha256
  OR NEW.decisions <> OLD.decisions OR NEW.transfer_group <> OLD.transfer_group OR NEW.livemode <> OLD.livemode OR NEW.currency <> OLD.currency
BEGIN SELECT RAISE(ABORT, 'a basket''s plan, decisions, money and mode never change: start a new basket'); END;

-- 2 · Shipments: each belongs to ONE artist; delivery and insurance are itemised and never carry commission.
CREATE TABLE IF NOT EXISTS basket_shipments (
  basket_id          TEXT NOT NULL REFERENCES basket_orders(id),
  shipment_id        TEXT NOT NULL,
  artist_id          TEXT NOT NULL,
  method             TEXT NOT NULL CHECK (method IN ('delivery','collection')),
  delivery_cents     INTEGER NOT NULL CHECK (delivery_cents >= 0),
  insurance_cents    INTEGER NOT NULL CHECK (insurance_cents >= 0),
  delivery           TEXT CHECK (delivery IS NULL OR json_valid(delivery)),   -- checkout-rules DELIVERY_FIELDS snapshot
  cover              TEXT CHECK (cover IS NULL OR json_valid(cover)),
  refunded_cents     INTEGER NOT NULL DEFAULT 0 CHECK (refunded_cents >= 0),
  fulfilment_status  TEXT NOT NULL DEFAULT 'none' CHECK (fulfilment_status IN ('none','dispatched','delivered','collected')),
  fulfilled_at       TEXT,
  cancellation_ends_at TEXT,                                                   -- set when the buyer's cancellation period is known
  PRIMARY KEY (basket_id, shipment_id),
  UNIQUE (basket_id, shipment_id, artist_id),
  CHECK (method = 'collection' OR cover IS NOT NULL),
  CHECK (refunded_cents <= delivery_cents + insurance_cents)
);

-- 3 · Artwork lines: commission per artwork, from the existing entitlement rule, with its evidence.
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
  commission_basis     TEXT NOT NULL,                                          -- e.g. founding_enquiry, gallery_artist_agreement
  entitlement_evidence TEXT CHECK (entitlement_evidence IS NULL OR json_valid(entitlement_evidence)),
  enquiry_ref          TEXT,
  processing_consent   INTEGER NOT NULL DEFAULT 0 CHECK (processing_consent IN (0, 1)),
  artwork_refunded_cents     INTEGER NOT NULL DEFAULT 0 CHECK (artwork_refunded_cents >= 0),
  commission_returned_cents  INTEGER NOT NULL DEFAULT 0 CHECK (commission_returned_cents >= 0),
  PRIMARY KEY (basket_id, line_id),
  UNIQUE (basket_id, artwork_id),
  FOREIGN KEY (basket_id, shipment_id, artist_id) REFERENCES basket_shipments(basket_id, shipment_id, artist_id),
  CHECK (commission_cents <= artwork_cents),
  CHECK (commission_cents = (artwork_cents * commission_bp) / 10000),         -- integer division: floor, as checkout-rules
  CHECK (artwork_refunded_cents <= artwork_cents),
  CHECK (commission_returned_cents <= commission_cents)
);
CREATE INDEX IF NOT EXISTS basket_lines_artwork ON basket_lines(artwork_id);
CREATE TRIGGER IF NOT EXISTS basket_lines_terms_fixed BEFORE UPDATE ON basket_lines
WHEN NEW.artwork_cents <> OLD.artwork_cents OR NEW.commission_bp <> OLD.commission_bp OR NEW.commission_cents <> OLD.commission_cents
  OR NEW.commission_basis <> OLD.commission_basis OR NEW.artist_id <> OLD.artist_id OR NEW.artwork_id <> OLD.artwork_id
BEGIN SELECT RAISE(ABORT, 'a basket line''s price and commission never change once recorded'); END;

-- 4 · Artist allocations: what each artist is owed, settled once Stripe records the processing fee.
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
  transferred_cents         INTEGER NOT NULL DEFAULT 0 CHECK (transferred_cents >= 0),
  reversed_cents            INTEGER NOT NULL DEFAULT 0 CHECK (reversed_cents >= 0),
  pending_reduced_cents     INTEGER NOT NULL DEFAULT 0 CHECK (pending_reduced_cents >= 0),
  shortfall_cents           INTEGER NOT NULL DEFAULT 0 CHECK (shortfall_cents >= 0),   -- recoverable only outside Stripe
  release                   TEXT NOT NULL CHECK (release IN ('on_payment','after_delivery','after_cancellation_window')),
  release_ready_at          TEXT,
  status                    TEXT NOT NULL DEFAULT 'awaiting_settlement' CHECK (status IN ('awaiting_settlement','held','ready',
                                                   'transferred','partially_reversed','reversed','shortfall')),
  updated_at                TEXT NOT NULL,
  PRIMARY KEY (basket_id, artist_id),
  CHECK (gross_cents = commission_cents + transfer_before_fees_cents),
  CHECK ((processing_share_cents IS NULL) = (transfer_due_cents IS NULL)),
  CHECK (transfer_due_cents IS NULL OR transfer_due_cents = transfer_before_fees_cents - processing_share_cents),
  CHECK (transfer_due_cents IS NOT NULL OR transferred_cents = 0),
  CHECK (transferred_cents + pending_reduced_cents <= COALESCE(transfer_due_cents, 0)),
  CHECK (reversed_cents <= transferred_cents)
);

-- 5 · Transfers to artists (one per artist per basket in the normal case). Idempotency keys make retries safe.
CREATE TABLE IF NOT EXISTS basket_transfers (
  id                    TEXT PRIMARY KEY,
  basket_id             TEXT NOT NULL,
  artist_id             TEXT NOT NULL,
  destination           TEXT NOT NULL CHECK (destination GLOB 'acct_*'),
  idempotency_key       TEXT NOT NULL UNIQUE,
  stripe_transfer_id    TEXT UNIQUE CHECK (stripe_transfer_id IS NULL OR stripe_transfer_id GLOB 'tr_*'),
  source_charge_id      TEXT NOT NULL CHECK (source_charge_id GLOB 'ch_*' OR source_charge_id GLOB 'py_*'),
  amount_cents          INTEGER NOT NULL CHECK (amount_cents > 0),
  amount_reversed_cents INTEGER NOT NULL DEFAULT 0 CHECK (amount_reversed_cents >= 0),
  livemode              INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  status                TEXT NOT NULL CHECK (status IN ('requested','created','failed')),
  failure               TEXT,
  created_at            TEXT NOT NULL,
  updated_at            TEXT NOT NULL,
  FOREIGN KEY (basket_id, artist_id) REFERENCES basket_artist_allocations(basket_id, artist_id),
  CHECK (amount_reversed_cents <= amount_cents),
  CHECK (status <> 'created' OR stripe_transfer_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS basket_transfers_basket ON basket_transfers(basket_id, artist_id);
CREATE TRIGGER IF NOT EXISTS basket_transfers_amount_fixed BEFORE UPDATE ON basket_transfers
WHEN NEW.amount_cents <> OLD.amount_cents OR NEW.destination <> OLD.destination OR NEW.source_charge_id <> OLD.source_charge_id
  OR NEW.idempotency_key <> OLD.idempotency_key OR NEW.livemode <> OLD.livemode
BEGIN SELECT RAISE(ABORT, 'a transfer''s amount, destination, source and key never change: record a reversal instead'); END;

-- 6 · Buyer refunds and how each was allocated (per line and per shipment).
CREATE TABLE IF NOT EXISTS basket_refunds (
  id                        TEXT PRIMARY KEY,
  basket_id                 TEXT NOT NULL REFERENCES basket_orders(id),
  idempotency_key           TEXT NOT NULL UNIQUE,
  stripe_refund_id          TEXT UNIQUE CHECK (stripe_refund_id IS NULL OR stripe_refund_id GLOB 're_*' OR stripe_refund_id GLOB 'pyr_*'),
  amount_cents              INTEGER NOT NULL CHECK (amount_cents > 0),
  commission_returned_cents INTEGER NOT NULL CHECK (commission_returned_cents >= 0 AND commission_returned_cents <= amount_cents),
  status                    TEXT NOT NULL CHECK (status IN ('requested','pending','requires_action','succeeded','failed','canceled')),
  reason                    TEXT NOT NULL,
  requested_by              TEXT NOT NULL,
  livemode                  INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  created_at                TEXT NOT NULL,
  updated_at                TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS basket_refund_parts (
  refund_id                 TEXT NOT NULL REFERENCES basket_refunds(id),
  kind                      TEXT NOT NULL CHECK (kind IN ('line','shipment')),
  ref                       TEXT NOT NULL,                   -- line_id or shipment_id
  artist_id                 TEXT NOT NULL,
  amount_cents              INTEGER NOT NULL CHECK (amount_cents > 0),
  commission_returned_cents INTEGER NOT NULL DEFAULT 0 CHECK (commission_returned_cents >= 0),
  artist_debit_cents        INTEGER NOT NULL CHECK (artist_debit_cents >= 0),
  PRIMARY KEY (refund_id, kind, ref),
  CHECK (amount_cents = artist_debit_cents + commission_returned_cents),
  CHECK (kind = 'line' OR commission_returned_cents = 0)
);
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_update BEFORE UPDATE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_refund_parts_no_delete BEFORE DELETE ON basket_refund_parts
BEGIN SELECT RAISE(ABORT, 'basket_refund_parts is append-only'); END;

-- 7 · Disputes on the basket payment (debited from PlotArt's platform balance by Stripe).
CREATE TABLE IF NOT EXISTS basket_disputes (
  id                 TEXT PRIMARY KEY,
  basket_id          TEXT NOT NULL REFERENCES basket_orders(id),
  stripe_dispute_id  TEXT NOT NULL UNIQUE CHECK (stripe_dispute_id GLOB 'du_*' OR stripe_dispute_id GLOB 'dp_*'),
  amount_cents       INTEGER NOT NULL CHECK (amount_cents > 0),
  fee_cents          INTEGER CHECK (fee_cents IS NULL OR fee_cents >= 0),
  status             TEXT NOT NULL CHECK (status IN ('open','won','lost')),
  reason             TEXT,
  attribution        TEXT CHECK (attribution IS NULL OR json_valid(attribution)),   -- basket-rules dispute().attribution
  allocation         TEXT CHECK (allocation IS NULL OR json_valid(allocation)),     -- per-artist recovery and PlotArt's cost
  livemode           INTEGER NOT NULL CHECK (livemode IN (0, 1)),
  opened_at          TEXT NOT NULL,
  closed_at          TEXT,
  CHECK ((status = 'open') = (closed_at IS NULL))
);

-- 8 · Transfer reversals, each tied to the refund or lost dispute that caused it.
CREATE TABLE IF NOT EXISTS basket_transfer_reversals (
  id                  TEXT PRIMARY KEY,
  transfer_id         TEXT NOT NULL REFERENCES basket_transfers(id),
  cause_kind          TEXT NOT NULL CHECK (cause_kind IN ('refund','dispute')),
  cause_id            TEXT NOT NULL,
  idempotency_key     TEXT NOT NULL UNIQUE,
  stripe_reversal_id  TEXT UNIQUE CHECK (stripe_reversal_id IS NULL OR stripe_reversal_id GLOB 'trr_*'),
  amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),
  status              TEXT NOT NULL CHECK (status IN ('requested','created','failed')),
  failure             TEXT,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  CHECK (status <> 'created' OR stripe_reversal_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS basket_transfer_reversals_cause ON basket_transfer_reversals(cause_kind, cause_id);

-- 9 · One original, one sale — across BOTH checkout paths. The basket's own reservations and sales, with guards that
--     refuse a basket hold or sale while the single-artist pilot (0017) holds or has sold the same work. The reverse guard
--     (the single-artist pilot refusing a work held by a basket) is NOT added here, because it would change an existing
--     table's behaviour; until it exists the two paths must not be switched on at the same time (see PR notes).
CREATE TABLE IF NOT EXISTS basket_artwork_reservations (
  artwork_id  TEXT PRIMARY KEY,
  basket_id   TEXT NOT NULL REFERENCES basket_orders(id),
  expires_at  TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS basket_artwork_reservations_not_single BEFORE INSERT ON basket_artwork_reservations
WHEN EXISTS (SELECT 1 FROM artwork_reservations r WHERE r.artwork_id = NEW.artwork_id AND julianday(r.expires_at) > julianday('now'))
  OR EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'this artwork is held or sold through the single-artist checkout'); END;
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
CREATE TRIGGER IF NOT EXISTS basket_artwork_sales_not_single BEFORE INSERT ON basket_artwork_sales
WHEN EXISTS (SELECT 1 FROM artwork_sales s WHERE s.artwork_id = NEW.artwork_id AND s.released_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'this artwork has already been sold through the single-artist checkout'); END;
CREATE TRIGGER IF NOT EXISTS basket_artwork_sales_no_delete BEFORE DELETE ON basket_artwork_sales
BEGIN SELECT RAISE(ABORT, 'basket_artwork_sales rows are kept with their basket; release them with a reason'); END;

-- 10 · Signed platform-account events (the basket's own webhook endpoint), recorded once each.
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

-- 11 · Audit trail for every basket change. Append-only.
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

-- Rollback (only before any basket data exists):
-- DROP TABLE IF EXISTS basket_events;
-- DROP TABLE IF EXISTS basket_payment_events;
-- DROP TABLE IF EXISTS basket_artwork_sales;
-- DROP TABLE IF EXISTS basket_artwork_reservations;
-- DROP TABLE IF EXISTS basket_transfer_reversals;
-- DROP TABLE IF EXISTS basket_disputes;
-- DROP TABLE IF EXISTS basket_refund_parts;
-- DROP TABLE IF EXISTS basket_refunds;
-- DROP TABLE IF EXISTS basket_transfers;
-- DROP TABLE IF EXISTS basket_artist_allocations;
-- DROP TABLE IF EXISTS basket_lines;
-- DROP TABLE IF EXISTS basket_shipments;
-- DROP TABLE IF EXISTS basket_orders;
