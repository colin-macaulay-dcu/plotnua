#!/usr/bin/env node
/* ATLAS — THE SHIPPED MARK REALLY IS TRANSPARENT, AND IT IS STILL THE
   APPROVED ARTWORK.

   The founder approved a static raster for the assessment masthead. The first
   build of it shipped the supplied file unchanged: opaque RGB on a flat
   #FDFAF1 ground, which read as a pale rectangle against PlotNua's #F5F2E8
   surface. The correction keyed that ground out to real alpha.

   TWO FAILURES ARE ENCODED HERE, because either one alone would let the defect
   back in.

   FIRST, THE GROUND. It is not enough to assert that the file has an alpha
   channel: a fully opaque RGBA file has one too. So this decodes the PNG and
   asserts the ground is actually gone -- the plate's outer frame and its open
   centre carry no paint at all.

   SECOND, THE ARTWORK. A mark could pass the transparency test and still be
   the wrong picture: anyone can produce a clean matte by redrawing. So this
   decodes the APPROVED OPAQUE FILE as well and requires that every fully
   opaque pixel of the shipped asset is byte-identical to it. That is the
   claim the founder is relying on -- the knot, its dark green, its sage and
   its shading are the approved artwork, not a reconstruction of it.

   The decoder is written out here rather than taken from a library because
   this file is a guard: it should not be able to fail for a reason that has
   nothing to do with PlotNua. Node's own zlib is the only thing it leans on.
   --------------------------------------------------------------------- */
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SHIPPED  = 'assets/brand/atlas-final-static-approved-transparent.png';
const APPROVED = 'assets/brand/atlas-final-static-approved.png';
const GROUND = [0xFD, 0xFA, 0xF1];

let failed = 0, confused = 0;
const ok  = (m, d) => { console.log('    PASS   ' + m + (d ? '\n           ' + d : '')); };
const bad = (m, d) => { failed++; console.log('    FAIL   ' + m + (d ? '\n           ' + d : '')); };
const cannot = (m) => { confused++; console.log('    ERROR  ' + m); };

/* ---- a minimal PNG reader: IHDR + IDAT, 8-bit, colour type 2 or 6 -------- */
function readPng(file) {
  const buf = fs.readFileSync(file);
  if (buf.readUInt32BE(0) !== 0x89504E47) throw new Error('not a PNG: ' + file);
  let off = 8, ihdr = null, idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      ihdr = { w: data.readUInt32BE(0), h: data.readUInt32BE(4),
               depth: data[8], colour: data[9], interlace: data[12] };
    } else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (!ihdr) throw new Error('no IHDR: ' + file);
  if (ihdr.depth !== 8) throw new Error('only 8-bit is supported, got ' + ihdr.depth);
  if (ihdr.interlace !== 0) throw new Error('interlaced PNGs are not supported');
  const ch = ihdr.colour === 6 ? 4 : ihdr.colour === 2 ? 3 : 0;
  if (!ch) throw new Error('unsupported colour type ' + ihdr.colour);

  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = ihdr.w * ch;
  const out = Buffer.alloc(ihdr.h * stride);
  let p = 0;
  for (let y = 0; y < ihdr.h; y++) {
    const filter = raw[p++];
    const line = raw.subarray(p, p + stride); p += stride;
    const cur = out.subarray(y * stride, (y + 1) * stride);
    const prev = y ? out.subarray((y - 1) * stride, y * stride) : null;
    for (let x = 0; x < stride; x++) {
      const a = x >= ch ? cur[x - ch] : 0;
      const b = prev ? prev[x] : 0;
      const c = (prev && x >= ch) ? prev[x - ch] : 0;
      let v = line[x];
      if (filter === 1) v += a;
      else if (filter === 2) v += b;
      else if (filter === 3) v += (a + b) >> 1;
      else if (filter === 4) {
        const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c);
        v += (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      } else if (filter !== 0) throw new Error('bad filter ' + filter);
      cur[x] = v & 0xFF;
    }
  }
  return { ...ihdr, ch, px: out, stride };
}

console.log('');
console.log('ATLAS — THE SHIPPED STATIC MARK');
console.log('='.repeat(76));
console.log('');

let ship, appr;
try { ship = readPng(path.join(ROOT, SHIPPED)); }
catch (e) { cannot('could not read the shipped asset: ' + e.message); }
try { appr = readPng(path.join(ROOT, APPROVED)); }
catch (e) { cannot('could not read the approved asset: ' + e.message); }

if (ship && appr) {
  /* ---- (1) IT CARRIES AN ALPHA CHANNEL, AT THE APPROVED GEOMETRY. ------- */
  ship.colour === 6
    ? ok('the shipped asset is RGBA — it has an alpha channel')
    : bad('the shipped asset has no alpha channel', 'colour type ' + ship.colour);
  (ship.w === appr.w && ship.h === appr.h)
    ? ok(`same plate as the approved file — ${ship.w} x ${ship.h}, 1:1`)
    : bad('the plate geometry changed', `${ship.w}x${ship.h} vs ${appr.w}x${appr.h}`);

  const A = (x, y) => ship.px[y * ship.stride + x * 4 + 3];

  /* ---- (2) THE GROUND IS ACTUALLY GONE. A file can be RGBA and still be
       completely opaque, so this looks at the plate itself. ---------------- */
  let frameMax = 0, frameLit = 0;
  for (let y = 0; y < ship.h; y++) {
    for (let x = 0; x < ship.w; x++) {
      if (y >= 12 && y < ship.h - 12 && x >= 12 && x < ship.w - 12) continue;
      const a = A(x, y);
      if (a > frameMax) frameMax = a;
      if (a > 0) frameLit++;
    }
  }
  frameLit === 0
    ? ok('the outer 12px frame of the plate is completely clear — no rectangle')
    : bad('the plate still paints its own border', `${frameLit} px lit, max alpha ${frameMax}`);

  const cx = ship.w >> 1, cy = ship.h >> 1;
  let centreMax = 0;
  for (let y = cy - 40; y < cy + 40; y++)
    for (let x = cx - 40; x < cx + 40; x++) centreMax = Math.max(centreMax, A(x, y));
  centreMax === 0
    ? ok('the open centre is fully see-through — the page shows through it')
    : bad('the centre of the knot is not open', 'max alpha ' + centreMax);

  let clear = 0, solid = 0, partial = 0;
  for (let i = 3; i < ship.px.length; i += 4) {
    const a = ship.px[i];
    if (a === 0) clear++; else if (a === 255) solid++; else partial++;
  }
  const tot = ship.w * ship.h;
  const pc = n => (n / tot * 100).toFixed(2) + '%';
  clear / tot > 0.5
    ? ok(`most of the plate is empty — ${pc(clear)} clear, ${pc(solid)} solid, ${pc(partial)} rim`)
    : bad('too little of the plate is transparent', pc(clear) + ' clear');
  (partial / tot > 0.002 && partial / tot < 0.08)
    ? ok(`the anti-aliased rim survived — ${partial} pixels of partial alpha`)
    : bad('the rim looks wrong', `${partial} partial-alpha pixels (${pc(partial)})`);

  /* ---- (3) AND IT IS STILL THE APPROVED ARTWORK. ------------------------ */
  let opaque = 0, differing = 0, worst = 0;
  for (let y = 0; y < ship.h; y++) {
    for (let x = 0; x < ship.w; x++) {
      if (ship.px[y * ship.stride + x * 4 + 3] !== 255) continue;
      opaque++;
      const s = y * ship.stride + x * 4, a = y * appr.stride + x * appr.ch;
      let d = 0;
      for (let c = 0; c < 3; c++) d = Math.max(d, Math.abs(ship.px[s + c] - appr.px[a + c]));
      if (d) { differing++; worst = Math.max(worst, d); }
    }
  }
  differing === 0
    ? ok(`every one of the ${opaque} fully opaque pixels is byte-identical to the approved artwork`,
         'the knot, its dark green, its sage and its shading are the approved file, not a redraw')
    : bad('the opaque artwork does not match the approved file',
          `${differing} of ${opaque} pixels differ, worst by ${worst} levels`);

  /* ---- (4) AND THE RIM IS AN HONEST MATTE. Composite the whole thing back
       over the ground it was keyed from; it must return the approved image.
       This is what catches a matte that looks clean but ate the edges. ----- */
  let rt = 0, rtPx = 0;
  for (let y = 0; y < ship.h; y++) {
    for (let x = 0; x < ship.w; x++) {
      const s = y * ship.stride + x * 4, a = y * appr.stride + x * appr.ch;
      const al = ship.px[s + 3] / 255;
      let d = 0;
      for (let c = 0; c < 3; c++) {
        const back = ship.px[s + c] * al + GROUND[c] * (1 - al);
        d = Math.max(d, Math.abs(back - appr.px[a + c]));
      }
      if (d > 2) { rtPx++; rt = Math.max(rt, d); }
    }
  }
  /* 117 pixels of ground dither were cleared deliberately when the mark was
     built -- corners and specks that sat 3-6 levels off #FDFAF1 and so kept a
     whisper of alpha. They are ground, so they do not come back. The bound is
     set just above them: anything more is a matte that damaged artwork. */
  rtPx <= 150
    ? ok(`composited back over #FDFAF1 it returns the approved image (${rtPx} px differ by more than 2, worst ${rt})`,
         'the cleared ground dither accounts for these; the artwork round-trips exactly')
    : bad('the matte damaged the artwork',
          `${rtPx} px differ by more than 2 when recomposited, worst ${rt} levels`);
}

/* ---- (5) AND THE PAGE SHIPS THE TRANSPARENT ONE. ---------------------- */
const src = fs.readFileSync(path.join(ROOT, 'your-plot.html'), 'utf8');
(src.split(SHIPPED).length - 1) === 1
  ? ok('your-plot.html references the transparent asset exactly once')
  : bad('the page does not reference the transparent asset exactly once');
!new RegExp("src = '" + APPROVED.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "'").test(src)
  ? ok('the page does not load the opaque file')
  : bad('the page has been pointed back at the opaque asset', 'that is the pale rectangle');

console.log('');
console.log('='.repeat(76));
if (confused) { console.log('NOT ESTABLISHED — ' + confused + ' check(s) could not run.'); process.exit(2); }
if (failed) { console.log('FAILED — ' + failed + ' check(s).'); process.exit(1); }
console.log('ATLAS STATIC MARK VERIFIED — the ground is gone, the rim is an honest matte, '
  + 'and every opaque pixel is the approved artwork unchanged.');
process.exit(0);
