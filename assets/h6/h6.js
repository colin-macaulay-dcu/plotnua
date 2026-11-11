/* PlotNua H6 · homepage garden component ("Discover What's Possible"), staging candidate, 25 Oct 2026.
   v7 (8 Nov 2026): daylight photographic pair. One shared camera container holds: the BEFORE photograph, six discovery
   layers (POSSIBLE pixels + mattes over BEFORE, compositing order) and one conditional layer (the Garden Room's reflection
   in the pool, shown only when both are on), the motion canvases (pool and hot-tub water, hot-tub chimney smoke, and the
   sky, whose own clouds gather into "Discover what's possible."), the House as a Power Station scene drawings (inline SVG
   in image coordinates; nothing is baked into any image) and the discovery dot. Only that container is ever transformed,
   so nothing can drift.
   Every action carries a token, so a newer click cancels any older animation.
   Mounted by atlas-tools/build-h6-homepage.py and held to assets/h6/h6-record.json by its --check guard. */
(function () {
  'use strict';
  var root = document.getElementById('h6p');
  if (!root) return;
  var IW = 1670, IH = 942;
  var PAGE = 'https://plotnua.ie/discovery-house-as-power-station.html';

  /* camera windows [x0, y0, width] in image px (height follows the 1677:938 frame); dots in image px */
  var D = {
    'garden-room':     { label: 'Garden Room',     focus: [1180, 400], dot: [1262, 352], href: 'https://plotnua.ie/discovery-living-in-the-garden.html' },
    'garden-retreat':  { label: 'Garden Retreat',  focus: [1670, 420], dot: [1440, 404], href: 'https://plotnua.ie/discovery-garden-retreat.html' },
    'borrowed-garden': { label: 'Borrowed Garden', focus: [0, 640],    dot: [196, 548],  href: 'https://plotnua.ie/discovery-the-borrowed-garden.html' },
    'treehouse':       { label: 'Treehouse',       focus: [0, 120],    dot: [226, 238],  href: 'https://plotnua.ie/discovery-above-and-beyond.html' },
    'natural-swimming-pool': { label: 'Natural Swimming Pool', focus: [1300, 942], dot: [1010, 690], href: 'https://plotnua.ie/discovery-natural-swimming-garden.html' },
    'power-station':   { label: 'House as a Power Station', focus: [520, 120], dot: [530, 184], href: PAGE }
  };
  var S = {   /* the eight scenes, in the approved order; wording from the Discovery page; anchors exist on that page.
                 legend: [swatch, words]; status: [kind, words] pills; play: ms each scene holds during Play all */
    sun:     { label: 'Sun',       chip: 'Today', head: 'The one position almost every house already has.', text: 'Panels turn daylight into electricity the house uses as it is made.', a: '#anat-roof',
               desk: [256, 56, 697],  mob: [338, 76, 442], legend: [['e', 'electricity from the panels into the home']], play: 6500 },
    store:   { label: 'Store',     chip: 'Today', head: 'A battery doesn’t make electricity. It moves it through time.', text: 'It holds the afternoon until the evening: the battery charges from the roof by day, and the house uses what was stored after dark.', a: '#anat-battery',
               desk: [380, 90, 860],  mob: [600, 180, 420], legend: [['e', 'electricity'], ['b', 'battery level']], play: 8500 },
    charge:  { label: 'Charge',    chip: 'Today — charging', head: 'Electricity made at home can charge your car.', text: 'Charging at home needs somewhere off-street to park. Two-way charging is being worked on in Ireland.', a: '#anat-driveway',
               desk: [380, 40, 960],  mob: [600, 160, 430], play: 6500 },
    grid:    { label: 'Grid',      chip: 'Today', head: 'The position nobody thinks of as part of the house.', text: 'A smart meter makes the house visible to the grid: a two-way connection. Every supplier must pay for eligible electricity you export, once ESB Networks has processed your connection.', a: '#anat-grid',
               desk: [380, 40, 960],  mob: [600, 130, 430], legend: [['e', 'electricity']],
               phases: [[0, 'Day', ['Home', 'Smart meter', 'Grid']], [4900, 'Evening', ['Grid', 'Smart meter', 'Home']]], play: 9500 },
    air:     { label: 'Air Heat',  chip: 'Today', head: 'The air outside can help heat the home inside.', text: 'An air-source heat pump uses electricity, some of it from your own roof, to draw heat out of the outdoor air, even on a cold February day, and move it indoors.', a: '#anat-air',
               desk: [330, 120, 800], mob: [520, 200, 440], legend: [['e', 'electricity from the roof'], ['a', 'outside air drawn in'], ['h', 'heat into the home']], play: 6500 },
    ground:  { label: 'Ground',    chip: 'Today', head: 'The ground can do more than heat a house.', text: 'Ground-source heating offers another way to heat your home, using energy stored beneath the garden rather than warmth from the outdoor air.', a: '#anat-ground',
               desk: [340, 350, 1050], mob: [390, 310, 960], legend: [['p', 'pipes in shallow trenches beneath the lawn'], ['h', 'heat into the home']],
               status: [['alt', 'An alternative to Air Heat: one or the other, not both']], play: 7500 },
    wind:    { label: 'Wind',      chip: 'Concept · needs a site assessment', concept: true, head: 'Could the roof catch the wind?', text: 'An illustration only. Ireland’s domestic planning exemption covers free-standing turbines in the garden, not turbines fixed to a house, so a rooftop turbine would need planning permission and a site-specific assessment of wind, structural loading, vibration and noise.', a: '#anat-garden',
               desk: [52, 0, 1198],   mob: [392, 9, 559], play: 6500 },
    compute: { label: 'Computing', chip: 'Emerging — outside Ireland', emerging: true, head: 'There are houses today with a computer bolted to the hot water cylinder.', text: 'Emerging: a business sends computing work to a server in the home. The heat it gives off is recovered into the hot water cylinder, and the household gets the hot water. Operating in homes in Britain; not available to an Irish homeowner today.', a: '#home-compute',
               desk: [270, 4, 930],   mob: [450, 135, 440], legend: [['d', 'dashed frame: emerging, not available in Ireland']],
               seq: [[300, 'Computing work arrives'], [1300, 'The server operates'], [2400, 'Heat is recovered'], [3300, 'Water is heated']],
               status: [['today', 'Established today, at district scale: since 2023, waste heat from a data centre in Tallaght has warmed public buildings through a heat network']], play: 9000 }
  };
  var ORDER = ['sun', 'store', 'charge', 'grid', 'air', 'ground', 'wind', 'compute'];
  var T = { cam: 1100, dotIn: 250, play: 6500 };

  var $ = function (id) { return document.getElementById(id); };
  var cam = $('h6p-cam'), stage = $('h6p-stage'), dot = $('h6p-dot'), svg = $('h6p-scenes');
  /* v7: the evening photograph's 3D lawn lettering is retired; the sky's own clouds form the words (FX.sky below). */
  var intro = $('h6p-intro'), explore = $('h6p-explore'), status = $('h6p-status');
  var btnAll = $('h6p-all'), btnClear = $('h6p-clear'), strip = $('h6p-strip'), cap = $('h6p-caption'), btnPlay = $('h6p-play');
  var sws = Array.prototype.slice.call(root.querySelectorAll('.h6p-sw'));
  var chips = Array.prototype.slice.call(root.querySelectorAll('.h6p-chip'));
  var ovs = {};
  Array.prototype.forEach.call(root.querySelectorAll('.h6p-ov'), function (im) { ovs[im.getAttribute('data-d')] = im; });
  var fix = $('h6p-reflection');   /* conditional: the Garden Room's reflection, only when the pool is on too */
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
  /* ---- v7 motion: pool and hot-tub water, hot-tub chimney smoke, and the sky's own clouds forming the words.
     Water and smoke exist only while their feature is shown; nothing draws while the hero is off screen, the tab is
     hidden or motion is paused; reduced motion gets still frames only (the words in the sky, the plume held still). */
  var FX = (function () {
    var V = '?v=20261109', IMG = 'assets/h6/img/H6v7-';
    var cw = $('h6p-water'), cs = $('h6p-smoke'), ck = $('h6p-sky'), btn = $('h6p-motion');
    if (!cw || !cs || !ck) return { features: function () {}, sky: function () {} };
    /* boxes in image pixels [x, y, w, h]; the canvases sit inside the camera container, so they zoom with the photograph */
    var BOX = { water: [718, 427, 954, 452], smoke: [1450, 93, 230, 210], sky: [870, 0, 640, 196] };
    var TEX = { pool: [718, 559, 954, 320], tub: [1493, 427, 157, 21] };
    function place(c, b) { c.style.left = (b[0] / IW * 100) + '%'; c.style.top = (b[1] / IH * 100) + '%'; c.style.width = (b[2] / IW * 100) + '%'; c.style.height = (b[3] / IH * 100) + '%'; }
    place(cw, BOX.water); place(cs, BOX.smoke); place(ck, BOX.sky);
    var wx = cw.getContext('2d'), sx = cs.getContext('2d'), kx = ck.getContext('2d');
    var show = { pool: false, reflect: false, tub: false, smoke: false };
    var paused = false, onScreen = true, raf = 0, clock = 0, prev = 0, lastW = 0, lastS = 0, lastK = 0;
    var img = {};
    function load(name) {
      if (img[name]) return img[name];
      var im = new Image(); im.decoding = 'async'; im.src = IMG + name + V; img[name] = im; return im;
    }
    function ready(im) { return im && im.complete && im.naturalWidth > 0; }

    /* water: the photograph's own water, re-drawn in thin rows with a gentle sideways drift (no generated texture) */
    function sizeWater() { var k = Math.min(1, (stage.clientWidth * Math.min(devicePixelRatio || 1, 2)) / IW); cw.width = Math.round(BOX.water[2] * k); cw.height = Math.round(BOX.water[3] * k); return k; }
    var wk = 0;
    function drawWater(t) {
      if (!wk || cw.width < 2) wk = sizeWater();
      wx.setTransform(wk, 0, 0, wk, 0, 0); wx.clearRect(0, 0, BOX.water[2], BOX.water[3]);
      if (show.pool) rows(load(show.reflect ? 'water-pool-reflect.webp' : 'water-pool.webp'), TEX.pool, t, 3.0, 0.9);
      if (show.tub) rows(load('water-tub.webp'), TEX.tub, t, 2.6, 1.6);
    }
    function rows(im, box, t, amp, speed) {
      if (!ready(im)) return;
      var ox = box[0] - BOX.water[0], oy = box[1] - BOX.water[1], h = box[3], sk = im.naturalHeight / h;
      for (var y = 0; y < h; y += 2) {
        var Y = box[1] + y, fade = Math.min(1, y / 10, (h - y) / 10);
        var drift = (Math.sin(Y * 0.115 - t * speed) * amp + Math.sin(Y * 0.047 + t * speed * 0.71) * amp * 0.4) * fade;
        var lift = Math.sin(Y * 0.072 + t * speed * 0.5) * 0.5;
        wx.drawImage(im, 0, Math.max(0, (y + lift) * sk), im.naturalWidth, 3 * sk, ox + drift, oy + y, box[2], 3);
      }
    }

    /* smoke: a continuous, noisy density field rising from the far-right hot-tub chimney (emitter ~1636, 303) */
    var SW = 116, SH = 105, vap = document.createElement('canvas'); vap.width = SW; vap.height = SH;
    var vc = vap.getContext('2d'), vpx = vc.createImageData(SW, SH);
    function hash(x, y) { var z = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return z - Math.floor(z); }
    function noise(x, y) { var ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy; fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
      var a = hash(ix, iy), b = hash(ix + 1, iy), d = hash(ix, iy + 1), e = hash(ix + 1, iy + 1); return (a + (b - a) * fx) * (1 - fy) + (d + (e - d) * fx) * fy; }
    function drawSmoke(t) {
      var X0 = BOX.smoke[0], Wd = BOX.smoke[2], data = vpx.data;
      for (var y = 0; y < SH; y++) {
        var p = (SH - y) / SH;
        var centre = 1636 - p * 96 + Math.sin(t * 0.45 - p * 6) * p * 16, width = 3.6 + p * 44;
        var fade = Math.pow(1 - p, 1.1) * Math.min(1, p * 18 + 0.25), breathe = 0.95 + Math.sin(t * 0.37) * 0.065;
        for (var x = 0; x < SW; x++) {
          var worldX = X0 + (x + 0.5) / SW * Wd, gx = x * 2, gy = y * 2;
          var env = Math.exp(-Math.pow((worldX - centre) / width, 2) * 1.2);
          var i = (y * SW + x) * 4;
          if (env < 0.01) { data[i + 3] = 0; continue; }
          var f = noise(gx * 0.07 + t * 0.1, gy * 0.045 + t * 0.7) * 0.57 + noise(gx * 0.15 - t * 0.12, gy * 0.1 + t * 1.3) * 0.28 + noise(gx * 0.32, gy * 0.22 + t * 2.2) * 0.15;
          var a = env * Math.max(0, (f - 0.16) * 2.05) * fade * breathe, sh = 192 + f * 38;
          data[i] = sh; data[i + 1] = sh + 5; data[i + 2] = sh + 5; data[i + 3] = Math.min(255, a * 255);
        }
      }
      vc.putImageData(vpx, 0, 0);
      if (cs.width !== SW * 2) { cs.width = SW * 2; cs.height = SH * 2; }
      sx.clearRect(0, 0, cs.width, cs.height); sx.imageSmoothingEnabled = true; sx.drawImage(vap, 0, 0, cs.width, cs.height);
    }

    /* sky: every letter is a translated piece of a real cloud from this sky (prepared offline from the BEFORE photograph);
       the frame between is a transport of the cloud material along that field with a late cross-fade into the words */
    var K = { w: 640, h: 196, src: null, tgt: null, flow: null, time: null, out: null, u: 0, dir: 0, t0: 0, from: 0, dur: 0, wanted: false };
    function pixels(name) {
      var im = load(name);
      return (im.decode ? im.decode() : new Promise(function (r) { im.onload = r; })).then(function () {
        var c = document.createElement('canvas'); c.width = K.w; c.height = K.h; var x = c.getContext('2d');
        x.drawImage(im, 0, 0, K.w, K.h); return x.getImageData(0, 0, K.w, K.h).data;
      });
    }
    var skyReady = null;
    function skyLoad() {
      if (!skyReady) skyReady = Promise.all([pixels('sky-src.webp'), pixels('sky-tgt.webp'), pixels('sky-flow.png'), pixels('sky-time.png')]).then(function (r) {
        K.src = r[0]; K.tgt = r[1]; K.flow = r[2]; K.time = r[3]; ck.width = K.w; ck.height = K.h; K.out = kx.createImageData(K.w, K.h);
      }).catch(function () { K.src = null; });
      return skyReady;
    }
    function ss(e0, e1, x) { var v = Math.max(0, Math.min(1, (x - e0) / (e1 - e0))); return v * v * (3 - 2 * v); }
    function drawSky(u, t) {
      if (!K.src) return;
      var S = K.src, T = K.tgt, F = K.flow, Q = K.time, O = K.out.data, w = K.w, h = K.h;
      var td = ss(0, 0.85, u), bump = Math.sin(Math.PI * td) * 1.2;
      for (var y = 0; y < h; y++) {
        for (var x = 0; x < w; x++) {
          var i = (y * w + x) * 4, reg = F[i + 2];
          if (reg === 0) { O[i + 3] = 0; continue; }
          var fx = F[i] - 128, fy = F[i + 1] - 128;
          var jx = Math.sin(y * 0.09 + t * 1.7 + x * 0.013) * bump, jy = Math.sin(x * 0.07 + t * 1.3) * bump * 0.6;
          var ax = x + td * fx + jx, ay = y + td * fy + jy, bx = x - (1 - td) * fx + jx, by = y - (1 - td) * fy + jy;
          var wv = ss(0, 0.45, u - Q[i] * 0.55 / 255);   /* letters condense core-first; the cloud around them thins in patches */
          for (var c = 0; c < 3; c++) O[i + c] = samp(S, ax, ay, c) * (1 - wv) + samp(T, bx, by, c) * wv;
          O[i + 3] = reg;
        }
      }
      kx.putImageData(K.out, 0, 0);
    }
    function samp(A, x, y, c) {
      var w = K.w, h = K.h;
      if (x < 0) x = 0; else if (x > w - 1.001) x = w - 1.001; if (y < 0) y = 0; else if (y > h - 1.001) y = h - 1.001;
      var x0 = x | 0, y0 = y | 0, fx = x - x0, fy = y - y0, i = (y0 * w + x0) * 4 + c, j = i + w * 4;
      return (A[i] * (1 - fx) + A[i + 4] * fx) * (1 - fy) + (A[j] * (1 - fx) + A[j + 4] * fx) * fy;
    }
    function sky(on) {
      K.wanted = on;
      skyLoad().then(function () {
        if (!K.src || K.wanted !== on) return;
        ck.classList.add('is-on');
        if (reduce.matches) { K.u = on ? 1 : 0; K.dir = 0; drawSky(K.u, 0); if (!on) ck.classList.remove('is-on'); return; }
        K.from = K.u; K.dir = on ? 1 : -1; K.dur = on ? 7000 * (1 - K.u) + 400 : 3200 * K.u + 200; K.t0 = -1; go();
      });
    }

    /* the loop: one requestAnimationFrame for everything, only when something is on, visible and not paused */
    function busy() { return show.pool || show.tub || show.smoke || K.dir !== 0; }
    function go() { if (!raf && busy() && onScreen && !document.hidden && !paused && !reduce.matches) { prev = 0; raf = requestAnimationFrame(tick); } }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    function tick(now) {
      raf = 0;
      if (!onScreen || document.hidden || paused) return;
      var dt = prev ? Math.min(0.1, (now - prev) / 1000) : 0; prev = now; clock += dt;
      if ((show.pool || show.tub) && now - lastW > 42) { drawWater(clock); lastW = now; }
      if (show.smoke && now - lastS > 42) { drawSmoke(clock); lastS = now; }
      if (K.dir !== 0 && now - lastK > 33) {
        if (K.t0 < 0) K.t0 = now - 0;
        var p = Math.min(1, (now - K.t0) / K.dur);
        K.u = K.dir > 0 ? K.from + (1 - K.from) * p : K.from * (1 - p);
        drawSky(K.u, clock); lastK = now;
        if (p >= 1) { if (K.dir < 0) { ck.classList.remove('is-on'); kx.clearRect(0, 0, K.w, K.h); } K.dir = 0; }
      }
      if (busy()) raf = requestAnimationFrame(tick);
    }
    function features(keys) {
      var pool = keys.indexOf('natural-swimming-pool') > -1, ret = keys.indexOf('garden-retreat') > -1;
      show.pool = pool; show.reflect = pool && keys.indexOf('garden-room') > -1; show.tub = ret; show.smoke = ret;
      cw.classList.toggle('is-on', pool || ret); cs.classList.toggle('is-on', ret);
      if (pool) load(show.reflect ? 'water-pool-reflect.webp' : 'water-pool.webp');
      if (ret) load('water-tub.webp');
      if (!pool && !ret) { wx.setTransform(1, 0, 0, 1, 0, 0); wx.clearRect(0, 0, cw.width, cw.height); }
      if (!ret) sx.clearRect(0, 0, cs.width, cs.height);
      if (reduce.matches) { if (ret) drawSmoke(4.0); return; }   /* still frame: the plume held still, water as photographed */
      go();
    }
    if (btn) btn.addEventListener('click', function () {
      paused = !paused; btn.setAttribute('aria-pressed', String(paused)); btn.textContent = paused ? 'Play motion' : 'Pause motion';
      if (paused) stop(); else go();
    });
    if (btn && reduce.matches) btn.hidden = true;
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { onScreen = es[0].isIntersecting; if (onScreen) go(); else stop(); }).observe(stage);
    document.addEventListener('visibilitychange', function () { if (document.hidden) stop(); else go(); });
    window.addEventListener('resize', function () { wk = 0; });
    return { features: features, sky: sky, _debug: function () { return { show: show, K: { u: K.u, dir: K.dir }, raf: !!raf, paused: paused, onScreen: onScreen }; } };
  })();

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
    if (key === 'garden-room' || key === 'natural-swimming-pool') arm(fix);
    if (im.complete && im.naturalWidth) return Promise.resolve();
    return (im.decode ? im.decode() : new Promise(function (r) { im.addEventListener('load', r, { once: true }); })).catch(function () {});
  }
  function showOnly(keys, tok) {
    return Promise.all(keys.map(ensure)).then(function () {
      if (tok !== state.token) return;
      Object.keys(ovs).forEach(function (k) { ovs[k].classList.toggle('is-on', keys.indexOf(k) > -1); });
      fix.classList.toggle('is-on', keys.indexOf('garden-room') > -1 && keys.indexOf('natural-swimming-pool') > -1);
      FX.features(keys);
    });
  }

  /* ---- the words in the sky: the clouds gather on arrival; once a discovery is chosen they drift apart again ---- */
  function lettering(on) { FX.sky(on); }
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
    /* 11 Nov 2026 fix: a scene switched off twice within the 520 ms fade (off, on, off quickly) queues two resets for
       the same group; the first replaces it, so the second found it detached (parentNode null → TypeError). A group
       that is no longer the live one for its scene has already been reset: leave it. */
    var key = g.getAttribute('data-scene');
    if (!g.parentNode || groups[key] !== g) return groups[key];
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
    Object.keys(ovs).forEach(function (k) { ovs[k].classList.remove('is-on'); }); fix.classList.remove('is-on'); FX.features([]);
    state.letterGone = false; lettering(true);                    /* Clear All (and Back to Garden) gathers the clouds into the words again */
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
  requestAnimationFrame(function () { setTimeout(function () { if (!state.letterGone) lettering(true); }, reduce.matches ? 0 : 700); });
  window.addEventListener('load', function () {
    /* nothing beyond the photograph and the lettering is fetched on arrival (layers load on demand; see prefetchRest) */
  });
  syncControls();
})();
