#!/usr/bin/env python3
"""PlotArt managed checkout pilot: TEST environment audit and (optionally) its Cloudflare Access application.

Run only by .github/workflows/plotart-checkout-test-setup.yml in the GitHub environment "checkout-test".

  audit         READ ONLY. Checks that the checkout-test variables and secrets exist and have the right form (values never
                printed), then reads Cloudflare: the token's status, the workers.dev subdomain, which plotart Workers
                exist, the TEST D1 database (name and table names only), the EU R2 buckets the TEST Studio binds, and
                (if the token may read them) the Access applications for the TEST hostnames.
  r2_plan       READ ONLY. For the two TEST buckets the TEST Studio binds (plotart-studio-test-images and
                plotart-studio-test-applications) checks the copies in the DEFAULT jurisdiction: objects, custom domains,
                public r2.dev access, event notifications and Worker bindings, and whether the EU copies exist.
  r2_apply      Repeats every r2_plan check and refuses unless each default copy is provably empty and unused; then creates
                the EU copy (cf-r2-jurisdiction: eu), deletes the unused default copy and verifies both. It deletes nothing
                else: DELETE is refused for any other path, mode or jurisdiction.
  create_access Creates ONE Access application for the TEST Studio hostname (plotart-studio-test.<subdomain>.workers.dev)
                with ONE allow policy for the founder's TEST addresses (CHECKOUT_TEST_FOUNDER_EMAILS), unless an application
                for that hostname already exists. It never modifies or deletes anything: this script makes no PUT, PATCH or
                DELETE request. Uses CHECKOUT_TEST_ACCESS_TOKEN (Account · Access: Apps and Policies · Edit) only for this.

Prints names, counts and PASS/FAIL/INFO only. The Access audience (AUD) tag is an identifier, not a secret: it is written
to the job summary so the founder can store it as the variable CHECKOUT_TEST_ACCESS_AUD."""
import json, os, re, sys, urllib.error, urllib.request

MODE = sys.argv[1] if len(sys.argv) > 1 else "audit"
R2_TEST = ("plotart-studio-test-images", "plotart-studio-test-applications")   # the ONLY buckets r2_* may touch
API = "https://api.cloudflare.com/client/v4"
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
E = lambda k: os.environ.get(k, "").strip()
ACC, TOKEN, ACCESS_TOKEN = E("CLOUDFLARE_ACCOUNT_ID"), E("CHECKOUT_TEST_CF_TOKEN"), E("CHECKOUT_TEST_ACCESS_TOKEN")
SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY")
fails = 0


def out(status, text):
    global fails
    if status == "FAIL": fails += 1
    line = f"  {status:<5} {text}"
    print(line)
    if SUMMARY:
        with open(SUMMARY, "a") as f: f.write(f"- **{status}** {text}\n")


def cf(method, path, token, body=None, headers=None):
    if method == "DELETE":
        if not (MODE == "r2_apply" and re.fullmatch(r"/accounts/[0-9a-f]{32}/r2/buckets/(%s)" % "|".join(R2_TEST), path) and not (headers or {}).get("cf-r2-jurisdiction")):
            raise SystemExit("REFUSED: the only deletion allowed is an empty default-jurisdiction TEST bucket in r2_apply")
    elif method not in ("GET", "POST"): raise SystemExit("REFUSED: this script only reads, creates and (r2_apply) deletes empty TEST buckets")
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: j = json.loads(e.read() or b"{}")
        except Exception: j = {}
        return e.code, j


def errs(j):
    return "; ".join(f"{x.get('code')}: {str(x.get('message', ''))[:120]}" for x in (j.get("errors") or [])) or "no detail"


# ---------------------------------------------------------------- configuration present and well formed (never printed)
print("PlotArt checkout TEST setup ·", MODE)
FORMS = {
    "CLOUDFLARE_ACCOUNT_ID": r"[0-9a-f]{32}", "CHECKOUT_TEST_D1_DATABASE_ID": UUID, "CHECKOUT_TEST_ACCESS_AUD": r"[0-9a-f]{64}",
    "CHECKOUT_TEST_ACCESS_TEAM": r"https://[a-z0-9-]+\.cloudflareaccess\.com", "CHECKOUT_TEST_ORIGIN": r"https://plotart-checkout-test\.[a-z0-9.-]+",
}
for k, p in FORMS.items():
    v = E(k)
    out("PASS" if re.fullmatch(p, v) else ("INFO" if k == "CHECKOUT_TEST_ACCESS_AUD" and MODE == "audit" and not v else "FAIL"),
        f"variable {k}: " + ("present, expected form" if re.fullmatch(p, v) else "missing" if not v else "present but NOT in the expected form"))
SECRETS = {"CHECKOUT_TEST_CF_TOKEN": r"\S{20,}", "CHECKOUT_TEST_STRIPE_SECRET_KEY": r"(sk|rk)_test_[A-Za-z0-9]+",
           "CHECKOUT_TEST_STRIPE_WEBHOOK_SECRET": r"whsec_[A-Za-z0-9]+", "CHECKOUT_TEST_FOUNDER_EMAILS": r".+@.+"}
for k, p in SECRETS.items():
    v = E(k)
    out("PASS" if re.fullmatch(p, v) else "FAIL", f"secret {k}: " + ("present, expected form" if re.fullmatch(p, v) else "missing" if not v else "present but NOT in the expected form"))
founders = [x.strip().lower() for x in re.split(r"[,\s]+", E("CHECKOUT_TEST_FOUNDER_EMAILS") or E("CHECKOUT_TEST_FOUNDER_EMAIL")) if "@" in x]
out("INFO", f"founder TEST addresses: {len(founders)}" + ("" if E("CHECKOUT_TEST_FOUNDER_EMAILS") else " (from the variable CHECKOUT_TEST_FOUNDER_EMAIL)" if founders else ""))
origin = E("CHECKOUT_TEST_ORIGIN")

# ---------------------------------------------------------------- Cloudflare (read only)
if not (re.fullmatch(FORMS["CLOUDFLARE_ACCOUNT_ID"], ACC) and TOKEN):
    out("FAIL", "Cloudflare not read: the account ID or CHECKOUT_TEST_CF_TOKEN is missing")
    sys.exit(1)
s, j = cf("GET", f"/accounts/{ACC}/tokens/verify", TOKEN)
if s != 200: s, j = cf("GET", "/user/tokens/verify", TOKEN)
out("PASS" if s == 200 and (j.get("result") or {}).get("status") == "active" else "FAIL", f"CHECKOUT_TEST_CF_TOKEN is active (HTTP {s})")

s, j = cf("GET", f"/accounts/{ACC}/workers/subdomain", TOKEN)
sub = (j.get("result") or {}).get("subdomain") if s == 200 else None
out("PASS" if sub else "INFO", f"workers.dev subdomain: {sub or 'not readable (HTTP %s)' % s}")
studio_host = f"plotart-studio-test.{sub}.workers.dev" if sub else None
if sub and origin:
    out("PASS" if origin == f"https://plotart-checkout-test.{sub}.workers.dev" else "FAIL",
        "CHECKOUT_TEST_ORIGIN matches plotart-checkout-test on this account's workers.dev subdomain")

s, j = cf("GET", f"/accounts/{ACC}/workers/scripts", TOKEN)
names = sorted(x.get("id") for x in (j.get("result") or []) if str(x.get("id", "")).startswith("plotart")) if s == 200 else None
out("INFO" if s == 200 else "FAIL", f"plotart Workers on the account: {', '.join(names) if names else 'none'}" if s == 200 else f"Workers not readable (HTTP {s}: {errs(j)})")
if names is not None:
    out("INFO", "TEST Workers deployed: " + (", ".join(n for n in names if n.endswith("-test")) or "none yet"))

db = E("CHECKOUT_TEST_D1_DATABASE_ID")
if re.fullmatch(UUID, db):
    s, j = cf("GET", f"/accounts/{ACC}/d1/database/{db}", TOKEN)
    r = j.get("result") or {}
    name = r.get("name")
    out("PASS" if s == 200 and name == "plotart-checkout-test" else "FAIL",
        f"TEST D1 database: {name or 'not readable (HTTP %s: %s)' % (s, errs(j))}" + (f" · region {r.get('running_in_region') or r.get('region') or '?'}" if s == 200 else ""))
    if name and name != "plotart-checkout-test": out("FAIL", "the TEST database identifier does not point at plotart-checkout-test: STOP")
    if s == 200 and name == "plotart-checkout-test":
        s2, q = cf("POST", f"/accounts/{ACC}/d1/database/{db}/query", TOKEN,
                   {"sql": "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name"})
        rows = ((q.get("result") or [{}])[0].get("results") or []) if s2 == 200 else []
        tables = [x["name"] for x in rows]
        pilot = [t for t in tables if t.startswith("checkout_")]
        out("INFO", f"TEST database tables: {len(tables)} (checkout pilot tables: {len(pilot)})" if s2 == 200 else f"TEST database tables not readable (HTTP {s2})")
        out("INFO", "TEST database schema: " + ("EMPTY: schema and seed not yet applied (needs the founder's approval)" if not tables else
                                                "pilot schema present" if pilot else "Studio tables present, pilot tables absent"))

for jur in ("eu", None):
    s, j = cf("GET", f"/accounts/{ACC}/r2/buckets", TOKEN, headers={"cf-r2-jurisdiction": jur} if jur else None)
    bk = sorted(b.get("name") for b in ((j.get("result") or {}).get("buckets") or [])) if s == 200 else None
    tag = "EU" if jur else "default"
    if bk is None: out("FAIL" if jur else "INFO", f"R2 ({tag}) not readable (HTTP {s}: {errs(j)})"); continue
    test_bk = [b for b in bk if "test" in b]
    out("INFO", f"R2 {tag} TEST buckets: {', '.join(test_bk) or 'none'}")
    if jur:
        for need in ("plotart-studio-test-images", "plotart-studio-test-applications"):
            out("PASS" if need in bk else "FAIL", f"EU R2 bucket {need} " + ("exists" if need in bk else "MISSING (the TEST Studio binds it)"))

# Access: read with the Access token if present, else try the deployment token (expected to be refused)
atok = ACCESS_TOKEN or TOKEN
s, j = cf("GET", f"/accounts/{ACC}/access/apps", atok)
apps = j.get("result") or [] if s == 200 else None
which = "CHECKOUT_TEST_ACCESS_TOKEN" if ACCESS_TOKEN else "CHECKOUT_TEST_CF_TOKEN"
if apps is None:
    out("INFO", f"Access applications not readable with {which} (HTTP {s}): a token with Account · Access: Apps and Policies is needed")
else:
    out("INFO", f"Access applications on the account: {len(apps)} (read with {which}; none changed)")
    mine = [a for a in apps if studio_host and (a.get("domain") == studio_host or studio_host in (a.get("self_hosted_domains") or []))]
    co = [a for a in apps if sub and f"plotart-checkout-test.{sub}.workers.dev" in ([a.get("domain")] + (a.get("self_hosted_domains") or []))]
    out("INFO", f"Access application for {studio_host}: " + (f"EXISTS ({mine[0].get('name')}) · AUD {mine[0].get('aud')}" if mine else "none"))
    if co: out("FAIL", "an Access application covers plotart-checkout-test: Stripe webhooks and buyers could not reach it")

# ---------------------------------------------------------------- what the existing credentials can do (read-only probes)
s, j = cf("GET", f"/accounts/{ACC}/access/organizations", atok)
out("INFO", f"Access organisation readable with {which}: " + ("yes · " + str((j.get('result') or {}).get('auth_domain', '?')) if s == 200 else f"no (HTTP {s})"))
sk = E("CHECKOUT_TEST_STRIPE_SECRET_KEY")
if re.fullmatch(r"(sk|rk)_test_[A-Za-z0-9]+", sk):
    rq = urllib.request.Request("https://api.stripe.com/v1/webhook_endpoints?limit=100", headers={"Authorization": f"Bearer {sk}"})
    try:
        with urllib.request.urlopen(rq, timeout=30) as r: wj = json.loads(r.read()); ws = 200
    except urllib.error.HTTPError as e: wj, ws = {}, e.code
    if ws == 200:
        eps = [x for x in wj.get("data", []) if x.get("livemode") is False]
        mine_ep = [x for x in eps if "plotart-checkout-test" in str(x.get("url", ""))]
        out("INFO", f"Stripe TEST webhook endpoints readable with CHECKOUT_TEST_STRIPE_SECRET_KEY: {len(eps)} (for plotart-checkout-test: {len(mine_ep)})")
    else:
        out("INFO", f"Stripe webhook endpoints NOT readable with CHECKOUT_TEST_STRIPE_SECRET_KEY (HTTP {ws}): creating the endpoint needs Webhook Endpoints: Write")

# ---------------------------------------------------------------- R2: TEST buckets in the wrong (default) jurisdiction
def r2_state(name):
    st = {"name": name}
    s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{name}", TOKEN)
    st["default_exists"] = s == 200
    s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{name}", TOKEN, headers={"cf-r2-jurisdiction": "eu"})
    st["eu_exists"] = s == 200
    st["eu_jurisdiction"] = (j.get("result") or {}).get("jurisdiction") if s == 200 else None
    if st["default_exists"]:
        s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{name}/objects?per_page=1", TOKEN)
        st["objects_readable"] = s == 200
        st["objects"] = len(j.get("result") or []) if s == 200 else None
        s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{name}/domains/custom", TOKEN)
        st["custom_domains"] = len((j.get("result") or {}).get("domains") or []) if s == 200 else None
        s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{name}/domains/managed", TOKEN)
        st["public_r2dev"] = bool((j.get("result") or {}).get("enabled")) if s == 200 else None
        s, j = cf("GET", f"/accounts/{ACC}/event_notifications/r2/{name}/configuration", TOKEN)
        st["event_notifications"] = len((j.get("result") or {}).get("queues") or []) if s == 200 else (0 if s == 404 else None)
        bound = []
        s, j = cf("GET", f"/accounts/{ACC}/workers/scripts", TOKEN)
        for w in (j.get("result") or []) if s == 200 else []:
            s2, b = cf("GET", f"/accounts/{ACC}/workers/scripts/{w.get('id')}/settings", TOKEN)
            if s2 != 200: bound.append(f"{w.get('id')} (bindings not readable)"); continue
            for x in (b.get("result") or {}).get("bindings") or []:
                if x.get("type") == "r2_bucket" and x.get("bucket_name") == name and (x.get("jurisdiction") or "default") != "eu":
                    bound.append(w.get("id"))
        st["bound_by"] = bound if s == 200 else None
        st["safe_to_delete"] = (st["objects"] == 0 and st["custom_domains"] == 0 and st["public_r2dev"] is False
                                and st["event_notifications"] == 0 and st["bound_by"] == [])
    return st

if MODE in ("r2_plan", "r2_apply"):
    fails = 0   # the run's result is the R2 result (the audit lines above are information here)
    states = [r2_state(n) for n in R2_TEST]
    for st in states:
        if not st["default_exists"] and st["eu_exists"]:
            out("PASS", f"{st['name']}: already EU only (jurisdiction {st['eu_jurisdiction']}); nothing to do"); continue
        if not st["default_exists"]:
            out("INFO", f"{st['name']}: no default-jurisdiction bucket; EU bucket {'exists' if st['eu_exists'] else 'to be created'}"); continue
        out("PASS" if st["safe_to_delete"] else "FAIL",
            f"{st['name']} (default jurisdiction): objects {st['objects']}, custom domains {st['custom_domains']}, public r2.dev {st['public_r2dev']}, "
            f"event notifications {st['event_notifications']}, bound by Workers {st['bound_by']} · EU bucket exists: {st['eu_exists']} · "
            + ("SAFE to replace" if st["safe_to_delete"] else "REFUSED: not provably empty and unused"))
    out("INFO", "in-progress multipart uploads cannot be listed through the Cloudflare API; R2 itself refuses to delete a bucket that is not empty")
    if MODE == "r2_apply":
        if not all(st["safe_to_delete"] or not st["default_exists"] for st in states):
            out("FAIL", "r2_apply REFUSED: at least one default bucket is not provably empty and unused; nothing changed"); sys.exit(1)
        for st in states:
            n = st["name"]
            if not st["eu_exists"]:
                s, j = cf("POST", f"/accounts/{ACC}/r2/buckets", TOKEN, {"name": n}, headers={"cf-r2-jurisdiction": "eu"})
                if s not in (200, 201) and st["default_exists"]:
                    # the name may be held by the default bucket: delete the (verified empty, unbound) default bucket, then create in EU
                    d, dj = cf("DELETE", f"/accounts/{ACC}/r2/buckets/{n}", TOKEN)
                    out("PASS" if d == 200 else "FAIL", f"{n}: default-jurisdiction bucket deleted first (HTTP {d}{'' if d == 200 else ': ' + errs(dj)})")
                    if d != 200: sys.exit(1)
                    st["default_exists"] = False
                    s, j = cf("POST", f"/accounts/{ACC}/r2/buckets", TOKEN, {"name": n}, headers={"cf-r2-jurisdiction": "eu"})
                out("PASS" if s in (200, 201) else "FAIL", f"{n}: EU bucket created (HTTP {s}{'' if s in (200, 201) else ': ' + errs(j)})")
                if s not in (200, 201): sys.exit(1)
            if st["default_exists"]:
                d, dj = cf("DELETE", f"/accounts/{ACC}/r2/buckets/{n}", TOKEN)
                out("PASS" if d == 200 else "FAIL", f"{n}: unused default-jurisdiction bucket deleted (HTTP {d}{'' if d == 200 else ': ' + errs(dj)})")
        for n in R2_TEST:
            s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{n}", TOKEN, headers={"cf-r2-jurisdiction": "eu"})
            jur = (j.get("result") or {}).get("jurisdiction")
            out("PASS" if s == 200 and jur == "eu" else "FAIL", f"{n}: accessible in the EU jurisdiction (HTTP {s}, jurisdiction {jur})")
            s, j = cf("GET", f"/accounts/{ACC}/r2/buckets/{n}", TOKEN)
            out("PASS" if s != 200 else "FAIL", f"{n}: no default-jurisdiction copy remains (HTTP {s})")

# ---------------------------------------------------------------- create the TEST Studio Access application
if MODE == "create_access":
    if not ACCESS_TOKEN: out("FAIL", "create_access needs the secret CHECKOUT_TEST_ACCESS_TOKEN"); sys.exit(1)
    if not studio_host: out("FAIL", "workers.dev subdomain unknown: nothing created"); sys.exit(1)
    if apps is None: out("FAIL", "Access applications could not be read: nothing created"); sys.exit(1)
    if not founders: out("FAIL", "no founder TEST addresses: nothing created"); sys.exit(1)
    if mine:
        out("PASS", f"already exists, nothing created · CHECKOUT_TEST_ACCESS_AUD = {mine[0].get('aud')}")
    else:
        s, p = cf("POST", f"/accounts/{ACC}/access/policies", ACCESS_TOKEN, {
            "name": "PlotArt Studio TEST · founder test addresses", "decision": "allow",
            "include": [{"email": {"email": e}} for e in founders], "session_duration": "24h"})
        pid = (p.get("result") or {}).get("id")
        out("PASS" if s in (200, 201) and pid else "FAIL", f"TEST allow policy created (HTTP {s}{'' if pid else ': ' + errs(p)})")
        if not pid: sys.exit(1)
        s, a = cf("POST", f"/accounts/{ACC}/access/apps", ACCESS_TOKEN, {
            "name": "PlotArt Studio TEST (checkout pilot)", "type": "self_hosted", "domain": studio_host,
            "session_duration": "24h", "app_launcher_visible": False, "policies": [{"id": pid, "precedence": 1}]})
        r = a.get("result") or {}
        out("PASS" if s in (200, 201) and re.fullmatch(r"[0-9a-f]{64}", r.get("aud", "")) else "FAIL",
            f"TEST Access application for {studio_host} (HTTP {s})" + (f" · CHECKOUT_TEST_ACCESS_AUD = {r.get('aud')}" if r.get("aud") else ": " + errs(a)))

print(f"done · {fails} failure(s)")
sys.exit(1 if fails and MODE in ("create_access", "r2_apply") else 0)
