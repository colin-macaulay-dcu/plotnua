/* PlotArt wall-size comparison. Pure centimetre geometry; no requests or storage. */
(function () {
  'use strict';
  var defaults = {mode:'furniture',reference:200,room:260,width:140,height:90,theme:'chalk'};
  var limits = {reference:[30,1000],room:[100,600],width:[5,1000],height:[5,600]};
  function measure(raw) {
    var s = {mode:raw.mode,theme:raw.theme}, errors = {};
    if (s.mode !== 'furniture' && s.mode !== 'wall') errors.mode = 'Choose a space type.';
    if (['chalk','green','clay'].indexOf(s.theme) < 0) errors.theme = 'Choose a wall colour.';
    Object.keys(limits).forEach(function(k) {
      var n = Number(raw[k]), l = limits[k];
      if (String(raw[k]).trim() === '' || !Number.isFinite(n) || n < l[0] || n > l[1]) errors[k] = 'Enter a value from '+l[0]+' to '+l[1]+' cm.';
      else s[k] = Math.round(n * 10) / 10;
    });
    if (Object.keys(errors).length) return {valid:false,errors:errors};
    var ww = s.mode === 'furniture' ? Math.max(300,s.reference+100,s.width+40) : s.reference;
    var y = s.mode === 'furniture' ? s.room-95-s.height : (s.room-s.height)/2;
    return {valid:true,state:s,wallWidth:ww,wallHeight:s.room,x:(ww-s.width)/2,y:y,
      fits:s.width<=ww && y>=0 && y+s.height<=s.room,
      low:Math.round(s.reference*2/3),high:Math.round(s.reference*3/4)};
  }
  function encode(s) {
    var params = new URLSearchParams();
    ['mode','reference','room','width','height','theme'].forEach(function(k){params.set(k,String(s[k]));});
    return '#'+params.toString();
  }
  function decode(hash) {
    var p = new URLSearchParams(hash.replace(/^#/,'')), raw = Object.assign({},defaults);
    Object.keys(defaults).forEach(function(k){if(p.has(k))raw[k]=p.get(k);});
    var m = measure(raw);return m.valid ? m.state : Object.assign({},defaults);
  }
  var api = {measure:measure,encode:encode,decode:decode,defaults:defaults};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  if(typeof document==='undefined')return;
  var app=document.querySelector('[data-size-app]');if(!app)return;
  var el=function(id){return document.getElementById('size-'+id);};
  var current=decode(location.hash), lastValid=current;
  function populate(s){['mode','reference','room','width','height'].forEach(function(k){el(k).value=s[k];});current.theme=s.theme;}
  function attrs(id,values){Object.keys(values).forEach(function(k){el(id).setAttribute(k,String(values[k]));});}
  function display(){
    var raw={theme:current.theme};['mode','reference','room','width','height'].forEach(function(k){raw[k]=el(k).value;});
    var m=measure(raw),error=el('error');
    ['reference','room','width','height'].forEach(function(k){el(k).setAttribute('aria-invalid',m.valid || !m.errors[k]?'false':'true');});
    if(!m.valid){error.hidden=false;error.textContent='Check your measurements. '+Object.keys(m.errors).map(function(k){return m.errors[k];}).filter(function(v,i,a){return a.indexOf(v)===i;}).join(' ');el('share').disabled=true;return;}
    error.hidden=true;el('share').disabled=false;current=m.state;lastValid=current;
    var s=m.state, furniture=s.mode==='furniture', dim=s.width+' × '+s.height+' cm', ww=m.wallWidth;
    el('reference-label').textContent=(furniture?'Furniture width':'Clear wall width')+' (cm)';
    el('reference-help').textContent=furniture?'Measure the furniture from one outer edge to the other.':'Measure the usable wall width between obstructions.';
    document.querySelector('[data-size-scene]').setAttribute('data-theme',s.theme);
    attrs('scene',{viewBox:'-20 -20 '+(ww+40)+' '+(s.room+40)});
    attrs('wall',{width:ww,height:s.room});attrs('floor',{d:'M0 '+(s.room-10)+'H'+ww});
    el('furniture').style.display=furniture?'':'none';
    attrs('sofa',{x:(ww-s.reference)/2,y:s.room-75,width:s.reference,height:65});
    attrs('sofa-detail',{d:'M'+((ww-s.reference)/2+5)+' '+(s.room-42)+'H'+((ww+s.reference)/2-5)+' M'+(ww/2)+' '+(s.room-70)+'V'+(s.room-42)});
    attrs('furniture-caption',{x:ww/2,y:s.room-25});el('furniture-caption').textContent='Furniture · '+s.reference+' cm';
    el('frame').style.display=m.fits?'':'none';
    attrs('frame-outer',{x:m.x,y:m.y,width:s.width,height:s.height});
    attrs('frame-paper',{x:m.x+2,y:m.y+2,width:Math.max(1,s.width-4),height:Math.max(1,s.height-4)});
    attrs('frame-caption',{x:ww/2,y:m.y+s.height/2});el('frame-caption').textContent=dim;
    el('dimensions').textContent=dim;
    el('svg-desc').textContent=m.fits?(dim+' artwork outline '+(furniture?'above furniture '+s.reference+' cm wide.':'on a clear wall '+s.reference+' cm wide.')):'The entered size extends beyond the illustrated wall; the frame outline is hidden.';
    el('range').textContent=furniture?'Try '+m.low+'–'+m.high+' cm wide':'Compare with '+s.reference+' cm of wall';
    el('explanation').textContent=furniture?'For furniture '+s.reference+' cm wide, two-thirds to three-quarters gives a useful range to compare. Your entered artwork is '+s.width+' cm wide.':'Your entered artwork is '+s.width+' cm wide. Compare the breathing space around it with your actual wall and the effect you want.';
    el('warning').hidden=m.fits;
    el('warning').textContent=m.fits?'':'This size extends beyond the illustrated wall. Its outline is hidden. Reduce the artwork dimensions or check your space measurements.';
    el('assumptions').textContent=furniture?'The furniture is illustrated at 75 cm high with a 20 cm gap below the artwork. Check the actual furniture, clear wall space, ceiling and fixings before choosing or hanging a work.':'The artwork is centred on the illustrated clear wall. Doors, sockets, radiators and other obstructions are not shown. Check the actual clear space and fixings.';
    document.querySelectorAll('[data-size-theme]').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.sizeTheme===s.theme?'true':'false');});
    document.querySelectorAll('[data-size-ratio]').forEach(function(b){b.setAttribute('aria-pressed',Math.abs(s.width-Math.round(s.reference*Number(b.dataset.sizeRatio)))<0.1?'true':'false');});
    el('share-status').textContent='';el('share-link').hidden=true;
  }
  populate(current);app.hidden=false;display();
  ['mode','reference','room','width','height'].forEach(function(k){el(k).addEventListener(k==='mode'?'change':'input',display);});
  document.querySelectorAll('[data-size-ratio]').forEach(function(b){b.addEventListener('click',function(){if(!measure({mode:el('mode').value,theme:current.theme,reference:el('reference').value,room:el('room').value,width:el('width').value,height:el('height').value}).valid)return;el('width').value=Math.round(Number(el('reference').value)*Number(b.dataset.sizeRatio));display();});});
  document.querySelectorAll('[data-size-theme]').forEach(function(b){b.addEventListener('click',function(){current.theme=b.dataset.sizeTheme;display();});});
  el('reset').addEventListener('click',function(){current=Object.assign({},defaults);populate(current);display();});
  el('share').addEventListener('click',async function(){
    var link=location.origin+location.pathname+encode(lastValid);
    try{if(!navigator.clipboard)throw new Error('Clipboard unavailable');await navigator.clipboard.writeText(link);el('share-status').textContent='Comparison link copied. It includes your measurements and wall-colour choice.';}
    catch(e){el('share-link').value=link;el('share-link').hidden=false;el('share-link').focus();el('share-link').select();el('share-status').textContent='Copy the comparison link shown below.';}
  });
  window.addEventListener('hashchange',function(){if(!/(?:^#|&)(mode|reference|room|width|height|theme)=/.test(location.hash))return;current=decode(location.hash);populate(current);display();});
}());
