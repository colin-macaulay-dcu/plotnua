-- PlotArt Studio · migration 0027 · Delivery and transport (Report 35/36, development 26 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Adds TWO optional columns to two existing tables and nothing else:
--   artist_delivery.methods         how a sold or hired work travels (general delivery to buyers and hirers).
--   artist_opportunities.placement_area   whether temporary placements follow the artist's general delivery area.
-- Every existing row starts with NULL in both, which means "not answered yet" / "answered before 0027, not yet confirmed".
-- No row is added, removed or otherwise changed; no existing column, answer, consent, agreement, gallery, position,
-- artwork, enquiry, payment or image record changes; there is no trigger and no index.
--
-- methods: ONE canonical value from a fixed list, so the database itself refuses an unknown, duplicated or re-ordered
-- method (no JSON to validate):
--   with a delivery area (scope counties / republic / northern_ireland / island / country):
--     any non-empty combination of personal, courier, specialist, always written in that order:
--     'personal' 'courier' 'specialist' 'personal,courier' 'personal,specialist' 'courier,specialist'
--     'personal,courier,specialist'
--   with no delivery area (scope none), exactly one of:
--     'collection'   No delivery: the buyer or hirer collects
--     'arrangement'  Delivery by arrangement, agreed individually with each buyer or hirer
-- so "not answered" (no row, or a NULL from before 0027), "no delivery" and "by arrangement" are three different answers.
-- The second CHECK ties the two together only once methods is answered: a row from before 0027 (NULL) is valid as it is,
-- and the live Studio before the new version is deployed never writes methods, so it can keep saving exactly as today.
--
-- placement_area:
--   'general'  the artist explicitly chose "Same as my general delivery": temporary placements follow their Profile
--              delivery area, and later Profile changes apply. Their own placement area (coverage_mode, coverage_counties)
--              is kept untouched underneath, so choosing "Different area" again restores it exactly.
--   'own'      their own placement area (selected counties, anywhere on the island, or "ask me about each opportunity").
--   NULL       answered before 0027 and not yet confirmed: treated exactly as today (their own area). Never inferred
--              from two answers that happen to match.
-- Standard courier and specialist art transport for placements are two separate keys in the existing transport list
-- (courier, specialist): no column is needed for that, and an earlier "courier or art transporter" answer keeps its stored
-- value until the artist confirms (placement_area NULL marks it as answered before the split).
--
-- Preconditions before anyone runs it:
--   (1) migrations up to 0026 have run (production carries them since 26 Nov 2026);
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration, which takes a Time Travel restore point and an encrypted full export first
--       and then checks that only these two tables changed, row counts and contents unchanged. Changing an existing
--       table is never automatic: the founder approves the run in GitHub (studio-database).
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- Compatibility: the live Studio (before the new version) names its columns when it writes these tables, so it neither
-- reads nor writes the new columns; the new Studio hides the new questions until both columns exist. Deploying the
-- Studio before or after this migration is safe either way.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artist_delivery ADD COLUMN methods TEXT
  CHECK (methods IS NULL OR methods IN ('personal', 'courier', 'specialist', 'personal,courier', 'personal,specialist', 'courier,specialist', 'personal,courier,specialist', 'collection', 'arrangement'))
  CHECK (methods IS NULL OR ((scope = 'none') = (methods IN ('collection', 'arrangement'))));
ALTER TABLE artist_opportunities ADD COLUMN placement_area TEXT CHECK (placement_area IS NULL OR placement_area IN ('general', 'own'));
