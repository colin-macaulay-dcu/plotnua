/* PlotArt Studio · Opportunities & delivery: shared rules (development 13 Nov 2026). NOT DEPLOYED.
   Pure functions only, used by the Worker (opportunities.js) and by the local preview. An artist's answers are an
   EXPRESSION OF INTEREST: they never enrol anyone in a programme, change an agreement, grant an image permission, offer a
   work for hire or send anything to anyone. Programme-specific consent (Art for Hire terms, image permissions, the
   Founding Artist agreement) stays where it is. */
import { COUNTIES, clean } from './ideas-rules.js';
export { COUNTIES };

// Order shown to the artist. "online_only" is exclusive of every other choice.
export const INTERESTS = {
  exhibitions: 'Physical gallery exhibitions',
  living_gallery: 'Living Gallery — displaying work in someone’s home',
  art_for_hire: 'Art for Hire — renting work',
  mobile_gallery: 'Mobile Gallery — home viewings through participating galleries',   // as on plotart/mobile-gallery/ (13 Nov 2026 wording review)
  venues: 'Hotel and workplace displays',
  commissions: 'Commissions',
  talks: 'Artist talks or events',
  online_only: 'Online gallery only for now',
};
// Short labels for the founder's table and filters.
export const INTEREST_SHORT = { exhibitions: 'Exhibitions', living_gallery: 'Living Gallery', art_for_hire: 'Art for Hire', mobile_gallery: 'Mobile Gallery',
  venues: 'Hotels and workplaces', commissions: 'Commissions', talks: 'Talks and events', online_only: 'Online only for now' };
export const TRANSPORT = {
  deliver: 'I can deliver and collect',
  courier: 'I could arrange a courier or art transporter',
  need_help: 'I would need help arranging transport',
  depends: 'It depends on the opportunity',
};
export const TRANSPORT_SHORT = { deliver: 'Delivers', courier: 'Arranges courier', need_help: 'Needs help', depends: 'Depends' };
// "depends" stands alone; someone who can arrange a courier does not also need help arranging transport.
export const TRANSPORT_CLASH = { depends: ['deliver', 'courier', 'need_help'], need_help: ['courier', 'depends'], courier: ['need_help', 'depends'], deliver: ['depends'] };
// The delivery question applies only when the artist (or their courier) would move the work.
export const asksCoverage = transport => transport.includes('deliver') || transport.includes('courier');

// The four provinces of the island of Ireland (Ulster has nine counties: six in Northern Ireland, three in the State).
export const PROVINCES = {
  Leinster: ['Carlow', 'Dublin', 'Kildare', 'Kilkenny', 'Laois', 'Longford', 'Louth', 'Meath', 'Offaly', 'Westmeath', 'Wexford', 'Wicklow'],
  Munster: ['Clare', 'Cork', 'Kerry', 'Limerick', 'Tipperary', 'Waterford'],
  Connacht: ['Galway', 'Leitrim', 'Mayo', 'Roscommon', 'Sligo'],
  Ulster: ['Antrim', 'Armagh', 'Cavan', 'Derry', 'Donegal', 'Down', 'Fermanagh', 'Monaghan', 'Tyrone'],
};
export const COVERAGE = { counties: 'Selected counties', anywhere: 'Anywhere on the island of Ireland', ask: 'Ask me about each opportunity' };
export const NOTE_MAX = 280;

const list = v => Array.isArray(v) ? v : null;
const uniq = a => [...new Set(a)];

/* Checks an artist's answers. Returns { prefs } with the normalised record, or { error } in plain words.
   Nothing is guessed or filled in: what is not answered is stored as not answered. */
export function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return { error: 'Nothing to save.' };
  const extra = Object.keys(body).filter(k => !['interests', 'artwork_county', 'transport', 'coverage', 'note'].includes(k));
  if (extra.length) return { error: 'Unexpected fields: ' + extra.join(', ') };
  const interests = list(body.interests);
  if (!interests || !interests.length) return { error: 'Choose at least one option in “What would you be interested in exploring?”, or choose “Online gallery only for now”.' };
  if (interests.some(k => typeof k !== 'string' || !INTERESTS[k]) || uniq(interests).length !== interests.length) return { error: 'Please choose from the options shown.' };
  const online = interests.includes('online_only');
  if (online && interests.length > 1) return { error: '“Online gallery only for now” can’t be combined with other options.' };

  const county = body.artwork_county == null || body.artwork_county === '' ? null : body.artwork_county;
  if (county !== null && !COUNTIES.includes(county)) return { error: 'Choose the county where your artwork is based from the list.' };

  const transport = body.transport == null ? [] : list(body.transport);
  if (!transport || transport.some(k => typeof k !== 'string' || !TRANSPORT[k]) || uniq(transport).length !== transport.length) return { error: 'Please choose transport options from the list.' };
  for (const k of transport) if ((TRANSPORT_CLASH[k] || []).some(o => transport.includes(o))) return { error: `“${TRANSPORT[k]}” can’t be combined with “${TRANSPORT[TRANSPORT_CLASH[k].find(o => transport.includes(o))]}”.` };
  if (online && transport.length) return { error: 'Transport isn’t needed while you’ve chosen “Online gallery only for now”.' };

  let mode = null, counties = [];
  const c = body.coverage;
  if (c != null) {
    if (typeof c !== 'object' || Array.isArray(c) || !COVERAGE[c.mode]) return { error: 'Please choose where you could deliver and collect from the options shown.' };
    if (!asksCoverage(transport)) return { error: 'Where you could deliver and collect applies only if you can deliver or arrange a courier.' };
    mode = c.mode;
    const cs = c.counties == null ? [] : list(c.counties);
    if (!cs || cs.some(x => !COUNTIES.includes(x)) || uniq(cs).length !== cs.length) return { error: 'Choose counties from the list.' };
    if (mode === 'counties' && !cs.length) return { error: 'Choose at least one county, “Anywhere on the island of Ireland” or “Ask me about each opportunity”.' };
    if (mode !== 'counties' && cs.length) return { error: `“${COVERAGE[mode]}” can’t be combined with individual counties.` };
    counties = COUNTIES.filter(x => cs.includes(x));   // stored in a fixed order
  }

  let note = body.note == null ? '' : body.note;
  if (typeof note !== 'string') return { error: 'The note must be text.' };
  note = clean(note);
  if (note.length > NOTE_MAX) return { error: `Please keep the note to ${NOTE_MAX} characters.` };

  return { prefs: { interests: Object.keys(INTERESTS).filter(k => interests.includes(k)), artwork_county: county,
    transport: Object.keys(TRANSPORT).filter(k => transport.includes(k)), coverage_mode: mode, coverage_counties: counties, note: note || null } };
}

/* Founder filter: does this saved record say the artist could reach a venue in the given county? */
export function covers(p, county) {
  return Boolean(p && (p.coverage_mode === 'anywhere' || (p.coverage_mode === 'counties' && p.coverage_counties.includes(county))));
}
