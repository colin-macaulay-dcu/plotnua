-- PlotArt Studio · migration 0015 · Opportunities shown publicly (development 16 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Changes ONE table, artist_opportunities, by adding three columns and nothing else. Every existing row and every existing
-- column is kept exactly as it is:
--   public_display      NULL = not decided yet, 1 = shown, 0 = kept private. EVERY existing answer starts NULL: answers given
--                       before this release were given under "Your answers are never published", so nothing an artist has
--                       already saved is shown until that artist confirms it in PlotArt Studio (one click).
--   public_decided_at   when the artist last chose (NULL while not decided).
--   public_notice       the version of the wording the artist was shown when they chose (e.g. PA-OPP-PUBLIC-2026-11).
-- What can ever be shown is ONLY the kinds of opportunity the artist selected (not "Online gallery only for now"), and only
-- while their gallery is published. County, transport, delivery coverage, the care box and the note are never shown.
-- No row is added or removed, no other table is touched, no trigger. No agreement, licence, gallery, enquiry, hire record,
-- image permission or the artists.open_for_commissions switch changes.
-- Preconditions before anyone runs it:
--   (1) migrations 0009 to 0014 have run;
--   (2) the privacy notice V16 (atlas-tools/privacy_v16_layer.py) is published first;
--   (3) the website release that accepts "open_to" in gallery exports is on main first (the publisher refuses unknown keys);
--   (4) the founder has approved this exact file (SHA-256);
--   (5) it runs through studio-d1-migration, which takes a Time Travel restore point and an encrypted export first and then
--       checks that only artist_opportunities changed. Claude never runs it outside that workflow.
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artist_opportunities ADD COLUMN public_display INTEGER CHECK (public_display IS NULL OR public_display IN (0, 1));
ALTER TABLE artist_opportunities ADD COLUMN public_decided_at TEXT CHECK (public_decided_at IS NULL OR length(public_decided_at) BETWEEN 20 AND 30);
ALTER TABLE artist_opportunities ADD COLUMN public_notice TEXT CHECK (public_notice IS NULL OR length(public_notice) BETWEEN 8 AND 40);

-- @@DDL-END

-- Rollback (separately approved, after a backup; removes only what this migration added; every earlier answer is untouched).
-- Older Studio code ignores these columns, so a Studio rollback alone does not need it:
-- ALTER TABLE artist_opportunities DROP COLUMN public_notice;
-- ALTER TABLE artist_opportunities DROP COLUMN public_decided_at;
-- ALTER TABLE artist_opportunities DROP COLUMN public_display;
