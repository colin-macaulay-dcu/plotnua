#!/usr/bin/env python3
"""PLOTNUA · PACKAGE N · 'Request an introduction' block (shared module and CLI).

ONE source for the block on every placement page. The switch is
atlas-tools/release/plotnua-introductions.json -> "public". While it is false,
apply() returns the page UNCHANGED (byte for byte) and strips any stale block,
so wiring this module into a builder changes nothing until the founder flips it.

Founder-approved principles carried by the block:
  * free to homeowners, no obligation; supplier participation optional;
  * a SUPPLIER-SPECIFIC form appears only for a supplier in config "suppliers"
    (written agreement on file), with the approved sentence naming that supplier;
    every other placement shows the GENERAL form (PlotNua reviews and replies;
    nothing is shared with any supplier without separate permission);
  * the referral-fee disclosure is always shown beside the form;
  * fields: name, email, county, timeframe, optional description. No phone,
    Eircode or address. Nothing preselected. No marketing permission.
  * no pop-up: the primary action expands the form in place;
  * analytics events only with Cookiebot statistics consent, never personal data.

Supplier pages call apply() from their own builder (fully regenerated pages).
Premium guides and discoveries take the block as a fenced region
(<!-- pn-intro:start --> ... <!-- pn-intro:end -->), the pattern premium_pages.py
allows for data-region builders, via this CLI:

  python3 atlas-tools/plotnua_introductions.py --check
      config valid; while off, NO placement page carries a block
  python3 atlas-tools/plotnua_introductions.py --apply
      write/strip the fenced region on the guide and discovery placements
  python3 atlas-tools/plotnua_introductions.py --preview DIR [--preview-supplier slug=Name]
      write flag-ON copies of every placement page into DIR (review only)
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "atlas-tools" / "release" / "plotnua-introductions.json"
START, END = "<!-- pn-intro:start -->", "<!-- pn-intro:end -->"
FENCE_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
ANCHOR = "</main>"

# Must equal worker/garden-lead/src/introduction.js (proved by prove-plotnua-introductions.py).
SUPPLIER_CONSENT_TEMPLATE = ("I agree that PlotNua may share my enquiry and contact details with "
                             "[supplier name] so they can contact me about this project.")
GENERAL_CONSENT = ("I agree that PlotNua may use my enquiry and contact details to review my project "
                   "and reply to me. PlotNua will not share my details with any supplier unless I "
                   "give separate permission.")
DISCLOSURE = ("Where a commercial referral arrangement exists, PlotNua may receive a referral fee. "
              "Such arrangements do not determine our editorial recommendations.")
TIMEFRAMES = [("within-3-months", "Within 3 months"), ("3-6-months", "3 to 6 months"),
              ("6-12-months", "6 to 12 months"), ("over-12-months", "More than 12 months"),
              ("not-sure", "Not sure yet")]
COUNTIES = ["Antrim", "Armagh", "Carlow", "Cavan", "Clare", "Cork", "Derry", "Donegal", "Down",
            "Dublin", "Fermanagh", "Galway", "Kerry", "Kildare", "Kilkenny", "Laois", "Leitrim",
            "Limerick", "Longford", "Louth", "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon",
            "Sligo", "Tipperary", "Tyrone", "Waterford", "Westmeath", "Wexford", "Wicklow"]


def load(path=CONFIG):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def placement_for(cfg, rel):
    for p in cfg["placements"]:
        if p["page"] == rel:
            return p
    return None


def supplier_consent(name):
    return SUPPLIER_CONSENT_TEMPLATE.replace("[supplier name]", name)


E = lambda s: html.escape(s, quote=True)

CSS = """<style>
.pni{--pni-a:#B39272;--pni-l:rgba(127,127,127,.38);--pni-bg:rgba(127,127,127,.07);color:inherit;
  font-family:var(--sans,var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif));padding:56px 0 64px;border-top:1px solid var(--pni-l)}
.pni[data-tone=light]{--pni-a:#7A5C3E}
.pni-w{max-width:760px;margin:0 auto;padding:0 16px}
.pni-k{margin:0 0 10px;font-size:11.5px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--pni-a)}
.pni-h{font-family:var(--serif,var(--p4-serif,'Instrument Serif',Georgia,serif));font-weight:400;font-size:clamp(30px,3.6vw,44px);line-height:1.1;margin:0 0 14px}
.pni-p{margin:0 0 20px;font-size:17px;line-height:1.6;max-width:62ch}
.pni-go,.pni-send{display:inline-flex;align-items:center;gap:10px;min-height:48px;padding:0 24px;border-radius:999px;border:1px solid var(--pni-a);
  background:var(--pni-a);color:#16171a;font:600 16px/1 inherit;font-family:inherit;cursor:pointer}
.pni-go:focus-visible,.pni-send:focus-visible,.pni input:focus-visible,.pni select:focus-visible,.pni textarea:focus-visible{outline:2px solid var(--pni-a);outline-offset:3px}
.pni-f{margin-top:22px;padding:24px;border:1px solid var(--pni-l);border-radius:14px;background:var(--pni-bg);display:grid;gap:16px}
.pni-f[hidden],.pni-ok[hidden],.pni-go[hidden]{display:none}
.pni-row{display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media (max-width:640px){.pni-row{grid-template-columns:1fr}.pni{padding:44px 0 52px}.pni-f{padding:18px}}
.pni label{display:grid;gap:6px;font-size:14px;font-weight:600}
.pni .pni-opt{font-weight:400;opacity:.75}
.pni input[type=text],.pni input[type=email],.pni select,.pni textarea{width:100%;box-sizing:border-box;min-height:46px;padding:10px 12px;border-radius:8px;
  border:1px solid var(--pni-l);background:transparent;color:inherit;font:16px/1.4 inherit;font-family:inherit}
.pni select option{color:#16171a}
.pni textarea{min-height:110px;resize:vertical}
.pni .pni-c{display:grid;grid-template-columns:22px 1fr;gap:12px;align-items:start;font-weight:400;font-size:15px;line-height:1.5}
.pni .pni-c input{width:20px;height:20px;margin:2px 0 0}
.pni-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.pni-fine{margin:0;font-size:13.5px;line-height:1.55;opacity:.82}
.pni-fine a{color:inherit}
.pni-msg{margin:0;font-size:15px;min-height:1.2em}
.pni-ok{margin-top:22px;padding:22px 24px;border:1px solid var(--pni-a);border-radius:14px}
.pni-ok p{margin:0 0 8px;font-size:17px;line-height:1.55}
</style>"""

JS = """<script>/* Package N introduction block. No storage. Analytics only with statistics consent, never personal data. */
(function(){var s=document.getElementById('pn-intro');if(!s)return;
var go=s.querySelector('.pni-go'),f=s.querySelector('.pni-f'),m=s.querySelector('.pni-msg'),ok=s.querySelector('.pni-ok'),t0=0,busy=false;
var kind=s.getAttribute('data-kind'),pt=s.getAttribute('data-page-type'),sup=s.getAttribute('data-supplier')||'';
function ev(n){try{if(window.Cookiebot&&Cookiebot.consent&&Cookiebot.consent.statistics&&typeof window.gtag==='function'){var p={intro_kind:kind,page_type:pt};if(kind==='supplier')p.supplier=sup;gtag('event',n,p);}}catch(e){}}
go.addEventListener('click',function(){f.hidden=false;go.setAttribute('aria-expanded','true');go.hidden=true;t0=Date.now();ev('pn_intro_open');var first=f.querySelector('input[name=name]');if(first)first.focus();});
f.addEventListener('submit',function(e){e.preventDefault();if(busy)return;
 if(!f.reportValidity()){return;}
 var v=function(n){var el=f.elements[n];return el?el.value:'';};
 var c=f.elements['consent'];
 var body={name:v('name'),email:v('email'),county:v('county'),timeframe:v('timeframe'),description:v('description'),
  page:s.getAttribute('data-page'),consent:!!(c&&c.checked),consent_text:s.querySelector('.pni-ct').textContent.replace(/\\s+/g,' ').trim(),
  elapsed_ms:t0?Date.now()-t0:0,gotcha:v('company_website')};
 if(kind==='supplier')body.supplier=sup;
 busy=true;f.querySelector('.pni-send').disabled=true;m.textContent='Sending\\u2026';ev('pn_intro_submit');
 fetch(s.getAttribute('data-endpoint'),{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body),credentials:'omit',referrerPolicy:'no-referrer'})
 .then(function(r){return r.json().catch(function(){return {};});})
 .then(function(j){if(j&&j.ok===true&&j.state==='received'&&j.reference){f.hidden=true;ok.hidden=false;ok.querySelector('.pni-ref').textContent=j.reference;ok.focus();ev('pn_intro_received');}
  else{throw new Error(j&&j.state==='refused'&&j.field?'field':'down');}})
 .catch(function(err){busy=false;f.querySelector('.pni-send').disabled=false;ev('pn_intro_error');
  m.textContent=err&&err.message==='field'?'Something in the form needs another look. Please check each field and try again.':'Your request could not be sent just now, and nothing was recorded. Please try again, or email hello@plotnua.ie.';});
});})();
</script>"""


def block(cfg, p, preview_suppliers=None):
    """The fenced block for one placement. preview_suppliers lets a REVIEW build show the
    supplier-specific variant; it is never read from the config file."""
    suppliers = dict(cfg.get("suppliers") or {})
    suppliers.update(preview_suppliers or {})
    slug = p.get("supplier")
    named = suppliers.get(slug) if slug else None
    tone = p.get("tone", "auto")
    if named:
        name = named["name"]
        kind, consent = "supplier", supplier_consent(name)
        head = "Request an introduction to %s" % E(name)
        lead = ("Tell PlotNua a little about your project and we&rsquo;ll introduce you to %s, who will contact you "
                "directly. It&rsquo;s free, with no obligation to buy." % E(name))
    else:
        kind, consent = "general", GENERAL_CONSENT
        head = "Request an introduction"
        if p.get("label"):
            lead = ("Tell PlotNua a little about your project. We&rsquo;ll review it and reply personally, and can "
                    "suggest makers worth talking to. It&rsquo;s free, with no obligation. We won&rsquo;t pass your "
                    "details to %s or any other supplier unless you agree." % E(p["label"]))
        else:
            lead = ("Tell PlotNua a little about your project. We&rsquo;ll review it and reply personally, and can "
                    "suggest makers worth talking to. It&rsquo;s free, with no obligation. We won&rsquo;t pass your "
                    "details to any supplier unless you agree.")
    counties = "".join('<option>%s</option>' % c for c in COUNTIES)
    times = "".join('<option value="%s">%s</option>' % (k, E(v)) for k, v in TIMEFRAMES)
    return "".join([
        START, "\n", CSS, "\n",
        '<section class="pni" id="pn-intro" aria-labelledby="pni-h" data-kind="%s" data-page-type="%s" data-supplier="%s" '
        'data-tone="%s" data-page="/%s" data-endpoint="%s"><div class="pni-w">\n' % (kind, E(p["page_type"]), E(slug if named else ""), E(tone), E(p["page"]), E(cfg["endpoint"])),
        '  <p class="pni-k">Free introduction</p>\n',
        '  <h2 class="pni-h" id="pni-h">%s</h2>\n' % head,
        '  <p class="pni-p">%s</p>\n' % lead,
        '  <button type="button" class="pni-go" aria-expanded="false" aria-controls="pni-f">Request an introduction <span aria-hidden="true">&rarr;</span></button>\n',
        '  <form class="pni-f" id="pni-f" hidden novalidate>\n',
        '    <div class="pni-row"><label>Name<input type="text" name="name" autocomplete="name" maxlength="80" required></label>\n',
        '      <label>Email<input type="email" name="email" autocomplete="email" maxlength="120" required></label></div>\n',
        '    <div class="pni-row"><label>County<select name="county" required><option value="">Choose a county</option>%s</select></label>\n' % counties,
        '      <label>Project timeframe<select name="timeframe" required><option value="">Choose a timeframe</option>%s</select></label></div>\n' % times,
        '    <label><span>About your project <span class="pni-opt">(optional)</span></span><textarea name="description" maxlength="1000" '
        'placeholder="What you have in mind, and anything useful about your garden"></textarea></label>\n',
        '    <div class="pni-hp" aria-hidden="true"><label>Company website<input type="text" name="company_website" tabindex="-1" autocomplete="off"></label></div>\n',
        '    <label class="pni-c"><input type="checkbox" name="consent" required><span class="pni-ct">%s</span></label>\n' % E(consent),
        '    <p class="pni-fine">PlotNua researches suppliers independently. %s Read how we handle your details in our '
        '<a href="/%s">privacy notice</a>.</p>\n' % (E(DISCLOSURE), E(cfg["privacy_anchor"])),
        '    <div><button type="submit" class="pni-send">Send my request</button></div>\n',
        '    <p class="pni-msg" role="status" aria-live="polite"></p>\n',
        '  </form>\n',
        '  <div class="pni-ok" tabindex="-1" hidden><p><strong>Thank you. Your request has been received.</strong></p>'
        '<p>Your reference is <span class="pni-ref"></span>. PlotNua will review it and reply by email.</p></div>\n',
        '</div></section>\n', JS, "\n", END, "\n"])


def apply(text, rel, cfg=None, force=False, preview_suppliers=None):
    """Page text with the block in place (switch on) or removed (switch off).
    Off + no stale block => returns `text` itself, unchanged."""
    cfg = cfg or load()
    stripped = FENCE_RE.sub("", text)
    p = placement_for(cfg, rel)
    if not p or not (cfg.get("public") is True or force):
        return stripped
    if stripped.count(ANCHOR) != 1:
        raise SystemExit("plotnua_introductions: %s must contain %s exactly once" % (rel, ANCHOR))
    return stripped.replace(ANCHOR, block(cfg, p, preview_suppliers) + ANCHOR, 1)


def validate(cfg):
    errs = []
    if cfg.get("schema") != "plotnua.introductions.v1": errs.append("schema")
    if not isinstance(cfg.get("public"), bool): errs.append("public must be true or false")
    if not str(cfg.get("endpoint", "")).startswith("https://"): errs.append("endpoint must be https")
    for slug, s in (cfg.get("suppliers") or {}).items():
        if not s.get("name") or not s.get("agreement"):
            errs.append("supplier %s needs a name and a written agreement reference" % slug)
    for p in cfg["placements"]:
        f = ROOT / p["page"]
        if not f.exists(): errs.append("missing page " + p["page"]); continue
        if p["page_type"] not in ("supplier", "guide", "discovery"): errs.append("page_type " + p["page"])
        t = f.read_text(encoding="utf-8")
        if t.count(ANCHOR) != 1: errs.append("%s: %s not unique" % (p["page"], ANCHOR))
        if not cfg["public"] and START in t: errs.append("%s carries a block while the switch is off" % p["page"])
    return errs


FENCED_TYPES = ("guide", "discovery")   # supplier pages go through their builders


def main(argv):
    cfg = load()
    errs = validate(cfg)
    if "--check" in argv:
        for p in cfg["placements"]:
            t = (ROOT / p["page"]).read_text(encoding="utf-8")
            if apply(t, p["page"], cfg) != t: errs.append("STALE " + p["page"])
        print("\n".join(errs) if errs else "CHECK OK  introductions %s · %d placements · %d suppliers with agreement"
              % ("PUBLIC" if cfg["public"] else "off", len(cfg["placements"]), len(cfg.get("suppliers") or {})))
        return 1 if errs else 0
    if errs:
        print("REFUSED: " + "; ".join(errs)); return 1
    if "--apply" in argv:
        for p in cfg["placements"]:
            if p["page_type"] in FENCED_TYPES:
                f = ROOT / p["page"]; t = f.read_text(encoding="utf-8"); n = apply(t, p["page"], cfg)
                if n != t: f.write_text(n, encoding="utf-8"); print("wrote " + p["page"])
        return 0
    if "--preview" in argv:
        out = pathlib.Path(argv[argv.index("--preview") + 1])
        ps = {}
        for a in argv:
            if a.startswith("--preview-supplier="):
                slug, name = a.split("=", 1)[1].split("=", 1)
                ps[slug] = {"name": name, "agreement": "PREVIEW ONLY"}
        for p in cfg["placements"]:
            dst = out / p["page"]; dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(apply((ROOT / p["page"]).read_text(encoding="utf-8"), p["page"], cfg, force=True,
                                 preview_suppliers=ps), encoding="utf-8")
        print("preview: %d pages in %s" % (len(cfg["placements"]), out)); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
