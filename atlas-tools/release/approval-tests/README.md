# Founder approval checkpoint · controlled tests

This file exists only to test the `website-production` approval checkpoint. It lives in `atlas-tools/`, which is never
published (`_config.yml` excludes it), so releasing or rejecting it cannot change any page of plotnua.ie.

- Rejection test (prepared 20 Nov 2026): this commit is requested as a release, reaches the approval checkpoint, and
  is REJECTED by the founder. Expected: approval job "rejected", promote job "skipped", main unchanged, no
  production tag, no Pages build, every live page byte-identical.
