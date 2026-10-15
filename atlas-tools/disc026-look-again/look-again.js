/* Progressive enhancement. Without JS: every word is on the page and the
   drawing shows the whole house. Reduced motion: the view changes without
   animating and the dashes are still. */
(function(){
  var svg = document.getElementById('lag-house');
  var canvas = document.getElementById('lag-canvas');
  var field = document.getElementById('look-again');
  var revs = Array.prototype.slice.call(document.querySelectorAll('.lag-rev[data-view]'));
  var chapters = Array.prototype.slice.call(document.querySelectorAll('.lag-ch'));
  var idx = Array.prototype.slice.call(document.querySelectorAll('.lag-index button'));
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var cur = [0,0,900,470], raf = null;

  function parse(v){ return v.split(/\s+/).map(Number); }
  function setView(target){
    if (raf) cancelAnimationFrame(raf);
    if (still){ cur = target; svg.setAttribute('viewBox', target.join(' ')); return; }
    var from = cur.slice(), t0 = performance.now(), dur = 900;
    function step(now){
      var k = Math.min(1,(now-t0)/dur); k = k<.5 ? 4*k*k*k : 1-Math.pow(-2*k+2,3)/2;
      cur = from.map(function(f,i){ return f + (target[i]-f)*k; });
      svg.setAttribute('viewBox', cur.join(' '));
      if (k<1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
  }
  function activate(rev){
    var lit = (rev.getAttribute('data-lit')||'').split(' ').filter(Boolean);
    var show = (rev.getAttribute('data-show')||'').split(' ').filter(Boolean);
    canvas.setAttribute('data-active','');
    svg.querySelectorAll('.lag-part').forEach(function(p){
      p.classList.toggle('is-lit', lit.some(function(c){ return p.classList.contains(c); }));
    });
    svg.querySelectorAll('.lag-show').forEach(function(s){
      s.classList.toggle('is-lit', show.some(function(c){ return s.classList.contains(c); }));
    });
    field.style.setProperty('--lag-warm', rev.getAttribute('data-warm') || 0);
    revs.forEach(function(r){ r.classList.toggle('is-on', r===rev); });
    var ch = rev.closest('.lag-ch'), n = chapters.indexOf(ch);
    idx.forEach(function(b,i){ b.classList.toggle('is-on', i<=n); if (i===n) b.setAttribute('aria-current','step'); else b.removeAttribute('aria-current'); });
    setView(parse(rev.getAttribute('data-view')));
  }
  idx.forEach(function(b){
    b.addEventListener('click', function(){
      var t = document.getElementById(b.getAttribute('data-go'));
      t.scrollIntoView({behavior: still ? 'auto' : 'smooth', block:'start'});
      t.setAttribute('tabindex','-1'); t.focus({preventScroll:true});
    });
  });
  if (!('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if (e.isIntersecting) activate(e.target); });
  }, {rootMargin:'-42% 0px -48% 0px'});
  revs.forEach(function(r){ io.observe(r); });
  /* back above the first revelation: the whole house, nothing dimmed */
  var top = new IntersectionObserver(function(es){
    es.forEach(function(e){
      if (e.isIntersecting && e.boundingClientRect.top > 0){
        canvas.removeAttribute('data-active'); field.style.setProperty('--lag-warm',0);
        svg.querySelectorAll('.lag-show.is-lit').forEach(function(s){ s.classList.remove('is-lit'); });
        idx.forEach(function(b){ b.classList.remove('is-on'); });
        setView([0,0,900,470]);
      }
    });
  }, {threshold:0});
  top.observe(document.querySelector('.lag-open'));
})();
