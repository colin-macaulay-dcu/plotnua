"""PLOTNUA · SEO and analytics package, PlotNua half (founder approval, 26 Nov 2026).

The ONE definition of the analytics change on PlotNua pages (everything outside /plotart/):

  1. the Google Consent Mode v2 DEFAULT (Basic mode: everything denied until Cookiebot sends the
     visitor's choice), inserted immediately BEFORE the existing <script id="Cookiebot" ...>, with
     data-cookieconsent="ignore" so Cookiebot's auto-blocking leaves it alone;
  2. one delegated click listener in the same head block: supplier_outbound_click {supplier_domain, page},
     whatsapp_click {page} and email_click {page}. It sends nothing unless the visitor has allowed
     statistics in Cookiebot and gtag exists, and it never reads a name, an email address or a message
     (page is location.pathname; the domain is the link's host). Links carrying data-outbound (triq-cube's
     own measured links) are left to their existing supplier_outbound_click;
  3. the GA4 config call gains { content_group: 'PlotNua' } so PlotNua and PlotArt report separately.

Used by the pages (applied once), by the supplier showcase builders (their HEAD templates carry the same
text), and by atlas-tools/seo-pn-repin-premium.py, which proves pinned snapshots change by exactly this.
"""
import re

CONSENT = """<script data-cookieconsent="ignore">
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', functionality_storage: 'denied',
    personalization_storage: 'denied', security_storage: 'granted',
    wait_for_update: 500 });
  gtag('set', 'ads_data_redaction', true);
</script>
"""

# Supplier hosts PlotNua's guides and Discoveries link to (makers with a PlotNua profile, guide or listing).
# On suppliers/*.html every external link except the excluded hosts counts as a supplier link.
SUPPLIER_HOSTS = ["arcticwellness.ie", "donmodularhomes.ie", "elmlandscaping.ie", "gardenroomireland.ie",
                  "gardenhouse24.ie", "nookprefab.com", "superiorpergola.ie", "themobilepods.ie", "thepodfactory.ie",
                  "shomera.ie", "irishsaunacompany.com", "polaris-sauna.ie", "summerhouse24.ie", "pineca.ie",
                  "ognyx.com", "conceptmodular.ie", "allinonecabins.ie", "triqbriq.de", "timbertrove.com",
                  "oodhouse.com", "powersheds.com", "yardbox.co.uk", "apexverandas.ie", "accesslifts.ie",
                  "tanktribe.ie"]
NOT_SUPPLIER = ["plotnua.ie", "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "pinterest.com",
                "x.com", "twitter.com", "youtube.com", "google.com", "googleapis.com", "gstatic.com",
                "cookiebot.com", "gov.ie", "irishstatutebook.ie"]


def _alt(hosts):
    return "|".join(h.replace(".", "\\.") for h in hosts)


LISTENER = ("<script data-cookieconsent=\"ignore\">\n"
            "/* PlotNua intention events: supplier_outbound_click, whatsapp_click, email_click. Statistics consent only; no personal data. */\n"
            "(function(){\n"
            "  var SUP=/(^|\\.)(" + _alt(SUPPLIER_HOSTS) + ")$/i;\n"
            "  var NOT=/(^|\\.)(" + _alt(NOT_SUPPLIER) + ")$/i;\n"
            "  document.addEventListener('click',function(e){\n"
            "    try{\n"
            "      var a=e.target&&e.target.closest?e.target.closest('a[href]'):null;\n"
            "      if(!a||typeof gtag!=='function'||!(window.Cookiebot&&Cookiebot.consent&&Cookiebot.consent.statistics))return;\n"
            "      var p=location.pathname,u=new URL(a.getAttribute('href'),location.href);\n"
            "      if(u.protocol==='mailto:'){gtag('event','email_click',{page:p});return;}\n"
            "      var h=u.hostname.toLowerCase().replace(/^www\\./,'');\n"
            "      if(h==='wa.me'||/(^|\\.)whatsapp\\.com$/.test(h)){gtag('event','whatsapp_click',{page:p});return;}\n"
            "      if(!/^https?:$/.test(u.protocol)||u.hostname===location.hostname||NOT.test(h)||a.hasAttribute('data-outbound'))return;\n"
            "      if(/^\\/suppliers\\//.test(p)||SUP.test(h))gtag('event','supplier_outbound_click',{supplier_domain:h,page:p});\n"
            "    }catch(_){}\n"
            "  },true);\n"
            "})();\n"
            "</script>\n")

BLOCK = CONSENT + LISTENER          # inserted immediately before <script id="Cookiebot"
COOKIEBOT = '<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="b8abbc45-15b0-4d27-8f95-83ebd240a305" data-blockingmode="auto" type="text/javascript"></script>'
GTAG_LOADER = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-PKKJ0RK6N8"></script>'
CONFIG_OLD, CONFIG_NEW = "gtag('config', 'G-PKKJ0RK6N8');", "gtag('config', 'G-PKKJ0RK6N8', { content_group: 'PlotNua' });"
CONFIG_MIN_OLD, CONFIG_MIN_NEW = "gtag('config','G-PKKJ0RK6N8');", "gtag('config','G-PKKJ0RK6N8',{content_group:'PlotNua'});"

# The full head block for a PlotNua page that had no analytics (the same tags every tagged page carries).
FULL = (BLOCK + COOKIEBOT + "\n<!-- Google tag (gtag.js) -->\n" + GTAG_LOADER + "\n<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n\n  " + CONFIG_NEW + "\n</script>\n")


def transform(text):
    """The declared analytics transform: consent default + listener before each Cookiebot tag (once), and the
    content group on each GA4 config call. Idempotent; text without Cookiebot is returned unchanged."""
    if BLOCK in text:
        return text
    text = re.sub(r'(?=<script id="Cookiebot")', lambda m: BLOCK, text)
    return text.replace(CONFIG_OLD, CONFIG_NEW).replace(CONFIG_MIN_OLD, CONFIG_MIN_NEW)


def json_transform(s):
    """The same transform for text stored JSON-escaped (pinned snapshots that hold raw HTML in a string)."""
    import json
    enc = lambda x: json.dumps(x, ensure_ascii=False)[1:-1]
    if enc(BLOCK) in s:
        return s
    s = s.replace(enc('<script id="Cookiebot"'), enc(BLOCK) + enc('<script id="Cookiebot"'))
    return s.replace(enc(CONFIG_OLD), enc(CONFIG_NEW)).replace(enc(CONFIG_MIN_OLD), enc(CONFIG_MIN_NEW))
