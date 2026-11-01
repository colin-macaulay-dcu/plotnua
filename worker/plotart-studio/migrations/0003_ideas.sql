-- PlotNua Idea Board · migration 0003 · ideas (founder approval of Phase 1 build, 1 Nov 2026). NOT APPLIED.
-- Apply ONCE to the production D1 database ONLY with the founder's explicit approval of this exact file, AFTER a backup
-- (see IDEA-BOARD-MIGRATION-0003.md), through the governed "PlotArt Studio · D1 migration" workflow
-- (.github/workflows/studio-d1-migration.yml: Time Travel restore point + encrypted full export, then the migration,
-- then a check that only the declared tables changed). Declared tables: ideas, idea_intake_days.
-- Additive only: two new tables and one index. No existing table, column or row changes.
-- Phase 1 stores no name, e-mail, telephone, IP address or cookie: an idea, an optional area and an optional county.
CREATE TABLE ideas (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL CHECK (length(text) BETWEEN 8 AND 160),
  public_text TEXT CHECK (public_text IS NULL OR length(public_text) BETWEEN 8 AND 160),
  area TEXT CHECK (area IS NULL OR area IN ('Space', 'Garden', 'Art', 'Energy', 'Frontage', 'Neighbourhood', 'Income')),
  county TEXT CHECK (county IS NULL OR length(county) BETWEEN 3 AND 20),
  show_county INTEGER NOT NULL DEFAULT 0 CHECK (show_county IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'approved', 'not_approved', 'removed')),
  became_discovery TEXT CHECK (became_discovery IS NULL OR became_discovery GLOB 'discovery-[a-z0-9]*.html'),
  edited INTEGER NOT NULL DEFAULT 0 CHECK (edited IN (0, 1)),
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by TEXT,
  published_at TEXT,
  removed_at TEXT,
  CHECK (show_county = 0 OR county IS NOT NULL)
);
CREATE INDEX ideas_status_published ON ideas(status, published_at);
-- Daily intake counter (the daily cap). One row per UTC day; holds a number only.
CREATE TABLE idea_intake_days (
  day TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0
);
