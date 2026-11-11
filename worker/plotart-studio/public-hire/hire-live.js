/* PlotArt · Art for Hire page script (Stages 3B-3/3B-4, development 10 Nov 2026). NOT PUBLISHED.
   No tracking, no storage, no third parties.

   FAILS CLOSED. Every hire card ships hidden in the page HTML, so with no script, a blocked script or a failed check,
   nothing is presented as available for hire. A card is shown only while the live check (/v1/hire-listed) has answered
   within its validity window AND names that work. If a later check fails or the answer goes stale, every card is hidden
   again. The enquiry relay re-checks eligibility on every enquiry, whatever this page shows.

   The enquiry form exists only when BOTH the page was built with it (data-enquiries="on", after the founder's legal and
   privacy approval) AND the relay reports enquiries open. Otherwise the button explains that enquiries are not yet open.

   Page contract:  <script src="hire-live.js" data-api="https://<relay>" data-enquiries="off|on" defer></script>
     [data-hire-work="<id>"] a card, hidden in the HTML, with data-hire-ref / -title / -artist
     [data-hire-availability] [data-hire-enquire]  inside a card      [data-hire-status] [data-hire-empty] [data-hire-closed]
     [data-hire-cta]  the hero's primary action (v3, 11 Nov 2026): ships as "How it works" (#afh3-how); it becomes
                      "See works for hire" (#afh3-works) only while the live check is showing at least one work, and
                      returns to "How it works" whenever nothing is shown. It never promises works that are not there. */
(() => {
  'use strict';
  const me = document.currentScript, API = (me && me.dataset.api || '').replace(/\/$/, ''), FORM_BUILT = !!me && me.dataset.enquiries === 'on';
  const NOTICE = 'PA-ENQ-HIRE-2026-11', TIMEOUT_MS = 6000, RECHECK_MS = 60_000;
  const EXPLAIN = [
    'PlotArt only introduces you to the artist. It is not a party to any hire and takes no payment.',
    'The hire fee (rental price) is agreed directly between you and the artist.',
    'Insurance, transport, installation and return are agreed between you and the artist.',
    'Screen and photo use is never included in a hire and is never granted automatically. Any permission must be agreed in writing with the artist.',
    'Film and television screen-use arrangements cannot be made through PlotArt until its legal review is complete.',
  ];
  const UNAVAILABLE = 'We can’t confirm which works are available for hire right now, so none are shown. Please try again shortly.';
  const E = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const $$ = s => [...document.querySelectorAll(s)];
  const cards = () => $$('[data-hire-work]');
  const empty = $$('[data-hire-empty]'), staticEmpty = empty.some(x => x.hasAttribute('data-hire-static'));
  const status = msg => $$('[data-hire-status]').forEach(el => { el.textContent = msg; el.hidden = !msg; });
  const cta = shown => $$('[data-hire-cta]').forEach(a => {
    a.textContent = shown ? 'See works for hire' : 'How it works';
    a.setAttribute('href', shown ? '#afh3-works' : '#afh3-how');
  });
  let state = { listed: new Map(), validUntil: 0, enquiries: false };

  function setEnquiries(on) {
    state.enquiries = on;
    $$('[data-hire-closed]').forEach(el => { el.hidden = on || !cards().length; });   // nothing to enquire about: no note
    cards().forEach(c => { const b = c.querySelector('[data-hire-enquire]'); if (b) { b.setAttribute('aria-disabled', on ? 'false' : 'true'); b.classList.toggle('is-off', !on); } });
  }
  function hideAll(msg) {
    state = { listed: new Map(), validUntil: 0, enquiries: false };
    cards().forEach(c => { c.hidden = true; });
    empty.forEach(el => { el.hidden = !staticEmpty; });
    cta(false);
    setEnquiries(false);
    closeForm();
    status(msg);
  }
  const fresh = () => Date.now() < state.validUntil;
  const label = i => i.availability === 'from' && i.available_from
    ? `Available for hire from ${new Date(i.available_from + 'T12:00:00Z').toLocaleDateString('en-IE', { day: 'numeric', month: 'long', year: 'numeric' })}` : 'Available for hire now';

  async function check() {
    if (!API) return hideAll(UNAVAILABLE);
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
    try {
      const r = await fetch(API + '/v1/hire-listed', { signal: ctl.signal, credentials: 'omit', cache: 'no-store' });
      const j = await r.json();
      const until = Date.parse(j && j.valid_until);
      if (!r.ok || !j || j.ok !== true || !Array.isArray(j.items) || !(until > Date.now())) return hideAll(UNAVAILABLE);
      if (j.open !== true) return hideAll('Art for Hire isn’t open yet.');
      state.listed = new Map(j.items.map(i => [i.id, i])); state.validUntil = until;
      let shown = 0;
      cards().forEach(c => {
        const i = state.listed.get(c.dataset.hireWork);
        c.hidden = !i;
        if (i) { shown++; const a = c.querySelector('[data-hire-availability]'); if (a) a.textContent = label(i); }
      });
      empty.forEach(el => { el.hidden = shown > 0; });
      cta(shown > 0);
      setEnquiries(FORM_BUILT && j.enquiries === true);
      if (openRef && !state.listed.has(openRef.id)) closeForm('This work is no longer available for hire.');
      status('');
    } catch { hideAll(UNAVAILABLE); }
    finally { clearTimeout(timer); }
  }
  // the answer expires on its own: if no new check succeeds in time, everything is hidden again
  setInterval(() => { if (state.validUntil && !fresh()) hideAll(UNAVAILABLE); }, 5000);

  /* ---------------------------------------------------------------- the enquiry dialog (one at a time) */
  let openRef = null, dialog = null, opener = null;
  function closeForm(msg) {
    if (dialog) { if (dialog.open) dialog.close(); dialog.remove(); dialog = null; }
    openRef = null;
    if (opener && document.contains(opener) && !opener.closest('[hidden]')) opener.focus();
    opener = null;
    if (msg) status(msg);
  }
  const opt = o => Object.entries(o).map(([k, v]) => `<option value="${k}">${E(v)}</option>`).join('');
  const field = (name, lab, html, hint, wide) => `<div class="pa-hf-f${wide ? ' pa-hf-wide' : ''}"><label for="hf-${name}">${lab}</label>${html}${hint ? `<small id="hf-${name}-h">${hint}</small>` : ''}</div>`;
  function openForm(card, btn) {
    const id = card.dataset.hireWork;
    if (!fresh() || !state.listed.has(id)) { hideAll(UNAVAILABLE); return; }
    if (!state.enquiries) { $$('[data-hire-closed]').forEach(el => { el.hidden = false; el.focus && el.focus(); }); return; }
    closeForm();
    opener = btn;
    openRef = { id, ref: card.dataset.hireRef, title: card.dataset.hireTitle || 'this work', artist: card.dataset.hireArtist || '' };
    const img = card.querySelector('img');
    dialog = document.createElement('dialog');
    dialog.className = 'pa-hf'; dialog.setAttribute('aria-labelledby', 'hf-h');
    dialog.innerHTML = `<div class="pa-hf-in">
      <div class="pa-hf-top">${img ? `<img src="${E(img.currentSrc || img.src)}" alt="" width="72" height="72">` : ''}<div><p class="pa-eyebrow">Hire enquiry</p>
        <h2 id="hf-h">${E(openRef.title)}</h2><p class="pa-muted">${E(openRef.artist)}</p></div>
        <button type="button" class="pa-hf-x" data-close aria-label="Close the enquiry form">×</button></div>
      <ul class="pa-hf-explain">${EXPLAIN.map(x => `<li>${E(x)}</li>`).join('')}</ul>
      <form novalidate>
        <div class="pa-hf-grid">
        ${field('name', 'Your name', '<input id="hf-name" name="name" required maxlength="80" autocomplete="name">')}
        ${field('email', 'Email', '<input id="hf-email" name="email" type="email" required maxlength="254" autocomplete="email">')}
        ${field('business', 'Business or production', '<input id="hf-business" name="business" required maxlength="160" autocomplete="organization">')}
        ${field('role', 'Your role', '<input id="hf-role" name="role" required maxlength="80" autocomplete="organization-title">')}
        ${field('business_url', 'Business website <span>(optional)</span>', '<input id="hf-business_url" name="business_url" type="url" maxlength="300" placeholder="https://">')}
        ${field('project_type', 'Type of project', `<select id="hf-project_type" name="project_type" required><option value="">Choose</option>${opt({ film_tv: 'Film or television', advertising: 'Advertising', photography: 'Photography', staging: 'Property or event staging', interiors: 'Interiors or office', other: 'Other' })}</select>`)}
        ${field('intended_use', 'How the work would be used', `<select id="hf-intended_use" name="intended_use" required aria-describedby="hf-intended_use-h"><option value="">Choose</option>${opt({ display_staging: 'Display or staging (not filmed)', photography: 'Photography', other: 'Other' })}</select>`, 'Filming can’t be arranged through PlotArt yet.', true)}
        ${field('date_from', 'Needed from', '<input id="hf-date_from" name="date_from" type="date" required>')}
        ${field('date_to', 'Needed until', '<input id="hf-date_to" name="date_to" type="date" required>')}
        ${field('use_place', 'Town or county where it would be used', '<input id="hf-use_place" name="use_place" required maxlength="40">')}
        ${field('territory', 'Where is the project?', `<select id="hf-territory" name="territory" required><option value="">Choose</option>${opt({ ie: 'Republic of Ireland', ni: 'Northern Ireland', gb: 'Great Britain', other: 'Elsewhere' })}</select>`)}
        </div>
        ${field('message', 'Anything else the artist should know <span>(optional)</span>', '<textarea id="hf-message" name="message" maxlength="1500" rows="4"></textarea>')}
        <div class="pa-hf-hp" aria-hidden="true"><label>Fax number<input name="fax_number" tabindex="-1" autocomplete="off"></label></div>
        <label class="pa-hf-privacy"><input name="privacy" type="checkbox" required> <span>I have read <a href="/privacy.html#plotart-hire-enquiries" target="_blank" rel="noopener">how PlotArt handles hire enquiries</a>. My details go to the artist so they can reply to me.</span></label>
        <p class="pa-hf-err" role="alert"></p>
        <div class="pa-hf-actions"><button type="submit" class="pa-btn pa-btn--solid">Send hire enquiry</button><button type="button" class="pa-btn pa-btn--ghost" data-close>Cancel</button></div>
      </form></div>`;
    document.body.appendChild(dialog);
    dialog.addEventListener('close', () => { if (dialog) closeForm(); });
    dialog.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => closeForm()));
    dialog.showModal();
    dialog.querySelector('#hf-name').focus();
    const f = dialog.querySelector('form'), err = dialog.querySelector('.pa-hf-err');
    f.addEventListener('submit', async ev => {
      ev.preventDefault(); err.textContent = '';
      if (!fresh() || !state.listed.has(openRef.id) || !state.enquiries) { closeForm(); hideAll(UNAVAILABLE); return; }
      const v = Object.fromEntries(new FormData(f).entries());
      const body = { ref: openRef.ref, notice: NOTICE, privacy: f.privacy.checked, name: v.name, email: v.email, business: v.business, role: v.role,
        business_url: v.business_url || '', project_type: v.project_type, intended_use: v.intended_use, date_from: v.date_from, date_to: v.date_to,
        use_place: v.use_place, territory: v.territory, message: v.message || '' };
      if (v.fax_number) body.fax_number = v.fax_number;
      const btn = f.querySelector('[type=submit]'); btn.disabled = true;
      try {
        const r = await fetch(API + '/v1/hire-enquiry', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), credentials: 'omit' });
        const j = await r.json().catch(() => ({}));
        if (r.ok && j.ok) {
          dialog.querySelector('.pa-hf-in').innerHTML = `<p class="pa-eyebrow">Hire enquiry sent</p><h2 id="hf-h" tabindex="-1">Thank you.</h2><p>${E(j.message || '')}</p>
            <ul class="pa-hf-explain">${EXPLAIN.map(x => `<li>${E(x)}</li>`).join('')}</ul><div class="pa-hf-actions"><button type="button" class="pa-btn pa-btn--solid" data-close>Close</button></div>`;
          dialog.querySelector('[data-close]').addEventListener('click', () => closeForm());
          dialog.querySelector('#hf-h').focus();
          return;
        }
        err.textContent = j.error || 'That didn’t work. Please try again or email hello@plotnua.ie.';
        if (r.status === 409) await check();                          // withdrawn meanwhile: the card and the form disappear
      } catch { err.textContent = 'No connection. Please try again or email hello@plotnua.ie.'; }
      if (btn.isConnected) btn.disabled = false;
    });
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-hire-enquire]'); if (b) { const c = b.closest('[data-hire-work]'); if (c && !c.hidden) openForm(c, b); } });

  hideAll(cards().length ? 'Checking which works are available for hire…' : '');
  if (cards().length) { check(); setInterval(check, RECHECK_MS); document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); }); }
})();
