#!/usr/bin/env python3
"""Build/check the PlotArt "For artists" page (plotart/for-artists.html, founder brief 17 Nov 2026).

A plain information page for artists already in PlotArt: one "Open My Studio" button to the existing PlotArt Studio, how
signing in works, getting started, and help with signing in. It adds NO login of its own: signing in stays entirely with
the Studio's existing Cloudflare Access one-time code (the Studio then recognises only the email address it is registered
to). An email box on plotnua.ie that hands off to Access is not offered: Access documents no supported way to prefill or
pass an email to its sign-in page, so it would mean a second, unsupported login path.

Instructions here describe the Studio as it is (ui/studio.js labels: Your profile, Your works, Add an artwork, Review and
submit, Opportunities & delivery). No private artist information appears. Outside the main navigation; reached from the
PlotArt footer ("For artists", "Artist Studio").

  python3 atlas-tools/build-plotart-for-artists.py            build plotart/for-artists.html
  python3 atlas-tools/build-plotart-for-artists.py --check    write nothing; refuse if the page differs
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import json                 # noqa: E402
import plotart_shell as S   # noqa: E402

# the Art for Hire tab follows the launch switch, as on the published galleries (plotart-gallery-publish.py)
HIRE = json.load(open(ROOT / "atlas-tools" / "release" / "plotart-launch-switches.json", encoding="utf-8")).get("art_for_hire_page") is True

PATH = "for-artists.html"
TITLE = "For Artists: Your PlotArt Studio | PlotArt"
DESC = ("For PlotArt artists: open your PlotArt Studio, sign in with your registered email address and a one-time code, "
        "and look after your gallery, artworks, availability and opportunities.")

BODY = """
<section class="pa-sec pa-sec--deep pa-fa-hero" aria-labelledby="faH"><div class="pa-wrap">
  <p class="pa-eyebrow">PlotArt · For artists</p>
  <h1 id="faH">Your PlotArt Studio.</h1>
  <p class="pa-lede">Your Studio is where you look after your PlotArt gallery: your profile, your artworks, their availability and the opportunities you’re open to.</p>
  <div class="pa-actions"><a class="pa-btn pa-btn--solid" href="%(studio)s" data-pa-track="for_artists_open_studio">Open My Studio</a></div>
  <p class="pa-fa-note">Sign in with the email address your Studio is registered to, the one in your invitation email. We’ll email you a one-time code; there’s no password.</p>
</div></section>

<section class="pa-sec pa-fa-sec" aria-labelledby="faStartH"><div class="pa-wrap pa-fa-grid">
  <h2 id="faStartH">Getting started</h2>
  <ol class="pa-steps">
    <li><div><h3>Sign in to your Studio</h3><p>Choose “Open My Studio”, enter your registered email address and select “Send login code”. Enter the code from the email to reach your Studio.</p></div></li>
    <li><div><h3>Set up your gallery</h3><p>In “Your profile”, add your portrait photograph, your practice and a short statement. Changes save as you go and stay private until your gallery is published.</p></div></li>
    <li><div><h3>Add your artworks</h3><p>In “Your works”, choose “Add an artwork”, add its main photograph and fill in the details: title, year, medium, size and price.</p></div></li>
    <li><div><h3>Submit for approval</h3><p>When you’re ready, open “Review and submit” and choose “Submit for review”. Before your gallery is first published, you’ll be asked to read and accept your artist agreement. PlotArt checks each submission, including the image details, before it goes live.</p></div></li>
    <li><div><h3>Keep availability up to date</h3><p>Mark each work as Available, Reserved, Sold or Not for sale. Changes to availability, and to the order of your works, go to your live gallery without a new review.</p></div></li>
    <li><div><h3>Choose further opportunities</h3><p>In “Opportunities &amp; delivery”, say which PlotArt opportunities you’d be open to, such as the Living Gallery, Art for Hire, the Mobile Gallery or exhibitions, and whether they may be shown on your public gallery. To receive commission enquiries, switch on “Open for commissions” in your profile.</p></div></li>
  </ol>
</div></section>

<section class="pa-sec pa-sec--deep pa-fa-sec" aria-labelledby="faHelpH"><div class="pa-wrap pa-fa-grid">
  <h2 id="faHelpH">Having trouble?</h2>
  <dl class="pa-fa-help">
    <dt>The code hasn’t arrived</dt>
    <dd>Check your spam or junk folder. Codes are only sent to the email address your Studio is registered to, so check that you typed it exactly.</dd>
    <dt>The code doesn’t work</dt>
    <dd>Each code lasts 10 minutes, and asking for a new code cancels the previous one. Use the most recent code only, or request a new one.</dd>
    <dt>“We couldn’t find an active PlotArt Studio account”</dt>
    <dd>You’ve signed in with a different email address, even if it’s another one of your own. Sign out, then sign in again with the address shown in your invitation email.</dd>
    <dt>Your email address has changed</dt>
    <dd>Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> from your registered address, and we’ll move your Studio to the new one.</dd>
    <dt>Still stuck?</dt>
    <dd>Email <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a> with your name. Never send us your login code.</dd>
  </dl>
</div></section>

<section class="pa-sec pa-fa-sec pa-fa-join"><div class="pa-wrap">
  <p>Not a PlotArt artist yet? Read about <a href="join.html">joining PlotArt</a>.</p>
</div></section>
""" % {"studio": S.STUDIO}


def render():
    return S.artist_page(PATH, TITLE, DESC, BODY, current="none", hire_nav=HIRE, styles=("assets/plotart-for-artists.css",))[1]


def main():
    page = ROOT / "plotart" / PATH
    want = render()
    if "--check" in sys.argv:
        if not page.exists() or page.read_text(encoding="utf-8") != want:
            raise SystemExit("FOR ARTISTS · plotart/%s differs from its reviewed source (rebuild and review)" % PATH)
        print("FOR ARTISTS · OK — plotart/%s matches its source; nothing written" % PATH)
        return
    page.write_text(want, encoding="utf-8")
    print("FOR ARTISTS · built plotart/%s" % PATH)


if __name__ == "__main__":
    main()
