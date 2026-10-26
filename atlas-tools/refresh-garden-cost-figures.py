#!/usr/bin/env python3
"""Maintain only the existing garden comparison's evidence list.

The legacy layout builder stays locked on Premium pages. This updater imports
its pure figure renderer but never invokes its layout-writing modes. Apply
requires an exact match to HEAD's evidence list; every byte outside that list
is preserved. Run --check in CI, or --apply after regenerating cost evidence.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / 'discovery-living-in-the-garden.html'
EVIDENCE = 'atlas-tools/cluster1-cost-evidence.json'


def rewrite(page, old, new):
    if old == new:
        if page.count(new) != 1:
            raise ValueError('the current evidence list must occur exactly once')
        return page
    if page.count(new) == 1 and page.count(old) == 0:
        return page
    if page.count(old) != 1 or page.count(new) != 0:
        raise ValueError('the page must contain HEAD evidence exactly once and no new list')
    before, after = page.split(old)
    return before + new + after


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else '--check' if len(sys.argv) == 1 else None
    if mode not in ('--check', '--apply'):
        raise ValueError('use --check or --apply')
    spec = importlib.util.spec_from_file_location('garden_cost_renderer', ROOT/'atlas-tools/build-cluster1-garden-authority.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    current = json.loads((ROOT/EVIDENCE).read_text())
    new = renderer.figure_rows(current)
    page = PAGE.read_text()
    if mode == '--check':
        if page.count(new) != 1:
            raise ValueError('the page does not carry current evidence exactly once')
        print('GARDEN COST FIGURES · CHECK OK — evidence list matches; no layout written')
        return
    old_raw = subprocess.check_output(['git','show','HEAD:'+EVIDENCE], cwd=ROOT, text=True)
    old = renderer.figure_rows(json.loads(old_raw))
    out = rewrite(page, old, new)
    if out != page:
        PAGE.write_text(out)
    print('GARDEN COST FIGURES · APPLY OK — only the evidence list refreshed')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit('REFUSED: '+str(exc))
