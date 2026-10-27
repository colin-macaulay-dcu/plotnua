#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refresh-ui-kit.py — PlotNua Supplier Preview System v2.0 (27 Oct 2026)

Regenerates supplier-preview-system/template-*.html from LIVE production code,
so a preview can never drift from the real interface or the real identity.

    python3 supplier-preview-system/refresh-ui-kit.py           write both templates
    python3 supplier-preview-system/refresh-ui-kit.py --check   compare, write nothing

WHAT CHANGED IN v2 (founder instruction, 27 Oct 2026)
  v1 lifted fixed LINE RANGES of your-plot.html into a light preview shell.
  Those ranges went stale (production's later Results typography was never in
  the kit) and the shell predated the dark identity. v2 builds both templates
  from four live sources, with no line numbers anywhere:

  1. THE PAGE AROUND THE DEMONSTRATION — PlotNua's approved premium dark design:
       assets/identity/pn-identity.css           tokens --p4-*, type, focus
       assets/identity/pn-premium-discovery.css  the Premium Discovery system
     inlined verbatim, activated as on the live Discoveries:
       <body class="pn-id pn-id--dark pn-sp">
     The shell's own CSS below uses only those tokens.

  2. THE DEMONSTRATION — production Your Plot Results, as it ships:
       your-plot.html, its one <style> block in <head>
       assets/identity/pn-your-plot.css, the live Batch 5C dark skin
     in production's cascade order (skin first, page second), re-scoped from
     the page to a .pn-yp wrapper inside the demo with ONE constant
     specificity offset, so the cascade between them is unchanged, and wrapped
     in production's own chain: #screen-match-results > .match-results-panel
     > #matchPrimary.results-hero > .results-hero-inner. The demo therefore
     matches production computed style; prove-results-fidelity.mjs proves it
     against the real your-plot.html.

  3. THE MARKUP — supplier-preview-system/kit/*.html: the Results hero (the
     PREVIEW-IDENTITY-001 band, both variants), the My Plot pill, the gallery
     script and the product-led credit line, exactly as in the v1.x templates.
     The brand-mark paths are re-checked against production on every run.

COMPATIBILITY WITH EXISTING BUILDERS
  Every {{TOKEN}}, and every anchor builders use, is unchanged: the instruction
  comment, the hero header, the FROZEN journey band, '  <div class="screen">',
  '<div class="pn-stage">', '      <div class="results-hero-inner">', the
  '<!-- WHY THIS COULD BE USEFUL' anchor, the closing heading, '<footer>\\n',
  .pn-open, .credit-line and the state-C slot. ONE anchor changes by
  necessity: the production chain closes between the hero and the end of the
  stage, so the old demo ending '\\n    </div>\\n  </div>\\n</section>' is now
  preceded by '      </div></div></section></div>'. Builders that slice up to
  the old ending REFUSE (loudly) and are migrated one at a time when that
  supplier is next worked on (§10.2 point 5). No built supplier page is
  touched by this script: it writes only the two templates.

Every guard aborts the run; nothing partial is written.
"""

import hashlib
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(REPO, 'supplier-preview-system')
KIT = os.path.join(HERE, 'kit')
CHECK = '--check' in sys.argv


def die(m):
    sys.exit('GUARD FAILED: ' + m)


def read(*p):
    return open(os.path.join(*p), encoding='utf-8').read()


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]


# ── sources ──────────────────────────────────────────────────────────────
YP_HTML = read(REPO, 'your-plot.html')
_head = YP_HTML.split('</head>')[0]
_blocks = re.findall(r'<style>\n(.*?)\n</style>', _head, re.S)
if len(_blocks) != 1:
    die('your-plot.html no longer has exactly one <style> block in <head>')
PROD_RAW = _blocks[0]
SKIN_RAW = read(REPO, 'assets/identity/pn-your-plot.css')
ID_CSS = read(REPO, 'assets/identity/pn-identity.css')
PD_CSS = read(REPO, 'assets/identity/pn-premium-discovery.css')
# Rules verbatim; comments stripped. The design files' comments name the
# pages they were built with (e.g. supplier pages), and builders rightly
# refuse any other supplier's name anywhere in a preview's source.
ID_CSS_SRC, PD_CSS_SRC = ID_CSS, PD_CSS
ID_CSS = re.sub(r'/\*.*?\*/', '', ID_CSS, flags=re.S)
PD_CSS = re.sub(r'/\*.*?\*/', '', PD_CSS, flags=re.S)
# Previews carry the Premium Discovery RULES under their own scope class,
# body.pn-sp, so they never register as Premium pages: the Premium page
# registry (atlas-tools/premium_pages.py, identity guard I13) stays exact and
# supplier previews stay outside the public page system.
if PD_CSS.count('body.pn-id.pn-pd') < 100 or re.search(r'(?<!body\.pn-id)\.pn-pd\b', PD_CSS):
    die('pn-premium-discovery.css is no longer scoped only by body.pn-id.pn-pd')
PD_CSS = PD_CSS.replace('body.pn-id.pn-pd', 'body.pn-id.pn-sp')
if 'body.pn-id.pn-sp' not in PD_CSS or '--p4-anth' not in ID_CSS:
    die('the premium dark design files no longer carry their scope/tokens')
if 'data-pn-skin="your-plot"' not in _head and 'data-pn-skin="your-plot"' not in YP_HTML[:4000]:
    die('your-plot.html no longer applies the Your Plot skin; the demo would '
        'not match production')

HERO = {'provider': read(KIT, 'hero-provider.html'),
        'product': read(KIT, 'hero-product.html')}
PILL = read(KIT, 'pill.html')
GALLERY_JS = read(KIT, 'gallery-script.html')
CREDIT_A = read(KIT, 'credit-product.html')

for n in ('PN_P_PATH', 'PN_HOUSE_PATH', 'PN_HEART_PATH'):
    m = re.search(r'const ' + n + r"\s*=\s*'([^']*)'", YP_HTML)
    if not m:
        die('missing ' + n + ' in production')
    for k, frag in (('pill', PILL), ('provider hero', HERO['provider']),
                    ('product hero', HERO['product'])):
        if m.group(1) not in frag:
            die('the brand mark in the kit %s no longer matches production %s'
                % (k, n))


# ── scoping (production cascade preserved) ───────────────────────────────
W_BASE = '.pn-yp'            # production page rules gain (0,1,0)
W_SKIN = 'div.pn-yp.pn-yp'   # skin: html[attr] (0,1,1) plus the same (0,1,0)


def _split(prelude):
    out, depth, cur, q = [], 0, '', None
    for ch in prelude:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in '"\'':
            q = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def map_base(sel):
    if sel in (':root', 'html', 'body', 'html body'):
        return W_BASE
    if sel == '*':
        return W_BASE + ' *'
    m = re.match(r'(?:html\s+)?body(?=[\s>+~]|$)', sel) or \
        re.match(r'html(?=[\s>+~]|$)', sel)
    if m:
        return W_BASE + sel[m.end():]
    m = re.match(r'(html|body|:root)(?=[.#\[:])', sel)
    if m:
        return W_BASE + sel[m.end():]
    return W_BASE + ' ' + sel


def map_skin(sel):
    head = 'html[data-pn-skin="your-plot"]'
    if not sel.startswith(head):
        die('a skin selector does not start with the html scope: %r' % sel)
    rest = sel[len(head):]
    m = re.match(r'((?::not\(#[^)]+\))*)\s+body(?=[\s>+~.:#\[]|$)', rest)
    if m:
        return W_SKIN + m.group(1) + rest[m.end():]
    return W_SKIN + rest


def scope_css(css, mapper):
    try:
        import tinycss2
    except ImportError:
        die('tinycss2 is required: pip install tinycss2')
    n = [0]

    def walk(rules):
        parts = []
        for r in rules:
            if r.type == 'qualified-rule':
                sels = _split(tinycss2.serialize(r.prelude))
                parts.append(', '.join(mapper(s) for s in sels) + '{'
                             + tinycss2.serialize(r.content) + '}')
                n[0] += 1
            elif r.type == 'at-rule':
                kw = r.lower_at_keyword
                if kw in ('media', 'supports') and r.content is not None:
                    inner = tinycss2.parse_rule_list(
                        r.content, skip_comments=True, skip_whitespace=True)
                    parts.append('@%s %s{%s}' % (
                        kw, tinycss2.serialize(r.prelude).strip(),
                        '\n'.join(walk(inner))))
                elif kw in ('keyframes', '-webkit-keyframes', 'font-face'):
                    parts.append(tinycss2.serialize([r]))
                elif kw == 'import':
                    continue          # the template loads the same fonts
                else:
                    die('unhandled at-rule @%s' % kw)
            elif r.type == 'error':
                die('CSS did not parse: %s' % r.message)
        return parts

    out = walk(tinycss2.parse_stylesheet(css, skip_comments=True,
                                         skip_whitespace=True))
    return '\n'.join(out), n[0]


SKIN_CSS, N_SKIN = scope_css(SKIN_RAW, map_skin)
PROD_CSS, N_PROD = scope_css(PROD_RAW, map_base)
if 'data-pn-skin' in SKIN_CSS:
    die('an html-scoped skin selector survived the re-scope')
if N_PROD < 1500 or N_SKIN < 200:
    die('the production stylesheets look truncated (%d / %d rules)'
        % (N_PROD, N_SKIN))


# ── the preview shell: premium dark design, approved tokens only ─────────
SHELL_CSS = r'''
/* ══ PREVIEW SHELL — the page AROUND the demonstration ═══════════════════
   Premium Discovery tokens (--p4-*, --pd-*) only; no new palette. Every
   selector is anchored to a shell container, so none of it can reach the
   production interface inside .pn-yp. */
body.pn-id.pn-sp{ margin:0; color:var(--p4-lime); font-family:var(--p4-sans);
  font-size:17px; line-height:1.65; -webkit-font-smoothing:antialiased; }
body.pn-sp .wrap{ max-width:var(--pd-max); margin:0 auto; padding:0 clamp(16px,3vw,40px); box-sizing:border-box; }

body.pn-sp .pv-bar{ background:var(--p4-anth); border-bottom:1px solid var(--p4-line); }
body.pn-sp .pv-bar > .wrap{ display:flex; align-items:center; gap:10px 22px; flex-wrap:wrap; padding-top:16px; padding-bottom:16px; }
body.pn-sp .pv-bar .pv-word{ font-family:var(--p4-serif); font-size:30px; line-height:1; color:var(--p4-ivory); letter-spacing:-.005em; }
body.pn-sp .pv-bar strong{ font-family:var(--p4-sans); font-weight:700; font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--p4-bronze-text); }
body.pn-sp .pv-bar span:not(.pv-word){ font-size:15px; color:var(--p4-stone); }

body.pn-sp .wrap > .hero{ padding:clamp(56px,8vw,112px) 0 0; }
body.pn-sp .wrap > .hero .brand{ font-family:var(--p4-sans); font-weight:700; font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--p4-bronze-text); margin:0 0 18px; }
body.pn-sp .wrap > .hero h1{ font-size:clamp(40px,5.4vw,80px); line-height:.98; margin:0 0 22px; max-width:16ch; text-wrap:balance; }
body.pn-sp .wrap > .hero .lede{ font-size:clamp(19px,1.45vw,22px); line-height:1.55; color:var(--p4-ivory); max-width:52ch; margin:0; }

body.pn-sp .journey{ background:var(--p4-earth); margin-top:clamp(56px,8vw,112px); padding:clamp(40px,5vw,72px) 0; }
body.pn-sp .journey .eyebrow{ font-family:var(--p4-sans); font-weight:700; font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--p4-bronze-text); margin:0 0 22px; }
body.pn-sp .journey .jrow{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:0; background:var(--pd-card); border:var(--pd-edge); border-radius:var(--pd-r); box-shadow:var(--pd-shadow); padding:clamp(20px,2.4vw,32px); }
body.pn-sp .journey .jstep{ padding:4px clamp(12px,1.4vw,20px); border-left:1px solid var(--p4-line); min-width:0; }
body.pn-sp .journey .jstep:first-child{ border-left:0; padding-left:0; }
body.pn-sp .journey .jstep b{ display:block; font-family:var(--p4-serif); font-weight:400; font-size:clamp(22px,1.9vw,28px); line-height:1.1; color:var(--p4-ivory); margin:0 0 8px; }
body.pn-sp .journey .jstep span{ display:block; font-size:15px; line-height:1.5; color:var(--p4-stone); }
body.pn-sp .journey .jstep.last b{ color:var(--p4-terra-text); }

body.pn-sp .wrap > section{ padding:clamp(56px,8vw,112px) 0 0; }
body.pn-sp .wrap > section > h2{ font-size:clamp(34px,4vw,58px); line-height:1.04; margin:0 0 22px; max-width:22ch; text-wrap:balance; }
body.pn-sp .wrap > section > p{ max-width:62ch; margin:0 0 16px; color:var(--p4-lime); }
body.pn-sp .wrap > section > h3{ font-size:clamp(25px,2.2vw,32px); line-height:1.12; margin:28px 0 12px; }

body.pn-sp .demo-intro{ display:flex; justify-content:space-between; align-items:flex-end; gap:16px 24px; flex-wrap:wrap; margin:0 0 18px; }
body.pn-sp .demo-intro > h2{ font-size:clamp(34px,4vw,58px); line-height:1.04; margin:0; max-width:20ch; text-wrap:balance; }
body.pn-sp .illus-tag{ font-family:var(--p4-sans); font-weight:700; font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--p4-terra-text); border:1px solid var(--p4-line2); border-radius:999px; padding:8px 16px; white-space:nowrap; }

body.pn-sp .screen{ margin-top:clamp(20px,3vw,36px); border-radius:var(--pd-r); overflow:hidden; border:var(--pd-edge); box-shadow:var(--pd-shadow-hi); background:var(--p4-anth); }
body.pn-sp .screen > .screen-chrome{ display:flex; align-items:center; gap:9px; padding:13px 18px; background:var(--pd-card); border-bottom:1px solid var(--p4-line); }
body.pn-sp .screen-chrome .dot{ width:9px; height:9px; border-radius:50%; background:var(--p4-line2); }
body.pn-sp .screen-chrome .screen-url{ margin-left:8px; font-size:13px; color:var(--p4-stone); letter-spacing:.02em; }
body.pn-sp .screen > .credit-line{ margin:0; padding:14px 20px; font-size:13px; line-height:1.55; color:var(--p4-stone); background:var(--pd-card); border-top:1px solid var(--p4-line); }
body.pn-sp .wrap > p.credit-line, body.pn-sp .wrap > section > p.credit-line, body.pn-sp .wrap > .credit-line{ font-size:14px; line-height:1.6; color:var(--p4-stone); margin:clamp(32px,4vw,48px) 0 0; padding-top:20px; border-top:1px solid var(--p4-line); max-width:80ch; }
body.pn-sp .credit-line a{ color:var(--p4-terra-text); text-decoration:none; border-bottom:1px solid rgba(207,133,102,.55); }
body.pn-sp .credit-line a:hover{ color:var(--p4-ivory); border-bottom-color:var(--p4-ivory); }

/* the framed production surface. .pn-stage sits outside .pn-yp; the real
   Results padding and ground come from #screen-match-results inside it. */
body.pn-sp .screen > .pn-stage{ background:var(--p4-anth); padding:0; }

/* .pn-open — preview-only "Still to establish" / question panel */
body.pn-sp .pn-open{ margin-top:22px; padding:clamp(20px,2.4vw,30px); background:var(--pd-card); border:var(--pd-edge); border-radius:var(--pd-r-sm); box-shadow:var(--pd-shadow); }
body.pn-sp .pn-open > b{ display:block; font-family:var(--p4-sans); font-size:12px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--p4-bronze-text); margin:0 0 12px; }
body.pn-sp .pn-open ul{ margin:0; padding:0; list-style:none; display:grid; gap:0; }
body.pn-sp .pn-open li{ font-size:16px; line-height:1.6; color:var(--p4-lime); padding:12px 0 12px 20px; position:relative; border-top:1px solid var(--p4-line); }
body.pn-sp .pn-open li:first-child{ border-top:0; padding-top:0; }
body.pn-sp .pn-open li::before{ content:'\2013'; position:absolute; left:0; color:var(--p4-terra-text); }
body.pn-sp .pn-open li b{ color:var(--p4-ivory); font-weight:600; }

body.pn-sp .why{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:clamp(20px,2.4vw,40px); background:var(--pd-card); border:var(--pd-edge); border-radius:var(--pd-r); box-shadow:var(--pd-shadow); padding:var(--pd-pad); }
body.pn-sp .why-c{ border-top:1px solid var(--p4-line2); padding-top:20px; min-width:0; }
body.pn-sp .why-c b{ display:block; font-family:var(--p4-sans); font-size:12px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--p4-terra-text); margin:0 0 10px; }
body.pn-sp .why-c span{ display:block; font-size:16px; line-height:1.6; color:var(--p4-stone); }

body.pn-sp .wrap > section > .close-statement{ font-family:var(--p4-serif); font-size:clamp(26px,2.6vw,38px); line-height:1.15; color:var(--p4-ivory); max-width:30ch; margin:0 0 18px; }

body.pn-id.pn-sp .wrap > footer{ background:transparent; margin-top:clamp(56px,8vw,112px); padding:28px 0 56px; border-top:1px solid var(--p4-line); color:var(--p4-stone); }
body.pn-id.pn-sp .wrap > footer p{ margin:0; font-size:15px; color:var(--p4-stone); }

@media (max-width:1080px){
  body.pn-sp .journey .jrow{ grid-template-columns:repeat(3,minmax(0,1fr)); row-gap:24px; }
  body.pn-sp .journey .jstep:nth-child(4){ border-left:0; padding-left:0; }
}
@media (max-width:720px){
  body.pn-sp .pv-bar .pv-word{ font-size:26px; }
  body.pn-sp .journey .jrow{ grid-template-columns:1fr; row-gap:0; padding:20px 22px; }
  body.pn-sp .journey .jstep{ border-left:0; padding:14px 0; border-top:1px solid var(--p4-line); }
  body.pn-sp .journey .jstep:first-child{ border-top:0; padding-top:0; }
  body.pn-sp .why{ grid-template-columns:1fr; gap:22px; padding:24px; }
  body.pn-sp .screen > .screen-chrome{ padding:11px 14px; }
}

/* ══ PREVIEW-ONLY ELEMENTS INSIDE THE DEMONSTRATION ═════════════════════
   Production Results has no equivalent of these, so production has no dark
   styling for them. Colours are the live skin's; the empty image position
   uses production's own empty image-well colour and keeps the certified
   label rule (SUPPLIER-PREVIEW-SYSTEM-V1.md §10.2). */
/* production Results inherits the browser's own font-size and line-height
   (your-plot.html sets neither on body); the shell's reading size must not
   leak into the demonstration */
.pn-yp{ font-size:medium; line-height:normal; }
.pn-yp .pn-stage-top{ display:flex; justify-content:flex-end; margin:0 0 26px; }
.pn-yp .pn-stage-top .my-plot-access{ position:static; }
.pn-yp .pn-media-col{ display:flex; flex-direction:column; min-width:0; }
.pn-yp .pn-photo-slot{ flex:1 1 auto; min-height:240px; aspect-ratio:4/3;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:10px; text-align:center; padding:24px;
  background:rgba(46,48,51,1.0); box-shadow:inset 0 0 0 1px rgba(0,0,0,0.154); }
.pn-yp .pn-photo-slot b{ font-family:'Work Sans',sans-serif; font-size:11px; font-weight:600;
  letter-spacing:.2em; text-transform:uppercase; color:var(--accent); }
.pn-yp .pn-facts{ list-style:none; margin:20px 0 14px; padding:16px 0 0;
  border-top:1px solid rgba(194,189,181,.16); display:grid; gap:9px; text-align:left; }
.pn-yp .pn-facts li{ display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 10px;
  font-size:13.5px; line-height:1.45; }
.pn-yp .pn-facts b{ color:var(--ink); font-weight:600; letter-spacing:.005em; }
.pn-yp .pn-facts span{ color:var(--soft); }
.pn-yp .pn-open{ text-align:left; }
@media (max-width:719px){
  .pn-yp .pn-facts{ gap:11px; }
  .pn-yp .pn-facts li{ flex-direction:column; gap:1px; }
}
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
    "    {{PRODUCT_NAME}}         the maker's own product name",
    '    {{OFFER_NAME}}           the category/offering, in their words').replace(
    '''    {{STILL_TO_ESTABLISH_N}} what PlotNua has NOT established
    {{IMAGE_*}}              imagery state A only — see the block below''',
    '''    (no imagery token: the image position carries no copy — see
    SUPPLIER-PREVIEW-SYSTEM-V1.md §10.2)''')

HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<meta name="theme-color" content="#1B1C1E">
<title>PlotNua &mdash; a short introduction for {{SUPPLIER_NAME}}</title>
<meta name="description" content="Private, unlisted introduction prepared for {{SUPPLIER_NAME}}. Not a public PlotNua page.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700&family=Work+Sans:wght@300;400;500;600&display=swap">
'''


def styles():
    return ('<!-- PREMIUM DARK DESIGN, rules verbatim (comments stripped): assets/identity/pn-identity.css '
            '(sha %s) -->\n<style>\n%s\n</style>\n'
            '<!-- PREMIUM DARK DESIGN: the Premium Discovery system, rules verbatim, comments stripped, '
            'scope body.pn-id.pn-pd renamed body.pn-id.pn-sp (sha %s) -->\n<style>\n%s\n</style>\n'
            '<!-- PRODUCTION YOUR PLOT RESULTS, demonstration only. Same order as\n'
            '     your-plot.html: the skin assets/identity/pn-your-plot.css (sha %s,\n'
            '     %d rules) first, then the page stylesheet (sha %s, %d rules).\n'
            '     Both re-scoped to .pn-yp by refresh-ui-kit.py; cascade unchanged. -->\n'
            '<style>\n%s\n</style>\n<style>\n%s\n</style>\n'
            '<style>%s</style>\n'
            % (sha(ID_CSS_SRC), ID_CSS, sha(PD_CSS_SRC), PD_CSS,
               sha(SKIN_RAW), N_SKIN, sha(PROD_RAW), N_PROD,
               SKIN_CSS, PROD_CSS, SHELL_CSS))


SHELL_TOP = '''</head>
<body class="pn-id pn-id--dark pn-sp">
__CONFIG__

<div class="pv-bar"><div class="wrap">
  <span class="pv-word">PlotNua</span>
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
     Everything inside .pn-yp is genuine production PlotNua markup and
     CSS (production's own chain, stylesheet and dark skin). Do not
     invent a mock interface, and do not restyle it to match the page. ═ -->
<section>
  <div class="demo-intro">
    <h2>{{DEMO_HEADING}}</h2>
    <span class="illus-tag">Illustrative preview</span>
  </div>
  <p>{{DEMO_LEDE}}</p>

  <div class="screen">
    <div class="screen-chrome">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      <span class="screen-url">plotnua.ie/your-plot</span>
    </div>

    <div class="pn-stage">
      <div class="pn-yp"><section id="screen-match-results"><div class="match-results-panel interactive results-v2">
__PILL__

      <div class="results-hero" id="matchPrimary">
__HERO__
      </div></div></section></div>
    </div><!-- /pn-stage -->
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

''' + GALLERY_JS + '''
</body>
</html>
'''


def build(variant):
    cfg = CONFIG_A if variant == 'product' else CONFIG_B
    credit = (CREDIT_A + '\n') if variant == 'product' else ''
    return (HEAD + styles() + SHELL_TOP.replace('__CONFIG__', cfg)
            .replace('__PILL__', PILL).replace('__HERO__', HERO[variant])
            + shell_end(credit))


files = {'template-product-led.html': build('product'),
         'template-provider-led.html': build('provider')}

# ── guards ───────────────────────────────────────────────────────────────
SUPPLIER_REMNANTS = ['triq', 'briq', 'superior', 'pergola', 'klerner', 'neringa',
                     'shomera', '2,500', '22,700', 'aluminium', 'dublin 6',
                     'christian', 'nua modular', 'modulux', 'ecosauna']
for fn, h in files.items():
    markup = h.split('</head>', 1)[1]
    visible = re.sub(r'<!--.*?-->', ' ', markup, flags=re.S)
    visible = re.sub(r'<script\b.*?</script>', ' ', visible, flags=re.S)
    vis_text = re.sub(r'<[^>]+>', ' ', visible).lower()
    for m in ['noindex', 'nofollow', 'noarchive', 'nosnippet', 'noimageindex']:
        if m not in h:
            die(fn + ': missing robots directive ' + m)
    if 'class="pn-id pn-id--dark pn-sp"' not in h:
        die(fn + ': the premium dark design is not active')
    if '--pn-paper:#FBFAF5' in h or 'class="pv-bar"><div class="wrap">\n  <strong>' in h:
        die(fn + ': the old light preview shell survived')
    for chain in ('<div class="pn-yp"><section id="screen-match-results"><div class="match-results-panel interactive results-v2">',
                  '<div class="results-hero" id="matchPrimary">'):
        if markup.count(chain) != 1:
            die(fn + ': production chain element missing or repeated: ' + chain[:40])
    # compatibility anchors existing builders rely on
    for anchor in ('  <div class="screen">', '<div class="pn-stage">',
                   '      <div class="results-hero-inner">',
                   '<!-- WHY THIS COULD BE USEFUL', '<footer>\n',
                   "<h2>What we&rsquo;d like to explore</h2>",
                   '<!-- FROZEN', '<div class="journey">'):
        if markup.count(anchor) != 1:
            die(fn + ': builder anchor changed: %r' % anchor)
    # The v1 demo ending must NOT survive: a builder that slices up to it
    # would cut the production chain's closing line and break the demo
    # silently (found on ognyx and ood-house, 27 Oct 2026). Without it those
    # builders fail loudly and are migrated deliberately.
    if '\n    </div>\n  </div>\n</section>' in markup:
        die(fn + ': the v1 demo ending survived; slicing builders would break silently')
    if not re.search(r'\n<div class="wrap">\n  <header class="hero">.*?\n  </header>\n</div>\n', markup, re.S):
        die(fn + ': the hero header block changed shape')
    if not re.search(r'\n<!--\s*[═=]{10,}.*?LED.*?[═=]{10,}\s*-->\n', markup, re.S):
        die(fn + ': the instruction comment changed shape')
    if markup.count('pn-mark-heart is-plot-active') != 2:
        die(fn + ': mark count')
    for r in SUPPLIER_REMNANTS:
        if r in h.lower():
            die(fn + ': supplier remnant "' + r + '"')
    for t in ['{{SUPPLIER_NAME}}', '{{PROPOSITION}}', '{{DEMO_HEADING}}', '{{PERSONALISATION}}',
              '{{CLOSING_PROPOSITION}}', '{{VERIFIED_PRICE}}', '{{WHY_1_LABEL}}',
              '{{THINGS_TO_CHECK}}', '{{HOMEOWNER_LOCALITY}}', '{{DATE}}']:
        if t not in markup:
            die(fn + ': missing token ' + t)
    if 'Discover' not in markup or 'Connect' not in markup:
        die(fn + ': journey band missing')
    if vis_text.count('illustrative') != 1:
        die(fn + ': illustrative status missing or repeated')
    for banned in ['stays with the provider', 'everything that follows', 'nothing here is real',
                   'we have not agreed', 'does not exist yet', 'no partnership exists',
                   'partner', 'commission', 'referral', 'recommended', 'endorsed']:
        if banned in vis_text:
            die(fn + ': banned phrasing "' + banned + '"')
    if re.search(r'__[A-Z]+__', h):
        die(fn + ': unsubstituted kit token')
    if re.search(r'url\(\s*["\']?https?://', h):
        die(fn + ': an external CSS image reached the template')

_p = files['template-provider-led.html']
if '<img' in _p.split('</head>', 1)[1]:
    die('provider-led template must carry no <img>')
if '<img' not in files['template-product-led.html']:
    die('product-led template lost its authorised-imagery slot')

# CERTIFIED RULE, 5 Oct 2026 — SUPPLIER-PREVIEW-SYSTEM-V1.md §10.2 (unchanged)
if 'PHOTO_SLOT_LINE' in _p:
    die('provider-led template reinstated the PHOTO_SLOT_LINE token (§10.2)')
if 'Your project photography here' in _p:
    die('provider-led template reinstated the photo-slot heading (§10.2)')
if 'Where your imagery would go' in _p:
    die('provider-led template reinstated the imagery subsection (§10.2)')
if _p.count('<div class="pn-photo-slot"><b>Your image here</b></div>') != 1:
    die('provider-led template must carry exactly one image position holding '
        'the neutral placeholder label and nothing else (§10.2)')
for _phrase in ('where they would sit', 'stay yours until',
                'imagery waits until', 'until you tell us otherwise'):
    if _phrase in _p.lower():
        die('provider-led template narrates the image-rights process: '
            '"' + _phrase + '" (§10.2)')

changed = []
for fn, h in files.items():
    path = os.path.join(HERE, fn)
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    if old != h:
        changed.append(fn)
    if not CHECK:
        open(path, 'w', encoding='utf-8').write(h)
    print(('CHECK ' if CHECK else 'WROTE ') + fn, len(h),
          hashlib.sha256(h.encode()).hexdigest()[:16],
          '(differs from the file on disk)' if old != h else '(identical)')
print('production rules: page %d, skin %d · design: pn-identity %s, pn-premium-discovery %s'
      % (N_PROD, N_SKIN, sha(ID_CSS_SRC), sha(PD_CSS_SRC)))
if CHECK and changed:
    sys.exit(3)
