# PlotNua release process

*Founder decision, 23 October 2026. This is how every PlotNua release reaches production.*

## The rules

1. **Nothing reaches production without Colin's explicit approval.** Production changes only when Colin runs `--release` and types the confirmation.
2. **The Image Rights Gate decides, for one exact commit.**
   - Pushing a `release/*` branch starts the gate by itself on exactly that commit.
   - The scripts accept only a green run on the release's own 40-character commit, on its own release branch.
   - A green run on any other commit, branch or workflow never counts, however recent.
   - If a later run on the same commit failed, the release is refused.
3. **Nobody vouches for the gate by hand.** There is no "Run workflow" click and no `GATE_GREEN=yes`. If GitHub cannot be read, the scripts refuse.
4. **Never forced.** Releases are fast-forwards of production. Rollbacks are revert commits.

## Step by step

| Step | Who | What happens |
|---|---|---|
| 1 · Prepare | Claude | Builds and tests the change locally from current production. Writes the release folder: report, preview `site/`, bundle, `deploy-<name>.sh`, `rollback-<name>.sh`. The scripts come from `atlas-tools/release/make-release-scripts.py`. |
| 2 · Preview | Colin | Opens the preview on Mac and iPhone. |
| 3 · Stage | Colin, after approving | `bash deploy-<name>.sh --stage` · runs every check in a clean checkout · pushes **only** `release/<name>` · the gate starts by itself · the script waits (up to 20 min) and prints the result and run link. Production is unchanged. |
| 4 · Release | Colin, after approving | `bash deploy-<name>.sh --release` · re-checks everything · confirms the gate passed on exactly this commit · asks you to type `RELEASE <commit>` · fast-forwards `main`. |
| 5 · Verify | Claude | Verifies production live and reports. |
| Rollback | Colin only | `bash rollback-<name>.sh`, confirmed by typing `ROLLBACK <commit>` · revert commits · production content returns exactly to the previous commit. |

**Any time:** `bash deploy-<name>.sh --status` prints the gate result for the release commit.

## What the scripts refuse

The scripts push nothing when any of these is true:
- `main` has moved since the release was prepared;
- the bundle hash, commit, tree, commit count or exact changed-file list differs;
- a commit message would skip CI;
- the release's own gate does not run on `release/*` pushes;
- any production check fails;
- the gate has not passed on exactly this commit;
- the confirmation was not typed at the keyboard.

## Pieces

| File | Role |
|---|---|
| `.github/workflows/image-rights-gate.yml` | Runs on `main`, `release/**`, pull requests and manual dispatch. All checks are unchanged. Permissions: `contents: read`. No secrets. |
| `atlas-tools/release/gate-result.py` | Reads the gate result for one exact commit and branch. Read-only. Exit codes: 0 passed · 2 failed · 3 pending · 4 no run · 5 unreadable. |
| `atlas-tools/release/prove-gate-result.py` | 18 recorded cases, run in the gate itself: only the exact commit's own green run approves. |
| `atlas-tools/release/deploy-template.sh`, `rollback-template.sh` | The guarded scripts every release is generated from. |
| `atlas-tools/release/make-release-scripts.py` | Fills the templates: commit, tree, file list, bundle, standard and release-specific checks. |

## GitHub access

- **Reading the gate:** the repository is public, so the scripts read GitHub's API with no token.
- **If the repository is ever made private:** run `gh auth login` once on the Mac (classic `repo` scope, or a fine-grained token with *Actions: read* and *Metadata: read* on this repository). The reader then uses `gh` automatically.
- **Pushing:** stays your SSH key. No new permissions are needed.
- **Optional server-side backstop:** a ruleset on `main` requiring the "Image rights gate / gate" check, so GitHub itself refuses an untested update to production. This needs repository admin.
