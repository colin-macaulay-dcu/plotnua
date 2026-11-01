-- PlotNua Idea Board · ROLLBACK of migration 0003. Use ONLY with the founder's approval, and ONLY if the Idea Board is
-- being withdrawn. It DELETES every idea received (the tables hold nothing else). Export first (see the migration notes).
-- Run through the same governed workflow (studio-d1-migration.yml), declared tables: ideas, idea_intake_days.
-- Touches nothing else: no other table, column or row. Dropping the table also drops its index.
DROP TABLE IF EXISTS ideas;
DROP TABLE IF EXISTS idea_intake_days;
