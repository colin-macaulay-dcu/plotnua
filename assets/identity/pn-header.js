/* PlotNua header · My Plot state (founder approval 28 Oct 2026).
   generated header companion — read-only, no storage writes, no network requests.

   The My Plot link always points at your-plot.html?myplot=1 (in the HTML), the My Plot
   view, which always opens the saved collection (an empty dashboard when nothing is
   saved) and never the Eircode / property journey. This
   script only changes how the pill LOOKS: with saved items, a filled red heart and the
   count; without, the subdued outline heart.

   The count is the same total My Plot itself shows: saved products + links the homeowner
   added, validated exactly as your-plot.html reads plotnua.myplot.v1 (duplicates collapse,
   malformed records are ignored, a schema-0 list of ids is read as saved products, a
   future schema counts as nothing). Discovery journeys are NOT counted.
   Any failure (storage blocked, private browsing, a damaged record) shows the empty state. */
(function () {
  'use strict';
  var KEY = 'plotnua.myplot.v1', SCHEMA = 1;

  function count() {
    var raw, d;
    try { raw = window.localStorage.getItem(KEY); } catch (e) { return 0; }
    if (!raw) return 0;
    try { d = JSON.parse(raw); } catch (e) { return 0; }
    if (!d || typeof d !== 'object') return 0;
    var ver = (!Array.isArray(d) && typeof d.schema === 'number') ? d.schema : 0;
    if (ver > SCHEMA) return 0;
    var saved = Array.isArray(d) ? d : (Array.isArray(d.saved) ? d.saved : []);
    var added = (!Array.isArray(d) && Array.isArray(d.added)) ? d.added : [];
    var n = 0, seen = {}, seenAdded = {}, i, r, k;
    for (i = 0; i < saved.length; i++) {
      r = saved[i];
      if (ver === 0 && typeof r === 'string') r = { productId: r };
      if (!r || typeof r !== 'object' || typeof r.productId !== 'string' || !r.productId) continue;
      if (Object.prototype.hasOwnProperty.call(seen, r.productId)) continue;
      seen[r.productId] = 1; n++;
    }
    for (i = 0; i < added.length; i++) {
      r = added[i];
      if (!r || typeof r !== 'object') continue;
      k = String(r.url || r.name || '').trim().toLowerCase();
      if (!k || Object.prototype.hasOwnProperty.call(seenAdded, k)) continue;
      seenAdded[k] = 1; n++;
    }
    return n;
  }

  function apply() {
    var n = count(), links = document.querySelectorAll('a[data-myplot]'), i, a, c;
    for (i = 0; i < links.length; i++) {
      a = links[i];
      c = a.querySelector('.pn-hdr-count');
      if (n > 0) {
        a.classList.add('is-saved');
        a.setAttribute('aria-label', 'My Plot, ' + n + (n === 1 ? ' saved item' : ' saved items'));
        if (c) { c.textContent = n > 99 ? '99+' : String(n); c.hidden = false; }
      } else {
        a.classList.remove('is-saved');
        a.setAttribute('aria-label', 'My Plot, nothing saved yet');
        if (c) { c.textContent = ''; c.hidden = true; }
      }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
  // another tab changed My Plot; or this page came back from the back/forward cache
  window.addEventListener('storage', function (e) { if (!e || e.key === KEY || e.key === null) apply(); });
  window.addEventListener('pageshow', apply);
})();
