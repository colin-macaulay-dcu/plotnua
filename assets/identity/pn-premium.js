/* PLOTNUA · PREMIUM TOOLKIT · shared behaviour (Batch 1, founder approval 23 Oct 2026).
   1. IN-PAGE NAVIGATION: every <nav data-pd-nav> marks the section being read
      (aria-current="location") and keeps that link in view inside the pill on a
      phone. Generalised from A Home for Art's PLOTNUA-HOME-FOR-ART-NAV script,
      same behaviour. Reading position only; nothing is stored or sent.
   Loaded only on Premium pages that use it; it does nothing where there is no
   such navigation. */
(function(){
  [].forEach.call(document.querySelectorAll('nav[data-pd-nav]'), function(nav){
    var list = nav.querySelector('ul');
    var links = [].slice.call(nav.querySelectorAll('a[href^="#"]'));
    var targets = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
    var current = -1, queued = false;
    function update(){
      queued = false;
      var line = window.innerHeight * 0.35, idx = -1;
      for (var i = 0; i < targets.length; i++){
        if (targets[i] && targets[i].getBoundingClientRect().top <= line) idx = i;
      }
      if (idx === current) return;
      current = idx;
      links.forEach(function(a, i){
        if (i === idx) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
      });
      if (list && idx === -1) list.scrollLeft = 0;   /* back above the first section: the pill starts at its start */
      if (list && idx > -1 && list.scrollWidth > list.clientWidth){
        var a = links[idx], l = a.offsetLeft, r = l + a.offsetWidth;
        if (l < list.scrollLeft + 12 || r > list.scrollLeft + list.clientWidth - 12) list.scrollLeft = Math.max(0, l - 24);
      }
    }
    function queue(){ if (!queued){ queued = true; window.requestAnimationFrame(update); } }
    window.addEventListener('scroll', queue, {passive:true});
    window.addEventListener('resize', queue);
    update();
  });
})();
