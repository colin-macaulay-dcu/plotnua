-- PlotArt Studio · migration 0019 · Multi-artist basket on the existing direct-charge checkout (prepared 21 Nov 2026).
-- PROPOSAL FOR FOUNDER APPROVAL. NOT APPLIED to any production database. Requires 0017 (managed checkout) first.
-- ADDITIVE: new tables, indexes and refusal-only BEFORE triggers on those NEW tables. No existing table, row, agreement,
-- acceptance, gallery position or publishing record is changed.
--
-- Supersedes the unmerged PR #43 proposal of the same number (0019_basket_checkout.sql, "separate charges and transfers"):
-- that design made PlotArt the merchant of record. This one keeps the existing architecture: every artwork in a basket is
-- an ordinary checkout_orders row paid by a DIRECT CHARGE on its artist's own Stripe account (artist = seller and merchant
-- of record; PlotArt's commission is the application fee). The buyer enters their card ONCE on Stripe-hosted Checkout in
-- setup mode on PlotArt's account; the saved card is cloned to each artist's account and each charge is AUTHORISED
-- (capture_method = manual) before ANY is captured (proven in Stripe TEST mode: run 44930999959, 21 PASS / 0 FAIL).
--
-- Every provider-facing table records livemode (0 test, 1 live); the code never mixes modes (stripe.js stripeMode).

-- 1 · Basket texts: the buyer's basket purchase terms and the artist's basket addendum. The single-artwork texts
--     (PA-PAY-2026-11 1.3, PA-BPT-2026-11) exclude multi-artwork orders, so a basket has its own texts. A text is accepted
--     only when the same fingerprint is bundled with the Workers (src/basket-terms.js). Rows never change.
CREATE TABLE IF NOT EXISTS basket_terms (
  doc_id       TEXT PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('artist_basket_addendum', 'buyer_basket_terms')),
  title        TEXT NOT NULL,
  html_sha256  TEXT NOT NULL CHECK (length(html_sha256) = 64),
  effective_at TEXT NOT NULL,
  created_at   TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS basket_terms_no_update BEFORE UPDATE ON basket_terms
BEGIN SELECT RAISE(ABORT, 'basket_terms rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS basket_terms_no_delete BEFORE DELETE ON basket_terms
BEGIN SELECT RAISE(ABORT, 'basket_terms rows are never removed'); END;

-- 2 · Artist opt-in to baskets, append-only (separate from the single-artwork pilot opt-in, which it requires).
CREATE TABLE IF NOT EXISTS basket_artist_events (
  id            TEXT PRIMARY KEY,
  artist_id     TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('opted_in', 'left')),
  doc_id        TEXT REFERENCES basket_terms(doc_id),
  doc_sha256    TEXT,
  account_email TEXT NOT NULL,
  statement     TEXT,
  at            TEXT NOT NULL,
  CHECK (kind = 'left' OR (doc_id IS NOT NULL AND length(doc_sha256) = 64 AND statement IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS basket_artist_events_artist ON basket_artist_events(artist_id, at);
CREATE TRIGGER IF NOT EXISTS basket_artist_events_valid BEFORE INSERT ON basket_artist_events
WHEN NEW.kind = 'opted_in' AND NOT EXISTS (SELECT 1 FROM basket_terms t WHERE t.doc_id = NEW.doc_id AND t.kind = 'artist_basket_addendum'
  AND t.html_sha256 = NEW.doc_sha256 AND julianday(NEW.at) >= julianday(t.effective_at))
BEGIN SELECT RAISE(ABORT, 'basket opt-in refused: not an installed basket addendum, wrong fingerprint, or dated before it took effect'); END;
CREATE TRIGGER IF NOT EXISTS basket_artist_events_no_update BEFORE UPDATE ON basket_artist_events
BEGIN SELECT RAISE(ABORT, 'basket_artist_events is append-only'); END;

-- 3 · The artist's standing delivery offer for one artwork (instant purchase needs a known delivery price, route and
--     cover before the buyer pays). Same fields as a quoted delivery (checkout-rules.js cleanDelivery), approved by the
--     artist. Withdrawn or edited offers never change a basket already opened: each order keeps its own copy.
CREATE TABLE IF NOT EXISTS artwork_delivery_offers (
  artwork_id     TEXT PRIMARY KEY,
  artist_id      TEXT NOT NULL,
  region         TEXT NOT NULL CHECK (region IN ('IE')),
  delivery_cents INTEGER NOT NULL CHECK (delivery_cents BETWEEN 0 AND 200000),
  delivery       TEXT NOT NULL,              -- JSON (checkout-rules.js cleanDelivery); destination is the region, completed per order
  version        INTEGER NOT NULL DEFAULT 1,
  approved_by    TEXT NOT NULL,
  approved_at    TEXT NOT NULL,
  withdrawn_at   TEXT,
  created_at     TEXT NOT NULL,
  updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS artwork_delivery_offers_artist ON artwork_delivery_offers(artist_id);

-- 4 · A basket: one buyer, one card entry, one or more artworks (each an ordinary checkout_orders row).
--     Status is "paid" ONLY when every line's charge has been captured and recorded.
CREATE TABLE IF NOT EXISTS checkout_baskets (
  id                TEXT PRIMARY KEY,
  reference         TEXT NOT NULL UNIQUE CHECK (reference GLOB 'PA-B-*'),
  status            TEXT NOT NULL CHECK (status IN ('open','authorising','action_required','capturing','paid','failed','expired','cancelled','needs_resolution')),
  buyer_email       TEXT NOT NULL,
  buyer_name        TEXT NOT NULL,
  delivery_address  TEXT NOT NULL,           -- JSON: name, lines, town, county, eircode, phone (Ireland only)
  buyer_token_hash  TEXT NOT NULL UNIQUE,
  terms_doc_id      TEXT NOT NULL REFERENCES basket_terms(doc_id),
  terms_accepted_at TEXT NOT NULL,
  total_cents       INTEGER NOT NULL CHECK (total_cents > 0),
  line_count        INTEGER NOT NULL CHECK (line_count BETWEEN 1 AND 10),
  platform_customer TEXT,                    -- Stripe Customer on PlotArt's account (deleted when the basket ends)
  setup_session     TEXT UNIQUE CHECK (setup_session IS NULL OR setup_session GLOB 'cs_test_*' OR setup_session GLOB 'cs_live_*'),
  setup_intent      TEXT,
  payment_method    TEXT,                    -- the saved card on PlotArt's account (detached when the basket ends)
  card_released_at  TEXT,
  expires_at        TEXT NOT NULL,           -- the hosted page and the reservations (extended while authorising)
  action_deadline   TEXT,                    -- additional authentication must be completed by then, or every charge is cancelled
  lease_until       TEXT,                    -- one coordinator at a time
  attempts          INTEGER NOT NULL DEFAULT 0,
  resolution        TEXT,
  livemode          INTEGER NOT NULL DEFAULT 0 CHECK (livemode IN (0, 1)),
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS checkout_baskets_status ON checkout_baskets(status, updated_at);
CREATE INDEX IF NOT EXISTS checkout_baskets_buyer ON checkout_baskets(buyer_email COLLATE NOCASE, created_at);

-- 5 · One line per artwork: its order, and the state of its direct charge on the artist's account.
CREATE TABLE IF NOT EXISTS basket_lines (
  order_id        TEXT PRIMARY KEY REFERENCES checkout_orders(id),
  basket_id       TEXT NOT NULL REFERENCES checkout_baskets(id),
  line_no         INTEGER NOT NULL,
  artist_id       TEXT NOT NULL,
  account         TEXT NOT NULL CHECK (account GLOB 'acct_*'),
  amount_cents    INTEGER NOT NULL CHECK (amount_cents > 0),
  fee_cents       INTEGER NOT NULL CHECK (fee_cents >= 0 AND fee_cents < amount_cents),
  state           TEXT NOT NULL CHECK (state IN ('pending','authorised','action_required','captured','declined','cancelled','error')),
  clone_pm        TEXT,
  payment_intent  TEXT UNIQUE,
  decline_code    TEXT,
  last_error      TEXT,
  attempts        INTEGER NOT NULL DEFAULT 0,
  updated_at      TEXT NOT NULL,
  UNIQUE (basket_id, line_no)
);
CREATE INDEX IF NOT EXISTS basket_lines_basket ON basket_lines(basket_id);

-- 6 · Basket history, append-only.
CREATE TABLE IF NOT EXISTS basket_events (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  basket_id TEXT NOT NULL REFERENCES checkout_baskets(id),
  at        TEXT NOT NULL,
  actor     TEXT NOT NULL,
  action    TEXT NOT NULL,
  prior     TEXT,
  next      TEXT,
  detail    TEXT
);
CREATE INDEX IF NOT EXISTS basket_events_basket ON basket_events(basket_id, id);
CREATE TRIGGER IF NOT EXISTS basket_events_no_update BEFORE UPDATE ON basket_events
BEGIN SELECT RAISE(ABORT, 'basket_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS basket_events_no_delete BEFORE DELETE ON basket_events
WHEN EXISTS (SELECT 1 FROM basket_lines l JOIN checkout_orders o ON o.id = l.order_id WHERE l.basket_id = OLD.basket_id
  AND (o.retain_until IS NULL OR julianday(o.retain_until) > julianday('now')))
BEGIN SELECT RAISE(ABORT, 'basket history is kept with its orders'); END;
