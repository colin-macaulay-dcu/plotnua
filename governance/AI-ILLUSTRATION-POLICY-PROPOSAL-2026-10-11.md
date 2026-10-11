# AI-GENERATED ILLUSTRATION POLICY — PROPOSAL

**Status: PROPOSAL. Nothing implemented. No website change.**
Written 11 October 2026. Awaiting founder authorisation.

---

## 1 · THE FINDING THAT CHANGES THE SHAPE OF THIS

This was framed as an addition for a capability PlotNua might use. It is not.
**Unlabelled, unrecorded editorial imagery is already live on the homepage and
on every Discovery page**, and two of the founder's own rules are currently
unmet on the published site.

Measured in the working tree on 11 October 2026:

| | count | governed by the rights gate |
|---|---|---|
| Externally-hosted supplier images on published pages | 40 | **yes** — every one has a live grant, gate passes |
| Locally-hosted images in `assets/img/` | **85** | **no** — not one is examined |

The 85 are the Discovery editorial imagery: 14 references on `index.html`, 13
on `discoveries.html`, and 5–10 on each of fourteen Discovery pages. They are
named by content hash. **There is no provenance record for a single one of
them** — no file in the repository says who made any of them, how, or from
what.

The cause is one line in `atlas-tools/validate-image-rights.js:395`:

```js
if (!/^https?:\/\//i.test(u)) continue;          /* relative = PlotNua's own */
```

That assumption was sound when it was written: everything local was PlotNua's
own artwork. The moment AI illustrations land as local files it becomes
`relative = unexamined`, and **a laundered supplier photograph saved to
`assets/img/` would pass the gate silently** — the precise failure the
founder's first rule exists to prevent.

Their alt text also reads as photography. From
`discovery-garden-retreat.html`:

> "An Irish suburban garden with a timber garden room, a barrel sauna, a hot
> tub and a plunge pool set among decking and planting."

Accurate about what the image shows. Silent about what the image *is*. Across
`index.html`, `discoveries.html` and `discovery-garden-retreat.html` the words
"illustration", "artist's impression", "not a photograph" and "indicative"
appear **zero times**.

**This policy is therefore not preparation. It is catching up with what
already shipped.** That does not make it urgent — these are generic garden
scenes, not supplier product shots, and no supplier permission is implicated —
but it does mean the addition has to handle 85 existing undeclared assets
honestly rather than starting from a clean sheet.

---

## 2 · THE TAXONOMY NEEDS ONE CORRECTION

The three categories as given mix two levels:

- `SUPPLIER_IMAGE` and `AI_ILLUSTRATION` classify **an asset**.
- `NO_IMAGE` classifies **a slot that has no asset**.

Keeping them as one enum would mean inventing a record for an image that does
not exist. The clean form, which preserves all three names:

> **Every image slot on a published page resolves to exactly one of three
> states. Two of them point at an asset record. The third is the absence of
> one, and it is a legitimate, declarable outcome.**

That third point is load-bearing, not pedantry. If `NO_IMAGE` is not a
*respectable* answer, the pressure is always to fill the slot with something —
and that pressure is how laundering starts. `NO_IMAGE` must be as easy to
declare as the other two, and the existing Results surfaces already render a
no-image state, so nothing needs building for it.

---

## 3 · THE SMALLEST ADDITION

Three artefacts. **One new file, one new guard, one new page element.** No
existing supplier permission is touched, and the publication gate is not
changed.

### 3.1 · `image-provenance-records.json` — a SEPARATE file

Deliberately not a new field on `image-rights-records.json`. Four reasons:

1. The founder's rule: AI illustrations stay out of supplier
   image-permission records.
2. That file's `source_of_record` is Atlas Core · Image Permission Outreach.
   An AI illustration has no outreach record and never will. Putting it there
   would make the file's own declaration false.
3. The two files answer different questions. Rights records answer *may we
   publish someone else's image*. Provenance records answer *what is this
   image*.
4. `image-rights-manifest.json` is generated from the records file and
   compared byte-for-byte in CI. Widening its schema means touching the
   generator, the manifest and the eleven-sabotage capability proof that
   guards it — a large change to carry a fact that does not belong there.

Proposed schema, one row per local asset:

```json
{
  "schema": "plotnua.image-provenance.records.v1",
  "what_this_is": "What every locally-hosted published image IS. Not a rights file: image-rights-records.json governs whether PlotNua may publish someone else's image, and this governs what PlotNua's own images are. A SUPPLIER_IMAGE row here points at that file and duplicates none of it.",
  "records": [
    {
      "asset": "assets/img/7d5f5718cf9cd3da.jpg",
      "sha256": "<of the bytes on disk>",
      "class": "AI_ILLUSTRATION",
      "label": "Illustration",
      "generated": { "tool": "<model/service>", "date": "2026-10-03" },
      "prompt": "<the prompt, verbatim>",
      "reference_inputs": [],
      "depicts_named_product": false,
      "depicts_named_organisation": false,
      "human_review": {
        "reviewer": "Colin MacAulay",
        "date": "2026-10-03",
        "attests": "Checked against the supplier imagery PlotNua holds. Does not reproduce any supplier photograph and does not resemble any identifiable product design."
      },
      "permitted_surfaces": ["discovery", "library-card", "homepage"]
    }
  ]
}
```

A `SUPPLIER_IMAGE` row carries `asset`, `sha256`, `class`, and
`rights_ref` — the `organisation_code` and `atlas_permission_ref` of the row in
`image-rights-records.json` that authorises it. **No permission data is
copied.** One source of record, one pointer.

Why `sha256`: it binds the record to the **bytes**, not the path. Swapping a
different image in under a declared filename is otherwise invisible, and a
content-hash filename does not prevent it — nothing recomputes the hash today.

Why `prompt` verbatim: it is the only durable evidence of *intent*, and it is
the one anti-laundering control that can be checked mechanically (§3.2).

Why `reference_inputs` must be present and explicitly empty rather than
omitted: an absent field is indistinguishable from an unanswered question. An
empty array is an assertion.

### 3.2 · `atlas-tools/validate-image-provenance.js` — the guard

Same shape as the existing rights gate: walks published HTML, fails closed,
exit 1 for a violation and exit 2 for *cannot establish*.

What it asserts:

| | assertion |
|---|---|
| **P1** | Every **local** image reference on a published page has a provenance record. This is the blind spot at `validate-image-rights.js:395`, closed. |
| **P2** | Every record's `sha256` matches the file on disk. A swapped image invalidates its own declaration. |
| **P3** | `class` is exactly one of the two asset values. An unrecognised value is refused, not ignored. |
| **P4** | A `SUPPLIER_IMAGE` row's `rights_ref` resolves to a live grant in the manifest. Routed through the existing gate's own outcome vocabulary — not a second rights rule. |
| **P5** | An `AI_ILLUSTRATION` row carries `generated`, `prompt`, `reference_inputs` and `human_review`, all non-empty (`reference_inputs` may be an explicit `[]`). |
| **P6** | **Anti-laundering.** An `AI_ILLUSTRATION`'s `prompt` names no organisation in Atlas, no product name, and no product code; `reference_inputs` contains no supplier domain from the rights records; `depicts_named_product` and `depicts_named_organisation` are both `false`. |
| **P7** | An `AI_ILLUSTRATION` is rendered only on a surface in `permitted_surfaces`, and **`product-card` is not an available value** until separately approved. The founder's rule becomes a vocabulary restriction rather than a convention. |
| **P8** | Every `AI_ILLUSTRATION` on a published page carries its visible label (§3.3). |
| **P9** | No provenance record exists for an asset no page references — so a withdrawn image's record goes with it. |

And the two negative assertions, which are what make this a policy rather than
an inventory:

| | assertion |
|---|---|
| **P10** | No page implies an AI illustration depicts a named supplier's actual product: an `AI_ILLUSTRATION` and a supplier's name do not appear in the same figure, caption or card. |
| **P11** | A provenance record is **never** accepted as evidence of rights. Mechanically: no code path reads `image-provenance-records.json` to answer a rights question, and `class: "AI_ILLUSTRATION"` can never produce an `ALLOW` in the rights gate. Asserted at source, because "AI generation is not proof of rights" is otherwise a sentence in a document. |

Plus a capability proof, per standing discipline: each assertion demonstrated
capable of failing against a deliberate mutation, control run first.

### 3.3 · The visible label

**This is the only part that touches a published page**, and it is held back
until authorised. Proposed:

- a visible caption on the illustration — one word, `Illustration`, in the
  existing caption style used for supplier credits;
- the same word opening the `alt` text, so it reaches a screen reader before
  the description: `"Illustration. An Irish suburban garden with…"`;
- one sentence, once per page, in the existing evidence disclosure:
  *"Illustrations on this page show what the possibility looks like. They are
  not photographs of a supplier's product."*

Not proposed: a watermark, a badge, or anything that reads as an apology. The
illustrations do honest work — they show a possibility PlotNua has not
photographed — and the label says what they are, not that they are inferior.

---

## 4 · WHAT THIS CANNOT DO, STATED PLAINLY

Three of the founder's rules **cannot be mechanised**, and pretending
otherwise would be the worse outcome.

> *Never recreate a supplier photograph.*
> *Never reproduce a supplier's distinctive product design.*

A hash comparison catches a byte-for-byte copy. It catches nothing about a
re-render. No check in this proposal can look at two images and judge
resemblance.

**What the guard actually buys**: it makes the *intent* reviewable and the
*inputs* declared. A prompt naming a supplier or a model is mechanically
refusable (P6), and `reference_inputs` turns "did you feed it their photo?"
from an unanswerable question into a recorded assertion that a person signed.
That is a real control and it is not the same control.

**What closes the gap**: `human_review.attests` — a named person, on a date,
having compared the illustration against the supplier imagery PlotNua holds.
The guard asserts the attestation exists. It cannot assert that it is true.
That is a human judgement and the policy should say so rather than imply a
machine is checking.

A fourth limit, less obvious: **P6 can only check prompts for organisations
Atlas already holds.** A supplier PlotNua has never researched cannot be
detected in a prompt. The control for that is the same human review.

---

## 5 · THE 85 EXISTING ASSETS

The guard's first run would refuse all 85. Three ways to handle that, and only
one of them is honest.

**Rejected — retro-declare from inference.** Writing `AI_ILLUSTRATION` rows
for 85 images based on what the build scripts suggest would be **inventing
provenance**, which is the same error as inventing a supplier permission. The
prompts, tools and dates are not in the repository. I do not know what these
images are, and neither does any file.

**Rejected — allowlist and move on.** A blanket exemption that never expires
is the fail-open the 11 October correction was written to stop.

**Proposed — a declared, enumerated, ratcheted backlog.**
`image-provenance-records.json` carries a `legacy_undeclared` array listing all
85 by path and `sha256`. The guard then:

- **refuses any local asset not in either the records or that list** — so no
  new undeclared image can ever be added. The ratchet is the whole point;
- **reports the legacy count on every run**, in the CI summary, as an open
  governance item rather than a silent pass;
- **never counts a legacy entry as a declaration**, and never lets one onto a
  product card or into a supplier context.

Backfilling is then ordinary work, done from real knowledge: Colin names the
tool, date and prompt for each batch as they are recalled or recovered, the
entry moves from `legacy_undeclared` to `records`, and the count drops. The
number only goes down, and it is visible in every build until it reaches zero.

If a legacy image's provenance genuinely cannot be recovered, the honest
outcomes are to re-generate it with a recorded prompt, or to retire it —
**not** to declare what nobody knows.

---

## 6 · A SEPARATE DEFECT FOUND WHILE AUDITING

`.github/workflows/image-rights-gate.yml`, the step named *"Prove the
image-rights gate still catches what it is for"*:

```yaml
test -f atlas-tools/prove-image-rights-gate-capability.mjs \
  && node atlas-tools/prove-image-rights-gate-capability.mjs \
  || echo "no image-rights capability proof in this repo yet; see FOLLOW-UPS"
```

**`atlas-tools/prove-image-rights-gate-capability.mjs` does not exist.** The
step prints a notice and passes on every run.

This is the same defect the comment directly above it records as having been
closed on 11 October — a `|| echo` fallback over a proof that was never there,
green by default. It was fixed in one step and reintroduced in the next.

Unrelated to AI illustrations, outside this proposal's scope, and worth a
separate decision: either write that proof or remove the step, but not leave a
guard-proof step that cannot fail.

---

## 7 · WHAT IS EXPLICITLY NOT CHANGED

- **Every existing supplier permission.** `image-rights-records.json` and
  `image-rights-manifest.json` are not edited. 40 externally-hosted images,
  13 organisation rows, all preserved.
- **The publication gate.** `derivePublicVisibility()` is untouched. BIOBUILDS
  stays on HOLD, and provenance is not an input to visibility — a third
  dimension in that derivation is exactly what the 11 October correction was
  written to prevent.
- **Product cards.** No AI illustration reaches one. `product-card` is not in
  the permitted-surface vocabulary, so enabling it is a deliberate schema
  change with its own approval, not an oversight away.
- **The rights gate's own logic.** `validate-image-rights.js` gains nothing.
  The new guard runs beside it and the two never answer each other's question.

---

## 8 · PROPOSED ORDER, IF AUTHORISED

1. `image-provenance-records.json` — schema, the 85 `legacy_undeclared`
   entries with real hashes computed from disk, and zero `records`.
2. `validate-image-provenance.js` — P1–P11, plus its capability proof.
3. Add both to the CI workflow. **No `||` fallback.**
4. Backfill a first real batch to prove the route works end to end.
5. **Then, and only then**, the visible label (§3.3) — a page change,
   separately authorised, with before/after captures.

Steps 1–4 are repository-only and change nothing a homeowner sees. Step 5 is
the only website change, and it is last because the label should arrive once
the records behind it are real.
