/* PlotArt · Founding 25 application · live submission · v3 (29 Oct 2026: artwork images)
 * ==========================================================================
 * Copied into plotart/assets/ by build-plotart.py ONLY when the form is live
 * (application state "open" with the approved endpoint, or an isolated test
 * build). Otherwise this file is not published.
 *
 * Sends ONE POST to the Founding 25 Worker route with exactly the keys the
 * route allows. The three confirmations are read from the page as rendered,
 * so the Worker can compare them with the approved wording.
 *  - Nothing is stored in the browser (no cookies, no local storage).
 *  - Nothing is logged, and no analytics event carries any detail.
 *  - A random submission id is made once per application and kept until it
 *    succeeds; a retry reuses it, so a double click or a retry after a dropped
 *    connection cannot create a second record.
 *  - A filled honeypot is treated as a bot: success is shown, nothing is sent.
 *  - Inputs are checked here for the applicant's convenience; the Worker
 *    checks everything again and is the only authority.
 *  - Artwork images (v3): up to five, added by drag and drop, the file picker
 *    (which offers the photo library on a phone) or paste. Each is re-drawn in
 *    the browser (at most 2,400 px on the long side, JPEG), which also removes
 *    camera and location data, then uploaded at once to the Worker's private
 *    holding area. Only the images still shown when the application is sent
 *    are attached to it.
 * ======================================================================== */
(function () {
  var form = document.querySelector('form[data-f25-form]');
  if (!form) return;
  var ENDPOINT = form.getAttribute('data-endpoint');
  var status = form.querySelector('[data-f25-status]');
  var button = form.querySelector('button[type="submit"]');
  var label = button.querySelector('[data-f25-label]');
  var done = document.querySelector('[data-f25-done]');
  var TIMEOUT_MS = 20000;
  var submissionId = null;
  var sending = false;
  var IMG_ENDPOINT = form.getAttribute('data-image-endpoint');
  var MAX_IMAGES = 5, MIN_IMAGES = 3, LONG_EDGE = 2400, MAX_RAW = 40 * 1024 * 1024;
  var TYPES = { 'image/jpeg': 1, 'image/png': 1, 'image/webp': 1 };
  var images = [];          /* {key, url, id, state: 'uploading'|'done'|'error', note} in the order shown */
  var nextKey = 1, replacing = null;

  var el = function (n) { return form.elements[n]; };
  var sentence = function (k) {
    var s = document.querySelector('[data-f25-sentence="' + k + '"]');
    return s ? s.textContent.replace(/\s+/g, ' ').trim() : '';
  };
  var HTTPS = /^https:\/\/[^\s\/:@]+\.[a-z]{2,}(?:[\/?#][^\s]*)?$/i;
  /* "yourwebsite.ie/work" is fine: https:// is added (and http:// upgraded), as the Worker does. */
  function link(t) { t = (t || '').trim(); if (!t) return ''; if (/^http:\/\//i.test(t)) return 'https://' + t.slice(7); return /^[a-z][a-z0-9+.-]*:/i.test(t) ? t : 'https://' + t.replace(/^\/+/, ''); }
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var HANDLE = /^@?[A-Za-z0-9._]{1,60}$/;

  /* Worker field -> [form control, message] */
  var MSG = {
    artist_name: ['artist_name', 'Please enter the name you work under.'],
    email: ['email', 'Please enter a valid email address, like name@example.com.'],
    region: ['region', 'Please choose the county where you live or work.'],
    medium: ['medium', 'Please choose your primary medium.'],
    bio: ['bio', 'Please write a short biography of at least 40 characters (up to 1,000).'],
    portfolio: ['portfolio', 'Please add at least three images of your work, or a link to an online portfolio.'],
    images: ['portfolio', 'Something went wrong with one of your images. Please remove it and add it again.'],
    website: ['website', 'Please check your website address, for example yourwebsite.ie'],
    social_link: ['social_link', 'Please enter an @handle, or a link to your profile.'],
    additional_info: ['additional_info', 'Please keep this to 800 characters or fewer.'],
    eligibility_text: ['eligibility', 'Please confirm you are 18 or over and based or working on the island of Ireland.'],
    ownership_text: ['ownership', 'Please confirm the work is your own, or that you are authorised to represent the artist.'],
    privacy_text: ['privacy', 'Please confirm you have read the privacy notice for applications.']
  };
  var ERR_ID = { artist_name: 'name', email: 'email', region: 'region', medium: 'medium', bio: 'bio', portfolio: 'portfolio', images: 'images',
                 website: 'website', social_link: 'social', additional_info: 'info',
                 eligibility_text: 'eligibility', ownership_text: 'ownership', privacy_text: 'privacy' };

  function setError(key, on, text) {
    var input = el(MSG[key][0]);
    var p = document.getElementById('f25-' + ERR_ID[key] + '-e');
    if (!input || !p) return;
    if (on) { input.setAttribute('aria-invalid', 'true'); p.textContent = text || MSG[key][1]; p.hidden = false; }
    else { input.removeAttribute('aria-invalid'); p.textContent = ''; p.hidden = true; }
  }
  function show(msg, state) {
    status.hidden = false;
    status.classList.add('is-on');
    status.textContent = msg;
    status.setAttribute('data-state', state);
  }
  function clearStatus() { status.hidden = true; status.classList.remove('is-on'); status.textContent = ''; status.removeAttribute('data-state'); }

  function v(n) { return (el(n).value || '').trim(); }
  function problems() {
    var bad = [];
    if (!v('artist_name')) bad.push('artist_name');
    if (!EMAIL.test(v('email'))) bad.push('email');
    if (!v('region')) bad.push('region');
    if (!v('medium')) bad.push('medium');
    var b = v('bio'); if (b.length < 40 || b.length > 1000) bad.push('bio');
    var done = images.filter(function (i) { return i.state === 'done'; }).length;
    if (v('portfolio') ? !HTTPS.test(link(v('portfolio'))) : done < MIN_IMAGES) bad.push('portfolio');
    if (v('website') && !HTTPS.test(link(v('website')))) bad.push('website');
    if (v('social_link') && !(HANDLE.test(v('social_link')) || HTTPS.test(link(v('social_link'))))) bad.push('social_link');
    if (v('additional_info').length > 800) bad.push('additional_info');
    if (!el('eligibility').checked) bad.push('eligibility_text');
    if (!el('ownership').checked) bad.push('ownership_text');
    if (!el('privacy').checked) bad.push('privacy_text');
    return bad;
  }
  function uuid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    var b = new Uint8Array(16); crypto.getRandomValues(b);
    b[6] = (b[6] & 15) | 64; b[8] = (b[8] & 63) | 128;
    var h = Array.prototype.map.call(b, function (x) { return (x + 256).toString(16).slice(1); }).join('');
    return h.slice(0, 8) + '-' + h.slice(8, 12) + '-' + h.slice(12, 16) + '-' + h.slice(16, 20) + '-' + h.slice(20);
  }
  function payload() {
    var b = {
      artist_name: v('artist_name'), email: v('email'), region: v('region'), medium: v('medium'),
      bio: el('bio').value.trim(),
      eligibility_text: sentence('eligibility'), ownership_text: sentence('ownership'), privacy_text: sentence('privacy'),
      submission_id: submissionId
    };
    if (v('portfolio')) b.portfolio = link(v('portfolio'));
    var ids = images.filter(function (i) { return i.state === 'done'; }).map(function (i) { return i.id; });
    if (ids.length) b.images = ids;
    if (v('website')) b.website = link(v('website'));
    if (v('social_link')) b.social_link = HANDLE.test(v('social_link')) ? v('social_link') : link(v('social_link'));
    if (v('additional_info')) b.additional_info = el('additional_info').value.trim();
    return b;
  }
  function busy(on) {
    sending = on;
    button.disabled = on;
    button.setAttribute('aria-busy', on ? 'true' : 'false');
    label.textContent = on ? 'Sending your application' : 'Send my application';
  }
  function succeed() {
    done.querySelector('[data-f25-done-email]').textContent = v('email');
    form.hidden = true;
    done.hidden = false;
    done.focus();
    form.reset();
    submissionId = null;
    images.forEach(function (i) { URL.revokeObjectURL(i.url); }); images = []; drawImages();
  }

  /* ---------------------------------------------------------------- images */
  var drop = form.querySelector('[data-f25-drop]'), picker = form.querySelector('[data-f25-file]');
  var thumbs = form.querySelector('[data-f25-thumbs]'), live = form.querySelector('[data-f25-up-live]');
  var imgErr = document.getElementById('f25-images-e');
  function imageNote(t) { imgErr.textContent = t || ''; imgErr.hidden = !t; }
  function say(t) { live.textContent = t; }
  function drawImages() {
    thumbs.innerHTML = '';
    images.forEach(function (im, n) {
      var li = document.createElement('li'); li.setAttribute('data-state', im.state);
      var img = document.createElement('img'); img.src = im.url; img.alt = 'Your image ' + (n + 1); li.appendChild(img);
      var s = document.createElement('span'); s.className = 'pa-thumb-s';
      s.textContent = im.state === 'uploading' ? 'Uploading…' : im.state === 'error' ? 'Not uploaded' : String(n + 1); li.appendChild(s);
      var a = document.createElement('div'); a.className = 'pa-thumb-a';
      [['Replace', function () { replacing = im.key; picker.multiple = false; picker.click(); }], ['Remove', function () { remove(im.key); }]].forEach(function (x) {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = x[0];
        b.setAttribute('aria-label', x[0] + ' image ' + (n + 1)); b.addEventListener('click', x[1]); a.appendChild(b);
      });
      li.appendChild(a); thumbs.appendChild(li);
    });
    drop.classList.toggle('is-full', images.length >= MAX_IMAGES);
    var done = images.filter(function (i) { return i.state === 'done'; }).length;
    say(images.length ? done + ' of ' + MAX_IMAGES + ' images added' + (done < MIN_IMAGES && !v('portfolio') ? ' · add at least ' + MIN_IMAGES + ', or a portfolio link below' : '') : '');
    if (done >= MIN_IMAGES && el('portfolio').getAttribute('aria-invalid') === 'true') setError('portfolio', false);
  }
  function remove(key) {
    images = images.filter(function (i) { if (i.key === key) { URL.revokeObjectURL(i.url); return false; } return true; });
    imageNote(''); drawImages();
  }
  /* Re-draw at no more than LONG_EDGE px as a JPEG: smaller uploads, and no camera or location data. */
  function prepare(file) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file), im = new Image();
      im.onload = function () {
        var w = im.naturalWidth, h = im.naturalHeight;
        if (w < 200 || h < 200) { URL.revokeObjectURL(url); reject('small'); return; }
        var k = Math.min(1, LONG_EDGE / Math.max(w, h)), c = document.createElement('canvas');
        c.width = Math.round(w * k); c.height = Math.round(h * k);
        var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(im, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        c.toBlob(function (b) { b ? resolve(b) : reject('read'); }, 'image/jpeg', 0.86);
      };
      im.onerror = function () { URL.revokeObjectURL(url); reject('read'); };
      im.src = url;
    });
  }
  function upload(im, blob) {
    if (!submissionId) submissionId = uuid();
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, 60000);
    return fetch(IMG_ENDPOINT + '?s=' + encodeURIComponent(submissionId), { method: 'POST', headers: { 'content-type': 'image/jpeg' }, body: blob,
      credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer', signal: ctl ? ctl.signal : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) { clearTimeout(timer); if (j && j.state === 'stored' && j.id) { im.id = j.id; im.state = 'done'; } else { im.state = 'error'; im.note = j && j.state; } })
      .catch(function () { clearTimeout(timer); im.state = 'error'; im.note = 'network'; })
      .then(function () {
        if (im.state === 'error') imageNote(im.note === 'not_open' ? "Applications aren't open at the moment, so your image wasn't sent." :
          im.note === 'slow_down' ? 'Lots of images at once: please wait a moment, then remove the image and add it again.' :
          "One of your images couldn't be uploaded. Please remove it and add it again, or check your connection.");
        drawImages();
      });
  }
  function addFiles(list) {
    imageNote('');
    var files = Array.prototype.slice.call(list || []), skipped = [];
    files.forEach(function (f) {
      if (!TYPES[f.type]) { skipped.push((f.name || 'That file') + ' isn\'t a JPG, PNG or WebP image'); return; }
      if (f.size > MAX_RAW) { skipped.push((f.name || 'That image') + ' is too large (over 40 MB)'); return; }
      var slot = null;
      if (replacing !== null) { slot = images.filter(function (i) { return i.key === replacing; })[0] || null; replacing = null; }
      if (!slot && images.length >= MAX_IMAGES) { skipped.push('You can add up to five images'); return; }
      var im = { key: nextKey++, url: URL.createObjectURL(f), id: null, state: 'uploading' };
      if (slot) { URL.revokeObjectURL(slot.url); images[images.indexOf(slot)] = im; } else images.push(im);
      drawImages();
      prepare(f).then(function (b) { return upload(im, b); }, function (why) {
        images = images.filter(function (i) { return i !== im; }); URL.revokeObjectURL(im.url); drawImages();
        imageNote(why === 'small' ? 'That image is too small to show your work (at least 200 pixels on each side).' : "We couldn't read one of those images. Please try a JPG, PNG or WebP.");
      });
    });
    replacing = null; picker.multiple = true;
    if (skipped.length) imageNote(skipped.filter(function (x, i, a) { return a.indexOf(x) === i; }).join('. ') + '.');
  }
  drop.addEventListener('click', function () { replacing = null; picker.multiple = true; picker.click(); });
  drop.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); drop.click(); } });
  picker.addEventListener('change', function () { addFiles(picker.files); picker.value = ''; });
  ['dragenter', 'dragover'].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add('is-over'); }); });
  ['dragleave', 'dragend'].forEach(function (t) { drop.addEventListener(t, function () { drop.classList.remove('is-over'); }); });
  drop.addEventListener('drop', function (e) { e.preventDefault(); drop.classList.remove('is-over'); addFiles(e.dataTransfer && e.dataTransfer.files); });
  /* Paste an image anywhere on the form (text fields still paste text). */
  form.addEventListener('paste', function (e) {
    var items = e.clipboardData && e.clipboardData.files;
    if (items && items.length && Array.prototype.some.call(items, function (f) { return /^image\//.test(f.type); })) {
      e.preventDefault(); addFiles(Array.prototype.filter.call(items, function (f) { return /^image\//.test(f.type); }));
    }
  });
  el('portfolio').addEventListener('input', drawImages);

  /* Bio character count (not announced on every keystroke). */
  var bio = el('bio'), count = document.getElementById('f25-bio-c');
  bio.addEventListener('input', function () {
    count.textContent = bio.value.trim().length.toLocaleString('en-IE') + ' of 1,000 characters';
  });
  /* Clear a field's error as soon as it is corrected. */
  Object.keys(MSG).forEach(function (k) {
    var input = el(MSG[k][0]);
    if (!input) return;
    input.addEventListener(input.type === 'checkbox' || input.tagName === 'SELECT' ? 'change' : 'blur', function () {
      if (input.getAttribute('aria-invalid') === 'true' && problems().indexOf(k) === -1) setError(k, false);
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (sending) return;                                                     /* double click */
    if (images.some(function (i) { return i.state === 'uploading'; })) { show('Your images are still uploading. Please wait a moment, then send again.', 'retry'); return; }
    if (el('nickname') && el('nickname').value) { succeed(); return; }      /* honeypot */
    Object.keys(MSG).forEach(function (k) { setError(k, false); });
    var bad = problems();
    if (bad.length) {
      bad.forEach(function (k) { setError(k, true); });
      show(bad.length === 1 ? 'Please check the highlighted field.' : 'Please check the ' + bad.length + ' highlighted fields.', 'error');
      el(MSG[bad[0]][0]).focus();
      return;
    }
    if (!submissionId) submissionId = uuid();
    busy(true);
    clearStatus();
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, TIMEOUT_MS);
    fetch(ENDPOINT, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload()),
                      credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer', signal: ctl ? ctl.signal : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (j) {
        clearTimeout(timer);
        busy(false);
        if (j && j.state === 'received') { succeed(); return; }
        if (j && j.state === 'refused' && j.field === 'images') {
          imageNote(MSG.images[1]); show('Please check your images and try again.', 'error');
        } else if (j && j.state === 'refused' && MSG[j.field]) {
          setError(j.field, true);
          show('Please check the highlighted field and try again.', 'error');
          el(MSG[j.field][0]).focus();
        } else if (j && j.state === 'refused') {
          show("Something in the form didn't go through. Please reload the page and try again, or email hello@plotnua.ie.", 'error');
        } else if (j && j.state === 'not_open') {
          show("Applications aren't open at the moment, so nothing was sent. Please check back later.", 'error');
        } else if (j && j.state === 'slow_down') {
          show("We're receiving a lot of applications right now. Your details are still here: please try again a little later.", 'retry');
        } else {
          show('Something went wrong on our side, and your application may not have been sent. Your details are still here: please try again in a moment.', 'retry');
        }
      })
      .catch(function () {
        clearTimeout(timer);
        busy(false);
        show("We couldn't reach PlotArt, so your application may not have been sent. Your details are still here: check your connection and press Send again.", 'retry');
      });
  });
})();
