// LOCAL DEMO ONLY: the Studio and the Idea Board intake on one local port, for previews and the moderation demo.
//   node test/serve-ideas-demo.mjs 8799 http://127.0.0.1:8791
import { start, token, FOUNDER, PIPELINE_TOKEN } from './local.mjs';
const port = Number(process.argv[2] || 8799), origin = process.argv[3] || 'http://127.0.0.1:8791';
const { url } = await start({ port, ideas: { ORIGIN: origin } });
console.log(`STUDIO ${url}\nFOUNDER_TOKEN ${token(FOUNDER, { exp: 86400 })}\nPIPELINE_TOKEN ${PIPELINE_TOKEN}`);
