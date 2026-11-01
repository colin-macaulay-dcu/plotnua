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
for bad, why in [(r"\bCREATE\s+(TEMP\w*\s+)?TRIGGER\b", "triggers"), (r"\bATTACH\b", "ATTACH"), (r"\bPRAGMA\s+\w+\s*=", "PRAGMA writes")]:
    if re.search(bad, sql, re.I): refuse("%s are not allowed in a migration" % why)
W = r'[`"\[]?([A-Za-z_][A-Za-z0-9_]*)[`"\]]?'
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
print("\n```sql\n%s\n```" % data.decode("utf-8").strip())
# Automation v1 (1 Nov 2026): a migration that only CREATEs new tables or indexes, and touches no existing table, is
# ADDITIVE: it changes no existing row and is reversed by dropping what it created. Anything else is DESTRUCTIVE and
# always waits for the founder's approval (environment studio-database).
stmts = [x.strip() for x in sql.split(";") if x.strip()]
additive = bool(stmts) and all(re.match(r"CREATE\s+(TABLE|(UNIQUE\s+)?INDEX)\b", x, re.I) for x in stmts)
created = {m.group(1).lower() for x in stmts for m in [re.match(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + W, x, re.I)] if m}
if additive and (targets - {"(index)"}) - created:
    additive = False                                 # an index on an EXISTING table changes that table: not additive
print("- Class: %s" % ("ADDITIVE (new tables and indexes only)" if additive else "DESTRUCTIVE or changes existing tables"))
print("MIGRATION CHECK OK")
print("MIGRATION CLASS: %s" % ("additive" if additive else "destructive"))
