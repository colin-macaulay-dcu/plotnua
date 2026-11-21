/* PlotArt multi-artist basket (21 Nov 2026; included only when the founder sets basket_origin for publishing).
   Asks the PlotArt checkout Worker whether this artwork can be bought online right now. Only then is the hidden
   "Add to basket" button shown; otherwise the page stays the enquiry page it was. The basket itself lives on the checkout
   Worker's page. Sends no cookies and stores nothing on plotnua.ie. */
(function () {
  'use strict';
  var box = document.querySelector('.pa-basket[data-pa-basket-origin][data-pa-artwork]');
  if (!box || !window.fetch) return;
  var origin = box.getAttribute('data-pa-basket-origin'), id = box.getAttribute('data-pa-artwork');
  if (!/^https?:\/\/[a-z0-9.:-]+$/.test(origin) || !/^[A-Za-z0-9_-]{1,64}$/.test(id)) return;
  fetch(origin + '/api/basket/items?ids=' + encodeURIComponent(id), { mode: 'cors', credentials: 'omit' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      if (!j || !j.open || !j.items || !j.items[0] || !j.items[0].ok) return;
      var a = box.querySelector('a'), img = document.querySelector('.pa-aw-frame img');
      var src = img && (img.currentSrc || img.src);
      if (a && src && /^https:\/\/plotnua\.ie\/plotart\/artists\/[a-z0-9-]+\/img\/[A-Za-z0-9._-]+$/.test(src)) a.href += '&img=' + encodeURIComponent(src);
      box.hidden = false;
    })
    .catch(function () { /* stays an enquiry page */ });
})();
