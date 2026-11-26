/* PlotArt Studio · artist location (Phase C, development 25 Nov 2026). NOT DEPLOYED.
   One shared capability for every gallery, Art for Hire, the Living Gallery and later regional discovery:
   where the artist is BASED NOW (not birthplace, not nationality), and where they can deliver.
   - country: ISO 3166-1 alpha-2, any country (international artists are welcome).
   - county: one of the 32 counties of Ireland. Required when based in Ireland (IE, the 26 counties); optional for
     Northern Ireland (GB with one of its 6 counties, shown "Co. Antrim, Northern Ireland"); never for other countries.
   - town: optional town or city. Never an address: no digits (house numbers, Eircodes, postcodes), no street words.
   - delivery coverage is SEPARATE from location (its own table and its own validator, founder direction 25 Nov 2026):
     chosen counties, the Republic of Ireland (26), Northern Ireland (6), the whole island (32), or (for an artist based
     outside Ireland) anywhere in their own country. An artist based anywhere may cover any Irish county.
   - public: nothing is public unless the artist ticks it (show_location; show_town; show_delivery). Delivery coverage is
     shown publicly only once the founder has switched on public delivery (privacy notice update), whatever was ticked.
   - Art for Hire's county filter finds artists BASED in the county AND artists based anywhere whose coverage includes it,
     labelled separately; nobody willing to supply that county is excluded. A residential address is never stored. */
import { Bad, COUNTIES, now } from './lib.js';

export const NI_COUNTIES = ['Antrim', 'Armagh', 'Derry', 'Down', 'Fermanagh', 'Tyrone'];
export const ROI_COUNTIES = COUNTIES.filter(c => !NI_COUNTIES.includes(c));
export const PROVINCES = {
  Connacht: ['Galway', 'Leitrim', 'Mayo', 'Roscommon', 'Sligo'],
  Leinster: ['Carlow', 'Dublin', 'Kildare', 'Kilkenny', 'Laois', 'Longford', 'Louth', 'Meath', 'Offaly', 'Westmeath', 'Wexford', 'Wicklow'],
  Munster: ['Clare', 'Cork', 'Kerry', 'Limerick', 'Tipperary', 'Waterford'],
  Ulster: ['Antrim', 'Armagh', 'Cavan', 'Derry', 'Donegal', 'Down', 'Fermanagh', 'Monaghan', 'Tyrone'],
};
// ISO 3166-1 alpha-2 (officially assigned codes)
export const COUNTRIES = ('AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ '
  + 'CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE '
  + 'GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP '
  + 'KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF '
  + 'NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN '
  + 'SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA '
  + 'ZM ZW').split(' ');
const NAMES = new Intl.DisplayNames(['en-IE'], { type: 'region' });
export const countryName = c => (c === 'GB' ? 'United Kingdom' : NAMES.of(c));
export const onIsland = loc => !!loc && (loc.country === 'IE' || (loc.country === 'GB' && NI_COUNTIES.includes(loc.county)));

const bool = v => (v === true || v === 1 || v === '1' || v === 'on' ? 1 : 0);
const ADDRESS = /\d|\b(street|st\.|road|rd\.?|avenue|ave\.?|lane|ln\.?|drive|apartment|apt\.?|flat|unit|house|no\.)\b/i;
export const SCOPES = ['none', 'counties', 'republic', 'northern_ireland', 'island', 'country'];

/* WHERE THE ARTIST IS BASED. Returns the row to store; throws Bad with a plain message. */
export function validateLocation(b) {
  if (!b || typeof b !== 'object') throw new Bad('Tell us where you’re based');
  const country = String(b.country || '').trim().toUpperCase();
  if (!COUNTRIES.includes(country)) throw new Bad('Choose the country where you’re based now');
  const county = b.county === undefined || b.county === null || b.county === '' ? null : String(b.county).trim();
  if (county !== null && !COUNTIES.includes(county)) throw new Bad('Choose a county from the list');
  if (country === 'IE' && (!county || !ROI_COUNTIES.includes(county))) throw new Bad('Choose the county where you’re based');
  if (country === 'GB' && county && !NI_COUNTIES.includes(county)) throw new Bad('That county is in Ireland: choose Ireland as your country');
  if (country !== 'IE' && country !== 'GB' && county) throw new Bad('A county is only needed when you’re based in Ireland or Northern Ireland');
  const town = b.town === undefined || b.town === null ? '' : String(b.town).replace(/\s+/g, ' ').trim();
  if (town && (town.length < 2 || town.length > 60 || /[<>]/.test(town) || ADDRESS.test(town)))
    throw new Bad('Give a town or city only, never your address');
  const show_location = bool(b.show_location);
  return { country, county, town: town || null, show_location, show_town: town ? bool(b.show_town) && show_location : 0 };
}

/* WHERE THE ARTIST CAN DELIVER (general delivery to buyers and hirers), kept apart from where they are based.
   loc: their location row (for "my country"); cur: their current delivery row; methodsOn: migration 0027 has run.
   Report 36: how the work travels (methods) is a separate answer from where. With no delivery area the artist says which
   of "No delivery: the buyer or hirer collects" (collection) or "Delivery by arrangement" (arrangement) applies, so
   unanswered, no delivery and by arrangement are three different answers. Public display of delivery areas can only ever
   be withdrawn here, never switched on: an earlier "show once available" tick is never treated as consent, and switching
   public delivery on in future needs a fresh, separately recorded consent (see publicDelivery). */
export const METHODS = { personal: 'I deliver personally', courier: 'Standard courier', specialist: 'Specialist art transport' };
export const NO_AREA = { collection: 'No delivery: the buyer or hirer collects', arrangement: 'Delivery by arrangement, agreed with each buyer or hirer' };
export const METHOD_SHORT = { personal: 'personal delivery', courier: 'standard courier', specialist: 'specialist art transport' };
export function validateDelivery(b, loc, { cur = null, methodsOn = false } = {}) {
  if (!b || typeof b !== 'object' || Array.isArray(b)) throw new Bad('Tell us where you can deliver');
  const extra = Object.keys(b).filter(k => !['scope', 'counties', 'show_delivery', ...(methodsOn ? ['methods'] : [])].includes(k));
  if (extra.length) throw new Bad('Unexpected fields: ' + extra.join(', '));
  // Report 35: no answer is not "I don't deliver". The artist must choose; nothing is assumed.
  if (b.scope === undefined || b.scope === null || b.scope === '') throw new Bad('Choose where you can deliver, or “No delivery” or “By arrangement”');
  const scope = String(b.scope);
  if (!SCOPES.includes(scope)) throw new Bad('Choose where you can deliver');
  let counties = Array.isArray(b.counties) ? [...new Set(b.counties.map(String))] : [];
  if (counties.some(c => !COUNTIES.includes(c))) throw new Bad('Choose delivery counties from the list');
  if (scope !== 'counties') counties = [];
  if (scope === 'counties' && !counties.length) throw new Bad('Choose the counties you can deliver to');
  if (scope === 'country' && (!loc || onIsland(loc))) throw new Bad('For Ireland, choose the Republic, Northern Ireland or the whole island');
  let methods;
  if (methodsOn) {
    const m = b.methods;
    if (!Array.isArray(m) || !m.length || m.some(x => typeof x !== 'string') || new Set(m).size !== m.length) throw new Bad(scope === 'none' ? 'Choose “No delivery” or “By arrangement”' : 'Choose how the work would travel');
    if (scope === 'none') { if (m.length !== 1 || !NO_AREA[m[0]]) throw new Bad('Choose “No delivery” or “By arrangement”'); methods = m[0]; }
    else { if (m.some(x => !METHODS[x])) throw new Bad('Choose how the work would travel from the list'); methods = Object.keys(METHODS).filter(k => m.includes(k)).join(','); }
  }
  // public display: only a withdrawal is accepted (false); otherwise the stored choice is kept exactly as it is
  if (b.show_delivery !== undefined && b.show_delivery !== false) throw new Bad('Showing delivery areas publicly isn’t available. If PlotArt offers it in future, you’ll be asked separately.');
  const show = scope === 'none' || b.show_delivery === false ? 0 : (cur && cur.show_delivery ? 1 : 0);
  return { scope, counties: JSON.stringify(COUNTIES.filter(c => counties.includes(c))), show_delivery: show, ...(methodsOn ? { methods } : {}) };
}

const upsert = (env, table, cols, artistId, row, by) => {
  const at = now(), all = [...cols, 'confirmed_at', 'confirmed_by', 'updated_at'];
  return env.DB.prepare(`INSERT INTO ${table} (artist_id, ${all.join(', ')}) VALUES (?, ${all.map(() => '?').join(', ')})
    ON CONFLICT(artist_id) DO UPDATE SET ${all.map(c => `${c}=excluded.${c}`).join(', ')}`).bind(artistId, ...cols.map(c => row[c]), at, by, at);
};
export const saveLocation = (env, artistId, row, by) => upsert(env, 'artist_locations', ['country', 'county', 'town', 'show_location', 'show_town'], artistId, row, by);
export const saveDelivery = (env, artistId, row, by) => upsert(env, 'artist_delivery', ['scope', 'counties', 'show_delivery', ...('methods' in row ? ['methods'] : [])], artistId, row, by);

/* Where the home county reads on a public page. */
export function placeLine(loc) {
  if (!loc) return null;
  const town = loc.show_town && loc.town ? loc.town + ', ' : '';
  if (loc.country === 'IE') return `${town}Co. ${loc.county}, Ireland`;
  if (loc.country === 'GB' && loc.county) return `${town}Co. ${loc.county}, Northern Ireland`;
  return `${town}${countryName(loc.country)}`;
}
/* The ONLY public view of a location: never an address, the town only when ticked, nothing when not shown. */
export function publicLocation(loc) {
  if (!loc || !loc.show_location) return null;
  return { country: loc.country, county: loc.county || null, line: placeLine(loc), ...(loc.show_town && loc.town ? { town: loc.town } : {}) };
}

/* The Irish counties a coverage includes. */
export function covered(del, loc) {
  if (!del) return [];
  switch (del.scope) {
    case 'counties': return JSON.parse(del.counties || '[]');
    case 'republic': return ROI_COUNTIES.slice();
    case 'northern_ireland': return NI_COUNTIES.slice();
    case 'island': return COUNTIES.slice();
    default: return [];
  }
}
const SCOPE_LINE = { republic: 'Delivers anywhere in the Republic of Ireland', northern_ireland: 'Delivers anywhere in Northern Ireland',
  island: 'Delivers anywhere on the island of Ireland' };
export function deliveryLine(del, loc) {
  if (!del || del.scope === 'none') return null;
  if (SCOPE_LINE[del.scope]) return SCOPE_LINE[del.scope];
  if (del.scope === 'country') return `Delivers anywhere in ${countryName(loc.country)}`;
  const cs = covered(del, loc);
  return `Delivers to ${cs.map(c => 'Co. ' + c).join(', ')}`;
}
/* General delivery as the artist and founder see it (never public): where, how, and a plain line for each. */
export function generalView(d) {
  if (!d) return null;
  const line = d.scope === 'none' ? (NO_AREA[d.methods] || 'No delivery or by arrangement (answered before these were separate)') : deliveryLine(d, d);
  return { scope: d.scope, counties: covered(d, d), country: d.country || null, line, methods: d.methods ?? null,
    how: d.scope === 'none' ? null : d.methods === null ? 'how not yet given (answered before this question)' : methodsLine(d) };
}
/* How the work travels (founder and artist only; never public). */
export function methodsLine(del) {
  if (!del || !del.methods) return null;
  if (NO_AREA[del.methods]) return NO_AREA[del.methods];
  return 'By ' + del.methods.split(',').map(k => METHOD_SHORT[k]).join(', ');
}
/* The ONLY public view of delivery coverage: only when the artist ticks it AND the founder has switched public delivery on. */
export function publicDelivery(del, loc, { deliveryPublic = false, consentNotice = null } = {}) {
  // Report 36: switching public delivery on (DELIVERY_PUBLIC) is never enough. It also needs the artist's fresh consent
  // recorded under the notice in force at the time (del.public_consent_notice === consentNotice). No such record can
  // exist yet (there is no column for it until a future, separately approved change), so this is always null today,
  // and an earlier "show once PlotArt switches this on" tick (show_delivery) is never treated as that consent.
  if (!deliveryPublic || !consentNotice || !del || !del.show_delivery || del.scope === 'none' || del.public_consent_notice !== consentNotice) return null;
  return { scope: del.scope, counties: covered(del, loc), line: deliveryLine(del, loc) };
}

/* Art for Hire's county filter, for one artist: BASED here (home county, location public), or DELIVERS here (coverage
   public and includes the county, wherever the artist is based), or null. Being based elsewhere never excludes. */
export function relation(pubLoc, pubDel, county) {
  if (!COUNTIES.includes(county)) return null;
  if (pubLoc && pubLoc.county === county) return 'based';
  if (pubDel && pubDel.counties.includes(county)) return 'delivers';
  return null;
}
