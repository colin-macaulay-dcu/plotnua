/* PlotNua H6 · homepage garden component ("Discover What's Possible"), staging candidate, 25 Oct 2026.
   One shared camera container holds: the empty garden (image set v6), the floating-lettering layers (letters + shadows),
   six discovery layers (manifest z-order), the House as a Power Station scene drawings (inline SVG in image coordinates;
   nothing is baked into any image) and the discovery dot. Only that container is ever transformed, so nothing can drift.
   Every action carries a token, so a newer click cancels any older animation.
   Mounted by atlas-tools/build-h6-homepage.py and held to assets/h6/h6-record.json by its --check guard. */
(function () {
  'use strict';
  var root = document.getElementById('h6p');
  if (!root) return;
  var IW = 1677, IH = 938;
  var PAGE = 'https://plotnua.ie/discovery-house-as-power-station.html';

  /* camera windows [x0, y0, width] in image px (height follows the 1677:938 frame); dots in image px */
  var D = {
    'garden-room':     { label: 'Garden Room',     focus: [1677, 376], dot: [1236, 326], href: 'https://plotnua.ie/discovery-living-in-the-garden.html' },
    'garden-retreat':  { label: 'Garden Retreat',  focus: [1677, 709], dot: [1572, 376], href: 'https://plotnua.ie/discovery-garden-retreat.html' },
    'borrowed-garden': { label: 'Borrowed Garden', focus: [0, 770],    dot: [206, 468],  href: 'https://plotnua.ie/discovery-the-borrowed-garden.html' },
    'treehouse':       { label: 'Treehouse',       focus: [0, 0],      dot: [236, 128],  href: 'https://plotnua.ie/discovery-above-and-beyond.html' },
    'wildlife-pond':   { label: 'Wildlife Pond',   focus: [1439, 938], dot: null,        href: null },   /* no Discovery page yet: no dot, no route */
    'power-station':   { label: 'House as a Power Station', focus: [0, 0], dot: [600, 163], href: PAGE }
  };
  var S = {   /* the eight scenes, in the approved order; wording from the Discovery page; anchors exist on that page.
                 legend: [swatch, words]; status: [kind, words] pills; play: ms each scene holds during Play all */
    sun:     { label: 'Sun',       chip: 'Today', head: 'The one position almost every house already has.', text: 'Panels turn daylight into electricity the house uses as it is made.', a: '#anat-roof',
               desk: [220, 60, 820],  mob: [300, 90, 520], legend: [['e', 'electricity from the panels into the home']], play: 6500 },
    store:   { label: 'Store',     chip: 'Today', head: 'A battery doesn’t make electricity. It moves it through time.', text: 'It holds the afternoon until the evening: the battery charges from the roof by day, and the house uses what was stored after dark.', a: '#anat-battery',
               desk: [0, 80, 900],    mob: [30, 170, 450], legend: [['e', 'electricity'], ['b', 'battery level']], play: 8500 },
    charge:  { label: 'Charge',    chip: 'Today — charging', head: 'Electricity made at home can charge your car.', text: 'Charging at home needs somewhere off-street to park. Two-way charging is being worked on in Ireland.', a: '#anat-driveway',
               desk: [0, 0, 1198],    mob: [40, 150, 645], play: 6500 },
    grid:    { label: 'Grid',      chip: 'Today', head: 'The position nobody thinks of as part of the house.', text: 'A smart meter makes the house visible to the grid: a two-way connection. Every supplier must pay for eligible electricity you export, once ESB Networks has processed your connection.', a: '#anat-grid',
               desk: [0, 80, 900],    mob: [30, 145, 450], legend: [['e', 'electricity']],
               phases: [[0, 'Day', ['Home', 'Smart meter', 'Grid']], [4900, 'Evening', ['Grid', 'Smart meter', 'Home']]], play: 9500 },
    air:     { label: 'Air Heat',  chip: 'Today', head: 'The air outside can help heat the home inside.', text: 'An air-source heat pump uses electricity, some of it from your own roof, to draw heat out of the outdoor air, even on a cold February day, and move it indoors.', a: '#anat-air',
               desk: [379, 107, 762], mob: [520, 160, 559], legend: [['e', 'electricity from the roof'], ['a', 'outside air drawn in'], ['h', 'heat into the home']], play: 6500 },
    ground:  { label: 'Ground',    chip: 'Today', head: 'The ground can do more than heat a house.', text: 'Ground-source heating offers another way to heat your home, using energy stored beneath the garden rather than warmth from the outdoor air.', a: '#anat-ground',
               desk: [380, 345, 1050], mob: [430, 300, 960], legend: [['p', 'pipes in shallow trenches beneath the lawn'], ['h', 'heat into the home']],
               status: [['alt', 'An alternative to Air Heat: one or the other, not both']], play: 7500 },
    wind:    { label: 'Wind',      chip: 'Concept · needs a site assessment', concept: true, head: 'Could the roof catch the wind?', text: 'An illustration only. Ireland’s domestic planning exemption covers free-standing turbines in the garden, not turbines fixed to a house, so a rooftop turbine would need planning permission and a site-specific assessment of wind, structural loading, vibration and noise.', a: '#anat-garden',
               desk: [0, 0, 1198],    mob: [340, 20, 559], play: 6500 },
    compute: { label: 'Computing', chip: 'Emerging — outside Ireland', emerging: true, head: 'There are houses today with a computer bolted to the hot water cylinder.', text: 'Emerging: a business sends computing work to a server in the home. The heat it gives off is recovered into the hot water cylinder, and the household gets the hot water. Operating in homes in Britain; not available to an Irish homeowner today.', a: '#home-compute',
               desk: [150, 60, 930],  mob: [330, 190, 440], legend: [['d', 'dashed frame: emerging, not available in Ireland']],
               seq: [[300, 'Computing work arrives'], [1300, 'The server operates'], [2400, 'Heat is recovered'], [3300, 'Water is heated']],
               status: [['today', 'Established today, at district scale: since 2023, waste heat from a data centre in Tallaght has warmed public buildings through a heat network']], play: 9000 }
  };
  var ORDER = ['sun', 'store', 'charge', 'grid', 'air', 'ground', 'wind', 'compute'];
  var T = { cam: 1100, dotIn: 250, play: 6500 };

  var $ = function (id) { return document.getElementById(id); };
  var cam = $('h6p-cam'), stage = $('h6p-stage'), dot = $('h6p-dot'), svg = $('h6p-scenes');
  var letters = [$('h6p-letter'), $('h6p-letter-shadow')], lawnText = $('h6p-lawn-text');
  var intro = $('h6p-intro'), explore = $('h6p-explore'), status = $('h6p-status');
  var btnAll = $('h6p-all'), btnClear = $('h6p-clear'), strip = $('h6p-strip'), cap = $('h6p-caption'), btnPlay = $('h6p-play');
  var sws = Array.prototype.slice.call(root.querySelectorAll('.h6p-sw'));
  var chips = Array.prototype.slice.call(root.querySelectorAll('.h6p-chip'));
  var ovs = {};
  Array.prototype.forEach.call(root.querySelectorAll('.h6p-ov'), function (im) { ovs[im.getAttribute('data-d')] = im; });
  var fix = $('h6p-retreat-patch');
  /* persistent Power Station bar */
  var psbar = $('h6p-psbar'), psbChip = $('psb-chip'), psbHead = $('psb-head'), psbNext = $('psb-next'), psbPlay = $('psb-play'), title = $('h6p-title');
  var psbChips = Array.prototype.slice.call(document.querySelectorAll('.psb-c'));
  function psbIntro() { psbChip.textContent = 'House as a Power Station'; psbChip.className = 'psb-chip is-intro'; psbHead.textContent = 'Your home could do more than consume energy. Discover how it could generate, store, share and reuse it.'; psbNext.innerHTML = 'Start: Sun <span aria-hidden="true">→</span>'; psbNext.setAttribute('data-go', 'sun'); }
  function psbScene(k) {
    var s = S[k], i = ORDER.indexOf(k), n = ORDER[i + 1];
    psbChip.textContent = s.chip; psbChip.className = 'psb-chip' + (s.concept ? ' is-concept' : s.emerging ? ' is-emerging' : '');
    psbHead.textContent = s.head;
    if (n) { psbNext.innerHTML = 'Next: ' + S[n].label + ' <span aria-hidden="true">→</span>'; psbNext.setAttribute('data-go', n); }
    else { psbNext.innerHTML = 'Start again <span aria-hidden="true">↺</span>'; psbNext.setAttribute('data-go', 'sun'); }
  }
  var psbRow = document.querySelector('.psb-chips');
  function psbFit() {   /* when space is tight, Back and Play become compact icon buttons so all eight scenes stay visible */
    psbar.classList.remove('is-compact'); var r = psbRow;
    if (r.scrollWidth > r.clientWidth + 2) psbar.classList.add('is-compact');
  }
  function psbEdges() { var r = psbRow, max = r.scrollWidth - r.clientWidth; r.classList.toggle('fade-l', r.scrollLeft > 4); r.classList.toggle('fade-r', max > 4 && r.scrollLeft < max - 4); }
  psbRow.addEventListener('scroll', psbEdges, { passive: true }); window.addEventListener('resize', function () { psbFit(); psbEdges(); });
  /* ---- mobile: one-time swipe hint + pinned bar ---- */
  var psbHint = $('psb-hint'), hintDone = false, nudging = false;
  function hintOff() { if (hintDone) return; hintDone = true; nudging = false; psbHint.classList.remove('is-on'); setTimeout(function () { psbHint.hidden = true; }, 420); }
  function hintOn() {
    if (hintDone || !phone() || psbRow.scrollWidth <= psbRow.clientWidth + 2) return;
    psbHint.hidden = false; requestAnimationFrame(function () { psbHint.classList.add('is-on'); });
    if (!reduce.matches) {   /* one gentle nudge of the row to show it moves */
      setTimeout(function () { if (hintDone) return; nudging = true; psbRow.scrollTo({ left: 64, behavior: 'smooth' });
        setTimeout(function () { nudging = false; if (hintDone) return; psbRow.scrollTo({ left: 0, behavior: 'smooth' }); }, 750); }, 900);
    }
    setTimeout(hintOff, 6500);   /* never a permanent distraction */
  }
  /* only the visitor's own input counts (the browser's own snap scroll and the nudge do not) */
  ['pointerdown', 'touchstart', 'wheel', 'keydown'].forEach(function (ev) { psbar.addEventListener(ev, hintOff, { passive: true }); });
  function hdrSync() { var h = document.querySelector('.pn-hdr'); if (h && getComputedStyle(h).position !== 'static') root.style.setProperty('--pn-hdr-h', Math.round(h.getBoundingClientRect().height) + 'px'); }
  hdrSync(); window.addEventListener('resize', hdrSync);
  window.addEventListener('scroll', function () { if (psbar.hidden || !phone()) return; var t = psbar.getBoundingClientRect().top, h = parseFloat(getComputedStyle(root).getPropertyValue('--pn-hdr-h')) || 61; psbar.classList.toggle('is-stuck', t <= h + 1 && window.pageYOffset > 0); }, { passive: true });
  function psbShow(on) {
    if (on) { psbar.hidden = false; psbFit(); psbEdges(); requestAnimationFrame(function () { psbar.classList.add('is-on'); psbEdges(); hintOn(); }); }
    else { psbar.classList.remove('is-on'); psbar.hidden = true; }
  }
  var groups = {};
  Array.prototype.forEach.call(svg.querySelectorAll('.h6p-scene'), function (g) { groups[g.getAttribute('data-scene')] = g; });

  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var state = { active: null, scene: null, playing: false, interacted: false, letterGone: false, token: 0, timers: [], scale: 1 };
  if (reduce.matches && svg.pauseAnimations) svg.pauseAnimations();

  function later(fn, ms, tok) { state.timers.push(setTimeout(function () { if (tok === state.token) fn(); }, ms)); }
  function cancel() { state.timers.forEach(clearTimeout); state.timers = []; state.token++; return state.token; }
  function phone() { return stage.clientWidth < 700; }

  /* ---- camera: one transform on the shared container ---- */
  function camWin(win) {
    if (!win || reduce.matches) { cam.style.transform = 'none'; state.scale = 1; root.style.setProperty('--h6p-s', 1); return; }
    var s = IW / win[2];
    cam.style.transform = 'scale(' + s.toFixed(4) + ') translate(' + (-win[0] / IW * 100).toFixed(3) + '%,' + (-win[1] / IH * 100).toFixed(3) + '%)';
    state.scale = s; root.style.setProperty('--h6p-s', s.toFixed(4));
  }
  function discWin(key) {   /* stays zoomed while selected: 1.4x desktop, 1.25x phone, focal point from the approved plan */
    var s = phone() ? 1.25 : 1.4, f = D[key].focus, w = IW / s;
    return [f[0] * (1 - 1 / s), f[1] * (1 - 1 / s), w];
  }

  /* ---- discovery dot ---- */
  function dotOn(key) {
    var d = D[key];
    dot.classList.remove('is-on');
    if (!d || !d.dot || !d.href) { dot.hidden = true; return; }
    dot.href = d.href; dot.setAttribute('aria-label', 'Explore the ' + d.label + ' Discovery');
    dot.style.left = (d.dot[0] / IW * 100) + '%'; dot.style.top = (d.dot[1] / IH * 100) + '%';
    dot.hidden = false; requestAnimationFrame(function () { dot.classList.add('is-on'); });
  }
  function dotOff() { dot.classList.remove('is-on'); dot.hidden = true; }

  /* ---- overlays ---- */
  /* Layers carry data-srcset only; arming sets sizes + srcset, so the browser fetches the width it needs (same widths and
     sizes for every layer, so every layer resolves to the same candidate as the photograph and stays in register). */
  function arm(im) {
    if (im.getAttribute('srcset')) return;
    im.setAttribute('sizes', im.getAttribute('data-sizes')); im.setAttribute('srcset', im.getAttribute('data-srcset'));
  }
  var prefetched = false;
  function prefetchRest() {   /* only after the visitor's first choice, and only when the browser is idle */
    if (prefetched) return; prefetched = true;
    var go = function () { Object.keys(ovs).forEach(function (k) { arm(ovs[k]); }); arm(fix); };
    if (window.requestIdleCallback) requestIdleCallback(go, { timeout: 4000 }); else setTimeout(go, 1500);
  }
  function ensure(key) {
    var im = ovs[key];
    arm(im);
    if (key === 'garden-retreat') arm(fix);
    if (im.complete && im.naturalWidth) return Promise.resolve();
    return (im.decode ? im.decode() : new Promise(function (r) { im.addEventListener('load', r, { once: true }); })).catch(function () {});
  }
  function showOnly(keys, tok) {
    return Promise.all(keys.map(ensure)).then(function () {
      if (tok !== state.token) return;
      Object.keys(ovs).forEach(function (k) { ovs[k].classList.toggle('is-on', keys.indexOf(k) > -1); });
      fix.classList.toggle('is-on', keys.indexOf('garden-retreat') > -1 && keys.indexOf('wildlife-pond') < 0);
    });
  }

  /* ---- floating lettering: fades in on a fresh visit; once a discovery is chosen it stays away for this page session ---- */
  function lettering(on) {
    letters.forEach(function (l) { l.classList.toggle('is-off', !on); });
    lawnText.classList.toggle('is-off', !on);
  }
  function dismissLettering() { state.letterGone = true; lettering(false); }

  /* ---- guidance ---- */
  function firstInteraction() {
    if (state.interacted) return;
    state.interacted = true; root.classList.remove('is-hint');
    intro.classList.add('is-done');
    setTimeout(function () { intro.classList.add('is-gone'); cueSync(); }, reduce.matches ? 170 : 620);
    try { localStorage.setItem('h6p-seen', '1'); } catch (e) {}
  }
  function cueSync() { root.classList.toggle('cue-empty', explore.hidden && intro.classList.contains('is-gone')); }
  function setExplore(key) {
    var d = key && D[key];
    if (d && d.href) {
      explore.innerHTML = '';
      var a = document.createElement('a'); a.href = d.href; a.textContent = 'Explore the ' + d.label + ' Discovery';
      var ar = document.createElement('span'); ar.setAttribute('aria-hidden', 'true'); ar.textContent = ' →'; a.appendChild(ar);
      explore.appendChild(a); explore.hidden = false; requestAnimationFrame(function () { explore.classList.add('is-on'); });
    } else { explore.classList.remove('is-on'); explore.hidden = true; explore.innerHTML = ''; }
    cueSync();
  }
  function syncControls() {
    sws.forEach(function (b) {
      var k = b.getAttribute('data-d');
      b.setAttribute('aria-pressed', String(state.active === k));
      b.classList.toggle('is-included', state.active === 'all');
    });
    btnAll.setAttribute('aria-pressed', String(state.active === 'all'));
    root.setAttribute('data-state', state.active || 'empty');
    root.setAttribute('data-scene', state.scene || '');
    var ps = state.active === 'power-station';
    strip.hidden = !ps; strip.classList.toggle('is-on', ps);
    chips.forEach(function (c) { c.setAttribute('aria-pressed', String(state.scene === c.getAttribute('data-scene'))); });
    btnPlay.setAttribute('aria-pressed', String(state.playing));
    btnPlay.textContent = state.playing ? 'Stop' : 'Play all';
    psbChips.forEach(function (c) { c.setAttribute('aria-pressed', String(state.scene === c.getAttribute('data-scene'))); });
    psbChips.forEach(function (c) { if (state.scene === c.getAttribute('data-scene')) { var row = c.parentNode, l = c.offsetParent === row ? c.offsetLeft : c.offsetLeft - row.offsetLeft; var pad = row.scrollWidth > row.clientWidth ? 44 : 0; if (l < row.scrollLeft + pad || l + c.offsetWidth > row.scrollLeft + row.clientWidth - pad) row.scrollTo({ left: Math.max(0, l - (row.clientWidth - c.offsetWidth) / 2), behavior: reduce.matches ? 'auto' : 'smooth' }); } });
    psbPlay.setAttribute('aria-pressed', String(state.playing));
    psbPlay.innerHTML = state.playing ? '<span aria-hidden="true">■</span><span class="t"> Stop</span>' : '<span aria-hidden="true">▶</span><span class="t"> Play all</span>';
    psbPlay.setAttribute('aria-label', state.playing ? 'Stop playing scenes' : 'Play all scenes');
    title.textContent = ps ? 'Explore Your Home as a Power Station.' : 'Discover What’s Possible.';
    if (!ps) psbShow(false);
  }
  function say(t) { status.textContent = ''; setTimeout(function () { status.textContent = t; }, 30); }

  /* ---- scenes (temporary drawings, one at a time) ---- */
  function runAnims(g) {
    if (reduce.matches) {   /* reduced motion: each drawing appears complete and still (final values applied directly; phase-B pieces stay hidden) */
      if (!g._orig) g._orig = g.cloneNode(true);
      Array.prototype.forEach.call(g.querySelectorAll('animate,animateMotion,animateTransform'), function (a) {
        var el = a.parentNode, to = a.getAttribute('to');
        if (a.tagName === 'animate' && a.getAttribute('data-rm') !== 'skip' && to !== null) el.setAttribute(a.getAttribute('attributeName'), to);
        a.parentNode.removeChild(a);
      });
      return;
    }
    Array.prototype.forEach.call(g.querySelectorAll('animate,animateMotion,animateTransform'), function (a) {
      var delay = parseFloat(a.getAttribute('data-delay') || '0') * 1000;
      setTimeout(function () { if (g.classList.contains('is-on')) { try { a.beginElement(); } catch (e) {} } }, delay);
    });
  }
  function resetAnims(g) {
    if (g._orig) { var o = g._orig; o.classList.remove('is-on'); g.parentNode.replaceChild(o, g); groups[o.getAttribute('data-scene')] = o; return o; }
    Array.prototype.forEach.call(g.querySelectorAll('animate,animateMotion,animateTransform'), function (a) { try { a.endElement(); } catch (e) {} });
    /* re-arm: clone so every animation starts from its first frame next time */
    var c = g.cloneNode(true); g.parentNode.replaceChild(c, g); groups[c.getAttribute('data-scene')] = c; return c;
  }
  function sceneOff() {
    Object.keys(groups).forEach(function (k) { if (groups[k].classList.contains('is-on')) { groups[k].classList.remove('is-on'); var g = groups[k]; setTimeout(function () { if (!g.classList.contains('is-on')) resetAnims(g); }, 520); } });
    cap.classList.remove('is-on'); state.scene = null;
  }
  function fillCaption(k) {
    var s = S[k];
    cap.querySelector('.h6p-cap-chip').textContent = s.chip;
    cap.querySelector('.h6p-cap-chip').className = 'h6p-cap-chip' + (s.concept ? ' is-concept' : s.emerging ? ' is-emerging' : '');
    cap.classList.remove('is-intro');
    cap.querySelector('.h6p-cap-head').textContent = s.head;
    cap.querySelector('.h6p-cap-text').textContent = s.text;
    var a = cap.querySelector('.h6p-cap-more'); a.href = PAGE + s.a;
    var lg = cap.querySelector('.h6p-cap-legend'); lg.innerHTML = '';
    (s.legend || []).forEach(function (it) { var sp = document.createElement('span'); sp.className = 'h6p-lg h6p-lg-' + it[0]; sp.textContent = it[1]; lg.appendChild(sp); });
    lg.hidden = !s.legend;
    var st = cap.querySelector('.h6p-cap-status'); st.innerHTML = '';
    (s.status || []).forEach(function (it) { var sp = document.createElement('span'); sp.className = 'h6p-pill h6p-pill-' + it[0]; sp.textContent = it[1]; st.appendChild(sp); });
    st.hidden = !s.status;
    var sp = cap.querySelector('.h6p-cap-steps'); sp.innerHTML = ''; sp.className = 'h6p-cap-steps';
    if (s.phases) {
      sp.classList.add('is-rows');
      s.phases.forEach(function (ph, i) {
        var row = document.createElement('span'); row.className = 'sp-row' + (i === 0 ? ' is-on' : '');
        var k = document.createElement('span'); k.className = 'sp-k'; k.textContent = ph[1]; row.appendChild(k);
        var t = document.createElement('span'); t.textContent = ph[2].join(' → '); row.appendChild(t);
        sp.appendChild(row);
      });
    } else if (s.seq) {
      s.seq.forEach(function (it, i) {
        if (i) { var ar = document.createElement('span'); ar.className = 'sp-ar'; ar.setAttribute('aria-hidden', 'true'); ar.textContent = '→'; sp.appendChild(ar); }
        var e = document.createElement('span'); e.className = 'sp'; e.textContent = it[1]; sp.appendChild(e);
      });
    }
    sp.hidden = !(s.phases || s.seq);
  }
  function syncSteps(k, tok) {   /* the caption's step line follows the drawing; reduced motion shows every step at once */
    var s = S[k], sp = cap.querySelector('.h6p-cap-steps');
    if (s.seq) {
      var items = sp.querySelectorAll('.sp');
      s.seq.forEach(function (it, i) { later(function () { items[i].classList.add('is-on'); }, reduce.matches ? 0 : it[0], tok); });
    }
    if (s.phases && !reduce.matches) {
      var rows = sp.querySelectorAll('.sp-row');
      s.phases.forEach(function (ph, i) { later(function () { Array.prototype.forEach.call(rows, function (r, j) { r.classList.toggle('is-on', j === i); }); }, ph[0], tok); });
    }
    if (s.phases && reduce.matches) Array.prototype.forEach.call(sp.querySelectorAll('.sp-row'), function (r) { r.classList.add('is-on'); });
  }
  /* Power Station introduction: shown beneath the image whenever the Power Station view is open and no scene is playing */
  var INTRO = { chip: 'House as a Power Station', head: 'Your home could do more than consume energy.', text: 'Discover how it could generate, store, share and reuse it. Choose a scene below, or play them all.' };
  function showIntro(tok) {
    later(function () {
      if (state.active !== 'power-station' || state.scene) return;
      cap.classList.add('is-intro');
      cap.querySelector('.h6p-cap-chip').textContent = INTRO.chip; cap.querySelector('.h6p-cap-chip').className = 'h6p-cap-chip is-intro';
      cap.querySelector('.h6p-cap-head').textContent = INTRO.head; cap.querySelector('.h6p-cap-text').textContent = INTRO.text;
      cap.querySelector('.h6p-cap-more').href = PAGE;
      ['.h6p-cap-legend', '.h6p-cap-status', '.h6p-cap-steps'].forEach(function (q) { cap.querySelector(q).hidden = true; });
      cap.classList.add('is-on');
    }, reduce.matches ? 0 : T.cam, tok);
  }
  function reveal() {   /* if the picture is scrolled out of view when a scene starts, glide back so the scene is seen (below the sticky header) */
    var r = stage.getBoundingClientRect(), hdr = document.querySelector('.pn-hdr'), h = hdr ? hdr.getBoundingClientRect().height : 0;
    if (r.top < h - 4 || r.top > window.innerHeight * 0.45) {
      try { window.scrollTo({ top: r.top + window.pageYOffset - h - 8, behavior: reduce.matches ? 'auto' : 'smooth' }); } catch (e) { window.scrollTo(0, r.top + window.pageYOffset - h - 8); }
    }
  }
  function scene(k, tok) {
    var s = S[k]; reveal(); psbScene(k);
    if (state.active === 'power-station' && psbar.hidden) psbShow(true);   /* invariant: whenever a scene runs, its navigation is visible */
    sceneOff(); state.scene = k; syncControls(); dotOff(); explore.classList.remove('is-on');
    camWin(phone() ? s.mob : s.desk);
    later(function () {
      var g = groups[k];   /* look the drawing up now: it may have been re-armed (cloned) since the click */
      Array.prototype.forEach.call(g.querySelectorAll('image[data-href]'), function (im) { im.setAttribute('href', im.getAttribute('data-href')); im.removeAttribute('data-href'); });   /* the Ground X-ray image loads only when its scene starts */
      g.classList.add('is-on'); runAnims(g);
      fillCaption(k); syncSteps(k, tok);
      later(function () { cap.classList.add('is-on'); say(s.label + '. ' + s.head + ' ' + s.chip + '.'); }, reduce.matches ? 0 : 1500, tok);
    }, reduce.matches ? 0 : T.cam, tok);
  }
  function chooseScene(k) {
    if (state.active !== 'power-station') return;
    var tok = cancel();
    /* clicking the scene that is already showing replays it (Esc or ← Garden leave the scene) */
    state.playing = false; scene(k, tok);
  }
  function psOverview(tok) {
    sceneOff(); state.playing = false; syncControls();
    camWin(discWin('power-station')); setExplore(null);
    later(function () { dotOn('power-station'); }, reduce.matches ? 0 : T.cam + T.dotIn, tok);
    showIntro(tok); psbIntro();
  }
  function playAll() {
    if (state.active !== 'power-station') return;
    var tok = cancel();
    if (state.playing) { return psOverview(tok); }
    state.playing = true;
    var i = 0;
    (function next() {
      if (tok !== state.token) return;
      if (i >= ORDER.length) { psOverview(tok); return; }   /* returns to the whole Power Station view */
      var k = ORDER[i++]; scene(k, tok); later(next, (S[k].play || T.play) + (reduce.matches ? 0 : T.cam), tok);
    })();
  }

  /* ---- the three main actions ---- */
  function choose(key) {
    var tok = cancel(); prefetchRest();
    firstInteraction(); dismissLettering();
    if (state.active === key) { return clearAll(true); }          /* clicking the active one switches it off */
    sceneOff(); state.playing = false; dotOff();
    state.active = key; syncControls(); setExplore(key === 'power-station' ? null : key);
    say(D[key].label + ' shown in the garden.' + (key === 'power-station' ? ' Choose a scene below to see how it works.' : ''));
    showOnly([key], tok).then(function () {
      if (tok !== state.token) return;
      camWin(discWin(key));                                      /* stays zoomed while selected */
      later(function () { dotOn(key); }, reduce.matches ? 0 : T.cam + T.dotIn, tok);
      if (key === 'power-station') {
        showIntro(tok); psbIntro(); later(function () { psbShow(true); }, reduce.matches ? 0 : T.cam - 150, tok);
        later(function () { if (state.active === 'power-station' && !state.scene) scene('sun', tok); }, reduce.matches ? 0 : T.cam + 2600, tok);   /* Sun starts by itself */
      }
    });
  }
  function showAll() {
    prefetchRest();
    if (state.active === 'all') return clearAll(true);
    var tok = cancel();
    firstInteraction(); dismissLettering(); sceneOff(); state.playing = false; dotOff();
    state.active = 'all'; syncControls(); setExplore(null);
    camWin(null);
    say('All six possibilities shown in the garden.');
    showOnly(Object.keys(ovs), tok);                             /* no dots, no scenes in Show All */
  }
  function clearAll(fromToggle) {
    var tok = cancel();
    if (!fromToggle) firstInteraction();
    sceneOff(); state.playing = false; dotOff();
    state.active = null; syncControls(); setExplore(null);
    camWin(null);
    Object.keys(ovs).forEach(function (k) { ovs[k].classList.remove('is-on'); }); fix.classList.remove('is-on');
    state.letterGone = false; lettering(true);                    /* Clear All (and Back to Garden) restores the floating lettering */
    say('Garden cleared. The empty garden is shown.');
    return tok;
  }

  sws.forEach(function (b) { b.addEventListener('click', function () { choose(b.getAttribute('data-d')); }); });
  chips.forEach(function (c) { c.addEventListener('click', function () { chooseScene(c.getAttribute('data-scene')); }); });
  btnPlay.addEventListener('click', playAll);
  psbChips.forEach(function (c) { c.addEventListener('click', function () { chooseScene(c.getAttribute('data-scene')); }); });
  psbPlay.addEventListener('click', playAll);
  psbNext.addEventListener('click', function () { var k = psbNext.getAttribute('data-go'); if (state.scene === k) return; var tok = cancel(); state.playing = false; scene(k, tok); });
  $('psb-back').addEventListener('click', function () { clearAll(false); });
  btnAll.addEventListener('click', showAll);
  btnClear.addEventListener('click', function () { clearAll(false); });
  root.addEventListener('keydown', function (e) {
    if (state.active !== 'power-station') return;
    if (e.key === 'Escape' && state.scene) { e.preventDefault(); psOverview(cancel()); return; }
    if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && e.target.classList && (e.target.classList.contains('h6p-chip') || e.target.classList.contains('psb-c'))) {
      e.preventDefault();
      var i = ORDER.indexOf(e.target.getAttribute('data-scene')) + (e.key === 'ArrowRight' ? 1 : -1);
      i = (i + ORDER.length) % ORDER.length; (e.target.classList.contains('psb-c') ? psbChips : chips)[i].focus(); chooseScene(ORDER[i]);
    }
  });

  /* ---- first visit: lettering fades in, one gentle highlight across the controls ---- */
  var seen = false; try { seen = localStorage.getItem('h6p-seen') === '1'; } catch (e) {}
  if (!seen) root.classList.add('is-hint');
  requestAnimationFrame(function () { setTimeout(function () { if (!state.letterGone) lettering(true); }, reduce.matches ? 0 : 400); });
  window.addEventListener('load', function () {
    /* nothing beyond the photograph and the lettering is fetched on arrival (layers load on demand; see prefetchRest) */
  });
  syncControls();
})();
