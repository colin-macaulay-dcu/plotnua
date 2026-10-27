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

   OPTIONAL PER-TAB PRESENTATION (14 Oct 2026, Garden Retreat restructure)
     * availabilityNote: a tab for which PlotNua holds no per-product Irish
       availability evidence shows this one sentence instead of a count of
       zero, and drops the per-product availability marks, legend and
       filter. A tab without it renders exactly as before.
     * a product's optional fifth element is a price line the builder
       composed from the published universe; shown as text, never a link.

   PRODUCT NAVIGATION (14 Oct 2026, Garden Retreat pre-launch corrections)
     * the optional sixth element of a product carries what the BUILDER has
       already proved against the rights record: `href`/`site`, the own
       product page of the maker (only where its grant includes a link back,
       on its permitted domain), and `img`, images enumerated for that exact
       product in the rights record, each with its label and credit. This
       file composes no URL of its own and contains no address.
     * one URL read, never a write: on load and on `hashchange` the
       fragment is matched against /^#p-rec[A-Za-z0-9]{14}$/ and against the
       ids this page lists. A match opens that product's maker and points to
       the product; anything else is ignored. Nothing is stored, sent, or
       written back to the address bar.

   AUTHORISED IMAGERY ON THE DIRECTORY (16 Oct 2026, founder approval to
   build "Authorised imagery integration")
     * a maker may carry `l`, a lead image the BUILDER chose from that
       maker's own listed product images (guard G3 proves it is one of them).
       The tile shows it above the maker's name with its label and credit as
       text; the image itself is decorative there (alt="") because the same
       image is shown with its full description inside the open maker.
     * a product image's credit is a link only where the grant gives a link
       back (`creditHref`); otherwise it is plain text. Images show larger.
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
      if (T.availabilityNote) { return s + esc(T.availabilityNote); }
      if (conf === n) { return s + 'Irish availability is confirmed for all ' + n + '.'; }
      return s + 'Irish availability is confirmed for ' + conf + ' and not yet confirmed for ' +
        (n - conf) + (F.noRoute ? ', including ' + F.noRoute +
        ' with no published Irish route' : '') + '.';
    }
    function label(st) { return st === 'c' ? 'Confirmed' : st === 'r' ? 'No published Irish route' : 'Not yet confirmed'; }
    function drawer(m, id) {
      var T = TABS[tab];
      var c = m.p.filter(function (p) { return p[3] === 'c'; }).length;
      var NA = T.availabilityNote;
      var h = '<li class="mx-drawer" id="' + id + '"><h3>' + esc(m.m) + '</h3>' +
        '<p class="mx-meta">' + m.p.length + ' ' + T.nouns[m.p.length === 1 ? 0 : 1] +
        (NA ? '' : ' · Irish availability confirmed for ' + c + ' of ' + m.p.length) + '</p>' + offer(m) +
        (m.cn ? '<p class="mx-meta mx-cur">' + esc(m.cn) + '</p>' : '') + '<ul class="mx-plist' +
        (m.p.some(function (p) { return p[5] && p[5].img; }) ? ' mx-plist-img' : '') + '">';
      m.p.forEach(function (p) {
        var X = p[5] || {};
        h += '<li id="mx-p-' + esc(p[0]) + '"' + (p[0] === target ? ' class="mx-target"' : '') + '>' + (T.productLink
            ? '<a class="mx-pn" href="' + T.productLink.replace('{id}', encodeURIComponent(p[0])) + '">' + esc(p[1]) + '</a>'
            : '<span class="mx-pn-text">' + esc(p[1]) + '</span>') +
          (p[2] ? '<span class="mx-pt">' + esc(p[2]) + '</span>' : '') +
          (p[4] ? '<span class="mx-pp">' + esc(p[4]) + '</span>' : '') +
          (X.notes ? X.notes.map(function (n) { return '<span class="mx-pt mx-pnote">' + esc(n) + '</span>'; }).join('') : '') +
          (X.img ? images(X.img) : '') +
          (X.href ? '<a class="mx-ext" href="' + esc(X.href) + '" target="_blank" rel="noopener noreferrer">See it on ' +
            esc(X.site) + '<span class="mx-sr"> (the maker&rsquo;s own page, opens in a new tab)</span>&nbsp;&rarr;</a>' : '') +
          (NA ? '' : '<span class="mx-st"><span class="mx-dot mx-' + p[3] + '" aria-hidden="true"></span>' + label(p[3]) + '</span>') +
          '</li>';
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
    /* A referral code agreed with this maker (G13): shown only here, inside the
       maker's own drawer, never on a tile or in the order; always disclosed.
       Benefit first; the code is copied with one click (Copy code -> Copied!). */
    function offer(m) {
      if (!m.o) { return ''; }
      var sid = 'mx-cs-' + esc(m.o.code);
      return '<div class="mx-offer" role="group" aria-label="Your PlotNua benefit with ' + esc(m.m) + '">' +
        '<p class="mx-offer-k">Your PlotNua benefit</p>' +
        '<p class="mx-offer-h">Save ' + m.o.pct + '% with ' + esc(m.m) + '</p>' +
        '<p class="mx-offer-row"><code class="mx-code">' + esc(m.o.code) + '</code>' +
        '<button type="button" class="mx-copy" data-code="' + esc(m.o.code) + '" aria-describedby="' + sid + '">Copy code</button>' +
        '<span class="mx-sr" id="' + sid + '" aria-live="polite"></span></p>' +
        '<p class="mx-offer-how">' + esc(m.o.how) + '</p>' +
        '<a class="mx-offer-go" href="' + esc(m.o.href) + '" target="_blank" rel="noopener noreferrer">Shop ' + esc(m.m) +
        '<span class="mx-sr"> on ' + esc(m.o.site) + ', opens in a new tab. The code is not applied automatically; enter it at checkout.</span>&nbsp;&rarr;</a>' +
        '<p class="mx-offer-disc">PlotNua earns a commission on qualifying purchases. This does not affect recommendations.</p></div>';
    }
    /* One click copies the code. Uses the browser's standard copy call where the page
       is secure; otherwise a temporary selection. No permission prompt, no storage. */
    function copyCode(btn) {
      var code = btn.getAttribute('data-code'), st = root.querySelector('#' + btn.getAttribute('aria-describedby'));
      function done() {
        btn.textContent = 'Copied!'; btn.classList.add('mx-copied'); if (st) { st.textContent = 'Code ' + code + ' copied'; }
        setTimeout(function () { btn.textContent = 'Copy code'; btn.classList.remove('mx-copied'); if (st) { st.textContent = ''; } }, 2200);
      }
      function fallback() {
        var ta = document.createElement('textarea'); ta.value = code; ta.setAttribute('readonly', '');
        ta.style.position = 'fixed'; ta.style.top = '0'; ta.style.opacity = '0'; document.body.appendChild(ta);
        ta.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
        document.body.removeChild(ta); btn.focus();
        if (ok) { done(); } else if (st) { st.textContent = 'Copy failed. The code is ' + code; btn.textContent = code; }
      }
      if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(code).then(done, fallback); }
      else { fallback(); }
    }
    function images(list) {
      var h = '<span class="mx-imgs">';
      list.forEach(function (im) {
        h += '<figure class="mx-img"><img src="' + esc(im.src) + '" alt="' + esc(im.alt) + '" width="' + im.w +
          '" height="' + im.h + '" loading="lazy" decoding="async"><figcaption><span class="mx-img-kind">' +
          esc(im.label || im.kind) + '</span> ' + credit(im) + '</figcaption></figure>';
      });
      return h + '</span>';
    }
    function credit(im) {
      return im.creditHref ? '<a href="' + esc(im.creditHref) + '" target="_blank" rel="noopener noreferrer">' +
        esc(im.credit) + '</a>' : '<span class="mx-img-credit">' + esc(im.credit) + '</span>';
    }
    function lead(m) {
      if (!m.l) { return ''; }
      return '<span class="mx-lead"><img src="' + esc(m.l.src) + '" alt="" width="' + m.l.w + '" height="' + m.l.h +
        '" loading="lazy" decoding="async"></span><span class="mx-lead-cap">' + esc(m.l.label || m.l.kind) + ' · ' + esc(m.l.credit) + '</span>';
    }
    /* THE ONE URL READ. A fragment naming a product this page lists opens
       that product's maker in the first tab that lists it. */
    var target = null;
    function fromHash() {
      var m = /^#p-(rec[A-Za-z0-9]{14})$/.exec(window.location.hash || '');
      if (!m) { return false; }
      for (var i = 0; i < CFG.tabs.length; i++) {
        var t = CFG.tabs[i];
        for (var j = 0; j < t.makers.length; j++) {
          for (var k = 0; k < t.makers[j].p.length; k++) {
            if (t.makers[j].p[k][0] === m[1]) {
              target = m[1]; tab = t.key; resetDirectory(); expanded = true; open = t.makers[j].m;
              tabs.forEach(function (b) { var on = b.getAttribute('data-k') === tab;
                b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1;
                if (on) { $('mx-pane').setAttribute('aria-labelledby', b.id); } });
              render();
              var row = root.querySelector('#mx-p-' + m[1]);
              if (row && row.scrollIntoView) {
                var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                row.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
              }
              var btn = root.querySelector('.mx-maker[aria-expanded="true"]');
              if (btn) { try { btn.focus({ preventScroll: true }); } catch (e) { btn.focus(); } }
              return true;
            }
          }
        }
      }
      return false;
    }
    function render() {
      var list = TABS[tab].makers, k = counts(list), NA = TABS[tab].availabilityNote;
      $('mx-line').innerHTML = line();
      $('mx-legend').hidden = !!NA;
      $('mx-legend').innerHTML = NA ? '' :
        '<li><span class="mx-dot mx-c" aria-hidden="true"></span>All products confirmed (' + k.c + ')</li>' +
        (k.s ? '<li><span class="mx-dot mx-s" aria-hidden="true"></span>Some products confirmed (' + k.s + ')</li>' : '') +
        (k.u ? '<li><span class="mx-dot mx-u" aria-hidden="true"></span>Not yet confirmed (' + k.u + ')</li>' : '');
      $('mx-tools').hidden = !expanded;
      $('mx-top').hidden = !expanded;
      $('mx-chips').hidden = !!NA || (k.s + k.u) === 0;
      var rows = expanded ? list : ORDER[tab].slice(0, INITIAL);
      if (expanded) {
        if (q) { rows = rows.filter(function (m) { return m.m.toLowerCase().indexOf(q.toLowerCase()) !== -1; }); }
        if (NA) { /* no availability filter on this tab */ }
        else if (filter === 'c') { rows = rows.filter(function (m) { return mstate(m) !== 'u'; }); }
        if (filter === 'u') { rows = rows.filter(function (m) { return mstate(m) !== 'c'; }); }
      }
      $('mx-order').textContent = expanded
        ? 'All makers, A to Z. Choose one to see its products.'
        : 'A few of the makers PlotNua has researched, in a different random order on every visit. Makers are never ranked.';
      var h = '';
      rows.forEach(function (m, i) {
        var st = mstate(m), id = 'mx-d-' + tab + '-' + i, isOpen = open === m.m;
        h += '<li><button type="button" class="mx-maker' + (m.l ? ' mx-maker-img' : '') + '" aria-expanded="' + isOpen + '"' +
          (isOpen ? ' aria-controls="' + id + '"' : '') + ' data-m="' + esc(m.m) + '">' + lead(m) +
          (NA ? '' : '<span class="mx-dot mx-' + st + '" aria-hidden="true"></span>') +
          '<span class="mx-nm">' + esc(m.m) + (NA ? '' : '<span class="mx-sr"> — ' +
          (st === 'c' ? 'Irish availability confirmed' : st === 's' ? 'Irish availability confirmed for some products' : 'Irish availability not yet confirmed') +
          '</span>') + '</span><span class="mx-ct">' + m.p.length + ' product' + (m.p.length === 1 ? '' : 's') + '</span></button></li>';
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
    $('mx-grid').addEventListener('click', function (ev) {
      var c = ev.target.closest ? ev.target.closest('.mx-copy') : null; if (c) { copyCode(c); }
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
    fromHash();
    window.addEventListener('hashchange', fromHash);
  }

  [].forEach.call(document.querySelectorAll('[data-pn-maker-explorer]'), boot);
}());
