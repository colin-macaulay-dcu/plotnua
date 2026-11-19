#!/usr/bin/env python3
"""Offline tests for the d1_setup gate and verification (PR #23 review). Touches no real resource.

A local mock of the Cloudflare API serves token verification, the database lookup and the D1 query endpoint from a
throwaway SQLite file standing in for the remote TEST database. The workflow's own d1_setup shell step is also run
end to end, with a fake `npx` that applies each file to that SQLite file (and can be told to fail on one file)."""
import http.server, json, os, re, shutil, sqlite3, subprocess, sys, tempfile, threading

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
GATE = os.path.join(REPO, "atlas-tools", "release", "studio", "checkout-test-d1.py")
WORKER = os.path.join(REPO, "worker", "plotart-studio")
ACC, DB = "a" * 32, "12345678-1234-1234-1234-123456789abc"
TMP = tempfile.mkdtemp(prefix="d1test-")
REMOTE = os.path.join(TMP, "remote.sqlite")
S = {"name": "plotart-checkout-test", "token": "active", "query": "ok"}


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body):
        b = (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.endswith("/tokens/verify"):
            return self.send(200, {"success": True, "result": {"status": S["token"]}}) if S["token"] == "active" else self.send(401, {"success": False, "errors": [{"code": 1000}]})
        if f"/d1/database/{DB}" in self.path:
            return self.send(200, {"success": True, "result": {"uuid": DB, "name": S["name"]}})
        if "/d1/database/" in self.path:
            return self.send(404, {"success": False, "errors": [{"code": 7404}]})
        self.send(404, {})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if not self.path.endswith(f"/d1/database/{DB}/query"): return self.send(404, {})
        if S["query"] == "500": return self.send(500, {"success": False, "errors": [{"code": 7500}]})
        if S["query"] == "malformed": return self.send(200, b"<html>not json")
        if S["query"] == "noresults": return self.send(200, {"success": True, "result": [{"success": True}]})
        if body["sql"].count("UNION ALL") > 10:   # D1 refused a 60-way UNION ALL in the first real run (HTTP 400, 7500)
            return self.send(400, {"success": False, "errors": [{"code": 7500}]})
        c = sqlite3.connect(REMOTE); c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute(body["sql"])]
        c.close()
        self.send(200, {"success": True, "result": [{"success": True, "results": rows}]})


srv = http.server.HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{srv.server_port}/client/v4"
ENV = dict(os.environ, CLOUDFLARE_ACCOUNT_ID=ACC, CHECKOUT_TEST_D1_DATABASE_ID=DB, CHECKOUT_TEST_CF_TOKEN="t" * 40, CHECKOUT_D1_API=API)
ENV.pop("GITHUB_STEP_SUMMARY", None)

SEED = os.path.join(TMP, "seed.sql")
subprocess.run(["node", os.path.join(WORKER, "test", "checkout-test-env-seed.mjs"), "--target", "plotart-checkout-test",
                "--founding", "colin+f1@plotnua.ie", "--gallery", "colin+g1@plotnua.ie"], stdout=open(SEED, "w"), check=True)
FILES = [os.path.join(WORKER, "schema.sql"), os.path.join(WORKER, "migrations", "0013_gallery_artist_agreement_text.sql"), SEED]


def reset(*files):
    if os.path.exists(REMOTE): os.remove(REMOTE)
    c = sqlite3.connect(REMOTE)
    for f in files: c.executescript(open(f).read())
    c.commit(); c.close()


def gate(mode, **env):
    r = subprocess.run([sys.executable, GATE, mode], env={**ENV, **env}, capture_output=True, text=True)
    return r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]


# the workflow's own d1_setup step, run end to end with a fake npx (Wrangler stand-in) applying files to REMOTE
import yaml
STEP = [s for s in yaml.safe_load(open(os.path.join(REPO, ".github/workflows/plotart-checkout-test-setup.yml")))["jobs"]["setup"]["steps"]
        if "gate, apply" in str(s.get("name"))][0]["run"]
BIN = os.path.join(TMP, "bin"); os.makedirs(BIN)
open(os.path.join(BIN, "npx"), "w").write(f"""#!/usr/bin/env python3
import sqlite3, sys, os
a = sys.argv; f = a[a.index('--file') + 1]
fail = os.environ.get('FAKE_FAIL_ON', '')
if fail and os.path.basename(f) == fail:
    print('✘ [ERROR] simulated failure token=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'); sys.exit(1)
c = sqlite3.connect({REMOTE!r}); c.executescript(open(f).read()); c.commit()
""")
os.chmod(os.path.join(BIN, "npx"), 0o755)
SUMF = os.path.join(TMP, "summary.md")


def step(**env):
    ws = os.path.join(TMP, "ws"); rt = os.path.join(TMP, "rt"); shutil.rmtree(ws, True); shutil.rmtree(rt, True); os.makedirs(rt)
    os.makedirs(os.path.join(ws, "atlas-tools", "release", "studio"))
    shutil.copytree(WORKER, os.path.join(ws, "worker", "plotart-studio"), ignore=shutil.ignore_patterns("node_modules", ".wrangler"))
    shutil.copy(GATE, os.path.join(ws, "atlas-tools", "release", "studio"))
    e = {**ENV, "GITHUB_WORKSPACE": ws, "RUNNER_TEMP": rt, "GITHUB_STEP_SUMMARY": SUMF, "PATH": BIN + os.pathsep + os.environ["PATH"], **env}
    r = subprocess.run(["bash", "-c", STEP], env=e, capture_output=True, text=True)
    return r.returncode, r.stdout


results = []
def case(name, ok, detail=""):
    results.append(ok); print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail[:160]}]" if detail else ""))


# (a) wrong database name / malformed IDs / token
reset(); S.update(name="plotart-studio")
rc, line = gate("check"); case("(a) wrong database NAME for the ID → check refuses", rc == 1 and "not plotart-checkout-test" in line, line)
S.update(name="plotart-checkout-test")
rc, line = gate("check", CHECKOUT_TEST_D1_DATABASE_ID="not-a-uuid"); case("(a) malformed database ID → refuses", rc == 1 and "not a UUID" in line, line)
rc, line = gate("check", CHECKOUT_TEST_D1_DATABASE_ID="87654321-4321-4321-4321-cba987654321"); case("(a) unknown database ID (404) → refuses", rc == 1 and "lookup failed" in line, line)
rc, line = gate("check", CLOUDFLARE_ACCOUNT_ID="xyz"); case("(a) malformed account ID → refuses", rc == 1 and "ACCOUNT_ID" in line, line)
S.update(token="inactive"); rc, line = gate("check"); case("token not verified active → refuses", rc == 1 and "not verified active" in line, line); S.update(token="active")
# (b) non-empty database
reset(FILES[0]); rc, line = gate("check"); case("(b) non-empty TEST database → check refuses", rc == 1 and "already has" in line, line)
rc, out = step(); case("(b) workflow step refuses a non-empty database and applies nothing", rc == 1 and "nothing was applied" in out and "applied schema.sql" not in out, out.strip().splitlines()[-1])
# (c) unreadable results
reset()
for mode in ("500", "malformed", "noresults"):
    S.update(query=mode); rc, line = gate("check"); case(f"(c) query answer {mode} → check refuses", rc == 1 and "STOPPED" in line, line)
    reset(*FILES); rc, line = gate("verify", D1_SEED_FILE=SEED); case(f"(c) query answer {mode} → verify refuses", rc == 1 and "STOPPED" in line, line); reset()
S.update(query="ok")
# (d) partial apply
reset(FILES[0], FILES[1]); rc, line = gate("verify", D1_SEED_FILE=SEED); case("(d) schema + 0013 without the seed → verify refuses", rc == 1 and "row counts differ" in line, line)
reset(FILES[0]); rc, line = gate("verify", D1_SEED_FILE=SEED); case("(d) schema only → verify refuses", rc == 1 and "STOPPED" in line, line)
reset(); rc, out = step(FAKE_FAIL_ON="seed.sql")
case("(d) workflow step: seed fails after schema + 0013 → loud PARTIAL SETUP, exit 1", rc == 1 and "PARTIAL SETUP: 2 of 3" in out and "[redacted]" in out and "AAAAAAAA" not in out, out.strip().splitlines()[-1])
reset(); rc, out = step(FAKE_FAIL_ON="schema.sql")
case("(d) workflow step: first file fails → nothing applied, exit 1", rc == 1 and "Nothing was applied before it" in out, out.strip().splitlines()[-1])
# (e) wrong synthetic artists
reset(*FILES); c = sqlite3.connect(REMOTE); c.execute("UPDATE artists SET email = 'someone@example.com' WHERE id = 'atestgal'"); c.commit(); c.close()
rc, line = gate("verify", D1_SEED_FILE=SEED); case("(e) a synthetic artist with the wrong address → verify refuses", rc == 1 and "artists are not exactly" in line, line)
reset(*FILES); c = sqlite3.connect(REMOTE)
c.execute("UPDATE artists SET id = 'arealone' WHERE id = 'atestgal'"); c.commit(); c.close()
rc, line = gate("verify", D1_SEED_FILE=SEED); case("(e) two artists but not the synthetic two → verify refuses", rc == 1 and "artists are not exactly" in line, line)
reset(*FILES); c = sqlite3.connect(REMOTE); c.execute("CREATE TABLE stray (x)"); c.commit(); c.close()
rc, line = gate("verify", D1_SEED_FILE=SEED); case("unexpected extra table → verify refuses", rc == 1 and "unexpected ['stray']" in line, line)
# d1_verify mode (read only) in the workflow
VSTEP = [s for s in yaml.safe_load(open(os.path.join(REPO, ".github/workflows/plotart-checkout-test-setup.yml")))["jobs"]["setup"]["steps"]
         if "verify only" in str(s.get("name"))][0]["run"]
reset(*FILES); r = subprocess.run(["bash", "-c", VSTEP], cwd=REPO, env={**ENV, "RUNNER_TEMP": os.path.join(TMP, "rt2")}, capture_output=True, text=True)
case("d1_verify mode (read only) passes on the exact expected state", r.returncode == 0 and "matches the expected state exactly" in r.stdout, r.stdout.strip()[-160:])
# (f) success
reset(); rc, line = gate("check"); case("(f) empty TEST database → check passes", rc == 0 and "EMPTY" in line, line)
reset(*FILES); rc, line = gate("verify", D1_SEED_FILE=SEED); case("(f) exact expected state → verify passes", rc == 0 and "matches the expected state exactly" in line, line)
reset(); rc, out = step(); case("(f) workflow step end to end: gate, 3 files, exact verification", rc == 0 and out.count("PASS  applied") == 3 and "matches the expected state exactly" in out, out.strip().splitlines()[-1])
# d1_legacy_licence (19 Nov 2026): the synthetic artists' migration-0005 licence row, on an existing TEST database
LEGACY_SQL = os.path.join(WORKER, "test", "checkout-test-legacy-licence.sql")
OLDSEED = os.path.join(TMP, "oldseed.sql")   # the seed as first applied on 19 Nov (without the migrated rows)
open(OLDSEED, "w").write(open(SEED).read().replace(open(LEGACY_SQL).read().strip(), ""))
LSTEP = [s for s in yaml.safe_load(open(os.path.join(REPO, ".github/workflows/plotart-checkout-test-setup.yml")))["jobs"]["setup"]["steps"]
         if "legacy licence row" in str(s.get("name"))][0]["run"]
def lstep(**env):
    ws = os.path.join(TMP, "lws"); rt = os.path.join(TMP, "lrt"); shutil.rmtree(ws, True); shutil.rmtree(rt, True); os.makedirs(rt)
    os.makedirs(os.path.join(ws, "atlas-tools", "release", "studio"))
    shutil.copytree(WORKER, os.path.join(ws, "worker", "plotart-studio"), ignore=shutil.ignore_patterns("node_modules", ".wrangler"))
    for f in (GATE, os.path.join(REPO, "atlas-tools", "release", "studio", "wrangler-error.py")): shutil.copy(f, os.path.join(ws, "atlas-tools", "release", "studio"))
    e = {**ENV, "GITHUB_WORKSPACE": ws, "RUNNER_TEMP": rt, "GITHUB_STEP_SUMMARY": SUMF, "PATH": BIN + os.pathsep + os.environ["PATH"], **env}
    r = subprocess.run(["bash", "-c", LSTEP], env=e, capture_output=True, text=True)
    return r.returncode, r.stdout
def migrated():
    c = sqlite3.connect(REMOTE); r = sorted(c.execute("SELECT artist_id, doc_id FROM agreement_acceptances WHERE method = 'migrated_from_artists_table'")); c.close(); return r
case("new seed carries the migrated licence row for both synthetic artists", (reset(*FILES), migrated())[1] == [("atestfnd", "PA-GPIL-2026-10-29"), ("atestgal", "PA-GPIL-2026-10-29")])
reset(FILES[0], FILES[1], OLDSEED); rc, line = gate("legacy_check"); case("legacy_check passes on the TEST database as first seeded", rc == 0 and "safe to apply" in line, line)
rc, line = gate("legacy_verify"); case("legacy_verify refuses before the row exists", rc == 1 and "not exactly one per synthetic artist" in line, line)
rc, out = lstep(); case("d1_legacy_licence step end to end: gate, one statement, verified", rc == 0 and "PASS  applied checkout-test-legacy-licence.sql" in out and "exactly one migrated licence row" in out and migrated() == [("atestfnd", "PA-GPIL-2026-10-29"), ("atestgal", "PA-GPIL-2026-10-29")], out.strip().splitlines()[-1])
c = sqlite3.connect(REMOTE); n = c.execute("SELECT COUNT(*) FROM agreement_acceptances").fetchone()[0]; c.close()
case("it creates no agreement acceptance (two migrated label rows only)", n == 2)
rc, out = lstep(); case("a second run refuses (row already present) and applies nothing", rc == 1 and "nothing was applied" in out and migrated() == [("atestfnd", "PA-GPIL-2026-10-29"), ("atestgal", "PA-GPIL-2026-10-29")], out.strip().splitlines()[-1])
reset(FILES[0], FILES[1], OLDSEED); c = sqlite3.connect(REMOTE); c.execute("UPDATE artists SET id = 'arealone' WHERE id = 'atestgal'"); c.commit(); c.close()
rc, out = lstep(); case("refuses when the artists are not exactly the synthetic two", rc == 1 and "nothing was applied" in out and migrated() == [], out.strip().splitlines()[-1])
reset(FILES[0], FILES[1], OLDSEED); S.update(name="plotart-studio"); rc, out = lstep(); S.update(name="plotart-checkout-test")
case("refuses when the ID resolves to another database name (e.g. production)", rc == 1 and "nothing was applied" in out and migrated() == [], out.strip().splitlines()[-1])
reset(FILES[0], FILES[1], OLDSEED); rc, out = lstep(FAKE_FAIL_ON="checkout-test-legacy-licence.sql")
case("a failed apply stops loudly, output sanitised", rc == 1 and "was not applied" in out and "AAAAAAAAAAAAAAAAAAAA" not in out, out.strip().splitlines()[-1])
# secrets never printed
case("no token value appears in any output", "t" * 40 not in open(SUMF).read() if os.path.exists(SUMF) else True)

shutil.rmtree(TMP, True)
print(f"D1 GATE MATRIX · {sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
