#!/usr/bin/env python3
"""Proof: only genuinely additive migrations can take the automatic lane (automation v1, 1 Nov 2026).
Every case is written to a temporary file named like a NEW migration (0099_*.sql) and run through migration-check.py
with its true table declaration. Unsafe SQL must come out DESTRUCTIVE (or be refused outright).
    python3 atlas-tools/release/studio/prove-migration-classifier.py
"""
import hashlib, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "migration-check.py")
cases = [  # (name, sql, declared tables, expected: additive | destructive | refused)
    ("new table", "CREATE TABLE widgets (id TEXT PRIMARY KEY);", "widgets", "additive"),
    ("new table + its index", "CREATE TABLE widgets (id TEXT, n INT); CREATE INDEX widgets_n ON widgets(n);", "widgets", "additive"),
    ("the real 0004 (Borrowed Garden)", open(os.path.join(HERE, "..", "..", "..", "worker", "plotart-studio", "migrations", "0004_garden_board.sql")).read(), "garden_listings,garden_intake_days,garden_enquiries,garden_enquiry_days", "additive4"),
    ("the real 0003", open(os.path.join(HERE, "..", "..", "..", "worker", "plotart-studio", "migrations", "0003_ideas.sql")).read(), "ideas,idea_intake_days", "additive*"),
    ("DROP an existing table", "DROP TABLE artists;", "artists", "destructive"),
    ("DROP IF EXISTS hidden after a create", "CREATE TABLE widgets (id TEXT); DROP TABLE IF EXISTS artists;", "widgets,artists", "destructive"),
    ("ALTER an existing table", "ALTER TABLE artists ADD COLUMN x TEXT;", "artists", "destructive"),
    ("rename an existing table", "ALTER TABLE artworks RENAME TO artworks_old;", "artworks", "destructive"),
    ("DELETE rows", "DELETE FROM audit;", "audit", "destructive"),
    ("UPDATE rows", "UPDATE artists SET email = '';", "artists", "destructive"),
    ("INSERT rows", "INSERT INTO gallery_positions (position) VALUES (99);", "gallery_positions", "destructive"),
    ("INSERT into the new table", "CREATE TABLE widgets (id TEXT); INSERT INTO widgets VALUES ('a');", "widgets", "destructive"),
    ("REPLACE INTO", "REPLACE INTO artists (id) VALUES ('x');", "artists", "destructive"),
    ("index on an existing table", "CREATE INDEX artists_email2 ON artists(email);", "artists", "destructive"),
    ("unique index on an existing table", "CREATE UNIQUE INDEX enq_u ON enquiries(id);", "enquiries", "destructive"),
    ("re-create an existing table (IF NOT EXISTS)", "CREATE TABLE IF NOT EXISTS artists (id TEXT);", "artists", "destructive"),
    ("re-create an existing table", "CREATE TABLE audit (id TEXT);", "audit", "destructive"),
    ("re-create a table from an earlier migration", "CREATE TABLE IF NOT EXISTS gallery_positions (p INT);", "gallery_positions", "destructive"),
    ("re-create the Idea Board table (0003)", "CREATE TABLE IF NOT EXISTS ideas (id TEXT);", "ideas", "destructive"),
    ("copy personal data with AS SELECT", "CREATE TABLE emails AS SELECT email FROM artists;", "emails", "destructive"),
    ("view over existing data", "CREATE VIEW v AS SELECT * FROM artists;", "none", "destructive"),
    ("trigger", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER t AFTER INSERT ON artists BEGIN DELETE FROM artists; END;", "widgets,artists", "refused"),
    ("refusal-only guard on a new table (0005 pattern)", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER IF NOT EXISTS w_no_update BEFORE UPDATE ON widgets BEGIN SELECT RAISE(ABORT, 'append-only'); END;", "widgets", "additive"),
    ("refusal-only guard with a read-only WHEN", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER w_no_delete BEFORE DELETE ON widgets WHEN NOT EXISTS (SELECT 1 FROM artists) BEGIN SELECT RAISE(ABORT, 'no'); END;", "widgets", "additive"),
    ("refusal-only guard on an EXISTING table", "CREATE TRIGGER a_no_update BEFORE UPDATE ON artists BEGIN SELECT RAISE(ABORT, 'no'); END;", "artists", "refused"),
    ("guard whose WHEN writes", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER w BEFORE DELETE ON widgets WHEN (DELETE FROM artists) BEGIN SELECT RAISE(ABORT, 'no'); END;", "widgets,artists", "refused"),
    ("BEFORE trigger that writes", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER w BEFORE INSERT ON widgets BEGIN UPDATE artists SET email = ''; END;", "widgets,artists", "refused"),
    ("guard plus a second statement in its body", "CREATE TABLE widgets (id TEXT); CREATE TRIGGER w BEFORE INSERT ON widgets BEGIN SELECT RAISE(ABORT, 'x'); DELETE FROM audit; END;", "widgets,audit", "refused"),
    ("ATTACH", "ATTACH DATABASE 'x' AS y;", "none", "refused"),
    ("PRAGMA write", "PRAGMA foreign_keys = OFF;", "none", "refused"),
    ("undeclared table", "CREATE TABLE widgets (id TEXT); DELETE FROM artists;", "widgets", "refused"),
    ("DROP INDEX", "DROP INDEX ideas_status_published;", "ideas", "refused"),
    ("statement hidden in a block comment", "CREATE TABLE widgets (id TEXT); /* harmless */ DELETE FROM audit;", "widgets,audit", "destructive"),
    ("statement after a line comment", "CREATE TABLE widgets (id TEXT); -- note\nDROP TABLE audit;", "widgets,audit", "destructive"),
    ("lower-case and quoted names", 'create table "Widgets" (id text); drop table "audit";', "widgets,audit", "destructive"),
    ("empty file", "-- nothing\n", "none", "destructive"),
]
fails = 0
with tempfile.TemporaryDirectory() as d:
    for name, sql, tables, want in cases:
        p = os.path.join(d, "0099_case.sql")
        open(p, "w").write(sql)
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if want == "additive*":     # the real file keeps its own number so schema.sql's 0003 marker applies
            p = os.path.join(HERE, "..", "..", "..", "worker", "plotart-studio", "migrations", "0003_ideas.sql"); want = "additive"
            sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if want == "additive4":
            p = os.path.join(HERE, "..", "..", "..", "worker", "plotart-studio", "migrations", "0004_garden_board.sql"); want = "additive"
            sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        out = subprocess.run([sys.executable, CHECK, p, sha, tables, "Classifier proof case: " + name], capture_output=True, text=True).stdout
        got = "refused" if out.startswith("REFUSED") else ("additive" if "MIGRATION CLASS: additive" in out else "destructive")
        ok = got == want
        fails += not ok
        print(("  PASS  " if ok else "  FAIL  ") + "%-46s expected %-11s got %s" % (name, want, got))
# The workflow must hand the classifier a copy that keeps the migration's own file name (NNNN_name.sql): a copy under
# another name has no number, so every existing table is counted as "existing" and nothing can ever be additive.
wf = open(os.path.join(HERE, "..", "..", "..", ".github", "workflows", "studio-d1-migration.yml")).read()
for i, line in enumerate(l for l in wf.splitlines() if "migration-check.py" in l):
    arg = line.split("migration-check.py", 1)[1].split()[0].strip('"')
    ok = arg.endswith("/$MIGRATION")
    fails += not ok
    print(("  PASS  " if ok else "  FAIL  ") + "workflow check %d passes the file under its own name (%s)" % (i + 1, arg))
# and a nameless copy of an additive migration is (safely) never additive: the failure mode the fix removes
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "m.sql"); open(p, "w").write("CREATE TABLE garden_listings (id TEXT);")
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    out = subprocess.run([sys.executable, CHECK, p, sha, "garden_listings", "Classifier proof: a copy without its number"], capture_output=True, text=True).stdout
    ok = "MIGRATION CLASS: destructive" in out
    fails += not ok
    print(("  PASS  " if ok else "  FAIL  ") + "an unnumbered copy falls back to DESTRUCTIVE (needs approval)")
print("\nMIGRATION CLASSIFIER · %s · %d cases, %d failed" % ("OK" if not fails else "FAIL", len(cases), fails))
sys.exit(1 if fails else 0)
