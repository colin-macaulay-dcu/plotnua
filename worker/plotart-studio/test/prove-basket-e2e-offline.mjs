// PROVE (offline) · the sandbox phase test/stripe-testmode-basket-e2e.mjs itself, run against the mock Stripe of
// mock-stripe-basket.mjs and a LOCAL IMITATION of Stripe's hosted setup page (same field ids as the real page, as recorded
// in the POC evidence). Nothing reaches Stripe. Proves the card-entry routine (ported from the POC, commit 9101fb3f) in the
// cases that matter for BE-A0: a page that completes at Stripe without the browser seeing the redirect (completion is then
// read from the Checkout Session), a page that redirects, Stripe's test 3-D Secure step, and Stripe rejecting the form (the
// failure is reported with Stripe's message and a screenshot instead of a silent time-out).
//   node test/prove-basket-e2e-offline.mjs
import { createServer } from 'node:http';
import { existsSync, rmSync } from 'node:fs';
import { M, stripe, enterCard } from './mock-stripe-basket.mjs';
import { basketE2E } from './stripe-testmode-basket-e2e.mjs';

const HERE = new URL('..', import.meta.url).pathname;
const results = [];
const check = (n, ok, d = '') => { results.push(!!ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}${!ok && d ? `  [${JSON.stringify(d).slice(0, 900)}]` : ''}`); };
const ACC = ['acct_offlineA', 'acct_offlineB'];
for (const a of ACC) M.accounts[a] = { id: a, object: 'account', livemode: false, charges_enabled: true, payouts_enabled: true, details_submitted: true, country: 'IE', capabilities: { card_payments: 'active' } };

/* ---- the imitation hosted page: Stripe's field ids; behaviour per scenario */
let MODE = {};   // label -> 'redirect' | 'noredirect' | 'reject'
const BEHAVIOUR = card => card.endsWith('0341') ? { [ACC[0]]: 'decline', [ACC[1]]: 'decline' } : card.endsWith('3184') ? { [ACC[0]]: 'auth', [ACC[1]]: 'auth' } : {};
const PAGE = sid => `<!doctype html><html><head><meta charset="utf-8"><title>PlotNua sandbox</title></head><body>
<form id="f"><input id="linkAuthentication-emailInput" type="email"><input id="payment-numberInput"><input id="payment-expiryInput"><input id="payment-cvcInput"><input id="payment-nameInput">
<select id="payment-countryInput"><option value="US" selected>United States</option><option value="IE">Ireland</option></select><input id="payment-postalCodeInput">
<label><input id="payment-linkOptInInput" type="checkbox" checked> Save my info</label><input id="payment-linkMobilePhoneCountryInput" value="US"><input id="payment-linkMobilePhoneInput">
<p id="msg"></p><button id="payment-form-submit-button" data-testid="payment-form-submit-button" type="submit">Save</button></form>
<script>
document.getElementById('f').addEventListener('submit', function (e) { e.preventDefault();
  var v = function (id) { return document.getElementById(id).value; };
  fetch('/c/setup/${sid}/submit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: v('linkAuthentication-emailInput'), card: v('payment-numberInput').replace(/\\s/g, ''), postal: v('payment-postalCodeInput'), phone: v('payment-linkMobilePhoneInput') }) })
  .then(function (r) { return r.json(); }).then(function (j) {
    if (j.reject) { var p = document.createElement('p'); p.className = 'FieldError'; p.setAttribute('role', 'alert'); p.textContent = j.reject; document.body.appendChild(p); return; }
    if (j.auth) { var b = document.createElement('button'); b.id = 'test-source-authorize-3ds'; b.textContent = 'Complete'; b.type = 'button';
      b.onclick = function () { fetch('/c/setup/${sid}/authorize', { method: 'POST' }).then(function (r) { return r.json(); }).then(go); }; document.body.appendChild(b); return; }
    go(j); });
  function go(j) { if (j.redirect) location.href = j.redirect; else document.getElementById('msg').textContent = 'Saved'; }
});
</script></body></html>`;
const pending = {};
const server = createServer(async (req, res) => {
  const m = req.url.match(/^\/c\/setup\/(cs_test_\w+)(\/submit|\/authorize)?$/);
  if (!m || !M.sessions[m[1]]) { res.writeHead(404); return res.end(); }
  const s = M.sessions[m[1]], send = o => { res.writeHead(200, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(o)); };
  if (!m[2]) { res.writeHead(200, { 'Content-Type': 'text/html' }); return res.end(PAGE(s.id)); }
  let body = ''; for await (const c of req) body += c;
  const label = (String((JSON.parse(body || '{}').email || '')).match(/-([a-z])@/) || [])[1] || (pending[s.id] && pending[s.id].label);
  const mode = MODE[label] || 'redirect', done = () => mode === 'noredirect' ? {} : { redirect: s.success_url };
  if (m[2] === '/submit') {
    const b = JSON.parse(body);
    if (mode === 'reject') return send({ reject: 'Your card number is incomplete.' });
    if (!b.postal || !b.phone || !/^4\d{15}$/.test(b.card)) return send({ reject: 'Your postal code or phone number is incomplete.' });
    if (b.card.endsWith('3184')) { pending[s.id] = { card: b.card, label }; return send({ auth: true }); }
    enterCard(s.id, BEHAVIOUR(b.card)); return send(done());
  }
  enterCard(s.id, BEHAVIOUR(pending[s.id].card)); return send(done());
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
M.hostedBase = `http://127.0.0.1:${server.address().port}`;

const offline = { apiBase: 'https://stripe.mock', fetchImpl: (u, i) => stripe(new Request(u, i)), outbound: stripe, hostedHosts: [new URL(M.hostedBase).host] };
const PW = process.env.PLAYWRIGHT_FROM || process.env.MINIFLARE_FROM || '/tmp/claude-0/studio-tools/package.json';
async function phase(modes, port) {
  MODE = modes; const recs = {};
  await basketE2E({ rec: (id, name, src, status, detail) => { recs[id] = { status, detail }; }, KEY: 'sk_test_offline123', accounts: ACC, runId: 'offline' + port, playwrightFrom: PW, v1: '2026-10-28.endive', port, offline });
  return recs;
}
try {
  console.log('PROVE · sandbox phase basket_e2e offline (mock Stripe, imitation hosted page)');
  console.log('— 1 · the page completes at Stripe but the browser never sees the redirect (the BE-A0 shape)');
  let r = await phase({ a: 'noredirect' }, 8894);
  check('O1 BE-A0 passes: completion is read from the Checkout Session when no redirect is seen', r['BE-A0']?.status === 'PASS' && r['BE-A0'].detail.entry.completed_by === 'stripe_session_status', r['BE-A0']);
  check('O2 the basket then runs forward from the session’s own return address: both direct charges authorised then captured (BE-A1)', r['BE-A1']?.status === 'PASS', r['BE-A1']);
  check('O3 commission 15% / 0% on the charges (BE-A2) and the orders recorded as paid (BE-A3); the card released (BE-A4)', ['BE-A2', 'BE-A3', 'BE-A4'].every(k => r[k]?.status === 'PASS'), { A2: r['BE-A2'], A3: r['BE-A3'], A4: r['BE-A4'] });
  check('O4 the POC’s Link handling is used: Link sign-up left ticked and the test phone filled (the routine that passed A0 in the POC)', r['BE-A0']?.detail.entry.link_opt_in_checked === true, r['BE-A0']?.detail.entry);
  check('O5 the redirecting decline page and the 3-D Secure page complete (BE-B1, BE-C2), and clean-up verifies nothing is left (BE-Z)', ['BE-B1', 'BE-C2', 'BE-Z'].every(k => r[k]?.status === 'PASS'), { B1: r['BE-B1'], C1: r['BE-C1'], C2: r['BE-C2'], Z: r['BE-Z'] });
  check('O6 a refund through the existing order path (BE-D1)', r['BE-D1']?.status === 'PASS', r['BE-D1']);
  console.log('— 2 · Stripe rejects the form after submit');
  rmSync(HERE + 'stripe-test-evidence/basket-e2e-a.png', { force: true });
  r = await phase({ a: 'reject' }, 8895);
  const e = r['BE-A0']?.detail.entry || {};
  check('O7 the failure names Stripe’s own message and stage at once, instead of waiting out the time limit', r['BE-A0']?.status === 'FAIL' && /Stripe rejected the form: Your card number is incomplete/.test(e.error || '') && e.stage === 'await completion or authentication', e);
  check('O8 the failure report carries diagnostics and a screenshot (stripe-test-evidence/basket-e2e-a.png)', e.screenshot === 'basket-e2e-a.png' && existsSync(HERE + 'stripe-test-evidence/basket-e2e-a.png') && Array.isArray(e.visible_controls) && e.visible_controls.includes('id:payment-numberInput'), e);
  check('O9 nothing is charged for that basket and the run still cleans up (BE-Z)', r['BE-A1']?.status === 'FAIL' && r['BE-Z']?.status === 'PASS', r['BE-Z']);
  console.log(`\nSANDBOX PHASE OFFLINE · ${results.length} checks, ${results.filter(Boolean).length} passed, ${results.filter(x => !x).length} failed`);
  process.exitCode = results.every(Boolean) ? 0 : 1;
} finally {
  server.close(); rmSync(HERE + 'stripe-test-evidence', { recursive: true, force: true });
}
