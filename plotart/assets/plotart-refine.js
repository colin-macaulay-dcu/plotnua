/* PlotArt · Refine on All Artworks (founder approval 21 Nov 2026).

   Progressive enhancement, failing safe: the Refine line ships hidden and every work ships visible, so with no
   script, a blocked script or ANY error here the page is the full collection exactly as before. Filtering only hides
   cards; it never moves one, so the collection's fair, stable order is kept. Choices live in the address
   (?price=…&size=…&artist=…&county=…) so a refined view can be shared; values the page does not offer are ignored.
   Nothing is stored and nothing is tracked.

   "Available to hire" follows exactly the rule the artists' galleries use (plotart.js): a work counts only if it is
   BOTH in the Art for Hire page's founder-approved catalogue AND named by the live check /v1/hire-listed within its
   validity window. Any failure, a stale answer, Art for Hire not being open, or no listed work on this page removes
   the choice (and its filter) again. It is never decided from this page's own markup. */
(function () {
  'use strict';
  var root = document.querySelector('[data-rf]'), grid = document.querySelector('.pa-coll-grid');
  if (!root || !grid || !window.URLSearchParams || !document.querySelectorAll) return;
  var cards = [].slice.call(grid.querySelectorAll('.pa-coll-work'));
  var count = document.querySelector('[data-rf-count]'), none = document.querySelector('[data-rf-none]');
  var openBtn = root.querySelector('.pa-rf-open'), sheet = root.querySelector('.pa-rf-sheet');
  var hireBox = root.querySelector('[data-rf-hire]'), hireInput = hireBox && hireBox.querySelector('input');
  var original = count ? count.textContent : '';
  var TOTAL = cards.length, mobile = window.matchMedia ? window.matchMedia('(max-width:760px)') : { matches: false };
  var hireLive = null, hireTimer = null, wantHire = false;

  // fail safe: put the page back to the full collection and hide the controls
  function failSafe() {
    try {
      cards.forEach(function (c) { c.removeAttribute('data-rf-out'); });
      if (count) count.textContent = original;
      if (none) none.hidden = true;
      root.hidden = true; root.classList.remove('is-open'); setInert(false); document.body.style.overflow = '';
    } catch (e) { /* nothing more can be done */ }
  }
  function guard(fn) { return function () { try { return fn.apply(this, arguments); } catch (e) { failSafe(); } }; }

  function chosen(name) {
    return [].slice.call(root.querySelectorAll('input[name="' + name + '"]:checked')).map(function (i) { return i.value; });
  }
  // half-open bands "lo-hi" (lo <= v < hi) and "lo-" (lo <= v); a price on request matches no price band
  function inBands(v, bands) {
    if (!bands.length) return true;
    if (v === 'request' || v === undefined || v === '') return false;
    var n = parseFloat(v);
    if (!isFinite(n)) return false;
    return bands.some(function (b) { var p = b.split('-'); return n >= +p[0] && (p[1] === '' || n < +p[1]); });
  }
  var apply = guard(function (fromUser) {
    var price = chosen('price'), size = chosen('size'), artist = chosen('artist'), county = chosen('county');
    var hire = !!hireLive && !!hireInput && hireInput.checked;
    var shown = 0, who = {};
    cards.forEach(function (c) {
      var d = c.dataset;
      var ok = inBands(d.price, price) && inBands(d.long, size) &&
        (!artist.length || artist.indexOf(d.artist) !== -1) &&
        (!county.length || (!!d.county && county.indexOf(d.county) !== -1)) &&
        (!hire || hireLive[d.work] === true);
      if (ok) { c.removeAttribute('data-rf-out'); shown++; who[d.artist] = 1; } else c.setAttribute('data-rf-out', '');
    });
    var artists = Object.keys(who).length, active = price.length + size.length + artist.length + county.length + (hire ? 1 : 0);
    count.textContent = active ? shown + ' of ' + TOTAL + ' works' + (shown ? ' · ' + artists + (artists === 1 ? ' artist' : ' artists') : '') : original;
    none.hidden = shown !== 0;
    root.querySelectorAll('[data-rf-n]').forEach(function (e) { e.textContent = shown; });
    root.querySelectorAll('[data-rf-word]').forEach(function (e) { e.textContent = shown === 1 ? 'work' : 'works'; });
    var badge = root.querySelector('[data-rf-badge]');
    badge.textContent = active ? String(active) : '';
    openBtn.setAttribute('aria-label', active ? 'Refine, ' + active + ' chosen' : 'Refine');
    root.querySelectorAll('.pa-rf-clear--line').forEach(function (b) { b.hidden = !active; });
    root.querySelectorAll('[data-rf-group]').forEach(function (g) {
      var labels = [].slice.call(g.querySelectorAll('input:checked')).map(function (i) { return i.nextElementSibling.textContent; });
      g.querySelector('[data-rf-val]').textContent = labels.length === 0 ? '' : labels.length === 1 ? labels[0] : labels.length + ' chosen';
    });
    if (fromUser && window.history && history.replaceState) {
      var q = new URLSearchParams();
      [['price', price], ['size', size], ['artist', artist], ['county', county]].forEach(function (p) { if (p[1].length) q.set(p[0], p[1].join(',')); });
      if (hire) q.set('hire', '1');
      var s = q.toString();
      history.replaceState(history.state, '', location.pathname + (s ? '?' + s : '') + location.hash);
    }
  });

  // ---- open and close: desktop menus, the phone sheet ------------------------------------------------------------
  function popOf(t) { return document.getElementById(t.getAttribute('aria-controls')); }
  function setOpen(t, open) { t.setAttribute('aria-expanded', String(open)); popOf(t).hidden = !open; }
  function closeMenus(except) {
    root.querySelectorAll('.pa-rf-trig').forEach(function (t) { if (t !== except && t.getAttribute('aria-expanded') === 'true') setOpen(t, false); });
  }
  // while the sheet is open, everything else on the page is inert (no tab stops, no clicks, hidden from readers)
  function setInert(on) {
    var outside = [document.querySelector('.pa-head'), document.querySelector('.pa-foot'), document.querySelector('.pa-coll-hero'),
      document.querySelector('.pa-coll-more'), grid, count, none, document.querySelector('.pa-skip')];
    outside.forEach(function (el) { if (!el) return; if (on) el.setAttribute('inert', ''); else el.removeAttribute('inert'); });
  }
  function sheetOpen() {
    root.classList.add('is-open'); openBtn.setAttribute('aria-expanded', 'true'); setInert(true);
    document.body.style.overflow = 'hidden';
    var t = root.querySelector('.pa-rf-sheet-t'); if (t) t.focus();
  }
  function sheetClose(returnFocus) {
    if (!root.classList.contains('is-open')) return;
    root.classList.remove('is-open'); openBtn.setAttribute('aria-expanded', 'false'); setInert(false);
    document.body.style.overflow = '';
    if (returnFocus !== false) openBtn.focus();
  }
  function clearAll() {
    root.querySelectorAll('input:checked').forEach(function (i) { i.checked = false; });
    apply(true);
  }

  root.addEventListener('click', guard(function (e) {
    var t = e.target.closest('.pa-rf-trig');
    if (t) { var open = t.getAttribute('aria-expanded') !== 'true'; if (!mobile.matches) closeMenus(t); setOpen(t, open); return; }
    if (e.target.closest('.pa-rf-open')) { sheetOpen(); return; }
    if (e.target.closest('[data-rf-close]')) { sheetClose(); return; }
    if (e.target.closest('[data-rf-clear]')) { clearAll(); }
  }));
  if (none) none.addEventListener('click', guard(function (e) { if (e.target.closest('[data-rf-clear]')) clearAll(); }));
  root.addEventListener('change', function () { apply(true); });
  // a desktop menu closes when you click elsewhere or tab out of it
  document.addEventListener('click', guard(function (e) { if (!mobile.matches && !e.target.closest('[data-rf]')) closeMenus(); }));
  root.addEventListener('focusout', guard(function (e) {
    if (mobile.matches) return;
    var g = e.target.closest('[data-rf-group]');
    if (g && !(e.relatedTarget && g.contains(e.relatedTarget))) { var t = g.querySelector('.pa-rf-trig'); if (t && t.getAttribute('aria-expanded') === 'true') setOpen(t, false); }
  }));
  // Escape: closes the open menu (focus back to its button), or the sheet (focus back to "Refine")
  document.addEventListener('keydown', guard(function (e) {
    if (e.key !== 'Escape' && e.key !== 'Esc') return;
    if (root.classList.contains('is-open')) { sheetClose(); return; }
    var t = root.querySelector('.pa-rf-trig[aria-expanded="true"]');
    if (t) { setOpen(t, false); t.focus(); }
  }));
  if (mobile.addEventListener) mobile.addEventListener('change', guard(function () { closeMenus(); sheetClose(false); }));

  // ---- Available to hire: the live, fail-closed check -------------------------------------------------------------
  function hireOff() {
    hireLive = null; clearTimeout(hireTimer);
    if (hireBox) { hireBox.hidden = true; if (hireInput) hireInput.checked = false; }
    apply(false);
  }
  function timed(url, opts) {
    var c = new AbortController(), t = setTimeout(function () { c.abort(); }, 6000);
    opts.signal = c.signal;
    return fetch(url, opts).then(function (r) { clearTimeout(t); return r; }, function (e) { clearTimeout(t); throw e; });
  }
  function hireCheck(api, catalogue) {
    timed(api + '/v1/hire-listed', { credentials: 'omit', cache: 'no-store' })
      .then(function (r) { return r.json().then(function (j) { return [r, j]; }); })
      .then(guard(function (rj) {
        var r = rj[0], j = rj[1], until = Date.parse(j && j.valid_until);
        if (!r.ok || !j || j.ok !== true || j.open !== true || !Array.isArray(j.items) || !(until > Date.now())) return hireOff();
        var live = {}, any = false;
        j.items.forEach(function (i) { if (i && typeof i.id === 'string' && catalogue[i.id]) live[i.id] = true; });
        cards.forEach(function (c) { if (live[c.dataset.work]) any = true; });
        if (!any) return hireOff();
        hireLive = live; hireBox.hidden = false;
        if (wantHire) { hireInput.checked = true; wantHire = false; }
        apply(false);
        clearTimeout(hireTimer);
        hireTimer = setTimeout(function () { hireCheck(api, catalogue); }, Math.max(30000, until - Date.now()));
      }))
      .catch(hireOff);
  }
  function hireStart() {
    if (!hireBox || !hireInput || !window.fetch || !window.DOMParser || !window.AbortController) return;
    timed('../art-for-hire/', { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error('hire page'); return r.text(); })
      .then(guard(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html'), catalogue = {}, n = 0;
        doc.querySelectorAll('[data-hire-work]').forEach(function (c) { catalogue[c.getAttribute('data-hire-work')] = true; n++; });
        if (!n) return;
        var s = doc.querySelector('script[src$="hire-live.js"][data-api]');
        var api = s && s.getAttribute('data-api');
        if (!api || !/^https:\/\/[a-z0-9.-]+$/.test(api)) return;
        hireCheck(api, catalogue);
      }))
      .catch(function () {});
  }

  // ---- start: choices from the address (only values this page offers), then show the line -----------------------
  try {
    var q = new URLSearchParams(location.search);
    ['price', 'size', 'artist', 'county'].forEach(function (k) {
      (q.get(k) || '').split(',').forEach(function (v) {
        if (!v) return;
        root.querySelectorAll('input[name="' + k + '"]').forEach(function (i) { if (i.value === v) i.checked = true; });
      });
    });
    wantHire = q.get('hire') === '1';   // honoured only once the live check confirms works on this page
    root.hidden = false;
    apply(false);
    hireStart();
  } catch (e) { failSafe(); }
})();
