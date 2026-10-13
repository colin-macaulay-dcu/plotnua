# The Borrowed Garden · Provider Explorer · governance record

**Founder approval:** 13 October 2026. The evidence pack is approved with conditions. Publication awaits a separate founder approval.

## Atlas records created 13 Oct 2026 (base `appoLZFWesvoPhZGR`)

**Discovery:** DISC-025 The Borrowed Garden (`recLkjbt4kCyQWTsT`).

**Organisations**

| Code | Name | Organisation Type | Partner Status | Record |
|---|---|---|---|---|
| ORG-000202 | Community Roots | Service Provider | Researching | `recjAV6RKIhEjMzzd` |
| ORG-000203 | Homegrown.ie | Service Provider | **Strategic Hold** | `recmsuYqFwv29IsW1` |
| ORG-000204 | Dublin City Council | Government | Researching | `recY9h82QghJ1oB4a` |
| ORG-000205 | Fingal County Council | Government | Researching | `recfdDnGD3G3iblUc` |
| ORG-000206 | Dún Laoghaire-Rathdown County Council | Government | Researching | `recSbjcpAu8SmOoFa` |

**Sources:** SRC-DISC025-01 to 09. SRC-DISC025-03 (communityroots.ie) is background only and is never used publicly. Following the existing Sources convention, the code is held in the primary "Source Title" field and the descriptive title in "Source Code".

**Partner records: 0. Product records: 0.**

## Rules

- **Homegrown.ie, Strategic Hold:** research and public factual display are permitted. No outreach without explicit founder approval.
- **Data path:** Atlas read-back (`atlas-tools/borrowed-garden-provider-atlas-snapshot.json`) plus approved wording (`atlas-tools/borrowed-garden-provider-text-v1.json`) feed `build-borrowed-garden-provider-universe.py`, which writes `borrowed-garden-provider-universe-v1.json`. `build-provider-explorer.py` then places it on the page. The page never reads Atlas.
- **Evidence refresh:**
  - 90-day review threshold.
  - A time-sensitive sentence is withheld once any of its sources is older than 90 days.
  - Non-time-sensitive sentences stay, flagged for review, up to 180 days.
  - Nothing is deleted from Atlas.
  - The build stops with a review list rather than silently dropping an organisation or the explorer.
  - First review due **15 Dec 2026**, when the Community Roots Rush project evidence turns 90 days old.
- **Community Roots:** the unconfirmed referee requirement is not published (founder ruling).
- **Councils:** in "Other growing opportunities", each labelled "This is not garden-sharing."
- **On the page:** no links, no partner labels, no ranking, no data collected. The Property Check and Garden Owner Register are unchanged.

## Live-page corrections in the same change

- **Homegrown.ie:** "with demand last reviewed in August 2026" is replaced by "which carry no review date". The site shows no date; "first ten hosts" was re-confirmed on 13 Oct 2026.
- **DLR:** "closed … in September 2024" is replaced by "is not accepting new applications … under a council notice dated September 2024".
