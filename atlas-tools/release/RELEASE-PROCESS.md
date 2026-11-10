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
| `.github/workflows/image-rights-gate.yml` | Runs on `main`, `release/**`, pull requests and manual dispatch. **Only push-started runs count for main's required check.** Permissions: `contents: read`. No secrets. |
| `atlas-tools/release/push-release-branch.sh` | Pushes a release branch with the release App token in Actions (refuses without it), or the caller's credentials elsewhere. Never `main`, never forced. |
| `atlas-tools/release/gate-result.py` | Reads the gate result for one exact commit and branch. Read-only. Exit codes: 0 passed · 2 failed · 3 pending · 4 no run · 5 unreadable. |
| `atlas-tools/release/prove-gate-result.py` | 18 recorded cases, run in the gate itself: only the exact commit's own green run approves. |
| `atlas-tools/release/deploy-template.sh`, `rollback-template.sh` | The guarded scripts every release is generated from. |
| `atlas-tools/release/make-release-scripts.py` | Fills the templates: commit, tree, file list, bundle, standard and release-specific checks. |

## GitHub access

- **Reading the gate:** the repository is public, so the scripts read GitHub's API with no token.
- **If the repository is ever made private:** run `gh auth login` once on the Mac (classic `repo` scope, or a fine-grained token with *Actions: read* and *Metadata: read* on this repository). The reader then uses `gh` automatically.
- **Pushing:** stays your SSH key. No new permissions are needed.
- **Server-side backstop:** the `protect-main` ruleset blocks deletion and force-pushes. Its **required status check `gate` (GitHub Actions)** was switched on 10 Nov 2026, then switched off again the same evening (see below). It goes back on after the Stage 1 release is verified.

## Automated releases (`release/auto/`) and the PlotNua Release App

*Stage 1, 10 November 2026.*

**What GitHub counts.** GitHub only counts a gate run toward `main`'s required `gate` check if the run was started by a **push** (or a pull request). A run that was **dispatched** shows a green check, but it never satisfies the rule, and it never starts "Release to production". On 10 Nov a PlotArt release was refused for exactly this reason.

**How the route works now:**

1. **Pushing the branch.** The release tools (`request-release.sh`, and `promote.sh` for automatic rollbacks) push the `release/auto/…` branch through `push-release-branch.sh`.
   - **In GitHub Actions** the push uses a 1-hour token of the GitHub App **"PlotNua Release"** (ID 5704323). The App is installed on this repository only. Its permissions are Contents read & write and Metadata read. It has **no Workflows permission**.
   - **Without that token, in Actions, the push is refused**, so nothing is released.
   - **On a Mac or in a Claude session** it is an ordinary push with the caller's own credentials.
2. **Gate and promotion.** The gate starts on that push. Nothing dispatches it any more.
   - "Release to production" promotes `release/auto/*` branches, except the publishers that promote their own releases and rollbacks: `plotart-`, `garden-` and `ideas-`.
   - Atlas stats, Atlas Match and Claude-session releases are promoted by "Release to production".
3. **Where the key lives.** The App key is the environment secret `RELEASE_APP_KEY` of the environment **`release-automation`** (deployment branches: `main` only), alongside the variable `RELEASE_APP_ID`.
   - Only the releasing jobs use that environment, with `deployment: false`, so no deployment records are created.
   - The key is never stored in the repository or in any report.
4. **Automatic rollback.**
   - The revert is pushed to `release/auto/rollback-<topic>` with the App token, gated on its push, and released.
   - **Releases that changed `.github/workflows/` cannot be reverted by the App**, by design. The run stops with **"FOUNDER ROLLBACK REQUIRED"**, and the founder runs `rollback-<name>.sh`.
5. **Proofs (run in the gate):**
   - `prove-release-app-push.py` (A1–A8, with a planted-fault self-test);
   - `prove-release-promote.sh` (local throw-away repositories).

**Key rotation:** once a year, or on suspicion.
1. Generate a new private key on the App page.
2. Paste it into `RELEASE_APP_KEY`.
3. Delete the old key.

**Emergency:** suspend or uninstall the App; releases are then refused, and nothing unchecked can reach production. To let checked releases through while that is fixed, untick the required check in `protect-main`.
