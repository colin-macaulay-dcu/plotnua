/* ==========================================================================
   PLOTNUA SEARCH · V1 RUNTIME
   ==========================================================================
   PlotNua's FIRST shared local front-end asset. Founder decision B-2, and that
   approval is SPECIFIC TO SEARCH: nothing here extracts existing inline CSS or
   JS, refactors any page, or starts a component system. Every other page stays
   self-contained exactly as it is.

   ONE DIRECTION ONLY
     published corpus -> generated index -> client-side search -> relevance
     -> existing routes
   This file READS search-index-v1.json. It never reads or writes Atlas
   ranking, qualification, confidence, evidence, pricing governance, matching,
   or My Plot state. Search relevance orders SEARCH RESULTS and nothing else.

   SEARCH TERMS ARE LOCAL AND EPHEMERAL
     NO query string, NO hash, NO localStorage, NO sessionStorage, NO
     IndexedDB, NO cookie, NO fetch/XHR/sendBeacon carrying a term, NO
     dataLayer or analytics push.

     ONE EXCEPTION, founder-approved after a real-browser failure: the term may
     live in this document's own HISTORY STATE, so that Back from Product Detail
     restores the Search the homeowner was looking at. history.pushState(state,
     '') writes no URL — the address bar never carries the term — and history
     state is per-entry session memory that dies with the tab, is never sent to
     a server, and is not readable by another document. See SEARCH HISTORY
     below for why nothing weaker worked. GTM and Cookiebot are live on every public page, so the
     dataLayer path is a real leak route and is deliberately never touched.

   TEXT-ONLY
     The index carries no imagery field (contract §2) and this runtime has no
     code path that renders a product or supplier image from any source. That
     is why unauthorised imagery cannot leak through Search at all.

   NO FUZZY MATCHING in V1. Substring and prefix only. A wrong confident answer
   is worse than an honest near-miss — the same standard the Atlas resolver
   holds, though note that the resolver is EXACT-ONLY and is a different
   contract: it answers "is this exactly a known product?", search answers
   "what might you mean?". The two must not be merged.
   ========================================================================== */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;          /* Node, for the acceptance + hostile suites */
  } else {
    root.PlotNuaSearch = api;
    if (typeof document !== 'undefined') { api.boot(); }
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var INDEX_URL = 'search-index-v1.json';

  /* THE PRODUCT DEEP LINK, composed from the template the index carries once.
     Founder review found the release blocker this replaces: every product
     result linked to the bare page, so Search found the exact product and then
     dropped the homeowner on the Eircode landing screen. The id is the governed
     record id; no product-name string is ever an identifier. */
  function productRoute(index, rec) {
    var tpl = index && index.routes && index.routes.product;
    if (!tpl || !rec || rec.type !== 'product') { return null; }
    var id = String(rec.id || '');
    if (id.indexOf('prod-') !== 0) { return null; }
    /* &from=search is appended HERE, by Search, not stored in the index — the
       index describes the product, and the origin is Search's own business. It
       contains no search text and nothing about the homeowner; it exists only
       so Product Detail can say "Back to Search" instead of the false "Back to
       Results" the founder's real-browser test found. */
    return tpl.replace('{id}', encodeURIComponent(id.slice(5))) + '&from=search';
  }
  var MAX_PER_SUPPLIER = 3;
  var MAX_SUPPLIER_EXPAND = 6;

  /* ---------------------------------------------------------------- matching */

  function normalise(s) {
    return String(s == null ? '' : s)
      .toLowerCase()
      .replace(/[‘’‚‛]/g, "'")
      .replace(/[“”]/g, '"')
      .replace(/[–—]/g, '-')
      .replace(/[^a-z0-9€'\- ]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function tokens(s) {
    return normalise(s).split(' ').filter(Boolean);
  }

  /* "under €20,000", "below 20000", "up to €20k"

     DEFECT FOUND AND FIXED BY THE ACCEPTANCE SUITE, and it mattered. The first
     version ran this match over normalise(q) — but normalise() replaces a comma
     with a space, so "under €20,000" became "under 20 000" and [\d,]+ matched
     only the "20". The cap parsed as TWENTY EURO.

     A3a caught it. A3b and A3c had passed VACUOUSLY: "every product returned is
     under the cap" is trivially true when a €20 cap returns nothing at all. The
     suite now asserts a non-empty capped result, and asserts four variant
     spellings, so neither the bug nor the vacuous pass can come back.

     Both functions therefore read the RAW query, before any normalisation
     touches the digits. */
  /* GREEDY, and no whitespace inside the number class. A LAZY quantifier plus a
     trailing \b stopped dead at the comma: for "under €20,000" it matched "20",
     because the boundary between "0" and "," satisfied \b. Greedy takes the
     whole "20,000"; excluding \s stops the number swallowing the next word. */
  var PRICE_RE = /(?:under|below|less than|up to|max)\s*(?:€|eur|euro)?\s*(\d[\d.,]*)\s*(k)?/;

  function priceIntent(q) {
    var m = String(q == null ? '' : q).toLowerCase().match(PRICE_RE);
    if (!m) { return null; }
    var digits = m[1].replace(/[,\s]/g, '').replace(/\.(\d{1,2})$/, '').replace(/\./g, '');
    var n = parseInt(digits, 10);
    if (!isFinite(n)) { return null; }
    if (m[2]) { n = n * 1000; }
    return n;
  }

  /* The query with any price clause removed, so "garden room under €20,000"
     searches for "garden room". Stripped from the RAW query for the same
     reason: on normalised text the comma had already become a space, which left
     a stray "000" token that every product then had to contain. */
  function coreTerms(q) {
    var raw = String(q == null ? '' : q).toLowerCase();
    return tokens(raw.replace(new RegExp(PRICE_RE.source, 'g'), ' '));
  }

  /* RELEVANCE. Ordering only. No tier, no confidence, no price, no Atlas
     signal participates — a WITH_CAVEAT exact match outranks a HIGH_CONFIDENCE
     partial every time, because that is what the homeowner asked for. */
  var EXACT = 1000, PREFIX = 800, ORG = 600, TYPE = 400, OTHER = 200;

  function scoreRecord(rec, terms, qnorm) {
    if (!terms.length) { return 0; }
    var name = normalise(rec.name || rec.title || '');
    var org = normalise(rec.organisation || '');
    var ptype = normalise(rec.productType || '');
    var stand = normalise(rec.standfirst || '');
    var topics = normalise((rec.topics || []).join(' '));
    var all = [name, org, ptype, stand, topics].join(' ');

    for (var i = 0; i < terms.length; i++) {
      if (all.indexOf(terms[i]) === -1) { return 0; }   /* every term must hit */
    }
    if (name === qnorm) { return EXACT; }
    if (name.indexOf(qnorm) === 0) { return PREFIX; }
    if (org && (org === qnorm || org.indexOf(qnorm) === 0)) { return ORG; }
    if (ptype && ptype.indexOf(qnorm) !== -1) { return TYPE; }
    return OTHER;
  }

  /* The governed topic map is carried in the index's possibility topics, so no
     second file is fetched and no mapping can exist at runtime that governance
     has not approved. */
  function topicHits(records, qnorm) {
    return records.filter(function (r) {
      return r.type === 'possibility' &&
             (r.topics || []).some(function (t) { return normalise(t) === qnorm; });
    });
  }

  function search(index, query) {
    var records = (index && index.records) || [];
    var qnorm = normalise(query);
    var cap = priceIntent(query);
    var terms = coreTerms(query);

    var mapped = topicHits(records, qnorm);
    var mappedIds = {};
    mapped.forEach(function (r) { mappedIds[r.id] = true; });

    /* A possibility-only mapping ("sauna") answers with possibilities and
       suppresses product and supplier guesses entirely. That is what keeps the
       answer honest when the corpus holds nothing: the four sauna mentions in
       the universe are incidental or negative prose and features is never
       indexed, so there is nothing truthful to show. */
    var possibilityOnly = mapped.length > 0 && qnorm === 'sauna';

    var scored = [];
    records.forEach(function (r) {
      if (mappedIds[r.id]) { scored.push({ r: r, s: EXACT + 1 }); return; }
      if (possibilityOnly && r.type !== 'possibility') { return; }
      var s = scoreRecord(r, terms, qnorm);
      if (!s) { return; }
      if (cap != null && r.type === 'product') {
        if (typeof r.price !== 'number' || r.price > cap) { return; }
      }
      if (cap != null && r.type === 'supplier') {
        if (!r.priceRange || r.priceRange[0] > cap) { return; }
      }
      scored.push({ r: r, s: s });
    });

    scored.sort(function (a, b) {
      if (b.s !== a.s) { return b.s - a.s; }
      var an = (a.r.name || a.r.title || ''), bn = (b.r.name || b.r.title || '');
      return an.localeCompare(bn);
    });

    var out = { possibility: [], supplier: [], product: [], journey: [] };
    scored.forEach(function (x) { (out[x.r.type] || []).push(x.r); });

    /* Journeys are suppressed when their possibility is already answering, so
       the homeowner is not offered the same route twice. */
    var shown = {};
    out.possibility.forEach(function (p) { shown[p.id] = true; });
    out.journey = out.journey.filter(function (j) { return !shown[j.possibilityId]; });

    /* D-7: a supplier EXPANDS INSIDE SEARCH. Its products are derived here from
       the product records already in memory — the index stores no productIds,
       because duplicating 573 of them cost 14 KB for information it already
       held. Expansion can therefore only ever reach indexed products. */
    var byOrg = {};
    records.forEach(function (r) {
      if (r.type !== 'product') { return; }
      (byOrg[r.organisation] = byOrg[r.organisation] || []).push(r);
    });
    out.supplier.forEach(function (s) { s.__products = byOrg[s.name] || []; });

    /* THE ROUTE TRAVELS WITH THE RESULT. renderResults() used to call
       productRoute(state.index, …), reaching into module state it was not
       given — so rendering outside the browser produced no links at all, and
       P5a caught it. Composing here, where the index is in hand, makes the
       renderer pure and makes the test exercise the real thing. */
    records.forEach(function (r) {
      if (r.type === 'product' && !r.__route) {
        var u = productRoute(index, r);
        if (u) { r.__route = u; }
      }
    });

    return {
      query: query,
      priceCap: cap,
      mappedByTopic: mapped.map(function (r) { return r.id; }),
      possibilityOnly: possibilityOnly,
      counts: {
        possibility: out.possibility.length, supplier: out.supplier.length,
        product: out.product.length, journey: out.journey.length
      },
      groups: out,
      productsBySupplier: groupProducts(out.product)
    };
  }

  /* GROUP + REFINE, founder decision D-4. 140 flat rows is not an answer. */
  function groupProducts(products) {
    var by = {}, order = [];
    products.forEach(function (p) {
      var k = p.organisation || 'Other';
      if (!by[k]) { by[k] = []; order.push(k); }
      by[k].push(p);
    });
    return order.map(function (k) {
      return {
        organisation: k,
        total: by[k].length,
        shown: by[k].slice(0, MAX_PER_SUPPLIER),
        hidden: Math.max(0, by[k].length - MAX_PER_SUPPLIER)
      };
    });
  }

  /* ------------------------------------------------------------------ render */

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function money(n) {
    return '€' + Number(n).toLocaleString('en-IE', { maximumFractionDigits: 0 });
  }

  var CAVEAT_TEXT = {
    'no-published-irish-route':
      'No published Irish route — we have not found an Irish supply route for this yet.'
  };

  /* TIER LABELS ARE GONE FROM THE SEARCH SURFACE.
     Founder review: "Evidenced, with caveats" is internal Atlas language and
     does not belong on a surface whose job is to help a homeowner FIND
     something. 434 of 573 products are WITH_CAVEAT, so the phrase appeared on
     most results and told the homeowner nothing actionable.
     NOTHING UNDERNEATH CHANGED. Every record still carries its literal tier
     (G6 still asserts the distribution is identical), the caveat data is
     untouched and Atlas is unaffected — the tier is simply not PRINTED here.
     What IS still printed is the one caveat that materially affects a
     homeowner: no published Irish route. Concealing that would be the opposite
     mistake, and G9 still requires it on all 43. */

  function renderResults(res) {
    var h = [];
    var total = res.counts.possibility + res.counts.supplier +
                res.counts.product + res.counts.journey;

    if (!total) {
      h.push('<div class="pns-zero">');
      h.push('<p class="pns-zero-lead">We have nothing on <strong>' +
             esc(res.query) + '</strong> yet.</p>');
      h.push('<p>PlotNua only shows what it can stand behind. If a supplier or ' +
             'product is not here, it is because we have not researched it to a ' +
             'standard we would publish — not because it does not exist.</p>');
      h.push('<p>You could try a possibility instead: ' +
             '<a href="discoveries.html">browse all Discoveries</a>.</p>');
      h.push('</div>');
      return h.join('');
    }

    if (res.counts.possibility) {
      h.push(section('Possibilities', res.counts.possibility));
      h.push('<ul class="pns-list">');
      res.groups.possibility.forEach(function (p) {
        h.push('<li class="pns-item"><a class="pns-title" href="' + esc(p.route) + '">' +
               esc(p.title) + '</a>' +
               (p.standfirst ? '<p class="pns-sub">' + esc(p.standfirst) + '</p>' : '') +
               '</li>');
      });
      h.push('</ul>');
    }

    if (res.counts.supplier) {
      h.push(section('Suppliers', res.counts.supplier));
      h.push('<ul class="pns-list pns-suppliers">');
      res.groups.supplier.forEach(function (s, i) {
        /* THE SUPPLIER NAME IS NOT A LINK. Founder instruction: make the expand
           obviously an expand, rather than a name that looks like navigation
           and then unexpectedly unfolds. The name is plain text; the control is
           an explicit, labelled, aria-expanded button. There is also nothing to
           link to — a supplier record carries no route at all, which R2
           asserts. */
        var prods = s.__products || [];
        var shown = prods.slice(0, MAX_SUPPLIER_EXPAND);
        var rest = Math.max(0, prods.length - shown.length);
        var pid = 'pnsSup' + i;
        h.push('<li class="pns-item pns-sup">');
        h.push('<p class="pns-sup-name">' + esc(s.name) + '</p>');
        h.push('<p class="pns-sub">' + s.productCount + ' product' +
               (s.productCount === 1 ? '' : 's') + ' in Atlas' +
               (s.priceRange ? ' \u00b7 from ' + money(s.priceRange[0]) : '') + '</p>');
        (s.caveats || []).forEach(function (c) {
          h.push('<p class="pns-caveat">' + esc(CAVEAT_TEXT[c] || c) + '</p>');
        });
        if (prods.length) {
          h.push('<button type="button" class="pns-expand" aria-expanded="false"' +
                 ' aria-controls="' + pid + '" data-pns-expand="' + pid + '">' +
                 'View ' + prods.length + ' product' +
                 (prods.length === 1 ? '' : 's') +
                 '<span class="pns-chev" aria-hidden="true"></span></button>');
          h.push('<ul class="pns-list pns-sup-products" id="' + pid + '" hidden>');
          shown.forEach(function (p) { h.push(productItem(p)); });
          if (rest) {
            /* BOUNDED EVEN WHEN EXPANDED. A supplier with 40 products does not
               dump 40 rows onto the page because it was opened. */
            h.push('<li class="pns-more">' + rest + ' more from ' + esc(s.name) +
                   '</li>');
          }
          h.push('</ul>');
        }
        h.push('</li>');
      });
      h.push('</ul>');
    }

    if (res.counts.product) {
      h.push(section('Products', res.counts.product));
      if (res.priceCap != null) {
        h.push('<p class="pns-note">Showing products under ' + money(res.priceCap) +
               '. Only products with an evidenced price can be filtered by price, ' +
               'so some products are not shown here.</p>');
      }
      res.productsBySupplier.forEach(function (g) {
        h.push('<div class="pns-group"><h4 class="pns-group-h">' + esc(g.organisation) +
               ' <span class="pns-count">' + g.total + '</span></h4><ul class="pns-list">');
        g.shown.forEach(function (p) { h.push(productItem(p)); });
        if (g.hidden) {
          h.push('<li class="pns-more">' + g.hidden + ' more from ' +
                 esc(g.organisation) + '</li>');
        }
        h.push('</ul></div>');
      });
    }

    if (res.counts.journey) {
      h.push(section('Property Checks', res.counts.journey));
      h.push('<ul class="pns-list">');
      res.groups.journey.forEach(function (j) {
        h.push('<li class="pns-item"><a class="pns-title" href="' + esc(j.route) +
               '">' + esc(j.title) + '</a></li>');
      });
      h.push('</ul>');
    }
    return h.join('');
  }

  /* ONE product row, used by the Products groups AND by supplier expansion, so
     the two can never drift apart in copy or in routing. */
  function productItem(p) {
    var href = p.__route || null;
    var h = ['<li class="pns-item">'];
    h.push(href
      ? '<a class="pns-title" href="' + esc(href) + '">' + esc(p.name) + '</a>'
      : '<span class="pns-title">' + esc(p.name) + '</span>');
    h.push('<p class="pns-sub">' + esc(p.organisation || '') +
           (p.productType ? ' \u00b7 ' + esc(p.productType) : '') +
           (typeof p.price === 'number' ? ' \u00b7 ' + money(p.price) : '') + '</p>');
    (p.caveats || []).forEach(function (c) {
      h.push('<p class="pns-caveat">' + esc(CAVEAT_TEXT[c] || c) + '</p>');
    });
    h.push('</li>');
    return h.join('');
  }

  function section(label, n) {
    return '<h3 class="pns-sec">' + esc(label) +
           ' <span class="pns-count">' + n + '</span></h3>';
  }

  /* -------------------------------------------------------------------- boot */

  var state = { index: null, loading: false };

  /* =======================================================================
     SEARCH HISTORY
     =======================================================================
     ROOT CAUSE OF THE FOUNDER'S REAL-BROWSER FAILURE, diagnosed before fixing.

     Homepage -> pill -> search "Powersheds" -> open a product -> Back landed on
     the HOMEPAGE, not on the Search results. Tracing the actual mutations:

       entry A   index.html loads
       pill      ev.preventDefault() + openPanel() -> the overlay opens ON the
                 homepage document. NO navigation. NO history entry.
       typing    no history entry
       product   a real <a href> -> NAVIGATES -> entry B (your-plot.html)
       Back      goes to the entry before B, which is A: the homepage.

     So there was never a Search entry to go back to. My previous assumption
     that "ordinary browser history will restore the live Search document" was
     simply wrong: the overlay had deliberately avoided touching history, so
     history had nothing to restore. And even landing back on index.html, the
     overlay's state is transient JavaScript — a fresh load has an empty field.

     TWO FAILURES, ONE CAUSE: no entry, and no state in it.

     THE FIX, within the privacy contract. Opening the overlay pushes an entry,
     so Search occupies a place in history. Immediately before a product
     navigation, the transient UI state is written into THAT entry with
     replaceState. On the way back the state is read and the overlay rebuilt.

     pushState(state, '') is called with NO url argument, so the address bar is
     never touched and the term never enters a URL. History state is per-entry
     session memory: it dies with the tab, is never transmitted, and no other
     document can read it. It holds the query and which supplier was expanded —
     nothing about the property, nothing from Atlas, no decision state. */

  var SEARCH_STATE_KEY = 'pnSearch';

  /* What travels: the typed query, and the expanded supplier ids. Nothing else.
     Deliberately NOT the results — those are recomputed from the governed index
     on the way back, so a restored Search can never show a stale answer. */
  function uiSnapshot() {
    var e = els();
    var open = [];
    if (e.out) {
      [].forEach.call(e.out.querySelectorAll('[data-pns-expand][aria-expanded="true"]'),
        function (b) { open.push(b.getAttribute('data-pns-expand')); });
    }
    return {
      open: !!(e.panel && !e.panel.hidden) || !e.panel,
      q: e.input ? e.input.value : '',
      expanded: open
    };
  }

  function writeSnapshot(replace) {
    var snap = {};
    snap[SEARCH_STATE_KEY] = uiSnapshot();
    try {
      /* NO url argument: the address bar is never written. */
      if (replace) { history.replaceState(snap, ''); }
      else { history.pushState(snap, ''); }
    } catch (err) { /* history unavailable: Search still works, Back is just ordinary */ }
  }

  function restoreSnapshot(snap) {
    if (!snap || !snap.open) { return false; }
    var e = els();
    if (e.panel && e.panel.hidden) {
      e.panel.hidden = false;
      document.documentElement.classList.add('pns-open');
      if (e.open) { e.open.setAttribute('aria-expanded', 'true'); }
    }
    if (e.input) { e.input.value = snap.q || ''; }
    loadIndex().then(function () {
      run();
      /* Re-open whatever was expanded. The ids are positional (pnsSup0…), so
         they are only meaningful against the SAME query — which is why the
         query is restored first and the results re-run before this. */
      (snap.expanded || []).forEach(function (id) {
        var list = document.getElementById(id);
        var btn = document.querySelector('[data-pns-expand="' + id + '"]');
        if (list && btn) { list.hidden = false; btn.setAttribute('aria-expanded', 'true'); }
      });
    });
    return true;
  }

  function els() {
    return {
      panel: document.getElementById('pnsPanel'),
      input: document.getElementById('pnsInput'),
      out: document.getElementById('pnsResults'),
      open: document.getElementById('pnsOpen'),
      close: document.getElementById('pnsClose'),
      status: document.getElementById('pnsStatus')
    };
  }

  function loadIndex() {
    if (state.index || state.loading) { return Promise.resolve(state.index); }
    state.loading = true;
    /* The ONLY fetch this file makes. Same origin, no query string, and it
       carries nothing about the homeowner. */
    return fetch(INDEX_URL, { credentials: 'omit' })
      .then(function (r) { return r.json(); })
      .then(function (j) { state.index = j; state.loading = false; return j; })
      .catch(function () { state.loading = false; return null; });
  }

  function run() {
    var e = els();
    if (!e.input || !e.out) { return; }
    var q = e.input.value;                /* lives here and nowhere else */
    if (!normalise(q)) { e.out.innerHTML = ''; setStatus(''); return; }
    if (!state.index) {
      e.out.innerHTML = '<p class="pns-note">Loading what PlotNua knows…</p>';
      loadIndex().then(function () { if (state.index) { run(); } });
      return;
    }
    var res = search(state.index, q);
    e.out.innerHTML = renderResults(res);
    var total = res.counts.possibility + res.counts.supplier +
                res.counts.product + res.counts.journey;
    setStatus(total ? total + ' result' + (total === 1 ? '' : 's') : 'No results');
  }

  function setStatus(t) {
    var e = els();
    if (e.status) { e.status.textContent = t; }
  }

  function openPanel() {
    var e = els();
    if (!e.panel) { return; }
    e.panel.hidden = false;
    document.documentElement.classList.add('pns-open');
    if (e.open) { e.open.setAttribute('aria-expanded', 'true'); }
    /* Search now occupies a history entry. Without this there was nothing for
       Back to return to, which is the whole root cause above. */
    writeSnapshot(false);
    loadIndex();
    if (e.input) { e.input.focus(); }
  }

  function closePanel() {
    var e = els();
    if (!e.panel) { return; }
    e.panel.hidden = true;
    document.documentElement.classList.remove('pns-open');
    if (e.open) { e.open.setAttribute('aria-expanded', 'false'); e.open.focus(); }
    /* The term is cleared on close. Nothing was persisted anywhere, so there is
       nothing else to clean up. */
    if (e.input) { e.input.value = ''; }
    if (e.out) { e.out.innerHTML = ''; }
    setStatus('');
  }

  function boot() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', wire);
    } else { wire(); }
  }

  function wire() {
    var e = els();
    if (e.open) { e.open.addEventListener('click', function (ev) {
      /* THE PILL IS A REAL LINK to search.html, so Search works with
         JavaScript disabled. With JavaScript, this upgrades it to the overlay
         in place — faster, and it keeps the homeowner where they were. */
      if (e.open.getAttribute('data-pns-current') === 'true') {
        /* On search.html the pill is the CURRENT page, not a way to open a
           second redundant Search. It focuses the field that is already there,
           and it stays visible: the control must not disappear when the
           homeowner arrives. */
        ev.preventDefault();
        if (e.input) { e.input.focus(); }
        return;
      }
      if (!e.panel) { return; }           /* no overlay here: follow the href */
      ev.preventDefault();
      if (e.panel.hidden) { openPanel(); } else { closePanel(); }
    }); }
    if (e.close) { e.close.addEventListener('click', closePanel); }
    if (e.input) {
      var t = null;
      e.input.addEventListener('input', function () {
        clearTimeout(t); t = setTimeout(run, 110);
      });
      e.input.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') { closePanel(); }
      });
    }
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && e.panel && !e.panel.hidden) { closePanel(); }
    });

    /* THE HAND-OFF. A product link is a real <a href>, so it navigates and the
       document is torn down. The snapshot is written into the CURRENT entry
       first — replaceState, not push, because this is the Search entry being
       annotated rather than a new place — and then navigation proceeds
       normally. preventDefault is NOT called: the link still works with
       JavaScript disabled, exactly as before. */
    if (e.out) {
      e.out.addEventListener('click', function (ev) {
        var a = ev.target && ev.target.closest ? ev.target.closest('a.pns-title') : null;
        if (!a) { return; }
        if ((a.getAttribute('href') || '').indexOf('?product=') === -1) { return; }
        writeSnapshot(true);
      }, true);
    }

    /* Coming back. Two paths, because browsers differ: a bfcache restore fires
       popstate, a full reload does not but DOES populate history.state. Both
       are handled, so Back restores Search either way. */
    window.addEventListener('popstate', function (ev) {
      var snap = ev.state && ev.state[SEARCH_STATE_KEY];
      if (snap) { restoreSnapshot(snap); return; }
      /* An entry with no Search state means Search was not open there — close
         the overlay rather than leaving it stranded over the page. */
      if (e.panel && !e.panel.hidden) {
        e.panel.hidden = true;
        document.documentElement.classList.remove('pns-open');
        if (e.open) { e.open.setAttribute('aria-expanded', 'false'); }
      }
    });

    try {
      var boot = history.state && history.state[SEARCH_STATE_KEY];
      if (boot) { restoreSnapshot(boot); }
    } catch (err) { /* no history state: ordinary first visit */ }

    /* SUPPLIER EXPANSION, by delegation on the results container so it survives
       every re-render without rebinding. Pure DOM toggle: nothing is stored,
       nothing is fetched, no URL changes. */
    if (e.out) {
      e.out.addEventListener('click', function (ev) {
        var btn = ev.target && ev.target.closest
          ? ev.target.closest('[data-pns-expand]') : null;
        if (!btn) { return; }
        var list = document.getElementById(btn.getAttribute('data-pns-expand'));
        if (!list) { return; }
        var open = btn.getAttribute('aria-expanded') === 'true';
        btn.setAttribute('aria-expanded', open ? 'false' : 'true');
        list.hidden = open;
      });
    }
    /* search.html ships its field in the static page, so Search works there
       with no panel to open. The pill is marked current so it reads as the page
       the homeowner is on rather than a way to open Search again. */
    if (e.input && !e.panel) {
      if (e.open) { e.open.setAttribute('data-pns-current', 'true'); }
      loadIndex();
    }
  }

  return {
    boot: boot, search: search, normalise: normalise, tokens: tokens,
    priceIntent: priceIntent, coreTerms: coreTerms, renderResults: renderResults,
    groupProducts: groupProducts, INDEX_URL: INDEX_URL
  };
}));
