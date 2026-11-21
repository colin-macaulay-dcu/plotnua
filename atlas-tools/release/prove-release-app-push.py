#!/usr/bin/env python3
"""PlotNua · static proof of the release-App push route (Stage 1, 10 Nov 2026). Read-only; runs in the Image rights gate.

Why it exists: main's required "gate" check only counts gate runs started by a PUSH (GitHub never counts checks from a
dispatched run), and only push-started gates start "Release to production". So every workflow that releases must push
its release/auto/ branch with the "PlotNua Release" App token, and nothing may dispatch the gate. This proof refuses:

  A1  a releasing workflow job without environment release-automation (deployment: false)
  A2  a releasing job that does not mint the App token with the pinned official action, from vars.RELEASE_APP_ID /
      secrets.RELEASE_APP_KEY, with Contents-only scope, BEFORE the step that uses it
  A3  a releasing step that does not receive RELEASE_PUSH_TOKEN from that token
  A4  "actions: write" in any releasing workflow (nothing dispatches any more)
  A5  any release tool or workflow that dispatches the Image rights gate
  A6  push-release-branch.sh that could push without the token in Actions, push main, or force
  A7  "Release to production" not leaving the self-promoting publishers' branches (and their rollbacks) to them
  A8  the App key referenced anywhere outside those environment-scoped jobs
  A11 promote.sh pushing main or a prod/ tag other than as the App, in one atomic push (Stage 2, 21 Nov 2026)

  python3 atlas-tools/release/prove-release-app-push.py [--self-test]
"""
import glob, os, re, sys, copy, json
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WF = os.path.join(ROOT, ".github", "workflows")
REL = os.path.join(ROOT, "atlas-tools", "release")
PIN = "actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510"
# workflow -> {job: [steps that push release/auto/ branches]}
RELEASING = {
    "release-promote.yml": {"promote": ["Promote, verify live, roll back automatically if the live check fails",
                                        "Release the automatic rollback (its own gate must pass on its exact commit)"],
                            "promote-atlas": ["Promote, verify live, roll back automatically if the live check fails",
                                              "Release the automatic rollback (its own gate must pass on its exact commit)"]},
    "plotnua-garden-publish.yml": {"publish": ["Publish approved noticeboard listings (content-only, guarded, gated)"],
                                   "promote": ["Wait for the gate on this exact commit, promote, verify live"]},
    "plotnua-ideas-publish.yml": {"publish": ["Publish approved ideas (content-only, guarded, fast-forward)"],
                                  "promote": ["Wait for the gate on this exact commit, promote, verify live"]},
    "plotart-content-publish.yml": {"publish": ["Publish approved gallery content (content-only, guarded, fast-forward)"]},
    "atlas-stats.yml": {"refresh": ["Commit, only if a governed figure changed"]},
    "atlas-match-universe-refresh.yml": {"refresh": ["Publish the candidates, only if they are genuinely different"]},
}
SELF_PROMOTING = ["plotart", "garden", "ideas"]


def load(name):
    with open(os.path.join(WF, name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def check(workflows, texts, tools):
    errs = []
    for name, jobs in RELEASING.items():
        w = workflows.get(name)
        if w is None:
            errs.append("A1 %s missing" % name); continue
        perms = w.get("permissions") or {}
        if perms.get("actions") == "write":
            errs.append("A4 %s grants actions: write" % name)
        for job, steps in jobs.items():
            j = (w.get("jobs") or {}).get(job)
            if not j:
                errs.append("A1 %s: job %s missing" % (name, job)); continue
            env = j.get("environment")
            if not (isinstance(env, dict) and env.get("name") == "release-automation" and env.get("deployment") is False):
                errs.append("A1 %s/%s: environment must be release-automation with deployment: false" % (name, job))
            if (j.get("permissions") or {}).get("actions") == "write":
                errs.append("A4 %s/%s grants actions: write" % (name, job))
            st = j.get("steps") or []
            names = [s.get("name") for s in st]
            app = [i for i, s in enumerate(st) if s.get("id") == "app"]
            if len(app) != 1:
                errs.append("A2 %s/%s: exactly one token step with id app required" % (name, job)); continue
            a = st[app[0]]; w_ = a.get("with") or {}
            if a.get("uses") != PIN:
                errs.append("A2 %s/%s: token step must use %s" % (name, job, PIN))
            if w_.get("app-id") != "${{ vars.RELEASE_APP_ID }}" or w_.get("private-key") != "${{ secrets.RELEASE_APP_KEY }}":
                errs.append("A2 %s/%s: token step must read vars.RELEASE_APP_ID and secrets.RELEASE_APP_KEY" % (name, job))
            if w_.get("permission-contents") != "write" or any(k.startswith("permission-") and k != "permission-contents" for k in w_):
                errs.append("A2 %s/%s: token must be scoped to permission-contents: write only" % (name, job))
            for sn in steps:
                if sn not in names:
                    errs.append("A3 %s/%s: step %r missing" % (name, job, sn)); continue
                i = names.index(sn)
                if i < app[0]:
                    errs.append("A2 %s/%s: token step must come before %r" % (name, job, sn))
                if (st[i].get("env") or {}).get("RELEASE_PUSH_TOKEN") != "${{ steps.app.outputs.token }}":
                    errs.append("A3 %s/%s: %r must receive RELEASE_PUSH_TOKEN from steps.app" % (name, job, sn))
    # A5 no dispatch of the gate anywhere
    for path, t in list(texts.items()) + list(tools.items()):
        if os.path.basename(path).startswith("prove-"):
            continue
        if re.search(r"gh\s+workflow\s+run\s+image-rights-gate", t) or re.search(r"workflows/image-rights-gate\.yml/dispatches", t):
            errs.append("A5 %s dispatches the Image rights gate" % os.path.relpath(path, ROOT))
    # A6 the push helper
    pb = tools.get(os.path.join(REL, "push-release-branch.sh"), "")
    if not pb:
        errs.append("A6 push-release-branch.sh missing")
    else:
        if 'GITHUB_ACTIONS:-}" = "true"' not in pb or "REFUSED: no RELEASE_PUSH_TOKEN" not in pb:
            errs.append("A6 push-release-branch.sh must refuse in Actions without the App token")
        if '[[ "$BR" == release/* ]]' not in pb:
            errs.append("A6 push-release-branch.sh must only push release/ branches")
        if re.search(r"push[^\n#]*(\s-f\b|--force)", pb):
            errs.append("A6 push-release-branch.sh must never force")
    for tool in ("request-release.sh", "promote.sh"):
        if "push-release-branch.sh" not in tools.get(os.path.join(REL, tool), ""):
            errs.append("A6 %s must push release branches through push-release-branch.sh" % tool)
    # A11 main and prod/ tags are pushed as the PlotNua Release App, in one atomic push (Stage 2, 21 Nov 2026)
    pr_sh = tools.get(os.path.join(REL, "promote.sh"), "")
    code = "\n".join(l for l in pr_sh.splitlines() if not l.lstrip().startswith("#"))
    if not re.search(r'GITHUB_ACTIONS:-\}" = "true" \]\s*&&\s*\[ -z "\$\{RELEASE_PUSH_TOKEN:-\}" \]', code) or "no RELEASE_PUSH_TOKEN" not in code:
        errs.append("A11 promote.sh must refuse in GitHub Actions without the App token (RELEASE_PUSH_TOKEN)")
    if code.count("push -q --atomic") != 2 or 'release_push "$SHA:refs/heads/main" "refs/tags/$T"' not in code:
        errs.append("A11 promote.sh must push main and its prod/ tag together in one --atomic push (release_push)")
    if re.search(r"(^|[^_])push[^\n]*refs/(heads/main|tags)", code.replace('release_push "$SHA:refs/heads/main" "refs/tags/$T"', "")):
        errs.append("A11 promote.sh must not push main or a tag any other way (e.g. with the built-in GITHUB_TOKEN)")
    if 'extraheader= -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $auth"' not in code:
        errs.append("A11 promote.sh must clear the built-in token and authenticate as the App only")
    if 'out="${out//"$RELEASE_PUSH_TOKEN"/***}"' not in code or re.search(r"push[^\n#]*(\s-f\b|--force)", code):
        errs.append("A11 promote.sh must redact the token from git's output and never force")
    # A7 Release to production leaves self-promoting publishers alone
    rp = workflows.get("release-promote.yml") or {}
    cond = str(((rp.get("jobs") or {}).get("promote") or {}).get("if", ""))
    for p in SELF_PROMOTING:
        for pre in ("release/auto/%s-" % p, "release/auto/rollback-%s-" % p):
            if "!startsWith(github.event.workflow_run.head_branch, '%s')" % pre not in cond:
                errs.append("A7 Release to production must leave %s* to its own publisher" % pre)
    # A9 founder approval before every website release (Stage 1, founder decision 20 Nov 2026)
    jobs = rp.get("jobs") or {}
    ap, pv, pr = jobs.get("approval") or {}, jobs.get("preview") or {}, jobs.get("promote") or {}
    aenv = ap.get("environment")
    if (aenv.get("name") if isinstance(aenv, dict) else aenv) != "website-production":
        errs.append("A9 Release to production must hold every release in an approval job on the website-production environment")
    if "preview" not in (ap.get("needs") if isinstance(ap.get("needs"), list) else [ap.get("needs")]) or ap.get("permissions") != {} or "secrets." in json.dumps(ap):
        errs.append("A9 the approval job must follow the preview, with no permissions and no secrets")
    if pv.get("environment") or (pv.get("permissions") or {}) != {"contents": "read"} or "release-preview.sh" not in json.dumps(pv.get("steps") or []):
        errs.append("A9 the preview job must be read-only (contents: read, no environment) and run release-preview.sh")
    needs = pr.get("needs") if isinstance(pr.get("needs"), list) else [pr.get("needs")]
    if "approval" not in needs or "needs.approval.result == 'success'" not in cond or "needs.preview.outputs.release == 'true'" not in cond:
        errs.append("A9 the promote job must need the approval job and run only after it succeeded")
    st = pr.get("steps") or []
    vi = [i for i, s in enumerate(st) if "verify-founder-approval.sh" in str(s.get("run", ""))]
    ai = [i for i, s in enumerate(st) if s.get("id") == "app"]
    if len(vi) != 1 or not ai or vi[0] > ai[0]:
        errs.append("A9 the promote job must verify the founder's approval (verify-founder-approval.sh) before the App token is created")
    for jn, jj in (("approval", ap), ("promote", pr)):
        if re.search(r"\b(?:always|failure|cancelled)\s*\(", str(jj.get("if", ""))):
            errs.append("A9 the %s job's condition must not use always(), failure() or cancelled(): it must never run after a failed, skipped or rejected step" % jn)
    if ap.get("concurrency") or pv.get("concurrency"):
        errs.append("A9 the preview and approval jobs must not take a concurrency lock (a waiting release must never block publishing)")
    if (rp.get("concurrency") or {}).get("group") == "production-site" or (pr.get("concurrency") or {}).get("group") != "production-site":
        errs.append("A9 the production-site lock must be taken by the promote job only, never while a release waits for approval")
    for name, w in workflows.items():
        envs = [((j or {}).get("environment") or {}) for j in ((w or {}).get("jobs") or {}).values()]
        if name != "release-promote.yml" and any(str(e.get("name") if isinstance(e, dict) else e).strip().lower() == "website-production" for e in envs):
            errs.append("A9 %s must not use the website-production environment (founder approval is for website releases only)" % name)
    # A10 the routine Atlas refresh exception (founder policy, 20 Nov 2026) is restricted to exactly that operation
    pa = jobs.get("promote-atlas") or {}
    pacond = str(pa.get("if", ""))
    pneeds = pa.get("needs") if isinstance(pa.get("needs"), list) else [pa.get("needs")]
    for need_txt in ("startsWith(github.event.workflow_run.head_branch, 'release/auto/atlas-stats-')",
                     "github.event.workflow_run.actor.login == 'plotnua-release[bot]'", "github.event.workflow_run.event == 'push'",
                     "needs.preview.outputs.atlas == 'true'", "needs.preview.outputs.release != 'true'"):
        if need_txt not in pacond:
            errs.append("A10 promote-atlas must require %s" % need_txt)
    if pneeds != ["preview"] or re.search(r"\b(?:always|failure|cancelled)\s*\(", pacond) or (pa.get("concurrency") or {}).get("group") != "production-site":
        errs.append("A10 promote-atlas must need only the preview, use no status function and take the production-site lock")
    pst = pa.get("steps") or []
    vi = [i for i, s in enumerate(pst) if "verify-atlas-refresh.sh" in str(s.get("run", ""))]
    ai = [i for i, s in enumerate(pst) if s.get("id") == "app"]
    if len(vi) != 1 or not ai or vi[0] > ai[0]:
        errs.append("A10 promote-atlas must re-check verify-atlas-refresh.sh before the App token is created")
    if any("verify-atlas-refresh" in str(s.get("run", "")) for s in (pr.get("steps") or [])):
        errs.append("A10 the ordinary promote job must never accept an Atlas check in place of the founder's approval")
    if set(jobs) != {"preview", "approval", "promote", "promote-atlas"}:
        errs.append("A10 Release to production must have exactly the jobs preview, approval, promote and promote-atlas")
    # A8 the key only in the releasing jobs
    allowed = set(RELEASING)
    for path, t in texts.items():
        if "RELEASE_APP_KEY" in t and os.path.basename(path) not in allowed:
            errs.append("A8 %s references the release App key" % os.path.relpath(path, ROOT))
    return errs


def gather():
    texts = {p: open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(WF, "*.yml"))}
    workflows = {os.path.basename(p): yaml.safe_load(t) for p, t in texts.items()}
    tools = {p: open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(REL, "*.sh"))}
    return workflows, texts, tools


def self_test():
    base = gather(); fails = 0
    if check(*base):
        print("  FAIL  control: the unmodified repository passes"); return 1
    print("  PASS  control: the unmodified repository passes")
    def case(label, mutate, code):
        nonlocal fails
        w, t, tl = copy.deepcopy(base); mutate(w, t, tl)
        errs = check(w, t, tl); hit = any(e.startswith(code) for e in errs)
        print("  %s  %s -> %s" % ("PASS" if hit else "FAIL", label, "refused (%s)" % code if hit else "NOT refused"))
        fails += 0 if hit else 1
    rel = lambda n: os.path.join(REL, n)
    case("environment removed from a publisher", lambda w,t,tl: w["plotart-content-publish.yml"]["jobs"]["publish"].pop("environment"), "A1")
    case("deployment record re-enabled", lambda w,t,tl: w["atlas-stats.yml"]["jobs"]["refresh"]["environment"].__setitem__("deployment", True), "A1")
    case("token action unpinned", lambda w,t,tl: next(s for s in w["release-promote.yml"]["jobs"]["promote"]["steps"] if s.get("id")=="app").__setitem__("uses","actions/create-github-app-token@v3"), "A2")
    case("token given extra permission", lambda w,t,tl: next(s for s in w["plotnua-ideas-publish.yml"]["jobs"]["publish"]["steps"] if s.get("id")=="app")["with"].__setitem__("permission-workflows","write"), "A2")
    case("token not passed to the releasing step", lambda w,t,tl: next(s for s in w["plotnua-garden-publish.yml"]["jobs"]["promote"]["steps"] if s.get("name","").startswith("Wait for the gate"))["env"].pop("RELEASE_PUSH_TOKEN"), "A3")
    case("actions: write restored", lambda w,t,tl: w["atlas-match-universe-refresh.yml"]["permissions"].__setitem__("actions","write"), "A4")
    case("gate dispatched again", lambda w,t,tl: tl.__setitem__(rel("request-release.sh"), tl[rel("request-release.sh")]+'\ngh workflow run image-rights-gate.yml --ref "$BR"\n'), "A5")
    case("push helper loses its Actions refusal", lambda w,t,tl: tl.__setitem__(rel("push-release-branch.sh"), tl[rel("push-release-branch.sh")].replace("REFUSED: no RELEASE_PUSH_TOKEN","pushing anyway")), "A6")
    case("push helper forces", lambda w,t,tl: tl.__setitem__(rel("push-release-branch.sh"), tl[rel("push-release-branch.sh")]+'\ngit push -f origin x\n'), "A6")
    case("promote.sh pushes rollbacks directly again", lambda w,t,tl: tl.__setitem__(rel("promote.sh"), tl[rel("promote.sh")].replace("push-release-branch.sh","")), "A6")
    sw = lambda a, b: (lambda w,t,tl: tl.__setitem__(rel("promote.sh"), tl[rel("promote.sh")].replace(a, b)))
    case("promote.sh pushes main without the App token in Actions", sw('[ -z "${RELEASE_PUSH_TOKEN:-}" ]', '[ -z "${NOT_SET:-x}" ]'), "A11")
    case("promote.sh pushes main and its tag separately again", sw("push -q --atomic", "push -q"), "A11")
    case("promote.sh pushes main with the built-in token again", lambda w,t,tl: tl.__setitem__(rel("promote.sh"), tl[rel("promote.sh")].replace('T="prod/', 'git push origin "$SHA:refs/heads/main"\nT="prod/')), "A11")
    case("promote.sh stops clearing the built-in token", sw('-c http.https://github.com/.extraheader= -c', '-c'), "A11")
    case("promote.sh stops redacting the token", sw('out="${out//"$RELEASE_PUSH_TOKEN"/***}"; ', ''), "A11")
    case("Release to production races PlotArt", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("if", w["release-promote.yml"]["jobs"]["promote"]["if"].replace("!startsWith(github.event.workflow_run.head_branch, 'release/auto/plotart-') &&","")), "A7")
    case("approval job removed", lambda w,t,tl: w["release-promote.yml"]["jobs"].pop("approval"), "A9")
    case("approval environment renamed", lambda w,t,tl: w["release-promote.yml"]["jobs"]["approval"].__setitem__("environment", "release-automation"), "A9")
    case("promote no longer waits for the approval", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("needs", ["preview"]), "A9")
    case("promote runs even if the approval failed", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("if", w["release-promote.yml"]["jobs"]["promote"]["if"].replace("needs.approval.result == 'success'", "always()")), "A9")
    case("approval check dropped from promote", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("steps", [s for s in w["release-promote.yml"]["jobs"]["promote"]["steps"] if "verify-founder-approval" not in str(s.get("run",""))]), "A9")
    case("approval job given a secret", lambda w,t,tl: w["release-promote.yml"]["jobs"]["approval"]["steps"][0].__setitem__("env", {"K": "${{ secrets.RELEASE_APP_KEY }}"}), "A9")
    case("whole run holds the production-site lock again", lambda w,t,tl: w["release-promote.yml"].__setitem__("concurrency", {"group": "production-site", "cancel-in-progress": False}), "A9")
    case("promote made to run always()", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("if", "always() && " + w["release-promote.yml"]["jobs"]["promote"]["if"]), "A9")
    case("the waiting approval made to hold the production-site lock", lambda w,t,tl: w["release-promote.yml"]["jobs"]["approval"].__setitem__("concurrency", {"group": "production-site"}), "A9")
    case("a publisher made to wait for website approval", lambda w,t,tl: w["plotnua-garden-publish.yml"]["jobs"]["promote"].__setitem__("environment", "website-production"), "A9")
    case("Atlas exception widened to any branch", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote-atlas"].__setitem__("if", w["release-promote.yml"]["jobs"]["promote-atlas"]["if"].replace("'release/auto/atlas-stats-'", "'release/auto/'")), "A10")
    case("Atlas exception no longer requires the App", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote-atlas"].__setitem__("if", w["release-promote.yml"]["jobs"]["promote-atlas"]["if"].replace("github.event.workflow_run.actor.login == 'plotnua-release[bot]'", "true")), "A10")
    case("Atlas re-check dropped", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote-atlas"].__setitem__("steps", [s for s in w["release-promote.yml"]["jobs"]["promote-atlas"]["steps"] if "verify-atlas" not in str(s.get("run",""))]), "A10")
    case("Atlas job made to run always()", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote-atlas"].__setitem__("if", "always() && " + w["release-promote.yml"]["jobs"]["promote-atlas"]["if"]), "A10")
    case("a third unapproved release job added", lambda w,t,tl: w["release-promote.yml"]["jobs"].__setitem__("promote-fast", {"runs-on": "ubuntu-latest", "steps": []}), "A10")
    case("key referenced by another workflow", lambda w,t,tl: t.__setitem__(os.path.join(WF,"site-health.yml"), t.get(os.path.join(WF,"site-health.yml"),"")+"\n# ${{ secrets.RELEASE_APP_KEY }}\n"), "A8")
    print("\nRELEASE APP PUSH SELF-TEST · %s · %d failed" % ("OK" if fails == 0 else "FAIL", fails))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    errs = check(*gather())
    for e in errs:
        print("  REFUSED  " + e)
    print("RELEASE APP PUSH · %s" % ("OK (A1-A11: %d releasing workflows)" % len(RELEASING) if not errs else "REFUSED · %d problem(s)" % len(errs)))
    sys.exit(1 if errs else 0)
