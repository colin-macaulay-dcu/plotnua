#!/usr/bin/env python3
"""Proof: in "Release to production", the promote job can only run after the founder approved (Stage 1, 20 Nov 2026).

Reads the REAL job conditions from .github/workflows/release-promote.yml and evaluates them with GitHub's documented
rules for every combination of:
  - the triggering gate run (conclusion, event, branch: ordinary, publisher, rollback, main, feature);
  - the preview job (succeeded and offered the release / found nothing to release / failed / cancelled);
  - the approval job (approved / rejected / approval expired after 30 days / cancelled / never run).
GitHub's rules modelled here (GitHub Actions documentation, "Using conditions to control job execution" and
"Defining prerequisite jobs"): a job whose `if` has no status function gets an implicit success(), which is true only
when every job in its `needs` succeeded; a job whose prerequisite is skipped, failed or cancelled is skipped; a
rejected or expired environment approval fails the job; a job that never runs has the result "skipped".
Then plants faults (always(), a dropped dependency, a dropped result check) and requires each to be caught.
Never touches GitHub.        python3 atlas-tools/release/prove-approval-jobs.py [.github/workflows/release-promote.yml]
"""
import copy, itertools, os, re, sys
import yaml

WF = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", ".github", "workflows", "release-promote.yml")
STATUS_FUNCS = ("success", "failure", "always", "cancelled")


# ---- a small evaluator for the GitHub expression syntax these conditions use ----
TOK = re.compile(r"\s*(?:(\|\||&&|==|!=|!|\(|\)|,)|'((?:[^']|'')*)'|([A-Za-z_][A-Za-z0-9_\-]*(?:\.[A-Za-z_][A-Za-z0-9_\-]*)*)|(\d+))")


def tokens(s):
    s = s.strip()
    if s.startswith("${{") and s.endswith("}}"):
        s = s[3:-2]
    out, i = [], 0
    while i < len(s):
        m = TOK.match(s, i)
        if not m or m.end() == i:
            if s[i:].strip() == "":
                break
            raise ValueError("cannot read expression at: %r" % s[i:i + 30])
        op, st, ident, num = m.groups()
        out.append(("op", op) if op else ("str", st.replace("''", "'")) if st is not None else ("id", ident) if ident else ("num", num))
        i = m.end()
    return out


class Ev:
    def __init__(self, toks, ctx, needs_results):
        self.t, self.i, self.ctx, self.nr = toks, 0, ctx, needs_results

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, v=None):
        k = self.peek()
        if v is not None and k[1] != v:
            raise ValueError("expected %s, got %s" % (v, k))
        self.i += 1
        return k

    def run(self):
        v = self.orx()
        if self.i != len(self.t):
            raise ValueError("trailing tokens %s" % self.t[self.i:])
        return v

    def orx(self):
        v = self.andx()
        while self.peek() == ("op", "||"):
            self.take(); r = self.andx(); v = v or r
        return v

    def andx(self):
        v = self.cmp()
        while self.peek() == ("op", "&&"):
            self.take(); r = self.cmp(); v = v and r
        return v

    def cmp(self):
        v = self.unary()
        while self.peek() in (("op", "=="), ("op", "!=")):
            op = self.take()[1]; r = self.unary()
            v = (v == r) if op == "==" else (v != r)
        return v

    def unary(self):
        if self.peek() == ("op", "!"):
            self.take(); return not self.unary()
        return self.prim()

    def prim(self):
        k, v = self.take()
        if k == "op" and v == "(":
            r = self.orx(); self.take(")"); return r
        if k == "str":
            return v
        if k == "num":
            return int(v)
        if k == "id":
            if self.peek() == ("op", "("):
                self.take("("); args = []
                while self.peek() != ("op", ")"):
                    args.append(self.orx())
                    if self.peek() == ("op", ","):
                        self.take(",")
                self.take(")")
                return self.call(v, args)
            if v in ("true", "false"):
                return v == "true"
            cur = self.ctx
            for part in v.split("."):
                cur = cur.get(part) if isinstance(cur, dict) else None
            return "" if cur is None else cur
        raise ValueError("unexpected %s" % ((k, v),))

    def call(self, name, args):
        if name == "startsWith":
            return str(args[0]).lower().startswith(str(args[1]).lower())
        if name == "success":
            return all(r == "success" for r in self.nr)
        if name == "failure":
            return any(r == "failure" for r in self.nr)
        if name == "cancelled":
            return any(r == "cancelled" for r in self.nr)
        if name == "always":
            return True
        raise ValueError("unsupported function %s" % name)


def should_run(job, ctx, results):
    needs = job.get("needs") or []
    needs = [needs] if isinstance(needs, str) else needs
    nr = [results[n] for n in needs]
    cond = job.get("if")
    if cond is None:
        return all(r == "success" for r in nr)
    cond = str(cond)
    if not any(re.search(r"\b%s\s*\(" % f, cond) for f in STATUS_FUNCS):   # implicit success() &&
        if not all(r == "success" for r in nr):
            return False
    return bool(Ev(tokens(cond), ctx, nr).run())


BRANCHES = ["release/auto/artist-submissions-abc1234", "release/auto/atlas-stats-abc1234", "release/auto/rollback-artist-submissions-abc1234",
            "release/auto/plotart-gallery-abc1234", "release/auto/garden-abc1234", "release/auto/ideas-abc1234",
            "release/auto/rollback-plotart-x", "release/auto/rollback-garden-x", "release/auto/rollback-ideas-x", "main", "feature/x", "release/manual-x"]
PREVIEW = {"offered": ("success", "true", ""), "nothing": ("success", "false", ""), "atlas": ("success", "false", "true"),
           "failed": ("failure", "", ""), "cancelled": ("cancelled", "", "")}
ACTORS = ["plotnua-release[bot]", "colin-macaulay-dcu", "github-actions[bot]"]
APPROVAL = {"approved": "success", "rejected": "failure", "expired": "failure", "cancelled": "cancelled"}


def simulate(wf):
    jobs = wf["jobs"]
    problems, n = [], 0
    for concl, event, br, pv, ap, actor in itertools.product(["success", "failure", "cancelled"], ["push", "workflow_dispatch", "pull_request"],
                                                              BRANCHES, PREVIEW, APPROVAL, ACTORS):
        n += 1
        ctx = {"github": {"event": {"workflow_run": {"conclusion": concl, "event": event, "head_branch": br, "head_sha": "a" * 40,
                                                     "actor": {"login": actor}}}}}
        results, outputs = {}, {}
        for name in ("preview", "approval", "promote", "promote-atlas"):
            j = jobs[name]
            c = copy.deepcopy(ctx); c["needs"] = {k: {"result": results[k], "outputs": outputs.get(k, {})} for k in results}
            if not should_run(j, c, results):
                results[name] = "skipped"; continue
            if name == "preview":
                results[name], rel, atl = PREVIEW[pv]; outputs[name] = {"release": rel, "atlas": atl}
            elif name == "approval":
                if (j.get("environment") or {}).get("name") != "website-production":
                    results[name] = "success"   # an unprotected job would simply run
                else:
                    results[name] = APPROVAL[ap]
            else:
                results[name] = "ran"
        eligible = (concl == "success" and event in ("push", "workflow_dispatch") and br.startswith("release/auto/")
                    and not re.match(r"release/auto/(rollback-)?(plotart|garden|ideas)-", br))
        expect_promote = eligible and pv == "offered" and ap == "approved"
        expect_approval_asked = eligible and pv == "offered"
        expect_atlas = (eligible and pv == "atlas" and br.startswith("release/auto/atlas-stats-") and actor == "plotnua-release[bot]"
                        and event == "push")
        if (results["promote-atlas"] == "ran") != expect_atlas:
            problems.append("promote-atlas %s for %s/%s/%s/%s preview=%s" % ("RAN" if results["promote-atlas"] == "ran" else "did not run", concl, event, br, actor, pv))
        if (results["promote"] == "ran") != expect_promote:
            problems.append("promote %s for %s/%s/%s preview=%s approval=%s" % ("RAN" if results["promote"] == "ran" else "did not run", concl, event, br, pv, ap))
        if (results["approval"] != "skipped") != expect_approval_asked:
            problems.append("approval %s for %s/%s/%s preview=%s" % ("asked" if results["approval"] != "skipped" else "not asked", concl, event, br, pv))
    return n, problems


def main():
    wf = yaml.safe_load(open(WF, encoding="utf-8"))
    n, problems = simulate(wf)
    for p in problems[:20]:
        print("  FAIL  " + p)
    print("  %s  %d combinations: promote runs only after the founder approved an offered release; promote-atlas only for an App-pushed atlas-stats refresh the preview classified as routine" % ("PASS" if not problems else "FAIL", n))
    fails = 1 if problems else 0
    # planted faults: each must let promote run without approval somewhere, and be caught
    def fault(label, mutate):
        nonlocal fails
        w = copy.deepcopy(wf); mutate(w["jobs"])
        _, pr = simulate(w)
        caught = any(p.startswith("promote RAN") or p.startswith("promote-atlas RAN") for p in pr)
        print("  %s  planted fault caught: %s" % ("PASS" if caught else "FAIL", label))
        fails += 0 if caught else 1
    base_if = wf["jobs"]["promote"]["if"]
    fault("promote condition starts with always()", lambda j: j["promote"].__setitem__("if", "always() && " + base_if.replace("needs.approval.result == 'success'", "true")))
    fault("promote no longer needs the approval job", lambda j: (j["promote"].__setitem__("needs", ["preview"]), j["promote"].__setitem__("if", base_if.replace("&& needs.approval.result == 'success'", ""))))
    fault("approval job's environment removed (it would run unprotected)", lambda j: j["approval"].pop("environment"))
    fault("promote runs whatever the approval result (always() + result check removed)", lambda j: j["promote"].__setitem__("if", "always() && needs.preview.outputs.release == 'true'"))
    fault("promote runs on failure() of the approval", lambda j: j["promote"].__setitem__("if", "failure() || " + base_if))
    atl_if = wf["jobs"]["promote-atlas"]["if"]
    fault("Atlas release job accepts any release branch", lambda j: j["promote-atlas"].__setitem__("if", atl_if.replace("startsWith(github.event.workflow_run.head_branch, 'release/auto/atlas-stats-') &&", "")))
    fault("Atlas release job accepts any pusher", lambda j: j["promote-atlas"].__setitem__("if", atl_if.replace("github.event.workflow_run.actor.login == 'plotnua-release[bot]' &&", "")))
    fault("Atlas release job runs for an ordinary offered release", lambda j: j["promote-atlas"].__setitem__("if", atl_if.replace("needs.preview.outputs.atlas == 'true' && needs.preview.outputs.release != 'true'", "needs.preview.outputs.release == 'true'")))
    print("APPROVAL JOBS PROOF · %s · %d failed" % ("OK" if fails == 0 else "FAIL", fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
