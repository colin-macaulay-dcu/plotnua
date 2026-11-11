/* =====================================================================
   PLOTART · page behaviour (prototype, 27 Oct 2026)
   - gallery filters and sorting (client-side, on the static cards)
   - prototype forms and buttons: NOTHING is sent, stored or remembered
   - analytics shim: named events, OFF in the prototype
   - gentle reveal on scroll (respects reduced motion)
   ===================================================================== */
(function () {
  'use strict';

  /* ---- analytics -------------------------------------------------------
     Events are named now so measurement can be switched on at launch
     without touching markup. In the prototype ENABLED is false, so nothing
     is pushed anywhere. At launch: the standard PlotNua Cookiebot + GA4
     head block, then set ENABLED = true. Event names (GA4 custom events):
       pa_view_artwork, pa_view_artist, pa_view_collection, pa_view_story,
       pa_view_listing, pa_enquiry_open, pa_enquiry_submit,
       pa_f25_apply_click, pa_f25_application_submit, pa_living_interest,
       pa_board_side, pa_board_filter, pa_board_view_listing,
       pa_cross_discovery, and (future) pa_sale_completed. */
  var ENABLED = false;
  function track(name, params) {
    if (!ENABLED || !window.dataLayer) return;
    var p = params || {}; p.event = 'pa_' + name; window.dataLayer.push(p);
  }
  window.PlotArt = { track: track };

  document.addEventListener('DOMContentLoaded', function () {
    var view = document.querySelector('[data-pa-view]');
    if (view) {
      var v = view.getAttribute('data-pa-view');
      track('view_' + v, { id: view.getAttribute('data-artwork') || view.getAttribute('data-artist') || view.getAttribute('data-collection-view') || '' });
    }
    document.addEventListener('click', function (e) {
      var t = e.target.closest('[data-pa-track]');
      if (!t) return;
      var k = t.getAttribute('data-pa-track');
      if (k.indexOf('cross_') === 0) track('cross_discovery', { to: k.slice(6) });
      else if (k === 'enquiry_open') track('enquiry_open', {});
      else if (k === 'f25_apply_click') track('f25_apply_click', {});
      else if (k.indexOf('living_interest') === 0) track('living_interest', { as: k.split('_').pop() });
    });

    /* ---- reveal ------------------------------------------------------ */
    var rv = document.querySelectorAll('.pa-rv');
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
      }, { rootMargin: '0px 0px -8% 0px' });
      rv.forEach(function (el) { io.observe(el); });
    } else {
      rv.forEach(function (el) { el.classList.add('in'); });
    }

    /* ---- prototype forms: never send, never store --------------------- */
    document.querySelectorAll('[data-prototype-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var note = form.querySelector('[data-proto-note]');
        if (note) { note.classList.add('is-on'); note.focus && note.setAttribute('tabindex', '-1'); note.focus(); }
        track(form.getAttribute('data-prototype-form') === 'f25' ? 'f25_application_submit' : 'enquiry_submit', { prototype: true });
        form.reset();
      });
    });
    document.querySelectorAll('[data-proto-button]').forEach(function (b) {
      b.addEventListener('click', function () {
        var note = b.parentNode.querySelector('[data-proto-note]');
        if (note) note.classList.add('is-on');
      });
    });

    /* ---- gallery filters ---------------------------------------------- */
    var gallery = document.querySelector('[data-gallery]');
    if (!gallery) return;
    var cards = Array.prototype.slice.call(gallery.querySelectorAll('.pa-card'));
    var order = cards.slice();
    var selects = document.querySelectorAll('[data-filter]');
    var countEl = document.querySelector('[data-count]');
    var empty = document.querySelector('[data-empty]');
    var resets = document.querySelectorAll('[data-reset]');

    function readHash() {
      var q = {};
      (location.hash.replace('#', '') || '').split('&').forEach(function (kv) {
        var p = kv.split('='); if (p[0]) q[decodeURIComponent(p[0])] = decodeURIComponent(p[1] || '');
      });
      selects.forEach(function (s) { if (q[s.getAttribute('data-filter')]) s.value = q[s.getAttribute('data-filter')]; });
    }
    function writeHash() {
      var parts = [];
      selects.forEach(function (s) { if (s.value) parts.push(s.getAttribute('data-filter') + '=' + encodeURIComponent(s.value)); });
      history.replaceState(null, '', parts.length ? '#' + parts.join('&') : location.pathname);
    }
    function apply() {
      var f = {}, sort = '';
      selects.forEach(function (s) { if (s.getAttribute('data-filter') === 'sort') sort = s.value; else if (s.value) f[s.getAttribute('data-filter')] = s.value; });
      var n = 0;
      cards.forEach(function (c) {
        var ok = Object.keys(f).every(function (k) { return c.getAttribute('data-' + k) === f[k]; });
        c.hidden = !ok; if (ok) n++;
      });
      var sorted = order.slice();
      if (sort === 'price-asc') sorted.sort(function (a, b) { return a.dataset.price - b.dataset.price; });
      if (sort === 'price-desc') sorted.sort(function (a, b) { return b.dataset.price - a.dataset.price; });
      if (sort === 'year-desc') sorted.sort(function (a, b) { return b.dataset.year - a.dataset.year; });
      if (!sort) sorted.sort(function (a, b) { return b.dataset.featured - a.dataset.featured; });
      sorted.forEach(function (c) { gallery.appendChild(c); });
      if (countEl) countEl.textContent = n + (n === 1 ? ' work' : ' works');
      if (empty) empty.hidden = n !== 0;
      var any = Object.keys(f).length > 0 || sort;
      resets.forEach(function (r) { if (!r.closest('[data-empty]')) r.hidden = !any; });
      writeHash();
    }
    selects.forEach(function (s) { s.addEventListener('change', function () { apply(); track('collection_filter', { filter: s.getAttribute('data-filter') }); }); });
    resets.forEach(function (r) { r.addEventListener('click', function () { selects.forEach(function (s) { s.value = ''; }); apply(); }); });
    readHash(); apply();
  });
})();

/* ---- Homepage artist showcase: fair rotation (refinement 27 Oct 2026) --------
   Every eligible artist is rendered into one rotation in the page. On each visit
   the rotation starts at a random position and shows the next `data-slots`
   artists in order, so over many visits every eligible artist has the same
   chance of every slot. Nothing is pinned or weighted, and nothing is stored or
   sent. Without JavaScript the first artists in the published order show. */
(function () {
  document.querySelectorAll('[data-pa-rotate]').forEach(function (box) {
    var items = Array.prototype.slice.call(box.querySelectorAll('[data-rotate-item]'));
    var slots = parseInt(box.getAttribute('data-slots'), 10) || 3;
    var n = items.length;
    if (n <= slots) return;
    var start = Math.floor(Math.random() * n);
    items.forEach(function (el) { el.hidden = true; });
    for (var k = 0; k < slots; k++) {
      var el = items[(start + k) % n];
      el.hidden = false;
      el.classList.toggle('pa-acard--flip', k % 2 === 1);
      el.classList.add('in');
      box.appendChild(el);            /* display order follows the rotation */
    }
  });
})();

/* ---- Art for Hire marks in an artist's gallery (11 Nov 2026) ------------------
   Runs only on an artist's gallery page or one of their artwork pages. It reads the
   published Art for Hire page (this site) and keeps the listings for THIS artist; if
   there are none it stops there, and nothing is asked of any other service. Otherwise
   it asks PlotArt's enquiry service which works are listed for hire right now (the
   same check the Art for Hire page makes; no personal data is sent). Only works that
   are both on the published page and listed now are marked. Any failure, an expired
   answer or Art for Hire not being open shows nothing, and the check repeats when the
   answer expires. Nothing is stored. */
(function () {
  'use strict';
  if (!window.fetch || !window.DOMParser || !window.AbortController) return;
  var m = location.pathname.match(/\/plotart\/artists\/([a-z0-9-]+)\/(?:([a-z0-9-]+)\.html)?$/);
  var grid = document.querySelector('.pa-ag-grid'), info = document.querySelector('.pa-aw-info');
  if (!m || (!grid && !info)) return;
  var ARTIST = m[1], WORK = m[2] || null, HIRE = '../../art-for-hire/';
  function timed(url, opts) {
    var c = new AbortController(), t = setTimeout(function () { c.abort(); }, 6000);
    opts.signal = c.signal;
    return fetch(url, opts).then(function (r) { clearTimeout(t); return r; }, function (e) { clearTimeout(t); throw e; });
  }
  function clear() {
    document.querySelectorAll('[data-pa-hire-mark]').forEach(function (el) { el.parentNode.removeChild(el); });
  }
  function el(tag, cls, html) { var e = document.createElement(tag); e.className = cls; e.setAttribute('data-pa-hire-mark', ''); e.innerHTML = html; return e; }
  function mark(listed) {
    clear();
    var link = '<a href="' + HIRE + '#afh3-works">';
    if (grid) {
      var n = 0;
      grid.querySelectorAll('.pa-ag-work').forEach(function (li) {
        var a = li.querySelector('a.pa-ag-tile'), cap = li.querySelector('.pa-ag-cap');
        var slug = a && (a.getAttribute('href') || '').replace(/\.html$/, '');
        if (cap && listed.indexOf(slug) !== -1) { cap.appendChild(el('span', 'pa-ag-hire', 'Available to hire')); n++; }
      });
      var head = document.querySelector('.pa-ag-head');
      if (n && head) head.parentNode.insertBefore(el('p', 'pa-ag-hirenote',
        (n === 1 ? 'One of these works is' : 'Works marked “Available to hire” are') +
        ' also offered for hire, for film and television, interiors and staging. ' + link + 'See ' + (n === 1 ? 'it' : 'them') + ' on Art for Hire</a>'), head.nextSibling);
    }
    if (info && WORK && listed.indexOf(WORK) !== -1) {
      var price = info.querySelector('.pa-aw-price');
      var p = el('p', 'pa-aw-hire', 'Also available to hire. ' + link + 'Enquire on Art for Hire</a>');
      if (price) price.parentNode.insertBefore(p, price.nextSibling); else info.appendChild(p);
    }
  }
  var bySlug = null, api = null, timer = null;
  function check() {
    timed(api + '/v1/hire-listed', { credentials: 'omit', cache: 'no-store' })
      .then(function (r) { return r.json().then(function (j) { return [r, j]; }); })
      .then(function (rj) {
        var r = rj[0], j = rj[1], until = Date.parse(j && j.valid_until);
        if (!r.ok || !j || j.ok !== true || j.open !== true || !Array.isArray(j.items) || !(until > Date.now())) return clear();
        var live = {};
        j.items.forEach(function (i) { if (i && typeof i.id === 'string') live[i.id] = true; });
        var listed = Object.keys(bySlug).filter(function (s) { return live[bySlug[s]]; });
        if (!listed.length) return clear();
        mark(listed);
        clearTimeout(timer);
        timer = setTimeout(check, Math.max(30000, until - Date.now()));
      })
      .catch(clear);
  }
  timed(HIRE, { credentials: 'same-origin' })
    .then(function (r) { if (!r.ok) throw new Error('hire page'); return r.text(); })
    .then(function (html) {
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var cards = doc.querySelectorAll('[data-hire-work][data-hire-artist-slug="' + ARTIST + '"][data-hire-slug]');
      if (!cards.length) return;
      var s = doc.querySelector('script[src$="hire-live.js"][data-api]');
      api = s && s.getAttribute('data-api');
      if (!api || !/^https:\/\/[a-z0-9.-]+$/.test(api)) return;
      bySlug = {};
      cards.forEach(function (c) { bySlug[c.getAttribute('data-hire-slug')] = c.getAttribute('data-hire-work'); });
      check();
    })
    .catch(function () {});
})();
