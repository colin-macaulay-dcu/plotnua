-- Preserve existing version assignments and register the fixed texts.
ALTER TABLE artist_terms ADD COLUMN agreement_version TEXT CHECK (agreement_version IS NULL OR agreement_version = 'PA-GAA-2026-11-R2');
CREATE TRIGGER artist_terms_agreement_version_fixed BEFORE UPDATE OF agreement_version ON artist_terms
WHEN NEW.agreement_version IS NOT OLD.agreement_version
BEGIN SELECT RAISE(ABORT, 'The invitation agreement version cannot be reassigned'); END;

INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GAA-2026-11-R2', 'gallery_artist_agreement', 'PlotArt Artist Agreement', 'fixed', '52a67d10ca3b9cd9343e9a962ca02fa2502256c1941b091a4eaedd8bd8110097', 'de57126faaabcb031702ea3af82f5d6af53e31fdebc882d367863081d14ff6a7', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at)
VALUES ('PA-GPIL-2026-11-R2', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'fixed', '22e1e5d55412a0e4a6d8a8f3a9e1dbc3967e0ffcf9cb2567ca21f0b11364d13c', '2047aef1da28b4857692db7d70f4da61635d9478a8f7039f835cbc9bd7cc7d6f', strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));
