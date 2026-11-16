/* Public Studio traffic retains its existing Access and founder checks. Token-only revision
 * requests arrive exclusively through a named Cloudflare service entrypoint. */
import { WorkerEntrypoint } from 'cloudflare:workers';
import revision from './application-revision.js';
export { default } from './index.js';
export class ApplicationRevision extends WorkerEntrypoint {
 fetch(request){return revision.fetch(request,this.env);}
}
