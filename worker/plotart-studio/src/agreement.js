/* PlotArt Studio · Founding Artist Agreement and licence acceptance (development, 6 Nov 2026; NOT DEPLOYED).
   PA-FAA-2026-11 includes PA-GPIL-2026-11; a Founding Artist accepts both with ONE tick. The record of every acceptance
   is agreement_acceptances (append-only, migration 0005). artists.licence_version / licence_accepted_at stay as the
   pointer the publishing pipeline reads; they are updated only after the immutable rows have been written. */
import { AGREEMENTS } from './assets.js';

export const FAA = 'PA-FAA-2026-11', GPIL = 'PA-GPIL-2026-11';
/* Gallery Artist Agreement (Phase 2, 13 Nov 2026): for artists the founder invites on the standard 15% commission terms.
   Accepted with the same image licence, in one tick. Its acceptances are kept in gallery_agreement_acceptances (0012). */
export const GAA = 'PA-GAA-2026-11';
export const LEGACY_GPIL = 'PA-GPIL-2026-10-29';          // label only: no fixed full text existed; never re-attributed
/* Licence versions the publishing pipeline may carry (must match atlas-tools LICENCE_VERSIONS and
   validate-image-provenance.js ARTIST_LICENCE_VERSIONS: the website release adds PA-GPIL-2026-11 first). */
export const PUBLISHABLE_LICENCES = [LEGACY_GPIL, GPIL];

export const STATEMENT = {
  founding: `I have read and accept the PlotArt Founding Artist Agreement ${FAA}, including the Gallery Publication and Image Licence ${GPIL}.`,
  licence_only: `I have read and accept the PlotArt Gallery Publication and Image Licence ${GPIL}.`,
  gallery_artist: `I have read and accept the PlotArt Gallery Artist Agreement ${GAA}, including the Gallery Publication and Image Licence ${GPIL}.`,
};
/* Which programme an artist is on. Founding Artists keep PA-FAA (artists.founding = 1, unchanged). An artist is a Gallery
   Artist only when the founder invited them as one (an artist_terms row, track gallery_artist). Anyone else keeps today's
   licence-only behaviour: nobody is moved between programmes automatically. */
export const programmeOf = (artist, terms) => (artist.founding ? 'founding' : terms && terms.track === 'gallery_artist' ? 'gallery_artist' : 'licence_only');
export const PROGRAMME_NAME = { founding: 'Founding Artist Agreement', gallery_artist: 'Gallery Artist Agreement', licence_only: 'Gallery Publication and Image Licence' };
/* Where an acceptance of each document is recorded: the Gallery Artist Agreement in its own table (0012), all others as before. */
export const acceptanceTable = id => (id.startsWith('PA-GAA-') ? 'gallery_agreement_acceptances' : 'agreement_acceptances');
/* The documents an artist must hold for a full submission: a Founding Artist the agreement and the licence it includes;
   any other artist the licence alone. */
export const required = (artist, terms = null) => ({ founding: [FAA, GPIL], gallery_artist: [GAA, GPIL], licence_only: [GPIL] })[programmeOf(artist, terms)];
export const statementFor = (artist, terms = null) => STATEMENT[programmeOf(artist, terms)];
export const doc = id => AGREEMENTS[id] || null;
export { dublinDate, dublinToday, dublinMidnightUtc, addDays, foundingYear, foundingAt } from './founding.js';
