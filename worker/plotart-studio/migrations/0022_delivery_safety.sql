-- PlotArt · delivery safety (22 Nov 2026). NEW TABLES ONLY: nothing existing changes. Requires 0017 and 0019.
-- Re-runnable (IF NOT EXISTS throughout).
--
--   delivery_offer_events   append-only history of the artist's own delivery-offer actions (saved, withdrawn), each with the
--                           offer version and the fingerprint of its exact content.
--   delivery_offer_reviews  append-only record of the founder's review of one exact offer version: approved or returned (with
--                           a note). An artwork is offered in the basket only while the LATEST review of its offer approves
--                           the CURRENT version AND fingerprint (basket.js lineFor). Any change by the artist makes a new
--                           version, so a previous approval no longer counts until the founder reviews again.
--   order_overdue_alerts    one row per (order, kind) when the founder has been alerted that a paid order passed its dispatch
--                           or delivery deadline: the key is what prevents a second alert for the same order and kind.

CREATE TABLE IF NOT EXISTS delivery_offer_events (
  id             TEXT PRIMARY KEY,
  artwork_id     TEXT NOT NULL,
  artist_id      TEXT NOT NULL,
  kind           TEXT NOT NULL CHECK (kind IN ('saved', 'withdrawn')),
  offer_version  INTEGER NOT NULL,
  offer_sha256   TEXT,
  actor          TEXT NOT NULL,
  at             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS delivery_offer_events_artwork ON delivery_offer_events(artwork_id, at);
CREATE TRIGGER IF NOT EXISTS delivery_offer_events_no_update BEFORE UPDATE ON delivery_offer_events
BEGIN SELECT RAISE(ABORT, 'delivery_offer_events rows never change'); END;
CREATE TRIGGER IF NOT EXISTS delivery_offer_events_no_delete BEFORE DELETE ON delivery_offer_events
BEGIN SELECT RAISE(ABORT, 'delivery_offer_events rows are never removed'); END;

CREATE TABLE IF NOT EXISTS delivery_offer_reviews (
  id             TEXT PRIMARY KEY,
  artwork_id     TEXT NOT NULL,
  artist_id      TEXT NOT NULL,
  offer_version  INTEGER NOT NULL,
  offer_sha256   TEXT NOT NULL,
  decision       TEXT NOT NULL CHECK (decision IN ('approved', 'returned')),
  note           TEXT,
  reviewed_by    TEXT NOT NULL,
  reviewed_at    TEXT NOT NULL,
  livemode       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS delivery_offer_reviews_artwork ON delivery_offer_reviews(artwork_id, reviewed_at);
CREATE TRIGGER IF NOT EXISTS delivery_offer_reviews_no_update BEFORE UPDATE ON delivery_offer_reviews
BEGIN SELECT RAISE(ABORT, 'delivery_offer_reviews rows never change: record a new review'); END;
CREATE TRIGGER IF NOT EXISTS delivery_offer_reviews_no_delete BEFORE DELETE ON delivery_offer_reviews
BEGIN SELECT RAISE(ABORT, 'delivery_offer_reviews rows are never removed'); END;
CREATE TRIGGER IF NOT EXISTS delivery_offer_reviews_current BEFORE INSERT ON delivery_offer_reviews
WHEN NOT EXISTS (SELECT 1 FROM artwork_delivery_offers o WHERE o.artwork_id = NEW.artwork_id AND o.artist_id = NEW.artist_id
  AND o.version = NEW.offer_version AND o.withdrawn_at IS NULL)
BEGIN SELECT RAISE(ABORT, 'review refused: not the current version of a current delivery offer'); END;

CREATE TABLE IF NOT EXISTS order_overdue_alerts (
  order_id       TEXT NOT NULL,
  kind           TEXT NOT NULL CHECK (kind IN ('dispatch_overdue', 'delivery_overdue')),
  due_at         TEXT NOT NULL,
  deadline_basis TEXT NOT NULL CHECK (deadline_basis IN ('agreed', 'default')),
  alerted_at     TEXT NOT NULL,
  PRIMARY KEY (order_id, kind)
);
CREATE TRIGGER IF NOT EXISTS order_overdue_alerts_no_update BEFORE UPDATE ON order_overdue_alerts
BEGIN SELECT RAISE(ABORT, 'order_overdue_alerts rows never change'); END;
