#!/usr/bin/env python3
"""Borrowed Garden register pause check (4 Nov 2026). Refuses unless the register Worker's wrangler.toml keeps BOTH
registers closed and carries no Airtable setting (those stay on the Worker, preserved by `wrangler deploy --keep-vars`).
    python3 atlas-tools/release/garden-register-pause-check.py worker/garden-register/wrangler.toml"""
import sys, tomllib
cfg = tomllib.loads(open(sys.argv[1], encoding="utf-8").read())
v = cfg.get("vars", {})
problems = []
if cfg.get("name") != "plotnua-garden-register": problems.append("the Worker is not plotnua-garden-register")
if cfg.get("main") != "src/index.js": problems.append("unexpected entry module")
for k in ("WRITES_ENABLED", "GROWER_WRITES_ENABLED", "EMAIL_ENABLED"):
    if v.get(k) != "false": problems.append('%s must be "false" (is %r)' % (k, v.get(k)))
for k in v:
    if k.upper().startswith("AIRTABLE"): problems.append("%s must not be in wrangler.toml (it would replace the stored setting)" % k)
for section in ("routes", "route", "d1_databases", "kv_namespaces"):
    if section in cfg: problems.append("unexpected %s in the configuration" % section)
if problems:
    print("REFUSED:\n- " + "\n- ".join(problems)); sys.exit(1)
print("REGISTER PAUSE CHECK OK · WRITES_ENABLED, GROWER_WRITES_ENABLED and EMAIL_ENABLED all \"false\" · no Airtable setting in the file (kept on the Worker by --keep-vars)")
