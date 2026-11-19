import {verifySignature} from '../../src/stripe.js';
import {quote} from './basket.mjs';

// A platform webhook for the two sample studios in the private checkout pilot.
export async function settleSandboxBasket(request, env, send = fetch) {
  const raw = await request.text();
  const signature = await verifySignature(env, request.headers.get('stripe-signature'), raw);
  if (!signature.ok) return new Response('Invalid signature', {status:400});
  const event = JSON.parse(raw);
  const session = event.data?.object;
  if (event.livemode !== false || event.account || session?.livemode !== false ||
      !['checkout.session.completed','checkout.session.async_payment_succeeded'].includes(event.type) ||
      session.metadata?.pilot !== 'plotart-private-basket-v1' || session.payment_status !== 'paid') return new Response(null,{status:204});
  const accountIds = env.recipients;
  if (!Array.isArray(accountIds) || accountIds.length !== 2 || new Set(accountIds).size !== 2 ||
      !accountIds.every(id=>/^acct_[a-zA-Z0-9]+$/.test(id)) ||
      ![env.checkoutKey,env.balanceKey].every(key=>/^rk_test_[A-Za-z0-9]+$/.test(key))) return new Response('Sandbox configuration missing',{status:503});
  const order = quote(session.metadata.items.split(',').map(Number),session.metadata.collection.split(',').map(v=>v==='1'));
  if (!order || order.total !== session.amount_total || session.currency !== 'eur' ||
      !/^pi_[A-Za-z0-9]+$/.test(session.payment_intent) || !/^cs_test_[A-Za-z0-9]+$/.test(session.id)) return new Response('Order mismatch',{status:422});
  async function stripe(path,key,data,idem) {
    const headers={Authorization:'Bearer '+key};
    if(idem) headers['Idempotency-Key']=idem;
    const r=await send('https://api.stripe.com/v1/'+path,{method:data?'POST':'GET',headers,body:data && new URLSearchParams(data)});
    const obj=await r.json();
    if(!r.ok || obj.livemode===true)throw Error('Stripe sandbox request failed');
    return obj;
  }
  const pi=await stripe('payment_intents/'+session.payment_intent+'?expand[]=latest_charge',env.checkoutKey);
  const charge=pi.latest_charge;
  const group='plotart-preview-'+session.client_reference_id;
  if(pi.id!==session.payment_intent || pi.livemode!==false || pi.status!=='succeeded' || pi.amount_received!==order.total ||
     pi.transfer_group!==group || !charge?.paid || charge.livemode!==false || charge.currency!=='eur' ||
     charge.amount!==order.total || charge.amount_refunded || charge.disputed) return new Response('Charge requires review',{status:409});
  const listed=await stripe('transfers?limit=100&transfer_group='+encodeURIComponent(group),env.balanceKey);
  if(listed.has_more || !Array.isArray(listed.data))return new Response('Transfers require review',{status:409});
  const transfers=[];
  for(const share of order.groups) {
    const destination=accountIds[share.artist];
    const prior=listed.data.filter(t=>t.source_transaction===charge.id && t.destination===destination);
    if(prior.length>1)return new Response('Duplicate transfer requires review',{status:409});
    const transfer=prior[0] || await stripe('transfers',env.balanceKey,{
      amount:String(share.cents),currency:'eur',destination,source_transaction:charge.id,transfer_group:group,
      'metadata[checkout_session]':session.id
    },'plotart-sandbox-'+charge.id+'-'+share.artist);
    if(transfer.amount!==share.cents || transfer.currency!=='eur' || transfer.destination!==destination ||
       transfer.source_transaction!==charge.id || transfer.transfer_group!==group || transfer.livemode!==false ||
       transfer.metadata?.checkout_session!==session.id) return new Response('Allocation mismatch',{status:409});
    transfers.push({id:transfer.id,cents:transfer.amount,artist:share.artist});
  }
  return Response.json({session:session.id,transfers});
}
