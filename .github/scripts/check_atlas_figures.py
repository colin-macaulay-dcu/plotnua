#!/usr/bin/env python3
"""
PlotNua — homepage Atlas figures: AGREEMENT GUARD.

    check_atlas_figures.py          exit 0 agree   exit 1 diverged

Compares two files that are already in the repository and nothing else. It
reads no third source, contacts no API, needs no token and writes nothing.

WHY IT EXISTS. The homepage figures are generated: atlas_stats.py reads Atlas,
writes the numbers into index.html and records them in atlas-stats.json, and
the workflow commits the two together. That mechanism cannot produce a
disagreement. A person can — by editing a number in index.html by hand, in
good faith, to "correct" it. This guard makes that edit fail instead of
quietly shipping a figure the Atlas never produced.

It deliberately imports METRICS, ATTRS and DTS from atlas_stats rather than
restating them. One definition of the anchors, in the generator that owns
them: if they move, the guard follows, and there is no second place to forget.

IT DOES NOT CHECK WHETHER THE FIGURES ARE CURRENT. Freshness is the scheduled
workflow's job. This answers one question only: does the page agree with the
generated record it came from?
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas_stats as gen          # noqa: E402  (constants only; no side effects)


def main() -> int:
    if not gen.STATS.exists():
        print(f"::error::{gen.STATS.name} not found — nothing to check against.")
        return 1
    if not gen.INDEX.exists():
        print(f"::error::{gen.INDEX.name} not found.")
        return 1

    try:
        counts = json.loads(gen.STATS.read_text(encoding="utf-8")).get("counts", {})
    except Exception as e:
        print(f"::error::{gen.STATS.name} is not readable JSON: {e}")
        return 1

    html = gen.INDEX.read_text(encoding="utf-8")
    problems: list[str] = []

    for key, m in gen.METRICS.items():
        entry = counts.get(key)
        n = entry.get("count") if isinstance(entry, dict) else entry
        if not isinstance(n, int) or isinstance(n, bool):
            problems.append(f"{m['label']}: {gen.STATS.name} has no integer count "
                            f"for '{key}' (found {n!r}).")
            continue

        # The two places the same number appears, found by the generator's own
        # anchors. The <dt> anchor also asserts the public label, so a guard
        # pass is also evidence the wording has not moved.
        attr = gen.ATTRS[key]
        sites = [
            (f'{attr}="…"',
             re.compile(r'(?:' + re.escape(attr) + r')="(\d+)"')),
            (f'<dt id="{gen.DTS[key]}"> with label "{m["label"]}"',
             re.compile(r'<dt id="' + re.escape(gen.DTS[key]) + r'">(\d+)</dt><dd>'
                        + re.escape(m["label"]) + r'</dd>')),
        ]

        for where, pat in sites:
            found = pat.findall(html)
            if len(found) != 1:
                problems.append(f"{m['label']}: expected exactly one {where} in "
                                f"{gen.INDEX.name}, found {len(found)}. The markup or "
                                f"the public label has moved.")
                continue
            if int(found[0]) != n:
                problems.append(f"{m['label']}: {gen.INDEX.name} shows {found[0]} at "
                                f"{where}, but {gen.STATS.name} records {n}.")

    if problems:
        for p in problems:
            print(f"::error::{p}")
        print("\nThe homepage Atlas figures are GENERATED. Do not edit them by hand:")
        print("re-run the Atlas statistics workflow, which writes index.html and")
        print("atlas-stats.json together. Nothing has been changed by this check.")
        return 1

    for key, m in gen.METRICS.items():
        entry = counts.get(key)
        print(f"  {m['label']:<16} {entry['count'] if isinstance(entry, dict) else entry}"
              f"  — agrees in both places")
    print("index.html agrees with atlas-stats.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
