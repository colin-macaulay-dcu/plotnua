-- Preserve existing version assignments and register the fixed texts.
ALTER TABLE artist_terms ADD COLUMN agreement_version TEXT CHECK (agreement_version IS NULL OR agreement_version = 'PA-GAA-2026-11-R2');
CREATE TRIGGER artist_terms_agreement_version_fixed BEFORE UPDATE OF agreement_version ON artist_terms
WHEN NEW.agreement_version IS NOT OLD.agreement_version
BEGIN SELECT RAISE(ABORT, 'The invitation agreement version cannot be reassigned'); END;

INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GAA-2026-11-R2', 'gallery_artist_agreement', 'PlotArt Artist Agreement', 'fixed', '911acac839aed25f2bbeadc8f15678e41c82e65bc361500795238a44bf5c82ad', '3d660bdee95fb00c940ccdefce9233c9b7307e5b8fc365999209d6189aadbdca', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GPIL-2026-11-R2', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'fixed', '0732b2d78e04482f3be9e50ee85153891f6c98a39b0692a25bec6cc66fa3be88', '52710066590bac8d2f27ef87bd3f7f213765b6249dceca2ee7ebc85a36857833', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));
