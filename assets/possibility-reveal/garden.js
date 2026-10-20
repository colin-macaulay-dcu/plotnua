/* PlotNua Possibility Reveal · H3 garden layers (L3–L6) · no dependencies
 *
 * Switches the locked garden layers on and off, one by one, over the unchanged
 * live picture (L1 + L2A). Each layer's tile sits in a <template> in the
 * component markup, so NOTHING is downloaded until the visitor switches that
 * layer on: the hero's first paint and its LCP image are untouched.
 *
 *   L3  Grow a garden room   · mirrored garden pavilion (L3 v2.1c)
 *   L4  Borrow a garden      · kitchen garden
 *   L5  Hold a treehouse     · elevated timber pod
 *   L6  Become a retreat     · sauna, and the TimberIN hot tub with its smoke
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
    L3: { d: [2100, 820, 1], m: [2100, 820, 1] },
    L4: { d: [946, 1180, 1], m: [946, 1160, 1] },
    L5: { d: [220, 560, 1], m: [260, 600, 1] },
    /* phones: a modest 1.35x zoom, held to the bottom-right corner, frames the sauna, the
       chimney and smoke and the hot tub's wooden body together (H3 review, 20 Oct 2026).
       Camera framing alone cannot lift the tub clear of the full-height paths, so while L6 is
       on, phones also show the paths as one compact row (garden.css). */
    L6: { d: [2452, 1110, 1], m: [2460, 1150, 1.35] }
  };
  /* L6's route to the existing Garden Retreat Discovery, in the Reveal's beacon pattern: a dot,
     its label on hover or focus. It sits on the generic sauna (never on the supplier's tub) and
     makes no product or commercial claim. */
  var RETREAT = { at: [2655, 960], href: "discovery-garden-retreat.html",
                  q: "Explore the Garden Retreat", label: "Explore the Garden Retreat Discovery: saunas, hot tubs and cold plunges at home" };
  var SAY = {
    L3: "A mirrored garden pavilion appears along the right-hand fence. Illustration.",
    L4: "A kitchen garden appears on the lawn. Illustration.",
    L5: "A timber pod appears in the tree at the left of the garden. Illustration.",
    L6: "A sauna and a wood-fired hot tub, with smoke from its chimney, appear in the far right corner of the garden. Illustration with adapted photography."
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
  cam.addEventListener("transitionend", function (e) { if (e.target === cam) { placeBeacon(); placeCredit(); } });
  function rect(sel) {
    var e = $(sel); if (!e || e.offsetParent === null) return null;
    var a = e.getBoundingClientRect(), s = stage.getBoundingClientRect();
    return { l: a.left - s.left, t: a.top - s.top, r: a.right - s.left, b: a.bottom - s.top };
  }
  function placeCredit() {
    if (credit.hidden) return;
    var avoid = ["#pr-introTitle", ".lede", "#pr-paths", "#pr-layers", ".g-beacon"].map(rect).filter(Boolean);
    var bk = rect(".g-beacon");
    var H = stage.clientHeight, h = credit.offsetHeight, nav = rect("#pr-layers"), paths = rect("#pr-paths"), lede = rect(".lede");
    var cands = [], phone = window.matchMedia("(max-width: 760px)").matches;
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
  }

  function frameFor(instant) {
    var last = on.length ? on[on.length - 1] : null;
    ROOT.classList.add("g-panning");
    API.frame(last ? VIEW[last] : null, instant || mqReduce.matches);
    clearTimeout(frameFor.t);
    frameFor.t = setTimeout(function () { ROOT.classList.remove("g-panning"); placeBeacon(); placeCredit(); }, instant || mqReduce.matches ? 0 : 1500);
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

  window.addEventListener("resize", function () {
    queuePlace();
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
