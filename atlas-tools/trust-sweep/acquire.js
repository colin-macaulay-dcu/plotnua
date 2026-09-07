/* TRUST SWEEP v1.1 — DOM ACQUISITION ADAPTER
   ============================================================================
   Supplies real-DOM pages to trust-sweep.js. Reads ONLY the supplier's own
   site. No Google Search, no Google Maps pages, no Places API, no ratings.

   WHY A PROJECTION RATHER THAN RAW HTML. Measured: a plain HTML fetch strips
   the attributes the engine depends on — the Garden Rooms Place ID lives in a
   data-id attribute that never survived. So pages must come from a real DOM.
   The capture below returns a PROJECTION of that DOM: every <a href>, every
   <iframe src>, every element carrying data-id/data-provider, plus body text.
   That is exactly the surface the classifier reads, taken from the rendered
   document, and it keeps captures small enough to move around. It is a
   projection, not the whole page, and is labelled as such in every record.

   ACQUISITION BOUNDARY. This module does not open a browser itself. The host
   agent drives the browser and hands captures back — see CAPTURE_SNIPPET.
   ========================================================================== */
'use strict';
const T = require('./trust-sweep.js');

/* Contact/location paths worth one attempt each. Homepage first: in the pilot
   the footer alone carried the evidence more often than the contact page did.
   Deliberately NOT a crawl — at most two pages per organisation. */
const CONTACT_PATHS = ['/contact/', '/contact-us/', '/contacts/', '/contact'];

function plan(org) {
  const base = 'https://' + String(org.canonicalDomain || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
  return { organisationId: org.organisationId, name: org.name, base,
           pages: [base + '/', ...CONTACT_PATHS.map(p => base + p)],
           maxPages: 2 };
}

/* Fetch state from what the browser actually returned. BLOCKED is a fact about
   the fetch; NOT_FOUND_PAGE is a fact about the path. They are never merged —
   a 404 body can still carry footer evidence and is parsed, a blocked page
   cannot be read at all and is not evidence of anything. */
function classifyState(title, text, projection) {
  const t = String(title || '');
  const b = String(text || '');
  if (/just a moment|attention required|checking your browser|access denied|forbidden|^403/i.test(t + ' ' + b.slice(0, 300)))
    return 'BLOCKED';
  if (/page not found|not found|404|does not exist/i.test(t)) return 'NOT_FOUND_PAGE';
  if (!projection || projection.length < 400) return 'THIN_PAGE';
  return 'READ';
}

/* Run in the browser pane, one page at a time. Returns a capture record. */
const CAPTURE_SNIPPET = `(function(){
  var parts=[],trunc=0,CAP=2000;
  function keep(html){ if(html.length>CAP){trunc++; return html.slice(0,CAP)+'<!--TRUNCATED-->';} return html; }
  document.querySelectorAll('a[href]').forEach(function(a){
    /* The href is captured WHOLE and separately from the markup. A Google Maps
       URL carries its CID late in the string, so slicing the outerHTML can sever
       an identifier and make a present fact look absent. */
    parts.push('<a href="'+a.getAttribute('href')+'"></a>');
    parts.push(keep(a.outerHTML.slice(0,400)));
  });
  document.querySelectorAll('iframe[src]').forEach(function(f){parts.push('<iframe src="'+f.src+'"></iframe>');});
  document.querySelectorAll('[data-id],[data-provider]').forEach(function(e){
    parts.push('<div data-id="'+(e.getAttribute('data-id')||'')+'" data-provider="'+(e.getAttribute('data-provider')||'')+'"></div>');});
  return {url:location.href,title:document.title,truncatedFields:trunc,
          text:document.body?document.body.innerText.slice(0,20000):'',
          projection:parts.join('\\n')};
})()`;

/* TRUNCATION IS UNRESOLVED ACQUISITION, NOT ABSENCE. If any field was cut, the
   record says so and the organisation is queued: "we could not read it all" and
   "there is nothing there" are different facts and must never be merged. */
function truncationExceptions(captures) {
  const hit = captures.filter(c => c.truncatedFields > 0 ||
    /<!--TRUNCATED-->/.test(c.projection || ''));
  return hit.length ? [{ code: 'TRUNCATED_ACQUISITION',
    detail: hit.map(c => c.url + ' (' + (c.truncatedFields || '?') + ' fields)').join(' | ') }] : [];
}

/* captures: [{organisationId, url, title, text, projection}] */
function pagesFromCaptures(captures) {
  return captures.map(c => ({
    url: c.url,
    fetchState: c.fetchState || classifyState(c.title, c.text, c.projection),
    html: (c.projection || '') + '\n' + (c.text || ''),
    acquisition: 'DOM_PROJECTION',
  }));
}

/* One organisation, from its captures, through the unchanged v1 classifier. */
function assessCaptured(org, captures, now) {
  const r = T.assess(org, pagesFromCaptures(captures), now);
  const tr = truncationExceptions(captures);
  if (tr.length) {
    r.exceptions.push(...tr);
    /* A clean-looking UNRESOLVED built on truncated input is not a finding. */
    if (r.identity.verdict === 'UNRESOLVED') r.identity.verdict = 'AMBIGUOUS';
  }
  return r;
}

/* Whole cohort: per-organisation records plus the cross-organisation pass. */
function sweep(orgsWithCaptures, now) {
  const records = orgsWithCaptures.map(o => assessCaptured(o.org, o.captures, now));
  T.collide(records);
  return { records, queue: T.queue(records) };
}

module.exports = { plan, classifyState, pagesFromCaptures, assessCaptured, sweep, truncationExceptions,
                   CAPTURE_SNIPPET, CONTACT_PATHS };
