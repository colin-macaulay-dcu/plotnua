"""PlotNua · Privacy Notice V18 layer (2026-11-PLOTART-PAYMENT-PILOT-V18): the PlotArt payment pilot (Stripe checkout).

PREPARED FOR RELEASE. NOT PUBLISHED. It is applied only with the founder's authorisation, in the same release that takes
the first live pilot payment, and not before: until then the pilot takes no live payment and V17 stays accurate.
V18 is an EXACT, REVERSIBLE set of edits on V17; nothing else changes. It matches PA-PAY-2026-11 (clause 9) and
PA-BPT-2026-11 (section 9) as prepared on 20 Nov 2026, PA-BBT-2026-11 (section 10) and PA-BAA-2026-11 (clauses 2.2, 4, 9)
as approved on 21 Nov 2026, and the pilot and basket as built.
  P1  Section 8, buyer enquiries: "PlotArt does not take payment or arrange delivery" is replaced by a pointer to the
      payment pilot sub-section (the enquiry processing itself is unchanged).
  P2  Section 8: a new sub-section "The PlotArt payment pilot (buyers and artists)" after the enquiry sub-section,
      including the basket (buyers buying several artworks together; artists' basket confirmations and consents).
  P3  Section 10: recipients for the pilot (Stripe as an independent controller, PlotNua's bank, Cloudflare, the email
      delivery service) and the email service's transfer safeguards.
  P4  Section 11: performing a contract (or steps before one) as a lawful basis.
  P5  Section 12: the pilot's and the basket's retention periods.
The "Last updated" label is governed by the V4/V5 verifiers and is not changed by V18.
without_v18() returns the exact page beneath V18 (privacy_v17_layer.without_v17 takes V18 off first).

    python3 atlas-tools/privacy_v18_layer.py --apply     write V18 into privacy.html (only with the founder's authorisation)
"""
from __future__ import annotations

MARKER = "PLOTNUA-PLOTART-PAYMENT-PILOT-PRIVACY-V18"
VERSION = "2026-11-PLOTART-PAYMENT-PILOT-V18"

P1_OLD = "The artist then handles your enquiry and any sale directly with you; PlotArt does not take payment or arrange delivery.</p>"
P1_NEW = (f"<!-- {MARKER} · PlotArt payment pilot, privacy notice {VERSION} -->"
          "The artist then handles your enquiry and any sale directly with you. If you and the artist agree to use PlotArt's "
          "payment pilot, the sub-section “The PlotArt payment pilot (buyers and artists)” below also applies.</p>")

P2_OLD = ("<p>If PlotArt passes your enquiry to an artist by email, we record the same minimal details, never your contact "
          "details, and we delete the email itself from our mailbox within 24 months.</p>")
P2_NEW = P2_OLD + """
    <h3 class="pv5-sub" id="plotart-payment-pilot">The PlotArt payment pilot (buyers and artists)</h3>
    <p>PlotArt runs an optional pilot in which a buyer can pay an artist for an original artwork by card, through a checkout provided by Stripe. The artist is the seller and is paid into their own Stripe account. PlotArt prepares the quote, operates the checkout and receives its commission from the artist's payment.</p>
    <p><strong>Buyers.</strong> We keep your email address with your quote, the exact quote you were shown, your acceptance of the purchase terms, your purchase confirmation, any notices about refunds, and the payment, refund and dispute records for your order (amounts, dates, statuses and Stripe reference numbers). We use them to take steps at your request before the sale and to provide the checkout, confirmation and notices you are sent (contract); to keep accounting records (legal obligation); and to prevent fraud, apply our purchase limits and be able to establish or defend legal claims (legitimate interests). We send Stripe your email address, the order reference, the artwork title, the artist's name and the amounts, and we share with the artist what they need to deliver the artwork and handle any return.</p>
    <p><strong>Artists in the pilot.</strong> We keep your opt-in record; your Stripe account reference and its status, and the names of any onboarding items Stripe still needs; the seller information you give us (legal and trading name, address, returns address, email, telephone, whether you sell as a trader, and VAT number), which we show to buyers on each quote and in each purchase confirmation; and each order's records and statement, and the amounts we owe you and have paid. We use them to operate the pilot under your agreement with us (contract), to keep accounting records and to give buyers the seller information the law requires (legal obligation). To open your Stripe account we send Stripe your PlotArt Studio email address, your country and our internal reference for you.</p>
    <p><strong>What we can see through Stripe but do not keep.</strong> Our access to Stripe lets us view some details that we do not copy into our own records. We look at them only when an order needs it, for example to resolve a refund or a payment dispute. About buyers: name, email address, billing country, and card brand, country, type, expiry date and last four digits; we never see full card numbers. About artists: the name, email address, address and date of birth given to Stripe, identity details given during Stripe's onboarding, business phone and website, and the bank's name, country and branch code and the last four digits of the payout account; we never see full account numbers.</p>
    <p><strong>Bank details for payments we make to artists.</strong> We ask for an artist's bank details only when we must pay them an amount directly. We ask by telephone and enter them only in our business online banking, which only the founder can access. They are never entered in PlotArt Studio, the payment pilot, our application logs or our emails. Our bank keeps them as a saved payee, which we delete once no further payment is expected, and in its record of each transfer, which is part of our accounting records.</p>
    <p><strong>Buying several artworks together (the basket).</strong> We keep your name, email address and delivery address; the artworks, sellers and amounts shown to you before you paid; your acceptance of the basket purchase terms; and, for each artwork, the order and payment records described above. You enter your card once, on Stripe's page: Stripe saves it on PlotArt's Stripe account and copies it to each seller's own Stripe account so that each seller can be paid for their artwork; it is used only for the payments in that basket, and we never see the full card number. We share with each seller your name and delivery address and, where needed, your email address, for their own artworks only; a seller is not told what you bought from other sellers. We do this on the same bases as for the pilot above (contract; legal obligation; legitimate interests).</p>
    <p><strong>Artists in the basket.</strong> If you take part in the basket we also keep your acceptance of the basket addendum; your confirmation that your seller information may be shown to buyers before they pay; any consent to Stripe's processing fees on commission-free sales, and any withdrawal; and your delivery offers. Your seller information is shown on the basket page, which anyone can open, only after you confirm it.</p>"""

P3_OLD = ("<p>Enquiry emails to artists and confirmations to buyers are sent by an email delivery service acting for PlotNua under "
          "its data processing terms.</p>")
P3_NEW = P3_OLD + """
    <p>The PlotArt payment pilot described in Section 8 uses Stripe (Stripe Payments Europe, Limited, Ireland), which processes payments as an independent controller under its own privacy policy; PlotNua's bank, for transfers we make to artists, under its own terms; services provided by Cloudflare, which host the pilot for PlotNua; and the same email delivery service, which sends pilot confirmations and notices for PlotNua under its data processing terms.</p>
    <p>That email delivery service, Resend, is based in the United States. Resend states that it is certified under the EU-U.S. Data Privacy Framework, and its Data Processing Addendum includes the EU Standard Contractual Clauses for transfers from the European Economic Area. Cloudflare's safeguards are described in Section 7.</p>"""

P4_OLD = "<li>taking steps at the visitor's request before entering into an arrangement; and</li>"
P4_NEW = ("<li>performing a contract with you, or taking steps at your request before entering into one (for example, the "
          "PlotArt payment pilot);</li>\n      " + P4_OLD)

P5_OLD = ("<p>PlotArt gallery records are kept while an artist takes part and for 12 months afterwards; the record of what was "
          "published and accepted, a minimal record of enquiries without buyers' details, and Gallery Artists' sale reports and "
          "commission records, for six years after an artist leaves (for commission records, or six years after the last "
          "commission invoice or payment, if later); and buyers' details in enquiries for 24 months, as described in Section 8.</p>")
P5_NEW = P5_OLD + """
    <p>PlotArt payment pilot records: paid orders (the order, quote, confirmation, notices, ledger and amounts owed) are kept until 31 December of the sixth year after the order is settled; unpaid quotes for two years after the quote ended; records are never deleted while a payment dispute about the order is open, and are kept longer only under a legal hold for a stated reason, reviewed at least every 12 months; an artist's opt-in record and Stripe account link for six years after they leave the pilot, or as long as any of their orders is kept; an artist's seller information is deleted when they leave the pilot (each order keeps the copy shown on its quote); and bank transfer records at our bank for six years after the end of the year of payment.</p>
    <p>Basket records follow the same periods as pilot orders. An artist's basket acceptance, confirmations and consents are kept for six years after the artist leaves the basket, or for as long as any of their basket orders is kept, whichever is later.</p>"""

PAIRS = [(P1_OLD, P1_NEW), (P2_OLD, P2_NEW), (P3_OLD, P3_NEW), (P4_OLD, P4_NEW), (P5_OLD, P5_NEW)]


def apply_v18(text: str) -> str:
    if MARKER in text:
        raise ValueError("V18 already applied")
    if "PLOTNUA-PLOTART-OPPORTUNITIES-OPT-IN-PRIVACY-V17" not in text:
        raise ValueError("V18 applies on top of V17 only")
    for old, _ in PAIRS:
        if text.count(old) != 1:
            raise ValueError("V18 anchor not found exactly once: " + old.strip()[:70])
    for old, new in PAIRS:
        text = text.replace(old, new)
    return text


def without_v18(text: str) -> str:
    """The exact page beneath V18. A page without V18 passes through untouched; a page that carries the V18 marker but
    not exactly the governed V18 text raises."""
    if MARKER not in text:
        return text
    for _, new in PAIRS:
        if text.count(new) != 1:
            raise ValueError("privacy.html carries the V18 marker but not exactly the governed V18 text")
    out = text
    for old, new in reversed(PAIRS):
        out = out.replace(new, old)
    if MARKER in out or apply_v18(out) != text:
        raise ValueError("privacy.html V18 layer is not an exact, reversible edit")
    return out


if __name__ == "__main__":
    import pathlib, sys
    page = pathlib.Path(__file__).resolve().parent.parent / "privacy.html"
    if "--apply" not in sys.argv:
        sys.exit(__doc__)
    page.write_text(apply_v18(page.read_text(encoding="utf-8")), encoding="utf-8")
    print("privacy.html: V18 (PlotArt payment pilot) applied")
