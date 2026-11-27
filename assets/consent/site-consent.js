/* Shared self-hosted cookie consent for plotnua.ie and plotart.ie (prepared 27 Nov 2026; one maintained file).
   Each website configures it on its own script tag, so choices stay independent (each domain has its own storage):
     <script src="/assets/consent/site-consent.js" data-site="PlotArt" data-key="pa-consent" data-version="PA-CK-2026-11"
             data-ga="G-PKKJ0RK6N8" data-domain="plotart.ie" data-policy="https://plotnua.ie/cookie-policy.html#plotart" defer>
   Branding comes from the site's own CSS variables (site-consent.css). Derived from the approved PlotArt banner.
   Self-hosted, no third party, no subscription. Served from plotart.ie itself, so the site's Content-Security-Policy stays
   "scripts from plotart.ie only" until a visitor accepts statistics.

   What it does
   - Before any choice: Google Consent Mode v2 defaults are all "denied" (set inline in the page head) and Google Analytics
     is NOT loaded at all (Basic Consent Mode): no request to Google, no cookie, no identifier.
   - The banner offers "Accept analytics" and "Reject optional" as two equal buttons, plus "Cookie settings" for the detail.
     Nothing is pre-ticked. Closing or ignoring the banner is not consent.
   - No cross-domain measurement: visits are not linked between plotnua.ie and plotart.ie (no linker is configured, and
     the GA4 "Configure your domains" setting must stay empty), so a choice on one site can never carry over to the other.
     A linker parameter (_gl) that arrives anyway is removed from the address straight away unless this visitor has
     accepted analytics on plotart.ie, so it is never read or kept.
   - Analytics cookies are set with a fixed 6-month life from the moment of Accept (cookie_expires, cookie_update false),
     the same as the consent record; when the choice expires, any analytics cookies left on plotart.ie are deleted.
   - Accept: Consent Mode update (analytics_storage granted; every advertising signal stays denied), then GA4 is loaded
     from googletagmanager.com with the same property as PlotNua (continuity) and site_name "PlotArt" (to tell traffic apart).
   - Reject: nothing is loaded; the choice is remembered.
   - Change of mind at any time: "Cookie settings" in the footer of every page (and any [data-pa-consent-open] element).
     Withdrawing stops GA4 immediately, deletes its _ga cookies on plotart.ie and reloads the page.
   - The choice is kept on this device only (localStorage "pa-consent", strictly necessary) for 6 months, then asked again
     (DPC guidance: reaffirm no later than 6 months); the analytics cookies are also limited to 6 months (cookie_expires);
     a new policy version (VERSION) also asks again. Nothing is sent to PlotArt or anyone else.
   - window.paConsent = { statistics: true|false|null } for PlotArt's own event code (pa-enquiry.js, pa-basket.js). */
(function () {
  'use strict';
  var w = window, d = document, me = d.currentScript || d.querySelector('script[data-key][src*="consent"]');
  var cfg = function (k, dflt) { return (me && me.getAttribute('data-' + k)) || dflt; };
  var SITE = cfg('site', 'PlotArt'), GA_ID = cfg('ga', 'G-PKKJ0RK6N8'), VERSION = cfg('version', 'PA-CK-2026-11'),
      KEY = cfg('key', 'pa-consent'), DOMAIN = cfg('domain', location.hostname),
      POLICY = cfg('policy', 'https://plotnua.ie/cookie-policy.html'), MAX_AGE = 183 * 864e5;
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
    w.gtag('config', GA_ID, { site_name: SITE, cookie_domain: DOMAIN, cookie_expires: 15552000, cookie_update: false, allow_google_signals: false, allow_ad_personalization_signals: false });
  }
  function stopAnalytics() {
    w['ga-disable-' + GA_ID] = true;
    w.gtag('consent', 'update', { analytics_storage: 'denied' });
    d.cookie.split(';').forEach(function (c) {
      var n = c.split('=')[0].trim();
      if (/^_ga($|_)/.test(n)) ['', '; domain=' + DOMAIN, '; domain=.' + DOMAIN].forEach(function (dom) {
        d.cookie = n + '=; Max-Age=0; path=/' + dom;
      });
    });
  }
  function apply(statistics) {
    w.paConsent = w.siteConsent = { statistics: statistics };
    try { w.dispatchEvent(new CustomEvent('site-consent', { detail: { statistics: statistics } })); } catch (e) {}
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
    el.setAttribute('aria-describedby', 'pa-ck-p');
    el.innerHTML =
      '<h2 id="pa-ck-t">Cookies on ' + SITE + '</h2>' +
      '<p id="pa-ck-p">We would like to use Google Analytics to understand how visitors find and use ' + SITE + '. It is off unless you accept, ' +
      'and you can change your mind at any time under “Cookie settings”. <a href="' + POLICY + '">Cookie policy</a></p>' +
      (detail ? '<div class="pa-ck-d">' +
        '<label><input type="checkbox" checked disabled> <span><strong>Necessary</strong> Remembers this choice on your device. Always on.</span></label>' +
        '<label><input type="checkbox" id="pa-ck-s"' + (cur && cur.statistics ? ' checked' : '') + '> <span><strong>Analytics</strong> Google Analytics: pages visited, device and approximate region. Never used for advertising.</span></label>' +
        '</div>' : '') +
      '<div class="pa-ck-b">' +
        '<button type="button" data-a="reject">Reject optional</button>' +
        (detail ? '<button type="button" data-a="save">Save choice</button>' : '<button type="button" data-a="accept">Accept analytics</button>') +
        (detail ? '' : '<button type="button" class="pa-ck-more" data-a="more">Cookie settings</button>') +
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
  if (!choice) stopAnalytics();          // no valid choice (first visit, or it expired): remove any leftover _ga cookies
  // a cross-domain linker parameter from plotnua.ie is only honoured with consent given here (see above)
  if (!(choice && choice.statistics) && /[?&]_gl=/.test(location.search) && w.history && history.replaceState) {
    var q = location.search.slice(1).split('&').filter(function (p) { return p.split('=')[0] !== '_gl'; }).join('&');
    history.replaceState(history.state, '', location.pathname + (q ? '?' + q : '') + location.hash);
  }
  apply(choice ? choice.statistics : null);
  function start() { settingsLink(); if (!choice) banner(false); }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', start); else start();
})();
