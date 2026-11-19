#!/usr/bin/env python3
"""Print the error block of a failed Wrangler run for the TEST checkout deployment, or nothing sensitive at all.

Usage: wrangler-error.py <wrangler.log>      (always exits 0; it only reports)

Fail closed: the block is cleaned (colours stripped; account IDs, bearer values, token/secret/key/password values and any
long token-like strings redacted), then checked again. If any line still looks sensitive, or if any credential value
present in this process's environment (CLOUDFLARE_API_TOKEN, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, FOUNDER_EMAILS and
any *_TOKEN / *_SECRET / *_KEY variable) appears anywhere in the log, NOTHING from the log is printed: only a fixed notice."""
import os, re, sys

WITHHELD = "  | (Wrangler's error details withheld: they could not be shown safely; nothing from the log is printed)"
ANSI = re.compile(r"\x1B\[[0-9;?]*[A-Za-z]")
REDACT = [
    (re.compile(r"\b(Bearer|Basic)\s+\S+", re.I), r"\1 [redacted]"),
    (re.compile(r"((?:api[_-]?)?(?:token|secret|password|passwd|key|authorization|cookie)\s*[:=]\s*)\S+", re.I), r"\1[redacted]"),
    (re.compile(r"/accounts/[0-9a-f]{32}"), "/accounts/[account]"),
    (re.compile(r"\b[0-9a-f]{32}\b"), "[id]"),
    (re.compile(r"[A-Za-z0-9_\-]{28,}"), "[redacted]"),
]
CREDENTIAL_SHAPES = re.compile(r"\b(sk|rk|pk)_(test|live)_|\bwhsec_|\bre_[A-Za-z0-9]{8,}|-----BEGIN|\bcfut_|\bghp_|\bgithub_pat_", re.I)
STILL_SENSITIVE = re.compile(r"Bearer\s+(?!\[redacted\])|(?=[A-Za-z0-9+/=_]*\d)(?=[A-Za-z0-9+/=_]*[A-Za-z])[A-Za-z0-9+/=_]{24,}", re.I)


def secrets_from_env():
    vals = []
    for k, v in os.environ.items():
        if v and len(v) >= 8 and (k in ("CLOUDFLARE_API_TOKEN", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "FOUNDER_EMAILS")
                                  or re.search(r"(TOKEN|SECRET|KEY|PASSWORD)$", k)):
            vals.append(v)
            vals.extend(x for x in re.split(r"[,\s]+", v) if len(x) >= 8)   # each address in a list, too
    return vals


def main(path):
    try: raw = open(path, encoding="utf-8", errors="replace").read()
    except Exception: print("  | (Wrangler wrote no log)"); return
    if any(s in raw for s in secrets_from_env()): print(WITHHELD); return
    lines, block, blanks = ANSI.sub("", raw).splitlines(), [], 0
    for ln in lines:
        if not block and not re.search(r"✘|\[ERROR\]", ln): continue
        block.append(ln)
        if not ln.strip():
            blanks += 1
            if blanks >= 2: break
        if len(block) >= 16: break
    if not block: print("  | (no error block found in the Wrangler log)"); return
    if any(CREDENTIAL_SHAPES.search(ln) for ln in block): print(WITHHELD); return   # a credential-shaped value: show nothing
    clean = []
    for ln in block:
        for pat, rep in REDACT: ln = pat.sub(rep, ln)
        clean.append(ln)
    if any(STILL_SENSITIVE.search(ln) for ln in clean): print(WITHHELD); return
    print("\n".join("  | " + ln for ln in clean))


if __name__ == "__main__":
    try: main(sys.argv[1] if len(sys.argv) > 1 else "")
    except Exception: print(WITHHELD)
    sys.exit(0)
