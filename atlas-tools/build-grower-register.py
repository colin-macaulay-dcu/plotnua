#!/usr/bin/env python3
"""PlotNua · THE BORROWED GARDEN · GROWER CHECK + GROWER REGISTER · bounded builder.

Founder direction, 16 October 2026 (controlled launch): one Borrowed Garden
Discovery, two routes, one PlotNua experience. The gardener route REUSES the
Garden Owner journey exactly:

    DISCOVERY  ->  GROWER CHECK  ->  REGISTER  ->  CONFIRMATION

Writes:
  disc025-borrowed-garden-grower-check.html   always. The host Property Check's
      own shell is the template: its <head> and full stylesheet (brand tokens,
      pc-* question components, progress dots, bg-res-* result, bg-int-*
      register panel), its header, and its Journey Exit footer. Only <main>
      and the journey script are this builder's.
  discovery-the-borrowed-garden.html          ONLY at launch (GROWER_PUBLIC =
      True): the closing "Property Check" panel offers both routes with the
      two-check component already live on A Home for Art.

Usage:
  python3 atlas-tools/build-grower-register.py                      build
  python3 atlas-tools/build-grower-register.py --check              fail if stale
  python3 atlas-tools/build-grower-register.py --preview-discovery F
        write the LAUNCH version of the Discovery to F (for review only;
        the repo copy is untouched while closed)

GUARDS (each refuses the build):
  G1  consent sentence == frozen G1B §3 == the Worker's
  G2  vocabularies == the Worker's V lists
  G3  payload keys == exactly the agreed set, inside GROWER_ALLOWED_KEYS
  G4  CLOSED: no page links to the grower check; the register panel is removed
      from the DOM unless GROWER_PUBLIC or ?interest=preview
  G5  no surname / address / Eircode / phone / file / tel field
  G6  honesty lines present in visible copy; no promise of a garden or match
  G8  host Property Check byte-identical; privacy.html and the Discovery change
      only at launch and only by their bounded blocks; host Worker handler identical
  G9  launch refused until OPEN_APPROVAL is complete, privacy.html carries the
      Grower Register notice, and wrangler.toml names that notice version
  G10 shell markers found exactly once
  G11 "Community Roots" (an independent organisation) never names this register
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "disc025-borrowed-garden-grower-check.html"
HOST = ROOT / "disc025-borrowed-garden-check.html"
DISCOVERY = ROOT / "discovery-the-borrowed-garden.html"
WORKER = ROOT / "worker" / "garden-register" / "src" / "index.js"
WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"
PRIVACY = ROOT / "privacy.html"
SITEMAP = ROOT / "sitemap.xml"
SEARCH = ROOT / "search-index-v1.json"

GROWER_PUBLIC = False
ENDPOINT = "https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/grower"
GROWER_PRIVACY_MARKER = "PLOTNUA-GROWER-PRIVACY-V6"
GROWER_PRIVACY_VERSION = "2026-10-PHASE2-V6"
OPEN_APPROVAL = {
    "privacy_v6_wording_approved": None,      # founder, date
    "launch_approved": None,                  # founder, date
}
BASE_REF = "84453f1"

# G1B §3, FROZEN 7 Oct 2026.
FROZEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby."

LABELS = {
    "district": [("raheny", "Raheny"), ("killester", "Killester"), ("donnycarney", "Donnycarney"),
                 ("artane", "Artane"), ("elsewhere_in_dublin", "Elsewhere in Dublin"),
                 ("elsewhere_in_ireland", "Elsewhere in Ireland")],
    "travel_radius": [("walking", "Within walking distance"), ("up_to_2km", "Up to 2 km"),
                      ("up_to_5km", "Up to 5 km"), ("up_to_10km", "Up to 10 km")],
    "space_band": [("very_small", "Very small — a bed or two"), ("small", "Small — a corner"),
                   ("medium", "Medium — a good patch"), ("large", "Large"), ("not_sure", "Not sure yet")],
    "timing": [("this_season", "This season"), ("within_3_months", "Within three months"),
               ("next_season", "Next season"), ("flexible", "I’m flexible")],
}
PAYLOAD_KEYS = ["first_name", "email", "district", "travel_radius", "space_wanted", "timing",
                "growing_note", "over_18", "consent_text", "source"]
SOURCE = "grower_register"

HONESTY = [
    "No garden is available through PlotNua today.",
    "We may never find a garden near you.",
    "This is a register, not a match.",
    "Nothing is shared with anybody until you say yes to one specific introduction.",
]
PROMISES = [r"\bguarantee(d|s)? (a|an|you)", r"\bwe will (match|introduce) you\b", r"\byour garden is waiting\b",
            r"\bgardens? (are|is) available (now|today)\b", r"\bget matched\b", r"\binstant(ly)? match"]

# ---------------------------------------------------- Discovery (launch only) --
DISC_OLD_CTA = ('    <p class="pb-cta-line"><a class="btn-primary" href="disc025-borrowed-garden-check.html?start=1">'
                'Start the check <span aria-hidden="true">&rarr;</span></a></p>\n')
DISC_NEW_CTA = '''    <!-- PLOTNUA-GROWER-ROUTES · two routes, one Discovery (founder direction 16 Oct 2026).
         The same two-check component as A Home for Art. No form here; nothing is matched. -->
    <div class="hfa-checks">
      <div class="hfa-check"><h3>I have garden space to share</h3><p>Four short questions about the part you could share, how somebody would reach it, and how you&rsquo;d use it yourself. At the end, you can choose to join the Garden Owner Register.</p>
        <a class="btn-primary" href="disc025-borrowed-garden-check.html?start=1">Check your garden <span aria-hidden="true">&rarr;</span></a></div>
      <div class="hfa-check"><h3>I&rsquo;m looking for somewhere to grow</h3><p>Four short questions about where you are, how far you&rsquo;d go, how much space and when. At the end, you can choose to join the Grower Register.</p>
        <a class="btn-primary" href="disc025-borrowed-garden-grower-check.html?start=1">Check your interest <span aria-hidden="true">&rarr;</span></a></div>
    </div>
'''
DISC_OLD_NOTE = ('    <p class="pb-note">The check reads your answers about the property. Nobody is contacted, '
                 'and nothing on this page sends your details anywhere.</p>\n')
DISC_NEW_NOTE = ('    <p class="pb-note">Neither check sends your details anywhere. Both registers are expressions of '
                 'interest only: free, private and non-binding. Nothing is matched or arranged.</p>\n')
DISC_CSS_ANCHOR = "</style>"
DISC_CSS = '''  /* PLOTNUA-GROWER-ROUTES-CSS · the two-check component, as on A Home for Art. */
  .hfa-checks{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; width:100%; max-width:860px;
    margin:8px auto 26px; text-align:left; }
  .hfa-check{ background:var(--paper); padding:26px 26px 28px; border:1px solid rgba(31,59,46,.12); border-radius:2px; }
  .hfa-check h3{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:21px; line-height:1.3; margin:0 0 8px; color:var(--ink); }
  .hfa-check p{ font-size:14.5px; line-height:1.6; color:var(--soft); margin:0; }
  .hfa-check .btn-primary{ text-decoration:none; }
  .hfa-check .btn-primary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  @media(max-width:820px){ .hfa-checks{ grid-template-columns:1fr; } }
'''
DISC_OLD_SUB = ('    <p class="pb-subhead">Four short questions about the part you could share, how\n'
                '      somebody would reach it, and how you would use it yourself. No address, and\n'
                '      nothing to measure.</p>\n')
DISC_NEW_SUB = ('    <p class="pb-subhead">Two short checks, one for each side. No address, and\n'
                '      nothing to measure.</p>\n')
DISC_OLD_HEAD = '    <p class="kicker">Property Check</p>\n    <h2 class="pb-headline">Which part of your garden could work?</h2>\n'
DISC_NEW_HEAD = '    <p class="kicker">Take part</p>\n    <h2 class="pb-headline">Two ways to take part</h2>\n'


def die(msg: str) -> None:
    sys.stderr.write("REFUSED: " + msg + "\n")
    sys.exit(2)


def once(text: str, needle: str, what: str) -> int:
    n = text.count(needle)
    if n != 1:
        die(f"G10 marker {what!r} found {n} times")
    return text.index(needle)


def git_show(ref_path: str) -> bytes:
    return subprocess.run(["git", "show", ref_path], cwd=ROOT, capture_output=True, check=True).stdout


def worker_facts() -> dict:
    src = WORKER.read_text()
    m = re.search(r"grower:\s*\"([^\"]+)\"", src)
    if not m or m.group(1) != FROZEN_CONSENT:
        die("G1 the Worker's grower sentence is not the frozen G1B §3 sentence")
    vocab = {}
    for key in ("district", "space_band", "timing", "travel_radius", "grower_source"):
        mm = re.search(key + r":\s*\[([^\]]*)\]", src)
        if not mm:
            die(f"G2 cannot read the Worker vocabulary {key}")
        vocab[key] = re.findall(r"'([a-z0-9_]+)'", mm.group(1))
    ak = re.search(r"GROWER_ALLOWED_KEYS = Object\.freeze\(\[([^\]]*)\]", src)
    if not ak:
        die("G3 cannot read GROWER_ALLOWED_KEYS")
    return {"consent": m.group(1), "vocab": vocab, "allowed": re.findall(r"'([a-z0-9_]+)'", ak.group(1))}


def discovery_launch(text: str) -> str:
    for old, what in [(DISC_OLD_CTA, "Discovery CTA"), (DISC_OLD_NOTE, "Discovery note"),
                      (DISC_OLD_SUB, "Discovery subhead"), (DISC_OLD_HEAD, "Discovery headline")]:
        once(text, old, what)
    text = (text.replace(DISC_OLD_CTA, DISC_NEW_CTA).replace(DISC_OLD_NOTE, DISC_NEW_NOTE)
                .replace(DISC_OLD_SUB, DISC_NEW_SUB).replace(DISC_OLD_HEAD, DISC_NEW_HEAD))
    i = text.index(DISC_CSS_ANCHOR)
    return text[:i] + DISC_CSS + text[i:]


def guards_before(w: dict) -> None:
    for key, pairs in LABELS.items():
        if [v for v, _ in pairs] != w["vocab"][key]:
            die(f"G2 {key} differs from the Worker")
    if any(k not in w["allowed"] for k in PAYLOAD_KEYS) or SOURCE not in w["vocab"]["grower_source"]:
        die("G3 payload keys or source outside the Worker's allow-list")
    # G8 host Property Check: always byte-identical.
    if hashlib.sha256(git_show(f"{BASE_REF}:{HOST.name}")).digest() != hashlib.sha256(HOST.read_bytes()).digest():
        die("G8 host file changed: " + HOST.name)
    base_w = git_show(f"{BASE_REF}:worker/garden-register/src/index.js").decode()
    wsrc = WORKER.read_text()
    try:
        a = base_w[base_w.index("async function handleGarden"):base_w.index("/* --------------------------------------------------------- grower handler")]
        b = wsrc[wsrc.index("async function handleGarden"):wsrc.index("/* ------------------------------------------------- grower route switches")]
    except ValueError:
        die("G8 cannot locate the host Worker handler")
    if a != b:
        die("G8 the host (garden) Worker handler changed")
    base_priv = git_show(f"{BASE_REF}:privacy.html").decode()
    priv = PRIVACY.read_text()
    if GROWER_PUBLIC:
        missing = [k for k, v in OPEN_APPROVAL.items() if not v]
        if missing:
            die(f"G9 cannot launch: OPEN_APPROVAL items missing {missing}")
        if GROWER_PRIVACY_MARKER not in priv:
            die("G9 cannot launch: privacy.html does not carry the Grower Register notice")
        if f'GROWER_PRIVACY_VERSION = "{GROWER_PRIVACY_VERSION}"' not in WRANGLER.read_text():
            die("G9 cannot launch: wrangler.toml does not name the grower privacy version")
    # In BOTH states privacy.html may differ from its base only by the governed
    # V6 blocks (exact, reversible: privacy_v6_layer.without_v6). While closed,
    # V6 may already be published (launch step 2); it must be V6 or nothing.
    sys.path.insert(0, str(ROOT / "atlas-tools"))
    from privacy_v6_layer import without_v6
    try:
        if without_v6(priv) != base_priv:
            die("G8 privacy.html differs from its base other than by the governed V6 blocks")
    except ValueError as e:
        die("G8 " + str(e))


def guards_after(html: str, disc: str) -> None:
    if f"var CONSENT_TEXT = {json.dumps(FROZEN_CONSENT)};" not in html or html.count(FROZEN_CONSENT) != 1:
        die("G1 consent sentence on the page differs, or appears more than once")
    if "if (!GROWER_PUBLIC && !preview())" not in html or "panel.parentNode.removeChild(panel)" not in html:
        die("G4 the register panel is not removed from the DOM when closed")
    if not GROWER_PUBLIC:
        for p in ROOT.glob("*.html"):
            if p.name != OUT.name and OUT.name in p.read_text(errors="ignore"):
                die(f"G4 {p.name} links to the closed grower check")
        if OUT.name in SITEMAP.read_text() or OUT.name in SEARCH.read_text():
            die("G4 the sitemap or Search lists the closed grower check")
    else:
        if disc.count('href="disc025-borrowed-garden-grower-check.html?start=1"') != 1 or \
           disc.count('href="disc025-borrowed-garden-check.html?start=1"') < 1:
            die("G8 the launch Discovery must offer both routes exactly once")
    low = html.lower()
    for bad in ['type="tel"', 'type="file"', 'name="surname"', 'name="last_name"', 'name="address"',
                'name="eircode"', 'name="phone"', 'autocomplete="family-name"', 'autocomplete="street-address"',
                'autocomplete="postal-code"', 'autocomplete="tel"']:
        if bad in low:
            die(f"G5 forbidden field on the page: {bad}")
    visible = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", visible)
    for a, b in [("&rsquo;", "’"), ("&mdash;", "—"), ("&nbsp;", " "), ("&amp;", "&"), ("&middot;", "·")]:
        text = text.replace(a, b)
    text = re.sub(r"\s+", " ", text)
    for line in HONESTY:
        if line not in text:
            die(f"G6 honesty line missing from visible copy: {line!r}")
    for pat in PROMISES:
        if re.search(pat, text, re.I):
            die(f"G6 a promise appears on the page: /{pat}/")
    pay = html[html.index("function payload()"):html.index("function localProblem()")]
    sent = re.findall(r"^\s{6}([a-z_0-9]+):", pay, re.M) + re.findall(r"body\.([a-z_0-9]+) =", pay)
    if sorted(set(sent)) != sorted(PAYLOAD_KEYS):
        die(f"G3 the page payload keys {sorted(set(sent))} are not exactly the agreed set")
    if re.search(r"community roots (gardener|grower) register", text, re.I) or "<title>Community Roots" in html:
        die("G11 Community Roots (an independent organisation) is used as this register's name")


def opts(key: str) -> str:
    return "".join(f'<option value="{v}">{l}</option>' for v, l in LABELS[key])


def main_html() -> str:
    def sel(fid, name, label, key):
        return (f'          <div class="bg-int-f">\n            <label for="{fid}">{label}</label>\n'
                f'            <select id="{fid}" name="{name}" required><option value="">Choose one</option>{opts(key)}</select>\n'
                f'          </div>\n')
    return f'''<main class="bg-wrap">

  <!-- THE BORROWED GARDEN · GROWER CHECK (founder direction 16 Oct 2026).
       Generated by atlas-tools/build-grower-register.py -- do not hand-edit.
       Same screens and components as the Property Check: intro, one question
       per screen with progress dots, result, then the register panel. -->
  <section class="bg-screen pc-intro is-on" id="bgIntro">
    <div class="pc-crest">
      <span class="pc-mark" aria-hidden="true">
        <img src="assets/brand/plotnua-mark-master.svg" alt="" width="56" height="56">
      </span>
      <span class="pc-crestlab">
        <b>The Borrowed Garden</b>
        <span>Grower Check</span>
      </span>
    </div>
    <h1 class="pc-introh">Looking for somewhere to grow?</h1>
    <p class="pc-introsub">Four quick questions about where you are, how far you&rsquo;d go,
      how much space would suit you and when. Nothing you answer is sent anywhere.</p>
    <div class="pc-actions">
    <button class="pc-cta" id="bgStart">Start the check
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></button>
    <a class="pc-ghost" href="discovery-the-borrowed-garden.html">Discover The Borrowed Garden
      <span class="pc-arrow" aria-hidden="true">&rarr;</span></a>
    </div>
  </section>

  <section class="bg-screen pc-qscreen" id="bgQ">
    <div class="pc-dots" id="bgDots" aria-hidden="true"></div>
    <p class="bg-prog sr-only" id="bgProg"></p>
    <p class="pc-qlab" id="bgQEyebrow"></p>
    <h2 class="pc-qh" id="bgQText"></h2>
    <p class="pc-qnote" id="bgQNote"></p>
    <div class="pc-opts is-stacked" id="bgOpts"></div>
    <p class="bg-nav"><button type="button" class="pc-back" id="bgBack">Back</button></p>
  </section>

  <section class="bg-screen" id="bgReveal">
    <div class="bg-revealband">
      <p class="bg-eyebrow">Your interest</p>
      <h2 class="bg-reveal-h" id="bgRevealH"></h2>
      <p class="bg-reveal-sub" id="bgRevealSub"></p>
    </div>

    <div class="bg-res" id="bgFinding"></div>

    <section class="bg-int" id="bgInterest" aria-labelledby="bgIntH">
      <p class="bg-int-prev" id="bgIntPrev" hidden>Private preview &middot; not public</p>
      <h2 class="bg-int-h" id="bgIntH">Would you like us to tell you if growing space comes up nearby?</h2>
      <div id="bgIntOffer">
        <p class="bg-int-p">PlotNua is exploring a small pilot that would introduce people who&rsquo;d
          like somewhere to grow to homeowners nearby with a spare corner. We&rsquo;re starting in
          Raheny, Killester, Donnycarney and Artane.</p>
        <ul class="bg-int-list">
          <li><strong>No garden is available through PlotNua today.</strong> Matching isn&rsquo;t live
            yet. Joining the register doesn&rsquo;t arrange anything.</li>
          <li><strong>There&rsquo;s no obligation.</strong> Registering commits you to nothing, and you can
            come off the register at any time.</li>
          <li><strong>We can&rsquo;t promise anything.</strong> We may never find a garden near you.</li>
          <li><strong>You stay in control.</strong> Nobody else sees your details. There is no public
            listing, no map and no profile page. Nothing is shared with anybody until you say yes to one specific introduction.</li>
        </ul>
        <p class="bg-int-p">If you live somewhere else, you&rsquo;re still welcome to tell us. Your
          interest goes on the register, but we aren&rsquo;t looking for anyone to introduce outside
          those four areas.</p>
        <p class="bg-int-cta">
          <button class="pc-cta" type="button" id="bgIntOpen">I&rsquo;m interested in growing space</button>
        </p>
        <p class="bg-int-caveat">This is a register, not a match.</p>
      </div>

      <form class="bg-int-form" id="bgIntForm" hidden novalidate>
        <p class="bg-int-privline">A first name, an email address and an area.
          No surname, no address, no Eircode, no phone number.</p>
        <div class="bg-int-grid">
          <div class="bg-int-f">
            <label for="bgIntName">First name</label>
            <input type="text" id="bgIntName" name="first_name" autocomplete="given-name" maxlength="40" required>
          </div>
          <div class="bg-int-f">
            <label for="bgIntEmail">Email address</label>
            <input type="email" id="bgIntEmail" name="email" autocomplete="email" maxlength="120" required>
          </div>
{sel("bgIntDistrict", "district", "Your area", "district")}{sel("bgIntTravel", "travel_radius", "How far you&rsquo;d go", "travel_radius")}{sel("bgIntSize", "space_wanted", "How much space", "space_band")}{sel("bgIntTiming", "timing", "Roughly when", "timing")}          <div class="bg-int-f is-wide">
            <label for="bgIntNote">Anything you&rsquo;d like us to know?</label>
            <textarea id="bgIntNote" name="growing_note" maxlength="600"></textarea>
            <span class="bg-int-hint" id="bgIntNoteHint">Optional. You could mention what you&rsquo;d like to grow,
              how much growing you&rsquo;ve done, whether you&rsquo;d rather work on your own or alongside the
              homeowner, and which days usually suit you. Please don&rsquo;t include your address, phone number
              or anything about your health.</span>
          </div>
        </div>

        <div class="bg-int-hp" aria-hidden="true">
          <label for="bgIntWebsite">Leave this field empty</label>
          <input type="text" id="bgIntWebsite" name="website" tabindex="-1" autocomplete="off" value="">
        </div>

        <div class="bg-int-tick">
          <input type="checkbox" id="bgIntConsent" required>
          <label for="bgIntConsent"><span id="bgIntConsentText"></span></label>
        </div>

        <details class="bg-int-notice" id="bgIntNotice">
          <summary>Before you join the register &mdash; what we keep, and what we never ask for</summary>
          <div class="bg-int-noticebody">
            <p><strong>What we keep.</strong> Your first name, your email address, the area you chose, how far
              you&rsquo;d travel, how much space you&rsquo;re looking for, roughly when, and anything you choose to
              tell us in the note. Your answers to the Grower Check are not sent to us; four of them fill in this
              form, where you can see and change them. We also keep the administrative records needed to manage
              your registration, your consent and its status.</p>
            <p><strong>What we never ask for.</strong> Your address, your Eircode, your phone number, your surname,
              your age, or anything about your health. We don&rsquo;t collect them, so we can&rsquo;t hold them or
              lose them.</p>
            <p><strong>Why we keep it.</strong> So that we can tell you if someone near you has growing space
              they&rsquo;d consider sharing.</p>
            <p><strong>Joining the register does not share your details with anyone.</strong> No other person sees
              your record. There is no public listing, no public map, no profile page, and no directory. Your
              record is private to PlotNua.</p>
            <p><strong>If we think there&rsquo;s a possible fit, we&rsquo;ll email you and ask.</strong> We&rsquo;ll
              describe the homeowner in general terms only. No name, no email, no contact details.</p>
            <p><strong>Nothing is shared until you say yes.</strong> Your email address only reaches another person
              after you have said yes to that specific introduction. If you don&rsquo;t reply, nothing happens.</p>
            <p><strong>What &ldquo;registered&rdquo; means.</strong> Only that you asked PlotNua to tell you about
              potential growing space. Nobody has checked or approved anything.</p>
            <p><strong>We never sell your information</strong>, and we never pass it to anyone for advertising.</p>
            <p><strong>Leaving.</strong> Email hello@plotnua.ie and we will delete your record. There&rsquo;s nothing
              to cancel and no notice period.</p>
            <p><strong>How long we keep it.</strong> A maximum of 24 months. You can ask us to delete it at any
              time, and we may delete it sooner if it is no longer needed.</p>
            <p><strong>One thing we keep after deletion.</strong> A separate note recording that you gave
              permission and that we honoured your request, holding a one-way digital fingerprint made from your
              email address, not the address itself.</p>
            <p>The full details are in our <a href="privacy.html">privacy notice</a>.</p>
          </div>
        </details>

        <p class="bg-int-msg" id="bgIntMsg" hidden role="status" aria-live="polite"></p>

        <div class="bg-int-actions">
          <button class="pc-cta" type="submit" id="bgIntSend">Join the register</button>
          <button class="bg-int-cancel" type="button" id="bgIntCancel">Not now</button>
        </div>
      </form>

      <div class="bg-int-done" id="bgIntDone" hidden role="status" aria-live="polite">
        <h3 class="bg-int-done-h" id="bgIntDoneH" tabindex="-1"></h3>
        <div id="bgIntDoneBody"></div>
      </div>

      <p class="bg-int-note">PlotNua does not verify anybody&rsquo;s identity and has not met anyone on this
        register. Nothing is arranged through this page.</p>
    </section>

    <p class="bg-foot">PlotNua does the homework. You make the decision. Your Grower Check stays
      private &mdash; answering the questions doesn&rsquo;t send us your details. If you&rsquo;d like to hear
      from us if somebody nearby has growing space, you can choose to join the register. That simply tells us
      you&rsquo;re interested. It isn&rsquo;t a match or an introduction.</p>
  </section>

</main>
'''


def script_js() -> str:
    labels = {k: dict(v) for k, v in LABELS.items()}
    qs = [
        {"var": "district", "eyebrow": "Where you are", "q": "Where do you live?",
         "note": "We&rsquo;re starting in Raheny, Killester, Donnycarney and Artane.", "key": "district"},
        {"var": "travel_radius", "eyebrow": "How far", "q": "How far would you go to a garden?",
         "note": "", "key": "travel_radius"},
        {"var": "space_band", "eyebrow": "How much space", "q": "How much space would suit you?",
         "note": "Most people start with a bed or two. Complete beginners are welcome.", "key": "space_band"},
        {"var": "timing", "eyebrow": "When", "q": "When would you like to start?", "note": "", "key": "timing"},
    ]
    for q in qs:
        q["opts"] = [{"v": v, "l": l} for v, l in LABELS[q.pop("key")]]
    return f"""<script>
/* PLOTNUA-GROWER-CHECK-JS · The Borrowed Garden Grower Check (founder direction
 * 16 Oct 2026). Generated by atlas-tools/build-grower-register.py.
 * The check is local: answers are never sent. Four of them pre-fill the
 * register form, where the person sees and can change them.
 * THE REGISTER PANEL SHIPS CLOSED: unless GROWER_PUBLIC or ?interest=preview,
 * it is REMOVED from the DOM. Even when shown, the Worker writes nothing for
 * a grower until its own switches name the published privacy notice. */
(function () {{
  'use strict';
  var GROWER_PUBLIC = {'true' if GROWER_PUBLIC else 'false'};
  var ENDPOINT = {json.dumps(ENDPOINT)};
  var CONSENT_TEXT = {json.dumps(FROZEN_CONSENT)};
  var QUESTIONS = {json.dumps(qs, ensure_ascii=False)};
  var LABEL = {json.dumps(labels, ensure_ascii=False)};
  var PILOT = ['raheny', 'killester', 'donnycarney', 'artane'];
  var answers = {{}}, trail = [];
  function $(id) {{ return document.getElementById(id); }}
  function preview() {{
    try {{ return /(?:^|[?&])interest=preview(?:&|$)/.test(location.search); }} catch (e) {{ return false; }}
  }}
  function show(id) {{
    try {{ if (window.PlotNuaFunnel) window.PlotNuaFunnel.start(); }} catch (e) {{}}
    ['bgIntro', 'bgQ', 'bgReveal'].forEach(function (s) {{ $(s).classList.toggle('is-on', s === id); }});
    window.scrollTo(0, 0);
  }}
  function pending() {{
    for (var i = 0; i < QUESTIONS.length; i++) if (!(QUESTIONS[i].var in answers)) return QUESTIONS[i];
    return null;
  }}
  function renderDots(q) {{
    var box = $('bgDots'); box.innerHTML = '';
    var idx = QUESTIONS.indexOf(q);
    QUESTIONS.forEach(function (_, i) {{
      var s = document.createElement('span');
      s.className = 'pc-dot' + (i < idx ? ' is-done' : (i === idx ? ' is-on' : ''));
      box.appendChild(s);
    }});
    $('bgProg').textContent = 'Question ' + (idx + 1) + ' of ' + QUESTIONS.length;
  }}
  function renderQuestion(q) {{
    renderDots(q);
    $('bgQEyebrow').textContent = q.eyebrow;
    $('bgQText').innerHTML = q.q;
    var note = $('bgQNote');
    if (q.note) {{ note.innerHTML = q.note; note.style.display = ''; }} else {{ note.textContent = ''; note.style.display = 'none'; }}
    var box = $('bgOpts'); box.innerHTML = '';
    box.className = 'pc-opts is-stacked';
    q.opts.forEach(function (o) {{
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'pc-opt'; b.textContent = o.l;
      b.addEventListener('click', function () {{ this.classList.add('is-chosen'); choose(q, o.v); }});
      box.appendChild(b);
    }});
    $('bgBack').style.display = trail.length ? '' : 'none';
    show('bgQ');
  }}
  function choose(q, v) {{ answers[q.var] = v; trail.push(q.var); advance(); }}
  function back() {{
    if (!trail.length) return;
    var last = trail.pop(); delete answers[last];
    var q = QUESTIONS.filter(function (x) {{ return x.var === last; }})[0];
    if (q) renderQuestion(q); else advance();
  }}
  function advance() {{ var n = pending(); if (n) renderQuestion(n); else reveal(); }}

  function li(text, tick) {{
    return '<li>' + (tick ? '<span class="bg-tick" aria-hidden="true">\\u2713</span>' : '') + text + '</li>';
  }}
  function reveal() {{
    try {{ if (window.PlotNuaFunnel) window.PlotNuaFunnel.complete(); }} catch (e) {{}}
    var inPilot = PILOT.indexOf(answers.district) !== -1;
    $('bgRevealH').textContent = inPilot ? 'You\\u2019re in one of our first areas'
                                         : 'We\\u2019re not in your area yet';
    $('bgRevealSub').textContent = inPilot
      ? 'We\\u2019re starting in ' + LABEL.district[answers.district] + ' and three neighbouring areas.'
      : 'We\\u2019re starting in Raheny, Killester, Donnycarney and Artane. You can still tell us you\\u2019re interested.';
    var h = '<div class="bg-res-item is-plain">';
    h += '<span class="bg-res-lab">How it would work</span><ul class="bg-res-ticks">';
    h += li('Homeowners with a spare corner tell PlotNua on the Garden Owner Register.', true);
    h += li('If one nearby could suit you, we\\u2019d email you separately and ask first.', true);
    h += li('Nothing is shared with anybody until you say yes to one specific introduction.', true);
    h += li('Complete beginners are welcome. A bed or two is a good place to start.', true);
    h += '</ul><span class="bg-res-lab">Worth knowing</span><ul class="bg-res-why">';
    h += li('No garden is available through PlotNua today, and matching isn\\u2019t live yet.');
    h += li('We may never find a garden near you.');
    if (answers.space_band === 'large') h += li('Larger spaces are rarer. Saying you\\u2019d also be happy with less can help.');
    h += li('Hoping to grow sooner? <a href="discovery-the-borrowed-garden.html#explore-providers">Community gardens, garden-sharing services and allotments</a> may have space now.');
    h += '</ul></div>';
    $('bgFinding').innerHTML = h;
    if ($('bgIntDistrict')) {{
      $('bgIntDistrict').value = answers.district; $('bgIntTravel').value = answers.travel_radius;
      $('bgIntSize').value = answers.space_band; $('bgIntTiming').value = answers.timing;
    }}
    show('bgReveal');
  }}

  /* ------------------------------------------------------------ register -- */
  var FIELD_NAME = {{ first_name: 'your first name', email: 'your email address', district: 'your area',
    travel_radius: 'how far you\\u2019d go', space_wanted: 'how much space', timing: 'roughly when',
    growing_note: 'the note', over_18: 'the confirmation that you are over 18 and agree',
    consent_text: 'the permission wording' }};
  var FIELD_EL = {{ first_name: 'bgIntName', email: 'bgIntEmail', district: 'bgIntDistrict',
    travel_radius: 'bgIntTravel', space_wanted: 'bgIntSize', timing: 'bgIntTiming', growing_note: 'bgIntNote',
    over_18: 'bgIntConsent' }};
  var STATE = 'offer', FLAGGED = null;
  function intShow(which) {{
    STATE = which;
    $('bgIntOffer').hidden = (which !== 'offer');
    $('bgIntForm').hidden = !(which === 'form' || which === 'sending');
    $('bgIntDone').hidden = !(which === 'received' || which === 'not_open' || which === 'unavailable');
    $('bgIntDone').setAttribute('data-state', which);
    var s = $('bgIntSend');
    s.disabled = (which === 'sending');
    s.textContent = which === 'sending' ? 'Sending\\u2026' : 'Join the register';
  }}
  function end(which, heading, paras) {{
    $('bgIntDoneH').textContent = heading;
    var b = $('bgIntDoneBody'); b.innerHTML = '';
    paras.forEach(function (t) {{ var p = document.createElement('p'); p.className = 'bg-int-p'; p.textContent = t; b.appendChild(p); }});
    intShow(which);
    try {{ $('bgIntDoneH').focus(); }} catch (e) {{}}
  }}
  function msg(t) {{ var m = $('bgIntMsg'); m.textContent = t || ''; m.hidden = !t; }}
  function flag(field) {{
    msg('We still need ' + (FIELD_NAME[field] || 'one more thing') + '.');
    var el = $(FIELD_EL[field]); FLAGGED = el;
    if (el) {{ el.setAttribute('aria-invalid', 'true'); try {{ el.focus(); }} catch (e) {{}} }}
  }}
  function received(district) {{
    var out = ['We have your first name, your email and what you\\u2019re looking for. Nobody else can see it.',
      'This is a register, not a match. If somebody nearby has space they\\u2019d consider sharing, we\\u2019ll email you and ask first. We may never find a garden near you.'];
    if (PILOT.indexOf(district) === -1) out.push('We\\u2019re starting in Raheny, Killester, Donnycarney and Artane, and we aren\\u2019t looking for anyone to introduce outside those areas. You\\u2019re on the register either way.');
    out.push('To come off it, email hello@plotnua.ie. There\\u2019s nothing to cancel and no notice period.');
    end('received', 'You\\u2019re on the register', out);
  }}
  function notOpen() {{
    end('not_open', 'The register isn\\u2019t open yet', ['Your details haven\\u2019t been saved. Your Grower Check is unchanged.',
      'Nothing is waiting on you. When the register opens, this is where it will happen.']);
  }}
  function unavailable() {{
    end('unavailable', 'That didn\\u2019t go through', ['Something went wrong between this page and PlotNua, and your details haven\\u2019t been saved.',
      'Trying again in a minute is usually the whole fix. If it keeps happening, hello@plotnua.ie reaches a person.']);
  }}
  function payload() {{
    var body = {{
      first_name: $('bgIntName').value,
      email: $('bgIntEmail').value,
      district: $('bgIntDistrict').value,
      travel_radius: $('bgIntTravel').value,
      space_wanted: $('bgIntSize').value,
      timing: $('bgIntTiming').value,
      over_18: $('bgIntConsent').checked === true,
      consent_text: CONSENT_TEXT,
      source: {json.dumps(SOURCE)}
    }};
    if ($('bgIntNote').value.trim()) body.growing_note = $('bgIntNote').value;
    return body;
  }}
  function localProblem() {{
    if (!$('bgIntName').value.trim()) return 'first_name';
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{{2,}}$/.test($('bgIntEmail').value.trim())) return 'email';
    if (!$('bgIntDistrict').value) return 'district';
    if (!$('bgIntTravel').value) return 'travel_radius';
    if (!$('bgIntSize').value) return 'space_wanted';
    if (!$('bgIntTiming').value) return 'timing';
    if (!$('bgIntConsent').checked) return 'over_18';
    return null;
  }}
  function submit(ev) {{
    ev.preventDefault();
    if (STATE === 'sending') return;
    Object.keys(FIELD_EL).forEach(function (k) {{ var el = $(FIELD_EL[k]); if (el) el.removeAttribute('aria-invalid'); }});
    var bad = localProblem();
    if (bad) {{ flag(bad); return; }}
    msg('');
    if ($('bgIntWebsite').value !== '') {{ unavailable(); return; }}
    var district = $('bgIntDistrict').value;
    intShow('sending');
    fetch(ENDPOINT, {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify(payload()) }})
      .then(function (r) {{ return r.json().then(function (j) {{ return {{ s: r.status, j: j }}; }}, function () {{ return {{ s: r.status, j: null }}; }}); }})
      .then(function (res) {{
        var st = res.j && res.j.state;
        if (res.s === 200 && st === 'received') {{ received(district); return; }}
        if (res.s === 503 && st === 'not_open') {{ notOpen(); return; }}
        if (res.s === 400 && st === 'refused') {{
          intShow('form');
          msg('PlotNua could not accept that: ' + (FIELD_NAME[res.j && res.j.field] || 'one of the answers') + '. Nothing has been saved.');
          return;
        }}
        unavailable();
      }}).catch(function () {{ unavailable(); }});
  }}
  function init() {{
    $('bgStart').addEventListener('click', function () {{ advance(); }});
    $('bgBack').addEventListener('click', back);
    var panel = $('bgInterest');
    if (!GROWER_PUBLIC && !preview()) {{
      if (panel && panel.parentNode) panel.parentNode.removeChild(panel);
    }} else {{
      if (!GROWER_PUBLIC) $('bgIntPrev').hidden = false;
      $('bgIntConsentText').textContent = CONSENT_TEXT;
      $('bgIntOpen').addEventListener('click', function () {{ intShow('form'); try {{ $('bgIntName').focus(); }} catch (e) {{}} }});
      $('bgIntCancel').addEventListener('click', function () {{ intShow('offer'); }});
      $('bgIntForm').addEventListener('submit', submit);
      $('bgIntForm').addEventListener('change', function (ev) {{
        if (!FLAGGED || !(FLAGGED === ev.target || FLAGGED.contains(ev.target))) return;
        FLAGGED.removeAttribute('aria-invalid'); FLAGGED = null;
      }});
      intShow('offer');
    }}
    if (/(?:^|[?&])start=1(?:&|$)/.test(location.search)) advance();
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}})();
</script>"""


def build() -> tuple[str, str]:
    w = worker_facts()
    guards_before(w)
    host = HOST.read_text()
    head_end = once(host, "</head>", "host </head>")
    main_at = once(host, '<main class="bg-wrap">', "host <main>")
    exit_at = once(host, "<!-- PLOTNUA JOURNEY EXIT v1 · BEGIN", "journey exit begin")
    exit_end_m = "<!-- PLOTNUA JOURNEY EXIT v1 · END -->"
    exit_end = once(host, exit_end_m, "journey exit end") + len(exit_end_m)
    head = host[:head_end]
    for old, new, what in [
        ('<link rel="canonical" href="https://plotnua.ie/disc025-borrowed-garden-check.html">',
         f'<link rel="canonical" href="https://plotnua.ie/{OUT.name}">', "canonical"),
        ("<title>The Borrowed Garden &mdash; Property Check | PlotNua</title>",
         "<title>The Borrowed Garden &mdash; Grower Check | PlotNua</title>", "title")]:
        once(head, old, what)
        head = head.replace(old, new)
    html = (head + host[head_end:main_at] + main_html() + "\n" + host[exit_at:exit_end] + "\n\n"
            + script_js() + "\n</body>\n</html>\n")
    disc = DISCOVERY.read_text()
    base_disc = git_show(f"{BASE_REF}:{DISCOVERY.name}").decode()
    launch_disc = discovery_launch(base_disc)
    if GROWER_PUBLIC:
        if disc not in (base_disc, launch_disc):
            die("G8 the Discovery differs from both its base and its bounded launch version")
        disc = launch_disc
    elif disc != base_disc:
        die("G8 the Discovery changed while the Grower Register is closed")
    guards_after(html, disc)
    return html, disc if GROWER_PUBLIC else launch_disc


def main() -> None:
    html, disc = build()
    if "--preview-discovery" in sys.argv:
        Path(sys.argv[sys.argv.index("--preview-discovery") + 1]).write_text(disc)
        print("wrote the LAUNCH Discovery preview (repo copy untouched)")
        return
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text() != html:
            die("the grower check is stale: run atlas-tools/build-grower-register.py")
        if GROWER_PUBLIC and DISCOVERY.read_text() != disc:
            die("the Discovery is stale")
        print("grower check is current")
        return
    OUT.write_text(html)
    if GROWER_PUBLIC:
        DISCOVERY.write_text(disc)
    print(f"wrote {OUT.name} ({len(html)} bytes) · GROWER_PUBLIC={GROWER_PUBLIC}")


if __name__ == "__main__":
    main()
