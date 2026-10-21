"""PlotNua · The House as a Power Station · Stage 2 bridge section (October 2026).

Founder approval, 21 Oct 2026 ("STAGE 2 BRIDGE · APPROVED FOR LOCAL BUILD"):
the revised proposal of 21 Oct 2026, with one wording correction (Tandem
Compute named, no partnership implied). Built on top of Stage 1.

The ONE definition of the change, shared by:
  * atlas-tools/build-disc026-bridge.py       (applies and checks it),
  * atlas-tools/build-disc026-seo-a.py        (S5 reads through it),
  * atlas-tools/build-disc026-facts-oct2026.py (T2 reads through it), and
  * atlas-tools/build-disc026-look-again.py   (L2 reads through it).

What changes, and nothing else:
  B1  the physics section's scale sentence: CSO terminology, 2025 figure
      ("5% of Ireland's metered electricity consumption in 2015 ... By 2025
      it was 23%"); the CRU 2034 projection is unchanged
  B2  one new section, directly after "Computing and heat" and before the
      "Not here yet" transition into Home compute

Every figure is first-party and re-read on 21 Oct 2026:
  CSO, Data Centres Metered Electricity Consumption 2025 (7 Jul 2026):
      23%; 7,663 GWh (6,973 in 2024); +10%; all other users +2%; urban
      households 18%; 2015 share 5%.
  CRU decision on data-centre connections (12 Dec 2025): generation and/or
      storage matching maximum import demand; at least 80% of annual demand
      from additional Irish renewables; 6-year glide path.
  SEAI Tallaght case study: Amazon data-centre heat, County Hall, TU Dublin,
      operating since 2023 (detail in the page's own Tallaght section).
  Fjernvarme Fyn (current suppliers page) + Dansk Fjernvarme (2 Apr 2025):
      Meta surplus heat in Odense's district heating; each year equal to the
      annual heat use of 11,000 households. Ramboll: operating since late 2019.
  Fortum (6 May 2026): Hepokorpi (Espoo) and Kolabacken (Kirkkonummi) plants
      operating on air-source heat pumps and electric boilers; Microsoft
      data-centre heat "will begin step by step next year"; about 40% of the
      2 TWh yearly district heat demand once fully implemented.
  Directive (EU) 2023/1791 Art. 26(6) (EUR-Lex): >1 MW, waste heat, "unless
      they can show that it is not technically or economically feasible";
      Art. 36(1): by 11 October 2025.

with_bridge / without_bridge: exact and reversible. A partial or duplicated
state raises ValueError, so nothing else can hide behind the layer.
"""
from __future__ import annotations

PHYS_OLD = ("    <p>In Ireland this stopped being a curiosity some time ago. Data centres took\n"
            "      <strong>5% of the country&rsquo;s electricity in 2015</strong>. By\n"
            "      <strong>2024 it was 22%</strong>, and the Commission for Regulation of\n"
            "      Utilities projects <strong>31% by 2034</strong>.</p>")
PHYS_NEW = ("    <p>In Ireland this stopped being a curiosity some time ago. Data centres\n"
            "      accounted for <strong>5% of Ireland&rsquo;s metered electricity consumption\n"
            "      in 2015</strong>. By <strong>2025 it was 23%</strong>, and the Commission for\n"
            "      Regulation of Utilities projects <strong>31% by 2034</strong>.</p>")

ANCHOR = ('  </section>\n</div>\n\n<section class="spark reveal">\n'
          '  <p>Not here yet. But not hypothetical either.</p>')

BEGIN = "  <!-- PN-DISC026-BRIDGE-BEGIN · founder-approved 21 Oct 2026 · built by atlas-tools/build-disc026-bridge.py -->\n"
END = "  <!-- PN-DISC026-BRIDGE-END -->\n"

H2 = ("Almost a quarter of Ireland&rsquo;s electricity now goes to data centres.\n"
      "      Nearly all of it ends up as heat.")

SECTION = BEGIN + """  <!-- ====================================================================
       S2b . THE IRISH PICTURE. The bridge from the public question (data
       centres, electricity, grid) to the possibility the page explores.
       Every figure is first-party: CSO 7 Jul 2026, CRU 12 Dec 2025, SEAI,
       Fjernvarme Fyn / Dansk Fjernvarme, Fortum 6 May 2026, Directive (EU)
       2023/1791 Art. 26(6). The compute-at-buildings idea is NOT presented
       as a replacement for data centres or an answer to Ireland's demand.
       ==================================================================== -->
  <section class="article-section reveal" id="data-centres-ireland">
    <div class="kicker">Data centres &middot; the Irish picture</div>
    <h2>""" + H2 + """</h2>
    <span class="ev">Today &mdash; the Irish picture</span>
    <p>Data centres used <strong>23% of Ireland&rsquo;s metered electricity
      consumption in 2025</strong>: 7,663 gigawatt hours, up 10% in a single year,
      while consumption by all other users rose 2%. Urban households, taken
      together, used 18%. CSO, July 2026.</p>
    <p>That growth is why data centres have become a question about the grid, about
      electricity bills and about which new homes get connected first. Under rules
      the Commission for Regulation of Utilities confirmed in December 2025, a new
      data centre must bring generation or storage to match its demand and, over a
      six-year transition, meet at least 80% of its annual demand from new
      renewable projects in Ireland.</p>
    <p><strong>Why the heat matters.</strong> None of that electricity disappears. A
      data centre turns almost all of it into low-grade heat, and then pays to remove
      it. Irish buildings, meanwhile, pay to make heat. Where that heat is not
      recovered, it is released to the surrounding environment.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">Where data-centre heat already warms buildings</span>
      <ul class="dq-adv-cols">
        <li>
          <span class="dq-adv-label">Tallaght, Dublin</span>
          <span class="ev">Today &mdash; since 2023</span>
          <span class="dq-fact">Heat from a neighbouring Amazon data centre warms
            South Dublin County Council&rsquo;s County Hall and TU Dublin&rsquo;s
            Tallaght campus, through a council-owned, not-for-profit heat
            network.</span>
          <span class="dq-note">SEAI. The detail is in the Tallaght section
            below.</span>
        </li>
        <li>
          <span class="dq-adv-label">Odense, Denmark</span>
          <span class="ev">Today &mdash; since 2019</span>
          <span class="dq-fact">Heat pumps lift surplus heat from Meta&rsquo;s data
            centre into the city&rsquo;s district heating. Each year it supplies
            about as much heat as 11,000 households use.</span>
          <span class="dq-note">Fjernvarme Fyn, the district heating
            company.</span>
        </li>
        <li>
          <span class="dq-adv-label">Espoo and Kirkkonummi, Finland</span>
          <span class="ev ev-emerging">Emerging &mdash; from 2027</span>
          <span class="dq-fact">Fortum&rsquo;s two large heat-pump plants have run
            since May 2026, on air-source heat pumps and electric boilers for now.
            Heat from Microsoft&rsquo;s data centres is due to be added step by step
            from next year.</span>
          <span class="dq-note">Fortum expects it to cover about 40% of the
            area&rsquo;s district heat once fully in use.</span>
        </li>
      </ul>
    </div>

    <p style="margin-top:38px"><strong>The rule is changing too.</strong> EU law now
      requires member states to ensure that data centres above 1&nbsp;MW use their
      waste heat, unless the operator can show that this is not technically or
      economically feasible. Member states were due to apply that rule by October
      2025.</p>
    <p><strong>The smaller idea.</strong> Alongside these, there is a much smaller
      idea: putting the computing where heat is already wanted, instead of piping the
      heat away afterwards. Small-scale examples already exist outside Ireland, while
      in Ireland, Tandem Compute is exploring and developing systems for buildings
      with substantial, consistent heat demand. It is not a replacement for large
      data centres, and it is not an answer to Ireland&rsquo;s data-centre demand.
      What it changes is where some of the heat ends up.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">Where each one stands</span>
      <ul class="dq-adv-cols">
        <li>
          <span class="ev">Today</span>
          <span class="dq-fact">Data-centre heat warming buildings through a heat
            network.</span>
          <span class="dq-note">Tallaght, Odense.</span>
        </li>
        <li>
          <span class="ev ev-emerging">Emerging</span>
          <span class="dq-fact">Larger schemes being connected, and computing placed
            at buildings with constant heat demand.</span>
          <span class="dq-note">Espoo, from 2027. Small-scale outside Ireland; being
            developed in Ireland.</span>
        </li>
        <li>
          <span class="ev ev-future">Not yet</span>
          <span class="dq-fact">Computing in an ordinary Irish home.</span>
          <span class="dq-note">Not available to an Irish homeowner today.</span>
        </li>
      </ul>
    </div>
  </section>
""" + END


def edits():
    new_anchor = ANCHOR.replace("  </section>\n</div>", "  </section>\n\n" + SECTION + "</div>", 1)
    return [(PHYS_OLD, PHYS_NEW), (ANCHOR, new_anchor)]


def with_bridge(text: str) -> str:
    out = text
    for old, new in edits():
        if out.count(old) != 1 or new in out:
            raise ValueError("bridge layer: anchor not found exactly once in the base state: " + old[:70])
        out = out.replace(old, new, 1)
    return out


def without_bridge(text: str) -> str:
    pairs = edits()
    present = [new in text for _, new in pairs]
    if not any(present) and BEGIN not in text:
        return text
    if not all(present):
        raise ValueError("bridge layer: the page carries only part of the governed change")
    out = text
    for old, new in pairs:
        if out.count(new) != 1 or old in out:
            raise ValueError("bridge layer: a governed string is duplicated or mixed with its original")
        out = out.replace(new, old, 1)
    if BEGIN in out or with_bridge(out) != text:
        raise ValueError("bridge layer is not an exact, reversible edit")
    return out
