#!/usr/bin/env python3
"""
PLOTNUA · THE BORROWED GARDEN NOTICEBOARD · governed builder (MVP, founder decision 4 Nov 2026). NOT RELEASED.

Writes borrowed-garden-board.html (noindex, follow) from the approved-listings snapshot
(atlas-tools/garden-board/approved-listings.json: public fields only, written by the content pipeline from PlotArt
Studio's /api/pipeline/garden). The page is built on The Borrowed Garden Discovery's own shell (head, global header,
related Discoveries, footer) so it reads as part of that Discovery; the Discovery file itself is never written.

Every listing is checked again here, as the intake Worker and the Studio check it: closed lists for kind, county, type
of space and availability; a general area with no digits; 20-400 characters of text with no e-mail address, link,
telephone number, Eircode, house number or markup; dates only; only the allowed public fields. All text is escaped.
No monetisation field is accepted: the snapshot cannot carry a tier, a featured date or an account, and listings are
shown newest first, by date only.

Two people, two sides: "I have space" and "I want space" are visually distinct and filterable, with county and area.
Contact between participants is NOT switched on: listings carry a reference and the page says contact opens later.

  python3 atlas-tools/build-garden-board.py                build into the repository
  python3 atlas-tools/build-garden-board.py --check        verify, write nothing
  python3 atlas-tools/build-garden-board.py --data F --root DIR [--endpoint URL] [--preview]
                                                           build into another tree (local previews and tests only)
"""
import html, json, pathlib, re, sys
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
ROOT = pathlib.Path(arg("--root") or HERE.parent)
DATA = pathlib.Path(arg("--data") or HERE / "garden-board" / "approved-listings.json")
CONFIG = json.loads((HERE / "garden-board" / "config.json").read_text(encoding="utf-8"))
ENDPOINT = arg("--endpoint") or CONFIG.get("endpoint")
CHECK, PREVIEW = "--check" in sys.argv, "--preview" in sys.argv
SHELL, PAGE = HERE.parent / "discovery-the-borrowed-garden.html", ROOT / "borrowed-garden-board.html"

KINDS = {"have": "I have space", "want": "I want space"}
SPACE = {"raised_beds": "Raised beds", "vegetable_patch": "A vegetable patch", "lawn": "Part of a lawn",
         "greenhouse": "A greenhouse or polytunnel", "orchard": "Fruit trees or an orchard corner", "flexible": "Open to suggestions"}
AVAIL = {"now": "Available now", "this_season": "This growing season", "next_season": "Next growing season", "flexible": "Flexible"}
COUNTIES = ["Antrim", "Armagh", "Carlow", "Cavan", "Clare", "Cork", "Derry", "Donegal", "Down", "Dublin", "Fermanagh", "Galway", "Kerry",
            "Kildare", "Kilkenny", "Laois", "Leitrim", "Limerick", "Longford", "Louth", "Mayo", "Meath", "Monaghan", "Offaly", "Roscommon", "Sligo",
            "Tipperary", "Tyrone", "Waterford", "Westmeath", "Wexford", "Wicklow"]
RULES = {"link": re.compile(r"(https?://|www\.|\b[a-z0-9-]{2,}\.(?:com|ie|net|org|co|uk|io|eu|info|biz|app|dev|ly|me)\b)", re.I),
         "email": re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+"), "phone": re.compile(r"\d(?:[\s().\-]?\d){6,}"), "markup": re.compile(r"[<>]"),
         "eircode": re.compile(r"\b[ACDEFHKNPRTVWXY][0-9]{2}[0-9W]?\s?[0-9ACDEFHKNPRTVWXY]{4}\b", re.I),
         "house": re.compile(r"\b\d+[a-z]?\s+[a-z]+(?:\s+[a-z]+)?\s+(?:road|rd|street|st|avenue|ave|park|drive|lane|close|crescent|grove|court|way|terrace|place|view|heights|gardens|square)\b", re.I)}
FIELDS = {"ref", "kind", "county", "area", "space_type", "availability", "text", "photo", "posted", "expires"}
REF = re.compile(r"^PN-G-\d{6}-[0-9A-F]{4}$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHOTO = re.compile(r"^assets/garden-board/photos/[a-z0-9-]+\.(?:webp|jpg)$")
ENDPOINT_RE = re.compile(r"^https://[a-z0-9.-]+\.workers\.dev/v1/garden-listings$|^https://[a-z0-9.-]+\.plotnua\.ie/v1/garden-listings$|^http://(127\.0\.0\.1|localhost):\d{2,5}/v1/garden-listings$")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
E = lambda s: html.escape(str(s), quote=True)
CONSENT = ("I am over 18. I agree that PlotNua may show this listing on The Borrowed Garden noticeboard, without my name or "
           "contact details, and keep my e-mail address privately so PlotNua can contact me about it.")


def die(m):
    sys.exit("REFUSED: " + m)


def bad_text(t, lo, hi):
    if not (lo <= len(t) <= hi): return "length"
    for k, rx in RULES.items():
        if rx.search(t): return k
    return None


def validate(listings):
    seen = set()
    for i, l in enumerate(listings):
        if not isinstance(l, dict) or set(l) - FIELDS or not {"ref", "kind", "county", "area", "space_type", "availability", "text", "posted", "expires"} <= set(l):
            die("listing %d: only the public fields are allowed, and all of them are required" % i)
        if not REF.match(l["ref"]) or l["ref"] in seen: die("listing %d: bad or repeated reference" % i)
        seen.add(l["ref"])
        if l["kind"] not in KINDS or l["county"] not in COUNTIES or l["space_type"] not in SPACE or l["availability"] not in AVAIL:
            die("listing %s: a value is not on its closed list" % l["ref"])
        if re.search(r"\d", l["area"]) or bad_text(l["area"], 2, 40): die("listing %s: the area must be general (no numbers or contact details)" % l["ref"])
        why = bad_text(l["text"], 20, 400)
        if why: die("listing %s: the text fails the %s rule" % (l["ref"], why))
        if not DAY.match(l["posted"]) or not DAY.match(l["expires"]): die("listing %s: dates must be YYYY-MM-DD" % l["ref"])
        if l.get("photo"):
            if not PHOTO.match(l["photo"]) or not (ROOT / l["photo"]).exists(): die("listing %s: the photograph must be an approved file in assets/garden-board/photos/" % l["ref"])
    order = [l["posted"] for l in listings]
    if order != sorted(order, reverse=True): die("listings must be newest first, by date posted only")


def nice(d):
    y, m, dd = (int(x) for x in d.split("-"))
    return "%d %s %d" % (dd, MONTHS[m - 1], y)


def card(l):
    kind = l["kind"]
    photo = ('<img class="gb-photo" src="%s" alt="" loading="lazy" decoding="async">' % E(l["photo"])) if l.get("photo") else ""
    return ('<li class="gb-card is-%s" data-kind="%s" data-county="%s" data-area="%s">%s'
            '<p class="gb-kind"><span class="gb-dot" aria-hidden="true"></span>%s</p>'
            '<h3 class="gb-where">%s<span>Co. %s</span></h3>'
            '<p class="gb-text">%s</p>'
            '<ul class="gb-facts" role="list"><li>%s</li><li>%s</li></ul>'
            '<p class="gb-meta"><span>%s</span><span>Posted %s</span><span>Listed until %s</span></p></li>'
            % (kind, kind, E(l["county"]), E(l["area"]), photo, E(KINDS[kind]), E(l["area"]), E(l["county"]), E(l["text"]),
               E(SPACE[l["space_type"]]), E(AVAIL[l["availability"]]), E(l["ref"]), nice(l["posted"]), nice(l["expires"])))


def form():
    if not ENDPOINT:
        return ('<section class="gb-post" id="post" aria-labelledby="gbPostH"><h2 id="gbPostH" class="gb-h2">Post a listing</h2>'
                '<p class="gb-closed">The noticeboard isn&rsquo;t taking listings yet. The Borrowed Garden is still being explored.</p></section>')
    if not ENDPOINT_RE.match(ENDPOINT): die("the intake endpoint must be the noticeboard Worker's /v1/garden-listings address")
    opt = lambda d: "".join('<option value="%s">%s</option>' % (E(k), E(v)) for k, v in d.items())
    counties = "".join("<option>%s</option>" % c for c in COUNTIES)
    return ('<section class="gb-post" id="post" aria-labelledby="gbPostH"><h2 id="gbPostH" class="gb-h2">Post a listing</h2>'
            '<p class="gb-sub">Free. PlotNua reads every listing before it appears, and never shows your name or contact details.</p>'
            '<form id="gbForm" method="post" action="%s">'
            '<fieldset class="gb-side"><legend class="gb-l">Which side are you on?</legend>'
            '<label class="gb-pick is-have"><input type="radio" name="kind" value="have" required><span><b>I have space</b>A garden, or part of one, someone could grow in.</span></label>'
            '<label class="gb-pick is-want"><input type="radio" name="kind" value="want"><span><b>I want space</b>Somewhere nearby to grow.</span></label></fieldset>'
            '<div class="gb-two"><div><label class="gb-l" for="gbCounty">County</label><select id="gbCounty" name="county" required><option value="">Choose&hellip;</option>%s</select></div>'
            '<div><label class="gb-l" for="gbArea">General area</label><input id="gbArea" name="area" maxlength="40" required placeholder="A town or neighbourhood, e.g. Raheny" autocomplete="off"></div></div>'
            '<div class="gb-two"><div><label class="gb-l" for="gbType">Type of space</label><select id="gbType" name="space_type" required><option value="">Choose&hellip;</option>%s</select></div>'
            '<div><label class="gb-l" for="gbWhen">When</label><select id="gbWhen" name="availability" required><option value="">Choose&hellip;</option>%s</select></div></div>'
            '<label class="gb-l" for="gbText">A short description</label>'
            '<textarea id="gbText" name="description" minlength="20" maxlength="400" required placeholder="What the space is like, or what you are looking for." aria-describedby="gbCount gbNo"></textarea>'
            '<div class="gb-count" id="gbCount" aria-live="polite">0 / 400</div>'
            '<p class="gb-no" id="gbNo">Please leave out names, addresses, Eircodes, phone numbers and e-mail addresses.</p>'
            '<label class="gb-l" for="gbEmail">Your e-mail address (private)</label>'
            '<input id="gbEmail" name="email" type="email" maxlength="120" required autocomplete="email" aria-describedby="gbEmailNote">'
            '<p class="gb-no" id="gbEmailNote">Never shown on the noticeboard. PlotNua uses it only about this listing.</p>'
            '<label class="gb-tick"><input type="checkbox" name="consent" value="1" required> %s</label>'
            '<div class="gb-hp" aria-hidden="true"><label>Leave this empty <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>'
            '<input type="hidden" name="t" value="">'
            '<button class="gb-btn" type="submit">Send for review</button>'
            '<p class="gb-result" id="gbResult" role="status" aria-live="polite" hidden></p>'
            '</form></section>' % (E(ENDPOINT), counties, opt(SPACE), opt(AVAIL), E(CONSENT)))


def body(listings):
    counties = sorted({l["county"] for l in listings})
    have = sum(1 for l in listings if l["kind"] == "have")
    want = len(listings) - have
    cards = "".join(card(l) for l in listings) or ""
    empty = '<p class="gb-empty" id="gbEmpty"%s>No listings match. Try another county, or post the first one.</p>' % ("" if not listings else " hidden")
    preview = '<p class="gb-preview">Private preview &middot; not public</p>' if PREVIEW else ""
    return ('<main class="gb" id="pn-main">\n'
            '<div class="article lg-ch-wrap gb-top">%s\n'
            '  <div class="lg-chapter"><span class="lg-plot" aria-hidden="true"><span>&nbsp;</span></span><p class="lg-kicker">The Borrowed Garden &middot; Noticeboard</p></div>\n'
            '  <h1 class="lg-title">Garden space, shared locally.</h1>\n'
            '  <p class="lg-stand">Two sides of one idea: people with ground they barely use, and people nearby looking for somewhere to grow. '
            'Listings are free and show a general area only. <a href="discovery-the-borrowed-garden.html">Read The Borrowed Garden first</a>.</p>\n'
            '  <ul class="gb-sides" role="list"><li class="is-have"><b>%d</b> I have space</li><li class="is-want"><b>%d</b> I want space</li></ul>\n'
            '</div>\n'
            '<div class="article gb-body">\n'
            '  <div class="gb-filters" role="group" aria-label="Filter the noticeboard">\n'
            '    <div class="gb-seg" role="radiogroup" aria-label="Show"><button type="button" data-k="all" aria-pressed="true">All</button>'
            '<button type="button" data-k="have" aria-pressed="false">I have space</button><button type="button" data-k="want" aria-pressed="false">I want space</button></div>\n'
            '    <div><label class="gb-l" for="gbFCounty">County</label><select id="gbFCounty"><option value="">All counties</option>%s</select></div>\n'
            '    <div><label class="gb-l" for="gbFArea">Area</label><select id="gbFArea" disabled><option value="">All areas</option></select></div>\n'
            '  </div>\n'
            '  <p class="gb-showing" id="gbShowing" aria-live="polite"></p>\n'
            '  <ul class="gb-list" id="gbList" role="list">%s</ul>\n  %s\n'
            '  <div class="gb-limits"><p><strong>How this noticeboard works.</strong> Every listing is read by PlotNua before it appears, and comes down after 90 days. '
            'Listings never show names, addresses or contact details. PlotNua does not match anyone, and contact between people through the noticeboard isn&rsquo;t open yet: '
            'each listing carries a reference for when it is. Nothing here is checked or inspected by PlotNua, and anything agreed is between the two people. '
            'Before agreeing anything, read <a href="discovery-the-borrowed-garden.html#bg-agree">what to settle first</a>.</p></div>\n'
            '  %s\n'
            '</div>\n</main>\n' % (preview, have, want, "".join("<option>%s</option>" % E(c) for c in counties), cards, empty, form()))


PAGE_CSS = """<style>
/* ==== The Borrowed Garden noticeboard (MVP, 4 Nov 2026) · page-local, on the Discovery's identity and pn-bg-editorial ==== */
body.pn-id.pn-pd .gb{ padding-bottom:clamp(56px,7vw,112px); }
body.pn-id.pn-pd .gb-top{ padding-top:clamp(40px,6vw,88px); }
body.pn-id.pn-pd .gb-top .lg-plot > span{ font-size:22px; }
body.pn-id.pn-pd .gb-top .lg-stand a{ color:#E8A88A; }
body.pn-id.pn-pd .gb-preview{ display:inline-block; margin:0 0 18px; padding:6px 10px; border:1px solid #CF8566; color:#F0C2A9; font:700 11px/1 var(--p4-sans); letter-spacing:.16em; text-transform:uppercase; }
.gb-sides{ list-style:none; display:flex; gap:12px; flex-wrap:wrap; margin:22px 0 0; padding:0; }
body.pn-id.pn-pd .gb-sides li{ font:600 14px/1.2 var(--p4-sans); color:var(--p4-ivory); padding:10px 14px; border-radius:999px; border:1px solid var(--bg-line,#37422D); }
body.pn-id.pn-pd .gb-sides b{ font-family:var(--p4-serif); font-weight:400; font-size:22px; margin-right:6px; }
body.pn-id.pn-pd .gb-sides .is-have{ border-color:#A3BE7E; } body.pn-id.pn-pd .gb-sides .is-want{ border-color:#D2AE6E; }
body.pn-id.pn-pd .gb-body{ padding-top:clamp(28px,3vw,44px); }
.gb-filters{ display:grid; grid-template-columns:auto 1fr 1fr; gap:14px 18px; align-items:end; padding:18px; border:1px solid var(--bg-line,#37422D); border-radius:4px; background:var(--bg-field,#1F241B); }
.gb-seg{ display:flex; border:1px solid var(--bg-line,#37422D); border-radius:999px; overflow:hidden; align-self:end; }
body.pn-id.pn-pd .gb-seg button{ min-height:44px; padding:0 16px; background:none; border:0; color:var(--p4-stone); font:600 14px/1 var(--p4-sans); cursor:pointer; }
body.pn-id.pn-pd .gb-seg button[aria-pressed="true"]{ background:var(--p4-ivory); color:var(--p4-anth); }
body.pn-id.pn-pd .gb-seg button:focus-visible{ outline:2px solid #CF8566; outline-offset:-2px; }
body.pn-id.pn-pd .gb-l{ display:block; margin:0 0 6px; font:700 12px/1.2 var(--p4-sans); letter-spacing:.16em; text-transform:uppercase; color:var(--bg-amber-2,#CFE0B4); }
body.pn-id.pn-pd .gb select, body.pn-id.pn-pd .gb input[type="text"], body.pn-id.pn-pd .gb input:not([type]), body.pn-id.pn-pd .gb input[type="email"], body.pn-id.pn-pd .gb textarea{
  width:100%; box-sizing:border-box; min-height:46px; padding:10px 12px; background:#151815; color:var(--p4-ivory); border:1px solid #4A4B4F; border-radius:3px; font:400 16px/1.4 var(--p4-sans); }
body.pn-id.pn-pd .gb select:disabled{ opacity:.5; }
body.pn-id.pn-pd .gb-showing{ margin:18px 0 0; font:500 14px/1.4 var(--p4-sans); color:var(--p4-stone); }
.gb-list{ list-style:none; padding:0; margin:14px 0 0; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; }
body.pn-id.pn-pd .gb-card{ position:relative; display:flex; flex-direction:column; padding:20px 20px 18px; border:1px solid var(--bg-line,#37422D); border-top:3px solid #A3BE7E; border-radius:4px; background:var(--bg-field,#1F241B); }
body.pn-id.pn-pd .gb-card.is-want{ border-top-color:#D2AE6E; background:#24211C; border-color:#3F382C; }
body.pn-id.pn-pd .gb-card[hidden]{ display:none; }
body.pn-id.pn-pd .gb-photo{ width:calc(100% + 40px); margin:-20px -20px 16px; height:180px; object-fit:cover; border-radius:3px 3px 0 0; }
body.pn-id.pn-pd .gb-kind{ margin:0; font:700 12px/1.2 var(--p4-sans); letter-spacing:.18em; text-transform:uppercase; color:#CFE0B4; display:flex; align-items:center; gap:8px; }
body.pn-id.pn-pd .is-want .gb-kind{ color:#E8CF9E; }
.gb-dot{ width:9px; height:9px; border-radius:0 8px 0 8px; background:#A3BE7E; } .is-want .gb-dot{ border-radius:50%; background:#D2AE6E; }
body.pn-id.pn-pd .gb-where{ margin:12px 0 0; font-family:var(--p4-serif); font-weight:400; font-size:clamp(24px,2vw,30px); line-height:1.1; color:var(--p4-ivory); }
body.pn-id.pn-pd .gb-where span{ display:block; margin-top:4px; font:500 14px/1.3 var(--p4-sans); color:var(--p4-stone); }
body.pn-id.pn-pd .gb-text{ margin:12px 0 0; font:400 16px/1.55 var(--p4-sans); color:#E4DED3; flex:1; }
.gb-facts{ list-style:none; padding:0; margin:14px 0 0; display:flex; flex-wrap:wrap; gap:6px; }
body.pn-id.pn-pd .gb-facts li{ font:600 12.5px/1 var(--p4-sans); color:var(--p4-ivory); padding:7px 9px; border:1px solid #4A4B4F; border-radius:999px; }
body.pn-id.pn-pd .gb-meta{ margin:14px 0 0; padding-top:12px; border-top:1px solid rgba(242,235,224,.1); display:flex; flex-wrap:wrap; gap:4px 14px; font:500 12.5px/1.4 var(--p4-sans); color:var(--p4-stone); }
body.pn-id.pn-pd .gb-meta span:first-child{ font-family:ui-monospace,monospace; color:var(--p4-ivory); }
body.pn-id.pn-pd .gb-empty{ margin:18px 0 0; padding:22px; border:1px dashed #4A4B4F; border-radius:4px; color:var(--p4-stone); }
body.pn-id.pn-pd .gb-limits{ margin:clamp(28px,3vw,40px) 0 0; padding:18px 20px; border-left:3px solid #A3BE7E; background:rgba(163,190,126,.06); }
body.pn-id.pn-pd .gb-limits p{ margin:0; font:400 15.5px/1.6 var(--p4-sans); color:var(--p4-stone); max-width:78ch; }
body.pn-id.pn-pd .gb-limits a{ color:#E8A88A; }
body.pn-id.pn-pd .gb-post{ margin:clamp(40px,5vw,72px) 0 0; padding:clamp(22px,3vw,36px); border:1px solid #4A4B4F; border-top:2px solid #CF8566; border-radius:4px; max-width:760px; }
body.pn-id.pn-pd .gb-h2{ margin:0; font-family:var(--p4-serif); font-weight:400; font-size:clamp(30px,3vw,42px); line-height:1.1; color:var(--p4-ivory); }
body.pn-id.pn-pd .gb-sub, body.pn-id.pn-pd .gb-closed{ margin:10px 0 22px; color:var(--p4-stone); font:400 16px/1.55 var(--p4-sans); }
.gb-side{ border:0; padding:0; margin:0 0 18px; display:grid; grid-template-columns:1fr 1fr; gap:12px; }
body.pn-id.pn-pd .gb-pick{ display:flex; gap:10px; padding:14px; border:1px solid #4A4B4F; border-radius:4px; cursor:pointer; color:var(--p4-stone); font:400 14.5px/1.45 var(--p4-sans); }
body.pn-id.pn-pd .gb-pick b{ display:block; color:var(--p4-ivory); font-size:16px; margin-bottom:2px; }
body.pn-id.pn-pd .gb-pick.is-have:has(input:checked){ border-color:#A3BE7E; background:rgba(163,190,126,.08); }
body.pn-id.pn-pd .gb-pick.is-want:has(input:checked){ border-color:#D2AE6E; background:rgba(210,174,110,.08); }
.gb-two{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:0 0 16px; }
body.pn-id.pn-pd .gb textarea{ min-height:120px; resize:vertical; }
body.pn-id.pn-pd .gb-count{ text-align:right; font:500 12.5px/1 var(--p4-sans); color:var(--p4-stone); margin:6px 0 0; }
body.pn-id.pn-pd .gb-no{ margin:6px 0 16px; font:400 13.5px/1.5 var(--p4-sans); color:var(--p4-stone); }
body.pn-id.pn-pd .gb-tick{ display:flex; gap:10px; align-items:flex-start; margin:4px 0 18px; font:400 14.5px/1.5 var(--p4-sans); color:var(--p4-stone); }
body.pn-id.pn-pd .gb-tick input{ margin-top:4px; }
.gb-hp{ position:absolute; left:-10000px; width:1px; height:1px; overflow:hidden; }
body.pn-id.pn-pd .gb-btn{ min-height:52px; padding:0 26px; border:0; border-radius:999px; background:var(--p4-terra,#CF8566); color:var(--p4-anth,#1B1C1E); font:700 16px/1 var(--p4-sans); cursor:pointer; }
body.pn-id.pn-pd .gb-btn:disabled{ opacity:.6; cursor:wait; }
body.pn-id.pn-pd .gb-result{ margin:16px 0 0; padding:12px 14px; border-radius:3px; background:rgba(163,190,126,.12); color:var(--p4-ivory); }
body.pn-id.pn-pd .gb-result.is-bad{ background:rgba(207,133,102,.14); }
@media (max-width:1023px){ .gb-list{ grid-template-columns:1fr 1fr; } .gb-filters{ grid-template-columns:1fr 1fr; } .gb-seg{ grid-column:1 / -1; justify-self:start; } }
@media (max-width:719px){
  .gb-list, .gb-two, .gb-side{ grid-template-columns:1fr; }
  .gb-filters{ grid-template-columns:1fr; padding:14px; gap:12px; }
  .gb-seg{ justify-self:stretch; } body.pn-id.pn-pd .gb-seg button{ flex:1; }
  body.pn-id.pn-pd .gb-seg button{ padding:0 12px; font-size:13.5px; }
  body.pn-id.pn-pd .gb-card{ padding:18px 16px 16px; }
}
</style>
"""

PAGE_JS = """<script>
/* The Borrowed Garden noticeboard: filter by side, county and area (no network), and the listing form. */
(function () {
  var list = document.getElementById('gbList'); if (!list) return;
  var cards = [].slice.call(list.querySelectorAll('.gb-card'));
  var seg = [].slice.call(document.querySelectorAll('.gb-seg button'));
  var fc = document.getElementById('gbFCounty'), fa = document.getElementById('gbFArea');
  var showing = document.getElementById('gbShowing'), empty = document.getElementById('gbEmpty');
  var kind = 'all';
  function areas() {
    var c = fc.value, seen = {}, opts = ['<option value="">All areas</option>'];
    cards.forEach(function (x) { if (c && x.dataset.county === c && !seen[x.dataset.area]) { seen[x.dataset.area] = 1; } });
    Object.keys(seen).sort().forEach(function (a) { var o = document.createElement('option'); o.textContent = a; opts.push(o.outerHTML); });
    fa.innerHTML = opts.join(''); fa.disabled = !c;
  }
  function apply() {
    var c = fc.value, a = fa.value, n = 0;
    cards.forEach(function (x) {
      var ok = (kind === 'all' || x.dataset.kind === kind) && (!c || x.dataset.county === c) && (!a || x.dataset.area === a);
      x.hidden = !ok; if (ok) n++;
    });
    empty.hidden = n !== 0;
    showing.textContent = cards.length ? 'Showing ' + n + ' of ' + cards.length + ' listing' + (cards.length === 1 ? '' : 's') + '.' : '';
  }
  seg.forEach(function (b) { b.addEventListener('click', function () { kind = b.dataset.k; seg.forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); }); apply(); }); });
  fc.addEventListener('change', function () { areas(); apply(); });
  fa.addEventListener('change', apply);
  apply();
  var f = document.getElementById('gbForm'); if (!f) return;
  var t = f.querySelector('[name="t"]'); t.value = String(Date.now());
  var ta = document.getElementById('gbText'), cnt = document.getElementById('gbCount');
  ta.addEventListener('input', function () { cnt.textContent = ta.value.length + ' / 400'; });
  var res = document.getElementById('gbResult'), btn = f.querySelector('.gb-btn');
  f.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var body = {}; new FormData(f).forEach(function (v, k) { body[k] = v; });
    btn.disabled = true; res.hidden = true;
    fetch(f.action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (j) {
        res.hidden = false; res.classList.toggle('is-bad', !j.ok);
        res.textContent = j.ok ? 'Thank you. PlotNua will read your listing before it appears. Your reference is ' + j.reference + '. To change or remove it, e-mail hello@plotnua.ie with this reference.'
                               : (j.error || 'Your listing could not be sent. Please try again later.');
        if (j.ok) { f.reset(); t.value = String(Date.now()); cnt.textContent = '0 / 400'; }
      })
      .catch(function () { res.hidden = false; res.classList.add('is-bad'); res.textContent = 'Your listing could not be sent. Please try again later.'; })
      .then(function () { btn.disabled = false; });
  });
})();
</script>
"""


def page(shell, listings):
    t = shell
    reps = [(r"<title>[^<]*</title>", "<title>The Borrowed Garden noticeboard | PlotNua</title>"),
            (r'<meta name="description" content="[^"]*">', '<meta name="description" content="A free noticeboard for garden space in Ireland: people with ground to share, and people looking for somewhere to grow.">'),
            (r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, follow">'),
            (r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="https://plotnua.ie/borrowed-garden-board.html">')]
    for rx, new in reps:
        n = len(re.findall(rx, t))
        if n == 0 and "robots" in rx:
            t = t.replace("</head>", '<meta name="robots" content="noindex, follow">\n</head>', 1); continue
        if n != 1: die("Discovery shell: %s found %d times" % (rx, n))
        t = re.sub(rx, lambda m: new, t, count=1)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", t, flags=re.S)
    t = re.sub(r'<meta property="og:[^"]*" content="[^"]*">\n?|<meta name="twitter:[^"]*" content="[^"]*">\n?', "", t)
    # Replace everything from the hero to the closing panel with the noticeboard; the header row above and the related
    # Discoveries and footer below stay exactly as the Discovery has them.
    i = t.index('<header class="d-hero')
    j = t.index('<section class="related reveal">')
    t = t[:i] + body(listings) + "\n" + t[j:]
    t = t.replace("</head>", PAGE_CSS + "</head>", 1)
    k = t.rindex("</body>"); t = t[:k] + PAGE_JS + t[k:]
    t = t.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n<!-- PLOTNUA BORROWED GARDEN NOTICEBOARD · generated by atlas-tools/build-garden-board.py from the approved listings — do not hand-edit -->\n", 1)
    return t


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    listings = d.get("listings")
    if not isinstance(listings, list): die("the snapshot has no listings list")
    validate(listings)
    new_page = page(SHELL.read_text(encoding="utf-8"), listings)
    if CHECK:
        ok = PAGE.exists() and PAGE.read_text(encoding="utf-8") == new_page
        print("GARDEN NOTICEBOARD · " + ("OK (%d approved listings; page noindex)" % len(listings) if ok else "NOT BUILT or out of date"))
        sys.exit(0 if ok else 1)
    PAGE.write_text(new_page, encoding="utf-8")
    print("built: %d approved listings; %s written" % (len(listings), PAGE))


if __name__ == "__main__":
    main()
