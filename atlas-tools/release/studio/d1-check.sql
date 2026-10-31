-- PlotArt Studio · database check for migrations: three result sets, read by d1-fingerprint.mjs (never printed).
SELECT (SELECT COUNT(*) FROM artists) artists, (SELECT COUNT(*) FROM artworks) artworks, (SELECT COUNT(*) FROM images) images, (SELECT COUNT(*) FROM submissions) submissions, (SELECT COUNT(*) FROM versions) versions, (SELECT COUNT(*) FROM publish_queue) publish_queue, (SELECT COUNT(*) FROM enquiries) enquiries, (SELECT COUNT(*) FROM audit) audit;
SELECT * FROM artists ORDER BY id;
SELECT position, artist_id, reserved, note FROM gallery_positions ORDER BY position;
