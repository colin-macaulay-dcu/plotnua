/* pn-compare · PlotNua Before → Possible comparison (v1.1, 30 Oct 2026; v1 27 Oct 2026)
   Shared behaviour for every .pn-compare figure on a page (hero or inline).
   - Value model: --pos = share of the width, from the left, showing BEFORE.
   - Pointer events (mouse, touch, pen) with pointer capture, so a drag
     survives leaving the frame (from .cmp); vertical page scroll is kept
     on touch by touch-action:pan-y in the CSS.
   - The native range input carries keyboard and assistive technology
     (arrows, Page Up/Down, Home, End).
   - Jump buttons glide unless the visitor prefers reduced motion.
   - One DOM write per animation frame. Nothing is stored or sent.
   Configuration (data attributes on the figure):
     data-start        initial BEFORE share, default 35
     data-subject      words used in aria-valuetext, e.g. "the room"
     data-label-before visible label for the left image (v1.1), default "Before"
     data-label-after  visible label for the right image (v1.1), default "Possible"
                       Labels set the tags and the jump buttons only; markup
                       without them renders exactly as v1.
*/
(function(){
  'use strict';
  if (!('PointerEvent' in window)) return;   /* very old browsers: stay static (POSSIBLE only) */
  var reduce = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : { matches:false };

  function init(box){
    if (box.__pnc) return; box.__pnc = true;
    var stage = box.querySelector('.pn-compare__stage');
    var range = box.querySelector('.pn-compare__range');
    if (!stage || !range) return;
    var jumps = [].slice.call(box.querySelectorAll('.pn-compare__jump [data-to]'));
    var subject = box.getAttribute('data-subject') || 'the property';
    var start = parseFloat(box.getAttribute('data-start'));
    if (isNaN(start)) start = 35;

    var pos = start, queued = false, anim = null;

    /* v1.1: configurable labels (e.g. "Home" / "Away"). Absent = v1 markup unchanged. */
    var lb = box.getAttribute('data-label-before'), la = box.getAttribute('data-label-after');
    function relabel(sel, txt){ if (!txt) return; [].forEach.call(box.querySelectorAll(sel), function(el){ el.textContent = txt; }); }
    relabel('.pn-compare__tag.is-before', lb); relabel('.pn-compare__jump [data-to="100"]', lb);
    relabel('.pn-compare__tag.is-possible', la); relabel('.pn-compare__jump [data-to="0"]', la);

    function say(v){
      if (v >= 97) return 'Showing ' + subject + ' before';
      if (v <= 3)  return 'Showing ' + subject + ' as it could be';
      if (v > 45 && v < 55) return 'Half before, half as it could be';
      return (v > 50 ? 'Mostly ' + subject + ' before' : 'Mostly ' + subject + ' as it could be') + ', divider at ' + Math.round(v) + ' per cent';
    }
    function paint(){ queued = false; box.style.setProperty('--pos', pos + '%'); }
    function set(v, fromRange){
      v = Math.max(0, Math.min(100, v));
      pos = v;
      if (!queued){ queued = true; requestAnimationFrame(paint); }
      var r = Math.round(v);
      if (!fromRange) range.value = r;
      range.setAttribute('aria-valuetext', say(r));
      box.setAttribute('data-end', r >= 97 ? 'before' : (r <= 3 ? 'possible' : ''));
      jumps.forEach(function(b){ b.setAttribute('aria-pressed', String(+b.getAttribute('data-to') === r)); });
    }
    function glide(to){
      if (anim) cancelAnimationFrame(anim);
      if (reduce.matches){ set(to); return; }
      var from = pos, t0 = null, dur = 420;
      function step(t){
        if (t0 === null) t0 = t;
        var k = Math.min(1, (t - t0) / dur); k = 1 - Math.pow(1 - k, 3);
        set(from + (to - from) * k);
        if (k < 1) anim = requestAnimationFrame(step); else anim = null;
      }
      anim = requestAnimationFrame(step);
    }

    /* Mouse: press moves the divider at once and drags.
       Touch / pen: nothing moves until the gesture is clearly horizontal
       (> 8 px and more sideways than vertical), so a vertical swipe over the
       image scrolls the page and leaves the divider where it was. A short
       tap (no real movement) still moves the divider to the tap point. */
    var active = null, rect = null, dragging = false, sx = 0, sy = 0;
    function fromX(x){ var r = rect || stage.getBoundingClientRect(); set((x - r.left) / r.width * 100); }
    stage.addEventListener('pointerdown', function(e){
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      if (anim){ cancelAnimationFrame(anim); anim = null; }
      active = e.pointerId; rect = stage.getBoundingClientRect();
      sx = e.clientX; sy = e.clientY;
      dragging = (e.pointerType === 'mouse');
      if (dragging){ try { stage.setPointerCapture(e.pointerId); } catch(_){} fromX(e.clientX); }
    });
    stage.addEventListener('pointermove', function(e){
      if (active === null || e.pointerId !== active) return;
      if (!dragging){
        var dx = Math.abs(e.clientX - sx), dy = Math.abs(e.clientY - sy);
        if (dx > 8 && dx > dy){ dragging = true; try { stage.setPointerCapture(e.pointerId); } catch(_){} }
        else return;
      }
      if (e.cancelable) e.preventDefault();
      fromX(e.clientX);
    });
    function release(e){
      if (active === null) return;
      if (e && e.pointerId != null && e.pointerId !== active) return;
      if (e && e.type === 'pointerup' && !dragging &&
          Math.abs(e.clientX - sx) < 8 && Math.abs(e.clientY - sy) < 8) fromX(e.clientX);   /* tap */
      try { stage.releasePointerCapture(active); } catch(_){}
      active = null; rect = null; dragging = false;
    }
    stage.addEventListener('pointerup', release);
    stage.addEventListener('pointercancel', release);
    stage.addEventListener('lostpointercapture', function(e){ if (e.buttons === 0) release(e); });   /* capture handover mid-gesture is ignored; pointerup/cancel end it */

    range.addEventListener('input', function(){ if (anim){ cancelAnimationFrame(anim); anim = null; } set(parseFloat(range.value), true); });
    range.addEventListener('focus', function(){ box.classList.add('is-focus-any'); });
    range.addEventListener('blur', function(){ box.classList.remove('is-focus-any', 'is-focus'); });
    range.addEventListener('keyup', function(){ box.classList.add('is-focus'); });   /* fallback where :has() is unsupported */
    jumps.forEach(function(b){ b.addEventListener('click', function(){ glide(+b.getAttribute('data-to')); }); });

    /* Optional: data-line-fade-under="#id" names text laid over the image
       (the hero copy). The divider line fades to a hairline from just above
       that text down, wherever the text sits at this viewport. */
    var fadeSel = box.getAttribute('data-line-fade-under');
    var fadeEl = fadeSel ? document.querySelector(fadeSel) : null;
    function fade(){
      if (!fadeEl) return;
      var s = stage.getBoundingClientRect(), f = fadeEl.getBoundingClientRect();
      var first = fadeEl.firstElementChild ? fadeEl.firstElementChild.getBoundingClientRect().top : f.top;
      var over = getComputedStyle(fadeEl).position === 'absolute' && first > s.top && first < s.bottom;
      box.style.setProperty('--pnc-line-fade', over ? ((first - 24 - s.top) / s.height * 100).toFixed(2) + '%' : '106%');
      /* keep the handle above that text too: lift it if the stylesheet
         position would bring it within 16 px of the text */
      box.style.removeProperty('--pnc-knob-y');
      if (over){
        var knob = box.querySelector('.pn-compare__knob');
        var kh = (knob && knob.offsetHeight) ? knob.offsetHeight / 2 : 28;
        var want = parseFloat(getComputedStyle(box).getPropertyValue('--pnc-knob-y')) / 100 * s.height;
        var max = first - s.top - kh - 16;
        if (!isNaN(want) && want > max) box.style.setProperty('--pnc-knob-y', Math.max(kh + 12, max).toFixed(0) + 'px');
      }
    }
    if (fadeEl){
      fade();
      if ('ResizeObserver' in window) new ResizeObserver(fade).observe(stage);
      else window.addEventListener('resize', fade);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(fade);
    }

    box.classList.add('is-live');
    set(start);
  }

  function boot(){ [].forEach.call(document.querySelectorAll('.pn-compare'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  window.PNCompare = { init: init };
})();
