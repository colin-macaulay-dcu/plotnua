"""PLOTNUA · consent migration from Cookiebot to the shared self-hosted consent module (prepared 27 Nov 2026, NOT released).

The ONE definition of the change, used on the pages (applied once by migrate-plotnua-consent.py), on the JSON-escaped
pinned snapshots, and by plotart_shell.ANALYTICS_HEAD for every PlotArt page on plotnua.ie.

What changes on a PlotNua page (everything else is byte-for-byte unchanged):
  * the Cookiebot loader (consent.cookiebot.com/uc.js) is removed;
  * the static Google tag loader and its config script are removed: Google Analytics is now started ONLY by
    /assets/consent/site-consent.js, after an explicit "Accept analytics" (Consent Mode v2 Basic mode, so no
    cookieless pings either);
  * the consent default block is kept (everything denied), and the intention-event listener is kept with the same
    event names (supplier_outbound_click, whatsapp_click, email_click) and parameters; only its consent check changes
    from Cookiebot.consent.statistics to siteConsent.statistics;
  * the module is configured for plotnua.ie: its own consent record (pn-consent), the same GA4 property and the
    existing content_group 'PlotNua' (and 'PlotArt' on PlotArt pages), so reports and history continue.
"""
import json
import re
import seo_pn_analytics as A

MODULE = ('<link rel="stylesheet" href="/assets/consent/site-consent.css?v=1">\n'
          '<script src="/assets/consent/site-consent.js?v=1" data-site="PlotNua" data-key="pn-consent" '
          'data-version="PN-CK-2026-12" data-ga="G-PKKJ0RK6N8" data-domain="plotnua.ie" '
          'data-policy="/cookie-policy.html" data-content-group="%s"></script>\n')
OLD_CHECK = "!(window.Cookiebot&&Cookiebot.consent&&Cookiebot.consent.statistics)"
NEW_CHECK = "!(window.siteConsent&&siteConsent.statistics)"
LISTENER = A.LISTENER.replace(OLD_CHECK, NEW_CHECK).replace("Statistics consent only", "Analytics consent only")
assert LISTENER != A.LISTENER

# the static Google tag and its config call, as every tagged PlotNua page carries them (pretty and minified forms)
_GTAG = re.compile(r'(?:<!-- Google tag \(gtag\.js\) -->\n)?' + re.escape(A.GTAG_LOADER) +
                   r'\n<script>\s*window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];?\s*function gtag\(\)\{dataLayer\.push\(arguments\);?\}\s*'
                   r"gtag\('js',\s*new Date\(\)\);?\s*(?:" + re.escape(A.CONFIG_NEW) + '|' + re.escape(A.CONFIG_MIN_NEW) + r')\s*</script>\n?')
_COOKIEBOT = re.compile(re.escape(A.COOKIEBOT) + r'\n?')


def transform(text, group='PlotNua'):
    """PlotNua page: Cookiebot + static gtag -> consent module. Idempotent. Raises if the page has an unexpected shape."""
    if 'site-consent.js' in text and 'consent.cookiebot.com' not in text:
        return text
    if text.count(A.COOKIEBOT) != 1 or text.count(A.BLOCK) != 1:
        raise ValueError('expected exactly one Cookiebot tag and one PlotNua analytics block')
    text = text.replace(A.BLOCK, A.CONSENT + LISTENER)
    text = _COOKIEBOT.sub(lambda m: MODULE % group, text, count=1)
    text, n = _GTAG.subn('', text)
    if n > 1:
        raise ValueError('more than one static Google tag')
    if 'googletagmanager.com/gtag/js' in text or 'consent.cookiebot.com' in text:
        raise ValueError('a Google tag or Cookiebot reference is left')
    return text


def json_transform(s, group='PlotNua'):
    """The same change for raw HTML stored JSON-escaped in a pinned snapshot (one string field)."""
    enc = lambda x: json.dumps(x, ensure_ascii=False)[1:-1]
    dec = lambda x: json.loads('"' + x + '"')
    if enc(A.COOKIEBOT) not in s:
        return s
    # decode the one string that holds the page, transform it, encode it back
    m = re.search(r'"((?:[^"\\]|\\.)*' + re.escape(enc(A.COOKIEBOT)) + r'(?:[^"\\]|\\.)*)"', s)
    return s[:m.start(1)] + enc(transform(dec(m.group(1)), group)) + s[m.end(1):]


# PlotArt pages on plotnua.ie (plotart_shell.ANALYTICS_HEAD): the same consent record and module as the rest of
# plotnua.ie (one choice per domain), content group 'PlotArt'. plotart.ie still replaces this block with its own.
PLOTART_HEAD = A.CONSENT + (MODULE % 'PlotArt')

# ---- declared mapping for the pinned-snapshot guards (same method as the Cookiebot id change of 26 Nov 2026) ----
# A guard that compares a page's external head scripts against a historical BASE applies this to the BASE list only:
# the Cookiebot loader becomes the consent module and the static Google tag loader is dropped. Nothing else is relaxed.
CB_SRC = 'https://consent.cookiebot.com/uc.js'
GTAG_SRC = 'https://www.googletagmanager.com/gtag/js?id=G-PKKJ0RK6N8'
MODULE_SRC = '/assets/consent/site-consent.js?v=1'


def swap_srcs(srcs):
    """List of script src values (BASE) -> the same list after the consent migration."""
    out = []
    for s in srcs:
        if s == CB_SRC: out.append(MODULE_SRC)
        elif s == GTAG_SRC: continue
        else: out.append(s)
    return out


def swap_tags(tags, group='PlotNua'):
    """List of opening <script ... src=...> tags (BASE) -> the same list after the consent migration."""
    module_tag = re.search(r'<script\b[^>]*src=[^>]*>', MODULE % group).group(0)
    out = []
    for t in tags:
        if 'consent.cookiebot.com/uc.js' in t: out.append(module_tag)
        elif 'googletagmanager.com/gtag/js' in t: continue
        else: out.append(t)
    return out
