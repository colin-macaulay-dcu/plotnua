#!/usr/bin/env python3
"""
G6 · R3 CLOSURE — DEPRECATED PROPERTY CHECK FIELDS REFUSED BY THE WORKER
===============================================================================
Founder instruction of 12 October 2026. Closes R3 of
governance/G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md.

Two layers, both applied here, in worker/garden-register/src/index.js only:
  W1  EXPLICIT REJECTION. A garden submission that CONTAINS any of the four
      deprecated keys — whatever its value, including null or '' — is refused
      400 { state:'refused', field:<key> } before validation, before the write
      switch, and before any Airtable call.
  W2  NO WRITE PATH. The four keys are no longer parsed or written, so even if
      W1 were removed in some later edit they still could not be stored.
  W3  The header's field description updated to match.

Post-gates prove the protections the founder listed are textually intact:
status ceiling, typecast:false, required tenure, the rent branch, consent
hashing, the write switch, the origin check, the consent sentences, and that
the four keys now appear ONLY in the deprecated list.

  python3 atlas-tools/build-g6-worker-deprecated-fields.py --check | --apply
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "worker" / "garden-register" / "src" / "index.js"
MARK = "G6-R3-DEPRECATED-FIELDS"
KEYS = ["inherited_spare_corner", "inherited_way_in",
        "inherited_your_own_use", "inherited_result_key"]


def refuse(msg):
    print("REFUSED: " + msg); sys.exit(2)


def sub(src, old, new, label):
    n = src.count(old)
    if n != 1:
        refuse(f"{label}: anchor expected once, found {n}")
    return src.replace(old, new)


W1_OLD = """/* --------------------------------------------------------- garden handler -- */
async function handleGarden(env, body, now, cors) {"""
W1_NEW = """/* ------------------------------------------------ deprecated garden keys --
   """ + MARK + """ · founder instruction, 12 October 2026 (closes G6 R3).
   Under privacy notice 2026-10-PHASE2-V3 the register keeps ONE Property
   Check answer: tenure. These four keys were accepted as optional fields
   until then. The page stopped sending them (D2), and the Worker now REFUSES
   any garden submission that carries one — by presence, whatever the value —
   rather than silently dropping it, so a caller that is still sending them
   finds out, and nothing about the refused request is stored.
   They are also no longer parsed or written below: two independent layers. */
const DEPRECATED_GARDEN_KEYS = Object.freeze([
  'inherited_spare_corner', 'inherited_way_in',
  'inherited_your_own_use', 'inherited_result_key'
]);

function deprecatedKeyIn(body) {
  for (const k of DEPRECATED_GARDEN_KEYS) {
    if (Object.prototype.hasOwnProperty.call(body, k)) return k;
  }
  return null;
}

/* --------------------------------------------------------- garden handler -- */
async function handleGarden(env, body, now, cors) {"""

W1B_OLD = """  if (!CONSENT_TEXT.garden) return NOT_OPEN(cors);

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);"""
W1B_NEW = """  if (!CONSENT_TEXT.garden) return NOT_OPEN(cors);

  /* G6 R3 · refused FIRST: before validation, before the write switch, before
     any Airtable call. Ordering matters — placed after the switch, a request
     with writes off would get 'not_open' and the refusal would be invisible. */
  const deprecated = deprecatedKeyIn(body);
  if (deprecated) return REFUSED(cors, deprecated);

  const first_name = cleanText(body.first_name, MAX_NAME_CHARS);"""

W2A_OLD = """  const tenure = pickEnum(V.tenure, body.inherited_tenure);
  const spare = pickEnum(V.spare_corner, body.inherited_spare_corner);
  const wayIn = pickEnum(V.way_in, body.inherited_way_in);
  const ownUse = pickEnum(V.your_own_use, body.inherited_your_own_use);
"""
W2A_NEW = """  const tenure = pickEnum(V.tenure, body.inherited_tenure);
"""

W2B_OLD = """  if (note) fields.garden_note = note;
  if (spare) fields.inherited_spare_corner = spare;
  if (wayIn) fields.inherited_way_in = wayIn;
  if (ownUse) fields.inherited_your_own_use = ownUse;
  const resultKey = cleanText(body.inherited_result_key, 60);
  if (resultKey) fields.inherited_result_key = resultKey;
"""
W2B_NEW = """  if (note) fields.garden_note = note;
"""

GATES_PRESENT = [
    ("status ceiling", "const SUBMIT_STATUS = 'interest_submitted';"),
    ("typecast false", "{ records: [{ fields }], typecast: false }"),
    ("tenure required", "  if (!tenure) return REFUSED(cors, 'inherited_tenure');"),
    ("rent permission", "    if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');"),
    ("rent statement", "    if (!note || note.length < 20) return REFUSED(cors, 'garden_note');"),
    ("consent compare", "  if (!sameString(consentHash, sentHash)) return REFUSED(cors, 'consent_text');"),
    ("write switch", "  if (!writesEnabled(env)) return NOT_OPEN(cors);"),
    ("origin", "    if (!cors) return json(403, { ok: false, state: 'refused' }, null);"),
    ("privacy version from env", "    privacy_version: env.PRIVACY_VERSION,"),
    ("garden consent", """  garden: "I'm over 18, and I'd like PlotNua to keep this and tell me if someone nearby is looking for growing space.\""""),
]


def build(src):
    if MARK in src:
        refuse("already applied (marker present)")
    out = src
    for old, new, lab in [(W1_OLD, W1_NEW, "W1 list"), (W1B_OLD, W1B_NEW, "W1 refusal"),
                          (W2A_OLD, W2A_NEW, "W2 parse"), (W2B_OLD, W2B_NEW, "W2 write")]:
        out = sub(out, old, new, lab)
    # Count UNCHANGED and at least one: several protections are shared by the
    # garden and grower routes, so "exactly once" was the wrong invariant.
    for lab, s in GATES_PRESENT:
        if out.count(s) < 1 or out.count(s) != src.count(s):
            refuse(f"GATE: protection '{lab}' changed ({src.count(s)} -> {out.count(s)})")
    # The four keys may appear ONLY inside the deprecated list now.
    list_m = re.search(r"const DEPRECATED_GARDEN_KEYS = Object\.freeze\(\[.*?\]\);", out, re.S)
    if not list_m:
        refuse("GATE: deprecated list not found")
    rest = out[:list_m.start()] + out[list_m.end():]
    for k in KEYS:
        if k not in list_m.group(0):
            refuse(f"GATE: {k} missing from the deprecated list")
        code = re.sub(r"/\*.*?\*/", "", rest, flags=re.S)       # comments may name them
        code = re.sub(r"(?m)//.*$", "", code)
        if k in code:
            refuse(f"GATE: {k} still referenced in executable code outside the list")
    # the refusal must sit before validation and before the write switch
    # STATUS CEILING, beyond the constant. Added after the capability proof
    # (B8) showed a rewrite could set a promotable status directly while the
    # SUBMIT_STATUS line stayed intact. Comments are stripped: the header
    # legitimately names the statuses this Worker cannot write.
    def code_only(t):
        return re.sub(r"(?m)//.*$", "", re.sub(r"/\*.*?\*/", "", t, flags=re.S))
    for st in ("qualified_garden_opportunity", "registered_grower", "needs_a_conversation",
               "contact_confirmed", "paused", "withdrawn"):
        if code_only(out).count(st) != code_only(src).count(st):
            refuse(f"GATE: promotable status '{st}' introduced into executable code")
    if "fields.status" in code_only(out):
        refuse("GATE: a status is assigned directly rather than via SUBMIT_STATUS")

    # find(), not index(): a missing line must REFUSE, never crash.
    h = out.find("async function handleGarden(")
    i_ref = out.find("if (deprecated) return REFUSED(cors, deprecated);", h)
    i_val = out.find("const first_name", h)
    i_sw = out.find("if (!writesEnabled(env))", h)
    if min(h, i_ref, i_val, i_sw) < 0 or not (i_ref < i_val < i_sw):
        refuse("GATE: the refusal is not ahead of validation and the write switch")
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = TARGET.read_text(encoding="utf-8")
    out = build(src)
    print(f"  worker/garden-register/src/index.js  "
          f"{hashlib.sha256(src.encode()).hexdigest()[:16]} -> "
          f"{hashlib.sha256(out.encode()).hexdigest()[:16]}")
    if mode == "--apply":
        TARGET.write_text(out, encoding="utf-8"); print("APPLIED")
    else:
        print("CHECK OK (nothing written)")


if __name__ == "__main__":
    main()
