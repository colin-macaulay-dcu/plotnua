/* PLOTNUA TRUST — FIRST-PARTY EVIDENCE SWEEP ENGINE v1
   ============================================================================
   ATLAS INTELLIGENCE INFRASTRUCTURE. Not part of the customer-facing site and
   never rendered to a homeowner. Reads ONLY a supplier's own pages.

   NO Google API. NO ratings. NO review counts. NO Trustpilot. NO scoring.
   NO blended reputation. NO Airtable write. Google reputation stays DISABLED
   pending the EEA use question.

   WHAT THIS IS. A pure core: HTML in, typed adjudication-ready evidence out.
   Fetching is deliberately NOT in here — see fetchAdapter() at the bottom for
   why, and how the caller supplies pages.

   THE PILOT'S LESSON, ENCODED. Finding a Google link is easy and nearly
   worthless. Every false positive in the manual pilot was a link that LOOKED
   like a business identity and was not: a GAA club, a region, a street pin, a
   hand-drawn map, a name search. So an identifier is TYPED before it is
   allowed to mean anything, and only three types can ever support an identity.
   ========================================================================== */
'use strict';

/* --- typed vocabularies -------------------------------------------------- */
const ID_TYPES = ['PROFILE_LINK','PLACE_ID','CID_BUSINESS','CID_ADDRESS',
                  'CID_REGION','SHORTLINK','NAME_QUERY','MYMAPS','NONE'];
const FETCH_STATES = ['READ','BLOCKED','NOT_FOUND_PAGE','THIN_PAGE','ERROR'];
const VERDICTS = ['CONFIRMED','PARTIAL','AMBIGUOUS','UNRESOLVED','BLOCKED'];

/* Only these can carry an identity. Everything else is provenance at best. */
const BUSINESS_TYPES = ['PROFILE_LINK','PLACE_ID','CID_BUSINESS'];

/* Place IDs are storable indefinitely under Google's published guidance, but a
   business can move, merge or close, so the record carries a revalidation
   target rather than pretending the ID is eternally true. */
const PLACE_ID_REVALIDATE_MONTHS = 12;

/* --- small helpers ------------------------------------------------------- */
const uniq = a => [...new Set(a.filter(Boolean))];
const EIRCODE = /\b[A-Z]\d{2}\s?[A-Z0-9]{4}\b/g;
const UKPOST  = /\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b/g;
const normPhone = p => String(p || '').replace(/[^\d]/g, '')
  .replace(/^00353/, '353').replace(/^0(?=\d)/, '353');
const host = u => { try { return new URL(u).hostname.replace(/^www\./, '').toLowerCase(); }
                    catch (e) { return ''; } };

/* A label is a REGION when it names a place rather than a business. Kept as an
   explicit list plus two shapes; nothing here is inferred from "sounds like". */
const REGION_WORDS = /^(northern ireland|ireland|republic of ireland|united kingdom|england|scotland|wales|county\b|co\.?\s)/i;

/* Google supplies the place name two ways and BOTH must be read: the !2s
   parameter, and the /maps/place/<name>/ path segment it emits when !2s is
   absent. Reading only !2s let Berko's "Northern Ireland, UK" fall through
   as a business identity — the name was in the path the whole time. */
function safeDecode(s) {
  const t = String(s).replace(/\+/g, ' ');
  try { return decodeURIComponent(t); } catch (e) { return t; }
}
function urlPlaceLabel(u) {
  const m = String(u).match(/\/maps\/place\/([^/@?#]+)/);
  return m ? safeDecode(m[1]) : '';
}

/* One Google listing is written several ways: 0x<mapcell>:0x<cid>, 0x0:0x<cid>
   with the map cell zeroed, and decimal in ?cid=. The BUSINESS is the second
   half; the first is a map cell. Identity comparisons therefore run on the
   business half, so one listing counts once — and two genuinely different
   business halves stay two. */
function cidKey(v) {
  const s = String(v || '');
  const m = s.match(/^0x[0-9a-f]+:0x([0-9a-f]+)$/i);
  if (m) return BigInt('0x' + m[1]).toString();
  return s;
}
const idKey = i => (i.type === 'CID_BUSINESS' ? cidKey(i.value) : i.value);

function typeCidByLabel(label) {
  const s = String(label || '').trim();
  if (!s) return 'CID_BUSINESS';                 // unlabelled cid= link
  if (REGION_WORDS.test(s)) return 'CID_REGION';
  // An address pin: starts with a unit/number, or carries a postcode and no
  // business-looking head. "unit 9, 50 Moira Rd, Aldergrove, Crumlin BT29 4JL"
  const hasPost = new RegExp(UKPOST.source).test(s) || new RegExp(EIRCODE.source).test(s);
  if (/^(unit|apt|no\.?|suite|\d+[a-z]?)[\s,]/i.test(s) && hasPost) return 'CID_ADDRESS';
  return 'CID_BUSINESS';
}

/* --- 1 · EXTRACT + TYPE -------------------------------------------------- */
function extract(html, pageUrl) {
  const H = String(html || '');
  const out = [];
  const push = (type, value, label, raw) =>
    out.push({ type, value, label: label || null, source: raw.slice(0, 220), page: pageUrl || null });

  /* MYMAPS first — a custom map is never a business listing. */
  for (const m of H.matchAll(/https?:\/\/[^"'\s)]*maps\/d\/[^"'\s)]*mid=([A-Za-z0-9_-]+)/g))
    push('MYMAPS', m[1], null, m[0]);

  /* PROFILE_LINK — the supplier publishing its own review profile. Strongest. */
  for (const m of H.matchAll(/https?:\/\/search\.google\.com\/local\/(?:reviews|writereview)\?placeid=(ChIJ[A-Za-z0-9_-]+)/g))
    push('PROFILE_LINK', m[1], null, m[0]);
  /* A Google reviews widget the supplier installed on its own site. */
  for (const m of H.matchAll(/data-id="(ChIJ[A-Za-z0-9_-]+)"[^>]*data-provider="google"|data-provider="google"[^>]*data-id="(ChIJ[A-Za-z0-9_-]+)"/g))
    push('PROFILE_LINK', m[1] || m[2], null, m[0]);

  /* PLACE_ID — an explicit place id in a link or attribute. */
  for (const m of H.matchAll(/(?:query_place_id|placeid|place_id)=(ChIJ[A-Za-z0-9_-]+)/g))
    push('PLACE_ID', m[1], null, m[0]);
  for (const m of H.matchAll(/\b(ChIJ[A-Za-z0-9_-]{15,})\b/g))
    push('PLACE_ID', m[1], null, m[0]);

  /* CID — hex pair in an embed/URL, typed by the label that travels with it.
     Scanned PER URL so the /maps/place/<name>/ path is available as a label
     when !2s is absent; !2s still wins when both are present. */
  const seenCid = new Set();
  for (const u of (H.match(/https?:\/\/[^"'\s<>]+/g) || [])) {
    const pathLabel = urlPlaceLabel(u);
    for (const m of u.matchAll(/1s(0x[0-9a-f]+(?::|%3A)0x[0-9a-f]{6,})(?:[^"'\s]*?!2s([^!"'&]+))?/gi)) {
      const value = m[1].replace(/%3A/i, ':');
      const label = m[2] ? safeDecode(m[2]) : pathLabel;
      seenCid.add(value);
      push(typeCidByLabel(label), value, label || null, m[0]);
    }
  }
  /* Any CID not carried by a recognisable URL — typed by !2s alone, as before. */
  for (const m of H.matchAll(/1s(0x[0-9a-f]+(?::|%3A)0x[0-9a-f]{6,})(?:[^"'\s]*?!2s([^!"'&]+))?/gi)) {
    const value = m[1].replace(/%3A/i, ':');
    if (seenCid.has(value)) continue;
    const label = m[2] ? safeDecode(m[2]) : '';
    push(typeCidByLabel(label), value, label || null, m[0]);
  }
  for (const m of H.matchAll(/[?&]cid=(\d{6,})/g)) push('CID_BUSINESS', m[1], null, m[0]);

  /* SHORTLINK — real, but opaque without a Google request we will not make. */
  for (const m of H.matchAll(/https?:\/\/(?:maps\.app\.goo\.gl|goo\.gl\/maps|g\.page)\/[A-Za-z0-9_-]+/g))
    push('SHORTLINK', m[0], null, m[0]);

  /* NAME_QUERY — a search or coordinate embed. Identifies no business. */
  for (const m of H.matchAll(/https?:\/\/[^"'\s)]*maps[^"'\s)]*[?&]q=([^&"'\s]+)[^"'\s)]*output=embed/g))
    push('NAME_QUERY', decodeURIComponent(m[1].replace(/\+/g, ' ')), null, m[0]);
  for (const m of H.matchAll(/https?:\/\/[^"'\s)]*maps\/search\/[^"'\s)]*query=([^&"'\s]+)/g))
    if (!/query_place_id/.test(m[0])) push('NAME_QUERY', decodeURIComponent(m[1].replace(/\+/g, ' ')), null, m[0]);
  /* A coordinate-only embed carries !2z rather than !2s: a point, not a place. */
  for (const m of H.matchAll(/maps\/embed\?pb=[^"'\s]*!2z[^"'\s]*/g))
    if (!/!2s/.test(m[0])) push('NAME_QUERY', 'coordinate-only embed', null, m[0]);

  /* first-party facts */
  const text = H.replace(/<[^>]+>/g, ' ');
  const eircodes = uniq((text.match(EIRCODE) || []));
  const postcodes = uniq((text.match(UKPOST) || [])).filter(p => !eircodes.includes(p));
  const phones = uniq([...H.matchAll(/href=["']tel:([^"']+)["']/g)].map(m => m[1].trim()));

  return { identifiers: dedupe(out), eircodes, postcodes, phones };
}
function dedupe(list) {
  const seen = new Set(); const out = [];
  for (const i of list) { const k = i.type + '|' + i.value; if (!seen.has(k)) { seen.add(k); out.push(i); } }
  return out;
}

/* --- 2 · VERDICT --------------------------------------------------------- */
/* org: { organisationId, name, canonicalDomain }
   pages: [{ url, fetchState, html }]                                        */
function assess(org, pages, now) {
  const at = (now || new Date()).toISOString().slice(0, 10);
  const states = pages.map(p => p.fetchState);
  const ev = { identifiers: [], eircodes: [], postcodes: [], phones: [] };

  for (const p of pages) {
    if (p.fetchState === 'BLOCKED' || p.fetchState === 'ERROR') continue;
    if (!p.html) continue;
    const e = extract(p.html, p.url);
    ev.identifiers.push(...e.identifiers);
    ev.eircodes.push(...e.eircodes); ev.postcodes.push(...e.postcodes); ev.phones.push(...e.phones);
  }
  ev.identifiers = dedupe(ev.identifiers);
  ev.eircodes = uniq(ev.eircodes); ev.postcodes = uniq(ev.postcodes); ev.phones = uniq(ev.phones);

  const exceptions = [];
  const business = ev.identifiers.filter(i => BUSINESS_TYPES.includes(i.type));
  const nonBusiness = ev.identifiers.filter(i => !BUSINESS_TYPES.includes(i.type));
  /* Counted on canonical keys: the same listing in two URL forms is one. */
  const distinct = uniq(business.map(idKey));

  /* BLOCKED is a fact about the fetch, never about the supplier. It is only
     reported when NOTHING was readable — a blocked contact page beside a read
     homepage is a partial read, not a blocked organisation. */
  const anyRead = pages.some(p => p.html && p.fetchState !== 'BLOCKED' && p.fetchState !== 'ERROR');
  if (!anyRead) {
    exceptions.push({ code: 'BLOCKED_SITE', detail: states.join(',') });
    return record(org, ev, 'BLOCKED', [], exceptions, states, at);
  }

  const axes = [];
  if (business.some(b => b.type === 'PROFILE_LINK')) axes.push('publisher-link');
  const dom = String(org.canonicalDomain || '').replace(/^www\./, '').toLowerCase();
  if (dom && pages.some(p => host(p.url) === dom)) axes.push('domain-match');
  if (ev.eircodes.length || ev.postcodes.length) axes.push('address-evidence');
  if (ev.phones.length) axes.push('phone-evidence');

  let verdict;
  if (distinct.length > 1) {
    verdict = 'AMBIGUOUS';
    exceptions.push({ code: 'MULTIPLE_LISTINGS', detail: uniq(business.map(b => b.value)).join(' | ') });
  } else if (distinct.length === 1) {
    if (axes.includes('publisher-link')) verdict = 'CONFIRMED';
    else if (axes.length >= 2) verdict = 'CONFIRMED';
    else { verdict = 'PARTIAL'; exceptions.push({ code: 'WEAK_SINGLE_AXIS', detail: axes.join(',') || 'none' }); }
  } else {
    verdict = 'UNRESOLVED';
    if (nonBusiness.length)
      exceptions.push({ code: 'NON_BUSINESS_IDENTIFIER',
        detail: uniq(nonBusiness.map(i => i.type + (i.label ? ':' + i.label : ''))).join(' | ') });
  }

  /* Labels the supplier's own embed exposes, compared with the Atlas name.
     Observable first-party only — nothing is fetched to check this. */
  for (const b of business) {
    if (b.label && !looseNameMatch(b.label, org.name))
      exceptions.push({ code: 'NAME_MISMATCH', detail: org.name + ' -> ' + b.label });
  }
  if (ev.eircodes.length + ev.postcodes.length > 1)
    exceptions.push({ code: 'MULTIPLE_PREMISES', detail: [...ev.eircodes, ...ev.postcodes].join(', ') });
  if (states.includes('BLOCKED') || states.includes('ERROR'))
    exceptions.push({ code: 'PARTIAL_FETCH', detail: states.join(',') });
  if (states.includes('NOT_FOUND_PAGE'))
    exceptions.push({ code: 'PAGE_NOT_FOUND', detail: states.join(',') });

  return record(org, ev, verdict, axes, exceptions, states, at);
}
function looseNameMatch(a, b) {
  const n = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const A = n(a), B = n(b);
  if (!A || !B) return true;
  if (A.includes(B) || B.includes(A)) return true;
  const at = new Set(A.split(' ')), bt = B.split(' ');
  const hits = bt.filter(t => t.length > 3 && at.has(t)).length;
  return hits >= Math.min(2, bt.filter(t => t.length > 3).length);
}

function record(org, ev, verdict, axes, exceptions, states, at) {
  const business = ev.identifiers.filter(i => BUSINESS_TYPES.includes(i.type));
  const placeId = (business.find(b => b.type === 'PROFILE_LINK' || b.type === 'PLACE_ID') || {}).value || null;
  const cid = (business.find(b => b.type === 'CID_BUSINESS') || {}).value || null;
  const due = new Date(at); due.setMonth(due.getMonth() + PLACE_ID_REVALIDATE_MONTHS);
  return {
    organisationId: org.organisationId, name: org.name,
    canonicalDomain: org.canonicalDomain,
    fetchStates: states,
    identity: {
      verdict, basis: axes,
      placeId, cid,
      identifierTypes: uniq(ev.identifiers.map(i => i.type)),
      identifiers: ev.identifiers,
      placeIdCheckedAt: placeId ? at : null,
      placeIdRefreshDueAt: placeId ? due.toISOString().slice(0, 10) : null,
    },
    firstParty: { eircodes: ev.eircodes, postcodes: ev.postcodes, phones: ev.phones, checkedAt: at },
    reputation: { enabled: false, blockedBy: 'EEA-PENDING-75180745',
                  rating: null, ratingScale: null, reviewCount: null, refreshDueAt: null },
    exceptions,
  };
}

/* --- 3 · CROSS-ORGANISATION COLLISIONS ----------------------------------- */
/* One organisation's record cannot see another's, so sharing is a second pass.
   This is what caught two Atlas organisations behind one Google business. */
function collide(records) {
  const byId = new Map(), byPhone = new Map();
  for (const r of records) {
    for (const v of uniq([r.identity.placeId, r.identity.cid ? cidKey(r.identity.cid) : null]))
      if (v) (byId.get(v) || byId.set(v, []).get(v)).push(r.organisationId);
    for (const p of r.firstParty.phones.map(normPhone))
      if (p) (byPhone.get(p) || byPhone.set(p, []).get(p)).push(r.organisationId);
  }
  const add = (map, code) => {
    for (const [val, orgs] of map) {
      const o = uniq(orgs);
      if (o.length < 2) continue;
      for (const r of records) if (o.includes(r.organisationId)) {
        r.exceptions.push({ code, detail: val + ' shared with ' + o.filter(x => x !== r.organisationId).join(', ') });
        if (r.identity.verdict === 'CONFIRMED') r.identity.verdict = 'AMBIGUOUS';
      }
    }
  };
  add(byId, 'SHARED_IDENTIFIER'); add(byPhone, 'SHARED_PHONE');
  return records;
}

/* --- 4 · OUTPUTS --------------------------------------------------------- */
/* DISPOSITION. "Not CONFIRMED" is not a reason to spend a person's attention.
   UNRESOLVED is a valid TERMINAL machine state: absence of evidence is a
   finding, not a question, and UNKNOWN is never FALSE. A person is asked only
   where a real adjudication exists — conflicting listings, one business behind
   two Atlas organisations, or a name/premises decision about an identity the
   engine actually HOLDS. Nothing here changes what the engine will CONFIRM;
   this decides who reads the result, not what the result is. */
const HUMAN_ALWAYS = ['MULTIPLE_LISTINGS', 'SHARED_IDENTIFIER', 'SHARED_PHONE',
                      'GOVERNANCE_CONFLICT'];
/* Only meaningful against a held identity. A name that differs from Atlas, or
   several premises, decides nothing when no listing was accepted. */
const HUMAN_IF_IDENTITY = ['NAME_MISMATCH', 'MULTIPLE_PREMISES'];
/* The fetch, not the supplier. Retry before troubling anyone. */
const RETRY_CODES = ['BLOCKED_SITE', 'PAGE_NOT_FOUND', 'PARTIAL_FETCH',
                     'TRUNCATED_ACQUISITION'];

function dispose(r) {
  const codes = r.exceptions.map(e => e.code);
  const held = !!(r.identity.placeId || r.identity.cid);
  if (codes.some(c => HUMAN_ALWAYS.includes(c))) return 'HUMAN_REVIEW';
  if (held && codes.some(c => HUMAN_IF_IDENTITY.includes(c))) return 'HUMAN_REVIEW';
  if (codes.some(c => RETRY_CODES.includes(c))) return 'RETRY_LATER';
  return 'AUTO_TERMINAL';
}

function queue(records) {
  return records.filter(r => r.exceptions.length || r.identity.verdict !== 'CONFIRMED')
    .map(r => ({ organisationId: r.organisationId, name: r.name,
                 verdict: r.identity.verdict,
                 disposition: dispose(r),
                 reasons: r.exceptions.map(e => e.code),
                 detail: r.exceptions }));
}
/* What a human is actually asked to look at. */
function humanQueue(records) {
  return queue(records).filter(q => q.disposition === 'HUMAN_REVIEW');
}

/* --- 5 · FETCH ADAPTER (documented, deliberately not implemented) --------- */
/* V1 ships no fetcher on purpose. Measured during the pilot: a plain HTML
   fetch STRIPS the attributes this engine depends on — the Garden Rooms Place
   ID lives in a data-id attribute that never survived. So pages must come from
   something that returns real DOM HTML, and the caller supplies them:
     assess(org, [{url, fetchState:'READ', html}], new Date())
   Classify fetchState at the fetch boundary: a Cloudflare interstitial or 403
   is BLOCKED, a 404 body is NOT_FOUND_PAGE, a near-empty body THIN_PAGE.
   BLOCKED must never be recorded as absence of evidence.                    */
function fetchAdapter() { throw new Error('V1 has no fetcher: supply pages to assess()'); }

module.exports = { extract, assess, collide, queue, typeCidByLabel, looseNameMatch,
                   cidKey, urlPlaceLabel, dispose, humanQueue,
                   HUMAN_ALWAYS, HUMAN_IF_IDENTITY, RETRY_CODES,
                   ID_TYPES, FETCH_STATES, VERDICTS, BUSINESS_TYPES,
                   PLACE_ID_REVALIDATE_MONTHS, fetchAdapter };
