/* PlotArt Studio · Commercial (founder; migration 0032, 27 Nov 2026). One page: the leads list (#/) and a lead (#/lead/<id>).
   Studio is the single record of business enquiries: emails captured from Gmail and website requests arrive here on their
   own; everything after (works, artist approvals, proposal, agreements, invoices, payments, placements, renewals) is
   recorded here, once. */
(() => {
  const app = document.getElementById('app');
  const E = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const eur = c => c == null ? '—' : '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: c % 100 ? 2 : 0, maximumFractionDigits: 2 });
  const when = s => s ? new Date(s).toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric' }) : '';
  const api = async (method, path, body) => {
    const r = await fetch(path, { method, headers: { 'X-Studio': '1', 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
    const j = await r.json().catch(() => ({ ok: false, error: 'Unreadable response' }));
    if (!j.ok) throw new Error(j.error || 'Refused');
    return j;
  };
  const say = m => { const s = document.getElementById('saved'); s.textContent = m; s.classList.add('on'); setTimeout(() => s.classList.remove('on'), 3500); };
  const fail = (f, msg) => { let b = f.querySelector('[data-err]'); if (!b) { b = document.createElement('p'); b.className = 'st-err'; b.dataset.err = ''; b.setAttribute('role', 'alert'); f.appendChild(b); } b.textContent = msg; b.hidden = false; };
  const form = f => Object.fromEntries(new FormData(f).entries());
  const SECTORS = ['hotel', 'office', 'hospitality', 'retail', 'healthcare', 'property', 'interiors', 'production', 'other'];
  const SOURCES = { outreach_reply: 'Outreach reply', email: 'Email', phone: 'Phone', introduction: 'Introduction', website_form: 'Website form', other: 'Other' };
  const SEL = { proposed: 'Proposed', artist_asked: 'Artist asked', artist_approved: 'Artist approved', artist_declined: 'Artist declined', client_chosen: 'Chosen by the business', client_declined: 'Not chosen', withdrawn: 'Withdrawn' };
  const DOCS = { proposal: ['Proposal', ['draft', 'sent', 'accepted', 'declined', 'void']], fee_agreement: ['PlotArt fee agreement', ['draft', 'sent', 'signed', 'void']],
    hire_agreement: ['Hire agreement (artist and business)', ['draft', 'sent', 'signed', 'void']], invoice: ['Invoice', ['draft', 'issued', 'paid', 'void']], credit_note: ['Credit note', ['issued', 'void']] };
  const PL = { scheduled: 'Scheduled', active: 'On the wall', sale_notice: 'Sale notice given', sold: 'Sold', replaced: 'Replaced', ended: 'Ended', renewed: 'Renewed' };
  const opts = (list, cur, label = x => x) => list.map(v => `<option value="${E(v)}"${v === cur ? ' selected' : ''}>${E(label(v))}</option>`).join('');
  const pill = (t, k) => `<span class="st-pill${k ? ' st-pill--' + k : ''}">${E(t)}</span>`;
  const stageKind = s => ['won', 'placed', 'agreed'].includes(s) ? 'ok' : ['lost', 'not_now'].includes(s) ? 'bad' : ['renewal_due', 'artist_approval'].includes(s) ? 'warn' : '';

  async function list() {
    let d; try { d = await api('GET', '/api/admin/commercial'); } catch (e) { app.innerHTML = `<p class="st-err">${E(e.message)}</p>`; return; }
    if (!d.installed) { app.innerHTML = '<section class="st-card"><h1 class="st-h">Commercial</h1><p class="st-muted">Commercial leads aren’t installed yet: they start once migration 0032 has run.</p></section>'; return; }
    const t = d.totals, today = new Date().toISOString().slice(0, 10);
    app.innerHTML = `<section class="st-card"><h1 class="st-h">Commercial</h1>
      <p class="st-muted">Every business enquiry and what follows it, in one place. Replies you label <b>PlotArt Lead</b> in Gmail and requests from the Art for Hire page arrive here on their own.</p>
      <div class="st-kpis st-kpis--fit">
        <div class="st-kpi"><b>${t.open}</b><span>open leads</span></div>
        <div class="st-kpi"><b>${t.due}</b><span>actions due</span></div>
        <div class="st-kpi"><b>${t.approved_rental_works}</b><span>works approved for rental (aim 10–20)</span></div>
        <div class="st-kpi"><b>${eur(t.monthly_cents)}</b><span>monthly rent on the wall (${eur(t.plotart_monthly_cents)} PlotArt)</span></div>
        <div class="st-kpi"><b>${t.ending_soon}</b><span>placements ending within a month</span></div>
        <div class="st-kpi"><b>${eur(t.rent_due_cents)}</b><span>PlotArt fees to invoice</span></div></div></section>
    ${d.rent_due.length ? `<section class="st-card"><h2 class="st-sub">Rent to invoice</h2><p class="st-muted">PlotArt invoices its 1% fee each month; the artist invoices their 3% under the hire agreement.</p>
      <div class="st-scroll"><table class="st-table"><thead><tr><th>Business</th><th>Work</th><th>Month</th><th>PlotArt fee</th><th>Artist (3%)</th><th></th></tr></thead><tbody>
      ${d.rent_due.map(r => `<tr><td><a href="#/lead/${E(r.lead_id)}">${E(r.business)}</a></td><td>${E(r.artwork_title)}<br><span class="st-muted">${E(r.artist)}</span></td><td>${E(when(r.period_from))} – ${E(when(r.period_to))}</td>
        <td>${eur(r.plotart_cents)}</td><td>${eur(r.artist_cents)}</td><td><form data-rent class="st-row"><input type="hidden" name="placement_id" value="${E(r.placement_id)}"><input type="hidden" name="period_from" value="${E(r.period_from)}">
        <input class="st-in" name="number" placeholder="Invoice no." required minlength="3" maxlength="40" size="10"><button class="st-btn st-btn--small">Record invoice</button></form></td></tr>`).join('')}</tbody></table></div></section>` : ''}
    ${d.renewals.length ? `<section class="st-card"><h2 class="st-sub">Renewals to discuss</h2><ul class="cm-tl">${d.renewals.map(p => `<li><a href="#/lead/${E(p.lead_id)}">${E(p.business)}</a>: ${E(p.artwork_title)} (${E(p.artist)}) ends ${E(when(p.end_on))}</li>`).join('')}</ul></section>` : ''}
    <section class="st-card"><h2 class="st-sub">Leads</h2>
      ${d.leads.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Business</th><th>Stage</th><th>Next action</th><th>Works</th><th>Last activity</th></tr></thead><tbody>
      ${d.leads.map(l => `<tr><td><a href="#/lead/${E(l.id)}"><b>${E(l.business)}</b></a><br><span class="st-muted">${E(l.contact_name || l.contact_email || '')} · ${E(SOURCES[l.source] || l.source)}</span></td>
        <td>${pill(d.stage_label[l.stage], stageKind(l.stage))}</td>
        <td>${l.next_action ? E(l.next_action) : '<span class="st-muted">—</span>'}${l.next_action_on ? `<br><span class="${l.next_action_on <= today ? 'st-err' : 'st-muted'}">${E(when(l.next_action_on))}</span>` : ''}</td>
        <td>${l.works}${l.placed ? ` · ${l.placed} placed` : ''}</td><td>${E(when(l.last_activity_at))}</td></tr>`).join('')}</tbody></table></div>`
        : '<p class="st-muted">No leads yet. Label a reply “PlotArt Lead” in Gmail, or add one below.</p>'}</section>
    ${d.placements.length ? `<section class="st-card"><h2 class="st-sub">On the wall</h2><div class="st-scroll"><table class="st-table"><thead><tr><th>Work</th><th>Business</th><th>Until</th><th>Monthly</th><th>Artist / PlotArt</th></tr></thead><tbody>
      ${d.placements.map(p => `<tr><td>${E(p.artwork_title)}<br><span class="st-muted">${E(p.artist)}</span></td><td><a href="#/lead/${E(p.lead_id)}">${E(p.business)}</a></td><td>${E(when(p.end_on))} ${pill(PL[p.status])}</td><td>${eur(p.monthly_cents)}</td><td>${eur(p.artist_monthly_cents)} / ${eur(p.plotart_monthly_cents)}</td></tr>`).join('')}
      </tbody></table></div></section>` : ''}
    <section class="st-card"><h2 class="st-sub">Add a lead</h2>
      <form data-new class="cm-grid">
        <label class="st-f"><span class="st-lab">Business</span><input class="st-in" name="business" required minlength="2" maxlength="160"></label>
        <label class="st-f"><span class="st-lab">Sector</span><select class="st-in" name="sector"><option value="">—</option>${opts(SECTORS)}</select></label>
        <label class="st-f"><span class="st-lab">Contact name</span><input class="st-in" name="contact_name" maxlength="120"></label>
        <label class="st-f"><span class="st-lab">Contact email</span><input class="st-in" name="contact_email" type="email" maxlength="200"></label>
        <label class="st-f"><span class="st-lab">Source</span><select class="st-in" name="source">${opts(Object.keys(SOURCES), 'email', k => SOURCES[k])}</select></label>
        <label class="st-f"><span class="st-lab">Interest</span><select class="st-in" name="interest">${opts(['rental', 'purchase', 'project', 'unsure'], 'unsure')}</select></label>
        <div class="st-actions"><button class="st-btn st-btn--solid">Add lead</button></div></form></section>`;
    app.querySelectorAll('[data-rent]').forEach(f => f.onsubmit = async ev => { ev.preventDefault(); try { await api('POST', '/api/admin/commercial/rent-invoices', form(f)); say('Invoice recorded'); list(); } catch (e) { fail(f, e.message); } });
    app.querySelector('[data-new]').onsubmit = async ev => { ev.preventDefault(); const f = ev.target;
      try { const r = await api('POST', '/api/admin/commercial/leads', form(f)); location.hash = '#/lead/' + r.lead.id; say('Lead added'); } catch (e) { fail(f, e.message); } };
  }

  let cat = null;
  async function lead(id) {
    let d; try { d = await api('GET', '/api/admin/commercial/leads/' + id); } catch (e) { app.innerHTML = `<p class="st-err">${E(e.message)}</p><p><a href="#/">← All leads</a></p>`; return; }
    const l = d.lead, chosen = d.selections.filter(s => s.status === 'client_chosen');
    app.innerHTML = `<p><a href="#/">← All leads</a></p>
    <section class="st-card"><h1 class="st-h">${E(l.business)}</h1><p class="st-muted">${E(l.reference)} · ${E(SOURCES[l.source] || l.source)} · opened ${E(when(l.created_at))}</p>
      <form data-lead class="cm-grid">
        <label class="st-f"><span class="st-lab">Stage</span><select class="st-in" name="stage">${opts(d.stages, l.stage, s => d.stage_label[s])}</select></label>
        <label class="st-f"><span class="st-lab">Next action</span><input class="st-in" name="next_action" maxlength="200" value="${E(l.next_action)}"></label>
        <label class="st-f"><span class="st-lab">Due</span><input class="st-in" type="date" name="next_action_on" value="${E(l.next_action_on)}"></label>
        <label class="st-f"><span class="st-lab">Interest</span><select class="st-in" name="interest">${opts(['rental', 'purchase', 'project', 'unsure'], l.interest)}</select></label>
        <label class="st-f"><span class="st-lab">Business</span><input class="st-in" name="business" value="${E(l.business)}"></label>
        <label class="st-f"><span class="st-lab">Sector</span><select class="st-in" name="sector"><option value="">—</option>${opts(SECTORS, l.sector)}</select></label>
        <label class="st-f"><span class="st-lab">Contact</span><input class="st-in" name="contact_name" value="${E(l.contact_name)}"></label>
        <label class="st-f"><span class="st-lab">Role</span><input class="st-in" name="contact_role" value="${E(l.contact_role)}"></label>
        <label class="st-f"><span class="st-lab">Email</span><input class="st-in" name="contact_email" value="${E(l.contact_email)}"></label>
        <label class="st-f"><span class="st-lab">Phone</span><input class="st-in" name="contact_phone" value="${E(l.contact_phone)}"></label>
        <label class="st-f"><span class="st-lab">Location</span><input class="st-in" name="location" value="${E(l.location)}"></label>
        <label class="st-f"><span class="st-lab">Website</span><input class="st-in" name="website" value="${E(l.website)}"></label>
        <label class="st-f" style="grid-column:1/-1"><span class="st-lab">Summary</span><input class="st-in" name="summary" maxlength="600" value="${E(l.summary)}"></label>
        <div class="st-actions"><button class="st-btn st-btn--solid">Save</button></div></form></section>

    <section class="st-card"><h2 class="st-sub">Works</h2>
      <p class="st-muted">Each work needs its artist’s approval before it’s offered. Business rental: 4% of the price a month, 3% to the artist and 1% to PlotArt.</p>
      ${d.selections.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Work</th><th>Arrangement</th><th>Price</th><th>Monthly (artist / PlotArt)</th><th>Status</th><th></th></tr></thead><tbody>
      ${d.selections.map(s => `<tr><td>${E(s.artwork_title)}<br><span class="st-muted">${E(s.artist)}</span></td><td>${E(s.arrangement)}</td><td>${eur(s.price_cents)}</td>
        <td>${s.monthly_cents ? `${eur(s.monthly_cents)} (${eur(s.artist_monthly_cents)} / ${eur(s.plotart_monthly_cents)})` : '—'}</td>
        <td>${pill(SEL[s.status], s.status === 'artist_approved' || s.status === 'client_chosen' ? 'ok' : /declined|withdrawn/.test(s.status) ? 'bad' : '')}${s.artist_decision_evidence ? `<br><span class="st-muted">${E(s.artist_decision_evidence)}</span>` : ''}</td>
        <td><form data-sel="${E(s.id)}" class="st-row"><select class="st-in" name="status">${opts(Object.keys(SEL), s.status, k => SEL[k])}</select>
          <input class="st-in" name="evidence" placeholder="Artist’s answer (e.g. email 28 Nov)" maxlength="300"><button class="st-btn st-btn--small">Update</button></form></td></tr>`).join('')}
      </tbody></table></div>` : '<p class="st-muted">No works proposed yet.</p>'}
      <form data-addsel class="cm-grid"><label class="st-f" style="grid-column:span 2"><span class="st-lab">Add a work</span><select class="st-in" name="artwork_id" data-cat><option value="">Loading works…</option></select></label>
        <label class="st-f"><span class="st-lab">Arrangement</span><select class="st-in" name="arrangement">${opts(['rental', 'purchase', 'project'], l.interest === 'purchase' ? 'purchase' : l.interest === 'project' ? 'project' : 'rental')}</select></label>
        <div class="st-actions"><button class="st-btn">Propose work</button></div></form></section>

    <section class="st-card"><h2 class="st-sub">Proposal, agreements and invoices</h2>
      ${d.documents.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Document</th><th>Number</th><th>Date</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody>
      ${d.documents.map(x => `<tr><td>${E(DOCS[x.kind][0])}${x.link ? ` · <a href="${E(x.link)}" rel="noopener" target="_blank">open</a>` : ''}</td><td>${E(x.number)}</td><td>${E(when(x.issued_on))}</td>
        <td>${eur(x.amount_cents)}${x.kind === 'invoice' && x.amount_cents ? `<br><span class="st-muted">paid ${eur(x.paid_cents)}</span>` : ''}</td>
        <td><form data-doc="${E(x.id)}" class="st-row"><select class="st-in" name="status">${opts(DOCS[x.kind][1], x.status)}</select><button class="st-btn st-btn--small">Update</button></form></td>
        <td>${x.kind === 'invoice' && x.status !== 'paid' && x.status !== 'void' ? `<form data-pay="${E(x.id)}" class="st-row"><input class="st-in" name="amount" placeholder="€" size="6"><input class="st-in" type="date" name="received_on"><button class="st-btn st-btn--small">Record payment</button></form>` : ''}</td></tr>`).join('')}
      </tbody></table></div>` : '<p class="st-muted">Nothing yet.</p>'}
      <form data-adddoc class="cm-grid">
        <label class="st-f"><span class="st-lab">Document</span><select class="st-in" name="kind">${opts(Object.keys(DOCS), 'proposal', k => DOCS[k][0])}</select></label>
        <label class="st-f"><span class="st-lab">Number or reference</span><input class="st-in" name="number" required minlength="3" maxlength="40"></label>
        <label class="st-f"><span class="st-lab">Date</span><input class="st-in" type="date" name="issued_on"></label>
        <label class="st-f"><span class="st-lab">Amount (€, before VAT)</span><input class="st-in" name="amount"></label>
        <label class="st-f"><span class="st-lab">Link to the file</span><input class="st-in" name="link" maxlength="500"></label>
        <div class="st-actions"><button class="st-btn">Add</button></div></form></section>

    <section class="st-card"><h2 class="st-sub">Placements</h2>
      ${d.placements.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Work</th><th>From</th><th>Until</th><th>Status</th></tr></thead><tbody>
      ${d.placements.map(p => `<tr><td>${E(p.artwork_title)}${p.renewal_of ? ' <span class="st-muted">(renewal)</span>' : ''}</td><td>${E(when(p.start_on))}</td><td>${E(when(p.end_on))}</td>
        <td><form data-pl="${E(p.id)}" class="st-row"><select class="st-in" name="status">${opts(Object.keys(PL), p.status, k => PL[k])}</select><button class="st-btn st-btn--small">Update</button></form></td></tr>`).join('')}
      </tbody></table></div>` : '<p class="st-muted">No work placed yet.</p>'}
      ${chosen.length ? `<form data-addpl class="cm-grid"><label class="st-f"><span class="st-lab">Work</span><select class="st-in" name="selection_id">${chosen.map(s => `<option value="${E(s.id)}">${E(s.artwork_title)}</option>`).join('')}</select></label>
        <label class="st-f"><span class="st-lab">Start</span><input class="st-in" type="date" name="start_on" required></label>
        <label class="st-f"><span class="st-lab">Where</span><input class="st-in" name="location" maxlength="160"></label>
        ${d.placements.length ? `<label class="st-f"><span class="st-lab">Renews</span><select class="st-in" name="renewal_of"><option value="">—</option>${d.placements.map(p => `<option value="${E(p.id)}">${E(p.artwork_title)} (until ${E(when(p.end_on))})</option>`).join('')}</select></label>` : ''}
        <div class="st-actions"><button class="st-btn">Place for six months</button></div></form>` : '<p class="st-muted">A work can be placed once its artist has approved it and the business has chosen it.</p>'}</section>

    <section class="st-card"><h2 class="st-sub">Timeline</h2>
      <form data-note class="st-row"><input class="st-in" name="text" placeholder="Add a note" maxlength="2000" style="flex:1"><button class="st-btn st-btn--small">Add note</button></form>
      <ol class="cm-tl">${d.events.map(ev => `<li><span class="st-muted">${E(when(ev.at))} · ${E(ev.kind.replace('_', ' '))}</span><br>${E(ev.summary)}${ev.body ? `<details><summary>Show</summary><pre style="white-space:pre-wrap;font:inherit">${E(ev.body)}</pre></details>` : ''}</li>`).join('')}</ol></section>`;

    const go = (fn, msg) => async ev => { ev.preventDefault(); const f = ev.target; try { await fn(f, form(f)); say(msg); lead(id); } catch (e) { fail(f, e.message); } };
    app.querySelector('[data-lead]').onsubmit = go((f, v) => api('PATCH', '/api/admin/commercial/leads/' + id, v), 'Saved');
    app.querySelector('[data-note]').onsubmit = go((f, v) => api('POST', `/api/admin/commercial/leads/${id}/notes`, v), 'Note added');
    app.querySelector('[data-addsel]').onsubmit = go((f, v) => api('POST', `/api/admin/commercial/leads/${id}/selections`, v), 'Work proposed');
    app.querySelector('[data-adddoc]').onsubmit = go((f, v) => api('POST', `/api/admin/commercial/leads/${id}/documents`, v), 'Added');
    const pl = app.querySelector('[data-addpl]'); if (pl) pl.onsubmit = go((f, v) => api('POST', `/api/admin/commercial/leads/${id}/placements`, v), 'Placed');
    app.querySelectorAll('[data-sel]').forEach(f => f.onsubmit = go((f, v) => api('PATCH', '/api/admin/commercial/selections/' + f.dataset.sel, v), 'Updated'));
    app.querySelectorAll('[data-doc]').forEach(f => f.onsubmit = go((f, v) => api('PATCH', '/api/admin/commercial/documents/' + f.dataset.doc, v), 'Updated'));
    app.querySelectorAll('[data-pay]').forEach(f => f.onsubmit = go((f, v) => api('POST', `/api/admin/commercial/documents/${f.dataset.pay}/payments`, v), 'Payment recorded'));
    app.querySelectorAll('[data-pl]').forEach(f => f.onsubmit = go((f, v) => api('PATCH', '/api/admin/commercial/placements/' + f.dataset.pl, v), 'Updated'));
    try { cat = cat || await api('GET', '/api/admin/commercial/catalogue'); } catch { cat = { works: [] }; }
    const sel = app.querySelector('[data-cat]');
    if (sel) sel.innerHTML = '<option value="">Choose a work</option>' + cat.works.map(w => `<option value="${E(w.id)}">${E(w.artist)}: ${E(w.title)}${w.price_eur ? ` (€${w.price_eur.toLocaleString('en-IE')})` : ''}</option>`).join('');
  }

  const route = () => { const m = /^#\/lead\/(cl[0-9a-z]+)$/.exec(location.hash); m ? lead(m[1]) : list(); window.scrollTo(0, 0); };
  window.addEventListener('hashchange', route); route();
})();
