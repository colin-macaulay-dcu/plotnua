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

  python3 atlas-tools/release/prove-release-app-push.py [--self-test]
"""
import glob, os, re, sys, copy
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WF = os.path.join(ROOT, ".github", "workflows")
REL = os.path.join(ROOT, "atlas-tools", "release")
PIN = "actions/create-github-app-token@64ab729a6294000f5aa4a4bc0b73d1f32bc45510"
# workflow -> {job: [steps that push release/auto/ branches]}
RELEASING = {
    "release-promote.yml": {"promote": ["Promote, verify live, roll back automatically if the live check fails",
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
    # A7 Release to production leaves self-promoting publishers alone
    rp = workflows.get("release-promote.yml") or {}
    cond = str(((rp.get("jobs") or {}).get("promote") or {}).get("if", ""))
    for p in SELF_PROMOTING:
        for pre in ("release/auto/%s-" % p, "release/auto/rollback-%s-" % p):
            if "!startsWith(github.event.workflow_run.head_branch, '%s')" % pre not in cond:
                errs.append("A7 Release to production must leave %s* to its own publisher" % pre)
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
    case("Release to production races PlotArt", lambda w,t,tl: w["release-promote.yml"]["jobs"]["promote"].__setitem__("if", w["release-promote.yml"]["jobs"]["promote"]["if"].replace("!startsWith(github.event.workflow_run.head_branch, 'release/auto/plotart-') &&","")), "A7")
    case("key referenced by another workflow", lambda w,t,tl: t.__setitem__(os.path.join(WF,"site-health.yml"), t.get(os.path.join(WF,"site-health.yml"),"")+"\n# ${{ secrets.RELEASE_APP_KEY }}\n"), "A8")
    print("\nRELEASE APP PUSH SELF-TEST · %s · %d failed" % ("OK" if fails == 0 else "FAIL", fails))
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    errs = check(*gather())
    for e in errs:
        print("  REFUSED  " + e)
    print("RELEASE APP PUSH · %s" % ("OK (A1-A8: %d releasing workflows)" % len(RELEASING) if not errs else "REFUSED · %d problem(s)" % len(errs)))
    sys.exit(1 if errs else 0)
