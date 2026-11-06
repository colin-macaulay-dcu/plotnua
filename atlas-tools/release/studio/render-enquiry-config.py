#!/usr/bin/env python3
"""Render the enquiry relay Worker's production Wrangler configuration (F2, 6 Nov 2026), on the pattern of render-config.py:
the D1 identifier comes from the GitHub environment variable STUDIO_D1_DATABASE_ID (never in the public repository) and the
live behaviour switches from worker/plotart-studio/enquiry-production.json. wrangler.enquiry.toml itself keeps shipping
CLOSED (that file is what activate.sh deploys); this renderer is the only route to the production settings. Writes
wrangler.enquiry.production.toml and prints nothing about the identifier.
    python3 render-enquiry-config.py <worker dir>"""
import json, os, re, sys, tomllib
W = sys.argv[1]
db = os.environ.get("STUDIO_D1_DATABASE_ID", "").strip()
if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", db):
    sys.exit("REFUSED: environment variable STUDIO_D1_DATABASE_ID is missing or not in the expected form")
src = open(os.path.join(W, "wrangler.enquiry.toml")).read()
prod = json.load(open(os.path.join(W, "enquiry-production.json")))
allowed = {"ENQUIRIES_ENABLED": ("true", "false"), "MAILER": ("resend", "none"), "GARDEN_ENQUIRIES_ENABLED": ("true", "false")}
if set(prod["vars"]) != set(allowed):
    sys.exit("REFUSED: enquiry-production.json must set exactly %s" % ", ".join(sorted(allowed)))
def setvar(text, key, value):
    out, n = re.subn(r'^(%s\s*=\s*)"[^"]*"' % re.escape(key), lambda m: m.group(1) + json.dumps(value), text, count=1, flags=re.M)
    if n != 1: sys.exit("REFUSED: %s not found in wrangler.enquiry.toml" % key)
    return out
out = setvar(src, "database_id", db)
for k, v in prod["vars"].items():
    if v not in allowed[k]: sys.exit("REFUSED: %s=%r is not an allowed value" % (k, v))
    out = setvar(out, k, v)
cfg = tomllib.loads(out)
assert cfg["name"] == "plotart-enquiry" and cfg["main"] == "src/enquiry.js"
assert cfg["vars"]["ORIGIN"] == "https://plotnua.ie" and cfg["vars"]["ENVIRONMENT"] == "production"
assert cfg["d1_databases"][0]["database_name"] == "plotart-studio" and cfg["d1_databases"][0]["database_id"] == db
open(os.path.join(W, "wrangler.enquiry.production.toml"), "w").write(out)
# what the deploy will set, for relay-settings.mjs to compare with the live Worker (runner only; never committed)
json.dump({"vars": cfg["vars"], "d1": {b["binding"]: b["database_id"] for b in cfg["d1_databases"]}, "secrets_required": prod.get("secrets_required", [])},
          open(os.path.join(W, "enquiry-expected.json"), "w"))
v = cfg["vars"]
print("enquiry relay configuration rendered (ENQUIRIES_ENABLED=%s, MAILER=%s, GARDEN_ENQUIRIES_ENABLED=%s)" % (v["ENQUIRIES_ENABLED"], v["MAILER"], v["GARDEN_ENQUIRIES_ENABLED"]))
