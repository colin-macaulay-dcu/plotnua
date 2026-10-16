#!/usr/bin/env python3
"""PlotNua · THE BORROWED GARDEN · GROWER REGISTER · bounded page builder.

Founder instruction, 16 October 2026 ("Community Roots Gardener Register
development"): build the gardener side of the Borrowed Garden pilot, using the
existing host-side architecture, and bring it back CLOSED for review.

Naming: "Community Roots" is an independent garden-sharing organisation in
Atlas (ORG-000202, Researching, not a partner) and appears in the Borrowed
Garden Provider Explorer. PlotNua's own two-sided register is therefore named
for PlotNua's own Discovery: the Garden Owner Register (hosts, live since
12 Oct 2026) and the Grower Register (this page). Guard G11 refuses a page
that presents "Community Roots" as the name of this register.

Writes ONE file: borrowed-garden-grower-register.html. Takes the shared site
shell (head, brand tokens, search rail, footer, reveal script) from
artist-register.html so the page is visually identical to the family.

Usage:
  python3 atlas-tools/build-grower-register.py           build
  python3 atlas-tools/build-grower-register.py --check   fail if the page is stale

GUARDS (each refuses the build; none is advisory):
  G1  consent sentence == the Worker's frozen grower sentence (G1B §3)
  G2  every vocabulary == the Worker's V lists, same values, same order
  G3  payload keys are a subset of the Worker's GROWER_ALLOWED_KEYS; source is
      a Worker grower_source value
  G4  CLOSED STATE: GROWER_PUBLIC false => noindex, form removed from the DOM
      unless ?register=preview, no other page links here, not in the sitemap,
      not in Search
  G5  no surname / address / Eircode / phone / file / tel field on the page
  G6  the honesty lines are present; no promise of a garden, match or
      introduction appears anywhere
  G7  the interest-check answers that the register does not keep (experience,
      working style) never reach the payload
  G8  the host journey is untouched: the host check page, the Discovery,
      privacy.html and the host Worker route are byte-identical to the base
  G9  opening (GROWER_PUBLIC = True) is refused until every OPEN_APPROVAL item
      is recorded, privacy.html carries the grower marker, and the Worker's
      committed GROWER_PRIVACY_VERSION names that notice
  G10 the shell markers exist exactly once (the shell cannot drift silently)
  G11 "Community Roots" is never used as the name of this register
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "borrowed-garden-grower-register.html"
SHELL = ROOT / "artist-register.html"
WORKER = ROOT / "worker" / "garden-register" / "src" / "index.js"
WRANGLER = ROOT / "worker" / "garden-register" / "wrangler.toml"
PRIVACY = ROOT / "privacy.html"
SITEMAP = ROOT / "sitemap.xml"
SEARCH = ROOT / "search-index-v1.json"

GROWER_PUBLIC = False
ENDPOINT = "https://plotnua-garden-register.colin-a41.workers.dev/v1/garden-register/grower"
GROWER_PRIVACY_MARKER = "PLOTNUA-GROWER-PRIVACY-V6"
GROWER_PRIVACY_VERSION = "2026-10-PHASE2-V6"

# Each item must be a dated founder record before GROWER_PUBLIC may be True.
OPEN_APPROVAL = {
    "founder_approval_to_open": None,
    "privacy_v6_approved_and_published": None,
    "worker_deployed_grower_closed": None,
    "controlled_test_passed": None,
    "discovery_entry_point_approved": None,
}

# The host files the gardener build must not touch (G8). Compared with the
# commit the gardener work started from.
HOST_FILES = ["disc025-borrowed-garden-check.html", "discovery-the-borrowed-garden.html",
              "privacy.html"]
BASE_REF = "84453f1"

LABELS = {
    "district": [("raheny", "Raheny"), ("killester", "Killester"), ("donnycarney", "Donnycarney"),
                 ("artane", "Artane"), ("elsewhere_in_dublin", "Elsewhere in Dublin"),
                 ("elsewhere_in_ireland", "Elsewhere in Ireland")],
    "travel_radius": [("walking", "Within walking distance"), ("up_to_2km", "Up to 2 km"),
                      ("up_to_5km", "Up to 5 km"), ("up_to_10km", "Up to 10 km")],
    "space_band": [("very_small", "Very small — a bed or two"), ("small", "Small — a corner"),
                   ("medium", "Medium — a good patch"), ("large", "Large"),
                   ("not_sure", "Not sure yet")],
    "timing": [("this_season", "This season"), ("within_3_months", "Within three months"),
               ("next_season", "Next season"), ("flexible", "I’m flexible")],
}
# Interest-check only. NEVER sent, never stored (G7).
CHECK_ONLY = {
    "experience": [("new", "I’m new to growing"), ("some", "I’ve grown a little"),
                   ("lots", "I’ve grown a lot")],
    "style": [("own", "Mostly on my own"), ("together", "Alongside the homeowner"),
              ("either", "Either would suit me")],
}
PAYLOAD_KEYS = ["first_name", "email", "district", "travel_radius", "space_wanted", "timing",
                "growing_note", "over_18", "consent_text", "source"]
SOURCE = "grower_register"
# G1B §3, FROZEN 7 Oct 2026. The page and the Worker must both equal THIS.
FROZEN_CONSENT = "I'm over 18, and I'd like PlotNua to keep this and tell me about possible growing space nearby."

HONESTY = [
    "No garden is available through PlotNua today.",
    "Matching isn’t live yet.",
    "We may never find a garden near you.",
    "This is a register, not a match.",
    "Nothing is shared with anybody until you say yes to one specific introduction.",
]
PROMISES = [r"\bguarantee(d|s)? (a|an|you)", r"\bwe will (match|introduce) you\b", r"\byour garden is waiting\b",
            r"\bgardens? (are|is) available (now|today)\b", r"\bget matched\b", r"\binstant(ly)? match"]


def die(msg: str) -> None:
    sys.stderr.write("REFUSED: " + msg + "\n")
    sys.exit(2)


def once(text: str, needle: str, what: str) -> int:
    n = text.count(needle)
    if n != 1:
        die(f"G10 shell marker {what!r} found {n} times in artist-register.html")
    return text.index(needle)


# ----------------------------------------------------------------- worker --
def worker_facts() -> dict:
    src = WORKER.read_text()
    m = re.search(r"grower:\s*\"([^\"]+)\"", src)
    if not m:
        die("G1 cannot read the Worker's grower consent sentence")
    vocab = {}
    for key in ("district", "space_band", "timing", "travel_radius", "grower_source"):
        mm = re.search(key + r":\s*\[([^\]]*)\]", src)
        if not mm:
            die(f"G2 cannot read the Worker vocabulary {key}")
        vocab[key] = re.findall(r"'([a-z0-9_]+)'", mm.group(1))
    ak = re.search(r"GROWER_ALLOWED_KEYS = Object\.freeze\(\[([^\]]*)\]", src)
    if not ak:
        die("G3 cannot read GROWER_ALLOWED_KEYS")
    if m.group(1) != FROZEN_CONSENT:
        die("G1 the Worker's grower sentence is not the frozen G1B §3 sentence")
    return {"consent": m.group(1), "vocab": vocab, "allowed": re.findall(r"'([a-z0-9_]+)'", ak.group(1))}


# ------------------------------------------------------------------ guards --
def guards_before(w: dict) -> None:
    # G2
    for key, pairs in LABELS.items():
        if [v for v, _ in pairs] != w["vocab"][key]:
            die(f"G2 {key} differs from the Worker: {[v for v, _ in pairs]} vs {w['vocab'][key]}")
    # G3
    extra = [k for k in PAYLOAD_KEYS if k not in w["allowed"]]
    if extra:
        die(f"G3 payload keys outside GROWER_ALLOWED_KEYS: {extra}")
    if SOURCE not in w["vocab"]["grower_source"]:
        die("G3 source is not a Worker grower_source value")
    # G8
    for f in HOST_FILES:
        try:
            base = subprocess.run(["git", "show", f"{BASE_REF}:{f}"], cwd=ROOT, capture_output=True,
                                  check=True).stdout
        except subprocess.CalledProcessError:
            die(f"G8 cannot read {f} at {BASE_REF}")
        if hashlib.sha256(base).hexdigest() != hashlib.sha256((ROOT / f).read_bytes()).hexdigest():
            if not (f == "privacy.html" and GROWER_PUBLIC):
                die(f"G8 host file changed: {f}")
    wsrc = WORKER.read_text()
    base_w = subprocess.run(["git", "show", f"{BASE_REF}:worker/garden-register/src/index.js"], cwd=ROOT,
                            capture_output=True, check=True).stdout.decode()
    seg = lambda s: s[s.index("async function handleGarden"):s.index("/* --------------------------------------------------------- grower handler")]
    try:
        base_seg = base_w[base_w.index("async function handleGarden"):base_w.index("/* --------------------------------------------------------- grower handler")]
        new_seg = wsrc[wsrc.index("async function handleGarden"):wsrc.index("/* ------------------------------------------------- grower route switches")]
    except ValueError:
        die("G8 cannot locate the host (garden) handler in the Worker")
    if base_seg != new_seg:
        die("G8 the host (garden) Worker handler changed")
    # G9
    if GROWER_PUBLIC:
        missing = [k for k, v in OPEN_APPROVAL.items() if not v]
        if missing:
            die(f"G9 cannot open: OPEN_APPROVAL items missing {missing}")
        if GROWER_PRIVACY_MARKER not in PRIVACY.read_text():
            die("G9 cannot open: privacy.html does not carry the Grower Register notice")
        if f'GROWER_PRIVACY_VERSION = "{GROWER_PRIVACY_VERSION}"' not in WRANGLER.read_text():
            die("G9 cannot open: wrangler.toml does not name the grower privacy version")


def guards_after(html: str, w: dict) -> None:
    # G1
    if f"var CONSENT_TEXT = {json.dumps(w['consent'])};" not in html:
        die("G1 consent sentence on the page differs from the Worker")
    if html.count(w["consent"]) != 1:
        die("G1 the consent sentence must exist exactly once (in the script)")
    # G4
    if not GROWER_PUBLIC:
        if '<meta name="robots" content="noindex, nofollow">' not in html:
            die("G4 closed page is not noindex")
        if "var GROWER_PUBLIC = false;" not in html:
            die("G4 closed page does not ship GROWER_PUBLIC false")
        for p in ROOT.glob("*.html"):
            if p.name != OUT.name and OUT.name in p.read_text(errors="ignore"):
                die(f"G4 {p.name} links to the closed register")
        if OUT.name in SITEMAP.read_text():
            die("G4 the sitemap lists the closed register")
        if OUT.name in SEARCH.read_text():
            die("G4 Search lists the closed register")
    if "if (!GROWER_PUBLIC && !preview())" not in html or "removeChild(card)" not in html:
        die("G4 the form is not removed from the DOM when closed")
    # G5
    low = html.lower()
    for bad in ['type="tel"', 'type="file"', 'name="surname"', 'name="last_name"', 'name="address"',
                'name="eircode"', 'name="phone"', 'autocomplete="family-name"', 'autocomplete="street-address"',
                'autocomplete="postal-code"', 'autocomplete="tel"']:
        if bad in low:
            die(f"G5 forbidden field on the page: {bad}")
    # G6
    visible = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", visible)
    text = (text.replace("&rsquo;", "’").replace("&mdash;", "—").replace("&nbsp;", " ")
                .replace("&amp;", "&"))
    text = re.sub(r"\s+", " ", text)
    for line in HONESTY:
        if line not in text:
            die(f"G6 honesty line missing: {line!r}")
    for pat in PROMISES:
        if re.search(pat, text, re.I):
            die(f"G6 a promise appears on the page: /{pat}/")
    # G7
    pay = html[html.index("function payload()"):html.index("function localProblem()")]
    for k in CHECK_ONLY:
        if k in pay:
            die(f"G7 the interest-check answer {k!r} reaches the payload")
    sent = re.findall(r"^\s{6}([a-z_0-9]+):", pay, re.M) + re.findall(r"body\.([a-z_0-9]+) =", pay)
    if sorted(set(sent)) != sorted(PAYLOAD_KEYS):
        die(f"G3 the page payload keys {sorted(set(sent))} are not exactly {sorted(PAYLOAD_KEYS)}")
    # G11
    if re.search(r"community roots (gardener|grower) register", text, re.I) or "<title>Community Roots" in html:
        die("G11 Community Roots (an independent organisation) is used as this register's name")


# ------------------------------------------------------------------- page --
def opts_js() -> str:
    o = {k: [[v, l] for v, l in pairs] for k, pairs in LABELS.items()}
    o.update({k: [[v, l] for v, l in pairs] for k, pairs in CHECK_ONLY.items()})
    return json.dumps(o, ensure_ascii=False)


def radio_set(name: str, legend: str, pairs, prefix: str, extra_cls: str = "") -> str:
    rows = "\n".join(
        f'              <div class="gr-tick"><input type="radio" id="{prefix}_{name}_{v}" name="{prefix}_{name}" '
        f'value="{v}"><label for="{prefix}_{name}_{v}">{l}</label></div>' for v, l in pairs)
    return (f'          <fieldset class="gr-set{extra_cls}" id="{prefix}Set_{name}"><legend>{legend}</legend>\n'
            f'            <div class="gr-ticks is-two">\n{rows}\n            </div>\n          </fieldset>')


def select(fid: str, name: str, label: str, key: str) -> str:
    opts = '<option value="">Choose one</option>' + "".join(
        f'<option value="{v}">{l}</option>' for v, l in LABELS[key])
    return (f'          <div class="gr-f"><label for="{fid}">{label}</label>\n'
            f'            <select id="{fid}" name="{name}" required>{opts}</select></div>')


CSS = r"""
  /* PLOTNUA-GROWER-REGISTER-CSS · The Borrowed Garden Grower Register (founder
     instruction 16 Oct 2026). Generated by atlas-tools/build-grower-register.py.
     Prefix gr-. Same tokens and form treatment as the Artist Register and the
     Art Space Register, so the registers read as one family. */
  :root{ --stone:#EFE9DA; --body:#3A453F; --muted:#5A655F;
    --rule:rgba(31,59,46,.18); --rule-soft:rgba(31,59,46,.10); }
  .gr-chip{display:inline-block;margin:0 0 22px;font-family:'Work Sans',sans-serif;font-size:11px;
    font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:#4F6B4A;
    border:1px solid rgba(79,107,74,.45);border-radius:20px;padding:5px 12px;}
  .gr-cta{display:inline-flex;align-items:center;gap:11px;background:var(--ink);color:var(--brand-ivory);
    border:none;font-family:'Work Sans',sans-serif;padding:16px 28px;font-size:13.5px;letter-spacing:.09em;
    text-transform:uppercase;border-radius:32px;cursor:pointer;text-decoration:none;min-height:48px;
    box-shadow:0 10px 26px rgba(31,59,46,.22);transition:background .22s ease, transform .22s ease;}
  .gr-cta:hover{background:var(--accent);transform:translateY(-2px);}
  .article a.gr-cta,.article a.gr-cta:hover,.article a.gr-cta:visited{color:var(--brand-ivory);text-decoration:none;}
  .gr-cta[disabled]{opacity:.7;cursor:default;transform:none;}
  .gr-cta:focus-visible,.gr-link:focus-visible{outline:3px solid var(--brand-sage);outline-offset:3px;}
  .gr-link{display:inline-flex;align-items:center;min-height:48px;font-size:15px;color:var(--ink);
    text-decoration:underline;text-underline-offset:3px;}
  .gr-ctas{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;margin-top:34px;}
  .gr-steps{list-style:none;counter-reset:gr;margin:18px 0 0;padding:0;display:grid;gap:14px;}
  .gr-steps li{counter-increment:gr;position:relative;padding:16px 18px 16px 62px;border-radius:14px;
    background:var(--stone);font-size:16px;line-height:1.6;color:var(--body);}
  .gr-steps li::before{content:counter(gr);position:absolute;left:18px;top:14px;width:30px;height:30px;
    border-radius:50%;background:var(--ink);color:var(--brand-ivory);font-family:'Fraunces',serif;
    font-size:15px;display:flex;align-items:center;justify-content:center;}
  .gr-steps strong{color:var(--ink);font-weight:500;}
  .gr-card{margin:8px 0 0;padding:28px 24px 26px;border-radius:18px;background:var(--stone);max-width:760px;}
  .gr-card[hidden],.gr-form[hidden],.gr-done[hidden],.gr-closed[hidden],.gr-prev[hidden],.gr-msg[hidden],
  .gr-result[hidden]{display:none;}
  .gr-prev{margin:0 0 16px;font-family:'Work Sans',sans-serif;font-size:10px;font-weight:500;
    letter-spacing:.2em;text-transform:uppercase;color:#6E5639;border:1px solid rgba(139,111,78,.4);
    border-radius:20px;padding:5px 12px;display:inline-block;}
  .article p.gr-prev{font-size:10px;line-height:1.4;letter-spacing:.2em;max-width:none;}
  .gr-privline{margin:0 0 20px;font-size:14px;line-height:1.6;color:var(--muted);}
  .gr-grid{display:grid;gap:18px;}
  @media(min-width:760px){ .gr-grid{grid-template-columns:repeat(2,1fr);} }
  .gr-f{display:grid;gap:6px;align-content:start;}
  .gr-f.is-wide{grid-column:1/-1;}
  .gr-f > label,.gr-set legend{font-family:'Work Sans',sans-serif;font-size:15px;font-weight:500;color:var(--ink);}
  .gr-opt{font-weight:400;color:var(--muted);}
  .gr-hint{font-size:13.5px;line-height:1.55;color:var(--muted);}
  .gr-f input[type=text],.gr-f input[type=email],.gr-f select,.gr-f textarea{
    width:100%;min-height:50px;font-family:'Work Sans',sans-serif;font-size:16px;line-height:1.5;color:var(--ink);
    background:#FFFDF7;border:1px solid var(--rule);border-radius:12px;padding:12px 14px;
    -webkit-appearance:none;appearance:none;}
  .gr-f select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' fill='none' stroke='%231F3B2E' stroke-width='1.6'/%3E%3C/svg%3E");
    background-repeat:no-repeat;background-position:right 14px center;background-size:12px;padding-right:38px;}
  .gr-f textarea{min-height:110px;resize:vertical;}
  .gr-f input:focus,.gr-f select:focus,.gr-f textarea:focus{outline:2px solid var(--accent);outline-offset:1px;}
  .gr-f [aria-invalid=true],.gr-set[aria-invalid=true] .gr-tick{border-color:#7A3B2E;}
  .gr-set{margin:0 0 20px;padding:0;border:0;min-width:0;}
  .gr-set legend{padding:0;margin:0 0 8px;}
  .gr-ticks{display:grid;gap:8px;margin:8px 0 0;}
  @media(min-width:760px){ .gr-ticks.is-two{grid-template-columns:1fr 1fr;} }
  .gr-tick{display:grid;grid-template-columns:20px 1fr;gap:4px 11px;align-items:center;padding:12px 14px;
    min-height:48px;border-radius:12px;background:#FFFDF7;border:1px solid var(--rule-soft);}
  .gr-tick:has(input:checked){border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink);}
  .gr-tick input{width:20px;height:20px;margin:0;accent-color:var(--accent);}
  .gr-tick label{font-size:15px;line-height:1.5;color:var(--body);cursor:pointer;}
  .gr-consent{margin:22px 0 0;align-items:start;border-color:var(--rule);}
  .gr-consent input{margin-top:2px;}
  .gr-notice{margin:12px 0 0;}
  .gr-notice summary{cursor:pointer;padding:12px 0;font-size:14px;color:var(--soft);min-height:44px;}
  .gr-notice summary:hover,.gr-notice[open] summary{color:var(--ink);}
  .gr-noticebody{font-size:14px;line-height:1.7;color:var(--body);max-width:68ch;}
  .gr-noticebody p{margin:0 0 12px;color:var(--body);font-size:14px;line-height:1.7;}
  .gr-noticebody strong{font-weight:500;color:var(--ink);}
  .gr-actions{margin:22px 0 0;display:flex;flex-wrap:wrap;gap:14px 20px;align-items:center;}
  .gr-msg{margin:16px 0 0;font-size:14.5px;line-height:1.65;color:#7A3B2E;}
  .gr-done-h,.gr-result-h{font-family:'Fraunces',Georgia,serif;font-weight:500;font-size:clamp(22px,4vw,26px);
    line-height:1.2;color:var(--ink);margin:0 0 12px;max-width:none;}
  .gr-done-h:focus,.gr-result-h:focus{outline:none;}
  .gr-done[data-state=received]::before{content:"";display:block;width:44px;height:44px;margin:0 0 14px;
    border-radius:50%;background:var(--ink) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M6 12.5l4 4 8-9' fill='none' stroke='%23F2EFE6' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/24px no-repeat;}
  .gr-card p.gr-p,.gr-result p{margin:0 0 12px;font-size:15.5px;line-height:1.65;color:var(--body);max-width:68ch;}
  .gr-result{margin:22px 0 0;padding:22px 0 0;border-top:1px solid var(--rule);}
  .gr-result ul{margin:0 0 14px 20px;}
  .gr-result li{margin:0 0 8px;font-size:15.5px;line-height:1.6;color:var(--body);}
  .gr-safe{margin:12px 0 0;}
  .gr-safe summary{cursor:pointer;font-size:16px;color:var(--ink);padding:12px 0;min-height:44px;}
  .gr-hp{position:absolute !important;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;}
  @media(max-width:560px){ .gr-card{padding:24px 18px;} .gr-actions .gr-cta,.gr-ctas .gr-cta{width:100%;justify-content:center;}
    .gr-steps li{padding-left:56px;} }
  @media(prefers-reduced-motion:reduce){ .gr-cta{transition:none;} }
"""


def body_html() -> str:
    check_sets = "\n".join([
        radio_set("district", "1. Where do you live?", LABELS["district"], "gc"),
        radio_set("travel_radius", "2. How far would you go to a garden?", LABELS["travel_radius"], "gc"),
        radio_set("space_band", "3. How much space would suit you?", LABELS["space_band"], "gc"),
        radio_set("timing", "4. When would you like to start?", LABELS["timing"], "gc"),
        radio_set("experience", "5. How much growing have you done?", CHECK_ONLY["experience"], "gc"),
        radio_set("style", "6. How would you like to work?", CHECK_ONLY["style"], "gc"),
    ])
    return f"""
<!-- THE BORROWED GARDEN · GROWER REGISTER (founder instruction 16 Oct 2026). SHIPPED CLOSED.
     Generated by atlas-tools/build-grower-register.py -- do not hand-edit. -->
<section class="privacy-intro reveal">
  <div class="privacy-intro-inner">
    <span class="gr-chip">The Borrowed Garden &middot; Grower Register</span>
    <h1>Somewhere to grow, closer than you think.</h1>
    <p class="subtitle">Would you like a little ground to grow on?</p>
    <p class="lede">Some homeowners have a corner of garden they don&rsquo;t use. PlotNua is exploring a small pilot that would introduce them to people nearby who&rsquo;d like somewhere to grow.</p>
    <p class="lede">If that&rsquo;s you, whether you&rsquo;re a complete beginner or have grown for years, tell us. It&rsquo;s free, private and doesn&rsquo;t commit you to anything.</p>
    <div class="gr-ctas">
      <a class="gr-cta" href="#check">Check your interest <span aria-hidden="true">&darr;</span></a>
      <a class="gr-link" href="#register">Go straight to the register</a>
    </div>
  </div>
</section>

<main class="article" id="pn-main">

  <section class="article-section reveal" aria-labelledby="grHowH">
    <div class="kicker">How It Would Work</div>
    <h2 id="grHowH">Two registers, one careful introduction.</h2>
    <ol class="gr-steps">
      <li><strong>Homeowners</strong> with a spare corner tell PlotNua on the Garden Owner Register.</li>
      <li><strong>Growers</strong> tell PlotNua what they&rsquo;re looking for, here.</li>
      <li>If we think there might be a fit, <strong>we email each of you separately and ask.</strong> We describe the other person only in general terms: an area, how much space, roughly when.</li>
      <li>Only if you both say yes do we share first names and email addresses. You meet at the garden, in daylight, and decide together.</li>
    </ol>
  </section>

  <section class="article-section reveal" aria-labelledby="grHonestH">
    <div class="kicker">Where Things Stand</div>
    <h2 id="grHonestH">Honest about where we are.</h2>
    <ul>
      <li><strong>No garden is available through PlotNua today.</strong> Matching isn&rsquo;t live yet. Joining the register doesn&rsquo;t arrange anything.</li>
      <li><strong>We&rsquo;re starting small</strong>, in Raheny, Killester, Donnycarney and Artane. If you live elsewhere you&rsquo;re welcome to join, but we aren&rsquo;t looking for anyone to introduce outside those areas yet.</li>
      <li><strong>We can&rsquo;t promise anything.</strong> We may never find a garden near you.</li>
      <li><strong>You stay in control.</strong> Nothing is shared with anybody until you say yes to one specific introduction.</li>
    </ul>
    <p>Hoping to grow sooner? Community gardens, garden-sharing services and council allotments may have space now. <a href="discovery-the-borrowed-garden.html#explore-providers">See who&rsquo;s already helping people find ground</a>.</p>
  </section>

  <section class="article-section reveal" id="check" aria-labelledby="grCheckH">
    <div class="kicker">Check Your Interest</div>
    <h2 id="grCheckH">Six quick questions.</h2>
    <p>See what the pilot could mean for you. <strong>Nothing you answer here is sent anywhere.</strong></p>
    <div class="gr-card">
      <form id="gcForm" novalidate>
{check_sets}
        <p class="gr-msg" id="gcMsg" hidden role="status" aria-live="polite"></p>
        <div class="gr-actions"><button class="gr-cta" type="submit" id="gcGo">See what this means for me</button></div>
      </form>
      <div class="gr-result" id="gcResult" hidden>
        <h3 class="gr-result-h" id="gcResultH" tabindex="-1"></h3>
        <div id="gcResultBody"></div>
        <div class="gr-actions"><a class="gr-cta" href="#register" id="gcJoin">Join the Grower Register</a></div>
      </div>
    </div>
  </section>

  <section class="article-section reveal" id="register" aria-labelledby="grRegH">
    <div class="kicker">Join the Register</div>
    <h2 id="grRegH">Tell us what you&rsquo;re looking for.</h2>
    <div class="gr-card gr-closed" id="grClosed">
      <p class="gr-p"><strong>The Grower Register isn&rsquo;t open yet.</strong> It&rsquo;s being prepared. When it opens, this is where you&rsquo;ll be able to join.</p>
    </div>
    <div class="gr-card" id="grCard" hidden>
      <p class="gr-prev" id="grPrev" hidden>Private preview &middot; not public</p>
      <form class="gr-form" id="grForm" novalidate>
        <p class="gr-privline">A first name, an email address and an area. No surname, no address, no Eircode, no phone number.</p>
        <div class="gr-grid">
          <div class="gr-f"><label for="grName">First name</label>
            <input type="text" id="grName" name="first_name" autocomplete="given-name" maxlength="40" required></div>
          <div class="gr-f"><label for="grEmail">Email address</label>
            <input type="email" id="grEmail" name="email" autocomplete="email" maxlength="120" required></div>
{select("grDistrict", "district", "Your area", "district")}
{select("grTravel", "travel_radius", "How far you&rsquo;d go", "travel_radius")}
{select("grSpace", "space_wanted", "How much space you&rsquo;re looking for", "space_band")}
{select("grTiming", "timing", "Roughly when", "timing")}
          <div class="gr-f is-wide"><label for="grNote">Anything you&rsquo;d like us to know? <span class="gr-opt">(optional)</span></label>
            <textarea id="grNote" name="growing_note" maxlength="600" aria-describedby="grNoteHint"></textarea>
            <span class="gr-hint" id="grNoteHint">You could mention what you&rsquo;d like to grow, how much growing you&rsquo;ve done, whether you&rsquo;d rather work on your own or alongside the homeowner, and which days usually suit you. Please don&rsquo;t include your address, phone number or anything about your health.</span></div>
        </div>
        <div class="gr-hp" aria-hidden="true"><label for="grWebsite">Leave this field empty</label>
          <input type="text" id="grWebsite" name="website" tabindex="-1" autocomplete="off" value=""></div>
        <div class="gr-tick gr-consent"><input type="checkbox" id="grConsent" required>
          <label for="grConsent"><span id="grConsentText"></span></label></div>
        <details class="gr-notice">
          <summary>Before you join &mdash; what we keep, and what we never ask for</summary>
          <div class="gr-noticebody">
            <p><strong>What we keep.</strong> Your first name, your email address, the area you chose, how far you&rsquo;d travel, how much space you&rsquo;re looking for, roughly when, and anything you choose to tell us in the notes box. We also keep the administrative records needed to manage your registration, your consent and its status.</p>
            <p><strong>What we never ask for.</strong> Your address, your Eircode, your phone number, your surname, your age, or anything about your health. Your answers to the six quick questions above are not sent.</p>
            <p><strong>Why we keep it.</strong> So that we can tell you if someone near you has growing space they&rsquo;d consider sharing.</p>
            <p><strong>Joining doesn&rsquo;t share your details with anyone.</strong> No other person sees your record. There is no public listing, no map, no profile page and no directory.</p>
            <p><strong>If we think there&rsquo;s a possible fit, we&rsquo;ll email you and ask.</strong> We&rsquo;ll describe the homeowner in general terms only. Your email address only reaches another person after you have said yes to that specific introduction. If you don&rsquo;t reply, nothing happens.</p>
            <p><strong>What &ldquo;registered&rdquo; means.</strong> Only that you asked PlotNua to tell you about potential growing space. It doesn&rsquo;t mean anyone has checked or approved anything.</p>
            <p><strong>Leaving.</strong> Email hello@plotnua.ie and we will delete your record. There&rsquo;s nothing to cancel and no notice period.</p>
            <p><strong>How long we keep it.</strong> A maximum of 24 months. You can ask us to delete it at any time.</p>
            <p><strong>One thing we keep after deletion.</strong> A separate note that you gave permission and that we honoured your request, holding a one-way digital fingerprint made from your email address, not the address itself.</p>
            <p>The full details are in our <a href="privacy.html">privacy notice</a>.</p>
          </div>
        </details>
        <p class="gr-msg" id="grMsg" hidden role="status" aria-live="polite"></p>
        <div class="gr-actions">
          <button class="gr-cta" type="submit" id="grSend">Join the Grower Register</button>
        </div>
        <p class="gr-hint">This is a register, not a match.</p>
      </form>
      <div class="gr-done" id="grDone" hidden role="status" aria-live="polite">
        <h3 class="gr-done-h" id="grDoneH" tabindex="-1"></h3>
        <div id="grDoneBody"></div>
      </div>
    </div>
  </section>

  <section class="article-section reveal" aria-labelledby="grSafeH">
    <div class="kicker">If an Introduction Ever Happens</div>
    <h2 id="grSafeH">PlotNua introduces people. That is all it does.</h2>
    <p>PlotNua doesn&rsquo;t verify anybody&rsquo;s identity, hasn&rsquo;t Garda vetted anyone, hasn&rsquo;t checked references and doesn&rsquo;t provide insurance. PlotNua doesn&rsquo;t handle money or take a fee.</p>
    <details class="gr-safe">
      <summary>Meeting for the first time</summary>
      <ul>
        <li>Meet at the garden, in daylight, before anything is agreed.</li>
        <li>Tell somebody else where you&rsquo;re going and when you expect to be back. Bring somebody with you if you&rsquo;d prefer.</li>
        <li>Agree how you&rsquo;ll get in, which tools you&rsquo;ll use and where they&rsquo;re kept. A key isn&rsquo;t needed for this to work.</li>
        <li>Either of you can stop at any time, for any reason or none.</li>
        <li>If something feels wrong, email hello@plotnua.ie. If you are in danger, contact An Garda S&iacute;och&aacute;na on 999 or 112.</li>
      </ul>
    </details>
  </section>

</main>
"""


def script_js(consent: str) -> str:
    return f"""<script>
/* PLOTNUA-GROWER-REGISTER-JS · The Borrowed Garden Grower Register (founder
 * instruction 16 Oct 2026). Generated by atlas-tools/build-grower-register.py.
 * SHIPS CLOSED: unless GROWER_PUBLIC or ?register=preview, the form is REMOVED
 * from the DOM and the page says the register isn't open. Expressions of
 * interest only: no matching, no introduction. The interest check is local:
 * its answers are never sent; four of them may pre-fill the form, where the
 * person sees and can change them. The consent sentence exists once, written
 * with textContent and sent verbatim. Reads no storage, cookie or My Plot data. */
(function () {{
  'use strict';
  var GROWER_PUBLIC = {'true' if GROWER_PUBLIC else 'false'};
  var ENDPOINT = {json.dumps(ENDPOINT)};
  var CONSENT_TEXT = {json.dumps(consent)};
  var OPTS = {opts_js()};
  var PILOT = ['raheny', 'killester', 'donnycarney', 'artane'];
  var FIELD_NAME = {{
    first_name: 'your first name', email: 'your email address', district: 'your area',
    travel_radius: 'how far you\\u2019d go', space_wanted: 'how much space you\\u2019re looking for',
    timing: 'roughly when', growing_note: 'the note', over_18: 'the confirmation that you are over 18 and agree',
    consent_text: 'the permission wording'
  }};
  var FIELD_EL = {{ first_name: 'grName', email: 'grEmail', district: 'grDistrict', travel_radius: 'grTravel',
    space_wanted: 'grSpace', timing: 'grTiming', growing_note: 'grNote', over_18: 'grConsent' }};
  var STATE = 'form';
  var FLAGGED = null;
  function $(id) {{ return document.getElementById(id); }}
  function preview() {{
    try {{ return /(?:^|[?&])register=preview(?:&|$)/.test(location.search); }} catch (e) {{ return false; }}
  }}
  function label(key, v) {{
    var l = ''; (OPTS[key] || []).forEach(function (o) {{ if (o[0] === v) l = o[1]; }}); return l;
  }}

  /* ---------------------------------------------- the interest check (local) -- */
  var CHECK_KEYS = ['district', 'travel_radius', 'space_band', 'timing', 'experience', 'style'];
  function checked(key) {{
    var out = '';
    (OPTS[key] || []).forEach(function (o) {{ var b = $('gc_' + key + '_' + o[0]); if (b && b.checked) out = o[0]; }});
    return out;
  }}
  function para(host, text) {{ var p = document.createElement('p'); p.textContent = text; host.appendChild(p); }}
  function checkSubmit(ev) {{
    ev.preventDefault();
    var a = {{}}, missing = null;
    CHECK_KEYS.forEach(function (k) {{ a[k] = checked(k); if (!a[k] && !missing) missing = k; }});
    var m = $('gcMsg');
    if (missing) {{
      m.textContent = 'Please answer question ' + (CHECK_KEYS.indexOf(missing) + 1) + '.'; m.hidden = false;
      var first = $('gc_' + missing + '_' + OPTS[missing][0][0]); try {{ first.focus(); }} catch (e) {{}}
      return;
    }}
    m.hidden = true;
    var inPilot = PILOT.indexOf(a.district) !== -1;
    var body = $('gcResultBody'); body.innerHTML = '';
    $('gcResultH').textContent = inPilot ? 'You\\u2019re in one of our first areas' : 'You\\u2019re welcome to join';
    para(body, inPilot
      ? 'We\\u2019re starting in ' + label('district', a.district) + ' and three neighbouring areas. If a homeowner nearby offers space that could suit you, we\\u2019d email you and ask first.'
      : 'We\\u2019re starting in Raheny, Killester, Donnycarney and Artane, and we aren\\u2019t looking for anyone to introduce elsewhere yet. You can still join, and it helps us see where people would like to grow.');
    if (a.experience === 'new') para(body, 'Complete beginners are welcome. A bed or two is a good place to start, and many homeowners would be glad to see a corner used at all.');
    else if (a.experience === 'some') para(body, 'A little experience goes a long way. You could tell us what you\\u2019ve grown before in the note.');
    else para(body, 'Experienced growers are very welcome. You could tell us what you\\u2019d like to grow, and whether you\\u2019d be happy to share what you know.');
    if (a.style === 'together') para(body, 'Some homeowners would enjoy growing alongside you; others would rather leave you to it. If a possible fit comes up, we\\u2019d ask both of you about this first.');
    else if (a.style === 'own') para(body, 'Some homeowners would rather leave you to it, which suits you well. If a possible fit comes up, we\\u2019d check this with both of you first.');
    if (a.space_band === 'large') para(body, 'Larger spaces are rarer, so it may take longer, or never happen. Saying you\\u2019d also be happy with less can help.');
    para(body, 'No garden is available through PlotNua today, and we may never find one near you. Nothing you\\u2019ve answered here has been sent anywhere.');
    /* Pre-fill ONLY the four fields the register keeps. The person sees them in
       the form and can change them; nothing is sent until they submit there. */
    if ($('grDistrict')) {{ $('grDistrict').value = a.district; $('grTravel').value = a.travel_radius;
      $('grSpace').value = a.space_band; $('grTiming').value = a.timing; }}
    $('gcResult').hidden = false;
    try {{ $('gcResultH').focus(); }} catch (e) {{}}
  }}

  /* ---------------------------------------------------------- the register -- */
  function msg(t) {{ var m = $('grMsg'); m.textContent = t || ''; m.hidden = !t; }}
  function clearInvalid() {{
    Object.keys(FIELD_EL).forEach(function (k) {{ var el = $(FIELD_EL[k]); if (el) el.removeAttribute('aria-invalid'); }});
  }}
  function flag(field) {{
    msg('We still need ' + (FIELD_NAME[field] || 'one more thing') + '.');
    var el = $(FIELD_EL[field]); FLAGGED = el;
    if (!el) return;
    el.setAttribute('aria-invalid', 'true');
    try {{ el.focus(); }} catch (e) {{}}
  }}
  function show(which) {{
    STATE = which;
    $('grForm').hidden = !(which === 'form' || which === 'sending');
    $('grDone').hidden = (which === 'form' || which === 'sending');
    $('grDone').setAttribute('data-state', which);
    var s = $('grSend');
    s.disabled = (which === 'sending');
    s.textContent = which === 'sending' ? 'Sending\\u2026' : 'Join the Grower Register';
  }}
  function end(which, heading, paras) {{
    $('grDoneH').textContent = heading;
    var b = $('grDoneBody'); b.innerHTML = '';
    paras.forEach(function (t) {{ var p = document.createElement('p'); p.className = 'gr-p'; p.textContent = t; b.appendChild(p); }});
    show(which);
    try {{ $('grDoneH').focus(); }} catch (e) {{}}
  }}
  function received(district) {{
    var out = [
      'We have your first name, your email and what you\\u2019re looking for. Nobody else can see it.',
      'This is a register, not a match. If somebody nearby has space they\\u2019d consider sharing, we\\u2019ll email you and ask first. We may never find a garden near you.'
    ];
    if (PILOT.indexOf(district) === -1) out.push('We\\u2019re starting in Raheny, Killester, Donnycarney and Artane, and we aren\\u2019t looking for anyone to introduce outside those areas yet. You\\u2019re on the register either way.');
    out.push('To come off it, email hello@plotnua.ie. There\\u2019s nothing to cancel and no notice period.');
    end('received', 'You\\u2019re on the Grower Register', out);
  }}
  function notOpen() {{
    end('not_open', 'The register isn\\u2019t open yet', [
      'Your details haven\\u2019t been saved.',
      'Nothing is waiting on you. When the register opens, this is where it will happen.'
    ]);
  }}
  function unavailable() {{
    end('unavailable', 'That didn\\u2019t go through', [
      'Something went wrong between this page and PlotNua, and your details haven\\u2019t been saved.',
      'Trying again in a minute is usually the whole fix. If it keeps happening, hello@plotnua.ie reaches a person.'
    ]);
  }}
  /* The payload. These keys are the Worker's GROWER_ALLOWED_KEYS (guard G3).
     The interest-check answers it does not keep are never read here (G7). */
  function payload() {{
    var body = {{
      first_name: $('grName').value,
      email: $('grEmail').value,
      district: $('grDistrict').value,
      travel_radius: $('grTravel').value,
      space_wanted: $('grSpace').value,
      timing: $('grTiming').value,
      over_18: $('grConsent').checked === true,
      consent_text: CONSENT_TEXT,
      source: {json.dumps(SOURCE)}
    }};
    if ($('grNote').value.trim()) body.growing_note = $('grNote').value;
    return body;
  }}
  function localProblem() {{
    if (!$('grName').value.trim()) return 'first_name';
    var e = $('grEmail').value.trim();
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{{2,}}$/.test(e)) return 'email';
    if (!$('grDistrict').value) return 'district';
    if (!$('grTravel').value) return 'travel_radius';
    if (!$('grSpace').value) return 'space_wanted';
    if (!$('grTiming').value) return 'timing';
    if (!$('grConsent').checked) return 'over_18';
    return null;
  }}
  function submit(ev) {{
    ev.preventDefault();
    if (STATE === 'sending') return;
    clearInvalid();
    var bad = localProblem();
    if (bad) {{ flag(bad); return; }}
    msg('');
    /* Honeypot, after ordinary validation: filled -> nothing is sent. */
    if ($('grWebsite').value !== '') {{ unavailable(); return; }}
    var district = $('grDistrict').value;
    show('sending');
    fetch(ENDPOINT, {{ method: 'POST', headers: {{ 'content-type': 'application/json' }}, body: JSON.stringify(payload()) }})
      .then(function (r) {{
        return r.json().then(function (j) {{ return {{ s: r.status, j: j }}; }}, function () {{ return {{ s: r.status, j: null }}; }});
      }}).then(function (res) {{
        var st = res.j && res.j.state;
        if (res.s === 200 && st === 'received') {{ received(district); return; }}
        if (res.s === 503 && st === 'not_open') {{ notOpen(); return; }}
        if (res.s === 400 && st === 'refused') {{
          show('form');
          msg('PlotNua could not accept that: ' + (FIELD_NAME[res.j && res.j.field] || 'one of the answers') +
              '. Nothing has been saved.');
          return;
        }}
        unavailable();
      }}).catch(function () {{ unavailable(); }});
  }}
  function init() {{
    $('gcForm').addEventListener('submit', checkSubmit);
    var card = $('grCard'), closed = $('grClosed');
    if (!card) return;
    if (!GROWER_PUBLIC && !preview()) {{
      if (card.parentNode) card.parentNode.removeChild(card);
      return;
    }}
    if (closed && closed.parentNode) closed.parentNode.removeChild(closed);
    card.hidden = false;
    if (!GROWER_PUBLIC) $('grPrev').hidden = false;
    $('grConsentText').textContent = CONSENT_TEXT;
    $('grForm').addEventListener('submit', submit);
    $('grForm').addEventListener('change', function (ev) {{
      if (STATE !== 'form' || !FLAGGED || !(FLAGGED === ev.target || FLAGGED.contains(ev.target))) return;
      FLAGGED.removeAttribute('aria-invalid'); FLAGGED = null;
    }});
    show('form');
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}})();
</script>"""


def build() -> str:
    w = worker_facts()
    guards_before(w)
    shell = SHELL.read_text()
    css_at = once(shell, "  /* PLOTNUA-ARTIST-REGISTER-CSS", "artist CSS")
    style_end = shell.index("</style>", css_at)
    rail_end_marker = "<!-- PLOTNUA SEARCH RAIL v1 · END -->"
    rail_end = once(shell, rail_end_marker, "search rail end") + len(rail_end_marker)
    foot_at = once(shell, "<footer>", "footer")
    js_at = once(shell, "<script>\n/* PLOTNUA-ARTIST-REGISTER-JS", "artist JS")

    head = shell[:css_at]
    title = "Grower Register | The Borrowed Garden | PlotNua"
    desc = ("Would you like somewhere to grow? PlotNua is exploring a small pilot introducing growers to homeowners "
            "with a spare corner. Join the Grower Register: free, private and non-binding.")
    url = "https://plotnua.ie/" + OUT.name
    robots = "index, follow" if GROWER_PUBLIC else "noindex, nofollow"
    head = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", head, count=1)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', head, count=1)
    head = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{robots}">', head, count=1)
    head = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', head, count=1)
    head = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', head, count=1)
    for must in (title, desc, robots, url):
        if must not in head:
            die("G10 the shell head could not be re-pointed: " + must[:40])

    html = (head + CSS.lstrip("\n") + shell[style_end:rail_end] + "\n" + body_html() + "\n"
            + shell[foot_at:js_at] + script_js(w["consent"]) + "\n</body>\n</html>\n")
    guards_after(html, w)
    return html


def main() -> None:
    html = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text() != html:
            die("the page is stale: run atlas-tools/build-grower-register.py")
        print("grower register page is current")
        return
    OUT.write_text(html)
    print(f"wrote {OUT.name} ({len(html)} bytes) · GROWER_PUBLIC={GROWER_PUBLIC}")


if __name__ == "__main__":
    main()
