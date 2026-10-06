/* PHASE 6B · SECTION 5 — LEGACY SAVED-BUDGET MIGRATION
   '30k-plus' is retired by the five-band architecture. A saved My Plot answer
   holding it must never silently lose the budget axis.

   RULE (founder-specified):
     stored numeric budget <  50000  -> '30k-50k'
     stored numeric budget >= 50000  -> '50k-plus'
     no numeric budget available     -> UNRESOLVED. The homeowner chooses.
                                        A legacy answer is NEVER defaulted to
                                        '30k-50k', because that would invent a
                                        budget the homeowner never gave. */

/* PHASE 6D REVISION. The 573-product evidence killed the five-band model:
   €50,000+ held 6 safe products from ONE supplier and no supplier entered the
   market there. The homeowner-facing architecture reverts to FOUR bands plus
   "Not sure", and `30k-plus` is therefore NOT retired after all.

   The consequence for this module is the important part: there is now NOTHING
   TO MIGRATE. Every stored answer is already a live key. The needs-choice path
   is retained only so that a future retirement cannot silently drop the axis,
   and RETIRED_BAND_KEYS is deliberately EMPTY rather than deleted. */
export const LIVE_BAND_KEYS = ['under-10k','10k-20k','20k-30k','30k-plus'];
export const RETIRED_BAND_KEYS = [];
export const MIGRATION_CHOICE = [];

/* Returns one of:
     {status:'current',  key}                      — already a live key
     {status:'migrated', key, from, basis}         — resolved from a stored amount
     {status:'needs-choice', from, options}        — must ask the homeowner
     {status:'absent'}                             — no budget answer at all
   It NEVER returns undefined, and never drops a retired key on the floor. */
export function resolveSavedBudget(saved) {
  const key = saved && typeof saved.budgetKey === 'string' ? saved.budgetKey.trim() : null;
  if (!key) return { status: 'absent' };
  if (LIVE_BAND_KEYS.includes(key)) return { status: 'current', key };
  if (!RETIRED_BAND_KEYS.includes(key)) return { status: 'absent', unrecognised: key };

  // A retired key. Look for a real stored amount — never infer one.
  const raw = [saved.budgetAmount, saved.budget, saved.budgetValue]
    .find(v => typeof v === 'number' && Number.isFinite(v) && v >= 0);
  if (typeof raw !== 'number') {
    return { status: 'needs-choice', from: key, options: MIGRATION_CHOICE.slice() };
  }
  return { status: 'migrated', key: raw < 50000 ? '30k-50k' : '50k-plus', from: key, basis: raw };
}

/* The band the ranker should use. null means "do not rank on budget yet" —
   which the caller must surface as a question, not swallow. */
export function budgetKeyForRanking(saved) {
  const r = resolveSavedBudget(saved);
  return (r.status === 'current' || r.status === 'migrated') ? r.key : null;
}
