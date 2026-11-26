"""PlotNua · Privacy Notice V18 proof: the PlotArt payment pilot. V18 applies exactly once on V17, is exactly reversible,
leaves every earlier version's governed text intact beneath it, and says what the pilot and its terms say (PA-PAY-2026-11
clause 9, PA-BPT-2026-11 section 9): who receives what, the lawful bases, the transfer safeguards and the retention periods.
    python3 atlas-tools/prove-privacy-v18.py
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "atlas-tools"))
import privacy_v18_layer as V  # noqa: E402
import privacy_v17_layer as V17  # noqa: E402

bad = []
ok = lambda c, m: None if c else bad.append(m)
import privacy_v19_layer as V19  # noqa: E402
priv = V19.without_v19((ROOT / "privacy.html").read_text(encoding="utf-8"))   # V19 (26 Nov 2026) sits on top: read the page beneath it
APPLIED = V.MARKER in priv
if not APPLIED:
    try:
        priv = V.apply_v18(priv)
    except ValueError as e:
        bad.append("V0 V18 cannot be applied to the page as it stands: " + str(e))
ok(priv.count(V.MARKER) == 1, "V1 V18 must be applied exactly once")
try:
    beneath = V.without_v18(priv)
    ok(V.apply_v18(beneath) == priv and V.MARKER not in beneath and V17.MARKER in beneath, "V1 V18 is not exactly reversible onto V17")
    ok(V17.without_v17(priv) == V17.without_v17(beneath), "V1 V17 and every earlier verifier read the same governed text beneath V18")
except ValueError as e:
    bad.append("V1 " + str(e))
flat = lambda s: re.sub(r"\s+", " ", re.sub(r"<!--.*?-->|<[^>]+>", " ", s, flags=re.S)).replace("&amp;", "&")
txt = flat(priv)
ok("PlotArt does not take payment or arrange delivery" not in txt, "V2 the notice no longer says PlotArt does not take payment")
a = priv.find('id="plotart-payment-pilot"')
sec = flat(priv[a:priv.find("</section>", a)]) if a > 0 else ""
for need, why in [("The artist is the seller and is paid into their own Stripe account", "the seller and Stripe Connect model"),
                  ("receives its commission from the artist's payment", "how PlotArt is paid"),
                  ("We send Stripe your email address, the order reference, the artwork title, the artist's name and the amounts", "what goes to Stripe (PA-BPT 9.2, PA-PAY 9.1(b))"),
                  ("your PlotArt Studio email address, your country and our internal reference for you", "what goes to Stripe for onboarding (PA-PAY 9.1(a))"),
                  ("we never see full card numbers", "no full card numbers"),
                  ("we never see full account numbers", "no full account numbers"),
                  ("We ask by telephone", "bank details by telephone only (PA-PAY 9.8)"),
                  ("(contract)", "contract as a lawful basis"), ("(legal obligation)", "legal obligation"), ("(legitimate interests)", "legitimate interests")]:
    ok(need in sec, "V3 the pilot sub-section must cover " + why)
ok("Stripe (Stripe Payments Europe, Limited, Ireland), which processes payments as an independent controller" in txt, "V4 Stripe named as an independent controller")
ok("EU-U.S. Data Privacy Framework" in txt and "EU Standard Contractual Clauses for transfers from the European Economic Area" in txt and "Resend" in txt,
   "V4 the email service and its transfer safeguards are named (GDPR Art. 13(1)(f))")
ok("performing a contract with you, or taking steps at your request before entering into one" in txt, "V5 contract as a lawful basis in Section 11")
for need in ["until 31 December of the sixth year after the order is settled", "unpaid quotes for two years", "never deleted while a payment dispute",
             "reviewed at least every 12 months", "six years after they leave the pilot", "seller information is deleted when they leave the pilot",
             "six years after the end of the year of payment"]:
    ok(need in txt, "V6 retention must state: " + need)
pay = (ROOT / "worker/plotart-studio/agreements/payment-drafts/PA-PAY-2026-11-DRAFT.md").read_text(encoding="utf-8")
ok("until 31 December of the sixth year after the order is settled" in pay and "privacy notice" in pay, "V7 the retention period matches PA-PAY clause 8.1")
_v18 = open(__import__("pathlib").Path(__file__).resolve().parent / "privacy_v18_layer.py", encoding="utf-8").read()
for need in ("Buying several artworks together (the basket).", "copies it to each seller's own Stripe account", "a seller is not told what you bought from other sellers",
             "your confirmation that your seller information may be shown to buyers before they pay", "any consent to Stripe's processing fees on commission-free sales",
             "Basket records follow the same periods as pilot orders"):
    ok(need in _v18, "V8 the basket (PA-BBT 10, PA-BAA 2.2/4/9) must state: " + need)
if bad:
    for x in bad: print("FAIL " + x)
    print("PRIVACY V18 · REFUSED — %d problem(s)" % len(bad)); sys.exit(2)
print("PRIVACY V18 · OK — " + ("applied" if APPLIED else "prepared, applies") + " once on V17, exactly reversible; payment pilot: seller and "
      "Stripe model, recipients, lawful bases, Resend transfer safeguards, retention matching PA-PAY 8.1")
