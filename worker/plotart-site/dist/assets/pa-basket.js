/* PlotArt multi-artist basket (21 Nov 2026; included only when the founder sets basket_origin for publishing).
   Asks the PlotArt checkout Worker whether this artwork can be bought online right now. Only then is the hidden
   "Buy online" box shown. If the artist arranges this work's delivery personally, a short note says so instead;
   otherwise the page stays the enquiry page it was. The basket itself lives on the checkout
   Worker's page. Sends no cookies and stores nothing on plotnua.ie.
   Commercial Conversion Sprint 1 (founder approval 26 Nov 2026): for a work the checkout confirms, "Buy online" becomes
   the first button and "Enquire to purchase" (buying directly from the artist) the second; under it, the work's OWN delivery, cancellation and seller
   details, taken only from the checkout's answer (written as text, never as HTML). A line whose detail is missing is
   left out rather than guessed. On any error or delay nothing changes: the page stays enquiry-only.
   Analytics (SEO and analytics package, founder approval 26 Nov 2026, section 1.3): a click on "Buy online" sends
   "begin_checkout" (a purchase intention, never a sale: payment happens on the checkout's own page) to the page's existing
   GA4 tag, only when it is there and the visitor has allowed statistics; it carries the artwork id and the checkout's
   price, nothing personal. The link itself works exactly as before. */
(function () {
  'use strict';
  var box = document.querySelector('.pa-basket[data-pa-basket-origin][data-pa-artwork]');
  if (!box || !window.fetch) return;
  var origin = box.getAttribute('data-pa-basket-origin'), id = box.getAttribute('data-pa-artwork');
  if (!/^https?:\/\/[a-z0-9.:-]+$/.test(origin) || !/^[A-Za-z0-9_-]{1,64}$/.test(id)) return;
  var eur = function (c) { return '€' + (c / 100).toLocaleString('en-IE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
  var days = function (n) { return n + (n === 1 ? ' day' : ' days'); };
  var whole = function (n) { return typeof n === 'number' && n >= 1 && Math.floor(n) === n; };
  // The checkout's own, artist-entered and reviewed details for this work (basket.js preview()); nothing else.
  function details(it) {
    var d = it.delivery || {}, out = [], t;
    if (typeof it.delivery_cents === 'number' && it.delivery_cents >= 0) {
      t = 'Delivery in Ireland ' + (it.delivery_cents === 0 ? 'included' : eur(it.delivery_cents));
      if (whole(d.dispatch_days)) t += ' · dispatched within ' + days(d.dispatch_days);
      if (whole(d.delivery_days)) t += ', delivered within ' + days(d.delivery_days) + ' of payment';
      out.push(t);
    }
    var x = [];
    if (d.tracking === true) x.push('Tracked');
    if (typeof d.cover === 'string' && d.cover) x.push('insured: ' + d.cover);
    if (x.length) out.push(x.join(' · ').replace(/^insured/, 'Insured'));
    // The issued buyer terms (PA-BBT-2026-11 §7) give every online purchase a 14-day right to cancel after delivery;
    // the return cost is the artist's own figure for this work.
    out.push('14-day right to cancel after delivery' + (typeof d.returns === 'string' && d.returns ? ' · ' + d.returns : ''));
    if (typeof it.seller === 'string' && it.seller) out.push('Sold by ' + it.seller + ' · secure card payment through PlotArt');
    return out;
  }
  fetch(origin + '/api/basket/items?ids=' + encodeURIComponent(id), { mode: 'cors', credentials: 'omit' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      if (!j || !j.open || !j.items || !j.items[0]) return;
      var it = j.items[0];
      if (!j.items[0].ok) {
        // the artist arranges this work's delivery personally (no fixed delivery price): say so beside the enquiry button
        // (23 Nov 2026). No basket button; the buyer enquires and agrees delivery and the full price before paying.
        if (it.delivery_arranged !== true) return;
        var link = box.querySelector('a'), note = box.querySelector('.pa-aw-cta-note'), lst = box.querySelector('.pa-aw-assure');
        if (link) link.parentNode.removeChild(link);
        if (lst) lst.parentNode.removeChild(lst);
        if (note) note.textContent = 'Delivery for this work is arranged with the artist. Enquire for a delivery quote and the full price before you buy.';
        box.hidden = false;
        return;
      }
      var a = box.querySelector('a'), img = document.querySelector('.pa-aw-frame img');
      if (a) a.addEventListener('click', function () {
        try {
          if (typeof window.gtag === 'function' && window.Cookiebot && window.Cookiebot.consent && window.Cookiebot.consent.statistics) {
            var ev = { currency: 'EUR', items: [{ item_id: id }] };
            if (typeof it.price_cents === 'number' && it.price_cents > 0) { ev.value = it.price_cents / 100; ev.items[0].price = it.price_cents / 100; }
            window.gtag('event', 'begin_checkout', ev);
          }
        } catch (err) { /* analytics never affects the checkout link */ }
      });
      var src = img && (img.currentSrc || img.src);
      if (a && src && /^https:\/\/plotnua\.ie\/plotart\/artists\/[a-z0-9-]+\/img\/[A-Za-z0-9._-]+$/.test(src)) a.href += '&img=' + encodeURIComponent(src);
      var list = box.querySelector('.pa-aw-assure');
      if (list) {
        details(it).forEach(function (t) { var li = document.createElement('li'); li.textContent = t; list.appendChild(li); });
        list.hidden = !list.children.length;
      }
      // "Buy online" first; the enquiry stays, as the second (outlined) choice
      var cta = box.parentNode, enq = cta && cta.querySelector('a.pa-btn--solid[data-pa-track="artwork_enquiry"]');
      if (enq) { enq.classList.remove('pa-btn--solid'); enq.classList.add('pa-btn--ghost'); }
      if (cta && cta.firstChild !== box) cta.insertBefore(box, cta.firstChild);
      box.hidden = false;
    })
    .catch(function () { /* stays an enquiry page */ });
})();
