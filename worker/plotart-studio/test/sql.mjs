// Splits a SQL file into statements for local tests: skips -- comments, respects '...' strings, and keeps
// CREATE TRIGGER ... BEGIN ... END; together. (Production runs files through D1 itself.)
export function statements(sql) {
  const out = []; let cur = '', i = 0, inStr = false;
  const flush = () => { const t = cur.trim(); if (t) out.push(t); cur = ''; };
  while (i < sql.length) {
    const c = sql[i];
    if (inStr) { cur += c; if (c === "'") { if (sql[i + 1] === "'") { cur += "'"; i++; } else inStr = false; } i++; continue; }
    if (c === "'") { inStr = true; cur += c; i++; continue; }
    if (c === '-' && sql[i + 1] === '-') { while (i < sql.length && sql[i] !== '\n') i++; continue; }
    if (c === ';') {
      const trig = /^\s*CREATE\s+TRIGGER\b/i.test(cur);
      if (!trig || /\bEND\s*$/i.test(cur)) { flush(); i++; continue; }
    }
    cur += c; i++;
  }
  flush();
  return out;
}
