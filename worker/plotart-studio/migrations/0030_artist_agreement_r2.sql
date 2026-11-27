-- PlotArt Studio · migration 0030 · Artist Agreement PA-GAA-2026-11-R2 and Image Licence PA-GPIL-2026-11-R2 for NEW
-- Gallery Artist invitations (development 27 Nov 2026). NOT APPLIED IN PRODUCTION.
-- Existing artists, Founding Artist agreements and historic acceptances are untouched: an artist with no row in
-- artist_agreement_versions keeps the agreement they were invited under. No trigger is placed on an existing table
-- (release checker rule): the version lock lives in a NEW table guarded by refusal-only triggers.

-- The agreement version fixed for an artist at invitation. Written only in the invitation batch, at the moment the
-- artist record is created; never changed or reassigned afterwards.
CREATE TABLE IF NOT EXISTS artist_agreement_versions (
  artist_id         TEXT PRIMARY KEY REFERENCES artists(id),
  agreement_version TEXT NOT NULL CHECK (agreement_version = 'PA-GAA-2026-11-R2'),
  licence_version   TEXT NOT NULL CHECK (licence_version = 'PA-GPIL-2026-11-R2'),
  assigned_by       TEXT NOT NULL,
  assigned_at       TEXT NOT NULL
);
-- A version can be fixed only for a non-Founding artist created in the same moment (the invitation) who has accepted
-- nothing yet, so an existing artist can never be moved onto R2 retrospectively.
CREATE TRIGGER IF NOT EXISTS artist_agreement_versions_at_invitation BEFORE INSERT ON artist_agreement_versions
WHEN NOT EXISTS (SELECT 1 FROM artists a WHERE a.id = NEW.artist_id AND a.created_at = NEW.assigned_at AND a.founding = 0)
  OR EXISTS (SELECT 1 FROM agreement_acceptances x WHERE x.artist_id = NEW.artist_id)
  OR EXISTS (SELECT 1 FROM gallery_agreement_acceptances y WHERE y.artist_id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'an agreement version is fixed only when the artist is invited'); END;
CREATE TRIGGER IF NOT EXISTS artist_agreement_versions_no_update BEFORE UPDATE ON artist_agreement_versions
BEGIN SELECT RAISE(ABORT, 'an artist''s agreement version never changes: a different agreement needs a new, expressly accepted text'); END;
CREATE TRIGGER IF NOT EXISTS artist_agreement_versions_no_delete BEFORE DELETE ON artist_agreement_versions
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'artist_agreement_versions is kept until its retention period has ended'); END;

-- The fixed texts (identical to plotart/legal and agreements/issued; fingerprints in agreements/issued/fingerprints.json).
INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GAA-2026-11-R2', 'gallery_artist_agreement', 'PlotArt Artist Agreement', 'fixed', '911acac839aed25f2bbeadc8f15678e41c82e65bc361500795238a44bf5c82ad', '3d660bdee95fb00c940ccdefce9233c9b7307e5b8fc365999209d6189aadbdca', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GPIL-2026-11-R2', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'fixed', '0732b2d78e04482f3be9e50ee85153891f6c98a39b0692a25bec6cc66fa3be88', '52710066590bac8d2f27ef87bd3f7f213765b6249dceca2ee7ebc85a36857833', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

-- Rollback (needs the founder's separate approval; acceptances already recorded against R2 make it inappropriate):
-- DROP TABLE artist_agreement_versions;
