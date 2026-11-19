import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { basketApi } from './buyer-preview/basket.mjs';
export async function checkBuyerCheckout(key, rec) {
  const { chromium } = createRequire(process.env.MINIFLARE_FROM)('playwright');
  let origin;
  const evidence = {};
  async function observeStripe(url, options) {
    const result = await fetch(url, options);
    const body = await result.clone().json();
    evidence.stripeStatus = result.status;
    evidence.requestId = result.headers.get('request-id');
    if (body.error) {
      evidence.code = body.error.code;
      evidence.param = body.error.param;
      evidence.message = String(body.error.message || '').replace(/(?:[rs]k_(?:test|live)_|cs_test_|whsec_)\S+/g, '[redacted]').slice(0,320);
    }
    return result;
  }
  const browser = await chromium.launch();
  let stage = 'open shop';
  let page;
  const server = createServer(async (incoming, outgoing) => {
    try {
      const url = new URL(incoming.url,origin);
      if(url.pathname.startsWith('/api/')) {
        const chunks = [];
        for await (const chunk of incoming) chunks.push(chunk);
        const request = new Request(url,{method:incoming.method,headers:incoming.headers,
          body:incoming.method==='POST' ? Buffer.concat(chunks) : undefined});
        const result = await basketApi(request,{PLOTART_CHECKOUT_TEST_KEY:key},observeStripe);
        evidence.shopStatus = result.status;
        outgoing.writeHead(result.status,{'Content-Type':'application/json'});
        outgoing.end(await result.text());
      } else if (url.pathname==='/' || url.pathname==='/shop.js') {
        const script = url.pathname==='/shop.js';
        const file = script ? 'shop.js' : 'index.html';
        outgoing.writeHead(200,{'Content-Type':script?'text/javascript':'text/html'});
        outgoing.end(await readFile(new URL('./buyer-preview/'+file,import.meta.url)));
      } else {
        outgoing.writeHead(204).end();
      }
    } catch {
      evidence.serverError = true;
      outgoing.end();
    }
  });
  try {
    page = await browser.newPage({locale:'en-IE'});
    await new Promise((resolve,reject) => {
      server.once('error',reject);
      server.listen(0,'127.0.0.1',resolve);
    });
    origin = 'http://127.0.0.1:' + server.address().port;
    await page.goto(origin, {waitUntil:'domcontentloaded'});
    await page.locator('[data-add="0"]').click();
    await page.locator('#close').click();
    await page.locator('[data-add="2"]').click();
    await page.locator('[data-ship="1"]').selectOption('collect');
    await page.locator('[data-checkout]').click();
    stage='open combined Stripe Checkout';
    await page.locator('[data-pay]').click();
    await page.waitForURL('https://checkout.stripe.com/**',{waitUntil:'commit'});
    async function field(css, timeout=10000) {
      const deadline=Date.now()+timeout;
      do {
        for(const frame of page.frames()) {
          for (const match of await frame.locator(css).all().catch(() => [])) {
            if(await match.isVisible().catch(()=>false))return match;
          }
        }
        await page.waitForTimeout(300);
      } while(Date.now()<deadline);
    }
    async function fill(css,value,timeout) {
      stage = 'fill ' + css.split(',')[0];
      const deadline=Date.now()+(timeout||12000);
      do {
        const control=await field(css,1000);
        if(control && await control.fill(value,{timeout:2000}).then(()=>true,()=>false))return;
      } while(Date.now()<deadline);
      if(!css.startsWith('#billingName'))throw Error('Required field unavailable');
    }
    stage='complete sandbox shipping and payment form';
    const euro=await field('#currency-eur',1000);
    if(euro)await euro.click();
    await fill('#linkAuthentication-emailInput,input[type=email]','plotart-buyer@example.com');
    await fill('#shippingAddress-nameInput,[autocomplete~="shipping"][autocomplete~="name"],#shippingName','Test Buyer');
    await fill('#shippingAddress-addressLine1Input,[autocomplete~="shipping"][autocomplete~="address-line1"],#shippingAddressLine1','1 Test Road');
    await fill('#shippingAddress-localityInput,[autocomplete~="shipping"][autocomplete~="address-level2"],#shippingLocality','Dublin');
    await fill('#shippingAddress-postalCodeInput,[autocomplete~="shipping"][autocomplete~="postal-code"],#shippingPostalCode','D02 X285',2000);
    const county=await field('#shippingAddress-administrativeAreaInput,#shippingAdministrativeArea,[autocomplete~="shipping"][autocomplete~="address-level1"]',2000);
    stage='select shipping county';
    if(county && await county.evaluate(el=>el.tagName==='SELECT')){
      const value=await county.locator('option').evaluateAll(options=>options.find(o=>/dublin/i.test(o.label))?.value);
      if(value!==undefined)await county.selectOption(value);
    } else if(county) await county.fill('Dublin');
    const cardCSS='#payment-numberInput,#cardNumber,input[autocomplete="cc-number"],input[name=cardnumber]';
    if(!await field(cardCSS,3000))await (await field('[data-testid="card-accordion-item-button"],button:text-is("Card"),[role="radio"]:text-is("Card")'))?.click();
    await fill(cardCSS,'4242424242424242',25000);
    await fill('#payment-expiryInput,#cardExpiry,input[autocomplete="cc-exp"]','12 / 34');
    await fill('#payment-cvcInput,#cardCvc,input[autocomplete="cc-csc"]','123');
    await fill('#billingName,input[autocomplete="cc-name"]','Test Buyer',3000);
    stage='submit hosted payment';
    const submit=await field('#payment-form-submit-button,[data-testid="payment-form-submit-button"],[data-testid="hosted-payment-submit-button"],button[type="submit"]:text-matches("^Pay(\\\\s|$)","i"),button.SubmitButton,button:text-is("Pay")');
    if(!submit)throw Error('Missing payment submit control');
    await submit.click({timeout:10000});
    stage='verify one combined confirmation';
    await page.getByRole('heading',{name:'Purchase confirmed'}).waitFor({timeout:90000});
    const receipt=await page.locator('main').innerText();
    if(!['€3,585','Rowan Studio','Alder Studio','Irish delivery','Studio collection'].every(s=>receipt.includes(s)))throw Error('Incorrect combined receipt');
    rec('BUYER1','One hosted sandbox payment confirmed for works from both studios with mixed fulfilment','stripe-test-api','PASS');
  } catch (error) {
    evidence.failure = error.name;
    if(page){
      const controls=[];
      for(const frame of page.frames()){
        const labels=await frame.locator('input:visible,select:visible,button:visible').evaluateAll(nodes=>nodes.map(n=>n.id ? 'id:'+n.id : n.getAttribute('data-testid') ? 'testid:'+n.getAttribute('data-testid') : n.getAttribute('autocomplete')).filter(Boolean)).catch(()=>[]);
        controls.push(...labels.filter(s=>/^[a-zA-Z][a-zA-Z0-9 :_-]{0,64}$/.test(s) && !/^(cs_|pi_|sk_|rk_)/.test(s)));
      }
      evidence.visibleControls=[...new Set(controls)].slice(0,40);
    }
    rec('BUYER1','Complete combined buyer checkout','stripe-test-api','FAIL',{stage,...evidence});
  } finally {await browser.close(); server.close()}
}
