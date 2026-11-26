/* PlotArt · Mobile Gallery · provider data (public work-in-progress release, 3 Nov 2026).
   The single source for the provider cards, the gallery profile template and the "Find art for your home" filter.

   RULES (founder brief, 3 Nov 2026):
   - Every gallery here is a PROSPECTIVE provider. `status` stays "prospective" until a written agreement is recorded,
     with its evidence reference in `agreement.evidence`. Nothing renders as a confirmed partner while it is prospective.
   - Each fact carries `verified`: "public-source" = checked on a named public source on `checked`, not yet confirmed
     by the gallery; "gallery-confirmed" = confirmed in writing by the gallery (evidence reference required).
     Unverified fields stay null and render as "Service details to be confirmed".
   - No logos or images: `image` stays null until permission is recorded in the image-rights register (fail closed).
   - Services, prices, coverage and styles are NEVER inferred. The filter matches only on gallery-confirmed values.
   - No commercial terms are recorded or implied for any gallery.
   - PUBLIC FILE (founder release authorisation, 3 Nov 2026): this file is published, so it holds only public facts.
     Internal notes (outreach, commercial discussion, contact people) are kept out of it. A gallery appears here only
     once publishing its name has no open question; until then its position is an open invitation (INVITE_SLOTS).
     Prices are not shown until the gallery confirms them itself. */
window.MG_INVITE_SLOTS = 2;   // positions held open for galleries that may wish to join
window.MG_SERVICES = [
  { id: 'home-delivery', label: 'Artwork brought to your home' },
  { id: 'try-before-buy', label: 'Try before you buy' },
  { id: 'consultation', label: 'Personal art consultation' },
  { id: 'gallery-appointment', label: 'Private gallery appointment' }
];
window.MG_STYLES = ['Landscape', 'Abstract', 'Figurative', 'Contemporary painting', 'Sculpture', 'Original oil paintings'];
window.MG_BUDGETS = [
  { id: 'u500', label: 'Under €500' }, { id: '500-1500', label: '€500 to €1,500' },
  { id: '1500-5000', label: '€1,500 to €5,000' }, { id: '5000+', label: '€5,000 and above' }
];
window.MG_COUNTIES = ['Antrim', 'Armagh', 'Carlow', 'Cavan', 'Clare', 'Cork', 'Derry', 'Donegal', 'Down', 'Dublin', 'Fermanagh',
  'Galway', 'Kerry', 'Kildare', 'Kilkenny', 'Laois', 'Leitrim', 'Limerick', 'Longford', 'Louth', 'Mayo', 'Meath', 'Monaghan',
  'Offaly', 'Roscommon', 'Sligo', 'Tipperary', 'Tyrone', 'Waterford', 'Westmeath', 'Wexford', 'Wicklow'];

window.MG_PROVIDERS = [
  {
    id: 'artworld', name: 'Artworld.ie', status: 'prospective', profile: true,
    agreement: { participation: null, commercial: null, images: null, evidence: null },
    intro: { text: 'Founded by artist Cathal Spelman, Artworld offers original oil paintings, large wall art and commissioned work by artists in Ireland and abroad.',
      verified: 'public-source', source: 'Golden Pages business listing; artworld.ie (reviewed 23 Oct 2026)', checked: '2026-11-03' },
    location: { text: 'County Laois', short: 'Laois', counties: ['Laois'], verified: 'public-source', source: 'Golden Pages business listing', checked: '2026-11-03' },
    serviceArea: null,      // published sources describe different areas; to be confirmed by Artworld
    styles: { list: ['Original oil paintings', 'Large wall art', 'Commissions'], verified: 'public-source', source: 'Golden Pages business listing; artworld.ie', checked: '2026-11-03' },
    price: null,          // public prices are not repeated until the gallery confirms them
    services: { described: ['home-delivery'], confirmed: [],
      text: 'Artworld describes a home viewing service that lets you see paintings in your own space before buying.',
      verified: 'public-source', source: 'Golden Pages business listing; artworld.ie booking page (reviewed 23 Oct 2026)', checked: '2026-11-03' },
    appointments: { text: 'Viewings are booked through Artworld’s own booking form. How many paintings are brought, any charge, and travel arrangements are set by Artworld.', verified: 'public-source', source: 'artworld.ie booking page (reviewed 23 Oct 2026)', checked: '2026-10-23' },
    website: 'https://artworld.ie/', image: null
  },
  {
    id: 'doorway', name: 'The Doorway Gallery', status: 'prospective', profile: false,
    agreement: { participation: null, commercial: null, images: null, evidence: null },
    intro: { text: 'A Dublin gallery showing fine art, mainly painting, by Irish-born and international artists.', verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    location: { text: 'South Frederick Street, Dublin 2', short: 'Dublin', counties: ['Dublin'], verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    serviceArea: null, styles: null, price: null, services: null, appointments: null,
    website: null, image: null
  },
  {
    id: 'sol-art', name: 'Sol Art Gallery', status: 'prospective', profile: false,
    agreement: { participation: null, commercial: null, images: null, evidence: null },
    intro: { text: 'A contemporary art gallery in Dublin city centre.', verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    location: { text: 'D’Olier Street, Dublin 2', short: 'Dublin', counties: ['Dublin'], verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    serviceArea: null, styles: null, price: null, services: null, appointments: null,
    website: null, image: null
  },
  {
    id: 'kinsale', name: 'The Gallery Kinsale', status: 'prospective', profile: false,
    agreement: { participation: null, commercial: null, images: null, evidence: null },
    intro: { text: 'A commercial art gallery on Short Quay in Kinsale, County Cork.', verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    location: { text: 'Kinsale, County Cork', short: 'Kinsale', counties: ['Cork'], verified: 'public-source', source: 'Discover Ireland listing', checked: '2026-11-03' },
    serviceArea: null, styles: null, price: null, services: null, appointments: null,
    website: null, image: null
  }
];
