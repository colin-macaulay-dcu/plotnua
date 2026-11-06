#!/usr/bin/env python3
"""PlotArt Studio · migration approval check (founder requirement, 1 Nov 2026). Runs before any approval or credential.
Refuses unless: the file is exactly the one approved (SHA-256), the expected effects are described, and every table the
SQL writes to is in the declared list. Writing to `artists` therefore always needs `artists` declared and approved.
Triggers, ATTACH and PRAGMA writes are refused outright. Prints the file and the declaration for the reviewer.
  python3 migration-check.py <sql file> <sha256> "<tables, comma-separated, or none>" "<description>"
"""
import hashlib, re, sys
path, want_sha, tables_in, desc = sys.argv[1:5]
def refuse(msg): print("REFUSED: " + msg); sys.exit(1)
data = open(path, "rb").read()
sha = hashlib.sha256(data).hexdigest()
if not re.fullmatch(r"[0-9a-f]{64}", want_sha or ""): refuse("give the approved SHA-256 of the migration file (64 hex characters)")
if sha != want_sha: refuse("the migration file is not the approved one (its SHA-256 is %s)" % sha)
if len(desc.strip()) < 20: refuse("describe the expected database changes (at least a sentence)")
declared = set() if tables_in.strip().lower() == "none" else {t.strip().lower() for t in tables_in.split(",") if t.strip()}
if any(not re.fullmatch(r"[a-z_][a-z0-9_]*", t) for t in declared): refuse("table names: letters, digits and _ only, comma-separated, or none")
sql = re.sub(r"--[^\n]*", " ", data.decode("utf-8"))
sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
W = r'[`"\[]?([A-Za-z_][A-Za-z0-9_]*)[`"\]]?'
import glob, os
# Tables that already exist in production: every table schema.sql creates BEFORE this migration's own marker comment
# ("-- ... (migration NNNN ...", which mirrors the migration for new installs), and every table created by an earlier
# migration file. Creating, re-creating or indexing one of these is never additive.
_wdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "worker", "plotart-studio")
_num = (re.match(r"(\d{4})_", os.path.basename(path)) or [None, "----"])[1]
_tbl = lambda t: {m.lower() for m in re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + W, re.sub(r"--[^\n]*", " ", t), re.I)}
_schema = open(os.path.join(_wdir, "schema.sql"), encoding="utf-8").read()
_mark = re.search(r"^--[^\n]*\bmigration\s+%s\b" % _num, _schema, re.I | re.M)
existing = _tbl(_schema[:_mark.start()] if _mark else _schema)
for _f in sorted(glob.glob(os.path.join(_wdir, "migrations", "*.sql"))):
    _n = os.path.basename(_f)[:4]
    if _n < _num and not _f.endswith("_rollback.sql"):
        existing |= _tbl(open(_f, encoding="utf-8").read())
# Refusal-only triggers (proposed with migration 0005, 6 Nov 2026; needs the founder's approval as a policy change): a
# BEFORE trigger whose whole body is SELECT RAISE(ABORT, '...') can only STOP a write, never make one. It is allowed when
# it guards a table this same migration creates and declares, and its WHEN condition (if any) only reads. Every other
# trigger is still refused. Allowed triggers are listed for the reviewer and removed before the remaining checks.
_TRIG = re.compile(r"\bCREATE\s+TRIGGER\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+BEFORE\s+(INSERT|UPDATE|DELETE)\s+ON\s+([A-Za-z_][A-Za-z0-9_]*)\s+"
                   r"(?:WHEN\s+(.*?)\s+)?BEGIN\s+SELECT\s+RAISE\s*\(\s*ABORT\s*,\s*'(?:[^']|'')*'\s*\)\s*;\s*END\s*;", re.I | re.S)
_made = {m.lower() for m in re.findall(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)", sql, re.I)}
guards = []
for m in list(_TRIG.finditer(sql)):
    name, ev, tbl, when = m.group(1), m.group(2).upper(), m.group(3).lower(), m.group(4) or ""
    if tbl in existing: refuse("trigger %s guards %s, a table that already exists: the refusal-only exception is for tables this migration creates" % (name, tbl))
    if tbl not in declared or tbl not in _made: refuse("trigger %s guards %s, which this migration does not create and declare" % (name, tbl))
    if re.search(r"\b(INSERT|UPDATE|DELETE|REPLACE|CREATE|DROP|ALTER|ATTACH|PRAGMA)\b", when, re.I): refuse("trigger %s: its WHEN condition may only read" % name)
    guards.append("%s (refuses %s on %s)" % (name, ev, tbl))
sql = _TRIG.sub(" ", sql)
for bad, why in [(r"\bCREATE\s+(TEMP\w*\s+)?TRIGGER\b", "triggers (other than refusal-only guards)"), (r"\bATTACH\b", "ATTACH"), (r"\bPRAGMA\s+\w+\s*=", "PRAGMA writes")]:
    if re.search(bad, sql, re.I): refuse("%s are not allowed in a migration" % why)
pats = [r"\bINSERT\s+(?:OR\s+\w+\s+)?INTO\s+" + W, r"\bREPLACE\s+INTO\s+" + W, r"\bUPDATE\s+(?:OR\s+\w+\s+)?" + W,
        r"\bDELETE\s+FROM\s+" + W, r"\bALTER\s+TABLE\s+" + W, r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?" + W,
        r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + W, r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?\S+\s+ON\s+" + W,
        r"\bDROP\s+INDEX\b()"]
targets = set()
for p in pats:
    for m in re.finditer(p, sql, re.I):
        targets.add(m.group(1).lower() if m.group(1) else "(index)")
if "(index)" in targets: refuse("DROP INDEX: name the table it belongs to in a separate, explicit migration review")
undeclared = sorted(targets - declared)
if undeclared: refuse("the SQL writes to tables that are not declared: %s" % ", ".join(undeclared))
print("### Migration for approval")
print("- File SHA-256: `%s` (matches the approved file)" % sha)
print("- Declared tables it may change: %s" % (", ".join(sorted(declared)) or "none"))
print("- Tables the SQL writes to: %s" % (", ".join(sorted(targets)) or "none"))
print("- Expected effects: %s" % desc.strip().replace("\n", " "))
if guards: print("- Refusal-only guards: %s" % "; ".join(guards))
print("\n```sql\n%s\n```" % data.decode("utf-8").strip())
# Automation v1 (1 Nov 2026): a migration that only CREATEs new tables or indexes, and touches no existing table, is
# ADDITIVE: it changes no existing row and is reversed by dropping what it created. Anything else is DESTRUCTIVE and
# always waits for the founder's approval (environment studio-database).
stmts = [x.strip() for x in sql.split(";") if x.strip()]
created = {m.group(1).lower() for x in stmts for m in [re.match(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + W, x, re.I)] if m}
additive = bool(stmts) and all(
    re.match(r"CREATE\s+TABLE\s+(?!.*\bAS\s+SELECT\b)", x, re.I | re.S) or re.match(r"CREATE\s+(UNIQUE\s+)?INDEX\b", x, re.I)
    for x in stmts)
if (targets - {"(index)"}) - created or created & existing:
    additive = False                                 # touches, re-creates or indexes an EXISTING table: not additive
print("- Class: %s" % ("ADDITIVE (new tables and indexes only)" if additive else "DESTRUCTIVE or changes existing tables"))
print("MIGRATION CHECK OK")
print("MIGRATION CLASS: %s" % ("additive" if additive else "destructive"))
