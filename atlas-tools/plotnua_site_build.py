#!/usr/bin/env python3
"""Builds the plotnua.ie site for the plotnua-site Worker (prepared 27 Nov 2026, NOT in use: GitHub Pages serves plotnua.ie).

Publishes exactly what GitHub Pages publishes today, byte for byte, and nothing else (fail-closed):
  * candidate files = tracked files (git ls-files) that Jekyll would publish: not under a _config.yml "exclude" entry and
    not hidden by Jekyll's defaults (any path part starting with ".", "_", "#" or "~"; node_modules/, vendor/, Gemfile*).
    The site has no Jekyll templating (no front matter anywhere), so Jekyll copies these files unchanged.
  * every candidate must match worker/plotnua-site/publish-allowlist.txt, or the build FAILS and names the file: a private
    or unexpected file can never become public by accident, only by a reviewed allowlist line.
  * files are copied unchanged; _headers gives the files served without the Worker their security headers.

Usage: python3 atlas-tools/plotnua_site_build.py <repo-root> <out-dir> [--mode test|live]
Writes <out-dir>/.build-report.json (file count, bytes, the allowlist lines that matched nothing).
"""
import argparse, fnmatch, json, os, shutil, subprocess, sys

HIDDEN_PREFIXES = (".", "_", "#", "~")


def jekyll_excludes(root):
    out = []
    with open(os.path.join(root, "_config.yml"), encoding="utf-8") as f:
        inside = False
        for line in f:
            if line.startswith("exclude:"):
                inside = True
                continue
            if inside:
                s = line.strip()
                if s.startswith("- "):
                    out.append(s[2:].strip().strip("'\""))
                elif s and not s.startswith("#"):
                    inside = False
    return out


def jekyll_publishes(path, excludes):
    parts = path.split("/")
    if any(p.startswith(HIDDEN_PREFIXES) for p in parts):
        return False
    if parts[0] in ("node_modules", "vendor") or path in ("Gemfile", "Gemfile.lock"):
        return False
    for e in excludes:
        if (e.endswith("/") and path.startswith(e)) or path == e.rstrip("/") or path.startswith(e.rstrip("/") + "/"):
            return False
    return True


def allowlist(root):
    with open(os.path.join(root, "worker/plotnua-site/publish-allowlist.txt"), encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]


def candidates(root):
    files = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout.decode().split("\0")
    ex = jekyll_excludes(root)
    return sorted(f for f in files if f and jekyll_publishes(f, ex) and os.path.isfile(os.path.join(root, f)))


def build(root, out, mode):
    allow = allowlist(root)
    files = candidates(root)
    used, refused = set(), []
    for f in files:
        hit = next((p for p in allow if fnmatch.fnmatchcase(f, p) and ("/" in p or "/" not in f)), None)
        if hit is None:
            refused.append(f)
        else:
            used.add(hit)
    if refused:
        sys.exit("REFUSED: not on the publication allowlist (add a reviewed line to worker/plotnua-site/publish-allowlist.txt):\n  "
                 + "\n  ".join(refused[:50]))
    if os.path.exists(out):
        shutil.rmtree(out)
    total = 0
    for f in files:
        dest = os.path.join(out, f)
        os.makedirs(os.path.dirname(dest) or out, exist_ok=True)
        shutil.copyfile(os.path.join(root, f), dest)
        total += os.path.getsize(dest)
    head = ["  X-Content-Type-Options: nosniff", "  Strict-Transport-Security: max-age=31536000"]
    if mode == "test":
        head.append("  X-Robots-Tag: noindex, nofollow")
    with open(os.path.join(out, "_headers"), "w", encoding="utf-8") as f:
        f.write("".join(f"{rule}\n" + "\n".join(head) + "\n" for rule in ("/assets/*", "/plotart/assets/*", "/plotart/artists/*/img/*")))
    report = {"mode": mode, "files": len(files), "bytes": total, "largest": max((os.path.getsize(os.path.join(out, f)), f) for f in files),
              "allowlist_lines_unused": [p for p in allow if p not in used]}
    with open(os.path.join(out, ".build-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    with open(os.path.join(out, ".assetsignore"), "w", encoding="utf-8") as f:
        f.write(".build-report.json\n.assetsignore\n")
    return report, files


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("--mode", choices=("test", "live"), default="test")
    a = ap.parse_args()
    r, _ = build(a.root, a.out, a.mode)
    print(json.dumps(r, indent=1))
