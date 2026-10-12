# DISC-025 V2 · POST-FREEZE AMENDMENT 2 — G6 PREPARATION

**Date:** 12 October 2026
**Status:** APPEND-ONLY AMENDMENT — applied and proven; awaiting founder visual acceptance
**Authority:** founder decisions of 12 October 2026 — Route A; D2 (ii); D3 including "approve the necessary bounded amendment to the frozen V2 experience"; D4
**Amends:** [`DISC-025-V2-EXPERIENCE-FREEZE-RECORD.md`](DISC-025-V2-EXPERIENCE-FREEZE-RECORD.md), after [`DISC-025-V2-POST-FREEZE-AMENDMENT-2026-10-09.md`](DISC-025-V2-POST-FREEZE-AMENDMENT-2026-10-09.md). Neither earlier record is edited.

## 1 · Hashes

| | before | after |
|---|---|---|
| whole page | `12e442393b135ab9598890e4ea1936454cb46312e0a47466790b6afb96d6a3c7` | `1083f0563c0f2094b1b54b91d72b3fae1a00f59bbec97fe3dc054085ffc1c6f7` |
| **frozen `<main>`** | `05bf977f0d4fb05a3310e1e3dc9bfb757b2d92d529f226f2c8bb97c805844a29` | **`338f6f0c3070f86ae008bc82214c666a10394f1ff60a34765ad5be45431bd7ab`** |

The "before" values were measured on disk immediately before the builder ran and match the 9 October amendment exactly, so nothing had drifted in between.

`atlas-tools/prove-landmarks.mjs` L10 is re-stamped to the new `<main>` value, with the previous value kept in a comment, as was done for the Search V1 re-stamps.

## 2 · What changed — inside the three G3 regions only

The builder masks the three G3 marker regions (CSS, HTML, INTEREST JS) in the before and after pages and **refuses unless everything outside them is byte-identical**. Its capability proof (C9) points a replacement at an engine line and confirms the refusal fires.

| | change |
|---|---|
| offer | heading "Could you see yourself sharing part of your garden?"; pilot sentence naming Raheny, Killester, Donnycarney and Artane; four statements (matching isn't live · no obligation · no introduction promised · you stay in control); out-of-area line; CTA "I'm interested in offering garden space"; caveat "This is a register, not a match." |
| notice | "What we keep" paragraph → privacy V3 |
| payload | `intPayload()` sends tenure only (D2) |
| honeypot | off-screen `website` field, `aria-hidden`, `tabindex=-1`; if filled, nothing is sent and the truthful "didn't go through" state is shown (D4) |
| confirmation | out-of-pilot line: "We are starting in Raheny, Killester, Donnycarney and Artane, and we are not looking for anybody to introduce outside those areas. You are on the register either way." |
| CSS | `.bg-int-list` (68ch measure, matching the offer's existing paragraph measure), `.bg-int-hp` |

## 3 · What did NOT change

| | |
|---|---|
| Property Check questions, options, engine, classification, result copy, reasons, context, evidence | **unchanged** — outside every G3 region, proven byte-identical by the builder's mask gate |
| `INTEREST_PUBLIC` | **`false`** (builder gate, and M1 in the mutation suite) |
| consent sentence | byte-identical, SHA-256 `85c43608…` |
| visibility gates, preview route, `no_garden` suppression, Save-to-My-Plot independence | unchanged |
| funnel events | unchanged; a honeypot-tripped submission fires no `garden_interest_submitted` |
| the PS-1 footer | unchanged |
| Worker source | unchanged |
