/* PlotArt · Founding 25 application · live submission · v2 (28 Oct 2026)
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

  var el = function (n) { return form.elements[n]; };
  var sentence = function (k) {
    var s = document.querySelector('[data-f25-sentence="' + k + '"]');
    return s ? s.textContent.replace(/\s+/g, ' ').trim() : '';
  };
  var HTTPS = /^https:\/\/[^\s\/:@]+\.[a-z]{2,}(?:[\/?#][^\s]*)?$/i;
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var HANDLE = /^@?[A-Za-z0-9._]{1,60}$/;

  /* Worker field -> [form control, message] */
  var MSG = {
    artist_name: ['artist_name', 'Please enter the name you work under.'],
    email: ['email', 'Please enter a valid email address, like name@example.com.'],
    region: ['region', 'Please choose the county where you live or work.'],
    medium: ['medium', 'Please choose your primary medium.'],
    bio: ['bio', 'Please write a short biography of at least 40 characters (up to 1,000).'],
    portfolio: ['portfolio', 'Please add a link to your work, beginning https://'],
    website: ['website', 'Please check your website link. It should begin https://'],
    social_link: ['social_link', 'Please enter an @handle, or a link beginning https://'],
    additional_info: ['additional_info', 'Please keep this to 800 characters or fewer.'],
    eligibility_text: ['eligibility', 'Please confirm you are 18 or over and based or working on the island of Ireland.'],
    ownership_text: ['ownership', 'Please confirm the work is your own, or that you are authorised to represent the artist.'],
    privacy_text: ['privacy', 'Please confirm you have read the privacy notice for applications.']
  };
  var ERR_ID = { artist_name: 'name', email: 'email', region: 'region', medium: 'medium', bio: 'bio', portfolio: 'portfolio',
                 website: 'website', social_link: 'social', additional_info: 'info',
                 eligibility_text: 'eligibility', ownership_text: 'ownership', privacy_text: 'privacy' };

  function setError(key, on) {
    var input = el(MSG[key][0]);
    var p = document.getElementById('f25-' + ERR_ID[key] + '-e');
    if (!input || !p) return;
    if (on) { input.setAttribute('aria-invalid', 'true'); p.textContent = MSG[key][1]; p.hidden = false; }
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
    if (!HTTPS.test(v('portfolio'))) bad.push('portfolio');
    if (v('website') && !HTTPS.test(v('website'))) bad.push('website');
    if (v('social_link') && !(HANDLE.test(v('social_link')) || HTTPS.test(v('social_link')))) bad.push('social_link');
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
      bio: el('bio').value.trim(), portfolio: v('portfolio'),
      eligibility_text: sentence('eligibility'), ownership_text: sentence('ownership'), privacy_text: sentence('privacy'),
      submission_id: submissionId
    };
    if (v('website')) b.website = v('website');
    if (v('social_link')) b.social_link = v('social_link');
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
  }

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
        if (j && j.state === 'refused' && MSG[j.field]) {
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
