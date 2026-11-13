#!/usr/bin/env python3
"""PlotArt · Join PlotArt (Gallery Artist Programme Phase 3, development 13 Nov 2026). NOT PUBLISHED.

Builds the public artist-recruitment pages from the founder-approved copy, in the state the launch switches say:

    plotart/join.html                 the application page and form
    plotart/curatorial-policy.html    the curatorial policy
    plotart/assets/pa-apply.js        the form script
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
No new imagery: the pages are type on the existing dark identity.
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

JOIN_STYLE = STYLE.replace("</style>", """.pa-join-ex{width:100%;max-width:460px;border-collapse:collapse;margin:26px 0 8px;font-size:16px}
.pa-join-ex th,.pa-join-ex td{text-align:left;padding:12px 0;border-bottom:1px solid rgba(242,235,224,.14)}
.pa-join-ex td{text-align:right;font-variant-numeric:tabular-nums;color:var(--ivory)}
.pa-join-ex th{font-weight:500;color:var(--lime)}
.pa-join-ex tr.is-you td,.pa-join-ex tr.is-you th{color:var(--ivory);font-weight:600}
.pa-join-crit{list-style:none;margin:0;padding:0;display:grid;gap:0;border-top:1px solid rgba(242,235,224,.14)}
.pa-join-crit li{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:8px 32px;padding:20px 0;border-bottom:1px solid rgba(242,235,224,.14)}
.pa-join-crit h3{font-size:clamp(22px,2vw,28px);margin:0}
.pa-join-crit p{margin:0;color:var(--lime);line-height:1.6;max-width:62ch}
@media (max-width:720px){.pa-join-crit li{grid-template-columns:1fr}}
.pa-join-status{max-width:760px}
</style>""") + "\n"

POLICY_STYLE = """<style>
.pa-pol{max-width:760px}
.pa-pol h2{font-size:clamp(30px,3vw,44px);margin:0 0 18px}
.pa-pol p{color:var(--lime);line-height:1.7;margin:0 0 16px}
.pa-pol ul{margin:0 0 16px;padding-left:1.2em;color:var(--lime);line-height:1.7}
.pa-pol li{margin:0 0 8px}
.pa-pol strong{color:var(--ivory);font-weight:600}
.pa-join-crit{list-style:none;margin:0;padding:0;display:grid;gap:0;border-top:1px solid rgba(242,235,224,.14)}
.pa-join-crit li{display:grid;grid-template-columns:minmax(0,15rem) minmax(0,1fr);gap:8px 32px;padding:20px 0;border-bottom:1px solid rgba(242,235,224,.14)}
.pa-join-crit h3{font-size:clamp(22px,2vw,28px);margin:0}
.pa-join-crit p{margin:0;color:var(--lime);line-height:1.6;max-width:62ch}
@media (max-width:720px){.pa-join-crit li{grid-template-columns:1fr}}
</style>
"""

CRITERIA = [
    ("Artistic quality", "A considered approach to technique, materials, composition, expression or ideas. We look at the work itself, not at how it is described."),
    ("A distinctive voice", "Originality and individuality: a recognisable direction that is your own, whatever your subject or medium."),
    ("A developed body of work", "A coherent portfolio that shows your approach, your interests and how your work is developing, rather than a single piece."),
    ("Commitment to your practice", "Sustained engagement with your work. Qualifications, exhibitions and gallery representation are welcome but never required."),
    ("Contribution to the gallery", "How your work would complement, strengthen or broaden the PlotArt collection."),
]
CRIT_HTML = "\n".join(f"    <li><h3>{E(h)}</h3><p>{E(p)}</p></li>" for h, p in CRITERIA)

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
    if OPEN:
        return f"""<section class="pa-sec pa-sec--deep" id="apply"><div class="pa-wrap pa-cols-2" style="align-items:start">
  <div class="pa-apply-intro"><p class="pa-eyebrow">Apply</p><h2 class="pa-apply-title">Apply to join PlotArt.</h2>
  <p class="pa-lede" style="margin-top:0">Tell us about you and your work. It takes about ten minutes, and applying is free. All you need is a few images of your work, or a link to where we can see it.</p>
  <p class="pa-select-note" style="margin-top:18px">{LINE}</p>
  <p class="pa-muted" style="margin-top:14px">Every application is read individually. Applying doesn’t guarantee a place, and we’ll let you know the outcome either way.</p>
  <p class="pa-note" style="margin-top:18px">Already on PlotNua's <a href="../artist-register.html">Artist Register</a>? That stays a private expression of interest. Applying here is a separate step.</p></div>
{form()}
</div></section>"""
    return f"""<section class="pa-sec pa-sec--deep" id="apply"><div class="pa-wrap">
  <div class="pa-join-status"><p class="pa-eyebrow">Apply</p><h2 class="pa-apply-title">{LINE}</h2>
  <p class="pa-lede" style="margin-top:16px">In the meantime, you're welcome to read our <a href="curatorial-policy.html">curatorial policy</a>, or to email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> with any questions.</p>
  <p class="pa-muted">How we handle artist applications is explained in the <a href="../privacy.html#plotart-artist-applications">privacy notice</a>.</p></div>
</div></section>"""


def join_page():
    acts = ('<a class="pa-btn pa-btn--solid" href="#apply" data-pa-track="join_apply_click">Apply now</a><a class="pa-btn pa-btn--ghost" href="#terms">Read the terms</a>' if OPEN
            else '<a class="pa-btn pa-btn--solid" href="#terms">Read the terms</a><a class="pa-btn pa-btn--ghost" href="curatorial-policy.html">Our curatorial policy</a>')
    return head("join.html", "Join PlotArt: Apply to a Curated Gallery of Irish Art | PlotArt",
                "Apply to join PlotArt, an independently curated online gallery of contemporary Irish art. 15% commission only on sales to collectors PlotArt introduces. No upfront fees. No exclusivity.",
                JOIN_STYLE) + HEADER + f"""<main id="main">

<section class="pa-fhero"><div class="pa-wrap">
  <div>
    <p class="pa-eyebrow">For artists</p>
    <h1>Join PlotArt.</h1>
    <p class="pa-lede" style="margin-top:26px">PlotArt is an independently curated gallery of contemporary Irish art. If you’re based or working on the island of Ireland and your work has a voice of its own, we’d love to see it.</p>
    <p class="pa-select-note" style="margin-top:22px">{LINE} Every application is read individually, and applying doesn’t guarantee a place.</p>
    <div class="pa-actions" style="margin-top:18px">{acts}</div>
  </div>
  <p class="big" aria-hidden="true">15%<small>only on sales to collectors PlotArt introduces · no upfront fees · no exclusivity</small></p>
</div></section>

<section class="pa-sec"><div class="pa-wrap">
  <div class="pa-sec-head"><div><p class="pa-eyebrow">What you receive</p><h2>A gallery of<br>your own.</h2></div>
  <p>Our first artists joined through the Founding 25, our introductory programme, which has now closed. Founding Artists keep their own terms. Artists who join now become Gallery Artists, on the terms below, and each receives their own gallery.</p></div>
  <ul class="pa-terms" style="list-style:none;margin:0">
    <li><strong>Your own artist gallery.</strong> Your biography and a page for each work, with large images and true dimensions. Start with one artwork and add more whenever you wish.</li>
    <li><strong>Collectors who come to you.</strong> Enquiries go straight to you, or to your gallery if you’re represented. You agree every sale yourself.</li>
    <li><strong>Your own Studio.</strong> Add works, set your prices and mark work sold in PlotArt Studio, at your own pace.</li>
    <li><strong>Your independence.</strong> No exclusivity: keep showing and selling your work wherever you like. You keep your copyright.</li>
  </ul>
</div></section>

<section class="pa-sec pa-sec--deep" id="terms"><div class="pa-wrap pa-cols-2" style="align-items:start">
  <div><p class="pa-eyebrow">The terms, plainly</p><h2 style="font-size:clamp(36px,3.8vw,56px)">15% commission, only when PlotArt introduces the collector.</h2>
  <table class="pa-join-ex"><caption class="pa-eyebrow" style="text-align:left;caption-side:top;margin:0 0 6px">An example: a collector PlotArt introduced buys a work</caption>
    <tbody><tr><th scope="row">Artwork sold for</th><td>€1,000</td></tr><tr class="is-you"><th scope="row">You receive</th><td>€850</td></tr><tr><th scope="row">PlotArt invoices you</th><td>€150</td></tr></tbody></table>
  <p class="pa-note">The collector pays you directly. Shipping, insurance and handling are never part of the commission. A sale to a collector who found you on their own carries no commission at all.</p></div>
  <ul class="pa-terms" style="list-style:none;margin:0">
    <li><strong>No upfront fees.</strong> Nothing to apply, nothing to join, and no membership, subscription or listing fees.</li>
    <li><strong>Your own sales stay yours.</strong> Collectors who find you independently, through your website, your studio, an exhibition or another gallery, carry no PlotArt commission.</li>
    <li><strong>15% on sales PlotArt introduces.</strong> Commission applies when a collector PlotArt has introduced to you buys your original work. That includes collectors who tell you they found you through PlotArt.</li>
    <li><strong>A clear two-year window.</strong> An introduction counts for 24 months. After that, a sale carries no commission unless it completes a conversation about a particular work that began within those 24 months.</li>
    <li><strong>You’re paid directly.</strong> Collectors pay you, and PlotArt invoices its commission after the sale completes.</li>
    <li><strong>New commissions are yours.</strong> A newly commissioned work is agreed directly between you and the collector, and isn’t covered by the commission.</li>
    <li><strong>No exclusivity.</strong> Show and sell your work wherever you like, and keep working with other galleries.</li>
    <li>The full terms are in the PlotArt Gallery Artist Agreement, which you read and accept in PlotArt Studio before your gallery is first published.</li>
  </ul>
</div></section>

<section class="pa-sec"><div class="pa-wrap">
  <div class="pa-sec-head"><div><p class="pa-eyebrow">What we look for</p><h2>Curated,<br>not catalogued.</h2></div>
  <p>We have no house style, and we welcome every medium and subject. Each application is considered against five criteria, with no scoring formula. <a href="curatorial-policy.html">Read our curatorial policy</a>.</p></div>
  <ul class="pa-join-crit">
{CRIT_HTML}
  </ul>
</div></section>

<section class="pa-sec" id="how"><div class="pa-wrap">
  <div class="pa-sec-head"><div><p class="pa-eyebrow">How it works</p><h2>From application<br>to gallery.</h2></div><p>Applying, accepting the agreement and publishing your gallery are three separate steps, and nothing is published without your approval.</p></div>
  <ol class="pa-steps">
    <li><div><h3>You apply</h3><p>Tell us about yourself and share three to five images of your work, or a link to your portfolio.</p></div></li>
    <li><div><h3>We review</h3><p>We confirm we’ve received your application, then read it individually against our criteria. We may ask to see a little more. Applying doesn’t guarantee a place.</p></div></li>
    <li><div><h3>We tell you the outcome</h3><p>By email, courteously and clearly, whatever the decision.</p></div></li>
    <li><div><h3>Your gallery opens</h3><p>If you’re selected, you receive an invitation to PlotArt Studio. Before you first submit your gallery, you read and accept the Gallery Artist Agreement there. Your gallery goes live once you’ve submitted it and we’ve reviewed it.</p></div></li>
  </ol>
</div></section>

{apply_section()}
</main>
""" + FOOTER.replace('<script src="assets/plotart.js" defer></script>', ('<script src="assets/pa-apply.js" defer></script>\n' if OPEN else "") + '<script src="assets/plotart.js" defer></script>', 1)


def policy_page():
    return head("curatorial-policy.html", "Our Curatorial Policy | PlotArt",
                "How PlotArt, an independently curated online gallery of contemporary Irish art, considers artist applications: five criteria, no house style, every application read individually.",
                POLICY_STYLE) + HEADER + f"""<main id="main">

<section class="pa-fhero"><div class="pa-wrap" style="grid-template-columns:1fr">
  <div class="pa-pol">
    <p class="pa-eyebrow">Curatorial policy</p>
    <h1>An independently curated gallery of contemporary Irish art.</h1>
    <p class="pa-lede" style="margin-top:26px">PlotArt brings together emerging, mid-career and established artists based or working on the island of Ireland, whose work shows quality, originality and a considered approach to their practice.</p>
  </div>
</div></section>

<section class="pa-sec"><div class="pa-wrap"><div class="pa-pol">
  <h2>No house style.</h2>
  <p>We welcome work in every medium, from painting, drawing and printmaking to photography, sculpture, ceramics, textiles, mixed media, digital and interdisciplinary practice, and on any subject. We don’t favour a particular style, subject, medium or way of working. Instead, we look at the strength of each artist’s work and what it would bring to the gallery as a whole.</p>
  <p>PlotArt is a growing gallery. Our aim is a collection that is diverse, coherent and rewarding to explore, introducing collectors to exceptional Irish artists and creating real opportunities for those artists to be seen and to sell their work. Our first artists joined through the Founding 25, our introductory programme; the gallery continues to grow through individual applications.</p>
</div></div></section>

<section class="pa-sec pa-sec--deep"><div class="pa-wrap">
  <div class="pa-sec-head"><div><p class="pa-eyebrow">Selection criteria</p><h2>Five things<br>we look for.</h2></div>
  <p>No single criterion decides an application, and there is no scoring formula. Selection is a matter of careful curatorial judgement across all five.</p></div>
  <ul class="pa-join-crit">
{CRIT_HTML}
  </ul>
</div></section>

<section class="pa-sec"><div class="pa-wrap"><div class="pa-pol">
  <h2>How applications are considered.</h2>
  <ul>
    <li><strong>Every application is read individually,</strong> with its images, statement and any links you provide.</li>
    <li><strong>We may ask for more,</strong> such as further images, a more focused selection of work or a little more about your practice, before we decide.</li>
    <li><strong>Submitting an application does not guarantee selection.</strong> We are building a considered collection, and each application is weighed on its own merits.</li>
    <li><strong>Decisions reflect the gallery’s curatorial direction.</strong> A decision not to include an artist is not a judgement on the value of your practice or on you as an artist.</li>
    <li><strong>We’ll always tell you the outcome,</strong> courteously and clearly.</li>
    <li><strong>Applying costs nothing,</strong> and selection is never influenced by payment.</li>
  </ul>
  <h2 style="margin-top:34px">Artificial intelligence.</h2>
  <p>We welcome original digital work and AI-assisted practice. Artists tell us about any meaningful use of AI in making a work. Images generated entirely from prompts are not automatically eligible as original artist-created work.</p>
  <h2 style="margin-top:34px">How the gallery is arranged.</h2>
  <p>We set the order of galleries in the Artists’ Gallery by hand, for curatorial reasons. It is never influenced by any fee, payment or commission arrangement.</p>
  <h2 style="margin-top:34px">Our commitment to artists.</h2>
  <p>PlotArt respects your independence, your creative ownership and your existing professional relationships. You keep your copyright. There is no exclusivity: you remain free to show and sell your work elsewhere, and to work with other galleries. We aim to present your work properly, introduce it to new audiences, and treat every artist, and every application, with the same care and respect.</p>
  <div class="pa-actions" style="margin-top:28px"><a class="pa-btn pa-btn--solid" href="join.html" data-pa-track="policy_join_click">Join PlotArt</a></div>
  <p class="pa-note" style="margin-top:22px">Questions about applying? Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>.</p>
</div></div></section>
</main>
""" + FOOTER


HB, HE = "<!-- pa-artist-apply:begin -->", "<!-- pa-artist-apply:end -->"


def home_band():
    cta = ('<a class="pa-btn pa-btn--solid" href="join.html#apply" data-pa-track="home_join_apply">Apply to PlotArt</a>' if OPEN
           else '<a class="pa-btn pa-btn--solid" href="join.html" data-pa-track="home_join">Join PlotArt</a>')
    return f"""{HB}
<section class="pa-sec pa-invite-sec" aria-labelledby="joinInviteH"><div class="pa-wrap">
  <div class="pa-f25 pa-f25--invite">
    <span class="num" aria-hidden="true">15%</span>
    <span><span class="pa-invite-k"><span class="pa-eyebrow">For artists</span><span class="pa-open-badge{'' if OPEN else ' pa-open-badge--off'}">{BADGE}</span></span><h2 id="joinInviteH">Your art deserves to be discovered.</h2><p>Apply to join PlotArt’s curated Artists’ Gallery. 15% commission only on sales to collectors PlotArt introduces; your own sales stay yours. No upfront fees. No exclusivity.</p></span>
    <span class="pa-invite-cta">{cta}<a class="pa-btn pa-btn--ghost" href="curatorial-policy.html" data-pa-track="home_curatorial_policy">Our curatorial policy</a></span>
  </div>
</div></section>
{HE}"""


F25_OLD_BAND = re.compile(r'<section class="pa-sec pa-invite-sec" aria-labelledby="f25InviteH">.*?</div></section>', re.S)
FB, FE = "<!-- pa-artist-apply-pointer:begin -->", "<!-- pa-artist-apply-pointer:end -->"
POINTER = '<p class="pa-muted">PlotArt now welcomes applications to the Artists’ Gallery. <a href="join.html">Join PlotArt</a>.</p>'


# While applications are not open, NOTHING of the recruitment is published (founder decision 13 Nov 2026): the homepage
# keeps the closed Founding 25 band exactly as it is on main, the Founding 25 page has no pointer, and join.html,
# curatorial-policy.html and pa-apply.js do not exist.
CLOSED_F25_BAND = '<section class="pa-sec pa-invite-sec" aria-labelledby="f25InviteH"><div class="pa-wrap">\n  <div class="pa-f25 pa-f25--invite">\n    <span class="num" aria-hidden="true">25</span>\n    <span><span class="pa-invite-k"><span class="pa-eyebrow">The PlotArt Founding 25</span><span class="pa-open-badge pa-open-badge--off">Applications have closed.</span></span><h2 id="f25InviteH">25 artists. 25 galleries.<br>100% free for the first year.</h2><p>Your art. Your sales. Your earnings. No membership, subscription or listing fees, ever, and keep 100% of your artwork sales — no PlotArt commission on enquiries from your founding year, even if the sale completes later.</p></span>\n    <span class="pa-invite-cta"><a class="pa-btn pa-btn--ghost" href="founding-25.html" data-pa-track="home_f25">About the Founding 25 <span aria-hidden="true">→</span></a></span>\n  </div>\n</div></section>'


def homepage(s):
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


def outputs():
    home = open(os.path.join(PA, "index.html"), encoding="utf-8").read()
    f25 = open(os.path.join(PA, "founding-25.html"), encoding="utf-8").read()
    out = {"index.html": homepage(home), "founding-25.html": f25_page(f25)}
    if OPEN:
        out.update({"join.html": join_page(), "curatorial-policy.html": policy_page()})
    return out


PAGES_ONLY_OPEN = ("join.html", "curatorial-policy.html")
SRC_JS = os.path.join(ROOT, "atlas-tools", "release", "plotart-apply.js")
if __name__ == "__main__":
    out = outputs()
    js_path = os.path.join(PA, "assets", "pa-apply.js")
    if "--check" in sys.argv:
        bad = [n for n, t in out.items() if not os.path.exists(os.path.join(PA, n)) or open(os.path.join(PA, n), encoding="utf-8").read() != t]
        bad += [n for n in PAGES_ONLY_OPEN if not OPEN and os.path.exists(os.path.join(PA, n))]
        js_ok = os.path.exists(js_path) == OPEN and (not OPEN or open(js_path, encoding="utf-8").read() == open(SRC_JS, encoding="utf-8").read())
        if bad or not js_ok:
            sys.exit("JOIN PLOTART · STALE (%s): rebuild with atlas-tools/build-plotart-join.py" % ", ".join(bad + ([] if js_ok else ["assets/pa-apply.js"])))
        print("JOIN PLOTART · OK — pages match the %s build" % STATE)
        sys.exit(0)
    for n, t in out.items():
        open(os.path.join(PA, n), "w", encoding="utf-8").write(t)
    for n in PAGES_ONLY_OPEN:
        if not OPEN and os.path.exists(os.path.join(PA, n)):
            os.remove(os.path.join(PA, n))
    if OPEN:
        open(js_path, "w", encoding="utf-8").write(open(SRC_JS, encoding="utf-8").read())
    elif os.path.exists(js_path):
        os.remove(js_path)
    print("JOIN PLOTART · built for %s" % STATE)
