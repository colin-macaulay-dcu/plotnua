/* PlotArt Studio · artist location (Phase C, development 25 Nov 2026). NOT DEPLOYED.
   One shared capability for every gallery, Art for Hire, the Living Gallery and later regional discovery:
   where the artist is BASED NOW (not birthplace, not nationality), and where they can deliver.
   - country: ISO 3166-1 alpha-2, any country (international artists are welcome).
   - county: one of the 32 counties of Ireland. Required when based in Ireland (IE, the 26 counties); optional for
     Northern Ireland (GB with one of its 6 counties, shown "Co. Antrim, Northern Ireland"); never for other countries.
   - town: optional town or city. Never an address: no digits (house numbers, Eircodes, postcodes), no street words.
   - delivery: local (the home county plus any chosen counties) and/or nationwide ("anywhere in Ireland" for an artist
     based on the island, otherwise anywhere in their country). The HOME county and the DELIVERY AREAS are kept apart.
   - public: nothing is public unless the artist ticks it (show_location; show_town; show_delivery). Delivery is shown
     publicly only once the founder has switched on public delivery (privacy notice update), whatever the artist ticked.
   Founder decisions still open (provisional defaults used here, each a one-line change): nationwide = island of Ireland;
   local delivery = chosen counties; Northern Ireland shown as "Co. X, Northern Ireland"; town public only when ticked. */
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

/* The artist's (or founder's) answer, validated. Returns the row to store; throws Bad with a plain message. */
export function validate(b) {
  if (!b || typeof b !== 'object') throw new Bad('Tell us where you’re based');
  const country = String(b.country || '').trim().toUpperCase();
  if (!COUNTRIES.includes(country)) throw new Bad('Choose the country where you’re based now');
  let county = b.county === undefined || b.county === null || b.county === '' ? null : String(b.county).trim();
  if (county !== null && !COUNTIES.includes(county)) throw new Bad('Choose a county from the list');
  if (country === 'IE' && (!county || !ROI_COUNTIES.includes(county))) throw new Bad('Choose the county where you’re based');
  if (country === 'GB' && county && !NI_COUNTIES.includes(county)) throw new Bad('That county is in Ireland: choose Ireland as your country');
  if (country !== 'IE' && country !== 'GB' && county) throw new Bad('A county is only needed when you’re based in Ireland or Northern Ireland');
  let town = b.town === undefined || b.town === null ? '' : String(b.town).replace(/\s+/g, ' ').trim();
  if (town && (town.length < 2 || town.length > 60 || /[<>]/.test(town) || ADDRESS.test(town)))
    throw new Bad('Give a town or city only, never your address');
  const delivers_local = bool(b.delivers_local), delivers_nationwide = bool(b.delivers_nationwide);
  let local = Array.isArray(b.local_counties) ? [...new Set(b.local_counties.map(String))] : [];
  if (local.some(c => !COUNTIES.includes(c))) throw new Bad('Choose delivery counties from the list');
  if (!delivers_local) local = [];
  if (delivers_local && !county && !local.length) throw new Bad('Choose the counties you can deliver to');
  local = COUNTIES.filter(c => local.includes(c) && c !== county);   // the home county is implied; stored once, in order
  const show_location = bool(b.show_location), show_town = town ? bool(b.show_town) && show_location : 0;
  return { country, county, town: town || null, delivers_local, local_counties: JSON.stringify(local), delivers_nationwide,
    show_location, show_town, show_delivery: bool(b.show_delivery) };
}

/* Save one artist's location (one row per artist; every change is in the audit log by the caller). */
export function saveStatement(env, artistId, row, by) {
  const at = now();
  return env.DB.prepare(`INSERT INTO artist_locations (artist_id, country, county, town, delivers_local, local_counties, delivers_nationwide,
      show_location, show_town, show_delivery, confirmed_at, confirmed_by, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(artist_id) DO UPDATE SET country=excluded.country, county=excluded.county, town=excluded.town, delivers_local=excluded.delivers_local,
      local_counties=excluded.local_counties, delivers_nationwide=excluded.delivers_nationwide, show_location=excluded.show_location,
      show_town=excluded.show_town, show_delivery=excluded.show_delivery, confirmed_at=excluded.confirmed_at, confirmed_by=excluded.confirmed_by,
      updated_at=excluded.updated_at`)
    .bind(artistId, row.country, row.county, row.town, row.delivers_local, row.local_counties, row.delivers_nationwide,
      row.show_location, row.show_town, row.show_delivery, at, by, at);
}

/* Where the home county reads on a public page. */
export function placeLine(loc, { withTown = true } = {}) {
  if (!loc) return null;
  const town = withTown && loc.show_town && loc.town ? loc.town + ', ' : '';
  if (loc.country === 'IE') return `${town}Co. ${loc.county}, Ireland`;
  if (loc.country === 'GB' && loc.county) return `${town}Co. ${loc.county}, Northern Ireland`;
  return `${town ? town : ''}${countryName(loc.country)}`;
}

/* The ONLY public view of a location (publisher, artist profile, Art for Hire). Never a private field. */
export function publicLocation(loc, { deliveryPublic = false } = {}) {
  if (!loc || !loc.show_location) return null;
  const out = { country: loc.country, county: loc.county || null, line: placeLine(loc) };
  if (loc.show_town && loc.town) out.town = loc.town;
  if (deliveryPublic && loc.show_delivery) {
    const local = JSON.parse(loc.local_counties || '[]');
    out.delivery = { nationwide: !!loc.delivers_nationwide, area: onIsland(loc) ? 'Ireland' : countryName(loc.country),
      counties: loc.delivers_local ? [...(loc.county ? [loc.county] : []), ...local] : [] };
  }
  return out;
}

/* Art for Hire's county filter: is this artist BASED in the county, or do they DELIVER there? (kept distinct) */
export function relation(pub, county) {
  if (!pub || !COUNTIES.includes(county)) return null;
  if (pub.county === county) return 'based';
  const d = pub.delivery;
  if (d && (d.counties.includes(county) || (d.nationwide && d.area === 'Ireland'))) return 'delivers';
  return null;
}
