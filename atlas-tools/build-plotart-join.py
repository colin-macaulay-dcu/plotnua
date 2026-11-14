#!/usr/bin/env python3
"""PlotArt · Join PlotArt (Gallery Artist Programme Phase 3, development 13 Nov 2026). NOT PUBLISHED.

Builds the public artist-recruitment pages from the founder-approved copy, in the state the launch switches say:

    plotart/join.html                 the application page and form
    plotart/curatorial-policy.html    the curatorial policy
    plotart/assets/pa-apply.js        the form script
    plotart/assets/plotart-join.css   the scoped Join styles (also linked by the homepage while open)
    plotart/index.html                the homepage "For artists" band, between its two markers
    plotart/founding-25.html          one pointer line to Join PlotArt

All of this exists ONLY in the "open" state (founder decision 13 Nov 2026: the recruitment pages are not published
while applications are closed). In every other state the homepage and the Founding 25 page are exactly as on main
and the three files above do not exist.

The state is gallery_application_state in the launch switches: not_open | open | paused | closed. It is never
inferred from the endpoint. The endpoint is gallery_application_endpoint, and the form posts only there.

    python3 atlas-tools/build-plotart-join.py [--switches FILE]           write the pages for the current state
    python3 atlas-tools/build-plotart-join.py --check [--switches FILE]   refuse if any page differs from that build
    python3 atlas-tools/build-plotart-join.py --out SITE [--switches FILE] build into a copy (SITE/plotart), for previews and proofs

Header, navigation and footer are copied from founding-25.html, so every PlotArt page stays identical in its chrome.
No new imagery: the pages are type, hairlines and space on the existing dark identity (design refinement 14 Nov 2026).
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PA = os.path.join(os.path.abspath(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else ROOT, "plotart")   # --out SITE: build into a copy
SW = sys.argv[sys.argv.index("--switches") + 1] if "--switches" in sys.argv else os.path.join(ROOT, "atlas-tools", "release", "plotart-launch-switches.json")
launch = json.load(open(SW, encoding="utf-8"))
STATE = launch.get("gallery_application_state")
EP = launch.get("gallery_application_endpoint")
STATES = ("not_open", "open", "paused", "closed")
if STATE not in STATES:
    sys.exit("gallery_application_state must be one of %s" % ", ".join(STATES))
if STATE == "open" and not (EP or "").endswith("/v1/art-space-register/gallery-application"):
    sys.exit("open needs gallery_application_endpoint to be the approved route")
OPEN = STATE == "open"
LINE = {"open": "Applications are open.", "paused": "Applications are paused at the moment.", "closed": "Applications have closed.", "not_open": "Applications are not yet open."}[STATE]
BADGE = "Applications open" if OPEN else LINE
E = lambda s: html.escape(s, quote=True)

# The three confirmations: exactly the Worker's (guard L18 compares them).
WSRC = open(os.path.join(ROOT, "worker", "art-space-register", "src", "index.js"), encoding="utf-8").read()
def wconst(name):
    m = re.search(r'const %s =\s*"([^"]+)";' % name, WSRC)
    return m.group(1) if m else None
SENT = {"eligibility": wconst("F25_ELIGIBILITY_TEXT"), "ownership": wconst("F25_OWNERSHIP_TEXT"), "privacy": wconst("GA_PRIVACY_TEXT")}
assert all(SENT.values()), SENT

F25 = open(os.path.join(PA, "founding-25.html"), encoding="utf-8").read()
HEADER = F25[F25.index('<body class="pa">'):F25.index('<main id="main">')]
FOOTER = F25[F25.index("</main>") + len("</main>\n"):]
STYLE = F25[F25.index("<style>"):F25.index("</style>") + len("</style>")]
OG_IMG = """<meta property="og:image" content="https://plotnua.ie/assets/og/plotart-og-1200x630.jpg">
<meta property="og:image:secure_url" content="https://plotnua.ie/assets/og/plotart-og-1200x630.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The PlotArt logo, an ivory serif P over bright painted brushstrokes, with the words PlotArt, A new home for Irish art">"""


def head(path, title, desc, extra_style=""):
    return f"""<!DOCTYPE html>
<html lang="en-IE" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<!-- Not for indexing until the founder approves it through the SEO workstream. Planned canonical:
     https://plotnua.ie/plotart/{path} -->
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#27282A">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotArt">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/plotart/{path}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
{OG_IMG}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(desc)}">
<meta name="twitter:image" content="https://plotnua.ie/assets/og/plotart-og-1200x630.jpg">
<meta name="twitter:image:alt" content="The PlotArt logo, an ivory serif P over bright painted brushstrokes, with the words PlotArt, A new home for Irish art">
<link rel="icon" href="/assets/brand/plotart-favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/brand/plotart-apple-touch-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="assets/plotart.css">
{extra_style}<script>document.documentElement.classList.remove('no-js');</script>
<link rel="stylesheet" href="/assets/identity/pn-section-menu.css?v=1">
</head>
"""

JOIN_STYLE = STYLE + "\n" + '<link rel="stylesheet" href="assets/plotart-join.css">\n'   # the form styles (as the Founding 25 form) + the scoped Join styles
POLICY_STYLE = '<link rel="stylesheet" href="assets/plotart-join.css">\n'

CRITERIA = [   # (name, short line for Join PlotArt, full line for the curatorial policy)
    ("Artistic quality", "A considered approach to materials, technique and ideas.",
     "A considered approach to technique, materials, composition, expression or ideas. We look at the work itself, not at how it is described."),
    ("A distinctive voice", "A recognisable direction that is your own.",
     "Originality and individuality: a recognisable direction that is your own, whatever your subject or medium."),
    ("A developed body of work", "A coherent portfolio rather than a single piece.",
     "A coherent portfolio that shows your approach, your interests and how your work is developing."),
    ("Commitment to your practice", "Sustained engagement. Qualifications and representation are welcome, never required.",
     "Sustained engagement with your work. Qualifications, exhibitions and gallery representation are welcome but never required."),
    ("Contribution to the gallery", "What your work would bring to the collection.",
     "How your work would complement, strengthen or broaden the PlotArt collection."),
]
CRIT_SHORT = "\n".join(f"    <li><h3>{E(h)}</h3><p>{E(a)}</p></li>" for h, a, _ in CRITERIA)
CRIT_FULL = "\n".join(f"    <li><h3>{E(h)}</h3><p>{E(b)}</p></li>" for h, _, b in CRITERIA)

COUNTIES = ["antrim", "armagh", "carlow", "cavan", "clare", "cork", "derry", "donegal", "down", "dublin", "fermanagh", "galway", "kerry", "kildare",
            "kilkenny", "laois", "leitrim", "limerick", "longford", "louth", "mayo", "meath", "monaghan", "offaly", "roscommon", "sligo", "tipperary",
            "tyrone", "waterford", "westmeath", "wexford", "wicklow"]
MEDIA = [("painting", "Painting"), ("drawing", "Drawing"), ("works_on_paper", "Works on paper"), ("printmaking", "Printmaking"), ("photography", "Photography"),
         ("sculpture", "Sculpture"), ("ceramics_craft", "Ceramics and craft"), ("textiles", "Textiles"), ("mixed_media", "Mixed media"),
         ("digital", "Digital and new media"), ("other", "Something else")]
REQ = '<span class="pa-req" aria-hidden="true">*</span>'


def form():
    counties = "".join(f'<option value="{c}">{c.title()}</option>' for c in COUNTIES)
    media = "".join(f'<option value="{k}">{E(v)}</option>' for k, v in MEDIA)
    return f"""  <div class="pa-formbox">
  <form class="pa-form" data-ap-form data-endpoint="{E(EP)}" data-image-endpoint="{E(EP)}/image" novalidate aria-describedby="ap-required">
    <p class="pa-note" id="ap-required" style="margin:0">Fields marked {REQ} are required.</p>
    <fieldset class="pa-fs"><legend class="pa-fs-l">About you</legend>
    <div class="pa-field"><label for="ap-name">Artist's name {REQ}<span class="hint">The name you work under</span></label><input id="ap-name" name="artist_name" type="text" maxlength="80" autocomplete="name" required aria-describedby="ap-name-e"><p class="pa-err" id="ap-name-e" hidden></p></div>
    <div class="pa-field"><label for="ap-email">Email address {REQ}<span class="hint">We'll only use it about your application</span></label><input id="ap-email" name="email" type="email" maxlength="120" autocomplete="email" inputmode="email" required aria-describedby="ap-email-e"><p class="pa-err" id="ap-email-e" hidden></p></div>
    <div class="pa-field"><label for="ap-region">County {REQ}<span class="hint">Where you live or work on the island of Ireland</span></label><select id="ap-region" name="region" required aria-describedby="ap-region-e"><option value="">Choose a county</option>{counties}</select><p class="pa-err" id="ap-region-e" hidden></p></div>
    </fieldset>
    <fieldset class="pa-fs"><legend class="pa-fs-l">Your work</legend>
    <div class="pa-field"><label for="ap-medium">Primary medium {REQ}</label><select id="ap-medium" name="medium" required aria-describedby="ap-medium-e"><option value="">Choose your main medium</option>{media}</select><p class="pa-err" id="ap-medium-e" hidden></p></div>
    <div class="pa-field"><label for="ap-bio">Short artist biography {REQ}<span class="hint">A few sentences about you and your practice, in your own words. Please don't include health or other sensitive personal details</span></label><textarea id="ap-bio" name="bio" rows="6" minlength="40" maxlength="1000" required aria-describedby="ap-bio-c ap-bio-e"></textarea><p class="pa-count" id="ap-bio-c" aria-live="off">0 of 1,000 characters</p><p class="pa-err" id="ap-bio-e" hidden></p></div>
    <div class="pa-field pa-upload" data-ap-upload><p class="pa-up-h" id="ap-images-l">Show us your work</p><p class="hint" id="ap-images-h">Upload three to five images that give us a sense of your practice, ideally recent work from a single body of work.</p>
      <div class="pa-drop" data-ap-drop tabindex="0" role="button" aria-labelledby="ap-images-l" aria-describedby="ap-images-h ap-images-s ap-images-e"><p class="pa-drop-t"><span class="pa-drop-desk"><strong>Drag images here</strong> or <span class="pa-drop-btn">choose images</span></span><span class="pa-drop-touch"><strong>Choose images</strong> from your photos or files</span></p><p class="pa-drop-s" id="ap-images-s">JPG, PNG or WebP · up to five<span class="pa-drop-desk"> · you can also paste an image</span></p></div>
      <input id="ap-images" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-ap-file>
      <ul class="pa-thumbs" data-ap-thumbs aria-label="Your images"></ul><p class="pa-up-live" data-ap-up-live aria-live="polite"></p>
      <p class="pa-err" id="ap-images-e" hidden></p></div>
    <div class="pa-field"><label for="ap-portfolio">Or a link to an online portfolio<span class="hint">A website or gallery page where we can see your original work. Please add at least three images above, or a link here</span></label><input id="ap-portfolio" name="portfolio" type="text" maxlength="200" inputmode="url" autocapitalize="off" spellcheck="false" placeholder="yourwebsite.ie/portfolio" aria-describedby="ap-portfolio-e"><p class="pa-err" id="ap-portfolio-e" hidden></p></div>
    </fieldset>
    <fieldset class="pa-fs"><legend class="pa-fs-l">If you'd like to add more <span class="hint" style="display:inline">(optional)</span></legend>
    <div class="pa-field"><label for="ap-website">Your website</label><input id="ap-website" name="website" type="text" maxlength="200" inputmode="url" autocapitalize="off" spellcheck="false" placeholder="yourwebsite.ie" aria-describedby="ap-website-e"><p class="pa-err" id="ap-website-e" hidden></p></div>
    <div class="pa-field"><label for="ap-social">Instagram or professional profile<span class="hint">An @handle or a link</span></label><input id="ap-social" name="social_link" type="text" maxlength="120" autocapitalize="off" spellcheck="false" aria-describedby="ap-social-e"><p class="pa-err" id="ap-social-e" hidden></p></div>
    <div class="pa-field"><label for="ap-info">Anything else you'd like us to know<span class="hint">For example, if a gallery represents you</span></label><textarea id="ap-info" name="additional_info" rows="3" maxlength="800" aria-describedby="ap-info-e"></textarea><p class="pa-err" id="ap-info-e" hidden></p></div>
    </fieldset>
    <fieldset class="pa-fs"><legend class="pa-fs-l">Before you apply {REQ}</legend>
    <label class="pa-check"><input type="checkbox" name="eligibility" required aria-describedby="ap-eligibility-e"> <span data-ap-sentence="eligibility">{E(SENT['eligibility'])}</span></label><p class="pa-err" id="ap-eligibility-e" hidden></p>
    <label class="pa-check"><input type="checkbox" name="ownership" required aria-describedby="ap-ownership-e"> <span data-ap-sentence="ownership">{E(SENT['ownership'])}</span></label><p class="pa-err" id="ap-ownership-e" hidden></p>
    <label class="pa-check"><input type="checkbox" name="privacy" required aria-describedby="ap-privacy-e"> <span data-ap-sentence="privacy">{E(SENT['privacy'])}</span></label><p class="pa-err" id="ap-privacy-e" hidden></p>
    <p class="pa-note" style="margin:6px 0 0">Read the <a href="../privacy.html#plotart-artist-applications">privacy notice for applications</a> and <a href="#terms">the terms</a>. Accepting the Gallery Artist Agreement, and agreeing what's published, come later and separately.</p>
    </fieldset>
    <div class="pa-hp" aria-hidden="true"><label>Leave this blank <input type="text" name="nickname" tabindex="-1" autocomplete="off"></label></div>
    <div><button class="pa-btn pa-btn--solid" type="submit" data-pa-track="join_application_submit"><span data-ap-label>Send my application</span></button></div>
    <p class="pa-select-note" style="margin-top:0">Submitting an application doesn't guarantee selection. Decisions reflect the gallery’s curatorial direction.</p>
    <p class="pa-proto-note" role="status" aria-live="polite" data-ap-status hidden></p>
  </form>
  <div class="pa-f25-done" data-ap-done hidden tabindex="-1">
    <p class="pa-eyebrow">Application received</p>
    <h3>Thank you. Your application is in.</h3>
    <p>We'll email you at <strong data-ap-done-email></strong> within two working days to confirm, with your application reference. If it hasn't arrived by then, please check your spam folder.</p>
    <p>Every application is read individually, and we'll let you know the outcome by email. Applying doesn't guarantee a place, and nothing is published without your approval.</p>
    <p class="pa-note">To update or withdraw your application, email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p>
  </div>
  </div>"""


def apply_section():
    # Built only in the "open" state (the page does not exist otherwise).
    return f"""<section class="pa-sec pa-sec--deep pa-jn-apply" id="apply"><div class="pa-wrap pa-cols-2" style="align-items:start">
  <div class="pa-apply-intro"><h2 class="pa-apply-title">Apply.</h2>
  <p>It takes about ten minutes. You’ll need a short biography and three to five images of your work, or a link to your portfolio.</p>
  <p class="pa-jn-status" style="margin-top:22px">{LINE}</p>
  <p class="pa-jn-note">Every application is read individually, and applying doesn’t guarantee a place.</p>
  <p class="pa-jn-note">Already on PlotNua’s <a href="../artist-register.html">Artist Register</a>? That remains a private expression of interest; applying here is a separate step.</p></div>
{form()}
</div></section>"""


def join_page():
    return head("join.html", "Join PlotArt | PlotArt",
                "An invitation to join PlotArt, a curated online gallery of contemporary Irish art. Applications from artists based or working on the island of Ireland.",
                JOIN_STYLE) + HEADER + f"""<main id="main">

<section class="pa-jn-hero pa-jn-hero--join"><div class="pa-wrap">
  <p class="pa-jn-k">For artists</p>
  <h1>An invitation to join PlotArt.</h1>
  <div class="pa-jn-grid pa-jn-hero-foot">
    <p class="pa-jn-status">{LINE}</p>
    <div><p class="pa-jn-lede">A curated space for contemporary Irish art. We welcome applications from artists based or working on the island of Ireland.</p>
    <div class="pa-jn-acts"><a class="pa-jn-btn" href="#apply" data-pa-track="join_apply_click">Apply</a><a class="pa-jn-link" href="curatorial-policy.html">Curatorial policy</a></div></div>
  </div>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">The gallery</p>
  <div><h2>A gallery of your own.</h2>
  <ul class="pa-jn-three">
    <li><h3>Your work, shown properly</h3><p>A biography and a page for each work, shown whole and at its true proportions.</p></li>
    <li><h3>Introductions to collectors</h3><p>Enquiries come to you, or to the gallery that represents you. Every sale is yours to agree.</p></li>
    <li><h3>Your own Studio</h3><p>Add work, set prices and update availability at your own pace.</p></li>
  </ul></div>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Selection</p>
  <div><h2>How we select.</h2>
  <p>Every application is read individually. We have no house style and welcome every medium and subject. Applying doesn’t guarantee a place. <a href="curatorial-policy.html">Read the curatorial policy</a>.</p>
  <ul class="pa-jn-list">
{CRIT_SHORT}
  </ul></div>
</div></section>

<section class="pa-jn-sec" id="how"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Applying</p>
  <div><h2>From application to gallery.</h2>
  <ol class="pa-jn-steps">
    <li><h3>Apply</h3><p>A short biography and three to five images of your work, or a link to your portfolio.</p></li>
    <li><h3>Review</h3><p>We read every application and may ask to see a little more.</p></li>
    <li><h3>Decision</h3><p>We let you know by email, whatever the outcome.</p></li>
    <li><h3>Your gallery</h3><p>If you’re selected, you’re invited to PlotArt Studio, where you read and accept the Gallery Artist Agreement before your gallery is first published. Nothing goes live without your approval.</p></li>
  </ol></div>
</div></section>

<section class="pa-jn-sec" id="terms"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Terms</p>
  <div><h2 class="pa-jn-h-sm">The practical details</h2>
  <dl class="pa-jn-terms">
    <dt>Fees</dt><dd>There are no fees to apply, to join or to remain.</dd>
    <dt>Commission</dt><dd>PlotArt’s commission is 15% of the price of an original work or signed limited-edition print sold to a collector PlotArt introduced to you, once the sale is complete. It doesn’t apply to your independent sales.</dd>
    <dt>Introductions</dt><dd>A collector is introduced by PlotArt when they reach you through an enquiry carrying a PlotArt reference, or tell you before the sale is agreed that they found you through PlotArt. Collectors you already knew, or who found you another way, are independent.</dd>
    <dt>Duration</dt><dd>An introduction counts for 24 months. After that, only the sale of a particular work you were already discussing in writing within those 24 months carries commission.</dd>
    <dt>Commissioned work</dt><dd>Newly commissioned work is agreed between you and the collector and isn’t subject to the commission.</dd>
    <dt>Payment</dt><dd>Collectors pay you directly. PlotArt invoices its commission after a completed sale, on the price of the work including any frame, and excluding delivery, insurance, installation and any VAT you charge.</dd>
    <dt>Independence</dt><dd>There is no exclusivity, and you keep your copyright.</dd>
    <dt>Agreement</dt><dd>The full terms are in the PlotArt Gallery Artist Agreement, which you read and accept in PlotArt Studio before your gallery is first published. Founding Artists keep their own agreement; artists joining now become Gallery Artists.</dd>
  </dl></div>
</div></section>

{apply_section()}
</main>
""" + FOOTER.replace('<script src="assets/plotart.js" defer></script>', '<script src="assets/pa-apply.js" defer></script>\n<script src="assets/plotart.js" defer></script>', 1)


def policy_page():
    return head("curatorial-policy.html", "Curatorial Policy | PlotArt",
                "How PlotArt, a curated online gallery of contemporary Irish art, considers applications from artists.",
                POLICY_STYLE) + HEADER + f"""<main id="main">

<section class="pa-jn-hero"><div class="pa-wrap">
  <p class="pa-jn-k">Curatorial policy</p>
  <h1>An independently curated gallery of contemporary Irish art.</h1>
  <p class="pa-jn-lede">PlotArt brings together emerging, mid-career and established artists based or working on the island of Ireland.</p>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Approach</p>
  <div><h2>No house style.</h2>
  <p>We welcome every medium, from painting, drawing and printmaking to photography, sculpture, ceramics, textiles, digital and interdisciplinary practice, and every subject. We look at the strength of each artist’s work and what it would bring to the gallery as a whole.</p>
  <p>Our first artists joined through the Founding 25, our introductory programme. The gallery continues to grow through individual applications.</p></div>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Criteria</p>
  <div><h2>Five considerations.</h2>
  <p>No single criterion decides an application, and there is no scoring formula. Selection is a matter of curatorial judgement across all five.</p>
  <ul class="pa-jn-list">
{CRIT_FULL}
  </ul></div>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Process</p>
  <div><h2>How applications are considered.</h2>
  <ul class="pa-jn-list">
    <li><h3>Individually</h3><p>Every application is read with its images, statement and any links you provide.</p></li>
    <li><h3>With care</h3><p>We may ask for further images or a little more about your practice before we decide.</p></li>
    <li><h3>Without guarantee</h3><p>Submitting an application doesn’t guarantee selection. Decisions reflect the direction of the collection, not a judgement on the value of your practice.</p></li>
    <li><h3>Always answered</h3><p>We’ll tell you the outcome, whatever it is.</p></li>
    <li><h3>Without cost</h3><p>Applying costs nothing, and selection is never influenced by payment.</p></li>
  </ul></div>
</div></section>

<section class="pa-jn-sec"><div class="pa-wrap pa-jn-grid">
  <p class="pa-jn-k">Also</p>
  <div><ul class="pa-jn-list" style="margin-top:0">
    <li><h3>Artificial intelligence</h3><p>We welcome original digital work and AI-assisted practice. Artists tell us about any meaningful use of AI in making a work. Images generated entirely from prompts are not automatically eligible as original artist-created work.</p></li>
    <li><h3>How the gallery is arranged</h3><p>We set the order of galleries in the Artists’ Gallery by hand, for curatorial reasons. It is never influenced by any fee, payment or commission arrangement.</p></li>
    <li><h3>Independence</h3><p>You keep your copyright, and there is no exclusivity: you remain free to show and sell your work elsewhere and to work with other galleries.</p></li>
  </ul>
  <div class="pa-jn-acts"><a class="pa-jn-btn" href="join.html" data-pa-track="policy_join_click">Apply to join</a><a class="pa-jn-link" href="mailto:hello@plotnua.ie">hello@plotnua.ie</a></div></div>
</div></section>
</main>
""" + FOOTER


HB, HE = "<!-- pa-artist-apply:begin -->", "<!-- pa-artist-apply:end -->"


def home_band():
    # Built only in the "open" state. An invitation, not an advertisement: no figures, no terms, no selling points.
    return f"""{HB}
<section class="pa-jn-band" aria-labelledby="joinInviteH"><div class="pa-wrap pa-jn-band-grid">
  <div class="pa-jn-band-head"><p class="pa-jn-k">For artists</p>
  <h2 id="joinInviteH">An invitation to join PlotArt.</h2></div>
  <div class="pa-jn-band-body"><p class="pa-jn-lede">A curated space for contemporary Irish art. Independent artists, distinctive work and new connections with collectors.</p>
  <div class="pa-jn-acts"><a class="pa-jn-btn" href="join.html" data-pa-track="home_join">Apply to join</a><a class="pa-jn-link" href="gallery/" data-pa-track="home_join_gallery">Explore the gallery</a></div>
  <p class="pa-jn-status"><span class="pa-open-badge">{BADGE}</span></p></div>
</div></section>
{HE}"""


F25_OLD_BAND = re.compile(r'<section class="pa-sec pa-invite-sec" aria-labelledby="f25InviteH">.*?</div></section>', re.S)
FB, FE = "<!-- pa-artist-apply-pointer:begin -->", "<!-- pa-artist-apply-pointer:end -->"
POINTER = '<p class="pa-muted">PlotArt now welcomes applications to the Artists’ Gallery. <a href="join.html">Join PlotArt</a>.</p>'


# While applications are not open, NOTHING of the recruitment is published (founder decision 13 Nov 2026): the homepage
# keeps the closed Founding 25 band exactly as it is on main, the Founding 25 page has no pointer, and join.html,
# curatorial-policy.html and pa-apply.js do not exist.
CLOSED_F25_BAND = '<section class="pa-sec pa-invite-sec" aria-labelledby="f25InviteH"><div class="pa-wrap">\n  <div class="pa-f25 pa-f25--invite">\n    <span class="num" aria-hidden="true">25</span>\n    <span><span class="pa-invite-k"><span class="pa-eyebrow">The PlotArt Founding 25</span><span class="pa-open-badge pa-open-badge--off">Applications have closed.</span></span><h2 id="f25InviteH">25 artists. 25 galleries.<br>100% free for the first year.</h2><p>Your art. Your sales. Your earnings. No membership, subscription or listing fees, ever, and keep 100% of your artwork sales — no PlotArt commission on enquiries from your founding year, even if the sale completes later.</p></span>\n    <span class="pa-invite-cta"><a class="pa-btn pa-btn--ghost" href="founding-25.html" data-pa-track="home_f25">About the Founding 25 <span aria-hidden="true">→</span></a></span>\n  </div>\n</div></section>'


CSS_LINK = '<link rel="stylesheet" href="assets/plotart.css">'
JOIN_CSS_LINK = '\n<link rel="stylesheet" href="assets/plotart-join.css">'


def homepage(s):
    s = s.replace(CSS_LINK + JOIN_CSS_LINK, CSS_LINK)
    if OPEN:
        if s.count(CSS_LINK) != 1:
            raise SystemExit("homepage: plotart.css link not found exactly once")
        s = s.replace(CSS_LINK, CSS_LINK + JOIN_CSS_LINK)
    if HB in s:
        a, b = s.index(HB), s.index(HE) + len(HE)
        return s[:a] + (home_band() if OPEN else CLOSED_F25_BAND) + s[b:]
    m = F25_OLD_BAND.search(s)
    if not m:
        raise SystemExit("homepage: neither the artist band markers nor the closed Founding 25 band found")
    return s[:m.start()] + (home_band() if OPEN else CLOSED_F25_BAND) + s[m.end():]


def f25_page(s):
    anchor = 'how long it&#x27;s kept are explained in the <a href="../privacy.html#founding-25-applications">privacy notice</a>.</p>'
    if FB in s:
        a, b = s.index(FB), s.index(FE) + len(FE)
        if not OPEN:
            return s[:a - len("\n  ")] + s[b:] if s[a - len("\n  "):a] == "\n  " else s[:a] + s[b:]
        return s[:a] + FB + POINTER + FE + s[b:]
    if not OPEN:
        return s
    if s.count(anchor) != 1:
        raise SystemExit("founding-25.html: pointer anchor not found exactly once")
    return s.replace(anchor, anchor + "\n  " + FB + POINTER + FE)


GB, GE = "<!-- pa-artist-apply-gallery:begin -->", "<!-- pa-artist-apply-gallery:end -->"
G_CSS_LINK = '<link rel="stylesheet" href="../assets/plotart.css">'
G_JOIN_CSS_LINK = '\n<link rel="stylesheet" href="../assets/plotart-join.css">'
G_ANCHOR = '<section class="pa-vg2-close">'


def gallery_band():
    # The Artists' Gallery invitation (founder decision 14 Nov 2026): the homepage invitation in a compact form,
    # between the collection and the closing links. Built only in the "open" state; no figures, terms or selling points.
    return f"""{GB}
<section class="pa-jn-band pa-jn-band--compact" aria-labelledby="joinGalleryH"><div class="pa-wrap pa-jn-band-grid">
  <div class="pa-jn-band-head"><p class="pa-jn-k">For artists</p>
  <h2 id="joinGalleryH">An invitation to join PlotArt.</h2></div>
  <div class="pa-jn-band-body"><p class="pa-jn-lede">A curated space for contemporary Irish art. Independent artists, distinctive work and new connections with collectors.</p>
  <div class="pa-jn-acts"><a class="pa-jn-btn" href="../join.html" data-pa-track="gallery_join">Apply to join</a></div>
  <p class="pa-jn-status"><span class="pa-open-badge">{BADGE}</span></p></div>
</div></section>
{GE}
"""


def gallery_page(s):
    # The collection region (pa-vg-collection markers) is never touched.
    s = s.replace(G_CSS_LINK + G_JOIN_CSS_LINK, G_CSS_LINK)
    if GB in s:
        a, b = s.index(GB), s.index(GE) + len(GE)
        if s[b:b + 2] != "\n\n":
            raise SystemExit("gallery/index.html: unexpected text after the invitation markers")
        s = s[:a] + s[b + 2:]
    if not OPEN:
        return s
    if s.count(G_CSS_LINK) != 1 or s.count(G_ANCHOR) != 1:
        raise SystemExit("gallery/index.html: stylesheet link or closing section not found exactly once")
    return s.replace(G_CSS_LINK, G_CSS_LINK + G_JOIN_CSS_LINK).replace(G_ANCHOR, gallery_band() + "\n" + G_ANCHOR)


def outputs():
    home = open(os.path.join(PA, "index.html"), encoding="utf-8").read()
    f25 = open(os.path.join(PA, "founding-25.html"), encoding="utf-8").read()
    gal = open(os.path.join(PA, "gallery", "index.html"), encoding="utf-8").read()
    out = {"index.html": homepage(home), "founding-25.html": f25_page(f25), "gallery/index.html": gallery_page(gal)}
    if OPEN:
        out.update({"join.html": join_page(), "curatorial-policy.html": policy_page()})
    return out


PAGES_ONLY_OPEN = ("join.html", "curatorial-policy.html")
SRC_JS = os.path.join(ROOT, "atlas-tools", "release", "plotart-apply.js")
SRC_CSS = os.path.join(ROOT, "atlas-tools", "release", "plotart-join.css")
if __name__ == "__main__":
    out = outputs()
    js_path = os.path.join(PA, "assets", "pa-apply.js")
    if "--check" in sys.argv:
        bad = [n for n, t in out.items() if not os.path.exists(os.path.join(PA, n)) or open(os.path.join(PA, n), encoding="utf-8").read() != t]
        bad += [n for n in PAGES_ONLY_OPEN if not OPEN and os.path.exists(os.path.join(PA, n))]
        css_path = os.path.join(PA, "assets", "plotart-join.css")
        js_ok = all(os.path.exists(pp) == OPEN and (not OPEN or open(pp, encoding="utf-8").read() == open(src, encoding="utf-8").read())
                    for pp, src in ((js_path, SRC_JS), (css_path, SRC_CSS)))
        if bad or not js_ok:
            sys.exit("JOIN PLOTART · STALE (%s): rebuild with atlas-tools/build-plotart-join.py" % ", ".join(bad + ([] if js_ok else ["assets/pa-apply.js or assets/plotart-join.css"])))
        print("JOIN PLOTART · OK — pages match the %s build" % STATE)
        sys.exit(0)
    for n, t in out.items():
        open(os.path.join(PA, n), "w", encoding="utf-8").write(t)
    for n in PAGES_ONLY_OPEN:
        if not OPEN and os.path.exists(os.path.join(PA, n)):
            os.remove(os.path.join(PA, n))
    for pp, src in ((js_path, SRC_JS), (os.path.join(PA, "assets", "plotart-join.css"), SRC_CSS)):
        if OPEN:
            open(pp, "w", encoding="utf-8").write(open(src, encoding="utf-8").read())
        elif os.path.exists(pp):
            os.remove(pp)
    print("JOIN PLOTART · built for %s" % STATE)
