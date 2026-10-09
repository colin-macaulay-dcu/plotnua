#!/usr/bin/env node
/**
 * JOB 4 · THE STRUCTURAL CONTRACT, ASSERTED INDEPENDENTLY OF THE BUILDER
 * ===========================================================================
 * build-landmarks.py checks its own work, which is necessary and not
 * sufficient: a builder that is wrong about what it produced will be wrong
 * about its own guards too. This reads the SHIPPED PAGES from disk and
 * asserts the contract from the outside.
 *
 * It is also the control that makes the Job 4 fix durable. Every historical
 * Discovery builder is a spent one-shot that refuses on its own anchors, so
 * nothing regenerates these pages today -- but if one is ever revived, or a
 * page is hand-edited back to the old shape, L1 turns that from a silent
 * accessibility regression into a red tick.
 *
 *   node atlas-tools/prove-landmarks.mjs
 *   node atlas-tools/prove-landmarks.mjs --dir /tmp/mutant   (capability proof)
 */
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const argDir = process.argv.indexOf("--dir");
const ROOT = argDir > -1
  ? path.resolve(process.argv[argDir + 1])
  : path.resolve(fileURLToPath(new URL(".", import.meta.url)), "..");

const DISCOVERIES = [
  "discovery-living-in-the-garden.html", "discovery-a-home-for-art.html",
  "discovery-open-your-home-to-art.html", "discovery-the-borrowed-garden.html",
  "discovery-house-as-power-station.html", "discovery-neighbourhood-parcel-house.html",
  "discovery-hidden-cars.html", "discovery-hidden-bins.html",
  "discovery-garden-retreat.html", "discovery-above-and-beyond.html",
  "discovery-your-home-on-screen.html", "discovery-driveway-income.html",
  "discovery-home-exchange.html",
];
const WRAPPED = ["index.html", "your-plot.html", "404.html"];
const SKIPPED = [...DISCOVERIES, ...WRAPPED];                 // get a skip link
const FOOTER  = ["index.html", "404.html", "about.html", "contact.html",
                 "privacy.html", "terms.html", "cookie-policy.html", ...DISCOVERIES];
const CAROUSEL = ["index.html", "404.html"];

const DISC025 = "disc025-borrowed-garden-check.html";
const DISC025_MAIN =
  "05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29";
const SEARCH_FROZEN = {
  // Re-stamped by JOB 6 (authorised Search V1 runtime change). Same
  // assertion, same strictness, new frozen value.
  "search.js":  "c7307b28d8629f278c021aaf105d8bd69f1c42db2890c51d9efd1b6acc63bf27",
  "search.css": "a0a1b07aaf6f729ab41873962a1ab1d5bf3b0a03defb1f8e21c0d9945de82e19",
};

let pass = 0, fail = 0;
const ok  = (n) => { pass++; console.log("  [PASS] " + n); };
const bad = (n, d) => { fail++; console.log("  [FAIL] " + n + (d ? "\n         " + d : "")); };
const read = (f) => readFileSync(path.join(ROOT, f), "utf8");
const sha  = (s) => createHash("sha256").update(s).digest("hex");
/* Comments are prose, not markup. A comment that quotes a tag or an id must
   never be counted as one -- that mistake cost this suite two false findings
   while it was being written. */
const code = (s) => s.replace(/<!--[\s\S]*?-->/g, " ");

console.log("\n  JOB 4 · LANDMARKS AND SEMANTICS — structural contract\n");
console.log("  reading from: " + ROOT + "\n");

// ---- L1 · exactly one main landmark on every governed public surface ------
for (const f of [...SKIPPED, "about.html", "contact.html", "privacy.html",
                 "terms.html", "cookie-policy.html", "discoveries.html",
                 "search.html"]) {
  if (!existsSync(path.join(ROOT, f))) { bad("L1 " + f, "missing"); continue; }
  const t = code(read(f));
  const opens = (t.match(/<main[\b\s>]/g) || []).length;
  const closes = (t.match(/<\/main>/g) || []).length;
  const roleMain = (t.match(/role="main"/g) || []).length;
  if (opens === 1 && closes === 1 && roleMain === 0) ok("L1 " + f + " has exactly one main landmark");
  else bad("L1 " + f, `<main> x${opens}, </main> x${closes}, role="main" x${roleMain}`);
}

// ---- L2 · all 13 public Discoveries, stated separately ---------------------
{
  const bads = DISCOVERIES.filter(f => (code(read(f)).match(/<main[\b\s>]/g) || []).length !== 1);
  bads.length ? bad("L2 all 13 public Discoveries have one main", bads.join(", "))
              : ok("L2 all 13 public Discoveries have exactly one main landmark");
}

// ---- L3 · the full-bleed sections survived the collapse --------------------
{
  const broken = [];
  for (const f of DISCOVERIES) {
    const t = read(f);
    const bleed = (t.match(/<section class="(imagine-photo|pn-bridge|spark|seam)[^"]*"/g) || []).length;
    const arts  = (t.match(/<div class="article">/g) || []).length;
    // every page keeps its full-bleed sections; the ones that had N mains now
    // have N article divs inside one main
    if (bleed === 0 && arts === 0) continue;               // single-main pages
    if (bleed === 0) broken.push(f + " lost all full-bleed sections");
  }
  broken.length ? bad("L3 full-bleed sections preserved", broken.join("; "))
                : ok("L3 every Discovery still carries its full-bleed sections");
}

// ---- L4 · no false tab interface on the carousel ---------------------------
for (const f of CAROUSEL) {
  const t = code(read(f));
  const falseTab = /<div class="d-dots"[^>]*role="tablist"/.test(t);
  const grouped  = /<div class="d-dots"[^>]*role="group"/.test(t);
  const realTabs = (t.match(/role="tab"/g) || []).length;
  if (!falseTab && grouped && realTabs === 0)
    ok("L4 " + f + " dots are a labelled group, not a false tablist");
  else bad("L4 " + f, `tablist=${falseTab} group=${grouped} role=tab x${realTabs}`);
}

// ---- L5 · footer heading hierarchy ----------------------------------------
for (const f of FOOTER) {
  const t = code(read(f));
  const h4 = (t.match(/<h4>(Navigation|Company|Social|Contact)<\/h4>/g) || []).length;
  const h2 = (t.match(/<h2>(Navigation|Company|Social|Contact)<\/h2>/g) || []).length;
  if (h4 === 0 && h2 === 4) ok("L5 " + f + " footer headings are h2");
  else bad("L5 " + f, `h4 x${h4}, h2 x${h2}`);
}

// ---- L6 · footer navigation landmark --------------------------------------
for (const f of FOOTER) {
  const t = code(read(f));
  const old = (t.match(/<div class="footer-cols">/g) || []).length;
  const nav = (t.match(/<nav class="footer-cols" aria-label="Footer">/g) || []).length;
  if (old === 0 && nav === 1) ok("L6 " + f + " footer links are a named nav landmark");
  else bad("L6 " + f, `div x${old}, nav x${nav}`);
}

// ---- L7 · skip link present, targeted and unobtrusive ---------------------
for (const f of SKIPPED) {
  const t = code(read(f));
  const link = (t.match(/<a class="pn-skip" href="#pn-main">/g) || []).length;
  const target = (t.match(/id="pn-main"/g) || []).length;
  const css = /\.pn-skip\{[^}]*left:-9999px/.test(t);
  const focus = /\.pn-skip:focus\{/.test(t);
  if (link === 1 && target === 1 && css && focus)
    ok("L7 " + f + " skip link -> #pn-main, hidden until focused");
  else bad("L7 " + f, `link x${link} target x${target} offscreenCSS=${css} focusCSS=${focus}`);
}

// ---- L8 · the skip link is the first thing a keyboard reaches -------------
for (const f of SKIPPED) {
  /* Comments are blanked length-preservingly first: a comment that MENTIONS
     <body> or a link must not be mistaken for one. This is the same trap that
     put the skip link inside a comment on your-plot.html. */
  const t = read(f)
    .replace(/<!--[\s\S]*?-->/g, (m) => " ".repeat(m.length))
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, (m) => " ".repeat(m.length))
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, (m) => " ".repeat(m.length));
  const b = t.search(/<body[^>]*>/);
  const after = t.slice(b);
  const firstFocusable = after.search(/<(a\s[^>]*href|button|input|select|textarea)/i);
  const skipAt = after.indexOf('<a class="pn-skip"');
  if (skipAt > -1 && skipAt === firstFocusable)
    ok("L8 " + f + " skip link is the first focusable element");
  else bad("L8 " + f, `skip at ${skipAt}, first focusable at ${firstFocusable}`);
}

// ---- L9 · no duplicate ids in real markup ---------------------------------
for (const f of [...SKIPPED, ...FOOTER]) {
  const t = code(read(f));
  const ids = [...t.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  const dup = [...new Set(ids.filter(i => ids.filter(x => x === i).length > 1))];
  dup.length ? bad("L9 " + f + " duplicate ids", dup.join(", "))
             : ok("L9 " + f + " has no duplicate ids");
}

// ---- L10 · DISC-025 frozen main, byte for byte ----------------------------
{
  const t = read(DISC025);
  const i = t.indexOf("<main"), j = t.lastIndexOf("</main>");
  const h = sha(t.slice(i, j + 7));
  h === DISC025_MAIN ? ok("L10 DISC-025 frozen <main> hash unchanged")
                     : bad("L10 DISC-025 frozen <main>", h + " != " + DISC025_MAIN);
}

// ---- L11 · Search V1 frozen artefacts -------------------------------------
for (const [f, want] of Object.entries(SEARCH_FROZEN)) {
  const h = sha(readFileSync(path.join(ROOT, f)));
  h === want ? ok("L11 " + f + " frozen hash unchanged") : bad("L11 " + f, h);
}

// ---- L12 · the Job 1 journey exits are still there ------------------------
{
  const exits = ["disc005-home-exchange.html", "disc014-driveway-income.html",
    "disc022-hidden-cars-check.html", "disc023-buy-original-irish-art.html",
    "disc024-open-your-home-to-art.html", DISC025,
    "disc026-compute-readiness-check.html", "disc026-power-station.html",
    "disc027-neighbourhood-parcel-house.html", "disc029-hidden-bins-check.html"];
  /* The capability proof caught this guard BLIND. It asked only whether the
     marker was present, and the marker appears THREE times per page (BEGIN,
     END and the commentary). Deleting one occurrence left the page still
     "containing" it and the suite passed a broken tree. It now asserts the
     exact census and the nav landmark Job 1 installed, so losing any part of
     the region is visible. */
  const broken = exits.filter(f => {
    const t = read(f);
    return (t.match(/PLOTNUA JOURNEY EXIT v1/g) || []).length !== 3
        || (t.match(/<nav class="pnx-nav" aria-label="PlotNua">/g) || []).length !== 1;
  });
  broken.length ? bad("L12 Job 1 journey exits intact", broken.join(", "))
                : ok("L12 all 10 Job 1 journey exits intact (3 markers + 1 nav each)");
}

// ---- L13 · Garden Register switch -----------------------------------------
{
  const t = read(DISC025);
  /INTEREST_PUBLIC\s*=\s*false/.test(t)
    ? ok("L13 INTEREST_PUBLIC remains false")
    : bad("L13 INTEREST_PUBLIC", "not false");
}

console.log("\n  " + pass + " passed, " + fail + " failed\n");
process.exit(fail === 0 ? 0 : 1);
