#!/usr/bin/env bash
# PlotArt Studio · controlled infrastructure activation (founder approval, 29 Oct 2026).
# Run from this folder, one step at a time. Each step stops on the first failure and appends
# a secret-free record to activation-log.txt so Claude can verify it.
#
#   bash activate.sh 1-database     D1 "plotart-studio" (Western Europe) + schema
#   bash activate.sh 2-storage      private R2 "plotart-studio-images" (EU jurisdiction)
#   bash activate.sh 3-studio       deploy the Studio (refuses every request until Access is set) + secrets
#      (dashboard: enable Cloudflare Access, see ACTIVATION.md)
#   bash activate.sh 4-access       paste the Access team domain + AUD tag, redeploy, store the pipeline service token
#   bash activate.sh 5-enquiry      deploy the enquiry Worker CLOSED
#   bash activate.sh verify         every security check from outside
#
# Never changes DNS, the website, GitHub, publishing, automatic updates or email sending.
# Secrets are never printed or written to disk: they go to Cloudflare and to your macOS Keychain only.
set -euo pipefail
cd "$(dirname "$0")"
W="npx --yes wrangler@4"
LOG="activation-log.txt"
STUDIO_HOST="plotart-studio.colin-a41.workers.dev"
ENQ_HOST="plotart-enquiry.colin-a41.workers.dev"
KC_ACCOUNT="plotart"
say()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
log()  { printf '%s  %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
pass() { printf '  \033[32mPASS\033[0m  %s\n' "$*"; log "PASS  $*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; log "FAIL  $*"; FAILED=1; }
die()  { printf '\n\033[31mSTOPPED: %s\033[0m\n' "$*"; log "STOPPED $*"; exit 1; }
kc_set() { security add-generic-password -U -a "$KC_ACCOUNT" -s "$1" -w "$2" >/dev/null; }
kc_get() { security find-generic-password -a "$KC_ACCOUNT" -s "$1" -w 2>/dev/null || true; }
toml_set() { # file key value : replaces  key = "..."  (first match)
  node -e '
    const fs=require("fs"),[f,k,v]=process.argv.slice(1);let s=fs.readFileSync(f,"utf8");
    const re=new RegExp("^("+k+"\\s*=\\s*)\"[^\"]*\"","m"); if(!re.test(s)){console.error("key not found: "+k);process.exit(1)}
    fs.writeFileSync(f,s.replace(re,(m,a)=>a+JSON.stringify(v)));' "$1" "$2" "$3"
}
FAILED=0
step="${1:-}"
log "---- $step"

case "$step" in
1-database)
  say "Cloudflare account"; $W whoami
  # Wrangler resolves "plotart-studio" through wrangler.toml, so the id must be in the config before d1 info/execute.
  ID=$(sed -n 's/^database_id = "\([0-9a-f-]\{36\}\)".*/\1/p' wrangler.toml)
  if [ -z "$ID" ]; then
    $W d1 list --json > /tmp/plotart-d1list.json
    ID=$(node -e 'const l=require("/tmp/plotart-d1list.json");const d=l.find(x=>x.name==="plotart-studio");process.stdout.write(d?d.uuid:"")')
    if [ -z "$ID" ]; then
      say "Creating D1 plotart-studio in Western Europe (answer No if Wrangler offers to edit the config: this script does it)"
      $W d1 create plotart-studio --location weur
      $W d1 list --json > /tmp/plotart-d1list.json
      ID=$(node -e 'const l=require("/tmp/plotart-d1list.json");const d=l.find(x=>x.name==="plotart-studio");process.stdout.write(d?d.uuid:"")')
    else
      say "D1 plotart-studio already exists: using it (not creating another)"
    fi
  fi
  [[ "$ID" =~ ^[0-9a-f-]{36}$ ]] || die "could not read the database id"
  toml_set wrangler.toml database_id "$ID"; toml_set wrangler.enquiry.toml database_id "$ID"
  $W d1 info plotart-studio --json > /tmp/plotart-d1.json
  node -e 'const j=require("/tmp/plotart-d1.json");if((j.uuid||j.database_id)!==process.argv[1]){console.error("id mismatch");process.exit(1)}' "$ID" || die "database id mismatch"
  pass "existing database plotart-studio recognised ($ID)"
  log "d1 id $ID written to wrangler.toml and wrangler.enquiry.toml"
  say "Applying schema.sql (answer y to proceed)"
  $W d1 execute plotart-studio --remote --file=schema.sql
  $W d1 execute plotart-studio --remote --json --command "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name" > /tmp/plotart-tables.json
  T=$(node -e 'const j=require("/tmp/plotart-tables.json");process.stdout.write((j[0]||j).results.map(r=>r.name).filter(n=>!n.startsWith("_cf")&&n!=="sqlite_sequence").join(","))')
  log "tables: $T"
  for t in artists artworks images submissions versions publish_queue audit enquiries; do
    [[ ",$T," == *",$t,"* ]] && pass "table $t" || fail "table $t missing"
  done
  [[ ",$T," == *",mail_capture,"* ]] && fail "test-only table mail_capture present" || pass "no test-only tables"
  node -e 'const j=require("/tmp/plotart-d1.json");console.log("  region:",j.running_in_region||j.region||"(see dashboard)")' | tee -a "$LOG"
  ;;
2-storage)
  if $W r2 bucket info plotart-studio-images --jurisdiction eu >/dev/null 2>&1; then
    say "R2 plotart-studio-images (EU) already exists"
  else
    say "Creating private R2 bucket plotart-studio-images, EU jurisdiction"
    $W r2 bucket create plotart-studio-images --jurisdiction eu
  fi
  $W r2 bucket info plotart-studio-images --jurisdiction eu | tee -a "$LOG"
  DEV=$($W r2 bucket dev-url get plotart-studio-images --jurisdiction eu 2>&1 || true); log "dev-url: $DEV"
  if echo "$DEV" | grep -qi "disabled\|not enabled"; then pass "public r2.dev access is off"; else fail "check r2.dev access: $DEV"; fi
  ;;
3-studio)
  grep -q 'database_id = "NOT-CREATED"' wrangler.toml && die "run 1-database first"
  grep -q '^ACCESS_AUD = ""' wrangler.toml || die "ACCESS_AUD is already set: use 4-access"
  say "Deploying the Studio. Access is not configured yet, so it refuses every request."
  $W deploy
  if [ -z "$(kc_get plotart-pipeline-token)" ]; then kc_set plotart-pipeline-token "$(openssl rand -hex 32)"; log "new pipeline token stored in Keychain (plotart-pipeline-token)"; fi
  say "Setting PIPELINE_TOKEN (from your Keychain; never shown)"
  printf %s "$(kc_get plotart-pipeline-token)" | $W secret put PIPELINE_TOKEN
  printf '\nYour founder sign-in email for the Studio (the one you will use with Cloudflare Access): '
  read -r FE; [[ "$FE" == *@*.* ]] || die "that is not an email address"
  printf %s "$FE" | tr 'A-Z' 'a-z' | $W secret put FOUNDER_EMAILS
  log "secrets set: PIPELINE_TOKEN, FOUNDER_EMAILS"
  $W secret list | tee -a "$LOG"
  C=$(curl -s -o /tmp/plotart-r.txt -w '%{http_code}' "https://$STUDIO_HOST/api/me")
  [[ "$C" == 500 ]] && grep -q "configuration" /tmp/plotart-r.txt && pass "Studio deployed and refusing every request until Access is set ($C)" || fail "Studio before Access: $C $(head -c 200 /tmp/plotart-r.txt)"
  ;;
4-access)
  printf 'Access team domain (e.g. https://plotnua.cloudflareaccess.com): '; read -r TD
  TD="${TD%/}"; [[ "$TD" == https://*.cloudflareaccess.com ]] || TD="https://${TD#https://}"
  [[ "$TD" =~ ^https://[a-z0-9-]+\.cloudflareaccess\.com$ ]] || die "team domain must look like https://NAME.cloudflareaccess.com"
  printf 'Application Audience (AUD) tag: '; read -r AUD
  [[ "$AUD" =~ ^[0-9a-f]{64}$ ]] || die "the AUD tag is 64 hexadecimal characters"
  curl -sf "$TD/cdn-cgi/access/certs" | grep -q '"keys"' || die "no signing keys at $TD/cdn-cgi/access/certs"
  toml_set wrangler.toml ACCESS_TEAM_DOMAIN "$TD"; toml_set wrangler.toml ACCESS_AUD "$AUD"
  log "access team $TD, aud ${AUD:0:8}… written to wrangler.toml"
  say "Pipeline service token (Zero Trust → Access → Service credentials). Input is hidden; stored in Keychain only."
  printf 'Client ID: '; read -r CID; [[ "$CID" == *.access ]] || die "the Client ID ends in .access"
  printf 'Client Secret: '; read -rs CSEC; echo; [ ${#CSEC} -ge 40 ] || die "that secret looks too short"
  kc_set plotart-access-client-id "$CID"; kc_set plotart-access-client-secret "$CSEC"
  log "service token stored in Keychain (plotart-access-client-id / -secret)"
  say "Redeploying the Studio with Access configured"
  $W deploy
  ;;
5-enquiry)
  grep -q 'database_id = "NOT-CREATED"' wrangler.enquiry.toml && die "run 1-database first"
  grep -q '^ENQUIRIES_ENABLED = "false"' wrangler.enquiry.toml || die "the enquiry Worker must ship closed"
  grep -q '^MAILER = "none"' wrangler.enquiry.toml || die "the enquiry Worker must ship with MAILER none"
  say "Deploying the enquiry Worker CLOSED (sends nothing, accepts nothing)"
  $W deploy -c wrangler.enquiry.toml
  ;;
verify)
  S="https://$STUDIO_HOST"; E="https://$ENQ_HOST/v1/enquiry"
  CID=$(kc_get plotart-access-client-id); CSEC=$(kc_get plotart-access-client-secret); TOK=$(kc_get plotart-pipeline-token)
  code() { curl -s -o /tmp/plotart-r.txt -w '%{http_code} %{redirect_url}' "$@"; }
  say "Studio behind Cloudflare Access"
  for p in / /admin /api/me /api/admin/overview /api/pipeline/queue /preview/; do
    R=$(code "$S$p")
    if grep -q "Please sign in\|configuration error" /tmp/plotart-r.txt; then fail "unauthenticated $p reached the Worker: Access is not in front ($R)"
    elif [[ "$R" == 302*cloudflareaccess.com* || "$R" == 401* || "$R" == 403* ]]; then pass "unauthenticated $p → stopped by Access (${R%% *})"
    else fail "unauthenticated $p → $R"; fi
  done
  R=$(code -H "Cf-Access-Jwt-Assertion: forged.token.value" "$S/api/me"); [[ "$R" == 302* || "$R" == 403* || "$R" == 401* ]] && pass "forged token refused (${R%% *})" || fail "forged token → $R"
  if [ -n "$CID" ] && [ -n "$CSEC" ]; then
    A=(-H "CF-Access-Client-Id: $CID" -H "CF-Access-Client-Secret: $CSEC")
    R=$(code "${A[@]}" "$S/api/pipeline/queue"); [[ "$R" == 401* ]] && pass "pipeline without its bearer token → 401" || fail "pipeline without bearer → $R"
    R=$(code "${A[@]}" -H "Authorization: Bearer wrong" "$S/api/pipeline/queue"); [[ "$R" == 401* ]] && pass "pipeline with a wrong token → 401" || fail "wrong bearer → $R"
    R=$(code "${A[@]}" -H "Authorization: Bearer $TOK" "$S/api/pipeline/queue"); [[ "$R" == 200* ]] && grep -q '"ok":true' /tmp/plotart-r.txt && pass "pipeline with service token + bearer → 200 (D1 read through the Worker)" || fail "pipeline with token → $R $(head -c 160 /tmp/plotart-r.txt)"
    R=$(code "${A[@]}" "$S/api/admin/overview"); [[ "$R" == 401* || "$R" == 403* ]] && pass "service token cannot reach the founder desk (${R%% *})" || fail "service token → admin $R"
    R=$(code "${A[@]}" "$S/api/me"); [[ "$R" == 401* || "$R" == 403* ]] && pass "service token cannot reach artist data (${R%% *})" || fail "service token → /api/me $R"
    R=$(code "${A[@]}" -H "X-Studio: 1" -X POST "$S/api/admin/selftest"); [[ "$R" == 401* || "$R" == 403* ]] && pass "service token cannot run founder actions (${R%% *})" || fail "service token → selftest $R"
  else
    fail "service token not in Keychain: run 4-access"
  fi
  R=$(curl -sI "$S/" | tr -d '\r' | grep -i '^location:' || true); log "login redirect: ${R:0:90}"
  say "Enquiry Worker is closed"
  R=$(code -X POST -H "Origin: https://plotnua.ie" -H "Content-Type: application/json" --data '{"artist":"x","name":"Test","email":"t@example.com","message":"verification"}' "$E"); [[ "$R" == 503* ]] && pass "enquiry from plotnua.ie → 503 closed" || fail "enquiry → $R $(head -c 120 /tmp/plotart-r.txt)"
  R=$(code -X POST -H "Origin: https://example.com" -H "Content-Type: application/json" --data '{}' "$E"); [[ "$R" == 403* ]] && pass "enquiry from another website → 403" || fail "foreign origin → $R"
  R=$(code "$E"); [[ "$R" == 405* ]] && pass "GET → 405" || fail "GET → $R"
  R=$(code "https://$ENQ_HOST/"); [[ "$R" == 404* ]] && pass "other paths → 404" || fail "other path → $R"
  say "Configuration"
  grep -q '^INSTANT_AUTOPUBLISH = "false"' wrangler.toml && pass "automatic artist updates off" || fail "INSTANT_AUTOPUBLISH not false"
  grep -q '^MAILER = "none"' wrangler.toml && grep -q '^MAILER = "none"' wrangler.enquiry.toml && pass "no email sending (MAILER none)" || fail "MAILER not none"
  grep -q '^ENQUIRIES_ENABLED = "false"' wrangler.enquiry.toml && pass "enquiries closed" || fail "ENQUIRIES_ENABLED not false"
  DEV=$($W r2 bucket dev-url get plotart-studio-images --jurisdiction eu 2>&1 || true); echo "$DEV" | grep -qi "disabled\|not enabled" && pass "R2 has no public address" || fail "r2.dev: $DEV"
  [ "$FAILED" = 0 ] && say "ALL CHECKS PASSED" || say "SOME CHECKS FAILED: see above"
  ;;
*) sed -n 2,15p "$0"; exit 2;;
esac
[ "$FAILED" = 0 ] || die "step $step had failures"
log "OK $step"
say "Step $step done."
