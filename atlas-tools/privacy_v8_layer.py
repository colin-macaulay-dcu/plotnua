"""PlotNua · Privacy Notice V8 layer (2026-10-PHASE2-V8): PlotArt artist galleries, PlotArt Studio and buyer
enquiries to PlotArt artists.

PREPARED FOR FOUNDER APPROVAL (29 Oct 2026; Phase 3). Source: the approved Phase 0 privacy draft (section C of
"Essential corrections", founder approval 29 Oct 2026) and the Phase 3 enquiry relay. NOT PUBLISHED.

V8 is a set of EXACT, REVERSIBLE additions on top of the published V7 page, like V7 itself:
  S8   Section 8: two sub-sections after "PlotArt Founding 25 applications (artists)":
       "PlotArt artist galleries and PlotArt Studio (artists)" and "Enquiries to PlotArt artists (buyers)".
  S10  Section 10: one line on the PlotArt Studio service and one on enquiry emails.
  S12  Section 12: one added line.
  F1/F2 Section 8, Founding 25 applications: artwork images (29 Oct 2026): two sentences changed, one paragraph added.
without_v8() returns the exact V7 page, so every earlier verifier keeps reading the text it governs
(privacy_v7_layer.without_v7 takes V8 off first).
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-PRIVACY-V8"
VERSION = "2026-10-PHASE2-V8"

S8_ANCHOR = ("You also have the other rights described in Section 14, including the right to object to processing based on our legitimate interests.</p>\n"
             "  </section>")
GALLERIES_SUB = f"""  <!-- {MARKER} · PlotArt artist galleries, PlotArt Studio and enquiries, privacy notice {VERSION} -->
    <h3 class="pv5-sub" id="plotart-galleries">PlotArt artist galleries and PlotArt Studio (artists)</h3>
    <p>If you become a PlotArt artist, you manage your gallery through PlotArt Studio, a private account you sign in to with a one-time code sent to your email address.</p>
    <p>What we hold for your gallery:</p>
    <ul>
      <li>your name and the email address you sign in with, and a record of your sign-ins, which our sign-in provider keeps for security;</li>
      <li>your biography and statement, your portrait if you add one, your county if you choose to show it, and links to your website or Instagram if you add them;</li>
      <li>your artworks' details and photographs, who took each photograph, and your declaration of any meaningful use of AI in making a work; and</li>
      <li>the version and date of the gallery licence you accepted, and a record of the changes you and we make to your gallery and of our review decisions.</li>
    </ul>
    <p>We use this information to run your gallery under your artist agreement. We show your county and your portrait only if you choose to, on the basis of your consent, which you can withdraw at any time in PlotArt Studio or by emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. We keep sign-in and change records, and a record of what was published and when, because we have a legitimate interest in keeping accounts and the gallery secure and accountable.</p>
    <p>Only what you approve is published, as it appears in your gallery. Before a photograph is published, hidden file information, including camera and location data, is removed. Your email address is never published.</p>
    <p>PlotArt Studio runs on infrastructure provided by Cloudflare. Your photographs are stored in the European Union. Published gallery pages are served from the same hosting as the rest of this website.</p>
    <p>We keep your account, your gallery records and your original photographs while you take part and for 12 months afterwards. Photographs you remove are deleted within 30 days. We keep a record of what was published and when, without images, for the records of the founding programme and of enquiries.</p>
    <h3 class="pv5-sub" id="plotart-enquiries">Enquiries to PlotArt artists (buyers)</h3>
    <p>If you send an enquiry about an artwork or an artist through a PlotArt gallery, we collect your name, your email address and your message, together with the artwork and the time you sent it.</p>
    <p>We pass your name, email address and message to the artist so that they can reply to you directly, and we send you a short confirmation. We do this to deal with your request, as a step you have asked us to take, and because we have a legitimate interest in keeping a record of the enquiries PlotArt introduces to artists. The artist then handles your enquiry and any sale directly with you; PlotArt does not take payment or arrange delivery.</p>
    <p>A simple hidden form field and limits on repeated enquiries keep the form free of spam. They do not use cookies, and we do not store your IP address.</p>
    <p>We keep the record of each enquiry for 24 months and then delete it. You can ask us to delete it sooner by emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>; the artist you contacted keeps any email you exchange with them under their own responsibility.</p>
"""
S8_OLD = S8_ANCHOR
S8_NEW = S8_ANCHOR.replace("  </section>", GALLERIES_SUB + "  </section>")
S10_OLD = "    <p>PlotNua's email, including hello@plotnua.ie, is provided by Google Workspace.</p>\n"
S10_NEW = S10_OLD + ("    <p>PlotArt Studio and PlotArt enquiries, described in Section 8, use services provided by Cloudflare, "
                     "with artists' photographs stored in the European Union.</p>\n"
                     "    <p>Enquiry emails to artists and confirmations to buyers are sent by an email delivery service acting for PlotNua under its data processing terms.</p>\n")
S12_OLD = "    <p>PlotArt Founding 25 applications are kept for the periods described in Section 8.</p>\n"
S12_NEW = S12_OLD + "    <p>PlotArt gallery records are kept while an artist takes part and for 12 months afterwards, and enquiries to artists for 24 months, as described in Section 8.</p>\n"
# F25 (29 Oct 2026, development approved): artwork images with a Founding 25 application. Two existing V7 sentences
# change and one paragraph is added; still exact and reversible.
F1_OLD = "      <li>your primary medium, a short biography you write, and a link to your portfolio or work;</li>\n"
F1_NEW = "      <li>your primary medium and a short biography you write, and images of your work that you upload (up to five), a link to your portfolio, or both;</li>\n"
F2_OLD = ("    <p>We do not ask for your home address, your phone number, your date of birth or images of your work when you apply. "
          "Please don't include health or other sensitive personal details in your biography.</p>\n")
F2_NEW = ("    <p>We do not ask for your home address, your phone number or your date of birth when you apply. "
          "Please don't include health or other sensitive personal details in your biography.</p>\n"
          "    <p>If you upload images of your work, your browser first makes a smaller copy of each one, which also removes hidden file information such as "
          "camera and location data. The images are stored privately in the European Union by Cloudflare, separately from anything published in PlotArt "
          "galleries. We use them only to consider your application: they are never published, and you can ask us to delete them at any time. Images you "
          "remove before you apply, or that are not sent with an application, are deleted automatically within a day. We keep the images sent with an "
          "application for as long as we keep the application, as described below, and delete them with it.</p>\n")
PAIRS = [(S8_OLD, S8_NEW), (S10_OLD, S10_NEW), (S12_OLD, S12_NEW), (F1_OLD, F1_NEW), (F2_OLD, F2_NEW)]


def apply_v8(text: str) -> str:
    if MARKER in text:
        raise ValueError("V8 already applied")
    if "PLOTNUA-F25-PRIVACY-V7" not in text:
        raise ValueError("V8 applies on top of V7 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V8 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v8(text: str) -> str:
    """The exact V7 page beneath V8. A page without V8 passes through untouched; a page that carries the V8 marker
    but not exactly the governed V8 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V8 marker but not exactly the governed V8 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v8(out) != text:
        raise ValueError("privacy.html V8 layer is not an exact, reversible edit")
    return out
