"""PlotNua · The House as a Power Station · factual corrections F1-F5, October 2026.

Founder review, 20 Oct 2026, Decision 2: "Prepare factual corrections F1-F5."
Every new sentence rests on an official source re-read on 20 Oct 2026:

  F1  Solar grant eligibility is "built and occupied before 2025" (seai.ie
      solar electricity grant page; SEAI news 29 Sep 2026: extended from
      6 Oct 2026). The page said "before 2021" in two places.
  F2  The battery text said the two grants use different construction years.
      They no longer do (seai.ie battery page: "prior to 2025").
  F3  The two "not established" points are now answered by SEAI's own words:
      "You must wait to receive a Grant Offer from SEAI before installing the
      battery"; "applications cannot be accepted for installations that have
      already started"; "maximum grant value for solar pv panels and battery
      to EUR 2,400" (seai.ie solar and battery pages).
  F4  The EUR 400 exemption is current law and stays. The increase to EUR 600
      is PROPOSED: Department of Finance press release, 19 Oct 2026, Finance
      (No. 2) Bill 2026 ("will be increased from EUR 400 to EUR 600 per
      annum"); not enacted; start year not stated.
  F5  Plug-in solar: no dedicated regulatory pathway published. ESB Networks
      convened the cross-industry group (with the CRU and the NSAI) developing
      an approach. F5a uses the founder's approved wording of 21 Oct 2026;
      F5b keeps its dated statement. Nothing is presented as enacted, and no
      800 W figure is added (founder decision 6).

THE SPLIT
  ARTICLE edits (F1a F1b F2a F2b F3a F3b F4a F4b F5b) are owned by this layer.
  The SECTION edit (F5a, the balcony line inside the look-again section) is
  owned by the look-again fragment atlas-tools/disc026-look-again/look-again.html,
  because that section is generated from it and look-again L1 requires the page
  to carry the fragment byte for byte. The facts builder asserts both halves.

with_facts / without_facts: exact, reversible, ARTICLE edits only. A partial
or duplicated state raises ValueError.
"""
from __future__ import annotations

ARTICLE_EDITS = [
    # F1a  solar drawer, "Who qualifies"
    ("F1a",
     "<strong>Who qualifies.</strong> The home must have been built and\n"
     "            occupied before 2021. The grant is not open where solar PV funding has",
     "<strong>Who qualifies.</strong> The home must have been built and\n"
     "            occupied before 2025. The grant is not open where solar PV funding has"),
    # F1b  "Grant, tax and permission in detail", Solar
    ("F1b",
     "installation. The house must have been built and occupied before 2021. The\n"
     "        grant can be claimed once at an MPRN",
     "installation. The house must have been built and occupied before 2025. The\n"
     "        grant can be claimed once at an MPRN"),
    # F2a  battery drawer, "Who qualifies"
    ("F2a",
     "built and occupied <em>before 2025</em> &mdash; a different year from the\n"
     "            solar grant, which is why a house finished in 2022 can be outside one and\n"
     "            inside the other. One per MPRN",
     "built and occupied <em>before 2025</em> &mdash; the same cut-off as the\n"
     "            solar grant. One per MPRN"),
    # F2b  detail drawer, Battery
    ("F2b",
     "and must have been built and occupied <em>before 2025</em> &mdash; a\n"
     "        different year from the solar grant, and the reason a 2022 house can be\n"
     "        outside one and inside the other. One per MPRN",
     "and must have been built and occupied <em>before 2025</em> &mdash; the\n"
     "        same cut-off as the solar grant. One per MPRN"),
    # F3a  battery drawer, the two open questions now answered
    ("F3a",
     "<strong>Two things we have not established.</strong> Whether a battery\n"
     "            installed before that date can be claimed retrospectively, and how the\n"
     "            &euro;600 interacts with the solar grant ceiling. We will not guess at\n"
     "            either.</div>",
     "<strong>Timing and the combined maximum.</strong> SEAI says you must wait\n"
     "            for its Grant Offer before installing, and that applications cannot be\n"
     "            accepted for installations that have already started. With solar panels\n"
     "            as well, the most the two grants can pay together is &euro;2,400.\n"
     "            SEAI.</div>"),
    # F3b  detail drawer, Battery
    ("F3b",
     "Solar and battery can go in a single application. Whether a\n"
     "        battery installed before that date can be claimed retrospectively, and how\n"
     "        the &euro;600 interacts with the solar ceiling, are two things PlotNua has\n"
     "        <em>not</em> established and will not guess at.<br><br>",
     "Solar and battery can go in a single application. Wait for\n"
     "        SEAI&rsquo;s Grant Offer before installing: applications cannot be accepted\n"
     "        for installations that have already started. Panels and battery together\n"
     "        come to a maximum of &euro;2,400.<br><br>"),
    # F4a  grid drawer, Tax
    ("F4a",
     "<strong>Tax.</strong> The first &euro;400 a year of microgeneration income\n"
     "            is exempt from income tax.<br><br>",
     "<strong>Tax.</strong> The first &euro;400 a year of microgeneration income\n"
     "            is exempt from income tax. Budget 2027 proposes raising that to\n"
     "            &euro;600. The change is in the Finance (No.&nbsp;2) Bill 2026, published\n"
     "            on 19 October 2026, and is not yet law.<br><br>"),
    # F4b  detail drawer, Tax
    ("F4b",
     "<strong>Tax.</strong> The first &euro;400 a year from exporting is exempt from\n"
     "        income tax. Above that it is taxed like other income.<br><br>",
     "<strong>Tax.</strong> The first &euro;400 a year from exporting is exempt from\n"
     "        income tax. Above that it is taxed like other income. The\n"
     "        Finance (No.&nbsp;2) Bill 2026, published on 19 October 2026, proposes\n"
     "        raising the exempt amount to &euro;600; until it is enacted, &euro;400 is\n"
     "        the law.<br><br>"),
    # F5b  "What we're watching", Ireland card
    ("F5b",
     "the Minister was expected in September 2026. Nothing has been published.",
     "the Minister was expected in September 2026. As of 20 October 2026, PlotNua\n"
     "            has found no published report and no published rules."),
]

# F5a lives in the look-again fragment (see THE SPLIT above).
SECTION_OLD = ("<p>In Germany, small plug-in panels hang from balconies. Ireland is still "
               "working out whether to allow them, and nothing has been published.</p>")
# Founder-approved wording, 21 Oct 2026 (final release preparation, decision 5).
SECTION_NEW = ("<p>In Germany, small plug-in panels hang from balconies. Ireland has not yet "
               "published a dedicated regulatory pathway for these systems. ESB Networks is "
               "involved in developing an approach, but homeowners should not assume that "
               "plug-in installation is currently permitted without following the applicable "
               "connection and safety requirements.</p>")


def with_facts(text: str) -> str:
    out = text
    for code, old, new in ARTICLE_EDITS:
        if out.count(old) != 1 or new in out:
            raise ValueError("facts layer: %s anchor not found exactly once in the base state" % code)
        out = out.replace(old, new, 1)
    return out


def without_facts(text: str) -> str:
    present = [new in text for _, _, new in ARTICLE_EDITS]
    if not any(present):
        return text
    if not all(present):
        raise ValueError("facts layer: the page carries only part of the governed correction")
    out = text
    for code, old, new in ARTICLE_EDITS:
        if out.count(new) != 1 or old in out:
            raise ValueError("facts layer: %s is duplicated or mixed with its original" % code)
        out = out.replace(new, old, 1)
    if with_facts(out) != text:
        raise ValueError("facts layer is not an exact, reversible edit")
    return out


def without_section_fact(text: str) -> str:
    """Revert F5a on a whole page (used only to compare with the pinned base)."""
    if text.count(SECTION_NEW) == 1 and SECTION_OLD not in text:
        return text.replace(SECTION_NEW, SECTION_OLD, 1)
    if text.count(SECTION_OLD) == 1 and SECTION_NEW not in text:
        return text
    raise ValueError("facts layer: the balcony line is missing, duplicated or mixed")
