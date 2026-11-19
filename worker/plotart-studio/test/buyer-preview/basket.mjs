const studios = ['Rowan Studio', 'Alder Studio'];
const works = [
  { name: 'Estuary, first light', artist: 0, cents: 145000 },
  { name: 'Estuary, slack water', artist: 0, cents: 125000 },
  { name: 'Last light on the hill', artist: 1, cents: 210000 }
];
const fees = [3500, 4500];
const response = (data, status = 200) => Response.json(data, { status, headers: { 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer' } });
export function quote(items, collection) {
  if (!Array.isArray(items) || !items.length || items.length > works.length ||
      new Set(items).size !== items.length || !items.every(id => Number.isInteger(id) && works[id]) ||
      !Array.isArray(collection) || collection.length !== 2 || !collection.every(v => typeof v === 'boolean')) return null;
  const groups = studios.flatMap((name, artist) => {
    const ids = items.filter(id => works[id].artist === artist);
    if (!ids.length) return [];
    const fee = collection[artist] ? 0 : fees[artist];
    return [{ artist, name, items: ids, method: collection[artist] ? 'Studio collection' : 'Irish delivery',
      fee, cents: fee + ids.reduce((n,id) => n + works[id].cents, 0) }];
  });
  return { groups, total: groups.reduce((n,g) => n + g.cents, 0) };
}
export async function basketApi(req, env, send = fetch) {
  const url = new URL(req.url);
  if (!/^rk_test_[A-Za-z0-9]+$/.test(env.PLOTART_CHECKOUT_TEST_KEY || ''))
    return response({ error: 'Stripe sandbox checkout is awaiting its test connection.' }, 503);
  const headers = { Authorization: 'Bearer ' + env.PLOTART_CHECKOUT_TEST_KEY };
  async function stripe(path, body, idem) {
    const h = { ...headers };
    if (idem) h['Idempotency-Key'] = idem;
    const r = await send('https://api.stripe.com/v1/checkout/sessions' + path, { method: body ? 'POST' : 'GET', headers: h, body });
    const session = await r.json();
    if (!r.ok || session.livemode !== false) throw Error('Stripe sandbox request failed');
    return session;
  }
  try {
    if (url.pathname === '/api/basket' && req.method === 'POST') {
      if (req.headers.get('origin') !== url.origin) return response({ error: 'Invalid origin.' }, 403);
      const { items, collection, attempt } = await req.json();
      const order = quote(items, collection);
      if (!order || !/^[0-9a-f-]{36}$/.test(attempt)) return response({ error: 'Please review your basket.' }, 400);
      const body = new URLSearchParams({ mode: 'payment', success_url: url.origin + '/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url: url.origin + '/#checkout', client_reference_id: attempt, 'metadata[pilot]': 'plotart-private-basket-v1',
        'metadata[items]': items.join(','), 'metadata[collection]': collection.map(Number).join(','),
        'payment_intent_data[transfer_group]': 'plotart-preview-' + attempt });
      if (order.groups.some(g => g.fee)) body.set('shipping_address_collection[allowed_countries][0]', 'IE');
      let i = 0;
      function addLine(name, cents) {
        const line = 'line_items[' + i++ + ']';
        body.set(line + '[quantity]', '1');
        body.set(line + '[price_data][currency]', 'eur');
        body.set(line + '[price_data][unit_amount]', String(cents));
        body.set(line + '[price_data][product_data][name]', name);
      }
      for (const g of order.groups) {
        for (const id of g.items) addLine(works[id].name + ' · ' + g.name, works[id].cents);
        if (g.fee) addLine('Irish delivery · ' + g.name, g.fee);
      }
      const s = await stripe('', body, 'basket-' + attempt);
      if (s.amount_total !== order.total || new URL(s.url).origin !== 'https://checkout.stripe.com') throw Error('Checkout mismatch');
      return response({ url: s.url });
    }
    if (url.pathname === '/api/basket/confirmation' && req.method === 'GET') {
      const id = url.searchParams.get('session');
      if (!/^cs_test_[a-zA-Z0-9]+$/.test(id)) return response({ error: 'Invalid checkout reference.' }, 400);
      const s = await stripe('/' + id);
      if (s.id !== id || s.metadata?.pilot !== 'plotart-private-basket-v1') return response({ error: 'Unknown order.' }, 404);
      if (s.payment_status !== 'paid' || s.status !== 'complete') return response({ pending: true }, 202);
      const order = quote(s.metadata.items.split(',').map(Number), s.metadata.collection.split(',').map(x => x === '1'));
      if (!order || order.total !== s.amount_total || s.currency !== 'eur' || !/^[0-9a-f-]{36}$/.test(s.client_reference_id)) throw Error('Order mismatch');
      return response({ ...order, reference: 'PA-' + s.client_reference_id });
    }
    return response({ error: 'Unknown checkout endpoint.' }, 404);
  } catch {
    return response({ error: 'Stripe could not verify this checkout. Please retry.' }, 502);
  }
}
