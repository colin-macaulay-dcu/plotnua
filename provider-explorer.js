/* ==========================================================================
   PLOTNUA PROVIDER EXPLORER · SHARED COMPONENT v1
   ==========================================================================
   PINNED by atlas-tools/build-provider-explorer.py (sha256). A change here is
   always a deliberate, re-pinned decision.

   Founder approval: 13 October 2026, The Borrowed Garden.

   Reads ONLY the <script type="application/json" class="pn-px-config">
   inside section[data-pn-provider-explorer], which the builder writes from
   borrowed-garden-provider-universe-v1.json. Styling is the Maker Explorer's
   shared stylesheet (maker-explorer.css), so the two read as one family.

   WHAT IT NEVER DOES
     no link of any kind, no fetch, no storage, no analytics, no URL state, no
     form, no ranking, no random order, no partner label. Organisations are
     listed A to Z exactly as the builder emitted them. Nothing here contacts,
     introduces or matches anybody.
   ========================================================================== */
(function () {
  'use strict';

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function boot(root) {
    var raw = root.querySelector('script.pn-px-config');
    if (!raw) { return; }
    var CFG = JSON.parse(raw.textContent);
    var $ = function (id) { return root.querySelector('#' + id); };
    var TABS = {};
    CFG.tabs.forEach(function (t) { TABS[t.key] = t; });
    var tab = CFG.tabs[0].key, open = null;

    function render() {
      var T = TABS[tab], h = '';
      $('px-line').textContent = T.note;
      T.orgs.forEach(function (o, i) {
        var id = 'px-d-' + tab + '-' + i, on = open === o.code;
        h += '<li><button type="button" class="mx-maker" aria-expanded="' + on + '"' +
          (on ? ' aria-controls="' + id + '"' : '') + ' data-o="' + esc(o.code) + '">' +
          '<span class="px-ring" aria-hidden="true"></span>' +
          '<span class="mx-nm">' + esc(o.name) + '<span class="px-kind">' + esc(o.kind) + ' · ' + esc(o.subtitle) + '</span></span>' +
          '<span class="px-status">Researched</span></button></li>';
        if (on) {
          var rows = [['What it offers', o.offers], ['Where it operates', o.where], ['How it works', o.how], ['Evidence', o.evidence]];
          h += '<li class="mx-drawer" id="' + id + '"><h3>' + esc(o.name) + '</h3><dl class="px-facts">' +
            rows.filter(function (r) { return r[1]; }).map(function (r) {
              return '<dt>' + r[0] + '</dt><dd>' + esc(r[1]) + '</dd>';
            }).join('') + '</dl><p class="px-rel">' + esc(o.relationship) + '</p></li>';
        }
      });
      $('px-grid').innerHTML = h;
    }

    var tabs = [].slice.call(root.querySelectorAll('.mx-tab'));
    tabs.forEach(function (b, i) {
      b.addEventListener('click', function () {
        tab = b.getAttribute('data-k'); open = null;
        tabs.forEach(function (t) { var on = t === b; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
        $('px-pane').setAttribute('aria-labelledby', b.id);
        render();
      });
      b.addEventListener('keydown', function (ev) {
        if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') { return; }
        var other = tabs[(i + (ev.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
        other.focus(); other.click();
      });
    });
    $('px-grid').addEventListener('click', function (ev) {
      var b = ev.target.closest ? ev.target.closest('.mx-maker') : null; if (!b) { return; }
      var code = b.getAttribute('data-o'); open = open === code ? null : code; render();
      var again = root.querySelector('.mx-maker[data-o="' + code + '"]');
      if (again) { again.focus(); }
    });
    render();
  }

  [].forEach.call(document.querySelectorAll('[data-pn-provider-explorer]'), boot);
}());
