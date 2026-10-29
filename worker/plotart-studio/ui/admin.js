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
          <td>${a.works}${a.min ? ` / ${a.min}` : ''}${a.below_minimum ? '<br><span class="st-flag">Below 10: 30-day top-up</span>' : ''}</td><td>${a.problems ? `${a.problems} item${a.problems > 1 ? 's' : ''}` : '✓'}</td>
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

  async function render() {
    const h = location.hash || '#/';
    try { if (h.startsWith('#/review/')) await review(h.slice(9)); else await home(); window.scrollTo(0, 0); }
    catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();
