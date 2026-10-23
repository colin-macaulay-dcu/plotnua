#!/usr/bin/env python3
"""
BUILD CLUSTER 2 · GARDEN RETREAT
================================
Bounded builder for the approved Cluster 2 changes to
discovery-garden-retreat.html plus the one sitemap lastmod.

Founder authorisation: 11 October 2026, "CLUSTER 2 — CONDITIONAL APPROVAL",
with two corrections, both applied:

  1. HOT TUB POSITION. The statutory definitions support an INTERPRETATION,
     not a conclusive determination. One bounded precedent search was made;
     its single relevant result (ABP-322192-25) is recorded and is about a
     COMMERCIAL sauna, not a domestic hot tub. Absence of a decision is not
     treated as proof that permission is unnecessary. All four domestic
     categories are expressed as "how the definitions read", never as a
     settled answer.
  2. RUNNING COST. Four quantities kept apart: electricity consumed
     (kW x hours), the marginal unit rate, an illustrative session cost, and
     standing charges / all-in household comparisons. Heater cycling is
     stated. No verifiable dated Irish unit rate was obtained from a primary
     source, so the formula ships with a CLEARLY LABELLED ILLUSTRATIVE rate
     and no claim of a current national price.

Also per the approval: no Atlas wellness intake, no market-wide price
comparison, no new Discovery URL, no change to Cluster 1, and NO routing into
the garden-room recommendation engine — there is no honest wellness matching
capability, and the engine registry (DISCOVERY_CONTENT in your-plot.html)
holds only 'garden-room' and 'residential'.

ALL COPY IS DATA. Every homeowner-visible string lives in EDITS below so the
guards can lift it verbatim from this file.

Every anchor must appear EXACTLY ONCE before the edit, and the replacement
exactly once after. Any other count is a refusal.

  --check   report BEFORE / AFTER / MIXED
  --stage   write the changes
  --revert  restore from the .cluster2.bak sidecars
"""
import sys, os, hashlib, shutil

# PREMIUM LOCK (founder decision, 23 Oct 2026): refuse before reading or writing anything
# when a page this layout builder rewrites carries the approved Premium design.
if __name__ == "__main__":
    import os as _pl_os, sys as _pl_sys
    _pl_sys.path.insert(0, _pl_os.path.dirname(_pl_os.path.abspath(__file__)))
    import premium_pages as _pl
    _pl.refuse_if_premium("build-cluster2-garden-retreat.py", ['discovery-garden-retreat.html'])

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, 'discovery-garden-retreat.html')
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
BAK = '.cluster2.bak'
BUILD_DATE = '2026-10-11'

# ---------------------------------------------------------------------------
# THE ILLUSTRATIVE RATE. Not a national price, and the page says so.
# ---------------------------------------------------------------------------
ILLUSTRATIVE_RATE_CENT = 35          # cent per kWh, marginal unit rate
EXAMPLE_HEATER_KW = 9
EXAMPLE_HOURS = 1
CEILING_EUR = EXAMPLE_HEATER_KW * EXAMPLE_HOURS * ILLUSTRATIVE_RATE_CENT / 100.0
if abs(CEILING_EUR - 3.15) > 0.005:
    sys.exit('REFUSE: the worked example no longer evaluates to the published figure')

EDITS = []
def edit(name, anchor, replacement):
    EDITS.append((name, anchor, replacement))

# --- E1 · meta description ---------------------------------------------------
edit('E1-meta-description',
 '<meta name="description" content="Compare a compact garden sauna, wood-fired hot tub and cold plunge in Ireland. Explore space, installation requirements and indicative Irish prices.">',
 '<meta name="description" content="A sauna cabin, a hot tub and a cold plunge are not the same thing in Irish planning law. How the definitions read for each, what the 30 m² and 25 m² limits mean, and what the law still does not settle.">')

# --- E2 · structured data ----------------------------------------------------
LD = '''
<!-- STRUCTURED DATA. Technical hygiene, not the ranking strategy. WebPage,
     not Article: a standing resource, not a dated piece. Deliberately absent:
     FAQPage (the answers are prose inside the narrative, not a Q&A list), and
     Product / Offer / AggregateOffer (this page states no market price and
     Atlas holds one wellness organisation, so price schema would assert what
     the page itself refuses to claim). -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "https://plotnua.ie/discovery-garden-retreat.html#webpage",
      "url": "https://plotnua.ie/discovery-garden-retreat.html",
      "name": "Garden Saunas, Hot Tubs & Cold Plunges in Ireland: the Planning Rules",
      "description": "How Irish planning law reads for a sauna cabin, a freestanding hot tub, a sunken tub and a cold plunge \\u2014 and what it does not settle.",
      "inLanguage": "en-IE",
      "dateModified": "%(date)s",
      "isPartOf": { "@id": "https://plotnua.ie/#website" },
      "publisher": { "@id": "https://plotnua.ie/#organisation" },
      "breadcrumb": { "@id": "https://plotnua.ie/discovery-garden-retreat.html#breadcrumb" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://plotnua.ie/discovery-garden-retreat.html#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/" },
        { "@type": "ListItem", "position": 2, "name": "Discoveries", "item": "https://plotnua.ie/discoveries.html" },
        { "@type": "ListItem", "position": 3, "name": "Garden Retreat" }
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://plotnua.ie/#website",
      "url": "https://plotnua.ie/",
      "name": "PlotNua",
      "inLanguage": "en-IE",
      "publisher": { "@id": "https://plotnua.ie/#organisation" }
    },
    {
      "@type": "Organization",
      "@id": "https://plotnua.ie/#organisation",
      "name": "PlotNua",
      "url": "https://plotnua.ie/"
    }
  ]
}
</script>
</head>''' % {'date': BUILD_DATE}
edit('E2-structured-data', '\n</head>', LD)

# --- E3 · the planning block, rebuilt ----------------------------------------
PLANNING_OLD = '''    <h3>Planning</h3>
    <div class="rule-group">
      <h3>What the rule says</h3>
      <p>A sauna is a small garden building, so the exempted development rules apply. Two figures matter:</p>
      <ul class="planning-conditions">
        <li>At least <strong>25&nbsp;m&sup2;</strong> of private open space must remain behind the house.</li>
        <li>Structures behind the line of the house are capped at <strong>30&nbsp;m&sup2;</strong> in total.</li>
      </ul>
    </div>
    <div class="rule-group">
      <h3>What that means in a real garden</h3>
      <p>Existing sheds and similar structures count towards the permitted area, so your remaining allowance may be smaller than you think.</p>
      <p>Whether a sauna&rsquo;s heater changes the answer is <strong>not something PlotNua can establish</strong>. For a definite answer, apply for a Section&nbsp;5 Declaration &mdash; &euro;80 in Dublin City Council when we checked.</p>
      <p>A hot tub or plunge tub may not count as a structure at all. We <strong>could not find an Irish source that settles this either way</strong>, and Building Regulations are unsettled for the same reason. This page does not say any of the three needs permission, or that it does not.</p>
    </div>'''

PLANNING_NEW = '''    <h3>Planning</h3>
    <div class="rule-group">
      <h3>The short answer</h3>
      <p>A sauna cabin is a building. You put it up, so the garden-building rules apply to it.</p>
      <p>A hot tub you stand on an existing patio is usually different. You are not building anything &mdash;
        you are putting something down. On the face of the rules, that is not the kind of work planning law is
        about.</p>
      <p>Two things change that. <strong>Dig a hole for it</strong> and you are excavating. <strong>Build a
        deck or a shelter around it</strong> and you are building. Either way you are back inside the rules.</p>
      <p>That is the useful answer. The rest of this section is why, and where it stops being that simple.</p>
    </div>
    <div class="rule-group">
      <h3>Why building something and putting something down are treated differently</h3>
      <p>The Planning and Development Act only bites on two things: carrying out <em>works</em>, or changing
        how land is used. It lists what counts as works &mdash; building, digging, knocking, extending,
        altering, repairing, renewing &mdash; and <strong>putting an object down is not on the list</strong>.</p>
      <p>That one omission is what separates a sauna cabin from a hot tub, and a hot tub from a sunken one.</p>
    </div>
    <div class="rule-group">
      <h3>Four things, four different answers</h3>
      <p>This is how the rules appear to read. It is not a decision by your council, and only a council or
        An Coimis&uacute;n Plean&aacute;la can give you one of those.</p>
      <ul class="planning-conditions">
        <li><strong>A sauna cabin.</strong> You build it, so the rules apply. It then has to fit the
          garden-building exemption. Worth knowing: that exemption lists a greenhouse, a garage, a store and a
          shed, and picks up anything else only as &ldquo;other similar structure&rdquo;. <strong>A sauna is
          not named anywhere in it.</strong></li>
        <li><strong>A hot tub on an existing patio.</strong> Nothing built, nothing dug. It appears to fall
          outside the rules altogether.</li>
        <li><strong>A sunken or in-ground tub.</strong> Digging is on the list, twice over. This one is clearly
          inside the rules.</li>
        <li><strong>A cold plunge tub you stand on the ground.</strong> Same as the hot tub. No Irish source we
          could find deals with it, and neither do the rules.</li>
      </ul>
      <p>And watch the services. Running a cable or a pipe underground means digging, so <strong>the connection
        can need permission even when the tub itself does not.</strong></p>
    </div>
    <div class="rule-group">
      <h3>If the rules do apply, here are the numbers</h3>
      <p>For a sauna cabin, two limits and one condition:</p>
      <ul class="planning-conditions">
        <li><strong>30&nbsp;m&sup2;</strong> total for everything in the garden, not just the new thing. This
          went up from 25&nbsp;m&sup2; in July 2026.</li>
        <li><strong>25&nbsp;m&sup2;</strong> of open garden has to be left.</li>
        <li>It has to be <strong>for personal use at home</strong>. Not somewhere to sleep, and not a business.</li>
      </ul>
      <p>Your existing shed counts towards the 30, so you may have less room than you think. The full
        conditions are on <a href="discovery-living-in-the-garden.html">Living in the Garden</a>.</p>
      <p><strong>Building Regulations are a separate rule with a separate number, and it is 25&nbsp;m&sup2;.</strong>
        Under that, a detached garden building is outside them &mdash; but only if it is also standing on its
        own, within the height limits, and used just for relaxing or storage rather than for a business. Most
        saunas are well under 25&nbsp;m&sup2;, so for most people this is one less thing to worry about. Go
        bigger, attach it to the house, or run it as a business, and the Building Regulations apply in full.</p>
    </div>
    <div class="rule-group">
      <h3>The one Irish case we found, and what it does not settle</h3>
      <p>We looked for Irish decisions about garden saunas and hot tubs. We found one:
        <strong>ABP-322192-25</strong>, from July 2025. A 7.3&nbsp;m&sup2; caravan run as a
        <em>paying</em> sauna in a side garden in Sandycove, along with screen fencing, a kiosk and a shelter.
        It was allowed to stay, for three years only, because a caravan is not a permanent building.</p>
      <p>What it tells you: <strong>a sauna people pay to use can end up in the planning system</strong>, and
        the inspector treated &ldquo;sauna&rdquo; as a use the local plan simply does not list, to be judged
        case by case.</p>
      <p>What it does not tell you: <strong>we are not saying the paying customers alone are what made
        permission necessary.</strong> The application covered the caravan, the fencing, the kiosk, the shelter
        and the site works together, and the decision does not separate them.</p>
      <p>It is also <strong>not a Section&nbsp;5 declaration, and it settles nothing about a private sauna, hot
        tub or plunge tub at home.</strong> We found no Irish decision on any of those &mdash; and we are not
        going to read that silence as a yes. If your plans turn on it, ask the council in writing. That is what
        a Section&nbsp;5 declaration is for: there is a fee, and they have four weeks to answer.</p>
    </div>'''
edit('E3-planning-block', PLANNING_OLD, PLANNING_NEW)

# --- E4 · electricity, verified only -----------------------------------------
ELEC_OLD = '''        <p>A sauna needs an electrician. This is Restricted Electrical Works: it must be done by a <strong>Registered Electrical Contractor</strong>, you get a completion certificate, and unregistered work carries penalties up to &euro;50,000 and three years. Ask the contractor what your heater needs. <a href="https://www.safeelectric.ie/" target="_blank" rel="noopener noreferrer">Safe Electric</a> publishes the register.</p>'''
ELEC_NEW = '''        <p>A sauna heater wires into the house like a cooker, not a kettle. In Ireland that work has to be
          done by a <strong>Registered Electrical Contractor</strong>, and they have to give you a
          <strong>Completion Certificate</strong> when they are finished. Keep it. Registered contractors work
          to the national wiring rules, I.S.&nbsp;10101, and the energy regulator prosecutes people who do this
          work without being registered. Ask your contractor what your heater needs.
          <a href="https://www.cru.ie/regulations-policy/safety/rgi-and-safe-electric/" target="_blank" rel="noopener noreferrer">CRU</a> &middot;
          <a href="https://www.safeelectric.ie/" target="_blank" rel="noopener noreferrer">Safe Electric</a> lists registered contractors.</p>
        <p class="rule-note">The exact electrical requirements depend on your installation. A registered
          electrical contractor can advise you and carry out the work safely.</p>'''
edit('E4-electricity', ELEC_OLD, ELEC_NEW)

# --- E5 · running cost, four quantities kept apart ---------------------------
RUNNING = '''      <div class="practical-item">
        <h3>What it costs to run</h3>
        <p>Start with the simple sum. A %(kw)d&nbsp;kW heater running flat out for an hour uses
          %(kw)d&nbsp;units of electricity. Multiply that by what you pay per unit &mdash; the figure on your
          own bill, not an average.</p>
        <p>At an illustrative %(rate)dc a unit, that hour comes to <strong>&euro;%(ceiling).2f</strong>. That
          figure is <strong>one hour of continuous %(kw)d&nbsp;kW operation at an illustrative rate</strong>,
          not a forecast of your bill.</p>
        <p>Real use is usually less. The heater runs flat out while the cabin warms up, then the thermostat
          switches it on and off to hold the heat. So what you actually use depends on <strong>how long it runs
          and how much it cycles</strong> &mdash; which depends on the cabin, the insulation, the weather and
          how long you leave it on. <strong>We are not going to put a percentage on that and pretend it is
          precise.</strong></p>
        <p class="rule-note">One thing to watch in other people&rsquo;s running costs: <strong>standing charges
          belong to your house, not to your sauna.</strong> You pay them whether or not you ever switch the
          heater on, so a figure that folds them in makes a session look dearer than it really is.</p>
      </div>
''' % {'kw': EXAMPLE_HEATER_KW, 'rate': ILLUSTRATIVE_RATE_CENT, 'ceiling': CEILING_EUR}
edit('E5-running-cost',
 '''      <div class="practical-item">
        <h3>Insurance</h3>''',
 RUNNING + '''      <div class="practical-item">
        <h3>Insurance</h3>''')

# --- E6 · evidence drawers ---------------------------------------------------
edit('E6a-evidence-electricity',
 '''      <div class="faq-a">The Electricity Regulation Act 1999 as amended, and Safe Electric guidance.</div>''',
 '''      <div class="faq-a">The Commission for Regulation of Utilities, &ldquo;RGI and Safe Electric Schemes&rdquo;,
        read 11&nbsp;October&nbsp;2026: an electrical contractor must be registered as a Registered Electrical
        Contractor under the Safe Electric scheme; a REC must give the customer a Completion Certificate; RECs
        are assessed against the National Rules for Electrical Installations, I.S.&nbsp;10101; and the CRU
        brings enforcement actions against unregistered contractors.<br><br><strong>Recorded gap.</strong> The
        CRU calls the regulated category &ldquo;restricted electrical works&rdquo; and Safe Electric calls it
        &ldquo;controlled electrical works&rdquo;. Neither body&rsquo;s published material sets out exactly
        which jobs fall inside it, so PlotNua does not state where the boundary falls for any particular
        heater. Penalty figures circulating in secondary sources were not verified at primary source and are
        not published here.</div>''')

edit('E6b-evidence-planning',
 '''      <div class="faq-a">The published exempted development conditions for garden structures. The &euro;80 Section&nbsp;5 fee is Dublin City Council&rsquo;s; fees are set locally.</div>''',
 '''      <div class="faq-a">Read first-hand from the Irish Statute Book on 11&nbsp;October&nbsp;2026: the
        Planning and Development Act 2000, sections&nbsp;2 (&ldquo;works&rdquo;, &ldquo;structure&rdquo;),
        3 (&ldquo;development&rdquo;) and 5 (declarations); the Planning and Development Regulations 2001,
        article&nbsp;6 and Schedule&nbsp;2 Part&nbsp;1 Class&nbsp;3; S.I. No.&nbsp;338 of 2026, which raised the
        garden-structure limit to 30&nbsp;m&sup2; on 27&nbsp;July&nbsp;2026; and the Building Regulations 1997,
        article&nbsp;8 and Third Schedule Class&nbsp;2, for the separate 25&nbsp;m&sup2; threshold. The
        Section&nbsp;5 fee is prescribed and set locally; we have not re-checked it, so no figure is quoted.</div>
    </details>

    <details class="faq-item is-inline">
      <summary><h3>The one case</h3><span class="icon"></span></summary>
      <div class="faq-a">ABP-322192-25, inspector&rsquo;s report by Natalie de R&oacute;iste dated
        7&nbsp;July&nbsp;2025, on a third-party appeal against D&uacute;n Laoghaire-Rathdown County
        Council&rsquo;s grant of retention (reg. ref. D25A/0034/WEB) for a 7.3&nbsp;m&sup2; caravan operated as a
        commercial sauna at 17 Sandycove Point. Retention recommended, limited to three years. A planning
        appeal, not a Section&nbsp;5 declaration.</div>
    </details>

    <details class="faq-item is-inline">
      <summary><h3>Running cost</h3><span class="icon"></span></summary>
      <div class="faq-a">The arithmetic is ours and the rate is illustrative. We did not find a dated Irish unit
        rate from a primary source that we were willing to publish as a current national price, so the page shows
        the formula with a labelled illustrative rate instead. Use the unit rate on your own bill.</div>''')

# --- E7 · what the evidence does not establish, narrowed ---------------------
edit('E7-not-established',
 '''    <p>Whether any of these three is exempted development, or is not. Whether a hot tub or plunge tub counts as a structure at all. The Building Regulations position. Stove and flue clearances. Where the water should go. The Irish insurance position. What a finished project costs. We also found no Irish supplier publishing a price for a chilled plunge or a built plunge pool. And we cannot tell you whether any of this suits your garden &mdash; the question that matters most.</p>''',
 '''    <p>Whether your council would read the rules the way we have &mdash; only a Section&nbsp;5 declaration
      settles that for your garden. Whether a sauna&rsquo;s heater changes anything about the
      personal-use condition. Whether a council counts a free-standing tub towards the 30&nbsp;m&sup2;,
      given that the garden-building rule mentions &ldquo;placing&rdquo; an &ldquo;object&rdquo; while the Act
      does not. Whether &ldquo;other similar structure&rdquo; definitely covers a sauna cabin. Exactly which
      electrical jobs need a registered contractor&rsquo;s certificate. Stove and flue clearances. Where the
      water should go. The Irish insurance position. What a finished project costs. We also found no Irish
      supplier publishing a price for a chilled plunge or a built plunge pool. And we cannot tell you whether
      any of this suits your garden &mdash; the question that matters most.</p>''')

SITEMAP_EDIT = (
 '''    <loc>https://plotnua.ie/discovery-garden-retreat.html</loc>
    <lastmod>2026-09-26</lastmod>''',
 '''    <loc>https://plotnua.ie/discovery-garden-retreat.html</loc>
    <lastmod>%s</lastmod>''' % BUILD_DATE)


def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]

def state(src):
    before = all(src.count(a) == 1 for _, a, _ in EDITS)
    after = all(src.count(r) == 1 for _, _, r in EDITS)
    return 'BEFORE' if before and not after else ('AFTER' if after and not before else 'MIXED/UNKNOWN')

PRESERVE = [
  ('<h1>Garden Retreat</h1>', 1),
  ('<title>Garden Saunas, Hot Tubs &amp; Cold Plunges in Ireland | PlotNua</title>', 1),
  ('<link rel="canonical" href="https://plotnua.ie/discovery-garden-retreat.html">', 1),
  ('mycabin.ie', None), ('gardenhouse24.ie', None), ('timbertrove.com', None),
  ('PlotNua has no commercial relationship with the three suppliers compared here', 1),
]
FORBIDDEN_AFTER = [
  ('?discovery=', 'a recommendation-engine route was introduced; Cluster 2 forbids it'),
  ('garden-retreat&#39;', 'engine parameter'),
]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'
    src = open(PAGE, encoding='utf-8').read()
    sm = open(SITEMAP, encoding='utf-8').read()

    if mode == '--check':
        print('page    %s  sha %s  %d lines' % (state(src), sha(src), src.count('\n') + 1))
        print('sitemap %s' % ('AFTER' if SITEMAP_EDIT[1] in sm else ('BEFORE' if SITEMAP_EDIT[0] in sm else 'UNKNOWN')))
        for name, anchor, repl in EDITS:
            print('  %-26s anchor=%d replacement=%d' % (name, src.count(anchor), src.count(repl)))
        return

    if mode == '--revert':
        for p in (PAGE, SITEMAP):
            b = p + BAK
            if not os.path.exists(b): raise SystemExit('REFUSE: no backup at %s' % b)
            shutil.copyfile(b, p); os.remove(b); print('reverted', os.path.basename(p))
        return

    if mode != '--stage':
        raise SystemExit('usage: --check | --stage | --revert')

    if state(src) != 'BEFORE':
        raise SystemExit('REFUSE: page is %s, not BEFORE. Nothing written.' % state(src))
    if sm.count(SITEMAP_EDIT[0]) != 1:
        raise SystemExit('REFUSE: sitemap anchor appears %d times' % sm.count(SITEMAP_EDIT[0]))

    pre = {k: src.count(k) for k, _ in PRESERVE}
    out = src
    for name, anchor, repl in EDITS:
        n = out.count(anchor)
        if n != 1: raise SystemExit('REFUSE: %s anchor appears %d times, expected 1' % (name, n))
        out = out.replace(anchor, repl, 1)
        if out.count(repl) != 1:
            raise SystemExit('REFUSE: %s replacement appears %d times' % (name, out.count(repl)))

    for k, expect in PRESERVE:
        if out.count(k) != pre[k]:
            raise SystemExit('REFUSE: preserved token %r went %d -> %d' % (k, pre[k], out.count(k)))
        if expect is not None and out.count(k) != expect:
            raise SystemExit('REFUSE: preserved token %r count %d, expected %d' % (k, out.count(k), expect))
    for tok, why in FORBIDDEN_AFTER:
        if tok in out and tok not in src:
            raise SystemExit('REFUSE: %s (%s)' % (why, tok))

    for p, new in ((PAGE, out), (SITEMAP, sm.replace(SITEMAP_EDIT[0], SITEMAP_EDIT[1], 1))):
        if not os.path.exists(p + BAK): shutil.copyfile(p, p + BAK)
        open(p, 'w', encoding='utf-8').write(new)

    print('STAGED  %d edits + 1 sitemap lastmod' % len(EDITS))
    print('page    %s -> %s  (%d -> %d lines)' % (sha(src), sha(out), src.count('\n') + 1, out.count('\n') + 1))
    print('worked example: %d kW x %d h x %dc = EUR %.2f (illustrative)'
          % (EXAMPLE_HEATER_KW, EXAMPLE_HOURS, ILLUSTRATIVE_RATE_CENT, CEILING_EUR))

if __name__ == '__main__':
    main()
