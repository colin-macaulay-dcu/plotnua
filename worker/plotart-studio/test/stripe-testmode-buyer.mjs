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
    const page = await browser.newPage({locale:'en-IE'});
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
          const match=frame.locator(css).first();
          if(await match.isVisible().catch(()=>false))return match;
        }
        await page.waitForTimeout(300);
      } while(Date.now()<deadline);
    }
    async function fill(css,value,timeout) {
      const f=await field(css,timeout);
      if(f)await f.fill(value);
    }
    stage='complete sandbox shipping and payment form';
    await fill('input[type=email]','plotart-buyer@example.com');
    await fill('[autocomplete="shipping name"],#shippingName','Test Buyer');
    await fill('[autocomplete="shipping address-line1"],#shippingAddressLine1','1 Test Road');
    await fill('[autocomplete="shipping address-level2"],#shippingLocality','Dublin');
    await fill('[autocomplete="shipping postal-code"],#shippingPostalCode','D02 X285',2000);
    const county=await field('#shippingAdministrativeArea,[autocomplete="shipping address-level1"]',2000);
    if(county){if(await county.evaluate(el=>el.tagName==='SELECT'))await county.selectOption({label:'Dublin'});else await county.fill('Dublin')}
    const cardCSS='#cardNumber,input[autocomplete="cc-number"],input[name=cardnumber]';
    if(!await field(cardCSS,3000))await (await field('[data-testid="card-accordion-item-button"]'))?.click();
    await fill(cardCSS,'4242424242424242',25000);
    await fill('#cardExpiry,input[autocomplete="cc-exp"]','12 / 34');
    await fill('#cardCvc,input[autocomplete="cc-csc"]','123');
    await fill('#billingName,input[autocomplete="cc-name"]','Test Buyer',3000);
    await page.locator('[data-testid="hosted-payment-submit-button"],button.SubmitButton').first().click();
    stage='verify one combined confirmation';
    await page.getByRole('heading',{name:'Purchase confirmed'}).waitFor({timeout:90000});
    const receipt=await page.locator('main').innerText();
    if(!['€3,585','Rowan Studio','Alder Studio','Irish delivery','Studio collection'].every(s=>receipt.includes(s)))throw Error('Incorrect combined receipt');
    rec('BUYER1','One hosted sandbox payment confirmed for works from both studios with mixed fulfilment','stripe-test-api','PASS');
  } catch (error) {
    evidence.failure = error.name;
    rec('BUYER1','Complete combined buyer checkout','stripe-test-api','FAIL',{stage,...evidence});
  } finally {await browser.close(); server.close()}
}
