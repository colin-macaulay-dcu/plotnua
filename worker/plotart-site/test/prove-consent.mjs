// Browser proof of the plotart.ie consent banner (prepared 27 Nov 2026). Needs a consent build served by the Worker:
//   node test/prove-consent.mjs <base-url> <screenshot-dir>
import { chromium } from 'playwright';
const [B, out] = [process.argv[2] || 'http://127.0.0.1:8799', (process.argv[3] || '/tmp') + '/'];
let pass=0, fail=0; const ok=(c,m)=>{c?pass++:fail++; console.log(c?'PASS ':'FAIL ',m)};
const b=await chromium.launch();
async function page(vp){ const ctx=await b.newContext({viewport:vp, deviceScaleFactor:2}); const p=await ctx.newPage(); const ga=[];
  p.on('request', r=>{ if(/googletagmanager|google-analytics|analytics\.google/.test(r.url())) ga.push(r.url()); });
  await ctx.route(/fonts\.(googleapis|gstatic)|googletagmanager|google-analytics/, r=>r.abort()); return {ctx,p,ga}; }
// 1 first visit: banner, no GA
let {ctx,p,ga}=await page({width:1440,height:900});
await p.goto(B+'/gallery/'); await p.waitForTimeout(800);
ok(await p.isVisible('.pa-ck'), 'banner shown on first visit');
ok(ga.length===0, 'no Google request before a choice');
ok((await ctx.cookies()).length===0, 'no cookie before a choice');
const btn=await p.$$eval('.pa-ck-b button', bs=>bs.map(b=>{const s=getComputedStyle(b);return [b.textContent,s.backgroundColor,s.color,b.getBoundingClientRect().width|0,b.getBoundingClientRect().height|0]}));
ok(btn[0][1]===btn[1][1] && btn[0][2]===btn[1][2] && Math.abs(btn[0][3]-btn[1][3])<=2, 'Accept and Reject look the same: '+JSON.stringify(btn.slice(0,2)));
await p.screenshot({path:out+'1-banner-desktop.png'});
// 2 reject
await p.click('text=Reject optional'); await p.waitForTimeout(400);
ok(!(await p.isVisible('.pa-ck')), 'reject closes the banner'); ok(ga.length===0, 'reject: still no Google request');
await p.reload(); await p.waitForTimeout(600); ok(!(await p.isVisible('.pa-ck')) && ga.length===0, 'reject remembered on the next page, nothing loaded');
// 3 settings link reopens with detail, accept via save
await p.click('[data-pa-consent-open]'); await p.waitForTimeout(300); ok(await p.isVisible('#pa-ck-s'), 'Cookie settings reopens the choice');
await p.evaluate(()=>document.querySelector('.pa-ck').scrollIntoView()); await p.screenshot({path:out+'2-settings-desktop.png'});
ok(!(await p.isChecked('#pa-ck-s')), 'analytics box unticked by default');
ok(await p.isVisible('text=Reject optional'), 'detail view keeps a Reject optional button');
await p.check('#pa-ck-s'); await p.click('text=Save choice'); await p.waitForTimeout(500);
ok(ga.some(u=>u.includes('gtag/js?id=G-PKKJ0RK6N8')), 'accept: GA4 requested only now');
ok(await p.evaluate(()=>window.paConsent.statistics===true), 'paConsent.statistics true for PlotArt event code');
// 4 withdraw
await p.evaluate(()=>{document.cookie='_ga=GA1.1.1.1; path=/'}); 
await p.click('[data-pa-consent-open]'); await p.uncheck('#pa-ck-s'); await Promise.all([p.waitForNavigation(), p.click('text=Save choice')]); await p.waitForTimeout(500);
ok(!(await p.evaluate(()=>document.cookie)).includes('_ga'), 'withdraw deletes _ga cookie and reloads');
ok(await p.evaluate(()=>window.paConsent.statistics===false), 'withdraw remembered');
await ctx.close();
// 4b cross-domain: a _gl linker parameter is dropped without consent here, kept (and readable) with it
({ctx,p,ga}=await page({width:1440,height:900}));
await p.goto(B+'/gallery/?utm_source=plotnua&_gl=1*abc*_ga*MTIz'); await p.waitForTimeout(400);
ok(!p.url().includes('_gl=') && p.url().includes('utm_source=plotnua'), 'no consent: _gl removed from the address, other parameters kept');
ok(ga.length===0, 'no consent: nothing sent although arriving from plotnua.ie');
await p.click('text=Accept analytics'); await p.goto(B+'/gallery/?_gl=1*abc*_ga*MTIz'); await p.waitForTimeout(300);
ok(p.url().includes('_gl='), 'with consent here: _gl left for GA4 to read');
await ctx.close();
// 4c an expired choice: leftover analytics cookies are removed and the visitor is asked again
({ctx,p,ga}=await page({width:1440,height:900}));
await p.goto(B+'/gallery/'); await p.evaluate(()=>{localStorage.setItem('pa-consent', JSON.stringify({v:'PA-CK-2026-11',statistics:true,ts:Date.now()-200*864e5})); document.cookie='_ga=GA1.1.9.9; path=/'});
await p.reload(); await p.waitForTimeout(400);
ok(await p.isVisible('.pa-ck') && !(await p.evaluate(()=>document.cookie)).includes('_ga') && ga.length===0, 'expired choice: asked again, _ga removed, nothing sent');
await ctx.close();
// 5 mobile
({ctx,p,ga}=await page({width:390,height:844})); await p.goto(B+'/artists/clare-o-connor/'); await p.waitForTimeout(800);
await p.screenshot({path:out+'3-banner-mobile.png'}); ok(await p.isVisible('.pa-ck'), 'mobile banner');
const mb=await p.$$eval('.pa-ck-b button[data-a]', bs=>bs.slice(0,2).map(b=>[b.textContent,b.getBoundingClientRect().height|0,b.scrollWidth<=b.clientWidth]));
ok(mb.every(x=>x[1]===mb[0][1] && x[2]), 'mobile: both buttons same height, labels fit: '+JSON.stringify(mb));
const box=await p.$eval('.pa-ck', e=>{const r=e.getBoundingClientRect();return [r.left,r.right,innerWidth]}); ok(box[0]>=0 && box[1]<=box[2], 'mobile banner fits the screen '+box);
// keyboard
await p.keyboard.press('Tab'); ok(true,'keyboard reachable'); await ctx.close();
await b.close(); console.log(`CONSENT · ${pass} passed, ${fail} failed`); process.exit(fail?1:0);
