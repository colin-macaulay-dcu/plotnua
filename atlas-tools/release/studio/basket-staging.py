#!/usr/bin/env python3
"""PlotArt multi-artist basket: PRIVATE STAGING on Cloudflare (prepared 21 Nov 2026).

Run only by .github/workflows/plotart-basket-staging.yml in the GitHub environment "checkout-test" (founder approval on
every run). It may touch ONLY these names, and refuses anything else:
  D1 database        plotart-basket-staging (location weur)
  Workers            plotart-basket-staging, plotart-basket-staging-studio   (deployed by Wrangler in the workflow)
  Access apps        "PlotArt basket staging" (the public Worker; testers), "PlotArt basket staging webhook" (bypass, path
                     /v1/stripe/webhook only), "PlotArt basket staging Studio" (founder only)

  plan      READ ONLY. Checks the variables and secrets exist and have the right form (values never printed), the token's
            status, whether the staging database and Access applications exist, and that no existing Worker is touched.
  create    Creates the staging database if absent and the three Access applications if absent. It makes no PUT, PATCH or
            DELETE request: nothing that exists is changed. Prints the database id and the Studio Access AUD (identifiers,
            not secrets) for the founder to store as variables.
  db_gate   READ ONLY. The database id names plotart-basket-staging and the database is EMPTY (no tables): db_setup may run.
  db_verify READ ONLY. The staging database holds the basket tables and the synthetic seed (two synthetic artists).
Prints names, counts and PASS/FAIL/INFO only."""
import json, os, re, sys, urllib.error, urllib.request

MODE = sys.argv[1] if len(sys.argv) > 1 else "plan"
API = "https://api.cloudflare.com/client/v4"
DB_NAME = "plotart-basket-staging"
WORKERS = ("plotart-basket-staging", "plotart-basket-staging-studio")
APPS = {"public": "PlotArt basket staging", "webhook": "PlotArt basket staging webhook", "studio": "PlotArt basket staging Studio"}
E = lambda k: os.environ.get(k, "").strip()
ACC, TOKEN, ACCESS_TOKEN, SUB = E("CLOUDFLARE_ACCOUNT_ID"), E("BASKET_STAGING_CF_TOKEN"), E("CHECKOUT_TEST_ACCESS_TOKEN"), E("WORKERS_SUBDOMAIN")
SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")
fails = 0


def out(status, text):
    global fails
    if status == "FAIL": fails += 1
    print(f"  {status:<5} {text}")
    if SUMMARY:
        with open(SUMMARY, "a") as f: f.write(f"- **{status}** {text}\n")


def cf(method, path, token, body=None):
    if method not in ("GET", "POST"): raise SystemExit("REFUSED: this script only reads and creates")
    if method == "POST" and not (re.fullmatch(r"/accounts/[0-9a-f]{32}/d1/database", path) or re.fullmatch(r"/accounts/[0-9a-f]{32}/access/apps", path)
                                 or re.fullmatch(r"/accounts/[0-9a-f]{32}/d1/database/[0-9a-f-]{36}/query", path)):
        raise SystemExit("REFUSED: POST allowed only to create the staging database / Access apps, or to query the staging database")
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}


def host(name): return f"{name}.{SUB}.workers.dev"


def forms():
    ok = True
    checks = {
        "CLOUDFLARE_ACCOUNT_ID": re.fullmatch(r"[0-9a-f]{32}", ACC),
        "WORKERS_SUBDOMAIN (from CHECKOUT_TEST_ORIGIN)": re.fullmatch(r"[a-z0-9-]{1,63}", SUB),
        "BASKET_STAGING_CF_TOKEN": len(TOKEN) >= 30,
        "CHECKOUT_TEST_ACCESS_TOKEN": len(ACCESS_TOKEN) >= 30,
        "BASKET_STAGING_TESTER_EMAILS": all(re.fullmatch(r"[^\s@,]+@[^\s@,]+\.[a-z]{2,}", x.strip(), re.I) for x in E("BASKET_STAGING_TESTER_EMAILS").split(",")) and E("BASKET_STAGING_TESTER_EMAILS") != "",
        "CHECKOUT_TEST_FOUNDER_EMAILS": E("CHECKOUT_TEST_FOUNDER_EMAILS") != "",
    }
    for k, v in checks.items():
        out("PASS" if v else "FAIL", f"{k} present and well-formed (value not printed)"); ok = ok and bool(v)
    return ok


def find_db():
    s, j = cf("GET", f"/accounts/{ACC}/d1/database?name={DB_NAME}&per_page=50", TOKEN)
    if s != 200: out("FAIL", f"D1 list not readable with BASKET_STAGING_CF_TOKEN (HTTP {s})"); return None
    dbs = [d for d in j.get("result") or [] if d.get("name") == DB_NAME]
    return dbs[0] if dbs else False


def apps():
    s, j = cf("GET", f"/accounts/{ACC}/access/apps?per_page=100", ACCESS_TOKEN)
    if s != 200: out("FAIL", f"Access applications not readable (HTTP {s})"); return None
    return {a.get("name"): a for a in j.get("result") or [] if a.get("name") in APPS.values()}


def app_body(kind):
    h = host(WORKERS[1] if kind == "studio" else WORKERS[0])
    emails = [x.strip() for x in (E("CHECKOUT_TEST_FOUNDER_EMAILS") if kind == "studio" else E("BASKET_STAGING_TESTER_EMAILS") + "," + E("CHECKOUT_TEST_FOUNDER_EMAILS")).split(",") if x.strip()]
    if kind == "webhook":   # Stripe cannot sign in: only this path bypasses Access; the Worker accepts only Stripe-signed events
        return {"name": APPS[kind], "type": "self_hosted", "domain": h + "/v1/stripe/webhook", "session_duration": "30m", "app_launcher_visible": False,
                "policies": [{"name": "Stripe webhooks (signature checked by the Worker)", "decision": "bypass", "include": [{"everyone": {}}], "precedence": 1}]}
    return {"name": APPS[kind], "type": "self_hosted", "domain": h, "session_duration": "24h", "app_launcher_visible": False,
            "policies": [{"name": "Staging testers" if kind == "public" else "Founder", "decision": "allow", "include": [{"email": {"email": e}} for e in sorted(set(emails))], "precedence": 1}]}


if MODE == "test_access":
    # The EXISTING TEST checkout Worker (plotart-checkout-test): put it behind Access before the basket and the synthetic gallery
    # are deployed there. The Stripe webhook path stays reachable (bypass; the Worker accepts only Stripe-signed events), so the
    # existing TEST webhooks keep working. Creates at most two Access applications; changes nothing that exists.
    H = re.sub(r"^https://|/$", "", E("CHECKOUT_TEST_ORIGIN"))
    if not re.fullmatch(r"plotart-checkout-test\.[a-z0-9-]+\.workers\.dev", H): raise SystemExit("REFUSED: CHECKOUT_TEST_ORIGIN is not the TEST checkout Worker")
    emails = sorted({x.strip() for x in (E("CHECKOUT_TEST_FOUNDER_EMAILS") + "," + E("BASKET_STAGING_TESTER_EMAILS")).split(",") if x.strip()})
    if not emails: raise SystemExit("REFUSED: no founder email to allow")
    s, j = cf("GET", f"/accounts/{ACC}/access/apps?per_page=100", ACCESS_TOKEN)
    if s != 200: out("FAIL", f"Access applications not readable with CHECKOUT_TEST_ACCESS_TOKEN (HTTP {s})"); sys.exit(1)
    have = {(a.get("domain") or "").rstrip("/"): a for a in j.get("result") or []}
    want = [("webhook", H + "/v1/stripe/webhook", {"name": "PlotArt checkout TEST webhook", "type": "self_hosted", "domain": H + "/v1/stripe/webhook", "session_duration": "30m", "app_launcher_visible": False,
              "policies": [{"name": "Stripe webhooks (signature checked by the Worker)", "decision": "bypass", "include": [{"everyone": {}}], "precedence": 1}]}),
            ("site", H, {"name": "PlotArt checkout TEST", "type": "self_hosted", "domain": H, "session_duration": "24h", "app_launcher_visible": False,
              "policies": [{"name": "Founder and testers", "decision": "allow", "include": [{"email": {"email": e}} for e in emails], "precedence": 1}]})]
    for kind, dom, body in want:
        if dom in have: out("INFO", f"Access already protects {dom} ({kind}): unchanged"); continue
        s, j = cf("POST", f"/accounts/{ACC}/access/apps", ACCESS_TOKEN, body)
        out("PASS" if s in (200, 201) else "FAIL", f"Access {kind} application for {dom} " + ("created" if s in (200, 201) else f"NOT created (HTTP {s})"))
    sys.exit(1 if fails else 0)
if MODE not in ("plan", "create", "db_gate", "db_verify"): raise SystemExit("unknown mode")
if not forms(): sys.exit(1)
s, j = cf("GET", "/user/tokens/verify", TOKEN)
out("PASS" if s == 200 and (j.get("result") or {}).get("status") == "active" else "FAIL", "BASKET_STAGING_CF_TOKEN is active")
db = find_db()
if MODE in ("plan", "create"):
    s, j = cf("GET", f"/accounts/{ACC}/workers/scripts", TOKEN)
    names = [w.get("id") for w in (j.get("result") or [])] if s == 200 else []
    out("INFO", f"staging Workers already deployed: {[n for n in names if n in WORKERS] or 'none'}; other Workers are never touched")
    a = apps()
    out("INFO", f"staging database: {'exists' if db else 'not created yet' if db is False else 'unknown'}; staging Access apps present: {sorted(a) if a is not None else 'unknown'}")
    out("INFO", f"staging hostnames: {host(WORKERS[0])} (testers), {host(WORKERS[1])} (founder)")
if MODE == "create" and not fails:
    if db is False:
        s, j = cf("POST", f"/accounts/{ACC}/d1/database", TOKEN, {"name": DB_NAME, "primary_location_hint": "weur"})
        db = j.get("result") if s == 200 else None
        out("PASS" if db else "FAIL", f"created D1 {DB_NAME} (weur)" if db else f"could not create D1 {DB_NAME} (HTTP {s})")
    a = apps() or {}
    for kind in ("webhook", "public", "studio"):
        if APPS[kind] in a: out("INFO", f"Access app '{APPS[kind]}' already exists: unchanged"); continue
        s, j = cf("POST", f"/accounts/{ACC}/access/apps", ACCESS_TOKEN, app_body(kind))
        out("PASS" if s in (200, 201) else "FAIL", f"Access app '{APPS[kind]}' created" if s in (200, 201) else f"Access app '{APPS[kind]}' not created (HTTP {s})")
        if s in (200, 201): a[APPS[kind]] = j.get("result") or {}
    if db: out("INFO", f"store as variable BASKET_STAGING_D1_DATABASE_ID: {db.get('uuid')}")
    st = a.get(APPS["studio"]) or {}
    if st.get("aud"): out("INFO", f"store as variable BASKET_STAGING_STUDIO_ACCESS_AUD: {st.get('aud')}")
if MODE in ("db_gate", "db_verify"):
    want = E("BASKET_STAGING_D1_DATABASE_ID")
    if not db or db.get("uuid") != want: out("FAIL", "BASKET_STAGING_D1_DATABASE_ID does not name plotart-basket-staging"); sys.exit(1)
    s, j = cf("POST", f"/accounts/{ACC}/d1/database/{want}/query", TOKEN, {"sql": "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"})
    tables = [r.get("name") for r in ((j.get("result") or [{}])[0].get("results") or [])] if s == 200 else None
    if tables is None: out("FAIL", f"staging database not readable (HTTP {s})")
    elif MODE == "db_gate": out("PASS" if not tables else "FAIL", "staging database is empty: setup may run" if not tables else f"staging database is NOT empty ({len(tables)} tables): setup refused")
    else:
        need = {"artists", "artworks", "checkout_orders", "checkout_baskets", "basket_lines", "artwork_delivery_offers", "basket_terms"}
        out("PASS" if need <= set(tables) else "FAIL", f"basket tables present ({len(tables)} tables)")
        s, j = cf("POST", f"/accounts/{ACC}/d1/database/{want}/query", TOKEN, {"sql": "SELECT COUNT(*) AS n FROM artists WHERE id IN ('astgal','astfnd')"})
        n = ((j.get("result") or [{}])[0].get("results") or [{}])[0].get("n") if s == 200 else None
        out("PASS" if n == 2 else "FAIL", f"the two synthetic staging artists are seeded ({n})")
sys.exit(1 if fails else 0)
