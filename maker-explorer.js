/* ==========================================================================
   PLOTNUA MAKER EXPLORER · SHARED COMPONENT v1
   ==========================================================================
   PINNED by atlas-tools/build-maker-explorer.py (sha256). The builder
   refuses to build any page while this file differs from the pinned hash,
   so a change here is always a deliberate, re-pinned decision.

   ONE IMPLEMENTATION, PER-DISCOVERY CONFIGURATION. A Discovery that carries
   the explorer has, inside section#explore-makers[data-pn-maker-explorer]:
     * the explorer markup emitted by the builder, and
     * <script type="application/json" class="pn-mx-config">, also emitted by
       the builder, holding the tabs, their published products and counts.
   This file reads that configuration and nothing else.

   WHAT IT NEVER DOES
     no fetch, no storage, no analytics, no URL state, no external link, no
     ranking. Initial makers are shuffled on every visit so no fixed order can
     favour anyone; the full directory is A to Z as the builder emitted it.
     Product links are composed ONLY from a tab's configured productLink
     template, which the builder permits only for a source whose products
     have a PlotNua product page (guard G3).
   ========================================================================== */
(function () {
  'use strict';

  function boot(root) {
    var raw = root.querySelector('script.pn-mx-config');
    if (!raw) { return; }
    var CFG = JSON.parse(raw.textContent), INITIAL = CFG.initial || 6;
    var TABS = {};
    CFG.tabs.forEach(function (t) { TABS[t.key] = t; });
    var $ = function (id) { return root.querySelector('#' + id); };
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
    function mstate(m) { var c = m.p.filter(function (p) { return p[3] === 'c'; }).length;
      return c === m.p.length ? 'c' : (c ? 's' : 'u'); }
    function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
    var ORDER = {};
    CFG.tabs.forEach(function (t) { ORDER[t.key] = shuffle(t.makers); });
    var tab = CFG.tabs[0].key, expanded = false, open = null, filter = 'all', q = '';

    function counts(list) {
      var o = { c: 0, s: 0, u: 0 }; list.forEach(function (m) { o[mstate(m)]++; }); return o;
    }
    function line() {
      var T = TABS[tab], F = T.figures, n = F.products, conf = F.confirmed;
      var s = '<strong>' + n + ' ' + T.nouns[n === 1 ? 0 : 1] + '</strong> from <strong>' + F.makers +
        (F.makers === 1 ? ' maker' : ' makers') + '</strong>. ';
      if (conf === n) { return s + 'Irish availability is confirmed for all ' + n + '.'; }
      return s + 'Irish availability is confirmed for ' + conf + ' and not yet confirmed for ' +
        (n - conf) + (F.noRoute ? ', including ' + F.noRoute +
        ' with no published Irish route' : '') + '.';
    }
    function label(st) { return st === 'c' ? 'Confirmed' : st === 'r' ? 'No published Irish route' : 'Not yet confirmed'; }
    function drawer(m, id) {
      var T = TABS[tab];
      var c = m.p.filter(function (p) { return p[3] === 'c'; }).length;
      var h = '<li class="mx-drawer" id="' + id + '"><h3>' + esc(m.m) + '</h3>' +
        '<p class="mx-meta">' + m.p.length + ' ' + T.nouns[m.p.length === 1 ? 0 : 1] +
        ' · Irish availability confirmed for ' + c + ' of ' + m.p.length + '</p><ul class="mx-plist">';
      m.p.forEach(function (p) {
        h += '<li>' + (T.productLink
            ? '<a class="mx-pn" href="' + T.productLink.replace('{id}', encodeURIComponent(p[0])) + '">' + esc(p[1]) + '</a>'
            : '<span class="mx-pn-text">' + esc(p[1]) + '</span>') +
          (p[2] ? '<span class="mx-pt">' + esc(p[2]) + '</span>' : '') +
          '<span class="mx-st"><span class="mx-dot mx-' + p[3] + '" aria-hidden="true"></span>' + label(p[3]) + '</span></li>';
      });
      h += '</ul>';
      /* A tab whose products have no PlotNua product page carries a route to
         the existing PlotNua journey where they are shown instead. */
      if (T.route) {
        h += '<p class="mx-meta mx-route-note">' + esc(T.route.note) + '</p>' +
             '<a class="mx-route" href="' + T.route.href + '">' + esc(T.route.label) + '&nbsp;&rarr;</a>';
      }
      return h + '</li>';
    }
    function render() {
      var list = TABS[tab].makers, k = counts(list);
      $('mx-line').innerHTML = line();
      $('mx-legend').innerHTML =
        '<li><span class="mx-dot mx-c" aria-hidden="true"></span>All products confirmed (' + k.c + ')</li>' +
        (k.s ? '<li><span class="mx-dot mx-s" aria-hidden="true"></span>Some products confirmed (' + k.s + ')</li>' : '') +
        (k.u ? '<li><span class="mx-dot mx-u" aria-hidden="true"></span>Not yet confirmed (' + k.u + ')</li>' : '');
      $('mx-tools').hidden = !expanded;
      $('mx-top').hidden = !expanded;
      $('mx-chips').hidden = (k.s + k.u) === 0;
      var rows = expanded ? list : ORDER[tab].slice(0, INITIAL);
      if (expanded) {
        if (q) { rows = rows.filter(function (m) { return m.m.toLowerCase().indexOf(q.toLowerCase()) !== -1; }); }
        if (filter === 'c') { rows = rows.filter(function (m) { return mstate(m) !== 'u'; }); }
        if (filter === 'u') { rows = rows.filter(function (m) { return mstate(m) !== 'c'; }); }
      }
      $('mx-order').textContent = expanded
        ? 'All makers, A to Z. Choose one to see its products.'
        : 'A few of the makers PlotNua has researched, in a different random order on every visit. Makers are never ranked.';
      var h = '';
      rows.forEach(function (m, i) {
        var st = mstate(m), id = 'mx-d-' + tab + '-' + i, isOpen = open === m.m;
        h += '<li><button type="button" class="mx-maker" aria-expanded="' + isOpen + '"' +
          (isOpen ? ' aria-controls="' + id + '"' : '') + ' data-m="' + esc(m.m) + '">' +
          '<span class="mx-dot mx-' + st + '" aria-hidden="true"></span>' +
          '<span class="mx-nm">' + esc(m.m) + '<span class="mx-sr"> — ' +
          (st === 'c' ? 'Irish availability confirmed' : st === 's' ? 'Irish availability confirmed for some products' : 'Irish availability not yet confirmed') +
          '</span></span><span class="mx-ct">' + m.p.length + ' product' + (m.p.length === 1 ? '' : 's') + '</span></button></li>';
        if (isOpen) { h += drawer(m, id); }
      });
      if (!rows.length) { h = '<li class="mx-empty">No maker matches that search.</li>'; }
      $('mx-grid').innerHTML = h;
      var total = list.length;
      $('mx-all').textContent = expanded ? 'Show fewer makers' : 'Show all ' + total + ' makers';
      $('mx-shown').textContent = (expanded ? rows.length : Math.min(INITIAL, total)) + ' of ' + total + ' shown';
      /* Nothing more to show when every maker already fits (14 Oct 2026:
         Garden Retreat lists one maker). A directory larger than INITIAL is
         unchanged. */
      $('mx-all').parentNode.style.display = total <= INITIAL ? 'none' : '';
    }
    /* Both "Show fewer makers" controls, and a tab switch, return the
       directory to its compact state: search, filter and any open maker are
       cleared. Collapsing also brings the visitor back to the explorer. */
    function resetDirectory() {
      expanded = false; open = null; q = ''; filter = 'all'; $('mx-find').value = '';
      [].forEach.call(root.querySelectorAll('.mx-chip'), function (c) {
        c.setAttribute('aria-pressed', c.getAttribute('data-f') === 'all'); });
    }
    function collapse() {
      resetDirectory(); render();
      var top = $('mx'), reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (top && top.scrollIntoView) { top.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' }); }
      var active = root.querySelector('.mx-tab[aria-selected="true"]');
      if (active) { try { active.focus({ preventScroll: true }); } catch (e) { active.focus(); } }
    }
    var tabs = [].slice.call(root.querySelectorAll('.mx-tab'));
    tabs.forEach(function (b, i) {
      b.addEventListener('click', function () {
        tab = b.getAttribute('data-k'); resetDirectory();
        tabs.forEach(function (t) { var on = t === b; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
        $('mx-pane').setAttribute('aria-labelledby', b.id);
        render();
      });
      b.addEventListener('keydown', function (ev) {
        if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') { return; }
        var step = ev.key === 'ArrowRight' ? 1 : -1;
        var other = tabs[(i + step + tabs.length) % tabs.length]; other.focus(); other.click();
      });
    });
    $('mx-grid').addEventListener('click', function (ev) {
      var b = ev.target.closest ? ev.target.closest('.mx-maker') : null; if (!b) { return; }
      var name = b.getAttribute('data-m'); open = open === name ? null : name; render();
      var again = root.querySelector('.mx-maker[data-m="' + name.replace(/"/g, '\\"') + '"]');
      if (again) { again.focus(); }
    });
    $('mx-all').addEventListener('click', function () {
      if (expanded) { collapse(); return; }
      expanded = true; open = null; render(); $('mx-find').focus();
    });
    $('mx-less-top').addEventListener('click', collapse);
    $('mx-find').addEventListener('input', function (ev) { q = ev.target.value.trim(); open = null; render(); });
    [].forEach.call(root.querySelectorAll('.mx-chip'), function (c) {
      c.addEventListener('click', function () {
        filter = c.getAttribute('data-f'); open = null;
        [].forEach.call(root.querySelectorAll('.mx-chip'), function (x) { x.setAttribute('aria-pressed', x === c); });
        render();
      });
    });
    render();
  }

  [].forEach.call(document.querySelectorAll('[data-pn-maker-explorer]'), boot);
}());
