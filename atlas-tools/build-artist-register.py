#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build artist-register.html: PlotArt's Artist Register, a private, CLOSED
expression-of-interest register for artists.

Founder approval to BUILD: 14 October 2026 ("PlotNua x PlotArt · Artist
Register · founder build approval"). SHIPPED CLOSED. Expressions of interest
only: no matching, public profiles, bookings, commissions, payments or
guaranteed introductions.

It reuses the Art Space Register infrastructure: the same Worker
(worker/art-space-register, a separate /artist route with its own switch,
allow-list, consent, duplicate check and 25-a-day cap), the same Airtable base
(a separate Artists table) and the same consent-proof, status-log and deletion
procedures. The homeowner register and its page are not touched.

The page is built from the site's own shell, taken from privacy.html: the
design-system stylesheet, brand mark, search rail, footer and reveal script.
Only the page's text, its scoped ar- styles and the register script are new.

GUARDS
  A1  the page on disk is exactly what this builder writes (--check)
  A2  ships closed. ARTIST_PUBLIC may be true only when (a) privacy.html
      carries the V5 artist section (V5_MARK and every governed sentence of
      governance/PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md), (b) the Worker's
      ARTIST_PRIVACY_VERSION is V5 and (c) ARTIST_OPEN_APPROVAL is complete.
      wrangler's ARTIST_WRITES_ENABLED may be "true" only while open. Closed:
      robots noindex, preview label, the form removed from the DOM unless
      ?register=preview.
  A3  the consent sentence on the page equals the Worker's ARTIST_CONSENT_TEXT
      and the proposed wording below, character for character
  A4  every option list on the page equals the Worker's VA vocabularies
  A5  the payload keys are exactly the Worker's ARTIST_ALLOWED_KEYS; the
      honeypot is never among them
  A6  no field for surname, address, Eircode, phone, date of birth, photo,
      price or sales; no file, tel, date or number input
  A7  the founder's heading and standfirst are present verbatim, the
      developmental disclaimer is present, and nothing promises a match,
      exhibition, sale, commission, booking, payment or introduction
  A8  the honeypot is present, off-screen, aria-hidden, out of the tab order
  A9  the register script calls only the artist endpoint, once, and reads no
      storage, cookie, analytics or My Plot contract
  A10 while closed, no page links to artist-register.html, the sitemap does
      not list it, and Search does not index it
  A11 A Home for Art: the future PlotArt link is PREPARED here (FUTURE_LINK,
      after FUTURE_ANCHOR) but NOT applied while closed (founder decision of
      13 Oct 2026 stays in force); the anchor exists exactly once
  A12 the homeowner register is untouched: the disc024 page and the homeowner
      Worker's vocabulary, allow-list, consent and handler are git HEAD's.
      (Its builder is not pinned here: Privacy V5 legitimately updates its
      publication check, founder approval 14 Oct 2026, 19:29.)
  A13 the Airtable schema's Artists table carries every field the artist route
      writes, with options identical to the Worker's

Usage:
  python3 atlas-tools/build-artist-register.py --apply
  python3 atlas-tools/build-artist-register.py --check
"""
import hashlib
import html as _html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE_NAME = "artist-register.html"
PAGE = ROOT / PAGE_NAME
SHELL = ROOT / "privacy.html"
WORKER = ROOT / "worker" / "art-space-register" / "src" / "index.js"
WRANGLER = ROOT / "worker" / "art-space-register" / "wrangler.toml"
SCHEMA = ROOT / "worker" / "art-space-register" / "airtable-schema.json"
V5_DRAFT = ROOT / "governance" / "PRIVACY-VERSION-2026-10-PHASE2-V5-DRAFT.md"
DISCOVERY = ROOT / "discovery-a-home-for-art.html"
SITEMAP = ROOT / "sitemap.xml"
SEARCH = ROOT / "search-index-v1.json"

# ----------------------------------------------------------------- the gate
ARTIST_PUBLIC = False            # CLOSED. Founder approval to build only, 14 Oct 2026.
ARTIST_OPEN_APPROVAL = {
    # NOT YET GIVEN. The founder's dated approval to OPEN goes here; until then
    # ARTIST_PUBLIC stays False and guard A2 refuses any opening.
    "founder_approval": "",
    "privacy_v5": "Privacy Notice V5 approved for publication by the founder, 14 October 2026 (19:45); "
                  "live on plotnua.ie from main 2c4e9dc.",
    "self_assessment": "Artist Register addendum to the Art Space Register GDPR self-assessment, dated and "
                       "approved by the founder, 14 October 2026 (19:45).",
    "airtable_created": "Artists table (tblwsmo1HGwd2ZG47) and the register fields on Status log, Consent proofs "
                        "and Deletion log created by the founder, 14 October 2026; verified read-only against "
                        "airtable-schema.json and the Worker the same evening (19 fields, all options match).",
    "controlled_test": "Controlled live registration-and-deletion test by the founder, 14 October 2026: valid "
                       "registration, Artists record, V5 consent proof, status log, duplicate prevention, "
                       "homeowner isolation, deletion and Deletion log entry all PASS; artist route closed again "
                       "(Worker version 33f42f08-0729-4cc3-b666-a69703ef4274). See "
                       "governance/ARTIST-REGISTER-BUILD-2026-10-14.md §8.",
}
V5_VERSION = "2026-10-PHASE2-V5"
V5_MARK = "PLOTNUA-ARTIST-PRIVACY-V5"

ENDPOINT = "https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/artist"
HOST_ENDPOINT_PATH = "/v1/art-space-register/host"

# FOUNDER WORDING, 14 Oct 2026 (19:25). Final only with the founder's approval of
# Privacy Notice V5. Kept identical to the Worker's ARTIST_CONSENT_TEXT (guard A3).
CONSENT = ("I confirm that I am 18 or over and consent to PlotNua storing my Artist Register details "
           "and contacting me about the development of PlotArt and potential opportunities to connect "
           "with homeowners. I understand that registering does not guarantee an opportunity and that "
           "I can withdraw my consent at any time.")

HEADING = "Your art. Somewhere unexpected."
STANDFIRST = "What if the perfect place for your artwork wasn&rsquo;t a gallery?"
SEND_LABEL = "Submit my registration"
DISCLAIMER = ("Registering doesn&rsquo;t mean you&rsquo;ll be offered a space, an exhibition, a sale, a "
              "commission or an introduction. PlotNua is simply finding out whether artists would be "
              "interested.")

# ----------------------------------------------------- A Home for Art (A11)
# PREPARED, NOT APPLIED. The founder's decision of 13 Oct 2026 (no link in the
# PlotArt section) stays in force until the register is tested and approved
# for launch. Opening applies this exact insertion after the anchor.
FUTURE_ANCHOR = '    <p class="dq-note">This matching service is not live yet.</p>\n'
FUTURE_LINK = ('    <p>Are you an artist? PlotArt&rsquo;s Artist Register is open for expressions of '
               'interest: free, private and non-binding. <a href="artist-register.html">Register your '
               'interest &rarr;</a></p>\n')

# ----------------------------------------------------------- vocab labels
LABELS = {
    "based_in": {
        "antrim": "Antrim", "armagh": "Armagh", "carlow": "Carlow", "cavan": "Cavan", "clare": "Clare",
        "cork": "Cork", "derry": "Derry / Londonderry", "donegal": "Donegal", "down": "Down",
        "dublin": "Dublin", "fermanagh": "Fermanagh", "galway": "Galway", "kerry": "Kerry",
        "kildare": "Kildare", "kilkenny": "Kilkenny", "laois": "Laois", "leitrim": "Leitrim",
        "limerick": "Limerick", "longford": "Longford", "louth": "Louth", "mayo": "Mayo",
        "meath": "Meath", "monaghan": "Monaghan", "offaly": "Offaly", "roscommon": "Roscommon",
        "sligo": "Sligo", "tipperary": "Tipperary", "tyrone": "Tyrone", "waterford": "Waterford",
        "westmeath": "Westmeath", "wexford": "Wexford", "wicklow": "Wicklow",
        "outside_ireland": "Outside Ireland"},
    "reach": {"local_area": "My local area", "particular_places": "Particular counties or regions",
              "anywhere_ireland": "Anywhere in Ireland"},
    "disciplines": {"painting": "Painting", "drawing_print": "Drawing and printmaking",
                    "photography": "Photography", "sculpture": "Sculpture",
                    "ceramics_craft": "Ceramics and craft", "textiles": "Textiles",
                    "installation_mixed": "Installation and mixed media",
                    "digital_video": "Digital and video art", "other": "Something else"},
    "interests": {"display": "Displaying artwork in a home",
                  "show_visitors": "Showing work to visitors, by arrangement",
                  "installation": "Creating a site-specific installation",
                  "store": "Storing finished artwork",
                  "reach_buyers": "Reaching potential buyers through a home setting"},
    "needs": {"wall": "Wall space", "floor_room": "Floor or room space", "outdoor": "Outdoor or garden space",
              "dry_storage": "Dry, secure storage", "not_sure": "Not sure yet"},
}

NOTICE = [
    ("What we keep.",
     "The name you work under, your email address, where you&rsquo;re based, where you would consider "
     "opportunities, what you make and which opportunities interest you &mdash; and, if you choose to "
     "tell us, the space your work needs, a website or portfolio link, and a short statement. We also "
     "keep a record that you gave your consent, which version of our privacy notice applied, and when "
     "you registered."),
    ("What we never ask for.",
     "Your home address, your phone number, your date of birth, photographs, prices or details of "
     "your sales."),
    ("Why we keep it.",
     "So that we can contact you about the development of PlotArt and about potential opportunities to "
     "connect with homeowners &mdash; for example to ask what would be useful to you, or to let you know "
     "if the idea develops."),
    ("Your details stay private.",
     "Registration details are accessible only to authorised people managing the register and to "
     "service providers where necessary to operate it. They are not shared with homeowners or made "
     "publicly available. There is no public profile, listing or directory, and nothing will be "
     "arranged without your agreement. We never sell your information or pass it to anyone for "
     "advertising."),
    ("Leaving.",
     "You can withdraw your consent at any time. Email hello@plotnua.ie and we will delete your "
     "record. There is nothing to cancel and no notice period."),
    ("How long we keep it.",
     "A maximum of 12 months, and less if the pilot no longer needs it. You can ask us to delete "
     "it at any time."),
    ("After deletion.",
     "We delete everything the register holds about you, including the record of your consent. "
     "Our database provider keeps deleted records in its trash for 7 days and its own recovery copies "
     "for up to 1 year; we never restore deleted records from them. We keep only an anonymous log "
     "entry with the dates and the reason, which contains nothing that identifies you."),
]

# -------------------------------------------------------------- the styles
CSS = """
  /* PLOTNUA-ARTIST-REGISTER-CSS · PlotArt Artist Register, founder approval to
     build 14 Oct 2026. Generated by atlas-tools/build-artist-register.py.
     Prefix ar-. The tokens and the form treatment are the Art Space
     Register's (disc024), so the two registers read as one family. */
  :root{ --stone:#EFE9DA; --body:#3A453F; --muted:#5A655F;
    --rule:rgba(31,59,46,.18); --rule-soft:rgba(31,59,46,.10); }
  .ar-chip{display:inline-block;margin:0 0 22px;font-family:'Work Sans',sans-serif;font-size:11px;
    font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:#6E5639;
    border:1px solid rgba(139,111,78,.4);border-radius:20px;padding:5px 12px;}
  .ar-cta{display:inline-flex;align-items:center;gap:11px;background:var(--ink);color:var(--brand-ivory);
    border:none;font-family:'Work Sans',sans-serif;padding:16px 28px;font-size:13.5px;letter-spacing:.09em;
    text-transform:uppercase;border-radius:32px;cursor:pointer;text-decoration:none;
    box-shadow:0 10px 26px rgba(31,59,46,.22);transition:background .22s ease, transform .22s ease;}
  .ar-cta:hover{background:var(--accent);transform:translateY(-2px);}
  .ar-cta[disabled]{opacity:.7;cursor:default;transform:none;}
  .privacy-intro .ar-cta{margin-top:34px;}
  .ar-card{margin:8px 0 0;padding:28px 24px 26px;border-radius:18px;background:var(--stone);max-width:760px;}
  .ar-card[hidden],.ar-form[hidden],.ar-done[hidden],.ar-closed[hidden],.ar-prev[hidden],.ar-msg[hidden],
  .ar-places[hidden]{display:none;}
  .ar-prev{margin:0 0 16px;font-family:'Work Sans',sans-serif;font-size:10px;font-weight:500;
    letter-spacing:.2em;text-transform:uppercase;color:#6E5639;border:1px solid rgba(139,111,78,.4);
    border-radius:20px;padding:5px 12px;display:inline-block;}
  .ar-privline{margin:0 0 20px;font-size:14px;line-height:1.6;color:var(--muted);}
  .ar-grid{display:grid;gap:18px;}
  @media(min-width:760px){ .ar-grid{grid-template-columns:repeat(2,1fr);} }
  .ar-f{display:grid;gap:6px;align-content:start;}
  .ar-f.is-wide{grid-column:1/-1;}
  .ar-f > label,.ar-set legend{font-family:'Work Sans',sans-serif;font-size:14.5px;font-weight:500;color:var(--ink);}
  .ar-opt{font-weight:400;color:var(--muted);}
  .ar-hint{font-size:13px;line-height:1.5;color:var(--muted);}
  .ar-f input[type=text],.ar-f input[type=email],.ar-f input[type=url],.ar-f select,.ar-f textarea{
    width:100%;min-height:50px;font-family:'Work Sans',sans-serif;font-size:16px;line-height:1.5;color:var(--ink);
    background:#FFFDF7;border:1px solid var(--rule);border-radius:12px;padding:12px 14px;
    -webkit-appearance:none;appearance:none;}
  .ar-f textarea{min-height:96px;resize:vertical;}
  .ar-f input:focus,.ar-f select:focus,.ar-f textarea:focus{outline:2px solid var(--accent);outline-offset:1px;}
  .ar-f [aria-invalid=true],.ar-set[aria-invalid=true] .ar-tick{border-color:#7A3B2E;}
  .ar-set{margin:0;padding:0;border:0;min-width:0;}
  .ar-set legend{padding:0;margin:0 0 8px;}
  .ar-ticks{display:grid;gap:8px;margin:8px 0 0;}
  @media(min-width:760px){ .ar-ticks.is-two{grid-template-columns:1fr 1fr;} }
  .ar-tick{display:grid;grid-template-columns:20px 1fr;gap:4px 11px;align-items:center;padding:12px 14px;
    border-radius:12px;background:#FFFDF7;border:1px solid var(--rule-soft);}
  .ar-tick:has(input:checked){border-color:var(--ink);}
  .ar-tick input{width:20px;height:20px;margin:0;accent-color:var(--accent);}
  .ar-tick label{font-size:15px;line-height:1.5;color:var(--body);cursor:pointer;}
  .ar-consent{margin:22px 0 0;align-items:start;border-color:var(--rule);}
  .ar-consent input{margin-top:2px;}
  .ar-notice{margin:12px 0 0;}
  .ar-notice summary{cursor:pointer;padding:12px 0;font-size:13.5px;color:var(--soft);}
  .ar-notice summary:hover,.ar-notice[open] summary{color:var(--ink);}
  .ar-noticebody{font-size:14px;line-height:1.7;color:var(--body);max-width:68ch;}
  .ar-noticebody p{margin:0 0 12px;color:var(--body);font-size:14px;line-height:1.7;}
  .ar-noticebody strong{font-weight:500;color:var(--ink);}
  .ar-actions{margin:22px 0 0;display:flex;flex-wrap:wrap;gap:14px 20px;align-items:center;}
  .ar-msg{margin:16px 0 0;font-size:14.5px;line-height:1.65;color:#7A3B2E;}
  .ar-done-h{font-family:'Fraunces',Georgia,serif;font-weight:500;font-size:clamp(22px,4vw,26px);
    line-height:1.2;color:var(--ink);margin:0 0 12px;max-width:none;}
  .ar-done-h:focus{outline:none;}
  .ar-done[data-state=received]::before{content:"";display:block;width:44px;height:44px;margin:0 0 14px;
    border-radius:50%;background:var(--ink) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M6 12.5l4 4 8-9' fill='none' stroke='%23F2EFE6' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/24px no-repeat;}
  .ar-card p.ar-p{margin:0 0 12px;font-size:15px;line-height:1.65;color:var(--body);max-width:68ch;}
  .ar-hp{position:absolute !important;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;}
  @media(max-width:560px){ .ar-card{padding:24px 18px;} .ar-actions .ar-cta{width:100%;justify-content:center;} }
  @media(prefers-reduced-motion:reduce){ .ar-cta{transition:none;} }
"""


# --------------------------------------------------------------- the worker
def worker_src():
    return WORKER.read_text(encoding="utf-8")


def worker_va():
    m = re.search(r"const VA = \{([\s\S]*?)\n\};", worker_src())
    if not m:
        die("A4 the Worker has no artist vocabulary (VA)")
    return {k: re.findall(r"'([a-z_]+)'", b) for k, b in re.findall(r"(\w+): \[([^\]]*)\]", m.group(1))}


def worker_consent():
    m = re.search(r'const ARTIST_CONSENT_TEXT =\s*"([^"]*)";', worker_src())
    return m.group(1) if m else None


def worker_allowed():
    m = re.search(r"const ARTIST_ALLOWED_KEYS = Object\.freeze\(\[([\s\S]*?)\]\)", worker_src())
    return sorted(re.findall(r"'([a-z_0-9]+)'", m.group(1))) if m else []


def wrangler(key):
    m = re.search(r'^%s\s*=\s*"([^"]*)"' % key, WRANGLER.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


# ------------------------------------------------------------------ page
def esc(s):
    return _html.escape(s, quote=True)


def ticks(name, key, two=False):
    rows = []
    for v in worker_va()[key]:
        rows.append('              <div class="ar-tick"><input type="checkbox" id="ar_%s_%s" name="%s" value="%s">'
                    '<label for="ar_%s_%s">%s</label></div>' % (key, v, key, v, key, v, esc(LABELS[key][v])))
    return ('            <div class="ar-ticks%s">\n' % (" is-two" if two else "")) + "\n".join(rows) + "\n            </div>\n"


def radios(key):
    rows = []
    for v in worker_va()[key]:
        rows.append('              <div class="ar-tick"><input type="radio" id="ar_%s_%s" name="%s" value="%s">'
                    '<label for="ar_%s_%s">%s</label></div>' % (key, v, key, v, key, v, esc(LABELS[key][v])))
    return '            <div class="ar-ticks">\n' + "\n".join(rows) + "\n            </div>\n"


def based_options():
    rows = ['              <option value="">Choose one</option>']
    for v in worker_va()["based_in"]:
        rows.append('              <option value="%s">%s</option>' % (v, esc(LABELS["based_in"][v])))
    return "\n".join(rows) + "\n"


def register_section():
    notice = "\n".join('            <p><strong>%s</strong> %s</p>' % (h, b) for h, b in NOTICE)
    return (
        '  <section class="article-section reveal" id="register" aria-labelledby="arRegH">\n'
        '    <div class="kicker">Register Your Interest</div>\n'
        '    <h2 id="arRegH">Tell us about your work.</h2>\n'
        '    <div class="ar-card ar-closed" id="arClosed">\n'
        '      <p class="ar-p"><strong>Registration isn&rsquo;t open yet.</strong> PlotArt&rsquo;s Artist Register is being '
        'prepared. When it opens, this is where you&rsquo;ll be able to register.</p>\n'
        '    </div>\n'
        '    <div class="ar-card" id="arCard" hidden>\n' +
        ('' if ARTIST_PUBLIC else '      <p class="ar-prev" id="arPrev">Private preview &middot; not public</p>\n') +
        '      <form class="ar-form" id="arForm" novalidate>\n'
        '        <p class="ar-privline">The name you work under, an email address and where you&rsquo;re based. '
        'No home address, no phone number, no photographs.</p>\n'
        '        <div class="ar-grid">\n'
        '          <div class="ar-f is-wide"><label for="arName">Artist name, or the name you work under</label>\n'
        '            <input type="text" id="arName" name="artist_name" autocomplete="name" maxlength="60" required></div>\n'
        '          <div class="ar-f"><label for="arEmail">Email address</label>\n'
        '            <input type="email" id="arEmail" name="email" autocomplete="email" maxlength="120" required></div>\n'
        '          <div class="ar-f"><label for="arBased">Where are you based?</label>\n'
        '            <select id="arBased" name="based_in" required>\n' + based_options() +
        '            </select></div>\n'
        '          <div class="ar-f is-wide">\n'
        '            <fieldset class="ar-set" id="arReach"><legend>Where would you consider opportunities?</legend>\n' +
        radios("reach") +
        '            </fieldset>\n'
        '            <div class="ar-f ar-places" id="arPlacesWrap" hidden><label for="arPlaces">Which counties or regions? '
        '<span class="ar-opt">(optional)</span></label>\n'
        '              <input type="text" id="arPlaces" name="reach_places" maxlength="120"></div></div>\n'
        '          <div class="ar-f is-wide">\n'
        '            <fieldset class="ar-set" id="arDisc"><legend>What do you make?</legend>\n'
        '            <span class="ar-hint">Tick any that apply.</span>\n' + ticks("disciplines", "disciplines", True) +
        '            </fieldset></div>\n'
        '          <div class="ar-f is-wide">\n'
        '            <fieldset class="ar-set" id="arInt"><legend>Which opportunities interest you?</legend>\n'
        '            <span class="ar-hint">Tick any that apply.</span>\n' + ticks("interests", "interests") +
        '            </fieldset></div>\n'
        '          <div class="ar-f is-wide">\n'
        '            <fieldset class="ar-set" id="arNeeds"><legend>What space would your work need? '
        '<span class="ar-opt">(optional)</span></legend>\n' + ticks("needs", "needs", True) +
        '            </fieldset></div>\n'
        '          <div class="ar-f is-wide"><label for="arPortfolio">Website or portfolio <span class="ar-opt">(optional)</span></label>\n'
        '            <input type="url" id="arPortfolio" name="portfolio" maxlength="200" inputmode="url" '
        'placeholder="https://" aria-describedby="arPortfolioHint">\n'
        '            <span class="ar-hint" id="arPortfolioHint">A link we can look at, starting https://. It stays private.</span></div>\n'
        '          <div class="ar-f is-wide"><label for="arStatement">A short artist statement <span class="ar-opt">(optional)</span></label>\n'
        '            <textarea id="arStatement" name="statement" maxlength="400" aria-describedby="arStatementHint"></textarea>\n'
        '            <span class="ar-hint" id="arStatementHint">A few sentences about your work. Please don&rsquo;t include '
        'your address, phone number or anyone else&rsquo;s details.</span></div>\n'
        '        </div>\n'
        '        <div class="ar-hp" aria-hidden="true"><label for="arWebsite">Leave this field empty</label>\n'
        '          <input type="text" id="arWebsite" name="website" tabindex="-1" autocomplete="off" value=""></div>\n'
        '        <div class="ar-tick ar-consent"><input type="checkbox" id="arConsent" required>\n'
        '          <label for="arConsent"><span id="arConsentText"></span></label></div>\n'
        '        <details class="ar-notice">\n'
        '          <summary>Before you register &mdash; what we keep, and what we never ask for</summary>\n'
        '          <div class="ar-noticebody">\n' + notice + "\n"
        '            <p>The full details are in our <a href="privacy.html">privacy notice</a>.</p>\n'
        '          </div>\n'
        '        </details>\n'
        '        <p class="ar-msg" id="arMsg" hidden role="status" aria-live="polite"></p>\n'
        '        <div class="ar-actions">\n'
        '          <button class="ar-cta" type="submit" id="arSend">%s</button>\n' % SEND_LABEL +
        '        </div>\n'
        '      </form>\n'
        '      <div class="ar-done" id="arDone" hidden role="status" aria-live="polite">\n'
        '        <h3 class="ar-done-h" id="arDoneH" tabindex="-1"></h3>\n'
        '        <div id="arDoneBody"></div>\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>\n')


def body_main():
    return (
        '<!-- ARTIST REGISTER · PlotArt (founder approval to build, 14 Oct 2026). SHIPPED CLOSED.\n'
        '     Generated by atlas-tools/build-artist-register.py -- do not hand-edit. -->\n'
        '<section class="privacy-intro reveal">\n'
        '  <div class="privacy-intro-inner">\n'
        '    <span class="ar-chip">PlotArt &middot; in development</span>\n'
        '    <h1>%s</h1>\n' % HEADING +
        '    <p class="subtitle">%s</p>\n' % STANDFIRST +
        '    <p class="lede">PlotArt is exploring whether homes and gardens in Ireland could become new places '
        'for artists to display, show, install and store their work &mdash; and perhaps help it find a buyer.</p>\n'
        '    <p class="lede">If that interests you, tell us. Registering is free, private and doesn&rsquo;t commit '
        'you to anything.</p>\n'
        '    <a class="ar-cta" href="#register">Register your interest <span aria-hidden="true">&darr;</span></a>\n'
        '  </div>\n'
        '</section>\n\n'
        '<main class="article">\n\n'
        '  <section class="article-section reveal">\n'
        '    <div class="kicker">The Idea</div>\n'
        '    <h2>Homeowners have space. Artists need it.</h2>\n'
        '    <p>Through A Home for Art, PlotNua is hearing from Irish homeowners who might be willing to offer a '
        'wall, a room, a garden or a dry place to keep finished work. Some would simply like to live with '
        'original art. Some would open a space to visitors, by arrangement.</p>\n'
        '    <p>Before anything is built, we want to hear from artists: whether this would be useful to you, '
        'what kind of opportunity would matter, and what your work needs.</p>\n'
        '  </section>\n\n'
        '  <section class="article-section reveal">\n'
        '    <div class="kicker">Before You Register</div>\n'
        '    <h2>What registering means, and what it doesn&rsquo;t.</h2>\n'
        '    <ul>\n'
        '      <li>It&rsquo;s free, and it doesn&rsquo;t commit you to anything.</li>\n'
        '      <li>It&rsquo;s private. Your details are not published, and there are no public artist profiles.</li>\n'
        '      <li>It&rsquo;s early. PlotArt is in development, and no matching service is being launched at this stage.</li>\n'
        '      <li id="arDisclaimer">%s</li>\n' % DISCLAIMER +
        '      <li>If the idea develops, we&rsquo;ll email you first, and nothing will be arranged without your agreement.</li>\n'
        '    </ul>\n'
        '  </section>\n\n' + register_section() +
        '\n</main>\n\n')


def script():
    va = worker_va()
    opts = {k: [[v, LABELS[k][v]] for v in va[k]] for k in ("disciplines", "interests", "needs", "reach")}
    return """<script>
/* PLOTNUA-ARTIST-REGISTER-JS · PlotArt Artist Register (founder approval to build,
 * 14 Oct 2026). Generated by atlas-tools/build-artist-register.py -- do not hand-edit.
 * SHIPS CLOSED: unless ARTIST_PUBLIC or ?register=preview, the form is REMOVED from
 * the DOM and the page says registration isn't open. Expressions of interest only.
 * Reads no storage, cookie or My Plot contract; calls one endpoint only. The consent
 * sentence exists once, written with textContent and sent verbatim. */
(function () {
  'use strict';
  var ARTIST_PUBLIC = %(public)s;
  var ENDPOINT = %(endpoint)s;
  var CONSENT_TEXT = %(consent)s;
  var OPTS = %(opts)s;
  var FIELD_NAME = {
    artist_name: 'the name you work under', email: 'your email address', based_in: 'where you\\u2019re based',
    reach: 'where you would consider opportunities', reach_places: 'the counties or regions',
    disciplines: 'at least one thing you make', interests: 'at least one opportunity',
    needs: 'the space your work needs', portfolio: 'a website link starting https://',
    statement: 'the statement', over_18: 'the confirmation that you are over 18 and agree',
    consent_text: 'the permission wording'
  };
  var FIELD_EL = { artist_name: 'arName', email: 'arEmail', based_in: 'arBased', reach: 'arReach',
    reach_places: 'arPlaces', disciplines: 'arDisc', interests: 'arInt', needs: 'arNeeds',
    portfolio: 'arPortfolio', statement: 'arStatement', over_18: 'arConsent' };
  var STATE = 'form';
  var FLAGGED = null;
  function $(id) { return document.getElementById(id); }
  function preview() {
    try { return /(?:^|[?&])register=preview(?:&|$)/.test(location.search); } catch (e) { return false; }
  }
  function picked(key) {
    var out = [];
    OPTS[key].forEach(function (o) { var b = $('ar_' + key + '_' + o[0]); if (b && b.checked) out.push(o[0]); });
    return out;
  }
  function msg(t) { var m = $('arMsg'); m.textContent = t || ''; m.hidden = !t; }
  function clearInvalid() {
    Object.keys(FIELD_EL).forEach(function (k) { var el = $(FIELD_EL[k]); if (el) el.removeAttribute('aria-invalid'); });
  }
  function flag(field) {
    msg('We still need ' + (FIELD_NAME[field] || 'one more thing') + '.');
    var el = $(FIELD_EL[field]);
    FLAGGED = el;
    if (!el) return;
    el.setAttribute('aria-invalid', 'true');
    var f = el.tagName === 'FIELDSET' ? el.querySelector('input') : el;
    try { f.focus(); } catch (e) {}
  }
  function show(which) {
    STATE = which;
    $('arForm').hidden = !(which === 'form' || which === 'sending');
    $('arDone').hidden = (which === 'form' || which === 'sending');
    $('arDone').setAttribute('data-state', which);
    var s = $('arSend');
    s.disabled = (which === 'sending');
    s.textContent = which === 'sending' ? 'Sending\\u2026' : %(send)s;
  }
  function end(which, heading, paras) {
    $('arDoneH').textContent = heading;
    var b = $('arDoneBody');
    b.innerHTML = '';
    paras.forEach(function (t) { var p = document.createElement('p'); p.className = 'ar-p'; p.textContent = t; b.appendChild(p); });
    show(which);
    try { $('arDoneH').focus(); } catch (e) {}
  }
  function received() {
    end('received', 'You\\u2019re on the register', [
      'We have what you told us about your work. Nobody else can see it.',
      'This is a register of interest, not a matching service. No homeowner will contact you, and nothing ' +
      'will be arranged without your agreement. If PlotArt develops in a way that could involve you, we\\u2019ll email you.',
      'To come off it, email hello@plotnua.ie. There is nothing to cancel and no notice period.'
    ]);
  }
  function notOpen() {
    end('not_open', 'The register isn\\u2019t open yet', [
      'Your details haven\\u2019t been saved.',
      'Nothing is waiting on you. When the register opens, this is where it will happen.'
    ]);
  }
  function unavailable() {
    end('unavailable', 'That didn\\u2019t go through', [
      'Something went wrong between this page and PlotNua, and your details haven\\u2019t been saved.',
      'Trying again in a minute is usually the whole fix. If it keeps happening, hello@plotnua.ie reaches a person.'
    ]);
  }
  function reach() { var r = picked('reach'); return r.length ? r[0] : ''; }
  /* The payload. These keys are the Worker's ARTIST_ALLOWED_KEYS exactly (guard A5);
     optional fields are sent only when filled in. */
  function payload() {
    var body = {
      artist_name: $('arName').value,
      email: $('arEmail').value,
      based_in: $('arBased').value,
      reach: reach(),
      disciplines: picked('disciplines'),
      interests: picked('interests'),
      over_18: $('arConsent').checked === true,
      consent_text: CONSENT_TEXT
    };
    if (body.reach === 'particular_places' && $('arPlaces').value.trim()) body.reach_places = $('arPlaces').value;
    if (picked('needs').length) body.needs = picked('needs');
    if ($('arPortfolio').value.trim()) body.portfolio = $('arPortfolio').value.trim();
    if ($('arStatement').value.trim()) body.statement = $('arStatement').value;
    return body;
  }
  function localProblem() {
    if (!$('arName').value.trim()) return 'artist_name';
    var e = $('arEmail').value.trim();
    if (!e || e.indexOf('@') < 1 || e.lastIndexOf('.') < e.indexOf('@')) return 'email';
    if (!$('arBased').value) return 'based_in';
    if (!reach()) return 'reach';
    if (!picked('disciplines').length) return 'disciplines';
    if (!picked('interests').length) return 'interests';
    var p = $('arPortfolio').value.trim();
    if (p && !/^https:\\/\\/[^\\s\\/:@]+\\.[^\\s\\/:@]{2,}(\\/\\S*)?$/i.test(p)) return 'portfolio';
    if (!$('arConsent').checked) return 'over_18';
    return null;
  }
  function submit(ev) {
    ev.preventDefault();
    if (STATE === 'sending') return;
    clearInvalid();
    var bad = localProblem();
    if (bad) { flag(bad); return; }
    msg('');
    /* Honeypot, after ordinary validation: filled -> nothing is sent. */
    if ($('arWebsite').value !== '') { unavailable(); return; }
    show('sending');
    fetch(ENDPOINT, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload()) })
      .then(function (r) {
        return r.json().then(function (j) { return { s: r.status, j: j }; }, function () { return { s: r.status, j: null }; });
      }).then(function (res) {
        var st = res.j && res.j.state;
        if (res.s === 200 && st === 'received') { received(); return; }
        if (res.s === 503 && st === 'not_open') { notOpen(); return; }
        if (res.s === 400 && st === 'refused') {
          show('form');
          msg('PlotNua could not accept that: ' + (FIELD_NAME[res.j && res.j.field] || 'one of the answers') +
              '. Nothing has been saved.');
          return;
        }
        unavailable();
      }).catch(function () { unavailable(); });
  }
  function init() {
    var card = $('arCard'), closed = $('arClosed');
    if (!card) return;
    if (!ARTIST_PUBLIC && !preview()) {
      if (card.parentNode) card.parentNode.removeChild(card);
      return;
    }
    if (closed && closed.parentNode) closed.parentNode.removeChild(closed);
    card.hidden = false;
    $('arConsentText').textContent = CONSENT_TEXT;
    OPTS.reach.forEach(function (o) {
      $('ar_reach_' + o[0]).addEventListener('change', function () {
        var on = reach() === 'particular_places';
        $('arPlacesWrap').hidden = !on;
        if (!on) $('arPlaces').value = '';
      });
    });
    $('arForm').addEventListener('submit', submit);
    /* A correction clears the flagged field's marking only. The message stays until
       the next submit replaces it: removing it here moved the Submit button out from
       under a click that had already started (the change fires on mousedown). */
    $('arForm').addEventListener('change', function (ev) {
      if (STATE !== 'form' || !FLAGGED || !(FLAGGED === ev.target || FLAGGED.contains(ev.target))) return;
      FLAGGED.removeAttribute('aria-invalid'); FLAGGED = null;
    });
    show('form');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
</script>
""" % {"public": "true" if ARTIST_PUBLIC else "false", "endpoint": json.dumps(ENDPOINT),
       "consent": json.dumps(CONSENT), "send": json.dumps(SEND_LABEL),
       "opts": json.dumps(opts, ensure_ascii=False)}


def build():
    shell = SHELL.read_text(encoding="utf-8")
    try:
        pre = shell[:shell.index('<title>')]
        fav = shell[shell.index("<!-- Favicons"):shell.index("<!-- Open Graph -->")]
        style = shell[shell.index('<link rel="preconnect"'):shell.index("</style>\n</head>")]
        # Privacy V5 adds one style rule for its own sub-headings; it is not part
        # of the shared shell, so the artist page is identical before and after V5.
        style = style.split("/* PLOTNUA PRIVACY V5")[0]
        top = shell[shell.index("<body>"):shell.index("<!-- PRIVACY INTRO")]
        foot = shell[shell.index("<footer>"):shell.index("</body>")]
    except ValueError:
        die("A1 the privacy.html shell no longer has the expected structure")
    title = "Artist Register | PlotArt | PlotNua"
    desc = ("PlotArt is exploring new places for artists&rsquo; work in Irish homes and gardens. Register "
            "your interest: free, private and non-binding.")
    robots = "index, follow" if ARTIST_PUBLIC else "noindex, nofollow"
    url = "https://plotnua.ie/" + PAGE_NAME
    head = (pre +
            '<title>%s</title>\n' % title +
            '<meta name="description" content="%s">\n' % desc +
            '<meta name="robots" content="%s">\n' % robots +
            '<link rel="canonical" href="%s">\n\n' % url + fav +
            '<!-- Open Graph -->\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:site_name" content="PlotNua">\n'
            '<meta property="og:title" content="%s">\n' % title +
            '<meta property="og:description" content="%s">\n' % desc +
            '<meta property="og:image" content="https://plotnua.ie/assets/og/plotnua-og-image-1200x630.png">\n'
            '<meta property="og:url" content="%s">\n' % url +
            '<meta property="og:locale" content="en_IE">\n\n' +
            style + CSS + "</style>\n</head>\n")
    return head + top + body_main() + foot + script() + "</body>\n</html>\n"


# ------------------------------------------------------------------ guards
def visible(fragment):
    t = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<!--[\s\S]*?-->", " ", fragment)
    return _html.unescape(re.sub(r"<[^>]+>", " ", t))


def v5_published(priv):
    if V5_MARK not in priv or not V5_DRAFT.exists():
        return False
    ws = lambda t: re.sub(r"\s+", " ", t).strip()
    gov = re.findall(r"^> (.+)$", V5_DRAFT.read_text(encoding="utf-8"), re.M)
    text = ws(visible(priv))
    return bool(gov) and all(ws(_html.unescape(re.sub(r"<[^>]+>", "", g))) in text for g in gov)


def guards(page):
    body = page[page.index("<body>"):]
    main = page[page.index('<section class="privacy-intro'):page.index("</main>")]
    js = page[page.index("PLOTNUA-ARTIST-REGISTER-JS"):]
    code_js = re.sub(r"/\*[\s\S]*?\*/", "", js)
    # A2
    writes = wrangler("ARTIST_WRITES_ENABLED")
    if writes not in ("true", "false"):
        die('A2 ARTIST_WRITES_ENABLED is missing or not "true"/"false"')
    if ARTIST_PUBLIC:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("build_privacy_v5", ROOT / "atlas-tools" / "build-privacy-v5.py")
        _pv5 = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_pv5)
        if not v5_published(SHELL.read_text(encoding="utf-8")) or not _pv5.published_ok():
            die("A2 the register may not open: privacy.html does not carry the approved V5 artist section")
        if wrangler("ARTIST_PRIVACY_VERSION") != V5_VERSION:
            die("A2 the register may not open: ARTIST_PRIVACY_VERSION is not %s" % V5_VERSION)
        if not all(isinstance(ARTIST_OPEN_APPROVAL.get(k), str) and ARTIST_OPEN_APPROVAL[k].strip()
                   for k in ARTIST_OPEN_APPROVAL):
            die("A2 the register may not open: ARTIST_OPEN_APPROVAL is incomplete")
        if 'id="arPrev"' in page or 'content="noindex' in page:
            die("A2 an open page still carries the preview label or noindex")
    else:
        if writes == "true":
            die("A2 the artist route would take writes while the register page is closed")
        if 'content="noindex, nofollow"' not in page or 'id="arPrev"' not in page or "var ARTIST_PUBLIC = false;" not in page:
            die("A2 a closed page must be noindex, carry the preview label and the closed switch")
        if 'id="arClosed"' not in page or "removeChild(card)" not in page:
            die("A2 a closed page must remove the form and say registration isn't open")
    # A3
    if worker_consent() != CONSENT:
        die("A3 the Worker's artist consent sentence differs from the proposed wording")
    if js.count(json.dumps(CONSENT)) != 1 or "$('arConsentText').textContent = CONSENT_TEXT" not in js:
        die("A3 the page's consent sentence is not the canonical one, written with textContent")
    # A4
    va = worker_va()
    for key in ("reach", "disciplines", "interests", "needs"):
        found = re.findall(r'id="ar_%s_([a-z_]+)"' % key, page)
        if found != va[key]:
            die("A4 %s on the page %r differs from the Worker %r" % (key, found, va[key]))
    based = re.findall(r'<option value="([a-z_]+)">', page)
    if based != va["based_in"] or len(based) != 33:
        die("A4 based_in options differ from the Worker's 32 counties plus outside_ireland")
    for key in LABELS:
        if set(LABELS[key]) != set(va[key]):
            die("A4 labels for %s do not cover exactly the Worker's values" % key)
    # A5
    keys = set(re.findall(r"\bbody\.([a-z_]+) =", js)) | set(
        re.findall(r"^\s+([a-z_0-9]+): ", re.search(r"var body = \{([\s\S]*?)\};", js).group(1), re.M))
    if sorted(keys) != worker_allowed():
        die("A5 payload keys %r differ from ARTIST_ALLOWED_KEYS %r" % (sorted(keys), worker_allowed()))
    if "website" in keys:
        die("A5 the honeypot is in the payload")
    # A6
    form = page[page.index('<form class="ar-form"'):page.index("</form>")]
    for bad in ("surname", "address\"", "eircode", "phone\"", "birth", "photo", "price", "sales\""):
        if re.search(r'name="[^"]*%s' % bad.strip('"'), form, re.I):
            die("A6 forbidden field: " + bad)
    if re.search(r'type="(file|tel|date|number)"', form):
        die("A6 a file, tel, date or number input is present")
    # A7
    if "<h1>%s</h1>" % HEADING not in page or '<p class="subtitle">%s</p>' % STANDFIRST not in page:
        die("A7 the founder's heading or standfirst is missing")
    if page.count(DISCLAIMER) != 1 or "PlotArt is in development" not in visible(main):
        die("A7 the developmental status or the disclaimer is missing")
    strings = " ".join(a or b for a, b in re.findall(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"", code_js))
    # The disclaimer and the consent sentence are the two places that NAME what is
    # not offered ("does not guarantee"); both are pinned elsewhere (A3, A7) and
    # removed before the scan, so any other promise wording still refuses.
    vis = (visible(main).replace(_html.unescape(DISCLAIMER), " ") + " " + strings.replace(CONSENT, " ")).lower()
    bad = re.search(r"\b(guarantee[ds]?|earn(ings)?|commissions?|bookings?|book a|matched|we will (introduce|match|"
                    r"exhibit|sell|book|find)|we'll (introduce|match|exhibit|sell|find)|you will be (paid|offered|"
                    r"matched)|get paid|be paid|sell your work|exhibition guaranteed)\b", vis)
    if bad:
        die("A7 promise wording on the page: %r" % bad.group(0))
    for need in ("not a matching service", "nothing will be arranged without your agreement",
                 "no public artist profiles", "doesn’t commit you to anything".lower()):
        if need not in vis:
            die("A7 assurance missing: " + need)
    # A8
    if not re.search(r'<div class="ar-hp" aria-hidden="true">[\s\S]*?tabindex="-1"', form):
        die("A8 honeypot missing, visible or in the tab order")
    # A9
    for bad in ("localStorage", "sessionStorage", "document.cookie", "gtag", "dataLayer", "PlotNuaJourneySave",
                "plotnua.myplot", "XMLHttpRequest", "sendBeacon", HOST_ENDPOINT_PATH, "garden-register"):
        if bad in code_js:
            die("A9 the register script references %r" % bad)
    if code_js.count("fetch(") != 1 or js.count(ENDPOINT) != 1:
        die("A9 the register script must call only the artist endpoint, once")
    # A10
    if not ARTIST_PUBLIC:
        for f in ROOT.glob("*.html"):
            if f.name != PAGE_NAME and "artist-register.html" in f.read_text(encoding="utf-8", errors="replace"):
                die("A10 %s links to the closed artist register" % f.name)
        if "artist-register" in SITEMAP.read_text(encoding="utf-8"):
            die("A10 the sitemap lists the closed artist register")
        if SEARCH.exists() and "artist-register" in SEARCH.read_text(encoding="utf-8"):
            die("A10 Search indexes the closed artist register")
    # A11
    disc = DISCOVERY.read_text(encoding="utf-8")
    if disc.count(FUTURE_ANCHOR) != 1:
        die("A11 the A Home for Art anchor for the future link is not found exactly once")
    if not ARTIST_PUBLIC and FUTURE_LINK in disc:
        die("A11 the A Home for Art link is visible while the register is closed")
    # A12
    try:
        d = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", "HEAD", "--",
                            "disc024-open-your-home-to-art.html"],
                           capture_output=True, text=True, check=True).stdout.strip()
        if d:
            die("A12 homeowner register files changed: " + d)
        head_w = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:worker/art-space-register/src/index.js"],
                                capture_output=True, text=True, check=True).stdout
        cur = worker_src()
        for const in ("const V = {", "const ALLOWED_KEYS", "const CONSENT_TEXT =", "async function handleHost"):
            seg = lambda s: s[s.index(const):s.index("\n}", s.index(const)) if const.startswith("async") else
                              s.index(";", s.index(const))]
            if const in head_w and seg(head_w) != seg(cur):
                die("A12 the homeowner Worker's %s changed" % const)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    # A13
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    artists = {t["name"]: t for t in schema["tables"]}.get("Artists")
    if not artists:
        die("A13 the schema has no Artists table")
    fields = {f["name"]: f for f in artists["fields"]}
    src = worker_src()
    rec = re.search(r"const rec = \{([\s\S]*?)\};", src).group(1)
    written = {i.split(":")[0].strip() for i in rec.split(",") if i.strip()} | set(re.findall(r"rec\.([a-z_]+) =", src))
    for w in written:
        if w not in fields:
            die("A13 the artist route writes Artists.%s but the schema lacks it" % w)
    for key in ("based_in", "reach", "disciplines", "interests", "needs"):
        if fields[key].get("options") != va[key]:
            die("A13 schema options for Artists.%s differ from the Worker" % key)
    if fields["status"].get("options") != ["interest_submitted"]:
        die("A13 Artists.status must have exactly one option, interest_submitted")


def main(argv):
    if "--apply" not in argv and "--check" not in argv:
        print(__doc__)
        sys.exit(1)
    page = build()
    guards(page)
    state = "OPEN" if ARTIST_PUBLIC else "CLOSED"
    if "--check" in argv:
        if not PAGE.exists() or PAGE.read_text(encoding="utf-8") != page:
            print("CHECK FAILED: %s is out of date; run --apply" % PAGE_NAME)
            sys.exit(1)
        print("%s: Artist Register %s · CHECK OK — A1-A13 pass" % (PAGE_NAME, state))
        return
    PAGE.write_text(page, encoding="utf-8")
    print("%s: Artist Register written, %s · APPLIED — A1-A13 pass" % (PAGE_NAME, state))


if __name__ == "__main__":
    main(sys.argv[1:])
