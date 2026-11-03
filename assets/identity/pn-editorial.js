/* PLOTNUA · PREMIUM EDITORIAL COMPONENTS · .pe-fold (shared, opt-in; 3 Nov 2026)
   A native <details class="pe-fold" open> whose <summary> is the short text that must always show.
   Desktop (1024 px and wider): open, and it does not collapse (the summary is kept out of the tab order,
   because its content is always on view). Phones and tablets: collapsed; the reader opens it.
   The markup ships open, so without scripting everything is on view.
   Native <details>/<summary>: keyboard (Enter/Space) and screen-reader state come from the browser. */
(function () {
  var folds = Array.prototype.slice.call(document.querySelectorAll('details.pe-fold'));
  if (!folds.length || !window.matchMedia) return;
  var narrow = window.matchMedia('(max-width:1023px)');
  function apply() {
    folds.forEach(function (d) {
      d.open = !narrow.matches;
      d.querySelector('summary').tabIndex = narrow.matches ? 0 : -1;
    });
  }
  apply();
  if (narrow.addEventListener) narrow.addEventListener('change', apply); else if (narrow.addListener) narrow.addListener(apply);
  folds.forEach(function (d) {
    d.querySelector('summary').addEventListener('click', function (e) { if (!narrow.matches) e.preventDefault(); });
  });
})();
