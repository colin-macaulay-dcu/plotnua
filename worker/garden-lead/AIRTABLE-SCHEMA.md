# Garden Room Leads — Airtable table

One table. Fifteen fields. Create it exactly as below, in the base whose id is set as the
Worker's `AIRTABLE_BASE`. `typecast` is **false** on every write, so a field that does not exist
here, or a single-select option that is not listed, is a **rejected** write rather than a
silently created one. That is deliberate: it means the table cannot drift to match a bug.

**Table name:** `Garden Room Leads` — exactly, including the spaces.

| Field | Type | Notes |
|---|---|---|
| `lead_id` | Single line text | `PNL-YYYYMMDD-XXXXXXXX`. Minted by the Worker, never by the caller |
| `created_at` | Single line text | UTC ISO 8601, e.g. `2026-10-10T11:04:22Z`. Text, not Date, so what is stored is exactly what was written |
| `product_id` | Single line text | Atlas product record id |
| `product_name` | Single line text | |
| `supplier_org_id` | Single line text | `ORG-000157` |
| `supplier_name` | Single line text | `Yard Box` |
| `homeowner_name` | Single line text | |
| `homeowner_email` | Email | |
| `county` | Single line text | Town or county as typed. **Never an address or Eircode** |
| `message` | Long text | The homeowner's own words. A Phase A test lead is prefixed `[PLOTNUA PHASE A TEST LEAD — NOT A HOMEOWNER]` |
| `consent_text_hash` | Single line text | SHA-256 of the consent sentence actually rendered |
| `consent_at` | Single line text | UTC ISO 8601 |
| `privacy_version` | Single line text | `2026-10-FIRSTLEAD-V1` |
| `source` | Single line text | `plotnua.garden-room.resolve` |
| `status` | Single select | Options below |

**`status` options — create all five, exactly:**

`RECEIVED` · `FORWARDED` · `SUPPLIER_ACKNOWLEDGED` · `OUTCOME_KNOWN` · `NOT_FORWARDED`

**The Worker can only ever write `RECEIVED`.** The other four are human acts, set by hand after
something has actually happened. There is no automated path to any of them, which is what keeps
"forwarded" a statement about something that was really done.

**`NOT_FORWARDED`** exists so a lead that is deliberately not passed on is still a closed record
rather than one that was quietly abandoned.

## Deploy

```
cd worker/garden-lead
wrangler secret put AIRTABLE_TOKEN      # scoped to this base only
wrangler secret put LEAD_PREVIEW_KEY    # >= 16 chars; never put it in a file
wrangler deploy --var AIRTABLE_BASE:appXXXXXXXXXXXXXX
```

Then, and only then, flip `WRITES_ENABLED` to `"true"`.
**`LEAD_PUBLIC_ENABLED` and `EMAIL_ENABLED` stay `"false"` for the whole of Phase A.**
