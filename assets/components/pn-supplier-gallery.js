/* ==========================================================================
   PLOTNUA · PREMIUM SUPPLIER GALLERY · v0.1 PROTOTYPE
   Branch pass2/supplier-galleries, 30 Oct 2026. NOT IN PRODUCTION.
   --------------------------------------------------------------------------
   Progressive enhancement only. The builder emits complete, working HTML
   (carousel + full A-Z directory, both visible). Without this file a
   visitor still sees every maker. With it:
     * the featured cards are shuffled on every visit, so no fixed order
       favours anyone (same rule as the Maker Explorer). Cards marked
       data-sg-placement="sponsored" would keep their slot and their visible
       label; none exist today and the guard refuses an unlabelled one;
     * the arrows scroll one card and disable at either end;
     * "View all" reveals the A-Z directory and moves focus to its heading.
   WHAT IT NEVER DOES: no fetch, no storage, no analytics, no URL state,
   no third-party code, no autoplay.
   ========================================================================== */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function shuffle(list) {
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = list[i]; list[i] = list[j]; list[j] = t;
    }
    return list;
  }

  function init(root) {
    var track = root.querySelector('.pn-sg-track');
    var prev = root.querySelector('[data-sg-prev]');
    var next = root.querySelector('[data-sg-next]');
    var grid = root.querySelector('.pn-sg-grid-wrap');
    var toggles = root.querySelectorAll('[data-sg-all]');
    var gridHead = root.querySelector('.pn-sg-h3');
    if (!track) return;

    /* 1 · fair order: shuffle editorial slots only; sponsored slots stay put */
    var items = Array.prototype.slice.call(track.children);
    var end = track.querySelector('[data-sg-end]');
    var editorial = items.filter(function (li) { return li !== end && li.getAttribute('data-sg-placement') === 'editorial'; });
    var slots = items.map(function (li) { return li !== end && li.getAttribute('data-sg-placement') === 'editorial'; });
    var order = shuffle(editorial.slice());
    var k = 0;
    items.forEach(function (li, i) { track.appendChild(slots[i] ? order[k++] : li); });
    if (end) track.appendChild(end);
    /* re-appending can let scroll-snap settle on a later card; always open on the first */
    track.scrollLeft = 0;
    window.addEventListener('load', function () { if (track.scrollLeft < step()) track.scrollLeft = 0; update(); });
    /* only the card now in first place loads eagerly */
    Array.prototype.forEach.call(track.querySelectorAll('img'), function (img, i) {
      img.loading = i === 0 ? 'eager' : 'lazy';
      if (i === 0) img.setAttribute('fetchpriority', 'high');
    });

    /* 2 · arrows */
    function step() {
      var card = track.querySelector('li');
      if (!card) return 0;
      var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return card.getBoundingClientRect().width + gap;
    }
    function update() {
      var max = track.scrollWidth - track.clientWidth - 2;
      var overflow = max > 2;
      [prev, next].forEach(function (b) { if (b) b.hidden = !overflow; });
      if (!overflow) return;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    }
    var ticking = false;
    track.addEventListener('scroll', function () {
      if (ticking) return; ticking = true;
      requestAnimationFrame(function () { ticking = false; update(); });
    }, { passive: true });
    window.addEventListener('resize', update, { passive: true });
    function go(dir) {
      track.scrollBy({ left: dir * step(), behavior: reduce ? 'auto' : 'smooth' });
    }
    if (prev) prev.addEventListener('click', function () { go(-1); });
    if (next) next.addEventListener('click', function () { go(1); });
    update();

    /* 3 · View all: the directory is visible without JS; collapse it now */
    if (grid && toggles.length) {
      grid.hidden = true;
      Array.prototype.forEach.call(toggles, function (t) { t.setAttribute('aria-expanded', 'false'); });
      Array.prototype.forEach.call(toggles, function (t) {
        t.addEventListener('click', function () {
          var open = grid.hidden;
          grid.hidden = !open;
          Array.prototype.forEach.call(toggles, function (b) {
            b.setAttribute('aria-expanded', String(open));
            var lbl = b.querySelector('[data-sg-label]') || b;
            lbl.textContent = open ? b.getAttribute('data-sg-close') : b.getAttribute('data-sg-open');
          });
          if (open && gridHead) {
            gridHead.focus({ preventScroll: true });
            grid.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
          }
        });
      });
    }
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-pn-supplier-gallery]'), init);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
