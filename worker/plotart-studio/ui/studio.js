/* PlotArt Studio · artist app (Phase 2). No framework, no tracking, no browser storage of content: every change is
   saved to the Studio immediately and confirmed on screen ("Saved"). */
(() => {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const E = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const app = $('#app'), toast = $('#saved');
  let ME = null, WORKS = [];
  const LIVE_DOMAIN = 'https://plotnua.ie/plotart/artists/';
  const AV = { available: 'Available', reserved: 'Reserved', sold: 'Sold', not_for_sale: 'Not for sale' };
  const MEDIUM = { painting: 'Painting', drawing: 'Drawing', works_on_paper: 'Works on paper', printmaking: 'Printmaking', photography: 'Photography',
    sculpture: 'Sculpture', ceramics_craft: 'Ceramics and craft', textiles: 'Textiles', mixed_media: 'Mixed media', digital_new_media: 'Digital and new media', other: 'Something else' };

  function say(msg, bad = false) {
    toast.textContent = msg; toast.classList.toggle('bad', bad); toast.classList.add('on');
    clearTimeout(say.t); say.t = setTimeout(() => toast.classList.remove('on'), bad ? 5200 : 1800);
  }
  async function api(method, path, body, raw) {
    const opt = { method, headers: { 'X-Studio': '1' }, credentials: 'same-origin' };
    if (raw) { opt.body = raw; } else if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    let r;
    try { r = await fetch(path, opt); } catch { throw new Error('No connection. Your last saved change is safe; try again in a moment.'); }
    const j = await r.json().catch(() => ({}));
    if (r.status === 401) { location.reload(); throw new Error('Please sign in again.'); }
    if (!r.ok || j.ok === false) { const e = new Error(j.error || (j.problems ? j.problems.join(' · ') : 'That didn’t work.')); e.data = j; e.status = r.status; throw e; }
    return j;
  }
  let afterRefresh = null;   // the open view may update itself (e.g. an artwork's "still needed" line) after each save
  const refresh = async () => { ME = await api('GET', '/api/me'); WORKS = (await api('GET', '/api/artworks')).works; if (afterRefresh) afterRefresh(); };

  /* ------------------------------------------------------------- submission checklist (PLOTART-STUDIO-SUBMISSION-002)
     The server sends each outstanding item with where it belongs; here it becomes a grouped list of links that open
     the right page and focus the missing field. The rules themselves live on the server and are unchanged. */
  const NEED = { title: 'title', medium: 'medium', size: 'size', ai: 'the AI question', ai_note: 'AI note', main_photo: 'main photograph',
    photo_alt: 'photograph description', photographer: 'who took the photograph', photo_credit: 'photographer’s name', photo_blocked: 'a new photograph' };
  const PHOTO = ['photo_alt', 'photographer', 'photo_credit'];
  const onlyPhoto = i => i.needs.every(c => PHOTO.includes(c));
  const workNeeds = i => onlyPhoto(i) ? 'photograph details' : i.needs.map(c => NEED[c]).join(', ');
  const fixHref = i => i.area === 'agreement' ? '#/agreement' : i.area === 'profile' ? `#/profile?fix=${i.field}` : i.area === 'works' ? '#/works?fix=add'
    : i.area === 'work' ? `#/work/${i.work_id}?fix=${i.field}${i.image_id ? '&img=' + i.image_id : ''}` : '#/submit';
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  function checklistHTML(list, { openWorks = false } = {}) {
    const prof = list.filter(i => i.area === 'profile'), wk = list.filter(i => i.area === 'work'), add = list.find(i => i.area === 'works'), agr = list.find(i => i.area === 'agreement');
    const link = (href, label, extra = '') => `<li><a class="st-ck-link" href="${href}"><span>${label}</span>${extra}<span class="st-ck-go" aria-hidden="true">→</span></a></li>`;
    const allPhoto = wk.length && wk.every(onlyPhoto);
    return `<div class="st-ck">
      ${agr ? `<div class="st-ck-g"><h4 class="st-ck-h">Agreement</h4><ul class="st-ck-l">${link(fixHref(agr), E(agr.text))}</ul></div>` : ''}
      ${prof.length ? `<div class="st-ck-g"><h4 class="st-ck-h">Profile</h4><ul class="st-ck-l">${prof.map(i => link(fixHref(i), E(i.text))).join('')}</ul></div>` : ''}
      ${add || wk.length ? `<div class="st-ck-g"><h4 class="st-ck-h">Artworks</h4>
        ${add ? `<ul class="st-ck-l">${link(fixHref(add), 'Add your first artwork')}</ul>` : ''}
        ${wk.length ? `<details class="st-ck-d"${openWorks || wk.length <= 3 ? ' open' : ''}><summary><span>${plural(wk.length, 'artwork needs', 'artworks need')} ${allPhoto ? 'photograph details' : 'details'}</span><span class="st-ck-n" aria-hidden="true">${wk.length}</span></summary>
          <ul class="st-ck-l">${wk.map(i => link(fixHref(i), E(i.title || 'Untitled artwork'), `<small>${E(workNeeds(i))}</small>`)).join('')}</ul></details>` : ''}</div>` : ''}
    </div>`;
  }
  // Open the page an item points to, then bring the missing field into view, focus it and mark it briefly.
  function focusFix(fix, img) {
    const sel = { photo_alt: `#alt-${img}`, photographer: `[name="photographer-${img}"]`, photo_credit: `#cr-${img}`, photo_blocked: '#mdrop input',
      main_photo: '#mdrop input', title: '#f-title', medium: '#f-medium', size: '#f-h_cm', ai: '[name=ai_involvement]', ai_note: '#f-ai_note',
      display_name: '#f-display_name', bio: '#f-bio', statement: '#f-statement', portrait_alt: '#f-palt', add: '[data-act=add]' }[fix];
    const el = sel && app.querySelector(sel);
    if (!el) return;
    const d = el.closest('details'); if (d) d.open = true;
    if (fix === 'photo_credit') { const box = el.closest('[data-credit]'); if (box) box.hidden = false; }
    const zone = el.closest('.st-f, .st-req-group, .st-drop') || el;
    zone.classList.remove('st-fix'); void zone.offsetWidth; zone.classList.add('st-fix');
    zone.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    el.focus({ preventScroll: true });
  }
  const live = w => w.in_version;

  /* ------------------------------------------------------------- views */
  const STATE = {
    draft: ['Not published yet', 'Add your profile and your works, preview your gallery, then submit it. Nothing is public until we have reviewed it together.'],
    in_review: ['Submitted for review', 'Thank you. We review every gallery and change ourselves, and we’ll email you. You can keep working: anything you change now can be submitted again.'],
    changes_requested: ['A few changes, please', 'We’ve looked at your submission. Make the changes below, then submit again.'],
    approved: ['Approved', 'Your gallery is approved and is being published.'],
    publishing: ['Approved: publishing', 'Your approved changes are being published to plotnua.ie.'],
    live: ['Live on plotnua.ie', 'Your gallery is public. Sold, reserved and removed works update straight away; other changes go to us for a quick check first.'],
  };
  function dashboard() {
    const s = ME.status, a = ME.artist, [title, text] = STATE[s.state];
    const n = s.counts.works;
    const canSubmit = s.unsubmitted.length && !s.problems.length && s.state !== 'in_review';
    const left = s.checklist.length;
    const pendingTier = s.tier === 'light' ? 'a quick check' : 'a review';
    app.innerHTML = `
      <p class="st-muted">Welcome${a.display_name ? ', ' + E(a.display_name.split(' ')[0]) : ''}</p>
      <h1 class="st-h1">Your gallery</h1>
      ${agreementCard(s)}
      <section class="st-card"><div class="st-status" data-s="${s.state}"><span class="st-dot" aria-hidden="true"></span><div>
        <h2>${E(title)}</h2><p class="st-muted" style="margin:0">${E(text)}</p>
        ${s.state === 'changes_requested' && s.last_decision?.founder_message ? `<p class="st-msg">${E(s.last_decision.founder_message)}</p>` : ''}
        ${s.state === 'live' ? `<p class="st-muted" style="margin:10px 0 0">Address: <a href="${LIVE_DOMAIN}${E(a.slug)}/" rel="noopener">plotnua.ie/plotart/artists/${E(a.slug)}/</a></p>` : ''}
        ${s.queue.some(q => q.kind === 'instant') ? `<p class="st-muted" style="margin:10px 0 0">Availability and order updates are on their way to your live gallery.</p>` : ''}
      </div></div>
      <div class="st-actions">
        <a class="st-btn" href="/preview/" target="_blank" rel="noopener">Preview your gallery</a>
        ${s.unsubmitted.length ? `<a class="st-btn st-btn--solid" href="#/submit">Review and submit (${s.unsubmitted.length})</a>` : ''}
      </div></section>

      <section class="st-card"><h3>Your works</h3>
        <p class="st-muted" style="margin:0">${n ? `${n} ${n === 1 ? 'work' : 'works'} in your gallery` : 'No works yet'}. Start with one artwork and add more whenever you wish${a.founding ? ': as a Founding Artist you have space for at least 10 at a time' : ''}.</p>
        <div class="st-actions"><a class="st-btn" href="#/works">Your works</a><button class="st-btn" data-act="add">Add an artwork</button></div></section>

      <section class="st-card" aria-labelledby="ck-h"><div class="st-ck-top"><h3 id="ck-h">Your gallery checklist</h3>${left ? `<span class="st-ck-count">${plural(left, 'detail', 'details')} to complete</span>` : ''}</div>
        ${left ? `<p class="st-muted st-ck-intro">Complete these to submit your gallery. Each one opens the right place.</p>${checklistHTML(s.checklist)}`
          : `<ul class="st-list ok"><li>Everything needed is in place${s.unsubmitted.length ? `: submit your changes for ${pendingTier}` : ''}.</li></ul>`}
        ${canSubmit ? `<div class="st-actions"><a class="st-btn st-btn--solid" href="#/submit">Review and submit</a></div>` : ''}
      </section>`;
    $('[data-act=add]', app)?.addEventListener('click', addWork);
  }

  function profile() {
    const a = ME.artist, p = ME.portrait && ME.portrait.id ? ME.portrait : null;
    app.innerHTML = `
      <h1 class="st-h1">Your profile</h1><p class="st-sub">This is how visitors meet you. Changes save as you go.</p>
      <div class="st-two"><div>
      <section class="st-card">
        ${f('display_name', 'The name you work under', a.display_name, { req: 1 })}
        ${f('practice', 'Your practice', a.practice, { hint: 'For example: Painter, Ceramicist, Printmaker' })}
        <div class="st-f"><label for="f-medium">Main medium</label><select id="f-medium" name="medium">${['', ...ME.media].map(m => `<option value="${m}"${a.medium === m ? ' selected' : ''}>${m ? E(MEDIUM[m]) : 'Choose…'}</option>`).join('')}</select></div>
        ${f('statement', 'A one-line statement (optional)', a.statement, { area: 1, hint: 'Shown large under your name. Up to 400 characters.' })}
        ${f('bio', 'Your biography', a.bio, { area: 1, hint: 'In your own words: who you are and how you work. 40–2,400 characters. A blank line starts a new paragraph.' })}
      </section></div><div>
      <section class="st-card"><h3>Portrait (optional)</h3>
        <div class="st-drop" id="pdrop">${p ? `<img src="/api/images/${p.id}/view" alt="">` : '<span>Add a portrait photograph</span><small class="st-muted">JPEG, PNG or WebP · at least 800 px</small>'}<input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload a portrait"></div>
        ${p ? `${f('palt', 'Describe your portrait', p.alt, { req: 1, hint: 'A short line for people using screen readers, e.g. “The artist in her studio”.' })}<button class="st-btn st-btn--small st-btn--danger" data-act="rmp">Remove portrait</button>` : ''}
      </section>
      <section class="st-card"><h3>Where you’re based</h3>
        <div class="st-f"><label for="f-county">County</label><select id="f-county" name="county">${['', ...ME.counties].map(c => `<option${a.county === c ? ' selected' : ''} value="${c}">${c || 'Choose…'}</option>`).join('')}</select></div>
        <label class="st-check"><input type="checkbox" name="county_public"${a.county_public ? ' checked' : ''} style="accent-color:var(--terra);width:20px;height:20px"> Show my county on my gallery</label>
      </section>
      <section class="st-card"><h3>Links (optional)</h3>
        ${f('website', 'Website', a.website, { type: 'url', hint: 'A full link starting https://' })}
        ${f('instagram', 'Instagram name', a.instagram, { hint: 'Without the @' })}
      </section></div></div>`;
    for (const el of app.querySelectorAll('[name]')) {
      if (el.name === 'palt') continue;
      el.addEventListener('change', async () => {
        const v = el.type === 'checkbox' ? el.checked : el.value;
        try { await api('PUT', '/api/me/profile', { [el.name]: v }); fieldErr(el, ''); say('Saved'); await refresh(); }
        catch (e) { fieldErr(el, e.message); say('Not saved: ' + e.message, true); }
      });
    }
    $('#pdrop input').addEventListener('change', e => uploadFlow(e.target.files[0], '/api/me/portrait', $('#pdrop'), { portrait: true, done: async () => { await refresh(); profile(); } }));
    $('[data-act=rmp]', app)?.addEventListener('click', async () => { await api('DELETE', '/api/me/portrait'); await refresh(); profile(); say('Portrait removed'); });
    $('[name=palt]', app)?.addEventListener('change', async e => { try { await api('PATCH', `/api/images/${p.id}`, { alt: e.target.value, photographer: 'self' }); say('Saved'); } catch (x) { say(x.message, true); } });
  }
  function f(name, label, val, o = {}) {
    const id = 'f-' + name;
    const rq = o.req ? ' aria-required="true"' : '';
    const input = o.area ? `<textarea id="${id}" name="${name}"${rq}>${E(val)}</textarea>` : `<input id="${id}" name="${name}" type="${o.type || 'text'}" value="${E(val)}"${o.step ? ` step="${o.step}" inputmode="decimal"` : ''}${o.type === 'number' ? ' inputmode="decimal"' : ''}${rq}>`;
    return `<div class="st-f"><label for="${id}">${E(label)}${o.req ? ' <span class="st-req">Required</span>' : ''}</label>${input}${o.hint ? `<small>${E(o.hint)}</small>` : ''}<span class="st-err" aria-live="polite"></span></div>`;
  }
  const fieldErr = (el, msg) => { const e = el.closest('.st-f')?.querySelector('.st-err'); if (e) e.textContent = msg; };

  function works() {
    const shown = WORKS.filter(w => !w.archived), arch = WORKS.filter(w => w.archived);
    const n = shown.length;
    app.innerHTML = `
      <h1 class="st-h1">Your works</h1>
      <p class="st-sub">${n} in your gallery. Add more whenever you wish. Changing availability, removing a work or changing the order updates your live gallery straight away.</p>
      <div class="st-actions" style="margin:-6px 0 16px"><button class="st-btn st-btn--solid" data-act="add">Add an artwork</button></div>
      ${n ? `<ol class="st-works">${shown.map((w, i) => workRow(w, i, n)).join('')}</ol>` : `<div class="st-card st-empty">No works yet. Add your first artwork to begin.</div>`}
      ${arch.length ? `<h2 class="st-card" style="background:none;border:0;box-shadow:none;padding:24px 0 6px;font-family:var(--serif);font-size:26px;color:var(--ivory);margin:0">Removed from your gallery</h2>
        <ol class="st-works">${arch.map(w => `<li class="st-work"><span class="st-thumb" style="${thumb(w)}"></span><div><p class="st-work-t">${E(w.title || 'Untitled')}</p>
        <div class="st-row"><button class="st-btn st-btn--small" data-restore="${w.id}">Put back in the gallery</button></div></div></li>`).join('')}</ol>` : ''}`;
    $('[data-act=add]', app).addEventListener('click', addWork);
    app.querySelectorAll('[data-av]').forEach(s => s.addEventListener('change', async () => {
      try { await api('POST', `/api/artworks/${s.dataset.av}/availability`, { availability: s.value }); say(live(WORKS.find(w => w.id === s.dataset.av)) ? 'Updated · your live gallery is updating' : 'Saved'); await refresh(); works(); }
      catch (e) { say(e.message, true); }
    }));
    app.querySelectorAll('[data-move]').forEach(b => b.addEventListener('click', async () => {
      const [id, d] = b.dataset.move.split(':'); const ids = WORKS.filter(w => !w.archived).map(w => w.id);
      const i = ids.indexOf(id), j = i + Number(d); if (j < 0 || j >= ids.length) return;
      [ids[i], ids[j]] = [ids[j], ids[i]];
      await api('POST', '/api/artworks/order', { ids: [...ids, ...WORKS.filter(w => w.archived).map(w => w.id)] }); say('Order saved'); await refresh(); works();
      $(`[data-move="${id}:${d}"]`)?.focus();
    }));
    app.querySelectorAll('[data-archive]').forEach(b => b.addEventListener('click', async () => {
      const w = WORKS.find(x => x.id === b.dataset.archive);
      if (!confirmInline(b, live(w) ? 'Remove from your live gallery?' : 'Remove this work?')) return;
      if (!live(w) && !w.images.length && !w.title) await api('DELETE', `/api/artworks/${w.id}`);
      else await api('POST', `/api/artworks/${w.id}/archive`, { archived: true });
      say('Removed'); await refresh(); works();
    }));
    app.querySelectorAll('[data-restore]').forEach(b => b.addEventListener('click', async () => { await api('POST', `/api/artworks/${b.dataset.restore}/archive`, { archived: false }); say('Back in your gallery (needs review)'); await refresh(); works(); }));
  }
  function confirmInline(btn, q) { if (btn.dataset.sure) return true; btn.dataset.sure = '1'; btn.textContent = q + ' Tap again'; setTimeout(() => { delete btn.dataset.sure; btn.textContent = 'Remove'; }, 4000); return false; }
  const thumb = w => { const m = w.images.find(i => i.role === 'main'); return m ? `background-image:url(/api/images/${m.id}/view)` : ''; };
  function needs(w) {
    const q = [];
    if (!w.images.some(i => i.role === 'main')) q.push('photo'); if (!w.title) q.push('title'); if (!w.medium) q.push('medium');
    if (!w.h_cm || !w.w_cm) q.push('size'); if (!w.ai_involvement) q.push('AI question');
    if (w.images.some(i => !i.alt || !i.photographer)) q.push('photo details'); if (w.blocked) q.push('new photo');
    return q;
  }
  function workRow(w, i, n) {
    const q = needs(w), sub = [w.year, w.medium, w.h_cm && w.w_cm ? `${+w.h_cm} × ${+w.w_cm} cm` : null].filter(Boolean).join(' · ');
    return `<li class="st-work"><a class="st-thumb" href="#/work/${w.id}" style="${thumb(w)}" aria-label="Edit ${E(w.title || 'untitled work')}">${w.images.length ? '' : 'Add photo'}</a>
      <div><p class="st-work-t"><a href="#/work/${w.id}" style="color:inherit;text-decoration:none">${E(w.title || 'Untitled')}</a></p><p class="st-work-s">${E(sub || 'Details to add')}${w.price_eur && w.availability === 'available' ? ` · €${Number(w.price_eur).toLocaleString('en-IE')}` : ''}</p>
      <div class="st-chips">${live(w) ? '<span class="st-chip st-chip--live">In your gallery</span>' : '<span class="st-chip">Not yet submitted</span>'}${q.length ? `<span class="st-chip st-chip--todo">Needs ${E(q.join(', '))}</span>` : ''}</div>
      <div class="st-row"><label class="st-lab" for="av-${w.id}" style="position:absolute;left:-999px">Availability</label><select id="av-${w.id}" data-av="${w.id}" style="width:auto">${Object.entries(AV).map(([k, v]) => `<option value="${k}"${w.availability === k ? ' selected' : ''}>${v}</option>`).join('')}</select>
      <a class="st-btn st-btn--small" href="#/work/${w.id}">Edit</a></div></div>
      <div class="st-row" style="justify-content:flex-end"><button class="st-btn st-btn--small" data-move="${w.id}:-1" ${i ? '' : 'disabled'} aria-label="Move earlier">↑</button><button class="st-btn st-btn--small" data-move="${w.id}:1" ${i < n - 1 ? '' : 'disabled'} aria-label="Move later">↓</button><button class="st-btn st-btn--small st-btn--danger" data-archive="${w.id}">Remove</button></div></li>`;
  }
  async function addWork() { const r = await api('POST', '/api/artworks'); await refresh(); location.hash = '#/work/' + r.id; }

  function work(id) {
    const w = WORKS.find(x => x.id === id);
    if (!w) { location.hash = '#/works'; return; }
    const main = w.images.find(i => i.role === 'main'), views = w.images.filter(i => i.role === 'view');
    const c = main ? main.checks : null;
    app.innerHTML = `
      <p><a href="#/works" style="color:var(--stone);text-decoration:none">← Your works</a></p>
      <h1 class="st-h1">${E(w.title || 'New artwork')}</h1>
      <p class="st-sub">${live(w) ? 'In your live gallery. Price and detail changes go to us for a quick check; new photographs are reviewed.' : 'Everything saves as you go. Submit when you’re ready.'}</p>
      <p class="st-needs" id="wneeds" aria-live="polite"></p>
      <div class="st-two"><div>
      <section class="st-card"><h3>Main photograph</h3>
        <div class="st-drop" id="mdrop">${main ? `<img src="/api/images/${main.id}/view" alt="">` : '<strong style="color:var(--ivory)">Add the main photograph</strong><span>Tap to choose a photo · JPEG, PNG or WebP · at least 2,000 px · up to 30 MB</span>'}<input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload the main photograph"></div>
        ${main ? `<ul class="st-checks"><li class="ok">${main.width} × ${main.height} px · ${(main.bytes / 1048576).toFixed(1)} MB · ${main.format.toUpperCase()}</li>${c.warns.map(x => `<li class="w">${E(x)}</li>`).join('')}<li class="ok">Shown whole: never cropped</li></ul>
          ${imageFields(main, 'Main photograph')}<p class="st-muted" style="margin:6px 0 0">To replace it, tap the photo and choose another.</p>` : '<p class="st-muted" style="margin:10px 0 0">See the photography guide: straight on, soft daylight, cropped to the edge of the work.</p>'}
      </section>
      <section class="st-card"><h3>More views (optional, up to 3)</h3><p class="st-muted" style="margin:0 0 10px">A detail, the side of a sculpture, or the work installed.${views.length ? ' <strong style="color:var(--ivory)">Each view needs its own description and photographer</strong>, just like the main photograph.' : ''}</p>
        <div class="st-views">${views.map((v, n) => `<div class="st-view" style="background-image:url(/api/images/${v.id}/view)">${photoComplete(v) ? '' : `<span class="st-view-flag" data-flag="${v.id}">View ${n + 1}: details needed</span>`}<button data-rmv="${v.id}" aria-label="Remove view ${n + 1}">✕</button></div>`).join('')}
        ${views.length < 3 ? `<label class="st-view st-drop" style="min-height:0;padding:0"><span style="font-size:28px">+</span><input type="file" accept="image/jpeg,image/png,image/webp" id="vadd" aria-label="Add a view"></label>` : ''}</div>
        ${views.map((v, n) => `<div class="st-view-d"><span class="st-view-mini" style="background-image:url(/api/images/${v.id}/view)" aria-hidden="true"></span>${imageFields(v, `View ${n + 1}`)}</div>`).join('')}
      </section></div><div>
      <section class="st-card"><h3>About the work</h3>
        ${f('title', 'Title', w.title)}
        <div class="st-grid2">${f('year', 'Year', w.year, { type: 'number' })}${f('medium', 'Medium', w.medium, { hint: 'e.g. Oil on canvas' })}</div>
        ${f('materials', 'Materials (optional)', w.materials)}
        <span class="st-lab">Size in cm</span>
        <div class="st-grid3">${f('h_cm', 'Height', w.h_cm, { type: 'number', step: '0.1' })}${f('w_cm', 'Width', w.w_cm, { type: 'number', step: '0.1' })}${f('d_cm', 'Depth', w.d_cm, { type: 'number', step: '0.1' })}</div>
        ${f('description', 'A few words about it (optional)', w.description, { area: 1 })}
      </section>
      <section class="st-card"><h3>Price and availability</h3>
        <div class="st-grid2">${f('price_eur', 'Price (€)', w.price_eur, { type: 'number' })}
        <div class="st-f"><label for="av">Availability</label><select id="av" data-avail>${Object.entries(AV).map(([k, v]) => `<option value="${k}"${w.availability === k ? ' selected' : ''}>${v}</option>`).join('')}</select></div></div>
        <label class="st-check"><input type="checkbox" name="price_on_request"${w.price_on_request ? ' checked' : ''} style="accent-color:var(--terra);width:20px;height:20px"> Show “Price on request” instead</label>
      </section>
      <section class="st-card"><h3>Did AI play a meaningful part in making this work?</h3>
        <div class="st-radio">${[['none', 'No'], ['assisted', 'Yes: AI-assisted, made by me'], ['generated', 'Yes: generated entirely from prompts']].map(([k, v]) => `<label><input type="radio" name="ai_involvement" value="${k}"${w.ai_involvement === k ? ' checked' : ''}> ${v}</label>`).join('')}</div>
        <div id="ainote" ${w.ai_involvement && w.ai_involvement !== 'none' ? '' : 'hidden'}>${f('ai_note', 'Say briefly how (shown on the work’s page)', w.ai_note, { area: 1 })}</div>
        <p class="st-muted" style="margin:6px 0 0">PlotArt welcomes digital and AI-assisted practice. Entirely prompt-generated images are reviewed for eligibility.</p>
      </section><div id="hirepanel"></div></div></div>
      <div class="st-sticky"><a class="st-btn" href="/preview/${E(w.slug)}.html" target="_blank" rel="noopener">Preview</a><a class="st-btn st-btn--solid" href="#/works">Done</a></div>`;
    app.querySelectorAll('[name]').forEach(el => {
      if (el.closest('[data-img]')) return;
      el.addEventListener('change', async () => {
        const v = el.type === 'checkbox' ? el.checked : el.type === 'radio' ? el.value : (el.value === '' ? null : el.value);
        if (el.name === 'ai_involvement') $('#ainote').hidden = v === 'none';
        try { await api('PUT', `/api/artworks/${w.id}`, { [el.name]: v }); fieldErr(el, ''); say('Saved'); await refresh(); if (el.name === 'title') $('.st-h1').textContent = el.value || 'New artwork'; }
        catch (e) { fieldErr(el, e.message); say('Not saved: ' + e.message, true); }
      });
    });
    $('[data-avail]').addEventListener('change', async e => { await api('POST', `/api/artworks/${w.id}/availability`, { availability: e.target.value }); say(live(w) ? 'Updated · your live gallery is updating' : 'Saved'); await refresh(); });
    bindImageFields();
    const needsLine = () => { const el = $('#wneeds'); if (!el) return; const it = ME.status.checklist.find(i => i.area === 'work' && i.work_id === w.id);
      el.hidden = !it; el.innerHTML = it ? `<span class="st-needs-dot" aria-hidden="true"></span>Still needed to submit: ${E(it.needs.map(c => NEED[c]).join(', '))}` : ''; };
    needsLine(); afterRefresh = needsLine;
    $('#mdrop input').addEventListener('change', e => uploadFlow(e.target.files[0], `/api/artworks/${w.id}/images?role=main`, $('#mdrop'), { done: async () => { await flushPhotoEdits(); await refresh(); work(w.id); } }));
    $('#vadd')?.addEventListener('change', e => uploadFlow(e.target.files[0], `/api/artworks/${w.id}/images?role=view`, $('#vadd').parentElement, { done: async () => { await flushPhotoEdits(); await refresh(); work(w.id); } }));
    app.querySelectorAll('[data-rmv]').forEach(b => b.addEventListener('click', async () => { await flushPhotoEdits(); await api('DELETE', `/api/images/${b.dataset.rmv}`); await refresh(); work(w.id); say('View removed'); }));
    hirePanel(w.id);
  }

  /* ------------------------------------------------------------- Art for Hire (separate, optional; Stage 3B-2)
     Shown only once Art for Hire is open (terms issued and switched on), or while a work is still offered so the artist
     can always take it off. Nothing here changes the gallery. Screen and photo choices are willingness to discuss only. */
  const HIRE = {
    availability: { now: 'Available for hire now', from: 'Available from a date', not_now: 'Not available for hire at the moment' },
    screen_use: { none: 'No', background: 'Open to discussing background use on screen', featured: 'Open to discussing featured use on screen' },
    photo_use: { none: 'No', yes: 'Open to discussing photography of the work' },
    framing: { '': 'Choose', framed: 'Framed', unframed: 'Unframed', ready_to_hang: 'Ready to hang (unframed)' },
    weight_band: { '': 'Choose', under_5kg: 'Under 5 kg', '5_15kg': '5 to 15 kg', over_15kg: 'Over 15 kg' },
    collection: { ask: 'Ask me', collect: 'Hirer collects', deliver_local: 'I can deliver locally' },
    review: { draft: 'Off', pending: 'Waiting for PlotArt to check', approved: 'Checked', declined: 'Not accepted' } };
  async function hirePanel(workId) {
    const box = $('#hirepanel'); if (!box) return;
    let H;
    try { H = await api('GET', '/api/hire'); } catch { return; }                    // not installed: nothing shown
    const it = H.works.find(x => x.artwork_id === workId);
    if (!it || (!H.active && !it.hire.offered)) {
      if (H.enabled && H.terms && it) box.innerHTML = `<section class="st-card"><h3>Commercial hire (optional)</h3><p class="st-muted" style="margin:0">Art for Hire is separate from your gallery and from your Founding Artist agreement. ${H.left ? 'You have left Art for Hire.' : 'To take part, read and accept the Art for Hire Artist Terms first.'} <a href="#/hire">Art for Hire</a></p></section>`;
      return;
    }
    const h = it.hire, sel = (k, map) => `<select name="hire_${k}" id="hire_${k}">${Object.entries(map).map(([v, t]) => `<option value="${v}"${String(h[k] ?? '') === v ? ' selected' : ''}>${E(t)}</option>`).join('')}</select>`;
    box.innerHTML = `<section class="st-card" aria-labelledby="hireh"><h3 id="hireh">Commercial hire (optional)</h3>
      <p class="st-muted" style="margin:0 0 10px">Separate from your gallery. Off unless you switch it on. PlotArt checks each work before it is listed, and you can take it off at any time.</p>
      <label class="st-check"><input type="checkbox" name="hire_offered"${h.offered ? ' checked' : ''} ${!it.published && !h.offered ? 'disabled' : ''} style="accent-color:var(--terra);width:20px;height:20px"> Offer this work for commercial hire</label>
      ${!it.published && !h.offered ? '<p class="st-muted">Only works already published in your gallery can be offered.</p>' : ''}
      <p class="st-muted" style="margin:6px 0 10px">Status: <strong>${E(h.offered ? HIRE.review[h.review_state] : 'Off')}</strong>${it.listed ? ' · listed' : ''}${h.review_state === 'declined' && h.decline_reason ? ` · ${E(h.decline_reason)}` : ''}</p>
      <div ${h.offered ? '' : 'hidden'} id="hirefields">
        <div class="st-f"><label for="hire_availability">Hire availability</label>${sel('availability', HIRE.availability)}</div>
        <div class="st-f" ${h.availability === 'from' ? '' : 'hidden'} id="hirefrom"><label for="hire_available_from">Available from</label><input type="date" id="hire_available_from" name="hire_available_from" value="${E(h.available_from || '')}"></div>
        <div class="st-f"><label for="hire_county">County where the work is kept</label><input type="text" id="hire_county" name="hire_county" maxlength="40" value="${E(h.county || '')}"></div>
        <div class="st-grid2"><div class="st-f"><label for="hire_framing">Framing</label>${sel('framing', HIRE.framing)}</div><div class="st-f"><label for="hire_weight_band">Weight</label>${sel('weight_band', HIRE.weight_band)}</div></div>
        <div class="st-grid2"><div class="st-f"><label for="hire_collection">Collection</label>${sel('collection', HIRE.collection)}</div>
          <div class="st-f" ${h.collection === 'deliver_local' ? '' : 'hidden'} id="hirekm"><label for="hire_deliver_km">Delivery distance (km)</label><input type="number" min="1" max="500" id="hire_deliver_km" name="hire_deliver_km" value="${E(h.deliver_km ?? '')}"></div></div>
        <div class="st-f"><label for="hire_handling_note">Handling note (private: shared only with a hirer you agree to)</label><textarea id="hire_handling_note" name="hire_handling_note" maxlength="280">${E(h.handling_note || '')}</textarea></div>
        <div class="st-f"><label for="hire_screen_use">Screen use (film, TV or video)</label>${sel('screen_use', HIRE.screen_use)}</div>
        <div class="st-f"><label for="hire_photo_use">Photography</label>${sel('photo_use', HIRE.photo_use)}</div>
        <p class="st-muted" style="margin:6px 0 0"><strong>${E(H.notice)}</strong> ${E(H.pilot_notice)}</p>
      </div></section>`;
    box.querySelectorAll('[name^="hire_"]').forEach(el => el.addEventListener('change', async () => {
      const k = el.name.slice(5);
      let v = el.type === 'checkbox' ? el.checked : (el.value === '' ? null : el.value);
      if (k === 'offered' && !v && !confirm('Take this work off hire now? It stops being listed at once. Your gallery is not affected.')) { el.checked = true; return; }
      const body = { [k]: v };
      if (k === 'availability' && v === 'from') { $('#hirefrom').hidden = false; if (!$('#hire_available_from').value) return; body.available_from = $('#hire_available_from').value; }
      if (k === 'available_from') body.availability = 'from';
      try { const r = await api('PUT', `/api/hire/artwork/${workId}`, body); say(r.review_state === 'pending' ? 'Saved · PlotArt will check it before it is listed' : 'Saved'); hirePanel(workId); }
      catch (e) { say('Not saved: ' + e.message, true); hirePanel(workId); }
    }));
  }
  async function hireView() {
    let H;
    try { H = await api('GET', '/api/hire'); } catch { H = null; }
    if (!H || !H.enabled || !H.terms) { app.innerHTML = '<div class="st-card"><h2>Art for Hire</h2><p class="st-muted">Art for Hire is not open yet.</p></div>'; return; }
    app.innerHTML = `<h1 class="st-h1">Art for Hire</h1>
      <p class="st-sub">Optional, and separate from your gallery and your Founding Artist agreement. PlotArt only introduces hirers to you; any hire, fee, replacement value or screen-use permission is agreed between you and the hirer.</p>
      <section class="st-card"><h3>${E(H.terms.title)} <span class="st-muted">(${E(H.terms.doc_id)})</span></h3>
        <p><a href="/hire-terms/${E(H.terms.doc_id)}.pdf" target="_blank" rel="noopener">Read the Art for Hire Artist Terms (PDF)</a></p>
        ${H.active ? `<p class="ok">You accepted these terms on ${E(new Date(H.accepted_at).toLocaleDateString('en-IE'))}.</p>
          <label class="st-check"><input type="checkbox" id="lv"> I want to leave Art for Hire. All my works come off hire at once; my gallery is not affected.</label>
          <button class="st-btn st-btn--danger" id="lvb" disabled>Leave Art for Hire</button>`
        : `<label class="st-check"><input type="checkbox" id="acc"> ${E(H.statement)}</label><button class="st-btn st-btn--solid" id="accb" disabled>Accept</button>`}
        <p class="st-err" id="herr" aria-live="polite"></p></section>
      <div id="hirereports"></div>`;
    const pair = (c, b, fn) => { const x = $(c), y = $(b); if (!x) return; x.addEventListener('change', () => { y.disabled = !x.checked; });
      y.addEventListener('click', async () => { y.disabled = true; try { await fn(); await hireView(); } catch (e) { $('#herr').textContent = e.message; y.disabled = !x.checked; } }); };
    pair('#acc', '#accb', async () => { await api('POST', '/api/hire/accept', { confirm: true, doc_id: H.terms.doc_id }); say('Accepted'); });
    pair('#lv', '#lvb', async () => { await api('POST', '/api/hire/leave', { confirm: true }); say('You have left Art for Hire'); });
    await hireReports();
  }
  /* Report a hire (PA-AFH r5 clause 6.5): only the artist's own hire introductions, once paid. Commission is worked out by
     PlotArt from the enquiry log; a hire introduced in the founding year shows "no commission". Invoicing is by email. */
  const BASIS = { commission: 'Commission', founding_year: 'No commission: founding year', outside_window: 'No commission: more than 12 months after the introduction', no_fee: 'No commission: no fee' };
  const INV = { not_invoiced: 'Not yet invoiced', invoiced: 'Invoiced', no_commission: 'No commission due', disputed: 'Under review', superseded: 'Replaced by a correction' };
  const PAY = { unpaid: 'Not paid', paid: 'Paid', not_due: 'Nothing to pay', refunded: 'Refunded' };
  const euro = c => '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  async function hireReports() {
    const box = $('#hirereports'); if (!box) return;
    let R; try { R = await api('GET', '/api/hire/reports'); } catch { return; }
    if (!R.installed || !R.accepted) return;
    const intro = new Map(R.introductions.map(i => [i.reference, i]));
    const opt = i => `<option value="${E(i.reference)}">${E(i.reference)} · ${E(new Date(i.introduced_on + 'T12:00:00Z').toLocaleDateString('en-IE'))}${i.artwork_title ? ' · ' + E(i.artwork_title) : ''}${i.protected ? ' · Founding year: no commission' : ''}</option>`;
    box.innerHTML = `<section class="st-card" aria-labelledby="rph"><h2 id="rph">Report a hire</h2>
      <p class="st-muted" style="margin-top:0">When a hire that came from a PlotArt hire enquiry has been paid, report it here within 14 days. PlotArt charges 10% of the hire fee, not counting VAT or separately itemised costs such as transport, insurance and installation. <b>Hires introduced during your founding year carry no commission.</b> PlotArt sends any invoice by email; nothing is charged here.</p>
      ${R.introductions.length ? `<form id="rpf" novalidate>
        <input type="hidden" id="rp-corrects" value="">
        <p class="st-muted" id="rp-corr" hidden></p>
        <div class="st-f"><label for="rp-ref">Hire enquiry</label><select id="rp-ref">${R.introductions.map(opt).join('')}</select>
          <small id="rp-prot" class="st-muted"></small></div>
        <fieldset class="st-req-group"><legend class="st-lab">Work or works hired</legend>
          ${R.works.map(w => `<label class="st-check"><input type="checkbox" name="rp-w" value="${E(w.id)}"> ${E(w.title || 'Untitled')}</label>`).join('')}</fieldset>
        <div class="st-f"><label for="rp-agreed">Date hire agreed</label><input type="date" id="rp-agreed" aria-describedby="rp-agreed-h">
          <small id="rp-agreed-h" class="st-muted">The day you and the hirer agreed this hire. It decides whether the hire falls within 12 months of PlotArt’s introduction.</small></div>
        <div class="st-grid2"><div class="st-f"><label for="rp-start">Hire starts</label><input type="date" id="rp-start"></div>
          <div class="st-f"><label for="rp-end">Hire ends</label><input type="date" id="rp-end"></div></div>
        <p class="st-muted" id="rp-dates" aria-live="polite"></p>
        <div class="st-f"><label for="rp-fee">Hire fee received (€), excluding VAT and itemised costs</label><input type="text" id="rp-fee" inputmode="decimal" autocomplete="off" placeholder="e.g. 450.00" aria-describedby="rp-calc">
          <small id="rp-calc" class="st-muted" aria-live="polite"></small></div>
        <fieldset class="st-req-group"><legend class="st-lab">Is more of the fee still to be paid?</legend><div class="st-radio">
          <label><input type="radio" name="rp-more" value="no" checked> No</label><label><input type="radio" name="rp-more" value="yes"> Yes, this is an instalment</label></div></fieldset>
        <label class="st-check"><input type="checkbox" id="rp-paid"> I have received payment of this fee.</label>
        <button class="st-btn st-btn--solid" id="rp-go" type="submit" disabled>Report this hire</button>
        <p class="st-err" id="rp-err" aria-live="polite"></p></form>`
      : '<p class="st-muted">There are no hire enquiries from PlotArt to report yet.</p>'}
      ${R.reports.length ? `<h3>Your reports</h3><div class="st-scroll"><table class="st-table"><thead><tr><th>Reported</th><th>Enquiry</th><th>Hire</th><th>Fee</th><th>Commission</th><th>Status</th><th></th></tr></thead><tbody>
        ${R.reports.map(r => `<tr><td>${E(new Date(r.reported_at).toLocaleDateString('en-IE'))}</td><td>${E(r.reference)}${r.corrects ? '<br><span class="st-muted">correction</span>' : ''}</td><td>${E(r.hire_start)} to ${E(r.hire_end)}<br><span class="st-muted">agreed ${E(r.agreed_on)}${r.starts_before_introduction ? ' · starts before the introduction' : ''}</span></td>
          <td>${euro(r.net_fee_cents)}${r.more_to_pay ? '<br><span class="st-muted">instalment</span>' : ''}</td><td>${r.basis === 'commission' ? euro(r.commission_cents) : E(BASIS[r.basis])}</td>
          <td>${r.corrected_by ? 'Replaced by a correction' : `${E(INV[r.invoice_status] || '')}<br><span class="st-muted">${E(PAY[r.payment_status] || '')}</span>`}</td>
          <td>${r.corrected_by ? '' : `<button class="st-btn" type="button" data-corr="${E(r.id)}" data-ref="${E(r.reference)}">Correct</button>`}</td></tr>`).join('')}</tbody></table></div>` : ''}
    </section>`;
    const f = $('#rpf'); if (!f) return;
    const ref = $('#rp-ref'), fee = $('#rp-fee'), paid = $('#rp-paid'), go = $('#rp-go');
    const cents = () => { const v = fee.value.trim().replace(/,/g, ''); return /^\d{1,7}(\.\d{1,2})?$/.test(v) ? Math.round(Number(v) * 100) : null; };
    const dmy = v => new Date(v + 'T12:00:00Z').toLocaleDateString('en-IE');
    const dates = () => {   // says what PlotArt will make of the dates; the Studio checks them again when the report is sent
      const i = intro.get(ref.value), ag = $('#rp-agreed').value, st = $('#rp-start').value, en = $('#rp-end').value, today = new Date().toISOString().slice(0, 10), msg = [];
      if (i && ag && ag < i.introduced_on) msg.push(`The hire can’t have been agreed before PlotArt introduced this hirer on ${dmy(i.introduced_on)}. Check the date or the enquiry.`);
      else if (ag && ag > today) msg.push('The date the hire was agreed can’t be in the future.');
      else if (i && ag && !i.protected && ag > i.window_ends) msg.push(`Agreed more than 12 months after the introduction: no commission on this hire.`);
      if (st && en && en < st) msg.push('The hire can’t end before it starts.');
      if (i && st && st < i.introduced_on) msg.push(`The hire period starts before PlotArt’s introduction (${dmy(i.introduced_on)}). You can still report it; PlotArt will check it with you.`);
      $('#rp-dates').textContent = msg.join(' ');
      return i && ag && (ag < i.introduced_on || ag > today) || (st && en && en < st);
    };
    const sync = () => {
      const i = intro.get(ref.value);
      $('#rp-prot').textContent = i ? (i.protected ? 'Introduced during your founding year: no commission on this hire or its follow-on hires.' : `Introduced on ${new Date(i.introduced_on + 'T12:00:00Z').toLocaleDateString('en-IE')}. Hires with this hirer until ${new Date(i.window_ends + 'T12:00:00Z').toLocaleDateString('en-IE')} carry commission.`) : '';
      const c = cents(), ag = $('#rp-agreed').value, late = i && !i.protected && ag && ag > i.window_ends;
      $('#rp-calc').textContent = c === null ? '' : i && i.protected ? 'No commission (founding year).' : late ? 'No commission (agreed more than 12 months after the introduction).' : c === 0 ? 'No commission (no fee).' : `Commission at 10%: ${euro(Math.round(c / 10))}. PlotArt confirms it when invoicing.`;
      const blocked = dates();
      go.disabled = !paid.checked || !!blocked;
    };
    const pickWorks = () => { const i = intro.get(ref.value); f.querySelectorAll('[name=rp-w]').forEach(x => { x.checked = !!i && x.value === i.artwork_id; }); };
    ref.addEventListener('change', () => { pickWorks(); sync(); }); fee.addEventListener('input', sync); paid.addEventListener('change', sync);
    ['#rp-agreed', '#rp-start', '#rp-end'].forEach(x => $(x).addEventListener('input', sync));
    pickWorks(); sync();
    box.querySelectorAll('[data-corr]').forEach(b => b.addEventListener('click', () => {
      $('#rp-corrects').value = b.dataset.corr; ref.value = b.dataset.ref; pickWorks(); sync();
      const n = $('#rp-corr'); n.hidden = false; n.textContent = 'Correcting an earlier report: enter the details as they should be. The earlier report stays on record, marked as replaced.';
      ref.focus();
    }));
    f.addEventListener('submit', async e => {
      e.preventDefault(); $('#rp-err').textContent = '';
      const c = cents(); if (c === null) { $('#rp-err').textContent = 'Give the fee in euro, for example 450 or 450.00.'; fee.focus(); return; }
      const works = [...f.querySelectorAll('[name=rp-w]:checked')].map(x => x.value);
      go.disabled = true;
      try {
        const r = await api('POST', '/api/hire/reports', { reference: ref.value, artwork_ids: works, agreed_on: $('#rp-agreed').value, hire_start: $('#rp-start').value, hire_end: $('#rp-end').value, net_fee_cents: c,
          more_to_pay: f.querySelector('[name=rp-more]:checked').value === 'yes', payment_received: paid.checked, corrects: $('#rp-corrects').value || null });
        say(r.report.basis === 'commission' ? `Reported · commission ${euro(r.report.commission_cents)}` : 'Reported · no commission'); await hireReports();
      } catch (err) { $('#rp-err').textContent = err.message; go.disabled = !paid.checked; }
    });
  }
  /* Photograph details (11 Nov 2026 reliability fix). Every photograph, main or extra view, needs its own description and
     photographer before a gallery can be submitted (the server's rule, unchanged). Here:
     · the description and photographer's name save as you type (a moment after you stop) as well as when you leave the field,
       and anything still unsaved is saved BEFORE the page is redrawn (after an upload), before moving to another page and
       when the app is put in the background, so typed text is never silently lost;
     · each photograph shows a status that stays until the next save: "Saved", or "Not saved" with a Retry button;
     · a field is only ever sent when the artist changed it, so nothing previously saved is overwritten. */
  const photoComplete = i => !!(i.alt && i.photographer && (i.photographer !== 'other_with_permission' || i.photo_credit));
  const PENDING = new Map();            // `${imageId}:${field}` → { id, field, value, box }
  const MIN = { alt: 5, photo_credit: 2 };
  function imageFields(i, label = 'Photograph') {
    const done = photoComplete(i);
    return `<div data-img="${i.id}" class="st-photo-d" data-alt="${E(i.alt || '')}" data-who="${E(i.photographer || '')}" data-credit-saved="${E(i.photo_credit || '')}">
      <p class="st-photo-h">${E(label)} details <span class="st-chip ${done ? 'st-chip--live' : 'st-chip--todo'}" data-badge>${done ? 'Complete' : 'Needed to submit'}</span></p>
      <div class="st-f"><label for="alt-${i.id}">Describe the photo <span class="st-req">Required</span></label><input id="alt-${i.id}" name="alt" type="text" value="${E(i.alt)}" aria-required="true" aria-describedby="alth-${i.id}" placeholder="e.g. Blue abstract painting with a yellow circle"><small id="alth-${i.id}">A short line for people using screen readers.</small><span class="st-err" aria-live="polite"></span></div>
      <fieldset class="st-req-group"><legend class="st-lab">Who took this photograph? <span class="st-req">Required</span></legend>
      <div class="st-radio" style="margin:6px 0 10px">${[['self', 'I did'], ['other_with_permission', 'Another photographer, with their permission']].map(([k, v]) => `<label><input type="radio" name="photographer-${i.id}" value="${k}"${i.photographer === k ? ' checked' : ''}> ${v}</label>`).join('')}</div></fieldset>
      <div class="st-f" ${i.photographer === 'other_with_permission' ? '' : 'hidden'} data-credit><label for="cr-${i.id}">Photographer’s name <span class="st-req">Required</span></label><input id="cr-${i.id}" name="photo_credit" type="text" value="${E(i.photo_credit)}" aria-required="true" aria-describedby="crh-${i.id}"><small id="crh-${i.id}">Shown as the photo credit on your gallery.</small><span class="st-err" aria-live="polite"></span></div>
      <p class="st-photo-s" data-pstat role="status" aria-live="polite">${done ? '' : 'Not complete yet'}</p></div>`;
  }
  const savedOf = (box, field) => field === 'alt' ? box.dataset.alt : field === 'photographer' ? box.dataset.who : box.dataset.creditSaved;
  function setSaved(box, field, value) { if (field === 'alt') box.dataset.alt = value; else if (field === 'photographer') box.dataset.who = value; else box.dataset.creditSaved = value; }
  function paint(box, state, msg) {
    const st = box.querySelector('[data-pstat]'), done = photoComplete({ alt: box.dataset.alt, photographer: box.dataset.who, photo_credit: box.dataset.creditSaved });
    const badge = box.querySelector('[data-badge]');
    badge.textContent = done ? 'Complete' : 'Needed to submit'; badge.className = `st-chip ${done ? 'st-chip--live' : 'st-chip--todo'}`;
    const flag = app.querySelector(`[data-flag="${box.dataset.img}"]`); if (flag) flag.hidden = done;
    st.className = 'st-photo-s' + (state === 'bad' ? ' bad' : state === 'ok' ? ' ok' : '');
    if (state === 'bad') { st.innerHTML = `Not saved: ${E(msg)} <button type="button" class="st-btn st-btn--small" data-retry>Retry</button>`; st.querySelector('[data-retry]').onclick = () => flushPhotoEdits(); }
    else if (state === 'saving') st.textContent = 'Saving…';
    else if (state === 'ok') st.textContent = `Saved ${new Date().toLocaleTimeString('en-IE', { hour: '2-digit', minute: '2-digit' })}${done ? ' · this photograph is complete' : ' · still needed: ' + [!box.dataset.alt && 'a description', !box.dataset.who && 'who took it', box.dataset.who === 'other_with_permission' && !box.dataset.creditSaved && 'the photographer’s name'].filter(Boolean).join(', ')}`;
  }
  async function saveField(id, field, value, box) {
    const key = `${id}:${field}`;
    PENDING.set(key, { id, field, value, box });
    if (box && box.isConnected) paint(box, 'saving');
    try {
      await api('PATCH', `/api/images/${id}`, { [field]: value });
      const cur = PENDING.get(key); if (cur && cur.value === value) PENDING.delete(key);   // a newer edit stays pending
      const live = app.querySelector(`[data-img="${id}"]`) || box;
      if (live) { setSaved(live, field, value); const el = field === 'photographer' ? null : live.querySelector(`[name="${field}"]`); if (el) fieldErr(el, ''); if (live.isConnected) paint(live, 'ok'); }
      try { await refresh(); } catch { /* the save itself succeeded */ }
      return true;
    } catch (e) {
      const live = app.querySelector(`[data-img="${id}"]`) || box;
      if (live && live.isConnected) { const el = field === 'photographer' ? null : live.querySelector(`[name="${field}"]`); if (el) fieldErr(el, e.message); paint(live, 'bad', e.message); }
      say('Not saved: ' + e.message, true);
      return false;
    }
  }
  // Save every photograph edit not yet saved (typed text included). Called before any redraw or navigation.
  async function flushPhotoEdits() {
    app.querySelectorAll('[data-img] input[type=text]').forEach(el => {
      const box = el.closest('[data-img]'), v = el.value.trim();
      if (v !== (savedOf(box, el.name) || '') && v.length >= MIN[el.name]) PENDING.set(`${box.dataset.img}:${el.name}`, { id: box.dataset.img, field: el.name, value: v, box });
    });
    let ok = true;
    for (const p of [...PENDING.values()]) ok = (await saveField(p.id, p.field, p.value, p.box)) && ok;
    return ok;
  }
  window.addEventListener('beforeunload', e => { if (PENDING.size || [...app.querySelectorAll('[data-img] input[type=text]')].some(el => el.value.trim() !== (savedOf(el.closest('[data-img]'), el.name) || ''))) { e.preventDefault(); e.returnValue = ''; } });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flushPhotoEdits(); });
  function bindImageFields() {
    app.querySelectorAll('[data-img]').forEach(box => {
      const id = box.dataset.img;
      box.querySelectorAll('input[type=radio]').forEach(el => el.addEventListener('change', () => {
        const cr = box.querySelector('[data-credit]'); cr.hidden = el.value !== 'other_with_permission';
        if (!cr.hidden && !cr.querySelector('input').value) setTimeout(() => cr.querySelector('input').focus(), 0);
        saveField(id, 'photographer', el.value, box);
      }));
      box.querySelectorAll('input[type=text]').forEach(el => {
        let t = null;
        const go = force => { clearTimeout(t); const v = el.value.trim();
          if (v === (savedOf(box, el.name) || '')) return;            // unchanged: nothing is sent
          if (!force && v.length < MIN[el.name]) return;              // still typing a very short value: wait for the field to be left
          saveField(id, el.name, force && !v ? '' : v, box); };
        el.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => go(false), 900); });
        el.addEventListener('change', () => go(true));
      });
    });
  }

  /* Checks in the browser first (instant feedback), then the Studio checks again; a preview copy is made here too. */
  async function uploadFlow(file, url, drop, { portrait = false, done }) {
    if (!file) return;
    const show = (html) => { drop.querySelectorAll(':scope > :not(input)').forEach(n => n.remove()); drop.insertAdjacentHTML('afterbegin', html); };
    const fail = msgs => { show(`<ul class="st-checks">${msgs.map(m => `<li class="b">${E(m)}</li>`).join('')}</ul><span class="st-muted">Tap to choose another photo</span>`); say('Photo not added', true); };
    if (file.size > 30 * 1048576) return fail([`This file is ${(file.size / 1048576).toFixed(1)} MB; the limit is 30 MB.`]);
    const head = new Uint8Array(await file.slice(0, 12).arrayBuffer());
    const fmt = head[0] === 0xFF && head[1] === 0xD8 ? 'jpeg' : head[0] === 0x89 && head[1] === 0x50 ? 'png' : (String.fromCharCode(...head.slice(8, 12)) === 'WEBP' ? 'webp' : null);
    if (!fmt) return fail(['This isn’t a JPEG, PNG or WebP photo. iPhone users: share or export the photo as JPEG, or set Camera › Formats › Most Compatible.']);
    let bmp;
    try { bmp = await createImageBitmap(file); } catch { return fail(['This photo couldn’t be opened. It may be damaged; try exporting it again.']); }
    const long = Math.max(bmp.width, bmp.height), min = portrait ? 800 : (ME.min_long_edge || 2000);
    if (long < min) return fail([`This photo is ${long} px on its long edge; at least ${min.toLocaleString('en-IE')} px is needed. Upload the full-size original, not a screenshot or a copy from social media or email.`]);
    show(`<span>Uploading…</span><span class="st-bar"><span></span></span>`);
    const s = Math.min(1, 1600 / long), cv = document.createElement('canvas');
    cv.width = Math.round(bmp.width * s); cv.height = Math.round(bmp.height * s);
    cv.getContext('2d').drawImage(bmp, 0, 0, cv.width, cv.height);
    const preview = await new Promise(r => cv.toBlob(r, 'image/jpeg', 0.86));
    const r = await new Promise(resolve => {
      const x = new XMLHttpRequest(); x.open('PUT', url); x.setRequestHeader('X-Studio', '1');
      x.upload.onprogress = e => { const b = drop.querySelector('.st-bar span'); if (b && e.lengthComputable) b.style.width = Math.round(e.loaded / e.total * 100) + '%'; };
      x.onload = () => { let j = {}; try { j = JSON.parse(x.responseText); } catch {} resolve({ status: x.status, j }); };
      x.onerror = () => resolve({ status: 0, j: { error: 'No connection. Try again in a moment.' } });
      x.send(file);
    });
    if (r.status !== 200 || !r.j.ok) return fail(r.j.blocks || [r.j.error || 'That didn’t work. Please try again.']);
    await api('PUT', `/api/images/${r.j.id}/preview`, undefined, preview).catch(() => {});
    say(r.j.warns?.length ? 'Photo added · see the note' : 'Photo added');
    await done();
  }

  function submitView() {
    const s = ME.status, groups = { full: [], light: [], instant: [] };
    for (const c of s.changes) groups[c.tier].push(c);
    const label = { full: 'Reviewed by PlotArt', light: 'Quick check', instant: 'Already live (no review needed)' };
    app.innerHTML = `
      <p><a href="#/" style="color:var(--stone);text-decoration:none">← Your gallery</a></p>
      <h1 class="st-h1">Review and submit</h1>
      ${s.state === 'in_review' ? `<p class="st-msg">You submitted on ${new Date(s.pending.created_at).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' })}. Submitting again replaces that submission with everything as it is now.</p>` : ''}
      <section class="st-card"><h3>What changes</h3>
        ${['full', 'light', 'instant'].filter(t => groups[t].length).map(t => `<p class="st-muted" style="margin:12px 0 4px"><span class="st-tier ${t}">${t === 'full' ? 'Review' : t === 'light' ? 'Quick check' : 'Live'}</span>${label[t]}</p>
          <ul class="st-list">${groups[t].map(c => `<li>${E(c.what)}${c.from !== undefined && c.to !== undefined && typeof c.to !== 'object' ? ` <span class="st-muted">(${E(c.from ?? '—')} → ${E(c.to ?? '—')})</span>` : ''}</li>`).join('')}</ul>`).join('') || '<p class="st-muted">Nothing new to submit.</p>'}
      </section>
      ${s.checklist.length ? `<section class="st-card" aria-labelledby="todo-h"><div class="st-ck-top"><h3 id="todo-h">Still to do</h3><span class="st-ck-count">${plural(s.checklist.length, 'detail', 'details')}</span></div>${checklistHTML(s.checklist, { openWorks: true })}</section>` : ''}
      ${s.agreement && s.agreement.installed && !s.agreement.accepted && s.tier === 'full' ? `<section class="st-card st-agr-ask"><h3>${s.agreement.founding ? 'Founding Artist Agreement' : 'Gallery Publication and Image Licence'}</h3>
        <p class="st-muted" style="margin:0">Changes that we review need ${s.agreement.founding ? 'the Founding Artist Agreement' : 'the current licence'} accepted first. It takes a few minutes and you can download a copy.</p>
        <div class="st-actions"><a class="st-btn st-btn--solid st-btn--small" href="#/agreement">Read and accept</a></div></section>` : ''}
      <section class="st-card"><div class="st-f"><label for="note">A note for us (optional)</label><textarea id="note" placeholder="Anything we should know"></textarea></div>
        <div class="st-actions st-submit-row"><a class="st-btn" href="/preview/" target="_blank" rel="noopener">Preview first</a><button class="st-btn st-btn--solid" id="go" ${s.unsubmitted.length && !s.problems.length ? '' : 'disabled aria-describedby="why"'}>Submit for review</button></div>
        ${s.problems.length ? `<p class="st-why" id="why"><span class="st-needs-dot" aria-hidden="true"></span><span><b>${plural(s.problems.length, 'detail still needs', 'details still need')} your attention</b> before you can submit your gallery. <a href="#todo-h" data-jump>See the list</a></span></p>`
          : !s.unsubmitted.length ? '<p class="st-why" id="why">There’s nothing new to submit.</p>' : ''}
        <p class="st-err" id="serr"></p></section>`;
    $('[data-jump]', app)?.addEventListener('click', e => { e.preventDefault(); const h = $('#todo-h'); h.setAttribute('tabindex', '-1'); h.scrollIntoView({ block: 'start' }); h.focus({ preventScroll: true }); });
    $('#go').addEventListener('click', async () => {
      $('#go').disabled = true;
      try { await api('POST', '/api/submit', { note: $('#note').value || null }); say('Submitted'); await refresh(); location.hash = '#/'; }
      catch (e) { $('#serr').textContent = e.message; $('#go').disabled = false; }
    });
  }

  async function enquiries() {
    const items = (await api('GET', '/api/enquiries')).items;
    const when = t => new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' });
    app.innerHTML = `<h1 class="st-h1">Enquiries</h1><p class="st-sub">Buyers who contact you through your gallery. Each one is also emailed to you; reply to the buyer directly. Any sale is agreed between you and the buyer.</p>
      ${items.length ? `<ul class="st-works">${items.map(e => `<li class="st-work" style="grid-template-columns:minmax(0,1fr)"><div>
        <p class="st-work-t">${e.kind === 'hire' ? '<span style="display:inline-block;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--terra);margin-right:6px">Hire enquiry</span>' : ''}${E(e.buyer_name)}${e.kind === 'hire' ? ` · ${E(e.role)}, ${E(e.business)}` : ''}</p><p class="st-work-s">${when(e.created_at)} · ${E(e.artwork_title || 'Your work in general')} · ${E(e.reference)}${e.business_url ? ` · ${E(e.business_url)}` : ''}</p>
        <p class="st-muted" style="white-space:pre-wrap;color:var(--lime);margin:0 0 10px">${E(e.message)}</p>
        ${e.kind === 'hire' ? '<p class="st-muted" style="margin:0 0 10px">A hire, not a sale. You agree any fee, insurance, transport and return with the hirer, in writing. Screen and photo use is never included unless you agree it in writing.</p>' : ''}
        <a class="st-btn st-btn--small st-btn--solid" href="mailto:${encodeURIComponent(e.buyer_email)}?subject=${encodeURIComponent('Re: your PlotArt enquiry ' + e.reference)}">Reply to ${E(e.buyer_email)}</a></div></li>`).join('')}</ul>`
        : '<div class="st-card st-empty">No enquiries yet. They’ll appear here when buyers contact you through your gallery.</div>'}`;
  }

  /* ------------------------------------------------------------- Founding Artist Agreement (development 6 Nov 2026)
     One page with both documents in full, a PDF of each, an optional legal name and ONE tick for both. The page sends
     the fingerprint of the exact text it displayed; the server refuses anything that is not the current text. */
  const DOCNAME = { 'PA-FAA-2026-11': 'Founding Artist Agreement', 'PA-GPIL-2026-11': 'Gallery Publication and Image Licence', 'PA-GPIL-2026-10-29': 'Gallery Publication and Image Licence' };
  const day = d => d ? new Date(d + 'T12:00:00Z').toLocaleDateString('en-IE', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Dublin' }) : '';
  const irish = t => t ? new Date(t).toLocaleString('en-IE', { dateStyle: 'long', timeStyle: 'short', timeZone: 'Europe/Dublin' }) : '';
  function agreementCard(s) {
    const g = s.agreement;
    if (!g || !g.installed) return '';
    const what = g.founding ? 'the Founding Artist Agreement' : 'the Gallery Publication and Image Licence';
    if (g.accepted) return `<section class="st-card st-agr-ok"><h3>${g.founding ? 'Founding Artist Agreement' : 'Gallery Publication and Image Licence'} · accepted</h3>
      <p class="st-muted" style="margin:0">Accepted ${E(irish(g.accepted_at))}.${g.founding_year ? ` Your founding year: ${E(day(g.founding_year.start))} to ${E(day(g.founding_year.end))}.` : g.founding ? ' Your founding year starts on the day your gallery is first published.' : ''}</p>
      <div class="st-actions"><a class="st-btn st-btn--small" href="#/agreement">View or download</a></div></section>`;
    const published = !!g.first_published_at;
    return `<section class="st-card st-agr-ask" aria-labelledby="agr-h"><h2 id="agr-h">${published ? 'Please read and accept ' + what : 'Before you submit: ' + what}</h2>
      <p class="st-muted" style="margin:0">${published
        ? 'Your gallery stays live and nothing changes in the meantime: you can keep editing, marking works sold or reserved, and withdrawing works as usual. You’ll need to accept it before you next submit new works, photographs or profile changes for review.'
        : 'Read it and accept it here before you submit your gallery for the first time. It takes a few minutes, and you can download a copy to keep.'}</p>
      <div class="st-actions"><a class="st-btn st-btn--solid" href="#/agreement">Read and accept</a></div></section>`;
  }
  async function sha256Hex(text) { return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(b => b.toString(16).padStart(2, '0')).join(''); }
  async function agreementView() {
    const g = await api('GET', '/api/agreement');
    const fy = g.founding_year;
    const earlier = g.history.filter(r => r.method === 'migrated_from_artists_table');
    const mine = g.history.filter(r => r.method === 'studio_checkbox');
    const record = mine.length ? `<section class="st-card st-agr-ok" aria-labelledby="rec-h"><h2 id="rec-h">Your acceptance</h2>
      <dl class="st-dl">
        <dt>Accepted</dt><dd>${E(irish(mine[mine.length - 1].accepted_at))} (Irish time) in PlotArt Studio</dd>
        <dt>Documents</dt><dd>${mine.filter(r => r.accepted_at === mine[mine.length - 1].accepted_at).map(r => `${E(DOCNAME[r.doc_id] || r.doc_id)}, ${E(r.doc_id)}<br><span class="st-muted st-fp">Fingerprint ${E(r.doc_sha256.slice(0, 16))}…</span>`).join('<br>')}</dd>
        <dt>Your name</dt><dd>${E(mine[mine.length - 1].display_name)}${mine[mine.length - 1].legal_name ? ` · legal name ${E(mine[mine.length - 1].legal_name)}` : ''}${mine[mine.length - 1].corrections.length ? `<br><span class="st-muted st-fp">Corrected ${E(irish(mine[mine.length - 1].corrections.slice(-1)[0].corrected_at))}: ${E(mine[mine.length - 1].corrections.slice(-1)[0].reason)}. Your original acceptance record is kept unchanged.</span>` : ''}</dd>
        <dt>Studio account</dt><dd>${E(mine[mine.length - 1].account_email)}</dd>
        ${g.founding ? `<dt>Founding year</dt><dd>${fy ? `${E(day(fy.start))} to ${E(day(fy.end))}` : 'Starts on the day your gallery is first published'}</dd>` : ''}
      </dl></section>` : '';
    const docs = g.documents;
    app.innerHTML = `
      <p><a href="#/" style="color:var(--stone);text-decoration:none">← Your gallery</a></p>
      <h1 class="st-h1">${g.founding ? 'Founding Artist Agreement' : 'Image licence'}</h1>
      <p class="st-sub">${g.accepted ? 'You have accepted these documents. You can read or download them at any time.' : `Please read ${docs.length > 1 ? 'both documents' : 'the document'} below. ${g.founding ? 'The agreement includes the image licence, so one tick accepts both.' : ''} You can download a PDF of each to keep.`}</p>
      ${record}
      ${g.founding && !g.accepted ? `<section class="st-card"><h3>In short</h3><ul class="st-list">
        <li>No membership, subscription or listing fees, ever.</li>
        <li>No commission in your founding year${fy ? ` (${E(day(fy.start))} to ${E(day(fy.end))})` : ', which starts on the day your gallery is first published'}, and enquiries from that year stay commission-free for good.</li>
        <li>Nothing changes automatically afterwards: any commission would apply only if you choose to accept new terms.</li>
        <li>You keep your copyright and handle your own sales. You can withdraw any work at any time.</li>
      </ul><p class="st-muted" style="margin:10px 0 0">This summary isn’t part of the agreement: the full text below is what you accept.</p></section>` : ''}
      ${docs.map(d => `<section class="st-card st-docwrap" aria-labelledby="h-${E(d.id)}">
        <div class="st-doc-top"><h2 id="h-${E(d.id)}">${E(DOCNAME[d.id] || d.title)}</h2><span class="st-muted">${E(d.id)}</span></div>
        <div class="st-doc" tabindex="0" role="region" aria-label="${E(DOCNAME[d.id] || d.title)}, full text" data-doc="${E(d.id)}"><p class="st-muted">Loading…</p></div>
        <div class="st-actions"><a class="st-btn st-btn--small" href="/agreements/${E(d.id)}.pdf" download>Download PDF</a><a class="st-btn st-btn--small" href="/agreements/${E(d.id)}.html" target="_blank" rel="noopener">Open in a new tab ↗</a></div></section>`).join('')}
      ${!g.accepted ? `<section class="st-card st-accept" aria-labelledby="acc-h"><h2 id="acc-h">Accept</h2>
        <div class="st-f"><label for="legal">Legal name (optional)</label><input id="legal" type="text" autocomplete="name" maxlength="120">
          <p class="st-hint">Only if it differs from the name you work under (${E(ME.artist.display_name)}). It’s kept with your acceptance record and never published.</p></div>
        <label class="st-check st-accept-box"><input type="checkbox" id="agree" style="accent-color:var(--terra);width:22px;height:22px;margin-top:2px"> <span>${E(g.statement)}</span></label>
        <div class="st-actions"><button class="st-btn st-btn--solid" id="accept" disabled>Accept</button></div>
        <p class="st-muted" style="margin:10px 0 0">PlotArt Studio records the date and time, the exact versions and their fingerprints, your Studio account and your name, and keeps them with a copy of each document you can download.</p>
        <p class="st-err" id="aerr" role="alert"></p></section>` : ''}
      ${g.leave ? `<section class="st-card st-leave" aria-labelledby="lv-h"><h3 id="lv-h">Leaving PlotArt</h3>
        ${g.leave.request ? `<p class="st-msg">You asked to leave on ${E(irish(g.leave.request.at))}. PlotArt will remove your gallery from plotnua.ie by ${E(day(new Date(g.leave.request.due).toLocaleDateString('en-CA', { timeZone: 'Europe/Dublin' })))} and confirm by email.</p>
          <div class="st-actions"><button class="st-btn st-btn--small" id="lv-undo">Withdraw my request</button></div>`
        : `<p class="st-muted" style="margin:0 0 10px">You can leave at any time. PlotArt then removes your gallery from plotnua.ie within 14 days. Your original photographs and Studio details are deleted 12 months after you leave, or sooner if you ask. The record of what you accepted and of enquiries is kept for six years, without buyer details, then deleted. Copies of published images stay in PlotArt’s private website history, which is not public.</p>
          <div class="st-f"><label for="lv-why">Anything you’d like to tell us (optional)</label><input id="lv-why" type="text" maxlength="280"></div>
          <label class="st-check"><input type="checkbox" id="lv-ok" style="accent-color:var(--terra);width:20px;height:20px"> I want to leave PlotArt and have my gallery removed.</label>
          <div class="st-actions"><button class="st-btn st-btn--small st-btn--danger" id="lv-go">Ask to leave</button></div>`}
        <p class="st-err" id="lv-err" role="alert"></p></section>` : ''}
      ${earlier.length ? `<section class="st-card"><h3>Earlier record</h3><ul class="st-list">${earlier.map(r => `<li>${E(DOCNAME[r.doc_id] || r.doc_id)}, version ${E(r.doc_id)}, accepted ${E(irish(r.accepted_at))}. This earlier version was accepted with a short summary and its version label; the record is kept exactly as it was made.</li>`).join('')}</ul></section>` : ''}`;
    const shown = {};
    await Promise.all(docs.map(async d => {
      const box = app.querySelector(`.st-doc[data-doc="${d.id}"]`);
      try {
        const r = await fetch(`/agreements/${d.id}.html`, { credentials: 'same-origin' }), t = await r.text();
        shown[d.id] = await sha256Hex(t);
        const art = new DOMParser().parseFromString(t, 'text/html').querySelector('article');
        art.querySelectorAll('.eyebrow, h1').forEach(n => n.remove());
        art.querySelectorAll('[id]').forEach(n => n.removeAttribute('id'));   // both texts share clause numbers
        box.innerHTML = art.innerHTML;
      } catch { box.innerHTML = '<p class="st-err">The document couldn’t be loaded. Please reload the page.</p>'; }
    }));
    $('#lv-go')?.addEventListener('click', async () => {
      if (!$('#lv-ok').checked) { $('#lv-err').textContent = 'Tick the box to confirm.'; return; }
      try { await api('POST', '/api/leave', { confirm: true, reason: $('#lv-why').value.trim() || null }); say('Request received'); agreementView(); } catch (e) { $('#lv-err').textContent = e.message; }
    });
    $('#lv-undo')?.addEventListener('click', async () => { try { await api('POST', '/api/leave/withdraw', {}); say('Request withdrawn'); agreementView(); } catch (e) { $('#lv-err').textContent = e.message; } });
    const box = $('#agree'), btn = $('#accept');
    if (!box) return;
    box.addEventListener('change', () => { btn.disabled = !box.checked; });
    btn.addEventListener('click', async () => {
      if (!box.checked) return;
      btn.disabled = true; $('#aerr').textContent = '';
      try {
        await api('POST', '/api/agreement/accept', { accept: true, documents: shown, statement: g.statement, legal_name: $('#legal').value.trim() || null });
        say('Accepted'); await refresh(); agreementView();
      } catch (e) { $('#aerr').textContent = e.message; btn.disabled = !box.checked; }
    });
  }

  /* ------------------------------------------------------------- router */
  async function render() {
    await flushPhotoEdits();
    const full = location.hash || '#/', [h, qs] = full.split('?'), q = new URLSearchParams(qs || '');
    afterRefresh = null;
    document.querySelectorAll('.st-tabs a').forEach(a => a.toggleAttribute('aria-current', h === a.getAttribute('href') || (a.getAttribute('href') === '#/works' && h.startsWith('#/work/'))));
    document.querySelectorAll('.st-tabs a[aria-current]').forEach(a => a.setAttribute('aria-current', 'page'));
    try {
      if (!ME) await refresh();
      $('#who').innerHTML = `${E(ME.artist.display_name)}<br><a href="/cdn-cgi/access/logout">Sign out</a>`;
      if (h === '#/') dashboard();
      else if (h === '#/profile') profile();
      else if (h === '#/works') works();
      else if (h.startsWith('#/work/')) work(h.slice(7));
      else if (h === '#/submit') submitView();
      else if (h === '#/enquiries') await enquiries();
      else if (h === '#/agreement') await agreementView();
      else if (h === '#/hire') await hireView();
      else dashboard();
      window.scrollTo(0, 0);
      if (q.get('fix')) requestAnimationFrame(() => focusFix(q.get('fix'), q.get('img')));
    } catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();
