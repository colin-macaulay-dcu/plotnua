#!/usr/bin/env python3
"""Offline tests for wrangler-error.py: shows Wrangler's reason and code, and withholds everything when unsure."""
import os, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, "..", "wrangler-error.py")
ESC = "\x1b[31m✘ \x1b[41;31m[\x1b[41;97mERROR\x1b[41;31m]\x1b[0m "
TOKEN, SK, WH = "cfut_" + "Q" * 40, "sk_test_" + "a1B2" * 10, "whsec_" + "Z9" * 16
def run(text, **env):
    d = tempfile.mkdtemp(); p = os.path.join(d, "w.log")
    if text is not None: open(p, "w").write(text)
    e = {k: v for k, v in os.environ.items() if not k.endswith(("TOKEN", "SECRET", "KEY"))}; e.update(env)
    r = subprocess.run([sys.executable, T, p], env=e, capture_output=True, text=True); return r.returncode, r.stdout
ok = []
def case(n, c, o=""): ok.append(c); print(("PASS" if c else "FAIL") + "  " + n + ("" if c else "  [" + o[:300] + "]"))
base = ESC + "A request to the Cloudflare API (/accounts/a410c6980febb4e8ee5c13d6248c9763/workers/scripts/plotart-studio-test) failed.\n\n  Binding R2 bucket not found in the eu jurisdiction [code: 10085]\n\nIf you think this is a bug, please open an issue.\n"
rc, o = run(base, CLOUDFLARE_API_TOKEN=TOKEN, STRIPE_SECRET_KEY=SK, STRIPE_WEBHOOK_SECRET=WH, FOUNDER_EMAILS="colin@plotnua.ie")
case("reason and code shown; account ID masked; colours stripped", rc == 0 and "[code: 10085]" in o and "a410c698" not in o and "\x1b" not in o and "/accounts/[account]" in o, o)
rc, o = run(base + "  token=" + TOKEN + "\n", CLOUDFLARE_API_TOKEN=TOKEN)
case("the API token value anywhere in the log → everything withheld", "withheld" in o and TOKEN not in o and "10085" not in o, o)
rc, o = run(ESC + "bad key " + SK + "\n\n", STRIPE_SECRET_KEY=SK)
case("the Stripe key value in the log → withheld", "withheld" in o and SK not in o, o)
rc, o = run(ESC + "secret " + WH + "\n\n", STRIPE_WEBHOOK_SECRET=WH)
case("the webhook secret value in the log → withheld", "withheld" in o and WH not in o, o)
rc, o = run(ESC + "user colin@plotnua.ie not allowed\n\n", FOUNDER_EMAILS="colin@plotnua.ie,other@plotnua.ie")
case("a founder address from FOUNDER_EMAILS in the log → withheld", "withheld" in o and "colin@plotnua.ie" not in o, o)
rc, o = run(ESC + "unknown key sk_live_" + "x" * 30 + "\n\n")
case("a Stripe-shaped key not in the environment → withheld", "withheld" in o and "sk_live" not in o, o)
rc, o = run(ESC + "Authorization: Bearer abc.def\n\n")
case("a bearer value is redacted", "abc.def" not in o and ("[redacted]" in o or "withheld" in o), o)
rc, o = run(ESC + "api_token=shortvalue1 failed\n\n")
case("token=… values are redacted", "shortvalue1" not in o, o)
rc, o = run(ESC + "blob " + "Ab3+/" * 8 + "\n\n")
case("a long base64-like string → redacted or withheld", "Ab3+/Ab3+/" not in o, o)
rc, o = run(None); case("missing log → fixed notice, exit 0", rc == 0 and "no log" in o, o)
rc, o = run("all fine\n"); case("no error block → fixed notice", rc == 0 and "no error block" in o, o)
rc, o = run(ESC + "x\n" + "\n".join(f"line {i}" for i in range(40))); case("block capped at 16 lines", o.count("  | ") <= 16, o)
print(f"WRANGLER ERROR SANITISER · {sum(ok)}/{len(ok)} passed"); sys.exit(0 if all(ok) else 1)
