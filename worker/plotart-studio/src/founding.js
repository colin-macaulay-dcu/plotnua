/* PlotArt Studio · founding year and Founding Enquiries in Irish time (development, 6 Nov 2026; NOT DEPLOYED).
   Shared by the Studio (index.js) and the enquiry relay (enquiry.js); no other imports, so the relay stays small. */
/* ---------------------------------------------------------------- Irish time
   The founding year (agreement 2.4) runs from the day the gallery is first publicly published and ends at the end of
   the day before the first anniversary of that date, Irish time. 29 February: the anniversary in a common year is taken
   as 1 March, so the year ends at the end of 28 February (a full twelve months; the reading more favourable to the
   artist, agreement 1.2). Dates are calendar dates in Europe/Dublin, so summer time never moves a boundary. */
const DUB = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit' });
export const dublinDate = iso => DUB.format(new Date(iso));            // 'YYYY-MM-DD'
const isLeap = y => (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
export function addDays(ymd, n) { const d = new Date(ymd + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
/* The UTC instant at which a Dublin calendar date begins (handles GMT and IST). */
export function dublinMidnightUtc(ymd) {
  let t = Date.parse(ymd + 'T00:00:00Z');
  for (let i = 0; i < 3; i++) {
    const parts = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Dublin', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      .formatToParts(new Date(t)).map(p => [p.type, p.value]));
    const local = Date.parse(`${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:00Z`);
    const want = Date.parse(ymd + 'T00:00:00Z');
    if (local === want) return new Date(t).toISOString();
    t += want - local;
  }
  return new Date(t).toISOString();
}
export function foundingYear(firstPublishedIso) {
  if (!firstPublishedIso) return null;
  const start = dublinDate(firstPublishedIso);
  const [y, m, d] = start.split('-').map(Number);
  const anniversary = m === 2 && d === 29 && !isLeap(y + 1) ? `${y + 1}-03-01` : `${y + 1}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
  const end = addDays(anniversary, -1);
  return { start, end, ends_at: dublinMidnightUtc(anniversary) };   // ends_at: the first instant AFTER the founding year
}
/* Is an enquiry introduced at `iso` a Founding Enquiry (agreement 5.1, read with 5.6)? Before first publication no
   commission-bearing terms can exist, so such an enquiry is treated as founding too. Non-founding artists: never. */
export function foundingAt(artist, iso) {
  if (!artist.founding) return { founding: 0, year_end: null };
  const fy = foundingYear(artist.first_published_at);
  if (!fy) return { founding: 1, year_end: null };
  return { founding: dublinDate(iso) <= fy.end ? 1 : 0, year_end: fy.end };
}
export const dublinToday = () => dublinDate(new Date().toISOString());
