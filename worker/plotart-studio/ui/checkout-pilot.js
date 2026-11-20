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
  /* Errors are written into the page (role="alert"): next to the form that was submitted, else at the top. Browser dialogs
     (alert, prompt, confirm) are not used for the founder's quote and refund steps: some browsers, including embedded ones,
     suppress them, which silently sent empty answers (20 Nov 2026, deployed TEST purchase). */
  const showError = (ev, msg) => {
    const f = ev && ev.target && ev.target.closest && ev.target.closest('form'), box = (f && f.querySelector('[data-err]')) || document.getElementById('page-error');
    if (box) { box.textContent = msg; box.hidden = false; box.focus && box.focus(); }
  };
  const act = fn => async ev => { ev.preventDefault(); const f = ev.target.closest && ev.target.closest('form'), box = f && f.querySelector('[data-err]');
    if (box) { box.textContent = ''; box.hidden = true; }
    const btn = f && f.querySelector('button[type=submit], button:not([type])'); if (btn) btn.disabled = true;
    try { await fn(ev); } catch (e) { showError(ev, e.message); } finally { if (btn && btn.isConnected) btn.disabled = false; } };
  /* "12.50" → 1250. Whole euro or euro and cents only; never via floating point. */
  const toCents = (v, what) => { const t = String(v ?? '').trim().replace(',', '.');
    if (!/^\d{1,7}(\.\d{1,2})?$/.test(t)) throw new Error(`Enter the ${what} in euro, for example 12.50`);
    const [w, c = ''] = t.split('.'); return Number(w) * 100 + Number((c + '00').slice(0, 2)); };
  let ISSUED = null;   // the one-time buyer link, kept on screen until the page is left or reloaded
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
  /* Issue buyer quote (founder). Same request and server rules as before: 1–7 days; the linked-purchases answer is required
     and only "not linked" lets the server issue the quote. */
  function issueForm(o) {
    const k = esc(o.id);
    return `<details class="st-step" open><summary>Issue buyer quote…</summary><form data-f="issue" novalidate>
      <p class="st-muted">Artwork ${eur(o.artwork_cents)} · delivery ${eur(o.delivery_cents)} · <strong>buyer pays ${eur(o.total_cents)}</strong> · PlotArt commission ${eur(o.commission_cents)} · quote version ${o.quote_version}, approved by the artist.</p>
      <label for="iq-days-${k}">Quote valid for (days, 1–7)</label> <input id="iq-days-${k}" name="days" type="number" inputmode="numeric" min="1" max="7" step="1" value="3" required>
      <fieldset><legend>Linked purchases: as far as you know, is this purchase linked to other purchases by this buyer or anyone acting with them (other email addresses, household, business, agents, staged payments)?</legend>
        <label><input type="radio" name="linked" value="not_linked" required> Not linked, as far as I know</label>
        <label><input type="radio" name="linked" value="linked_or_unsure"> Linked, or I am not sure (the quote will not be issued)</label></fieldset>
      <p class="st-err" role="alert" tabindex="-1" data-err hidden></p>
      <button type="submit">Issue buyer quote</button></form></details>`;
  }
  /* Refund (founder). Same request as before: artwork and delivery amounts in cents, and a reason. The server keeps every
     rule (paid orders only, never more than is still unrefunded, PlotArt's commission share returned under the agreement). */
  function refundForm(o) {
    const k = esc(o.id), st = o.statement || {};
    return `<details class="st-step"><summary>Refund…</summary><form data-f="refund" novalidate>
      <p class="st-muted">Paid: artwork ${eur(o.artwork_cents)}, delivery ${eur(o.delivery_cents)}${st.refunded_to_buyer ? ` · already refunded ${eur(st.refunded_to_buyer)}` : ''}. Stripe refunds the buyer from the artist’s Stripe account; Studio then returns PlotArt’s commission share as the agreement provides.</p>
      <label for="rf-art-${k}">Artwork amount to refund (€)</label> <input id="rf-art-${k}" name="artwork" inputmode="decimal" value="0.00" required>
      <label for="rf-del-${k}">Delivery amount to refund (€)</label> <input id="rf-del-${k}" name="delivery" inputmode="decimal" value="0.00" required>
      <label for="rf-why-${k}">Reason (shown in the order record)</label> <input id="rf-why-${k}" name="reason" maxlength="300" required>
      <p data-sum aria-live="polite"></p>
      <label><input type="checkbox" name="confirm" required> I confirm this refund through Stripe. A refund cannot be undone.</label>
      <p class="st-err" role="alert" tabindex="-1" data-err hidden></p>
      <button type="submit">Refund through Stripe</button></form></details>`;
  }
  function orderCard(o) {
    const d = o.delivery;
    let h = `<section class="st-card" id="order-${esc(o.id)}" data-id="${esc(o.id)}"><h3>${esc(o.reference)} · ${esc(o.artwork && o.artwork.title)} <small class="st-muted">${esc(o.status.replace(/_/g, ' '))}</small></h3>
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
      if (o.status === 'awaiting_artist' && o.artist_approved_version === o.quote_version) h += issueForm(o);
      if (['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'payment_failed', 'expired'].includes(o.status)) b.push(['cancel', 'Cancel']);
      if (o.payment_intent || o.status === 'checkout_open') b.push(['reconcile', 'Reconcile with Stripe']);
      if (o.payment_intent && ['paid', 'dispatched', 'delivered', 'refund_pending', 'disputed', 'refunded'].includes(o.status)) h += refundForm(o);
      if (['delivered', 'refunded'].includes(o.status)) b.push(['close', 'Close']);
      if (o.payment_intent) b.push(['hold', 'Legal hold…'], ['repaid', 'Record repayment outside Stripe…']);
      if (o.payment_intent && o.commission_cents > 0) b.push(['processing', 'Reconcile processing fee']);
      if (o.statement && o.statement.shortfall_still_owed_by_plotart) b.push(['shortfallpaid', 'Record shortfall paid…']);
      if (o.statement && o.statement.commission_refund_owed) b.push(['returncommission', 'Return commission (lost dispute)']);
      if (o.payment_intent) b.push(['confirmation', 'Re-deliver buyer confirmation']);
      if (ISSUED && ISSUED.id === o.id) h += `<div class="st-card st-issued" role="status" data-issued><h4>Buyer quote issued (version ${ISSUED.version})</h4>
        <p><strong>Buyer link, shown once.</strong> Copy it now and send it to the buyer yourself. Studio keeps only a fingerprint of it and cannot show it again.</p>
        <label>Buyer link <input data-link readonly value="${esc(ISSUED.link)}" style="width:100%" aria-describedby="link-note-${esc(o.id)}"></label>
        <p><button type="button" data-copy>Copy link</button> <span id="link-note-${esc(o.id)}" class="st-muted" data-copied aria-live="polite"></span></p></div>`;
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
    let h = `<h1>Payment pilot <small class="st-muted">(Stripe test mode)</small></h1><p id="page-error" class="st-err" role="alert" tabindex="-1" hidden></p>`;
    const sw = j.switches;
    h += `<p class="st-muted">Pilot ${sw.enabled ? 'switched ON (test mode)' : 'switched OFF'}${founder && sw.key_problem ? ' · ' + esc(sw.key_problem) : ''}. No live payment can be taken.</p>`;
    if (founder) {
      const pz = j.pause || { paused: false }, ab = j.absence || { items: [], open_sessions: [], quotes_awaiting_payment: [] };
      h += `<section id="pause-control" class="st-card ${pz.paused ? 'st-paused' : ''}"><h2>${esc(pz.label || 'Pause new quotes and payments')} <span class="st-badge">${pz.paused ? 'PAUSED' : 'Not paused'}</span></h2>
        ${pz.paused ? `<p><strong>Paused since ${esc(new Date(pz.since).toLocaleString('en-IE', { timeZone: 'Europe/Dublin', dateStyle: 'medium', timeStyle: 'short' }))}</strong> · expected back ${esc(pz.return_on)}${pz.note ? ` · ${esc(pz.note)}` : ''}</p><p><button data-pause="0">Resume new quotes and payments</button></p>`
          : `<form data-f="pause"><label>Back on (Irish date) <input type="date" name="return_on" required></label> <label>Note (optional) <input name="note" maxlength="300"></label> <button>Pause new quotes and payments</button></form>`}
        <p class="st-muted">${esc(pz.explanation || '')}</p>
        <details ${pz.paused ? 'open' : ''}><summary>Absence checklist — ${ab.quotes_awaiting_payment.length} quote(s) awaiting payment (${ab.open_sessions.length} with a Stripe page open), ${ab.items.length} item(s) due before ${esc(ab.horizon || '')}${ab.assumed_return ? ' (preview, assumed return date)' : ''}</summary>
          <p class="st-muted">${esc(ab.horizon_note || '')}</p>
          ${ab.quotes_awaiting_payment.length ? `<h3>Quotes awaiting payment</h3><table class="st-table"><tr><th>Quote</th><th>Payment status</th><th>Quote expiry</th></tr>${ab.quotes_awaiting_payment.map(x => `<tr><td><a href="#order-${esc(x.id)}">${esc(x.reference)}</a></td><td><strong>${x.payment === 'stripe_page_open' ? 'Stripe payment page open' : 'Payment not started'}</strong><br>${esc(x.payment_status)}</td><td>${esc(x.quote_expiry)}</td></tr>`).join('')}</table>` : '<p class="st-muted">No quotes awaiting payment.</p>'}
          ${ab.items.length ? `<h3>Due before you are back — needs action before you leave</h3><table class="st-table"><tr><th>Order</th><th>What</th><th>Amount</th><th>Due</th><th>Action</th></tr>${ab.items.map(x => `<tr><td><a href="#order-${esc(x.order_id)}">${esc(x.reference)}</a></td><td>${esc(x.what)}${x.note ? `<br><small class="st-muted">${esc(x.note)}</small>` : ''}</td><td>${esc(x.amount)}</td><td>${esc(x.due_label)}</td><td><strong>${esc(x.action)}</strong></td></tr>`).join('')}</table>` : '<p class="st-muted">Nothing falls due before you are back.</p>'}
        </details></section>`;
      const fa = j.founder_alerts || { items: [], unread: 0, open: 0, follow_ups_due: 0, note: '' };
      h += `<section id="founder-alerts" class="st-card"><h2>Founder alerts <span class="st-badge">${fa.unread} unread</span> <small class="st-muted">${fa.open} open · ${fa.follow_ups_due} follow-up${fa.follow_ups_due === 1 ? '' : 's'} due</small></h2>
        <p class="st-muted">${esc(fa.note)}</p>`;
      const short = t => t.length > 180 ? t.slice(0, 177) + '…' : t;
      const rowA = x => `<tr data-alert="${x.id}" class="${x.read ? '' : 'st-unread'} ${x.follow_up_due || (x.state === 'open' && /OVERDUE/.test(x.due_label)) ? 'st-warn' : ''}">
          <td>${x.read ? 'Read' : '<strong>Unread</strong>'}<br><small>${x.state === 'open' ? 'Open' : 'Resolved'}</small></td><td><small>${esc(x.recorded_irish)}<br>${esc(x.delivery)}</small></td>
          <td>${esc(x.reason)}<br><small class="st-muted" title="${esc(x.detail)}">${esc(short(x.detail))}</small></td><td>${x.link ? `<a href="${esc(x.link)}">${esc(x.reference || x.order_id)}</a>` : '—'}</td>
          <td>${esc(x.amount_label)}</td><td>${esc(x.due_label)}</td>
          <td><input data-next="${x.id}" maxlength="300" placeholder="Next action" value="${esc(x.next_action || '')}"> <input data-fu="${x.id}" type="date" value="${esc(x.follow_up_on || '')}">${x.follow_up_due ? '<br><strong>Follow-up due</strong>' : ''}</td>
          <td><button data-alert-save="${x.id}">Save</button> <button data-alert-read="${x.id}" data-v="${x.read ? '0' : '1'}">${x.read ? 'Mark unread' : 'Mark read'}</button></td></tr>`;
      const head = '<tr><th></th><th>Recorded</th><th>Reason</th><th>Order</th><th>Outstanding now</th><th>Due (Irish date)</th><th>Next action</th><th></th></tr>';
      const openA = fa.items.filter(x => x.state === 'open').sort((p, q) => (q.follow_up_due - p.follow_up_due) || (p.read - q.read)), doneA = fa.items.filter(x => x.state !== 'open');
      h += openA.length ? `<table class="st-table">${head}${openA.map(rowA).join('')}</table>` : '<p class="st-muted">Nothing open.</p>';
      if (doneA.length) h += `<details><summary>Resolved items (${doneA.length}${doneA.some(x => !x.read) ? `, ${doneA.filter(x => !x.read).length} unread` : ''})</summary><table class="st-table">${head}${doneA.map(rowA).join('')}</table></details>`;
      h += `</section>`;
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
          <td>${eur(w.cents)}</td><td>${eur(w.settled_cents)}</td><td><strong>${eur(w.outstanding_cents)}</strong></td><td>${w.age_days} d</td><td>${esc(w.due_label || w.due_date)}${w.due_provisional ? ' <em>(provisional)</em>' : ''}<br><small class="st-muted">${esc(w.due_rule)}</small>${w.due_review ? `<br><strong>For review:</strong> <small>${esc(w.due_review)}</small>` : ''}</td>
          <td>${esc(w.reminders.join(', ') || '—')}</td><td>${w.kind === 'lost_dispute_commission' ? '<button data-a="returncommission">Return commission</button>' : '<button data-a="shortfallpaid">Record payment…</button>'}</td></tr>
          ${w.payments.length ? `<tr data-id="${esc(w.order_id)}"><td></td><td colspan="9"><small>${w.payments.map(x => `${eur(x.cents)} · ${esc(x.method.replace(/_/g, ' '))}${x.executed_on ? ` · executed ${esc(x.executed_on)}` : ''} · ref ${esc(x.reference)} · recorded by ${esc(x.recorded_by)} at ${esc(x.at)}${x.returned_on ? ` · <strong>returned ${esc(x.returned_on)}</strong> (${esc(x.returned_reason)})` : x.method === 'bank_transfer' ? ` <button data-a="shortfallreturned" data-pay="${esc(x.id)}">Transfer returned…</button>` : ''}`).join('<br>')}</small></td></tr>` : ''}`).join('')}</table>` : '<p class="st-muted">Nothing owed.</p>'}
        ${(j.reimbursements || []).length ? `<h3>Processing reimbursements (seven-day rule${j.deadlines && j.deadlines.reimburse_provisional ? ', provisional' : ', sandbox rule approved 18 Nov 2026'})</h3><table class="st-table"><tr><th>Order</th><th>Status</th><th>Amount</th><th>Paid (Irish date)</th><th>Due</th><th>Alerts and attempts</th></tr>${j.reimbursements.map(x => `<tr${x.overdue || x.failing ? ' class="st-warn"' : ''}><td>${esc(x.reference)}<br><small>day ${x.day}</small></td><td>${esc(x.status_label)}${x.overdue ? '<br><strong>OVERDUE</strong>' : ''}</td><td>${esc(x.amount_label)}</td><td>${esc(x.payment_confirmed)}</td><td>${esc(x.due_label)}</td><td><small>${[x.alerts.day5 ? 'Day-5 alert sent' : '', x.alerts.deadline || x.alerts.extended_deadline ? 'Deadline alert sent' : '', x.delay_notice_at ? 'Delay notice sent to the artist (test sink)' : '', x.attempts ? `${x.attempts} failed attempt(s); last: ${x.last_error || ''}. Due date unchanged.` : '', ...x.flags].filter(Boolean).map(esc).join('<br>')}</small>${x.action ? `<br><button data-a="processing" data-id="${esc(x.order_id)}">Reconcile processing fee</button>` : ''}</td></tr>`).join('')}</table>` : ''}
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
        if (j.seller_profile && !j.checkout_available) h += `<p class="st-warn">${esc(j.trader_question.unavailable)}</p>`;
        const sp = j.seller_profile || {};
        h += `<details ${j.seller_problems.length ? 'open' : ''}><summary>Seller information for managed checkout${j.seller_problems.length ? ' — needed before any managed-checkout quote' : ''}</summary><p>${esc(j.trader_question.direct)}</p><form data-f="seller">
          ${[['legal_name', 'Legal name'], ['trading_name', 'Trading name (optional)'], ['address', 'Address where you are established'], ['returns_address', 'Returns and complaints address, if different (optional)'], ['email', 'Email for buyers'], ['phone', 'Telephone for buyers'], ['vat_number', 'VAT number, if registered (optional)']]
            .map(([k, t]) => `<label>${t} <input name="${k}" value="${esc(sp[k] || '')}"></label>`).join('')}
          <fieldset><legend>${esc(j.trader_question.question)}</legend><p class="st-muted"><em>${esc(j.trader_question.review_note)}</em></p><p class="st-muted">${esc(j.trader_question.intro)}</p><p class="st-muted">${esc(j.trader_question.explain)}</p>
          ${j.trader_choices.map(c => `<label><input type="radio" name="trader_status" value="${esc(c.value)}" required ${sp.trader_status === c.value ? 'checked' : ''}> <strong>${esc(c.label)}</strong><br><small>${esc(c.meaning)}</small></label>`).join('')}</fieldset>
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
    on('form[data-f="pause"]', 'submit', async e => { const f = new FormData(e.target); await api('POST', base + '/pause', { paused: true, return_on: f.get('return_on'), note: f.get('note') }); say('New quotes and payments paused'); load(); });
    on('button[data-pause]', 'click', async () => { await api('POST', base + '/pause', { paused: false }); say('New quotes and payments resumed'); load(); });
    on('button[data-alert-read]', 'click', async e => { await api('POST', `${base}/alerts/${e.target.dataset.alertRead}`, { read: e.target.dataset.v === '1' }); load(); });
    on('button[data-alert-save]', 'click', async e => { const id = e.target.dataset.alertSave;
      await api('POST', `${base}/alerts/${id}`, { next_action: app.querySelector(`[data-next="${id}"]`).value, follow_up_on: app.querySelector(`[data-fu="${id}"]`).value }); say('Next action saved'); load(); });
    on('button[data-a]', 'click', async e => {
      const id = idOf(e.target), a = e.target.dataset.a;
      if (a === 'hold') await api('POST', `${base}/orders/${id}/hold`, { basis: prompt('Basis: dispute, claim, revenue_enquiry, investigation, litigation, data_subject_request or other'), reason: prompt('Specific reason'), review_by: prompt('Review by (YYYY-MM-DD, within 12 months)') });
      else if (a === 'repaid') await api('POST', `${base}/orders/${id}/repaid`, { artwork_cents: Number(prompt('Artwork amount repaid (cents)', '0')), delivery_cents: Number(prompt('Delivery amount repaid (cents)', '0')), evidence: prompt('Evidence: transfer reference, date, buyer confirmation') });
      else if (a === 'shortfallpaid') await api('POST', `${base}/orders/${id}/shortfallpaid`, { amount_cents: Number(prompt('Amount the bank shows as EXECUTED (cents). Record it only once the bank shows the transfer executed.', '0')), executed_on: prompt('Date the bank shows the transfer executed (YYYY-MM-DD)'), reference: prompt('The bank’s transfer reference only — never bank details') });
      else if (a === 'shortfallreturned') await api('POST', `${base}/orders/${id}/shortfallreturned`, { payment_id: e.target.dataset.pay, returned_on: prompt('Date the bank shows the transfer returned (YYYY-MM-DD)'), reason: prompt('Reason the bank gave (no bank details)') });
      else if (a === 'returncommission') await api('POST', `${base}/orders/${id}/refund`, { commission_only: true, reason: prompt('Reason', 'Dispute lost: commission returned under PA-GAA 9.1') || '' });
      else if (a === 'cancel') await api('POST', `${base}/orders/${id}/cancel`, { reason: prompt('Reason') || '' });
      else if (a === 'decline') await api('POST', `${base}/orders/${id}/approve`, { decision: 'decline', quote_version: j.orders.find(o => o.id === id).quote_version, note: prompt('What should change?') || '' });
      else await api('POST', `${base}/orders/${id}/${a}`, {});
      say('Done'); load(); });
    on('form[data-f="issue"]', 'submit', async e => { const f = new FormData(e.target), id = idOf(e.target);
      const days = Number(f.get('days')), linked = f.get('linked');
      if (!Number.isInteger(days) || days < 1 || days > 7) throw new Error('Enter how many days the quote is valid: a whole number from 1 to 7');
      if (!linked) throw new Error('Answer the linked-purchases question');
      const r = await api('POST', `${base}/orders/${id}/issue`, { days, linked_check_confirmed: linked === 'not_linked' });
      ISSUED = { id, link: r.buyer_link, version: r.order && r.order.quote_version };
      say('Buyer quote issued'); await load();
      const box = app.querySelector('[data-issued] [data-link]'); if (box) { box.focus(); box.select(); } });
    on('form[data-f="refund"]', 'submit', async e => { const f = new FormData(e.target), id = idOf(e.target);
      const artwork_cents = toCents(f.get('artwork'), 'artwork amount'), delivery_cents = toCents(f.get('delivery'), 'delivery amount'), reason = String(f.get('reason') || '').trim();
      if (artwork_cents + delivery_cents === 0) throw new Error('Enter an artwork or delivery amount to refund');
      if (reason.length < 3) throw new Error('Give a reason for the refund');
      if (f.get('confirm') !== 'on') throw new Error('Tick the box to confirm the refund');
      await api('POST', `${base}/orders/${id}/refund`, { artwork_cents, delivery_cents, reason }); say('Refund sent to Stripe'); load(); });
    app.querySelectorAll('form[data-f="refund"]').forEach(fm => { const sum = fm.querySelector('[data-sum]'), upd = () => {
      try { const t = toCents(fm.artwork.value, 'artwork amount') + toCents(fm.delivery.value, 'delivery amount'); sum.textContent = t ? `The buyer will be refunded ${eur(t)}.` : ''; } catch { sum.textContent = ''; } };
      fm.addEventListener('input', upd); upd(); });
    app.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', async () => { const box = b.closest('[data-issued]'), inp = box.querySelector('[data-link]'), note = box.querySelector('[data-copied]');
      inp.focus(); inp.select();
      try { await navigator.clipboard.writeText(inp.value); note.textContent = 'Copied.'; } catch { note.textContent = 'Selected: press Ctrl+C (or ⌘C) to copy.'; } }));
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
