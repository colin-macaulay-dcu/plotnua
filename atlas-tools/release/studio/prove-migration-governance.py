#!/usr/bin/env python3
"""PlotArt Studio · migration governance proof for migration 0005 (development, 6 Nov 2026). Runs locally; touches nothing.
Shows that the refusal-only trigger exception in migration-check.py cannot be used to change data or existing tables, that
the earlier safeguards still hold, and that the workflow still sends 0005 to the founder's approval with both backups
taken before anything is applied and no automatic restore.
  python3 atlas-tools/release/studio/prove-migration-governance.py
"""
import hashlib, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHECK = os.path.join(HERE, "migration-check.py")
MIG = os.path.join(ROOT, "worker", "plotart-studio", "migrations", "0005_agreements_and_enquiry_log.sql")
WF = os.path.join(ROOT, ".github", "workflows", "studio-d1-migration.yml")
TABLES = "agreement_documents,agreement_acceptances,enquiry_log,record_retention,acceptance_corrections,participation_events"
DESC = "Creates six new tables guarded by refusal-only triggers; carries over existing licence acceptances and relay enquiry references."
results = []
def check(name, ok, detail=""):
    results.append(bool(ok)); print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok or not detail else "  [%s]" % str(detail)[:300]))
def run_check(path, tables=TABLES, desc=DESC, sha=None):
    sha = sha or hashlib.sha256(open(path, "rb").read()).hexdigest()
    r = subprocess.run([sys.executable, CHECK, path, sha, tables, desc], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr
src = open(MIG, encoding="utf-8").read()
tmp = tempfile.mkdtemp(prefix="mig-gov-")
def variant(text):
    p = os.path.join(tmp, "0005_agreements_and_enquiry_log.sql")   # same number: the checker reads it to find existing tables
    open(p, "w", encoding="utf-8").write(text); return p

print("PROVE · migration governance (0005)")
rc, out = run_check(MIG)
n_trig = len(re.findall(r"\bCREATE\s+TRIGGER\b", re.sub(r"--[^\n]*", " ", src), re.I))
n_guard = len(re.findall(r"\(refuses (INSERT|UPDATE|DELETE) on ", out))
check("G1 migration 0005 passes the check with its six new tables declared", rc == 0 and "MIGRATION CHECK OK" in out, out[-300:])
check("G2 it is classed DESTRUCTIVE (it inserts rows), so it can never run without the founder's approval", "MIGRATION CLASS: destructive" in out)
check("G3 every one of its %d triggers is a refusal-only guard on a table it creates (none slips through as anything else)" % n_trig, n_trig == n_guard == 15, (n_trig, n_guard))
guarded = set(re.findall(r"refuses (?:INSERT|UPDATE|DELETE) on ([a-z_]+)", out))
check("G4 the guarded tables are exactly the six new ones; no existing table is guarded", guarded == set(TABLES.split(",")), guarded)

rcg, og = run_check(variant("CREATE TABLE widgets (id TEXT);\nCREATE TRIGGER w_no_update BEFORE UPDATE ON widgets BEGIN SELECT RAISE(ABORT, 'x'); END;\n"), tables="widgets", desc="Only a new table and one refusal-only guard.")
check("G5 a migration with nothing but a new table and a refusal-only guard is still classed as needing the founder's approval (never automatic)", rcg == 0 and "MIGRATION CLASS: destructive" in og, og[-200:])
print("— the exception cannot be used for anything else (each variant of the real file must be REFUSED)")
tamper = {
  "an extra trigger that deletes from an existing table": src + "\nCREATE TRIGGER x AFTER INSERT ON agreement_documents BEGIN DELETE FROM artists; END;\n",
  "a guard turned into a writing trigger": src.replace("BEGIN SELECT RAISE(ABORT, 'enquiry_log is append-only; add a correcting row'); END;", "BEGIN UPDATE artists SET email = ''; END;", 1),
  "a guard with a second statement": src.replace("BEGIN SELECT RAISE(ABORT, 'agreement_documents rows are never removed'); END;", "BEGIN SELECT RAISE(ABORT, 'x'); DELETE FROM audit; END;", 1),
  "a refusal-only guard on the existing artists table": src + "\nCREATE TRIGGER a_lock BEFORE UPDATE ON artists BEGIN SELECT RAISE(ABORT, 'locked'); END;\n",
  "a guard on an existing table re-created with IF NOT EXISTS": src + "\nCREATE TABLE IF NOT EXISTS enquiries (id TEXT);\nCREATE TRIGGER e_lock BEFORE DELETE ON enquiries BEGIN SELECT RAISE(ABORT, 'x'); END;\n",
  "RAISE(IGNORE), which would silently drop writes": src.replace("BEGIN SELECT RAISE(ABORT, 'participation_events is append-only'); END;", "BEGIN SELECT RAISE(IGNORE); END;", 1),
  "a WHEN condition that writes": src.replace("WHEN NEW.kind = 'ended'", "WHEN (DELETE FROM artists) IS NULL AND NEW.kind = 'ended'", 1),
  "an UPDATE of the artists table added": src + "\nUPDATE artists SET licence_version = 'PA-GPIL-2026-11';\n",
}
for why, text in tamper.items():
    rc2, o2 = run_check(variant(text))
    check("T  %s" % why, rc2 != 0 and "REFUSED" in o2, o2[-200:])
rc3, o3 = run_check(MIG, tables="agreement_documents,agreement_acceptances,enquiry_log,record_retention,acceptance_corrections")
check("T  one table left out of the declaration", rc3 != 0 and "REFUSED" in o3)
rc4, o4 = run_check(MIG, sha="0" * 64)
check("T  a file that is not the approved one (SHA-256)", rc4 != 0 and "not the approved one" in o4)
rc5, o5 = run_check(MIG, desc="short")
check("T  no description of the expected changes", rc5 != 0 and "REFUSED" in o5)

print("— earlier safeguards and migrations unchanged")
# the checker as it is on main today, run from this same folder (it finds the Studio files relative to itself), then removed
mainck = os.path.join(HERE, "_migration-check-main-tmp.py")
open(mainck, "w").write(subprocess.run(["git", "-C", ROOT, "show", "origin/main:atlas-tools/release/studio/migration-check.py"], capture_output=True, text=True).stdout)
cls = lambda o: "additive" if "MIGRATION CLASS: additive" in o else "destructive" if "MIGRATION CLASS: destructive" in o else "refused"
try:
    for f, tables in [("0002_gallery_order.sql", "artists,gallery_positions"), ("0003_ideas.sql", "ideas,idea_intake_days"),
                      ("0004_garden_board.sql", "garden_listings,garden_intake_days,garden_enquiries,garden_enquiry_days")]:
        path = os.path.join(ROOT, "worker", "plotart-studio", "migrations", f)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        rc6, o6 = run_check(path, tables=tables, desc="Regression check of an earlier migration.")
        mm = subprocess.run([sys.executable, mainck, path, sha, tables, "Regression check of an earlier migration."], capture_output=True, text=True)
        check("E  %s: same result as main's checker (%s)" % (f, cls(mm.stdout)), rc6 == 0 and cls(o6) == cls(mm.stdout) != "refused", (cls(o6), mm.stdout[-150:]))
    mm = subprocess.run([sys.executable, mainck, MIG, hashlib.sha256(open(MIG, "rb").read()).hexdigest(), TABLES, DESC], capture_output=True, text=True)
    # the checker change reached main with Stage D (6 Nov 2026): main's checker now gives the approved result for 0005
    check("E  main's checker accepts 0005 as destructive (the checker change reached main at Stage D)", "MIGRATION CHECK OK" in mm.stdout and "MIGRATION CLASS: destructive" in mm.stdout, mm.stdout[-150:])
finally:
    os.remove(mainck)
cl = subprocess.run([sys.executable, os.path.join(HERE, "prove-migration-classifier.py")], capture_output=True, text=True)
check("E  the classifier proof (every earlier case plus the new trigger cases) still passes", cl.returncode == 0 and "OK" in cl.stdout.splitlines()[-1], cl.stdout[-200:])

print("— the workflow still requires the founder's approval and both backups")
wf = open(WF, encoding="utf-8").read()
cls = re.search(r'if grep -q "\^MIGRATION CLASS: additive" "\$RUNNER_TEMP/check.txt"; then E=studio-database-auto; else E=studio-database; fi', wf)
check("W1 anything not additive runs in environment studio-database (waits for the founder to press Approve)", bool(cls))
check("W2 after approval the check runs again, and studio-database-auto refuses anything not additive", "Check again after approval" in wf and 'grep -q "^MIGRATION CLASS: additive" "$RUNNER_TEMP/c2.txt" || { echo "REFUSED: not additive"' in wf)
steps = [m.group(1) for m in re.finditer(r"- name: (.+)", wf)]
idx = lambda s: next((i for i, x in enumerate(steps) if x.startswith(s)), -1)
order = [idx("Check again after approval"), idx("Backup 1 of 2"), idx("Backup 2 of 2"), idx("Keep the encrypted backup"), idx("Database fingerprint before"), idx("Apply the migration"), idx("Only the declared tables changed"), idx("If anything failed after the backups")]
check("W3 order: re-check → Time Travel restore point → encrypted full export → kept as artifact → fingerprint → apply → only declared tables changed → failure notice", -1 not in order and order == sorted(order), list(zip(order, steps)))
fail = wf[wf.index("- name: If anything failed after the backups"):]
check("W4 a failure is never restored automatically (restore needs the founder's separate approval)", "NOT RESTORED AUTOMATICALLY" in fail and "d1 execute" not in fail and "time-travel restore" not in fail)

print("— the gallery order is protected (founder decision 6 Nov 2026: Leah Hewson holds position 01)")
check("W5 the migration workflow records the complete gallery order before applying and verifies it after (d1-snapshot save → apply → compare)",
      'd1-snapshot.mjs "$CONFIG" save "$RUNNER_TEMP/db-before"' in wf and 'd1-snapshot.mjs "$CONFIG" compare "$RUNNER_TEMP/db-before" "$TABLES"' in wf)
dep = open(os.path.join(ROOT, ".github", "workflows", "studio-deploy.yml"), encoding="utf-8").read()
check("W6 the Studio deploy workflow records the order before deploying and verifies it after (order-check save → deploy → compare, automatic rollback on failure)",
      'order-check.mjs save "$RUNNER_TEMP/order-before"' in dep and 'order-check.mjs compare "$RUNNER_TEMP/order-before"' in dep and "Automatic rollback to the previous version" in dep)
for f in ("d1-snapshot.mjs", "order-check.mjs"):
    t = open(os.path.join(HERE, f), encoding="utf-8").read()
    check("W7 %s holds position 01 for the approved artist and no longer requires 01 to be empty" % f,
          "const POSITION_01 = 'leah-hewson'" in t and "reserved01" not in t)
go = subprocess.run(["node", os.path.join(HERE, "prove-gallery-order-safeguards.mjs")], capture_output=True, text=True)
check("W8 the gallery-order safeguard proof passes (occupied 01 accepted; any move, release, reassignment or artist-record change stops)",
      go.returncode == 0 and "GALLERY ORDER SAFEGUARDS · OK" in go.stdout, go.stdout[-300:])
shutil.rmtree(tmp)
print("\nMIGRATION GOVERNANCE · %d checks, %d passed, %d failed" % (len(results), sum(results), len(results) - sum(results)))
sys.exit(0 if all(results) else 1)
