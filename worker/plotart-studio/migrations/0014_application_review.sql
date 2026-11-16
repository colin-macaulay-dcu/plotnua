-- Gallery applications only. No existing application/artist rows are changed.
CREATE TABLE IF NOT EXISTS application_review (
  ref TEXT PRIMARY KEY,
  revision INTEGER NOT NULL DEFAULT 0,
  token_hash TEXT,
  token_expires TEXT,
  requested_message TEXT,
  active_action TEXT,
  active_since TEXT,
  revised_at TEXT
);
CREATE TABLE IF NOT EXISTS application_review_actions (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL,
  kind TEXT NOT NULL,
  actor TEXT NOT NULL,
  payload TEXT NOT NULL,
  phase TEXT NOT NULL DEFAULT 'prepared',
  running_at TEXT,
  created_at TEXT NOT NULL,
  sent_at TEXT,
  completed_at TEXT,
  error TEXT,
  FOREIGN KEY(ref) REFERENCES application_review(ref) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS application_review_actions_ref ON application_review_actions(ref,created_at);
