/* PlotArt Studio · founder review and publishing desk (Phase 2). */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const E = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const app = $('#app'), toast = $('#saved');
  const STATE = { draft: 'Setting up', in_review: 'Waiting for you', changes_requested: 'Changes requested', approved: 'Approved', publishing: 'Publishing', live: 'Live' };
  const when = t => t ? new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' }) : '';
  function say(m, bad) { toast.textContent = m; toast.classList.toggle('bad', !!bad); toast.classList.add('on'); clearTimeout(say.t); say.t = setTimeout(() => toast.classList.remove('on'), 2400); }
  async function api(method, path, body) {
    const r = await fetch(path, { method, headers: { 'X-Studio': '1', ...(body ? { 'Content-Type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined, credentials: 'same-origin' });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || j.ok === false) throw new Error(j.error || 'That didn’t work.');
    return j;
  }


  /* ---- PlotNua Idea Board (Phase 1, 1 Nov 2026): the founder's moderation of homeowner ideas */
  async function ideas() {
    let d = await api('GET', '/api/admin/ideas');
    const opt = (sel) => '<option value="">No area</option>' + d.areas.map(a => `<option${a === sel ? ' selected' : ''}>${E(a)}</option>`).join('');
    const county = i => i.county ? `Co. ${E(i.county)} · ${i.show_county ? 'the visitor chose to show it' : 'kept private by the visitor'}` : 'No county given';
    const item = (i, on) => `<li data-id="${i.id}" style="padding:18px 0;border-top:1px solid var(--line,rgba(242,235,224,.12))">
        <p class="st-work-s" style="margin:0 0 8px">${E(i.ref)} · received ${when(i.created_at)}${on ? ` · on the board since ${when(i.published_at)}${i.edited ? ' · <b>wording edited</b>' : ''}` : ''}</p>
        ${on ? '' : `<p class="st-work-s" style="margin:0 0 8px;${i.days_left <= d.warn_days ? 'color:#CF8566;font-weight:600' : ''}">${i.days_left <= d.warn_days ? '⚠ ' : ''}Deleted automatically ${i.days_left === 0 ? 'today' : `in ${i.days_left} day${i.days_left === 1 ? '' : 's'}`} (${when(i.expires_at)}) unless you decide on it.</p>`}
        <div class="st-f" style="margin:0"><label>Wording shown on the board · <span data-n></span></label>
        <textarea data-k="public_text" maxlength="160" style="min-height:76px">${E(i.public_text || i.text)}</textarea></div>
        ${i.public_text ? `<p class="st-muted" style="margin:6px 0 0">Original: “${E(i.text)}”</p>` : ''}
        <div class="st-row" style="gap:16px;flex-wrap:wrap;margin-top:10px;align-items:end">
          <div class="st-f" style="margin:0"><label>Area (correct it if needed)</label><select data-k="area">${opt(i.area)}</select></div>
          ${on ? `<div class="st-f" style="margin:0;flex:1;min-width:240px"><label>Now a Discovery (optional)</label><input type="text" data-k="became_discovery" placeholder="discovery-….html" value="${E(i.became_discovery || '')}"></div>` : ''}
          <div><p class="st-muted" style="margin:0 0 6px">${county(i)}</p>${i.show_county ? '<label class="st-muted"><input type="checkbox" data-k="hide_county"> Hide the county</label>' : ''}</div>
        </div>
        <div class="st-actions" style="margin-top:14px">${on
          ? '<button class="st-btn st-btn--solid st-btn--small" data-a="save">Save changes</button><button class="st-btn st-btn--small" data-a="remove">Remove from the board</button>'
          : '<button class="st-btn st-btn--solid st-btn--small" data-a="approve">Approve</button><button class="st-btn st-btn--small" data-a="not_approve">Not approved</button><button class="st-btn st-btn--small" data-a="delete">Delete now</button>'}</div></li>`;
    const match = i => !q || (i.ref || '').toUpperCase().includes(q.toUpperCase());
    let q = '';
    function draw() {
      const W = d.waiting.filter(match), A = d.approved.filter(match), D = d.decided.filter(match);
      app.innerHTML = `<h1 class="st-h1">Idea Board</h1>
        <p class="st-sub">Homeowner ideas for plotnua.ie/ideas.html. Nothing appears until you approve it; approved ideas reach plotnua.ie in about 2–3 minutes, and the Discovery Library card shows the latest three. Edit wording only to tidy it or remove identifying details, never to change its meaning.</p>
        ${d.expiring_soon ? `<div class="st-card" role="alert" style="border-color:#CF8566"><p style="margin:0"><b>⚠ ${d.expiring_soon} waiting idea${d.expiring_soon === 1 ? '' : 's'} will be deleted within ${d.warn_days} days</b> unless you approve or decline ${d.expiring_soon === 1 ? 'it' : 'them'}. Ideas waiting for review are kept for ${d.pending_days} days.</p></div>` : ''}
        <div class="st-f" style="max-width:360px"><label for="ibRef">Find by reference (for a removal request)</label><input id="ibRef" type="text" placeholder="PN-I-…" value="${E(q)}"></div>
        <section class="st-card"><h2>Waiting for you (${d.waiting.length})</h2><p class="st-muted" style="margin-top:0">Kept for ${d.pending_days} days, then deleted automatically.</p>${W.length ? `<ul style="list-style:none;padding:0;margin:0">${W.map(i => item(i, false)).join('')}</ul>` : `<p class="st-muted">${q ? 'No waiting idea with that reference.' : 'Nothing waiting.'}</p>`}</section>
        <section class="st-card"><h2>On the board (${d.approved.length})</h2>${A.length ? `<ul style="list-style:none;padding:0;margin:0">${A.map(i => item(i, true)).join('')}</ul>` : `<p class="st-muted">${q ? 'No idea on the board with that reference.' : 'The board is empty: plotnua.ie shows the empty-board invitation.'}</p>`}</section>
        <section class="st-card"><h2>Declined or removed</h2><p class="st-muted">Deleted automatically ${d.purge_days} days after your decision, or now with “Delete now”.</p>
          ${D.length ? `<ul class="st-works">${D.map(i => `<li class="st-work" data-id="${i.id}" style="grid-template-columns:1fr auto;align-items:center"><p class="st-work-s" style="margin:0">${E(i.ref)} · ${i.status === 'removed' ? 'removed ' + when(i.removed_at) : 'not approved ' + when(i.decided_at)} · “${E(i.public_text || i.text)}”</p><button class="st-btn st-btn--small" data-a="delete">Delete now</button></li>`).join('')}</ul>` : ''}</section>`;
      const ref = app.querySelector('#ibRef');
      ref.addEventListener('input', () => { q = ref.value.trim(); draw(); const r2 = app.querySelector('#ibRef'); r2.focus(); r2.setSelectionRange(r2.value.length, r2.value.length); });
      app.querySelectorAll('[data-id]').forEach(li => {
        const ta = li.querySelector('textarea'), n = li.querySelector('[data-n]');
        if (ta) { const count = () => { n.textContent = `${ta.value.length}/160`; }; count(); ta.addEventListener('input', count); }
        li.querySelectorAll('[data-a]').forEach(btn => btn.addEventListener('click', async () => {
          const body = { action: btn.dataset.a };
          if (['approve', 'save'].includes(btn.dataset.a)) {
            body.public_text = ta.value; body.area = li.querySelector('[data-k="area"]').value || null;
            const disc = li.querySelector('[data-k="became_discovery"]'); if (disc) body.became_discovery = disc.value || null;
            const hide = li.querySelector('[data-k="hide_county"]'); if (hide && hide.checked) body.hide_county = true;
          }
          if (btn.dataset.a === 'remove' && !confirm('Remove this idea from the public board?')) return;
          if (btn.dataset.a === 'delete' && !confirm('Delete this idea permanently now? This cannot be undone.')) return;
          try {
            d = await api('POST', `/api/admin/ideas/${li.dataset.id}`, body);
            const when = d.publish === 'requested' ? 'plotnua.ie updates in about 2–3 minutes' : d.publish === 'failed' ? 'publishing could not be started now: it will happen at the next scheduled run' : 'it will appear on plotnua.ie at the next scheduled publishing run';
            say({ approve: 'Approved: ' + when, save: 'Saved: ' + when, remove: 'Removed from the board: ' + when, not_approve: 'Not approved', delete: 'Deleted' }[btn.dataset.a], d.publish === 'failed');
            draw(); }
          catch (e) { say(e.message, true); }
        }));
      });
    }
    draw();
  }

  /* ---- The Borrowed Garden noticeboard (MVP, 4 Nov 2026): the founder's moderation of listings */
  async function garden() {
    let d = await api('GET', '/api/admin/garden');
    const kind = l => l.kind === 'have' ? '<span style="color:#CFE0B4;font-weight:700">I HAVE SPACE</span>' : '<span style="color:#E8CF9E;font-weight:700">I WANT SPACE</span>';
    const meta = l => `${E(d.space_types[l.space_type] || l.space_type)} · ${E(d.availability[l.availability] || l.availability)} · Co. ${E(l.county)}`;
    const item = (l, on) => `<li data-id="${l.id}" style="padding:18px 0;border-top:1px solid var(--line,rgba(242,235,224,.12))">
        <p class="st-work-s" style="margin:0 0 8px">${kind(l)} · ${E(l.ref)} · received ${when(l.created_at)}${on ? ` · on the noticeboard since ${when(l.published_at)} · expires ${when(l.expires_at)}${l.edited ? ' · <b>edited</b>' : ''}` : ''}</p>
        <p class="st-muted" style="margin:0 0 8px">${meta(l)} · private contact: ${E(l.contact_email)} (never published)</p>
        <div class="st-row" style="gap:16px;flex-wrap:wrap;align-items:end">
          <div class="st-f" style="margin:0;min-width:220px"><label>General area shown</label><input type="text" data-k="area" maxlength="40" value="${E(l.area)}"></div></div>
        <div class="st-f" style="margin:10px 0 0"><label>Wording shown on the noticeboard · <span data-n></span></label>
        <textarea data-k="public_text" maxlength="400" style="min-height:96px">${E(l.public_text || l.description)}</textarea></div>
        ${l.public_text ? `<p class="st-muted" style="margin:6px 0 0">Original: “${E(l.description)}”</p>` : ''}
        <div class="st-actions" style="margin-top:14px">${on
          ? '<button class="st-btn st-btn--solid st-btn--small" data-a="save">Save changes</button><button class="st-btn st-btn--small" data-a="expire">Expire now</button><button class="st-btn st-btn--small" data-a="remove">Remove from the noticeboard</button>'
          : '<button class="st-btn st-btn--solid st-btn--small" data-a="approve">Approve</button><button class="st-btn st-btn--small" data-a="reject">Reject</button><button class="st-btn st-btn--small" data-a="delete">Delete now</button>'}</div></li>`;
    let q = '';
    const match = l => !q || (l.ref || '').toUpperCase().includes(q.toUpperCase()) || (l.contact_email || '').toLowerCase().includes(q.toLowerCase());
    function draw() {
      const W = d.waiting.filter(match), A = d.approved.filter(match), C = d.closed.filter(match);
      app.innerHTML = `<h1 class="st-h1">The Borrowed Garden noticeboard</h1>
        <p class="st-sub">Listings for plotnua.ie/borrowed-garden-board.html. Nothing appears until you approve it. An approved listing stays up for ${d.listing_days} days, then expires. Edit wording only to tidy it or take out identifying details (names, addresses, contact details), never to change its meaning.</p>
        <div class="st-f" style="max-width:360px"><label for="gbRef">Find by reference or e-mail (for a removal request)</label><input id="gbRef" type="text" placeholder="PN-G-…" value="${E(q)}"></div>
        <section class="st-card"><h2>Waiting for you (${d.waiting.length})</h2><p class="st-muted" style="margin-top:0">Kept for ${d.pending_days} days, then deleted automatically.</p>${W.length ? `<ul style="list-style:none;padding:0;margin:0">${W.map(l => item(l, false)).join('')}</ul>` : `<p class="st-muted">Nothing waiting.</p>`}</section>
        <section class="st-card"><h2>On the noticeboard (${d.approved.length})</h2>${A.length ? `<ul style="list-style:none;padding:0;margin:0">${A.map(l => item(l, true)).join('')}</ul>` : `<p class="st-muted">The noticeboard is empty.</p>`}</section>
        <section class="st-card"><h2>Rejected, removed or expired</h2><p class="st-muted">Deleted automatically ${d.purge_days} days later, or now with “Delete now”.</p>
          ${C.length ? `<ul class="st-works">${C.map(l => `<li class="st-work" data-id="${l.id}" style="grid-template-columns:1fr auto;align-items:center"><p class="st-work-s" style="margin:0">${E(l.ref)} · ${E(l.status)} ${when(l.removed_at || l.decided_at)} · ${E(l.area)}, Co. ${E(l.county)}</p><button class="st-btn st-btn--small" data-a="delete">Delete now</button></li>`).join('')}</ul>` : ''}</section>`;
      const ref = app.querySelector('#gbRef');
      ref.addEventListener('input', () => { q = ref.value.trim(); draw(); const r2 = app.querySelector('#gbRef'); r2.focus(); r2.setSelectionRange(r2.value.length, r2.value.length); });
      app.querySelectorAll('[data-id]').forEach(li => {
        const ta = li.querySelector('textarea'), n = li.querySelector('[data-n]');
        if (ta) { const count = () => { n.textContent = `${ta.value.length}/400`; }; count(); ta.addEventListener('input', count); }
        li.querySelectorAll('[data-a]').forEach(btn => btn.addEventListener('click', async () => {
          const body = { action: btn.dataset.a };
          if (['approve', 'save'].includes(btn.dataset.a)) { body.public_text = ta.value; body.area = li.querySelector('[data-k="area"]').value; }
          if (btn.dataset.a === 'remove' && !confirm('Remove this listing from the public noticeboard?')) return;
          if (btn.dataset.a === 'delete' && !confirm('Delete this listing permanently now? This cannot be undone.')) return;
          try {
            d = await api('POST', `/api/admin/garden/${li.dataset.id}`, body);
            const when = d.publish === 'requested' ? 'plotnua.ie updates in a few minutes' : d.publish === 'failed' ? 'publishing could not be started now: it will happen at the next scheduled run' : 'it updates at the next scheduled publishing run';
            say({ approve: 'Approved: ' + when, save: 'Saved: ' + when, remove: 'Removed: ' + when, expire: 'Expired: ' + when, reject: 'Rejected', delete: 'Deleted' }[btn.dataset.a], d.publish === 'failed');
            draw(); }
          catch (e) { say(e.message, true); }
        }));
      });
    }
    draw();
  }

  async function home() {
    const o = await api('GET', '/api/admin/overview');
    const ready = o.queue.filter(q => q.status === 'awaiting_founder');
    const live = o.artists.filter(a => a.state === 'live').length;
    app.innerHTML = `
      <h1 class="st-h1">Review desk</h1><p class="st-sub">Everything that needs you, in one place.</p>
      <div class="st-kpis">
        <div class="st-kpi"><b>${o.submissions.length}</b><span>to review</span></div>
        <div class="st-kpi"><b>${ready.length}</b><span>ready to publish</span></div>
        <div class="st-kpi"><b>${live}</b><span>galleries live</span></div>
        <div class="st-kpi"><b>${o.artists.filter(a => a.founding).length}/25</b><span>Founding Artists in Studio</span></div>
      </div>
      <section class="st-card"><h2>To review</h2>
        ${o.submissions.length ? `<ul class="st-works">${o.submissions.map(s => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto"><div>
          <p class="st-work-t">${E(s.display_name)}</p><p class="st-work-s"><span class="st-tier ${s.tier}">${s.tier === 'full' ? 'Review' : 'Quick check'}</span>Submitted ${when(s.created_at)}</p>
          ${s.note ? `<p class="st-muted" style="margin:0">“${E(s.note)}”</p>` : ''}</div>
          <div class="st-row"><a class="st-btn st-btn--solid st-btn--small" href="#/review/${s.id}">Open</a></div></li>`).join('')}</ul>` : '<p class="st-muted">Nothing waiting. 🎨</p>'}
      </section>
      <section class="st-card"><h2>Ready to publish</h2>
        <p class="st-muted">Publishing sends approved gallery content to plotnua.ie through the content-only pipeline. Nothing else on the website can change this way.${o.instant_autopublish ? ' Availability and removals publish automatically.' : ' Availability and removal updates wait here until automatic publishing is switched on.'}</p>
        ${o.queue.length ? `<ul class="st-works">${o.queue.map(q => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto"><div><p class="st-work-t">${E(q.display_name)}</p>
          <p class="st-work-s" style="margin:0">Version ${q.version} · ${q.kind === 'instant' ? 'availability, removal or order' : q.kind === 'remove' ? 'remove the gallery' : 'approved changes'} · ${q.status === 'awaiting_founder' ? 'waiting for you' : E(q.status)}</p></div>
          ${q.status === 'awaiting_founder' ? `<div class="st-row"><a class="st-btn st-btn--small" href="/admin/preview/v-${q.artist_id}-${q.version}/index.html" target="_blank" rel="noopener">Preview</a><button class="st-btn st-btn--solid st-btn--small" data-pub="${q.id}">Publish</button></div>` : '<span></span>'}</li>`).join('')}</ul>` : '<p class="st-muted">Nothing waiting.</p>'}
      </section>
      ${o.flags.length ? `<section class="st-card"><h2 class="st-flag">Rights check</h2><p class="st-muted">The same photograph appears in more than one artist’s Studio. Check before approving.</p>
        <ul class="st-list">${o.flags.map(f => `<li>${E(f.display_name)} · image ${E(f.id)} · fingerprint ${E(f.sha256.slice(0, 12))}…</li>`).join('')}</ul></section>` : ''}
      <section class="st-card"><h2>Enquiries</h2><p class="st-muted">Buyer enquiries go straight to the artist (Reply-To the buyer). This is the record of founding-period enquiries.</p>
        <div id="enq"><p class="st-muted">Loading…</p></div></section>
      <section class="st-card"><h2>Artists</h2><div class="st-scroll"><table class="st-table"><thead><tr><th>Artist</th><th>Status</th><th>Works</th><th>To do</th><th></th></tr></thead><tbody>
        ${o.artists.map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${a.founding ? ' <span class="pa-gcard-badge" style="display:inline-block">Founding</span>' : ''}<br><span class="st-muted">${E(a.email)}${a.application_ref ? ' · ' + E(a.application_ref) : ''}</span></td>
          <td>${a.account_status === 'suspended' ? '<span class="st-flag">Suspended</span>' : E(STATE[a.state])}${a.account_status === 'invited' ? '<br><span class="st-muted">Not signed in yet</span>' : ''}</td>
          <td>${a.works}</td><td>${a.problems ? `${a.problems} item${a.problems > 1 ? 's' : ''}` : '✓'}</td>
          <td class="st-row">${a.account_status === 'suspended' ? `<button class="st-btn st-btn--small" data-act="reactivate" data-id="${a.id}">Reactivate</button>` : `<button class="st-btn st-btn--small" data-act="suspend" data-id="${a.id}">Suspend</button>`}
          ${a.live_version ? `<button class="st-btn st-btn--small st-btn--danger" data-act="unpublish" data-id="${a.id}">Unpublish</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="5" class="st-muted">No artists yet.</td></tr>'}
      </tbody></table></div></section>
      <section class="st-card"><h2>Invite a selected artist</h2><p class="st-muted">After they accept the Founding Artist Agreement (terms_accepted_at in Airtable), copy their name, email and reference from the application. The invitation email goes automatically when email is switched on.</p>
        <div class="st-two"><div>
        <div class="st-f"><label for="i-name">Artist name</label><input id="i-name" type="text"></div>
        <div class="st-f"><label for="i-email">Email they applied with</label><input id="i-email" type="email"></div></div><div>
        <div class="st-f"><label for="i-ref">Application reference</label><input id="i-ref" type="text" placeholder="F25-YYMMDD-XXXXXX"></div>
        <label class="st-check" style="margin:4px 0 14px"><input id="i-f" type="checkbox" checked style="accent-color:var(--terra);width:20px;height:20px"> Founding Artist</label>
        <button class="st-btn st-btn--solid" id="inv">Create Studio account</button><p class="st-err" id="ierr"></p></div></div></section>
      <section class="st-card"><h2>System check</h2><p class="st-muted">Writes, reads back and removes a test record in the database and a test file in image storage.</p>
        <button class="st-btn" id="sys">Run system check</button><ul class="st-list" id="sysout"></ul></section>`;
    $('#sys').addEventListener('click', async () => { const r = await api('POST', '/api/admin/selftest');
      $('#sysout').innerHTML = [['Database', r.database], ['Image storage', r.image_storage], ['Automatic updates', r.publishing], ['Email', r.email]].map(([k, v]) => `<li><b style="color:var(--ivory)">${k}:</b> ${E(v)}</li>`).join('') + `<li><b style="color:var(--ivory)">${r.passed ? '✓ Passed' : '✗ Failed'}</b></li>`; });
    api('GET', '/api/admin/enquiries').then(r => { $('#enq').innerHTML = r.items.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Reference</th><th>Date</th><th>Artist</th><th>Artwork</th><th>Delivered</th></tr></thead><tbody>${r.items.slice(0, 30).map(e => `<tr><td>${E(e.reference)}</td><td>${when(e.created_at)}</td><td>${E(e.display_name)}</td><td>${E(e.artwork_title || 'General')}</td><td>${e.status === 'sent' ? '✓ emailed' : 'in Studio'}</td></tr>`).join('')}</tbody></table></div>` : '<p class="st-muted">None yet.</p>'; });
    app.querySelectorAll('[data-pub]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = 'Publish to plotnua.ie?'; return; }
      await api('POST', `/api/admin/queue/${b.dataset.pub}/publish`); say('Sent to the publishing pipeline'); home();
    }));
    app.querySelectorAll('[data-act]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = b.textContent + '?'; return; }
      await api('POST', `/api/admin/artists/${b.dataset.id}/${b.dataset.act}`); say('Done'); home();
    }));
    $('#inv').addEventListener('click', async () => {
      try {
        const r = await api('POST', '/api/admin/artists', { display_name: $('#i-name').value, email: $('#i-email').value, application_ref: $('#i-ref').value || null, founding: $('#i-f').checked });
        say(r.invitation_sent ? 'Account created · invitation emailed' : 'Account created · email is off, so send the invitation by hand'); home();
      } catch (e) { $('#ierr').textContent = e.message; }
    });
  }

  async function review(id) {
    const r = await api('GET', `/api/admin/submissions/${id}`), s = r.submission;
    const gen = r.works.filter(w => w.ai_involvement === 'generated');
    const tiers = { full: 'Review', light: 'Quick check', instant: 'Live' };
    app.innerHTML = `
      <p><a href="#/" style="color:var(--stone);text-decoration:none">← Review desk</a></p>
      <h1 class="st-h1">${E(r.artist.display_name)}</h1>
      <p class="st-sub"><span class="st-tier ${s.tier}">${tiers[s.tier]}</span>Submitted ${when(s.created_at)} · ${s.status === 'pending' ? 'waiting for you' : E(s.status)}${r.artist.founding ? ' · Founding Artist' : ''} · licence ${E(r.artist.licence_version || 'not accepted')}</p>
      ${s.note ? `<p class="st-msg">${E(s.note)}</p>` : ''}
      <div class="st-two"><div>
      <section class="st-card"><h2>What changes</h2><ul class="st-list">${s.changes.map(c => `<li><span><span class="st-tier ${c.tier}">${tiers[c.tier]}</span>${E(c.what)}${c.to !== undefined && typeof c.to !== 'object' ? ` <span class="st-muted">${E(c.from ?? '—')} → ${E(c.to ?? '—')}</span>` : ''}</span></li>`).join('')}</ul>
        <div class="st-actions"><a class="st-btn st-btn--solid" href="/admin/preview/${s.id}/index.html" target="_blank" rel="noopener">Open the gallery preview</a></div></section>
      <section class="st-card"><h2>Photographs</h2><div class="st-imgs">${r.images.map(i => `<div class="st-img"><div style="background-image:url(/admin/preview/${s.id}/img/${i.id})"></div>
        <p>${i.width} × ${i.height} px · ${(i.bytes / 1048576).toFixed(1)} MB${i.checks.warns.length ? `<br>⚠ ${E(i.checks.warns.map(w => /3,000 px/.test(w) ? 'under 3,000 px' : /long format/.test(w) ? 'very long format' : w).join(' · '))}` : ''}${i.checks.flags?.length ? '<br><span class="st-flag">Same photo is in another artist’s Studio</span>' : ''}</p></div>`).join('')}</div></section>
      </div><div>
      ${gen.length ? `<section class="st-card"><h2>AI eligibility</h2><p class="st-muted">These works are declared as entirely prompt-generated. Decide each one.</p>
        ${gen.map(w => `<div class="st-f"><span class="st-lab">${E(w.title)}</span><small>${E(w.ai_note)}</small><div class="st-radio">${[['approved', 'Eligible'], ['declined', 'Not eligible']].map(([k, v]) => `<label><input type="radio" name="ai-${w.id}" value="${k}"> ${v}</label>`).join('')}</div></div>`).join('')}</section>` : ''}
      <section class="st-card"><h2>Your decision</h2>
        <div class="st-f"><label for="msg">Message to the artist</label><textarea id="msg" placeholder="Required when you ask for changes: say exactly what to change."></textarea></div>
        <div class="st-actions"><button class="st-btn st-btn--solid" data-d="approve">Approve</button><button class="st-btn" data-d="changes">Request changes</button><button class="st-btn st-btn--danger" data-d="decline">Decline</button></div>
        <p class="st-muted">Approving adds this version to “Ready to publish”. You publish it from the review desk.</p><p class="st-err" id="derr"></p></section></div></div>`;
    app.querySelectorAll('[data-d]').forEach(b => b.addEventListener('click', async () => {
      const ai = {}; gen.forEach(w => { const c = app.querySelector(`[name="ai-${w.id}"]:checked`); if (c) ai[w.id] = c.value; });
      try { await api('POST', `/api/admin/submissions/${id}/decision`, { decision: b.dataset.d, message: $('#msg').value || null, ai_decisions: ai }); say('Decision saved'); location.hash = '#/'; }
      catch (e) { $('#derr').textContent = e.message; }
    }));
  }

  /* ---- Founding 25 applications with artwork images (private; founder only). Decisions stay in Airtable. */
  const MED = { painting: 'Painting', drawing: 'Drawing', works_on_paper: 'Works on paper', printmaking: 'Printmaking', photography: 'Photography', sculpture: 'Sculpture',
    ceramics_craft: 'Ceramics and craft', textiles: 'Textiles', mixed_media: 'Mixed media', digital: 'Digital', other: 'Other' };
  const county = c => c ? c.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ') : '';
  const ext = (u, label) => u ? `<a class="st-btn st-btn--small" href="${E(u)}" target="_blank" rel="noopener noreferrer nofollow">${E(label)} ↗</a>` : '';
  async function apps() {
    const r = await api('GET', '/api/admin/applications');
    app.innerHTML = `<h1 class="st-h1">Applications</h1><p class="st-sub">Founding 25 applications that came with images of the artist's work. Private: only you can see them. Shortlist and select in Airtable.</p>
      ${!r.connected ? '<section class="st-card"><p class="st-muted">Application image storage isn’t connected yet.</p></section>' : r.items.length ? `<ul class="st-works">${r.items.map(a => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto">
        <div><p class="st-work-t"><a href="/admin/applications/${E(a.ref)}" style="color:inherit">${E(a.artist_name)}</a></p>
        <p class="st-work-s">${E(a.ref)} · ${E(MED[a.medium] || a.medium)}${a.region ? ' · ' + E(county(a.region)) : ''} · ${when(a.submitted_at)}</p>
        <div class="st-appthumbs">${a.images.map(i => `<img src="${E(i.src)}" alt="" loading="lazy">`).join('')}</div></div>
        <div class="st-row"><a class="st-btn st-btn--solid st-btn--small" href="/admin/applications/${E(a.ref)}">Open</a></div></li>`).join('')}</ul>` : '<section class="st-card"><p class="st-muted">No applications with images yet.</p></section>'}`;
  }
  async function appView(ref) {
    const a = (await api('GET', '/api/admin/applications/' + ref)).application;
    app.innerHTML = `<p><a href="/admin/applications" style="color:var(--stone);text-decoration:none">← Applications</a></p>
      <h1 class="st-h1">${E(a.artist_name)}</h1><p class="st-sub">${E(a.ref)} · ${E(MED[a.medium] || a.medium)}${a.region ? ' · ' + E(county(a.region)) : ''} · applied ${when(a.submitted_at)}</p>
      <div class="st-appgrid">${a.images.map((i, n) => `<a href="${E(i.src)}" target="_blank" rel="noopener"><img src="${E(i.src)}" alt="Artwork ${n + 1} of ${a.images.length} from ${E(a.artist_name)}"${i.w ? ` width="${i.w}" height="${i.h}"` : ''}></a>`).join('')}</div>
      <div class="st-two" style="margin-top:18px"><section class="st-card"><h2>Artist statement</h2><p style="white-space:pre-line">${E(a.bio)}</p>
        ${a.additional_info ? `<h2 style="margin-top:18px">Anything else</h2><p style="white-space:pre-line">${E(a.additional_info)}</p>` : ''}</section>
      <section class="st-card"><h2>Links</h2><div class="st-row" style="flex-wrap:wrap;gap:8px">${ext(a.portfolio, 'Portfolio')}${ext(a.website, 'Website')}${a.social_link ? (a.social_link.startsWith('@') ? ext('https://www.instagram.com/' + a.social_link.slice(1) + '/', a.social_link) : ext(a.social_link, 'Profile')) : ''}${!a.portfolio && !a.website && !a.social_link ? '<p class="st-muted" style="margin:0">No links: the images are the portfolio.</p>' : ''}</div>
        <h2 style="margin-top:18px">Decision</h2><p class="st-muted">Shortlist, select or decline in Airtable, where the application's status and emails are recorded.</p>
        ${a.airtable ? `<a class="st-btn st-btn--solid" href="${E(a.airtable)}" target="_blank" rel="noopener noreferrer">Open in Airtable ↗</a>` : '<p class="st-muted">Find it in Airtable by its reference.</p>'}
        <h2 style="margin-top:22px">When the application is closed</h2><p class="st-muted">Erase these images when the application is deleted under the retention rules.</p>
        <button class="st-btn st-btn--small st-btn--danger" id="erase">Erase these images</button><p class="st-err" id="eerr"></p></section></div>`;
    $('#erase').addEventListener('click', async e => {
      const b = e.currentTarget;
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = 'Erase permanently?'; return; }
      try { await api('POST', `/api/admin/applications/${ref}/erase`); say('Images erased'); location.href = '/admin/applications'; } catch (x) { $('#eerr').textContent = x.message; }
    });
  }


  /* ---- Gallery order (founder only, 31 Oct 2026). The 25 positions of the public Virtual Gallery. Display order only:
     a Founding 25 number is set separately below and never changes when cards move. */
  async function order() {
    let d = await api('GET', '/api/admin/gallery-order');
    let pos = d.positions.map(p => ({ ...p })), dirty = false;
    const two = n => String(n).padStart(2, '0');
    const name = id => (d.artists.find(a => a.id === id) || {}).display_name || 'Artist';
    const swap = (i, j) => { if (j < 0 || j >= pos.length) return; const a = pos[i], b = pos[j];
      pos[i] = { ...b, position: a.position }; pos[j] = { ...a, position: b.position }; dirty = true; draw(j); };
    function row(p, i) {
      const body = p.state === 'artist'
        ? `<p class="st-work-t">${E(p.display_name || name(p.artist_id))}</p><p class="st-work-s" style="margin:0">${p.live ? 'Live on plotnua.ie' : 'Not published yet · shows as ' + two(p.position) + ' until published'}${p.founding_number ? ' · Founding No. ' + p.founding_number : ''}</p>`
        : p.state === 'reserved'
        ? `<p class="st-work-t">Reserved</p><label class="st-go-note"><span class="st-muted">Private note (never shown publicly)</span><input type="text" maxlength="140" data-note="${i}" value="${E(p.note || '')}" placeholder="Who it is held for"></label>`
        : `<p class="st-work-t st-muted" style="color:var(--stone)">Open</p><label class="st-go-note"><span class="st-muted">Place an artist</span><select data-assign="${i}"><option value="">Choose…</option>${d.artists.filter(a => !pos.some(q => q.artist_id === a.id)).map(a => `<option value="${a.id}">${E(a.display_name)}${a.live ? ' · live' : ''}${a.founding ? '' : ' · not Founding'}</option>`).join('')}</select></label>`;
      const acts = p.state === 'artist' ? `<button class="st-btn st-btn--small" data-clear="${i}">Remove from position</button>`
        : p.state === 'reserved' ? `<button class="st-btn st-btn--small" data-clear="${i}">Release</button>`
        : `<button class="st-btn st-btn--small" data-reserve="${i}">Reserve</button>`;
      return `<li class="st-go-row is-${p.state}" draggable="true" data-i="${i}" aria-label="Position ${two(p.position)}">
        <span class="st-go-grip" aria-hidden="true">⠿</span><span class="st-go-n">${two(p.position)}</span>
        <div class="st-go-body">${body}</div>
        <div class="st-go-acts"><button class="st-btn st-btn--small st-go-mv" data-up="${i}" aria-label="Move position ${two(p.position)} up"${i === 0 ? ' disabled' : ''}>↑</button><button class="st-btn st-btn--small st-go-mv" data-down="${i}" aria-label="Move position ${two(p.position)} down"${i === pos.length - 1 ? ' disabled' : ''}>↓</button>${acts}</div></li>`;
    }
    function draw(focus) {
      app.innerHTML = `<h1 class="st-h1">Gallery order</h1>
        <p class="st-sub">The 25 positions of the public Virtual Gallery, in order. Drag a card onto another to swap them, or use ↑ ↓. Only you can change this. Saved changes reach plotnua.ie on the next publishing run (within about 10 minutes).</p>
        <div class="st-go-bar"><span id="go-state" class="st-muted">${dirty ? 'Unsaved changes' : 'Saved'}</span><button class="st-btn st-btn--solid" id="go-save"${dirty ? '' : ' disabled'}>Save order</button></div>
        <ol class="st-go" id="go">${pos.map(row).join('')}</ol>
        <section class="st-card" style="margin-top:22px"><h2>Founding 25 numbers</h2>
          <p class="st-muted">Each Founding Artist's permanent number. It is separate from the gallery order above: moving a card never changes it. Numbers are set only here, by you, and are never assigned automatically.</p>
          <div class="st-scroll"><table class="st-table"><thead><tr><th>Artist</th><th>Founding No.</th></tr></thead><tbody>
          ${d.artists.filter(a => a.founding).map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${a.live ? ' <span class="st-muted">· live</span>' : ''}</td><td><select data-fn="${a.id}" aria-label="Founding 25 number for ${E(a.display_name)}"><option value="">—</option>${Array.from({ length: 25 }, (_, k) => k + 1).map(n => { const h = d.artists.find(x => x.founding_number === n && x.id !== a.id); return `<option value="${n}"${a.founding_number === n ? ' selected' : ''}${h ? ' disabled' : ''}>${n}${h ? ' · ' + E(h.display_name) : ''}</option>`; }).join('')}</select></td></tr>`).join('') || '<tr><td colspan="2" class="st-muted">No Founding Artists yet.</td></tr>'}
          </tbody></table></div><p class="st-err" id="fnerr"></p></section>`;
      wire();
      if (focus != null) { const b = app.querySelector(`[data-i="${focus}"] .st-go-mv:not([disabled])`); if (b) b.focus(); }
    }
    function wire() {
      const L = $('#go');
      L.querySelectorAll('[data-up]').forEach(b => b.addEventListener('click', () => swap(+b.dataset.up, +b.dataset.up - 1)));
      L.querySelectorAll('[data-down]').forEach(b => b.addEventListener('click', () => swap(+b.dataset.down, +b.dataset.down + 1)));
      L.querySelectorAll('[data-reserve]').forEach(b => b.addEventListener('click', () => { pos[+b.dataset.reserve] = { position: pos[+b.dataset.reserve].position, state: 'reserved', note: '' }; dirty = true; draw(); }));
      L.querySelectorAll('[data-clear]').forEach(b => b.addEventListener('click', () => { pos[+b.dataset.clear] = { position: pos[+b.dataset.clear].position, state: 'open' }; dirty = true; draw(); }));
      L.querySelectorAll('[data-note]').forEach(f => f.addEventListener('input', () => { pos[+f.dataset.note].note = f.value; if (!dirty) { dirty = true; $('#go-state').textContent = 'Unsaved changes'; $('#go-save').disabled = false; } }));
      L.querySelectorAll('[data-assign]').forEach(f => f.addEventListener('change', () => { if (!f.value) return; const a = d.artists.find(x => x.id === f.value);
        pos[+f.dataset.assign] = { position: pos[+f.dataset.assign].position, state: 'artist', artist_id: a.id, display_name: a.display_name, live: a.live, founding_number: a.founding_number }; dirty = true; draw(); }));
      let from = null;
      L.querySelectorAll('.st-go-row').forEach(r => {
        r.addEventListener('dragstart', e => { from = +r.dataset.i; r.classList.add('is-drag'); e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(from)); });
        r.addEventListener('dragend', () => r.classList.remove('is-drag'));
        r.addEventListener('dragover', e => { e.preventDefault(); r.classList.add('is-over'); });
        r.addEventListener('dragleave', () => r.classList.remove('is-over'));
        r.addEventListener('drop', e => { e.preventDefault(); r.classList.remove('is-over'); const to = +r.dataset.i; if (from !== null && from !== to) swap(from, to); from = null; });
      });
      $('#go-save').addEventListener('click', async () => {
        const b = $('#go-save'); b.disabled = true;
        try { d = await api('PUT', '/api/admin/gallery-order', { positions: pos.filter(p => p.state !== 'open').map(p => ({ position: p.position, state: p.state, artist_id: p.artist_id, note: p.note })) });
          pos = d.positions.map(p => ({ ...p })); dirty = false; draw(); say('Saved · plotnua.ie updates on the next publishing run'); }
        catch (e) { b.disabled = false; say(e.message, true); }
      });
      app.querySelectorAll('[data-fn]').forEach(f => f.addEventListener('change', async () => {
        try { await api('PUT', `/api/admin/artists/${f.dataset.fn}/founding-number`, { founding_number: f.value ? Number(f.value) : null }); say('Founding number saved');
          d = await api('GET', '/api/admin/gallery-order'); if (!dirty) pos = d.positions.map(p => ({ ...p })); draw(); }
        catch (e) { $('#fnerr').textContent = e.message; }
      }));
    }
    addEventListener('beforeunload', e => { if (dirty && location.pathname.startsWith('/admin/gallery')) { e.preventDefault(); e.returnValue = ''; } });
    draw();
  }

  async function render() {
    const h = location.hash || '#/', path = location.pathname.replace(/\/$/, '');
    const am = path.match(/^\/admin\/applications\/(F25-\d{6}-[0-9A-F]{6})$/);
    document.querySelectorAll('.st-tabs a').forEach(a => a.toggleAttribute('aria-current', a.dataset.t === (path.startsWith('/admin/applications') ? 'apps' : path === '/admin/gallery' ? 'order' : path === '/admin/ideas' ? 'ideas' : path === '/admin/garden' ? 'garden' : 'desk')));
    document.querySelectorAll('.st-tabs a[aria-current]').forEach(a => a.setAttribute('aria-current', 'page'));
    try { if (am) await appView(am[1]); else if (path === '/admin/gallery') await order(); else if (path === '/admin/ideas') await ideas(); else if (path === '/admin/garden') await garden(); else if (path === '/admin/applications') await apps(); else if (h.startsWith('#/review/')) await review(h.slice(9)); else await home(); window.scrollTo(0, 0); }
    catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();
