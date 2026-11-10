#!/usr/bin/env python3
"""SEARCH V1 · MOBILE LATENCY BENCHMARK (Amendment A4, founder approval 10 Nov 2026). Read-only.

Measures what a visitor feels on a slow phone: the per-keystroke cost of search.js's own search()
over the committed search-index-v1.json, in Chromium with mobile emulation (390 x 844) and CDP CPU
throttling (default 6x). The query set includes the one- and two-character prefixes that match
almost every record, which are the slowest keystrokes.

A4 early warning: 95th-percentile query time above 100 ms at 6x, taking the WORSE of the warmed
runs and the cold first pass (an unwarmed engine, as on a visitor's first keystrokes), means an architecture review
(Option C, a sharded index) is due. This tool reports; it never changes a file and never fails
a build. It is local tooling (Playwright and Chromium), not a CI gate.

    python3 atlas-tools/bench-search-mobile.py [--rate 6] [--runs 5] [--json out.json]
"""
import argparse, functools, http.server, json, pathlib, statistics, sys, threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
WARN_P95_MS = 100.0
QUERIES = (list("gsahcpflbtwmr") +
           ["ga", "gar", "sa", "sh", "lo", "ca", "po", "ho", "fl", "so", "un", "wa"] +
           ["garden room", "garden room under €30,000", "sauna", "log cabin", "solar battery",
            "flood barrier", "home lift", "underground", "shelter", "planning", "garden office",
            "powersheds", "hot tub", "treehouse", "pergola"])

PAGE = """<!doctype html><meta charset=utf-8><script src="/search.js"></script><script>
window.bench = async (queries, runs) => {
  const ix = await (await fetch('/search-index-v1.json', {cache: 'no-store'})).json();
  const cold = [];                                                // first pass: an unwarmed engine, like a visitor's first keystrokes
  for (const q of queries) { const a = performance.now(); PlotNuaSearch.search(ix, q); cold.push(performance.now() - a); }
  const per = {}; const all = [];
  for (let k = 0; k < runs; k++) for (const q of queries) {
    const a = performance.now(); PlotNuaSearch.search(ix, q); const t = performance.now() - a;
    (per[q] = per[q] || []).push(t); all.push(t);
  }
  return {records: ix.records.length, all, per, cold};
};
</script>"""


class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/__bench"):
            b = PAGE.encode(); self.send_response(200); self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b); return
        if self.path.split("?")[0] not in ("/search.js", "/search-index-v1.json"):
            self.send_error(404); return
        super().do_GET()

    def log_message(self, *a):
        pass


def pct(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rate", type=float, default=6)
    ap.add_argument("--runs", type=int, default=5); ap.add_argument("--json")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/__bench" % srv.server_address[1]
    with sync_playwright() as p:
        b = p.chromium.launch()
        c = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = c.new_page(); cdp = c.new_cdp_session(pg)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": a.rate})
        pg.goto(url); r = pg.evaluate("([q, n]) => bench(q, n)", [QUERIES, a.runs]); b.close()
    srv.shutdown()
    allt = r["all"]; short = [t for q in QUERIES if len(q) <= 2 for t in r["per"][q]]
    out = {"cpu_throttle": a.rate, "records": r["records"], "queries": len(QUERIES), "runs": a.runs,
           "median_ms": round(statistics.median(allt), 1), "p95_ms": round(pct(allt, 0.95), 1),
           "max_ms": round(max(allt), 1),
           "cold_first_pass_median_ms": round(statistics.median(r["cold"]), 1),
           "cold_first_pass_p95_ms": round(pct(r["cold"], 0.95), 1),
           "cold_first_pass_max_ms": round(max(r["cold"]), 1),
           "short_prefix_median_ms": round(statistics.median(short), 1), "short_prefix_p95_ms": round(pct(short, 0.95), 1),
           "slowest": sorted(((round(statistics.median(v), 1), q) for q, v in r["per"].items()), reverse=True)[:6],
           "warn_p95_ms": WARN_P95_MS}
    print("SEARCH MOBILE BENCH · %dx CPU · %d records · median %.1f ms · p95 %.1f ms · 1-2 char p95 %.1f ms"
          % (a.rate, out["records"], out["median_ms"], out["p95_ms"], out["short_prefix_p95_ms"]))
    print("  cold first pass (unwarmed engine): median %.1f ms · p95 %.1f ms · max %.1f ms"
          % (out["cold_first_pass_median_ms"], out["cold_first_pass_p95_ms"], out["cold_first_pass_max_ms"]))
    print("  slowest (median ms, query):", out["slowest"])
    worst_p95 = max(out["p95_ms"], out["cold_first_pass_p95_ms"])
    out["a4_trigger_p95_ms"] = worst_p95
    if worst_p95 > WARN_P95_MS:
        print("  WARNING A4 early warning: p95 %.1f ms > %.0f ms at %gx (worse of warm and cold). Plan Option C." % (worst_p95, WARN_P95_MS, a.rate))
    else:
        print("  A4 latency trigger not reached (p95 <= %.0f ms at %gx)." % (WARN_P95_MS, a.rate))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
