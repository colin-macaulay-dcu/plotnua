/* PlotNua · The Borrowed Garden noticeboard: shared rules (MVP, founder decision 4 Nov 2026). NOT DEPLOYED.
   Used by the public intake Worker (garden.js), the founder's Garden tab in PlotArt Studio (index.js) and the
   enquiry relay (enquiry.js), so a listing the founder edits is held to exactly the same rules as one a visitor sends.

   A listing never carries a name, an e-mail address, a telephone number, a website or a precise address. The contact
   e-mail is collected privately (for the founder, and for the relay once it is switched on) and is never published. */
import { COUNTIES, clean, rules } from './ideas-rules.js';
export { COUNTIES, clean };

export const KINDS = { have: 'I have space', want: 'I want space' };
export const SPACE_TYPES = {
  raised_beds: 'Raised beds',
  vegetable_patch: 'A vegetable patch',
  lawn: 'Part of a lawn',
  greenhouse: 'A greenhouse or polytunnel',
  orchard: 'Fruit trees or an orchard corner',
  flexible: 'Open to suggestions',
};
export const AVAILABILITY = {
  now: 'Available now',
  this_season: 'This growing season',
  next_season: 'Next growing season',
  flexible: 'Flexible',
};
export const LISTING_DAYS = 90;            // an approved listing expires 90 days after approval unless renewed
export const DESC_MIN = 20, DESC_MAX = 400, AREA_MAX = 40;

// A precise address, in any of the forms people actually type.
const EIRCODE = /\b[ACDEFHKNPRTVWXY][0-9]{2}[0-9W]?\s?[0-9ACDEFHKNPRTVWXY]{4}\b/i;
const HOUSE_NO = /\b\d+[a-z]?\s+[a-z]+(?:\s+[a-z]+)?\s+(?:road|rd|street|st|avenue|ave|park|drive|lane|close|crescent|grove|court|way|terrace|place|view|heights|gardens|square)\b/i;

export function textProblem(text, { min = DESC_MIN, max = DESC_MAX, what = 'description' } = {}) {
  if (text.length < min) return `Please write a little more: at least ${min} characters.`;
  if (text.length > max) return `Please keep the ${what} to ${max} characters.`;
  if (rules.email.test(text)) return 'Please leave out e-mail addresses: listings never show contact details.';
  if (rules.link.test(text)) return 'Please leave out website addresses.';
  if (rules.phone.test(text)) return 'Please leave out telephone numbers: listings never show contact details.';
  if (rules.markup.test(text)) return 'Please leave out the < and > characters.';
  if (EIRCODE.test(text) || HOUSE_NO.test(text)) return 'Please leave out your address or Eircode: give a general area only.';
  return null;
}

export function areaProblem(area) {
  if (area.length < 2) return 'Please give a general area, such as a town or neighbourhood.';
  if (area.length > AREA_MAX) return `Please keep the area to ${AREA_MAX} characters.`;
  if (/\d/.test(area)) return 'Please give a general area only: no house numbers or Eircodes.';
  return textProblem(area, { min: 2, max: AREA_MAX, what: 'area' });
}

// Checks a listing's public fields. Returns null, or the problem to show.
export function listingProblem(l) {
  if (!KINDS[l.kind]) return 'Please choose whether you have space or want space.';
  if (!COUNTIES.includes(l.county)) return 'Please choose a county from the list.';
  if (!SPACE_TYPES[l.space_type]) return 'Please choose a type of space from the list.';
  if (!AVAILABILITY[l.availability]) return 'Please choose when from the list.';
  return areaProblem(l.area) || textProblem(l.description);
}

// The consent sentence the page shows next to the tick-box (also in atlas-tools/build-garden-board.py).
export const CONSENT = 'I am over 18. I agree that PlotNua may show this listing on The Borrowed Garden noticeboard, without my name or contact details, and keep my e-mail address privately so PlotNua can contact me about it.';
export const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
