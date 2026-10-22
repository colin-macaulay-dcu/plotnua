/* PlotNua Possibility Reveal · H3 garden layers (L3–L6) · no dependencies
 *
 * Switches the locked garden layers on and off, one by one, over the unchanged
 * live picture (L1 + L2A). Each layer's tile sits in a <template> in the
 * component markup, so NOTHING is downloaded until the visitor switches that
 * layer on: the hero's first paint and its LCP image are untouched.
 *
 *   L3  Grow a garden room   · mirrored garden pavilion (L3 v2.1c)
 *   L4  Borrowed Garden      · a productive growing space (garden sharing; illustration)
 *   L5  Hold a treehouse     · elevated timber pod
 *   L6  Become a retreat     · H5C4-S garden retreat: the TimberIN hot tub with its smoke and the TimberIN Nordic Cube sauna, terrace and cold plunge, planting
 *
 * L6 shares pixels with L3 (the approved smoke drifts over the pavilion), so
 * its tile is a two-state sprite: "with L3" (exactly the locked L6) and
 * "without L3" (the same smoke over the garden). Which half shows follows L3.
 * The TimberIN credit and the accessible disclosure show whenever L6 is on, with a
 * beacon (the Reveal's own pattern) leading to the existing Garden Retreat Discovery.
 *
 * Camera: switching a layer on frames it through the Reveal's own camera
 * (PN_REVEAL_API.frame), so beacons, lens and resize keep working. Where the
 * whole picture already fits the stage (most desktops) nothing moves.
 * A Discovery scene hides the layers and restores them on return (CSS).
 * Review hook: #layers=L3,L6 switches layers on at load, without animation.
 */
(function () {
  "use strict";
  var ROOT = document.querySelector("[data-pr-root]");
  var API = window.PN_REVEAL_API;
  if (!ROOT || !API || !API.frame) return;
  var $ = function (s) { return ROOT.querySelector(s); };
  var cam = $("#pr-cam"), credit = $("#pr-gardenCredit"), status = $("#pr-gardenStatus");
  var mqReduce = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* where each layer is framed: [x, y, zoom] in picture pixels (2752 x 1536). */
  var VIEW = {
    L3: { d: [1900, 800, 1], m: [1890, 790, 1] },   /* H5C4: the pavilion at 85 %, moved towards the house */
    L4: { d: [946, 1180, 1], m: [946, 1160, 1] },
    L5: { d: [220, 560, 1], m: [260, 600, 1] },
    /* phones: a modest 1.35x zoom, held to the bottom-right corner, frames the sauna, the
       chimney and smoke and the hot tub's wooden body together (H3 review, 20 Oct 2026).
       Camera framing alone cannot lift the tub clear of the full-height paths, so while L6 is
       on, phones and portrait tablets (below 1024px) also show the paths as one compact row
       (garden.css; tablets added in the H3 final review, 20 Oct 2026). */
    L6: { d: [2150, 1060, 1], m: [2240, 1130, 1.2] }   /* H5C4: the whole retreat, maple to hot tub */
  };
  /* L6's route to the existing Garden Retreat Discovery, in the Reveal's beacon pattern: a dot,
     its label on hover or focus. It sits on the terrace beside the cold plunge (never on the supplier's
     tub) and makes no product or commercial claim. H5C4, 22 Oct 2026. */
  var RETREAT = { at: [2075, 1005], href: "discovery-garden-retreat.html",
                  q: "Explore the Garden Retreat", label: "Explore the Garden Retreat Discovery: saunas, hot tubs and cold plunges at home" };
  var SAY = {
    L3: "A mirrored garden pavilion appears along the right-hand fence. Illustration.",
    L4: "Part of the lawn becomes a productive growing space that could be shared with someone nearby who wants to grow. Illustration.",
    L5: "A timber pod appears in the tree at the left of the garden. Illustration.",
    L6: "A garden retreat appears in the far right corner: a wood-fired hot tub with smoke from its chimney, a dark timber sauna with a glass front, a cold plunge set into a charcoal terrace, stepping stones, planting and a Japanese maple. Illustration with adapted photography."
  };
  var on = [], mounted = {};

  function scaleNow() { return cam.getBoundingClientRect().width / 2752 || 0.5; }

  function mount(id) {
    if (mounted[id]) return mounted[id];
    var tpl = ROOT.querySelector('template[data-layer="' + id + '"]');
    if (!tpl) return null;
    var el = tpl.content.firstElementChild.cloneNode(true);
    var img = el.querySelector("img");
    img.setAttribute("sizes", Math.ceil(parseFloat(el.style.width) * scaleNow()) + "px");
    tpl.parentNode.insertBefore(el, tpl.nextSibling);
    mounted[id] = el;
    return el;
  }

  function show(el) {
    var img = el.querySelector("img");
    var go = function () { requestAnimationFrame(function () { if (el.dataset.want === "1") el.classList.add("is-on"); }); };
    el.dataset.want = "1";
    if (img.complete && img.naturalWidth) go();
    else if (img.decode) img.decode().then(go, go);
    else img.addEventListener("load", go, { once: true });
  }

  /* the credit sits clear of the headline, lede, paths and chips: under the chips where there is
     room (desktop, tablet), otherwise just above the paths (phones) */
  var stage = $("#pr-stage");

  /* ---------- the Garden Retreat beacon ---------- */
  var beacon = document.createElement("a");
  beacon.className = "beacon g-beacon"; beacon.href = RETREAT.href; beacon.hidden = true;
  beacon.setAttribute("aria-label", RETREAT.label);
  beacon.innerHTML = '<span class="b-dot" aria-hidden="true"></span><span class="b-q" aria-hidden="true">' + RETREAT.q + ' →</span>';
  var beaconsEl = $("#pr-beacons");
  beaconsEl.parentNode.insertBefore(beacon, beaconsEl.nextSibling);
  function placeBeacon() {
    if (beacon.hidden) return;
    var s = stage.getBoundingClientRect(), c = cam.getBoundingClientRect(), k = c.width / 2752;
    var x = c.left - s.left + RETREAT.at[0] * k, y = c.top - s.top + RETREAT.at[1] * k;
    var dot = beacon.querySelector(".b-dot"), pad = 10, r = dot.offsetWidth / 2;
    /* the dot sits exactly on the sauna; as with the Reveal's other beacons, its label shows on
       hover and keyboard focus only, so at rest nothing covers the chimney or the smoke */
    beacon.style.left = Math.round(x - pad - r) + "px";
    beacon.style.top = Math.round(y) + "px";
  }
  cam.addEventListener("transitionend", function (e) { if (e.target === cam) { fitCounts(); placeBeacon(); placeCredit(); } });
  function rect(sel) {
    var e = $(sel); if (!e || e.offsetParent === null) return null;
    var a = e.getBoundingClientRect(), s = stage.getBoundingClientRect();
    return { l: a.left - s.left, t: a.top - s.top, r: a.right - s.left, b: a.bottom - s.top };
  }
  function pillsRect() {
    var u = null;
    ROOT.querySelectorAll("#pr-paths .path").forEach(function (e) {
      if (e.offsetParent === null) return;
      var a = e.getBoundingClientRect(), s = stage.getBoundingClientRect();
      var q = { l: a.left - s.left, t: a.top - s.top, r: a.right - s.left, b: a.bottom - s.top };
      u = u ? { l: Math.min(u.l, q.l), t: Math.min(u.t, q.t), r: Math.max(u.r, q.r), b: Math.max(u.b, q.b) } : q;
    });
    return u;
  }
  function placeCredit() {
    if (credit.hidden) return;
    /* portrait tablets with L6 on: the paths box keeps its usual height, but only its compact row
       of pills is drawn, so the credit avoids the pills themselves and sits as on phones */
    var tab = mqTab && mqTab.matches && on.indexOf("L6") >= 0;
    var paths = tab ? pillsRect() : rect("#pr-paths");
    var avoid = ["#pr-introTitle", ".lede", "#pr-layers", ".g-beacon"].map(rect).concat([paths]).filter(Boolean);
    var bk = rect(".g-beacon");
    var H = stage.clientHeight, h = credit.offsetHeight, nav = rect("#pr-layers"), lede = rect(".lede");
    var cands = [], phone = tab || window.matchMedia("(max-width: 760px)").matches;
    if (phone && lede) cands.push(lede.b + 10);   /* phones: above the lawn, clear of the tub and the compact paths */
    if (phone && bk) cands.push(bk.b + 8);
    if (nav) cands.push(nav.b + 8);
    if (paths) cands.push(paths.t - 8 - h);
    if (lede) cands.push(lede.b + 10);
    var l = credit.offsetLeft, r = l + credit.offsetWidth;
    var free = function (t) {
      if (t < 8 || t + h > H - 8) return false;
      return !avoid.some(function (q) { return l < q.r && r > q.l && t < q.b && t + h > q.t; });
    };
    var top = cands.filter(free)[0];
    credit.style.top = (top === undefined ? Math.max(8, H - h - 8) : Math.round(top)) + "px";
  }
  var raf = 0;
  function queuePlace() { if (!raf) raf = requestAnimationFrame(function () { raf = 0; placeCredit(); }); }
  window.addEventListener("scroll", queuePlace, { passive: true });

  /* portrait tablets: while L6 compacts the paths, the headline and lede stay exactly where they
     were. The height the full paths took is kept as margin under the lede (--g-hold, measured with
     the compact rule off and on), so only the pills move. Phones keep the approved layout. */
  var mqTab = window.matchMedia("(min-width: 761px) and (max-width: 1023px)");
  var pathsEl = $("#pr-paths");
  function holdIntro() {
    ROOT.style.removeProperty("--g-hold");
    if (!mqTab.matches || on.indexOf("L6") < 0) return;
    var g = ROOT.getAttribute("data-garden");
    ROOT.setAttribute("data-garden", "");
    var full = pathsEl.offsetHeight;
    ROOT.setAttribute("data-garden", g);
    var compact = pathsEl.offsetHeight;
    if (full && compact && full > compact) ROOT.style.setProperty("--g-hold", (full - compact) + "px");
  }
  new MutationObserver(function () { holdIntro(); fitCounts(); queuePlace(); }).observe(ROOT, { attributes: true, attributeFilter: ["data-mode"] });

  /* desktops and landscape tablets (1024px and wider): where the one-row paths cover more than a
     tenth of the hot tub's wooden body (measured with their counts showing: about 1243-1439px), the
     small secondary counts ("4 discoveries", "Next build stage") are hidden while L6 is on. The path
     names stay; screen readers still hear the counts. Nothing changes where the tub is already clear. */
  var mqWide = window.matchMedia("(min-width: 1024px)");
  function tubCovered() {
    var c = cam.getBoundingClientRect(), k = c.width / 2752, n = 0, hit = 0;
    var pills = [].slice.call(ROOT.querySelectorAll("#pr-paths .path")).map(function (e) { return e.getBoundingClientRect(); });
    for (var i = 0; i < 24; i++) for (var j = 0; j < 8; j++) {
      var X = c.left + (2260 + 380 * (i + .5) / 24) * k, Y = c.top + (1330 + 120 * (j + .5) / 8) * k; n++;
      if (pills.some(function (r) { return X >= r.left && X <= r.right && Y >= r.top && Y <= r.bottom; })) hit++;
    }
    return hit / n;
  }
  function fitCounts() {
    ROOT.classList.remove("g-counts-off");
    if (on.indexOf("L6") < 0 || !mqWide.matches || ROOT.getAttribute("data-mode") !== "entry") return;
    if (tubCovered() > 0.1) ROOT.classList.add("g-counts-off");
  }

  function sync() {
    ROOT.classList.toggle("g-noL3", on.indexOf("L3") < 0);
    var l6 = on.indexOf("L6") >= 0;
    credit.hidden = !l6;
    beacon.hidden = !l6;
    placeCredit(); placeBeacon();
    ROOT.querySelectorAll(".lay-btn").forEach(function (b) {
      b.setAttribute("aria-pressed", on.indexOf(b.dataset.layer) >= 0 ? "true" : "false");
    });
    ROOT.setAttribute("data-garden", on.slice().sort().join(" "));
    holdIntro(); fitCounts(); placeCredit();
  }

  /* the sizes where, with L6 on, the resting lens or its label can sit on the Garden Retreat beacon
     (measured: portrait tablets up to about 928px, depending on height, so the whole portrait-tablet
     band below 1024px for a margin; and phones narrower than 360px, where it also faded the headline
     under Option A): while L6 is on, the lens rests on the open lawn instead, far enough from the
     ground-source beacon that its label lets go. Switching L6 off returns the lens exactly to where it
     was; dragging and hovering work as before. */
  var mqLens = window.matchMedia("(max-width: 359px), (min-width: 761px) and (max-width: 1023px)");
  var L6_LENS = { d: [1800, 1100], m: [1800, 1100] };
  function frameFor(instant) {
    var last = on.length ? on[on.length - 1] : null, v = last ? VIEW[last] : null;
    if (v && on.indexOf("L6") >= 0 && mqLens.matches) v = { d: v.d, m: v.m, lens: L6_LENS };
    ROOT.classList.add("g-panning");
    /* H5C4 · phones: moving from one close-up to another passes briefly through the whole house
       first (a short establishing pan), so each transformation reads as part of the same property.
       Never under reduced motion, and never on wider screens, where everything switched on is framed. */
    var phone = window.matchMedia("(max-width: 760px)").matches, quick = instant || mqReduce.matches;
    clearTimeout(frameFor.p);
    if (phone && !quick && v && frameFor.last && frameFor.last !== last) {
      API.frame(null, false);
      frameFor.p = setTimeout(function () { API.frame(v, false); }, 800);
    } else API.frame(v, quick);
    frameFor.last = last;
    clearTimeout(frameFor.t);
    frameFor.t = setTimeout(function () { ROOT.classList.remove("g-panning"); fitCounts(); placeBeacon(); placeCredit(); }, instant || mqReduce.matches ? 0 : 2300);
  }

  function set(id, want, instant) {
    var i = on.indexOf(id);
    if (want && i < 0) {
      on.push(id);
      var el = mount(id);
      if (el) { if (instant) { el.dataset.want = "1"; el.classList.add("is-on", "no-fade"); } else show(el); }
    } else if (!want && i >= 0) {
      on.splice(i, 1);
      var e2 = mounted[id];
      if (e2) { e2.dataset.want = "0"; e2.classList.remove("is-on"); }
    } else return;
    sync();
    frameFor(instant);
    if (status && !instant) status.textContent = want ? SAY[id] : "";
  }

  ROOT.querySelectorAll(".lay-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      set(b.dataset.layer, b.getAttribute("aria-pressed") !== "true");
    });
  });

  var onLensBand = function () { if (on.indexOf("L6") >= 0) frameFor(true); };
  if (mqLens.addEventListener) mqLens.addEventListener("change", onLensBand); else if (mqLens.addListener) mqLens.addListener(onLensBand);

  window.addEventListener("resize", function () {
    holdIntro(); fitCounts(); queuePlace();
    setTimeout(placeBeacon, 200);
    Object.keys(mounted).forEach(function (id) {
      var img = mounted[id].querySelector("img");
      img.setAttribute("sizes", Math.ceil(parseFloat(mounted[id].style.width) * scaleNow()) + "px");
    });
  });

  var h = new URLSearchParams(location.hash.slice(1)).get("layers");   // review hook
  if (h) h.split(",").forEach(function (id) { if (VIEW[id]) set(id, true, true); });

  window.PN_REVEAL_GARDEN = { set: set, on: function () { return on.slice(); }, place: function () { placeBeacon(); placeCredit(); } };   // for automated checks only
})();
