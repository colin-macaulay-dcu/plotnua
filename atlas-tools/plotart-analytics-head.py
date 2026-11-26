#!/usr/bin/env python3
"""PlotArt · analytics head (SEO and analytics package, founder approval 26 Nov 2026, section 1.2).

Puts the one approved analytics block (plotart_shell.ANALYTICS_HEAD: Consent Mode v2 defaults, the existing Cookiebot
banner, the existing GA4 property with content_group 'PlotArt') directly after the viewport meta of every PlotArt page under
ROOT/plotart that does not carry it yet: the hand-built pages (home, About, Founding 25, Living Gallery, Mobile Gallery, the
Artists' Gallery, ...) and pages published before the block existed. The builders and the content pipeline write the same
block themselves (plotart_shell.artist_page, build-plotart-join.py, build-plotart-opportunities.py; the guides, collections
and calculator copy the homepage's head), so patched and generated pages cannot drift apart.

The four generated former-address redirect pages (build-plotart-galleries.py LEGACY) are left out on purpose: they redirect
immediately, are noindex and outside the sitemap, and a render-blocking consent script would only delay the redirect.

  python3 atlas-tools/plotart-analytics-head.py ROOT            apply
  python3 atlas-tools/plotart-analytics-head.py ROOT --check    exit 1 if any page lacks the block; change nothing

Idempotent. Strict: a page whose head does not open with charset + viewport, or which already carries another analytics or
consent script, stops the run with nothing written."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plotart_shell as S  # noqa: E402

REDIRECTS = ("environment/index.html", "landscape/index.html", "places-and-spaces/index.html", "portraiture/index.html")


def pages(base):
    for d, _, files in os.walk(base):
        for f in sorted(files):
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(d, f), base).replace(os.sep, "/")
                if rel not in REDIRECTS:
                    yield rel


def main(root, check=False):
    base = os.path.join(root, "plotart")
    plan, errors = [], []
    for rel in sorted(pages(base)):
        p = os.path.join(base, rel)
        text = open(p, encoding="utf-8").read()
        try:
            new = S.with_analytics(text)
        except ValueError as e:
            errors.append("%s: %s" % (rel, e))
            continue
        if new != text:
            plan.append((p, rel, new))
    if errors:
        print("REFUSED (nothing written):\n  " + "\n  ".join(errors))
        return 2
    if not check:
        for p, _rel, new in plan:
            open(p, "w", encoding="utf-8").write(new)
    total = sum(1 for _ in pages(base))
    print("PLOTART ANALYTICS HEAD · %d pages, %d %s%s" % (total, len(plan), "missing the block" if check else "patched",
                                                         (": " + ", ".join(r for _p, r, _n in plan[:12]) + (" …" if len(plan) > 12 else "")) if plan else ""))
    return 1 if (check and plan) else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], "--check" in sys.argv))
