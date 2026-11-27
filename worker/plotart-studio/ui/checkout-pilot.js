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
    const f = ev && ev.target && ev.target.closest && ev.target.closest('form');
    let box = f && f.querySelector('[data-err]');
    // a form without its own error line gets one, beside its button: the message is always where the artist pressed
    // (23 Nov 2026: it went to the top of the page, out of sight on a phone, so the page only seemed to jump back)
    if (f && !box) { box = document.createElement('p'); box.className = 'st-err'; box.setAttribute('data-err', ''); box.setAttribute('role', 'alert'); box.tabIndex = -1; f.appendChild(box); }
    box = box || document.getElementById('page-error');
    if (!box) return;
    box.textContent = msg; box.hidden = false;
    const hdr = document.querySelector('.st-top'), off = (hdr ? hdr.getBoundingClientRect().bottom : 0) + 12, r = box.getBoundingClientRect();
    if (r.top < off || r.bottom > window.innerHeight) window.scrollTo({ top: Math.max(0, r.top + window.scrollY - off - 40), behavior: 'auto' });
    box.focus && box.focus({ preventScroll: true });
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
  const todayIE = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Dublin' }).format(new Date());
  const plusDaysIE = n => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Dublin' }).format(new Date(Date.now() + n * 86400_000));
  const isDate = v => /^\d{4}-\d{2}-\d{2}$/.test(String(v || ''));
  /* One collapsible on-page form. Errors appear inside it (role="alert"); an irreversible financial step carries its own
     confirmation tick, checked again before anything is sent. No browser dialogs anywhere on this page (20 Nov 2026). */
  const step = (kind, summary, body, submit, { open = false, extra = '' } = {}) =>
    `<details class="st-step"${open ? ' open' : ''}${extra}><summary>${summary}</summary><form data-f="${kind}" novalidate>${body}
      <p class="st-err" role="alert" tabindex="-1" data-err hidden></p><button type="submit">${submit}</button></form></details>`;
  const field = (id, label, input) => `<label for="${id}">${label}</label> ${input}`;
  const tick = (label) => `<label><input type="checkbox" name="confirm" required> ${label}</label>`;
  const need = (cond, msg) => { if (!cond) throw new Error(msg); };
  // One owed item's payments, each bank transfer not yet returned with its "Transfer returned…" form (shown once: the
  // control disappears when a return is recorded, and the server refuses a second return of the same transfer).
  const payRow = (w, cols) => w.payments.length ? `<tr data-id="${esc(w.order_id)}"><td></td><td colspan="${cols}"><small>${w.payments.map(x => `${eur(x.cents)} · ${esc(x.method.replace(/_/g, ' '))}${x.executed_on ? ` · executed ${esc(x.executed_on)}` : ''} · ref ${esc(x.reference)} · recorded by ${esc(x.recorded_by)} at ${esc(x.at)}${x.returned_on ? ` · <strong>returned ${esc(x.returned_on)}</strong> (${esc(x.returned_reason)})` : x.method === 'bank_transfer' ? step('shortfallreturned', 'Transfer returned…', `<input type="hidden" name="payment_id" value="${esc(x.id)}">
            ${field(`sr-on-${esc(x.id)}`, 'Date the bank shows it returned', `<input id="sr-on-${esc(x.id)}" name="returned_on" type="date" min="${esc(x.executed_on || '')}" max="${todayIE()}" required>`)}
            ${field(`sr-why-${esc(x.id)}`, 'Reason the bank gave (5–300 characters, no bank details)', `<input id="sr-why-${esc(x.id)}" name="reason" maxlength="300" required>`)}
            ${tick(`The bank shows this ${eur(x.cents)} transfer as returned. The amount becomes owed again.`)}`, 'Record returned transfer') : ''}`).join('<br>')}</small></td></tr>` : '';
  const HOLD_BASES = [['dispute', 'Dispute'], ['claim', 'Claim'], ['revenue_enquiry', 'Revenue enquiry'], ['investigation', 'Investigation'], ['litigation', 'Litigation'], ['data_subject_request', 'Data subject request'], ['other', 'Other']];
  const TEMPLATE = { collection_county: '', destination: '', destination_country: 'IE', dispatch_days: 7, delivery_days: 14, unpacked_cm: '', packed_cm: '', weight_kg: 0, medium: '', framing: '', glazing: '', condition: '', access_notes: null,
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
  function holdForm(o) { const k = esc(o.id);
    return step('hold', 'Legal hold…', `<p class="st-muted">Keeps this order’s records beyond the normal retention date while the hold is active. Review it at least every 12 months.</p>
      ${field(`hd-basis-${k}`, 'Basis', `<select id="hd-basis-${k}" name="basis" required><option value="">Choose…</option>${HOLD_BASES.map(([v, t]) => `<option value="${v}">${t}</option>`).join('')}</select>`)}
      ${field(`hd-why-${k}`, 'Specific reason (10–1,000 characters)', `<textarea id="hd-why-${k}" name="reason" rows="3" maxlength="1000" required></textarea>`)}
      ${field(`hd-rv-${k}`, 'Review by (within 12 months)', `<input id="hd-rv-${k}" name="review_by" type="date" min="${plusDaysIE(1)}" max="${plusDaysIE(365)}" required>`)}`, 'Place legal hold'); }
  function repaidForm(o) { const k = esc(o.id);
    return step('repaid', 'Record repayment outside Stripe…', `<p class="st-muted">Only when the artist has repaid the buyer directly (not through Stripe). Studio books it as a refund and returns PlotArt’s commission share as the agreement provides.</p>
      ${field(`rp-art-${k}`, 'Artwork amount repaid (€)', `<input id="rp-art-${k}" name="artwork" inputmode="decimal" value="0.00" required>`)}
      ${field(`rp-del-${k}`, 'Delivery amount repaid (€)', `<input id="rp-del-${k}" name="delivery" inputmode="decimal" value="0.00" required>`)}
      ${field(`rp-ev-${k}`, 'Evidence: transfer reference, date and the buyer’s confirmation (no bank details)', `<textarea id="rp-ev-${k}" name="evidence" rows="2" maxlength="500" required></textarea>`)}
      ${tick('I confirm the buyer has been repaid as described. This is recorded as a refund and cannot be undone.')}`, 'Record repayment'); }
  function shortfallForm(o) { const k = esc(o.id), out = o.statement.shortfall_still_owed_by_plotart;
    return step('shortfallpaid', 'Record shortfall paid…', `<p class="st-muted">PlotArt still owes the artist <strong>${eur(out)}</strong> outside Stripe on this order. Record a payment only once PlotArt’s bank shows the transfer as <strong>executed</strong>. Never enter bank details here.</p>
      ${field(`sp-amt-${k}`, `Amount the bank shows as executed (€, up to ${eur(out)})`, `<input id="sp-amt-${k}" name="amount" inputmode="decimal" required>`)}
      ${field(`sp-on-${k}`, 'Date the bank shows it executed', `<input id="sp-on-${k}" name="executed_on" type="date" max="${todayIE()}" required>`)}
      ${field(`sp-ref-${k}`, 'The bank’s transfer reference only (6–200 characters)', `<input id="sp-ref-${k}" name="reference" maxlength="200" required autocomplete="off">`)}
      ${tick('PlotArt’s bank shows this transfer as executed. Recording it settles the amount owed and tells the artist.')}`, 'Record shortfall paid', { extra: ` data-step="shortfallpaid"` }); }
  function returnCommissionForm(o) { const k = esc(o.id), due = o.statement.commission_refund_owed;
    return step('returncommission', 'Return commission (lost dispute)…', `<p class="st-muted">The dispute was lost, so PlotArt returns its commission under PA-GAA 9.1: <strong>${eur(due)}</strong>, through Stripe where the application fee allows, otherwise owed by bank transfer.</p>
      ${field(`rc-why-${k}`, 'Reason (recorded on the order)', `<input id="rc-why-${k}" name="reason" maxlength="300" value="Dispute lost: commission returned under PA-GAA 9.1" required>`)}
      ${tick(`Return ${eur(due)} of PlotArt’s commission to the artist. This cannot be undone.`)}`, 'Return commission', { extra: ` data-step="returncommission"` }); }
  function cancelForm(o) { const k = esc(o.id);
    return step('cancel', 'Cancel order…', `<p class="st-muted">Cancels this unpaid order and any open quote; the buyer’s link then says it cannot be paid. A paid order is never cancelled: refund it instead.</p>
      ${field(`cn-why-${k}`, 'Reason (optional, recorded on the order)', `<input id="cn-why-${k}" name="reason" maxlength="300">`)}
      ${tick('Cancel this order.')}`, 'Cancel order'); }
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
      const more = [];
      if (['draft', 'awaiting_artist', 'quoted', 'checkout_open', 'payment_failed', 'expired'].includes(o.status)) more.push(cancelForm(o));
      if (o.payment_intent || o.status === 'checkout_open') b.push(['reconcile', 'Reconcile with Stripe']);
      if (o.payment_intent && ['paid', 'dispatched', 'delivered', 'refund_pending', 'disputed', 'refunded'].includes(o.status)) h += refundForm(o);
      if (['delivered', 'refunded'].includes(o.status)) b.push(['close', 'Close']);
      if (o.payment_intent) more.push(holdForm(o), repaidForm(o));
      if (o.payment_intent && o.commission_cents > 0) b.push(['processing', 'Reconcile processing fee']);
      if (o.statement && o.statement.shortfall_still_owed_by_plotart) more.push(shortfallForm(o));
      if (o.statement && o.statement.commission_refund_owed) more.push(returnCommissionForm(o));
      if (o.payment_intent) b.push(['confirmation', 'Re-deliver buyer confirmation']);
      if (ISSUED && ISSUED.id === o.id) h += `<div class="st-card st-issued" role="status" data-issued><h4>Buyer quote issued (version ${ISSUED.version})</h4>
        <p><strong>Buyer link, shown once.</strong> Copy it now and send it to the buyer yourself. Studio keeps only a fingerprint of it and cannot show it again.</p>
        <label>Buyer link <input data-link readonly value="${esc(ISSUED.link)}" style="width:100%" aria-describedby="link-note-${esc(o.id)}"></label>
        <p><button type="button" data-copy>Copy link</button> <span id="link-note-${esc(o.id)}" class="st-muted" data-copied aria-live="polite"></span></p></div>`;
      h += `<p>${b.map(([k, t]) => `<button data-a="${k}">${t}</button>`).join(' ')}</p>` + more.join('');
    } else if (o.status === 'awaiting_artist' && o.artist_approved_version !== o.quote_version) {
      h += `<form data-f="approve"><p>Please check this quote carefully. Approving confirms each of the following for <em>this shipment</em>:</p>
        ${[['available', 'The work is available and not sold or promised elsewhere'], ['location', 'The collection location is correct'], ['condition', 'The condition description is accurate'],
          ['framing', 'Framing and glazing are as described'], ['dimensions', 'Unpacked and packed dimensions and weight are correct'], ['packing_and_handover', 'I agree the packing, transport and cover responsibilities shown'],
          ['returns', 'The return method, address, cost estimate and who arranges the return are correct'], ['seller_information', 'My seller information (shown to the buyer) is correct and up to date']]
          .map(([k, t]) => `<label><input type="checkbox" name="${k}"> ${t}</label>`).join('')}
        <label>Note (optional) <input name="note" maxlength="500"></label><button>Approve this quote (version ${o.quote_version})</button></form>`
        + step('decline', 'Ask for changes instead…', `<p class="st-muted">The quote goes back to PlotArt as a draft; nothing is sent to the buyer.</p>
          ${field(`dc-note-${esc(o.id)}`, 'What should change? (optional, up to 500 characters)', `<textarea id="dc-note-${esc(o.id)}" name="note" rows="3" maxlength="500"></textarea>`)}`, 'Ask for changes');
    }
    if (['paid', 'dispatched', 'delivered', 'disputed'].includes(o.status)) h += `<form data-f="fulfil"><label>Record <select name="kind"><option>insurance</option><option>dispatched</option><option>tracking</option><option>condition_photos</option><option>delivered</option><option>signed_receipt</option><option>note</option></select></label>
      <label>Evidence <input name="evidence" maxlength="2000" required placeholder="tracking number, receipt or photo reference"></label><button>Record</button></form>`;
    return h + '</section>';
  }

  /* ---------------------------------------------------------------- multi-artist basket (optional; PA-BAA) */
  let J_BASKET = null;
  let RD = null;   // the artist's readiness (steps), for the step links
  const CENTS = ['covered_value_cents', 'excess_cents', 'return_cost_cents'];
  const LABELS = { dispatch_days: 'Dispatch within (days after payment)', delivery_days: 'Delivered within (days after payment)', offshore_islands: 'Also deliver to offshore islands (no road connection) at this charge' };
  const REQUIRED_HERE = ['dispatch_days', 'delivery_days'];   // optional in quotes, required in a basket delivery offer
  const label = k => LABELS[k] || k.replace(/_cents$/, ' (€)').replace(/_kg$/, ' (kg)').replace(/_cm$/, ' (cm)').replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
  const offerForm = (w, bj) => { const d = (w.offer && w.offer.delivery) || {}, F = bj.delivery_fields;
    const input = (k, t) => { const id = `of-${esc(w.id)}-${k}`, v = k === 'offshore_islands' ? d[k] === true : d[k], opt = typeof t === 'string' && t.endsWith('?') && !REQUIRED_HERE.includes(k), ty = typeof t === 'string' ? t.replace('?', '') : t;
      if (Array.isArray(ty)) return field(id, label(k), `<select id="${id}" name="${k}">${ty.map(x => `<option ${v === x ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select>`);
      if (ty === 'p') return field(id, label(k), `<select id="${id}" name="${k}">${bj.parties.map(x => `<option value="${esc(x)}" ${v === x ? 'selected' : ''}>${esc(x.replace(/_/g, ' '))}</option>`).join('')}</select>`);
      if (ty === 'b') return field(id, label(k), `<select id="${id}" name="${k}"><option value="true" ${v === true ? 'selected' : ''}>yes</option><option value="false" ${v === false ? 'selected' : ''}>no</option></select>`);
      if (ty === 'd') return field(id, label(k), `<input id="${id}" name="${k}" type="date" value="${esc(v || '')}">`);
      const val = CENTS.includes(k) && typeof v === 'number' ? (v / 100).toFixed(2) : (v ?? '');
      return field(id, label(k) + (opt ? ' (optional)' : ''), `<input id="${id}" name="${k}" value="${esc(val)}" ${ty === 'n' && !CENTS.includes(k) ? 'inputmode="decimal"' : ''}>`); };
    return step('offer', w.offer ? 'Change the fixed delivery price…' : 'Set the fixed delivery price…', `<div data-id="${esc(w.id)}">
      ${field(`of-${esc(w.id)}-charge`, 'Delivery charge to the buyer (€), anywhere in the Republic of Ireland', `<input id="of-${esc(w.id)}-charge" name="charge" value="${w.offer ? (w.offer.delivery_cents / 100).toFixed(2) : ''}" required>`)}
      ${Object.entries(F).filter(([k]) => !['destination', 'destination_country'].includes(k)).map(([k, t]) => input(k, t)).join('')}
      <p class="st-muted">PlotArt reviews each delivery offer, and every change to it, before the artwork can be bought online.</p>
      ${tick('I will sell and deliver this artwork as described, anywhere in the Republic of Ireland, for this delivery charge, with this transit insurance and these return arrangements.')}</div>`, 'Save the fixed delivery price'); };
  function basketArtist(bj, j) {
    const m = bj.membership, pc = m.processing_consent || {}, sd = m.seller_disclosure || {};
    let h = `<section class="st-card" id="basket"><h2>Online purchase through the basket <small class="st-muted">(optional)</small></h2>
      <p class="st-muted">Buyers can buy your available artworks online, alone or with other artists’ works. You remain the seller and each payment goes to your own Stripe account. Not taking part changes nothing for your gallery listing, enquiries or direct sales.</p>`;
    if (!bj.addendum) return h + '<p>The basket addendum has not been issued yet.</p></section>';
    if (!m.current) return h + `<p>Read the <a href="/basket-terms/${esc(bj.addendum.doc_id)}.html" target="_blank" rel="noopener">${esc(bj.addendum.title)}</a>.</p>
      <form data-f="basket-optin"><label><input type="checkbox" name="accept" required> ${esc(bj.addendum.statement)}</label><button>Accept and take part</button></form></section>`;
    h += `<p>You accepted ${esc(m.doc_id)} on ${esc(m.at)}.</p>`;
    // 1 · seller information shown before payment
    const si = bj.seller_info;
    h += `<h3 id="pay-disclosure">Seller information shown to buyers before payment</h3>`;
    if (!si) h += '<p class="st-warn">Complete your seller information above first.</p>';
    else {
      h += `<dl class="st-dl">${[['Seller', si.shown.legal_name + (si.shown.trading_name ? ` (trading as ${si.shown.trading_name})` : '')], ['Address', si.shown.address], ['Returns and complaints', si.shown.returns_address], ['Email', si.shown.email], ['Telephone', si.shown.phone], ['VAT number', si.shown.vat_number]].filter(([, v]) => v).map(([t, v]) => `<dt>${esc(t)}</dt><dd>${esc(v)}</dd>`).join('')}</dl>`;
      h += sd.valid ? `<p>Confirmed on ${esc(sd.at)}. <button data-a2="withdraw-disclosure">Withdraw (stops online purchase)</button></p>`
        : `${sd.changed_since ? '<p class="st-warn">Your seller information has changed since you confirmed it: confirm again to keep your works online.</p>' : ''}<form data-f="basket-disclosure"><label><input type="checkbox" name="accept" required> ${esc(bj.disclosure_statement)}</label><button>Confirm</button></form>`;
    }
    // 2 · commission-free works: the separate processing-fee consent
    if (bj.founding) {
      h += `<h3>Your commission-free artworks <small class="st-muted">(optional, separate consent)</small></h3>`;
      h += pc.valid ? `<p>You agreed on ${esc(pc.at)} that your commission-free artworks may be bought online, with Stripe’s processing fees deducted from your Stripe balance and 0% PlotArt commission. <button data-a2="withdraw-basket-processing">Withdraw this consent</button></p>`
        : `<p class="st-muted">Without this consent your commission-free artworks stay on enquiry and direct sale, as now.</p><form data-f="basket-processing"><p style="white-space:pre-line">${esc(bj.processing_statement)}</p><label><input type="checkbox" name="accept" required> I agree to the statement above.</label><button>Give this consent</button></form>`;
    }
    // 3 · delivery, per artwork (23 Nov 2026): two choices. Fixed delivery price = the existing offer form (insurance,
    //     PlotArt's review, every rule unchanged). Arranged personally = no offer: buyers enquire; nothing to fill in.
    h += `<h3 id="pay-delivery">Delivery for each artwork</h3><p class="st-muted">Choose for each available artwork. You can change it at any time.</p><ul class="st-dv-list">`;
    for (const w of bj.works) {
      const avail = w.availability === 'available', fixed = !!w.offer, rv = fixed && w.offer.review, priced = !!w.price_eur && !w.price_on_request;
      h += `<li class="st-dv" data-id="${esc(w.id)}"><p class="st-dv-t"><strong>${esc(w.title)}</strong> <span class="st-muted">${priced ? '€' + esc(w.price_eur) : 'price on request'} · ${esc(w.availability)}</span></p>`;
      if (!avail) { h += `<p class="st-muted st-dv-s">Not available, so no delivery choice is needed.</p></li>`; continue; }
      h += `<div class="st-dv-choice" role="group" aria-label="Delivery for ${esc(w.title)}">
          <button type="button" class="st-dv-opt" data-dv="fixed" aria-pressed="${fixed}" ${priced ? '' : 'disabled'}><b>Fixed delivery price</b><small>Buyers can pay online</small></button>
          <button type="button" class="st-dv-opt" data-dv="arranged" aria-pressed="${!fixed}"><b>Arranged personally</b><small>Buyers enquire</small></button></div>`;
      if (!priced) h += `<p class="st-muted st-dv-s">Add a price to this artwork in Studio to offer a fixed delivery price. Until then buyers enquire.</p>`;
      else if (fixed) h += `<p class="st-dv-s">Delivery ${eur(w.offer.delivery_cents)} · <span class="${rv && rv.state === 'approved' ? 'st-ok' : 'st-warn'}">${esc(rv ? rv.text : 'Waiting for PlotArt to review it')}</span>${rv && rv.note ? `<br><small>PlotArt’s note: ${esc(rv.note)}</small>` : ''}</p>`
        + `<div class="st-dv-off" hidden><p>Stop the fixed delivery price for this artwork? Buyers will enquire instead. A basket already being paid is not affected.</p><button data-withdraw-offer="${esc(w.id)}">Yes, arrange delivery personally</button> <button type="button" data-dv-cancel>Keep the fixed price</button></div>`;
      else h += `<p class="st-muted st-dv-s">Buyers see “Enquire to purchase” and a note that delivery is arranged with you. You agree delivery and the full price with them before any payment.</p>`;
      if (priced) h += offerForm(w, bj);
      h += `</li>`;
    }
    h += `</ul>` + step('basket-leave', 'Stop online purchase…', `<p class="st-muted">Your artworks are no longer offered in the basket. Baskets already paid or being paid are completed.</p>${tick('Stop online purchase of my artworks.')}`, 'Stop');
    return h + '</section>';
  }
  function basketFounder(bj, own) {   // own: the Review desk tab, where the page heading already names it
    const on = a => a.online || { available: 0, purchasable: 0, not_purchasable: {} };
    const ready = bj.artists.filter(a => !a.missing.length).length, tot = bj.artists.reduce((n, a) => n + on(a).available, 0), buy = bj.artists.reduce((n, a) => n + on(a).purchasable, 0);
    const why = o => Object.entries(o.not_purchasable).map(([k, n]) => `${n} ${esc(k)}`).join('<br>');
    const policy = `commission-free works: ${esc(bj.commission_free_policy.replace(/_/g, ' '))}${bj.consents_installed ? '' : ' · migration 0020 not installed'}`;
    return `<section class="st-card" id="basket-readiness">${own ? `<p class="st-muted">${policy}</p>` : `<h2>Basket readiness <small class="st-muted">${policy}</small></h2>`}
      <p>${ready} of ${bj.artists.length} artists ready · ${buy} of ${tot} available artworks can be bought online. <span class="st-muted">Every other artwork stays enquiry-only; its Add to basket button appears by itself once its artist is ready.</span></p>
      <div class="st-scroll"><table class="st-table"><tr><th>Artist</th><th>Stripe</th><th>Addendum</th><th>Seller info shown</th><th>Processing-fee consent</th><th>Delivery</th><th>Missing</th><th>Online purchase</th></tr>
      ${bj.artists.map(a => `<tr><td>${esc(a.display_name)}${a.founding ? ' <small>(Founding)</small>' : ''}</td><td>${esc(a.stripe)}</td><td>${esc(a.basket_addendum || '—')}${a.basket_addendum && !a.basket_current ? ' (old)' : ''}</td>
        <td>${a.seller_disclosure.valid ? 'confirmed ' + esc(a.seller_disclosure.at) : a.seller_disclosure.changed_since ? 'changed since confirmed' : '—'}</td>
        <td>${a.founding ? (a.processing_consent.valid ? 'given ' + esc(a.processing_consent.at) + ' (' + esc(a.processing_consent.doc_id) + ')' : a.processing_consent.given ? 'given for an older addendum' : 'none') : 'not needed'}</td>
        <td>${a.delivery ? `${a.delivery.fixed_approved} fixed, approved${a.delivery.fixed_waiting ? `<br><strong>${a.delivery.fixed_waiting} fixed, waiting for you</strong>` : ''}${a.delivery.fixed_returned ? `<br>${a.delivery.fixed_returned} fixed, returned` : ''}<br>${a.delivery.arranged} arranged personally` : `${esc(a.delivery_offers_approved ?? 0)} of ${esc(a.delivery_offers)} approved`}</td><td>${a.missing.length ? esc(a.missing.join(', ')) : 'account set up'}</td>
        <td><strong>${on(a).purchasable} of ${on(a).available}</strong> artworks${on(a).purchasable < on(a).available ? `<br><small class="st-muted">${why(on(a))}</small>` : ''}</td></tr>`).join('')}</table></div></section>`;
  }

  /* /admin/baskets: the Review desk's "Basket readiness" tab shows this same founder section on its own (22 Nov 2026). */
  async function loadReadiness() {
    document.querySelector('.st-tabs a[aria-current]')?.scrollIntoView({ block: 'nearest', inline: 'center' });   // the tab bar scrolls: show this tab
    let bj = null, err = '';
    try { bj = await api('GET', base + '/baskets/artists'); } catch (e) { err = e.message; }
    let oj = null; try { oj = await api('GET', base + '/baskets/offers'); } catch (e) { err = err || e.message; }
    let out = null; try { out = await api('GET', '/api/admin/outcomes'); } catch { /* the section simply stays out */ }
    app.innerHTML = `<h1 class="st-h1">Basket readiness</h1><p class="st-muted">Each artist completes these steps themselves in Studio → Payment pilot. <a href="/admin/checkout">Open the Payment pilot page</a></p>`
      + (out ? outcomesCard(out) : '')
      + (oj && oj.installed ? offerReviews(oj) : '')
      + (bj && bj.installed ? basketFounder(bj, true) : `<p class="st-err" role="alert">${esc(err || 'The multi-artist basket is not installed.')}</p>`);
    wireOffers(oj);
  }
  /* Commercial outcomes (Sprint 1, 26 Nov 2026): counts the server has confirmed, from records the Studio already keeps.
     No names, emails or messages: the endpoint returns counts and totals only. */
  function outcomesCard(o) {
    const n = v => v === null || v === undefined ? '—' : esc(String(v));
    const row = (label, f) => `<tr><th scope="row">${esc(label)}</th>${o.windows.map(w => `<td>${f(w)}</td>`).join('')}</tr>`;
    return `<section class="st-card" id="commercial-outcomes"><h2>Commercial outcomes <small class="st-muted">server-confirmed counts · ${esc(o.as_of.slice(0, 16).replace('T', ' '))} UTC</small></h2>
      <div class="st-scroll"><table class="st-table"><tr><th></th><th>Last 7 days</th><th>Last 30 days</th><th>All time</th></tr>
      ${row('Enquiries sent from gallery pages', w => n(o.enquiries[w].from_gallery_pages))}
      ${row('Email enquiries you logged', w => n(o.enquiries[w].logged_by_email))}
      ${row('Art for Hire enquiries', w => n(o.hire_enquiries[w]))}
      ${row('Checkouts started (live)', w => n(o.checkout_started[w].live))}
      ${row('Purchases completed (live)', w => n(o.purchases[w].live_paid_baskets))}
      ${row('Value of completed purchases (live)', w => o.purchases[w].live_paid_total_cents === null ? '—' : eur(o.purchases[w].live_paid_total_cents))}
      ${row('Artworks sold and not released', w => n(o.purchases[w].artworks_sold_standing))}
      ${row('Refunds completed', w => n(o.refunds[w]))}
      ${row('Test checkouts started', w => n(o.checkout_started[w].test))}</table></div>
      <p class="st-muted">Relay email to artists, recent enquiries: ${n(o.enquiry_delivery.sent)} sent · ${n(o.enquiry_delivery.send_failed)} failed · ${n(o.enquiry_delivery.received)} waiting. Basket additions are not recorded on the server. — means the records are not installed.</p></section>`;
  }
  /* Delivery offers to review (22 Nov 2026): an artwork can be bought online only once the founder has approved its exact
     current delivery offer. Any change by the artist is a new version and comes back here. */
  const PARTY_LABEL = x => String(x || '—').replace(/_/g, ' ');
  function offerReviews(oj) {
    if (!oj.reviews_installed) return '<section class="st-card"><h2>Delivery offers to review</h2><p class="st-warn">Reviews are not installed (migration 0022): no artwork can be bought online.</p></section>';
    const card = o => { const d = o.delivery, st = o.review.state;
      const facts = [['Artwork price', o.price_eur ? '€' + o.price_eur : 'no price'], ['Delivery charge', eur(o.delivery_cents)], ['From', d.collection_county], ['Islands', d.offshore_islands ? 'included' : 'not included (enquiry)'],
        ['Dispatch within', d.dispatch_days ? d.dispatch_days + ' days' : '—'], ['Delivered within', d.delivery_days ? d.delivery_days + ' days' : '—'], ['Window shown to buyer', d.delivery_window],
        ['Packed / transport by', `${PARTY_LABEL(d.packer)} / ${PARTY_LABEL(d.transport_contracting_party)}${d.transporter_name ? ' (' + d.transporter_name + ')' : ''}`], ['Tracking', d.tracking],
        ['Insurance', `${d.cover_provider || '—'} · holder ${PARTY_LABEL(d.insured_party)} · up to ${eur(d.covered_value_cents || 0)} · excess ${d.excess_cents != null ? eur(d.excess_cents) : '—'} · ${d.cover_period || ''}`],
        ['Cover confirmed', `${d.cover_confirmation_ref || '—'} by ${d.cover_confirmed_by || '—'} on ${d.cover_confirmed_on || '—'}`],
        ['Returns', `${d.return_method || '—'} · ${d.return_address || '—'} · ${d.return_cost_cents != null ? eur(d.return_cost_cents) : '—'} (${d.return_cost_basis || '—'}) · arranged by ${PARTY_LABEL(d.return_arranged_by)}`]];
      const hist = (o.history || []).map(h => `<li>${esc(h.at)} · ${esc(h.type === 'review' ? 'PlotArt ' + h.what : 'artist ' + h.what)} v${esc(h.version)}${h.note ? ' · ' + esc(h.note) : ''}</li>`).join('');
      return `<article class="st-card" data-offer="${esc(o.artwork_id)}" data-version="${esc(o.version)}" data-sha="${esc(o.sha256)}"><h3>${esc(o.title)} <small class="st-muted">by ${esc(o.artist)} · offer version ${esc(o.version)}</small></h3>
        <p><strong>${st === 'approved' ? 'Approved' : st === 'returned' ? 'Returned to the artist' : 'Waiting for your review'}</strong>${o.review.previous ? ` <small class="st-muted">(earlier version ${esc(o.review.previous.version)} was ${esc(o.review.previous.decision)}; this version has not been reviewed)</small>` : ''}</p>
        ${o.problems.length ? `<p class="st-warn">${o.problems.map(esc).join('<br>')}</p>` : ''}
        <dl class="st-dl">${facts.map(([t, v]) => `<dt>${esc(t)}</dt><dd>${esc(v ?? '—')}</dd>`).join('')}</dl>
        ${st !== 'approved' && !o.problems.length ? step('offer-approve', 'Approve this delivery offer…', `<p>${tick(esc(oj.statement))}</p><p><label>Note (optional) <input name="note" maxlength="600"></label></p>`, 'Approve') : ''}
        ${step('offer-return', st === 'approved' ? 'Withdraw approval and return to the artist…' : 'Return to the artist…', `<label>What should the artist change?<textarea name="note" rows="3" maxlength="600" required></textarea></label>`, 'Return')}
        ${hist ? `<details><summary>History</summary><ul>${hist}</ul></details>` : ''}</article>`; };
    const open = oj.offers.filter(o => !o.review.approved), done = oj.offers.filter(o => o.review.approved);
    const compact = o => `<details class="st-step" data-offer="${esc(o.artwork_id)}" data-version="${esc(o.version)}" data-sha="${esc(o.sha256)}"><summary>${esc(o.title)} · ${esc(o.artist)} · delivery ${eur(o.delivery_cents)} · v${esc(o.version)}</summary>${card(o)}</details>`;
    return `<section class="st-card" id="offer-reviews"><h2>Delivery offers to review <small class="st-muted">${oj.waiting} waiting</small></h2>
      <p class="st-muted">An artwork can be bought online only after you approve its exact current delivery offer. Any change by the artist comes back here.</p>
      ${open.length ? open.map(card).join('') : '<p>Nothing waiting for review.</p>'}
      ${done.length ? `<details><summary>Approved offers (${done.length})</summary>${done.map(compact).join('')}</details>` : ''}</section>`;
  }
  function wireOffers(oj) {
    if (!oj || !oj.installed) return;
    const go = (kind, fn) => app.querySelectorAll(`form[data-f="${kind}"]`).forEach(f => f.addEventListener('submit', act(async e => { const card = e.target.closest('[data-offer]');
      await fn(new FormData(e.target), { id: card.dataset.offer, version: Number(card.dataset.version), sha256: card.dataset.sha }); loadReadiness(); })));
    go('offer-approve', async (f, o) => { need(f.get('confirm') === 'on', 'Tick the box to confirm your review');
      await api('POST', `${base}/baskets/offers/${encodeURIComponent(o.id)}/review`, { decision: 'approved', version: o.version, sha256: o.sha256, confirm: true, statement: oj.statement, note: String(f.get('note') || '').trim() }); say('Delivery offer approved'); });
    go('offer-return', async (f, o) => { const note = String(f.get('note') || '').trim(); need(note.length >= 3, 'Say what the artist should change');
      await api('POST', `${base}/baskets/offers/${encodeURIComponent(o.id)}/review`, { decision: 'returned', version: o.version, sha256: o.sha256, note }); say('Returned to the artist'); });
  }

  /* The artist's steps (22 Nov 2026), from the same readiness check as the founder's Basket readiness tab. Each step
     jumps to its section below; nothing here changes anything. */
  const STEP_AT = { join: '#pay-join', seller: '#pay-seller', stripe: '#pay-stripe', basket: '#basket', disclosure: '#pay-disclosure', delivery: '#pay-delivery' };
  /* Step links (fixed 22 Nov 2026, mobile report). A step's section appears on the page only once the step it depends on
     is done (the server decides; nothing is unlocked here). Tapping such a step now SAYS which step to complete first,
     beside the list, instead of silently jumping to step 1. An available step scrolls to its section BELOW the sticky
     Studio header (which hid the heading on phones) and opens it if it is folded. */
  const STEP_NEEDS = { seller: 'join', stripe: 'join', basket: 'join', disclosure: 'basket', delivery: 'basket' };
  function goTo(t) {
    if (t.tagName === 'DETAILS') t.open = true;
    const hdr = document.querySelector('.st-top'), off = (hdr ? hdr.getBoundingClientRect().bottom : 0) + 12;
    window.scrollTo({ top: Math.max(0, t.getBoundingClientRect().top + window.scrollY - off), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    const f = t.matches('h2, h3, p, details') ? (t.tagName === 'DETAILS' ? t.querySelector('summary') : t) : null;
    if (f) { if (!f.hasAttribute('tabindex') && f.tagName !== 'SUMMARY') f.setAttribute('tabindex', '-1'); f.focus({ preventScroll: true }); }
  }
  function wireSteps() {
    const msg = app.querySelector('[data-step-msg]');
    app.querySelectorAll('a[data-step]').forEach(a => a.addEventListener('click', e => {
      e.preventDefault();
      const k = a.dataset.step, t = app.querySelector(a.getAttribute('href'));
      if (msg) { msg.hidden = true; msg.textContent = ''; }
      if (t) { goTo(t); return; }
      // not on the page yet: name the step to complete first (from the server's own list), and offer to go there
      const steps = (RD && RD.steps) || [], at = x => steps.indexOf(x) + 1, me = steps.find(x => x.key === k), by = key => steps.find(x => x.key === key);
      // the earliest unfinished step this one depends on (step 5 needs step 4, which needs step 1)
      let first = null; for (let q = STEP_NEEDS[k]; q; q = STEP_NEEDS[q]) { const x = by(q); if (x && !x.done) first = x; }
      if (!first) first = steps.find(x => !x.done && x.key !== k);
      if (!msg) return;
      const what = me ? `Step ${at(me)} opens` : 'Delivery choices open';
      msg.innerHTML = first ? `${what} once step ${at(first)} is complete: <strong>${esc(first.label)}</strong>. <a href="${STEP_AT[first.key]}" data-step-go="${esc(first.key)}">Go to step ${at(first)}</a>`
        : 'This step is not available just now. Please refresh the page.';
      msg.hidden = false;
      const go = msg.querySelector('[data-step-go]');
      if (go) go.addEventListener('click', ev => { ev.preventDefault(); const g = app.querySelector(go.getAttribute('href')); if (g) goTo(g); });
      msg.focus({ preventScroll: true });
      msg.scrollIntoView({ block: 'nearest' });
    }));
  }

  /* Two separate things (23 Nov 2026): the account set-up (five steps, once) and, per artwork, whether it can be bought
     online (a fixed delivery price approved by PlotArt, or delivery arranged personally: buyers enquire). Finishing the
     set-up never suggests that every artwork can now be bought online. */
  function stepsCard(r) {
    const o = r.online, d = r.delivery || { fixed_approved: 0, fixed_waiting: 0, fixed_returned: 0, arranged: 0 };
    const why = Object.entries(o.reasons || {}).filter(([t]) => !/^delivery arranged personally|^fixed delivery price (waiting|returned)/.test(t)).sort((x, y) => y[1] - x[1]);
    const n = (k, one, many) => `${k} ${k === 1 ? one : many}`;
    return `<section class="st-card st-os-steps" aria-labelledby="os-steps-h"><div class="st-ck-top"><h2 id="os-steps-h">Account set-up</h2><span class="st-ck-count">${r.done} of ${r.total} done</span></div>
      <p class="st-muted st-os-note" style="margin-top:6px">Once, for your account. It lets you sell online; each artwork is then set up below.</p>
      <div class="st-os-bar" aria-hidden="true"><span style="width:${Math.round(100 * r.done / r.total)}%"></span></div>
      <ol class="st-os-list">${r.steps.map((x, i) => `<li class="${x.done ? 'done' : x.key === r.next ? 'next' : ''}"><a href="${STEP_AT[x.key]}" data-step="${x.key}"><span class="st-os-n" aria-hidden="true">${x.done ? '✓' : i + 1}</span><span>${esc(x.label)}</span><span class="st-os-s">${x.done ? 'Done' : x.key === r.next ? 'Next' : 'To do'}</span></a></li>`).join('')}</ol>
      <p class="st-os-msg" data-step-msg role="status" aria-live="polite" tabindex="-1" hidden></p>
      ${r.enabled ? '' : '<p class="st-os-msg" data-os-closed>Online sales are not open yet. Your steps can be completed once PlotArt opens them; nothing you have saved is lost.</p>'}
      ${r.founding ? `<p class="st-muted st-os-note">Founding Artist: your commission-free artworks can also be bought online if you give the separate, optional processing-fee consent in the basket section${r.processing_consent ? ' (given)' : ''}.</p>` : ''}
      </section>
      <section class="st-card st-os-art" aria-labelledby="os-art-h"><div class="st-ck-top"><h2 id="os-art-h">Your artworks</h2><span class="st-ck-count">${o.purchasable} of ${o.available} online</span></div>
      <p class="st-os-state">${o.available ? `${n(o.purchasable, 'artwork', 'artworks')} of ${o.available} available can be bought online` : 'No available artworks yet'}</p>
      <p class="st-muted st-os-note" style="margin-top:4px">${r.ready ? 'An artwork can be bought online only with a fixed delivery price that PlotArt has approved. For the others, buyers enquire.' : 'Artworks can be bought online once your account set-up is complete and an artwork has a fixed delivery price approved by PlotArt.'}</p>
      <ul class="st-os-dv">
        <li><span>Fixed delivery price, approved</span><b>${d.fixed_approved}</b></li>
        ${d.fixed_waiting ? `<li><span>Fixed delivery price, waiting for PlotArt</span><b>${d.fixed_waiting}</b></li>` : ''}
        ${d.fixed_returned ? `<li class="st-warn"><span>Fixed delivery price, returned by PlotArt</span><b>${d.fixed_returned}</b></li>` : ''}
        <li><span>Delivery arranged personally (buyers enquire)</span><b>${d.arranged}</b></li>
      </ul>
      ${why.length ? `<ul class="st-os-why">${why.map(([t, k]) => `<li>${k} ${esc(t)}</li>`).join('')}</ul>` : ''}
      <p class="st-actions" style="margin:12px 0 0"><a class="st-btn st-btn--small" href="#pay-delivery" data-step="delivery">Choose delivery for each artwork</a></p></section>`;
  }

  async function load() {
    const j = await api('GET', base);
    if (!j.installed) { app.innerHTML = '<h1>Payment pilot</h1><p>The payment pilot is not installed.</p>'; return; }
    const sw = j.switches;
    let h;
    if (founder) {
      h = `<h1>Payment pilot <small class="st-muted">(${sw && sw.live ? 'LIVE: real payments' : 'Stripe test mode'})</small></h1><p id="page-error" class="st-err" role="alert" tabindex="-1" hidden></p>`;
      h += `<p class="st-muted">Pilot ${sw.enabled ? (sw.live ? 'switched ON (LIVE: real card payments)' : 'switched ON (test mode)') : 'switched OFF'}${sw.key_problem ? ' · ' + esc(sw.key_problem) : ''}.${sw.live ? '' : ' No live payment can be taken.'}</p>`;
    } else {
      // the artist's Online sales page (22 Nov 2026): what it is, then their steps and which artworks can be bought online
      h = `<p class="st-muted">Optional</p><h1 class="st-h1">Online sales</h1><p id="page-error" class="st-err" role="alert" tabindex="-1" hidden></p>
        <p class="st-muted st-os-lead">Buyers can buy your available artworks online with one secure card payment, alone or with other artists’ works. You remain the seller and are paid into your own Stripe account. Your gallery, enquiries and direct sales work exactly as now whether or not you set this up.${sw.enabled ? (sw.live ? '' : ' <strong>Test mode: no real payment can be taken.</strong>') : ' <strong>Online sales are not open at the moment.</strong>'}</p>`;
      let rd = null; try { rd = await api('GET', base + '/basket/readiness'); } catch { rd = null; }
      RD = rd && rd.installed ? rd : null;
      if (rd && rd.installed) h += stepsCard(rd);
    }
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
          <td>${esc(w.reminders.join(', ') || '—')}</td><td><a href="#order-${esc(w.order_id)}" data-open="${w.kind === 'lost_dispute_commission' ? 'returncommission' : 'shortfallpaid'}">${w.kind === 'lost_dispute_commission' ? 'Return commission…' : 'Record payment…'}</a></td></tr>
          ${payRow(w, 9)}`).join('')}</table>` : '<p class="st-muted">Nothing owed.</p>'}
        ${(j.owed_returnable || []).length ? `<h3>Settled by bank transfer: record a returned transfer</h3><p class="st-muted">Fully paid amounts leave the list above. If the bank later returns one of these transfers (executed in the last ${esc(String(j.return_window_days || 90))} days), record it here; the amount becomes owed again.</p>
          <table class="st-table" data-owed-returnable><tr><th>Order</th><th>Artist</th><th>What</th><th>Owed</th><th>Paid</th></tr>
          ${j.owed_returnable.map(w => `<tr data-id="${esc(w.order_id)}"><td>${esc(w.reference)}</td><td>${esc(w.artist_name)}</td><td>${esc(w.kind.replace(/_/g, ' '))}</td><td>${eur(w.cents)}</td><td>${eur(w.settled_cents)}</td></tr>${payRow(w, 4)}`).join('')}</table>` : ''}
        ${(j.reimbursements || []).length ? `<h3>Processing reimbursements (seven-day rule${j.deadlines && j.deadlines.reimburse_provisional ? ', provisional' : ', sandbox rule approved 18 Nov 2026'})</h3><table class="st-table"><tr><th>Order</th><th>Status</th><th>Amount</th><th>Paid (Irish date)</th><th>Due</th><th>Alerts and attempts</th></tr>${j.reimbursements.map(x => `<tr${x.overdue || x.failing ? ' class="st-warn"' : ''}><td>${esc(x.reference)}<br><small>day ${x.day}</small></td><td>${esc(x.status_label)}${x.overdue ? '<br><strong>OVERDUE</strong>' : ''}</td><td>${esc(x.amount_label)}</td><td>${esc(x.payment_confirmed)}</td><td>${esc(x.due_label)}</td><td><small>${[x.alerts.day5 ? 'Day-5 alert sent' : '', x.alerts.deadline || x.alerts.extended_deadline ? 'Deadline alert sent' : '', x.delay_notice_at ? 'Delay notice sent to the artist (test sink)' : '', x.attempts ? `${x.attempts} failed attempt(s); last: ${x.last_error || ''}. Due date unchanged.` : '', ...x.flags].filter(Boolean).map(esc).join('<br>')}</small>${x.action ? `<br><button data-a="processing" data-id="${esc(x.order_id)}">Reconcile processing fee</button>` : ''}</td></tr>`).join('')}</table>` : ''}
        <details><summary>How to pay a shortfall (bank details process)</summary><ol>${j.bank_details_process.map(x => `<li>${esc(x)}</li>`).join('')}</ol></details>`;
      if (j.holds.length) h += `<h2>Legal holds</h2><ul>${j.holds.map(x => `<li data-hold="${esc(x.id)}">${esc(x.reference)} · ${esc(x.basis)} · review by ${esc(x.review_by)}${x.review_overdue ? ' <strong>(review overdue)</strong>' : ''} — ${esc(x.reason)}
        ${step('renew', 'Renew…', `${field(`hr-rv-${esc(x.id)}`, 'New review date (within 12 months)', `<input id="hr-rv-${esc(x.id)}" name="review_by" type="date" min="${plusDaysIE(1)}" max="${plusDaysIE(365)}" required>`)}
          ${field(`hr-why-${esc(x.id)}`, 'Why is the hold still needed? (10 characters or more)', `<textarea id="hr-why-${esc(x.id)}" name="note" rows="2" maxlength="1000" required></textarea>`)}`, 'Renew hold')}
        ${step('release', 'Release…', `${field(`hl-why-${esc(x.id)}`, 'Why can it be released? (10 characters or more)', `<textarea id="hl-why-${esc(x.id)}" name="note" rows="2" maxlength="1000" required></textarea>`)}
          ${tick('Release this hold. The order’s records then follow the normal retention rules.')}`, 'Release hold')}</li>`).join('')}</ul>`;
      if (j.unprocessed_events.length) h += `<h2>Provider events waiting</h2><ul>${j.unprocessed_events.map(e => `<li>${esc(e.type)} · ${esc(e.status)} · ${esc(e.detail || '')}</li>`).join('')}</ul>`;
    } else {
      const m = j.membership;
      h += '<section class="st-card st-os-sec">';   // the artist's payment set-up in one card (22 Nov 2026)
      if (j.agreement_unavailable) h += `<h2 id="pay-join">Online sales</h2><p class="st-warn" data-r2-unavailable>${esc(j.agreement_unavailable)}</p>`;
      else if (!m.opted_in) h += j.addendum ? `<h2 id="pay-join">Join online sales</h2><p>Read the <a href="/payment-terms/${esc(j.addendum.doc_id)}.html" target="_blank" rel="noopener">${esc(j.addendum.title)}</a>.</p>
        <form data-f="optin"><label><input type="checkbox" name="accept" required> ${esc(j.addendum.statement)}</label>${sw.enabled ? '<button>Set up online sales</button>' : '<button disabled aria-describedby="os-closed-note">Set up online sales</button><p class="st-muted" id="os-closed-note">Online sales are not open yet.</p>'}</form>` : '<p id="pay-join">The payment addendum has not been issued yet.</p>';
      else {
        h += `<h2>Payments and Stripe</h2><p class="st-muted">${esc(j.direct_payment_note)}</p>`;
        if (j.seller_profile && !j.checkout_available) h += `<p class="st-warn">${esc(j.trader_question.unavailable)}</p>`;
        const sp = j.seller_profile || {};
        h += `<p id="pay-join" class="st-muted">You joined on ${esc(m.opted_in_at)} (${esc(m.addendum)}).</p><details id="pay-seller" ${j.seller_problems.length ? 'open' : ''}><summary>Seller information for managed checkout${j.seller_problems.length ? ' — needed before any managed-checkout quote' : ''}</summary><p>${esc(j.trader_question.direct)}</p><form data-f="seller">
          ${[['legal_name', 'Legal name'], ['trading_name', 'Trading name (optional)'], ['address', 'Address where you are established'], ['returns_address', 'Returns and complaints address, if different (optional)'], ['email', 'Email for buyers'], ['phone', 'Telephone for buyers'], ['vat_number', 'VAT number, if registered (optional)']]
            .map(([k, t]) => `<label>${t} <input name="${k}" value="${esc(sp[k] || '')}"></label>`).join('')}
          <fieldset><legend>${esc(j.trader_question.question)}</legend><p class="st-muted"><em>${esc(j.trader_question.review_note)}</em></p><p class="st-muted">${esc(j.trader_question.intro)}</p><p class="st-muted">${esc(j.trader_question.explain)}</p>
          ${j.trader_choices.map(c => `<label><input type="radio" name="trader_status" value="${esc(c.value)}" required ${sp.trader_status === c.value ? 'checked' : ''}> <strong>${esc(c.label)}</strong><br><small>${esc(c.meaning)}</small></label>`).join('')}</fieldset>
          <label><input type="checkbox" name="confirm" required> ${esc(j.seller_declaration)}</label><button>Save seller information</button></form></details>`;
        if (j.pending_refunds.length) h += `<h2>A refund is waiting for your Stripe balance</h2>${j.pending_refunds.map(r => `<p class="st-warn">${esc(r.reference)}: ${eur(r.amount_cents)}, waiting ${r.days_pending} days. Stripe cancels it on ${esc(r.stripe_fails_it_by)} if still unfunded.</p>`).join('')}<ol>${j.pending_refunds[0].what_to_do.map(x => `<li>${esc(x)}</li>`).join('')}</ol>`;
        h += m.processing_consent ? `<p>You have agreed that Stripe’s processing fees may be deducted on commission-free pilot orders (${esc(m.processing_consent_at)}). <button data-a2="withdraw-processing">Withdraw this consent</button></p>`
          : `<details><summary>Commission-free sales through the pilot (optional, separate consent)</summary><form data-f="processing"><label><input type="checkbox" name="accept" required> ${esc(j.processing_statement)}</label><button>Give this consent</button></form></details>`;
        h += `<p id="pay-stripe">Stripe: ${m.account ? (m.ready ? (j.switches && j.switches.live ? 'ready to take payments' : 'ready to take test payments') : 'onboarding incomplete' + (m.account.requirements_due.length ? ' — Stripe still needs: ' + esc(m.account.requirements_due.join(', ')) : '')) : 'not connected yet'}.</p>
          <p><button data-a2="onboard">${m.account ? 'Continue Stripe onboarding' : 'Connect a Stripe account'}</button> ${m.account ? '<button data-a2="refresh">Refresh status</button>' : ''}</p>`
          + step('leave', 'Stop online sales…', `<p class="st-muted">Unpaid quotes are cancelled; paid orders continue to completion. Your seller information is removed (each issued quote keeps its own copy). You keep selling directly, as now, and can join again later.</p>
            ${tick('Stop online sales.')}`, 'Stop online sales');
      }
      h += '</section>';
    }
    // multi-artist basket (separate, optional): artist controls and founder readiness
    let bj = null;
    try { bj = founder ? await api('GET', base + '/baskets/artists') : (j.membership && j.membership.opted_in ? await api('GET', base + '/basket') : null); } catch { bj = null; }
    if (bj && bj.installed) h += founder ? basketFounder(bj) : basketArtist(bj, j);
    h += `<h2>Orders</h2>${j.orders.length ? j.orders.map(orderCard).join('') : '<p class="st-muted">None yet.</p>'}`;
    app.innerHTML = h;
    wireSteps();
    J_BASKET = bj;
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
      await api('POST', `${base}/orders/${id}/${a}`, {});
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
    on('form[data-f="basket-optin"]', 'submit', async () => { const b = J_BASKET; await api('POST', base + '/basket/opt-in', { accept: true, doc_id: b.addendum.doc_id, html_sha256: b.addendum.html_sha256 }); say('You are taking part in the basket'); load(); });
    on('form[data-f="basket-disclosure"]', 'submit', async () => { const b = J_BASKET; await api('POST', base + '/basket/seller-disclosure', { accept: true, statement: b.disclosure_statement, subject_sha256: b.seller_info.subject_sha256 }); say('Confirmed'); load(); });
    on('form[data-f="basket-processing"]', 'submit', async () => { const b = J_BASKET; await api('POST', base + '/basket/processing-consent', { accept: true, statement: b.processing_statement }); say('Consent recorded'); load(); });
    on('form[data-f="offer"]', 'submit', async e => { const f = new FormData(e.target), id = e.target.querySelector('[data-id]').dataset.id, F = J_BASKET.delivery_fields, d = {};
      need(f.get('confirm') === 'on', 'Tick the box to confirm the delivery offer');
      for (const [k, t] of Object.entries(F)) { if (k === 'destination' || k === 'destination_country') continue; const raw = String(f.get(k) ?? '').trim(), ty = typeof t === 'string' ? t.replace('?', '') : t;
        if (!raw) { d[k] = null; continue; }
        d[k] = CENTS.includes(k) ? toCents(raw, label(k)) : ty === 'n' ? Number(raw.replace(',', '.')) : ty === 'b' ? raw === 'true' : raw; }
      await api('PUT', `${base}/basket/offers/${encodeURIComponent(id)}`, { confirm: true, delivery_cents: toCents(f.get('charge'), 'delivery charge'), delivery: d }); say('Delivery offer saved'); load(); });
    // delivery choice (23 Nov 2026): "Fixed" opens the existing form; "Arranged personally" on a fixed offer asks to confirm, then withdraws it
    app.querySelectorAll('.st-dv-opt').forEach(b => b.addEventListener('click', () => {
      const li = b.closest('.st-dv'), form = li.querySelector('details'), off = li.querySelector('.st-dv-off');
      if (b.dataset.dv === 'fixed') { if (off) off.hidden = true; if (form) { form.open = true; goTo(form); } return; }
      if (off) { off.hidden = false; off.querySelector('button').focus(); } else if (form) form.open = false;
    }));
    app.querySelectorAll('[data-dv-cancel]').forEach(b => b.addEventListener('click', () => { b.closest('.st-dv-off').hidden = true; }));
    on('button[data-withdraw-offer]', 'click', async e => { await api('DELETE', `${base}/basket/offers/${encodeURIComponent(e.target.dataset.withdrawOffer)}`); say('Delivery is now arranged personally for this artwork'); load(); });
    on('form[data-f="basket-leave"]', 'submit', async (e) => { need(new FormData(e.target).get('confirm') === 'on', 'Tick the box to confirm'); await api('POST', base + '/basket/leave', {}); say('Online purchase stopped'); load(); });
    on('form[data-f="processing"]', 'submit', async () => { await api('POST', base + '/processing-consent', { accept: true, statement: j.processing_statement }); say('Consent recorded'); load(); });
    const F = (kind, fn) => on(`form[data-f="${kind}"]`, 'submit', async e => fn(e, new FormData(e.target), e.target));
    const noteOf = (f, min, what) => { const t = String(f.get('note') || '').trim(); need(t.length >= min, what); return t; };
    F('hold', async (e, f) => { const basis = f.get('basis'), reason = String(f.get('reason') || '').trim(), review_by = f.get('review_by');
      need(basis, 'Choose the basis for the hold'); need(reason.length >= 10, 'Give the specific reason for the hold (10–1,000 characters)'); need(isDate(review_by), 'Give a review date within the next 12 months');
      await api('POST', `${base}/orders/${idOf(e.target)}/hold`, { basis, reason, review_by }); say('Legal hold placed'); load(); });
    F('repaid', async (e, f) => { const artwork_cents = toCents(f.get('artwork'), 'artwork amount'), delivery_cents = toCents(f.get('delivery'), 'delivery amount'), evidence = String(f.get('evidence') || '').trim();
      need(artwork_cents + delivery_cents > 0, 'Enter the artwork or delivery amount repaid'); need(evidence.length >= 10, 'Describe the evidence (bank transfer reference, date, and the buyer’s confirmation)');
      need(f.get('confirm') === 'on', 'Tick the box to confirm the repayment');
      await api('POST', `${base}/orders/${idOf(e.target)}/repaid`, { artwork_cents, delivery_cents, evidence }); say('Repayment recorded'); load(); });
    F('shortfallpaid', async (e, f) => { const amount_cents = toCents(f.get('amount'), 'amount paid'), executed_on = f.get('executed_on'), reference = String(f.get('reference') || '').trim();
      need(amount_cents > 0, 'Enter the amount the bank shows as executed'); need(isDate(executed_on), 'Give the date the bank shows the transfer as executed');
      need(executed_on <= todayIE(), 'The execution date cannot be in the future: record the payment once the bank shows it executed');
      need(reference.length >= 6, 'Give the bank’s transfer reference (6–200 characters)'); need(f.get('confirm') === 'on', 'Tick the box to confirm the bank shows the transfer as executed');
      await api('POST', `${base}/orders/${idOf(e.target)}/shortfallpaid`, { amount_cents, executed_on, reference }); say('Shortfall payment recorded'); load(); });
    F('shortfallreturned', async (e, f) => { const returned_on = f.get('returned_on'), reason = String(f.get('reason') || '').trim();
      need(isDate(returned_on), 'Give the date the bank shows the transfer as returned'); need(reason.length >= 5, 'Give the reason the bank gave (5–300 characters, no bank details)');
      need(f.get('confirm') === 'on', 'Tick the box to confirm the bank shows the transfer as returned');
      await api('POST', `${base}/orders/${idOf(e.target)}/shortfallreturned`, { payment_id: f.get('payment_id'), returned_on, reason }); say('Returned transfer recorded'); load(); });
    F('returncommission', async (e, f) => { const reason = String(f.get('reason') || '').trim();
      need(reason.length >= 3, 'Give a reason'); need(f.get('confirm') === 'on', 'Tick the box to confirm the commission return');
      await api('POST', `${base}/orders/${idOf(e.target)}/refund`, { commission_only: true, reason }); say('Commission returned'); load(); });
    F('cancel', async (e, f) => { need(f.get('confirm') === 'on', 'Tick the box to confirm the cancellation');
      await api('POST', `${base}/orders/${idOf(e.target)}/cancel`, { reason: String(f.get('reason') || '').trim() }); say('Order cancelled'); load(); });
    F('decline', async (e, f) => { const id = idOf(e.target);
      await api('POST', `${base}/orders/${id}/approve`, { decision: 'decline', quote_version: j.orders.find(o => o.id === id).quote_version, note: String(f.get('note') || '').trim() }); say('Sent back to PlotArt for changes'); load(); });
    F('renew', async (e, f) => { const id = e.target.closest('[data-hold]').dataset.hold, review_by = f.get('review_by');
      need(isDate(review_by), 'Give a new review date within the next 12 months'); const note = noteOf(f, 10, 'Record why the hold is still needed (10 characters or more)');
      await api('POST', `${base}/holds/${id}`, { decision: 'renew', review_by, note }); say('Hold renewed'); load(); });
    F('release', async (e, f) => { const id = e.target.closest('[data-hold]').dataset.hold, note = noteOf(f, 10, 'Record why the hold can be released (10 characters or more)');
      need(f.get('confirm') === 'on', 'Tick the box to confirm the release');
      await api('POST', `${base}/holds/${id}`, { decision: 'release', note }); say('Hold released'); load(); });
    F('leave', async (e, f) => { need(f.get('confirm') === 'on', 'Tick the box to confirm you are leaving the pilot');
      await api('POST', `${base}/leave`, {}); say('You left the payment pilot'); load(); });
    app.querySelectorAll('a[data-open]').forEach(a => a.addEventListener('click', () => {
      const d = app.querySelector(`#order-${CSS.escape(a.getAttribute('href').slice(7))} details[data-step="${a.dataset.open}"]`); if (d) { d.open = true; setTimeout(() => d.querySelector('input, textarea, select')?.focus(), 0); } }));
    on('button[data-a2]', 'click', async e => { const a = e.target.dataset.a2;
      if (a === 'withdraw-basket-processing') { await api('POST', base + '/basket/processing-consent/withdraw', {}); say('Consent withdrawn'); load(); return; }
      if (a === 'withdraw-disclosure') { await api('POST', base + '/basket/seller-disclosure/withdraw', {}); say('Withdrawn'); load(); return; }
      if (a === 'withdraw-processing') { await api('POST', base + '/processing-consent/withdraw', {}); load(); return; }
      if (a === 'onboard') { const r = await api('POST', base + '/onboarding', {}); location.href = r.url; return; }
      if (a === 'refresh') { await api('POST', `${base}/account/refresh`, {}); load(); } });
    on('button[data-refresh]', 'click', async e => { await api('POST', `${base}/accounts/${e.target.dataset.refresh}/refresh`, {}); load(); });
  }
  if (location.pathname === '/admin/baskets') { loadReadiness(); return; }
  document.querySelector('.st-tabs a[aria-current]')?.scrollIntoView({ block: 'nearest', inline: 'center' });   // Online sales tab in view on phones
  load().catch(e => { app.innerHTML = `<p>${esc(e.message)}</p>`; });
})();
