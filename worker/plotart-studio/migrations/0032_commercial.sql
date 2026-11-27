-- PlotArt Studio · migration 0032 · Commercial leads and placements (founder approval in principle, 27 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Adds SIX new tables and their indexes. No existing table, row, column, consent, agreement, artwork or artist record
-- changes: artists and artworks are only REFERENCED (never written).
--
-- Studio becomes the single record of commercial work (business rentals under PA-BHR-2026-11, purchases and project
-- enquiries from businesses): one lead per business enquiry, and everything that follows it:
--   commercial_leads       the business, its contact, where the lead came from, its stage and next action
--   commercial_events      the timeline: notes, emails in and out (captured from Gmail), stage changes, decisions
--   commercial_selections  artworks proposed for the lead, each with the artist's own approval (or refusal) recorded
--   commercial_documents   proposals, the PlotArt fee agreement, the artist-business hire agreement and invoices
--   commercial_payments    payments received against an invoice
--   commercial_placements  a work placed with the business: dates (six months), status, sale notice, replacement, renewal
--
-- Amounts are stored in euro cents. A business rental selection stores the work's price when proposed and the monthly
-- charge at 4% split 3% (artist) / 1% (PlotArt), computed by the Studio with the same rounding as the website table.
-- General hire (PA-AFH) and any introducer / referral share are NOT modelled: neither is active.
--
-- Personal data: business contact details (name, role, work email and phone) of the person who asked, and the email text
-- the founder chose to capture. Retention: retain_until = last activity + 24 months; for a lead with an issued invoice,
-- the end of the sixth year after the invoice (Revenue record-keeping). The Studio's daily run deletes expired leads
-- (events, selections, documents, payments and placements go with them: ON DELETE CASCADE).
--
-- Safe to run again: CREATE ... IF NOT EXISTS only. Preconditions: migrations up to 0031 have run (0030 Artist Agreement R2, 0031 open Founding Artist numbers); the founder has approved
-- this exact file (SHA-256); it runs through studio-d1-migration (Time Travel restore point and encrypted full backup first).
-- Compatibility: the live Studio never reads these tables; the new Studio uses them only once they exist.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS commercial_leads (
  id TEXT PRIMARY KEY,
  reference TEXT NOT NULL UNIQUE CHECK (reference GLOB 'PA-CL-[0-9][0-9][0-9][0-9][0-9][0-9]-*'),
  business TEXT NOT NULL CHECK (length(business) BETWEEN 2 AND 160),
  sector TEXT CHECK (sector IS NULL OR sector IN ('hotel', 'office', 'hospitality', 'retail', 'healthcare', 'property', 'interiors', 'production', 'other')),
  contact_name TEXT CHECK (contact_name IS NULL OR length(contact_name) BETWEEN 2 AND 120),
  contact_role TEXT CHECK (contact_role IS NULL OR length(contact_role) <= 120),
  contact_email TEXT CHECK (contact_email IS NULL OR (length(contact_email) BETWEEN 5 AND 200 AND contact_email LIKE '%_@_%.__%')),
  contact_phone TEXT CHECK (contact_phone IS NULL OR length(contact_phone) <= 40),
  website TEXT CHECK (website IS NULL OR length(website) <= 300),
  location TEXT CHECK (location IS NULL OR length(location) <= 120),
  source TEXT NOT NULL CHECK (source IN ('outreach_reply', 'website_form', 'email', 'phone', 'introduction', 'other')),
  interest TEXT NOT NULL DEFAULT 'unsure' CHECK (interest IN ('rental', 'purchase', 'project', 'unsure')),
  stage TEXT NOT NULL DEFAULT 'new' CHECK (stage IN ('new', 'in_conversation', 'selecting', 'artist_approval', 'proposal_sent',
    'agreed', 'placed', 'renewal_due', 'won', 'not_now', 'lost')),
  next_action TEXT CHECK (next_action IS NULL OR length(next_action) <= 200),
  next_action_on TEXT CHECK (next_action_on IS NULL OR next_action_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  gmail_thread_id TEXT UNIQUE CHECK (gmail_thread_id IS NULL OR length(gmail_thread_id) <= 64),
  summary TEXT CHECK (summary IS NULL OR length(summary) <= 600),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_activity_at TEXT NOT NULL,
  retain_until TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS commercial_leads_stage ON commercial_leads(stage, next_action_on);
CREATE INDEX IF NOT EXISTS commercial_leads_email ON commercial_leads(contact_email);
CREATE INDEX IF NOT EXISTS commercial_leads_retain ON commercial_leads(retain_until);

CREATE TABLE IF NOT EXISTS commercial_events (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES commercial_leads(id) ON DELETE CASCADE,
  at TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('note', 'email_in', 'email_out', 'form', 'stage', 'selection', 'artist_approval',
    'document', 'payment', 'placement', 'renewal')),
  summary TEXT NOT NULL CHECK (length(summary) BETWEEN 1 AND 300),
  body TEXT CHECK (body IS NULL OR length(body) <= 8000),
  gmail_message_id TEXT UNIQUE CHECK (gmail_message_id IS NULL OR length(gmail_message_id) <= 64),
  actor TEXT NOT NULL CHECK (length(actor) BETWEEN 3 AND 200)
);
CREATE INDEX IF NOT EXISTS commercial_events_lead ON commercial_events(lead_id, at);

CREATE TABLE IF NOT EXISTS commercial_selections (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES commercial_leads(id) ON DELETE CASCADE,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  artwork_id TEXT REFERENCES artworks(id) ON DELETE SET NULL,
  artwork_title TEXT NOT NULL CHECK (length(artwork_title) BETWEEN 1 AND 200),
  arrangement TEXT NOT NULL CHECK (arrangement IN ('rental', 'purchase', 'project')),
  price_cents INTEGER CHECK (price_cents IS NULL OR price_cents > 0),
  monthly_cents INTEGER CHECK (monthly_cents IS NULL OR monthly_cents > 0),
  artist_monthly_cents INTEGER CHECK (artist_monthly_cents IS NULL OR artist_monthly_cents > 0),
  plotart_monthly_cents INTEGER CHECK (plotart_monthly_cents IS NULL OR plotart_monthly_cents >= 0),
  status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'artist_asked', 'artist_approved', 'artist_declined',
    'client_chosen', 'client_declined', 'withdrawn')),
  artist_decision_at TEXT,
  artist_decision_evidence TEXT CHECK (artist_decision_evidence IS NULL OR length(artist_decision_evidence) <= 300),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (arrangement <> 'rental' OR (price_cents IS NOT NULL AND monthly_cents IS NOT NULL AND artist_monthly_cents IS NOT NULL AND plotart_monthly_cents IS NOT NULL)),
  CHECK (status NOT IN ('artist_approved', 'artist_declined', 'client_chosen') OR (artist_decision_at IS NOT NULL AND artist_decision_evidence IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS commercial_selections_lead ON commercial_selections(lead_id);
CREATE INDEX IF NOT EXISTS commercial_selections_artist ON commercial_selections(artist_id, status);
-- An artwork can't be chosen by a business unless its artist approved it.
CREATE TRIGGER IF NOT EXISTS commercial_selections_approved_first BEFORE UPDATE OF status ON commercial_selections
  WHEN NEW.status = 'client_chosen' AND OLD.status <> 'artist_approved'
  BEGIN SELECT RAISE(ABORT, 'commercial_selections: the artist must approve a work before the business can choose it'); END;

CREATE TABLE IF NOT EXISTS commercial_documents (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES commercial_leads(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('proposal', 'fee_agreement', 'hire_agreement', 'invoice', 'credit_note')),
  number TEXT NOT NULL CHECK (length(number) BETWEEN 3 AND 40),
  status TEXT NOT NULL CHECK (status IN ('draft', 'sent', 'signed', 'accepted', 'declined', 'issued', 'paid', 'void')),
  issued_on TEXT CHECK (issued_on IS NULL OR issued_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  period_from TEXT, period_to TEXT,
  placement_id TEXT REFERENCES commercial_placements(id) ON DELETE SET NULL,   -- a monthly PlotArt fee invoice: the placement it is for
  amount_cents INTEGER CHECK (amount_cents IS NULL OR amount_cents >= 0),
  vat_cents INTEGER CHECK (vat_cents IS NULL OR vat_cents >= 0),
  link TEXT CHECK (link IS NULL OR length(link) <= 500),
  note TEXT CHECK (note IS NULL OR length(note) <= 300),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (kind, number)
);
CREATE INDEX IF NOT EXISTS commercial_documents_lead ON commercial_documents(lead_id, kind);

CREATE TABLE IF NOT EXISTS commercial_payments (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES commercial_documents(id) ON DELETE CASCADE,
  received_on TEXT NOT NULL CHECK (received_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
  method TEXT NOT NULL CHECK (method IN ('bank_transfer', 'card', 'other')),
  reference TEXT CHECK (reference IS NULL OR length(reference) <= 80),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS commercial_placements (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES commercial_leads(id) ON DELETE CASCADE,
  selection_id TEXT NOT NULL REFERENCES commercial_selections(id),
  location TEXT CHECK (location IS NULL OR length(location) <= 160),
  start_on TEXT NOT NULL CHECK (start_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  end_on TEXT NOT NULL CHECK (end_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'sale_notice', 'sold', 'replaced', 'ended', 'renewed')),
  sale_notice_on TEXT,
  replaced_by TEXT REFERENCES commercial_placements(id),
  renewal_of TEXT REFERENCES commercial_placements(id),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (end_on > start_on)
);
CREATE INDEX IF NOT EXISTS commercial_placements_lead ON commercial_placements(lead_id);
CREATE INDEX IF NOT EXISTS commercial_placements_end ON commercial_placements(status, end_on);
-- A work is placed only after the artist approved it and the business chose it.
CREATE TRIGGER IF NOT EXISTS commercial_placements_chosen BEFORE INSERT ON commercial_placements
  WHEN NOT EXISTS (SELECT 1 FROM commercial_selections s WHERE s.id = NEW.selection_id AND s.lead_id = NEW.lead_id AND s.status = 'client_chosen')
  BEGIN SELECT RAISE(ABORT, 'commercial_placements: only a work the artist approved and the business chose can be placed'); END;
-- @@DDL-END

-- Rollback (separately approved, after a backup; drops only what this migration created):
-- DROP TABLE IF EXISTS commercial_placements; DROP TABLE IF EXISTS commercial_payments; DROP TABLE IF EXISTS commercial_documents;
-- DROP TABLE IF EXISTS commercial_selections; DROP TABLE IF EXISTS commercial_events; DROP TABLE IF EXISTS commercial_leads;
