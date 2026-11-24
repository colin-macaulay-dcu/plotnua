// PlotArt · gallery D1 test · clean-up decisions, FAIL-CLOSED (founder safeguards, 24 Nov 2026). Used by
// .github/workflows/plotart-galleries-cloudflare-test.yml. It never calls Cloudflare itself: it reads the JSON that
// `wrangler d1 list --json` wrote, and (for leftovers) the GitHub status of the run that created each one.
//
//   node test/cf-test-cleanup.mjs verify-gone --list FILE --name NAME [--id UUID]
//       exit 0  the list was read and holds neither that name nor that id   → "gone" (the ONLY success)
//       exit 1  the database is still there                                  → visible failure
//       exit 2  the list could not be read or is not a database list         → inconclusive = visible failure
//   node test/cf-test-cleanup.mjs plan-leftovers --list FILE --run-id ID --attempt N
//       prints {"delete":[…], "review":[{name, reason}]}; exit 2 if the list cannot be read (nothing may be deleted)
//       A leftover is a database named EXACTLY plotart-gallery-phaseb-test-<run id>-<attempt>. It is deleted only when its
//       run is known to be finished: the run's status is "completed", or the run has since moved on to a later attempt
//       (attempts of one run never overlap). Anything else (the run is queued, waiting, in progress, or its status cannot
//       be read) goes to "review" and is left alone for the founder to check by hand. Other databases are never listed.
//   node test/cf-test-cleanup.mjs --self-test     (offline; no Cloudflare, no GitHub)
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export const PATTERN = /^plotart-gallery-phaseb-test-([0-9]+)-([0-9]+)$/;
const arg = (a, k) => { const i = a.indexOf(k); return i > 0 ? a[i + 1] : null; };

export function readList(file) {
  let l;
  try { l = JSON.parse(readFileSync(file, 'utf8')); } catch { return null; }
  if (!Array.isArray(l) || l.some(d => !d || typeof d.name !== 'string')) return null;
  return l;
}
export function verifyGone(list, name, id) {
  if (!list) return 2;
  return list.some(d => d.name === name || (id && d.uuid === id)) ? 1 : 0;
}
// status(runId) → { status, run_attempt } or null when it cannot be read
export function planLeftovers(list, current, status) {
  if (!list) return null;
  const out = { delete: [], review: [] };
  for (const d of list) {
    const m = PATTERN.exec(d.name);
    if (!m) continue;                                                     // not ours: never touched, never listed
    const [run, attempt] = [m[1], Number(m[2])];
    if (run === current.runId && attempt === current.attempt) { out.review.push({ name: d.name, reason: 'has this run’s own name before it was created' }); continue; }
    const st = status(run);
    if (!st || typeof st.status !== 'string') { out.review.push({ name: d.name, reason: 'the status of its run could not be read' }); continue; }
    if (st.status === 'completed') out.delete.push(d.name);
    else if (Number(st.run_attempt) > attempt) out.delete.push(d.name);   // that attempt is over: its run has moved on
    else out.review.push({ name: d.name, reason: `its run is still ${st.status}` });
  }
  return out;
}
function ghStatus(repo) {
  return run => {
    try { const j = JSON.parse(execFileSync('gh', ['api', `repos/${repo}/actions/runs/${run}`], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }));
      return { status: j.status, run_attempt: j.run_attempt }; } catch { return null; }
  };
}

function selfTest() {
  const dir = mkdtempSync(join(tmpdir(), 'cft-'));
  const f = (n, v) => { const p = join(dir, n); writeFileSync(p, typeof v === 'string' ? v : JSON.stringify(v)); return p; };
  const res = []; const check = (n, ok) => { res.push(ok); console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${n}`); };
  const ours = 'plotart-gallery-phaseb-test-100-1', prod = { name: 'plotart-studio', uuid: 'p-1' };
  check('V1 gone: a readable list without the name or id → success (exit 0)', verifyGone(readList(f('a', [prod])), ours, 'u-1') === 0);
  check('V2 still there by name → visible failure (exit 1)', verifyGone(readList(f('b', [prod, { name: ours, uuid: 'u-1' }])), ours, 'u-1') === 1);
  check('V3 still there by id under another name → visible failure (exit 1)', verifyGone(readList(f('c', [{ name: 'renamed', uuid: 'u-1' }])), ours, 'u-1') === 1);
  check('V4 list could not be read (empty output) → inconclusive (exit 2), never success', verifyGone(readList(f('d', '')), ours, 'u-1') === 2);
  check('V5 list is an error object, not a list → inconclusive (exit 2)', verifyGone(readList(f('e', { error: 'Authentication error' })), ours, 'u-1') === 2);
  check('V6 list is malformed JSON → inconclusive (exit 2)', verifyGone(readList(f('g', '[{"name":')), ours, 'u-1') === 2);
  const list = readList(f('h', [prod, { name: 'plotart-checkout-test', uuid: 't' }, { name: 'plotart-gallery-phaseb-test-7', uuid: 'x' },
    { name: 'plotart-gallery-phaseb-test-90-1', uuid: 'a' }, { name: 'plotart-gallery-phaseb-test-91-1', uuid: 'b' },
    { name: 'plotart-gallery-phaseb-test-92-1', uuid: 'c' }, { name: 'plotart-gallery-phaseb-test-93-2', uuid: 'd' },
    { name: 'plotart-gallery-phaseb-test-94-1', uuid: 'e' }, { name: 'plotart-gallery-phaseb-test-100-1', uuid: 'f' }]));
  const S = { 90: { status: 'completed', run_attempt: 1 }, 91: { status: 'in_progress', run_attempt: 1 }, 92: { status: 'in_progress', run_attempt: 2 },
    93: { status: 'waiting', run_attempt: 2 }, 94: null };
  const p = planLeftovers(list, { runId: '100', attempt: 1 }, r => S[r] ?? null);
  check('L1 a database whose run is completed → deleted', p.delete.includes('plotart-gallery-phaseb-test-90-1'));
  check('L2 a database whose run is still in progress → NOT deleted; reported for review', !p.delete.includes('plotart-gallery-phaseb-test-91-1') && p.review.some(x => x.name.endsWith('-91-1')));
  check('L3 an earlier attempt of a run now on a later attempt → deleted (attempts never overlap)', p.delete.includes('plotart-gallery-phaseb-test-92-1'));
  check('L4 the current attempt of a run that is waiting for approval → NOT deleted; reported', !p.delete.includes('plotart-gallery-phaseb-test-93-2') && p.review.some(x => x.name.endsWith('-93-2')));
  check('L5 a run whose status cannot be read → NOT deleted; reported for manual review', !p.delete.includes('plotart-gallery-phaseb-test-94-1') && p.review.some(x => x.name.endsWith('-94-1')));
  check('L6 this run’s own name already present → NOT deleted; reported', !p.delete.includes(ours) && p.review.some(x => x.name === ours));
  check('L7 production, the checkout test database and any other name are never touched or listed',
    ![...p.delete, ...p.review.map(x => x.name)].some(n => ['plotart-studio', 'plotart-checkout-test', 'plotart-gallery-phaseb-test-7'].includes(n)));
  check('L8 an unreadable database list → no plan at all (nothing may be deleted)', planLeftovers(readList(f('i', 'oops')), { runId: '100', attempt: 1 }, () => null) === null);
  const fail = res.filter(x => !x).length;
  console.log(`\nD1 TEST CLEAN-UP (fail-closed) · ${res.length} checks, ${res.length - fail} passed, ${fail} failed`);
  return fail ? 1 : 0;
}

const a = process.argv.slice(2);
if (a[0] === '--self-test') process.exit(selfTest());
if (a[0] === 'verify-gone') process.exit(verifyGone(readList(arg(a, '--list')), arg(a, '--name'), arg(a, '--id')));
if (a[0] === 'plan-leftovers') {
  const p = planLeftovers(readList(arg(a, '--list')), { runId: String(arg(a, '--run-id')), attempt: Number(arg(a, '--attempt')) }, ghStatus(process.env.GITHUB_REPOSITORY || ''));
  if (!p) { console.error('the database list could not be read'); process.exit(2); }
  console.log(JSON.stringify(p)); process.exit(0);
}
if (process.argv[1] && process.argv[1].endsWith('cf-test-cleanup.mjs')) { console.log('usage: see the header of this file'); process.exit(2); }
