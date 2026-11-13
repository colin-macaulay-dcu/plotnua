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
    const live = o.artists.filter(a => a.state === 'live').length;
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
          <p class="st-work-t">${E(s.display_name)}</p><p class="st-work-s"><span class="st-tier ${s.tier}">${s.tier === 'full' ? 'Review' : 'Quick check'}</span>Submitted ${when(s.created_at)}</p>
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
        ${o.artists.map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${a.founding ? ' <span class="pa-gcard-badge" style="display:inline-block">Founding</span>' : ''}<br><span class="st-muted">${E(a.email)}${a.application_ref ? ' · ' + E(a.application_ref) : ''}</span></td>
          <td>${a.account_status === 'suspended' ? '<span class="st-flag">Suspended</span>' : E(STATE[a.state])}${a.account_status === 'invited' ? '<br><span class="st-muted">Not signed in yet</span>' : ''}</td>
          <td>${agrCell(a)}</td><td>${a.works}</td><td>${a.problems ? `<button class="st-btn st-btn--small st-todo-btn" data-ck="${a.id}" aria-expanded="false" aria-controls="ck-${a.id}">${a.problems} item${a.problems > 1 ? 's' : ''}</button>` : '✓'}</td>
          <td class="st-row">${a.account_status === 'suspended' ? `<button class="st-btn st-btn--small" data-act="reactivate" data-id="${a.id}">Reactivate</button>` : `<button class="st-btn st-btn--small" data-act="suspend" data-id="${a.id}">Suspend</button>`}
          ${a.live_version ? `<button class="st-btn st-btn--small st-btn--danger" data-act="unpublish" data-id="${a.id}">Unpublish</button>` : ''}
          <button class="st-btn st-btn--small" data-email="${a.id}" aria-expanded="false" aria-controls="em-${a.id}">Change email</button>
          ${a.account_status !== 'ended' ? `<button class="st-btn st-btn--small" data-pf="${a.id}" aria-expanded="false" aria-controls="pf-${a.id}">Start profile from application</button>` : ''}</td></tr>
          <tr id="pf-${a.id}" class="st-em-row" hidden><td colspan="6"><form class="st-em" data-pfform="${a.id}" novalidate>
            <p class="st-em-h">Start the profile of <b>${E(a.display_name)}</b> from their Founding 25 application</p>
            <div class="st-f"><label for="pf-r-${a.id}">Application reference</label><input id="pf-r-${a.id}" type="text" autocomplete="off" spellcheck="false" placeholder="F25-YYMMDD-XXXXXX" value="${E(a.application_ref || '')}"></div>
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
        const r = await api('POST', '/api/admin/artists', { display_name: $('#i-name').value, email: $('#i-email').value, application_ref: $('#i-ref').value || null, founding: $('#i-f').checked });
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

  /* ---- Founding Artist Agreement (development 6 Nov 2026): status, acceptance history, founding years, enquiry log */
  const DOCNAME = { 'PA-FAA-2026-11': 'Founding Artist Agreement', 'PA-GPIL-2026-11': 'Image Licence', 'PA-GPIL-2026-10-29': 'Image Licence (earlier label)' };
  const irishDay = d => d ? new Date(d + 'T12:00:00Z').toLocaleDateString('en-IE', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/Dublin' }) : '';
  const irish = t => t ? new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Dublin' }) : '';
  function agrCell(a) {
    const g = a.agreement;
    if (!g || !g.installed) return '<span class="st-muted">Not installed</span>';
    if (g.accepted) return `<span class="st-pill st-pill--ok">Accepted</span><br><span class="st-muted">${E(irish(g.accepted_at))}</span>`;
    if (g.legacy) return `<span class="st-pill st-pill--warn">Earlier licence only</span><br><span class="st-muted">${E(g.legacy.version)}</span>`;
    return '<span class="st-pill">Not accepted</span>';
  }
  async function agreements() {
    const o = await api('GET', '/api/admin/overview');
    let L = await api('GET', '/api/admin/enquiry-log');
    const fy = g => g && g.founding_year ? `${irishDay(g.founding_year.start)} – ${irishDay(g.founding_year.end)}` : g && g.founding ? 'Starts at first publication' : '—';
    const waiting = o.artists.filter(a => a.agreement && a.agreement.installed && !a.agreement.accepted);
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
        ${o.artists.map(a => `<tr><td><b style="color:var(--ivory)">${E(a.display_name)}</b>${a.founding ? ' <span class="pa-gcard-badge" style="display:inline-block">Founding</span>' : ''}${a.founding_number ? `<br><span class="st-muted">No. ${a.founding_number}</span>` : ''}</td>
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
      <p class="st-muted" style="margin:10px 0 0">${r.enquiries.length} logged enquir${r.enquiries.length === 1 ? 'y' : 'ies'}, ${r.enquiries.filter(e => e.founding).length} Founding.</p>`;
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
    const O = d.options, T = d.totals, f = { status: '', interest: '', county: '', reach: '' };
    const provOpts = (sel, extra = '') => extra + Object.entries(O.provinces).map(([p, cs]) => `<optgroup label="${p}">${cs.map(c => `<option value="${c}"${c === sel ? ' selected' : ''}>${c}</option>`).join('')}</optgroup>`).join('');
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
    const match = i => {
      const p = i.prefs;
      if (f.status === 'answered' && !p) return false;
      if (f.status === 'unanswered' && p) return false;
      if (f.status === 'online' && !isOnline(i)) return false;
      if (f.interest && !(p && p.interests.includes(f.interest))) return false;
      if (f.county === '_none' ? !(p && !p.artwork_county) : f.county && !(p && p.artwork_county === f.county)) return false;
      if (f.reach) {
        if (!p) return false;
        if (f.reach === 'anywhere' || f.reach === 'ask') { if (p.coverage_mode !== f.reach) return false; }
        else if (f.reach === 'need_help' || f.reach === 'depends') { if (!p.transport.includes(f.reach)) return false; }
        else if (!(p.coverage_mode === 'anywhere' || (p.coverage_mode === 'counties' && p.coverage_counties.includes(f.reach)))) return false;
      }
      return true;
    };
    const row = i => {
      const p = i.prefs, who = `<b>${E(i.display_name)}</b>${i.founding_number ? ` <span class="st-muted">· F${String(i.founding_number).padStart(2, '0')}</span>` : ''}${i.account_status !== 'active' ? ` <span class="st-muted">· ${E(i.account_status)}</span>` : ''}`;
      if (!p) return `<li class="st-opp-row is-none"><div>${who}</div><div><span class="st-pill">Not answered yet</span></div></li>`;
      if (isOnline(i)) return `<li class="st-opp-row"><div>${who}</div><div><span class="st-pill st-pill--warn">Online only for now</span>${p.artwork_county ? `<span class="st-opp-k">Artwork in Co. ${E(p.artwork_county)}</span>` : ''}${p.note ? `<p class="st-opp-note">“${E(p.note)}”</p>` : ''}</div><div class="st-muted st-opp-when">${E(when(p.updated_at))}</div></li>`;
      return `<li class="st-opp-row"><div>${who}</div>
        <div><div class="st-chips" style="margin:0 0 6px">${p.interests.map(k => `<span class="st-chip">${E(O.interest_short[k])}</span>`).join('')}</div>
          <span class="st-opp-k">Artwork: ${p.artwork_county ? `Co. ${E(p.artwork_county)}` : '<i>not given</i>'}</span>
          <span class="st-opp-k">Transport: ${p.transport.length ? p.transport.map(k => E(O.transport_short[k])).join(', ') : '<i>not given</i>'}${p.coverage_mode ? ` · ${E(coverage(p))}` : ''}</span>
          ${p.note ? `<p class="st-opp-note">“${E(p.note)}”</p>` : ''}</div>
        <div class="st-muted st-opp-when">${E(when(p.updated_at))}</div></li>`;
    };
    app.innerHTML = `
      <h1 class="st-h1">Opportunities &amp; delivery</h1>
      <p class="st-sub">What artists have said they’d be open to, where their work is based and how it could reach a venue. These are expressions of interest only: talk to the artist before arranging anything.</p>
      <div class="st-kpis">
        <div class="st-kpi"><b>${T.answered}</b><span>answered</span></div>
        <div class="st-kpi"><b>${T.unanswered}</b><span>not answered yet</span></div>
        <div class="st-kpi"><b>${T.online_only}</b><span>online only for now</span></div>
        <div class="st-kpi"><b>${T.artists}</b><span>artists in Studio</span></div>
      </div>
      <section class="st-card">
        <h3 class="st-opp-h3">Interest by opportunity</h3>
        <div class="st-opts st-opts--sm" style="margin-top:6px">${Object.keys(O.interests).filter(k => k !== 'online_only').map(k => `<button type="button" class="st-opt st-opt--sm st-opt--count" data-int="${k}" aria-pressed="false">${E(O.interest_short[k])} <b>${T.by_interest[k]}</b></button>`).join('')}</div>
        <div class="st-opp-filters">
          <div class="st-f"><label for="of-status">Answers</label><select id="of-status"><option value="">Everyone</option><option value="answered">Answered</option><option value="unanswered">Not answered yet</option><option value="online">Online only for now</option></select></div>
          <div class="st-f"><label for="of-int">Interested in</label><select id="of-int"><option value="">Any opportunity</option>${Object.keys(O.interests).filter(k => k !== 'online_only').map(k => `<option value="${k}">${E(O.interest_short[k])}</option>`).join('')}</select></div>
          <div class="st-f"><label for="of-county">Artwork based in</label><select id="of-county">${provOpts('', '<option value="">Any county</option><option value="_none">Not given</option>')}</select></div>
          <div class="st-f"><label for="of-reach">Can deliver to</label><select id="of-reach"><option value="">Any</option><option value="anywhere">Anywhere on the island</option><option value="ask">Ask about each opportunity</option><option value="need_help">Needs help with transport</option><option value="depends">Depends on the opportunity</option>${provOpts('')}</select></div>
        </div>
        <p class="st-muted" style="margin:0" aria-live="polite"><span id="of-n"></span> <button type="button" class="st-linkbtn" id="of-reset" hidden>Clear filters</button></p>
      </section>
      <ul class="st-opp-list" id="of-list"></ul>
      <p class="st-muted">“Can deliver to” a county includes artists who said “Anywhere on the island”. Artists who answered “Ask about each opportunity” or need help with transport appear under those choices.</p>`;
    const draw = () => {
      const rows = d.items.filter(match);
      $('#of-list').innerHTML = rows.length ? rows.map(row).join('') : '<li class="st-opp-row is-none"><div class="st-muted">No artists match these filters.</div></li>';
      $('#of-n').textContent = `Showing ${rows.length} of ${d.items.length} artists.`;
      $('#of-reset').hidden = !Object.values(f).some(Boolean);
      app.querySelectorAll('[data-int]').forEach(b => b.setAttribute('aria-pressed', String(f.interest === b.dataset.int)));
    };
    const bind = (id, k) => $(id).addEventListener('change', e => { f[k] = e.target.value; draw(); });
    bind('#of-status', 'status'); bind('#of-int', 'interest'); bind('#of-county', 'county'); bind('#of-reach', 'reach');
    app.querySelectorAll('[data-int]').forEach(b => b.addEventListener('click', () => { f.interest = f.interest === b.dataset.int ? '' : b.dataset.int; $('#of-int').value = f.interest; draw(); }));
    $('#of-reset').addEventListener('click', () => { Object.keys(f).forEach(k => { f[k] = ''; }); ['#of-status', '#of-int', '#of-county', '#of-reach'].forEach(s => { $(s).value = ''; }); draw(); });
    draw();
  }

  async function render() {
    const h = location.hash || '#/', path = location.pathname.replace(/\/$/, '');
    const am = path.match(/^\/admin\/applications\/(F25-\d{6}-[0-9A-F]{6})$/);
    document.querySelectorAll('.st-tabs a').forEach(a => a.toggleAttribute('aria-current', a.dataset.t === (path.startsWith('/admin/applications') ? 'apps' : path === '/admin/gallery' ? 'order' : path === '/admin/ideas' ? 'ideas' : path === '/admin/garden' ? 'garden' : path === '/admin/agreements' ? 'agree' : path === '/admin/leaving' ? 'leave' : path === '/admin/hire' ? 'hire' : path === '/admin/opportunities' ? 'opps' : 'desk')));
    document.querySelectorAll('.st-tabs a[aria-current]').forEach(a => a.setAttribute('aria-current', 'page'));
    try { if (am) await appView(am[1]); else if (path === '/admin/gallery') await order(); else if (path === '/admin/ideas') await ideas(); else if (path === '/admin/garden') await garden(); else if (path === '/admin/agreements') await agreements(); else if (path === '/admin/leaving') await leaving(); else if (path === '/admin/hire') await hire(); else if (path === '/admin/opportunities') await opportunities(); else if (path === '/admin/applications') await apps(); else if (h.startsWith('#/review/')) await review(h.slice(9)); else await home(); window.scrollTo(0, 0); }
    catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();
