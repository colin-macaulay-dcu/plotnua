#!/usr/bin/env python3
"""Build/check the PlotArt "Art Services & Providers" page (plotart/services.html, founder brief 19 Nov 2026).

A plain, restrained listing of independent providers who have explicitly agreed to be listed on PlotArt. They are not
partners, PlotArt does not arrange, supervise or guarantee their work, and customers arrange quotations, services and
insurance directly with them. No logos or provider photographs (no image permissions held). Details are as supplied by
each provider (founder brief); the prices are the provider's own and are the only prices this page may show.

  python3 atlas-tools/build-plotart-services.py            build plotart/services.html
  python3 atlas-tools/build-plotart-services.py --check    write nothing; refuse if the page differs
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import json                 # noqa: E402
import plotart_shell as S   # noqa: E402

HIRE = json.load(open(ROOT / "atlas-tools" / "release" / "plotart-launch-switches.json", encoding="utf-8")).get("art_for_hire_page") is True

PATH = "services.html"
TITLE = "Art Services & Providers | PlotArt"
DESC = ("Independent art handling and picture hanging providers in Ireland: specialist art transport, delivery and "
        "installation, and professional artwork hanging. Contact each provider directly.")

# the provider's own pricing, exactly as supplied (the launch guard allows this text, and only this, to show a price)
HANGIT_PRICES = "€70 call-out, then €60 an hour for labour. Materials and parking are extra."

BODY = """
<section class="pa-sec pa-sec--deep pa-sv-hero" aria-labelledby="svH"><div class="pa-wrap">
  <p class="pa-eyebrow">PlotArt · Services</p>
  <h1 id="svH">Art Services &amp; Providers</h1>
  <p class="pa-lede">Independent specialists who can help once you’ve chosen a work: moving it safely, and hanging it well.</p>
  <p class="pa-sv-note">These are independent businesses, listed with their agreement. They aren’t PlotArt partners, and PlotArt doesn’t arrange, supervise or guarantee their work. You arrange quotations, services and insurance directly with each provider.</p>
</div></section>

<section class="pa-sec pa-sv-sec" aria-label="Providers"><div class="pa-wrap pa-sv-list">

  <article class="pa-sv-card" aria-labelledby="svMW">
    <h2 id="svMW">Maurice Ward Art Handling</h2>
    <p class="pa-sv-what">Specialist art transport, delivery, unpacking and installation.</p>
    <dl class="pa-sv-facts">
      <dt>Quotations</dt><dd>Each job is quoted individually.</dd>
      <dt>Insurance</dt><dd>Transit insurance is arranged separately, by you.</dd>
    </dl>
    <p class="pa-sv-contact">
      <a class="pa-btn pa-btn--ghost" href="https://mauriceward-arthandling.com/" rel="noopener" target="_blank" data-pa-track="services_mauriceward_web">Website <span aria-hidden="true">↗</span><span class="pa-sr"> (opens in a new tab)</span></a>
      <a class="pa-btn pa-btn--ghost" href="mailto:movingart@mauriceward.com" data-pa-track="services_mauriceward_email">Email movingart@mauriceward.com</a>
    </p>
  </article>

  <article class="pa-sv-card" aria-labelledby="svHI">
    <h2 id="svHI">Hang-It</h2>
    <p class="pa-sv-what">Professional artwork and picture hanging and installation.</p>
    <dl class="pa-sv-facts">
      <dt>Area</dt><dd>Mainly Dublin. Other locations may be possible, at extra cost.</dd>
      <dt>Prices from Hang-It</dt><dd>%(hangit_prices)s</dd>
      <dt>Insurance</dt><dd>Fully insured, according to Hang-It.</dd>
      <dt>Please note</dt><dd>Hang-It doesn’t transport artwork.</dd>
    </dl>
    <p class="pa-sv-contact">
      <a class="pa-btn pa-btn--ghost" href="https://www.hangit.ie/" rel="noopener" target="_blank" data-pa-track="services_hangit_web">Website <span aria-hidden="true">↗</span><span class="pa-sr"> (opens in a new tab)</span></a>
      <a class="pa-btn pa-btn--ghost" href="https://wa.me/353876634458" rel="noopener" target="_blank" data-pa-track="services_hangit_whatsapp">WhatsApp 087 663 4458<span class="pa-sr"> (opens WhatsApp)</span></a>
    </p>
  </article>

</div></section>

<section class="pa-sec pa-sv-sec pa-sv-foot"><div class="pa-wrap">
  <p>Details and prices are as supplied by each provider and may change, so please confirm them directly. Listing a provider isn’t a recommendation for any particular job, and other providers may be listed in future.</p>
</div></section>
""" % {"hangit_prices": HANGIT_PRICES}


FINE = ("Artworks in PlotArt galleries are offered by their artists: PlotArt introduces buyers and doesn't take payment. "
        "Providers listed on this page are independent businesses, not PlotArt partners, and PlotArt doesn't guarantee their services.")


def render():
    return S.artist_page(PATH, TITLE, DESC, BODY, current="services", hire_nav=HIRE, fine=FINE, styles=("assets/plotart-services.css",))[1]


def main():
    page = ROOT / "plotart" / PATH
    want = render()
    if "--check" in sys.argv:
        if not page.exists() or page.read_text(encoding="utf-8") != want:
            raise SystemExit("SERVICES · plotart/%s differs from its reviewed source (rebuild and review)" % PATH)
        print("SERVICES · OK — plotart/%s matches its source; nothing written" % PATH)
        return
    page.write_text(want, encoding="utf-8")
    print("SERVICES · built plotart/%s" % PATH)


if __name__ == "__main__":
    main()
