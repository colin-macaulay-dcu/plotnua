# PlotArt Studio · deployment workflows (prepared; inactive until the founder's setup)

- `.github/workflows/studio-deploy.yml`: deploys the Studio Worker at one exact commit already on main. Environment
  `studio-production.` (exact name, with a final full stop) (required reviewer: the founder; secret `STUDIO_CF_DEPLOY_TOKEN`, Workers Scripts: Edit only).
  Read-only repository access. The live release is read from this workflow's own successful runs.
- `.github/workflows/studio-d1-migration.yml`: one approved migration file (SHA-256), declared tables and described
  effects. Environment `studio-database` (required reviewer: the founder; secrets `STUDIO_CF_D1_TOKEN`, D1: Edit only,
  and `STUDIO_BACKUP_PASSPHRASE`). Two backups before it runs: a Time Travel restore point and an encrypted full export.

Both are started by hand, default to a dry run, and cannot read their secrets until the founder presses Approve in GitHub.

| File | What it does |
|---|---|
| `guard.sh` | Full commit ID; on main; contains the live Studio release; the bundle matches its sources; lists changed Studio files |
| `render-config.py` | Production `wrangler.production.toml` from `wrangler.toml` + environment variables + `worker/plotart-studio/production.json` |
| `order-check.mjs` | Gallery order before/after a Worker deployment (pipeline view): 01 reserved, order unchanged |
| `migration-check.py` | Approved file (SHA-256), described effects, every table the SQL writes to declared; no triggers, ATTACH or PRAGMA writes |
| `d1-snapshot.mjs` | Every table's fingerprint before/after a migration: fails if anything outside the declaration changed or 01 is released |

Logs are public: nothing prints a credential, an environment identifier, a count, a name, an email address or a note.
A failed check never restores anything by itself: a restore needs the founder's separate approval.
