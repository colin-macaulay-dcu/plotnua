/* PlotArt Studio · payment pilot page (development 16 Nov 2026; TEST MODE). One small page for both roles:
   /admin/checkout (founder) and /checkout-pilot (artist). Not linked from the Studio tabs: reached by its address only. */
(() => {
  const founder = location.pathname.startsWith('/admin');
  const base = founder ? '/api/admin/checkout' : '/api/checkout';
  const app = document.getElementById('app');
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const eur = c => c == null ? '—' : '€' + (c / 100).toFixed(2);
  const api = async (method, path, body) => {
    const r = await fetch(path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    const j = await r.json().catch(() => ({ ok: false, error: 'Unreadable response' }));
    if (!j.ok) throw new Error(j.error || 'Refused');
    return j;
  };
  const say = m => { const s = document.getElementById('saved'); s.textContent = m; s.classList.add('on'); setTimeout(() => s.classList.remove('on'), 4000); };
  const act = fn => async ev => { ev.preventDefault(); try { await fn(ev); } catch (e) { alert(e.message); } };
  const TEMPLATE = { collection_county: '', destination: '', unpacked_cm: '', packed_cm: '', weight_kg: 0, medium: '', framing: '', glazing: '', condition: '', access_notes: null,
    organiser: 'artist', packer: 'artist', transport_booker: 'artist', transport_contracting_party: 'artist', transport_payer: 'artist', transporter_name: '',
    installation: 'not_applicable', import_costs: 'not_applicable', cover_type: 'transit_insurance', cover_provider: '', covered_value_cents: 0, valuation_basis: '',
    excess_cents: null, exclusions: null, cover_period: '', claims_contact: '', insured_party: 'transporter', cover_confirmation_ref: '', cover_confirmed_by: '', cover_confirmed_on: new Date().toISOString().slice(0, 10), delivery_window: '', tracking: '', signed_receipt: true, condition_photos: true,
    return_method: '', return_address: '', return_cost_cents: 0, return_cost_basis: 'estimated_maximum', return_arranged_by: 'buyer', shipment_confirmation_ref: '', shipment_confirmed_by: '', shipment_confirmed_on: new Date().toISOString().slice(0, 10) };

  /* The artist's statement: every amount on its own line, nothing netted silently (fee model B). */
  function statementTable(st) {
    const row = (label, c, sign = '', strong = false) => c || strong ? `<tr><td>${strong ? '<strong>' : ''}${label}${strong ? '</strong>' : ''}</td><td style="text-align:right">${sign}${eur(Math.abs(c))}</td></tr>` : '';
    return `<details open><summary>Statement</summary><table class="st-table" style="max-width:34rem">
      ${row('Gross payment from the buyer', st.gross_payment, '', true)}
      ${row('of which artwork', st.of_which_artwork)}${row('of which delivery', st.of_which_delivery)}
      ${row('PlotArt commission (on the artwork only)', st.plotart_commission, '− ')}
      ${row('Commission refunded by PlotArt', st.commission_refunded, '+ ')}
      ${row('Stripe processing fee (whole payment)', st.stripe_processing_fee, '− ')}
      ${row('VAT charged by Stripe on that fee', st.vat_on_processing_fee, '− ')}
      ${row('Processing fee and VAT reimbursed by PlotArt', st.processing_reimbursed_by_plotart, '+ ')}
      ${row('Paid directly by PlotArt (shortfall)', st.shortfall_paid_by_plotart, '+ ')}
      ${row('Other Stripe fees on this payment (not reimbursed)', st.other_stripe_fees_not_reimbursed, '− ')}
      ${row('Refunded to the buyer', st.refunded_to_buyer, '− ')}
      ${row('Disputes (net)', st.disputes_net, st.disputes_net < 0 ? '− ' : '+ ')}
      ${row('Stripe dispute fees (incl. VAT)', st.dispute_fees_charged_by_stripe, '− ')}${row('Dispute fees returned by Stripe', st.dispute_fees_returned_by_stripe, '+ ')}
      ${row('Net proceeds', st.net_proceeds, st.net_proceeds < 0 ? '− ' : '', true)}
      ${st.shortfall_still_owed_by_plotart ? row('Owed by PlotArt, not yet paid (shortfall)', st.shortfall_still_owed_by_plotart, '', true) : ''}
      ${st.commission_refund_owed ? row('Commission to be returned after a lost dispute, not yet returned', st.commission_refund_owed, '', true) : ''}
      </table><small class="st-muted">Processing: ${esc(String(st.processing_status).replace(/_/g, ' '))}. Dispute fees: ${esc(st.dispute_fees_status)}. ${esc(st.not_included)}</small></details>`;
  }
  function orderCard(o) {
    const d = o.delivery;
    let h = `<section class="st-card" data-id="${esc(o.id)}"><h3>${esc(o.reference)} · ${esc(o.artwork && o.artwork.title)} <small class="st-muted">${esc(o.status.replace(/_/g, ' '))}</small></h3>
      <p>Artwork ${eur(o.artwork_cents)} · delivery ${eur(o.delivery_cents)} · total ${eur(o.total_cents)} · PlotArt commission ${o.commission_bp == null ? '—' : (o.commission_bp / 100).toFixed(2) + '% = ' + eur(o.commission_cents)}
      ${o.commission_basis ? `<br><small class="st-muted">Basis: ${esc(o.commission_basis.replace(/_/g, ' '))}. ${esc(o.processing_fees)}</small>` : ''}</p>
      ${o.needs_resolution ? `<p class="st-warn"><strong>Needs resolution:</strong> ${esc(o.needs_resolution)}</p>` : ''}
      ${o.statement ? statementTable(o.statement) : ''}
      <p class="st-muted">Quote version ${o.quote_version}${o.artist_approved_version === o.quote_version ? ' · approved by the artist' : ''}${o.quote_expires_at ? ' · expires ' + esc(o.quote_expires_at) : ''} · payment ${esc(o.payment_status)} · fulfilment ${esc(o.fulfilment_status)} · dispute ${esc(o.dispute_status)}</p>`;
    if (d) h += `<details><summary>Delivery and cover</summary><pre style="white-space:pre-wrap">${esc(JSON.stringify(d, null, 2))}</pre></details>`;
    if (founder) {
      if (['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'payment_failed', 'expired'].includes(o.status)) h += `<details><summary>Edit price, delivery and cover (creates a new quote version)</summary><form data-f="edit">
        <label>Artwork price (cents) <input name="artwork_cents" type="number" min="100" value="${o.artwork_cents ?? ''}"></label>
        <label>Delivery charge (cents) <input name="delivery_cents" type="number" min="0" value="${o.delivery_cents ?? ''}"></label>
        <label>Delivery and cover (JSON) <textarea name="delivery" rows="14" style="width:100%;font-family:monospace">${esc(JSON.stringify(d || TEMPLATE, null, 2))}</textarea></label>
        <label>Commission exclusion <select name="exclusion"><option value="">none</option>${['prior_relationship', 'representing_gallery', 'independent_sale', 'founder_waiver'].map(x => `<option ${o.exclusion === x ? 'selected' : ''}>${x}</option>`).join('')}</select></label>
        <button>Save as new version</button></form></details>`;
      const b = [];
      if (o.status === 'draft') b.push(['send', 'Send to artist for approval']);
      if (o.status === 'awaiting_artist' && o.artist_approved_version === o.quote_version) b.push(['issue', 'Issue buyer quote']);
      if (['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'payment_failed', 'expired'].includes(o.status)) b.push(['cancel', 'Cancel']);
      if (o.payment_intent || o.status === 'checkout_open') b.push(['reconcile', 'Reconcile with Stripe']);
      if (o.payment_intent) b.push(['refund', 'Refund…']);
      if (['delivered', 'refunded'].includes(o.status)) b.push(['close', 'Close']);
      if (o.payment_intent) b.push(['hold', 'Legal hold…'], ['repaid', 'Record repayment outside Stripe…']);
      if (o.payment_intent && o.commission_cents > 0) b.push(['processing', 'Reconcile processing fee']);
      if (o.statement && o.statement.shortfall_still_owed_by_plotart) b.push(['shortfallpaid', 'Record shortfall paid…']);
      if (o.statement && o.statement.commission_refund_owed) b.push(['returncommission', 'Return commission (lost dispute)']);
      if (o.payment_intent) b.push(['confirmation', 'Re-deliver buyer confirmation']);
      h += `<p>${b.map(([k, t]) => `<button data-a="${k}">${t}</button>`).join(' ')}</p>`;
    } else if (o.status === 'awaiting_artist' && o.artist_approved_version !== o.quote_version) {
      h += `<form data-f="approve"><p>Please check this quote carefully. Approving confirms each of the following for <em>this shipment</em>:</p>
        ${[['available', 'The work is available and not sold or promised elsewhere'], ['location', 'The collection location is correct'], ['condition', 'The condition description is accurate'],
          ['framing', 'Framing and glazing are as described'], ['dimensions', 'Unpacked and packed dimensions and weight are correct'], ['packing_and_handover', 'I agree the packing, transport and cover responsibilities shown'],
          ['returns', 'The return method, address, cost estimate and who arranges the return are correct'], ['seller_information', 'My seller information (shown to the buyer) is correct and up to date']]
          .map(([k, t]) => `<label><input type="checkbox" name="${k}"> ${t}</label>`).join('')}
        <label>Note (optional) <input name="note" maxlength="500"></label><button>Approve this quote (version ${o.quote_version})</button> <button data-a="decline" type="button">Ask for changes</button></form>`;
    }
    if (['paid', 'dispatched', 'delivered', 'disputed'].includes(o.status)) h += `<form data-f="fulfil"><label>Record <select name="kind"><option>insurance</option><option>dispatched</option><option>tracking</option><option>condition_photos</option><option>delivered</option><option>signed_receipt</option><option>note</option></select></label>
      <label>Evidence <input name="evidence" maxlength="2000" required placeholder="tracking number, receipt or photo reference"></label><button>Record</button></form>`;
    return h + '</section>';
  }

  async function load() {
    const j = await api('GET', base);
    if (!j.installed) { app.innerHTML = '<h1>Payment pilot</h1><p>The payment pilot is not installed.</p>'; return; }
    let h = `<h1>Payment pilot <small class="st-muted">(Stripe test mode)</small></h1>`;
    const sw = j.switches;
    h += `<p class="st-muted">Pilot ${sw.enabled ? 'switched ON (test mode)' : 'switched OFF'}${founder && sw.key_problem ? ' · ' + esc(sw.key_problem) : ''}. No live payment can be taken.</p>`;
    if (founder) {
      h += `<p>Addendum: ${esc(j.addendum || 'not issued')} · Buyer terms: ${esc(j.buyer_terms || 'not issued')}</p><h2>Artists who opted in</h2>`;
      h += j.artists.length ? `<ul>${j.artists.map(a => `<li>${esc(a.display_name)} — ${a.membership.opted_in ? 'opted in' : 'left'} · Stripe ${a.membership.account ? (a.membership.ready ? 'ready' : 'onboarding incomplete') : 'not connected'}
        ${a.membership.account ? `<button data-refresh="${esc(a.id)}">Refresh</button>` : ''}</li>`).join('')}</ul>` : '<p class="st-muted">Nobody yet. Artists opt in themselves at /checkout-pilot.</p>';
      h += `<h2>New order from an enquiry</h2><form data-f="create"><label>Artist <select name="artist_id">${j.artists.filter(a => a.membership.opted_in).map(a => `<option value="${esc(a.id)}">${esc(a.display_name)}</option>`).join('')}</select></label>
        <label>Artwork id <input name="artwork_id" required></label><label>Enquiry reference <input name="enquiry_ref" required placeholder="PA-E-…"></label>
        <label>Buyer email <input name="buyer_email" type="email" required></label><button>Create draft</button></form>`;
      if (j.pending_refunds.length) h += `<h2>Refunds waiting for an artist’s Stripe balance</h2><ul>${j.pending_refunds.map(r => `<li class="${r.urgency === 'new' ? '' : 'st-warn'}">${esc(r.reference)} · ${eur(r.amount_cents)} · pending ${r.days_pending} days · Stripe cancels it on ${esc(r.stripe_fails_it_by)} (${esc(r.urgency)})</li>`).join('')}</ul>
        <details><summary>What the artist does</summary><ol>${j.refund_funding_steps.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
      h += `<h2>Amounts owed to artists</h2><p class="st-muted">${esc(j.deadlines.note)}</p>${j.owed.length ? `<table class="st-table"><tr><th>Order</th><th>Artist</th><th>What</th><th>Owed</th><th>Paid</th><th>Outstanding</th><th>Age</th><th>Due</th><th>Reminders</th><th></th></tr>
        ${j.owed.map(w => `<tr data-id="${esc(w.order_id)}" class="${w.status === 'overdue' ? 'st-warn' : ''}"><td>${esc(w.reference)}</td><td>${esc(w.artist_name)}</td><td>${esc(w.kind.replace(/_/g, ' '))}<br><small class="st-muted">${esc(w.reason)}</small></td>
          <td>${eur(w.cents)}</td><td>${eur(w.settled_cents)}</td><td><strong>${eur(w.outstanding_cents)}</strong></td><td>${w.age_days} d</td><td>${esc(w.due_date)}${w.due_provisional ? ' <em>(provisional)</em>' : ''}<br><small class="st-muted">${esc(w.due_rule)}</small></td>
          <td>${esc(w.reminders.join(', ') || '—')}</td><td>${w.kind === 'lost_dispute_commission' ? '<button data-a="returncommission">Return commission</button>' : '<button data-a="shortfallpaid">Record payment…</button>'}</td></tr>
          ${w.payments.length ? `<tr><td></td><td colspan="9"><small>${w.payments.map(x => `${eur(x.cents)} · ${esc(x.method.replace(/_/g, ' '))} · ${esc(x.reference)} · ${esc(x.at)}`).join('<br>')}</small></td></tr>` : ''}`).join('')}</table>` : '<p class="st-muted">Nothing owed.</p>'}
        <details><summary>How to pay a shortfall (bank details process)</summary><ol>${j.bank_details_process.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
      if (j.holds.length) h += `<h2>Legal holds</h2><ul>${j.holds.map(x => `<li data-hold="${esc(x.id)}">${esc(x.reference)} · ${esc(x.basis)} · review by ${esc(x.review_by)}${x.review_overdue ? ' <strong>(review overdue)</strong>' : ''} — ${esc(x.reason)}
        <button data-hold-act="renew">Renew…</button> <button data-hold-act="release">Release…</button></li>`).join('')}</ul>`;
      if (j.unprocessed_events.length) h += `<h2>Provider events waiting</h2><ul>${j.unprocessed_events.map(e => `<li>${esc(e.type)} · ${esc(e.status)} · ${esc(e.detail || '')}</li>`).join('')}</ul>`;
    } else {
      const m = j.membership;
      if (!m.opted_in) h += j.addendum ? `<h2>Join the payment pilot (optional)</h2><p>Read the <a href="/payment-terms/${esc(j.addendum.doc_id)}.html" target="_blank" rel="noopener">${esc(j.addendum.title)}</a>.</p>
        <form data-f="optin"><label><input type="checkbox" name="accept" required> ${esc(j.addendum.statement)}</label><button>Join the pilot</button></form>` : '<p>The payment addendum has not been issued yet.</p>';
      else {
        h += `<p class="st-muted">${esc(j.direct_payment_note)}</p>`;
        const sp = j.seller_profile || {};
        h += `<details ${j.seller_problems.length ? 'open' : ''}><summary>Seller information shown to buyers${j.seller_problems.length ? ' — needed before any quote' : ''}</summary><form data-f="seller">
          ${[['legal_name', 'Legal name'], ['trading_name', 'Trading name (optional)'], ['address', 'Address where you are established'], ['returns_address', 'Returns and complaints address, if different (optional)'], ['email', 'Email for buyers'], ['phone', 'Telephone for buyers'], ['vat_number', 'VAT number, if registered (optional)']]
            .map(([k, t]) => `<label>${t} <input name="${k}" value="${esc(sp[k] || '')}"></label>`).join('')}
          <label>Do you sell as a trader (in the course of your business, craft or profession)? <select name="trader_status"><option value="">choose</option><option value="trader" ${sp.trader_status === 'trader' ? 'selected' : ''}>Yes, as a trader</option><option value="not_trader" ${sp.trader_status === 'not_trader' ? 'selected' : ''}>No</option></select></label>
          <label><input type="checkbox" name="confirm" required> ${esc(j.seller_declaration)}</label><button>Save seller information</button></form></details>`;
        if (j.pending_refunds.length) h += `<h2>A refund is waiting for your Stripe balance</h2>${j.pending_refunds.map(r => `<p class="st-warn">${esc(r.reference)}: ${eur(r.amount_cents)}, waiting ${r.days_pending} days. Stripe cancels it on ${esc(r.stripe_fails_it_by)} if still unfunded.</p>`).join('')}<ol>${j.pending_refunds[0].what_to_do.map(x => `<li>${esc(x)}</li>`).join('')}</ol>`;
        h += m.processing_consent ? `<p>You have agreed that Stripe’s processing fees may be deducted on commission-free pilot orders (${esc(m.processing_consent_at)}). <button data-a2="withdraw-processing">Withdraw this consent</button></p>`
          : `<details><summary>Commission-free sales through the pilot (optional, separate consent)</summary><form data-f="processing"><label><input type="checkbox" name="accept" required> ${esc(j.processing_statement)}</label><button>Give this consent</button></form></details>`;
        h += `<p>You joined the pilot on ${esc(m.opted_in_at)} (${esc(m.addendum)}). Stripe: ${m.account ? (m.ready ? 'ready to take test payments' : 'onboarding incomplete' + (m.account.requirements_due.length ? ' — Stripe still needs: ' + esc(m.account.requirements_due.join(', ')) : '')) : 'not connected yet'}.</p>
          <p><button data-a2="onboard">${m.account ? 'Continue Stripe onboarding' : 'Connect a Stripe account'}</button> ${m.account ? '<button data-a2="refresh">Refresh status</button>' : ''} <button data-a2="leave">Leave the pilot</button></p>`;
      }
    }
    h += `<h2>Orders</h2>${j.orders.length ? j.orders.map(orderCard).join('') : '<p class="st-muted">None yet.</p>'}`;
    app.innerHTML = h;
    wire(j);
  }

  function wire(j) {
    const on = (sel, ev, fn) => app.querySelectorAll(sel).forEach(el => el.addEventListener(ev, act(fn)));
    const idOf = el => el.closest('[data-id]').dataset.id;
    on('form[data-f="create"]', 'submit', async e => { const f = new FormData(e.target); await api('POST', base + '/orders', Object.fromEntries(f)); say('Draft created'); load(); });
    on('form[data-f="edit"]', 'submit', async e => { const f = new FormData(e.target);
      await api('PUT', `${base}/orders/${idOf(e.target)}`, { artwork_cents: Number(f.get('artwork_cents')), delivery_cents: Number(f.get('delivery_cents')), delivery: JSON.parse(f.get('delivery')), exclusion: f.get('exclusion') || null });
      say('Saved as a new quote version'); load(); });
    on('button[data-a]', 'click', async e => {
      const id = idOf(e.target), a = e.target.dataset.a;
      if (a === 'issue') { const r = await api('POST', `${base}/orders/${id}/issue`, { days: Number(prompt('Quote valid for how many days (1–7)?', '3')),
          linked_check_confirmed: confirm('Linked purchases: as far as you know, is this purchase NOT linked to other purchases by this buyer or anyone acting with them (other email addresses, household, business, agents, staged payments)? OK = not linked.') }); prompt('Buyer link (shown once). Copy it now and send it to the buyer yourself:', r.buyer_link); }
      else if (a === 'refund') { const art = Number(prompt('Artwork amount to refund (cents)', '0')), del = Number(prompt('Delivery amount to refund (cents)', '0')), reason = prompt('Reason');
        await api('POST', `${base}/orders/${id}/refund`, { artwork_cents: art, delivery_cents: del, reason }); }
      else if (a === 'hold') await api('POST', `${base}/orders/${id}/hold`, { basis: prompt('Basis: dispute, claim, revenue_enquiry, investigation, litigation, data_subject_request or other'), reason: prompt('Specific reason'), review_by: prompt('Review by (YYYY-MM-DD, within 12 months)') });
      else if (a === 'repaid') await api('POST', `${base}/orders/${id}/repaid`, { artwork_cents: Number(prompt('Artwork amount repaid (cents)', '0')), delivery_cents: Number(prompt('Delivery amount repaid (cents)', '0')), evidence: prompt('Evidence: transfer reference, date, buyer confirmation') });
      else if (a === 'shortfallpaid') await api('POST', `${base}/orders/${id}/shortfallpaid`, { amount_cents: Number(prompt('Amount PlotArt paid the artist directly (cents)', '0')), reference: prompt('Bank transfer reference and date only — never bank details') });
      else if (a === 'returncommission') await api('POST', `${base}/orders/${id}/refund`, { commission_only: true, reason: prompt('Reason', 'Dispute lost: commission returned under PA-GAA 9.1') || '' });
      else if (a === 'cancel') await api('POST', `${base}/orders/${id}/cancel`, { reason: prompt('Reason') || '' });
      else if (a === 'decline') await api('POST', `${base}/orders/${id}/approve`, { decision: 'decline', quote_version: j.orders.find(o => o.id === id).quote_version, note: prompt('What should change?') || '' });
      else await api('POST', `${base}/orders/${id}/${a}`, {});
      say('Done'); load(); });
    on('form[data-f="approve"]', 'submit', async e => { const f = new FormData(e.target), id = idOf(e.target);
      const confirm = Object.fromEntries(['available', 'location', 'condition', 'framing', 'dimensions', 'packing_and_handover', 'returns', 'seller_information'].map(k => [k, f.get(k) === 'on']));
      await api('POST', `${base}/orders/${id}/approve`, { quote_version: j.orders.find(o => o.id === id).quote_version, confirm, note: f.get('note') }); say('Approved'); load(); });
    on('form[data-f="fulfil"]', 'submit', async e => { const f = new FormData(e.target); await api('POST', `${base}/orders/${idOf(e.target)}/fulfilment`, Object.fromEntries(f)); say('Recorded'); load(); });
    on('form[data-f="seller"]', 'submit', async e => { const f = new FormData(e.target); await api('PUT', base + '/seller-profile', { ...Object.fromEntries(f), confirm: f.get('confirm') === 'on' }); say('Seller information saved'); load(); });
    on('form[data-f="optin"]', 'submit', async () => { await api('POST', base + '/opt-in', { accept: true, doc_id: j.addendum.doc_id, html_sha256: j.addendum.html_sha256 }); say('You joined the pilot'); load(); });
    on('form[data-f="processing"]', 'submit', async () => { await api('POST', base + '/processing-consent', { accept: true, statement: j.processing_statement }); say('Consent recorded'); load(); });
    on('button[data-hold-act]', 'click', async e => { const id = e.target.closest('[data-hold]').dataset.hold, a = e.target.dataset.holdAct;
      await api('POST', `${base}/holds/${id}`, a === 'renew' ? { decision: 'renew', review_by: prompt('New review date (YYYY-MM-DD, within 12 months)'), note: prompt('Why is the hold still needed?') } : { decision: 'release', note: prompt('Why can it be released?') }); load(); });
    on('button[data-a2]', 'click', async e => { const a = e.target.dataset.a2;
      if (a === 'withdraw-processing') { await api('POST', base + '/processing-consent/withdraw', {}); load(); return; }
      if (a === 'onboard') { const r = await api('POST', base + '/onboarding', {}); location.href = r.url; return; }
      if (a === 'leave' && !confirm('Leave the payment pilot? Unpaid quotes are cancelled; paid orders continue.')) return;
      await api('POST', `${base}/${a === 'refresh' ? 'account/refresh' : 'leave'}`, {}); load(); });
    on('button[data-refresh]', 'click', async e => { await api('POST', `${base}/accounts/${e.target.dataset.refresh}/refresh`, {}); load(); });
  }
  load().catch(e => { app.innerHTML = `<p>${esc(e.message)}</p>`; });
})();
