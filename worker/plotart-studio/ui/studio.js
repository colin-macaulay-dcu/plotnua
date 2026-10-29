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
  const refresh = async () => { ME = await api('GET', '/api/me'); WORKS = (await api('GET', '/api/artworks')).works; };
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
    const n = s.counts.works, min = s.counts.min, pct = min ? Math.min(100, Math.round(n / min * 100)) : 100;
    const canSubmit = s.unsubmitted.length && !s.problems.length && s.state !== 'in_review';
    const pendingTier = s.tier === 'light' ? 'a quick check' : 'a review';
    app.innerHTML = `
      <p class="st-muted">Welcome${a.display_name ? ', ' + E(a.display_name.split(' ')[0]) : ''}</p>
      <h1 class="st-h1">Your gallery</h1>
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

      ${min ? `<section class="st-card"><h3>Your works</h3>
        <div class="st-prog" role="progressbar" aria-valuemin="0" aria-valuemax="${min}" aria-valuenow="${Math.min(n, min)}" aria-label="Works in your gallery"><span style="width:${pct}%"></span></div>
        <p class="st-muted" style="margin:0">${n} of at least ${min} works${n >= min ? ' · you can add more at any time' : ''}</p>
        ${s.below_minimum ? `<p class="st-msg">Your gallery now shows ${n} works. Founding galleries keep at least ${min}: please add a new work by ${new Date(s.top_up_by).toLocaleDateString('en-IE', { day: 'numeric', month: 'long' })}. Your gallery stays live meanwhile.</p>` : ''}
        <div class="st-actions"><a class="st-btn" href="#/works">Your works</a><button class="st-btn" data-act="add">Add an artwork</button></div></section>` : ''}

      <section class="st-card"><h3>${s.problems.length ? 'Before you submit' : 'Ready'}</h3>
        ${s.problems.length ? `<ul class="st-list">${s.problems.slice(0, 8).map(p => `<li>${E(p)}</li>`).join('')}</ul>${s.problems.length > 8 ? `<p class="st-muted">and ${s.problems.length - 8} more</p>` : ''}`
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
        ${p ? `${f('palt', 'Describe your portrait (for screen readers)', p.alt)}<button class="st-btn st-btn--small st-btn--danger" data-act="rmp">Remove portrait</button>` : ''}
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
    const input = o.area ? `<textarea id="${id}" name="${name}">${E(val)}</textarea>` : `<input id="${id}" name="${name}" type="${o.type || 'text'}" value="${E(val)}"${o.step ? ` step="${o.step}" inputmode="decimal"` : ''}${o.type === 'number' ? ' inputmode="decimal"' : ''}>`;
    return `<div class="st-f"><label for="${id}">${E(label)}${o.req ? '' : ''}</label>${input}${o.hint ? `<small>${E(o.hint)}</small>` : ''}<span class="st-err" aria-live="polite"></span></div>`;
  }
  const fieldErr = (el, msg) => { const e = el.closest('.st-f')?.querySelector('.st-err'); if (e) e.textContent = msg; };

  function works() {
    const shown = WORKS.filter(w => !w.archived), arch = WORKS.filter(w => w.archived);
    const n = shown.length, min = ME.status.counts.min;
    app.innerHTML = `
      <h1 class="st-h1">Your works</h1>
      <p class="st-sub">${n} in your gallery${min ? ` · at least ${min} for a Founding gallery, and as many more as you like` : ''}. Changing availability, removing a work or changing the order updates your live gallery straight away.</p>
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
      <div class="st-two"><div>
      <section class="st-card"><h3>Main photograph</h3>
        <div class="st-drop" id="mdrop">${main ? `<img src="/api/images/${main.id}/view" alt="">` : '<strong style="color:var(--ivory)">Add the main photograph</strong><span>Tap to choose a photo · JPEG, PNG or WebP · at least 2,000 px · up to 30 MB</span>'}<input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload the main photograph"></div>
        ${main ? `<ul class="st-checks"><li class="ok">${main.width} × ${main.height} px · ${(main.bytes / 1048576).toFixed(1)} MB · ${main.format.toUpperCase()}</li>${c.warns.map(x => `<li class="w">${E(x)}</li>`).join('')}<li class="ok">Shown whole: never cropped</li></ul>
          ${imageFields(main)}<p class="st-muted" style="margin:6px 0 0">To replace it, tap the photo and choose another.</p>` : '<p class="st-muted" style="margin:10px 0 0">See the photography guide: straight on, soft daylight, cropped to the edge of the work.</p>'}
      </section>
      <section class="st-card"><h3>More views (optional, up to 3)</h3><p class="st-muted" style="margin:0 0 10px">A detail, the side of a sculpture, or the work installed.</p>
        <div class="st-views">${views.map(v => `<div class="st-view" style="background-image:url(/api/images/${v.id}/view)"><button data-rmv="${v.id}" aria-label="Remove this view">✕</button></div>`).join('')}
        ${views.length < 3 ? `<label class="st-view st-drop" style="min-height:0;padding:0"><span style="font-size:28px">+</span><input type="file" accept="image/jpeg,image/png,image/webp" id="vadd" aria-label="Add a view"></label>` : ''}</div>
        ${views.map(v => `<details style="margin-top:10px"><summary class="st-muted">Details for view ${views.indexOf(v) + 1}</summary>${imageFields(v)}</details>`).join('')}
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
      </section></div></div>
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
    $('#mdrop input').addEventListener('change', e => uploadFlow(e.target.files[0], `/api/artworks/${w.id}/images?role=main`, $('#mdrop'), { done: async () => { await refresh(); work(w.id); } }));
    $('#vadd')?.addEventListener('change', e => uploadFlow(e.target.files[0], `/api/artworks/${w.id}/images?role=view`, $('#vadd').parentElement, { done: async () => { await refresh(); work(w.id); } }));
    app.querySelectorAll('[data-rmv]').forEach(b => b.addEventListener('click', async () => { await api('DELETE', `/api/images/${b.dataset.rmv}`); await refresh(); work(w.id); say('View removed'); }));
  }
  function imageFields(i) {
    return `<div data-img="${i.id}" style="margin-top:12px">
      <div class="st-f"><label for="alt-${i.id}">Describe the photo (for screen readers)</label><input id="alt-${i.id}" name="alt" type="text" value="${E(i.alt)}" placeholder="e.g. Blue abstract painting with a yellow circle"><span class="st-err"></span></div>
      <span class="st-lab">Who took this photograph?</span>
      <div class="st-radio" style="margin:6px 0 10px">${[['self', 'I did'], ['other_with_permission', 'Another photographer, with their permission']].map(([k, v]) => `<label><input type="radio" name="photographer-${i.id}" value="${k}"${i.photographer === k ? ' checked' : ''}> ${v}</label>`).join('')}</div>
      <div class="st-f" ${i.photographer === 'other_with_permission' ? '' : 'hidden'} data-credit><label for="cr-${i.id}">Photographer’s name (for the credit)</label><input id="cr-${i.id}" name="photo_credit" type="text" value="${E(i.photo_credit)}"><span class="st-err"></span></div></div>`;
  }
  function bindImageFields() {
    app.querySelectorAll('[data-img]').forEach(box => {
      const id = box.dataset.img;
      box.querySelectorAll('input').forEach(el => el.addEventListener('change', async () => {
        const key = el.type === 'radio' ? 'photographer' : el.name;
        if (key === 'photographer') box.querySelector('[data-credit]').hidden = el.value !== 'other_with_permission';
        try { await api('PATCH', `/api/images/${id}`, { [key]: el.value }); fieldErr(el, ''); say('Saved'); await refresh(); }
        catch (e) { fieldErr(el, e.message); say('Not saved: ' + e.message, true); }
      }));
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
      ${s.problems.length ? `<section class="st-card"><h3>Still to do</h3><ul class="st-list">${s.problems.map(p => `<li>${E(p)}</li>`).join('')}</ul></section>` : ''}
      ${!s.licence_ok ? `<section class="st-card"><h3>Gallery Publication and Image Licence</h3>
        <p class="st-muted">You keep your copyright. This licence lets PlotArt show the work and words you approve, on your gallery and PlotArt pages, and nothing more. Version ${E(s.licence_version)}.</p>
        <label class="st-check"><input type="checkbox" id="lic" style="accent-color:var(--terra);width:22px;height:22px;margin-top:2px"> I approve my PlotArt gallery preview and accept the Gallery Publication and Image Licence, version ${E(s.licence_version)}.</label></section>` : ''}
      <section class="st-card"><div class="st-f"><label for="note">A note for us (optional)</label><textarea id="note" placeholder="Anything we should know"></textarea></div>
        <div class="st-actions"><a class="st-btn" href="/preview/" target="_blank" rel="noopener">Preview first</a><button class="st-btn st-btn--solid" id="go" ${s.unsubmitted.length && !s.problems.length ? '' : 'disabled'}>Submit for review</button></div>
        <p class="st-err" id="serr"></p></section>`;
    $('#go').addEventListener('click', async () => {
      const lic = $('#lic');
      if (lic && !lic.checked) { $('#serr').textContent = 'Please accept the licence to submit.'; return; }
      $('#go').disabled = true;
      try { await api('POST', '/api/submit', { note: $('#note').value || null, accept_licence: !!lic }); say('Submitted'); await refresh(); location.hash = '#/'; }
      catch (e) { $('#serr').textContent = e.message; $('#go').disabled = false; }
    });
  }

  async function enquiries() {
    const items = (await api('GET', '/api/enquiries')).items;
    const when = t => new Date(t).toLocaleString('en-IE', { dateStyle: 'medium', timeStyle: 'short' });
    app.innerHTML = `<h1 class="st-h1">Enquiries</h1><p class="st-sub">Buyers who contact you through your gallery. Each one is also emailed to you; reply to the buyer directly. Any sale is agreed between you and the buyer.</p>
      ${items.length ? `<ul class="st-works">${items.map(e => `<li class="st-work" style="grid-template-columns:minmax(0,1fr)"><div>
        <p class="st-work-t">${E(e.buyer_name)}</p><p class="st-work-s">${when(e.created_at)} · ${E(e.artwork_title || 'Your work in general')} · ${E(e.reference)}</p>
        <p class="st-muted" style="white-space:pre-wrap;color:var(--lime);margin:0 0 10px">${E(e.message)}</p>
        <a class="st-btn st-btn--small st-btn--solid" href="mailto:${encodeURIComponent(e.buyer_email)}?subject=${encodeURIComponent('Re: your PlotArt enquiry ' + e.reference)}">Reply to ${E(e.buyer_email)}</a></div></li>`).join('')}</ul>`
        : '<div class="st-card st-empty">No enquiries yet. They’ll appear here when buyers contact you through your gallery.</div>'}`;
  }

  /* ------------------------------------------------------------- router */
  async function render() {
    const h = location.hash || '#/';
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
      else dashboard();
      window.scrollTo(0, 0);
    } catch (e) { app.innerHTML = `<div class="st-card"><h2>Something went wrong</h2><p class="st-muted">${E(e.message)}</p></div>`; }
  }
  addEventListener('hashchange', render);
  render();
})();
