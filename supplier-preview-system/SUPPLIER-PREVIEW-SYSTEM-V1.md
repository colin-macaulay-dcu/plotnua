# PLOTNUA SUPPLIER PREVIEW SYSTEM v1.0

A private supplier preview shows a supplier how they would appear inside the
real PlotNua homeowner experience, so they can decide whether a relationship
is worth exploring. It is a commercial introduction, not a governance
document and not an advertisement.

This standard is self-contained. You do not need the history of the TRIQ or
Superior Pergola builds to produce a preview from it.

---

## 1 · WHEN TO USE WHICH VARIANT

| | **A · Product-led** | **B · Provider-led** |
|---|---|---|
| File | `template-product-led.html` | `template-provider-led.html` |
| Use when | one specific, verified product carries the conversation | the relationship is with a provider or category |
| Supplier shape | single named product, published spec and price | multiple or custom products, made to measure |
| Imagery | usually state A (authorised) | usually state C (not yet authorised) |
| Extra block | "Still to establish" list | none |
| Reference build | `triq-cube-preview.html` | `superior-pergola-platform-preview.html` |

If in doubt, use Provider-led. It makes fewer claims.

---

## 2 · EVIDENCE PACK — BEFORE ANY BUILD

Assemble this first, from **first-party sources only** (the supplier's own
site, their own written words). Record the URL and the date read for each.

- official supplier name, exactly as they write it
- specific product or category name, in their words
- published price and what it includes
- key verified features and specifications
- Irish availability / service area
- installation or service proposition
- provider role (who does what)
- source URLs + date read
- imagery rights status

**UNKNOWN STAYS UNKNOWN.** A gap is a gap. On a product-led preview it goes
in "Still to establish"; on a provider-led preview it is simply absent.
Never fill a gap with a plausible-sounding fact.

Third-party listings, directories and aggregators are not evidence.

---

## 3 · IMAGERY RIGHTS — THREE STATES, NO FOURTH

**A · AUTHORISED.** Written permission exists. Use their image, unmodified,
served from their own domain, with the credit they require and a line naming
who gave permission and when.

**B · PLOTNUA-OWNED / CLEARED.** Use PlotNua's own or properly licensed
imagery where it genuinely fits.

**C · NOT YET AUTHORISED.** Use the premium held panel in the provider-led
template. It should read as a purposeful invitation — *this is where your
photography would sit* — never as an apology.

A photograph being publicly visible is **not** permission to reproduce it.
Never use supplier imagery because the page is private. Never download,
re-host, crop or alter a supplier image.

---

## 4 · FROZEN SHARED STRUCTURE

Every preview, both variants, in this order:

1. **Private bar** — "Private preview · Prepared for X".
2. **PlotNua hero** — wordmark, short proposition, one supporting line. No
   long introductory explanation.
3. **Homeowner journey** — DISCOVER → CHECK → EXPLORE → COMPARE → DECIDE →
   CONNECT. Frozen. Change only if the real PlotNua architecture changes.
4. **The visual demonstration** — mandatory. See §5.
5. **Why this could be useful** — three points, what PlotNua adds before the
   homeowner arrives.
6. **What we'd like to explore** — one proposition or question.
7. **Footer** — one line.

No new sections. If something does not fit these seven, it does not go on
the page.

---

## 5 · THE DEMONSTRATION — THE RULE

> **REAL PLOTNUA INTERFACE + VERIFIED SUPPLIER INFORMATION + CLEARLY
> ILLUSTRATIVE COMMERCIAL PLACEMENT**

Never ship a supplier preview that is mainly explanatory paragraphs. A
supplier must **see** their offering inside the product, not imagine it.

Everything inside `.pn-stage` is genuine production markup and CSS, lifted
from `your-plot.html` by `refresh-ui-kit.py`: the PlotNua P mark, the My Plot
pill, the result field and typography, the Save/heart treatment, Open My
Plot, and the established information hierarchy.

**Do not invent a mock interface for each supplier.** If the real interface
needs something it does not have, that is a product question, not a preview
question.

Templates are generated. Edit `refresh-ui-kit.py`, re-run it, never hand-edit
the emitted HTML.

---

## 6 · PERSONALISATION GUARDRAIL

Anything shown as personalised to a homeowner must trace to a capability
PlotNua genuinely has.

**Supported today:** locality from the Eircode lookup
(`simplifyLocalityDisplay`), the style/appearance preference and budget band
from the journey's own questions, and the editorial sentence
`buildCardEditorialSentence()` builds from them.

**Not supported:** garden aspect, orientation, surface, existing structures —
anything the journey neither asks nor infers.

*The guardrail incident:* a Superior Pergola draft read "south-facing
patio". It was convincing and completely invented; the production code
carries an explicit orientation limitation. It was caught only by checking
the claim against the source. **Check every personalised element against real
code before it ships.**

---

## 7 · COPY RULES

**Human voice.** Every visible sentence must pass: *would Colin say this to
the supplier, in person?* Reject AI prose, technical documentation,
governance language, research-hypothesis framing, legal disclaimer and
architecture-specification wording. Use contractions and ordinary business
English.

**Do not explain what the visual already shows.** No feature-status
commentary on the buttons. No paragraph restating the demonstration.

**Illustrative status, once.** One `ILLUSTRATIVE PREVIEW` label is enough.
Banned as repetition: "we haven't agreed anything", "nothing here is real",
"this does not exist yet", "no partnership exists", and running explanations
of what is and is not operational. Stay accurate without apologising.

**Commercial value.** Answer visually: *what does PlotNua add before the
homeowner reaches the provider?* Defaults — MORE CONTEXT · CLEARER INTENT ·
A BETTER STARTING POINT — are a starting point, not a formula. Rewrite them
in the supplier's own terms where they do not fit. Do not expand to four.

**Commercial boundary.** Do not prematurely define PlotNua as ending at
information or referral. Banned: "everything that follows stays with the
provider" and its variants. Specialist advice, design, survey, quotation and
installation are the provider's. PlotNua may retain the homeowner decision
relationship, the connection, attribution, homeowner advantage and a
measurable commercial outcome — but **never state any of these as
operational unless they actually are.**

**The ending.** One commercially interesting proposition or question. Do not
summarise the page again. The reader should finish understanding why a
relationship with PlotNua might be worth exploring.

---

## 8 · ACCURACY RULES

- Every supplier claim traces to first-party evidence read for this build.
- Never call the supplier a PlotNua partner, approved, recommended, trusted
  or preferred. They are not.
- No invented product name, price, dimension, availability, lead time or
  capability.
- No claim that a connection, attribution or commercial mechanism exists.
- Prices carry their basis ("including fitting", "as published"). Do not
  restate a foreign-market price as an Irish delivered price.
- If the supplier's site changes, the preview is stale. Re-verify before
  re-sending.

---

## 9 · QA CHECKLIST

Render at **1440 / 768 / 390** and confirm:

- [ ] no horizontal scroll, no overflowing element at any width
- [ ] demonstration responsive; facts readable, not one compressed run
- [ ] PlotNua mark, My Plot pill, Save, Open My Plot all render correctly
- [ ] zero console/runtime errors
- [ ] every `{{TOKEN}}` replaced; no other supplier's content anywhere
- [ ] no external imagery unless state A, with credit present
- [ ] every supplier claim checked against the evidence pack
- [ ] every personalised element checked against real PlotNua code (§6)
- [ ] `noindex, nofollow, noarchive, nosnippet, noimageindex` present
- [ ] not in `sitemap.xml`; no page links to it
- [ ] no partnership implication; no false PlotNua capability

---

## 10 · RELEASE WORKFLOW

```
SUPPLIER IDENTIFIED
→ FIRST-PARTY EVIDENCE PACK
→ IMAGE-RIGHTS STATE (A / B / C)
→ CHOOSE PRODUCT- OR PROVIDER-LED VARIANT
→ POPULATE THE TEMPLATE
→ ACCURACY GUARDS (§6, §8)
→ DESKTOP / TABLET / MOBILE RENDER
→ FOUNDER REVIEW
→ PRIVATE DEPLOY (push main; Pages serves it)
→ VERIFY THE LIVE URL, not the local file
→ SEND
→ FREEZE the sent commit SHA
→ WAIT FOR THE SUPPLIER RESPONSE
```

Copy the chosen template to the repository root as
`<supplier>-preview.html`, fill it, and commit by explicit path. Never
`git add .` or `git add -A`.

Deploying is pushing `main`. Confirm the branch is exactly the expected
number of commits ahead of a freshly fetched `origin/main` first, and never
force-push.

A sent preview is frozen at its commit. Do not edit it afterwards unless the
supplier's response creates a genuine reason to.

---

## 11 · STOP CONDITIONS

Stop and ask the founder if:

- a needed fact is not on the supplier's own site;
- imagery rights are unclear, or permission is implied rather than written;
- the preview would need a PlotNua capability that does not exist;
- the supplier asks for something that implies partnership, endorsement or
  ranking;
- push credentials are unavailable — hand over the exact terminal command
  instead of improvising;
- the remote has diverged — hand over a bounded reconciliation, never a
  force-push or a blind pull.

**No speculative CONNECT build.** A preview existing is not a reason to
implement a handoff, an attribution mechanism or any commercial arrangement.

---

## 12 · FILES

| File | Role |
|---|---|
| `template-product-led.html` | Variant A — generated, do not hand-edit |
| `template-provider-led.html` | Variant B — generated, do not hand-edit |
| `refresh-ui-kit.py` | regenerates both from live `your-plot.html` |
| `SUPPLIER-PREVIEW-SYSTEM-V1.md` | this standard |

**Frozen supplier-facing baselines — do not modify:**

- `triq-cube-preview.html` — TRIQBRIQ AG
- `superior-pergola-platform-preview.html` — Superior Pergola Ireland,
  frozen at `e226684a3c0a464f7d20b0704a41eb66bb1a5308`

---

*PlotNua Supplier Preview System v1.0 · 23 September 2026*
