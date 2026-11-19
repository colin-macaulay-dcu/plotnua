'use strict';
const artists=['Rowan Studio','Alder Studio'];
const works=[
 {title:'Estuary, first light',artist:0,price:1450,size:'60 × 50 cm',medium:'Monotype on paper',description:'Pale bands of green and silver settle into the dark edge of the estuary.'},
 {title:'Estuary, slack water',artist:0,price:1250,size:'55 × 45 cm',medium:'Monotype on paper',description:'A companion study of the same shoreline, with the tide drawn back.'},
 {title:'Last light on the hill',artist:1,price:2100,size:'76 × 62 cm',medium:'Mixed media on panel',description:'Dry marks in clay, ochre and plum trace the evening contours of a hillside.'}
];
const rates=[35,45], key='plotart-private-shop-v1';
const empty=()=>({cart:[],orders:[],collection:[false,false]});
let state;try{state=JSON.parse(localStorage.getItem(key))||empty()}catch{state=empty()}
const main=document.querySelector('main'),drawer=document.querySelector('dialog'),panel=document.querySelector('#panel');
const money=n=>new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(n);
const available=id=>!state.orders.some(o=>o.items.includes(id));
const itemsFor=a=>state.cart.filter(id=>works[id].artist===a&&available(id));
const delivery=a=>state.collection[a]?0:rates[a];
const total=(ids,fee)=>ids.reduce((sum,id)=>sum+works[id].price,fee);
const image=id=>'<img src="work-'+id+'.webp" alt="'+works[id].title+'">';
const frame=id=>'<a class="art" aria-label="View '+works[id].title+'" href="#work/'+id+'">'+image(id)+'</a>';
const addButton=id=>'<button data-add="'+id+'" '+(!available(id)?'disabled':'')+'>'+(!available(id)?'Purchased in preview':state.cart.includes(id)?'View in basket':'Add to basket')+'</button>';
const line=(id,remove=false)=>'<div class="line">'+image(id)+'<div>'+works[id].title+'<br><small>'+works[id].size+'</small>'+(remove?'<br><button class="text" data-remove="'+id+'">Remove</button>':'')+'</div><strong>'+money(works[id].price)+'</strong></div>';
function save(){localStorage.setItem(key,JSON.stringify(state))}
function basketContent(){
 const groups=artists.map((name,a)=>{const ids=itemsFor(a);if(!ids.length)return '';
 return '<section class="group"><h3>'+name+'</h3>'+ids.map(id=>line(id,true)).join('')+'<p class="small"><label>Delivery or collection <select data-ship="'+a+'"><option value="deliver">Irish delivery · '+money(rates[a])+'</option><option value="collect" '+(state.collection[a]?'selected':'')+'>Studio collection · Free</option></select></label></p><div class="row"><strong>'+money(total(ids,delivery(a)))+'</strong></div></section>'});
 const heading='<h2>Your basket</h2>';
 if(!state.cart.length)return heading+'<p>Your basket is empty.</p><button class="text" data-close>Continue browsing</button>';
 return heading+'<p>One checkout for all your works. Choose delivery or collection for each artist.</p>'+groups.join('')+'<div class="checkout-bar"><button data-checkout>Checkout · '+money(basketTotal())+'</button></div><button class="text" data-close>Continue browsing</button>';
}
function basketTotal(){return artists.reduce((sum,_,a)=>itemsFor(a).length?sum+total(itemsFor(a),delivery(a)):sum,0)}
function openBasket(){panel.innerHTML=basketContent();if(!drawer.open)drawer.showModal()}
function receipt(o){return '<section class="sheet"><h3>'+artists[o.artist]+'</h3><p class="meta">Order '+o.ref+' · Artist fulfilment order</p>'+o.items.map(id=>line(id)).join('')+'<p>'+o.method+' · '+money(o.fee)+'</p><strong>Total paid '+money(total(o.items,o.fee))+'</strong></section>'}
async function startPayment(button){
 const status = document.querySelector('#payment-status');
 const items = state.cart.filter(available);
 const signature = JSON.stringify([items, state.collection]);
 if (!state.attempt || state.attempt.signature !== signature) {
   state.attempt = {signature, id:crypto.randomUUID()};
   save();
 }
 button.disabled = true;
 status.textContent = 'Opening Stripe sandbox checkout…';
 try {
   const r = await fetch('/api/basket', {method:'POST', headers:{'Content-Type':'application/json'},
     body:JSON.stringify({items,collection:state.collection,attempt:state.attempt.id})});
   const data = await r.json();
   if (!r.ok) throw Error(data.error);
   location.assign(data.url);
 } catch(e) {
   status.textContent = e.message || 'Unable to open checkout. Please retry.';
   button.disabled = false;
 }
}
async function confirmReturn(id){
 main.innerHTML='<h1>Checking your payment</h1><p role="status">Waiting for Stripe to confirm this order.</p>';
 try {
   const r = await fetch('/api/basket/confirmation?session='+encodeURIComponent(id));
   const result = await r.json();
   if (!r.ok || result.pending) throw Error(result.error || 'Payment confirmation is pending.');
   const reference = result.reference;
   if (!state.orders.some(o=>o.purchase===reference)) {
     const purchased = new Set(result.groups.flatMap(g=>g.items));
     state.orders.push(...result.groups.map(g=>({ref:reference+'-'+(g.artist+1),purchase:reference,
       artist:g.artist,items:g.items,fee:g.fee/100,method:g.method,verified:true})));
     state.cart=state.cart.filter(id=>!purchased.has(id));
     delete state.attempt;
     save();
   }
   history.replaceState(null,'','/#purchase/'+reference);
   render();
 } catch(e) {
   main.innerHTML='<h1>Payment confirmation</h1><p role="status"></p><button data-recheck>Check again</button>';
   main.querySelector('[role=status]').textContent=e.message;
 }
}
function render(){
 const session=new URLSearchParams(location.search).get('session_id');
 if(session){confirmReturn(session);return}

 const [page,arg]=location.hash.slice(1).split('/'),id=Number(arg);
 document.querySelector('#basket').textContent='Basket ('+state.cart.length+')';
 if(page==='work'&&works[id]){
 const w=works[id];main.innerHTML='<a href="#shop">All artworks</a><div class="detail">'+frame(id)+'<section><p>'+artists[w.artist]+'</p><h1>'+w.title+'</h1><p>'+w.medium+' · '+w.size+'</p><h2>'+money(w.price)+'</h2><p>'+w.description+'</p><div class="actions">'+addButton(id)+'</div><details><summary>Delivery and collection</summary><p>Sample delivery within Ireland costs '+money(rates[w.artist])+' per artist order. Studio collection is free.</p></details><details><summary>About this work</summary><p>One original available in this simulated collection.</p></details></section></div>';return}
 if((page==='checkout'||page==='review')&&state.cart.length){
  const groups=artists.map((name,a)=>{
   const ids=itemsFor(a);
   if(!ids.length)return '';
   return '<section class="sheet"><h2>'+name+'</h2>'+ids.map(id=>line(id)).join('')+'<p>'+(state.collection[a]?'Studio collection':'Irish delivery')+' · '+money(delivery(a))+'</p></section>';
  });
  main.innerHTML='<button class="text" data-basket>Edit basket</button><h1>Checkout</h1>'+groups.join('')+'<section class="sheet"><p>Total including delivery <strong>'+money(basketTotal())+'</strong></p><p>Private preview · Stripe test payment</p><p id="payment-status" role="status"></p><button data-pay>Continue to Stripe · '+money(basketTotal())+'</button></section>';return}
 if(page==='purchase'){
  const orders=state.orders.filter(o=>o.purchase===arg && o.purchase);
  if(orders.length){const sum=orders.reduce((v,o)=>v+total(o.items,o.fee),0);
   main.innerHTML='<h1>Purchase confirmed</h1><p>One '+(orders[0].verified?'Stripe sandbox':'simulated preview')+' payment of <strong>'+money(sum)+'</strong> · '+arg+'</p>'+orders.map(receipt).join('')+'<a href="#orders">View orders</a>';return}
 }
 if(page==='confirmation'&&state.orders.some(o=>o.ref===arg)){
 const o=state.orders.find(o=>o.ref===arg);main.innerHTML='<h1>Order confirmed</h1>'+receipt(o)+(state.cart.length?'<p>Your other artist’s works are still in your basket.</p><button data-basket>Continue to remaining order</button>':'<p>All selected works are paid for in this preview.</p><a class="btn" href="#orders">View orders</a>');return}
 if(page==='orders'){const filter=arg??'buyer';const view=state.orders.filter(o=>filter==='buyer'||filter==='founder'||String(o.artist)===filter);main.innerHTML='<h1>Orders</h1><label>Preview as <select id="role">'+[['buyer','Buyer'],['0','Rowan Studio'],['1','Alder Studio'],['founder','Founder desk']].map(([v,n])=>'<option value="'+v+'" '+(v===filter?'selected':'')+'>'+n+'</option>').join('')+'</select></label>'+(view.length?view.map(receipt).join(''):'<p>No orders yet in this view.</p>');return}
 main.innerHTML='<div class="intro"><p class="pa-eyebrow">PlotArt · Available artworks</p><h1>Shop original art</h1><p class="lede">Explore original works from two sample studios.</p></div><div class="grid">'+works.map((w,i)=>'<article>'+frame(i)+'<p class="meta">'+artists[w.artist]+'</p><h3><a href="#work/'+i+'">'+w.title+'</a></h3><p>'+w.medium+' · '+w.size+'</p><div class="row"><strong>'+money(w.price)+'</strong>'+addButton(i)+'</div></article>').join('')+'</div>';
}
document.addEventListener('click',e=>{
 const el=e.target.closest('button');if(!el)return;const d=el.dataset;
 if('recheck' in d){render();return}
 if(el.id==='close'||'close' in d){drawer.close();return}
 if(el.id==='basket'||'basket' in d){openBasket();return}
 if('checkout' in d){drawer.close();location.hash='checkout';render();return}
 if('add' in d){const id=Number(d.add);if(available(id)&&!state.cart.includes(id))state.cart.push(id);save();render();openBasket();return}
 if('remove' in d){state.cart=state.cart.filter(id=>id!==Number(d.remove));save();render();openBasket();return}
 if('pay' in d){
  startPayment(el);return}
 if(el.id==='reset'&&confirm('Clear the sample orders and start again?')){state=empty();save();location.hash='shop';render()}
});
document.addEventListener('change',e=>{if(e.target.id==='role'){location.hash='orders/'+e.target.value;return}if(e.target.hasAttribute('data-ship')){state.collection[Number(e.target.dataset.ship)]=e.target.value==='collect';save();openBasket()}});
window.addEventListener('hashchange',()=>{render();window.scrollTo(0,0)});render();
