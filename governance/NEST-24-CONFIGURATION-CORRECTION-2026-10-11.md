# BIOBUILDS NEST 24 · THE BLOCKED SNAPSHOT

Raised 11 October 2026 when `deploy-biobuilds.sh` stopped at the snapshot:

```
BIOBUILDS Nest 24 carries 2 numeric pricing rows and 2 of them have no
Configuration. Atlas cannot say which price to show, so the product would be
published with no price at all. Rows: recbpHBkH3mA0oEPP, recq2C9BkhWSRhODN
```

No snapshot written. No repository file changed. **The guard was right to stop**,
and the stop is worth more than the inconvenience: without it Nest 24 would
have regenerated as a held product with no price, silently.

---

## 1 · WHAT EACH PRICE REPRESENTS

Both records are, in fact, documented in unusual detail. The scope of each is
recorded in **three** places — the record title, the Known Exclusions prose,
and (for one row) the Price Type.

| record | amount | scope, in the supplier's own wording | Price Type |
|---|---|---|---|
| `recbpHBkH3mA0oEPP` | €101,100 incl. VAT | **TURNKEY** — "Finished inside and out" | `Turnkey` |
| `recq2C9BkhWSRhODN` | €74,300 incl. VAT | **EXTERIOR FINISHED** — "Be your own interior designer" | `Standard Price` |

Both: Product-Specific, Verified, `Price Includes VAT = Yes`, VAT rate not
published and not inferred, source `SRC-BBD-IE-001`, delivery and installation
to Ireland included, foundations / utility connections / Irish adaptations
quoted separately, no kitchen.

The Exterior Finished record even documents the workaround explicitly:

> PRICE-TYPE NOTE: recorded as Standard Price because the Atlas Pricing type
> list has no 'Exterior Finished'/'Shell' option; the actual published scope is
> stated in full above and must be read from these notes, not from the type
> field alone. No new select option was created.

That is a curator saying, in the record, that the mapping was incomplete.

## 2 · FIELD-MAPPING ISSUE, NOT A DATA OMISSION

**Mapping.** The scope was never missing — it was written where the generator
does not look. `additional_home_qualification._configuration_of()` reads the
`Configuration` field. That field exists, and already carries exactly the two
labels needed:

```
Configuration (fldp4puJm09VbGYR6) — single select, existing options:
  Exterior Finished   selI6YdqBdK6AWkZq
  Turnkey             selsVQgLnXra1nNOq
  Basic               selBsJJ9kOBr9sBTQ
  Optima              selrBZqksQuLlJjiX
```

**No label needs inventing.** Both required options already exist, and both are
already in use elsewhere.

Four other Additional Home products carry more than one numeric price, and all
four are correctly labelled — which is also how we know the field name and the
convention are right, because the founder's run passed them and stopped only
on Nest 24:

| product | rows | labels |
|---|---|---|
| PROD-000523 Wanderlust | 2 | Exterior Finished · Turnkey |
| PROD-000524 Serenity | 2 | Exterior Finished · Turnkey |
| PROD-000526 Baby (Tiny House Heavens) | 2 | Basic · Optima |
| PROD-000527 Liora (Tiny House Heavens) | 2 | Basic · Optima |
| **PROD-001172 Nest 24** | **2** | **none — this is the whole defect** |

Nest 24 was intaken on 28 September, and the two rows were created in the same
minute. It is a single-product gap in one intake, not a systemic failure.

## 3 · THE CORRECTION

Two single-select writes. Nothing else. No price, VAT field, status, evidence
scope, source link, prose or permission is touched.

```
Table    Pricing (tblqsjmkTrwSct7gv)
Field    Configuration (fldp4puJm09VbGYR6)

recbpHBkH3mA0oEPP   €101,100 Turnkey row            →  Turnkey
recq2C9BkhWSRhODN   €74,300 Exterior Finished row    →  Exterior Finished
```

Both values are existing select options; **do not create a new option.**

### Measured outcome, through the real functions

```
                         BEFORE                        AFTER
snapshot guard           REFUSED                       ACCEPTED
price state              PRICE_AMBIGUOUS_MULTI_ROW     VERIFIED_NUMERIC_PRICE
scalar                   None                          74,300 EUR (the lower, per contract)
VAT basis                None                          INCLUDES_VAT
configurations           none                          Exterior Finished  74,300
                                                       Turnkey           101,100
commercialTerms          none                          none — see below
Class 3A                 NOT_A_CANDIDATE               NOT_A_CANDIDATE (no-usable-area)
```

Two consequences worth stating plainly:

**No commercial terms are published for Nest 24.** Its Known Exclusions wording
("quoted separately", "Transport to Ireland and assembly") does not match the
four `COMMERCIAL_TERM_ANCHORS`, which require phrases such as "quoted per
project". So no token is produced and no term is stated. That is the
honest-direction failure BB-CFG-002 predicted: thin, not wrong. Nothing renders
an absent term as an inclusion.

**Nest 24 does not enter Class 3A Results.** It has no feature values at all,
so no interior area — `no-usable-area`, the same containment as Serenity. It
also has no approved imagery: the BIOBUILDS grant enumerates six assets, three
for PROD-000523 and three for PROD-000524, none for PROD-001172. So this
correction does not put Nest 24 in front of a homeowner.

Do **not** read an area from the model name. BIOBUILDS' own naming is a
configurator key, not a measurement — the Wanderlust record says so, and the
live page proves it: "Wanderlust 48" has a published interior of 35.54 m², and
"Serenity 95" has 77.06–78.21 m².

## 4 · A SEPARATE PROBLEM THE GUARD HAS UNCOVERED

Applying §3 unblocks the deployment. It does not settle this, and this needs a
founder decision rather than a mechanical fix.

**Nest 24's Irish prices cannot be re-verified first-party today.** Checked
11 October 2026:

- `biobuilds.com/ie/design` publishes **four** models — Wanderlust, Serenity,
  Sanctuary, Bloom. Anchors `#wanderlust-48`, `#serenity-95`, `#sanctuary-142`,
  `#bloom-190`. There is **no Nest and no `#nest-24`**, which is the exact URL
  the Atlas records cite as their source.
- `biobuilds.com/design` (EU) publishes the same four. No Nest.
- Nest is nonetheless a real BIOBUILDS model: a 24 m² unit referenced on the
  company's blog, FAQ, catalog and turnkey pages, with a blog figure of "From
  €62,200" net of VAT — which is what the Atlas record itself notes as the EU
  price. It appears to have been withdrawn from, or never carried on, the
  configurators now serving Ireland and the EU.

The 28 September capture has also drifted on figures that *can* still be
compared. The Nest 24 record lists the option prices as smart blinds €2,500,
Zehnder ventilation €6,000, prosumer solar €9,800. The live Irish configurator
today lists €5,000, €9,500 and €14,500.

**Wanderlust and Serenity are unaffected.** Their Irish figures on the live page
today match Atlas exactly — €105,000 / €163,000 and €191,000 / €306,000, with
Wanderlust's interior at 35.54 m². The drift is specific to Nest 24, not general
staleness, so the authorised deployment is still correct.

### The decision

**Option A — apply §3, deploy, then re-verify Nest 24.**
Proportionate, and my recommendation. Nest 24 reaches no homeowner surface
(no usable area, no imagery), so the exposure is an unverifiable price sitting
in the artefact marked `Verified`, which is a governance debt rather than a
homeowner-facing falsehood. Deploy Wanderlust as authorised, then settle Nest
24 on its own.

**Option B — apply §3, and also mark Nest 24's two prices as not currently
verified before regenerating.**
Stricter. It keeps `Verified` honest in the one place that word is load-bearing.
It costs a second Airtable edit and a fresh judgement about which status value
is right, which is a decision this note should not make for you.

Either way the §3 labels are correct and should be applied: they describe what
the supplier published, which is true of the capture whatever its current
availability.

## 5 · WHAT IS EXPLICITLY NOT PROPOSED

- The snapshot validation is **not** weakened, relaxed or scoped around. It
  found a real defect on its first real run.
- No `Configuration` option is created.
- No price, VAT field, status, evidence scope, source or prose is edited.
- No other product is touched. Baby, Liora, Wanderlust and Serenity are already
  correct and must be left alone.
- The Turnkey row's `Price Type = Turnkey` is left as it is. It is inconsistent
  with the Wanderlust convention (`Standard Price` on both rows), but it has
  **no runtime effect**: `pnPriceToken` recognises only `starting from`,
  `estimated price` and `custom quote`, so `Turnkey` falls through to an exact
  figure, and `Turnkey` is not in `QUOTE_TYPES`. Changing a Verified record for
  tidiness alone is scope creep, so it is recorded here and not done.
- Nothing is deployed.

## 6 · RERUN

After the two writes:

```bash
cd ~/Documents/PlotNua/04\ Deploy/plotnua-github
read -rs AIRTABLE_TOKEN && export AIRTABLE_TOKEN
./atlas-tools/deploy-biobuilds.sh
```

The snapshot should now pass the configuration check. If it stops again, the
message names the product and the rows, exactly as it did here.
