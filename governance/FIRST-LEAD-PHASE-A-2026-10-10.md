# GARDEN ROOM FIRST LEAD · PHASE A

**Date:** 10 October 2026 · **Base:** `260f24a409dfaf2a7ffb12b2365d068a53b76746`

**Public state: the Yard Box enquiry CTA is OFF.** Ordinary visitors see the pending status
exactly as before. This record exists so that stays true by construction rather than by memory.

---

## What was built

A second route through the existing enquiry screen that records an attributable Garden Room lead
for **one** supplier and **three** products, and a Worker that is the only thing able to write
one. Nothing is emailed to anybody: forwarding a lead is a human act.

The synthetic `?enquiry=test` route is **unchanged** and still gated by J07.

## The release gate — two switches, and hiding is not one of them

| Layer | What it does | Ships |
|---|---|---|
| Page `?leadkey=` | Convenience, so the journey can be exercised privately | **Not a control.** Anybody can type a query string |
| Worker `LEAD_PUBLIC_ENABLED` | The public route | `"false"` |
| Worker `LEAD_PREVIEW_KEY` | While public is false, every write must carry a matching secret | **Secret only.** Not in the page, not in this repository |
| Worker `WRITES_ENABLED` | Whether anything is written at all | `"false"` |
| Worker `EMAIL_ENABLED` | There is no mail adapter. The var exists so the refusal is explicit | `"false"` |

**The real gate is server-side.** A visitor who finds the query string, or hand-edits the DOM,
still cannot record a lead: the Worker refuses before it reads a body. A deploy that forgets the
secret is **closed**, not open — `releaseOpen()` requires a key of at least 16 characters.

## The allow-list

`ORG-000157` Yard Box · `receaph6vCI7xtS5K` Whistler · `reckMDqp4tVjAjM7b` Vancouver ·
`recLEonLKyhNTUiAt` Toronto.

Checked **three times**: where the control is drawn, where the screen opens, and in the Worker.
Adding a supplier to either list is the act that makes them reachable and must not happen without
founder authorisation **and** that supplier having been told PlotNua may send them enquiries.

## Truthfulness

The Yard Box control claims no price, currency, VAT treatment, warranty, or that groundworks are
included — the last because the supplier's own comparison table says *"Prices exclude
groundworks."* The sub-line says only that Yard Box don't publish prices, which is their own
published position (*"Enquire for pricing"* on every model, read 10 October 2026).

**No response time is promised.** The design proposed "within a working day"; it was dropped on
founder instruction, because PlotNua has no arrangement with Yard Box and should not create a
service-level promise it cannot keep.

## Journey contract

A bounded exception is recorded in `PLOTNUA-JOURNEY-CONTRACT.md`. It is an **enquiry**, not a
handoff: `pnSupplierHandover()` and the single `window.open(` door are untouched and the homeowner
is not sent anywhere. Guards **J13** (six assertions) and **J14** were added, each with a mutation
in `--self-test` that only it catches.

## Privacy — a correction to an earlier finding

The Phase A design recorded blocker **PR-1**: *"privacy.html does not say PlotNua shares personal
data with suppliers."* **That was wrong.** Section 6, *Supplier Enquiries*, already said so in
detail, including a what-is-not-sent list. The earlier audit had grepped §8 only and did not read
§6. The real defect was narrower and would have been easy to miss: §6 named **Formspree** as the
processor, and the lead route uses PlotNua's own Worker and records the enquiry. The policy has
been corrected to name both routes, to say what is recorded, and to say that a person forwards
the enquiry rather than an automated send.

## Two Yard Box data defects — deliberately NOT patched in the artefact

The brief authorised correcting them. On inspection neither reaches a homeowner, and the file
that holds them is **generated** (`sourceKind: airtable-live`, with a `governedDigest`):

- **Vancouver jurisdiction wording** — `features.irishAvailability.text` says *"an Irish garden
  room supplier… on an Irish domain"*. The domain is `yardbox.co.uk` and the company is in
  Co. Down. But the page renders `irishAvailabilityConfirmationState`, not this prose, so no
  homeowner sees it.
- **`floorAreaM2` null** — the verified areas (9 / 15 / 24 m²) live in `features.floorArea` and
  were re-confirmed against the supplier's live table today, but never reached the canonical
  field.

Hand-editing a generated artefact would be undone at the next regeneration and would leave the
`governedDigest` asserting an integrity that no longer held — the same class of silent drift that
broke the 404 baseline. **The durable fix is in Airtable, which this work could not reach.** The
lead surface was therefore designed not to need either value: it names the supplier and the
product and says price is on enquiry. Both corrections are carried for the founder.

## Gates this work could not execute

Deploying the Worker needs Cloudflare credentials and creating the leads table needs an Airtable
token; neither exists in this environment. **The end-to-end test lead has therefore NOT been
run.** The mechanism is proven against a stubbed Airtable (43 behaviour cases, 18 mutations), not
against the real one. `worker/garden-lead/AIRTABLE-SCHEMA.md` has the exact table and deploy
steps.

## Lesson

The enquiry screen, its consent UX, its honeypot, its fail-closed error handling and even its live
success sentence had all been built by earlier jobs and left deliberately unreachable, with the
CSS slot measured and a comment naming Yard Box. **Phase A was mostly wiring, not building.**
Reading what was already there before designing anything saved the larger part of this job.
