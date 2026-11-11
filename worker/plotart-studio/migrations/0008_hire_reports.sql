-- PlotArt Studio · migration 0008 · Art for Hire hire reports (development 11 Nov 2026, PA-AFH-2026-11 r5 clauses 6.5, 6.6, 10.1)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Additive only: two NEW tables, their indexes and refusal-only guards. No existing table, column, row, trigger, agreement,
-- gallery, enquiry or document is changed. enquiry_log, artists and artworks are read by the Studio, never written here.
-- The lightweight administration model (founder decision, 11 Nov 2026): artists report successful hires in Studio; the founder
-- keeps the invoice and payment status here by hand; invoices are issued and payments taken OUTSIDE Studio. There is no
-- invoicing, payment, ledger or reminder machinery, and no hirer contact detail is stored in either table.
-- Preconditions before anyone runs it:
--   (1) a fresh D1 backup (studio-d1-backup or the migration workflow's own two backups);
--   (2) migration 0007 has run (hire_terms_acceptances is referenced by the Studio before a report is accepted);
--   (3) the founder has approved this exact file (SHA-256) and its refusal-only guards;
--   (4) it runs through studio-d1-migration (environment studio-database, founder approval). Claude never runs it.
-- Foreign keys: none to artists (the six-year deletion clears these rows BEFORE record_retention, as for 0007's append-only
-- tables); hire_report_records references hire_reports only.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

-- 1 · An artist's report of a successful hire (r5 clause 6.5). Append-only: a mistake is corrected by a NEW report that
--     names the one it corrects. The commission basis and amount are fixed when the report is made, from the enquiry log's
--     founding flag (fixed at introduction, clause 6.3) and the 12-month window measured from the introduction to the date
--     the hire was AGREED (clause 6.2(c)). A hire period starting before the introduction is flagged for the founder.
CREATE TABLE IF NOT EXISTS hire_reports (
  id               TEXT PRIMARY KEY,
  artist_id        TEXT NOT NULL,                     -- artists.id (no foreign key: see the header)
  reference        TEXT NOT NULL,                     -- enquiry_log.reference: PA-H-... (relay) or PA-EM-... (logged email introduction)
  artwork_ids      TEXT NOT NULL CHECK (json_valid(artwork_ids) AND json_array_length(artwork_ids) BETWEEN 1 AND 20),
  hire_start       TEXT NOT NULL CHECK (hire_start GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  hire_end         TEXT NOT NULL CHECK (hire_end GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND hire_end >= hire_start),
  agreed_on        TEXT NOT NULL CHECK (agreed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),   -- the date the hire was agreed (clause 6.2(c))
  starts_before_introduction INTEGER NOT NULL CHECK (starts_before_introduction IN (0, 1)),            -- flagged for the founder, not refused
  net_fee_cents    INTEGER NOT NULL CHECK (net_fee_cents BETWEEN 0 AND 100000000),   -- excludes VAT and itemised expenses (6.2(d))
  more_to_pay      INTEGER NOT NULL CHECK (more_to_pay IN (0, 1)),                  -- an instalment: more of the fee is still due
  introduced_at    TEXT NOT NULL,                     -- copied from enquiry_log.introduced_at
  founding         INTEGER NOT NULL CHECK (founding IN (0, 1)),   -- copied from enquiry_log.founding (protected, 6.3)
  basis            TEXT NOT NULL CHECK (basis IN ('commission', 'founding_year', 'outside_window', 'no_fee')),
  rate_bp          INTEGER NOT NULL CHECK (rate_bp = 1000),       -- 10% in basis points (PA-AFH-2026-11 clause 6.1)
  commission_cents INTEGER NOT NULL CHECK (commission_cents >= 0 AND (basis = 'commission' OR commission_cents = 0)),
  terms_doc        TEXT NOT NULL,                     -- the PA-AFH identifier the artist had accepted when reporting
  corrects         TEXT REFERENCES hire_reports(id),
  reported_at      TEXT NOT NULL,
  reported_by      TEXT NOT NULL,                     -- the artist's Studio address
  CHECK (basis <> 'founding_year' OR founding = 1)
);
CREATE INDEX IF NOT EXISTS hire_reports_artist ON hire_reports(artist_id, reported_at);
CREATE INDEX IF NOT EXISTS hire_reports_reference ON hire_reports(reference);
CREATE TRIGGER IF NOT EXISTS hire_reports_no_update BEFORE UPDATE ON hire_reports
BEGIN SELECT RAISE(ABORT, 'hire_reports is append-only: report a correction instead'); END;
CREATE TRIGGER IF NOT EXISTS hire_reports_no_delete BEFORE DELETE ON hire_reports
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_reports is kept until its retention period has ended'); END;

-- 2 · The founder's own manual record for each report (r5 clauses 6.6 and 10.1): whether it has been invoiced and paid.
--     Editable by the founder only (every change audited); deleted with the report once retention has ended.
CREATE TABLE IF NOT EXISTS hire_report_records (
  report_id      TEXT PRIMARY KEY REFERENCES hire_reports(id),
  artist_id      TEXT NOT NULL,
  invoice_status TEXT NOT NULL DEFAULT 'not_invoiced' CHECK (invoice_status IN ('not_invoiced', 'invoiced', 'no_commission', 'disputed', 'superseded')),
  invoice_no     TEXT CHECK (invoice_no IS NULL OR length(invoice_no) BETWEEN 1 AND 40),
  invoiced_on    TEXT CHECK (invoiced_on IS NULL OR invoiced_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  payment_status TEXT NOT NULL DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'paid', 'not_due', 'refunded')),
  paid_on        TEXT CHECK (paid_on IS NULL OR paid_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  note           TEXT CHECK (note IS NULL OR length(note) <= 280),   -- private to the founder
  updated_at     TEXT NOT NULL,
  updated_by     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_report_records_artist ON hire_report_records(artist_id);
CREATE TRIGGER IF NOT EXISTS hire_report_records_no_delete BEFORE DELETE ON hire_report_records
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_report_records is kept until its retention period has ended'); END;

-- @@DDL-END

-- Rollback (separately approved, after a backup; drops only what this migration created):
-- DROP TABLE IF EXISTS hire_report_records;
-- DROP TABLE IF EXISTS hire_reports;
