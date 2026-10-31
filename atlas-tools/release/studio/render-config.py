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
for k, v in prod["vars"].items():
    out = setvar(out, k, v)
cfg = tomllib.loads(out)
assert cfg["vars"]["ENVIRONMENT"] == "production" and cfg["d1_databases"][0]["database_id"] == val["STUDIO_D1_DATABASE_ID"]
assert cfg["vars"]["ACCESS_AUD"] and cfg["vars"]["ACCESS_TEAM_DOMAIN"], "Access must never be empty in production"
open(os.path.join(W, "wrangler.production.toml"), "w").write(out)
print("production configuration rendered")
