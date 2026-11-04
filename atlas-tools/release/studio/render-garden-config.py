#!/usr/bin/env python3
"""Render The Borrowed Garden noticeboard intake Worker's production Wrangler configuration (4 Nov 2026), on the pattern of
render-config.py: the D1 identifier comes from the GitHub environment variable STUDIO_D1_DATABASE_ID (never in the
public repository), and GARDEN_ENABLED from the deploy workflow's own input ("true" only when the founder approves
opening the noticeboard). Writes wrangler.garden.production.toml and prints nothing about the identifier.
    python3 render-garden-config.py <worker dir> <true|false>"""
import json, os, re, sys, tomllib
W, enabled = sys.argv[1], sys.argv[2]
if enabled not in ("true", "false"):
    sys.exit("REFUSED: GARDEN_ENABLED must be true or false")
db = os.environ.get("STUDIO_D1_DATABASE_ID", "").strip()
if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", db):
    sys.exit("REFUSED: environment variable STUDIO_D1_DATABASE_ID is missing or not in the expected form")
src = open(os.path.join(W, "wrangler.garden.toml")).read()
def setvar(text, key, value):
    out, n = re.subn(r'^(%s\s*=\s*)"[^"]*"' % re.escape(key), lambda m: m.group(1) + json.dumps(value), text, count=1, flags=re.M)
    if n != 1: sys.exit("REFUSED: %s not found in wrangler.garden.toml" % key)
    return out
out = setvar(setvar(src, "database_id", db), "GARDEN_ENABLED", enabled)
cfg = tomllib.loads(out)
assert cfg["name"] == "plotnua-garden-board" and cfg["main"] == "src/garden.js"
assert cfg["vars"]["ORIGIN"] == "https://plotnua.ie" and cfg["vars"]["ENVIRONMENT"] == "production"
assert cfg["d1_databases"][0]["database_name"] == "plotart-studio" and cfg["d1_databases"][0]["database_id"] == db
open(os.path.join(W, "wrangler.garden.production.toml"), "w").write(out)
print("Borrowed Garden intake configuration rendered (GARDEN_ENABLED=%s)" % enabled)
