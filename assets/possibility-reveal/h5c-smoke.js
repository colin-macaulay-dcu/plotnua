/* PlotNua Possibility Reveal · H5 · chimney smoke animation
 *
 * PUBLICATION: approved by the founder on 21 Oct 2026 as a PlotNua design decision
 * (governance/FOUNDER-DECISION-H5-SMOKE-ANIMATION-2026-10-21.md). This is NOT additional written
 * permission from TimberIN and must never be represented as one; TimberIN's written permission and its
 * scope are recorded, unchanged, in image-adaptation-licences.json (L6-TIMBERIN-TWO-PHOTOS-20261019).
 *
 * A separate animation layer over the locked picture. It reads, copies and alters NO image pixels:
 * every wisp is drawn in code (soft value-noise puffs) on a canvas placed in picture coordinates
 * inside the camera, so it follows every framing, zoom and resize exactly. The locked L6 tile,
 * including the licensed TimberIN smoke, is untouched underneath and stays as it is.
 *
 *  - runs only while "Garden Retreat" (L6) is on, the photograph is on screen and the tab is visible
 *  - never runs under prefers-reduced-motion (the still, locked smoke remains)
 *  - about 40-50 particles, at most 30 frames a second, on a small canvas: no WebGL, no filters
 *  - no fixed loop: each wisp has its own speed, size, drift and life, and a slow, irregular "breeze"
 *    (three incommensurate sine terms) moves them all, so the motion does not visibly repeat
 *  - preview switch: ?smoke=off in the address turns it off for comparison
 */
(function () {
  "use strict";
  var ROOT = document.querySelector("[data-pr-root]");
  if (!ROOT || /[?&]smoke=off/.test(location.search)) return;
  var cam = ROOT.querySelector("#pr-cam"), stage = ROOT.querySelector("#pr-stage");
  if (!cam || !stage || !document.createElement("canvas").getContext) return;
  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  var BOX = { x: 2380, y: 300, w: 372, h: 610 };      /* picture px: the air above the hot tub's chimney */
  var CAP = { x: 2566, y: 892 };                       /* the mouth under the chimney's hood (locked L6) */
  var RES = 0.75;                                      /* canvas pixels per picture pixel: smoke is soft */

  var cv = document.createElement("canvas");
  cv.className = "h5c-smoke"; cv.setAttribute("aria-hidden", "true");
  cv.width = Math.round(BOX.w * RES); cv.height = Math.round(BOX.h * RES);
  cv.style.left = BOX.x + "px"; cv.style.top = BOX.y + "px"; cv.style.width = BOX.w + "px"; cv.style.height = BOX.h + "px";
  cam.appendChild(cv);
  var ctx = cv.getContext("2d");

  /* deterministic pseudo-random numbers (so a review looks the same for everyone) */
  var seed = 20261021;
  function R() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }

  /* six soft puff sprites: value noise shaped by a radial falloff, warm off-white */
  var SPRITES = [];
  (function makeSprites() {
    for (var s = 0; s < 6; s++) {
      var N = 64, c = document.createElement("canvas"); c.width = c.height = N;
      var g = c.getContext("2d"), img = g.createImageData(N, N), d = img.data;
      var G = 7, grid = [];
      for (var i = 0; i < (G + 1) * (G + 1); i++) grid.push(R());
      var G2 = 15, grid2 = [];
      for (i = 0; i < (G2 + 1) * (G2 + 1); i++) grid2.push(R());
      var lerp = function (a, b, t) { t = t * t * (3 - 2 * t); return a + (b - a) * t; };
      var noise = function (gr, n, u, v) {
        var x = u * n, y = v * n, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0, w = n + 1;
        return lerp(lerp(gr[y0 * w + x0], gr[y0 * w + x0 + 1], fx), lerp(gr[(y0 + 1) * w + x0], gr[(y0 + 1) * w + x0 + 1], fx), fy);
      };
      for (var y = 0; y < N; y++) for (var x = 0; x < N; x++) {
        var u = x / (N - 1), v = y / (N - 1), dx = u - 0.5, dy = v - 0.5, r = Math.sqrt(dx * dx + dy * dy) * 2;
        var fall = Math.max(0, 1 - r); fall = fall * fall * (3 - 2 * fall);
        var n = 0.62 * noise(grid, G, Math.min(u, 0.999), Math.min(v, 0.999)) + 0.38 * noise(grid2, G2, Math.min(u, 0.999), Math.min(v, 0.999));
        var a = fall * Math.max(0, Math.min(1, (n - 0.18) * 1.6));
        var k = (y * N + x) * 4;
        d[k] = 238; d[k + 1] = 236; d[k + 2] = 231; d[k + 3] = Math.round(255 * a);
      }
      g.putImageData(img, 0, 0);
      SPRITES.push(c);
    }
  })();

  var parts = [], clock = 0, nextSpawn = 0;
  function spawn() {
    parts.push({
      x: CAP.x + (R() - 0.5) * 16, y: CAP.y - 2 - R() * 6,
      vx: 5 + R() * 8, vy: -(26 + R() * 14),
      r0: 8 + R() * 6, grow: 6 + R() * 5,
      life: 6 + R() * 3.5, age: 0,
      rot: R() * 6.283, vr: (R() - 0.5) * 0.35,
      a: 0.2 + R() * 0.14, sp: (R() * SPRITES.length) | 0, ph: R() * 6.283, wob: 1.5 + R() * 3
    });
  }
  function breeze(t) { return 8 * Math.sin(t * 0.131 + 1.7) + 5.5 * Math.sin(t * 0.0517 + 0.3) + 3.5 * Math.sin(t * 0.293 + 4.1); }
  function step(dt) {
    clock += dt; nextSpawn -= dt;
    while (nextSpawn <= 0) { spawn(); nextSpawn += 0.09 + R() * 0.2; }   /* ~6-7 wisps a second, irregular */
    var w = breeze(clock);
    for (var i = parts.length - 1; i >= 0; i--) {
      var p = parts[i]; p.age += dt;
      if (p.age >= p.life) { parts.splice(i, 1); continue; }
      var k = p.age / p.life;
      p.x += (p.vx + w * (0.25 + 0.75 * k) + Math.sin(p.ph + p.age * 0.9) * p.wob) * dt;
      p.y += p.vy * (1 - 0.35 * k) * dt;
      p.rot += p.vr * dt;
    }
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i], k = p.age / p.life;
      var fadeIn = Math.min(1, p.age / 0.9), alpha = p.a * fadeIn * Math.pow(1 - k, 1.5);
      if (alpha < 0.004) continue;
      var r = (p.r0 + p.grow * p.age) * RES, cx = (p.x - BOX.x) * RES, cy = (p.y - BOX.y) * RES;
      ctx.globalAlpha = alpha;
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(p.rot);
      ctx.drawImage(SPRITES[p.sp], -r, -r, r * 2, r * 2);
      ctx.restore();
    }
    ctx.globalAlpha = 1;
  }

  var running = false, raf = 0, last = 0, inView = true;
  function want() {
    var g = ROOT.getAttribute("data-garden") || "";
    return (" " + g + " ").indexOf(" L6 ") >= 0 && ROOT.getAttribute("data-mode") === "entry" &&
      inView && document.visibilityState === "visible" && !mqReduce.matches;
  }
  function frame(ts) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    if (ts - last < 32) return;                         /* at most ~30 frames a second */
    var dt = Math.min(0.1, (ts - last) / 1000); last = ts;
    step(dt); draw();
  }
  function sync() {
    var w = want();
    if (w && !running) {
      if (!parts.length) for (var i = 0; i < 120; i++) step(1 / 15);   /* pre-warm: the plume is already there */
      running = true; last = performance.now(); cv.classList.add("run"); raf = requestAnimationFrame(frame);
    } else if (!w && running) {
      running = false; cancelAnimationFrame(raf);
      if (mqReduce.matches) { cv.classList.remove("run"); ctx.clearRect(0, 0, cv.width, cv.height); }
    }
    if (!(" " + (ROOT.getAttribute("data-garden") || "") + " ").match(/ L6 /)) cv.classList.remove("run");
  }
  new MutationObserver(sync).observe(ROOT, { attributes: true, attributeFilter: ["data-garden", "data-mode"] });
  document.addEventListener("visibilitychange", sync);
  if (mqReduce.addEventListener) mqReduce.addEventListener("change", sync);
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { inView = en[0].isIntersecting; sync(); }).observe(stage);
  sync();
  window.PN_H5_SMOKE = { running: function () { return running; }, particles: function () { return parts.length; } };   /* automated checks only */
})();
