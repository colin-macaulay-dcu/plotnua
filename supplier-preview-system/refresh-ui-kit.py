#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refresh-ui-kit.py — PlotNua Supplier Preview System v1.0
Regenerates supplier-preview-system/template-*.html from the LIVE production
Results / My Plot code in your-plot.html, so a preview can never drift from
the real interface.

    python3 supplier-preview-system/refresh-ui-kit.py

Run it from the repository root after any change to the Results surface, then
re-QA both templates. It rewrites the templates wholesale: the templates are
generated artefacts, so edit THIS file, never the HTML it emits.

Every guard aborts the run; nothing partial is written.
"""

import re, sys, os, json, hashlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(REPO, 'your-plot.html')
OUT  = os.path.join(REPO, 'supplier-preview-system')

def die(m):
    sys.exit('GUARD FAILED: ' + m)

L = open(SRC, encoding='utf-8').read().split('\n')

def grab(a, b, label):
    i, j = a - 1, b
    seg = '\n'.join(L[i:j]); n = 0
    while seg.count('{') != seg.count('}'):
        j += 1; n += 1
        if n > 40: die('unbalanced braces in ' + label)
        seg = '\n'.join(L[i:j])
    if seg.count('/*') != seg.count('*/'): die('unterminated comment in ' + label)
    return seg

BLOCKS = [('root',473,477),('heart',2470,2476),('heartsizes',2522,2533),
          ('myplot',2334,2404),('cardactions',1967,1967),('save',2003,2052),
          ('hero1',3555,3599),('media',3604,3606),('herobody',3607,3607),
          ('hero2',3621,3636),('hero3',3642,3652),('prop',5503,5560),
          ('secondary',4219,4227),('mq720',4229,4267),('mq719',4268,4290),
          ('late',5183,5239)]
C = {n: grab(a, b, n) for n, a, b in BLOCKS}

src = '\n'.join(L)
P = {}
for n in ('PN_P_PATH','PN_HOUSE_PATH','PN_HEART_PATH'):
    m = re.search(r'const ' + n + r"\s*=\s*'([^']*)'", src)
    if not m: die('missing ' + n)
    P[n] = m.group(1)

def mark(clip):
    return ('<span class="pn-mark-heart is-plot-active" aria-hidden="true">'
      '<svg viewBox="0 0 3000 3000" xmlns="http://www.w3.org/2000/svg" class="pmh-svg" aria-hidden="true">'
      '<defs><clipPath id="' + clip + '"><rect width="3000" height="3000" rx="666.5"/></clipPath></defs>'
      '<rect width="3000" height="3000" rx="666.5" fill="#1F3B2E"/>'
      '<g clip-path="url(#' + clip + ')"><g transform="translate(0,3000) scale(0.1,-0.1)">'
      '<path d="' + P['PN_P_PATH'] + '" fill="#F2EFE6"/>'
      '<path d="' + P['PN_HOUSE_PATH'] + '" fill="#8FAF8A"/>'
      '</g></g>'
      '<path class="pmh-heart-path" fill="#C57A5A" d="' + P['PN_HEART_PATH'] + '"/>'
      '</svg></span>')

UI_KIT = "\n".join([
 "/* ══ BEGIN PLOTNUA UI KIT — GENERATED, DO NOT HAND-EDIT ══════════════",
 "   Lifted verbatim from your-plot.html by refresh-ui-kit.py. These are the",
 "   production Results / My Plot rules, not a copy of them. Re-run the script",
 "   after any change to the real Results surface. */",
 C['root'], C['heart'], C['heartsizes'], C['myplot'], C['cardactions'], C['save'],
 C['hero1'], C['media'], C['herobody'], C['hero2'], C['hero3'], C['prop'],
 C['secondary'], C['mq720'], C['mq719'], C['late'],
 "/* ══ END PLOTNUA UI KIT ════════════════════════════════════════════ */",
])

# ─────────────────────────────────────────────────────────────────────
PAGE_CSS = r'''
/* ── PREVIEW SHELL — the page around the demonstration ───────────── */
:root{
  --pn-ground:#F5F2E8; --pn-voice:#24351F; --pn-fact:#16190F; --pn-body:#474B3B;
  --pn-stone:#8B8971; --pn-meta:#9E9C86; --pn-hair:#DBD7C5;
  --pn-on-dark:#F5F2E8; --pn-edge:rgba(139,137,113,.42);
  --pn-panel:rgba(139,137,113,.09); --pn-paper:#FBFAF5;
  --pn-s-hero:66px; --pn-s-section:40px; --pn-s-statement:26px; --pn-s-quote:19px;
  --pn-w-body-lg:17.5px; --pn-w-body:15px; --pn-w-body-sm:13px;
  --pn-w-caption:11.5px; --pn-w-meta:10px;
  --pn-sm:16px; --pn-md:24px; --pn-lg:36px; --pn-xl:56px; --pn-sec:88px;
}
@media (max-width:1100px){ :root{
  --pn-s-hero:clamp(36px,6vw,66px); --pn-s-section:clamp(27px,3.6vw,40px);
  --pn-s-statement:clamp(20px,2.7vw,26px); --pn-sec:60px; --pn-xl:40px; } }
*{box-sizing:border-box;}
body{ margin:0; background:var(--pn-ground); color:var(--pn-body);
  font-family:'Work Sans',system-ui,sans-serif; font-size:var(--pn-w-body);
  line-height:1.6; -webkit-font-smoothing:antialiased; }
.wrap{ max-width:1060px; margin:0 auto; padding:0 28px; }
h1,h2,h3,.serif{ font-family:'Fraunces',Georgia,serif; font-weight:400;
  color:var(--pn-voice); letter-spacing:-.015em; }
p{ margin:0 0 15px; max-width:60ch; }
.eyebrow{ font-size:var(--pn-w-meta); font-weight:600; letter-spacing:.2em;
  text-transform:uppercase; color:var(--pn-stone); margin:0 0 14px; }

.pv-bar{ background:var(--pn-voice); color:var(--pn-on-dark); padding:13px 0;
  font-size:var(--pn-w-body-sm); }
.pv-bar .wrap{ display:flex; gap:16px; align-items:baseline; flex-wrap:wrap; }
.pv-bar strong{ font-size:var(--pn-w-meta); font-weight:600; letter-spacing:.2em;
  text-transform:uppercase; }
.pv-bar span{ opacity:.82; }

.hero{ padding:var(--pn-xl) 0 var(--pn-lg); }
.brand{ font-family:'Fraunces',serif; font-size:var(--pn-w-caption); letter-spacing:.34em;
  text-transform:uppercase; color:var(--pn-stone); margin-bottom:var(--pn-md); }
h1{ font-size:var(--pn-s-hero); line-height:1.02; margin:0 0 var(--pn-md); max-width:15ch; }
.lede{ font-size:var(--pn-w-body-lg); line-height:1.5; max-width:48ch;
  color:var(--pn-fact); margin:0; }

.journey{ background:var(--pn-voice); color:var(--pn-on-dark); padding:var(--pn-lg) 0; }
.journey .eyebrow{ color:rgba(245,242,232,.55); margin-bottom:10px; }
.jrow{ display:flex; flex-wrap:wrap; gap:0; }
.jstep{ flex:1 1 132px; padding:10px 14px 10px 0; min-width:118px; }
.jstep + .jstep{ border-left:1px solid rgba(245,242,232,.2); padding-left:14px; }
.jstep b{ display:block; font-family:'Fraunces',serif; font-weight:400;
  font-size:var(--pn-s-quote); color:var(--pn-on-dark); margin-bottom:3px; }
.jstep span{ font-size:var(--pn-w-body-sm); color:rgba(245,242,232,.7); line-height:1.4; }
.jstep.last b{ color:#CBD8BE; }

section{ padding:var(--pn-sec) 0 0; }
h2{ font-size:var(--pn-s-section); line-height:1.12; margin:0 0 var(--pn-md); max-width:22ch; }

.demo-intro{ display:flex; justify-content:space-between; align-items:flex-end;
  gap:var(--pn-md); flex-wrap:wrap; margin-bottom:var(--pn-md); }
.illus-tag{ font-size:var(--pn-w-meta); font-weight:600; letter-spacing:.16em;
  text-transform:uppercase; color:var(--pn-stone);
  border:1px solid var(--pn-edge); border-radius:2px; padding:5px 10px; white-space:nowrap; }
.screen{ background:var(--pn-paper); border:1px solid var(--pn-hair); border-radius:5px;
  overflow:hidden; box-shadow:0 1px 0 rgba(22,25,15,.03), 0 18px 44px -28px rgba(22,25,15,.34); }
.screen-chrome{ display:flex; align-items:center; gap:10px; padding:11px 16px;
  border-bottom:1px solid var(--pn-hair); background:var(--pn-ground); }
.dot{ width:8px; height:8px; border-radius:50%; background:var(--pn-hair); }
.screen-url{ font-size:var(--pn-w-caption); color:var(--pn-meta); letter-spacing:.02em; }
.credit-line{ font-size:var(--pn-w-caption); color:var(--pn-stone);
  border-top:1px solid var(--pn-hair); padding:12px 16px; background:var(--pn-ground); }

/* the live PlotNua surface, hosted inside the frame */
.pn-stage{ background:var(--paper); color:var(--ink);
  font-family:'Work Sans',system-ui,sans-serif; font-size:15px; line-height:1.6;
  padding:22px 26px 34px; }
@media (max-width:820px){ .pn-stage{ padding:16px 16px 26px; } }
.pn-stage-top{ display:flex; justify-content:flex-end; margin-bottom:26px; }
.pn-stage p{ max-width:none; margin:0; }
.pn-stage .results-hero-inner{ margin-bottom:0; }
/* The production field goes full-bleed on a phone; contained inside a framed
   screenshot. Preview scope only — the production rule is untouched. */
.pn-stage .results-hero-inner.is-fieldonly{ margin-left:0; margin-right:0; border-radius:6px; }
@media (min-width:720px){
  .pn-stage .results-hero-inner{ align-items:stretch; }
  .pn-stage .results-hero-media{ aspect-ratio:auto; min-height:320px; }
  .pn-stage .results-hero-inner.is-fieldonly .match-card-open-myplot-link{
    grid-column:2; justify-self:start; }
}
.pn-stage .results-hero-media{ display:flex; }
.pn-stage .results-hero-media img{ width:100%; height:100%; object-fit:cover; display:block; }
.pn-stage .results-hero-budget-note{ margin-top:14px; }
.pn-stage .match-card-open-myplot-link{ align-self:flex-start; }
.pn-stage .hero-secondary{ flex-wrap:wrap; }
.pn-stage .hero-secondary .hero-secondary-dot{ display:none; }
.pn-stage .hero-secondary .hero-secondary-link + .hero-secondary-link{ flex-basis:100%; }

/* Imagery state C — a purposeful held space, never an apology. */
.pn-photo-slot{ flex:1 1 auto; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:10px; text-align:center; padding:24px;
  background:
    radial-gradient(120% 90% at 18% 8%, rgba(255,253,246,.85) 0%, rgba(255,253,246,0) 60%),
    linear-gradient(158deg, #E9E3D3 0%, #DED7C3 56%, #D2CBB4 100%);
  box-shadow:inset 0 0 0 1px rgba(31,59,46,.09); }
.pn-photo-slot b{ font-family:'Work Sans',sans-serif; font-size:11px; font-weight:600;
  letter-spacing:.2em; text-transform:uppercase; color:var(--accent); }
.pn-photo-slot span{ font-size:13px; line-height:1.5; color:var(--soft); max-width:30ch; }

/* Verified supplier facts, read as rows rather than one dense run. */
.pn-facts{ list-style:none; margin:20px 0 0; padding:16px 0 0;
  border-top:1px solid rgba(31,59,46,.10); display:grid; gap:9px; }
.pn-facts li{ display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 10px;
  font-size:13.5px; line-height:1.45; }
.pn-facts b{ color:var(--ink); font-weight:600; letter-spacing:.005em; }
.pn-facts span{ color:var(--soft); }
@media (max-width:719px){
  .pn-facts{ gap:11px; }
  .pn-facts li{ flex-direction:column; gap:1px; }
}

/* PRODUCT-LED ONLY — what has not been established, stated plainly. */
.pn-open{ margin-top:22px; padding:16px 18px; border:1px solid rgba(31,59,46,.14);
  border-radius:4px; background:rgba(139,137,113,.07); }
.pn-open b{ display:block; font-size:11px; font-weight:600; letter-spacing:.16em;
  text-transform:uppercase; color:var(--soft); margin-bottom:8px; }
.pn-open ul{ margin:0; padding:0; list-style:none; display:grid; gap:6px; }
.pn-open li{ font-size:13px; line-height:1.45; color:var(--ink); padding-left:16px; position:relative; }
.pn-open li::before{ content:'\2013'; position:absolute; left:0; color:var(--soft); }

.why{ display:grid; grid-template-columns:repeat(3,1fr); gap:var(--pn-md); margin-top:var(--pn-md); }
@media (max-width:820px){ .why{ grid-template-columns:1fr; } }
.why-c{ border-top:2px solid var(--pn-voice); padding-top:14px; }
.why-c b{ display:block; font-size:var(--pn-w-meta); font-weight:600; letter-spacing:.16em;
  text-transform:uppercase; color:var(--pn-voice); margin-bottom:8px; }
.why-c span{ font-size:var(--pn-w-body-sm); color:var(--pn-body); }

.close-statement{ font-family:'Fraunces',serif; font-size:var(--pn-s-statement);
  line-height:1.32; color:var(--pn-voice); max-width:32ch; margin:0 0 var(--pn-md); }

footer{ margin-top:var(--pn-sec); padding:var(--pn-lg) 0 var(--pn-sec);
  border-top:1px solid var(--pn-hair); font-size:var(--pn-w-body-sm); color:var(--pn-stone); }
'''

CONFIG_A = '''<!--
  ════════════════════════════════════════════════════════════════════
  PLOTNUA SUPPLIER PREVIEW — VARIANT A · PRODUCT-LED
  Use when a specific, verified product carries the preview.
  Read SUPPLIER-PREVIEW-SYSTEM-V1.md before filling this in.

  REPLACE EVERY {{TOKEN}}. Delete nothing structural.
  Every {{VERIFIED_*}} value must come from the first-party evidence pack.
  UNKNOWN STAYS UNKNOWN — move it to the "Still to establish" list.

    {{SUPPLIER_NAME}}        official name, exactly as they write it
    {{PRODUCT_NAME}}         the maker's own product name
    {{PROPOSITION}}          the PlotNua hero line (rarely changed)
    {{LEDE}}                 one supporting line
    {{DEMO_HEADING}}         e.g. "Imagine a homeowner reaching X like this."
    {{DEMO_LEDE}}            one line, no apology
    {{VERIFIED_PRICE}}       as published, with its own currency
    {{VERIFIED_PRICE_BASIS}} e.g. "including fitting", "as published, ex VAT"
    {{VERIFIED_FACT_N}}      label + value, first-party only
    {{PERSONALISATION}}      MUST trace to a real PlotNua capability
    {{THINGS_TO_CHECK}}      one honest line
    {{STILL_TO_ESTABLISH_N}} what PlotNua has NOT established
    {{IMAGE_*}}              imagery state A only — see the block below
    {{WHY_*}}                the commercial difference, in their language
    {{CLOSING_PROPOSITION}}  ONE interesting question
  ════════════════════════════════════════════════════════════════════
-->'''

CONFIG_B = CONFIG_A.replace('VARIANT A · PRODUCT-LED',
                            'VARIANT B · PROVIDER-LED').replace(
  'Use when a specific, verified product carries the preview.',
  'Use when the relationship is with a provider or category, not one product.').replace(
  '    {{PRODUCT_NAME}}         the maker\'s own product name',
  '    {{OFFER_NAME}}           the category/offering, in their words').replace(
  '''    {{STILL_TO_ESTABLISH_N}} what PlotNua has NOT established
    {{IMAGE_*}}              imagery state A only — see the block below''',
  '''    {{PHOTO_SLOT_LINE}}      what the held image panel says (state C)''')

HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<title>PlotNua &mdash; a short introduction for {{SUPPLIER_NAME}}</title>
<meta name="description" content="Private, unlisted introduction prepared for {{SUPPLIER_NAME}}. Not a public PlotNua page.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700&family=Work+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>'''

SHELL_TOP = '''</style>
</head>
<body>

<div class="pv-bar"><div class="wrap">
  <strong>Private preview</strong>
  <span>Prepared for {{SUPPLIER_NAME}}</span>
</div></div>

<div class="wrap">
  <header class="hero">
    <div class="brand">PlotNua</div>
    <h1>{{PROPOSITION}}</h1>
    <p class="lede">{{LEDE}}</p>
  </header>
</div>

<!-- FROZEN — the real PlotNua homeowner journey. Change only if the
     platform architecture itself changes. -->
<div class="journey">
  <div class="wrap">
    <div class="eyebrow">How a homeowner moves through it</div>
    <div class="jrow">
      <div class="jstep"><b>Discover</b><span>See what a property like theirs could do.</span></div>
      <div class="jstep"><b>Check</b><span>What would actually work in their garden.</span></div>
      <div class="jstep"><b>Explore</b><span>Look at real options in detail.</span></div>
      <div class="jstep"><b>Compare</b><span>Weigh them up side by side.</span></div>
      <div class="jstep"><b>Decide</b><span>Settle on what to pursue.</span></div>
      <div class="jstep last"><b>Connect</b><span>When ready, connect with a provider.</span></div>
    </div>
  </div>
</div>

<div class="wrap">

<!-- ═══ THE DEMONSTRATION — MANDATORY ══════════════════════════════
     Never ship a supplier preview that is mainly explanatory prose.
     Everything inside .pn-stage is genuine production PlotNua markup
     and CSS. Do not invent a mock interface. ═══════════════════════ -->
<section>
  <div class="demo-intro">
    <h2 style="margin:0">{{DEMO_HEADING}}</h2>
    <span class="illus-tag">Illustrative preview</span>
  </div>
  <p style="margin-bottom:var(--pn-lg)">{{DEMO_LEDE}}</p>

  <div class="screen">
    <div class="screen-chrome">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      <span class="screen-url">plotnua.ie/your-plot</span>
    </div>

    <div class="pn-stage">
      <div class="pn-stage-top">
        <button type="button" class="my-plot-access">__MARK_PILL__<span class="my-plot-access-label"><span class="my-plot-access-title">My Plot</span><span class="my-plot-access-count">1 option saved</span></span><span class="my-plot-access-chevron" aria-hidden="true">&rarr;</span></button>
      </div>

      <div class="results-hero-inner">
'''

MEDIA_A = '''        <!-- IMAGERY STATE A — AUTHORISED. Credit is mandatory and the
             image must be served from the supplier's own domain, unmodified.
             If permission has NOT been given in writing, delete this block and
             use the state-C panel from the provider-led template instead. -->
        <div class="results-hero-media">
          <img src="{{IMAGE_URL}}" alt="{{IMAGE_ALT}}" loading="lazy">
        </div>
'''

MEDIA_B = '''        <!-- IMAGERY STATE C — NOT YET AUTHORISED. A purposeful held space
             that shows the supplier where their photography would sit. Never
             substitute their pictures because the page is private. -->
        <div class="results-hero-media">
          <div class="pn-photo-slot">
            <b>Your project photography here</b>
            <span>{{PHOTO_SLOT_LINE}}</span>
          </div>
        </div>
'''

def body_mid(name_token, open_block):
    return '''        <div class="results-hero-body">
          <h2 class="results-hero-name">''' + name_token + '''</h2>
          <div class="results-hero-org">{{SUPPLIER_NAME}}</div>

          <div class="results-hero-price-row">
            <span class="results-hero-price">{{VERIFIED_PRICE}}</span>
            <span class="results-hero-area">{{VERIFIED_PRICE_BASIS}}</span>
          </div>

          <!-- PERSONALISATION GUARDRAIL. Anything shown here must trace to a
               real PlotNua capability. PlotNua does NOT capture or infer
               garden aspect, orientation or surface, so lines such as
               "south-facing patio" are forbidden however well they read. -->
          <section class="prop-confirm is-in-hero" aria-label="Your property">
            <p class="prop-confirm-place">Your property &middot; {{HOMEOWNER_LOCALITY}}</p>
          </section>

          <p class="results-hero-editorial">{{PERSONALISATION}}</p>

          <ul class="pn-facts">
            <li><b>{{VERIFIED_FACT_1_LABEL}}</b><span>{{VERIFIED_FACT_1_VALUE}}</span></li>
            <li><b>{{VERIFIED_FACT_2_LABEL}}</b><span>{{VERIFIED_FACT_2_VALUE}}</span></li>
            <li><b>{{VERIFIED_FACT_3}}</b></li>
            <li><b>{{VERIFIED_FACT_4}}</b></li>
            <li><b>{{VERIFIED_FACT_5}}</b></li>
          </ul>

          <div class="results-hero-budget-note">Things to check: {{THINGS_TO_CHECK}}</div>
''' + open_block + '''
          <div class="match-card-actions">
            <button type="button" class="match-card-save-primary is-saved" aria-pressed="true">__MARK_SAVE__ Saved to My Plot &#10003;</button>
          </div>
          <button type="button" class="match-card-open-myplot-link">Open My Plot &rarr;</button>

          <div class="hero-secondary">
            <a class="hero-secondary-link" href="#">Ask PlotNua</a>
            <span class="hero-secondary-dot">&middot;</span>
            <a class="hero-secondary-link" href="#">Explore with {{SUPPLIER_SHORT}} &rarr;</a>
          </div>
        </div>
      </div>
    </div>
'''

OPEN_BLOCK = '''
          <!-- PRODUCT-LED ONLY. State gaps as plainly as facts. Delete any
               line that has since been established; never soften one. -->
          <div class="pn-open">
            <b>Still to establish</b>
            <ul>
              <li>{{STILL_TO_ESTABLISH_1}}</li>
              <li>{{STILL_TO_ESTABLISH_2}}</li>
              <li>{{STILL_TO_ESTABLISH_3}}</li>
            </ul>
          </div>
'''

CREDIT_A = '''    <div class="credit-line">{{IMAGE_CREDIT}} &mdash; used with written permission from {{IMAGE_PERMISSION_SOURCE}}, unmodified. Product information taken from {{SUPPLIER_SHORT}}&rsquo;s own published material.</div>
'''

def shell_end(credit):
    return credit + '''  </div>
</section>

<!-- WHY THIS COULD BE USEFUL — what PlotNua adds BEFORE the homeowner
     arrives. Keep three points. Rewrite them in the supplier's own terms
     if the defaults do not fit; do not expand the section. -->
<section>
  <h2>Why this could be useful</h2>
  <div class="why">
    <div class="why-c"><b>{{WHY_1_LABEL}}</b><span>{{WHY_1_TEXT}}</span></div>
    <div class="why-c"><b>{{WHY_2_LABEL}}</b><span>{{WHY_2_TEXT}}</span></div>
    <div class="why-c"><b>{{WHY_3_LABEL}}</b><span>{{WHY_3_TEXT}}</span></div>
  </div>
</section>

<!-- THE ENDING — ONE commercially interesting proposition or question.
     Do not summarise the page again. Do not define PlotNua as ending at
     referral, and do not claim any connection, attribution or commercial
     mechanism is operational. -->
<section>
  <h2>What we&rsquo;d like to explore</h2>
  <p class="close-statement">{{CLOSING_PROPOSITION}}</p>
  <p>{{CLOSING_SUPPORT}}</p>
</section>

<footer>
  <p>Private preview prepared for {{SUPPLIER_NAME}} &middot; {{DATE}}</p>
</footer>

</div>
</body>
</html>
'''

def build(variant):
    cfg    = CONFIG_A if variant == 'product' else CONFIG_B
    media  = MEDIA_A if variant == 'product' else MEDIA_B
    nametok = '{{PRODUCT_NAME}}' if variant == 'product' else '{{OFFER_NAME}}'
    openb  = OPEN_BLOCK if variant == 'product' else ''
    credit = CREDIT_A if variant == 'product' else ''
    html = (HEAD + PAGE_CSS + "\n" + UI_KIT + "\n" + SHELL_TOP
            + media + body_mid(nametok, openb) + shell_end(credit))
    html = html.replace('<body>', '<body>\n' + cfg, 1)
    html = html.replace('__MARK_PILL__', mark('pnMarkClipPill'))
    html = html.replace('__MARK_SAVE__', mark('pnMarkClipSave'))
    return html

files = {'template-product-led.html': build('product'),
         'template-provider-led.html': build('provider')}

# ── guards ───────────────────────────────────────────────────────────
SUPPLIER_REMNANTS = ['triq','briq','superior','pergola','klerner','neringa',
                     'shomera','2,500','22,700','aluminium','dublin 6','christian']
for fn, h in files.items():
    css = h.split('<style>', 1)[1].split('</style>', 1)[0]
    markup = h.split('</style>', 1)[1]
    if css.count('{') != css.count('}'): die(fn + ': brace imbalance')
    if css.count('/*') != css.count('*/'): die(fn + ': unterminated comment')
    for s in ['.my-plot-access{', '.match-card-save-primary{', '.pn-mark-heart{',
              '.results-hero-inner{', '.match-card-open-myplot-link{',
              '.hero-secondary{', '.prop-confirm.is-in-hero{', '.results-hero-media{']:
        if s not in css: die(fn + ': missing production rule ' + s)
    if markup.count('pn-mark-heart is-plot-active') != 2: die(fn + ': mark count')
    for r in SUPPLIER_REMNANTS:
        if r in markup.lower(): die(fn + ': supplier remnant "' + r + '"')
    for m in ['noindex','nofollow','noarchive','nosnippet','noimageindex']:
        if m not in h: die(fn + ': missing robots directive ' + m)
    for t in ['{{SUPPLIER_NAME}}','{{PROPOSITION}}','{{DEMO_HEADING}}','{{PERSONALISATION}}',
              '{{CLOSING_PROPOSITION}}','{{VERIFIED_PRICE}}','{{WHY_1_LABEL}}']:
        if t not in markup: die(fn + ': missing token ' + t)
    if 'Discover' not in markup or 'Connect' not in markup: die(fn + ': journey band missing')
    if 'Illustrative preview' not in markup: die(fn + ': illustrative label missing')
    if markup.lower().count('illustrative') != 1: die(fn + ': illustrative status repeated')
    for banned in ['stays with the provider','everything that follows','nothing here is real',
                   'we have not agreed','does not exist yet','no partnership exists']:
        if banned in markup.lower(): die(fn + ': banned defensive phrasing "' + banned + '"')
    if '__MARK' in h: die(fn + ': unsubstituted mark token')

if '<img' in files['template-provider-led.html'].split('</style>',1)[1]:
    die('provider-led template must carry no <img>')
if '<img' not in files['template-product-led.html']:
    die('product-led template lost its authorised-imagery slot')

os.makedirs(OUT, exist_ok=True)
for fn, h in files.items():
    open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(h)
    print('WROTE', fn, len(h), hashlib.sha256(h.encode()).hexdigest()[:16])
