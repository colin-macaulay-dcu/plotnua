#!/usr/bin/env python3
"""
PlotNua — NON-GENUINE ATLAS RECORDS, excluded from every published count.

WHY THIS FILE EXISTS. Atlas holds a small number of records that are not real
organisations, products or suppliers: fixtures created to test machinery safely.
They must never reach a homeowner-facing figure. Until 26 September 2026 that
was enforced by a sentence in a Notes field, which is a hope, not a mechanism.
This module is the mechanism.

IT IS DELIBERATELY TINY AND EXPLICIT. Record ids, enumerated by hand, with the
reason written next to each one. No pattern matching on names, because a pattern
like "TEST" would one day exclude a genuine supplier with "Test" in its name and
quietly shrink a published count. An id cannot drift.

ADDING TO THIS LIST LOWERS A PUBLISHED FIGURE, so it is a founder-level act.
Removing something from it raises one. Either way, say which and why in the
commit.

WHAT THIS IS NOT. It is not a quality filter, not a suppression list for
suppliers PlotNua would rather not show, and not a way to make a number look
better. Every entry must be a record that does not describe a real business.
"""

# {record id: reason}. The reason is not decoration: it is what a future reader
# needs in order to judge whether the exclusion is still correct.
EXCLUDED_RECORD_IDS = {
    "recFiK85wMsREJ3AY":
        "ORG-000195 is TRIQBRIQ; this is ORG-TEST-001, "
        "'PlotNua Internal Test Organisation — DO NOT CONTACT'. Created "
        "26 September 2026 as the fixture for the image-permission system so "
        "that end-to-end tests never touch a real supplier. It is not a "
        "company, sells nothing, owns no images and has no products. Its "
        "contact address is PlotNua's own hello@plotnua.ie and its Partner "
        "Status is Strategic Hold so no outreach can reach it.",
}


def is_excluded(record_id: str) -> bool:
    return record_id in EXCLUDED_RECORD_IDS


def drop_excluded(records: list) -> tuple:
    """Returns (kept, dropped). Never mutates the input.

    Airtable records carry their id at the top level, so this needs no extra
    field fetch and cannot be defeated by a renamed field or select choice.
    """
    kept, dropped = [], []
    for r in records:
        (dropped if is_excluded(r.get("id", "")) else kept).append(r)
    return kept, dropped
