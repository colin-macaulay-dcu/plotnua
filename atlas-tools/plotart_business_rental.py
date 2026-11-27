"""Founder-approved business rental information, 16 November 2026; presented under the PlotArt communication standard
(founder approval, 27 November 2026), with PlotArt coordinating every placement. Every rate, split and protection kept.

One bounded, exact section in the existing Art for Hire page. This is published
information only: it never lists work, opens enquiries or changes artist terms.
"""
BEGIN = "<!-- plotart-business-rentals:begin -->"
END = "<!-- plotart-business-rentals:end -->"
TERMS_BEGIN = "<!-- plotart-business-terms:begin -->"
TERMS_END = "<!-- plotart-business-terms:end -->"
PDF = "downloads/plotart-business-rental-artist-guide-and-agreement.pdf"
SELECTION = "mailto:hello@plotnua.ie?subject=Art%20for%20Hire%3A%20request%20a%20selection"
BRIEF = "mailto:hello@plotnua.ie?subject=Art%20for%20Hire%3A%20project%20brief"
# PlotArt communication standard (founder approval, 27 Nov 2026): the approved 16 Nov terms, presented as the offer at a
# glance, two ways to hire, a numbered process and clear monthly pricing, with PlotArt coordinating every placement.
# Every rate, split, term and protection is kept; the long explanations live in the bounded terms region (expandable).
REGION = BEGIN + """
<section class="afx-sec" id="business-rentals" aria-label="Business rental at a glance"><div class="pa-wrap">
  <div class="afx-figs">
    <div class="afx-fig"><span class="afx-num">4<small>%</small></span><p>of the artwork’s price, per month.</p></div>
    <div class="afx-fig"><span class="afx-num">6<small>months</small></span><p>Initial term. Replacements if a work sells.</p></div>
    <div class="afx-fig"><span class="afx-num">1<small>contact</small></span><p>PlotArt coordinates the placement with the artist.</p></div>
  </div>
</div></section>

<section class="afx-sec" aria-labelledby="afx-offers-h"><div class="pa-wrap">
  <div class="afx-head"><h2 class="afx-h2" id="afx-offers-h">Two ways to hire.</h2><p class="afx-lede">A monthly rental for the spaces you work in, or a short hire for a single project.</p></div>
  <div class="afx-offers">
    <article class="afx-offer afx-offer--main">
      <h3>Business rental</h3><p class="afx-for">Offices, hotels, clinics and shared workspaces.</p>
      <dl><dt>Price</dt><dd>4% of the artwork’s price, per month</dd><dt>Term</dt><dd>Six months to start</dd><dt>Costs</dt><dd>Transport, installation and insurance quoted up front</dd><dt>Buying</dt><dd>Every work stays for sale</dd></dl>
      <p class="afx-acts"><a class="afx-btn" href="mailto:hello@plotnua.ie?subject=Art%20for%20Hire%3A%20request%20a%20selection" data-pa-track="hire_request_selection">Request a selection</a></p>
    </article>
    <article class="afx-offer">
      <h3>Project hire</h3><p class="afx-for">Interiors, property staging, photography and events.</p>
      <dl><dt>Price</dt><dd>Quoted per project</dd><dt>Term</dt><dd>Days or weeks</dd><dt>Screen use</dt><dd>Film and TV can’t yet be arranged</dd></dl>
      <p class="afx-acts"><a class="afx-link" href="mailto:hello@plotnua.ie?subject=Art%20for%20Hire%3A%20project%20brief" data-pa-track="hire_project_brief">Send a project brief →</a></p>
    </article>
  </div>
</div></section>

<section class="afx-sec" id="afh3-how" aria-labelledby="afx-how-h"><div class="pa-wrap">
  <div class="afx-head"><h2 class="afx-h2" id="afx-how-h">How it works.</h2><p class="afx-lede">One conversation with PlotArt, from first brief to the work on your wall.</p></div>
  <ol class="afx-steps">
    <li><span class="n">01</span><h3>Tell us about the space</h3><p>Location, wall sizes, number of works, budget and dates.</p></li>
    <li><span class="n">02</span><h3>Choose from a selection</h3><p>We propose works that their artists have approved for hire, with exact monthly costs.</p></li>
    <li><span class="n">03</span><h3>Agree it once</h3><p>One written placement agreement, with transport, installation and insurance confirmed before anything moves.</p></li>
    <li><span class="n">04</span><h3>Live with it</h3><p>If a work sells, we arrange a replacement, or that placement ends without penalty.</p></li>
  </ol>
</div></section>

<section class="afx-sec afx-sec--wall" id="pricing" aria-labelledby="afx-price-h"><div class="pa-wrap">
  <div class="afx-price">
    <div>
      <h2 class="afx-h2" id="afx-price-h">Clear monthly pricing.</h2>
      <p class="afx-eg">A €2,000 painting<b>€80 a month</b></p>
      <p class="afx-split"><strong>3% to the artist and 1% to PlotArt</strong>: €60 and €20 of the €80.</p>
    </div>
    <div>
      <table class="afx-table"><caption class="pa-skip">Monthly rental by artwork price</caption>
        <thead><tr><th scope="col">Artwork price</th><th scope="col">Per month</th><th scope="col">Six months</th></tr></thead>
        <tbody><tr><th scope="row">€1,000</th><td>€40</td><td>€240</td></tr><tr><th scope="row">€2,000</th><td>€80</td><td>€480</td></tr><tr><th scope="row">€3,000</th><td>€120</td><td>€720</td></tr><tr><th scope="row">€5,000</th><td>€200</td><td>€1,200</td></tr></tbody>
      </table>
      <p class="afx-note">Transport, installation, insurance and any VAT are quoted separately and paid by the business. Rent is not credited towards buying a work. Your written proposal shows the actual total before you commit.</p>
    </div>
  </div>
</div></section>
""" + END
TERMS = TERMS_BEGIN + """
<section class="afx-sec" id="details" aria-labelledby="afx-terms-h"><div class="pa-wrap">
  <div class="afx-head"><h2 class="afx-h2" id="afx-terms-h">The details.</h2><p class="afx-lede">The full terms, for when you need them.</p></div>
  <div class="afx-details">
    <details id="sale-first"><summary>If a work sells</summary><div><p>Buying is the priority: every work stays for sale while it is on rent. The standard notice is 30 calendar days. We propose a replacement for you to approve. If none is agreed within seven days of removal, that placement ends without penalty, and unused prepaid charges are refunded within 14 days. No rent is charged for an uncovered gap, and a replacement does not restart the six months.</p></div></details>
    <details id="rental-insurance"><summary>Insurance</summary><div><p>The renting business pays for artwork insurance at the agreed value, covering packing, transport, installation, display, removal and return. Ordinary business cover or a courier’s cover is not automatically enough. Cover is confirmed before any work moves. PlotArt doesn’t provide insurance, and the artist is not expected to buy placement cover.</p></div></details>
    <details id="rental-delivery"><summary>Delivery and installation</summary><div><p>The renting business pays the approved packing, delivery, hanging, removal and return, quoted in writing before booking, including agreed sale changeovers. Neither artist nor PlotArt is expected to advance these costs. Large or fragile works may need specialist art handlers; either side can propose a provider from <a href="../services.html">Art Services &amp; Providers</a>. The artist approves the handling arrangements and doesn’t need to attend unless agreed. Condition photographs are taken on arrival and after hanging.</p></div></details>
    <details id="rental-direct"><summary>Payments and agreements</summary><div><p>PlotArt prepares the paperwork and coordinates the placement. The hire agreement itself is between you and the artist, and PlotArt’s fee is a separate agreement with PlotArt. The artist’s share and PlotArt’s fee are invoiced separately, on the same schedule. Each artist approves the work, price basis and actual amounts before any proposal. Any change to the standard rate needs everyone’s written agreement. Existing artist gallery and founding terms are unchanged.</p></div></details>
    <details id="rental-project"><summary>Project hire, film, television and photography</summary><div><p>Project hire is quoted per project, and the hire terms are agreed with the artist. Hire doesn’t include permission to film, photograph or reproduce a work: any photography permission is agreed in writing with the artist. Film and television screen use can’t yet be arranged through PlotArt.</p></div></details>
  </div>
</div></section>
""" + TERMS_END
ARTIST_LINE = ('<p class="afx-artist-line">Are you a PlotArt artist? <a href="../' + PDF + '?v=1.1" download>Read the artist guide and agreement (PDF)</a>'
               ' <span class="afx-ver">PA-BHR-2026-11 · Version 1.1 · 16 November 2026</span></p>')

def outside(doc):
    """Remove only the two exact approved regions (the offer and the terms); anything else in them is refused."""
    for begin, end, text in ((BEGIN, END, REGION), (TERMS_BEGIN, TERMS_END, TERMS)):
        if doc.count(begin) != 1 or doc.count(end) != 1:
            raise ValueError("business rental information needs exactly one bounded %s region" % begin.split()[1].split(":")[0])
        a, b = doc.index(begin), doc.index(end) + len(end)
        if doc[a:b] != text:
            raise ValueError("business rental wording, figures or download differ from the approved section")
        doc = doc[:a] + doc[b:]
    return doc

def verify_document(site, tools_root):
    """Bind the downloadable PDF to the reviewed template source, without PDF dependencies."""
    from pathlib import Path
    import hashlib
    import json
    record = json.loads((Path(tools_root) / "atlas-tools/plotart-business-rental-document.json").read_text())
    source = (Path(tools_root) / "atlas-tools/plotart-business-rental-terms.md").read_bytes()
    pdf = (Path(site) / "plotart" / PDF).read_bytes()
    if record.get("version") != "PA-BHR-2026-11-v1.1":
        raise ValueError("unexpected business rental document version")
    if hashlib.sha256(source).hexdigest() != record.get("source_sha256"):
        raise ValueError("rental template source differs from its verified document record")
    if hashlib.sha256(pdf).hexdigest() != record.get("pdf_sha256") or not pdf.startswith(b"%PDF-"):
        raise ValueError("rental PDF differs from its verified document record")
    return True


