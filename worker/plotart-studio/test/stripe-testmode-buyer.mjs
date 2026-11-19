import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { basketApi } from './buyer-preview/basket.mjs';
export async function checkBuyerCheckout(key, rec) {
  const { chromium } = createRequire(process.env.MINIFLARE_FROM)('playwright');
  const origin = 'https://plotart-basket-test.invalid';
  const browser = await chromium.launch();
  let stage = 'open shop';
  try {
    const page = await browser.newPage({locale:'en-IE'});
    await page.route(origin+'/**', async route => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      if (path.startsWith('/api/')) {
        const headers = await request.allHeaders();
        const api = await basketApi(new Request(request.url(), {method:request.method(), headers,
          body:request.method()==='POST' ? request.postData() : undefined}), {PLOTART_CHECKOUT_TEST_KEY:key});
        return route.fulfill({status:api.status,contentType:'application/json',body:await api.text()});
      }
      if (path==='/' || path==='/shop.js') {
        const file=path==='/'?'index.html':'shop.js';
        return route.fulfill({contentType:path==='/'?'text/html':'text/javascript',body:await readFile(new URL('./buyer-preview/'+file, import.meta.url))});
      }
      await route.fulfill({status:204,body:''});
    });
    await page.goto(origin, {waitUntil:'domcontentloaded'});
    await page.locator('[data-add="0"]').click();
    await page.locator('#close').click();
    await page.locator('[data-add="2"]').click();
    await page.locator('[data-ship="1"]').selectOption('collect');
    await page.locator('[data-checkout]').click();
    stage='open combined Stripe Checkout';
    await page.locator('[data-pay]').click();
    await page.waitForURL('https://checkout.stripe.com/**');
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
  } catch {
    rec('BUYER1','Complete combined buyer checkout','stripe-test-api','FAIL',{stage});
  } finally {await browser.close()}
}
