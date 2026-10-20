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
  // discovery-open-your-home-to-art.html is now a redirect to A Home for Art (13 Oct 2026)
  "discovery-the-borrowed-garden.html",
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
// 19 Oct 2026 (Phase 4, founder-approved): the homepage carousel is replaced
// by the Discovery showcase, so index.html leaves CAROUSEL and is held to the
// stronger SHOWCASE contract in L4 below. 404.html keeps its carousel.
const CAROUSEL = ["404.html"];
const SHOWCASE = "index.html";

const DISC025 = "disc025-borrowed-garden-check.html";
// Re-stamped 12 October 2026 for the founder-authorised G6 preparation
// amendment applied by atlas-tools/build-g6-owner-register.py (D2/D3/D4),
// recorded in governance/DISC-025-V2-POST-FREEZE-AMENDMENT-2-2026-10-12.md.
// Same assertion, same strictness, new frozen value. The previous value was
// 05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29.
// Re-stamped again 12 October 2026 for the founder-authorised G6 entry-link
// UX change (atlas-tools/build-g6-entry-links.py): one secondary link added
// under START THE CHECK. Previous value was
// 338f6f0c3070f86ae008bc82214c666a10394f1ff60a34765ad5be45431bd7ab.
// Re-stamped again 12 October 2026: the entry link became an outlined
// secondary pill (atlas-tools/build-g6-discover-button.py). Previous value
// was 4aec70baa55c7733eb34f1159e7a669b034211d8417191880de39567f3bc48d5.
const DISC025_MAIN =
  "15924561a4daeb23ade8bbc3e046a66c0c8b0af74d633f339a13dd1ff58a9fc2";
const SEARCH_FROZEN = {
  // Re-stamped by JOB 6 (authorised Search V1 runtime change), then again on
  // 11 October 2026 for the authorised no-results copy correction applied by
  // atlas-tools/build-search-zero-state.py. Same assertion, same strictness,
  // new frozen value. The previous value was
  // c7307b28d8629f278c021aaf105d8bd69f1c42db2890c51d9efd1b6acc63bf27.
  // Re-stamped again on 13 October 2026 for the founder-approved mobile
  // floating navigation (Option B: compact logo and Search icon, hide on
  // downward scroll), which lives in these two shared files. Same assertion,
  // same strictness. Previous values: search.js
  // 3e91e8793f40159082267b2190c02edb923c21618e1e8aa33715ad4db8f7901d,
  // search.css a0a1b07aaf6f729ab41873962a1ab1d5bf3b0a03defb1f8e21c0d9945de82e19.
  // Re-stamped 14 October 2026 for the authorised OGNYX public integration:
  // productRoute() honours a product's own route (wellness products, which
  // have no PlotNua product page) and the "sauna" possibility-only special
  // case is retired now that a governed corpus answers it. Previous value:
  // 53a462294de862f8563c2698cf14979874d276139c6ebc2fef0c1d135ba40d88.
  "search.js":  "7ae73e451c516dae274cc53d61ab98b4d86310f41fbdfa78ee96f880cacfd7ab",
  "search.css": "5923bcbcf3ccf31224f662d860d5f59d6f420ff9ace128f397b092b4a603fd55",
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

// ---- L2 · all 12 public Discoveries, stated separately ---------------------
{
  const bads = DISCOVERIES.filter(f => (code(read(f)).match(/<main[\b\s>]/g) || []).length !== 1);
  bads.length ? bad("L2 all 12 public Discoveries have one main", bads.join(", "))
              : ok("L2 all 12 public Discoveries have exactly one main landmark");
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
    // ONE DECLARED SUBSTITUTION (14 Oct 2026, Garden Retreat restructure
    // brief). Its three full-bleed photographs were moved, deliberately, into
    // the option cards; build-garden-retreat-restructure.py owns that page's
    // structure (GR1-GR9). Not an exemption from losing pictures: each of the
    // three must still be on the page, inside a card, or this fails.
    if (bleed === 0 && f === "discovery-garden-retreat.html") {
      const cardImgs = ["45a270b7716e4a94", "83da38d51a03414d", "5d6a5fd0aab3d9ce"]
        .filter(h => new RegExp('<figure class="gr-card-img">'
          // a hash-bound WebP derivative wrap (build-hero-webp-derivatives.py, 20 Oct 2026)
          // may sit between the figure and its JPEG <img>; the <img> itself must still be there
          + '(?:<picture style="display:contents"><source type="image/webp" srcset="assets/img/' + h + '-960w\\.webp[^"]*" sizes="[^"]*">)?'
          + '<img src="assets/img/' + h + '\\.jpg"').test(t));
      if (cardImgs.length !== 3) broken.push(f + " lost its full-bleed photographs without the declared card substitution");
      continue;
    }
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

// ---- L4 · the homepage showcase: no tab interface, every Discovery reachable
{
  /* What the carousel rule protected (no false ARIA tab pattern, and every
     Discovery reachable from the homepage control) is asserted for the
     showcase that replaced it -- more strictly: no tablist, tab or tabpanel
     ANYWHERE on the page, and each public Discovery (the independent list at
     the top of this file) linked exactly once as a showcase card, plus the
     "Explore all Discoveries" route to the Library. */
  const t = code(read(SHOWCASE));
  const tabRoles = (t.match(/role="(tablist|tab|tabpanel)"/g) || []).length;
  const ariaSel = (t.match(/aria-selected=/g) || []).length;
  const a = t.indexOf('<section class="discover p4-showcase" id="discover"');
  const sect = a > -1 ? t.slice(a, t.indexOf("</section>", a)) : "";
  const cards = [...sect.matchAll(/<a class="p4s-go" href="([^"]+)">/g)].map(m => m[1]);
  const missing = DISCOVERIES.filter(d => cards.filter(c => c === d).length !== 1);
  const extra = cards.filter(c => !DISCOVERIES.includes(c));
  const all = /<a class="p4-btn p4-btn-primary p4s-cta" href="discoveries\.html">/.test(sect);
  if (sect && !tabRoles && !ariaSel && !missing.length && !extra.length && all)
    ok("L4 " + SHOWCASE + " showcase: no tab interface, all " + DISCOVERIES.length + " Discoveries linked once, Library route present");
  else bad("L4 " + SHOWCASE, `section=${!!sect} tabRoles=${tabRoles} aria-selected=${ariaSel} missing=[${missing.join(",")}] extra=[${extra.join(",")}] exploreAll=${all}`);
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
  // Inverted by the opening commit (opening/g6-register): the register is
  // open by founder decision. On release/g6-register this still asserts false.
  /INTEREST_PUBLIC\s*=\s*true/.test(t) && !/INTEREST_PUBLIC\s*=\s*false/.test(t)
    ? ok("L13 INTEREST_PUBLIC is true (register opened by founder decision)")
    : bad("L13 INTEREST_PUBLIC", "not true");
}

console.log("\n  " + pass + " passed, " + fail + " failed\n");
process.exit(fail === 0 ? 0 : 1);
