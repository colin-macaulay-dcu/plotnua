/* PlotArt · multi-artist basket · buyer pages, served by the existing public checkout Worker (checkout-public.js).
   NOT DEPLOYED. TEST MODE ONLY. OFF BY DEFAULT.
     GET  /basket                         the basket (kept in this browser only), live prices, delivery and the buyer's details
     GET  /api/basket/items?ids=…         live availability, seller, price and delivery for up to 10 artworks (JSON)
     POST /basket/checkout                prices, checks and reserves every artwork, then opens Stripe's card page (JSON → url)
     GET  /b/<token>                      the basket's verified status, per artist payment
     GET  /b/<token>/return               back from Stripe: PlotArt checks with Stripe and continues
     POST /b/<token>/continue | /cancel   continue after an extra bank check, or cancel before payment
     GET  /b/<token>/authenticate/<ref>   the extra bank check for one artist's payment (Stripe.js, on that artist's account)
     GET  /b/<token>/confirmation/<ref>   the stored purchase confirmation for one artwork, once paid
     GET  /terms/PA-BBT-….html            the installed basket purchase terms
   The token in a basket link is its only key; it is stored hashed. Prices and amounts always come from the server. */
import * as B from './basket.js';
import * as C from './checkout.js';
import * as S from './stripe.js';
import * as G from './basket-staging-gallery.js';

export const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
export const eur = c => c == null ? '—' : '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nonce = () => [...crypto.getRandomValues(new Uint8Array(16))].map(b => b.toString(16).padStart(2, '0')).join('');
const gallery = env => env.GALLERY_ORIGIN || 'https://plotnua.ie';
/* STAGING ONLY: synthetic artwork pages served by this Worker so testers can browse, add to a basket and pay in Stripe TEST
   mode. Never in production or live mode: all three conditions must hold. */
const galleryLink = env => env.STAGING_GALLERY_URL || '/gallery';
export const stagingGallery = env => env.STAGING_GALLERY === 'true' && ['staging', 'test', 'local'].includes(env.ENVIRONMENT) && (() => { const m = S.stripeMode(env); return m.ok && !m.live; })();

function headers(env, n, { stripe = false } = {}) {
  const csp = ["default-src 'none'", `script-src 'nonce-${n}'${stripe ? ' https://js.stripe.com' : ''}`, `connect-src 'self'${stripe ? ' https://api.stripe.com' : ''}`,
    `img-src 'self' ${gallery(env)} data:`, "style-src 'unsafe-inline' https://fonts.googleapis.com", 'font-src https://fonts.gstatic.com',
    ...(stripe ? ['frame-src https://js.stripe.com https://hooks.stripe.com'] : []), "form-action 'self' https://checkout.stripe.com", "frame-ancestors 'none'", "base-uri 'none'"].join('; ');
  return { 'Content-Security-Policy': csp, 'X-Frame-Options': 'DENY', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow' };
}
const STYLE = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<style>
:root{--anth:#1B1C1E;--wall:#27282A;--wall-2:#2C2E30;--raised:#2E3033;--ivory:#EDEBE7;--lime:#D9D7D3;--stone:#B8B6B2;--mute:#A09F9B;--paper:#F4F0EB;--paper-2:#F7F4EF;
--line:#3A3B3E;--line-2:#4A4B4F;--serif:'Instrument Serif',Georgia,'Times New Roman',serif;--sans:'Hanken Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif;--r:18px;--r-sm:12px;
--shadow-art:0 2px 3px rgba(0,0,0,.28),0 14px 28px rgba(0,0,0,.30);color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;background:var(--wall);color:var(--lime);font:17px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
a{color:var(--ivory);text-underline-offset:3px}a:hover{color:var(--paper-2)}:focus-visible{outline:2px solid var(--ivory);outline-offset:3px;border-radius:4px}
h1,h2,h3{font-family:var(--serif);font-weight:400;color:var(--ivory);letter-spacing:-.01em;line-height:1.05;margin:0}
h1{font-size:clamp(38px,6vw,60px);margin:.15em 0 .35em}h2{font-size:clamp(26px,3.4vw,34px);margin:0 0 .5em}h3{font-size:24px}
.top{border-bottom:1px solid var(--line);background:var(--anth)}.top .in{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px clamp(16px,4vw,48px);max-width:1240px;margin:0 auto}
.brand{font-family:var(--serif);font-size:26px;color:var(--ivory);text-decoration:none;letter-spacing:.01em}.brand small{font-family:var(--sans);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--stone);margin-left:10px}
.wrap{max-width:1240px;margin:0 auto;padding:clamp(24px,5vw,56px) clamp(16px,4vw,48px) 96px}
.eyebrow{font-size:12.5px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--stone);margin:0}
.lede{font-size:clamp(17px,1.4vw,19px);color:var(--lime);max-width:62ch}.muted{color:var(--stone)}.small{font-size:14px}
.grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(300px,1fr);gap:clamp(24px,4vw,56px);align-items:start}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
.item{display:grid;grid-template-columns:132px minmax(0,1fr) auto;gap:20px;padding:22px 0;border-top:1px solid var(--line)}
.item:last-child{border-bottom:1px solid var(--line)}
.item .art{width:132px;height:132px;background:var(--anth);border-radius:var(--r-sm);display:flex;align-items:center;justify-content:center;overflow:hidden;box-shadow:var(--shadow-art)}
.item .art img{max-width:100%;max-height:100%;object-fit:contain;display:block}
.item h3 a{color:var(--ivory);text-decoration:none}.item .by{margin:4px 0 6px;color:var(--lime)}.item .meta{font-size:14px;color:var(--stone)}
.item .price{text-align:right;white-space:nowrap;color:var(--ivory);font-size:18px}.item .price .d{display:block;font-size:13.5px;color:var(--stone)}
.sri{border-top:1px solid var(--line);padding:10px 0;font-size:14px;color:var(--stone)}.sri summary{cursor:pointer;color:var(--paper)}.sri summary:focus-visible{outline:2px solid var(--lime);outline-offset:2px}.sri dl{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:4px 14px;margin:10px 0 4px}.sri dt{color:var(--stone)}.sri dd{margin:0;color:var(--paper);overflow-wrap:anywhere}.sri p{margin:6px 0 0}
.item.off{opacity:.62}.item .why{font-size:14px;color:var(--paper);margin:8px 0 0}
@media (max-width:560px){.item{grid-template-columns:88px minmax(0,1fr)}.item .art{width:88px;height:88px}.item .price{grid-column:2;text-align:left}}
.link{background:none;border:0;padding:0;color:var(--stone);font:inherit;font-size:14px;text-decoration:underline;text-underline-offset:3px;cursor:pointer;margin-top:10px}
.panel{background:var(--anth);border:1px solid var(--line);border-radius:var(--r);padding:clamp(20px,3vw,32px);position:sticky;top:20px}
@media (max-width:900px){.panel{position:static}}
.sum{width:100%;border-collapse:collapse;font-size:16px}.sum td{padding:7px 0}.sum td:last-child{text-align:right;color:var(--ivory)}
.sum .tot td{border-top:1px solid var(--line-2);padding-top:14px;font-size:20px;color:var(--ivory)}.sum.only .tot td{border-top:0;padding-top:0}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;width:100%;font:600 16px var(--sans);padding:15px 24px;border-radius:999px;border:1px solid var(--paper);background:var(--paper);color:var(--anth);cursor:pointer;text-decoration:none}
.btn:hover{background:var(--paper-2)}.btn[disabled]{opacity:.5;cursor:not-allowed}.btn.ghost{background:transparent;color:var(--ivory);border-color:var(--line-2)}
.note{background:var(--wall-2);border:1px solid var(--line);border-radius:var(--r-sm);padding:14px 16px;font-size:14.5px;color:var(--lime);margin:16px 0}
.note.test{background:#33302a;border-color:#5a5242;color:#ece2c8}.note.err{border-color:#7a5a52;background:#352a27;color:#f3ddd6}
fieldset{border:0;padding:0;margin:22px 0 0}legend{font-family:var(--serif);font-size:24px;color:var(--ivory);margin-bottom:8px}
label{display:block;font-size:14px;color:var(--stone);margin:12px 0 0}input[type=text],input[type=email],input[type=tel],select{display:block;width:100%;margin-top:6px;padding:12px 14px;border-radius:10px;border:1px solid var(--line-2);background:var(--wall);color:var(--ivory);font:16px var(--sans)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:480px){.two{grid-template-columns:1fr}}
.check{display:flex;gap:12px;align-items:flex-start;color:var(--lime);font-size:14.5px;margin:18px 0}.check input{margin-top:4px;width:18px;height:18px;flex:none}
.steps{list-style:none;padding:0;margin:14px 0 0;font-size:14.5px;color:var(--lime)}.steps li{padding:6px 0 6px 28px;position:relative}.steps li:before{content:attr(data-n);position:absolute;left:0;top:6px;width:20px;height:20px;border-radius:50%;border:1px solid var(--line-2);font-size:12px;text-align:center;line-height:18px;color:var(--stone)}
.state{display:inline-block;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;padding:4px 10px;border-radius:999px;border:1px solid var(--line-2);color:var(--stone)}
.state.captured,.state.paid{color:#d6ecd8;border-color:#4d6b51}.state.declined,.state.failed{color:#f3ddd6;border-color:#7a5a52}.state.action_required{color:#f2e6c8;border-color:#7a6a45}
.empty{padding:40px 0;color:var(--stone)}
h1.bh{font-size:clamp(34px,4.6vw,48px);margin:.1em 0 .7em}.grid.bk{gap:clamp(20px,3.5vw,48px)}
.bk .item{padding:18px 0}.bk .item .meta{margin:2px 0 0}.bk .by{margin:2px 0 6px}.bk .panel{padding:clamp(18px,2.6vw,28px)}
.bk legend{font-family:var(--sans);font-size:12.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--stone);margin:0 0 2px}.bk fieldset{margin-top:18px}
.item.st{grid-template-columns:minmax(0,1fr) auto}.btn.inl{width:auto;max-width:100%;white-space:normal;text-align:center;line-height:1.3}
@media (max-width:560px){.item.st{grid-template-columns:1fr;gap:8px}.item.st .price{grid-column:1;text-align:left;display:flex;gap:12px;align-items:center;flex-wrap:wrap}.item.st .price .d{display:inline}.btn.inl{width:100%}
.top .in{flex-wrap:wrap;row-gap:6px}.brand small{display:none}}footer{border-top:1px solid var(--line);margin-top:56px;padding-top:20px;font-size:13.5px;color:var(--mute)}
</style>`;
const TEST_BANNER = '<p class="note test"><strong>Test mode.</strong> This basket runs in Stripe test mode. No real payment can be taken and no artwork is sold. Use Stripe’s test card 4242 4242 4242 4242.</p>';
const banner = env => { const m = S.stripeMode(env); return (m.ok && m.live) || stagingGallery(env) ? '' : TEST_BANNER; };   // staging shows its own fuller note
export function page(env, title, body, { status = 200, script = '', stripe = false } = {}) {
  const n = nonce();
  return new Response(`<!DOCTYPE html><html lang="en-IE"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">
<title>${esc(title)} · PlotArt</title>${STYLE}</head><body>
<header class="top"><div class="in"><a class="brand" href="${stagingGallery(env) ? esc(galleryLink(env)) : esc(gallery(env)) + '/plotart/'}">PlotArt<small>Artists’ Gallery${stagingGallery(env) ? ' · staging' : ''}</small></a><span class="small"><a href="${stagingGallery(env) ? esc(galleryLink(env)) : esc(gallery(env)) + '/plotart/gallery/'}">Continue browsing</a>&nbsp;&nbsp;·&nbsp;&nbsp;<a href="${esc(String(env.CHECKOUT_ORIGIN || '').replace(/\/$/, ''))}/basket">Basket</a></span></div></header>
${stagingGallery(env) ? '<div class="wrap" style="padding-bottom:0"><p class="note test" style="margin:0"><strong>Private staging.</strong> Synthetic artists and artworks, Stripe test mode. No real payment is taken and nothing is sold. Card <strong>4242 4242 4242 4242</strong> pays; <strong>4000 0000 0000 0341</strong> is declined; <strong>4000 0027 6000 3184</strong> asks for a bank check. Any future expiry, any CVC.</p></div>' : ''}
<main class="wrap">${body}<footer>Each artwork is sold by its artist. PlotArt introduces buyers to artists and is not the seller. Questions: <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a></footer></main>
${stripe ? '<script src="https://js.stripe.com/v3/"></script>' : ''}${script ? `<script nonce="${n}">${script}</script>` : ''}</body></html>`, { status, headers: { 'Content-Type': 'text/html; charset=utf-8', ...headers(env, n, { stripe }) } });
}
const json = (env, o, status = 200, extra = {}) => new Response(JSON.stringify(o), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', ...extra } });

/* ---------------------------------------------------------------- the basket page (client: localStorage list of artwork ids) */
const reEsc = s => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
// images the basket may show: the gallery's published artwork images, and (staging only) the synthetic staging images
const IMG = env => `^${reEsc(gallery(env))}/(plotart/artists/[a-z0-9-]{1,80}/img/[A-Za-z0-9._-]{1,120}${stagingGallery(env) ? '|staging-img/[A-Za-z0-9_-]{1,64}\\.svg' : ''})$`;
function basketPage(env) {
  const counties = B.COUNTIES.map(c => `<option>${esc(c)}</option>`).join('');
  const body = `${banner(env)}<h1 class="bh">Your Basket</h1>
<div class="grid bk"><section aria-label="Artworks"><div id="items"><p class="empty">Loading your basket…</p></div><div id="sellers"></div>
<noscript><p class="note">The basket needs JavaScript. You can still enquire about any artwork from its page in the gallery.</p></noscript></section>
<aside class="panel" aria-label="Order summary"><table class="sum"><tbody>
<tr><td>Artworks</td><td id="t-art">—</td></tr><tr><td>Delivery</td><td id="t-del">—</td></tr><tr class="tot"><td>Total</td><td id="t-tot">—</td></tr></tbody></table>
<form id="buy" novalidate hidden><fieldset><legend>Delivery address</legend>
<label>Full name<input type="text" name="name" autocomplete="name" required maxlength="120"></label>
<label>Email<input type="email" name="email" autocomplete="email" required maxlength="254"></label>
<label>Address<input type="text" name="address_line1" autocomplete="address-line1" required maxlength="120"></label>
<label>Address line 2 (optional)<input type="text" name="address_line2" autocomplete="address-line2" maxlength="120"></label>
<div class="two"><label>Town or city<input type="text" name="town" autocomplete="address-level2" required maxlength="80"></label>
<label>County<select name="county" required><option value="">Choose…</option>${counties}</select></label></div>
<div class="two"><label>Eircode<input type="text" name="eircode" autocomplete="postal-code" maxlength="8"></label>
<label>Telephone (for delivery)<input type="tel" name="phone" autocomplete="tel" required maxlength="30"></label></div></fieldset>
<label class="check"><input type="checkbox" name="accept" id="accept" required><span>I have read the <a id="terms" target="_blank" rel="noopener">purchase terms</a>. Each artwork is sold by its artist.</span></label>
<p id="err" class="note err" role="alert" hidden></p><button class="btn" type="submit" id="pay">Checkout</button></form>
<p id="closed" class="note" hidden>Online purchase is not open at the moment. You can enquire about any artwork from its page.</p></aside></div>`;
  const script = `(function(){'use strict';
var KEY='pa-basket-v1',IMG=new RegExp(${JSON.stringify(IMG(env))}),MAX=10;
function load(){try{var v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v.filter(function(x){return x&&typeof x.id==='string'}).slice(0,MAX):[]}catch(e){return[]}}
function save(v){try{localStorage.setItem(KEY,JSON.stringify(v))}catch(e){}}
var list=load(),q=new URLSearchParams(location.search),add=q.get('add');
if(add&&/^[A-Za-z0-9_-]{1,64}$/.test(add)){var img=q.get('img');if(!list.some(function(x){return x.id===add})&&list.length<MAX)list.push({id:add,img:img&&IMG.test(img)?img:null});save(list);history.replaceState(null,'',location.pathname)}
var eur=function(c){return '€'+(c/100).toLocaleString('en-IE',{minimumFractionDigits:2,maximumFractionDigits:2})};
var el=function(t,a,c){var e=document.createElement(t);if(a)for(var k in a){if(k==='text')e.textContent=a[k];else e.setAttribute(k,a[k])}(c||[]).forEach(function(x){if(x)e.appendChild(x)});return e};
var data=null,form=document.getElementById('buy');
function render(){var box=document.getElementById('items');box.textContent='';
if(!list.length){box.appendChild(el('p',{'class':'empty',text:'Your basket is empty.'}));form.hidden=true;document.getElementById('t-art').textContent=document.getElementById('t-del').textContent=document.getElementById('t-tot').textContent='—';return}
if(!data)return;
data.items.forEach(function(it){var mine=list.filter(function(x){return x.id===it.id})[0]||{};
var art=el('div',{'class':'art'},[mine.img?el('img',{src:mine.img,alt:it.title?('“'+it.title+'”'+(it.artist?' by '+it.artist:'')):'Artwork',loading:'lazy'}):null]);
var rm=el('button',{'class':'link',type:'button',text:'Remove'});rm.addEventListener('click',function(){list=list.filter(function(x){return x.id!==it.id});save(list);refresh()});
var info=el('div',null,[el('h3',null,[it.url?el('a',{href:it.url,text:it.title||'Artwork'}):el('span',{text:it.title||'Artwork'})]),
el('p',{'class':'by',text:it.artist?('by '+it.artist):''}),
it.ok?el('p',{'class':'meta',text:[it.medium,it.size,it.year].filter(Boolean).join(' · ')}):null,
it.ok?el('p',{'class':'meta',text:it.delivery.window+' · '+it.delivery.tracking+' · insured'}):null,
it.ok?el('p',{'class':'meta',text:it.delivery.returns}):null,
!it.ok?el('p',{'class':'why',text:it.reason}):null,rm]);
var price=it.ok?el('div',{'class':'price'},[document.createTextNode(eur(it.price_cents)),el('span',{'class':'d',text:'+ '+eur(it.delivery_cents)+' delivery'})]):el('div',{'class':'price'});
box.appendChild(el('article',{'class':'item'+(it.ok?'':' off')},[art,info,price]))});
renderSellers(data.items.filter(function(i){return i.ok}));
var ok=data.items.filter(function(i){return i.ok}),artists={};ok.forEach(function(i){artists[i.artist]=1});
document.getElementById('t-art').textContent=eur(data.totals.artworks_cents);document.getElementById('t-del').textContent=eur(data.totals.delivery_cents);document.getElementById('t-tot').textContent=eur(data.totals.total_cents);
var can=data.open&&ok.length>0&&ok.length===data.items.length;form.hidden=!data.open||!ok.length;document.getElementById('closed').hidden=data.open;
document.getElementById('pay').disabled=!can;if(data.terms){var t=document.getElementById('terms');t.href='/terms/'+data.terms.doc_id+'.html';t.textContent='purchase terms ('+data.terms.doc_id+')'}
if(ok.length!==data.items.length&&ok.length)showErr('Remove the artworks that are no longer available to continue.');else hideErr()}
function renderSellers(ok){var box=document.getElementById('sellers');box.textContent='';var by={},order=[];
ok.forEach(function(i){var k=i.artist_id||i.artist;if(!by[k]){by[k]={name:i.artist,info:i.seller_info||{},works:[]};order.push(k)}by[k].works.push(i)});
order.forEach(function(k){var g=by[k],s=g.info,dl=el('dl');
var row=function(t,v){if(v){dl.appendChild(el('dt',{text:t}));dl.appendChild(el('dd',{text:v}))}};
row('Seller',s.legal_name+(s.trading_name?' (trading as '+s.trading_name+')':''));row('Address',s.address);row('Returns and complaints',s.returns_address);
row('Email',s.email);row('Telephone',s.phone);row('VAT number',s.vat_number);
var ret=g.works.map(function(i){var r=i.returns||{};return el('p',{text:(g.works.length>1?'“'+(i.title||'Artwork')+'”: ':'Returns: ')+[r.method,r.address?'to '+r.address:'',r.arranged_by?'arranged by '+r.arranged_by:''].filter(Boolean).join(', ')+'.'})});
box.appendChild(el('details',{'class':'sri'},[el('summary',{text:'Seller and returns information · '+(g.name||'Artist')}),dl].concat(g.works.length>1?[el('p',{text:'Returns:'})]:[]).concat(ret)))})}
function showErr(m){var e=document.getElementById('err');e.textContent=m;e.hidden=false}function hideErr(){document.getElementById('err').hidden=true}
function refresh(){if(!list.length){data=null;render();return}fetch('/api/basket/items?ids='+encodeURIComponent(list.map(function(x){return x.id}).join(',')),{credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){data=j;render()}).catch(function(){showErr('Your basket could not be loaded. Please try again.')})}
form.addEventListener('submit',function(e){e.preventDefault();hideErr();var f=form.elements;
if(!document.getElementById('accept').checked){showErr('Please read and accept the purchase terms.');return}
var b={artworks:data.items.filter(function(i){return i.ok}).map(function(i){return i.id}),expected_total_cents:data.totals.total_cents,accept_terms:data.terms&&data.terms.doc_id,
name:f.name.value,email:f.email.value,address_line1:f.address_line1.value,address_line2:f.address_line2.value,town:f.town.value,county:f.county.value,eircode:f.eircode.value,phone:f.phone.value};
var btn=document.getElementById('pay');btn.disabled=true;btn.textContent='Opening checkout…';
fetch('/basket/checkout',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(function(r){return r.json().then(function(j){return{ok:r.ok,j:j}})})
.then(function(r){if(r.ok&&r.j.url){location.href=r.j.url;return}btn.disabled=false;btn.textContent='Checkout';showErr(r.j.error||'Something went wrong. Please try again.');refresh()})
.catch(function(){btn.disabled=false;btn.textContent='Checkout';showErr('Something went wrong. Please try again.')})});
refresh();})();`;
  return page(env, 'Your basket', body, { script });
}

/* ---------------------------------------------------------------- the order's status (one order, however many artists) */
const irishTime = iso => new Date(iso).toLocaleTimeString('en-IE', { timeZone: 'Europe/Dublin', hour: '2-digit', minute: '2-digit' });
function statusPage(env, token, v, msg = null) {
  const pending = ['open', 'authorising', 'capturing'].includes(v.status);
  const rows = v.lines.map(l => `<article class="item st"><div><h3>${esc(l.title || 'Original artwork')}</h3>
<p class="by">by ${esc(l.artist)}</p>
<p class="meta">${eur(l.artwork_cents)} + ${eur(l.delivery_cents)} delivery${l.delivery_window ? ` · delivered in ${esc(l.delivery_window)}` : ''}</p>
${l.action ? `<p><a class="btn inl" href="/b/${esc(token)}/authenticate/${esc(l.order)}">Confirm payment</a></p>` : ''}
${l.confirmation ? `<p class="small"><a href="/b/${esc(token)}/confirmation/${esc(l.order)}">View confirmation</a></p>` : ''}</div>
<div class="price">${eur(l.total_cents)}${l.action ? '<span class="d"><span class="state action_required">Needs confirmation</span></span>' : ''}</div></article>`).join('');
  const head = v.paid ? `<h1>Thank you for your purchase</h1><p class="lede"><span class="state paid">Order confirmed</span></p>
<p class="lede">Your order has been successfully placed.</p>
<p>Your artwork will be prepared for delivery to your nominated address. You’ll receive confirmation of your purchase, and we’ll be in touch with any delivery updates.</p>`
    : v.status === 'action_required' ? `<h1>Confirm your payment</h1><p class="lede">${esc(v.status_text)}</p>
<p class="note">Please confirm by ${esc(irishTime(v.action_deadline))} (Irish time); otherwise your order is cancelled and nothing is charged.</p>`
    : v.ended ? `<h1>Payment not completed</h1><p class="lede">${esc(v.status_text)}</p>${v.resolution ? `<p class="note">${esc(v.resolution)}</p>` : ''}`
    : `<h1>Confirming your order</h1><p class="lede">${esc(v.status_text)}</p>`;
  const body = `${banner(env)}<p class="eyebrow">Order ${esc(v.reference)}</p>${head}
${msg ? `<p class="note err" role="alert">${esc(msg)}</p>` : ''}
<div class="grid"><section>${rows}</section><aside class="panel"><table class="sum only"><tbody><tr class="tot"><td>Total</td><td>${eur(v.total_cents)}</td></tr></tbody></table>
${v.paid ? `<p class="small muted">Delivering to ${esc(v.delivery_to)}</p>` : ''}
${['open', 'action_required'].includes(v.status) ? `<form method="post" action="/b/${esc(token)}/cancel"><button class="btn ghost" type="submit">Cancel order</button></form>` : ''}
${pending ? '<p class="small muted">This page updates automatically.</p>' : ''}</aside></div>`;
  return page(env, v.paid ? 'Order confirmed' : `Order ${v.reference}`, body, { script: pending ? 'setTimeout(function(){location.reload()},4000);' : '' });
}
function authenticatePage(env, token, a) {
  const body = `${banner(env)}<p class="eyebrow">Order ${esc(a.order)}</p><h1>Confirm your payment</h1>
<p class="lede">Your bank asks you to confirm a payment of ${eur(a.amount_cents)}${a.title ? ` for ${esc(a.title)}` : ''}. Your bank’s own screen will open.</p>
<p id="msg" class="note" role="status">Opening your bank’s check…</p><p><a class="btn ghost" style="width:auto" href="/b/${esc(token)}">Back to your order</a></p>`;
  const script = `(function(){var m=document.getElementById('msg');
var s=Stripe(${JSON.stringify(a.publishable_key)},{stripeAccount:${JSON.stringify(a.account)}});
s.confirmCardPayment(${JSON.stringify(a.client_secret)},${a.payment_method ? `{payment_method:${JSON.stringify(a.payment_method)}}` : '{}'}).then(function(r){
m.textContent=r.error?('Not confirmed: '+(r.error.message||'please try again')):'Confirmed. Continuing…';
fetch(${JSON.stringify(`/b/${token}/continue`)},{method:'POST',credentials:'same-origin'}).finally(function(){location.href=${JSON.stringify(`/b/${token}`)}})})})();`;
  return page(env, 'Confirm payment', body, { script, stripe: true });
}

export async function handle(req, env, url) {
  const p = url.pathname, m = req.method;
  let mm;
  if (stagingGallery(env) && m === 'GET') {
    // TEST: the synthetic gallery pages live in the TEST Studio (behind Access); this Worker serves only their images
    if (env.ENVIRONMENT === 'test' && !/^\/staging-img\//.test(p)) { /* not served here */ }
    else { const r = await G.route(env, url, { page, esc, eur }); if (r) return r; }
  }
  if (p === '/basket' && m === 'GET') {
    if (!(await B.installed(env))) return page(env, 'Not available', '<h1>Not available</h1><p>Online purchase is not available.</p>', { status: 404 });
    return basketPage(env);
  }
  if (p === '/api/basket/items' && m === 'GET') {
    const ids = String(url.searchParams.get('ids') || '').split(',').filter(Boolean);
    const out = await B.preview(env, ids);
    // the gallery (plotnua.ie) may ask which works can be added to a basket; nothing else is exposed cross-origin
    return json(env, out, 200, { 'Access-Control-Allow-Origin': gallery(env), 'Vary': 'Origin' });
  }
  if (p === '/basket/checkout' && m === 'POST') {
    if (req.headers.get('Origin') !== env.CHECKOUT_ORIGIN) return json(env, { error: 'Refused' }, 403);
    try {
      const b = await req.json().catch(() => null);
      const r = await B.openBasket(env, b);
      return json(env, { url: r.url, reference: r.reference });
    } catch (e) {
      if (e instanceof C.Bad) return json(env, { error: e.message, artwork: e.artwork || null }, e.status || 400);
      throw e;
    }
  }
  if ((mm = p.match(/^\/terms\/(PA-BBT-[0-9A-Z-]{4,20})\.html$/)) && m === 'GET') {
    const t = await B.currentDoc(env, 'buyer_basket_terms').catch(() => null);
    if (!t || t.doc_id !== mm[1]) return page(env, 'Not found', '<h1>Not found</h1>', { status: 404 });
    return new Response(t.html, { headers: { 'Content-Type': 'text/html; charset=utf-8', ...headers(env, nonce()), 'X-Document-SHA256': t.html_sha256 } });
  }
  if ((mm = p.match(/^\/b\/([0-9a-z]{48})(?:\/(return|continue|cancel|authenticate|confirmation)(?:\/(PA-O-[0-9A-Z-]{6,30}))?)?$/))) {
    if (!(await B.installed(env))) return page(env, 'Not available', '<h1>This page is not available.</h1>', { status: 404 });
    const [, token, act, ref] = mm;
    const notFound = () => page(env, 'Not found', '<h1>This basket is not available.</h1>', { status: 404 });
    if (!act && m === 'GET') { const v = await B.buyerView(env, token); return v ? statusPage(env, token, v, url.searchParams.get('cancelled') ? 'You left the secure payment page. Nothing has been charged.' : null) : notFound(); }
    if (act === 'return' && m === 'GET') { const v = await B.buyerContinue(env, token); return v ? new Response(null, { status: 303, headers: { Location: `/b/${token}`, 'Cache-Control': 'no-store' } }) : notFound(); }
    if ((act === 'continue' || act === 'cancel') && m === 'POST') {
      if (req.headers.get('Origin') !== env.CHECKOUT_ORIGIN) return page(env, 'Refused', '<h1>Refused</h1>', { status: 403 });
      const v = act === 'cancel' ? await B.buyerCancel(env, token) : await B.buyerContinue(env, token);
      return v ? new Response(null, { status: 303, headers: { Location: `/b/${token}`, 'Cache-Control': 'no-store' } }) : notFound();
    }
    if (act === 'authenticate' && ref && m === 'GET') {
      try { const a = await B.actionFor(env, token, ref); return a ? authenticatePage(env, token, a) : new Response(null, { status: 303, headers: { Location: `/b/${token}` } }); }
      catch (e) { if (e instanceof C.Bad) return page(env, 'Not available', `<h1>${esc(e.message)}</h1>`, { status: e.status }); throw e; }
    }
    if (act === 'confirmation' && ref && m === 'GET') {
      const c = await B.confirmationFor(env, token, ref);
      if (!c) return page(env, 'Not found', '<h1>No confirmation is available yet.</h1>', { status: 404 });
      return new Response(c.body, { headers: { 'Content-Type': 'text/plain; charset=utf-8', 'X-Document-SHA256': c.sha256, ...headers(env, nonce()) } });
    }
  }
  return null;
}
