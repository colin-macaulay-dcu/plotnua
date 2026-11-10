-- PlotArt Studio · migration 0006 · return one failed publication to the publishing queue
-- Founder instruction, 10 Nov 2026. Runs only through the studio-d1-migration workflow, after the founder approves it in
-- GitHub (environment studio-database), with both backups taken first.
-- Effect: Studio queue record qlho7xswxng (Rasher Mark Kavanagh, version 1, approved changes) changes from 'failed' to
-- 'ready'. No other row or table changes. Artist, artwork, image, agreement and gallery-order records are not touched.
-- Running it again changes nothing (the WHERE clause requires status 'failed').
-- Publication is a separate step, authorised separately: the next PlotArt content publishing run picks up 'ready' items.
UPDATE publish_queue SET status='ready' WHERE id='qlho7xswxng' AND status='failed';
