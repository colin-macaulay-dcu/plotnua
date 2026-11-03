/* PlotArt · Mobile Gallery · public work-in-progress release (3 Nov 2026).
   Renders the provider cards, the "Find art for your home" filter and the provider-profile template from
   mobile-gallery-data.js. Sends nothing, stores nothing, sets no cookies. No enquiry is submitted anywhere. */
(function () {
  'use strict';
  var P = window.MG_PROVIDERS || [], SERVICES = window.MG_SERVICES || [], TBC = 'Service details to be confirmed';
  var E = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var FRAMES = ['p', 'l', 's', 'l', 'p', 's'];
  var participating = function (p) { return p.status === 'participating' && p.agreement && p.agreement.evidence; };
  var svcLabel = function (id) { var s = SERVICES.filter(function (x) { return x.id === id; })[0]; return s ? s.label : id; };

  function fact(v, render) {
    if (!v) return '<dd class="mg-tbc">' + TBC + '</dd>';
    var src = v.verified === 'gallery-confirmed' ? 'Confirmed by the gallery' : 'Public source, to be confirmed by the gallery';
    return '<dd>' + render(v) + '<span class="mg-src">' + src + '</span></dd>';
  }

  /* ---- reusable provider card (Phase 1B: a gallery introduction) ------
     The top panel is a "gallery plaque": the gallery's name and verified address set like lettering on a painted
     gallery wall. Wall tones are presentation only (not gallery colours or branding). Facts appear only when a source
     exists; everything still unconfirmed is gathered into one honest line instead of four empty rows. */
  var TONES = ['moss', 'oxblood', 'slate', 'umber', 'ink', 'plaster'];
  var FIELDS = [['serviceArea', 'service area'], ['styles', 'artwork'], ['price', 'price guide'], ['services', 'home services']];
  var srcNote = function (v) { return v.verified === 'gallery-confirmed' ? 'Confirmed by the gallery' : 'Public source · to be confirmed by the gallery'; };
  function listing(a) { var s = a.length > 1 ? a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1] : a[0] || ''; return s.charAt(0).toUpperCase() + s.slice(1) + '.'; }
  function street(p) { if (!p.location) return ''; var t = p.location.text.split(',')[0]; return (t === p.location.text || t === p.location.short) ? '' : t; }
  function card(p, i, opts) {
    opts = opts || {};
    var n = String(i + 1).padStart(2, '0');
    var status = participating(p) ? 'Participating gallery' : 'Prospective Gallery — Participation Unconfirmed';
    var plaque = p.image && p.image.src && p.image.rights_ref
      ? '<img src="' + E(p.image.src) + '" alt="' + E(p.image.alt) + '" loading="lazy">'
      : '<span class="mg-plaque" aria-hidden="true"><span class="mg-plaque-name">' + E(p.name) + '</span>' +
        (street(p) ? '<span class="mg-plaque-st">' + E(street(p)) + '</span>' : '') +
        '<span class="mg-plaque-town">' + E(p.location ? p.location.short : '') + '</span></span>';
    var rows = [], pending = [], notes = [];
    FIELDS.forEach(function (f) {
      var v = p[f[0]], txt = null;
      if (v && f[0] === 'styles') txt = v.list.join(' · ');
      else if (v && f[0] === 'services') txt = v.confirmed && v.confirmed.length ? v.confirmed.map(svcLabel).join(' · ') : v.text;
      else if (v) txt = v.text;
      if (txt) { rows.push('<div><dt>' + f[1] + '</dt><dd>' + E(txt) + '</dd></div>'); notes.push(srcNote(v)); }
      else pending.push(f[1]);
    });
    var profile = p.profile
      ? '<a class="pa-btn pa-btn--ghost" href="' + E((opts.base || '') + 'gallery.html#' + p.id) + '">View gallery profile <span aria-hidden="true">→</span></a>'
      : '<span class="pa-btn pa-btn--ghost" aria-disabled="true">Profile to follow</span>';
    return '<li class="mg-card mg-tone-' + TONES[i % TONES.length] + '" data-provider="' + E(p.id) + '">' +
      '<div class="mg-card-wall"><span class="mg-card-top"><span class="mg-card-n">' + n + '</span></span>' + plaque + '</div>' +
      '<div class="mg-card-body">' +
        '<p class="mg-card-flag">' + status + '</p>' +
        '<h3 class="pa-sr">' + E(p.name) + '</h3>' +
        '<p class="mg-card-loc">' + (p.location ? E(p.location.text) : TBC) + '</p>' +
        (p.intro ? '<p class="mg-card-intro">' + E(p.intro.text) + '</p>' : '') +
        (rows.length ? '<dl class="mg-card-dl">' + rows.join('') + '</dl><p class="mg-card-srcline">' + E(notes.filter(function (x, k) { return notes.indexOf(x) === k; }).join(' · ')) + '</p>' : '') +
        (pending.length ? '<p class="mg-pending"><span class="mg-pending-k">' + TBC + '</span>' + E(listing(pending)) + '</p>' : '') +
        '<div class="mg-card-act">' + profile +
          '<span class="pa-btn pa-btn--solid" aria-disabled="true">Appointments not yet available</span></div>' +
      '</div></li>';
  }
  window.MGCard = card;

  var cards = document.getElementById('mg-cards');
  /* An open position for a gallery that may wish to join: never a gallery's name, image or details. */
  function invite(i) {
    return '<li class="mg-card mg-card--invite mg-tone-' + TONES[i % TONES.length] + '">' +
      '<div class="mg-card-wall"><span class="mg-card-top"><span class="mg-card-n">' + String(i + 1).padStart(2, '0') + '</span><span class="mg-card-status">Open to galleries</span></span>' +
      '<span class="mg-plaque" aria-hidden="true"><span class="mg-plaque-name">Your gallery</span><span class="mg-plaque-town">Anywhere in Ireland</span></span></div>' +
      '<div class="mg-card-body"><h3 class="pa-sr">A place for your gallery</h3>' +
      '<p class="mg-card-loc">Independent Irish galleries</p>' +
      '<p class="mg-card-intro">Do you offer home viewings, artwork trials or personal art consultations? This space is for a gallery that would like to take part.</p>' +
      '<div class="mg-card-act"><a class="pa-btn pa-btn--ghost" href="#for-galleries">Bring your gallery to PlotArt <span aria-hidden="true">→</span></a></div>' +
      '</div></li>';
  }
  window.MGInvite = invite;
  if (cards) cards.innerHTML = P.map(function (p, i) { return card(p, i); }).join('') +
    Array.apply(null, Array(window.MG_INVITE_SLOTS || 0)).map(function (_, k) { return invite(P.length + k); }).join('');

  /* ---- Find art for your home --------------------------------------- */
  var form = document.getElementById('mg-find');
  if (form) {
    var county = form.querySelector('#mg-county'), style = form.querySelector('#mg-style'), budget = form.querySelector('#mg-budget');
    (window.MG_COUNTIES || []).forEach(function (c) { county.insertAdjacentHTML('beforeend', '<option>' + E(c) + '</option>'); });
    (window.MG_STYLES || []).forEach(function (c) { style.insertAdjacentHTML('beforeend', '<option>' + E(c) + '</option>'); });
    (window.MG_BUDGETS || []).forEach(function (b) { budget.insertAdjacentHTML('beforeend', '<option value="' + E(b.id) + '">' + E(b.label) + '</option>'); });
    var svcBox = form.querySelector('#mg-services');
    SERVICES.forEach(function (s) {
      svcBox.insertAdjacentHTML('beforeend', '<label class="mg-chip"><input type="radio" name="service" id="mg-svc-' + E(s.id) + '" value="' + E(s.id) + '"><span>' + E(s.label) + '</span></label>');
    });
    var out = document.getElementById('mg-results'), count = document.getElementById('mg-count');
    var run = function () {
      var f = { county: county.value, style: style.value, budget: budget.value, service: (form.querySelector('input[name=service]:checked') || {}).value || '' };
      /* Only gallery-confirmed data can produce a match. Today no provider is participating, so there are none. */
      var matches = P.filter(function (p) {
        if (!participating(p)) return false;
        if (f.county && !(p.serviceArea && p.serviceArea.verified === 'gallery-confirmed' && (p.serviceArea.counties || []).indexOf(f.county) > -1)) return false;
        if (f.service && !(p.services && (p.services.confirmed || []).indexOf(f.service) > -1)) return false;
        if (f.style && !(p.styles && p.styles.verified === 'gallery-confirmed' && p.styles.list.indexOf(f.style) > -1)) return false;
        if (f.budget && !(p.price && p.price.verified === 'gallery-confirmed' && (p.price.bands || []).indexOf(f.budget) > -1)) return false;
        return true;
      });
      count.textContent = matches.length + (matches.length === 1 ? ' matching gallery' : ' matching galleries');
      if (matches.length) { out.innerHTML = '<ul class="mg-cards">' + matches.map(function (p) { return card(p, P.indexOf(p)); }).join('') + '</ul>'; return; }
      var located = f.county ? P.filter(function (p) { return p.location && (p.location.counties || []).indexOf(f.county) > -1; }) : [];
      var ask = [f.style, f.budget && (window.MG_BUDGETS.filter(function (b) { return b.id === f.budget; })[0] || {}).label, f.service && svcLabel(f.service)].filter(Boolean);
      out.innerHTML =
        '<div class="mg-empty">' +
          '<svg viewBox="0 0 120 120" fill="none" aria-hidden="true"><rect x="22" y="18" width="76" height="92" stroke="#C2BDB5" stroke-opacity=".55"/><rect x="31" y="27" width="58" height="74" stroke="#C2BDB5" stroke-opacity=".25"/><path d="M60 4v14" stroke="#C2BDB5" stroke-opacity=".4"/></svg>' +
          '<div><h4>No galleries have joined yet.</h4>' +
          '<p>Mobile Gallery is being prepared with independent Irish galleries. When a gallery confirms its services, coverage and prices, it will appear here for homes that match.</p>' +
          (ask.length ? '<p>Your choices so far: ' + E(ask.join(' · ')) + '. They will be matched only against details the galleries confirm themselves.</p>' : '') +
          '</div></div>' +
        (f.county ? '<div class="mg-located"><h4>Prospective galleries based in County ' + E(f.county) + '</h4>' +
          (located.length ? '<ul>' + located.map(function (p) { return '<li><b>' + E(p.name) + '</b><span>' + E(p.location.text) + ' · <span class="mg-unv">Prospective gallery. Participation unconfirmed.</span></span></li>'; }).join('') + '</ul>'
            : '<p class="pa-muted" style="margin:0">None of the prospective galleries is based in County ' + E(f.county) + '. A gallery’s base is not its service area, which each gallery will confirm.</p>') + '</div>' : '');
    };
    form.addEventListener('change', run);
    form.addEventListener('submit', function (e) { e.preventDefault(); run(); });
    form.addEventListener('reset', function () { setTimeout(run, 0); });
    run();
  }

  /* ---- provider-profile template (gallery.html#<id>) ----------------
     Public release (3 Nov 2026): an illustrative profile, clearly marked as unconfirmed. Facts come only from the data file; each carries a
     numbered source note. Photograph slots show where the gallery's own images would go once permission exists. */
  var prof = document.getElementById('mg-profile');
  if (prof) {
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var day = function (iso) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || ''); return m ? (+m[3]) + ' ' + MONTHS[+m[2] - 1] + ' ' + m[1] : E(iso); };
    var show = function () {
      var id = (location.hash || '').replace('#', '') || prof.getAttribute('data-default');
      var p = P.filter(function (x) { return x.id === id && x.profile; })[0];
      if (!p) { prof.innerHTML = '<div class="pa-wrap" style="padding-block:80px"><h1>Profile to follow.</h1><p class="pa-lede">This gallery’s profile hasn’t been prepared.</p><a class="mg-back" href="index.html#galleries">← Back to Mobile Gallery</a></div>'; return; }
      var i = P.indexOf(p), notes = [];
      document.title = p.name + ' | Mobile Gallery | PlotArt';
      var cite = function (v) {
        if (!v) return '';
        var key = v.source + '|' + v.checked, k = notes.indexOf(key);
        if (k < 0) { notes.push(key); k = notes.length - 1; }
        return '<sup class="mg-cite"><a href="#mg-notes" aria-label="Source note ' + (k + 1) + '">' + (k + 1) + '</a></sup>';
      };
      var tbc = '<p class="mg-tbc">' + TBC + '</p>';
      var sec = function (h, body) { return '<section class="mg-prof-sec"><h2>' + h + '</h2><div>' + body + '</div></section>'; };
      var gallerySet = function (v) { return v ? '<p>' + E(v.text) + cite(v) + '</p>' : tbc; };
      var demo = participating(p) ? '' :
        '<div class="mg-demo" role="note"><span class="mg-demo-k">Illustrative gallery profile.</span>' +
        '<span>Participation has not been confirmed. This shows how ' + E(p.name) + ' could appear on Mobile Gallery; nothing here is agreed.</span></div>';
      var slots = ['The gallery', 'A home viewing', 'A painting in place'].map(function (t) {
        return '<li><span class="mg-slot-f" aria-hidden="true"></span><span class="mg-slot-t">' + t + '</span><span class="mg-slot-s">Gallery photograph, shown only with permission</span></li>';
      }).join('');
      var body =
        sec('The gallery', p.intro ? '<p class="mg-prof-lede">' + E(p.intro.text) + cite(p.intro) + '</p>' : tbc) +
        sec('Artwork', p.styles ? '<ul class="mg-tags">' + p.styles.list.map(function (s) { return '<li>' + E(s) + '</li>'; }).join('') + '</ul><p class="mg-src" style="margin-top:10px">As described publicly' + cite(p.styles) + '</p>' : tbc) +
        sec('Price guide', gallerySet(p.price)) +
        sec('At home', (p.services && p.services.text ? '<p>' + E(p.services.text) + cite(p.services) + '</p>' : tbc) +
          '<p class="pa-muted mg-small">Any charge or deposit, how many works come, and who insures them in transit and in your home are set by the gallery. Nothing here promises a free viewing or trial.</p>') +
        sec('How appointments work', (p.appointments ? '<p>' + E(p.appointments.text) + cite(p.appointments) + '</p>' : tbc) +
          '<p class="pa-muted mg-small">If ' + E(p.name) + ' takes part, a viewing arranged through Mobile Gallery could work like this:</p><ol class="mg-mini"><li>You ask for a home viewing.</li><li>' + E(p.name) + ' contacts you to arrange a time.</li><li>The gallery visits, and handles any sale, payment and delivery.</li></ol>') +
        sec('Coverage', gallerySet(p.serviceArea)) +
        sec('Photographs', '<ul class="mg-slots">' + slots + '</ul><p class="pa-muted mg-small">No ' + E(p.name) + ' images are shown. The gallery’s own photographs would appear here only with its written permission.</p>') +
        sec('Website', (p.website ? '<p><a href="' + E(p.website) + '" rel="noopener">' + E(p.website.replace(/^https?:\/\//, '').replace(/\/$/, '')) + ' ↗</a></p>' : tbc));
      var noteList = notes.map(function (k) { var s = k.split('|'); return '<li>' + E(s[0]) + '. Checked ' + day(s[1]) + '.</li>'; }).join('');
      prof.innerHTML = demo +
        '<section class="mg-prof-hero"><div class="pa-wrap"><div>' +
          '<a class="mg-back" href="index.html#galleries">← Mobile Gallery</a>' +
          '<p class="pa-eyebrow" style="margin-top:28px">' + (participating(p) ? 'Gallery profile' : 'Illustrative gallery profile') + '</p>' +
          '<h1>' + E(p.name) + '</h1>' +
          '<div class="mg-prof-meta">' + (participating(p) ? '' : '<span class="pa-chip mg-chip-prosp">Prospective Gallery — Participation Unconfirmed</span>') +
            (p.location ? '<span class="pa-chip">' + E(p.location.text) + '</span>' : '') +
            (p.services && p.services.described && p.services.described.length ? '<span class="pa-chip">' + E(p.services.described.map(svcLabel).join(' · ')) + ' · described publicly</span>' : '') + '</div>' +
        '</div><div class="mg-card-wall mg-tone-' + TONES[i % TONES.length] + '"><span class="mg-plaque" aria-hidden="true"><span class="mg-plaque-name">' + E(p.name) + '</span>' +
          '<span class="mg-plaque-town">' + E(p.location ? p.location.short : '') + '</span></span></div></div></section>' +
        '<section class="pa-sec" style="padding-top:clamp(24px,3vw,40px)"><div class="pa-wrap mg-prof-grid"><div>' + body +
          '<section class="mg-notes" id="mg-notes"><h2>Sources</h2><ol>' + noteList + '</ol><p>Every detail above comes from a public source and has not yet been confirmed by ' + E(p.name) + '.</p></section>' +
        '</div><aside class="mg-prof-side" aria-labelledby="mg-req-h">' +
          '<h2 id="mg-req-h">Request a home viewing</h2>' +
          '<p>When Mobile Gallery opens, you’ll be able to tell a participating gallery about your room and the kind of work you love, and the gallery will arrange a time.</p>' +
          '<span class="pa-btn pa-btn--solid" aria-disabled="true">Appointments not yet available</span>' +
          '<p class="mg-small" style="color:var(--mute)">Appointments can’t yet be arranged through PlotArt. Mobile Gallery is still in development.</p>' +
          '<a class="mg-back" href="index.html#galleries">← Return to Mobile Gallery</a>' +
        '</aside></div></section>';
    };
    window.addEventListener('hashchange', show);
    show();
  }
})();
