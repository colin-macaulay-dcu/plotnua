#!/usr/bin/env node
/**
 * THE IMAGE PROVENANCE GUARD · P1–P14
 * ====================================
 * Closes the blind spot at atlas-tools/validate-image-rights.js:395:
 *
 *     if (!/^https?:\/\//i.test(u)) continue;   // relative = PlotNua's own
 *
 * That assumption was sound when it was written -- everything local was
 * PlotNua's own artwork. It means the rights gate examines 40 externally
 * hosted supplier images and skips 85 locally hosted ones entirely. The
 * moment an AI illustration lands as a local file the assumption becomes
 * "relative = unexamined", and a laundered supplier photograph saved to
 * assets/img/ would pass silently. This guard is what makes a local image
 * declared rather than merely unexamined.
 *
 * IT IS NOT A RIGHTS GATE, AND MUST NEVER BECOME ONE. P11 asserts that:
 * nothing here can produce a permission, a provenance record can never
 * authorise supplier imagery, and the two files are read for two different
 * questions. The rights gate keeps its own job; this one keeps its own.
 *
 * IT FAILS CLOSED. Exit 1 = a violation. Exit 2 = the facts could not be
 * established, which is also a failure: a guard that passes when it is
 * confused is not a guard.
 *
 *   node atlas-tools/validate-image-provenance.js [--root PATH]
 *
 * The legacy backlog count is printed on every run and in the CI summary.
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { posix } from 'node:path';
import { createHash } from 'node:crypto';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => {
  const i = process.argv.indexOf('--' + n);
  return i === -1 ? d : process.argv[i + 1];
};
const ROOT = arg('root', dirname(HERE));
const REGISTER = join(ROOT, 'image-provenance-records.json');
const RIGHTS = join(ROOT, 'image-rights-manifest.json');
/* H2, 20 Oct 2026: permission to ADAPT a supplier photograph into a composite.
   Read only for the licensed-photography exception (P6, P10, P13) and to add
   the licensed organisations to the names P6 and P10 protect. */
const LICENCES = join(ROOT, 'image-adaptation-licences.json');

let pass = 0, fail = 0;
const ok  = (n, d) => { pass++; console.log(`  PASS  ${n}${d ? '  [' + d + ']' : ''}`); };
const bad = (n, d) => { fail++; console.log(`  FAIL  ${n}${d ? '  [' + d + ']' : ''}`); };

function refuse(why) {
  console.log('\nIMAGE PROVENANCE GUARD');
  console.log('='.repeat(74));
  console.log('  INSTRUMENT UNAVAILABLE: ' + why);
  console.log('  Nothing was established. A guard that passes when it cannot');
  console.log('  establish the facts is not a guard.');
  process.exit(2);
}

/* ── the register ─────────────────────────────────────────────────────── */
if (!existsSync(REGISTER)) {
  refuse('image-provenance-records.json is missing. Every locally hosted '
         + 'image would be unexamined.');
}
let reg;
try { reg = JSON.parse(readFileSync(REGISTER, 'utf8')); }
catch (e) { refuse('the provenance register is not valid JSON: ' + e.message); }

const records = Array.isArray(reg.records) ? reg.records : null;
const legacy = Array.isArray(reg.legacy_undeclared) ? reg.legacy_undeclared : null;
if (!records || !legacy) {
  refuse('the register has no records array and/or no legacy_undeclared array');
}

/* ILLUSTRATION_VERIFIED_NOT_AI (founder decision PN-FDR-2026-10-26-H6-HOME, 26 Oct 2026): an image
   made without any generative model (e.g. a 3D render of typeset lettering).
   The register has reserved its label, 'Illustration', since 11 Oct 2026.
   Checked by P5b: tool, date, method and a named human review. */
/* FOUNDER_ORIGINAL_ARTWORK (founder decision, 29 Oct 2026): a photograph of an original artwork
   created and owned by PlotNua's founder. Not AI, not a supplier image. Checked by P5c: the
   creator, the owner's attestation, the photograph and its processing, the visible credit and the
   photographer (recorded as NOT YET CONFIRMED until the founder confirms who took it). */
/* ARTIST_SUPPLIED_ARTWORK (founder decision, 29 Oct 2026; PlotArt artist galleries): a published derivative of
   a photograph supplied by a PlotArt artist through PlotArt Studio, under the Gallery Publication and Image
   Licence. Written by atlas-tools/plotart-gallery-ingest.py; checked by P5d. Public fields only: the record
   names the artist's public slug and an opaque permission reference, never personal data. */
const ASSET_CLASSES = ['SUPPLIER_IMAGE', 'AI_ILLUSTRATION', 'ILLUSTRATION_VERIFIED_NOT_AI', 'FOUNDER_ORIGINAL_ARTWORK', 'ARTIST_SUPPLIED_ARTWORK'];
const ARTIST_LICENCE_VERSIONS = ['PA-GPIL-2026-10-29'];
/* product-card is DELIBERATELY ABSENT. The founder's rule becomes a
   vocabulary restriction rather than a convention somebody has to remember:
   enabling it is a schema change with its own approval, not an oversight
   away. */
/* FOUNDER-ATTESTED CONTEXT · THE GARDEN ROOM PRICES HERO (PN-FDR-2026-10-23-GRP-HERO).
   The Garden Room Prices hero: an original AI illustration whose exact
   prompt is unavailable and whose reference history is uncertain (supplier
   photographs were in the generation conversation). Instead of a prompt and
   reference_inputs -- which cannot be stated truthfully -- its records carry
   prompt_status UNAVAILABLE, a reference_disclosure with status UNCERTAIN and
   a resemblance_review. ONLY these six files may use that form, and these six
   may use no other. This is not a way to declare images: every new AI
   illustration records its prompt verbatim at creation. */
const FOUNDER_ATTESTED_GRP = {
  decision: 'PN-FDR-2026-10-23-GRP-HERO',
  sha256: new Set([
    'f5ca159b61a95bb129291a693dd1aab37328eadfa076a2b777bb683f5631be7d',
    'a92f40549c52b9f73dfdf9611d9aa1f35e163825a9fc18a8e898c847bc1633ff',
    'a016f563d6f422e42c4f212f8fd929cd28523e304c72171c103064ef27ef97fb',
    'd6a86a11293346b51d49386472803160e5d23d937202ebcc0fdb562c13de6edc',
    'feca00626ff061699a55dd8d1882d74efa0eda57097790f0ce059f4be62ac5b5',
    'e0ca487506f2db412ad00daaa6a60cfec3b01ec4d48e1a2308c30e548c56a531',
  ]),
  surfaces: ['discovery'],
};
/* FOUNDER-ATTESTED CONTEXT · THE H6 HOMEPAGE GARDEN (PN-FDR-2026-10-26-H6-HOME,
   founder approval 26 Oct 2026). Its master is the founder's ChatGPT image, whose
   prompt is unavailable and whose reference inputs are not recorded, so the same
   founder-attested form is the only truthful record. ONLY these eighteen files,
   and ONLY on the homepage. Not a way to declare future images. */
const FOUNDER_ATTESTED_H6 = {
  decision: 'PN-FDR-2026-10-26-H6-HOME',
  sha256: new Set([
    '5ddc50bcddafb2c4d6600a19f00ad47249017f10e625d781529b3638e39dd5f0',
    '731420977c1cf58cd67d3de66d6eb923d7e865d93246f4d869c58f3e7ab63317',
    'fa3eb93ad06f6f4e4fd348e986ee9c9d9615c4c49a9dcc99da1b441ed88c84e9',
    'dbda9eb6e02e06ff55ba4e5b244002891694d0ab3a4edb336318b35be78e230e',
    '9e4d8ac4abbab1a505e9965aacda10930e9a4af7a718a50d1282dd2067785463',
    '5157222f9debe404a47eb4caddefa8748222bd053d2acc3b189a5056ca3783c5',
    'ed6018b5810f2acf685f31ee484fb86d1d57986446c5c3a85d6cacfbaf678789',
    '80c09c8b62d1fc1fde341076bdbb0e444fbb00b42aec956c14b325693cd8f1fa',
    'dce97ce3c290507b1f67511b4aec7c84a6bbd3973ef616b34984e446b39dd0c1',
    'f8f38fcfe84eac6c132b137236fcf7ca8ba52cbae8931260011f03f003ca4e4b',
    'ba69c8276bf45f0203463d8e2a2647d1fbeb7ab58365789ace3aa41008120f47',
    'c779c33d5c7b29ebebf6bda8c94b974dff6d2675d80595814ec433158def4ab7',
    'd69a16405a572c7de4a569412a2da006191f8c220f54f2a4fee23a0d2ca3f4fa',
    '325c8358507a412108563c7a0b7eba51bd0d2b75e12f0f044dab4e523d4b6eb0',
    'b95f0f7c7d97acecdb79aa7fec2b1b7aac1c702d06e4e5d56978443f943b1818',
    'e1ba51f825285d4615266dd6965078512e6991a1ca9d1db8dfac66d2cf82fb68',
    '4b5662dabf1b39d70f61fcdffbfdb9ce9448fd1a6a172b473bc7cad6019110ab',
    '125dfb49ed899409a60154700e227ab9d07b96bc9b62be74ba4263b5428318fa',
  ]),
  surfaces: ['homepage'],
};
/* FOUNDER-ATTESTED CONTEXT · DISC-031 THE NATURAL SWIMMING GARDEN (PN-FDR-2026-10-26-DISC031,
   PENDING founder signature). The four masters were supplied in the founder build instruction of
   26 Oct 2026 without their tool, prompts or reference history, so until the founder supplies those
   the founder-attested form is the only truthful record. ONLY these web encodings (thirteen, plus fourteen hero-slider derivatives of the same two masters, 30 Oct 2026), and
   ONLY on the discovery and library-card surfaces. The records are added by
   atlas-tools/declare-disc031-provenance.py from the signed declaration
   governance/DISC-031-PROVENANCE-DECLARATION-DRAFT-2026-10-26.json; until then this pin admits
   nothing, because no record carries the decision. Not a way to declare future images. */
const FOUNDER_ATTESTED_DISC031 = {
  decision: 'PN-FDR-2026-10-26-DISC031',
  sha256: new Set([
    'dadf65fbd5032ab99b8eaaa7958a3dfc70fcf2ad22470e4edac4805b0219dc01',
    'bd4c5d5f9cb9793d8fd17e5d6018f07167a2cfee1612bad044cadd1ca46aea03',
    '9435a1ddcdde1b7b85e9153d1f0cd079959a040a067875c994a46b5c030cee50',
    '529cc02add7b357e909ca8159165d962996e72fa1855cba8e5850929ff809311',
    '6ea8a0cbee36991b4e495ec84cb83af8ef7d4406c6415d9eb837410c8a79a0eb',
    '15bb786bc4f073984929f4f6df0dcdf257ae89af7cbff7de5cbb09829d10b182',
    '28f4a0a4a338fe373d7b2baff83f530109c10e46f19e78811d5f4c75fa21ad91',
    '4188e1e7120e57041801d010c99308cea318bffcd42ebd3a331728c3200851e3',
    'e7ccd4f36d4d4718f459ede823a65fbff02f77446e350fbee90130674db8b3fa',
    '89599340a81d344d6cb894df9905ac26d653934bcd565eb99fba7e12e31e851e',
    '521a6d3d372047b700b88b3fc9956b55da751e14a280bf76005fd8c87f691e6d',
    '85b9df7bf4bfca819a39523b5beb869637c12e94b515f6cf8a52f05062911102',
    // the V2 diagram's two panels, exact crops of the same master (26 Oct 2026)
    '001dcae58abd79f20c41ba30ebaf3b77d3da71c6507523f87d590885b80023d9',
    '2efb18a0ab94104ff1908d8e60ffdd58f2c854866908984bb6371c91ff605300',
    '5daf8859e62ff93b7613b84e940e3b87d66361a88402691cd0183fbbfe2bad6f',
    '42d48d0de2446df8b57524d84441196cf56417d66738daa6fbcfbbbd959a2081',
    // hero-slider web derivatives of the pinned BEFORE / POSSIBLE 1536 encodings (AVIF 960/1200/1536,
    // WebP 1200, 4:5 phone crops): founder Pass 2 performance instruction, 30 Oct 2026
    '6993006506aff51ea475517e6815afdeb707ed3fc164cb9a6f720378603e3528',
    'bc71842ef94e94cd37188388c7e963070c0e4ad5959c0a9a9516dad1a710dc33',
    '63962cd9709879b22e382a313cef893b11f7e7b59ce9e10dfc6e11e0c5e62339',
    '7eb7fe49e92731748de91697314194d9a46b14111318a831d10a681d73180a33',
    '729bff54d70076787245f5aa40362dd3e50f1b2c920a5349931cb8ebe67e765f',
    'd4711b2ad86847dbb02e26f575d4ed32255c5ba4443ff80fe3854698e735e722',
    'e0d11f16743876d700a6070036622eb2c287d5029d8e924eb138a057e9699108',
    '30f0c6cb9f6a536cdc42685fbcf7558b839bd707ba517807c97739f7ae00c880',
    '3e719a1e73f312be7a14a2e25be689101bab33f7e2dc95fe89a63ba12d59179c',
    '4e188983f3b42c7cd178a46f7a60614b285a5aa06f5555a0770c01bc27fc7361',
    '97f5048fdd73cf12d06e9a77132772d78dee4bbd04c99cd7ecdbca506f5232c0',
    'cea11bc9e4691a4cf7a35a7808a8911c3c4ae08954a497d45fc76d0b80ec221b',
    '79a57e6ea958b8076fe6da635558225cf648408f481a4489592a26872c3c542c',
    '4bb302188a8168b51344bf81bf1471641b7ac9263e441d58fb7625215aefe1dc',
  ]),
  surfaces: ['discovery', 'library-card'],
};
/* FOUNDER-ATTESTED CONTEXT · DISC-033 THE HIDDEN FLOOD BARRIER (PN-FDR-2026-10-27-DISC033;
   release candidate, 27 Oct 2026). Founder statements of 27 Oct 2026: both masters made with
   ChatGPT; IMG-02 after IMG-01; no third-party supplier or listing photographs supplied; the
   exact derivation is not verified and the prompts were not supplied. ONLY these thirteen web
   derivatives (badge-retouched, documented in each record), and ONLY on the discovery and
   library-card surfaces. Declaration: governance/DISC-033-PROVENANCE-DECLARATION-2026-10-27.json.
   Not a way to declare future images. */
const FOUNDER_ATTESTED_DISC033 = {
  decision: 'PN-FDR-2026-10-27-DISC033',
  sha256: new Set([
    'd613eecbd2058c61075436459694604055b9f13b1ac1bb221badde5828fb2e02',
    '40133dea4f0a7ecd0bcce0a60050b2a18eaaec39c20e05a7e6bf0e717829aeef',
    'c40babf806476e07a7fd1ae3e30bf81a41337893fcac85eabb7c64c54f54ad30',
    '3d9d3bfbd38de7ca85f082b2a243464bef21f8553695a97597e87f96c09bc0ac',
    'ef847f0fde4cac77277f45414f271b282b5d2ed519429dfd8d54153cf53c03a0',
    '9275eedd9585fb0e001bfaf3084a4eb50e813743c6389280daa9b3134416b678',
    'c1c80efd7c3f39309a92fca1466cc317086f7dec3180b4981231a764a098c532',
    'cb826c5b34159f74514124c4dc59d042f8ebef074f8c8b2615367378fa27e003',
    'd1d2abf2b3f2737600ed4934056e029ebc0e88d54d529f2901a8ccbd7cde8877',
    '99c2cf1ecc026ef88f3ccf4522e12ad8540503de0a3997b49171b1d816286df2',
    '0e508779cbab580cdac03300ef9516b5549b7a49888945ce0b6aea10d04ad5ba',
    '4dcb36804a6e7f29175835a82c4428d86536b6d1214c5a67d8fd3b55e674ccf1',
    '1b9e7e6b0e66eacf2e62ad0c05c75e4e860647010b794b0c8fcfe7a39b58aa6a',
    // hero-slider web derivatives of the pinned encodings (AVIF 768/1024/1536 and 4:5 M-640/M-819):
    // founder Pass 2 Release 2 performance instruction, 30 Oct 2026
    '47b19989e79d62224fcc171a5692f2028a7b5c2e8aadfc4a6c37c28bc930e5f7',
    'cb0097719d1819297765a44e513169859261e7463c2f5377f60fb272c5a24284',
    '15b27b43e02b87ffd9aaff17f7277d492eafe55ae79dd7b3dc69f180657360b9',
    'b58f3de01df55ca7843719689546dcb4f050c4c5f01f55d1196b0ac0d425730f',
    '4f2034d00cf3ff606c3a93379ff53694d7a6aa993fa993a850a82c6587f04cce',
    'e56284f3601790a93dd8f1390f955b8c7f972441fdfa0bb8eeb19e2e3a0aaff9',
    '10864af5a82675d6cc85193e48051781347cff9b01572f2473f7667a7db71246',
    'b3b75b60ecb34b6a1f320627b2d015a4f2d353f97700ca1b1d7f43397bd4cbc2',
    'e1576b70c4bca51118b633acc6aff25229c60f08eb0dc4b4275832f3362d0dd6',
    '60954a0b01e9843998f5abe1c3e3cd3ec7c182c861828fe4122322c623ddced8',
  ]),
  surfaces: ['discovery', 'library-card'],
};
/* FOUNDER-ATTESTED CONTEXT · DISC-032 THE SUPPER CLUB AT HOME (PN-FDR-2026-10-27-DISC032).
   The founder approved the C1 v3 / C2 pair, its provenance chain and the 0.2 px tolerance exception
   on 27 Oct 2026, and instructed that the declaration be applied after validation (Phase 2). The
   prompts were not supplied and the credentials do not record conversation inputs, so the
   founder-attested form is the only truthful record. C1 v3 is a deterministic geometric correction of
   C1 v2 and carries no OpenAI credentials of its own. ONLY these nine web encodings, and ONLY on the
   discovery and library-card surfaces. The records are added by atlas-tools/declare-disc032-provenance.py
   from governance/DISC-032-PROVENANCE-DECLARATION-2026-10-27.json. Not a way to declare future images. */
const FOUNDER_ATTESTED_DISC032 = {
  decision: 'PN-FDR-2026-10-27-DISC032',
  sha256: new Set([
    '3ffd2642ddd0d46873149d37e643d6546bb83ac5a8cd386aaac441bc2e438faa',   // DISC-032-before-768.webp
    '48f892c1c66e6f64c20f8fbd1bfec629d8a53f48bea7ee91dd547b4fa38c396e',   // DISC-032-before-1024.webp
    'eb2e1efe5f14ceab51fd551f78c15b46f22e4230f1546a60b326390a50121007',   // DISC-032-before-1536.webp
    'c0457073b141357e3669763a0b264c6cfb47dfce3fd30595c414be06eb75e45e',   // DISC-032-before-1536.jpg
    'ef0bfb0964b12dfe8e59eb870717c81b351d9ee23883c18fe1d69f74f470d142',   // DISC-032-possible-768.webp
    '13ae00e506e334068aa0d2fcf3f6d5b0c3c79043d95ac2b432bee76dfa0649d5',   // DISC-032-possible-1024.webp
    '5a2dcaedea5913e6fb63de61ad2d252a72be9cf795327235b3e0e0813455d75f',   // DISC-032-possible-1536.webp
    '32159a386d6adfc4bcb0110281446a8239cfed757505d08a51f7f8cd0c54e6f2',   // DISC-032-possible-1536.jpg
    '1b86269f66388e9295633935ce8f2af7d489fb4206ed9b965dd137ad20a7a733',   // DISC-032-og-1200x630.jpg
  ]),
  surfaces: ['discovery', 'library-card'],
};
/* PN-FDR-2026-10-29-PLOTART-LG (founder, 29 Oct 2026): the PlotArt Living Gallery composite. The room was
   generated with ChatGPT (prompt unavailable; the founder supplied a photograph of his own painting as the
   reference); the AI rendition of the painting was then replaced by the actual photograph of the painting.
   Pinned to this one file and the PlotArt surface only. */
const FOUNDER_ATTESTED_PLOTART_LG = {
  decision: 'PN-FDR-2026-10-29-PLOTART-LG',
  sha256: new Set(['f4861333a80fda7f704fd3c57d0a2b8f18db589b8505eb11192ac05c08d8d0f9']),
  surfaces: ['plotart'],
};
const FOUNDER_ATTESTED_ALL = [FOUNDER_ATTESTED_GRP, FOUNDER_ATTESTED_H6, FOUNDER_ATTESTED_DISC031, FOUNDER_ATTESTED_DISC033, FOUNDER_ATTESTED_DISC032, FOUNDER_ATTESTED_PLOTART_LG];
const attestedFor = h => FOUNDER_ATTESTED_ALL.find(x => x.sha256.has(String(h)));
/* 'gridnua' (founder approval of the GridNua limited launch, 29 Oct 2026): the GridNua initiative pages. */
const PERMITTED_SURFACES = ['discovery', 'library-card', 'homepage',
                            'about', 'journey', 'preview', 'plotart', 'gridnua',
                            'plotart-artist-gallery', 'plotart-virtual-gallery'];
const IMG_EXT = /\.(jpe?g|png|webp|avif|gif|svg|ico)$/i;
/* PlotNua's own origins. An absolute self-reference is still one of our
   images and still needs declaring: twitter:image points at
   https://plotnua.ie/assets/og/... on 23 pages, which a "skip anything
   absolute" rule would have missed entirely. */
const SELF_ORIGINS = [/^https?:\/\/(www\.)?plotnua\.ie\//i];
/* Not part of the published site. */
const SKIP_DIRS = new Set(['.git', 'node_modules', 'outputs', '.github',
                           '__pycache__', 'atlas-tools']);

/* ── every local image a published page can show ──────────────────────────
   WIDENED 11 October 2026 after a coverage audit, and four of the gaps were
   real and in use:

     <link rel="icon|apple-touch-icon" href>   122 references, never scanned
     <meta twitter:image>                       23 references, never scanned
     site.webmanifest icons                      2 images, not HTML at all
     pages below the root                       12 files, never walked

   The first version walked only readdirSync(ROOT) for *.html and read four
   attribute shapes. The rights gate next to it walks recursively, so the two
   disagreed about what "published" means -- which is itself a defect.

   The remaining mechanisms below are covered PRE-EMPTIVELY: <img srcset>,
   imagesrcset, image-set(), <video poster>, <input type=image>, <object
   data>, xlink:href, SVG <image href>, msapplication-TileImage and
   JavaScript .src assignments to literal paths. None is in use today. That
   is exactly why they are covered -- the ratchet exists for the image
   somebody adds next month, and a mechanism nobody uses yet is the one most
   likely to slip in unexamined. */
function publishedLocalImages() {
  const found = new Map();      // asset path -> Set(pages)
  let pages = 0;

  const sources = [];
  (function walk(dir, rel) {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (SKIP_DIRS.has(e.name) || e.name.startsWith('.')) continue;
      const full = join(dir, e.name);
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) walk(full, r);
      else if (/\.(html|webmanifest)$/i.test(e.name)) sources.push([full, r]);
    }
  })(ROOT, '');

  for (const [full, rel] of sources) {
    let body;
    try { body = readFileSync(full, 'utf8'); } catch { continue; }
    pages++;
    body = body.replace(/<!--[\s\S]*?-->/g, ' ');   // comments are not published
    const urls = new Set();
    const addSet = v => v.split(',')
      .forEach(part => urls.add(part.trim().split(/\s+/)[0]));

    /* ---- in use today ---- */
    for (const m of body.matchAll(/<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<source\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<meta[^>]+(?:property|name)=["'](?:og:image|twitter:image|msapplication-TileImage)["'][^>]+content=["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<link\b[^>]*\brel=["'][^"']*icon[^"']*["'][^>]*\bhref\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<link\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*\brel=["'][^"']*icon[^"']*["']/gi)) urls.add(m[1]);
    // the web manifest's icon list
    for (const m of body.matchAll(/"src"\s*:\s*"([^"]+)"/gi)) urls.add(m[1]);
    // JS assigning a literal path
    for (const m of body.matchAll(/\.src\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);

    /* ---- covered pre-emptively, not in use today ---- */
    for (const m of body.matchAll(/<img\b[^>]*?\bsrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/\bimagesrcset\s*=\s*["']([^"']+)["']/gi)) addSet(m[1]);
    for (const m of body.matchAll(/image-set\(\s*["']?([^"')]+)["']?/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<video\b[^>]*?\bposter\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<input\b[^>]*?\btype=["']image["'][^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<object\b[^>]*?\bdata\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/<embed\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/(?:xlink:)?href\s*=\s*["']([^"']+\.(?:jpe?g|png|webp|avif|gif|svg|ico))["']/gi)) urls.add(m[1]);
    for (const m of body.matchAll(/\bdata-(?:src|bg|image|background)\s*=\s*["']([^"']+)["']/gi)) urls.add(m[1]);

    for (let u of urls) {
      if (!u) continue;
      if (u.startsWith('data:')) continue;             // inline, nothing to declare
      const self = SELF_ORIGINS.find(re => re.test(u));
      if (self) u = '/' + u.replace(self, '');         // our own origin, our own image: site-root path (30 Oct 2026: from a page below the root it was resolved against the page's folder)
      else if (/^(https?:)?\/\//i.test(u)) continue;    // somebody else's: the rights gate's job
      u = u.split('?')[0].split('#')[0];
      /* A relative path resolves against the page's own folder (29 Oct 2026: the first image on a
         page below the site root, plotart/index.html). Root-relative and root-level paths are unchanged. */
      const pageDir = rel.includes('/') ? rel.slice(0, rel.lastIndexOf('/') + 1) : '';
      u = u.startsWith('/') ? u.replace(/^\/+/, '') : posix.normalize(pageDir + u.replace(/^\.\//, ''));
      if (!u || !IMG_EXT.test(u)) continue;
      if (!found.has(u)) found.set(u, new Set());
      found.get(u).add(rel);
    }
  }
  return { found, pages };
}
const { found, pages } = publishedLocalImages();
if (!pages) refuse('no published HTML page was found under ' + ROOT);

const byAsset = new Map();
for (const r of records) if (r && r.asset) byAsset.set(r.asset, r);
const legacySet = new Map();
for (const e of legacy) if (e && e.asset) legacySet.set(e.asset, e);
/* HASH-BOUND DERIVATIVES (SEO Phase 1b, 16 Oct 2026). A re-encoding of one
   enumerated source file. It is accounted for ONLY through its source, is
   checked by P12, and is never counted in -- or added to -- the backlog. */
if (reg.derivatives !== undefined && !Array.isArray(reg.derivatives)) {
  refuse('the register has a derivatives field that is not an array');
}
const derivatives = Array.isArray(reg.derivatives) ? reg.derivatives : [];
const derivSet = new Map();
for (const d of derivatives) if (d && d.asset) derivSet.set(d.asset, d);

/* STAGED COMPOSITES (H2, 20 Oct 2026). A locked composite whose provenance is
   recorded BEFORE it is published. It names no asset path, so it can never
   satisfy P1 for a file on a page: publishing it means moving it to records
   with an asset, where every P-check applies. Checked by P6 and P13. */
if (reg.staged_composites !== undefined && !Array.isArray(reg.staged_composites)) {
  refuse('the register has a staged_composites field that is not an array');
}
const staged = Array.isArray(reg.staged_composites) ? reg.staged_composites : [];

/* BRAND VECTOR DERIVATIVES (22 Oct 2026, founder-approved Atlas symbol C).
   A pure vector redrawn from brand artwork the register already holds, bound
   to each source's exact sha256. Like a derivative it inherits its sources'
   provenance state, declares nothing and is not counted in the backlog.
   Checked by P14. */
if (reg.brand_vector_derivatives !== undefined && !Array.isArray(reg.brand_vector_derivatives)) {
  refuse('the register has a brand_vector_derivatives field that is not an array');
}
const brandVectors = Array.isArray(reg.brand_vector_derivatives) ? reg.brand_vector_derivatives : [];
const brandSet = new Map();
for (const v of brandVectors) if (v && v.asset) brandSet.set(v.asset, v);

/* ── THE LICENSED-PHOTOGRAPHY EXCEPTION TO P6 AND P10 ──────────────────────
   Founder decision, H2, 20 Oct 2026 (approved in principle at the L6 audit):
   "a supplier name may sit beside the illustration ONLY as the required credit
   of a granted, modification-permitting photo record bound to that asset."

   P6 and P10 exist to stop an AI image passing as a real supplier's product.
   A composite that really does contain a supplier's photographed product,
   used with written permission to adapt it, is the one case where naming the
   supplier is the honest thing to do -- as a credit, and as nothing else.

   The exception is DERIVED, never claimed. A record qualifies only if every
   licensed_photographic_elements entry resolves to exactly one licence in
   image-adaptation-licences.json, ALL of them granted by the SAME organisation
   (22 Oct 2026: one composite may carry more than one written grant from one
   supplier -- TimberIN's hot-tub grant of 20 Oct and its sauna grant of 22 Oct --
   and every one of those licences is held to every rule below; a composite
   can never mix organisations) (NOT the rights manifest: a record there is
   a hot-link host grant and a supplier listing record, and this is neither),
   and each such licence:
     a. is a live grant in the gate's own vocabulary, not withdrawn;
     b. says modification_permitted === true and carries a required credit;
     c. points back at Atlas by its outreach ref and a PN-EVID evidence_ref;
     d. enumerates the element's source photograph BY SHA-256, with
        use 'adapted-into-composite' and bound_composite equal to this
        record's composite_id;
   and the composite_id is claimed by exactly one record or staged composite.
   The provenance register holds only the POINTER (organisation_code +
   atlas_permission_ref, as P4 does). It grants nothing: P11 still holds.

   What it relaxes, and only for the bound organisation:
     P6  a reference input that IS one of the bound source photographs (its
         url, or a string carrying its sha256); depicts_named_product may be
         true, because it truthfully is.
     P10 the organisation's name beside the asset, but only inside the exact
         required credit of EVERY bound licence -- and each of those credits
         must then be present.
   What it never relaxes: a prompt naming any supplier; any other
   organisation; any other reference input; depicts_named_organisation. */
const LIVE_GRANTS = ['Granted — Founder Confirmed',
                     'Granted with Conditions — Founder Confirmed',
                     'Granted — Supplier Confirmed (one-click)'];
let licenceRows = [];
if (existsSync(LICENCES)) {
  try {
    const d = JSON.parse(readFileSync(LICENCES, 'utf8'));
    if (!Array.isArray(d.licences)) refuse('image-adaptation-licences.json has no licences array');
    licenceRows = d.licences;
  } catch (e) { refuse('image-adaptation-licences.json is not valid JSON: ' + e.message); }
}
let rightsRows = null;
function readRightsRows() {
  if (rightsRows !== null) return rightsRows;
  rightsRows = [];
  if (existsSync(RIGHTS)) {
    try {
      const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
      rightsRows = Array.isArray(d) ? d
        : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                      && typeof v[0] === 'object') || []);
    } catch { rightsRows = []; }
  }
  return rightsRows;
}
const compositeClaims = new Map();
for (const r of [...records, ...staged]) {
  if (r && r.composite_id) compositeClaims.set(r.composite_id,
    (compositeClaims.get(r.composite_id) || 0) + 1);
}
/* -> { ok:true, row, rows, credits, sources:[{url, sha256}] } or { ok:false, why }
   row = the first bound licence; rows = every bound licence (same organisation). */
function licensedBinding(r) {
  const els = r && r.licensed_photographic_elements;
  if (els === undefined) return { ok: false, none: true, why: 'no licensed elements' };
  if (!Array.isArray(els) || !els.length) return { ok: false, why: 'licensed_photographic_elements is not a non-empty list' };
  if (!r.composite_id) return { ok: false, why: 'no composite_id to bind to' };
  if (compositeClaims.get(r.composite_id) !== 1) return { ok: false, why: `composite_id ${r.composite_id} is claimed ${compositeClaims.get(r.composite_id)} times` };
  const rows = licenceRows;
  let row = null;
  const rowsBound = [];
  const sources = [];
  for (const e of els) {
    const x = (e && e.rights_ref) || {};
    const hits = rows.filter(w => w.organisation_code && w.organisation_code === x.organisation_code
                                  && w.atlas_permission_ref === x.atlas_permission_ref);
    if (hits.length !== 1) return { ok: false, why: `rights_ref ${x.organisation_code}/${x.atlas_permission_ref} resolves to ${hits.length} licences` };
    if (row && hits[0].organisation_code !== row.organisation_code) return { ok: false, why: 'elements bind to licences of more than one organisation' };
    row = row || hits[0];
    const lic = hits[0];
    if (!rowsBound.includes(lic)) rowsBound.push(lic);
    const a = (lic.approved_assets || []).filter(s => s && s.sha256 && s.sha256 === e.source_sha256);
    if (a.length !== 1) return { ok: false, why: `source ${String(e.source_sha256).slice(0, 12)} is not enumerated once in the grant` };
    if (a[0].use !== 'adapted-into-composite') return { ok: false, why: `source ${a[0].id} is not granted for adaptation` };
    if (a[0].bound_composite !== r.composite_id) return { ok: false, why: `source ${a[0].id} is bound to ${a[0].bound_composite}, not ${r.composite_id}` };
    sources.push({ url: a[0].url, sha256: a[0].sha256 });
  }
  for (const lic of rowsBound) {
    const ref = lic.atlas_permission_ref;
    if (!LIVE_GRANTS.includes(lic.permission_outcome) || lic.withdrawal_effective_at) {
      return { ok: false, why: `the grant ${ref} is not live (${lic.permission_outcome}${lic.withdrawal_effective_at ? ', withdrawn' : ''})` };
    }
    if (lic.modification_permitted !== true) return { ok: false, why: `the grant ${ref} does not permit modification` };
    if (!lic.required_credit || !lic.organisation_name) return { ok: false, why: `the grant ${ref} carries no required credit` };
    if (lic.organisation_name !== row.organisation_name) return { ok: false, why: 'the bound licences name different organisations' };
    /* The licence file is PUBLIC (H2 founder review, 20 Oct 2026): it points
       back at Atlas by its outreach ref and a non-sensitive evidence_ref, never
       by correspondence identifiers. Both are still required. */
    if (!lic.atlas_permission_ref || !/^PN-EVID-[A-Z0-9-]+$/.test(String(lic.evidence_ref || ''))) {
      return { ok: false, why: `the grant ${ref} does not point back at Atlas and its evidence reference` };
    }
  }
  return { ok: true, row, rows: rowsBound, credits: rowsBound.map(l => String(l.required_credit)), sources };
}

console.log('\nIMAGE PROVENANCE GUARD · P1–P14');
console.log('='.repeat(74));
console.log(`  pages scanned        ${pages}`);
console.log(`  local images on them ${found.size}`);
console.log(`  declared records     ${records.length}`);
console.log(`  legacy undeclared    ${legacy.length}`);
console.log(`  derivatives          ${derivatives.length}  (not counted in the backlog)`);
console.log(`  staged composites    ${staged.length}  (locked, not published)`);
console.log(`  brand vectors        ${brandVectors.length}  (not counted in the backlog)`);
console.log('-'.repeat(74));

/* ── P1 · every local image on a published page is accounted for ──────── */
{
  /* THE RATCHET, AND THE WHOLE POINT OF THIS FILE. An image in neither the
     records nor the enumerated backlog is a NEW undeclared image, and it is
     refused. */
  const unaccounted = [...found.keys()]
    .filter(a => !byAsset.has(a) && !legacySet.has(a) && !derivSet.has(a) && !brandSet.has(a));
  unaccounted.length
    ? bad('P1 every local image on a published page is declared or enumerated',
          `${unaccounted.length} unaccounted: ${unaccounted.slice(0, 5).join(', ')}`)
    : ok('P1 every local image on a published page is declared or enumerated',
         `${found.size} checked`);
}

/* ── P2 · the hash binds the record to the bytes ──────────────────────── */
{
  /* A content-hash filename does not prevent a swap -- nothing recomputes
     it. Without this, a different image under a declared filename is
     invisible. */
  const wrong = [];
  for (const e of [...records, ...legacy]) {
    const p = join(ROOT, e.asset || '');
    if (!e.asset || !existsSync(p)) {
      if (e.asset && found.has(e.asset)) wrong.push(`${e.asset} (missing on disk)`);
      continue;
    }
    const h = createHash('sha256').update(readFileSync(p)).digest('hex');
    if (h !== e.sha256) wrong.push(`${e.asset} (${String(e.sha256).slice(0, 12)} != ${h.slice(0, 12)})`);
  }
  wrong.length
    ? bad('P2 every record’s sha256 matches the file on disk',
          `${wrong.length}: ${wrong.slice(0, 3).join('; ')}`)
    : ok('P2 every record’s sha256 matches the file on disk',
         `${records.length + legacy.length} hashed`);
}

/* ── P3 · the class vocabulary is closed ──────────────────────────────── */
{
  const badClass = records.filter(r => !ASSET_CLASSES.includes(r.class));
  const noImageAsClass = records.filter(r => r.class === 'NO_IMAGE');
  (!badClass.length && !noImageAsClass.length)
    ? ok('P3 every record carries a recognised asset class, and NO_IMAGE is '
         + 'not one of them')
    : bad('P3 every record carries a recognised asset class',
          `unrecognised=${badClass.length} NO_IMAGE-as-class=${noImageAsClass.length}`);
}

/* ── P4 · a SUPPLIER_IMAGE resolves to a live grant ───────────────────── */
{
  /* Routed through the EXISTING rights manifest's own vocabulary. This guard
     does not invent a second rights rule; it checks that the pointer lands
     on a row the rights gate already recognises. */
  const sup = records.filter(r => r.class === 'SUPPLIER_IMAGE');
  if (!sup.length) {
    ok('P4 a SUPPLIER_IMAGE row resolves to a live grant',
       'no SUPPLIER_IMAGE rows yet; the check is live and has nothing to test');
  } else if (!existsSync(RIGHTS)) {
    bad('P4 a SUPPLIER_IMAGE row resolves to a live grant',
        'the rights manifest is missing, so the pointer cannot be resolved');
  } else {
    let rows = [];
    try {
      const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
      rows = Array.isArray(d) ? d
        : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                      && typeof v[0] === 'object') || []);
    } catch { /* handled below */ }
    const codes = new Set(rows.map(r => r.organisation_code).filter(Boolean));
    const refs = new Set(rows.map(r => r.atlas_permission_ref).filter(Boolean));
    const broken = sup.filter(r => {
      const x = r.rights_ref || {};
      return !(codes.has(x.organisation_code) && refs.has(x.atlas_permission_ref));
    });
    broken.length
      ? bad('P4 a SUPPLIER_IMAGE row resolves to a live grant',
            `${broken.length} unresolved`)
      : ok('P4 a SUPPLIER_IMAGE row resolves to a live grant', `${sup.length} checked`);
  }
}

/* ── P5 · an AI_ILLUSTRATION is fully declared ────────────────────────── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const problems = [];
  for (const r of ai) {
    const g = r.generated || {};
    if (!g.tool) problems.push(`${r.asset}: no tool`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || ''))) problems.push(`${r.asset}: no date`);
    const FA = attestedFor(r.sha256);
    const pinned = !!FA;
    const attestedForm = 'prompt_status' in r || 'reference_disclosure' in r || 'resemblance_review' in r;
    if (pinned || attestedForm) {
      /* The one-image exception: all of it, or none of it. */
      const rd = r.reference_disclosure || {}, rv = r.resemblance_review || {};
      if (!pinned) problems.push(`${r.asset}: founder-attested form on an image outside ${FOUNDER_ATTESTED_ALL.map(x => x.decision).join(' / ')}`);
      if (pinned && !String(r.decision_ref || '').includes(FA.decision)) problems.push(`${r.asset}: no ${FA.decision}`);
      if ('prompt' in r || 'reference_inputs' in r) problems.push(`${r.asset}: attested record also claims a prompt or reference_inputs`);
      if (r.prompt_status !== 'UNAVAILABLE') problems.push(`${r.asset}: prompt_status is not UNAVAILABLE`);
      if (rd.status !== 'UNCERTAIN' || !rd.statement || !rd.evidence) problems.push(`${r.asset}: reference uncertainty not disclosed`);
      if (!rv.date || !rv.compared_against || !rv.verdict || !(rv.findings || []).length) problems.push(`${r.asset}: no resemblance review`);
      if (pinned && JSON.stringify(r.permitted_surfaces) !== JSON.stringify(FA.surfaces)) problems.push(`${r.asset}: attested image outside its decision's surface (${FA.surfaces.join(', ')})`);
    } else {
      if (!r.prompt || !String(r.prompt).trim()) problems.push(`${r.asset}: no prompt`);
      /* An ABSENT reference_inputs is indistinguishable from an unanswered
         question. An empty array is an assertion that nothing was fed in. */
      if (!Array.isArray(r.reference_inputs)) problems.push(`${r.asset}: reference_inputs absent, not []`);
    }
    const hr = r.human_review || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${r.asset}: no named human review`);
  }
  (ai.length && !problems.length) ? ok('P5 every AI_ILLUSTRATION is fully declared', `${ai.length} checked`)
    : problems.length ? bad('P5 every AI_ILLUSTRATION is fully declared',
                            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P5 every AI_ILLUSTRATION is fully declared',
         'no AI_ILLUSTRATION rows yet; the check is live and has nothing to test');
}

/* ── P5b · an ILLUSTRATION_VERIFIED_NOT_AI is fully declared (26 Oct 2026) ── */
{
  const na = records.filter(r => r.class === 'ILLUSTRATION_VERIFIED_NOT_AI');
  const problems = [];
  for (const r of na) {
    const g = r.generated || {};
    if (!g.tool || /chatgpt|dall|midjourney|gemini|imagen|flux|stable diffusion|firefly|sora/i.test(g.tool)) problems.push(`${r.asset}: no tool, or a generative tool`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || ''))) problems.push(`${r.asset}: no date`);
    if (!g.method) problems.push(`${r.asset}: no method record`);
    if ('prompt' in r || 'reference_inputs' in r) problems.push(`${r.asset}: a non-AI record claims a prompt`);
    const hr = r.human_review || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${r.asset}: no named human review`);
  }
  problems.length ? bad('P5b every ILLUSTRATION_VERIFIED_NOT_AI is fully declared', `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P5b every ILLUSTRATION_VERIFIED_NOT_AI is fully declared', na.length ? `${na.length} checked` : 'none recorded; the check is live');
}

/* ── P5c · a FOUNDER_ORIGINAL_ARTWORK is fully declared (29 Oct 2026) ── */
{
  const fo = records.filter(r => r.class === 'FOUNDER_ORIGINAL_ARTWORK');
  const problems = [];
  for (const r of fo) {
    const a = r.artwork || {};
    if (!a.creator || !a.owner || !a.medium_note) problems.push(`${r.asset}: no creator, owner or description of the artwork`);
    const ph = r.photograph || {};
    if (!ph.photographer) problems.push(`${r.asset}: photographer not recorded (use "NOT YET CONFIRMED" until confirmed)`);
    if (!Array.isArray(ph.processing) || !ph.processing.length) problems.push(`${r.asset}: no processing record`);
    if ('prompt' in r || 'reference_inputs' in r || /chatgpt|dall|midjourney|gemini|imagen|flux|stable diffusion|firefly|sora/i.test(JSON.stringify(ph))) problems.push(`${r.asset}: a founder artwork record names a generative tool or prompt`);
    if (!r.credit) problems.push(`${r.asset}: no visible credit`);
    const hr = r.human_review || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${r.asset}: no owner attestation`);
    if (!Array.isArray(r.permitted_surfaces) || !r.permitted_surfaces.length) problems.push(`${r.asset}: no permitted_surfaces`);
  }
  problems.length ? bad('P5c every FOUNDER_ORIGINAL_ARTWORK is fully declared', `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P5c every FOUNDER_ORIGINAL_ARTWORK is fully declared', fo.length ? `${fo.length} checked` : 'none recorded; the check is live');
}

/* ── P5d · an ARTIST_SUPPLIED_ARTWORK is fully declared (29 Oct 2026) ── */
{
  const ar = records.filter(r => r.class === 'ARTIST_SUPPLIED_ARTWORK');
  const problems = [];
  for (const r of ar) {
    const slug = String(r.artist_slug || '');
    if (!/^[a-z0-9]+(?:-[a-z0-9]+){0,6}$/.test(slug)) problems.push(`${r.asset}: no valid artist slug`);
    else if (!String(r.asset).startsWith(`plotart/artists/${slug}/img/`)) problems.push(`${r.asset}: not inside its artist's gallery folder`);
    if (!['artwork', 'portrait'].includes(r.subject)) problems.push(`${r.asset}: subject must be artwork or portrait`);
    if (r.subject === 'artwork' && !r.work_slug) problems.push(`${r.asset}: an artwork image names no artwork`);
    if (!ARTIST_LICENCE_VERSIONS.includes(r.licence_version)) problems.push(`${r.asset}: no accepted Gallery Publication and Image Licence version`);
    if (!r.permission_ref) problems.push(`${r.asset}: no permission reference`);
    if (!['self', 'other_with_permission'].includes(r.photographer)) problems.push(`${r.asset}: who took the photograph is not declared`);
    if (r.photographer === 'other_with_permission' && !r.photo_credit) problems.push(`${r.asset}: a photographer's permission without a credit`);
    if (!['none', 'assisted', 'generated'].includes(r.ai_involvement)) problems.push(`${r.asset}: no AI declaration`);
    if (!/^[0-9a-f]{64}$/.test(String(r.source_sha256 || ''))) problems.push(`${r.asset}: no source fingerprint`);
    if (!Array.isArray(r.processing) || !r.processing.some(x => /metadata removed/.test(x))) problems.push(`${r.asset}: no record that metadata was removed`);
    if ('prompt' in r || 'reference_inputs' in r) problems.push(`${r.asset}: an artist image record carries a prompt`);
    if (/@|\+?\d[\d ]{8,}\d/.test(JSON.stringify({c: r.photo_credit, p: r.permission_ref, s: slug}))) problems.push(`${r.asset}: personal contact details in a public record`);
    if (!Array.isArray(r.permitted_surfaces) || !r.permitted_surfaces.length || r.permitted_surfaces.some(x => !/^plotart-/.test(x))) problems.push(`${r.asset}: artist images are permitted on PlotArt gallery surfaces only`);
  }
  problems.length ? bad('P5d every ARTIST_SUPPLIED_ARTWORK is fully declared', `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P5d every ARTIST_SUPPLIED_ARTWORK is fully declared', ar.length ? `${ar.length} checked` : 'none recorded; the check is live');
}

/* ── P6 · anti-laundering ─────────────────────────────────────────────── */
{
  /* THE ONE ANTI-LAUNDERING CONTROL THAT CAN BE MECHANISED, and it is worth
     being precise about what it buys. It cannot look at two pictures and
     judge resemblance -- no check here can. What it does is make INTENT
     reviewable: a prompt naming a supplier, an organisation or a product is
     refused, and reference_inputs turns "did you feed it their photograph?"
     from an unanswerable question into a recorded assertion a named person
     signed. The resemblance judgement stays human, and P5 requires that the
     human attestation exists. It cannot require that it is true. */
  /* Staged composites are held to the same rule as published records. */
  const ai = [...records, ...staged].filter(r => r.class === 'AI_ILLUSTRATION');
  const orgs = new Set();
  /* An enumerated supplier photograph, by url or sha256, is a supplier
     reference input wherever it is hosted (H2: TimberIN's photographs live on
     woodenhottubsale.co.uk, which is not its permitted_domain). */
  const supplierPhotos = [];
  for (const r of [...readRightsRows(), ...licenceRows]) {
    if (r.organisation_name) orgs.add(String(r.organisation_name).toLowerCase());
    if (r.permitted_domain) orgs.add(String(r.permitted_domain).toLowerCase());
    if (r.organisation_domain) orgs.add(String(r.organisation_domain).toLowerCase());
    for (const a of (Array.isArray(r.approved_assets) ? r.approved_assets : [])) {
      if (a && a.url) supplierPhotos.push(String(a.url).toLowerCase());
      if (a && a.sha256) supplierPhotos.push(String(a.sha256).toLowerCase());
    }
  }
  const problems = [];
  for (const r of ai) {
    const id = r.asset || r.composite_id;
    const b = licensedBinding(r);
    if (!b.ok && !b.none) problems.push(`${id}: licensed-photography binding fails: ${b.why}`);
    const boundOrg = b.ok ? new Set([String(b.row.organisation_name).toLowerCase(),
                                     String(b.row.organisation_domain || '').toLowerCase()]) : new Set();
    const boundSrc = b.ok ? b.sources.flatMap(s => [String(s.url || '').toLowerCase(),
                                                    String(s.sha256).toLowerCase()]).filter(Boolean) : [];
    /* The attested form's free text is held to the same rule as a prompt. */
    const prompt = [r.prompt, r.creative_direction_reconstructed, r.reference_disclosure, r.resemblance_review]
      .filter(Boolean).map(x => typeof x === 'string' ? x : JSON.stringify(x)).join(' ').toLowerCase();
    for (const o of orgs) {
      if (o.length > 3 && prompt.includes(o)) {
        problems.push(`${id}: prompt names ${o}`);          // never excepted
      }
    }
    for (const src of (r.reference_inputs || [])) {
      const s = String(src).toLowerCase();
      /* Excepted ONLY if the input is itself one of the bound photographs. */
      const isBound = boundSrc.some(x => s === x || (x.length === 64 && s.includes(x)));
      for (const o of orgs) {
        if (o.includes('.') && s.includes(o) && !(isBound && boundOrg.has(o))) {
          problems.push(`${id}: reference input from ${o}`);
        }
      }
      if (!isBound && supplierPhotos.some(x => s.includes(x))) {
        problems.push(`${id}: reference input is an enumerated supplier photograph`);
      }
    }
    if (r.depicts_named_product !== false && !(b.ok && r.depicts_named_product === true)) {
      problems.push(`${id}: depicts_named_product not false`);
    }
    if (r.depicts_named_organisation !== false) problems.push(`${id}: depicts_named_organisation not false`);
  }
  const note = orgs.size
    ? `${orgs.size} organisation names and domains checked`
    : 'NO organisation list could be read, so prompts were not checked';
  if (!orgs.size && ai.length) {
    bad('P6 no AI prompt or reference input names a supplier', note);
  } else {
    problems.length
      ? bad('P6 no AI prompt or reference input names a supplier',
            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
      : ok('P6 no AI prompt or reference input names a supplier', note);
  }
}

/* ── P7 · AI illustrations never reach a product card ─────────────────── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const problems = [];
  for (const r of ai) {
    const s = r.permitted_surfaces;
    if (!Array.isArray(s) || !s.length) { problems.push(`${r.asset}: no permitted_surfaces`); continue; }
    for (const surface of s) {
      if (!PERMITTED_SURFACES.includes(surface)) {
        problems.push(`${r.asset}: ${surface} is not a permitted surface`);
      }
    }
  }
  const cardIsAvailable = PERMITTED_SURFACES.includes('product-card');
  (!problems.length && !cardIsAvailable)
    ? ok('P7 product-card is not an available surface, and every AI surface '
         + 'is recognised', `${PERMITTED_SURFACES.length} surfaces`)
    : bad('P7 product-card is not an available surface',
          `cardAvailable=${cardIsAvailable} problems=${problems.length}`);
}

/* H3 (20 Oct 2026): the labels of a LICENSED PHOTOGRAPHIC COMPOSITE. Such an
   image is not only AI-generated, so the generic AI label would understate it.
   Its record carries a visible caption and an accessible disclosure, and they
   qualify only if, against the licence the record is bound to:
     - the caption contains the required credit of EVERY bound licence exactly
       and says it is an illustration;
     - the disclosure says "AI-generated", says photography, names the
       licensed organisation, and is no longer than 200 characters.
   Returns { ok, caption, disclosure } or { ok:false, why }. */
function compositeLabels(r, b) {
  const cap = String(r.visible_caption || ''), dis = String(r.accessible_disclosure || '');
  if (!cap || !dis) return { ok: false, why: 'no visible_caption and accessible_disclosure' };
  for (const c of b.credits) if (!cap.includes(c)) return { ok: false, why: `the caption does not carry the exact credit "${c}"` };
  if (!/illustrat/i.test(cap)) return { ok: false, why: 'the caption does not say it is an illustration' };
  if (!dis.includes('AI-generated') || !/photograph/i.test(dis) || !dis.includes(String(b.row.organisation_name))) {
    return { ok: false, why: 'the disclosure does not say AI-generated, photography and whose' };
  }
  if (dis.length > 200) return { ok: false, why: 'the disclosure is longer than 200 characters' };
  return { ok: true, caption: cap, disclosure: dis };
}
const pageText = html => html.replace(/<!--[\s\S]*?-->/g, ' ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ');

/* ── P8 · a declared AI illustration carries its visible label ────────── */
{
  /* The founder held the page captions back until records exist. So this
     check is LIVE and currently has nothing to assert -- and it says so,
     rather than passing quietly as though it had verified something. */
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  const expected = (reg.labels || {}).AI_ILLUSTRATION;
  if (!expected) {
    bad('P8 a declared AI illustration carries its approved label',
        'the register declares no AI_ILLUSTRATION label');
  } else if (!ai.length) {
    ok('P8 a declared AI illustration carries its approved label',
       'no AI_ILLUSTRATION rows yet, so no caption is due; the check is live');
  } else {
    const missing = [];
    for (const r of ai) {
      const onPages = found.get(r.asset);
      if (!onPages) continue;              // declared but not published: fine
      /* H3: a licensed photographic composite carries its own two labels
         instead; the generic AI label alone is not enough for it. */
      const b = licensedBinding(r);
      if (!b.none) {
        if (!b.ok) { missing.push(`${r.asset}: licensed binding fails (${b.why})`); continue; }
        const lab = compositeLabels(r, b);
        if (!lab.ok) { missing.push(`${r.asset}: ${lab.why}`); continue; }
        for (const page of onPages) {
          const text = pageText(readFileSync(join(ROOT, page), 'utf8'));
          if (!text.includes(lab.caption)) missing.push(`${r.asset} on ${page}: visible caption missing`);
          if (!text.includes(lab.disclosure)) missing.push(`${r.asset} on ${page}: accessible disclosure missing`);
        }
        continue;
      }
      for (const page of onPages) {
        const html = readFileSync(join(ROOT, page), 'utf8');
        if (!html.includes(expected)) missing.push(`${r.asset} on ${page}`);
      }
    }
    missing.length
      ? bad('P8 a declared AI illustration carries its approved label',
            `${missing.length}: ${missing.slice(0, 3).join('; ')}`)
      : ok('P8 a declared AI illustration carries its approved label',
           `${ai.length} checked`);
  }
}

/* ── P9 · no record for an asset no page references ───────────────────── */
{
  /* A withdrawn image's record should go with it, or the register slowly
     fills with claims about files nobody can see. Legacy entries are exempt:
     the backlog is a census of what is ON DISK, and 28 of the 85 are
     referenced by no page -- which is a real finding, reported below, and
     not a reason to drop them from the ratchet. */
  const stale = records.filter(r => !found.has(r.asset));
  stale.length
    ? bad('P9 no declared record describes an unreferenced asset',
          `${stale.length}: ${stale.slice(0, 3).map(r => r.asset).join(', ')}`)
    : ok('P9 no declared record describes an unreferenced asset');
}

/* ── P10 · no AI illustration shares a surface with a supplier name ───── */
{
  const ai = records.filter(r => r.class === 'AI_ILLUSTRATION');
  if (!ai.length) {
    ok('P10 no AI illustration is presented as a named supplier’s product',
       'no AI_ILLUSTRATION rows yet; the check is live');
  } else {
    const problems = [];
    let orgNames = [];
    if (existsSync(RIGHTS)) {
      try {
        const d = JSON.parse(readFileSync(RIGHTS, 'utf8'));
        const rows = Array.isArray(d) ? d
          : (Object.values(d).find(v => Array.isArray(v) && v[0]
                                        && typeof v[0] === 'object') || []);
        orgNames = rows.map(r => r.organisation_name).filter(Boolean);
      } catch { /* empty */ }
    }
    for (const l of licenceRows) if (l.organisation_name) orgNames.push(l.organisation_name);
    for (const r of ai) {
      for (const page of (found.get(r.asset) || [])) {
        const html = readFileSync(join(ROOT, page), 'utf8');
        /* The same <figure>, caption or card as a supplier's name. Scoped to
           a window around the asset reference rather than the whole page, so
           a supplier mentioned elsewhere on a long page is not a violation. */
        const i = html.indexOf(r.asset);
        if (i === -1) continue;
        const win = html.slice(Math.max(0, i - 1200), i + 1200);
        /* The licensed-photography exception: the bound organisation's name
           may appear ONLY inside its exact required credit, and that credit
           must then be there. Every other organisation is refused as before. */
        const b = licensedBinding(r);
        if (!b.ok && !b.none) problems.push(`${r.asset}: licensed-photography binding fails: ${b.why}`);
        const credits = b.ok ? b.credits : [];
        for (const credit of credits) if (!win.includes(credit)) {
          problems.push(`${r.asset} on ${page} lacks its required credit "${credit}"`);
        }
        /* ...and inside its approved accessible disclosure, which P8 holds to
           its own rules (H3). */
        const lab = b.ok ? compositeLabels(r, b) : { ok: false };
        for (const o of orgNames) {
          if (o.length <= 3) continue;
          let seen = win;
          if (credits.length && o === b.row.organisation_name) {
            for (const credit of credits) seen = seen.split(credit).join(' ');
            if (lab.ok) seen = seen.split(lab.disclosure).join(' ');
          }
          if (seen.includes(o)) {
            problems.push(`${r.asset} on ${page} sits beside ${o}`);
          }
        }
      }
    }
    problems.length
      ? bad('P10 no AI illustration is presented as a named supplier’s product',
            `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
      : ok('P10 no AI illustration is presented as a named supplier’s product');
  }
}

/* ── P11 · provenance NEVER grants a permission ───────────────────────── */
{
  /* "AI generation is not proof of rights" is otherwise a sentence in a
     document. Asserted at SOURCE, three ways:
       a. the rights gate does not read this register at all;
       b. this register carries no rights field it could be mistaken for;
       c. no record claims a permission of its own. */
  const gatePath = join(HERE, 'validate-image-rights.js');
  let gateClean = true, gateRead = false;
  if (existsSync(gatePath)) {
    gateRead = true;
    const gate = readFileSync(gatePath, 'utf8');
    gateClean = !/image-provenance/.test(gate);
  }
  const blob = JSON.stringify(reg);
  const leaked = ['permission_outcome', 'permitted_domain', 'required_credit',
                  'permitted_delivery_hosts', 'permission_date']
    .filter(k => blob.includes(k));
  const claiming = records.filter(r =>
    r.permission_outcome || r.permitted_domain || r.required_credit);
  if (!gateRead) {
    bad('P11 (source) a provenance record can never grant a permission',
        'validate-image-rights.js could not be read, so the separation was '
        + 'not established');
  } else {
    (gateClean && !leaked.length && !claiming.length)
      ? ok('P11 (source) a provenance record can never grant a permission',
           'the rights gate does not read this register; it carries no rights '
           + 'field')
      : bad('P11 (source) a provenance record can never grant a permission',
            `gateReadsRegister=${!gateClean} leakedFields=${leaked.join(',')} `
            + `claimingRecords=${claiming.length}`);
  }
}

/* ── P12 · a derivative is bound to its source and never outgrows it ──── */
{
  /* Added 16 Oct 2026 (SEO Phase 1b, founder-approved). The only way a new
     local file may avoid the ratchet is as a verified re-encoding of a file
     the register already holds. Every condition below is what makes that
     exemption narrow:
       a. it is not also a record or a backlog entry, and appears once;
       b. its source is in the register with the SAME sha256 it was made from
          (a changed source makes the derivative stale);
       c. its source is not itself a derivative (no chains);
       d. it is WebP and its method is from a closed vocabulary;
       e. no crop and no upscale: same aspect ratio, never wider than the
          source -- read from the file's own header, not trusted from JSON;
       f. its bytes match its recorded hash;
       g. every page that shows it also carries its source (the fallback),
          so a derivative can never reach a surface its source is not on;
       h. it declares nothing: no class, status, label or permitted surface;
       i. its source is not on provenance hold (derivative_holds), and it never
          claims an embedded signed credential (re-encoding removes C2PA). */
  const METHODS = ['webp-reencode', 'webp-resize'];
  const problems = [];
  /* Provenance holds (17 Oct 2026): a held source may not have a derivative. */
  if (reg.derivative_holds !== undefined && !Array.isArray(reg.derivative_holds)) {
    problems.push('derivative_holds is not an array');
  }
  const held = new Set((Array.isArray(reg.derivative_holds) ? reg.derivative_holds : [])
    .map(h => h && h.source).filter(Boolean));
  for (const d of derivatives) {
    if (d && d.derived_from && held.has(d.derived_from.asset))
      problems.push(`${d.asset}: its source ${d.derived_from.asset} is on provenance hold`);
    if (d && d.content_credentials && d.content_credentials.derivative_embeds_c2pa !== false)
      problems.push(`${d.asset}: claims or carries an embedded credential`);
  }
  const seen = new Set();
  const webpSize = (buf) => {
    if (buf.length < 30 || buf.toString('ascii', 0, 4) !== 'RIFF'
        || buf.toString('ascii', 8, 12) !== 'WEBP') return null;
    const kind = buf.toString('ascii', 12, 16);
    if (kind === 'VP8 ') return [buf.readUInt16LE(26) & 0x3fff, buf.readUInt16LE(28) & 0x3fff];
    if (kind === 'VP8L') {
      const b = buf.readUInt32LE(21);
      return [(b & 0x3fff) + 1, ((b >> 14) & 0x3fff) + 1];
    }
    if (kind === 'VP8X') return [buf.readUIntLE(24, 3) + 1, buf.readUIntLE(27, 3) + 1];
    return null;
  };
  for (const d of derivatives) {
    const a = d && d.asset;
    if (!a) { problems.push('an entry has no asset'); continue; }
    if (seen.has(a)) problems.push(`${a} listed twice`);
    seen.add(a);
    if (byAsset.has(a) || legacySet.has(a)) problems.push(`${a} is also a record/backlog entry`);
    const from = d.derived_from || {};
    const srcEntry = byAsset.get(from.asset) || legacySet.get(from.asset);
    if (!srcEntry) problems.push(`${a}: source ${from.asset} is not in the register`);
    else if (srcEntry.sha256 !== from.sha256) problems.push(`${a}: source ${from.asset} has changed since derivation`);
    if (derivSet.has(from.asset)) problems.push(`${a}: derived from another derivative`);
    if (!/\.webp$/i.test(a) || !METHODS.includes(d.method)) problems.push(`${a}: not a WebP re-encoding (${d.method})`);
    for (const k of ['class', 'status', 'label', 'permitted_surfaces'])
      if (k in d) problems.push(`${a}: declares "${k}"`);
    const full = join(ROOT, a);
    if (!existsSync(full)) {
      if (found.has(a)) problems.push(`${a}: on a page but missing on disk`);
    } else {
      const buf = readFileSync(full);
      if (createHash('sha256').update(buf).digest('hex') !== d.sha256) problems.push(`${a}: bytes do not match its hash`);
      const wh = webpSize(buf);
      const sp = srcEntry && srcEntry.pixels;
      if (!wh) problems.push(`${a}: not a readable WebP file`);
      else if (Array.isArray(sp) && sp[0] && sp[1]) {
        if (wh[0] > sp[0]) problems.push(`${a}: wider than its source (upscaled)`);
        if (Math.abs(wh[0] / wh[1] - sp[0] / sp[1]) > 0.005) problems.push(`${a}: aspect ratio differs from its source (cropped)`);
      } else problems.push(`${a}: source pixels unknown, crop/upscale cannot be ruled out`);
    }
    for (const page of (found.get(a) || [])) {
      if (!(found.get(from.asset) || new Set()).has(page))
        problems.push(`${a} is on ${page} without its source ${from.asset}`);
    }
  }
  problems.length
    ? bad('P12 every derivative is hash-bound to an unchanged source and never outgrows it',
          `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P12 every derivative is hash-bound to an unchanged source and never outgrows it',
         derivatives.length ? `${derivatives.length} checked` : 'no derivatives yet; the check is live');
}

/* The active L3 (H5C4, 22 Oct 2026; was "must be v2.1c"). Every superseded L3
   layer (L3_v2, L3_v2.1c, ...) is refused as the active L3 and as a chain step;
   the active L3 must be named by hash, and the version it replaced must record
   replaced_by === the active version, so a supersession is always explicit.
   L3_v2 must stay recorded (the original pavilion is never forgotten). */
function supersededL3(chain) {
  return Object.entries((chain && chain.superseded) || {})
    .filter(([k, v]) => /^L3_v[0-9.]+[a-z]?$/.test(k) && v && /^[0-9a-f]{64}$/.test(String(v.sha256 || '')))
    .map(([k, v]) => ({ key: k, sha256: v.sha256, replaced_by: v.replaced_by }));
}
function l3ChainProblems(chain) {
  const out = [];
  const L3 = ((chain && chain.active_layers) || {}).L3 || {};
  const sup = supersededL3(chain);
  if (!L3.version || !/^[0-9a-f]{64}$/.test(String(L3.sha256 || ''))) out.push('the lock chain does not name the active L3 by version and hash');
  if (!sup.some(x => x.key === 'L3_v2')) out.push('the superseded L3 v2 is not recorded');
  if (sup.some(x => x.sha256 === L3.sha256)) out.push('a superseded L3 is the active L3');
  if (!sup.some(x => x.replaced_by === L3.version)) out.push(`no superseded L3 records replaced_by ${L3.version}`);
  const steps = Array.isArray(chain && chain.chain) ? chain.chain : [];
  if (!steps.some(c => c.layer_sha256 === L3.sha256)) out.push('the chain does not apply the active L3 layer');
  if (steps.some(c => sup.some(x => x.sha256 === c.layer_sha256))) out.push('the chain applies a superseded L3 layer');
  return out;
}

/* ── P14 · a brand vector is bound to brand sources and is pure vector ── */
{
  /* Added 22 Oct 2026 (founder-approved Atlas symbol C: the approved ribbon
     artwork redrawn as a clean vector with the official P). The risk this
     exemption must not open: a new image escaping the ratchet, or a raster
     or photograph laundered into the brand folder. So:
       a. it is not also a record, backlog entry or derivative, and appears once;
       b. it lives in assets/brand/ and is an SVG;
       c. it names one or more sources, each in the register (record or
          backlog) with the SAME sha256, each in assets/brand/, none a
          derivative or brand vector itself (no chains);
       d. its bytes match its recorded hash;
       e. it is pure vector: no embedded or linked image, no script, no
          foreignObject, no external reference of any kind;
       f. it declares nothing: no class, status, label or permitted surface;
       g. its method is from a closed vocabulary and it records the founder
          approval it was made under;
       h. if it is on disk, a published page shows it (no orphan exemption). */
  const METHODS = ['vector-trace-and-compose'];
  const problems = [];
  const seen = new Set();
  for (const v of brandVectors) {
    const a = v && v.asset;
    if (!a) { problems.push('an entry has no asset'); continue; }
    if (seen.has(a)) problems.push(`${a} listed twice`);
    seen.add(a);
    if (byAsset.has(a) || legacySet.has(a) || derivSet.has(a)) problems.push(`${a} is also a record/backlog/derivative entry`);
    if (!/^assets\/brand\/[^/]+\.svg$/i.test(a)) problems.push(`${a}: not an SVG in assets/brand/`);
    const srcs = Array.isArray(v.derived_from) ? v.derived_from : [];
    if (!srcs.length) problems.push(`${a}: names no source`);
    for (const f of srcs) {
      const e = f && (byAsset.get(f.asset) || legacySet.get(f.asset));
      if (!e) problems.push(`${a}: source ${f && f.asset} is not in the register`);
      else if (e.sha256 !== f.sha256) problems.push(`${a}: source ${f.asset} has changed since derivation`);
      if (f && !/^assets\/brand\//.test(f.asset || '')) problems.push(`${a}: source ${f && f.asset} is not brand artwork`);
      if (f && (derivSet.has(f.asset) || brandSet.has(f.asset))) problems.push(`${a}: derived from another derivative`);
    }
    if (!METHODS.includes(v.method)) problems.push(`${a}: method outside the closed vocabulary (${v.method})`);
    if (!v.founder_approval || !v.founder_approval.date || !v.founder_approval.decision)
      problems.push(`${a}: records no founder approval`);
    for (const k of ['class', 'status', 'label', 'permitted_surfaces'])
      if (k in v) problems.push(`${a}: declares "${k}"`);
    const full = join(ROOT, a);
    if (!existsSync(full)) {
      if (found.has(a)) problems.push(`${a}: on a page but missing on disk`);
    } else {
      const buf = readFileSync(full);
      if (createHash('sha256').update(buf).digest('hex') !== v.sha256) problems.push(`${a}: bytes do not match its hash`);
      const t = buf.toString('utf8');
      if (/<image\b|<script\b|<foreignObject\b|<use\b[^>]*href|url\(|@import|(?:xlink:)?href\s*=/i.test(t))
        problems.push(`${a}: is not pure vector (embeds or links something)`);
      if (!found.has(a)) problems.push(`${a}: no published page shows it`);
    }
  }
  problems.length
    ? bad('P14 every brand vector is bound to unchanged brand sources and is pure vector',
          problems.slice(0, 4).join('; '))
    : ok('P14 every brand vector is bound to unchanged brand sources and is pure vector',
         brandVectors.length ? `${brandVectors.length} checked` : 'none recorded; the check is live');
}

/* ── P13 · a staged composite is declared, bound, unpublished, and on the
         authoritative lock chain ─────────────────────────────────────── */
{
  /* Added H2, 20 Oct 2026. A staged composite is a locked image recorded
     before publication. Conditions:
       a. fully declared as P5 requires of a published AI_ILLUSTRATION;
       b. names no asset path, so nothing on a page can be accounted for by
          it (publishing it means moving it to records, under every check);
       c. its composite_id is unique and not also a published record's;
       d. any licensed photographic elements bind (licensedBinding);
       e. its master is the ACTIVE master of possibility_reveal_lock_chain,
          the chain names the active L3 by hash (H5C4 since 22 Oct 2026), no
          superseded L3 version is the active one or a chain step, and the
          supersession is recorded (l3ChainProblems). The pixels themselves are verified offline by
          atlas-tools/verify-possibility-reveal-locks.py against the lock
          repository, which holds the images this tree must not carry. */
  const problems = [];
  const chain = reg.possibility_reveal_lock_chain;
  const ids = new Set();
  for (const s of staged) {
    const id = (s && s.composite_id) || '(no composite_id)';
    if (!s || !s.composite_id) problems.push('a staged composite has no composite_id');
    if (ids.has(id)) problems.push(`${id} staged twice`);
    ids.add(id);
    if (s && 'asset' in s) problems.push(`${id}: names an asset; a published image belongs in records`);
    if (records.some(r => r.composite_id === id)) problems.push(`${id}: is also a published record`);
    if (!ASSET_CLASSES.includes(s && s.class)) problems.push(`${id}: unrecognised class`);
    const g = (s && s.generated) || {};
    if (!g.tool || !/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || ''))) problems.push(`${id}: generation not declared`);
    if (!s || !String(s.prompt || '').trim()) problems.push(`${id}: no prompt`);
    if (!s || !Array.isArray(s.reference_inputs)) problems.push(`${id}: reference_inputs absent, not []`);
    const hr = (s && s.human_review) || {};
    if (!hr.reviewer || !hr.date || !hr.attests) problems.push(`${id}: no named human review`);
    const b = licensedBinding(s);
    if (!b.ok && !b.none) problems.push(`${id}: ${b.why}`);
    const m = (s && s.master) || {};
    if (!chain || typeof chain !== 'object') { problems.push(`${id}: no possibility_reveal_lock_chain to check against`); continue; }
    const am = chain.active_master || {};
    if (!/^[0-9a-f]{64}$/.test(String(am.pixel_sha256 || ''))) problems.push('the lock chain has no active master pixel hash');
    if (m.pixel_sha256 !== am.pixel_sha256) problems.push(`${id}: master ${String(m.pixel_sha256).slice(0, 12)} is not the active master ${String(am.pixel_sha256).slice(0, 12)}`);
    for (const p of l3ChainProblems(chain)) problems.push(p);
    const steps = Array.isArray(chain.chain) ? chain.chain : [];
    const last = steps[steps.length - 1] || {};
    if (last.output_sha256 !== am.sha256) problems.push('the chain does not end at the active master');
  }
  /* H3 (20 Oct 2026): PUBLISHED Reveal layers stay on the lock chain too.
       f. a record with reveal_layer names the layer's LOCKED file by hash: the
          chain's active layer for L3 / L5 / L6 (L3 must be the active, explicitly superseding L3, never a
          superseded v2), or the locked layer carried in the base for L4;
       g. a published composite (composite_id) names the ACTIVE master. */
  if (chain && typeof chain === 'object') {
    const act = chain.active_layers || {}, inBase = chain.locked_layers_in_base || {};
    const supL3 = supersededL3(chain).map(x => x.sha256);
    for (const r of records) {
      const rl = r.reveal_layer;
      if (rl) {
        const want = (act[rl.id] || {}).sha256 || (inBase[rl.id] || {}).sha256;
        if (!want) problems.push(`${r.asset}: ${rl.id} is not a layer of the lock chain`);
        else if (rl.layer_sha256 !== want) problems.push(`${r.asset}: ${rl.id} is not the locked layer`);
        if (rl.id === 'L3' && (l3ChainProblems(chain).length || supL3.includes(rl.layer_sha256))) problems.push(`${r.asset}: L3 is not the active, explicitly superseding L3`);
      }
      if (r.composite_id) {
        const m = r.master || {};
        if (m.pixel_sha256 !== (chain.active_master || {}).pixel_sha256) problems.push(`${r.asset}: composite master is not the active master`);
      }
    }
  } else if (records.some(r => r.reveal_layer || r.composite_id)) {
    problems.push('published Reveal layers but no possibility_reveal_lock_chain');
  }
  problems.length
    ? bad('P13 every Reveal layer and composite, staged or published, is on the active lock chain',
          `${problems.length}: ${problems.slice(0, 3).join('; ')}`)
    : ok('P13 every Reveal layer and composite, staged or published, is on the active lock chain',
         `${staged.length} staged, ${records.filter(r => r.reveal_layer).length} published Reveal layer(s) on the chain`);
}

/* ── the backlog, visible on every run ────────────────────────────────── */
const unreferenced = legacy.filter(e => !(e.referenced_by || []).length);
console.log('-'.repeat(74));
console.log(`  LEGACY UNDECLARED: ${legacy.length} asset(s) awaiting a `
            + 'provenance declaration.');
console.log('  A legacy entry is NOT a declaration, NOT verified, and NOT '
            + 'authorised');
console.log('  supplier imagery. The count only goes down.');
if (unreferenced.length) {
  console.log(`  Of those, ${unreferenced.length} are referenced by no `
              + 'published page.');
}
if (process.env.GITHUB_STEP_SUMMARY) {
  try {
    const { appendFileSync } = await import('node:fs');
    appendFileSync(process.env.GITHUB_STEP_SUMMARY,
      `\n### Image provenance\n\n`
      + `- declared records: **${records.length}**\n`
      + `- legacy undeclared: **${legacy.length}**\n`
      + `- local images on published pages: **${found.size}**\n`
      + `\nA legacy entry is not a declaration and not an authorisation.\n`);
  } catch { /* the summary is a convenience, never the gate */ }
}

console.log('\n' + '='.repeat(74));
console.log(`${pass + fail} checks, ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
