-- PlotArt Studio · migration 0013 · install the Gallery Artist Agreement text PA-GAA-2026-11 (development 13 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database. RUN ONLY AFTER THE FOUNDER HAS APPROVED THE FINAL TEXT.
-- Adds ONE row to gallery_agreement_documents (created by 0012): the identifier, title and the SHA-256 fingerprints of the
-- exact page and PDF PlotArt Studio serves (agreements/issued/fingerprints.json). From the moment it runs, an artist on the
-- Gallery Artist terms can read and accept PA-GAA-2026-11 in Studio; until then Studio shows them nothing to accept and
-- their first publication stays blocked (the existing safeguard).
-- If the founder changes the text before approving it, agreements/build.cjs is run again and this file is regenerated
-- with the new fingerprints, so the file approved always matches the text approved. No existing row or table changes.
-- Preconditions: (1) 0012 has run; (2) the founder has approved the final PA-GAA text and this exact file (SHA-256);
-- (3) privacy notice V14 (Gallery Artist commission records) is live; (4) it runs through studio-d1-migration.
-- Run it ONCE: the primary key refuses a second run.

INSERT INTO gallery_agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES
 ('PA-GAA-2026-11', 'gallery_artist_agreement', 'PlotArt Gallery Artist Agreement', 'fixed',
  '60bab19a949add256b53162b2819c610985e02c878eadd45f274a1e1fb39d038', 'a7f943f391674f8df1f430be4ae575c531c6752c75c44f186950934389f51781',
  strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));
