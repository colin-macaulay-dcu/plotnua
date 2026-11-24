# PlotArt · proofs that already fail on main (recorded 24 Nov 2026, for separate investigation)

Recorded during the three-gallery Phase A preview (branch `preview/plotart-three-galleries-phase-a`), at the founder's
request. All six fail **in the same way on main `9261e56` as on the preview branch**: Phase A did not cause them and did not
change their results. None of them is run by the Image rights gate workflow; every gate check passes (36 / 36).

They were run in a cloud session with a **shallow clone** (`--depth 1`) and **without the Python Playwright package**, which
explains several of them. Re-run each with full history and the browser tooling before treating it as a code defect.

| Proof | What fails | Likely cause | Suggested next step |
|---|---|---|---|
| `atlas-tools/prove-plotart-featured.py` | Stops with `TypeError: 'NoneType' object is not callable` at `sync_playwright()` (line 339), so the browser checks never run | The Python `playwright` package is not installed in that environment | Install Python Playwright (`pip install playwright`), re-run, then judge the real result |
| `atlas-tools/prove-plotart-vg-collection.py` | G10 ("the markers are removed → refused"): the launch guard raises `ValueError: substring not found` instead of reporting a refusal; C2: two artist gallery pages (`anna-marie-savage/index.html`, `mark-kavanagh-rasher/index.html`) differ from the current renderer's body | G10: `prove-plotart-launch.py` reads a region without first checking its markers exist (it refuses, but by crashing). C2: those two pages were published by an older renderer and have not been re-published since | G10: make that guard read fail with a clear L-message. C2: a routine re-publication of the two galleries brings them up to date |
| `atlas-tools/prove-plotart-join.py` | O1 compares the Join form with the Founding 25 form at commit `43655d8^`, which a shallow clone does not have, so the comparison list is empty; then `ValueError: substring not found` (line 165) for the same reason | Needs git history (`git show 43655d8^:…`) | Re-run in a full clone |
| `atlas-tools/prove-plotart-hire-release.py` | D2b: "no commit with Art for Hire off was found", then `TypeError` (line 79) | Searches git history for a commit with `art_for_hire_page` off; a shallow clone has none | Re-run in a full clone |
| `atlas-tools/prove-plotart-commissions.py` | C2: "every artwork page byte-identical to main's renderer" fails | The same stale artist pages as vg-collection C2 (published by an older renderer) | Re-publish the affected galleries, then re-run |
| `atlas-tools/prove-plotart-refine.cjs` | `ERR_INVALID_ARG_TYPE` reading `process.argv[3]` | It is a browser test harness that needs a running local server and an EXPECTED.json argument (`node … http://127.0.0.1:8767 EXPECTED.json`); it was started without them | Run it as documented in its header |

No production, payment, image-rights or publishing safeguard depends on fixing these first: the publisher's own guards
(content boundary, launch guard, image provenance, image rights) all pass.
