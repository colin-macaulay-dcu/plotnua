// LOCAL DEMO ONLY: the Studio and the Idea Board intake on one local port, for previews and the moderation demo.
//   node test/serve-ideas-demo.mjs 8799 http://127.0.0.1:8791 [--seed]
// --seed adds clearly labelled LOCAL TEST ideas to the local database only (one waiting 80 days, to show the warning).
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
const port = Number(process.argv[2] || 8799), origin = process.argv[3] || 'http://127.0.0.1:8791';
const { url, db } = await start({ port, ideas: { ORIGIN: origin } });
if (process.argv.includes('--seed')) {
  const ago = d => new Date(Date.now() - d * 86400_000).toISOString();
  const rows = [['itest000000000001', 'PN-I-260813-T001', 'LOCAL TEST · A shared compost bay for the three houses at the end of the lane', 'Garden', 'Galway', 1, 80],
                ['itest000000000002', 'PN-I-261030-T002', 'LOCAL TEST · Turn the box room into a quiet music practice space', 'Space', null, 0, 2]];
  for (const [id, ref, text, area, county, show, d] of rows)
    await db.prepare('INSERT INTO ideas (id, ref, text, area, county, show_county, status, created_at) VALUES (?,?,?,?,?,?,?,?)').bind(id, ref, text, area, county, show, 'received', ago(d)).run();
}
console.log(`STUDIO ${url}\nFOUNDER_TOKEN ${token(FOUNDER, { exp: 86400 })}\nPIPELINE_TOKEN ${PIPELINE_TOKEN}`);
