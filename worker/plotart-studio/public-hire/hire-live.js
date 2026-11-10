/* PlotArt · Art for Hire page script (Stage 3B-3, development 10 Nov 2026). PREPARED FOR STAGE 3B-4, NOT PUBLISHED.
   No tracking, no storage, no third parties.

   FAILS CLOSED. Every hire tile ships hidden in the page HTML (<article data-hire-work="w…" hidden>), so with no script,
   a blocked script or a failed check, nothing is presented as available for hire. A tile is shown only while the live
   check (/v1/hire-listed) has answered within its validity window AND names that work. If a later check fails or the
   answer goes stale, every tile is hidden again. The enquiry relay re-checks eligibility independently on every enquiry.

   Page contract:  <script src="…/hire-live.js" data-api="https://<relay>" defer></script>
     [data-hire-work="<artwork id>"]   a tile (hidden in the HTML)          [data-hire-status]  a status line
     [data-hire-availability]          inside a tile: the hire availability [data-hire-enquire] button opening the form
     [data-hire-ref="PA-<slug>-<id>"]  on the tile: the enquiry reference   [data-hire-title]   on the tile: the title */
(() => {
  'use strict';
  const me = document.currentScript, API = (me && me.dataset.api || '').replace(/\/$/, '');
  const NOTICE = 'PA-ENQ-HIRE-2026-11', TIMEOUT_MS = 6000, RECHECK_MS = 60_000;
  const EXPLAIN = [
    'PlotArt only introduces you to the artist. It is not a party to any hire and takes no payment.',
    'The hire fee (rental price) is agreed directly between you and the artist.',
    'Insurance, transport, installation and return are agreed between you and the artist.',
    'Screen and photo use is never included in a hire and is never granted automatically. Any permission must be agreed in writing with the artist.',
    'Film and television screen-use arrangements cannot be made through PlotArt until its legal review is complete.',
  ];
  const UNAVAILABLE = 'Hire availability can’t be confirmed right now, so no works are shown. Please try again shortly or email hello@plotnua.ie.';
  const E = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const tiles = () => [...document.querySelectorAll('[data-hire-work]')];
  const status = msg => document.querySelectorAll('[data-hire-status]').forEach(el => { el.textContent = msg; el.hidden = !msg; });
  let state = { listed: new Map(), validUntil: 0 };

  function hideAll(msg) {
    state = { listed: new Map(), validUntil: 0 };
    tiles().forEach(t => { t.hidden = true; t.setAttribute('aria-hidden', 'true'); });
    closeForm();
    status(msg);
  }
  const fresh = () => Date.now() < state.validUntil;
  const label = i => i.availability === 'from' && i.available_from
    ? `Available for hire from ${new Date(i.available_from + 'T12:00:00Z').toLocaleDateString('en-IE', { day: 'numeric', month: 'long', year: 'numeric' })}` : 'Available for hire';

  async function check() {
    if (!API) return hideAll(UNAVAILABLE);
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
    try {
      const r = await fetch(API + '/v1/hire-listed', { signal: ctl.signal, credentials: 'omit', cache: 'no-store' });
      const j = await r.json();
      const until = Date.parse(j && j.valid_until);
      if (!r.ok || !j || j.ok !== true || !Array.isArray(j.items) || !(until > Date.now())) return hideAll(UNAVAILABLE);
      if (j.open !== true) return hideAll('Art for Hire enquiries aren’t open yet.');
      state = { listed: new Map(j.items.map(i => [i.id, i])), validUntil: until };
      let shown = 0;
      tiles().forEach(t => {
        const i = state.listed.get(t.dataset.hireWork);
        t.hidden = !i; t.toggleAttribute('aria-hidden', !i);
        if (i) { shown++; const a = t.querySelector('[data-hire-availability]'); if (a) a.textContent = label(i); }
      });
      if (openRef && !state.listed.has(openRef.id)) closeForm('This work is no longer available for hire.');
      status(shown ? '' : 'No works are available for hire at the moment.');
    } catch { hideAll(UNAVAILABLE); }
    finally { clearTimeout(timer); }
  }
  // the answer expires on its own: if no new check succeeds in time, everything is hidden again
  setInterval(() => { if (state.validUntil && !fresh()) hideAll(UNAVAILABLE); }, 5000);

  /* ---------------------------------------------------------------- the enquiry form (one at a time) */
  let openRef = null, dialog = null;
  function closeForm(msg) { if (dialog) { dialog.remove(); dialog = null; } openRef = null; if (msg) status(msg); }
  const opt = o => Object.entries(o).map(([k, v]) => `<option value="${k}">${E(v)}</option>`).join('');
  function openForm(tile) {
    const id = tile.dataset.hireWork;
    if (!fresh() || !state.listed.has(id)) { hideAll(UNAVAILABLE); return; }
    closeForm();
    openRef = { id, ref: tile.dataset.hireRef, title: tile.dataset.hireTitle || 'this work' };
    dialog = document.createElement('section');
    dialog.className = 'pa-hire-form'; dialog.setAttribute('aria-labelledby', 'pa-hire-h');
    dialog.innerHTML = `<h2 id="pa-hire-h">Hire enquiry: ${E(openRef.title)}</h2>
      <ul class="pa-hire-explain">${EXPLAIN.map(x => `<li>${E(x)}</li>`).join('')}</ul>
      <form novalidate>
        <label>Your name<input name="name" required maxlength="80" autocomplete="name"></label>
        <label>Email<input name="email" type="email" required maxlength="254" autocomplete="email"></label>
        <label>Business or production<input name="business" required maxlength="160" autocomplete="organization"></label>
        <label>Your role<input name="role" required maxlength="80" autocomplete="organization-title"></label>
        <label>Business website (optional)<input name="business_url" type="url" maxlength="300" placeholder="https://"></label>
        <label>Type of project<select name="project_type" required><option value="">Choose</option>${opt({ film_tv: 'Film or television', advertising: 'Advertising', photography: 'Photography', staging: 'Property or event staging', interiors: 'Interiors or office', other: 'Other' })}</select></label>
        <label>How the work would be used<select name="intended_use" required><option value="">Choose</option>${opt({ display_staging: 'Display or staging (not filmed)', photography: 'Photography', other: 'Other' })}</select></label>
        <fieldset><legend>Dates needed</legend><label>From<input name="date_from" type="date" required></label><label>To<input name="date_to" type="date" required></label></fieldset>
        <label>Town or county where it would be used<input name="use_place" required maxlength="40"></label>
        <label>Where is the project?<select name="territory" required><option value="">Choose</option>${opt({ ie: 'Republic of Ireland', ni: 'Northern Ireland', gb: 'Great Britain', other: 'Elsewhere' })}</select></label>
        <label>Anything else the artist should know (optional)<textarea name="message" maxlength="1500" rows="4"></textarea></label>
        <div class="pa-hire-hp" aria-hidden="true" style="position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden"><label>Fax number<input name="fax_number" tabindex="-1" autocomplete="off"></label></div>
        <label class="pa-hire-privacy"><input name="privacy" type="checkbox" required> I have read <a href="/privacy.html#plotart-hire-enquiries" target="_blank" rel="noopener">how PlotArt handles hire enquiries</a>. My details are passed to the artist so they can reply to me.</label>
        <p class="pa-hire-err" role="alert" aria-live="assertive"></p>
        <button type="submit">Send hire enquiry</button> <button type="button" data-close>Cancel</button>
      </form>`;
    tile.after(dialog);
    const f = dialog.querySelector('form'), err = dialog.querySelector('.pa-hire-err');
    dialog.querySelector('[data-close]').addEventListener('click', () => closeForm());
    f.addEventListener('submit', async ev => {
      ev.preventDefault(); err.textContent = '';
      if (!fresh() || !state.listed.has(openRef.id)) { closeForm(); hideAll(UNAVAILABLE); return; }
      const v = Object.fromEntries(new FormData(f).entries());
      const body = { ref: openRef.ref, notice: NOTICE, privacy: f.privacy.checked, name: v.name, email: v.email, business: v.business, role: v.role,
        business_url: v.business_url || '', project_type: v.project_type, intended_use: v.intended_use, date_from: v.date_from, date_to: v.date_to,
        use_place: v.use_place, territory: v.territory, message: v.message || '' };
      if (v.fax_number) body.fax_number = v.fax_number;
      const btn = f.querySelector('[type=submit]'); btn.disabled = true;
      try {
        const r = await fetch(API + '/v1/hire-enquiry', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), credentials: 'omit' });
        const j = await r.json().catch(() => ({}));
        if (r.ok && j.ok) { dialog.innerHTML = `<h2>Enquiry sent</h2><p>${E(j.message || 'Thank you.')}</p><ul class="pa-hire-explain">${EXPLAIN.map(x => `<li>${E(x)}</li>`).join('')}</ul>`; openRef = null; return; }
        err.textContent = j.error || 'That didn’t work. Please try again or email hello@plotnua.ie.';
        if (r.status === 409) { await check(); }                         // withdrawn meanwhile: the tile disappears
      } catch { err.textContent = 'No connection. Please try again or email hello@plotnua.ie.'; }
      btn.disabled = false;
    });
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-hire-enquire]'); if (b) { const t = b.closest('[data-hire-work]'); if (t && !t.hidden) openForm(t); } });

  hideAll('Checking which works are available for hire…');
  check();
  setInterval(check, RECHECK_MS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) check(); });
})();
