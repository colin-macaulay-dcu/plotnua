// A LOCAL IMITATION of Stripe's hosted setup page for offline tests: the same field ids as the real page (as recorded in the
// POC evidence). Submitting it completes the mock Checkout Session (mock-stripe-basket.mjs) with a card whose behaviour on
// each artist account follows the Stripe test card number. Never used against Stripe.
import { createServer } from 'node:http';
import { M, enterCard } from './mock-stripe-basket.mjs';

export async function startHostedImitation(ACC) {
/* ---- the imitation hosted page: Stripe's field ids; behaviour per scenario */
const state = { MODE: {} };   // label -> 'redirect' | 'noredirect' | 'reject'
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
  const mode = state.MODE[label] || 'redirect', done = () => mode === 'noredirect' ? {} : { redirect: s.success_url };
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
  return { base: M.hostedBase, host: new URL(M.hostedBase).host, setMode: m => { state.MODE = m; }, close: () => server.close() };
}
