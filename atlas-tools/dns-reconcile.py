#!/usr/bin/env python3
"""plotnua.ie DNS reconciliation (prepared 27 Nov 2026) for a future move of the zone from Blacknight to Cloudflare.
Read-only: changes nothing anywhere. No nameserver change without the founder's explicit approval.

  python3 atlas-tools/dns-reconcile.py live  [--out dns-live.json]      public DNS today (DNS over HTTPS), names below
  python3 atlas-tools/dns-reconcile.py check <blacknight-zone-file> [--live dns-live.json] [--cloudflare <cf-export>]

check reads the Blacknight zone export (BIND format) and, for every record:
  * classifies it (Google Workspace mail, Resend, SPF, DKIM, DMARC, site verification, GitHub Pages, other);
  * says how it must exist on Cloudflare: DNS only (grey cloud) for every mail, verification and GitHub Pages record
    (Pages must stay DNS only so GitHub can renew its certificate and remain the tested fallback);
  * compares it with public DNS today, so nothing that answers today is missing from the export, and with a Cloudflare
    export (after Cloudflare's import scan) so nothing is lost, added or proxied by mistake;
  * checks the mail authentication essentials: exactly one SPF at the apex, DMARC present, Google and Resend DKIM
    present, MX present, no CNAME sharing a name with other records, no DNSSEC DS left at the registrar.
Exit 1 if anything needs attention before a nameserver change.
"""
import json, re, sys, urllib.request

ZONE = 'plotnua.ie'
NAMES = ['', 'www', '_dmarc', 'google._domainkey', 'resend._domainkey', 'send', 'mail', 'autodiscover', 'em', 'bounce',
         'k1._domainkey', 's1._domainkey', 's2._domainkey', 'selector1._domainkey', 'selector2._domainkey', 'calendar',
         'drive', 'sites', 'docs', '_github-pages-challenge-colin-macaulay-dcu']
TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'CAA', 'NS', 'DS', 'SRV']
TYPE_NO = {1: 'A', 2: 'NS', 5: 'CNAME', 15: 'MX', 16: 'TXT', 28: 'AAAA', 33: 'SRV', 43: 'DS', 257: 'CAA'}


def fqdn(name):
    return ZONE if name in ('', '@') else f'{name}.{ZONE}'


def doh(name, rtype):
    req = urllib.request.Request(f'https://cloudflare-dns.com/dns-query?name={name}&type={rtype}', headers={'accept': 'application/dns-json'})
    d = json.load(urllib.request.urlopen(req, timeout=10))
    # keep only answers owned by the name itself (a CNAME's target answers are not records of this zone)
    return [(TYPE_NO.get(a['type'], str(a['type'])), a['data']) for a in d.get('Answer', []) if a['name'].rstrip('.') == name]


def live():
    out = {}
    for n in NAMES:
        for t in TYPES:
            for typ, data in doh(fqdn(n), t):
                if typ == t:
                    out.setdefault(fqdn(n), set()).add((typ, data.strip()))
    return {k: sorted(v) for k, v in out.items()}


def parse_zone(text):
    """Minimal BIND parser: $ORIGIN/$TTL, owner inheritance, parentheses, quoted TXT strings."""
    text = re.sub(r';[^\n"]*(?=\n)', '', text)
    text = re.sub(r'\(([^)]*)\)', lambda m: m.group(1).replace('\n', ' '), text, flags=re.S)
    origin, last, recs = ZONE + '.', None, []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith('$ORIGIN'):
            origin = line.split()[1]; continue
        if line.startswith('$'):
            continue
        toks = re.findall(r'"(?:[^"\\]|\\.)*"|\S+', line)
        if line[0] in ' \t':
            owner = last
        else:
            owner = toks.pop(0)
        owner = origin.rstrip('.') if owner == '@' else (owner.rstrip('.') if owner.endswith('.') else f'{owner}.{origin}'.rstrip('.'))
        last = owner
        while toks and (toks[0].isdigit() or toks[0].upper() in ('IN', 'CH')):
            toks.pop(0)
        if not toks:
            continue
        typ, data = toks[0].upper(), ' '.join(toks[1:])
        if typ == 'TXT':
            data = ' '.join(re.findall(r'"(?:[^"\\]|\\.)*"', data)) or data
        recs.append((owner.lower(), typ, data.strip()))
    return recs


def classify(owner, typ, data):
    d = data.lower()
    if typ == 'NS' and owner == ZONE: return 'registrar nameservers (replaced by Cloudflare at the approved change)', None
    if typ == 'SOA': return 'zone authority (Cloudflare creates its own)', None
    if typ == 'MX' and 'google' in d: return 'Google Workspace mail', 'DNS only'
    if 'v=spf1' in d: return 'SPF (mail authentication)', 'DNS only'
    if owner.startswith('_dmarc.'): return 'DMARC (mail authentication)', 'DNS only'
    if owner.startswith('google._domainkey'): return 'Google Workspace DKIM', 'DNS only'
    if owner.startswith('resend._domainkey') or owner.startswith('send.') or 'rmta.net' in d or 'amazonses' in d:
        return 'Resend (transactional email)', 'DNS only'
    if '._domainkey.' in owner: return 'DKIM (other sender)', 'DNS only'
    if 'verification' in d or owner.startswith('_github-pages-challenge'): return 'site / service verification', 'DNS only'
    if typ in ('A', 'AAAA') and d.startswith(('185.199.', '2606:50c0:')): return 'GitHub Pages (website, fallback)', 'DNS only'
    if typ == 'CNAME' and 'github.io' in d: return 'GitHub Pages (website, fallback)', 'DNS only'
    if typ == 'CAA': return 'certificate authority policy', 'DNS only'
    return 'other: review', 'review'


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('live', 'check'):
        sys.exit(__doc__)
    arg = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    if sys.argv[1] == 'live':
        snap = live()
        out = arg('--out')
        if out: json.dump(snap, open(out, 'w'), indent=1)
        for k, v in snap.items():
            for t, d in v: print(f'{k:40} {t:6} {d[:110]}')
        return
    recs = parse_zone(open(sys.argv[2], encoding='utf-8', errors='replace').read())
    snap = json.load(open(arg('--live'))) if arg('--live') else live()
    problems, rows = [], []
    for owner, typ, data in recs:
        what, mode = classify(owner, typ, data)
        rows.append((owner, typ, data, what, mode))
    print(f'{"name":36} {"type":6} {"on Cloudflare":14} {"what":44} value')
    for owner, typ, data, what, mode in rows:
        print(f'{owner:36} {typ:6} {mode or "-":14} {what:44} {data[:80]}')
        if mode == 'review': problems.append(f'review {owner} {typ} {data[:60]}')
    norm = lambda s: re.sub(r'"\s+"', '', s.strip().rstrip('.').lower()).replace('"', '')
    have = {(o, t, norm(d)) for o, t, d in recs}
    for name, items in snap.items():
        for t, d in items:
            if t in ('NS', 'DS'): continue
            if (name, t, norm(d)) not in have:
                problems.append(f'MISSING from the export but answering today: {name} {t} {d[:70]}')
    apex_spf = [d for o, t, d in recs if o == ZONE and t == 'TXT' and 'v=spf1' in d.lower()]
    if len(apex_spf) != 1: problems.append(f'apex must have exactly one SPF record (found {len(apex_spf)})')
    for need, test in (('MX at the apex', lambda o, t, d: o == ZONE and t == 'MX'),
                       ('DMARC', lambda o, t, d: o == '_dmarc.' + ZONE and t == 'TXT'),
                       ('Google DKIM', lambda o, t, d: o == 'google._domainkey.' + ZONE),
                       ('Resend DKIM', lambda o, t, d: o == 'resend._domainkey.' + ZONE)):
        if not any(test(*r) for r in recs): problems.append(f'{need} not found in the export')
    by = {}
    for o, t, d in recs: by.setdefault(o, set()).add(t)
    for o, ts in by.items():
        if 'CNAME' in ts and len(ts) > 1: problems.append(f'{o}: CNAME shares its name with {sorted(ts - {"CNAME"})} (invalid; Cloudflare will refuse)')
    if snap.get(ZONE) and any(t == 'DS' for t, _ in snap[ZONE]): problems.append('DNSSEC DS record present at the registrar: remove it before any nameserver change')
    cf = arg('--cloudflare')
    if cf:
        crecs = parse_zone(open(cf, encoding='utf-8', errors='replace').read())
        chave = {(o, t, norm(d)) for o, t, d in crecs if t not in ('NS', 'SOA')}
        bl = {(o, t, norm(d)) for o, t, d in recs if t not in ('NS', 'SOA')}
        for r in sorted(bl - chave): problems.append(f'Cloudflare is MISSING {r[0]} {r[1]} {r[2][:60]}')
        for r in sorted(chave - bl): problems.append(f'Cloudflare has an EXTRA record {r[0]} {r[1]} {r[2][:60]}')
    print()
    for p in problems: print('ATTENTION ', p)
    print(f'DNS RECONCILIATION · {len(recs)} records · {len(problems)} item(s) needing attention')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
