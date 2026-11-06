/* PlotArt Studio · Founding Artist Agreement and licence acceptance (development, 6 Nov 2026; NOT DEPLOYED).
   PA-FAA-2026-11 includes PA-GPIL-2026-11; a Founding Artist accepts both with ONE tick. The record of every acceptance
   is agreement_acceptances (append-only, migration 0005). artists.licence_version / licence_accepted_at stay as the
   pointer the publishing pipeline reads; they are updated only after the immutable rows have been written. */
import { AGREEMENTS } from './assets.js';

export const FAA = 'PA-FAA-2026-11', GPIL = 'PA-GPIL-2026-11';
export const LEGACY_GPIL = 'PA-GPIL-2026-10-29';          // label only: no fixed full text existed; never re-attributed
/* Licence versions the publishing pipeline may carry (must match atlas-tools LICENCE_VERSIONS and
   validate-image-provenance.js ARTIST_LICENCE_VERSIONS: the website release adds PA-GPIL-2026-11 first). */
export const PUBLISHABLE_LICENCES = [LEGACY_GPIL, GPIL];

export const STATEMENT = {
  founding: `I have read and accept the PlotArt Founding Artist Agreement ${FAA}, including the Gallery Publication and Image Licence ${GPIL}.`,
  licence_only: `I have read and accept the PlotArt Gallery Publication and Image Licence ${GPIL}.`,
};
/* The documents an artist must hold for a full submission: a Founding Artist the agreement and the licence it includes;
   any other artist the licence alone. */
export const required = artist => (artist.founding ? [FAA, GPIL] : [GPIL]);
export const statementFor = artist => (artist.founding ? STATEMENT.founding : STATEMENT.licence_only);
export const doc = id => AGREEMENTS[id] || null;
export { dublinDate, dublinToday, dublinMidnightUtc, addDays, foundingYear, foundingAt } from './founding.js';
