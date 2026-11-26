/* PlotArt buyer-to-artist enquiries (Phase 3). Reveals the enquiry form beside an "Enquire" button and sends it to the
   PlotArt enquiry relay, which passes it to the artist. Without JavaScript the button stays a plain email link.
   Stores nothing in the browser and sends no cookies.
   Analytics (SEO and analytics package, founder approval 26 Nov 2026, section 1.3): "enquiry_open" when the enquiry is
   opened (an intention) and "generate_lead" only when the relay confirms the enquiry was passed on with a reference (a
   confirmed enquiry). Both go to the page's existing GA4 tag only when it is there and the visitor has allowed statistics
   in the cookie banner; they carry the gallery address and artwork id from the page, never a name, email or message. */
(function () {
  'use strict';
  var forms = document.querySelectorAll('form.pa-enq[data-endpoint]');
  if (!forms.length || !window.fetch) return;
  var artist = (location.pathname.match(/\/artists\/([a-z0-9-]+)\//) || [])[1] || '';
  function track(name, params) {
    try {
      if (typeof window.gtag === 'function' && window.Cookiebot && window.Cookiebot.consent && window.Cookiebot.consent.statistics) window.gtag('event', name, params);
    } catch (err) { /* analytics never affects the enquiry */ }
  }
  Array.prototype.forEach.call(forms, function (form) {
    var btn = form.parentNode.querySelector('[data-pa-enquire]');
    var commission = form.getAttribute('data-kind') === 'commission', ref = form.getAttribute('data-ref') || '';
    var work = !commission && artist && ref.indexOf('PA-' + artist + '-') === 0 ? ref.slice(artist.length + 4) : '';
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(work)) work = '';
    var about = { artist: artist, enquiry_kind: commission ? 'commission' : (work ? 'artwork' : 'artist') };
    if (work) about.artwork_id = work;
    if (btn) btn.addEventListener('click', function (e) {
      e.preventDefault(); form.hidden = false; btn.hidden = true;
      var first = form.querySelector('input[name=name]'); if (first) first.focus();
      track('enquiry_open', about);
    });
    var status = form.querySelector('.pa-enq-status'), send = form.querySelector('button[type=submit]');
    // Open for Commissions (13 Nov 2026): only a form marked data-kind="commission" adds kind; every other form is unchanged
    var withKind = function (o) { if (form.getAttribute('data-kind') === 'commission') o.kind = 'commission'; return o; };
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = form.elements, msg = '';
      if (!f.name.value.trim()) msg = 'Please add your name.';
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.value.trim())) msg = 'Please check your email address.';
      else if (f.message.value.trim().length < 10) msg = 'Please write a short message (at least 10 characters).';
      if (msg) { status.textContent = msg; status.setAttribute('data-state', 'error'); return; }
      send.disabled = true; send.setAttribute('aria-busy', 'true'); status.textContent = 'Sending…'; status.removeAttribute('data-state');
      fetch(form.getAttribute('data-endpoint'), {
        method: 'POST', mode: 'cors', credentials: 'omit', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(withKind({ ref: form.getAttribute('data-ref'), notice: form.getAttribute('data-notice'), name: f.name.value.trim(),
          email: f.email.value.trim(), message: f.message.value.trim(), website: f.website.value }))
      }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok && j.ok, j: j }; }); })
        .then(function (r) {
          if (r.ok) {
            form.innerHTML = '<p class="pa-enq-h">Thank you</p><p class="pa-enq-notice">Your enquiry has been passed to the artist, who will reply to you by email. Your reference is <strong>' +
              String(r.j.reference).replace(/[^A-Z0-9-]/g, '') + '</strong>.</p>';
            form.setAttribute('data-state', 'sent');
            var lead = { lead_type: commission ? 'commission_enquiry' : (work ? 'artwork_enquiry' : 'artist_enquiry'), artist: artist };
            if (work) lead.artwork_id = work;
            if (r.j.reference) track('generate_lead', lead);
          } else {
            status.textContent = r.j.error || 'Sorry, that didn’t send. Please try again, or email hello@plotnua.ie.';
            status.setAttribute('data-state', 'error'); send.disabled = false; send.removeAttribute('aria-busy');
          }
        }, function () {
          status.textContent = 'No connection. Please try again in a moment, or email hello@plotnua.ie.'; status.setAttribute('data-state', 'error');
          send.disabled = false; send.removeAttribute('aria-busy');
        });
    });
  });
})();
