/* PlotArt Studio · internal test artist accounts (founder decision 26 Nov 2026, Report 33).
   The founder's permanent test account(s) are named by their stable Studio artist ID in the configuration TEST_ARTIST_IDS
   (comma-separated; empty = none). No database change: the designation lives in configuration, like FOUNDER_EMAILS.
   A test account works like any artist's account (onboarding, profile, works, galleries, opportunities, agreements,
   submissions, reviews, previews) except that:
     - it is never published: the founder's Publish and Retry refuse it, the publishing pipeline neither lists nor exports it,
       and the website builder refuses it independently (atlas-tools/release/plotart-test-artists.json);
     - it is never given a Contemporary position 01-25, a Founding 25 number or an Artists in Focus place;
     - no genuine commercial record is made for it (enquiry log, hire reports), and Stripe is refused while live keys are in use;
     - its agreement acceptances are test acceptances: every founder view marks them, and they are never counted as consent;
     - founder screens mark it TEST wherever artists are listed. */
import { Bad } from './lib.js';
import { stripeMode } from './stripe.js';
export const testIds = env => String(env.TEST_ARTIST_IDS || '').split(',').map(s => s.trim()).filter(Boolean);
export const isTest = (env, id) => !!id && testIds(env).includes(id);
export function refuse(env, id, what) {
  if (isTest(env, id)) throw new Bad(`This is an internal test account: ${what}`, 409);
}
// Payments: a test account may use Stripe only in TEST mode. Wherever the Studio is configured for live payments (or the
// mode cannot be established), every payment step for a test account is refused.
export function refuseLive(env, id) {
  if (!isTest(env, id)) return;
  const m = stripeMode(env);
  if (!m.ok || m.live) throw new Bad('This is an internal test account: payments run only in Stripe test mode', 409);
}
