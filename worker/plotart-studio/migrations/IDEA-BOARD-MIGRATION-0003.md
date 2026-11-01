# Idea Board · D1 migration 0003 · approval package

**Status: NOT APPLIED. Approval requested. Nothing has been sent to Cloudflare.**
Prepared 1 November 2026 on branch `dev/idea-board`, for the PlotArt Studio production database `plotart-studio`.

## 1. What it does

It adds two new tables and one index. It is additive only: no existing table, column, row or index changes.

| Object | Purpose | Personal data |
|---|---|---|
| `ideas` (table) | One row per submitted idea. Holds the wording, an optional area, an optional county and whether to show it, the moderation status, an optional edited public wording and an optional "Now a Discovery" link. | None about the visitor. No name, e-mail, telephone, IP address, user-agent or cookie. `decided_by` holds the founder's own sign-in e-mail. |
| `ideas_status_published` (index) | Lets the board and the Studio list ideas by status and date. | — |
| `idea_intake_days` (table) | One number per UTC day, used for the daily cap of 60. | None |

The database enforces the rules too:
- the text is 8–160 characters;
- the area must come from the list of seven;
- the status must be one of the four;
- the "Now a Discovery" link must be a `discovery-*.html` page;
- a county can be shown only if one was given.

## 2. Exact SQL

- File: `worker/plotart-studio/migrations/0003_ideas.sql`
- SHA-256: `bf044dc5c917faf6a5b88d2e7cf7efa92faa1c0ca6b0c063c72cc8f8a1a57496`

```sql
CREATE TABLE ideas (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL CHECK (length(text) BETWEEN 8 AND 160),
  public_text TEXT CHECK (public_text IS NULL OR length(public_text) BETWEEN 8 AND 160),
  area TEXT CHECK (area IS NULL OR area IN ('Space', 'Garden', 'Art', 'Energy', 'Frontage', 'Neighbourhood', 'Income')),
  county TEXT CHECK (county IS NULL OR length(county) BETWEEN 3 AND 20),
  show_county INTEGER NOT NULL DEFAULT 0 CHECK (show_county IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'approved', 'not_approved', 'removed')),
  became_discovery TEXT CHECK (became_discovery IS NULL OR became_discovery GLOB 'discovery-[a-z0-9]*.html'),
  edited INTEGER NOT NULL DEFAULT 0 CHECK (edited IN (0, 1)),
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by TEXT,
  published_at TEXT,
  removed_at TEXT,
  CHECK (show_county = 0 OR county IS NOT NULL)
);
CREATE INDEX ideas_status_published ON ideas(status, published_at);
CREATE TABLE idea_intake_days (
  day TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0
);
```

The tables are created with plain `CREATE TABLE`, not `IF NOT EXISTS`. If the migration is run a second time by mistake, the database refuses it and changes nothing.

## 3. Backup procedure

Use the existing governed workflow, **PlotArt Studio · D1 migration** (`.github/workflows/studio-d1-migration.yml`). It runs only on `main`, by hand, with these inputs.

**Inputs**

| Input | Value |
|---|---|
| commit | the full 40-character commit on `main` that contains this file (it exists only after the branch is released) |
| migration | `0003_ideas.sql` |
| migration_sha256 | `bf044dc5c917faf6a5b88d2e7cf7efa92faa1c0ca6b0c063c72cc8f8a1a57496` |
| tables | `ideas,idea_intake_days` |
| expected_effects | Adds the Idea Board tables ideas and idea_intake_days and the index ideas_status_published. No existing table, column or row changes. Both new tables are empty. |
| dry_run | first `true`, then `false` |

**What the workflow does**

1. **Approval check.** `migration-check.py` refuses unless the file's SHA-256 matches and every table the SQL writes to is declared. It was run locally: `MIGRATION CHECK OK`. Declaring only `ideas` is refused, as it should be.
2. **Backup 1 of 2, Time Travel restore point.** It records the current D1 bookmark and puts it in the run summary. If no bookmark is available, it stops and nothing is applied.
3. **Backup 2 of 2, full export.** It runs `wrangler d1 export plotart-studio --remote` and checks that the export contains `artists`. It then encrypts the export with AES-256 using the `STUDIO_BACKUP_PASSPHRASE` secret and confirms the encrypted file decrypts to the export. The encrypted file is kept as a workflow artifact for 90 days. If the export fails, the migration does not start.
4. **Fingerprint before.** It records a fingerprint of every existing table.
5. **Apply.** It runs `wrangler d1 execute plotart-studio --remote --file migrations/0003_ideas.sql`.
6. **Compare.** It checks that only the declared tables changed. Every existing table must be identical to before.
7. **On any failure after the backups,** it does not restore automatically. It reports the restore point and the backup, and any restore needs your separate approval.

**Recommended order**

1. Release the code to `main`, inert: the intake Worker is not deployed and the pipeline is switched off.
2. Run this workflow as a dry run.
3. Run it for real, after you give the approval in section 5.
4. Deploy the Studio.

The Studio code is safe before the migration. Until the tables exist, its Ideas tab says "The Idea Board isn't installed yet (migration 0003 has not been applied)", and the nightly clean-up skips the ideas.

## 4. Rollback procedure

**Option A, remove the Idea Board tables (normal rollback).**
- File: `worker/plotart-studio/migrations/0003_ideas_rollback.sql`
- SHA-256: `07d82c92d1dc074df722702691efd6c1d88d60bbd12a589847db7292b9e3a7d0`

```sql
DROP TABLE IF EXISTS ideas;
DROP TABLE IF EXISTS idea_intake_days;
```

- Run it through the same governed workflow, with migration `0003_ideas_rollback.sql` and tables `ideas,idea_intake_days`. The workflow takes the same two backups first.
- Dropping the table also drops its index.
- It deletes every idea received. Before running it:
  - switch off the intake (`IDEAS_ENABLED=false`);
  - switch off the publisher (`IDEAS_PUBLISH_ENABLED` unset);
  - put the "not taking ideas" page live (`config.json` endpoint `null`).
- `migration-check.py` on the rollback: `MIGRATION CHECK OK`.

**Option B, restore the whole database to before the migration.**
- Use the Time Travel bookmark from step 2: `wrangler d1 time-travel restore plotart-studio --bookmark=<bookmark>`.
- This also undoes anything else written after that moment, such as artist activity. Use it only if Option A is not enough, and only with your separate approval.

**Proven locally** (`node test/prove-migration-0003.mjs`, on the current production schema with realistic rows): **9 of 9 pass**.

| Check | Result |
|---|---|
| M1 | Every existing row is unchanged |
| M2 | Exactly two tables and one index are added |
| M3 | The new tables are empty |
| M4 | No personal-data columns |
| M5, M6 | Invalid rows are refused; valid rows are accepted |
| M7 | A re-run is refused |
| M8 | The rollback restores exactly the previous objects and rows |
| M9 | The migration can be re-applied cleanly after a rollback |

## 5. Approval requested

> I approve applying `worker/plotart-studio/migrations/0003_ideas.sql`, SHA-256
> `bf044dc5c917faf6a5b88d2e7cf7efa92faa1c0ca6b0c063c72cc8f8a1a57496`, to the production D1 database `plotart-studio`
> through the governed D1 migration workflow, declared tables `ideas,idea_intake_days`, after its Time Travel restore
> point and encrypted full export, from commit `<commit on main>`.

This approval is **not** being requested now. It is requested only after you have reviewed the Phase 1 results and approved releasing the code to `main`. Until then, nothing in this package can run: the workflow refuses any commit that is not on `main`.
