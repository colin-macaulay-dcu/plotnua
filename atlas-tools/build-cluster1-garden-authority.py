#!/usr/bin/env python3
"""
BUILD CLUSTER 1 · GARDEN AUTHORITY
==================================
Bounded builder for the approved Cluster 1 changes to
discovery-living-in-the-garden.html plus the one sitemap lastmod.

Founder authorisation: 11 October 2026, "GO - IMPLEMENT CLUSTER 1, WITH FOUR
REQUIRED COPY CORRECTIONS". The four corrections are applied:

  1. C1  25 m2 Building Regulations wording made conditional on the Class 2
         conditions, including use. No claim that everything under 25 m2 is
         automatically exempt.
  2. C3  OPTION A TAKEN. The garden-room Commencement Notice claim is OMITTED
         entirely. The only change to section 6 is a scope correction so the
         two verified notices read as the garden home's, not the garden
         room's. The uncertainty ledger records why.
  3.     Unresolved questions CURATED: measurement, toilet/incidental use,
         semi-detached/terraced drafting conflict, and the seven-year rule.
         Special Amenity Area numbering, Fire Safety Certificate scope and
         amendment-history questions stay in governance.
  4.     Price block simplified to the consumer finding plus the three
         questions. No average. No census claim. No Class 3A price.

ALL COPY IS DATA. Every homeowner-visible string lives in EDITS below so the
guards can lift it verbatim from this file and compare it with the page.

Every anchor must appear EXACTLY ONCE in the source before the edit, and the
replacement must appear exactly once after. Any other count is a refusal.

  --check   report whether the page is at BEFORE, at AFTER, or neither
  --stage   write the changes
  --revert  restore from the .cluster1.bak sidecar written by --stage
"""
import sys, os, json, hashlib, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, 'discovery-living-in-the-garden.html')
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
EVIDENCE = os.path.join(HERE, 'cluster1-cost-evidence.json')
BAK = '.cluster1.bak'

BUILD_DATE = '2026-10-11'

# ---------------------------------------------------------------------------
# THE FIGURES. Lifted from the frozen artefact, never typed by hand.
# ---------------------------------------------------------------------------
EV = json.load(open(EVIDENCE))
FIG = EV['homeownerVisibleFigures']
N_REL      = FIG['relevantProducts']            # 247
N_NOBASIS  = FIG['priceBasisNotEstablished']    # 177
N_NOVAT    = FIG['vatStatusUnknown']            #  94
N_AREA     = FIG['floorAreaPublished']          #  45
N_3A       = FIG['class3AProductsInAtlas']      #   1
N_RECORDS  = EV['totals']['gardenRoomRecords']  # 573
# 14 Oct 2026 (final publication consistency corrections): every figure in the
# price section is the 7 October research snapshot this evidence file was
# computed from, not the live universe (572 after the Cosy Cabins hold). The
# date is DERIVED from the evidence file's own source stamp, so it can never
# drift from the counts beside it, and no new hand-maintained number appears.
import datetime as _dt
_d = _dt.date.fromisoformat(EV['source']['generated'][:10])
AS_OF = "%d %s %d" % (_d.day, _d.strftime("%B"), _d.year)
N_ORGS     = EV['totals']['relevantOrganisations']  # 24

if N_3A > 2:
    sys.exit('REFUSE: Atlas now holds %d Class 3A products. The copy below is '
             'written for a set too small to price. Re-approve the wording.' % N_3A)

# ---------------------------------------------------------------------------
# EDITS. (name, anchor, replacement). Anchor count must be exactly 1.
# ---------------------------------------------------------------------------
EDITS = []
def edit(name, anchor, replacement):
    EDITS.append((name, anchor, replacement))

# --- E1 · meta description ---------------------------------------------------
edit('E1-meta-description',
 '<meta name="description" content="Can you build a garden room or a small home in your Irish garden? Understand the different 2026 planning rules, space limits and what to check for your property.">',
 '<meta name="description" content="What the July 2026 regulations changed: the 30&nbsp;m² garden room, the new 32&ndash;45&nbsp;m² garden home, what counts towards the limit &mdash; and the separate 25&nbsp;m² Building Regulations threshold almost nobody mentions.">'.replace('&nbsp;',' ').replace('&ndash;','–').replace('&mdash;','—'))

# --- E2 · structured data ----------------------------------------------------
LD = '''
<!-- STRUCTURED DATA. Technical hygiene, not the ranking strategy.
     WebPage, not Article: this is a standing resource, not a dated piece.
     Deliberately absent: FAQPage (the direct answers are prose inside the
     narrative, not a Q&A list), and Product / Offer / AggregateOffer (the
     page's own finding is that PlotNua cannot state a comparable price, so
     emitting price schema would contradict it). Every property below is a
     fact already visible on the page. -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebPage",
      "@id": "https://plotnua.ie/discovery-living-in-the-garden.html#webpage",
      "url": "https://plotnua.ie/discovery-living-in-the-garden.html",
      "name": "Garden Rooms & Garden Homes in Ireland: 2026 Planning Rules",
      "description": "What the July 2026 regulations changed: the 30 m\\u00b2 garden room, the new 32\\u201345 m\\u00b2 garden home, and what counts towards the limit.",
      "inLanguage": "en-IE",
      "dateModified": "%(date)s",
      "isPartOf": { "@id": "https://plotnua.ie/#website" },
      "publisher": { "@id": "https://plotnua.ie/#organisation" },
      "breadcrumb": { "@id": "https://plotnua.ie/discovery-living-in-the-garden.html#breadcrumb" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://plotnua.ie/discovery-living-in-the-garden.html#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/" },
        { "@type": "ListItem", "position": 2, "name": "Discoveries", "item": "https://plotnua.ie/discoveries.html" },
        { "@type": "ListItem", "position": 3, "name": "Living in the Garden" }
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

# --- E3 · the real window ----------------------------------------------------
edit('E3-relevant-period',
 '''    <p>The exemption is temporary. The work has to be both started and finished by
      31&nbsp;December&nbsp;2030.</p>''',
 '''    <p>The exemption is temporary. The window opened on 16&nbsp;July&nbsp;2026, the
      day the regulations were signed, and closes on 31&nbsp;December&nbsp;2030 &mdash;
      and the work has to be both started and finished inside it.</p>''')

# --- E4 · the 25 m2 / 30 m2 finding, plus the 45 m2 extension line -----------
C1_COPY = '''
    <p>Two different limits, and only one of them moved. Thirty square metres is the
      planning ceiling for a garden room. The Building Regulations have their own,
      separate threshold, and it is still 25&nbsp;m&sup2;: a detached garden building of
      no more than 25&nbsp;m&sup2; can fall inside the Building Regulations exemption,
      but only if it also meets the rest of the conditions attached to it &mdash;
      detached from any other building, inside the height limits, and used only for
      recreation or storage, not for human habitation and not for a trade or business.
      Go over 25&nbsp;m&sup2;, or fail one of those conditions, and the Building
      Regulations apply to the building in full: structure, fire, ventilation,
      insulation. You still need no planning application. That is a different question
      from whether the building has to be built to standard.</p>

    <p>The same July 2026 regulations also raised what you can add to the back of the
      house without permission, from 40&nbsp;m&sup2; to 45&nbsp;m&sup2;. If the room you
      need could be an extension instead, that number moved too.</p>'''
edit('E4-building-regs-threshold',
 '''      </li>
    </ul>
  </section>

  <!-- 5 · THE SELF-CHECK.''',
 '''      </li>
    </ul>
''' + C1_COPY + '''
  </section>

  <!-- 5 · THE SELF-CHECK.''')

# --- E5 · the measurement row ------------------------------------------------
edit('E5-measurement-row',
 '''      <li><span class="dq-fact">Getting to it.</span>
          <span class="dq-note">A way in on foot or by wheelchair, inside your own
            property. No new entrance onto the road.</span></li>
    </ul>''',
 '''      <li><span class="dq-fact">Getting to it.</span>
          <span class="dq-note">A way in on foot or by wheelchair, inside your own
            property. No new entrance onto the road.</span></li>
      <li><span class="dq-fact">How you measure it.</span>
          <span class="dq-note">The regulations set the limits in square metres and
            never say how to measure them. They define &ldquo;gross floor space&rdquo;
            as an internal measurement, but the garden-building rules do not use that
            term &mdash; they say &ldquo;total area&rdquo;, which is defined nowhere.
            That is why a council and a supplier can give you different answers and
            both point at the text. Measure inside and out, take the larger figure,
            and if you are within a metre or two of the limit, ask the council before
            you order.</span></li>
    </ul>''')

# --- E6 · scope correction on the two notices. NO garden-room CN claim. -------
edit('E6-two-notices-scope',
 '''    <p>Exempted development means no planning application. It does not mean nothing
      to file.</p>''',
 '''    <p>Exempted development means no planning application. For a garden home, it does
      not mean nothing to file.</p>''')

# --- E7 · the price-comparison section, before the evidence drawers ----------
PRICE_SECTION = '''
  <!-- 6b · THE PRICE QUESTION. Not a dataset report. The homeowner-visible
       claim is that published prices are often not comparable, with the
       counts that establish it and the three questions that fix it. Every
       figure comes from atlas-tools/cluster1-cost-evidence.json; no figure is
       averaged across price bases; and no price is stated for the 32-45 m2
       envelope, because Atlas holds one product in it. -->
  <section class="article-section reveal">
    <div class="kicker">What It Costs</div>
    <h2>Garden room prices are hard to compare.</h2>
    <p>Before you can tell whether one garden room is dearer than another, you have to
      know what each price covers. Most of the time, it is not published.</p>

    <ul class="dq-rows">
      <li><span class="dq-fact">%(rel)d garden-room products with a euro price we can
            stand behind.</span>
          <span class="dq-note">From %(orgs)d suppliers, out of %(records)d garden-room
            products in PlotNua&rsquo;s %(asof)s research snapshot.</span></li>
      <li><span class="dq-fact">%(nobasis)d of them do not establish what the price
            includes.</span>
          <span class="dq-note">A kit you assemble, a building delivered and erected,
            and a turnkey finish with foundations and power are three different
            purchases. The same building lands at very different numbers depending on
            which one you are being quoted.</span></li>
      <li><span class="dq-fact">%(novat)d do not publish whether VAT is in the
            price.</span>
          <span class="dq-note">That can make a substantial difference to the price
            you actually pay.</span></li>
      <li><span class="dq-fact">Only %(area)d publish a floor area.</span>
          <span class="dq-note">Which is the one number the planning rules actually
            turn on.</span></li>
    </ul>

    <p>So we are not going to tell you what a garden room costs in Ireland, and we are
      certainly not going to tell you what a garden home costs: the market has not
      published enough for anyone to say honestly. What we can tell you is what to ask.</p>

    <p>Before comparing two prices, get the same three answers from both suppliers.
      Is erection included? Are foundations included? Is VAT included? If the answers
      differ, the prices were never comparable in the first place.</p>
  </section>

  <!-- 7 · THE EVIDENCE LAYER.''' % {
    'rel': N_REL, 'orgs': N_ORGS, 'records': N_RECORDS, 'asof': AS_OF,
    'nobasis': N_NOBASIS, 'novat': N_NOVAT, 'area': N_AREA}
if '%(' in PRICE_SECTION:
    sys.exit('REFUSE: PRICE_SECTION still carries an unsubstituted placeholder')
# Founder correction, 11 October 2026: the pricing heading is
# "Garden room prices are hard to compare." The superseded heading must never
# come back through a regeneration.
RETIRED_HEADING = 'Why the prices you are quoted will not compare'
if RETIRED_HEADING in PRICE_SECTION:
    sys.exit('REFUSE: the retired pricing heading is back in PRICE_SECTION')
if 'Garden room prices are hard to compare.' not in PRICE_SECTION:
    sys.exit('REFUSE: the approved pricing heading is missing from PRICE_SECTION')
edit('E7-price-section', '\n  <!-- 7 · THE EVIDENCE LAYER.', PRICE_SECTION)

# --- E8 · conditions-as-written, three appends -------------------------------
edit('E8a-conditions-building',
 '''wall or party boundary, with windows at least 0.6&nbsp;m from the boundary
          they face.<br><br><strong>The garden.</strong>''',
 '''wall or party boundary, with windows at least 0.6&nbsp;m from the boundary
          they face. Permanent, too &mdash; the regulations rule out a caravan or a
          mobile home. And they state expressly that building control legislation
          applies to it: Building Regulations, fire safety and the Building Control
          Regulations. That is what the two notices above are
          about.<br><br><strong>The garden.</strong>''')

edit('E8b-conditions-garden',
 '''the system must have capacity for the extra load.<br><br><strong>Ownership''',
 '''the system must have capacity for the extra load, must comply with the EPA Code
          of Practice for Domestic Waste Water Treatment Systems, and no additional
          treatment unit may be installed under this
          exemption.<br><br><strong>Ownership''')

edit('E8c-conditions-use',
 '''          been subdivided.<br><br><strong>Time.</strong> Started and finished by
          31&nbsp;December&nbsp;2030.''',
 '''          been subdivided. The council keeps a record of every notification it
          receives under this exemption and reports the number to the Minister each
          year.<br><br><strong>Time.</strong> Signed on 16&nbsp;July&nbsp;2026.
          Started and finished by 31&nbsp;December&nbsp;2030.''')

# --- E9 · protected structures CORRECTION ------------------------------------
edit('E9-protected-structures',
 '''        <div class="faq-a">If your house is a protected structure, the protection
          extends to the land in its curtilage and to other structures on that land,
          and work that would materially affect its character is not exempt. You can
          ask the council for a declaration on what would and would not affect the
          character: it is free, and the council has twelve weeks to answer. A
          declaration cannot exempt work that would need permission
          anyway.<br><br>''',
 '''        <div class="faq-a">If your house is a protected structure, work that would
          materially affect its character &mdash; or the character of any element that
          gives it its special interest &mdash; is not exempted development. The
          protection can reach into the grounds as well, but only where the
          council&rsquo;s Record of Protected Structures says so, and only for the
          features that record names. So the first thing to read is your own entry in
          that record, not a general rule.<br><br>You can ask the council for a
          declaration on what would and would not affect the character, and it has
          twelve weeks to answer. That is a different request from the Section&nbsp;5
          declaration below, which answers whether something is exempted development
          at all, carries a prescribed fee and has a four-week clock. Neither kind of
          declaration can exempt work that would need permission anyway.<br><br>''')

# --- E10 · two new drawers, after the money drawer ---------------------------
NEW_DRAWERS = '''      <details class="faq-item">
        <summary><h3>Settling it in writing: the Section 5 declaration</h3><span class="icon"></span></summary>
        <div class="faq-a">If your situation turns on a question the regulations do not
          answer &mdash; and several of them do not &mdash; you can put the question to
          the council and get an answer you can rely on. Anyone may ask, in writing,
          for a declaration on whether something is or is not exempted development.
          There is a prescribed fee. The council must give you the declaration
          <em>and its main reasons</em> within four weeks, or within three weeks of any
          further information it asks for. If you disagree, you have four weeks to refer
          it to An Bord Pleanála. The declaration goes on the planning
          register.<br><br>It is the right move if you are near a limit, if your house
          came with planning conditions, if there is already a shed out there and the
          arithmetic is tight, or if you are in a conservation area.</div>
      </details>
      <details class="faq-item">
        <summary><h3>What the regulations do not say</h3><span class="icon"></span></summary>
        <div class="faq-a"><strong>Whether a semi-detached or terraced house qualifies
          for a garden home.</strong> The exemption is written for &ldquo;the rear
          garden of a principal house&rdquo;, but one of its own conditions says
          &ldquo;the rear garden of the curtilage of a detached house&rdquo;. Those are
          not the same thing, and the regulations do not reconcile them. If your house
          is not detached, this is the question to put to the council in
          writing.<br><br><strong>How the area is measured.</strong> Covered above.
          Undefined, and that is the honest answer rather than a cautious
          one.<br><br><strong>Whether a toilet in a garden room is still
          &ldquo;incidental to the enjoyment of the house&rdquo;.</strong> The
          garden-room rules say nothing about plumbing at all. What they restrict is the
          use, and where a WC sits against that test is not settled in the text. For a
          garden <em>home</em> the position is clear: water and wastewater yes, a
          separate connection no.<br><br><strong>And the seven-year rule, which is not
          what people think it is.</strong> Section&nbsp;157 of the Planning and
          Development Act stops enforcement seven years after unauthorised development
          started. It does not make the building lawful, it produces no certificate, and
          it will not satisfy a purchaser&rsquo;s solicitor. It is a limit on the
          council, not a route for you.</div>
      </details>
    </div>
  </section>'''
edit('E10-new-drawers',
 '''authority may inspect. Nothing here is tax or legal advice.</div>
      </details>
    </div>
  </section>''',
 '''authority may inspect. Nothing here is tax or legal advice.</div>
      </details>
''' + NEW_DRAWERS)

# ---------------------------------------------------------------------------
SITEMAP_EDIT = (
 '<url><loc>https://plotnua.ie/discovery-living-in-the-garden.html</loc><lastmod>2026-08-27</lastmod>',
 '<url><loc>https://plotnua.ie/discovery-living-in-the-garden.html</loc><lastmod>%s</lastmod>' % BUILD_DATE)


def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]

def apply_all(src, strict=True):
    out = src
    for name, anchor, repl in EDITS:
        n = out.count(anchor)
        if n != 1:
            if strict:
                raise SystemExit('REFUSE: %s anchor appears %d times, expected 1' % (name, n))
            return None
        out = out.replace(anchor, repl, 1)
        if out.count(repl) != 1:
            raise SystemExit('REFUSE: %s replacement appears %d times after edit'
                             % (name, out.count(repl)))
    return out

def state(src):
    before = all(src.count(a) == 1 for _, a, _ in EDITS)
    after = all(src.count(r) == 1 for _, _, r in EDITS)
    return 'BEFORE' if before and not after else ('AFTER' if after and not before else 'MIXED/UNKNOWN')

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'
    src = open(PAGE, encoding='utf-8').read()
    sm = open(SITEMAP, encoding='utf-8').read()

    if mode == '--check':
        print('page   %s  sha %s  %d lines' % (state(src), sha(src), src.count('\n') + 1))
        print('sitemap lastmod %s' % ('AFTER' if SITEMAP_EDIT[1] in sm else
              ('BEFORE' if SITEMAP_EDIT[0] in sm else 'UNKNOWN')))
        for name, anchor, repl in EDITS:
            print('  %-28s anchor=%d replacement=%d' % (name, src.count(anchor), src.count(repl)))
        return

    if mode == '--revert':
        for p in (PAGE, SITEMAP):
            b = p + BAK
            if not os.path.exists(b):
                raise SystemExit('REFUSE: no backup at %s' % b)
            shutil.copyfile(b, p); os.remove(b)
            print('reverted', os.path.basename(p))
        return

    if mode != '--stage':
        raise SystemExit('usage: --check | --stage | --revert')

    if state(src) != 'BEFORE':
        raise SystemExit('REFUSE: page is %s, not BEFORE. Nothing written.' % state(src))
    if SITEMAP_EDIT[0] not in sm:
        raise SystemExit('REFUSE: sitemap lastmod anchor not found. Nothing written.')
    if sm.count(SITEMAP_EDIT[0]) != 1:
        raise SystemExit('REFUSE: sitemap anchor appears %d times' % sm.count(SITEMAP_EDIT[0]))

    # preservation invariants, asserted before and after
    PRESERVE = [
      ('<title>Garden Rooms &amp; Garden Homes in Ireland: 2026 Planning Rules | PlotNua</title>', 1),
      ('What Could You Build in Your Garden?', None),
      ("garden_discovery_assessment_click", 1),
      ("!destination.pathname.endsWith('/your-plot.html')", 1),
      ("route !== 'garden-room' && route !== 'residential'", 1),
      ('<link rel="canonical" href="https://plotnua.ie/discovery-living-in-the-garden.html">', 1),
    ]
    pre = {k: src.count(k) for k, _ in PRESERVE}

    out = apply_all(src)
    for k, expect in PRESERVE:
        if out.count(k) != pre[k]:
            raise SystemExit('REFUSE: preserved token %r went %d -> %d' % (k, pre[k], out.count(k)))
        if expect is not None and out.count(k) != expect:
            raise SystemExit('REFUSE: preserved token %r count %d, expected %d' % (k, out.count(k), expect))

    for p, new in ((PAGE, out), (SITEMAP, sm.replace(*SITEMAP_EDIT, 1) if False else sm.replace(SITEMAP_EDIT[0], SITEMAP_EDIT[1], 1))):
        if not os.path.exists(p + BAK):
            shutil.copyfile(p, p + BAK)
        open(p, 'w', encoding='utf-8').write(new)

    print('STAGED  %d edits + 1 sitemap lastmod' % len(EDITS))
    print('page    %s -> %s  (%d -> %d lines)' % (sha(src), sha(out), src.count('\n') + 1, out.count('\n') + 1))
    print('figures 247/%d  no-basis/%d  no-VAT/%d  area/%d  class3A/%d'
          % (N_REL, N_NOBASIS, N_NOVAT, N_AREA, N_3A))

if __name__ == '__main__':
    main()
