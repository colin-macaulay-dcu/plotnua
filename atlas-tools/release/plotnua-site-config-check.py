#!/usr/bin/env python3
"""plotnua-site wrangler.toml guard (A4/A5 preparation, 28 Nov 2026).

    python3 atlas-tools/release/plotnua-site-config-check.py worker/plotnua-site/wrangler.toml staging|production

Fails (exit 1) unless the configuration is safe for the named target:
  both        no route, routes or custom_domain anywhere (top level or any env): plotnua.ie and www.plotnua.ie are attached
              as Custom Domains in the Cloudflare dashboard at the approved A4 checkpoint, and a deploy never declares or
              removes them;
  staging     [env.staging] names a DIFFERENT Worker ("plotnua-site-staging"), workers_dev = true, INDEXING = "noindex",
              so a test deploy can never replace what plotnua.ie serves;
  production  top-level name "plotnua-site", INDEXING = "index", and (once plotnua_host is "worker") workers_dev = false.
"""
import json, sys, tomllib
from pathlib import Path

def fail(m):
    print("FAIL  " + m); sys.exit(1)

def walk_routes(d, where):
    for k, v in d.items():
        if k in ("route", "routes", "custom_domain"):
            fail(f"{where}{k} is declared: domains are attached in the dashboard, never by a deploy")
        if k == "env" and isinstance(v, dict):
            for e, ev in v.items():
                walk_routes(ev, f"env.{e}.")

def main(path, target):
    cfg = tomllib.loads(Path(path).read_text())
    walk_routes(cfg, "")
    if cfg.get("name") != "plotnua-site":
        fail("the production Worker must be named plotnua-site")
    st = cfg.get("env", {}).get("staging", {})
    if target == "staging":
        if st.get("name") in (None, "plotnua-site") or not st.get("name", "").endswith("-staging"):
            fail("[env.staging] must name a separate *-staging Worker")
        if st.get("workers_dev") is not True:
            fail("staging must be on workers.dev")
        if st.get("vars", {}).get("INDEXING") != "noindex":
            fail("staging must be noindexed")
        if st.get("assets", {}).get("directory") != cfg.get("assets", {}).get("directory"):
            fail("staging must serve the same build")
    elif target == "production":
        if cfg.get("vars", {}).get("INDEXING") != "index":
            fail("plotnua.ie must be indexable")
        flags = json.loads((Path(path).resolve().parents[2] / "atlas-tools/release/flags.json").read_text())
        if flags.get("plotnua_host") == "worker" and cfg.get("workers_dev") is not False:
            fail("plotnua_host is worker but workers_dev is not false")
    else:
        fail("target must be staging or production")
    print(f"PASS  plotnua-site configuration is safe for {target}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    main(sys.argv[1], sys.argv[2])
