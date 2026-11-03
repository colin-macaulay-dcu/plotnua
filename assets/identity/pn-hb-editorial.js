/* PLOTNUA · The Hidden Bins · practical questions (founder refinement, 3 Nov 2026).
   Desktop (1024 px and wider): all nine answers stay open as cards; the cards do not collapse.
   Phones and tablets: the same nine native <details> cards, the first open, the rest collapsed.
   The markup ships with every card open, so without scripting every answer is on view.
   Native <details>/<summary>: keyboard (Enter/Space) and screen-reader state come from the browser. */
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('#practical-questions details.hb-qa'));
  if (!items.length || !window.matchMedia) return;
  var narrow = window.matchMedia('(max-width:1023px)');
  function apply() {
    items.forEach(function (d, i) {
      d.open = narrow.matches ? i === 0 : true;
      // desktop: a card, not a control -- kept out of the tab order (its content is always on view)
      d.querySelector('summary').tabIndex = narrow.matches ? 0 : -1;
    });
  }
  apply();
  if (narrow.addEventListener) narrow.addEventListener('change', apply); else if (narrow.addListener) narrow.addListener(apply);
  items.forEach(function (d) {
    d.querySelector('summary').addEventListener('click', function (e) { if (!narrow.matches) e.preventDefault(); });
  });
})();
