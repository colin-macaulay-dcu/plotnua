/* PlotArt Studio · commercial outcomes (Commercial Conversion Sprint 1, founder approval 26 Nov 2026). FOUNDER ONLY.
   Aggregate, server-confirmed counts from records the Studio already keeps. Nothing new is recorded, nothing is sent
   anywhere, and no row, name, email, address or message ever leaves this function: counts and euro totals only.
     enquiries      enquiry_log (the permanent record): 'relay' = sent from a gallery page and accepted by the relay;
                    'email' = an email enquiry the founder logged. Corrections (rows that correct another) are not counted.
     delivery       enquiries (kept until each row's delete_after): how the relay's email to the artist went.
     hire           hire_enquiries (Art for Hire; switched off unless the founder opens it).
     checkout       checkout_baskets: a buyer reached payment (a basket opened at checkout), live and test kept apart.
     purchases      checkout_baskets paid (live / test), artwork_sales still standing, order_refunds succeeded.
   Basket ADDITIONS are not recorded on the server (the basket list lives in the buyer's browser on the checkout page),
   so they are reported as not measured rather than estimated. */
const DAY = 864e5;

async function count(env, sql, ...b) {
  try { const r = await env.DB.prepare(sql).bind(...b).first(); return r ? Number(Object.values(r)[0]) || 0 : 0; } catch { return null; }   // null: not installed
}
async function sum(env, sql, ...b) {
  try { const r = await env.DB.prepare(sql).bind(...b).first(); return r ? Number(Object.values(r)[0]) || 0 : 0; } catch { return null; }
}

export async function outcomes(env, at = new Date()) {
  const iso = d => new Date(at.getTime() - d * DAY).toISOString();
  const windows = { last_7_days: iso(7), last_30_days: iso(30), all_time: '0000' };
  const out = { as_of: at.toISOString(), windows: Object.keys(windows), enquiries: {}, enquiry_delivery: {}, hire_enquiries: {}, checkout_started: {}, purchases: {}, refunds: {},
    basket_additions: 'not measured on the server (the basket list stays in the buyer’s browser); see the analytics decision' };
  for (const [k, since] of Object.entries(windows)) {
    out.enquiries[k] = {
      from_gallery_pages: await count(env, "SELECT COUNT(*) FROM enquiry_log WHERE route = 'relay' AND corrects IS NULL AND introduced_at >= ?", since),
      logged_by_email: await count(env, "SELECT COUNT(*) FROM enquiry_log WHERE route = 'email' AND corrects IS NULL AND introduced_at >= ?", since),
    };
    out.hire_enquiries[k] = await count(env, 'SELECT COUNT(*) FROM hire_enquiries WHERE created_at >= ?', since);
    out.checkout_started[k] = {
      live: await count(env, 'SELECT COUNT(*) FROM checkout_baskets WHERE livemode = 1 AND created_at >= ?', since),
      test: await count(env, 'SELECT COUNT(*) FROM checkout_baskets WHERE livemode = 0 AND created_at >= ?', since),
    };
    out.purchases[k] = {
      live_paid_baskets: await count(env, "SELECT COUNT(*) FROM checkout_baskets WHERE livemode = 1 AND status = 'paid' AND created_at >= ?", since),
      live_paid_total_cents: await sum(env, "SELECT COALESCE(SUM(total_cents), 0) FROM checkout_baskets WHERE livemode = 1 AND status = 'paid' AND created_at >= ?", since),
      test_paid_baskets: await count(env, "SELECT COUNT(*) FROM checkout_baskets WHERE livemode = 0 AND status = 'paid' AND created_at >= ?", since),
      artworks_sold_standing: await count(env, 'SELECT COUNT(*) FROM artwork_sales WHERE released_at IS NULL AND sold_at >= ?', since),
    };
    out.refunds[k] = await count(env, "SELECT COUNT(*) FROM order_refunds WHERE status = 'succeeded' AND created_at >= ?", since);
  }
  for (const s of ['received', 'sent', 'send_failed']) out.enquiry_delivery[s] = await count(env, 'SELECT COUNT(*) FROM enquiries WHERE status = ?', s);
  out.enquiry_delivery.note = 'Only rows still within their retention period; the permanent count is under enquiries.';
  return out;
}
