/* ==========================================================================
   PLOTNUA · PREMIUM SUPPLIER GALLERY · v1
   Design approved by founder 30 Oct 2026. Built into pages by atlas-tools/build-supplier-gallery.py.
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
   no third-party code, no autoplay. Safe to execute more than once.
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
    /* once per gallery: consent managers (Cookiebot) may run this file a second time */
    if (root.getAttribute('data-sg-ready')) return;
    root.setAttribute('data-sg-ready', '1');
    var track = root.querySelector('.pn-sg-track');
    var prev = root.querySelector('[data-sg-prev]');
    var next = root.querySelector('[data-sg-next]');
    var grid = root.querySelector('.pn-sg-grid-wrap');
    var toggles = root.querySelectorAll('[data-sg-all]');
    var gridHead = root.querySelector('.pn-sg-h3');
    if (!track) return;

    /* 0 · in a page column: let the track run to the window's right edge */
    function bleed() {
      if (!root.parentElement || !root.parentElement.classList.contains('article')) return;
      var gap = document.documentElement.clientWidth - root.getBoundingClientRect().right;
      root.style.setProperty('--sg-bleed-r', Math.max(0, Math.round(gap)) + 'px');
    }
    bleed();
    window.addEventListener('resize', bleed, { passive: true });

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
    /* nothing here may move the track: consent managers (Cookiebot) replay 'load'
       listeners later, possibly while a visitor is scrolling */
    window.addEventListener('load', function () { update(); });
    /* images stay lazy; only if the gallery starts on or just below the screen
       does the card now in first place load eagerly (never above a page's hero) */
    var near = root.getBoundingClientRect().top < window.innerHeight * 1.25;
    Array.prototype.forEach.call(track.querySelectorAll('img'), function (img, i) {
      img.loading = (near && i === 0) ? 'eager' : 'lazy';
    });

    /* 2 · arrows */
    function step() {
      var card = track.querySelector('li');
      if (!card) return 0;
      var gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return card.getBoundingClientRect().width + gap;
    }
    function update() {
      /* trailing padding alone is not something to scroll to: arrows appear only
         when at least 48px of a card is out of view */
      var max = track.scrollWidth - track.clientWidth - 2;
      var overflow = max > 48;
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

    /* 3 · View all: the directory is a native <details> (closed by default, and
       openable by keyboard even without JS). With JS the header and end-card
       buttons drive it and its own summary is hidden. */
    if (grid && toggles.length) {
      root.classList.add('is-enhanced');
      function sync() {
        var open = grid.open;
        Array.prototype.forEach.call(toggles, function (b) {
          b.setAttribute('aria-expanded', String(open));
          var lbl = b.querySelector('[data-sg-label]') || b;
          lbl.textContent = open ? b.getAttribute('data-sg-close') : b.getAttribute('data-sg-open');
        });
      }
      sync();
      grid.addEventListener('toggle', sync);
      Array.prototype.forEach.call(toggles, function (t) {
        t.addEventListener('click', function () {
          grid.open = !grid.open;
          sync();
          if (grid.open && gridHead) {
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
