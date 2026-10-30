/* PlotNua · phone Menu (founder approval 30 Oct 2026). Shared by PlotNua, PlotArt and GridNua.
   The Menu is a native <details data-pn-menu> disclosure: it opens and closes with or without
   this script, and the browser reports its expanded state. This script only adds the closings a
   visitor expects: Escape (focus returns to Menu), a tap or click outside, choosing a link,
   scrolling the page, and the window growing past the phone breakpoint. When it opens, focus
   moves to the first link so keyboard users land in the list. No storage, no network. */
(function () {
  'use strict';
  var menus = [].slice.call(document.querySelectorAll('details[data-pn-menu]'));
  if (!menus.length) return;
  var wide = window.matchMedia ? window.matchMedia('(min-width:721px)') : null;

  function close(d, refocus) {
    if (!d.open) return;
    d.open = false;
    if (refocus) { var s = d.querySelector('summary'); if (s) s.focus(); }
  }
  function closeAll(except) { menus.forEach(function (d) { if (d !== except) close(d, false); }); }

  menus.forEach(function (d) {
    var y0 = 0;
    d.addEventListener('toggle', function () {
      document.documentElement.classList.toggle('pn-menu-open', menus.some(function (m) { return m.open; }));
      if (!d.open) return;
      closeAll(d);
      y0 = window.scrollY;
      var first = d.querySelector('.pn-sm-panel a, .pn-hdr-panel a');
      if (first && d.__kbd) { try { first.focus({ preventScroll: true }); } catch (e) { first.focus(); } }
    });
    var sum = d.querySelector('summary');
    if (sum) {
      sum.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') d.__kbd = true; });
      sum.addEventListener('pointerdown', function () { d.__kbd = false; });
    }
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' || e.key === 'Esc') { close(d, true); } });
    d.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('a')) close(d, false); });
    window.addEventListener('scroll', function () { if (d.open && Math.abs(window.scrollY - y0) > 48) close(d, false); }, { passive: true });
  });
  document.addEventListener('pointerdown', function (e) {
    menus.forEach(function (d) { if (d.open && !d.contains(e.target)) close(d, false); });
  });
  if (wide) {
    var onWide = function () { if (wide.matches) closeAll(null); };
    if (wide.addEventListener) wide.addEventListener('change', onWide); else if (wide.addListener) wide.addListener(onWide);
  }
  window.addEventListener('pageshow', function () { closeAll(null); });
})();
