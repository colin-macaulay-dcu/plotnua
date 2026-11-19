// Provider integration proof for one sandbox payment and two artist allocations.
export async function proveBasketSplit({ accounts, runnerKey, balanceKey, configureRecipients = false, v1, v2, rec, runId }) {
  const source = 'stripe-test-api';
  const check = (id, name, pass, details) => rec(id, name, source, pass ? 'PASS' : 'FAIL', details);
  if (!/^(rk|sk)_test_[A-Za-z0-9]+$/.test(runnerKey) ||
      !/^rk_test_[A-Za-z0-9]+$/.test(balanceKey) ||
      accounts.length !== 2 || new Set(accounts).size !== 2 ||
      !accounts.every(id => /^acct_[A-Za-z0-9]+$/.test(id))) {
    check('BASKET0', 'Two distinct sandbox recipients and test keys configured', false, {});
    return;
  }

  const group = 'plotart-basket-' + runId;
  async function request(path, { key = runnerKey, version = v1, data, json, action } = {}) {
    const headers = { Authorization: 'Bearer ' + key, 'Stripe-Version': version };
    if (action) headers['Idempotency-Key'] = group + '-' + action;
    if (json) headers['Content-Type'] = 'application/json';
    const response = await fetch('https://api.stripe.com' + path, {
      method: data || json ? 'POST' : 'GET', headers,
      body: json ? JSON.stringify(json) : data && new URLSearchParams(data)
    });
    const obj = await response.json();
    if (!response.ok || obj.livemode === true) {
      throw new Error([response.status, obj.error?.code, obj.error?.param,
        obj.error?.message?.replace(/(?:rk|sk)_(?:test|live)_[^ '\"]+/g, '[key]'),
        response.headers.get('request-id')].filter(Boolean).join(' ').slice(0, 550));
    }
    return obj;
  }

  let ready = true;
  for (const [i, id] of accounts.entries()) {
    try {
      const path = '/v2/core/accounts/' + id;
      const read = () => request(path + '?include[0]=configuration.recipient', { version: v2 });
      let account = await read();
      const capability = a => a.configuration?.recipient?.capabilities?.stripe_balance?.stripe_transfers;
      let cap = capability(account);
      if (configureRecipients && account.id === id && account.livemode === false && !cap?.requested && cap?.status !== 'active') {
        await request(path, { version: v2, action: 'enable-recipient-' + id, json: {
          configuration: { recipient: { capabilities: { stripe_balance: { stripe_transfers: { requested: true } } } } }
        } });
        account = await read();
        cap = capability(account);
      }
      for (let attempt = 0; configureRecipients && cap?.status === 'pending' && attempt < 3; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        account = await read();
        cap = capability(account);
      }
      const active = account.id === id && cap?.status === 'active';
      check('BASKET-R' + (i + 1), 'Sandbox recipient can receive transfers', active,
        { account: id, status: cap?.status || 'recipient capability absent', details: cap?.status_details });
      if (!active) ready = false;
    } catch (e) {
      ready = false;
      check('BASKET-R' + (i + 1), 'Prepare sandbox transfer recipient', false, { account: id, error: e.message });
    }
  }
  if (!ready) return;

  // Synthetic €10 basket, with explicit test allocations; no live commission assumptions.
  const shares = [600, 400];
  const transfers = [];
  let payment;
  try {
    payment = await request('/v1/payment_intents', { action: 'pay', data: {
      amount: '1000', currency: 'eur', payment_method: 'pm_card_visa', confirm: 'true',
      return_url: 'https://example.com/plotart-sandbox-return', transfer_group: group
    } });
    if (payment.status !== 'succeeded' || !payment.latest_charge || payment.amount_received !== 1000)
      throw new Error('Sandbox payment did not settle as expected');
    for (const [i, destination] of accounts.entries()) {
      const transfer = await request('/v1/transfers', { key: balanceKey, action: 'artist-' + i, data: {
        amount: String(shares[i]), currency: 'eur', destination, source_transaction: payment.latest_charge, transfer_group: group
      } });
      transfers.push(transfer.id);
      if (transfer.amount !== shares[i] || transfer.destination !== destination ||
          transfer.source_transaction !== payment.latest_charge) throw new Error('Unexpected transfer allocation');
    }
    check('BASKET1', 'One €10 test charge allocated €6 and €4', true, { payment: payment.id, transfers });
    const refund = await request('/v1/refunds', { action: 'refund-first', data: {
      payment_intent: payment.id, amount: String(shares[0])
    } });
    if (refund.status !== 'succeeded' || refund.amount !== shares[0]) throw new Error('Partial refund not confirmed: ' + refund.id);
    const reversal = await request('/v1/transfers/' + transfers[0] + '/reversals', {
      key: balanceKey, action: 'reverse-first', data: { amount: String(shares[0]) }
    });
    const [first, second, charge] = await Promise.all([
      ...transfers.map(id => request('/v1/transfers/' + id, { key: balanceKey })),
      request('/v1/charges/' + payment.latest_charge)
    ]);
    check('BASKET2', 'First share refunded and reversed; second share retained', reversal.amount === shares[0] &&
      first.amount_reversed === shares[0] && second.amount_reversed === 0 && second.amount === shares[1] &&
      charge.amount_refunded === shares[0], { refund: refund.id, reversal: reversal.id,
      buyer_refunded: charge.amount_refunded, artist_one_reversed: first.amount_reversed, artist_two_retained: second.amount - second.amount_reversed });
  } catch (e) {
    check('BASKET', 'Sandbox combined payment, split and partial refund', false,
      { group, payment: payment?.id, transfers, error: e.message });
  }
}
