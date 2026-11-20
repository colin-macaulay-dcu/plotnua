#!/usr/bin/env python3
"""Render the Studio's production Wrangler configuration from the repository's wrangler.toml (31 Oct 2026).
The production identifiers live in GitHub environment variables, never in the public repository; the production
behaviour switches live in worker/plotart-studio/production.json. Writes wrangler.production.toml next to wrangler.toml
and prints nothing about the values.  python3 render-config.py <worker dir>"""
import json, os, re, sys, tomllib
W = sys.argv[1]
src = open(os.path.join(W, "wrangler.toml")).read()
prod = json.load(open(os.path.join(W, "production.json")))
need = {"STUDIO_D1_DATABASE_ID": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "STUDIO_ACCESS_AUD": r"[0-9a-f]{64}", "STUDIO_ACCESS_TEAM": r"https://[a-z0-9-]+\.cloudflareaccess\.com"}
val = {}
for k, pat in need.items():
    v = os.environ.get(k, "").strip()
    if not re.fullmatch(pat, v):
        sys.exit("REFUSED: environment variable %s is missing or not in the expected form" % k)
    val[k] = v
def setvar(text, key, value):
    out, n = re.subn(r'^(%s\s*=\s*)"[^"]*"' % re.escape(key), lambda m: m.group(1) + json.dumps(value), text, count=1, flags=re.M)
    if n != 1: sys.exit("REFUSED: %s not found in wrangler.toml" % key)
    return out
out = setvar(src, "ACCESS_TEAM_DOMAIN", val["STUDIO_ACCESS_TEAM"])
out = setvar(out, "ACCESS_AUD", val["STUDIO_ACCESS_AUD"])
out = setvar(out, "database_id", val["STUDIO_D1_DATABASE_ID"])
CHECKOUT_KEYS = {"CHECKOUT_PILOT_ENABLED", "CHECKOUT_LIVE", "CHECKOUT_ORIGIN", "CHECKOUT_MAIL", "CHECKOUT_MAIL_APPROVED", "CHECKOUT_MAIL_FROM",
                 "CHECKOUT_MAIL_TEST_RECIPIENTS", "CHECKOUT_MAIL_SANDBOX_TEST", "CHECKOUT_NOTIFY_EMAIL", "SANDBOX", "STRIPE_API_BASE"}
bad = CHECKOUT_KEYS & set(prod["vars"])
if bad: sys.exit("REFUSED: production.json may not set %s in vars: live checkout is enabled only by its checkout_live block" % sorted(bad))
for k, v in prod["vars"].items():
    out = setvar(out, k, v)
# Live checkout (20 Nov 2026): OFF unless production.json carries a checkout_live block with the exact confirmation phrase
# (a reviewed, founder-approved change to production.json, deployed through this protected workflow). The Stripe LIVE key
# itself is written separately by plotart-checkout-deploy.yml (live path); without it the code refuses every Stripe call.
LIVE_CONFIRMATION = "ENABLE LIVE PLOTART CHECKOUT"
live = prod.get("checkout_live")
if live is not None:
    if not isinstance(live, dict) or set(live) != {"confirmation", "checkout_origin", "mail_from", "notify_email"}:
        sys.exit("REFUSED: checkout_live must hold exactly confirmation, checkout_origin, mail_from and notify_email")
    if live["confirmation"] != LIVE_CONFIRMATION: sys.exit("REFUSED: checkout_live needs the exact confirmation phrase")
    if not re.fullmatch(r"https://[a-z0-9.-]+", live["checkout_origin"]) or "-test" in live["checkout_origin"]:
        sys.exit("REFUSED: checkout_live.checkout_origin must be the production checkout origin")
    if not re.fullmatch(r"[^<>]{1,60} <[a-z0-9._-]+@plotnua\.ie>", live["mail_from"]): sys.exit("REFUSED: checkout_live.mail_from must be a plotnua.ie sender")
    if not re.fullmatch(r"[a-z0-9._+-]+@plotnua\.ie", live["notify_email"]): sys.exit("REFUSED: checkout_live.notify_email must be a plotnua.ie address")
    out = setvar(out, "CHECKOUT_PILOT_ENABLED", "true")
    out = setvar(out, "CHECKOUT_ORIGIN", live["checkout_origin"])
    add = '\n'.join('%s = %s' % (k, json.dumps(v)) for k, v in (("CHECKOUT_LIVE", "true"), ("CHECKOUT_MAIL", "resend"),
                                                               ("CHECKOUT_MAIL_APPROVED", "true"), ("CHECKOUT_MAIL_FROM", live["mail_from"]), ("CHECKOUT_NOTIFY_EMAIL", live["notify_email"])))
    out, n = re.subn(r'^(CHECKOUT_PILOT_ENABLED\s*=.*)$', lambda m: m.group(1) + "\n" + add, out, count=1, flags=re.M)
    if n != 1: sys.exit("REFUSED: could not place the live checkout settings")
cfg = tomllib.loads(out)
v = cfg["vars"]
assert v["CHECKOUT_PILOT_ENABLED"] == ("true" if live else "false") and v.get("CHECKOUT_LIVE", "false") == ("true" if live else "false")
assert "SANDBOX" not in v and "STRIPE_API_BASE" not in v and "CHECKOUT_MAIL_TEST_RECIPIENTS" not in v
assert cfg["vars"]["ENVIRONMENT"] == "production" and cfg["d1_databases"][0]["database_id"] == val["STUDIO_D1_DATABASE_ID"]
assert cfg["vars"]["ACCESS_AUD"] and cfg["vars"]["ACCESS_TEAM_DOMAIN"], "Access must never be empty in production"
open(os.path.join(W, "wrangler.production.toml"), "w").write(out)
print("production configuration rendered" + (" (LIVE checkout ENABLED)" if live else ""))
