"""PlotNua · Privacy Notice V7 layer (2026-10-PHASE2-V7): PlotArt Founding 25 applications,
business-name details and the PlotNua footer.

DRAFT FOR FOUNDER APPROVAL (28 Oct 2026). The ONE definition of the V7 changes,
shared by build-privacy-v7.py, prove-privacy-v7.py, privacy_page_layers.py and
build-artist-register.py.

Sources: Privacy Notice V7 legal-review draft r7 (lean-launch corrections C1-C4,
C10), the Record of Processing v1.1 (28 Oct 2026) and the legal-information
release (production 2c89865).

V7 is a set of EXACT, REVERSIBLE replacements of the published V6 page:
  S1   Section 1: the controller's name in the certificate spelling, plus one
       sentence on the registered business name (No. 794392) and PlotArt.
  S2   Section 2: one added line.
  S8   Section 8: the "PlotArt Founding 25 applications (artists)" sub-section
       (C1 required details; C2 Google Workspace; C10 waiting-list consent).
  S10  Section 10: one line on the application service, one on Google Workspace.
  S12  Section 12: one added line.
  S14  Section 14: firm rights wording (C3).
  S15  Section 15: firm complaint wording with the DPC's address (C3).
  FOOT the footer column heading "Company" -> "PlotNua", plus a Legal information link.
The WhatsApp subsection (Section 5) is NOT changed by V7 (C4 is deferred until
the founder's WhatsApp checks V1-V4).

without_v7() returns the exact V6 page, so every earlier verifier (V3-V6, the
Art Space and Artist Registers) keeps reading byte for byte the text it governs.
"""
from __future__ import annotations

MARKER = "PLOTNUA-F25-PRIVACY-V7"
VERSION = "2026-10-PHASE2-V7"

S1_OLD = ('    <p>PlotNua is an independent website operated by Colin MacAulay, who is the data controller for the personal information processed through this website. '
          'PlotNua explores new possibilities for residential property in Ireland and helps homeowners discover ideas, information and, where appropriate, independent suppliers.</p>\n')
S1_NEW = ('    <p>PlotNua is an independent website operated by Colin Macaulay, who is the data controller for the personal information processed through this website. '
          'PlotNua explores new possibilities for residential property in Ireland and helps homeowners discover ideas, information and, where appropriate, independent suppliers.</p>\n'
          f'    <!-- {MARKER} · business name, privacy notice {VERSION} -->\n'
          '    <p>PlotNua is a business name registered with the Companies Registration Office (Business Name Registration No. 794392) by Colin Macaulay, who runs it as an individual; it is not a company. '
          'PlotArt is an initiative of PlotNua. Our full business details are on our <a href="terms.html#legal-information">Legal information</a> page.</p>\n')

S2_OLD = "    <p>If you choose to join the Artist Register, we also collect the information described in Section 8.</p>\n"
S2_NEW = S2_OLD + "    <p>If you apply to the PlotArt Founding 25, we also collect the information described in Section 8.</p>\n"

F25_SUB = f"""  <!-- {MARKER} · PlotArt Founding 25 applications, privacy notice {VERSION} -->
    <h3 class="pv5-sub" id="founding-25-applications">PlotArt Founding 25 applications (artists)</h3>
    <p>PlotArt, an initiative of PlotNua, is inviting artists based or working on the island of Ireland to apply to become one of up to 25 Founding Artists, the first artists in the PlotArt Virtual Gallery. Applications are reviewed individually, and places are awarded through a curated selection, not on a first-come, first-served basis. Applying is separate from the Artist Register: it does not add you to the Artist Register, and being on the Artist Register does not count as an application.</p>
    <p>What we collect when you apply:</p>
    <ul>
      <li>the name you work under, your email address and your county;</li>
      <li>your primary medium, a short biography you write, and a link to your portfolio or work;</li>
      <li>if you choose to give them, your website, an Instagram handle or professional profile link, and anything else you tell us;</li>
      <li>your confirmations that you are 18 or over and based or working on the island of Ireland, that the work is your own or that you are authorised to represent the artist, and that you have read this notice; and</li>
      <li>which version of that wording and of this notice applied, and when you applied.</li>
    </ul>
    <p>The details marked as required are needed for us to consider your application. If you don't provide them, we can't review it. The optional details are up to you.</p>
    <p>We do not ask for your home address, your phone number, your date of birth or images of your work when you apply. Please don't include health or other sensitive personal details in your biography.</p>
    <p>We use this information to review your application and to contact you about it. We do this because you have asked us to consider your application, as a step before any agreement is made. We keep a record of each decision and of the wording you confirmed because we have a legitimate interest in running a fair and accountable selection, and we use simple technical checks, such as a hidden form field and limits on repeated submissions, to keep the form free of spam, which is also in our legitimate interests. These checks do not use cookies. Every application is read and decided by a person. We do not use automated decision-making or profiling to select artists.</p>
    <p>Applying is only a request to be considered. It does not make you a member of PlotArt or give you a place. If you are selected, accepting a Founding Artist place happens separately, under the Founding Artist terms, and you have 30 days to accept an offer. Nothing about you or your work is published unless and until you approve your artist gallery. Applying does not give us permission to publish anything.</p>
    <p>Your application is stored privately and is not published. It is accessible only to the person at PlotNua who reviews applications, and to our service providers where necessary to operate the form. Applications are kept in the same database as the Artist Register but in a separate table, and are sent and stored by the same service providers, in the same way, as described above for the Art Space Register. We reply to you by email from <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>, which runs on Google Workspace. Google may process this information outside the European Economic Area; where it does, it relies on the safeguards in its data processing terms, including the EU&ndash;US Data Privacy Framework and standard contractual clauses.</p>
    <p>How long we keep your application: if it is not selected, is withdrawn, or a place offered is not taken up, for 12 months after that decision; if it has not been decided, for no more than 12 months after you applied. If you become a Founding Artist, we keep your application for as long as you take part and for 12 months afterwards, and any record we are required by law to keep is kept only for as long as the law requires.</p>
    <p>If you agree to join our waiting list, we keep your application on the basis of your consent, which you can withdraw at any time by emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. We will ask you again before keeping it on the waiting list for longer than 12 months.</p>
    <p>If you become a Founding Artist, we will also use your contact details to manage your Founding Artist agreement and to prepare your gallery with you. Anything published about you or your work is published only with your approval, under the separate gallery terms, and this notice will be updated before any artist gallery is published.</p>
    <p>You can withdraw your application, correct it, or ask us to delete it at any time by emailing <a href="mailto:hello@plotnua.ie">hello@plotnua.ie</a>. When we delete an application, we delete everything we hold about it, including the record of the wording you confirmed, and the same arrangements for our database provider's trash and recovery copies, and for our anonymous deletion log, apply as described above for the Art Space Register. You also have the other rights described in Section 14, including the right to object to processing based on our legitimate interests.</p>
"""

S8_OLD = "as described above for the Art Space Register.</p>\n  </section>"
S8_NEW = "as described above for the Art Space Register.</p>\n" + F25_SUB + "  </section>"

S10_OLD = ("    <p>The Artist Register described in Section 8 uses the same PlotNua service on infrastructure provided by Cloudflare, "
           "and the same Airtable database, as the Art Space Register, with artist registrations kept as separate records in their own table.</p>\n")
S10_NEW = S10_OLD + ("    <p>PlotArt Founding 25 applications described in Section 8 use the same PlotNua service on infrastructure provided by Cloudflare, "
                     "and the same Airtable database, as the Artist Register, with applications kept as separate records in their own table.</p>\n"
                     "    <p>PlotNua's email, including hello@plotnua.ie, is provided by Google Workspace.</p>\n")

S12_OLD = "    <p>Artist Register records are kept for a maximum of 12 months, as described in Section 8.</p>\n"
S12_NEW = S12_OLD + "    <p>PlotArt Founding 25 applications are kept for the periods described in Section 8.</p>\n"

S14_OLD = "    <p>Subject to applicable law, visitors may have rights including:</p>\n"
S14_NEW = "    <p>Visitors have the following rights, subject to the conditions set out in data protection law:</p>\n"

S15_OLD = ("They may also have the right to lodge a complaint with the Data Protection Commission in Ireland "
           "or another relevant supervisory authority.</p>\n")
S15_NEW = ("They also have the right to lodge a complaint with the Data Protection Commission in Ireland "
           '(<a href="https://www.dataprotection.ie" target="_blank" rel="noopener noreferrer">www.dataprotection.ie</a>) '
           "or another relevant supervisory authority.</p>\n")

FOOT_OLD = ('        <h2>Company</h2>\n        <ul>\n          <li><a href="about.html">About PlotNua</a></li>\n'
            '          <li><a href="privacy.html">Privacy Policy</a></li>\n          <li><a href="terms.html">Terms of Use</a></li>\n')
FOOT_NEW = ('        <h2>PlotNua</h2>\n        <ul>\n          <li><a href="about.html">About PlotNua</a></li>\n'
            '          <li><a href="privacy.html">Privacy Policy</a></li>\n          <li><a href="terms.html">Terms of Use</a></li>\n'
            '          <li><a href="terms.html#legal-information">Legal information</a></li>\n')

NOTICE_PAIRS = [(S1_OLD, S1_NEW), (S2_OLD, S2_NEW), (S8_OLD, S8_NEW), (S10_OLD, S10_NEW),
                (S12_OLD, S12_NEW), (S14_OLD, S14_NEW), (S15_OLD, S15_NEW)]
PAIRS = NOTICE_PAIRS + [(FOOT_OLD, FOOT_NEW)]


def apply_v7(text: str) -> str:
    if MARKER in text:
        raise ValueError("V7 already applied")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V7 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v7(text: str) -> str:
    """The exact V6 page beneath V7. A page without V7 passes through untouched;
    a page that carries the V7 marker but not exactly the governed V7 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V7 marker but not exactly the governed V7 text")
    out = text
    for old, new in PAIRS:
        out = out.replace(new, old)
    if MARKER in out or apply_v7(out) != text:
        raise ValueError("privacy.html V7 layer is not an exact, reversible edit")
    return out


def footer_v7(page: str) -> str:
    """The V7 footer for another page built from the privacy shell (the Artist Register)."""
    if page.count(FOOT_OLD) != 1:
        raise ValueError("the privacy-shell footer is not present exactly once")
    return page.replace(FOOT_OLD, FOOT_NEW)


def without_footer_v7(page: str) -> str:
    if FOOT_NEW not in page:
        return page
    if page.count(FOOT_NEW) != 1:
        raise ValueError("the V7 footer is not present exactly once")
    return page.replace(FOOT_NEW, FOOT_OLD)
