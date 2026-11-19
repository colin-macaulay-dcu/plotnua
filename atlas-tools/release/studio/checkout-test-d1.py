#!/usr/bin/env python3
"""PlotArt managed checkout pilot: TEST database (plotart-checkout-test) gate and verification for d1_setup.

Run only by .github/workflows/plotart-checkout-test-setup.yml (mode d1_setup) in the GitHub environment "checkout-test".
It never writes: the workflow applies the files with Wrangler between `check` and `verify`. Fails closed on everything.

  check    Validates the account ID and database ID formats, that CHECKOUT_TEST_CF_TOKEN is active, that the database ID
           resolves to the database NAMED plotart-checkout-test, and that it has NO tables. Any other answer, status or
           malformed response stops the run (exit 1). Run immediately before the files are applied.
  verify   Builds the expected end state OFFLINE (schema.sql, migration 0013 and the very seed file the workflow applied,
           loaded into an in-memory SQLite) and compares the remote TEST database with it exactly: the same set of tables,
           the same row count in every table, and exactly the two synthetic artists (IDs and test addresses).

Prints names, counts and PASS/FAIL only; never a token, never a raw API response.
Environment: CLOUDFLARE_ACCOUNT_ID, CHECKOUT_TEST_D1_DATABASE_ID, CHECKOUT_TEST_CF_TOKEN; verify also D1_SEED_FILE.
CHECKOUT_D1_API may point the API at a local mock (offline tests only)."""
import json, os, re, sqlite3, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.normpath(os.path.join(HERE, "..", "..", "..", "worker", "plotart-studio"))
API = os.environ.get("CHECKOUT_D1_API", "https://api.cloudflare.com/client/v4")
NAME = "plotart-checkout-test"
SYNTHETIC = {"atestfnd": "colin+f1@plotnua.ie", "atestgal": "colin+g1@plotnua.ie"}
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
E = lambda k: os.environ.get(k, "").strip()
SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")


class Stop(Exception): pass


def out(status, text):
    print(f"  {status:<5} {text}")
    if SUMMARY:
        with open(SUMMARY, "a") as f: f.write(f"- **{status}** {text}\n")


def must(cond, what):
    if not cond: raise Stop(what)


def code_of(j):
    """Cloudflare error codes only (never messages or bodies): safe to print."""
    try: return ",".join(str(x.get("code")) for x in (j.get("errors") or [])) or "none"
    except Exception: return "unreadable"


def cf(method, path, token, body=None):
    must(method in ("GET", "POST"), "only reads and the D1 read-query endpoint are used here")
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: status, raw = r.status, r.read()
    except urllib.error.HTTPError as e: status, raw = e.code, e.read()
    except Exception as e: raise Stop(f"Cloudflare API not reachable ({type(e).__name__})")
    try: j = json.loads(raw or b"{}")
    except Exception: raise Stop(f"{path.split('/')[-1] or 'API'}: malformed response (HTTP {status})")
    must(isinstance(j, dict), f"malformed response (HTTP {status})")
    return status, j


def prerequisites():
    acc, db, tok = E("CLOUDFLARE_ACCOUNT_ID"), E("CHECKOUT_TEST_D1_DATABASE_ID"), E("CHECKOUT_TEST_CF_TOKEN")
    must(re.fullmatch(r"[0-9a-f]{32}", acc), "CLOUDFLARE_ACCOUNT_ID missing or not 32 hex characters")
    must(re.fullmatch(UUID, db), "CHECKOUT_TEST_D1_DATABASE_ID missing or not a UUID")
    must(len(tok) >= 20 and not re.search(r"\s", tok), "CHECKOUT_TEST_CF_TOKEN missing or malformed")
    s, j = cf("GET", f"/accounts/{acc}/tokens/verify", tok)
    if s != 200: s, j = cf("GET", "/user/tokens/verify", tok)
    must(s == 200 and isinstance(j.get("result"), dict) and j["result"].get("status") == "active",
         f"CHECKOUT_TEST_CF_TOKEN is not verified active (HTTP {s}, codes {code_of(j)})")
    s, j = cf("GET", f"/accounts/{acc}/d1/database/{db}", tok)
    r = j.get("result")
    must(s == 200 and isinstance(r, dict), f"TEST database lookup failed (HTTP {s}, codes {code_of(j)})")
    must(r.get("name") == NAME, f"the database ID resolves to {r.get('name')!r}, not {NAME}: nothing done")
    must(r.get("uuid", db) == db, "the lookup returned a different database ID")
    return acc, db, tok


def query(acc, db, tok, sql):
    s, j = cf("POST", f"/accounts/{acc}/d1/database/{db}/query", tok, {"sql": sql})
    res = j.get("result")
    must(s == 200 and j.get("success") is True and isinstance(res, list) and len(res) == 1 and isinstance(res[0], dict)
         and res[0].get("success", True) is True and isinstance(res[0].get("results"), list),
         f"TEST database query not readable (HTTP {s}, codes {code_of(j)})")
    return res[0]["results"]


TABLES_SQL = "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name"


def remote_tables(acc, db, tok):
    rows = query(acc, db, tok, TABLES_SQL)
    must(all(isinstance(x, dict) and isinstance(x.get("name"), str) for x in rows), "malformed table list")
    return sorted(x["name"] for x in rows)


def expected_state(seed_file):
    must(seed_file and os.path.isfile(seed_file), "D1_SEED_FILE (the seed the workflow applied) is missing")
    c = sqlite3.connect(":memory:")
    for f in (os.path.join(WORKER, "schema.sql"), os.path.join(WORKER, "migrations", "0013_gallery_artist_agreement_text.sql"), seed_file):
        c.executescript(open(f, encoding="utf-8").read())
    tables = sorted(r[0] for r in c.execute(TABLES_SQL))
    counts = {t: c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    artists = {r[0]: r[1] for r in c.execute("SELECT id, email FROM artists")}
    must(artists == SYNTHETIC, f"the seed file does not contain exactly the two synthetic artists ({sorted(artists)})")
    return tables, counts


def check():
    acc, db, tok = prerequisites()
    t = remote_tables(acc, db, tok)
    must(not t, f"{NAME} already has {len(t)} tables: nothing applied (setup runs only on an EMPTY TEST database)")
    out("PASS", f"{NAME} resolved from its ID, token active, database EMPTY: safe to apply the schema and synthetic seed")


def verify():
    acc, db, tok = prerequisites()
    tables, counts = expected_state(E("D1_SEED_FILE"))
    got = remote_tables(acc, db, tok)
    missing, extra = sorted(set(tables) - set(got)), sorted(set(got) - set(tables))
    must(not missing and not extra, f"table set differs from the expected state: missing {missing[:8]}{'…' if len(missing) > 8 else ''}, "
                                    f"unexpected {extra[:8]}{'…' if len(extra) > 8 else ''} (partial or wrong setup)")
    sql = " UNION ALL ".join(f"SELECT '{t}' AS t, COUNT(*) AS n FROM \"{t}\"" for t in tables)
    rows = query(acc, db, tok, sql)
    got_counts = {r.get("t"): r.get("n") for r in rows if isinstance(r, dict)}
    must(set(got_counts) == set(tables), "row counts not readable for every table")
    diff = [f"{t} {got_counts[t]}≠{counts[t]}" for t in tables if got_counts[t] != counts[t]]
    must(not diff, f"row counts differ from the expected state: {diff[:8]} (partial or wrong setup)")
    arts = query(acc, db, tok, "SELECT id, email FROM artists ORDER BY id")
    must({a.get("id"): a.get("email") for a in arts} == SYNTHETIC and len(arts) == 2,
         f"artists are not exactly the two synthetic test artists ({[a.get('id') for a in arts]})")
    out("PASS", f"{NAME} matches the expected state exactly: {len(tables)} tables, {sum(counts.values())} rows, "
                f"synthetic artists {', '.join(sorted(SYNTHETIC))} only")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if mode == "check": check()
        elif mode == "verify": verify()
        else: raise Stop("usage: checkout-test-d1.py check|verify")
    except Stop as e:
        out("FAIL", f"STOPPED (fail closed): {e}")
        sys.exit(1)
    except Exception as e:   # anything unexpected also fails closed, without printing data
        out("FAIL", f"STOPPED (fail closed): unexpected {type(e).__name__}")
        sys.exit(1)
