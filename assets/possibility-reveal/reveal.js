/* PlotNua Possibility Reveal · L2B v2 · homepage component (generated; do not hand-edit) */
/* PlotNua Possibility Reveal · L2B prototype · behaviour (no dependencies) */
(function () {
  "use strict";
  var D = window.PN_REVEAL;
  if (!D) return;

  var ROOT = document.querySelector("[data-pr-root]");
  if (!ROOT) return;
  var $ = function (s, r) { return (r || ROOT).querySelector(s); };
  var pn = ROOT, stage = $("#pr-stage"), cam = $("#pr-cam"), hidden = $("#pr-hidden"), lens = $("#pr-lens"), grip = $("#pr-lensGrip");
  var beaconsEl = $("#pr-beacons"), pathsEl = $("#pr-paths"), cap = $("#pr-caption"), more = $("#pr-more");
  var mqMobile = window.matchMedia("(max-width: 760px)");
  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var H5 = true, PS = false;   /* H5 Phase C: the Power Station experience (lens, tour, markers, scenes) runs only while its switch is on */
  var REVIEW = /[?&]review=1/.test(location.search);

  /* ---------- presentation config (camera framing, beacon placement, step timing) ---------- */
  var ORDER = ["ground", "wind", "compute"];
  var ENTRY_VIEW = { d: [1376, 640, 1], m: [1250, 800, 1] };   /* H5: the sky kept in view; phones see house, extension and the screened heat pump */
  var FRAME = null;   /* H3: a garden layer may re-frame the entry view (PN_REVEAL_API.frame) */
  var PS_VIEW = { d: [1376, 640, 1], m: [1000, 800, 1] };   /* H5: with Power Station on, phones frame the original view (wind, house, lawn) */
  /* H5 Phase C (framing fix, 21 Oct 2026): on wider screens the photograph is shown full width, so it
     shows only part of the picture's height. The camera now keeps EVERYTHING that is switched on in view
     (each garden layer's own area, and with Power Station the roof marker and the whole lens over the lawn),
     centred when it fits and, when it cannot all fit, favouring the lower garden (hot tub, beds, lawn).
     Phones keep their approved close framing of the last layer switched on. */
  var ZONES = { L3: [526, 1118], L4: [832, 1420], L5: [394, 724], L6: [640, 1465] };
  var entryView = function () {
    var base = FRAME || (PS ? PS_VIEW : ENTRY_VIEW);
    if (mob()) return base;
    var on = (pn.getAttribute("data-garden") || "").split(" ").filter(function (x) { return ZONES[x]; });
    if (!on.length && !PS) return base;
    var W = stage.clientWidth, H = stage.clientHeight, k = Math.max(W / 2752, H / 1536), R = H / k, a = 1e9, b = -1e9, low = false;
    on.forEach(function (id) { a = Math.min(a, ZONES[id][0]); b = Math.max(b, ZONES[id][1]); if (id === "L6" || id === "L4") low = true; });
    if (PS) { a = Math.min(a, 140); b = Math.max(b, BEACON.ground.d[1] + lensRadius() / k + 14); low = true; }
    var top = (b - a <= R) ? a - (R - (b - a)) / 2 : (low ? b - R : a);
    top = Math.max(0, Math.min(1536 - R, top));
    return { d: [base.d[0], top + 0.46 * R, 1], m: base.m, lens: base.lens };
  };
  var restAt = function () { return (FRAME && FRAME.lens) || BEACON.ground; };   /* H3: where the lens rests */
  var BEACON = { ground: { d: [2250, 1060], m: [1250, 1110] }, wind: { d: [735, 190], m: [745, 225] }, compute: { d: [1190, 690], m: [1190, 690] } };
  var SCENE = {
    ground:  { view: { d: [1700, 1080, 1.12], m: [1760, 1060, 1.0] }, steps: [1400, 2800, 4100, 5300], capPos: { d: "pos-tr", m: "m-top" } },
    wind:    { view: { d: [900, 330, 1.7],    m: [860, 330, 1.35] }, steps: [1400, 2500, 3500, 4600, 5900], capPos: { d: "", m: "" } },
    compute: { view: { d: [1190, 690, 1.4],   m: [1190, 690, 1.3] },  steps: [1200, 2300, 3500, 4600, 6400],
               pull: { d: [1440, 600, 1.0], m: [1450, 560, 1.0] }, capPos: { d: "", m: "" } }
  };

  var cur = { k: 1, tx: 0, ty: 0 }, timers = [], state = { mode: "entry", id: null, trigger: null };
  var lensPos = { x: 0, y: 0, r: 0 }, gliding = 0, dragging = false, hiRes = false;
  var reduce = function () { return mqReduce.matches; };
  var mob = function () { return mqMobile.matches; };
  var pick = function (o) { return mob() ? o.m : o.d; };

  /* ---------- camera ---------- */
  function camera(v, instant) {
    var W = stage.clientWidth, H = stage.clientHeight, base = Math.max(W / 2752, H / 1536), k = base * v[2];
    var cx = W / 2, cy = mob() ? H * 0.46 : H * 0.46;
    var tx = Math.min(0, Math.max(W - 2752 * k, cx - v[0] * k));
    var ty = Math.min(0, Math.max(H - 1536 * k, cy - v[1] * k));
    cur = { k: k, tx: tx, ty: ty };
    cam.classList.toggle("no-anim", !!instant || reduce());
    cam.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + k + ")";
  }
  var toScreen = function (p) { return [p[0] * cur.k + cur.tx, p[1] * cur.k + cur.ty]; };

  /* ---------- lens ---------- */
  /* v2: about 38% smaller (desktop radius ≈ 7.4% of stage width, 82–124 px; mobile 64–72 px),
     always fully inside the photograph, kept off the headline/paths/layers where practical,
     and only one discovery is "active" at a time. */
  function lensRadius() { return mob() ? Math.max(64, Math.min(72, stage.clientWidth * 0.18)) : Math.max(82, Math.min(124, stage.clientWidth * 0.074)); }
  function rel(el) { var a = el.getBoundingClientRect(), b = stage.getBoundingClientRect(); return { l: a.left - b.left, t: a.top - b.top, r: a.right - b.left, b: a.bottom - b.top }; }
  function keepOut(forLabel) {   /* rectangles to keep clear. On phones the lens may pass behind the headline (text stays on top). */
    var out = [], sel = (mob() && !forLabel) ? ["#pr-paths", "#pr-layers"] : ["#pr-introTitle", ".lede", "#pr-paths", "#pr-layers"];
    sel.forEach(function (s) { var e = $(s); if (e && e.offsetParent !== null) out.push(rel(e)); });
    return out;
  }
  function clampLens(x, y, r) {
    var W = stage.clientWidth, H = stage.clientHeight, pad = 6;
    x = Math.min(W - r - pad, Math.max(r + pad, x));
    y = Math.min(H - r - pad, Math.max(r + pad, y));
    /* push the lens off UI rectangles: move vertically (up) first, then sideways if that fails */
    keepOut().forEach(function (q) {
      var nx = Math.max(q.l, Math.min(x, q.r)), ny = Math.max(q.t, Math.min(y, q.b));
      var dx = x - nx, dy = y - ny;
      if (dx * dx + dy * dy < (r + 4) * (r + 4)) {
        var upY = q.t - r - 6, downY = q.b + r + 6;
        if (upY >= r + pad && (y <= q.b || downY > H - r - pad)) y = Math.min(y, upY);
        else if (downY <= H - r - pad) y = Math.max(y, downY);
      }
    });
    return [x, y];
  }
  function setLens(x, y, r) {
    var R = (H5 && !PS) ? 0 : (r == null ? lensRadius() : r), c = clampLens(x, y, Math.max(R, 1));
    lensPos.x = c[0]; lensPos.y = c[1]; lensPos.r = R;
    hidden.style.setProperty("--lx", ((c[0] - cur.tx) / cur.k) + "px");
    hidden.style.setProperty("--ly", ((c[1] - cur.ty) / cur.k) + "px");
    hidden.style.setProperty("--lr", (R / cur.k) + "px");
    lens.style.transform = "translate(" + c[0] + "px," + c[1] + "px)";
    lens.style.setProperty("--rr", R + "px");
    if (mob() && $(".lede")) {   /* on phones the roof sits behind the headline: let the headline step back while the lens is there */
      var q = rel($(".lede")), over = c[1] - R < q.b && R > 20;
      pn.classList.toggle("lens-over-intro", over);
    }
    updateActive();
  }
  /* single active discovery, with hysteresis so labels never flicker between neighbours */
  var activeId = null, labelEl = $("#pr-lensLabel");
  function updateActive() {
    var best = null, bestD = 1e9;
    ORDER.forEach(function (id) {
      var p = toScreen(pick(BEACON[id])), d = Math.hypot(p[0] - lensPos.x, p[1] - lensPos.y);
      if (d < bestD) { bestD = d; best = id; }
    });
    var enter = lensPos.r * 0.85, leave = lensPos.r * 1.25, next = activeId;
    if (activeId) {
      var pa = toScreen(pick(BEACON[activeId])), da = Math.hypot(pa[0] - lensPos.x, pa[1] - lensPos.y);
      if (da > leave) next = null;
      if (best !== activeId && bestD < enter && bestD < da - 12) next = best;
    } else if (bestD < enter) next = best;
    if (lensPos.r < 20) next = null;
    if (next !== activeId) setActive(next);
    else if (activeId) placeLabel();
  }
  function setActive(id) {
    activeId = id;
    hidden.setAttribute("data-active", id || "");
    beaconsEl.querySelectorAll(".beacon").forEach(function (b) { b.classList.toggle("active", b.dataset.id === id); });
    if (!id) { labelEl.classList.remove("show"); return; }
    labelEl.innerHTML = '<span class="ll-q">' + D.discoveries[id].beacon.q + '</span><span class="ll-cta" aria-hidden="true">Reveal →</span>';
    labelEl.dataset.id = id;
    placeLabel(); labelEl.classList.add("show");
  }
  function placeLabel() {   /* outside the lens; never over the headline, paths, layers or the stage edge */
    var W = stage.clientWidth, H = stage.clientHeight, w = labelEl.offsetWidth, h = labelEl.offsetHeight, r = lensPos.r, g = 12;
    var c = [[lensPos.x + r + g, lensPos.y - h / 2], [lensPos.x - r - g - w, lensPos.y - h / 2], [lensPos.x - w / 2, lensPos.y - r - g - h], [lensPos.x - w / 2, lensPos.y + r + g]];
    var avoid = keepOut(true), pick1 = null;
    var ok = function (x, y) {
      if (x < 8 || y < 8 || x + w > W - 8 || y + h > H - 8) return false;
      var lx = Math.max(x, Math.min(lensPos.x, x + w)), ly = Math.max(y, Math.min(lensPos.y, y + h));
      if (Math.hypot(lx - lensPos.x, ly - lensPos.y) < r + 4) return false;           /* never over the lens */
      return !avoid.some(function (q) { return x < q.r && x + w > q.l && y < q.b && y + h > q.t; });
    };
    for (var pass = 0; pass < 2 && !pick1; pass++) for (var i = 0; i < c.length && !pick1; i++) {
      var x = pass ? Math.min(W - w - 8, Math.max(8, c[i][0])) : c[i][0], y = c[i][1];   /* second pass: slide sideways into view */
      if (ok(x, y)) pick1 = [x, y];
    }
    if (!pick1) { pick1 = [Math.min(W - w - 8, Math.max(8, c[0][0])), Math.min(H - h - 8, Math.max(8, c[0][1]))]; }
    labelEl.style.transform = "translate(" + Math.round(pick1[0]) + "px," + Math.round(pick1[1]) + "px)";
  }
  function restLens() { setLens.apply(null, toScreen(pick(restAt()))); }
  function easeLensTo(x, y, ms) {          /* smooth return to rest when the pointer leaves */
    if (reduce()) { setLens(x, y); return; }
    var x0 = lensPos.x, y0 = lensPos.y, t0 = null, my = ++gliding;
    function f(ts) { if (my !== gliding || state.mode !== "entry") return; if (t0 === null) t0 = ts;
      var u = Math.min(1, (ts - t0) / ms), s = u * u * (3 - 2 * u); setLens(x0 + (x - x0) * s, y0 + (y - y0) * s); if (u < 1) requestAnimationFrame(f); }
    requestAnimationFrame(f);
  }

  function glide() {
    var pts = ["ground", "wind", "compute", "ground"].map(function (id) { return toScreen(pick(BEACON[id])); });
    if (reduce()) { restLens(); showPaths(); return; }
    var t0 = null, open = 700, seg = 1350, my = ++gliding;
    function frame(ts) {
      if (my !== gliding || state.mode !== "entry") return;
      if (t0 === null) t0 = ts;
      var t = ts - t0;
      if (t < open) { var e = t / open; setLens(pts[0][0], pts[0][1], lensRadius() * (1 - Math.pow(1 - e, 3))); }
      else {
        var u = (t - open) / seg, i = Math.floor(u);
        if (i >= pts.length - 1) { setLens(pts[pts.length - 1][0], pts[pts.length - 1][1]); gliding++; return; }
        var f = u - i, s = f * f * (3 - 2 * f), a = pts[i], b = pts[i + 1];
        setLens(a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s);
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    timers.push(setTimeout(showPaths, 1500));
  }
  function stopGlide() { gliding++; }

  function localXY(e) { var r = stage.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
  stage.addEventListener("pointermove", function (e) {
    if (state.mode !== "entry") return;
    if (H5 && !PS) return;
    if (dragging || e.pointerType === "mouse") {
      if (e.pointerType === "mouse" && e.target.closest && e.target.closest("button, a, .intro h1, .lede, .layers")) return;   /* don't chase the cursor onto controls */
      stopGlide(); showPaths(); setLens.apply(null, localXY(e));
    }
  });
  stage.addEventListener("pointerleave", function (e) {
    if ((H5 && !PS) || state.mode !== "entry" || dragging || e.pointerType !== "mouse") return;
    var p = toScreen(pick(restAt())); easeLensTo(p[0], p[1], 600);
  });
  grip.addEventListener("pointerdown", function (e) { if (H5 && !PS) return; dragging = true; stopGlide(); grip.setPointerCapture(e.pointerId); e.preventDefault(); });
  grip.addEventListener("pointerup", function () { dragging = false; });
  grip.addEventListener("pointercancel", function () { dragging = false; });
  labelEl.addEventListener("click", function () { if (activeId) play(activeId, beaconsEl.querySelector('.beacon[data-id="' + activeId + '"]')); });

  /* ---------- entry UI ---------- */
  function buildBeacons() {
    beaconsEl.innerHTML = "";
    ORDER.forEach(function (id) {
      var d = D.discoveries[id], b = document.createElement("button");
      b.type = "button"; b.className = "beacon"; b.dataset.id = id;
      b.setAttribute("aria-label", d.beacon.q + " Reveal it on the house.");
      b.innerHTML = '<span class="b-dot" aria-hidden="true"></span>';
      b.addEventListener("click", function () { play(id, b); });
      b.addEventListener("focus", function () { if (state.mode === "entry") { stopGlide(); var p = toScreen(pick(BEACON[id])); setLens(p[0], p[1]); setActive(id); } });
      b.addEventListener("mouseenter", function () { if (state.mode === "entry") { stopGlide(); var p = toScreen(pick(BEACON[id])); setLens(p[0], p[1]); setActive(id); } });
      beaconsEl.appendChild(b);
    });
    placeBeacons();
  }
  function placeBeacons() {
    beaconsEl.querySelectorAll(".beacon").forEach(function (b) {
      var p = toScreen(pick(BEACON[b.dataset.id]));
      b.style.left = p[0] + "px"; b.style.top = p[1] + "px";
    });
  }
  function buildPaths() {
    pathsEl.innerHTML = "";
    D.paths.forEach(function (p) {
      var b = document.createElement("button"), ready = p.discoveries.length > 0;
      b.type = "button"; b.className = "path"; b.dataset.path = p.id;
      b.innerHTML = '<span class="p-dot" aria-hidden="true"></span><b>' + p.title + "</b><small>" + (ready ? p.total + " discoveries" : p.note) + "</small>";
      if (!ready) { b.setAttribute("aria-disabled", "true"); b.setAttribute("aria-label", p.title + ": " + p.note + "."); }
      b.addEventListener("click", function () { if (ready) play(p.discoveries[0], b); });
      pathsEl.appendChild(b);
    });
  }
  function showPaths() { pathsEl.classList.add("show"); beaconsEl.classList.add("ready"); }

  /* ---------- scenes ---------- */
  function clearTimers() { timers.forEach(clearTimeout); timers = []; }
  function chipHTML(key) { var c = D.chips[key]; return '<span class="chip t-' + c.tone + '">' + c.text + "</span>"; }
  function mk(m) { return '<span class="mk mk-' + D.maturity[m].shape + '" aria-hidden="true"></span>'; }
  function pathOf(id) { return D.paths.filter(function (p) { return p.discoveries.indexOf(id) >= 0; })[0]; }

  function captionHTML(id) {
    var d = D.discoveries[id], i = ORDER.indexOf(id), last = i === ORDER.length - 1;
    var nextLabel = last ? "Whole property" : (pathOf(ORDER[i + 1]) !== pathOf(id) ? "Next path" : "Next");
    return '<p class="tag">' + mk(d.maturity) + '<span><span class="sr-only">' + D.maturity[d.maturity].name + ". </span>" + d.tag + "</span></p>" +
      '<h2 tabindex="-1" id="pr-capTitle">' + d.hook + "</h2>" +
      '<p class="line">' + d.line + "</p>" +
      '<div class="chips">' + d.chips.map(chipHTML).join("") + "</div>" +
      '<p class="sr-only">' + d.alt + "</p>" +
      '<div class="row"><button type="button" class="btn" data-act="more" aria-haspopup="dialog">Tell me more</button><span class="sp"></span>' +
      '<button type="button" class="btn btn-dark" data-act="next">' + nextLabel + ' <span aria-hidden="true">→</span></button></div>';
  }

  function play(id, trigger) {
    clearTimers(); stopGlide(); closeMore(true); setActive(null);
    var d = D.discoveries[id], sc = SCENE[id], svg = $("#pr-sc-" + id);
    state.id = id; if (trigger) state.trigger = trigger;
    setMode("scene");
    ROOT.querySelectorAll(".scene").forEach(function (s) { s.classList.remove("on", "c-open"); });
    svg.querySelectorAll(".on").forEach(function (e) { e.classList.remove("on"); });
    svg.querySelectorAll(".dim").forEach(function (e) { e.classList.remove("dim"); });
    svg.classList.add("on");
    camera(pick(sc.view));
    var p = pathOf(id);
    $("#pr-pathName").textContent = p.title;
    renderDots(p, id);
    cap.className = "caption " + pick(sc.capPos); cap.inert = true;
    cap.innerHTML = captionHTML(id);
    var capAt = sc.capAt || sc.steps.length;
    var step = function (n) {
      svg.querySelectorAll(".s" + n).forEach(function (e) { e.classList.add("on"); });
      if (id === "compute" && n === 1) svg.classList.add("c-open");
      if (id === "compute" && n === 5) camera(pick(sc.pull));
      if (n === capAt) showCaption();
    };
    if (reduce()) { for (var n = 1; n <= sc.steps.length; n++) step(n); if (id === "compute") camera(pick(sc.pull), true); }
    else sc.steps.forEach(function (t, i) { timers.push(setTimeout(function () { step(i + 1); }, t)); });
    upgradeImage();
  }
  function showCaption() {
    cap.classList.add("show"); cap.inert = false;
    var h = $("#pr-capTitle"); if (h) h.focus({ preventScroll: true });
  }
  function renderDots(p, id) {
    var html = p.discoveries.map(function (x) {
      return '<li><button type="button" data-go="' + x + '" aria-label="' + D.discoveries[x].hook + '"' + (x === id ? ' aria-current="step"' : "") + "></button></li>";
    }).join("");
    for (var i = p.discoveries.length; i < p.total; i++) html += '<li><span class="later" title="In the next build stage"><span class="sr-only">Another discovery, in the next build stage</span></span></li>';
    $("#pr-dots").innerHTML = html;
  }
  function next() { var i = ORDER.indexOf(state.id); if (i < ORDER.length - 1) play(ORDER[i + 1]); else home(); }
  function prev() { var i = ORDER.indexOf(state.id); if (i > 0) play(ORDER[i - 1]); }

  function home() {
    clearTimers(); closeMore(true);
    setMode("entry");
    cap.classList.remove("show");
    ROOT.querySelectorAll(".scene").forEach(function (s) { s.classList.remove("on"); });
    camera(pick(entryView())); placeBeacons(); setActive(null); restLens(); showPaths();
    var t = state.trigger && document.contains(state.trigger) ? state.trigger : pathsEl.querySelector(".path:not([aria-disabled])");
    if (t) t.focus({ preventScroll: true });
  }

  /* ---------- "Tell me more" ---------- */
  function href(h) { return h.charAt(0) === "#" ? D.discoveryUrl + h : h; }
  function activeOffers(d) {
    return (d.offers || []).filter(function (o) { return D.commerceEnabled === true && o.status === "active" && !!o.approval; });
  }
  function moreHTML(id) {
    var d = D.discoveries[id], m = d.more, n = d.nextStep;
    var h = '<button type="button" class="btn m-close" data-act="close">Close</button>' +
      '<p class="tag">' + mk(d.maturity) + "<span>" + D.maturity[d.maturity].name + "</span></p>" +
      '<h2 id="pr-moreTitle">' + d.hook + "</h2>" +
      '<p class="quote">' + m.quote + "</p><p>" + m.body + "</p>";
    if (m.split) h += '<div class="split">' + m.split.map(function (s) { return "<div><b>" + s.title + "</b>" + chipHTML(s.chip) + "<br>" + s.text + "</div>"; }).join("") + "</div>";
    else h += '<div class="chips">' + d.chips.map(chipHTML).join("") + "</div>";
    h += '<p class="honest">' + m.honest + "</p>";
    h += '<div class="next"><p class="n-lab">Next step</p><a class="n-btn" href="' + href(n.href) + '">' + n.label + ' <span aria-hidden="true">→</span></a>' +
         (n.note ? '<p class="n-note">' + n.note + "</p>" : "");
    activeOffers(d).forEach(function () { /* intentionally empty: no offer can render while commerce is disabled */ });
    if (REVIEW) (d.offers || []).forEach(function (o) {
      h += '<p class="slot"><b>Inactive offer</b>' + o.offerType + " · fulfiller: " + o.fulfiller + " · terms: " + o.commercialTerms + " · " + o.status + (o.approval ? "" : " · not approved") + "</p>";
    });
    h += "</div>" + '<a class="d-link" href="' + D.discoveryUrl + '">More in the Discovery</a>';
    return h;
  }
  var moreReturn = null;
  function openMore() {
    moreReturn = document.activeElement;
    more.innerHTML = moreHTML(state.id); more.hidden = false;
    requestAnimationFrame(function () { more.classList.add("open"); $(".m-close", more).focus({ preventScroll: true }); });
  }
  function closeMore(silent) {
    if (more.hidden) return;
    more.classList.remove("open");
    var done = function () { more.hidden = true; };
    if (reduce() || silent) done(); else setTimeout(done, 450);
    if (!silent && moreReturn && document.contains(moreReturn)) moreReturn.focus({ preventScroll: true });
  }

  /* ---------- events ---------- */
  document.addEventListener("click", function (e) {
    if (!ROOT.contains(e.target)) return;
    var b = e.target.closest("button"); if (!b) return;
    if (b.id === "pr-btnHome") home();
    else if (b.id === "pr-btnReplay") play(state.id);
    else if (b.dataset.go) play(b.dataset.go);
    else if (b.dataset.act === "more") openMore();
    else if (b.dataset.act === "close") closeMore();
    else if (b.dataset.act === "next") next();
  });
  document.addEventListener("keydown", function (e) {
    if (e.target !== document.body && !ROOT.contains(e.target)) return;
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key === "Escape") { if (!more.hidden) closeMore(); else if (state.mode === "scene") home(); return; }
    if (state.mode !== "scene" || !more.hidden) return;
    if (e.key === "ArrowRight") { e.preventDefault(); next(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
    else if (e.key === "r" || e.key === "R") play(state.id);
  });
  var rt;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      if (state.mode === "entry") { camera(pick(entryView()), true); placeBeacons(); setLens(lensPos.x, lensPos.y); }
      else { var sc = SCENE[state.id]; camera(pick(state.id === "compute" && cap.classList.contains("show") ? sc.pull : sc.view), true); cap.className = "caption show " + pick(sc.capPos); }
    }, 120);
  });

  /* load the full-resolution image only once someone starts zooming in */
  function upgradeImage() {
    if (hiRes) return; hiRes = true;
    var go = function () { ROOT.querySelectorAll(".cam source, .cam img").forEach(function (el) { el.setAttribute("sizes", "2752px"); }); };
    (window.requestIdleCallback || function (f) { setTimeout(f, 200); })(go);
  }

  /* only the controls for the current mode are reachable (keyboard and screen readers) */
  function syncInert() {
    var scene = state.mode === "scene";
    ["#pr-bar"].forEach(function (s) { $(s).inert = !scene; });
    [".intro", "#pr-beacons", "#pr-layers"].forEach(function (s) { var e = $(s); if (e) e.inert = scene; });
  }
  function setMode(m) { state.mode = m; pn.setAttribute("data-mode", m); syncInert(); }

  /* ---------- H5 · Power Station on demand ----------
     The original, approved Power Station experience (the lens and its opening glide, the three
     hidden-energy drawings, the markers, labels, scenes, paths and their links) runs only while
     the Power Station switch is on. It never changes the garden layers; switching it off returns
     the clean illustration with nothing on it. */
  var psBtn = $("#pr-psSwitch"), psPanel = $("#pr-psPanel");
  function setPS(on) {
    on = !!on; if (on === PS) return;
    PS = on;
    pn.classList.toggle("ps-on", on);
    if (psBtn) psBtn.setAttribute("aria-pressed", on ? "true" : "false");
    if (psPanel) psPanel.hidden = !on;
    if (on) {
      if (state.mode !== "entry") home();
      camera(pick(entryView())); placeBeacons();
      beaconsEl.classList.add("ready");
      setLens.apply(null, toScreen(pick(restAt())).concat([0]));
      if (reduce()) { restLens(); showPaths(); } else glide();
    } else {
      stopGlide(); clearTimers(); dragging = false;
      if (state.mode !== "entry") home();
      setActive(null); setLens(lensPos.x, lensPos.y, 0);
      pn.classList.remove("lens-over-intro");
      camera(pick(entryView())); placeBeacons();
    }
  }
  if (psBtn) psBtn.addEventListener("click", function () { setPS(!PS); });

  /* ---------- start ---------- */
  buildPaths(); syncInert();
  camera(pick(ENTRY_VIEW), true);
  buildBeacons();
  setLens.apply(null, toScreen(pick(BEACON.ground)).concat([0]));
  var hash = new URLSearchParams(location.hash.slice(1));              // review hooks: #play=wind  #lens=1190,690  #more=1
  if (hash.get("play") && D.discoveries[hash.get("play")]) {
    showPaths(); play(hash.get("play"));
    if (hash.get("more") === "1") setTimeout(openMore, reduce() ? 0 : (SCENE[hash.get("play")].steps.slice(-1)[0] + 300));
  } else if (hash.get("lens")) {
    var p = hash.get("lens").split(",").map(Number); showPaths(); setLens.apply(null, toScreen(p));
  } else {
    if (!H5) timers.push(setTimeout(function () { beaconsEl.classList.add("ready"); glide(); }, 650));
  }
  /* H3: frame a garden layer through this camera; null returns to the whole property.
     If the frame names its own lens resting place, the lens goes there, and when that
     ends it returns exactly to where it was before; otherwise it stays where it is. */
  var lensHome = null;
  function frame(v, instant) {
    var own0 = !!(FRAME && FRAME.lens);
    FRAME = v || null;
    if (state.mode !== "entry") return;
    stopGlide(); showPaths();
    camera(pick(entryView()), instant); placeBeacons();
    var own1 = !!(FRAME && FRAME.lens);
    if (own1 && !dragging) { if (!own0) lensHome = [lensPos.x, lensPos.y]; restLens(); }
    else if (own0 && !own1 && lensHome && !dragging) { setLens(lensHome[0], lensHome[1]); lensHome = null; }
    else setLens(lensPos.x, lensPos.y);
  }
  window.PN_REVEAL_API = { play: play, home: home, state: state, frame: frame, ps: setPS, psOn: function () { return PS; } };   // play/home/state: automated checks; frame: garden.js
})();
