// Test-only Worker: runs src/founding.js inside workerd (the Workers runtime) for test/prove-enquiry-log.mjs.
import { foundingYear, foundingAt } from '../src/founding.js';
export default {
  async fetch(r) {
    const c = await r.json();
    return Response.json({ years: c.map(p => { const f = foundingYear(p); return [f.start, f.end, f.ends_at]; }),
      edge: [foundingAt({ founding: 1, first_published_at: '2027-06-30T23:30:00Z' }, '2028-06-30T22:59:00Z'), foundingAt({ founding: 1, first_published_at: '2027-06-30T23:30:00Z' }, '2028-06-30T23:00:00Z')] });
  },
};
