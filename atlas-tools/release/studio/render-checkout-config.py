#!/usr/bin/env python3
"""Render Wrangler configurations for the PlotArt managed checkout pilot (development 16 Nov 2026), on the pattern of
render-enquiry-config.py. Identifiers come from GitHub environment variables (never the public repository) and nothing about
them is printed. TEST and PRODUCTION are rendered by separate rules and never share a Worker, database, bucket or secret.

  python3 render-checkout-config.py <worker dir> test         -> wrangler.checkout.test.toml + wrangler.studio.test.toml
  python3 render-checkout-config.py <worker dir> production   -> wrangler.checkout.production.toml (pilot always OFF)

TEST (GitHub environment "checkout-test"):
  Workers plotart-checkout-test and plotart-studio-test; D1 database plotart-checkout-test (CHECKOUT_TEST_D1_DATABASE_ID,
  refused if it equals the production STUDIO_D1_DATABASE_ID when that is visible); R2 buckets plotart-studio-test-images
  and plotart-studio-test-applications; its own Cloudflare Access application (CHECKOUT_TEST_ACCESS_AUD /
  CHECKOUT_TEST_ACCESS_TEAM); MAILER none, deletion schedule off, instant publishing off; no publishing pipeline token and
  no application-register service binding. CHECKOUT_PILOT_ENABLED follows the workflow input ENABLE_TEST_PILOT (default off).
PRODUCTION (GitHub environment "studio-production."):
  Worker plotart-checkout on the production database; CHECKOUT_PILOT_ENABLED is ALWAYS "false" here, whatever is asked.
  The production Studio is rendered by render-config.py / studio-deploy.yml, never by this script."""
import json, os, re, sys, tomllib
W, TARGET = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
def need(name, pattern):
    v = os.environ.get(name, "").strip()
    if not re.fullmatch(pattern, v): sys.exit(f"REFUSED: environment variable {name} is missing or not in the expected form")
    return v
def setkey(text, key, value, where):
    out, n = re.subn(r'^(%s\s*=\s*)"[^"]*"' % re.escape(key), lambda m: m.group(1) + json.dumps(value), text, count=1, flags=re.M)
    if n != 1: sys.exit(f"REFUSED: {key} not found in {where}")
    return out
def drop_block(text, header, binding):
    # remove one [[header]] block whose binding is `binding`
    pat = re.compile(r'^\[\[%s\]\]\n(?:(?!^\[).*\n?)*' % re.escape(header), re.M)
    out, n = text, 0
    for m in list(pat.finditer(text)):
        if re.search(r'^binding\s*=\s*"%s"' % re.escape(binding), m.group(0), re.M): out = out.replace(m.group(0), ""); n += 1
    if n != 1: sys.exit(f"REFUSED: could not remove [[{header}]] {binding}")
    return out

checkout_src = open(os.path.join(W, "wrangler.checkout.toml")).read()
if not re.search(r'^CHECKOUT_PILOT_ENABLED = "false"', checkout_src, re.M):
    sys.exit("REFUSED: wrangler.checkout.toml must ship with CHECKOUT_PILOT_ENABLED = \"false\"")

if TARGET == "production":
    db = need("STUDIO_D1_DATABASE_ID", UUID)
    origin = need("CHECKOUT_PRODUCTION_ORIGIN", r"https://[a-z0-9.-]+")
    if os.environ.get("ENABLE_TEST_PILOT", "false") != "false": sys.exit("REFUSED: the pilot cannot be switched on in production by this workflow")
    out = setkey(checkout_src, "database_id", db, "wrangler.checkout.toml")
    out = setkey(out, "CHECKOUT_ORIGIN", origin, "wrangler.checkout.toml")
    cfg = tomllib.loads(out)
    assert cfg["name"] == "plotart-checkout" and cfg["vars"]["CHECKOUT_PILOT_ENABLED"] == "false" and cfg["vars"]["ENVIRONMENT"] == "production"
    assert cfg["d1_databases"][0]["database_name"] == "plotart-studio" and "STRIPE_API_BASE" not in cfg["vars"]
    open(os.path.join(W, "wrangler.checkout.production.toml"), "w").write(out)
    print("production checkout configuration rendered (plotart-checkout, CHECKOUT_PILOT_ENABLED=false)")

elif TARGET == "test":
    db = need("CHECKOUT_TEST_D1_DATABASE_ID", UUID)
    prod_db = os.environ.get("STUDIO_D1_DATABASE_ID", "").strip()
    if prod_db and prod_db == db: sys.exit("REFUSED: the test database must not be the production database")
    aud = need("CHECKOUT_TEST_ACCESS_AUD", r"[0-9a-f]{64}")
    team = need("CHECKOUT_TEST_ACCESS_TEAM", r"https://[a-z0-9-]+\.cloudflareaccess\.com")
    origin = need("CHECKOUT_TEST_ORIGIN", r"https://plotart-checkout-test\.[a-z0-9.-]+")
    enable = os.environ.get("ENABLE_TEST_PILOT", "false")
    if enable not in ("true", "false"): sys.exit("REFUSED: ENABLE_TEST_PILOT must be true or false")
    # checkout (public) test Worker
    c = setkey(checkout_src, "name", "plotart-checkout-test", "wrangler.checkout.toml")
    c = setkey(c, "ENVIRONMENT", "test", "wrangler.checkout.toml")
    c = setkey(c, "CHECKOUT_PILOT_ENABLED", enable, "wrangler.checkout.toml")
    c = setkey(c, "CHECKOUT_ORIGIN", origin, "wrangler.checkout.toml")
    c = setkey(c, "database_name", "plotart-checkout-test", "wrangler.checkout.toml")
    c = setkey(c, "database_id", db, "wrangler.checkout.toml")
    cc = tomllib.loads(c)
    assert cc["name"].endswith("-test") and cc["d1_databases"][0]["database_name"] == "plotart-checkout-test"
    # Studio test Worker, from the production wrangler.toml with every production binding replaced or removed
    s = open(os.path.join(W, "wrangler.toml")).read()
    s = setkey(s, "name", "plotart-studio-test", "wrangler.toml")
    for k, v in {"ENVIRONMENT": "test", "ACCESS_TEAM_DOMAIN": team, "ACCESS_AUD": aud, "INSTANT_AUTOPUBLISH": "false", "HIRE_TERMS_ENABLED": "false",
                 "HIRE_RETENTION": "off", "MAILER": "none", "CHECKOUT_PILOT_ENABLED": enable, "CHECKOUT_ORIGIN": origin, "APPLICATION_REVIEW_PUBLIC_URL": ""}.items():
        s = setkey(s, k, v, "wrangler.toml")
    s = setkey(s, "database_name", "plotart-checkout-test", "wrangler.toml")
    s = setkey(s, "database_id", db, "wrangler.toml")
    s = s.replace('bucket_name = "plotart-studio-images"', 'bucket_name = "plotart-studio-test-images"').replace('bucket_name = "plotart-applications"', 'bucket_name = "plotart-studio-test-applications"')
    s = drop_block(s, "services", "APPLICATION_REGISTER")
    st = tomllib.loads(s)
    assert st["name"] == "plotart-studio-test" and st["vars"]["ENVIRONMENT"] == "test" and st["vars"]["MAILER"] == "none"
    assert st["d1_databases"][0]["database_name"] == "plotart-checkout-test" and all("-test-" in b["bucket_name"] for b in st["r2_buckets"])
    assert "services" not in st and "PARTICIPATION_DELETION" not in st["vars"]
    open(os.path.join(W, "wrangler.checkout.test.toml"), "w").write(c)
    open(os.path.join(W, "wrangler.studio.test.toml"), "w").write(s)
    print(f"test configurations rendered (plotart-checkout-test, plotart-studio-test, CHECKOUT_PILOT_ENABLED={enable})")
else:
    sys.exit("usage: render-checkout-config.py <worker dir> test|production")
