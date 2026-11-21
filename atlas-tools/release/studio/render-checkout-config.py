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
  CHECKOUT_TEST_ACCESS_TEAM); MAILER none, deletion schedule off, instant publishing off; sandbox mode (simulated publication only); no publishing pipeline token and
  no application-register service binding. CHECKOUT_PILOT_ENABLED follows the workflow input ENABLE_TEST_PILOT (default off).
PRODUCTION (GitHub environment "studio-production."):
  Worker plotart-checkout on the production database. The pilot is OFF unless live checkout is explicitly enabled
  (ENABLE_LIVE_PILOT=true AND LIVE_CONFIRMATION exactly "ENABLE LIVE PLOTART CHECKOUT"), which sets CHECKOUT_PILOT_ENABLED,
  CHECKOUT_LIVE and live email. The code accepts live mode only with ENVIRONMENT=production and a LIVE key (stripe.js).
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

LIVE_CONFIRMATION = "ENABLE LIVE PLOTART CHECKOUT"
def live_requested():
    """Live checkout (20 Nov 2026) is enabled ONLY by both workflow inputs together: ENABLE_LIVE_PILOT=true and the exact
    confirmation phrase. Anything else renders the pilot OFF, as before."""
    en, conf = os.environ.get("ENABLE_LIVE_PILOT", "false"), os.environ.get("LIVE_CONFIRMATION", "")
    if en not in ("true", "false"): sys.exit("REFUSED: ENABLE_LIVE_PILOT must be true or false")
    if en == "true" and conf != LIVE_CONFIRMATION: sys.exit("REFUSED: live checkout needs the exact confirmation phrase")
    return en == "true"

def insert_var(text, after_key, key, value, where):
    if re.search(r'^%s\s*=' % re.escape(key), text, flags=re.M): sys.exit(f"REFUSED: {where} already defines {key}")
    out, n = re.subn(r'^(%s\s*=.*)$' % re.escape(after_key), lambda m: m.group(1) + "\n%s = %s" % (key, json.dumps(value)), text, count=1, flags=re.M)
    if n != 1: sys.exit(f"REFUSED: could not place {key} in {where}")
    return out

if TARGET == "production":
    db = need("STUDIO_D1_DATABASE_ID", UUID)
    origin = need("CHECKOUT_PRODUCTION_ORIGIN", r"https://[a-z0-9.-]+")
    if os.environ.get("ENABLE_TEST_PILOT", "false") != "false": sys.exit("REFUSED: the test pilot cannot be switched on in production")
    live = live_requested()
    out = setkey(checkout_src, "database_id", db, "wrangler.checkout.toml")
    out = setkey(out, "CHECKOUT_ORIGIN", origin, "wrangler.checkout.toml")
    if live:
        out = setkey(out, "CHECKOUT_PILOT_ENABLED", "true", "wrangler.checkout.toml")
        out = insert_var(out, "CHECKOUT_PILOT_ENABLED", "CHECKOUT_LIVE", "true", "wrangler.checkout.toml")
        mail_from = need("CHECKOUT_LIVE_MAIL_FROM", r"[^<>]{1,60} <[a-z0-9._-]+@plotnua\.ie>")
        notify = need("CHECKOUT_LIVE_NOTIFY_EMAIL", r"[a-z0-9._+-]+@plotnua\.ie")
        for k, v in (("CHECKOUT_MAIL", "resend"), ("CHECKOUT_MAIL_APPROVED", "true"), ("CHECKOUT_MAIL_FROM", mail_from), ("CHECKOUT_NOTIFY_EMAIL", notify)):
            out = insert_var(out, "CHECKOUT_LIVE", k, v, "wrangler.checkout.toml")
    # Multi-artist basket (21 Nov 2026): ONLY with live checkout, the explicit basket switch, approved LIVE basket texts bundled
    # (src/basket-terms.js LIVE_BASKET_DOCS not empty) and a LIVE publishable key. The synthetic staging gallery never.
    basket = os.environ.get("ENABLE_LIVE_BASKET", "false")
    if basket not in ("true", "false"): sys.exit("REFUSED: ENABLE_LIVE_BASKET must be true or false")
    if basket == "true":
        if not live: sys.exit("REFUSED: the basket can be enabled only together with live checkout")
        # issued texts: both kinds in agreements/basket-issued (fingerprints), bundled into src/basket-live-docs.js by build-assets
        fpp = os.path.join(W, "agreements", "basket-issued", "fingerprints.json")
        kinds = {d.get("kind") for d in json.load(open(fpp, encoding="utf-8"))["documents"].values()} if os.path.exists(fpp) else set()
        if kinds != {"artist_basket_addendum", "buyer_basket_terms"}: sys.exit("REFUSED: no approved LIVE basket texts are issued (agreements/basket-issued needs PA-BBT and PA-BAA)")
        bundled = open(os.path.join(W, "src", "basket-live-docs.js"), encoding="utf-8").read()
        if re.search(r"LIVE_BASKET_TEXTS\s*=\s*\{\s*\}", bundled) or "-TEST-" in bundled: sys.exit("REFUSED: the issued LIVE basket texts are not bundled (run build-assets.mjs)")
        if not all(os.path.exists(os.path.join(W, "migrations", m)) for m in ("0019_multi_artist_basket.sql", "0020_basket_consents.sql", "0021_basket_terms_issue.sql")):
            sys.exit("REFUSED: the basket migrations 0019, 0020 and 0021 must be in the release")
        pk = need("CHECKOUT_LIVE_PUBLISHABLE_KEY", r"pk_live_[A-Za-z0-9]+")
        out = insert_var(out, "CHECKOUT_PILOT_ENABLED", "BASKET_ENABLED", "true", "wrangler.checkout.toml")
        out = insert_var(out, "BASKET_ENABLED", "STRIPE_PUBLISHABLE_KEY", pk, "wrangler.checkout.toml")
    cfg = tomllib.loads(out)
    v = cfg["vars"]
    assert "STAGING_GALLERY" not in v and "BASKET_COMMISSION_FREE" not in v and "STRIPE_API_BASE" not in v, "no staging or test-only switch in production"
    assert v.get("BASKET_ENABLED", "false") == ("true" if basket == "true" else "false")
    assert cfg["name"] == "plotart-checkout" and v["ENVIRONMENT"] == "production" and "SANDBOX" not in v
    assert cfg["d1_databases"][0]["database_name"] == "plotart-studio" and "STRIPE_API_BASE" not in v
    assert v["CHECKOUT_PILOT_ENABLED"] == ("true" if live else "false") and v.get("CHECKOUT_LIVE", "false") == ("true" if live else "false")
    assert "CHECKOUT_MAIL_TEST_RECIPIENTS" not in v and "CHECKOUT_MAIL_SANDBOX_TEST" not in v
    open(os.path.join(W, "wrangler.checkout.production.toml"), "w").write(out)
    print("production checkout configuration rendered (plotart-checkout, %s%s)" % ("LIVE checkout ENABLED" if live else "CHECKOUT_PILOT_ENABLED=false", ", BASKET ENABLED" if basket == "true" else ""))

elif TARGET == "test":
    db = need("CHECKOUT_TEST_D1_DATABASE_ID", UUID)
    prod_db = os.environ.get("STUDIO_D1_DATABASE_ID", "").strip()
    if prod_db and prod_db == db: sys.exit("REFUSED: the test database must not be the production database")
    aud = need("CHECKOUT_TEST_ACCESS_AUD", r"[0-9a-f]{64}")
    team = need("CHECKOUT_TEST_ACCESS_TEAM", r"https://[a-z0-9-]+\.cloudflareaccess\.com")
    origin = need("CHECKOUT_TEST_ORIGIN", r"https://plotart-checkout-test\.[a-z0-9.-]+")
    enable = os.environ.get("ENABLE_TEST_PILOT", "false")
    if enable not in ("true", "false"): sys.exit("REFUSED: ENABLE_TEST_PILOT must be true or false")
    if os.environ.get("ENABLE_LIVE_PILOT", "false") != "false": sys.exit("REFUSED: live checkout can never be enabled in the TEST environment")
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
    # Studio TEST runs in sandbox mode (19 Nov 2026): "Publish" is simulated and recorded in the TEST database only, so an
    # artwork can reach "published" for a TEST quote; no publishing dispatch, no pipeline API, no email, banner on every page.
    if re.search(r'^SANDBOX\s*=', s, flags=re.M): sys.exit("REFUSED: wrangler.toml already defines SANDBOX")
    s, n = re.subn(r'^(ENVIRONMENT\s*=\s*"test".*)$', lambda m: m.group(1) + '\nSANDBOX = "true"', s, count=1, flags=re.M)
    if n != 1: sys.exit("REFUSED: could not place SANDBOX in the Studio TEST configuration")
    st = tomllib.loads(s)
    assert st["name"] == "plotart-studio-test" and st["vars"]["ENVIRONMENT"] == "test" and st["vars"]["MAILER"] == "none"
    assert st["d1_databases"][0]["database_name"] == "plotart-checkout-test" and all("-test-" in b["bucket_name"] for b in st["r2_buckets"])
    assert "services" not in st and "PARTICIPATION_DELETION" not in st["vars"]
    assert st["vars"].get("SANDBOX") == "true" and "SANDBOX" not in cc["vars"]
    assert "CHECKOUT_LIVE" not in st["vars"] and "CHECKOUT_LIVE" not in cc["vars"], "the TEST Workers never carry the live switch"
    open(os.path.join(W, "wrangler.checkout.test.toml"), "w").write(c)
    open(os.path.join(W, "wrangler.studio.test.toml"), "w").write(s)
    print(f"test configurations rendered (plotart-checkout-test, plotart-studio-test, CHECKOUT_PILOT_ENABLED={enable})")
else:
    sys.exit("usage: render-checkout-config.py <worker dir> test|production")
