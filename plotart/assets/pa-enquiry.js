/* PlotArt buyer-to-artist enquiries (Phase 3). Reveals the enquiry form beside an "Enquire" button and sends it to the
   PlotArt enquiry relay, which passes it to the artist. Without JavaScript the button stays a plain email link.
   Stores nothing in the browser and sends no cookies. */
(function () {
  'use strict';
  var forms = document.querySelectorAll('form.pa-enq[data-endpoint]');
  if (!forms.length || !window.fetch) return;
  Array.prototype.forEach.call(forms, function (form) {
    var btn = form.parentNode.querySelector('[data-pa-enquire]');
    if (btn) btn.addEventListener('click', function (e) {
      e.preventDefault(); form.hidden = false; btn.hidden = true;
      var first = form.querySelector('input[name=name]'); if (first) first.focus();
    });
    var status = form.querySelector('.pa-enq-status'), send = form.querySelector('button[type=submit]');
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
        body: JSON.stringify({ ref: form.getAttribute('data-ref'), notice: form.getAttribute('data-notice'), name: f.name.value.trim(),
          email: f.email.value.trim(), message: f.message.value.trim(), website: f.website.value })
      }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok && j.ok, j: j }; }); })
        .then(function (r) {
          if (r.ok) {
            form.innerHTML = '<p class="pa-enq-h">Thank you</p><p class="pa-enq-notice">Your enquiry has been passed to the artist, who will reply to you by email. Your reference is <strong>' +
              String(r.j.reference).replace(/[^A-Z0-9-]/g, '') + '</strong>.</p>';
            form.setAttribute('data-state', 'sent');
          } else {
            status.textContent = r.j.error || 'Sorry, that didn’t send. Please try again, or email hello@plotnua.ie.';
            status.setAttribute('data-state', 'error'); send.disabled = false; send.removeAttribute('aria-busy');
          }
        }, function () {
          status.textContent = 'No connection. Please try again in a moment.'; status.setAttribute('data-state', 'error');
          send.disabled = false; send.removeAttribute('aria-busy');
        });
    });
  });
})();
