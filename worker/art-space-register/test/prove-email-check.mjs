// Proves the shared email check (Art Space Register, Artist Register, Founding 25, Gallery Artist applications):
// valid addresses, including plus-addressing, are accepted; a trailing full stop and empty domain labels are refused.
import { __test as T } from '../src/index.js';
const ok = ['hello@plotnua.ie', 'hello+gatest2114@plotnua.ie', 'first.last@example.co.uk', 'a_b-c@sub.domain.ie', 'ARTIST@Example.IE', 'x@studio.gallery'];
const bad = ['hello+gatest2114@plotnua.ie.', 'hello@plotnua.ie.', 'hello@plotnua..ie', 'hello@.plotnua.ie', 'hello@plotnua', 'hello@plotnua.i', 'hello @plotnua.ie', 'hello@@plotnua.ie', '@plotnua.ie', 'hello@'];
let pass = 0, fail = 0;
for (const e of ok) { if (T.EMAIL_RE.test(e)) pass++; else { fail++; console.log('  FAIL  should accept ' + e); } }
for (const e of bad) { if (!T.EMAIL_RE.test(e)) pass++; else { fail++; console.log('  FAIL  should refuse ' + e); } }
console.log(`EMAIL CHECK · ${pass + fail} checks, ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
