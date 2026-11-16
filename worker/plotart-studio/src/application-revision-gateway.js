/* Public shell only; no database, bucket or credentials. All token validation and storage
 * stay in the existing Studio backend via its private named service entrypoint. */
export default {fetch(request,env){return env.APPLICATION_REVIEW.fetch(request);}};
