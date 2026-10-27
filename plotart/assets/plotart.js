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
