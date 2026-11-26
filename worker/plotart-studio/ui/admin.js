/* PlotArt Studio · founder review and publishing desk (Phase 2). */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const E = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const app = $('#app'), toast = $('#saved');
  // what the founder needs to know at a glance (18 Nov 2026): a draft with nothing outstanding is "Ready to submit", not
  // "Setting up"; a pending submission reads as submitted
  const STATE = { draft: 'Setting up', ready: 'Ready to submit (not submitted yet)', in_review: 'Submitted for review', changes_requested: 'Changes requested', approved: 'Approved', publishing: 'Approved: publishing', live: 'Published' };
  const stateOf = a => a.state === 'draft' && !a.problems && a.works ? 'ready' : a.state;
  const when = t => t ? new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' }) : '';
  function say(m, bad) { toast.textContent = m; toast.classList.toggle('bad', !!bad); toast.classList.add('on'); clearTimeout(say.t); say.t = setTimeout(() => toast.classList.remove('on'), 2400); }
  async function api(method, path, body) {
    const r = await fetch(path, { method, headers: { 'X-Studio': '1', ...(body ? { 'Content-Type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined, credentials: 'same-origin' });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || j.ok === false) { const e = new Error(j.error || 'That didn’t work.'); e.data = j; throw e; }
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

  // the first line of a publishing failure that names what failed (the publisher puts FAIL/REFUSED lines first)
  const failLine = d => { const l = String(d).split('\n').map(x => x.trim()).filter(Boolean);
    const f = l.find(x => /^(FAIL|REFUSED|ERROR)\b/.test(x)) || l[0] || ''; return 'Last attempt: ' + (f.length > 220 ? f.slice(0, 220) + '…' : f); };

  async function home() {
    const o = await api('GET', '/api/admin/overview');
    const ready = o.queue.filter(q => q.status === 'awaiting_founder');
    const live = o.artists.filter(a => a.gallery_live).length;  // galleries on plotnua.ie, even with an update queued
    app.innerHTML = `
      <h1 class="st-h1" style="margin-bottom:1.75rem">Review desk</h1>
      <div class="st-kpis">
        <div class="st-kpi"><b>${o.submissions.length}</b><span>to review</span></div>
        <div class="st-kpi"><b>${ready.length}</b><span>ready to publish</span></div>
        <div class="st-kpi"><b>${live}</b><span>galleries live</span></div>
        <div class="st-kpi"><b>${o.artists.filter(a => a.founding).length}/25</b><span>Founding Artists in Studio</span></div>
      </div>
      <section class="st-card"><h2>To review</h2>
        ${o.submissions.length ? `<ul class="st-works">${o.submissions.map(s => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto"><div>
          <p class="st-work-t">${E(s.display_name)}${TB(s.artist_id)}</p><p class="st-work-s"><span class="st-tier ${s.tier}">${s.tier === 'full' ? 'Review' : 'Quick check'}</span>Submitted ${when(s.created_at)}</p>
          ${s.note ? `<p class="st-muted" style="margin:0">“${E(s.note)}”</p>` : ''}</div>
          <div class="st-row"><a class="st-btn st-btn--solid st-btn--small" href="#/review/${s.id}">Open</a></div></li>`).join('')}</ul>` : '<p class="st-muted">Nothing waiting.</p>'}
      </section>
      <section class="st-card"><h2>Ready to publish</h2>
        <p class="st-muted">Publishing sends approved gallery content to plotnua.ie through the content-only pipeline. Nothing else on the website can change this way.${o.instant_autopublish ? ' Availability and removals publish automatically.' : ' Availability and removal updates wait here until automatic publishing is switched on.'}</p>
        ${o.queue.length ? `<ul class="st-works">${o.queue.map(q => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto"><div><p class="st-work-t">${E(q.display_name)}</p>
          <p class="st-work-s" style="margin:0">Version ${q.version} · ${q.kind === 'instant' ? 'availability, removal or order' : q.kind === 'remove' ? 'remove the gallery' : 'approved changes'} · ${q.status === 'awaiting_founder' ? 'waiting for you' : q.status === 'failed' ? '<span class="st-flag">publishing failed</span>' : E(q.status)}</p>
          ${q.status === 'failed' && q.detail ? `<p class="st-muted st-pubfail" style="margin:.25rem 0 0">${E(failLine(q.detail))}</p>` : ''}</div>
          ${q.status === 'awaiting_founder' ? `<div class="st-row"><a class="st-btn st-btn--small" href="/admin/preview/v-${q.artist_id}-${q.version}/index.html" target="_blank" rel="noopener">Preview</a><button class="st-btn st-btn--solid st-btn--small" data-pub="${q.id}">Publish</button></div>`
            : q.status === 'failed' ? `<div class="st-row"><a class="st-btn st-btn--small" href="/admin/preview/v-${q.artist_id}-${q.version}/index.html" target="_blank" rel="noopener">Preview</a><button class="st-btn st-btn--solid st-btn--small" data-retry="${q.id}">Retry publishing</button></div>` : '<span></span>'}
          <p class="st-pubwarn" data-pubwarn role="alert" hidden></p></li>`).join('')}</ul>` : '<p class="st-muted">Nothing waiting.</p>'}
      </section>
      ${o.flags.length ? `<section class="st-card"><h2 class="st-flag">Rights check</h2><p class="st-muted">The same photograph appears in more than one artist’s Studio. Check before approving.</p>
        <ul class="st-list">${o.flags.map(f => `<li>${E(f.display_name)} · image ${E(f.id)} · fingerprint ${E(f.sha256.slice(0, 12))}…</li>`).join('')}</ul></section>` : ''}
      <section class="st-card"><h2>Enquiries</h2><p class="st-muted">Buyer enquiries go straight to the artist (Reply-To the buyer). This is the record of founding-period enquiries.</p>
        <div id="enq"><p class="st-muted">Loading…</p></div></section>
      <section class="st-card"><h2>Artists</h2><div class="st-scroll"><table class="st-table"><thead><tr><th>Artist</th><th>Status</th><th>Agreement</th><th>Works</th><th>To do</th><th></th></tr></thead><tbody>
        ${o.artists.map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${TB(a.id)}${a.founding ? ' <span class="pa-gcard-badge" style="display:inline-block">Founding</span>' : a.programme === 'gallery_artist' ? ' <span class="pa-gcard-badge" style="display:inline-block">Gallery Artist</span>' : ''}<br><span class="st-muted">${E(a.email)}${a.application_ref ? ' · ' + E(a.application_ref) : ''}</span>
          <details class="st-ids"><summary>Identifiers</summary><span class="st-muted">Studio ID</span> <code>${E(a.id)}</code> <button type="button" class="st-linkbtn" data-copy="${E(a.id)}">Copy</button><br><span class="st-muted">Gallery address</span> <code>${E(a.slug)}</code> <button type="button" class="st-linkbtn" data-copy="${E(a.slug)}">Copy</button></details></td>
          <td>${a.account_status === 'suspended' ? '<span class="st-flag">Suspended</span>' : E(STATE[stateOf(a)])}${a.account_status === 'invited' ? '<br><span class="st-muted">Not signed in yet</span>' : ''}</td>
          <td>${agrCell(a)}</td><td>${a.works}</td><td>${a.problems ? `<button class="st-btn st-btn--small st-todo-btn" data-ck="${a.id}" aria-expanded="false" aria-controls="ck-${a.id}">${a.problems} item${a.problems > 1 ? 's' : ''}</button>` : '✓'}</td>
          <td class="st-row"><a class="st-btn st-btn--small" href="/admin/preview/d-${a.id}/index.html" target="_blank" rel="noopener" title="The artist’s saved draft, unpublished, read-only">Preview draft</a>
          ${a.account_status === 'suspended' ? `<button class="st-btn st-btn--small" data-act="reactivate" data-id="${a.id}">Reactivate</button>` : `<button class="st-btn st-btn--small" data-act="suspend" data-id="${a.id}">Suspend</button>`}
          ${a.live_version ? `<button class="st-btn st-btn--small st-btn--danger" data-act="unpublish" data-id="${a.id}">Unpublish</button>` : ''}
          <button class="st-btn st-btn--small" data-email="${a.id}" aria-expanded="false" aria-controls="em-${a.id}">Change email</button>
          ${a.account_status !== 'ended' ? `<button class="st-btn st-btn--small" data-pf="${a.id}" aria-expanded="false" aria-controls="pf-${a.id}">Start profile from application</button>` : ''}</td></tr>
          <tr id="pf-${a.id}" class="st-em-row" hidden><td colspan="6"><form class="st-em" data-pfform="${a.id}" novalidate>
            <p class="st-em-h">Start the profile of <b>${E(a.display_name)}</b> from their application</p>
            <div class="st-f"><label for="pf-r-${a.id}">Application reference</label><input id="pf-r-${a.id}" type="text" autocomplete="off" spellcheck="false" placeholder="F25-… or PA-AP-…" value="${E(a.application_ref || '')}"></div>
            <p class="st-muted st-em-note">Fills only the empty biography, medium, county, website and Instagram fields, using the Studio’s normal checks. Nothing already written is replaced. The county stays hidden from the public, application images and additional information are never copied, and no email is sent: let the artist know yourself.</p>
            <div class="st-row"><button type="submit" class="st-btn st-btn--solid st-btn--small">Start profile</button><button type="button" class="st-btn st-btn--small" data-pfcancel="${a.id}">Cancel</button></div>
            <p class="st-err" role="alert" data-pferr></p></form></td></tr>
          <tr id="ck-${a.id}" class="st-em-row" hidden><td colspan="6"><div class="st-ck-admin" data-ckbox="${a.id}"><p class="st-muted">Loading…</p></div></td></tr>
          <tr id="em-${a.id}" class="st-em-row" hidden><td colspan="6"><form class="st-em" data-emform="${a.id}" novalidate>
            <p class="st-em-h">Correct the sign-in email for <b>${E(a.display_name)}</b></p>
            <p class="st-muted st-em-now">Current address: <b>${E(a.email)}</b></p>
            <div class="st-two"><div class="st-f"><label for="em-n-${a.id}">New email address</label><input id="em-n-${a.id}" type="email" autocomplete="off" spellcheck="false" autocapitalize="off"></div>
            <div class="st-f"><label for="em-c-${a.id}">Type it again to confirm</label><input id="em-c-${a.id}" type="email" autocomplete="off" spellcheck="false" autocapitalize="off"></div></div>
            <label class="st-check st-em-ok"><input type="checkbox" data-emok style="accent-color:var(--terra);width:20px;height:20px"> I’ve checked this is the address the artist uses to sign in. The current address will stop working straight away.</label>
            <p class="st-muted st-em-note">Their gallery, artwork, Founding status and progress stay exactly as they are. No email is sent: let the artist know yourself.</p>
            <div class="st-row"><button type="submit" class="st-btn st-btn--solid st-btn--small">Save new email</button><button type="button" class="st-btn st-btn--small" data-emcancel="${a.id}">Cancel</button></div>
            <p class="st-err" role="alert" data-emerr></p></form></td></tr>`).join('') || '<tr><td colspan="6" class="st-muted">No artists yet.</td></tr>'}
      </tbody></table></div></section>
      <section class="st-card"><h2>Invite a selected artist</h2><p class="st-muted">New artists join as Gallery Artists, on the standard 15% commission terms, and accept the Gallery Artist Agreement in Studio before their gallery is first published. Copy their name, email and any application reference. The invitation email goes automatically when email is switched on.</p>
        <div class="st-two"><div>
        <div class="st-f"><label for="i-name">Artist name</label><input id="i-name" type="text"></div>
        <div class="st-f"><label for="i-email">Email they applied with</label><input id="i-email" type="email"></div></div><div>
        <div class="st-f"><label for="i-ref">Application reference</label><input id="i-ref" type="text" placeholder="PA-AP-…"></div>
        <p class="st-f" style="margin:0 0 12px"><span class="st-lab" style="display:block;margin-bottom:4px">Programme</span>Gallery Artist <span class="st-muted">· Gallery Artist Agreement, 15% commission${o.terms_installed ? '' : ' (available once migration 0012 has run)'}</span></p>
        ${o.galleries_installed ? `<fieldset class="st-f st-inv-gal" style="border:0;margin:0 0 14px;padding:0"><legend style="padding:0;margin:0 0 6px">Galleries <span class="st-req">At least one</span></legend>
          <label class="st-check"><input type="checkbox" name="i-gal" value="contemporary" checked style="accent-color:var(--terra);width:20px;height:20px"> <span>Contemporary <span class="st-muted">· joins with their gallery, as every artist does today</span></span></label>
          <label class="st-check"><input type="checkbox" name="i-gal" value="spaces" style="accent-color:var(--terra);width:20px;height:20px"> <span>Spaces <span class="st-muted">· an invitation they accept in their Studio</span></span></label>
          <label class="st-check"><input type="checkbox" name="i-gal" value="being" style="accent-color:var(--terra);width:20px;height:20px"> <span>Being <span class="st-muted">· an invitation they accept in their Studio</span></span></label>
        </fieldset>` : ''}
        <button class="st-btn st-btn--solid" id="inv"${o.terms_installed ? '' : ' disabled'}>Create Studio account</button><p class="st-err" id="ierr"></p></div></div></section>
      <section class="st-card"><h2>System check</h2><p class="st-muted">Writes, reads back and removes a test record in the database and a test file in image storage.</p>
        <button class="st-btn" id="sys">Run system check</button><ul class="st-list" id="sysout"></ul></section>`;
    $('#sys').addEventListener('click', async () => { const r = await api('POST', '/api/admin/selftest');
      $('#sysout').innerHTML = [['Database', r.database], ['Image storage', r.image_storage], ['Automatic updates', r.publishing], ['Email', r.email]].map(([k, v]) => `<li><b style="color:var(--ivory)">${k}:</b> ${E(v)}</li>`).join('') + `<li><b style="color:var(--ivory)">${r.passed ? '✓ Passed' : '✗ Failed'}</b></li>`; });
    api('GET', '/api/admin/enquiries').then(r => { $('#enq').innerHTML = r.items.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Reference</th><th>Type</th><th>Date</th><th>Artist</th><th>Artwork</th><th>Delivered</th></tr></thead><tbody>${r.items.slice(0, 30).map(e => `<tr><td>${E(e.reference)}</td><td>${e.kind === 'hire' ? 'Hire' : 'Purchase'}</td><td>${when(e.created_at)}</td><td>${E(e.display_name)}</td><td>${E(e.artwork_title || 'General')}</td><td>${e.status === 'sent' ? '✓ emailed' : 'in Studio'}</td></tr>`).join('')}</tbody></table></div>` : '<p class="st-muted">None yet.</p>'; });
    app.querySelectorAll('[data-pub]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = 'Publish to plotnua.ie?'; return; }
      const warn = b.closest('li').querySelector('[data-pubwarn]');
      try {
        const d = await api('POST', `/api/admin/queue/${b.dataset.pub}/publish`, b.dataset.force ? { confirm_without_agreement: true } : {});
        say(d.publish === 'requested' ? 'Publishing started: plotnua.ie updates once every check has passed (usually within 5–15 minutes)'
          : d.publish === 'failed' ? 'Approved for publishing. It could not be started just now, so it will go out at the next scheduled run' : 'Approved for publishing: it will go out at the next scheduled run', d.publish === 'failed');
        home();
      }
      catch (e) {
        warn.hidden = false; warn.textContent = e.message;
        if (e.data && e.data.needs_confirmation) { b.dataset.force = 1; b.textContent = 'Publish anyway'; } else { b.disabled = true; }
      }
    }));
    // Retry publishing (12 Nov 2026): a failed job goes back through the same protected workflow and every image check
    app.querySelectorAll('[data-retry]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = 'Retry publishing to plotnua.ie?'; return; }
      const warn = b.closest('li').querySelector('[data-pubwarn]');
      b.disabled = true;
      try {
        const d = await api('POST', `/api/admin/queue/${b.dataset.retry}/retry`, b.dataset.force ? { confirm_without_agreement: true } : {});
        say(d.publish === 'requested' ? 'Retry started: plotnua.ie updates once every check has passed (usually within 5–15 minutes). If a check fails again, it shows here as failed.'
          : d.publish === 'failed' ? 'Retry queued. Publishing could not be started just now, so it will go out at the next scheduled run' : 'Retry queued: it will go out at the next scheduled publishing run', d.publish === 'failed');
        home();
      }
      catch (e) {
        warn.hidden = false; warn.textContent = 'Not retried: ' + e.message;
        if (e.data && e.data.needs_confirmation) { b.disabled = false; b.dataset.force = 1; b.textContent = 'Retry anyway'; }
      }
    }));
    app.querySelectorAll('[data-act]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = b.textContent + '?'; return; }
      await api('POST', `/api/admin/artists/${b.dataset.id}/${b.dataset.act}`); say('Done'); home();
    }));
    // Submission checklist (PLOTART-STUDIO-SUBMISSION-002): read-only; exactly what the artist sees, nothing can be waived here
    const NEED = { title: 'title', medium: 'medium', size: 'size', ai: 'AI question', ai_note: 'AI note', main_photo: 'main photograph',
      photo_alt: 'photograph description', photographer: 'who took the photograph', photo_credit: 'photographer’s name', photo_blocked: 'replacement photograph' };
    const SECTION = { profile: 'Profile', works: 'Artworks', work: 'Artwork', licence: 'Licence' };
    app.querySelectorAll('[data-ck]').forEach(b => b.addEventListener('click', async () => {
      const row = $(`#ck-${b.dataset.ck}`), open = row.hidden; row.hidden = !open; b.setAttribute('aria-expanded', String(open));
      if (!open || row.dataset.loaded) return;
      const box = $(`[data-ckbox="${b.dataset.ck}"]`, row);
      try {
        const r = await api('GET', `/api/admin/artists/${b.dataset.ck}/checklist`); row.dataset.loaded = '1';
        box.innerHTML = `<p class="st-em-h">${E(r.artist.display_name)} · ${r.count} item${r.count === 1 ? '' : 's'} before they can submit <span class="st-muted">(read-only: the artist completes these in their Studio)</span></p>
          <table class="st-table st-ck-table"><thead><tr><th>Section</th><th>Outstanding</th></tr></thead><tbody>${r.items.map(i => `<tr><td>${E(SECTION[i.area])}${i.area === 'work' ? `<br><span class="st-muted">${E(i.title || 'Untitled artwork')}</span>` : ''}</td>
            <td>${i.area === 'work' ? E(i.needs.map(c => NEED[c]).join(', ')) : E(i.text)}</td></tr>`).join('')}</tbody></table>`;
      } catch (e) { box.innerHTML = `<p class="st-err">${E(e.message)}</p>`; }
    }));
    // Start profile from application (11 Nov 2026): founder-only; the server applies every pre-fill safeguard and sends no email
    const PF = { bio: 'biography', medium: 'medium', county: 'county', website: 'website', instagram: 'Instagram' };
    app.querySelectorAll('[data-pf]').forEach(b => b.addEventListener('click', () => {
      const row = $(`#pf-${b.dataset.pf}`), open = row.hidden; row.hidden = !open; b.setAttribute('aria-expanded', String(open));
      if (open) $('input', row).focus();
    }));
    app.querySelectorAll('[data-pfcancel]').forEach(b => b.addEventListener('click', () => {
      $(`#pf-${b.dataset.pfcancel}`).hidden = true; $(`[data-pf="${b.dataset.pfcancel}"]`).setAttribute('aria-expanded', 'false');
    }));
    app.querySelectorAll('[data-pfform]').forEach(f => f.addEventListener('submit', async ev => {
      ev.preventDefault();
      const err = $('[data-pferr]', f), ref = $('input', f).value.trim();
      err.textContent = '';
      if (!ref) { err.textContent = 'Enter the application reference.'; return; }
      try {
        const r = await api('POST', `/api/admin/artists/${f.dataset.pfform}/prefill`, { application_ref: ref });
        say(r.fields.length ? `Profile started from ${r.application_ref}: ${r.fields.map(k => PF[k]).join(', ')}. No email was sent.`
          : `Nothing to fill: those fields already hold information. No email was sent.`); home();
      } catch (e) { err.textContent = e.message; }
    }));
    // Change email (PLOTART-STUDIO-ACCESS-002): founder-only, typed twice and confirmed; the server re-checks everything
    const emRow = id => $(`#em-${id}`);
    app.querySelectorAll('[data-email]').forEach(b => b.addEventListener('click', () => {
      const row = emRow(b.dataset.email), open = row.hidden; row.hidden = !open; b.setAttribute('aria-expanded', String(open));
      if (open) $('input[type=email]', row).focus();
    }));
    app.querySelectorAll('[data-emcancel]').forEach(b => b.addEventListener('click', () => {
      const row = emRow(b.dataset.emcancel); row.hidden = true; $(`[data-email="${b.dataset.emcancel}"]`).setAttribute('aria-expanded', 'false');
    }));
    app.querySelectorAll('[data-emform]').forEach(f => f.addEventListener('submit', async ev => {
      ev.preventDefault();
      const id = f.dataset.emform, err = $('[data-emerr]', f), [n, c] = f.querySelectorAll('input[type=email]');
      err.textContent = '';
      if (!n.value.trim()) { err.textContent = 'Enter the new email address.'; return; }
      if (n.value.trim().toLowerCase() !== c.value.trim().toLowerCase()) { err.textContent = 'The two entries don’t match. Type the new address the same way twice.'; return; }
      if (!$('[data-emok]', f).checked) { err.textContent = 'Tick the box to confirm before saving.'; return; }
      try {
        const r = await api('POST', `/api/admin/artists/${id}/email`, { email: n.value, confirm_email: c.value, confirm: true });
        say(`Email changed to ${r.email}. No email was sent.`); home();
      } catch (e) { err.textContent = e.message; }
    }));
    $('#inv').addEventListener('click', async () => {
      try {
        // Gallery Artist is the only programme for new invitations (26 Nov 2026). Galleries: Contemporary alone sends no choice,
        // exactly as before; any other choice is sent, and none ticked is refused here and by the server.
        const gals = [...document.querySelectorAll('input[name=i-gal]:checked')].map(x => x.value), hasGal = !!document.querySelector('input[name=i-gal]');
        if (hasGal && !gals.length) { $('#ierr').textContent = 'Choose at least one gallery.'; return; }
        const r = await api('POST', '/api/admin/artists', { display_name: $('#i-name').value, email: $('#i-email').value, application_ref: $('#i-ref').value || null, programme: 'gallery_artist',
          ...(hasGal && !(gals.length === 1 && gals[0] === 'contemporary') ? { galleries: gals } : {}) });
        const pf = r.prefill || {};
        const pfNote = pf.fields && pf.fields.length ? ` · profile started from the application (${pf.fields.length} of 5 fields)`
          : ($('#i-ref').value ? ` · profile not pre-filled: ${pf.reason || 'nothing usable in the application'}` : '');
        say((r.invitation_sent ? 'Account created · invitation emailed' : 'Account created · email is off, so send the invitation by hand') + pfNote); home();
      } catch (e) { $('#ierr').textContent = e.message; }
    });
  }

  async function review(id) {
    const r = await api('GET', `/api/admin/submissions/${id}`), s = r.submission;
    const gen = r.works.filter(w => w.ai_involvement === 'generated');
    const tiers = { full: 'Review', light: 'Quick check', instant: 'Live' };
    app.innerHTML = `
      <p><a href="#/" style="color:var(--stone);text-decoration:none">← Review desk</a></p>
      <h1 class="st-h1">${E(r.artist.display_name)}${TB(r.artist.id)}</h1>
      <p class="st-sub"><span class="st-tier ${s.tier}">${tiers[s.tier]}</span>Submitted ${when(s.created_at)} · ${s.status === 'pending' ? 'waiting for you' : E(s.status)}${r.artist.founding ? ' · Founding Artist' : ''} · ${agrLine(r.agreement, r.artist)}</p>
      ${s.note ? `<p class="st-msg">${E(s.note)}</p>` : ''}
      <div class="st-two"><div>
      <section class="st-card"><h2>What changes</h2><ul class="st-list">${s.changes.map(c => `<li><span><span class="st-tier ${c.tier}">${tiers[c.tier]}</span>${E(c.what)}${PAChanges.detail(c)}</span></li>`).join('')}</ul>
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

  /* ---- Applications with artwork images (private; founder only): Founding 25 (F25-…) and PlotArt (PA-AP-…, Phase 3). Decisions stay in Airtable. */
  const MED = { painting: 'Painting', drawing: 'Drawing', works_on_paper: 'Works on paper', printmaking: 'Printmaking', photography: 'Photography', sculpture: 'Sculpture',
    ceramics_craft: 'Ceramics and craft', textiles: 'Textiles', mixed_media: 'Mixed media', digital: 'Digital', other: 'Other' };
  const county = c => c ? c.split('_').map(w => w[0].toUpperCase() + w.slice(1)).join(' ') : '';
  const ext = (u, label) => u ? `<a class="st-btn st-btn--small" href="${E(u)}" target="_blank" rel="noopener noreferrer nofollow">${E(label)} ↗</a>` : '';
  async function apps() {
    const r = await api('GET', '/api/admin/applications');
    app.innerHTML = `<h1 class="st-h1">Applications</h1><p class="st-sub">Gallery Artist applications and earlier Founding 25 applications. Private: only you can see them.</p>
      ${!r.connected ? '<section class="st-card"><p class="st-muted">Application image storage isn’t connected yet.</p></section>' : r.items.length ? `<ul class="st-works">${r.items.map(a => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto">
        <div><p class="st-work-t"><a href="/admin/applications/${E(a.ref)}" style="color:inherit">${E(a.artist_name)}</a></p>
        <p class="st-work-s">${a.ref.startsWith('PA-AP-') ? 'PlotArt application' : 'Founding 25'} · ${E(a.ref)} · ${E(MED[a.medium] || a.medium)}${a.region ? ' · ' + E(county(a.region)) : ''} · ${when(a.submitted_at)}${a.status ? ' · ' + E(a.status) : ''}${a.revised_at && a.status === 'under_review' ? ' · Revised information ready for review' : ''}</p>
        <div class="st-appthumbs">${a.images.map(i => `<img src="${E(i.src)}" alt="" loading="lazy">`).join('')}</div></div>
        <div class="st-row"><a class="st-btn st-btn--solid st-btn--small" href="/admin/applications/${E(a.ref)}">Open</a></div></li>`).join('')}</ul>` : '<section class="st-card"><p class="st-muted">No applications yet.</p></section>'}`;
  }
  async function appView(ref) {
    const a = (await api('GET', '/api/admin/applications/' + ref)).application;
    app.innerHTML = `<p><a href="/admin/applications" style="color:var(--stone);text-decoration:none">← Applications</a></p>
      <h1 class="st-h1">${E(a.artist_name)}</h1><p class="st-sub">${E(a.ref)} · ${E(MED[a.medium] || a.medium)}${a.region ? ' · ' + E(county(a.region)) : ''} · applied ${when(a.submitted_at)}</p>
      <div class="st-appgrid">${a.images.map((i, n) => `<a href="${E(i.src)}" target="_blank" rel="noopener"><img src="${E(i.src)}" alt="Artwork ${n + 1} of ${a.images.length} from ${E(a.artist_name)}"${i.w ? ` width="${i.w}" height="${i.h}"` : ''}></a>`).join('')}</div>
      <div class="st-two" style="margin-top:18px"><section class="st-card"><h2>Artist statement</h2><p style="white-space:pre-line">${E(a.bio)}</p>
        ${a.additional_info ? `<h2 style="margin-top:18px">Anything else</h2><p style="white-space:pre-line">${E(a.additional_info)}</p>` : ''}</section>
      <section class="st-card"><h2>Links</h2><div class="st-row" style="flex-wrap:wrap;gap:8px">${ext(a.portfolio, 'Portfolio')}${ext(a.website, 'Website')}${a.social_link ? (a.social_link.startsWith('@') ? ext('https://www.instagram.com/' + a.social_link.slice(1) + '/', a.social_link) : ext(a.social_link, 'Profile')) : ''}${!a.portfolio && !a.website && !a.social_link ? '<p class="st-muted" style="margin:0">No links: the images are the portfolio.</p>' : ''}</div>
        <h2 style="margin-top:18px">Decision</h2><p class="st-muted">${a.ref.startsWith('PA-AP-') ? 'Review this application using the controls below. After acceptance, invite the artist separately from the Review Desk as a Gallery Artist.' : 'Shortlist, select or decline in Airtable, where the application\'s status and emails are recorded.'}</p>
        ${!a.ref.startsWith('PA-AP-') && a.airtable ? `<a class="st-btn st-btn--solid" href="${E(a.airtable)}" target="_blank" rel="noopener noreferrer">Open in Airtable ↗</a>` : ''}
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

  /* ---- Founding Artist Agreement (development 6 Nov 2026): status, acceptance history, founding years, enquiry log */
  const DOCNAME = { 'PA-GAA-2026-11': 'Gallery Artist Agreement', 'PA-FAA-2026-11': 'Founding Artist Agreement', 'PA-GPIL-2026-11': 'Image Licence', 'PA-GPIL-2026-10-29': 'Image Licence (earlier label)' };
  const irishDay = d => d ? new Date(d + 'T12:00:00Z').toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/Dublin' }) : '';
  const irish = t => t ? new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Dublin' }) : '';
  /* one line for a submission: the agreement status the publishing gate uses (never the pre-agreement licence label alone) */
  function agrLine(g, a) {
    if (g && g.accepted) return a && TEST.has(a.id) ? `test acceptance ${E(irish(g.accepted_at))} · not genuine consent` : `agreement accepted ${E(irish(g.accepted_at))}`;
    if (g && g.installed === false) return 'agreement not installed';
    if (a && a.licence_version) return `<span style="color:#CF8566">agreement not accepted (earlier licence ${E(a.licence_version)} only)</span>`;
    return '<span style="color:#CF8566">agreement not accepted</span>';
  }
  function agrCell(a) {
    const g = a.agreement;
    if (!g || !g.installed) return '<span class="st-muted">Not installed</span>';
    if (g.accepted) return TEST.has(a.id) ? `<span class="st-pill st-pill--warn">Test acceptance</span><br><span class="st-muted">not genuine consent</span>` : `<span class="st-pill st-pill--ok">Accepted</span><br><span class="st-muted">${E(irish(g.accepted_at))}</span>`;
    if (g.legacy) return `<span class="st-pill st-pill--warn">Earlier licence only</span><br><span class="st-muted">${E(g.legacy.version)}</span>`;
    return '<span class="st-pill">Not accepted</span>';
  }
  async function agreements() {
    const o = await api('GET', '/api/admin/overview');
    let L = await api('GET', '/api/admin/enquiry-log');
    const fy = g => g && g.founding_year ? `${irishDay(g.founding_year.start)} – ${irishDay(g.founding_year.end)}` : g && g.founding ? 'Starts at first publication' : '—';
    const waiting = o.artists.filter(a => a.agreement && a.agreement.installed && !a.agreement.accepted && !TEST.has(a.id));   // a test account is never counted
    function drawLog() {
      const el = $('#elog');
      if (!L.installed) { el.innerHTML = '<p class="st-muted">The enquiry log is installed with migration 0005.</p>'; return; }
      el.innerHTML = `<div class="st-scroll"><table class="st-table"><thead><tr><th>Reference</th><th>Introduced</th><th>Artist</th><th>Artwork</th><th>Route</th><th>Founding</th><th>Recorded</th><th></th></tr></thead><tbody>
        ${L.items.map(i => `<tr><td>${E(i.reference)}${i.corrects ? `<br><span class="st-muted">corrects ${E((L.items.find(x => x.id === i.corrects) || {}).reference || i.corrects)}</span>` : ''}</td><td>${E(irishDay(new Date(i.introduced_at).toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' })))}</td>
          <td>${E(i.display_name)}</td><td>${E(i.artwork_title || 'General')}</td><td>${i.route === 'relay' ? 'Online form' : 'Email'}</td>
          <td>${i.founding ? '<span class="st-pill st-pill--ok">Founding</span>' : '<span class="st-pill">After founding year</span>'}</td>
          <td><span class="st-muted">${E(irish(i.logged_at))}${i.late_entry ? '<br><b>late entry</b>' : ''}${i.note ? `<br>“${E(i.note)}”` : ''}</span></td>
          <td>${i.route === 'email' ? `<button class="st-btn st-btn--small" data-fix="${E(i.id)}">Correct</button>` : ''}</td></tr>`).join('') || '<tr><td colspan="8" class="st-muted">Nothing logged yet.</td></tr>'}</tbody></table></div>`;
      el.querySelectorAll('[data-fix]').forEach(b => b.addEventListener('click', () => {
        const i = L.items.find(x => x.id === b.dataset.fix);
        $('#lg-corrects').value = i.id; $('#lg-artist').value = i.artist_id; works(); $('#lg-work').value = i.artwork_id || '';
        $('#lg-fixnote').hidden = false; $('#lg-fixnote').textContent = `Correcting ${i.reference}: the original stays on record and this new entry is linked to it.`;
        $('#lg-form').scrollIntoView({ block: 'start' }); $('#lg-day').focus();
      }));
    }
    function works() {
      const a = L.artists.find(x => x.id === $('#lg-artist').value);
      $('#lg-work').innerHTML = '<option value="">General enquiry (no particular work)</option>' + (a ? a.works.map(w => `<option value="${E(w.id)}">${E(w.title)}</option>`).join('') : '');
      $('#lg-fy').textContent = a ? (a.founding ? (a.founding_year ? `Founding year: ${irishDay(a.founding_year.start)} to ${irishDay(a.founding_year.end)}.` : 'Not published yet: an enquiry now counts as a Founding Enquiry.') : 'Not a Founding Artist.') : '';
    }
    app.innerHTML = `<h1 class="st-h1">Agreements</h1>
      <p class="st-sub">Founding Artist Agreement ${E('PA-FAA-2026-11')} and Image Licence ${E('PA-GPIL-2026-11')}: who has accepted, each artist’s founding year, and the enquiry log. Acceptance records can’t be edited or deleted.</p>
      ${!o.agreement_installed ? '<div class="st-card" role="alert"><p style="margin:0"><b>Not installed yet.</b> Artists can accept once migration 0005 has been run. Everything else in Studio works as before.</p></div>' : ''}
      ${waiting.length ? `<div class="st-card st-agr-warn"><p style="margin:0"><b>${waiting.length} artist${waiting.length === 1 ? ' hasn’t' : 's haven’t'} accepted yet.</b> Their galleries stay live and they can keep editing. A first publication is blocked until the artist accepts; for an artist who is already published, Publish asks you to confirm.</p></div>` : ''}
      <section class="st-card"><h2>Artists</h2><div class="st-scroll"><table class="st-table"><thead><tr><th>Artist</th><th>Agreement</th><th>Founding year</th><th></th></tr></thead><tbody>
        ${o.artists.map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${TB(a.id)}${a.founding ? ' <span class="pa-gcard-badge" style="display:inline-block">Founding</span>' : a.programme === 'gallery_artist' ? ' <span class="pa-gcard-badge" style="display:inline-block">Gallery Artist</span>' : ''}${a.founding_number ? `<br><span class="st-muted">No. ${a.founding_number}</span>` : ''}</td>
          <td>${agrCell(a)}</td><td>${E(fy(a.agreement))}</td><td><button class="st-btn st-btn--small" data-hist="${a.id}" aria-expanded="false" aria-controls="hi-${a.id}">History</button></td></tr>
          <tr id="hi-${a.id}" class="st-em-row" hidden><td colspan="4"><div data-hibox="${a.id}"><p class="st-muted">Loading…</p></div></td></tr>`).join('') || '<tr><td colspan="4" class="st-muted">No artists yet.</td></tr>'}
      </tbody></table></div></section>
      <section class="st-card" id="lg-form" aria-labelledby="lg-h"><h2 id="lg-h">Log enquiry</h2>
        <p class="st-muted">Record an enquiry PlotArt introduced to an artist <b>by email</b>. Enquiries through the online form are logged automatically. Record only real enquiries, with the date you introduced them; an entry more than 7 days old is marked as a late entry. Nothing here can be edited or deleted: use Correct to add a linked correction.</p>
        <input type="hidden" id="lg-corrects"><p class="st-msg" id="lg-fixnote" hidden></p>
        <div class="st-two"><div>
          <div class="st-f"><label for="lg-artist">Artist</label><select id="lg-artist"><option value="">Choose…</option>${L.artists.map(a => `<option value="${E(a.id)}">${E(a.display_name)}</option>`).join('')}</select><p class="st-hint" id="lg-fy"></p></div>
          <div class="st-f"><label for="lg-work">Artwork (optional)</label><select id="lg-work"><option value="">General enquiry (no particular work)</option></select></div>
          <div class="st-f"><label for="lg-day">Date PlotArt introduced it (Irish date)</label><input id="lg-day" type="date" value="${E(L.today || '')}" max="${E(L.today || '')}" min="${E(L.floor || '')}"></div>
        </div><div>
          <div class="st-f"><label for="lg-note">Note (optional)</label><textarea id="lg-note" maxlength="280" placeholder="e.g. Forwarded from the PlotNua inbox"></textarea>
            <p class="st-hint"><b>Never enter the buyer’s name, email address or phone number.</b> Up to 280 characters.</p></div>
          <label class="st-check"><input type="checkbox" id="lg-ok" style="accent-color:var(--terra);width:20px;height:20px"> PlotArt introduced this enquiry to the artist on this date.</label>
          <div class="st-actions"><button class="st-btn st-btn--solid" id="lg-go">Log enquiry</button></div><p class="st-err" id="lg-err" role="alert"></p>
        </div></div></section>
      <section class="st-card"><h2>Enquiry log</h2><p class="st-muted">Reference, date, artist and artwork only: no buyer details. Kept for the life of the agreement and six years afterwards. Buyer names, emails and messages from the online form are deleted after 24 months as before.</p><div id="elog"></div></section>`;
    drawLog();
    $('#lg-artist').addEventListener('change', works);
    $('#lg-go').addEventListener('click', async () => {
      $('#lg-err').textContent = '';
      try {
        const corrects = $('#lg-corrects').value || null;
        L = await api('POST', '/api/admin/enquiry-log', { artist_id: $('#lg-artist').value, artwork_id: $('#lg-work').value || null, introduced_on: $('#lg-day').value, note: $('#lg-note').value || null, confirm: $('#lg-ok').checked, corrects });
        say(`Logged ${L.reference}${L.founding ? ' · Founding Enquiry' : ''}${L.late_entry ? ' · late entry' : ''}`);
        $('#lg-note').value = ''; $('#lg-ok').checked = false; $('#lg-corrects').value = ''; $('#lg-fixnote').hidden = true; drawLog();
      } catch (e) { $('#lg-err').textContent = e.message; }
    });
    app.querySelectorAll('[data-hist]').forEach(b => b.addEventListener('click', async () => {
      const row = $(`#hi-${b.dataset.hist}`), open = row.hidden; row.hidden = !open; b.setAttribute('aria-expanded', String(open));
      if (!open || row.dataset.loaded) return;
      const box = $(`[data-hibox="${b.dataset.hist}"]`, row);
      row.dataset.loaded = '1'; await historyBox(box, b.dataset.hist);
    }));
  }

  /* Acceptance history for one artist, grouped by acceptance, with linked corrections (6 Nov 2026). Nothing here edits a
     record: "Correct" adds a separate correction with a reason; the original values stay visible. */
  const FIELD = { legal_name: 'Legal name', display_name: 'Professional name', account_email: 'Studio email address' };
  async function historyBox(box, id) {
    let r;
    try { r = await api('GET', `/api/admin/artists/${id}/agreement`); } catch (e) { box.innerHTML = `<p class="st-err">${E(e.message)}</p>`; return; }
    const ev = {};
    for (const x of r.agreement.history) (ev[x.event_id] ||= []).push(x);
    const groups = Object.values(ev);
    const corrLine = c => `<li>${E(irish(c.corrected_at))} · ${E(FIELD[c.field])}: “${E(c.previous_value ?? '—')}” → “${E(c.corrected_value ?? '(removed)')}” · asked by ${c.requested_by === 'artist' ? 'the artist' : 'you'} · ${E(c.reason)}</li>`;
    box.innerHTML = `<p class="st-em-h">${E(r.artist.display_name)} · first published ${r.artist.first_published_at ? E(irish(r.artist.first_published_at)) : 'not yet'}${r.agreement.founding_year ? ` · founding year ${E(irishDay(r.agreement.founding_year.start))} to ${E(irishDay(r.agreement.founding_year.end))}` : ''}</p>
      ${groups.length ? groups.map(g => { const x = g[0], studio = x.method === 'studio_checkbox', cs = g[0].corrections;
        return `<div class="st-acc" data-ev="${E(x.event_id)}">
        <p class="st-acc-h"><b>${E(irish(x.accepted_at))}</b> · ${studio ? 'Ticked in Studio' : 'Carried over from the earlier Studio record (label only)'}</p>
        <ul class="st-acc-docs">${g.map(d => `<li>${E(DOCNAME[d.doc_id] || d.doc_id)} <span class="st-muted">${E(d.doc_id)}${d.doc_sha256 ? ` · fingerprint ${E(d.doc_sha256.slice(0, 16))}…` : ' · no fixed text'}</span>${d.doc_sha256 ? ` <a class="st-btn st-btn--small" href="/agreements/${E(d.doc_id)}.pdf" download>PDF</a>` : ''}</li>`).join('')}</ul>
        <dl class="st-dl st-acc-dl"><dt>Professional name</dt><dd>${E(x.display_name || '—')}${x.original.display_name !== x.display_name ? ` <span class="st-muted">(as recorded: ${E(x.original.display_name)})</span>` : ''}</dd>
          ${studio ? `<dt>Legal name</dt><dd>${E(x.legal_name || '—')}${x.original.legal_name !== x.legal_name ? ` <span class="st-muted">(as recorded: ${E(x.original.legal_name || '—')})</span>` : ''}</dd>
          <dt>Studio address</dt><dd>${E(x.account_email || '—')}${x.original.account_email !== x.account_email ? ` <span class="st-muted">(as recorded: ${E(x.original.account_email)})</span>` : ''}</dd>` : ''}</dl>
        ${cs.length ? `<p class="st-acc-ch">Corrections (the record above is unchanged; these are kept beside it)</p><ul class="st-list">${cs.map(corrLine).join('')}</ul>` : ''}
        <button class="st-btn st-btn--small" data-corr="${E(x.event_id)}" aria-expanded="false">Correct a detail</button>
        <form class="st-em" data-corrform="${E(x.event_id)}" hidden novalidate>
          <p class="st-em-h">Correct a detail of this acceptance</p>
          <p class="st-muted">The documents, versions, fingerprints and the time of acceptance can’t be corrected, and a correction is not a new acceptance.</p>
          <div class="st-two"><div class="st-f"><label>What to correct</label><select data-k="field">${(studio ? ['legal_name', 'display_name', 'account_email'] : ['display_name']).map(f => `<option value="${f}">${FIELD[f]}</option>`).join('')}</select></div>
          <div class="st-f"><label>Correct value</label><input type="text" data-k="value" autocomplete="off"><p class="st-hint">For a legal name entered by mistake, leave it empty to remove it.</p></div></div>
          <div class="st-f"><label>Reason</label><textarea data-k="reason" maxlength="280" style="min-height:70px" placeholder="e.g. The artist emailed: their legal name was mistyped"></textarea></div>
          <div class="st-row" style="gap:16px;flex-wrap:wrap"><label class="st-check"><input type="radio" name="rq-${E(x.event_id)}" value="artist" checked> The artist asked</label><label class="st-check"><input type="radio" name="rq-${E(x.event_id)}" value="founder"> My own correction</label></div>
          <label class="st-check"><input type="checkbox" data-k="ok" style="accent-color:var(--terra);width:20px;height:20px"> I’ve checked this correction.</label>
          <div class="st-row"><button type="submit" class="st-btn st-btn--solid st-btn--small">Save correction</button></div><p class="st-err" role="alert" data-corrERR></p></form></div>`; }).join('')
        : '<p class="st-muted">No acceptance recorded.</p>'}
      <p class="st-muted" style="margin:10px 0 0">${r.enquiries.length} logged enquir${r.enquiries.length === 1 ? 'y' : 'ies'}, ${r.enquiries.filter(e => e.founding).length} Founding.</p>
      ${r.terms ? `<form class="st-em" data-terms novalidate>
        <p class="st-em-h">Gallery Artist terms <span class="st-muted">· private to you; the artist sees only their rate</span></p>
        <p class="st-muted">The standard commission is 15%. A different rate needs an individual variation agreed in writing (agreement clause 13), and never more than 15%. Last set ${E(irish(r.terms.updated_at))}.</p>
        <div class="st-two"><div class="st-f"><label for="tm-rate">Commission rate (%)</label><input id="tm-rate" type="number" min="0" max="15" step="0.01" inputmode="decimal" value="${(r.terms.commission_bp / 100).toFixed(2).replace(/\.00$/, '')}"></div>
        <div class="st-f"><label for="tm-day">Date the written variation was agreed</label><input id="tm-day" type="date" value="${E(r.terms.variation_agreed_on || '')}"><p class="st-hint">Required for any rate other than 15%.</p></div></div>
        <div class="st-f"><label for="tm-note">Private note</label><textarea id="tm-note" maxlength="1000" style="min-height:70px" placeholder="e.g. Agreed by email on this date; reference to the written variation">${E(r.terms.variation_note || '')}</textarea></div>
        <div class="st-row"><button type="submit" class="st-btn st-btn--solid st-btn--small">Save terms</button></div><p class="st-err" role="alert" data-termserr></p></form>` : ''}`;
    const tf = box.querySelector('[data-terms]');
    if (tf) tf.addEventListener('submit', async ev => {
      ev.preventDefault(); const err = tf.querySelector('[data-termserr]'); err.textContent = '';
      const bp = Math.round(Number(tf.querySelector('#tm-rate').value) * 100);
      try { await api('PUT', `/api/admin/artists/${id}/terms`, { commission_bp: bp, variation_agreed_on: tf.querySelector('#tm-day').value || null, variation_note: tf.querySelector('#tm-note').value });
        err.textContent = 'Saved.'; } catch (e) { err.textContent = e.message; }
    });
    box.querySelectorAll('[data-corr]').forEach(btn => btn.addEventListener('click', () => {
      const f = box.querySelector(`[data-corrform="${btn.dataset.corr}"]`); f.hidden = !f.hidden; btn.setAttribute('aria-expanded', String(!f.hidden));
    }));
    box.querySelectorAll('[data-corrform]').forEach(f => f.addEventListener('submit', async e => {
      e.preventDefault();
      const k = n => f.querySelector(`[data-k="${n}"]`);
      try {
        await api('POST', `/api/admin/artists/${id}/acceptance-corrections`, { event_id: f.dataset.corrform, field: k('field').value, value: k('value').value, reason: k('reason').value,
          requested_by: f.querySelector('input[type=radio]:checked').value, confirm: k('ok').checked });
        say('Correction saved beside the original record'); historyBox(box, id);
      } catch (x) { f.querySelector('[data-corrERR]').textContent = x.message; }
    }));
  }

  /* ---- Leaving PlotArt (founder decision 6 Nov 2026): requests, ending participation, and the deletion schedule */
  const STATE_L = { done: ['Done', 'ok'], pending: ['Waiting for the pipeline', 'warn'], overdue: ['Overdue', 'bad'], scheduled: ['Scheduled', ''], due: ['Due: deleted at the next daily run', 'warn'],
    due_job_off: ['Due, but deletion is switched off', 'bad'], manual: ['Your decision', ''], not_published: ['Never published', 'ok'] };
  /* ---- Art for Hire (Stage 3B-2): the founder's separate approval queue and recorded use permissions. Nothing here
     touches galleries, publishing or agreements. Screen and photo choices are the artist's willingness to discuss only. */
  async function hire() {
    let d;
    try { d = await api('GET', '/api/admin/hire'); } catch (e) { app.innerHTML = `<div class="st-card"><h1 class="st-h1">Art for Hire</h1><p class="st-muted">${E(e.message)}</p></div>`; return; }
    const L = { availability: 'Availability', available_from: 'From', county: 'County', screen_use: 'Screen use (willing to discuss)', photo_use: 'Photography (willing to discuss)',
      framing: 'Framing', glazed: 'Glazed', weight_band: 'Weight', collection: 'Collection', deliver_km: 'Delivery km' };
    const row = (k, p, a) => `<tr><td>${L[k]}</td><td>${E(p[k] ?? '—')}</td><td${a && (a[k] ?? null) !== (p[k] ?? null) ? ' style="color:#CF8566;font-weight:600"' : ''}>${a ? E(a[k] ?? '—') : 'not listed before'}</td></tr>`;
    app.innerHTML = `<h1 class="st-h1">Art for Hire</h1>
      <p class="st-sub">Status: ${d.enabled ? 'switched on' : '<b>switched off</b>'} · terms: ${d.terms ? E(d.terms.doc_id) : '<b>not issued</b>'}. A work is listed only when the artist holds the terms, has offered it, and you approve it. ${E(d.notice)}</p>
      <section class="st-card"><h2>Waiting for you (${d.pending.length})</h2>
        ${d.pending.length ? d.pending.map(i => `<div class="st-acc" data-w="${E(i.artwork_id)}"><p class="st-acc-h"><b>${E(i.artist)}</b> · ${E(i.title || 'Untitled')} · changed ${when(i.updated_at)}</p>
          <table class="st-table"><tr><th></th><th>Proposed</th><th>Listed now</th></tr>${Object.keys(L).map(k => row(k, i.proposed, i.approved)).join('')}</table>
          <div class="st-f"><label>Reason if not accepted (sent to the artist in Studio)</label><input type="text" data-reason maxlength="280"></div>
          <div class="st-row" style="gap:10px"><button class="st-btn st-btn--solid" data-ok>Approve</button><button class="st-btn st-btn--danger" data-no>Not accepted</button></div></div>`).join('') : '<p class="st-muted">Nothing waiting.</p>'}
      </section>
      <section class="st-card"><h2>Listed for hire (${d.listed.length})</h2>
        ${d.listed.length ? `<ul>${d.listed.map(i => `<li>${E(i.artist_slug)} / ${E(i.work_slug)} · ${E(i.hire.availability)} · ${E(i.hire.county || '')}</li>`).join('')}</ul>` : '<p class="st-muted">None.</p>'}
      </section>
      <section class="st-card"><h2>Record a use permission</h2>
        <p class="st-muted">For one specific use only (for example a lookbook sent to named businesses), and only after the artist has answered in writing. A “no” is recorded too.</p>
        <div class="st-grid2"><div class="st-f"><label for="pm-artist">Artist ID</label><input id="pm-artist" type="text"></div>
          <div class="st-f"><label for="pm-kind">Use</label><select id="pm-kind"><option value="lookbook">Lookbook</option><option value="social">Social</option><option value="press">Press</option><option value="other">Other</option></select></div></div>
        <div class="st-f"><label for="pm-purpose">The specific use</label><textarea id="pm-purpose" maxlength="500"></textarea></div>
        <div class="st-f"><label for="pm-rec">Recipients</label><input id="pm-rec" type="text" maxlength="500"></div>
        <div class="st-f"><label for="pm-works">Work IDs (comma separated)</label><input id="pm-works" type="text"></div>
        <div class="st-grid2"><div class="st-f"><label for="pm-ans">Artist’s answer</label><select id="pm-ans"><option value="yes">Yes</option><option value="no">No</option></select></div>
          <div class="st-f"><label for="pm-at">Answered on</label><input id="pm-at" type="datetime-local"></div></div>
        <button class="st-btn st-btn--solid" id="pm-go">Record</button><p class="st-err" id="pm-err" aria-live="polite"></p>
        ${d.permissions.length ? `<table class="st-table"><tr><th>Artist</th><th>Use</th><th>Answer</th><th>Answered</th></tr>${d.permissions.map(x => `<tr><td>${E(x.display_name || x.artist_id)}</td><td>${E(x.use_kind)}: ${E(x.purpose)}</td><td>${E(x.answer)}</td><td>${when(x.answered_at)}</td></tr>`).join('')}</table>` : ''}
      </section>
      <div id="hrep"></div>`;
    app.querySelectorAll('[data-w]').forEach(box => {
      const id = box.dataset.w;
      box.querySelector('[data-ok]').addEventListener('click', async () => { try { await api('POST', `/api/admin/hire/artwork/${id}/decision`, { decision: 'approve' }); say('Approved'); hire(); } catch (e) { say(e.message, true); } });
      box.querySelector('[data-no]').addEventListener('click', async () => { try { await api('POST', `/api/admin/hire/artwork/${id}/decision`, { decision: 'decline', reason: box.querySelector('[data-reason]').value }); say('Not accepted'); hire(); } catch (e) { say(e.message, true); } });
    });
    $('#pm-go').addEventListener('click', async () => {
      try { await api('POST', '/api/admin/hire/permissions', { artist_id: $('#pm-artist').value.trim(), use_kind: $('#pm-kind').value, purpose: $('#pm-purpose').value, recipients: $('#pm-rec').value,
        artwork_ids: $('#pm-works').value.split(',').map(x => x.trim()).filter(Boolean), answer: $('#pm-ans').value, answered_at: $('#pm-at').value ? new Date($('#pm-at').value).toISOString() : '' }); say('Recorded'); hire(); }
      catch (e) { $('#pm-err').textContent = e.message; }
    });
    await hireReports();
  }
  /* Hire reports (PA-AFH r5 6.5–6.6, 10.1): the founder's manual record of invoices and payments. Studio sends nothing and
     takes no payment; invoices are issued by email outside Studio. */
  const RB = { commission: 'Commission', founding_year: 'Founding year: none', outside_window: 'Over 12 months: none', no_fee: 'No fee: none' };
  const RI = { not_invoiced: 'Not invoiced', invoiced: 'Invoiced', no_commission: 'No commission', disputed: 'Disputed', superseded: 'Superseded' };
  const RP = { unpaid: 'Unpaid', paid: 'Paid', not_due: 'Not due', refunded: 'Refunded' };
  const eur = c => '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  async function hireReports() {
    const box = $('#hrep'); if (!box) return;
    let d; try { d = await api('GET', '/api/admin/hire/reports'); } catch (e) { box.innerHTML = `<section class="st-card"><h2>Hire reports</h2><p class="st-muted">${E(e.message)}</p></section>`; return; }
    if (!d.installed) { box.innerHTML = '<section class="st-card"><h2>Hire reports</h2><p class="st-muted">Hire reports are not installed (migration 0008).</p></section>'; return; }
    const sel = (name, map, v) => `<select name="${name}">${Object.entries(map).map(([k, t]) => `<option value="${k}"${k === v ? ' selected' : ''}>${E(t)}</option>`).join('')}</select>`;
    const T = d.totals;
    box.innerHTML = `<section class="st-card" aria-labelledby="hrep-h"><h2 id="hrep-h">Hire reports (${d.reports.length})</h2>
      <p class="st-muted">Reported by artists. Commission is 10% of the net hire fee, worked out from the enquiry log; founding-year introductions carry none. Invoices and payments are handled outside Studio: record them here by hand.</p>
      <p>Commission reported ${eur(T.commission_cents)} · not yet invoiced ${eur(T.not_invoiced_cents)} · invoiced, unpaid ${eur(T.invoiced_unpaid_cents)} · paid ${eur(T.paid_cents)}
        · <a href="/api/admin/hire/reports.csv" download>Download CSV</a></p>
      ${d.reports.length ? `<div class="st-scroll"><table class="st-table"><thead><tr><th>Reported</th><th>Artist</th><th>Enquiry</th><th>Artwork</th><th>Hire fee</th><th>Commission</th><th>Invoice</th><th>Payment</th><th></th></tr></thead><tbody>
        ${d.reports.map(r => `<tr${r.corrected_by ? ' style="opacity:.55"' : ''}><td>${E(new Date(r.reported_at).toLocaleDateString('en-IE'))}</td><td>${E(r.artist)}</td>
          <td>${E(r.reference)}${r.founding ? '<br><span class="st-muted">founding year</span>' : ''}${r.corrects ? '<br><span class="st-muted">correction</span>' : ''}${r.corrected_by ? '<br><span class="st-muted">replaced</span>' : ''}</td>
          <td>${E(r.artworks.join(', '))}<br><span class="st-muted">${E(r.hire_start)} to ${E(r.hire_end)} · agreed ${E(r.agreed_on)}</span>${r.starts_before_introduction ? '<br><span style="color:#CF8566">starts before the introduction: check</span>' : ''}</td>
          <td>${eur(r.net_fee_cents)}${r.more_to_pay ? '<br><span class="st-muted">instalment</span>' : ''}</td>
          <td>${r.basis === 'commission' ? eur(r.commission_cents) : E(RB[r.basis])}</td>
          <td>${E(RI[r.invoice_status] || '')}${r.invoice_no ? `<br><span class="st-muted">${E(r.invoice_no)} · ${E(r.invoiced_on || '')}</span>` : ''}</td>
          <td>${E(RP[r.payment_status] || '')}${r.paid_on ? `<br><span class="st-muted">${E(r.paid_on)}</span>` : ''}</td>
          <td><button class="st-btn" type="button" data-edit="${E(r.id)}" aria-expanded="false">Update</button></td></tr>
          <tr data-form="${E(r.id)}" hidden><td colspan="9"><div class="st-grid2">
            <div class="st-f"><label>Invoice</label>${sel('invoice_status', RI, r.invoice_status)}</div><div class="st-f"><label>Invoice number</label><input name="invoice_no" maxlength="40" value="${E(r.invoice_no || '')}"></div>
            <div class="st-f"><label>Invoice date</label><input type="date" name="invoiced_on" value="${E(r.invoiced_on || '')}"></div><div class="st-f"><label>Payment</label>${sel('payment_status', RP, r.payment_status)}</div>
            <div class="st-f"><label>Payment date</label><input type="date" name="paid_on" value="${E(r.paid_on || '')}"></div><div class="st-f"><label>Private note</label><input name="note" maxlength="280" value="${E(r.note || '')}"></div></div>
            <button class="st-btn st-btn--solid" type="button" data-save="${E(r.id)}">Save</button> <span class="st-err" data-err aria-live="polite"></span></td></tr>`).join('')}</tbody></table></div>`
      : '<p class="st-muted">No hire has been reported yet.</p>'}</section>`;
    box.querySelectorAll('[data-edit]').forEach(b => b.addEventListener('click', () => { const r = box.querySelector(`[data-form="${b.dataset.edit}"]`); r.hidden = !r.hidden; b.setAttribute('aria-expanded', String(!r.hidden)); }));
    box.querySelectorAll('[data-save]').forEach(b => b.addEventListener('click', async () => {
      const r = box.querySelector(`[data-form="${b.dataset.save}"]`), v = n => r.querySelector(`[name=${n}]`).value;
      try { await api('POST', `/api/admin/hire/reports/${b.dataset.save}/record`, { invoice_status: v('invoice_status'), invoice_no: v('invoice_no'), invoiced_on: v('invoiced_on'),
        payment_status: v('payment_status'), paid_on: v('paid_on'), note: v('note') }); say('Saved'); await hireReports(); }
      catch (e) { r.querySelector('[data-err]').textContent = e.message; }
    }));
  }
  async function leaving() {
    const d = await api('GET', '/api/admin/participation');
    const o = await api('GET', '/api/admin/overview');
    const reqs = d.items.filter(i => i.request), ended = d.items.filter(i => i.ended);
    const pill = st => `<span class="st-pill${STATE_L[st][1] ? ' st-pill--' + STATE_L[st][1] : ''}">${E(STATE_L[st][0])}</span>`;
    const sched = i => `<div class="st-scroll"><table class="st-table"><thead><tr><th>Information</th><th>Rule</th><th>Due</th><th>Status</th></tr></thead><tbody>${i.ended.schedule.map(x => `<tr>
      <td>${E(x.what)}${x.branches ? `<br><span class="st-muted">Audit branches: <code>${E(x.branches)}</code></span>` : ''}</td><td><span class="st-muted">${E(x.rule)}</span></td>
      <td>${x.due ? E(irishDay(new Date(x.due).toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' }))) : '—'}</td><td>${pill(x.state)}${x.done_at ? `<br><span class="st-muted">${E(irish(x.done_at))}</span>` : ''}</td></tr>`).join('')}</tbody></table></div>`;
    app.innerHTML = `<h1 class="st-h1">Leaving PlotArt</h1>
      <p class="st-sub">An artist can leave at any time. Ending participation removes their gallery from plotnua.ie (within ${d.rules ? d.rules.removal_days : 14} days), stops sign-in and enquiries, and fixes the deletion dates. Records are kept only as long as the agreement and privacy notice say, then deleted. Nothing here touches any other artist.</p>
      ${!d.installed ? '<div class="st-card" role="alert"><p style="margin:0"><b>Not installed yet.</b> This needs migration 0005.</p></div>' : ''}
      <div class="st-card ${d.deletion_enabled ? 'st-agr-ok' : 'st-agr-warn'}"><p style="margin:0"><b>Scheduled deletion is ${d.deletion_enabled ? 'ON' : 'OFF'} in this Studio.</b> ${d.deletion_enabled ? 'Due deletions run in the daily clean-up.' : 'Due deletions are shown here but nothing is deleted until it is switched on (a release step that needs your approval).'}</p></div>
      <section class="st-card"><h2>Requests to leave (${reqs.length})</h2>
        ${reqs.length ? `<ul class="st-works">${reqs.map(i => `<li class="st-work" style="grid-template-columns:minmax(0,1fr) auto"><div><p class="st-work-t">${E(i.display_name)}</p>
          <p class="st-work-s" style="margin:0">Asked ${E(irish(i.request.at))} · gallery to be removed by ${E(irishDay(new Date(i.request.due).toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' })))}${i.request.reason ? ` · “${E(i.request.reason)}”` : ''}</p></div>
          <a class="st-btn st-btn--solid st-btn--small" href="#end-${E(i.id)}" data-pick="${E(i.id)}">End participation</a></li>`).join('')}</ul>` : '<p class="st-muted">No open requests.</p>'}</section>
      <section class="st-card" id="endform" aria-labelledby="end-h"><h2 id="end-h">End participation</h2>
        <p class="st-muted">For an artist who asked to leave (in Studio or by email), or when you end it under the agreement. This can’t be undone from here.</p>
        <div class="st-two"><div>
          <div class="st-f"><label for="en-artist">Artist</label><select id="en-artist"><option value="">Choose…</option>${o.artists.filter(a => a.account_status !== 'ended').map(a => `<option value="${E(a.id)}" data-name="${E(a.display_name)}">${E(a.display_name)}${a.leave_requested_at ? ' (asked to leave)' : ''}</option>`).join('')}</select></div>
          <div class="st-row" style="gap:16px;flex-wrap:wrap;margin:0 0 12px"><label class="st-check"><input type="radio" name="en-src" value="artist_request" checked> The artist asked to leave</label><label class="st-check"><input type="radio" name="en-src" value="founder"> I’m ending it</label></div>
          <div class="st-f"><label for="en-told">If the artist told you by email: the date they did (Irish date)</label><input id="en-told" type="date"><p class="st-hint">The 14 days, 12 months and six years run from when the artist told PlotArt (agreement 10.1). Leave empty for a Studio request or if you are ending it.</p></div>
          <div class="st-f"><label for="en-reason">Reason</label><textarea id="en-reason" maxlength="280" style="min-height:70px" placeholder="e.g. Artist emailed on 6 November asking to leave"></textarea></div>
        </div><div>
          <p class="st-muted" id="en-what">Choose an artist to see exactly what will happen.</p>
          <div class="st-f"><label for="en-name">Type the artist’s name to confirm</label><input id="en-name" type="text" autocomplete="off"></div>
          <div class="st-actions"><button class="st-btn st-btn--solid" id="en-go">End participation</button></div><p class="st-err" id="en-err" role="alert"></p>
        </div></div></section>
      <section class="st-card"><h2>Ended (${ended.length})</h2>
        ${ended.length ? ended.map(i => `<div class="st-acc"><p class="st-acc-h"><b>${E(i.display_name)}</b> · ${i.ended.notice_at !== i.ended.at ? `told PlotArt ${E(irish(i.ended.notice_at))} · ` : ''}ended ${E(irish(i.ended.at))} by ${E(i.ended.by)} · ${i.ended.source === 'artist_request' ? 'the artist asked to leave' : 'ended by you'}${i.ended.reason ? ` · “${E(i.ended.reason)}”` : ''}</p>
          ${sched(i)}
          ${i.ended.schedule.find(x => x.key === 'originals').state !== 'done' ? `<div class="st-row" style="margin-top:10px;gap:10px;flex-wrap:wrap;align-items:end"><div class="st-f" style="margin:0;flex:1;min-width:240px"><label>Delete originals now (the artist asked for earlier deletion)</label><input type="text" data-er-reason="${E(i.id)}" placeholder="Reason"></div>
            <button class="st-btn st-btn--small st-btn--danger" data-erase="${E(i.id)}"${d.deletion_enabled ? '' : ' disabled title="Deletion is switched off"'}>Delete originals now</button></div><p class="st-err" data-er-err="${E(i.id)}"></p>` : ''}
          <details class="st-ck-d"><summary><span>Event log (${i.events.length})</span></summary><ul class="st-list">${i.events.map(e => `<li>${E(irish(e.at))} · ${E(e.kind.replace(/_/g, ' '))} · ${E(e.actor)}${e.reason ? ` · ${E(e.reason)}` : ''}</li>`).join('')}</ul></details></div>`).join('') : '<p class="st-muted">No artist has left.</p>'}</section>`;
    const sel = $('#en-artist');
    const what = () => { const a = o.artists.find(x => x.id === sel.value);
      $('#en-what').innerHTML = !a ? 'Choose an artist to see exactly what will happen.' : `<b>${E(a.display_name)}</b>: ${a.live_version ? 'their gallery is queued for removal from plotnua.ie now' : 'not published, so there is nothing to remove from plotnua.ie'}; pending submissions are withdrawn and nothing of theirs waits to publish; sign-in and enquiries stop. Original photographs and account details are deleted after 12 months; acceptance and enquiry records after 6 years. No other artist is affected.`; };
    sel.addEventListener('change', what);
    app.querySelectorAll('[data-pick]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); sel.value = b.dataset.pick; what(); $('#en-reason').focus(); $('#endform').scrollIntoView({ block: 'start' }); }));
    $('#en-go').addEventListener('click', async () => {
      $('#en-err').textContent = '';
      if (!sel.value) { $('#en-err').textContent = 'Choose the artist.'; return; }
      try { await api('POST', `/api/admin/artists/${sel.value}/end`, { confirm_name: $('#en-name').value, source: app.querySelector('input[name=en-src]:checked').value, reason: $('#en-reason').value, told_on: $('#en-told').value || undefined });
        say('Participation ended · gallery removal queued'); leaving(); }
      catch (e) { $('#en-err').textContent = e.message; }
    });
    app.querySelectorAll('[data-erase]').forEach(b => b.addEventListener('click', async () => {
      if (!b.dataset.sure) { b.dataset.sure = 1; b.textContent = 'Delete them permanently?'; return; }
      try { await api('POST', `/api/admin/artists/${b.dataset.erase}/erase-originals`, { confirm: true, reason: app.querySelector(`[data-er-reason="${b.dataset.erase}"]`).value }); say('Originals deleted'); leaving(); }
      catch (e) { app.querySelector(`[data-er-err="${b.dataset.erase}"]`).textContent = e.message; }
    }));
  }

  /* ---- Opportunities & delivery (development 13 Nov 2026): artists' expressions of interest, read-only here.
     Nothing on this page enrols an artist, changes an agreement, grants a permission, lists a work for hire or contacts anyone. */
  async function opportunities() {
    let d;
    try { d = await api('GET', '/api/admin/opportunities'); } catch (e) { app.innerHTML = `<div class="st-card"><h1 class="st-h1">Opportunities</h1><p class="st-muted">${E(e.message)}</p></div>`; return; }
    if (!d.installed) { app.innerHTML = '<h1 class="st-h1">Opportunities &amp; delivery</h1><section class="st-card"><p class="st-muted" style="margin:0">Not installed yet (migration 0009 has not run).</p></section>'; return; }
    const O = d.options, T = d.totals, f = { status: '', interest: '', county: '', reach: '', transport: '', general: '', how: '' };
    const provOpts = (sel, extra = '') => extra + Object.entries(O.provinces).map(([p, cs]) => `<optgroup label="${p}">${cs.map(c => `<option value="${c}"${c === sel ? ' selected' : ''}>${c}</option>`).join('')}</optgroup>`).join('');
    // Report 36 (0027): "Same as my general delivery" follows the artist's Profile; the effective placement counties are
    // then the general delivery counties (an artist abroad covering their own country has no Irish counties).
    const followsGeneral = i => i.prefs && i.prefs.placement_area === 'general';
    const placeCounties = i => followsGeneral(i) ? (i.general ? i.general.counties : []) : i.prefs.coverage_mode === 'anywhere' ? O.counties : i.prefs.coverage_mode === 'counties' ? i.prefs.coverage_counties : [];
    const trLabel = (i, k) => k === 'courier' && O.v27 && i.prefs.placement_area === null ? 'Courier or art transporter (answered before; not yet confirmed)' : O.transport_short[k];
    const coverage = p => {
      if (p.coverage_mode === 'anywhere') return 'Anywhere on the island';
      if (p.coverage_mode === 'ask') return 'Ask about each opportunity';
      if (p.coverage_mode !== 'counties') return '';
      const out = [];
      for (const [pv, cs] of Object.entries(O.provinces)) {
        const got = cs.filter(c => p.coverage_counties.includes(c));
        if (got.length === cs.length) out.push(`all ${pv}`); else out.push(...got);
      }
      return out.join(', ');
    };
    const isOnline = i => i.prefs && i.prefs.interests.includes('online_only');
    const PUBK = ['exhibitions', 'living_gallery', 'art_for_hire', 'mobile_gallery', 'venues', 'commissions', 'talks'];
    const pub = p => PUBK.filter(k => p.interests.includes(k));
    const match = i => {
      const p = i.prefs;
      if (f.status === 'answered' && !p) return false;
      if (f.status === 'unanswered' && p) return false;
      if (f.status === 'online' && !isOnline(i)) return false;
      if (f.status === 'care' && !(p && p.care_condition)) return false;
      if (f.interest && !(p && p.interests.includes(f.interest))) return false;
      if (f.county === '_none' ? !(p && !p.artwork_county) : f.county && !(p && p.artwork_county === f.county)) return false;
      // Report 35: three separate questions. Placement area (where they'd deliver and collect for a temporary placement),
      // placement transport (how), and general delivery to buyers and hirers (the Profile). Never merged.
      if (f.reach) {
        if (!p) return false;
        if (f.reach === 'ask') { if (followsGeneral(i) || p.coverage_mode !== 'ask') return false; }
        else if (f.reach === 'anywhere') { if (placeCounties(i).length !== O.counties.length) return false; }
        else if (f.reach === 'general') { if (!followsGeneral(i)) return false; }
        else if (!placeCounties(i).includes(f.reach)) return false;
      }
      if (f.transport && !(p && p.transport.includes(f.transport))) return false;
      if (f.general) {
        const g = i.general;
        const ok = f.general === '_none' ? g && g.scope === 'none' : f.general === '_unanswered' ? !g
          : f.general === '_collection' || f.general === '_arrangement' ? g && g.scope === 'none' && g.methods === f.general.slice(1)
          : f.general === '_legacy' ? g && g.scope === 'none' && !g.methods : g && g.counties.includes(f.general);
        if (!ok) return false;
      }
      if (f.how && !(i.general && i.general.methods && i.general.scope !== 'none' && i.general.methods.split(',').includes(f.how))) return false;
      return true;
    };
    const row = i => {
      const p = i.prefs, who = `<b>${E(i.display_name)}</b>${TB(i.id)}${i.founding_number ? ` <span class="st-muted">· F${String(i.founding_number).padStart(2, '0')}</span>` : ''}${i.account_status !== 'active' ? ` <span class="st-muted">· ${E(i.account_status)}</span>` : ''}`;
      if (!p) return `<li class="st-opp-row is-none"><div>${who}</div><div><span class="st-pill">Not answered yet</span></div></li>`;
      if (isOnline(i)) return `<li class="st-opp-row"><div>${who}</div><div><span class="st-pill st-pill--warn">Online only for now</span>${p.artwork_county ? `<span class="st-opp-k">Artwork in Co. ${E(p.artwork_county)}</span>` : ''}${p.note ? `<p class="st-opp-note">${E(p.note)}</p>` : ''}</div><div class="st-muted st-opp-when">${E(when(p.updated_at))}</div></li>`;
      return `<li class="st-opp-row"><div>${who}</div>
        <div><div class="st-chips" style="margin:0 0 6px">${p.interests.map(k => `<span class="st-chip">${E(O.interest_short[k])}</span>`).join('')}${p.care_condition ? `<span class="st-chip st-chip--care" title="${E(O.care ? O.care.label : '')}">${E(O.care ? O.care.short : 'Depends on care, handling and insurance')}</span>` : ''}</div>
          ${O.public ? `<span class="st-opp-k">Public gallery: ${p.public_display === true ? (p.public_notice === 'PA-OPP-FOUNDER-CONFIRMED-2026-11' ? 'shown (agreement obtained by the founder; only while the gallery is published)' : 'shown (only while the gallery is published)') : p.public_display === false ? 'kept private' : '<i>not confirmed yet: not shown</i>'}</span>` : ''}
          ${O.public && p.public_display === null && pub(p).length ? `<div class="st-opp-fc" style="margin:8px 0"><label class="st-check"><input type="checkbox" data-fc="${E(i.id)}"> <span>I personally obtained ${E(i.display_name)}’s agreement to show these publicly: ${pub(p).map(k => E(O.interest_short[k])).join(', ')}</span></label>
            <button type="button" class="st-btn st-btn--small" data-fcgo="${E(i.id)}" disabled style="margin-top:6px">Show these publicly</button></div>` : ''}
          <span class="st-opp-k">Artwork kept in: ${p.artwork_county ? `Co. ${E(p.artwork_county)}` : '<i>not given</i>'}</span>
          <span class="st-opp-k">Placements, deliver &amp; collect: ${followsGeneral(i) ? `Same as general delivery (${i.general ? E(i.general.line) : 'no general delivery'})` : p.coverage_mode ? E(coverage(p)) : '<i>not given</i>'}${O.v27 && p.placement_area === null && p.coverage_mode ? ' <span class="st-muted">· not yet confirmed</span>' : ''}</span>
          <span class="st-opp-k">Placements, transport: ${p.transport.length ? p.transport.map(k => E(trLabel(i, k))).join(', ') : '<i>not given</i>'}</span>
          ${d.general_installed ? `<span class="st-opp-k">General delivery (sales &amp; hire): ${i.general ? E(i.general.line) + (i.general.how ? ` · ${E(i.general.how)}` : '') : '<i>not answered</i>'}</span>` : ''}
          ${p.note ? `<p class="st-opp-note">${E(p.note)}</p>` : ''}</div>
        <div class="st-muted st-opp-when">${E(when(p.updated_at))}</div></li>`;
    };
    app.innerHTML = `
      <h1 class="st-h1">Opportunities &amp; delivery</h1>
      <p class="st-sub">What artists have said they’d be open to, where their work is based and how it could reach a venue. These are expressions of interest only: talk to the artist before arranging anything.</p>
      <div class="st-kpis st-kpis--fit">
        <div class="st-kpi"><b>${T.answered}</b><span>answered</span></div>
        <div class="st-kpi"><b>${T.unanswered}</b><span>not answered yet</span></div>
        <div class="st-kpi"><b>${T.online_only}</b><span>online only for now</span></div>
        ${O.care ? `<div class="st-kpi"><b>${T.care_condition}</b><span>depend on care, handling and insurance</span></div>` : ''}
        ${O.public ? `<div class="st-kpi"><b>${T.shown}</b><span>shown publicly</span></div><div class="st-kpi"><b>${T.undecided}</b><span>not confirmed yet</span></div>` : ''}
        <div class="st-kpi"><b>${T.artists}</b><span>artists in Studio</span></div>
      </div>
      <section class="st-card">
        <h3 class="st-opp-h3">Interest by opportunity</h3>
        <div class="st-opts st-opts--sm" style="margin-top:6px">${Object.keys(O.interests).filter(k => k !== 'online_only').map(k => `<button type="button" class="st-opt st-opt--sm st-opt--count" data-int="${k}" aria-pressed="false">${E(O.interest_short[k])} <b>${T.by_interest[k]}</b></button>`).join('')}</div>
        <div class="st-opp-filters">
          <div class="st-f"><label for="of-status">Answers</label><select id="of-status"><option value="">Everyone</option><option value="answered">Answered</option><option value="unanswered">Not answered yet</option><option value="online">Online only for now</option>${O.care ? '<option value="care">Depends on care, handling and insurance</option>' : ''}</select></div>
          <div class="st-f"><label for="of-int">Interested in</label><select id="of-int"><option value="">Any opportunity</option>${Object.keys(O.interests).filter(k => k !== 'online_only').map(k => `<option value="${k}">${E(O.interest_short[k])}</option>`).join('')}</select></div>
          <div class="st-f"><label for="of-county">Artwork kept in</label><select id="of-county">${provOpts('', '<option value="">Any county</option><option value="_none">Not given</option>')}</select></div>
          <div class="st-f"><label for="of-reach">Placements: deliver &amp; collect in</label><select id="of-reach"><option value="">Any</option><option value="anywhere">Anywhere on the island</option><option value="ask">Ask about each opportunity</option>${O.v27 ? '<option value="general">Same as their general delivery</option>' : ''}${provOpts('')}</select></div>
          <div class="st-f"><label for="of-tr">Placements: transport</label><select id="of-tr"><option value="">Any</option>${Object.keys(O.transport_short).map(k => `<option value="${k}">${E(O.transport_short[k])}</option>`).join('')}</select></div>
          ${d.general_installed ? `<div class="st-f"><label for="of-gen">General delivery (sales &amp; hire) to</label><select id="of-gen">${provOpts('', '<option value="">Any</option>' + (d.transport_installed ? '<option value="_collection">No delivery: buyer or hirer collects</option><option value="_arrangement">By arrangement</option><option value="_legacy">No delivery or by arrangement (answered before)</option>' : '<option value="_none">No delivery: collection or by arrangement</option>') + '<option value="_unanswered">Not answered</option>')}</select></div>` : ''}
          ${d.transport_installed ? `<div class="st-f"><label for="of-how">General delivery: how</label><select id="of-how"><option value="">Any</option><option value="personal">Personal delivery</option><option value="courier">Standard courier</option><option value="specialist">Specialist art transport</option></select></div>` : ''}
        </div>
        <p class="st-muted" style="margin:0" aria-live="polite"><span id="of-n"></span> <button type="button" class="st-linkbtn" id="of-reset" hidden>Clear filters</button></p>
      </section>
      <ul class="st-opp-list" id="of-list"></ul>
      <p class="st-muted">“Placements: deliver &amp; collect in” a county includes artists who said “Anywhere on the island”; it is about temporary placements only. “General delivery” is what the artist set in their Profile for selling or hiring a work, and says nothing about placements.${O.care ? ' Care, handling and insurance arrangements are discussed for every placement: an artist who left that box unticked has not waived them.' : ''}</p>`;
    const draw = () => {
      const rows = d.items.filter(match);
      $('#of-list').innerHTML = rows.length ? rows.map(row).join('') : '<li class="st-opp-row is-none"><div class="st-muted">No artists match these filters.</div></li>';
      $('#of-n').textContent = `Showing ${rows.length} of ${d.items.length} artists.`;
      $('#of-reset').hidden = !Object.values(f).some(Boolean);
      app.querySelectorAll('[data-int]').forEach(b => b.setAttribute('aria-pressed', String(f.interest === b.dataset.int)));
    };
    $('#of-list').addEventListener('change', e => { const c = e.target.closest('[data-fc]'); if (c) app.querySelector(`[data-fcgo="${c.dataset.fc}"]`).disabled = !c.checked; });
    $('#of-list').addEventListener('click', async e => {
      const b = e.target.closest('[data-fcgo]'); if (!b || b.disabled) return;
      const it = d.items.find(x => x.id === b.dataset.fcgo); b.disabled = true;
      try { await api('POST', '/api/admin/opportunities/confirm', { artist_id: it.id, interests: it.prefs.interests, confirm: true }); await opportunities(); }
      catch (err) { b.disabled = false; b.insertAdjacentHTML('afterend', `<p class="st-err" role="alert">${E(err.message)}</p>`); }
    });
    const bind = (id, k) => $(id).addEventListener('change', e => { f[k] = e.target.value; draw(); });
    bind('#of-status', 'status'); bind('#of-int', 'interest'); bind('#of-county', 'county'); bind('#of-reach', 'reach'); bind('#of-tr', 'transport'); if ($('#of-gen')) bind('#of-gen', 'general'); if ($('#of-how')) bind('#of-how', 'how');
    locationOverview();
    app.querySelectorAll('[data-int]').forEach(b => b.addEventListener('click', () => { f.interest = f.interest === b.dataset.int ? '' : b.dataset.int; $('#of-int').value = f.interest; draw(); }));
    $('#of-reset').addEventListener('click', () => { Object.keys(f).forEach(k => { f[k] = ''; }); ['#of-status', '#of-int', '#of-county', '#of-reach', '#of-tr', '#of-gen', '#of-how'].forEach(s => { if ($(s)) $(s).value = ''; }); draw(); });
    draw();
  }

  /* Featured Artists (founder brief 17 Nov 2026; was the Homepage tab): up to six published artists for the top of the
     Artists' Gallery, each shown with the published artwork the founder chooses, in her order. Arrange, preview, then save;
     saving publishes through the usual protected route. Only published work can be chosen, and each artist appears once.
     The complete collection below the section is never changed from here. */

  /* ---- Where artists are based (Phase C, Track C, 25 Nov 2026): the founder's read-only overview of each artist's location
     and delivery coverage (GET /api/admin/locations), under Opportunities & delivery. Shown only once migration 0025 has
     run. A county filter lists artists based there, then, labelled separately, artists who deliver there. Never an address. */
  async function locationOverview() {
    let d; try { d = await api('GET', '/api/admin/locations'); } catch { return; }
    if (!d.installed || location.pathname.replace(/\/$/, '') !== '/admin/opportunities') return;
    const box = document.createElement('section'); box.className = 'st-card st-loc-ov'; box.setAttribute('aria-labelledby', 'lo-h');
    app.appendChild(box);
    const row = a => `<li class="st-gm-person"><div><p class="st-work-t">${E(a.name)}${TB(a.id)}</p>
      <p class="st-work-s">${a.place ? E(a.place) + (a.public ? ' · they chose to show it' : ' · private') : a.county ? 'Co. ' + E(a.county) + ' (profile county; location not confirmed yet)' : 'Not given yet'}</p>
      <p class="st-work-s">${a.delivery ? E(a.delivery) + (a.delivery_public ? ' · they chose to show it' : ' · private') : 'No delivery areas given'}</p></div></li>`;
    async function draw(county) {
      if (county) d = await api('GET', '/api/admin/locations?county=' + encodeURIComponent(county)); else d = await api('GET', '/api/admin/locations');
      const based = d.artists.filter(a => !county || a.relation === 'based'), del = county ? d.artists.filter(a => a.relation === 'delivers') : [];
      box.innerHTML = `<h3 class="st-opp-h3" id="lo-h">Where artists are based</h3>
        <p class="st-muted" style="margin:0 0 10px">From each artist’s Studio: where they live and work now, and where they can deliver. Read-only. Delivery areas stay private on the public site until public delivery is switched on.</p>
        <div class="st-f" style="max-width:320px"><label for="lo-c">County</label><select id="lo-c"><option value="">All artists</option>${d.counties.map(c => `<option${c === county ? ' selected' : ''}>${E(c)}</option>`).join('')}</select></div>
        ${county ? `<h4 class="st-gm-h3">Based in Co. ${E(county)} (${based.length})</h4>` : ''}
        <ul class="st-gm-list">${based.map(row).join('') || '<li class="st-muted" style="padding:10px 0">Nobody.</li>'}</ul>
        ${county ? `<h4 class="st-gm-h3">Deliver to Co. ${E(county)} (${del.length})</h4><ul class="st-gm-list">${del.map(row).join('') || '<li class="st-muted" style="padding:10px 0">Nobody.</li>'}</ul>` : ''}`;
      box.querySelector('#lo-c').addEventListener('change', e => draw(e.target.value));
    }
    await draw('');
  }

  async function featured() {
    let d = await api('GET', '/api/admin/featured');
    if (!d.installed) { app.innerHTML = '<h1 class="st-h1">Featured Artists</h1><section class="st-card"><p class="st-muted">Featured Artists isn’t set up yet (migration 0016).</p></section>'; return; }
    let sel = d.items.filter(i => i.shown).map(i => ({ artist_id: i.artist_id, artwork_id: i.artwork_id })), msg = '';
    // earlier homepage choices (single artworks, or an artist listed twice) are shown as artists and need one save to confirm
    const earlier = d.items.some(i => i.earlier_kind !== 'artist' || i.repeat);
    let dirty = earlier;
    const dropped = d.items.filter(i => !i.shown && !i.repeat).length;
    let choosing = null;   // { artist_id, index, replace, scroll }: choosing the artwork that represents an artist (index: an existing card)
    let replacing = null;  // index of the card whose artist is being replaced
    const gal = id => d.galleries.find(g => g.artist_id === id);
    const info = it => { const g = gal(it.artist_id); const w = g && g.works.find(x => x.id === it.artwork_id); return w ? { g, w } : null; };
    const at = id => sel.findIndex(s => s.artist_id === id);
    const img = w => `<img src="/api/admin/featured/image/${E(w.image.id)}" alt="${E(w.image.alt)}" loading="lazy">`;
    const card = (it, i) => { const x = info(it); if (!x) return ''; return `<li class="st-fa-card${replacing === i ? ' st-fa-card--replacing' : ''}">
        <span class="st-hp-frame">${img(x.w)}</span>
        <p class="st-fa-credit"><i>${E(x.w.title)}</i>${x.w.year ? ', ' + E(x.w.year) : ''} · ${E(x.g.display_name)}</p>
        <p class="st-hp-t">${E(x.g.display_name)}</p>${x.g.practice ? `<p class="st-fa-prac">${E(x.g.practice)}</p>` : ''}
        ${x.g.intro ? `<p class="st-fa-intro">${E(x.g.intro)}</p>` : '<p class="st-fa-intro st-muted">No biography published: no introduction is shown.</p>'}
        <p class="st-fa-view">View Gallery →</p>
        <div class="st-row st-fa-ctl"><button class="st-btn st-btn--small" data-up="${i}" aria-label="Move ${E(x.g.display_name)} earlier"${i === 0 ? ' disabled' : ''}>↑</button><button class="st-btn st-btn--small" data-down="${i}" aria-label="Move ${E(x.g.display_name)} later"${i === sel.length - 1 ? ' disabled' : ''}>↓</button>
        <button class="st-btn st-btn--small" data-change="${i}">Change artwork</button><button class="st-btn st-btn--small" data-replace="${i}"${replacing === i ? ' aria-pressed="true"' : ''}>${replacing === i ? 'Choosing…' : 'Replace'}</button><button class="st-btn st-btn--small" data-rm="${i}">Remove</button></div></li>`; };
    function draw() {
      const full = sel.length >= d.max;
      const rname = replacing !== null && info(sel[replacing]) ? info(sel[replacing]).g.display_name : '';
      app.innerHTML = `<h1 class="st-h1">Featured Artists</h1>
        <p class="st-sub">Choose up to ${d.max} published artists to feature at the top of the Artists’ Gallery, the artwork that represents each, and their order. Each artist appears once and stays in the complete collection below. The introduction is the start of the artist’s own published biography. Only published work can be chosen; anything withdrawn or unpublished drops out by itself. Saving changes nothing in any artist’s gallery or in the collection, and publishes through the usual protected route.</p>
        ${earlier ? '<p class="st-card st-fa-notice">Your earlier homepage choices are listed here as featured artists, each shown with the artwork you chose for them. Review them, then save to confirm the selection for the Artists’ Gallery.</p>' : ''}
        ${dropped ? `<p class="st-muted">${dropped} earlier choice${dropped > 1 ? 's are' : ' is'} no longer published and won’t be shown.</p>` : ''}
        <div class="st-go-bar"><span class="st-muted" id="hp-state">${msg || (dirty ? 'Unsaved changes' : 'Saved')}</span><button class="st-btn st-btn--solid" id="hp-save"${dirty ? '' : ' disabled'}>Save and publish</button></div>
        <section class="st-card"><h2>Preview · Featured Artists in the Artists’ Gallery (${sel.length} of ${d.max})</h2>
          <p class="st-fa-head"><span class="st-fa-eyebrow">Selected by PlotArt</span><b>Featured Artists</b><span>A changing selection of artists and their work.</span></p>
          ${sel.length ? `<ol class="st-hp-grid st-fa-grid">${sel.map(card).join('')}</ol>` : '<p class="st-muted">No artists featured. The Artists’ Gallery shows the complete collection only until you choose someone.</p>'}</section>
        <section class="st-card" style="margin-top:18px"><h2>${replacing !== null ? `Choose the artist to feature in place of ${E(rname)} <button class="st-btn st-btn--small" data-cancel-replace="1">Cancel</button>` : 'Published artists you can feature'}</h2>
          ${d.galleries.map(g => { const ai = at(g.artist_id), ch = choosing && choosing.artist_id === g.artist_id, rep = ai >= 0 ? sel[ai].artwork_id : null;
            const can = ai < 0 && (!full || replacing !== null);
            return `<div class="st-hp-gal${ch ? ' st-hp-gal--choosing' : ''}"><div class="st-row" style="justify-content:space-between"><div><p class="st-work-t" style="margin:0">${E(g.display_name)}</p>${g.practice ? `<p class="st-muted" style="margin:2px 0 0">${E(g.practice)}</p>` : ''}</div>
            ${ch ? `<button class="st-btn st-btn--small" data-cancel="1">Cancel</button>` : `<button class="st-btn st-btn--small" data-artist="${E(g.artist_id)}"${can ? '' : ' disabled'}>${ai >= 0 ? 'Featured' : replacing !== null ? 'Feature instead' : 'Feature artist'}</button>`}</div>
            ${ch ? `<p class="st-hp-note">Choose the published artwork that represents ${E(g.display_name)}. The card links to their gallery; their own gallery and order of works don’t change.</p>
            <ul class="st-hp-pick">${g.works.map(w => `<li>${img(w)}<span>${E(w.title)}${rep === w.id ? '<br><span class="st-muted">Represents the artist</span>' : ''}</span>
              <button class="st-btn st-btn--small" data-rep="${E(w.id)}"${rep === w.id ? ' disabled' : ''}>${rep === w.id ? 'Chosen' : 'Use this artwork'}</button></li>`).join('')}</ul>` : ''}</div>`; }).join('') || '<p class="st-muted">No published galleries yet.</p>'}</section>`;
      if (choosing && choosing.scroll) { const el = app.querySelector('.st-hp-gal--choosing'); if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' }); choosing.scroll = false; }
    }
    const change = f => { f(); dirty = true; msg = ''; draw(); };
    app.addEventListener('click', async function onClick(e) {
      if (location.pathname.replace(/\/$/, '') !== '/admin/featured') { app.removeEventListener('click', onClick); return; }
      const b = e.target.closest('button'); if (!b || b.disabled) return;
      if (b.dataset.up) change(() => { const i = +b.dataset.up; [sel[i - 1], sel[i]] = [sel[i], sel[i - 1]]; });
      else if (b.dataset.down) change(() => { const i = +b.dataset.down; [sel[i + 1], sel[i]] = [sel[i], sel[i + 1]]; });
      else if (b.dataset.rm) change(() => { sel.splice(+b.dataset.rm, 1); choosing = null; replacing = null; });
      else if (b.dataset.replace) { replacing = replacing === +b.dataset.replace ? null : +b.dataset.replace; choosing = null; draw(); }
      else if (b.dataset.cancelReplace) { replacing = null; choosing = null; draw(); }
      else if (b.dataset.artist) { choosing = { artist_id: b.dataset.artist, index: replacing, replace: replacing !== null, scroll: true }; draw(); }
      else if (b.dataset.change) { const i = +b.dataset.change; replacing = null; choosing = { artist_id: sel[i].artist_id, index: i, replace: false, scroll: true }; draw(); }
      else if (b.dataset.cancel) { choosing = null; draw(); }
      else if (b.dataset.rep && choosing) change(() => { const c = choosing; choosing = null; replacing = null;
        const item = { artist_id: c.artist_id, artwork_id: b.dataset.rep };
        if (c.index === null) sel.push(item); else sel[c.index] = item; });
      else if (b.id === 'hp-save') {
        b.disabled = true;
        try {
          const r = await api('PUT', '/api/admin/featured', { items: sel.map(s => ({ artist_id: s.artist_id, artwork_id: s.artwork_id })) });
          d = r; dirty = false; msg = r.changed ? (r.publish === 'requested' ? 'Saved · publishing to the Artists’ Gallery has started' : 'Saved · it will go live on the next publishing run') : 'Saved · nothing changed';
        } catch (err) { msg = err.message; }
        draw();
      }
    });
    draw();
  }


  let TEST = new Set();
  const TB = id => TEST.has(id) ? ' <span class="st-test-badge" title="Internal test account: never published, never counted">TEST</span>' : '';
  /* ---- Three galleries (Phase C, Track C, 25 Nov 2026): the founder's management of Contemporary, Spaces and Being.
     Everything here calls the Phase B routes (galleries.js); nothing new is decided in the browser. Membership and placement
     need the founder's approval AND the artist's acceptance; Artists in Focus and the order are the founder's alone. Opening a
     gallery here records the decision in the Studio only: the public page opens in a separate, approved website release. */
  async function galleries() {
    let d = await api('GET', '/api/admin/galleries'), g = sessionStorage.getItem('pa-gal') || 'spaces', msg = '';
    const TITLE = { contemporary: 'Contemporary', spaces: 'Spaces', being: 'Being' };
    const STATUS = { open: 'Open', in_preparation: 'In preparation', paused: 'Paused' };
    const MEMBER = { live: 'Member', founder_approved: 'Invited · waiting for the artist', artist_accepted: 'Asked to join · waiting for you',
      proposed: 'Proposed · waiting for you', declined: 'Declined by the artist', withdrawn: 'Left or withdrawn', refused: 'Not accepted' };
    const PLACE = { live: 'In this gallery', founder_approved: 'Offered · waiting for the artist', artist_accepted: 'Proposed by the artist · waiting for you',
      proposed: 'Proposed', declined: 'Declined by the artist', withdrawn: 'Withdrawn', refused: 'Not accepted' };
    const SCOPE = { homepage_feature: 'Homepage feature', promotional_campaign: 'Promotional campaign', social_media: 'Social media', editorial_feature: 'Editorial feature', video_feature: 'Video feature' };
    const name = id => (d.artists.find(a => a.id === id) || d.memberships.find(m => m.artist_id === id) || {}).display_name || id;
    const pubOf = id => d.published.find(p => p.artist_id === id);
    const img = w => w && w.image ? `<img src="/api/admin/featured/image/${E(w.image.id)}" alt="" loading="lazy">` : '<span class="st-gm-noimg" aria-hidden="true"></span>';
    let order = null, focus = null, dirtyO = false, dirtyF = false, inv = { artist_id: '', source: 'founder_curation', application_ref: '' };
    const G = () => d.galleries.find(x => x.gallery_id === g);
    function load() {
      const x = G();
      order = (x.order || []).map(o => o.artist_id);
      for (const m of x.members) if (!order.includes(m.artist_id) && !(g === 'contemporary' && d.held.includes(m.artist_id))) order.push(m.artist_id);
      focus = (x.features || []).map(f => ({ artist_id: f.artist_id, artwork_id: f.artwork_id }));
      dirtyO = dirtyF = false;
    }
    const rows = st => d.memberships.filter(m => m.gallery_id === g && st.includes(m.state));
    const placeOf = (wid) => d.placements.find(p => p.gallery_id === g && p.artwork_id === wid);
    function statusCard(x) {
      const isNew = g !== 'contemporary';
      const bar = (n, t) => t ? `<span class="st-gm-meter" role="img" aria-label="${n} of ${t}"><i style="width:${Math.min(100, Math.round(100 * n / t))}%"></i></span>` : '';
      return `<section class="st-card st-gm-status"><div class="st-gm-head"><h2>${TITLE[g]}</h2><span class="st-chip ${x.status === 'open' ? 'st-chip--live' : 'st-chip--light'}">${STATUS[x.status]}</span></div>
        ${isNew ? `<div class="st-gm-ready">
          <div><p class="st-lab">Artists</p><p class="st-gm-num"><b>${x.live_artists}</b> of ${x.target_artists}</p>${bar(x.live_artists, x.target_artists)}</div>
          <div><p class="st-lab">Works</p><p class="st-gm-num"><b>${x.live_works}</b> of ${x.target_works}</p>${bar(x.live_works, x.target_works)}</div>
          <form class="st-gm-targets" data-targets novalidate><p class="st-lab">Targets (advisory)</p>
            <label>Artists <input class="st-in" type="number" min="0" max="500" name="target_artists" value="${x.target_artists}" inputmode="numeric"></label>
            <label>Works <input class="st-in" type="number" min="0" max="5000" name="target_works" value="${x.target_works}" inputmode="numeric"></label>
            <button class="st-btn st-btn--small" type="submit">Save targets</button></form></div>
          <p class="st-muted st-gm-note">Counts include only published artists and works placed live in ${TITLE[g]}. ${x.status === 'open' ? `Opened ${when(x.opened_at)}.` : ''} Opening records your decision in the Studio; the public ${TITLE[g]} page opens only in a separate website release you approve.</p>
          <div class="st-row">${x.status !== 'open' ? `<button class="st-btn st-btn--solid st-btn--small" data-status="open">Open ${TITLE[g]}…</button>` : ''}
            ${x.status === 'open' ? '<button class="st-btn st-btn--small" data-status="paused">Pause</button>' : ''}
            ${x.status !== 'in_preparation' ? '<button class="st-btn st-btn--small" data-status="in_preparation">Back to preparation</button>' : ''}</div>`
        : `<p class="st-muted">Always open. Every artist is a member unless taken out, and every published work appears unless taken out here. Positions 01–25 stay in <a href="/admin/gallery">Gallery order</a>; Artists in Focus stays in <a href="/admin/featured">Featured Artists</a>.</p>
          <p class="st-gm-num"><b>${x.live_artists}</b> published artists · <b>${x.live_works}</b> works</p>`}</section>`;
    }
    function membersCard() {
      const reqs = rows(['artist_accepted', 'proposed']), wait = rows(['founder_approved']), closed = rows(['declined', 'withdrawn', 'refused']);
      const live = G().members, liveIds = new Set(live.map(m => m.artist_id));
      const unpub = rows(['live']).filter(m => !liveIds.has(m.artist_id));
      const can = d.artists.filter(a => { const r = d.memberships.find(m => m.gallery_id === g && m.artist_id === a.id); return !r || ['declined', 'withdrawn', 'refused'].includes(r.state); })
        .filter(a => g !== 'contemporary' || d.memberships.some(m => m.artist_id === a.id));   // Contemporary: only someone taken out can be invited back
      const li = (id, state, acts, extra = '') => `<li class="st-gm-person"><div><p class="st-work-t">${E(name(id))}${TB(id)}</p><p class="st-work-s">${E(MEMBER[state] || state)}${extra}</p></div><div class="st-row">${acts}</div></li>`;
      return `<section class="st-card"><h2>Artists</h2>
        ${reqs.length ? `<h3 class="st-gm-h3">Asked to join (${reqs.length})</h3><ul class="st-gm-list">${reqs.map(m => li(m.artist_id, m.state, `<button class="st-btn st-btn--solid st-btn--small" data-m="approve" data-a="${m.artist_id}">Approve</button><button class="st-btn st-btn--small" data-m="refuse" data-a="${m.artist_id}">Don’t accept</button>`)).join('')}</ul>` : ''}
        <h3 class="st-gm-h3">Members (${live.length + unpub.length})</h3>
        ${live.length + unpub.length ? `<ul class="st-gm-list">${live.map(m => li(m.artist_id, 'live', `<button class="st-btn st-btn--small" data-m="withdraw" data-a="${m.artist_id}">${g === 'contemporary' ? 'Remove from Contemporary…' : 'Withdraw…'}</button>`, ` · ${m.works} ${m.works === 1 ? 'work' : 'works'} shown`)).join('')}
          ${unpub.map(m => li(m.artist_id, 'live', `<button class="st-btn st-btn--small" data-m="withdraw" data-a="${m.artist_id}">Withdraw…</button>`, ' · gallery not published yet')).join('')}</ul>` : `<p class="st-muted">No members yet. Nobody is added to ${TITLE[g]} automatically.</p>`}
        ${wait.length ? `<h3 class="st-gm-h3">Invited (${wait.length})</h3><ul class="st-gm-list">${wait.map(m => li(m.artist_id, m.state, `<button class="st-btn st-btn--small" data-m="withdraw" data-a="${m.artist_id}">Cancel invitation</button>`, ` · ${when(m.founder_approved_at)}`)).join('')}</ul>` : ''}
        <form class="st-gm-invite" data-invite novalidate><h3 class="st-gm-h3">Invite an artist to ${TITLE[g]}</h3>
          <div class="st-gm-invite-row"><div class="st-f"><label for="gm-who">Artist</label><select id="gm-who" name="artist_id"><option value="">Choose…</option>${can.map(a => `<option value="${a.id}"${a.id === inv.artist_id ? ' selected' : ''}>${E(a.display_name)}${TEST.has(a.id) ? ' (TEST)' : ''}${a.account_status === 'invited' ? ' (not signed in yet)' : ''}</option>`).join('')}</select></div>
          <div class="st-f"><label for="gm-src">How</label><select id="gm-src" name="source">${[['founder_curation', 'Your curation'], ['founder_invitation', 'Invitation'], ['application', 'From an application']].map(([k, v]) => `<option value="${k}"${k === inv.source ? ' selected' : ''}>${v}</option>`).join('')}</select></div>
          <div class="st-f" data-ref${inv.source === 'application' ? '' : ' hidden'}><label for="gm-ref">Application reference</label><input id="gm-ref" type="text" name="application_ref" value="${E(inv.application_ref)}" placeholder="PA-AP-… or F25-…" autocomplete="off" spellcheck="false"></div></div>
          <p class="st-muted st-gm-note">The artist sees the invitation in their Studio and chooses whether to accept. No email is sent.</p>
          <button class="st-btn st-btn--solid st-btn--small" type="submit"${can.length ? '' : ' disabled'}>Invite</button></form>
        ${closed.length ? `<details class="st-gm-closed"><summary>Earlier decisions (${closed.length})</summary><ul class="st-gm-list">${closed.map(m => li(m.artist_id, m.state, '', m.closed_at ? ` · ${when(m.closed_at)}` : '')).join('')}</ul></details>` : ''}</section>`;
    }
    function worksCard() {
      const members = G().members.map(m => pubOf(m.artist_id)).filter(Boolean);
      if (g === 'contemporary') {
        const pubs = d.published.filter(p => G().members.some(m => m.artist_id === p.artist_id) || d.placements.some(x => x.gallery_id === 'contemporary' && x.artist_id === p.artist_id));
        return `<section class="st-card"><h2>Works</h2><p class="st-muted">Every published work is in Contemporary unless you take it out. Taking a work out never changes the artist’s own gallery.</p>
          ${pubs.map(p => `<details class="st-gm-artist"><summary>${E(p.display_name)} <span class="st-muted">· ${p.works.length}</span></summary><ul class="st-gm-works">${p.works.map(w => { const out = placeOf(w.id);
            return `<li class="st-gm-work">${img(w)}<div><p class="st-work-t">${E(w.title)}</p><p class="st-work-s">${out ? 'Taken out of Contemporary' : 'In Contemporary'}</p></div>
            <button class="st-btn st-btn--small" data-w="${out ? 'restore' : 'withdraw'}" data-id="${w.id}">${out ? 'Put back' : 'Take out…'}</button></li>`; }).join('')}</ul></details>`).join('') || '<p class="st-muted">No published galleries yet.</p>'}</section>`;
      }
      return `<section class="st-card"><h2>Works</h2><p class="st-muted">Only members’ published works can be placed. You offer a work and the artist accepts it, or the artist proposes one and you approve it.</p>
        ${members.length ? members.map(p => `<details class="st-gm-artist" open><summary>${E(p.display_name)}</summary><ul class="st-gm-works">${p.works.map(w => { const pl = placeOf(w.id), st = pl ? pl.state : null;
          const acts = !st || ['declined', 'withdrawn', 'refused'].includes(st) ? `<button class="st-btn st-btn--small" data-w="place" data-id="${w.id}">Offer for ${TITLE[g]}</button>`
            : st === 'artist_accepted' || st === 'proposed' ? `<button class="st-btn st-btn--solid st-btn--small" data-w="place" data-id="${w.id}">Approve</button><button class="st-btn st-btn--small" data-w="refuse" data-id="${w.id}">Don’t accept</button>`
            : `<button class="st-btn st-btn--small" data-w="withdraw" data-id="${w.id}">${st === 'live' ? 'Withdraw…' : 'Cancel offer'}</button>`;
          return `<li class="st-gm-work">${img(w)}<div><p class="st-work-t">${E(w.title)}${w.year ? ', ' + E(w.year) : ''}</p><p class="st-work-s">${st ? E(PLACE[st]) : 'Not in ' + TITLE[g]}</p></div><div class="st-row">${acts}</div></li>`; }).join('')}</ul></details>`).join('')
          : `<p class="st-muted">Works can be placed once an artist is a member and their gallery is published.</p>`}</section>`;
    }
    function orderCard() {
      const x = G();
      return `<section class="st-card"><h2>Order</h2><p class="st-muted">${g === 'contemporary' ? 'Contemporary members without one of the 25 founding positions, from position 26. Positions 01–25 stay in Gallery order.' : `The order of artists in ${TITLE[g]}. Only members appear; nobody moves automatically.`}</p>
        ${order.length ? `<ol class="st-gm-order">${order.map((id, i) => `<li><span class="st-gm-pos">${String((g === 'contemporary' ? 26 : 1) + i).padStart(2, '0')}</span><span class="st-gm-oname">${E(name(id))}${TB(id)}</span>
          <span class="st-row"><button class="st-btn st-btn--small" data-o="up" data-i="${i}" aria-label="Move ${E(name(id))} earlier"${i ? '' : ' disabled'}>↑</button><button class="st-btn st-btn--small" data-o="down" data-i="${i}" aria-label="Move ${E(name(id))} later"${i < order.length - 1 ? '' : ' disabled'}>↓</button></span></li>`).join('')}</ol>
          <div class="st-row st-gm-save"><span class="st-muted">${dirtyO ? 'Unsaved order' : 'Saved'}</span><button class="st-btn st-btn--solid st-btn--small" data-save-order${dirtyO ? '' : ' disabled'}>Save order</button></div>` : '<p class="st-muted">No members to order yet.</p>'}</section>`;
    }
    function focusCard() {
      if (g === 'contemporary') return '';
      const placed = G().members.map(m => ({ p: pubOf(m.artist_id) })).filter(x => x.p).map(({ p }) => ({ p, works: p.works.filter(w => { const pl = placeOf(w.id); return pl && pl.state === 'live'; }) })).filter(x => x.works.length);
      const card = (f, i) => { const p = pubOf(f.artist_id), w = p && p.works.find(x => x.id === f.artwork_id); if (!w) return '';
        return `<li class="st-gm-focus">${img(w)}<div><p class="st-work-t">${E(p.display_name)}</p><p class="st-work-s"><i>${E(w.title)}</i></p></div>
          <span class="st-row"><button class="st-btn st-btn--small" data-f="up" data-i="${i}" aria-label="Earlier"${i ? '' : ' disabled'}>↑</button><button class="st-btn st-btn--small" data-f="down" data-i="${i}" aria-label="Later"${i < focus.length - 1 ? '' : ' disabled'}>↓</button><button class="st-btn st-btn--small" data-f="rm" data-i="${i}">Remove</button></span></li>`; };
      return `<section class="st-card"><h2>Artists in Focus · ${TITLE[g]}</h2><p class="st-muted">Up to 6 members, each with one of their works placed in ${TITLE[g]}. Separate from Contemporary’s selection.</p>
        ${focus.length ? `<ol class="st-gm-focuslist">${focus.map(card).join('')}</ol>` : '<p class="st-muted">Nobody chosen yet.</p>'}
        ${focus.length < 6 && placed.some(x => !focus.some(f => f.artist_id === x.p.artist_id)) ? `<div class="st-f st-gm-add"><label for="gm-focus">Add an artist and work</label><select id="gm-focus"><option value="">Choose…</option>${placed.filter(x => !focus.some(f => f.artist_id === x.p.artist_id))
          .map(x => `<optgroup label="${E(x.p.display_name)}">${x.works.map(w => `<option value="${x.p.artist_id}|${w.id}">${E(w.title)}</option>`).join('')}</optgroup>`).join('')}</select></div>` : ''}
        <div class="st-row st-gm-save"><span class="st-muted">${dirtyF ? 'Unsaved selection' : 'Saved'}</span><button class="st-btn st-btn--solid st-btn--small" data-save-focus${dirtyF ? '' : ' disabled'}>Save Artists in Focus</button></div></section>`;
    }
    function useCard() {
      const open = d.open_requests;
      return `<section class="st-card"><h2>Image use permissions</h2><p class="st-muted">Ask an artist before using a work’s image beyond their gallery (a campaign, social media, an editorial or video feature). Each request is for one use; the artist answers yes or no in their Studio, and can withdraw a yes later. Nothing is assumed from an earlier answer.</p>
        ${open.length ? `<h3 class="st-gm-h3">Waiting for an answer (${open.length})</h3><ul class="st-gm-list">${open.map(r => `<li class="st-gm-person"><div><p class="st-work-t">${E(name(r.artist_id))} · ${E(SCOPE[r.scope])}${r.gallery_id ? ' · ' + TITLE[r.gallery_id] : ''}</p>
          <p class="st-work-s">${E(r.purpose)} · ${E(r.channels)}${r.valid_until ? ' · until ' + E(r.valid_until) : ''} · asked ${when(r.requested_at)}</p></div>
          <div class="st-row"><button class="st-btn st-btn--small" data-u="yes" data-id="${r.id}" data-artist="${r.artist_id}" title="The artist answered by email">They said yes</button><button class="st-btn st-btn--small" data-u="no" data-id="${r.id}" data-artist="${r.artist_id}">They said no</button><button class="st-btn st-btn--small" data-u="cancel" data-id="${r.id}">Cancel</button></div></li>`).join('')}</ul>` : '<p class="st-muted">No open requests.</p>'}
        <details class="st-gm-closed" data-ask${open.length ? '' : ' open'}><summary>Ask for permission</summary><form class="st-gm-use" data-use novalidate>
          <div class="st-gm-invite-row"><div class="st-f"><label for="gu-a">Artist</label><select id="gu-a" name="artist_id"><option value="">Choose…</option>${d.published.map(p => `<option value="${p.artist_id}">${E(p.display_name)}</option>`).join('')}</select></div>
          <div class="st-f"><label for="gu-s">Use</label><select id="gu-s" name="scope">${Object.entries(SCOPE).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select></div>
          <div class="st-f"><label for="gu-g">Gallery</label><select id="gu-g" name="gallery_id"><option value="">Any (not tied to a gallery)</option>${Object.entries(TITLE).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select></div></div>
          <fieldset class="st-f st-gm-pick"><legend>Artworks</legend><div data-works><p class="st-muted">Choose an artist first.</p></div></fieldset>
          <div class="st-f"><label for="gu-p">What the image would be used for</label><textarea id="gu-p" name="purpose" maxlength="600" rows="3" placeholder="For example: one post introducing Spaces, with a link to the artist’s gallery"></textarea></div>
          <div class="st-gm-invite-row"><div class="st-f"><label for="gu-c">Where it would appear</label><input id="gu-c" type="text" name="channels" maxlength="300" placeholder="For example: PlotArt Instagram"></div>
          <div class="st-f"><label for="gu-v">Until (optional)</label><input id="gu-v" name="valid_until" type="date"></div></div>
          <button class="st-btn st-btn--solid st-btn--small" type="submit">Send request to the artist’s Studio</button></form></details></section>`;
    }
    function draw() {
      if (!d.installed) { app.innerHTML = `<h1 class="st-h1">Galleries</h1><section class="st-card"><h2>Not available yet</h2><p class="st-muted">Contemporary, Spaces and Being are managed here once the three-gallery records are installed (migrations 0023 and 0024). Until then everything works exactly as today.</p></section>`; return; }
      const x = G();
      app.innerHTML = `<h1 class="st-h1">Galleries</h1>
        <p class="st-sub">Contemporary, Spaces and Being. An artist or work joins Spaces or Being only with your approval and the artist’s acceptance. Nothing here changes an artist’s own gallery, prices, agreements or Contemporary positions 01–25.</p>
        <nav class="st-gm-tabs" aria-label="Gallery">${Object.entries(TITLE).map(([k, v]) => { const y = d.galleries.find(z => z.gallery_id === k), n = d.memberships.filter(m => m.gallery_id === k && ['artist_accepted', 'proposed'].includes(m.state)).length + d.placements.filter(p => p.gallery_id === k && ['artist_accepted', 'proposed'].includes(p.state)).length;
          return `<button type="button" data-g="${k}"${k === g ? ' aria-current="true"' : ''}><b>${v}</b><span>${STATUS[y.status]}${n ? ` · <em>${n} waiting</em>` : ''}</span></button>`; }).join('')}</nav>
        ${msg ? `<p class="st-gm-msg st-err" role="alert">${E(msg)}</p>` : ''}
        ${statusCard(x)}<div class="st-gm-cols"><div>${membersCard()}${orderCard()}</div><div>${worksCard()}${focusCard()}</div></div>${useCard()}`;
    }
    async function act(fn, ok) { try { await fn(); d = await api('GET', '/api/admin/galleries'); load(); msg = ''; say(ok); } catch (e) { msg = e.message; say(e.message, true); } draw(); }
    const confirmTyped = (word, text) => (prompt(`${text}\n\nType ${word} to confirm.`) || '').trim().toUpperCase() === word;
    app.onclick = async e => {
      if (location.pathname.replace(/\/$/, '') !== '/admin/galleries') { app.onclick = null; return; }
      const b = e.target.closest('button'); if (!b || b.disabled || (b.type === 'submit' && b.form)) return;
      if (b.dataset.g) { if ((dirtyO || dirtyF) && !confirm('Leave without saving the order or Artists in Focus?')) return; g = b.dataset.g; sessionStorage.setItem('pa-gal', g); msg = ''; inv = { artist_id: '', source: 'founder_curation', application_ref: '' }; load(); return draw(); }
      if (b.dataset.status) {
        const want = b.dataset.status, x = G();
        if (want === 'open') {
          const word = `OPEN ${TITLE[g].toUpperCase()}`;
          if (!confirmTyped(word, `Open ${TITLE[g]} in the Studio? ${x.live_artists} of ${x.target_artists} artists and ${x.live_works} of ${x.target_works} works. The public page changes only in a separate release you approve.`)) return;
          return act(() => api('POST', `/api/admin/galleries/${g}/status`, { status: 'open', confirm: word, below_target: !x.ready }), `${TITLE[g]} recorded as open`);
        }
        if (!confirm(want === 'paused' ? `Pause ${TITLE[g]}?` : `Move ${TITLE[g]} back to preparation?`)) return;
        return act(() => api('POST', `/api/admin/galleries/${g}/status`, { status: want }), `${TITLE[g]}: ${STATUS[want].toLowerCase()}`);
      }
      if (b.dataset.m) {
        const a = b.dataset.a, how = b.dataset.m;
        if (how === 'withdraw' && !confirm(g === 'contemporary'
          ? `Remove ${name(a)} from Contemporary? Only their Contemporary membership and any Contemporary order position from 26 end. Their own gallery page, works, agreements, prices, commercial terms, Founding position and their other galleries are not affected. You can invite them back later.`
          : `Withdraw ${name(a)} from ${TITLE[g]}? Their works placed there, their order position and any Artists in Focus entry in ${TITLE[g]} go too. Their own gallery is not affected.`)) return;
        return act(() => api('POST', `/api/admin/galleries/${g}/members/${a}/${how}`), { approve: 'Approved', refuse: 'Not accepted', withdraw: g === 'contemporary' ? 'Removed from Contemporary' : 'Withdrawn' }[how]);
      }
      if (b.dataset.w) {
        const how = b.dataset.w;
        if (how === 'withdraw' && !confirm(g === 'contemporary' ? 'Take this work out of Contemporary? It stays in the artist’s own gallery.' : `Withdraw this work from ${TITLE[g]}?`)) return;
        return act(() => api('POST', `/api/admin/galleries/${g}/artworks/${b.dataset.id}/${how}`), { place: 'Saved', refuse: 'Not accepted', withdraw: 'Withdrawn', restore: 'Put back in Contemporary' }[how]);
      }
      if (b.dataset.o) { const i = +b.dataset.i, j = b.dataset.o === 'up' ? i - 1 : i + 1; [order[i], order[j]] = [order[j], order[i]]; dirtyO = true; return draw(); }
      if (b.dataset.f) { const i = +b.dataset.i; if (b.dataset.f === 'rm') focus.splice(i, 1); else { const j = b.dataset.f === 'up' ? i - 1 : i + 1; [focus[i], focus[j]] = [focus[j], focus[i]]; } dirtyF = true; return draw(); }
      if (b.hasAttribute('data-save-order')) return act(() => api('PUT', `/api/admin/galleries/${g}/order`, { artists: order }), 'Order saved');
      if (b.hasAttribute('data-save-focus')) return act(() => api('PUT', `/api/admin/galleries/${g}/features`, { items: focus }), 'Artists in Focus saved');
      if (b.dataset.u) {
        if (b.dataset.u === 'cancel') { if (!confirm('Cancel this request? The artist will no longer see it.')) return; return act(() => api('POST', `/api/admin/image-use/requests/${b.dataset.id}/cancel`), 'Request cancelled'); }
        if (!confirm(`Record that the artist answered ${b.dataset.u} by email?`)) return;
        return act(() => api('POST', '/api/admin/image-use/record', { request_id: b.dataset.id, artist_id: b.dataset.artist, answer: b.dataset.u }), 'Answer recorded');
      }
    };
    app.onchange = e => {
      const t = e.target;
      if (t.id === 'gm-src') { inv.source = t.value; app.querySelector('[data-ref]').hidden = t.value !== 'application'; }
      if (t.id === 'gm-who') inv.artist_id = t.value;
      if (t.id === 'gm-focus' && t.value) { const [artist_id, artwork_id] = t.value.split('|'); focus.push({ artist_id, artwork_id }); dirtyF = true; draw(); }
      if (t.id === 'gu-a') { const p = pubOf(t.value), box = app.querySelector('[data-works]');
        box.innerHTML = p ? p.works.map(w => `<label class="st-check"><input type="checkbox" name="artwork_ids" value="${w.id}" style="accent-color:var(--terra);width:20px;height:20px"> ${E(w.title)}</label>`).join('') : '<p class="st-muted">Choose an artist first.</p>'; }
    };
    app.oninput = e => { if (e.target.id === 'gm-ref') inv.application_ref = e.target.value; };
    app.onsubmit = e => {
      e.preventDefault(); const f = e.target, v = Object.fromEntries(new FormData(f).entries());
      if (f.hasAttribute('data-targets')) return act(() => api('PUT', `/api/admin/galleries/${g}/targets`, { target_artists: +v.target_artists, target_works: +v.target_works }), 'Targets saved');
      if (f.hasAttribute('data-invite')) {
        if (!v.artist_id) return say('Choose an artist', true);
        const body = { artist_id: v.artist_id, source: v.source, ...(v.source === 'application' ? { application_ref: (v.application_ref || '').trim() } : {}) };
        inv = { artist_id: body.artist_id, source: body.source, application_ref: body.application_ref || '' };
        return act(async () => { await api('POST', `/api/admin/galleries/${g}/members`, body); inv = { artist_id: '', source: 'founder_curation', application_ref: '' }; }, `Invited to ${TITLE[g]}`);
      }
      if (f.hasAttribute('data-use')) {
        const ids = [...f.querySelectorAll('input[name="artwork_ids"]:checked')].map(i => i.value);
        return act(() => api('POST', '/api/admin/image-use/requests', { artist_id: v.artist_id, scope: v.scope, gallery_id: v.gallery_id || null, artwork_ids: ids,
          purpose: v.purpose, channels: v.channels, valid_until: v.valid_until || null }), 'Request sent to the artist’s Studio');
      }
    };
    addEventListener('beforeunload', e => { if ((dirtyO || dirtyF) && location.pathname.startsWith('/admin/galleries')) { e.preventDefault(); e.returnValue = ''; } });
    if (d.installed) load();
    draw();
  }

  // Internal test accounts (26 Nov 2026): marked TEST wherever the founder sees artists; their records are never genuine
  // statistics, consent, commercial records or publications.
  async function loadTest() { try { TEST = new Set((await api('GET', '/api/admin/test-artists')).ids || []); } catch { TEST = new Set(); } }
  async function render() {
    await loadTest();
    const h = location.hash || '#/', path = location.pathname.replace(/\/$/, '');
    const am = path.match(/^\/admin\/applications\/((?:F25|PA-AP)-\d{6}-[0-9A-F]{6})$/);
    document.querySelectorAll('.st-tabs a').forEach(a => a.toggleAttribute('aria-current', a.dataset.t === (path.startsWith('/admin/applications') ? 'apps' : path === '/admin/gallery' ? 'order' : path === '/admin/ideas' ? 'ideas' : path === '/admin/garden' ? 'garden' : path === '/admin/agreements' ? 'agree' : path === '/admin/leaving' ? 'leave' : path === '/admin/hire' ? 'hire' : path === '/admin/opportunities' ? 'opps' : path === '/admin/featured' ? 'feat' : path === '/admin/galleries' ? 'gals' : 'desk')));
    document.querySelectorAll('.st-tabs a[aria-current]').forEach(a => a.setAttribute('aria-current', 'page'));
    try { if (am) await appView(am[1]); else if (path === '/admin/gallery') await order(); else if (path === '/admin/ideas') await ideas(); else if (path === '/admin/garden') await garden(); else if (path === '/admin/agreements') await agreements(); else if (path === '/admin/leaving') await leaving(); else if (path === '/admin/hire') await hire(); else if (path === '/admin/opportunities') await opportunities(); else if (path === '/admin/featured') await featured(); else if (path === '/admin/galleries') await galleries(); else if (path === '/admin/applications') await apps(); else if (h.startsWith('#/review/')) await review(h.slice(9)); else await home(); window.scrollTo(0, 0); }
    catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();

/* Report 36: copy a founder-only identifier (Studio ID or gallery address) from the Review desk. */
document.addEventListener('click', async e => {
  const b = e.target.closest && e.target.closest('[data-copy]'); if (!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = 'Copied'; } catch { b.textContent = 'Select and copy'; }
  setTimeout(() => { b.textContent = 'Copy'; }, 1600);
});
