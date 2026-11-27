"""Contact-detail withholding for PlotNua's published research data (founder direction, 27 Nov 2026).

Research and evidence text sometimes quotes a maker's telephone number or email address as proof of an Irish presence
("an Irish mobile line (087 ...)"). Those details are WITHHELD from every published data file, but the sentence is
kept: the number or address is replaced by a neutral marker, so the evidence still reads ("an Irish mobile line
(phone number withheld)") and no useful supplier information is lost. Websites (URLs) are kept. A supplier's chosen
public contact on its own PlotNua page is not touched by this module.

One definition, used by every generator before it writes, and by the validators (which refuse any number or address
that is left)."""
import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(
    r"\+\d[\d ()-]{7,}\d"                                   # international, e.g. +353 56 777 4010
    r"|(?<![\w.,-])0\d{1,4}[ -]\d{3,4}(?:[ -]\d{3,4})?(?!\d)"  # national, e.g. 087 123 4567, 01 564 1964
)
PHONE_MARK, EMAIL_MARK = "[phone number withheld]", "[email address withheld]"


def redact(text):
    if not isinstance(text, str):
        return text
    text = EMAIL.sub(EMAIL_MARK, text)
    return PHONE.sub(PHONE_MARK, text)


def redact_tree(obj):
    if isinstance(obj, dict):
        return {k: redact_tree(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_tree(v) for v in obj]
    return redact(obj)


def found(text):
    """Any contact detail still present (validators refuse it)."""
    m = EMAIL.search(text) or PHONE.search(text)
    return m.group(0) if m else None
