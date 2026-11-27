/* PlotArt cookie consent for plotart.ie (prepared 27 Nov 2026, NOT ACTIVE: worker/plotart-site/site.json "analytics": "off").
   Self-hosted, no third party, no subscription. Served from plotart.ie itself, so the site's Content-Security-Policy stays
   "scripts from plotart.ie only" until a visitor accepts statistics.

   What it does
   - Before any choice: Google Consent Mode v2 defaults are all "denied" (set inline in the page head) and Google Analytics
     is NOT loaded at all (Basic Consent Mode): no request to Google, no cookie, no identifier.
   - The banner offers "Accept analytics" and "Reject" as two equal buttons, plus "Choose" for the detail. Nothing is
     pre-ticked. Closing or ignoring the banner is not consent.
   - Accept: Consent Mode update (analytics_storage granted; every advertising signal stays denied), then GA4 is loaded
     from googletagmanager.com with the same property as PlotNua (continuity) and site_name "PlotArt" (to tell traffic apart).
   - Reject: nothing is loaded; the choice is remembered.
   - Change of mind at any time: "Cookie settings" in the footer of every page (and any [data-pa-consent-open] element).
     Withdrawing stops GA4 immediately, deletes its _ga cookies on plotart.ie and reloads the page.
   - The choice is kept on this device only (localStorage "pa-consent", strictly necessary) for 6 months, then asked again;
     a new policy version (VERSION) also asks again. Nothing is sent to PlotArt or anyone else.
   - window.paConsent = { statistics: true|false|null } for PlotArt's own event code (pa-enquiry.js, pa-basket.js). */
(function () {
  'use strict';
  var GA_ID = 'G-PKKJ0RK6N8', VERSION = 'PA-CK-2026-11', KEY = 'pa-consent', MAX_AGE = 183 * 864e5;
  var POLICY = 'https://plotnua.ie/cookie-policy.html#plotart';
  var w = window, d = document;
  w.dataLayer = w.dataLayer || [];
  function gtag() { w.dataLayer.push(arguments); }
  if (typeof w.gtag !== 'function') w.gtag = gtag;

  function read() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (c && c.v === VERSION && typeof c.statistics === 'boolean' && Date.now() - c.ts < MAX_AGE) return c;
    } catch (e) { /* storage blocked: ask each visit, track nothing */ }
    return null;
  }
  function save(statistics) {
    try { localStorage.setItem(KEY, JSON.stringify({ v: VERSION, statistics: statistics, ts: Date.now() })); } catch (e) {}
  }

  var loaded = false;
  function loadAnalytics() {
    if (loaded) return;
    loaded = true;
    w['ga-disable-' + GA_ID] = false;
    w.gtag('consent', 'update', { analytics_storage: 'granted' });
    var s = d.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    d.head.appendChild(s);
    w.gtag('js', new Date());
    w.gtag('config', GA_ID, { site_name: 'PlotArt', cookie_domain: 'plotart.ie', allow_google_signals: false, allow_ad_personalization_signals: false });
  }
  function stopAnalytics() {
    w['ga-disable-' + GA_ID] = true;
    w.gtag('consent', 'update', { analytics_storage: 'denied' });
    d.cookie.split(';').forEach(function (c) {
      var n = c.split('=')[0].trim();
      if (/^_ga($|_)/.test(n)) ['', '; domain=plotart.ie', '; domain=.plotart.ie'].forEach(function (dom) {
        d.cookie = n + '=; Max-Age=0; path=/' + dom;
      });
    });
  }
  function apply(statistics) {
    w.paConsent = { statistics: statistics };
    if (statistics) loadAnalytics();
  }

  var el;
  function close() { if (el) { el.remove(); el = null; } }
  function choose(statistics) {
    var was = w.paConsent && w.paConsent.statistics;
    save(statistics);
    close();
    if (!statistics && (was || loaded)) { stopAnalytics(); location.reload(); return; }
    apply(statistics);
  }
  function banner(detail) {
    close();
    var cur = read();
    el = d.createElement('section');
    el.className = 'pa-ck';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'false');
    el.setAttribute('aria-labelledby', 'pa-ck-t');
    el.innerHTML =
      '<h2 id="pa-ck-t">Cookies on PlotArt</h2>' +
      '<p>We would like to use Google Analytics to understand how visitors find and use PlotArt. It is off unless you accept, ' +
      'and you can change your mind at any time under “Cookie settings”. <a href="' + POLICY + '">Cookie policy</a></p>' +
      (detail ? '<div class="pa-ck-d">' +
        '<label><input type="checkbox" checked disabled> <span><strong>Necessary</strong> Remembers this choice on your device. Always on.</span></label>' +
        '<label><input type="checkbox" id="pa-ck-s"' + (cur && cur.statistics ? ' checked' : '') + '> <span><strong>Analytics</strong> Google Analytics: pages visited, device and approximate region. Never used for advertising.</span></label>' +
        '</div>' : '') +
      '<div class="pa-ck-b">' +
        '<button type="button" data-a="reject">Reject</button>' +
        (detail ? '<button type="button" data-a="save">Save choice</button>' : '<button type="button" data-a="accept">Accept analytics</button>') +
        (detail ? '' : '<button type="button" class="pa-ck-more" data-a="more">Choose</button>') +
      '</div>';
    el.addEventListener('click', function (e) {
      var a = e.target && e.target.getAttribute && e.target.getAttribute('data-a');
      if (a === 'accept') choose(true);
      else if (a === 'reject') choose(false);
      else if (a === 'save') choose(!!d.getElementById('pa-ck-s').checked);
      else if (a === 'more') banner(true);
    });
    d.body.appendChild(el);
    var first = el.querySelector('button');
    if (first && (detail || cur)) first.focus();
  }
  function settingsLink() {
    var foot = d.querySelector('footer.pa-foot .fine') || d.querySelector('footer');
    if (foot && !d.querySelector('[data-pa-consent-open]')) {
      var a = d.createElement('button');
      a.type = 'button';
      a.className = 'pa-ck-link';
      a.setAttribute('data-pa-consent-open', '');
      a.textContent = 'Cookie settings';
      foot.appendChild(d.createTextNode(' '));
      foot.appendChild(a);
    }
    d.addEventListener('click', function (e) {
      var t = e.target && e.target.closest && e.target.closest('[data-pa-consent-open]');
      if (t) { e.preventDefault(); banner(true); }
    });
  }

  var choice = read();
  apply(choice ? choice.statistics : null);
  function start() { settingsLink(); if (!choice) banner(false); }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', start); else start();
})();
