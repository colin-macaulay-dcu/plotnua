-- PlotArt Studio · migration 0016 · Managed checkout pilot (development 16 Nov 2026). NOT APPLIED IN PRODUCTION.
-- New tables only. No existing table, row, agreement, acceptance, gallery position or publishing record is changed.
-- Triggers are refusal-only BEFORE triggers on these NEW tables (migration-check policy, 6 Nov 2026): this migration
-- needs the founder's explicit approval of this exact file, and both production backups, before it runs.
-- Test mode only: every provider-facing table carries livemode = 0 by CHECK.
-- No foreign keys to artists/artworks: order and accounting records follow their own retention, and never block the
-- existing participation-deletion schedule.

-- 1 · Installed pilot texts: the artist payment addendum and the buyer purchase terms. A text is accepted only when the
--     same fingerprint is bundled with the Workers (src/payment-terms.js). Rows never change: a new text gets a new id.
CREATE TABLE IF NOT EXISTS payment_terms (
  doc_id       TEXT PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('artist_payment_addendum', 'buyer_purchase_terms')),
  title        TEXT NOT NULL,
  html_sha256  TEXT NOT NULL CHECK (length(html_sha256) = 64),
  effective_at TEXT NOT NULL,
  created_at   TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS payment_terms_no_update BEFORE UPDATE ON payment_terms
BEGIN SELECT RAISE(ABORT, 'payment_terms rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS payment_terms_no_delete BEFORE DELETE ON payment_terms
BEGIN SELECT RAISE(ABORT, 'payment_terms rows are never removed'); END;

-- 2 · Explicit artist opt-in and opt-out, append-only. The latest row decides. Joining needs the artist's own tick on
--     the installed addendum; nobody is enrolled by the founder or by default. The SEPARATE consent to Stripe's processing
--     charge on commission-free orders ('processing_consent' / '..._withdrawn') is recorded here too, with its statement.
CREATE TABLE IF NOT EXISTS payment_pilot_events (
  id            TEXT PRIMARY KEY,
  artist_id     TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('opted_in', 'left', 'processing_consent', 'processing_consent_withdrawn')),
  doc_id        TEXT REFERENCES payment_terms(doc_id),
  doc_sha256    TEXT,
  account_email TEXT NOT NULL,
  display_name  TEXT,
  statement     TEXT,
  at            TEXT NOT NULL,
  CHECK (kind IN ('left', 'processing_consent_withdrawn')
    OR (kind = 'opted_in' AND doc_id IS NOT NULL AND length(doc_sha256) = 64 AND statement IS NOT NULL AND display_name IS NOT NULL)
    OR (kind = 'processing_consent' AND doc_id IS NULL AND statement IS NOT NULL AND display_name IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS payment_pilot_events_artist ON payment_pilot_events(artist_id, at);
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_valid BEFORE INSERT ON payment_pilot_events
WHEN NEW.kind = 'opted_in' AND NOT EXISTS (SELECT 1 FROM payment_terms t WHERE t.doc_id = NEW.doc_id AND t.kind = 'artist_payment_addendum'
  AND t.html_sha256 = NEW.doc_sha256 AND julianday(NEW.at) >= julianday(t.effective_at))
BEGIN SELECT RAISE(ABORT, 'opt-in refused: not an installed addendum, wrong fingerprint, or dated before it took effect'); END;
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_no_update BEFORE UPDATE ON payment_pilot_events
BEGIN SELECT RAISE(ABORT, 'payment_pilot_events is append-only'); END;
-- deletable only six years after the artist LEFT the pilot, and only once none of their orders is still kept
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_no_delete BEFORE DELETE ON payment_pilot_events
WHEN EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artist_id = OLD.artist_id)
  OR NOT EXISTS (SELECT 1 FROM payment_pilot_events e WHERE e.artist_id = OLD.artist_id AND e.kind = 'left' AND julianday(e.at) <= julianday('now', '-6 years')
    AND e.at = (SELECT MAX(x.at) FROM payment_pilot_events x WHERE x.artist_id = OLD.artist_id))
BEGIN SELECT RAISE(ABORT, 'payment_pilot_events is kept until six years after the artist left and their orders are gone'); END;

-- 3 · The artist's own Stripe account (identity documents stay with Stripe's hosted onboarding; none are stored here).
CREATE TABLE IF NOT EXISTS payment_accounts (
  artist_id         TEXT PRIMARY KEY,
  provider          TEXT NOT NULL DEFAULT 'stripe' CHECK (provider = 'stripe'),
  account_id        TEXT NOT NULL UNIQUE CHECK (account_id GLOB 'acct_*'),
  country           TEXT NOT NULL CHECK (country IN ('IE', 'GB')),
  livemode          INTEGER NOT NULL DEFAULT 0 CHECK (livemode = 0),
  charges_enabled   INTEGER NOT NULL DEFAULT 0 CHECK (charges_enabled IN (0, 1)),
  payouts_enabled   INTEGER NOT NULL DEFAULT 0 CHECK (payouts_enabled IN (0, 1)),
  details_submitted INTEGER NOT NULL DEFAULT 0 CHECK (details_submitted IN (0, 1)),
  requirements_due  TEXT,
  checked_at        TEXT,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);

-- 4 · Orders: one artist, one unique original, EUR, integer cents. Money and entitlement are snapshotted when quoted.
CREATE TABLE IF NOT EXISTS checkout_orders (
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
  artwork_cents      INTEGER CHECK (artwork_cents IS NULL OR artwork_cents BETWEEN 100 AND 999999),
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
  livemode           INTEGER NOT NULL DEFAULT 0 CHECK (livemode = 0),
  created_by         TEXT NOT NULL,
  created_at         TEXT NOT NULL,
  updated_at         TEXT NOT NULL,
  CHECK (commission_cents IS NULL OR (commission_cents >= 0 AND commission_cents <= artwork_cents))
);
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

-- 5 · One reservation per original, with an explicit expiry. The PRIMARY KEY is what stops two checkouts at once.
CREATE TABLE IF NOT EXISTS artwork_reservations (
  artwork_id    TEXT PRIMARY KEY,
  order_id      TEXT NOT NULL UNIQUE REFERENCES checkout_orders(id),
  quote_version INTEGER NOT NULL,
  expires_at    TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

-- 6 · One sale per original. The partial unique index makes a second concurrent sale impossible at the database.
CREATE TABLE IF NOT EXISTS artwork_sales (
  order_id    TEXT PRIMARY KEY REFERENCES checkout_orders(id),
  artwork_id  TEXT NOT NULL,
  sold_at     TEXT NOT NULL,
  released_at TEXT,
  released_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS artwork_sales_one_active ON artwork_sales(artwork_id) WHERE released_at IS NULL;
CREATE TRIGGER IF NOT EXISTS artwork_sales_no_delete BEFORE DELETE ON artwork_sales
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'artwork_sales rows are kept with their order (retention and legal holds); release them with a reason'); END;

-- 7 · Hosted checkout sessions. At most one open session per order; a revised quote supersedes it first.
CREATE TABLE IF NOT EXISTS checkout_sessions (
  id              TEXT PRIMARY KEY CHECK (id GLOB 'cs_test_*'),
  order_id        TEXT NOT NULL REFERENCES checkout_orders(id),
  quote_version   INTEGER NOT NULL,
  amount_total    INTEGER NOT NULL,
  application_fee_cents INTEGER NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('open','complete','expired','superseded')),
  url             TEXT,
  expires_at      TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS checkout_sessions_one_open ON checkout_sessions(order_id) WHERE status = 'open';

-- 8 · Verified provider events. The provider's event id is unique: a repeated delivery is recognised, never re-applied.
CREATE TABLE IF NOT EXISTS payment_events (
  event_id     TEXT PRIMARY KEY CHECK (event_id GLOB 'evt_*'),
  type         TEXT NOT NULL,
  account      TEXT,
  livemode     INTEGER NOT NULL CHECK (livemode = 0),
  created      INTEGER NOT NULL,
  object_id    TEXT,
  order_id     TEXT,
  status       TEXT NOT NULL CHECK (status IN ('received','processed','ignored','deferred','failed')),
  attempts     INTEGER NOT NULL DEFAULT 1,
  detail       TEXT,
  received_at  TEXT NOT NULL,
  processed_at TEXT
);

-- 9 · The money ledger, append-only. Positive = towards the party named by kind; refunds and disputes are negative.
--     (kind, provider_ref) is unique so a repeated event can never book the same movement twice.
CREATE TABLE IF NOT EXISTS order_ledger (
  id           TEXT PRIMARY KEY,
  order_id     TEXT NOT NULL REFERENCES checkout_orders(id),
  kind         TEXT NOT NULL CHECK (kind IN ('charge','commission','artist_artwork','delivery_allocation',
                 'artwork_refund','delivery_refund','artwork_refund_reversed','delivery_refund_reversed','commission_refund','processing_fee','processing_reimbursement','processing_shortfall_paid','dispute','dispute_reinstated','dispute_fee','dispute_fee_returned','external_refund','adjustment')),
  amount_cents INTEGER NOT NULL,
  provider_ref TEXT,
  at           TEXT NOT NULL,
  note         TEXT,
  UNIQUE (kind, provider_ref)
);
CREATE INDEX IF NOT EXISTS order_ledger_order ON order_ledger(order_id, at);
CREATE TRIGGER IF NOT EXISTS order_ledger_no_update BEFORE UPDATE ON order_ledger
BEGIN SELECT RAISE(ABORT, 'order_ledger is append-only; add an adjustment'); END;
CREATE TRIGGER IF NOT EXISTS order_ledger_no_delete BEFORE DELETE ON order_ledger
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_ledger is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 10 · Refunds requested by the founder (the artist, as seller, can also refund in their own Stripe Dashboard: those
--      arrive as provider events and are booked as external_refund for founder review).
CREATE TABLE IF NOT EXISTS order_refunds (
  id                  TEXT PRIMARY KEY,
  order_id            TEXT NOT NULL REFERENCES checkout_orders(id),
  artwork_cents       INTEGER NOT NULL CHECK (artwork_cents >= 0),
  delivery_cents      INTEGER NOT NULL CHECK (delivery_cents >= 0),
  commission_refund_cents INTEGER NOT NULL CHECK (commission_refund_cents >= 0),
  reason              TEXT NOT NULL CHECK (length(reason) BETWEEN 3 AND 500),
  status              TEXT NOT NULL CHECK (status IN ('pending','succeeded','failed')),
  provider_refund_id  TEXT UNIQUE,
  fee_refund_id       TEXT UNIQUE,
  error               TEXT,
  requested_by        TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  CHECK (artwork_cents + delivery_cents > 0)
);

-- 11 · Fulfilment evidence, append-only: confirmations, dispatch, delivery, signed receipt, condition photographs.
CREATE TABLE IF NOT EXISTS order_fulfilment_events (
  id        TEXT PRIMARY KEY,
  order_id  TEXT NOT NULL REFERENCES checkout_orders(id),
  kind      TEXT NOT NULL CHECK (kind IN ('dispatched','delivered','signed_receipt','condition_photos','tracking','insurance','note')),
  actor     TEXT NOT NULL,
  at        TEXT NOT NULL,
  evidence  TEXT NOT NULL CHECK (length(evidence) BETWEEN 2 AND 2000)
);
CREATE TRIGGER IF NOT EXISTS order_fulfilment_events_no_update BEFORE UPDATE ON order_fulfilment_events
BEGIN SELECT RAISE(ABORT, 'order_fulfilment_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS order_fulfilment_events_no_delete BEFORE DELETE ON order_fulfilment_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_fulfilment_events is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 12 · Order audit: actor, action, time, prior and new status. Append-only.
CREATE TABLE IF NOT EXISTS order_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id    TEXT NOT NULL REFERENCES checkout_orders(id),
  at          TEXT NOT NULL,
  actor       TEXT NOT NULL,
  action      TEXT NOT NULL,
  prior_status TEXT,
  new_status  TEXT,
  detail      TEXT
);
CREATE INDEX IF NOT EXISTS order_events_order ON order_events(order_id, id);
CREATE TRIGGER IF NOT EXISTS order_events_no_update BEFORE UPDATE ON order_events
BEGIN SELECT RAISE(ABORT, 'order_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS order_events_no_delete BEFORE DELETE ON order_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_events is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 13 · Legal holds: keep one order's records past its retention date for a stated reason, reviewed at least every 12
--      months, released with a reason. Only review_by can change (renewal) and released_* can be set once.
CREATE TABLE IF NOT EXISTS checkout_holds (
  id             TEXT PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES checkout_orders(id),
  basis          TEXT NOT NULL CHECK (basis IN ('dispute','claim','revenue_enquiry','investigation','litigation','data_subject_request','other')),
  reason         TEXT NOT NULL CHECK (length(reason) BETWEEN 10 AND 1000),
  placed_by      TEXT NOT NULL,
  placed_at      TEXT NOT NULL,
  review_by      TEXT NOT NULL CHECK (review_by GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  released_at    TEXT,
  released_by    TEXT,
  release_reason TEXT,
  CHECK ((released_at IS NULL) = (released_by IS NULL) AND (released_at IS NULL) = (release_reason IS NULL))
);
CREATE INDEX IF NOT EXISTS checkout_holds_order ON checkout_holds(order_id, released_at);
CREATE TRIGGER IF NOT EXISTS checkout_holds_limited_update BEFORE UPDATE ON checkout_holds
WHEN NEW.id <> OLD.id OR NEW.order_id <> OLD.order_id OR NEW.basis <> OLD.basis OR NEW.reason <> OLD.reason OR NEW.placed_by <> OLD.placed_by
  OR NEW.placed_at <> OLD.placed_at OR OLD.released_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'a hold can only be renewed (new review date) or released once'); END;
CREATE TRIGGER IF NOT EXISTS checkout_holds_no_delete BEFORE DELETE ON checkout_holds
WHEN OLD.released_at IS NULL OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'a hold is deleted only after release, with its order, once retention has ended'); END;
CREATE TABLE IF NOT EXISTS checkout_hold_events (
  id        TEXT PRIMARY KEY,
  hold_id   TEXT NOT NULL REFERENCES checkout_holds(id),
  order_id  TEXT NOT NULL,
  kind      TEXT NOT NULL CHECK (kind IN ('placed','renewed','released')),
  actor     TEXT NOT NULL,
  at        TEXT NOT NULL,
  note      TEXT NOT NULL,
  review_by TEXT
);
CREATE TRIGGER IF NOT EXISTS checkout_hold_events_no_update BEFORE UPDATE ON checkout_hold_events
BEGIN SELECT RAISE(ABORT, 'checkout_hold_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS checkout_hold_events_no_delete BEFORE DELETE ON checkout_hold_events
WHEN EXISTS (SELECT 1 FROM checkout_holds h WHERE h.id = OLD.hold_id AND h.released_at IS NULL)
  OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hold history is kept with its order'); END;

-- 13 · Seller information a buyer must have before paying (CRA 2022 Sch. 3; s.107). Kept by the artist in Studio while they
--      are in the pilot; each issued quote keeps its own copy (quote_snapshots), so later edits never change a quote.
CREATE TABLE IF NOT EXISTS seller_profiles (
  artist_id       TEXT PRIMARY KEY,
  legal_name      TEXT NOT NULL,
  trading_name    TEXT,
  address         TEXT NOT NULL,              -- geographical address at which the seller is established
  returns_address TEXT,                       -- if different: where returns and complaints go
  email           TEXT NOT NULL,
  phone           TEXT NOT NULL,
  trader_status   TEXT NOT NULL CHECK (trader_status IN ('trader','not_trader')),
  vat_number      TEXT,
  declared_at     TEXT NOT NULL,
  declared_by     TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

-- 14 · The exact quote the buyer was shown, per issued version: append-only, fingerprinted, kept with its order.
CREATE TABLE IF NOT EXISTS quote_snapshots (
  order_id      TEXT NOT NULL REFERENCES checkout_orders(id),
  quote_version INTEGER NOT NULL,
  snapshot      TEXT NOT NULL,
  sha256        TEXT NOT NULL,
  issued_at     TEXT NOT NULL,
  PRIMARY KEY (order_id, quote_version)
);
CREATE TRIGGER IF NOT EXISTS quote_snapshots_no_update BEFORE UPDATE ON quote_snapshots
BEGIN SELECT RAISE(ABORT, 'quote_snapshots is append-only'); END;
CREATE TRIGGER IF NOT EXISTS quote_snapshots_no_delete BEFORE DELETE ON quote_snapshots
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'quote_snapshots are kept with their order'); END;

-- 15 · Messages PlotArt prepares for an order (the buyer's purchase confirmation): the exact text, fingerprinted, once
--      per order and kind; every delivery attempt is recorded separately. In test mode nothing leaves PlotArt: messages
--      go only to checkout_mail_sink.
CREATE TABLE IF NOT EXISTS order_messages (
  id             TEXT PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES checkout_orders(id),
  kind           TEXT NOT NULL CHECK (kind IN ('buyer_confirmation','buyer_refund_pending','buyer_refund_failed','buyer_refund_reversed')),
  item_key       TEXT NOT NULL DEFAULT '',          -- e.g. the refund a notice is about: one notice per order, kind and refund
  recipient_role TEXT NOT NULL CHECK (recipient_role IN ('buyer','artist','founder')),
  subject        TEXT NOT NULL,
  body           TEXT NOT NULL,
  sha256         TEXT NOT NULL,
  created_at     TEXT NOT NULL,
  UNIQUE (order_id, kind, item_key)
);
CREATE TRIGGER IF NOT EXISTS order_messages_no_update BEFORE UPDATE ON order_messages
BEGIN SELECT RAISE(ABORT, 'order_messages is append-only'); END;
CREATE TABLE IF NOT EXISTS order_message_deliveries (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT NOT NULL REFERENCES order_messages(id),
  order_id   TEXT NOT NULL,
  at         TEXT NOT NULL,
  channel    TEXT NOT NULL CHECK (channel IN ('test_sink','none','provider')),
  status     TEXT NOT NULL CHECK (status IN ('held_in_test_sink','not_sent_no_provider','accepted_by_provider','failed')),   -- 'accepted_by_provider' is not proof of inbox delivery
  detail     TEXT
);
CREATE TRIGGER IF NOT EXISTS order_message_deliveries_no_update BEFORE UPDATE ON order_message_deliveries
BEGIN SELECT RAISE(ABORT, 'order_message_deliveries is append-only'); END;
CREATE TABLE IF NOT EXISTS checkout_mail_sink (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         TEXT NOT NULL,
  order_id   TEXT,
  kind       TEXT NOT NULL,
  to_role    TEXT NOT NULL,
  to_sha256  TEXT NOT NULL,                   -- the intended address is never stored here, only its fingerprint
  subject    TEXT NOT NULL,
  body       TEXT NOT NULL
);

-- 16 · Amounts PlotArt owes artists (fee model B shortfalls; commission to return after a lost dispute, PA-GAA 9).
--      One row per item; the amount, rule and due date never change; settlement is recorded payment by payment.
CREATE TABLE IF NOT EXISTS checkout_owed (
  id              TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL REFERENCES checkout_orders(id),
  kind            TEXT NOT NULL CHECK (kind IN ('processing_shortfall','commission_shortfall','lost_dispute_commission')),
  item_key        TEXT NOT NULL,
  cents           INTEGER NOT NULL CHECK (cents > 0),
  reason          TEXT NOT NULL,
  arisen_at       TEXT NOT NULL,
  due_at          TEXT NOT NULL,
  due_rule        TEXT NOT NULL,
  due_provisional INTEGER NOT NULL CHECK (due_provisional IN (0,1)),
  settled_cents   INTEGER NOT NULL DEFAULT 0 CHECK (settled_cents >= 0),
  reminders       TEXT,                       -- JSON: reminder stages already sent
  due_basis_event TEXT,                       -- PA-PAY 3.5 (sandbox rule, 18 Nov 2026): the record that first established the amount owed by bank transfer
  due_basis_at    TEXT,                       -- that record's time
  due_basis_date  TEXT,                       -- its Irish (Europe/Dublin) date; day one is the next day, due by the end of day 30
  due_basis_source TEXT CHECK (due_basis_source IS NULL OR due_basis_source IN ('stripe','pilot')),
  due_review      TEXT,                       -- why the founder should review the start date (uncertain time), if so
  last_return_id  TEXT,                       -- the returned transfer that last reduced settled_cents (see trigger)
  UNIQUE (order_id, item_key),
  CHECK (settled_cents <= cents)
);
CREATE INDEX IF NOT EXISTS checkout_owed_open ON checkout_owed(due_at) WHERE settled_cents < cents;
CREATE TRIGGER IF NOT EXISTS checkout_owed_fixed BEFORE UPDATE ON checkout_owed
WHEN NEW.cents <> OLD.cents OR NEW.kind <> OLD.kind OR NEW.due_at <> OLD.due_at OR NEW.order_id <> OLD.order_id
  OR NEW.due_basis_date IS NOT OLD.due_basis_date OR NEW.due_basis_at IS NOT OLD.due_basis_at OR NEW.due_basis_event IS NOT OLD.due_basis_event
  OR (NEW.settled_cents < OLD.settled_cents AND NOT (NEW.last_return_id IS NOT NULL AND NEW.last_return_id IS NOT OLD.last_return_id
      AND EXISTS (SELECT 1 FROM checkout_owed_payment_returns r WHERE r.id = NEW.last_return_id AND r.owed_id = OLD.id AND r.cents = OLD.settled_cents - NEW.settled_cents)))
BEGIN SELECT RAISE(ABORT, 'an owed amount, its rule and due date are fixed; settlement only increases, except by a recorded returned transfer'); END;
CREATE TABLE IF NOT EXISTS checkout_owed_payments (
  id          TEXT PRIMARY KEY,
  owed_id     TEXT NOT NULL REFERENCES checkout_owed(id),
  order_id    TEXT NOT NULL,
  cents       INTEGER NOT NULL CHECK (cents > 0),
  method      TEXT NOT NULL CHECK (method IN ('bank_transfer','stripe_application_fee_refund','moved_to_direct_payment')),
  reference   TEXT NOT NULL,                  -- transfer reference / fee refund id: never bank details
  executed_on TEXT,                           -- bank_transfer: the date PlotArt's bank shows the transfer as executed (YYYY-MM-DD)
  recorded_by TEXT NOT NULL,
  at          TEXT NOT NULL,
  UNIQUE (owed_id, reference),
  CHECK (method <> 'bank_transfer' OR executed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);
CREATE TRIGGER IF NOT EXISTS checkout_owed_payments_no_update BEFORE UPDATE ON checkout_owed_payments
BEGIN SELECT RAISE(ABORT, 'checkout_owed_payments is append-only'); END;
-- A bank transfer that came back: the outstanding amount is restored; the payment itself stays in the history.
CREATE TABLE IF NOT EXISTS checkout_owed_payment_returns (
  id          TEXT PRIMARY KEY,
  payment_id  TEXT NOT NULL UNIQUE REFERENCES checkout_owed_payments(id),
  owed_id     TEXT NOT NULL REFERENCES checkout_owed(id),
  order_id    TEXT NOT NULL,
  cents       INTEGER NOT NULL CHECK (cents > 0),
  returned_on TEXT NOT NULL CHECK (returned_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  reason      TEXT NOT NULL,
  recorded_by TEXT NOT NULL,
  at          TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS checkout_owed_payment_returns_no_update BEFORE UPDATE ON checkout_owed_payment_returns
BEGIN SELECT RAISE(ABORT, 'checkout_owed_payment_returns is append-only'); END;

-- Rollback (only before any pilot data exists):
-- DROP TABLE IF EXISTS checkout_owed_payment_returns;
-- DROP TABLE IF EXISTS checkout_owed_payments;
-- DROP TABLE IF EXISTS checkout_owed;
-- DROP TABLE IF EXISTS checkout_mail_sink;
-- DROP TABLE IF EXISTS order_message_deliveries;
-- DROP TABLE IF EXISTS order_messages;
-- DROP TABLE IF EXISTS quote_snapshots;
-- DROP TABLE IF EXISTS seller_profiles;
-- DROP TABLE IF EXISTS checkout_hold_events;
-- DROP TABLE IF EXISTS checkout_holds;
-- DROP TABLE IF EXISTS order_events;
-- DROP TABLE IF EXISTS order_fulfilment_events;
-- DROP TABLE IF EXISTS order_refunds;
-- DROP TABLE IF EXISTS order_ledger;
-- DROP TABLE IF EXISTS payment_events;
-- DROP TABLE IF EXISTS checkout_sessions;
-- DROP TABLE IF EXISTS artwork_sales;
-- DROP TABLE IF EXISTS artwork_reservations;
-- DROP TABLE IF EXISTS checkout_orders;
-- DROP TABLE IF EXISTS payment_accounts;
-- DROP TABLE IF EXISTS payment_pilot_events;
-- DROP TABLE IF EXISTS payment_terms;
