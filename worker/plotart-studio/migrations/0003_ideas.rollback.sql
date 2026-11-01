-- PlotNua Idea Board · ROLLBACK of migration 0003. Use ONLY with the founder's approval, and ONLY if the Idea Board is
-- being withdrawn. It DELETES every idea received (the tables hold nothing else). Export first (see the migration notes).
--   npx wrangler d1 execute plotart-studio --remote --file=migrations/0003_ideas.rollback.sql
-- Touches nothing else: no other table, column or row.
DROP INDEX IF EXISTS ideas_status_published;
DROP TABLE IF EXISTS ideas;
DROP TABLE IF EXISTS idea_intake_days;
