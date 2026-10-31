# PlotArt Studio · deployment workflows (prepared 31 Oct 2026, not yet active)

- `.github/workflows/studio-deploy.yml`: deploys the Studio Worker at one exact commit. Environment `studio-production`
  (required reviewer: the founder; secret `CLOUDFLARE_API_TOKEN` with Workers Scripts: Edit only).
- `.github/workflows/studio-d1-migration.yml`: runs one migration file at one exact commit. Environment `studio-database`
  (required reviewer: the founder; secret `CLOUDFLARE_API_TOKEN` with D1: Edit only).

Both are started by hand with a full commit ID, refuse any commit not already on main, and cannot read their token
until the founder presses Approve in GitHub. `dry_run: true` (the default) exercises the approval without contacting Cloudflare.

| File | What it does |
|---|---|
| `guard.sh` | Full commit ID; on main; contains the live Studio release (tag `studio-live`); the bundle matches its sources; lists the Studio files that change |
| `render-config.py` | Production `wrangler.production.toml` from `wrangler.toml` + environment variables + `worker/plotart-studio/production.json` |
| `order-check.mjs` | Gallery order before/after a deployment from the pipeline view: 01 reserved, order unchanged (no names, notes or addresses printed) |
| `d1-check.sql`, `d1-fingerprint.mjs` | Database fingerprints before/after a migration: PASS/FAIL and short hashes only |

Logs are public: nothing prints a credential, an environment identifier, a count, a name, an email address or a note.
