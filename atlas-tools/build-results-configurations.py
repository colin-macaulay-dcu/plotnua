#!/usr/bin/env python3
"""
BOUNDED BUILDER — NAMED PRICE CONFIGURATIONS IN RESULTS AND COMPARE
===================================================================
Five anchored edits to your-plot.html, all inside the ONE price presentation
contract the page already has: pnPriceView() / pnPriceDisplay() for a
product's own price, pnPriceDelta() for a difference between two.

THE FAILURE THIS EXISTS TO PREVENT.

A supplier can publish two prices for one building. BIOBUILDS publishes
Wanderlust at EUR 105,000 exterior finished and EUR 163,000 turnkey. The
generator now keeps both, ordered cheapest first, and RETAINS the lowest as
the scalar so every existing consumer keeps working.

That scalar is the SHELL. Printed bare -- "Wanderlust, EUR 105,000" -- it
reads as the price of a finished home, and the homeowner is short EUR 58,000
before they have spoken to anyone. The figure would be accurate and the
sentence would be false.

So: a figure that belongs to a named configuration is NEVER printed without
its name. That is one rule, applied at the one place every surface reads.

WHAT ELSE THE PRICE NOW CARRIES.
  * the VAT basis, from the existing governed `Price Includes VAT` field.
    Liora is published EXCLUDING VAT and Wanderlust INCLUDING it; at
    23% that is not a detail. VAT_UNKNOWN says nothing rather than
    assuming inclusive.
  * the commercial terms, as tokens from the generator, each mapped here to
    one approved sentence. A term with no token is NOT rendered as an
    inclusion: absence of evidence is not absence of a cost.

AND THE REFUSAL TO RANK.

pnPriceDelta() subtracts one product's price from another's. Across unlike
configurations that difference is meaningless -- a shell against a finished
home -- and so is a comparison across unlike VAT bases. It now returns null
in both cases, which is the path every caller already has for products
priced in different currencies.

WHAT IS DELIBERATELY NOT TOUCHED. Single-price products. Every assertion
below is written so that a product with one unnamed price renders exactly
the bytes it renders today, and PC3/PC3b in the guard suite prove it.

    python3 atlas-tools/build-results-configurations.py [--stage] [--check]
                                                        [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
SRC = SITE / "your-plot.html"
BAK = SRC.with_suffix(".html.bak")

STAGE = "--stage" in sys.argv
CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/your-plot.html") if STAGE else SRC)

SENTINEL = "PN_PRICE_TERM_COPY"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 1 · THE CONFIGURATION READERS, ahead of pnPriceView().
# ═══════════════════════════════════════════════════════════════════════════
A1_OLD = """  /* THE VIEW. kind is decided from governed evidence only:"""

A1_NEW = """  /* WHAT A PRICE INCLUDES — ONE APPROVED SENTENCE PER GOVERNED TOKEN.

     The generator recognises a closed set of commercial terms in the Pricing
     record's own evidence and emits TOKENS. The prose stays in Atlas, because
     it is a curator's working paragraph — sources, supersession notes, items
     deliberately not claimed — and the Garden Room price contract already
     refuses to let that field reach a homeowner.

     A token with no sentence here renders NOTHING, and a term with no token
     renders nothing either. Neither is ever turned into an inclusion:
     absence of evidence is not absence of a cost, so no surface may say or
     imply that whatever is unlisted is covered. */
  const PN_PRICE_TERM_COPY = {
    TRANSPORT_AND_ASSEMBLY_INCLUDED:
      'Transport and assembly on prepared ground screws are included.',
    FOUNDATIONS_UTILITIES_SITEWORKS_QUOTED_SEPARATELY:
      'Foundations, utility connections and site works are quoted separately.',
    KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED:
      'Kitchen furniture and appliances are not included.',
    DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED:
      'Delivery, installation and foundations are not included and are charged '
      + 'separately.'
  };

  /* THE VAT BASIS, NEVER ASSUMED. Two of the suppliers who publish named
     configurations publish them on opposite bases: BIOBUILDS including 23%
     VAT, Tiny House Heavens excluding it. At that rate the basis is not a
     footnote. VAT_UNKNOWN deliberately maps to nothing — saying "including
     VAT" because it is the common case would be inventing a term. */
  const PN_VAT_BASIS_COPY = {
    INCLUDES_VAT: 'including VAT',
    EXCLUDES_VAT: 'excluding VAT'
  };

  function pnVatBasis(product){
    const e = (product && product.priceEvidence) || null;
    const b = e && e.basis;
    return (b === 'INCLUDES_VAT' || b === 'EXCLUDES_VAT' ||
            b === 'VAT_UNKNOWN') ? b : null;
  }

  /* The governed terms, as approved sentences. Product-level only: the
     generator publishes the INTERSECTION across every priced configuration,
     so a term true of turnkey alone never arrives here. */
  function pnPriceTerms(product){
    const e = (product && product.priceEvidence) || null;
    const t = e && e.commercialTerms;
    if (Object.prototype.toString.call(t) !== '[object Array]') return [];
    const out = [];
    for (let i = 0; i < t.length; i++) {
      const s = PN_PRICE_TERM_COPY[t[i]];
      if (s && out.indexOf(s) === -1) out.push(s);
    }
    return out;
  }

  /* THE NAMED CONFIGURATIONS, cheapest first — the order is the generator's
     contract, not a ranking, and is not re-derived here.

     An entry survives only if it carries BOTH a usable figure and a governed
     label. A figure with no label is exactly the bare number this whole
     change exists to prevent, so it is dropped rather than printed: the
     product then falls back to the single-price presentation it has today. */
  function pnPriceConfigurations(product){
    const e = (product && product.priceEvidence) || null;
    const raw = e && e.configurations;
    if (Object.prototype.toString.call(raw) !== '[object Array]') return [];
    const cur = pnPriceCurrency(product);
    const out = [];
    for (let i = 0; i < raw.length; i++) {
      const c = raw[i] || {};
      const amount = pnUsablePrice(c.amount);
      const label = (typeof c.label === 'string' && c.label.trim())
        ? c.label.trim() : null;
      if (amount == null || !label) continue;
      out.push({ key: c.key || null, label: label, amount: amount,
                 figure: pnMoney(amount, cur),
                 priceType: c.priceType || null });
    }
    return out;
  }

  /* The governed name beside a figure, in parentheses so the supplier's own
     wording is carried VERBATIM. Lower-casing "Optima" or title-casing
     "Exterior Finished" would both be editing a commercial term. */
  function pnConfigSuffix(label){
    return label ? (' (' + label + ')') : '';
  }

  /* ONE PRICE PRESENTATION, REACHABLE FROM THE OTHER SCRIPT.

     The Additional Home journey lives in a separate <script type="module">
     and cannot see this scope, so it had its own small price reader — which
     printed the governed scalar bare, with no configuration name. That is
     exactly the defect this Piece exists to close, and a second copy of the
     rule would be a second answer to the same question.

     So the contract is published on the window-handle pattern the page
     already uses for __PN_ATLAS_LOADER__ and __PN_GOTO__. pnPriceView is a
     function declaration and therefore hoisted, and nothing calls this
     until a homeowner reaches a result. */
  window.__PN_PRICE_VIEW__ = function (product) { return pnPriceView(product); };

  /* THE VIEW. kind is decided from governed evidence only:"""


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 2 · pnPriceView() carries the configurations and labels the scalar.
# ═══════════════════════════════════════════════════════════════════════════
A2_OLD = """    const display = kind === 'from'      ? ('From ' + figure)
                  : kind === 'estimated' ? ('Estimated ' + figure)
                  : kind === 'quoted'    ? ('Quoted ' + figure)
                  : figure;
    const tail    = kind === 'from'      ? ('from ' + figure)
                  : kind === 'estimated' ? ('at an estimated ' + figure)
                  : kind === 'quoted'    ? ('at a quoted ' + figure)
                  : ('at ' + figure);
    return { known: true, kind: kind, amount: amount, ceiling: to, currency: cur,
             scopeNote: scope, figure: figure, display: display, tail: tail };
  }"""

A2_NEW = """    const display0 = kind === 'from'      ? ('From ' + figure)
                  : kind === 'estimated' ? ('Estimated ' + figure)
                  : kind === 'quoted'    ? ('Quoted ' + figure)
                  : figure;
    const tail0   = kind === 'from'      ? ('from ' + figure)
                  : kind === 'estimated' ? ('at an estimated ' + figure)
                  : kind === 'quoted'    ? ('at a quoted ' + figure)
                  : ('at ' + figure);

    /* NAMED CONFIGURATIONS — THE SCALAR IS NEVER PRINTED BARE.

       The generator retains the LOWEST configuration as amount, so for a
       supplier publishing a shell and a finished home the scalar is the
       SHELL. Bare, it reads as the price of the finished building. Every
       existing surface prints `display`, so the name is attached HERE, once,
       rather than at twenty call sites that could each forget.

       `configurationLine` is the both-prices form, for the surfaces with room
       to show both. Nothing is dropped from either: the figures and the
       labels are the governed ones, in the governed order. */
    const configs = pnPriceConfigurations(P);
    const mine = configs.length
      ? (configs.filter(function(c){ return c.amount === amount; })[0] || configs[0])
      : null;
    const suffix = mine ? pnConfigSuffix(mine.label) : '';
    const display = display0 + suffix;
    const tail = tail0 + suffix;
    const configurationLine = configs.length
      ? configs.map(function(c){ return c.figure + pnConfigSuffix(c.label); })
               .join(' \\u00B7 ')
      : null;
    const basis = pnVatBasis(P);
    return { known: true, kind: kind, amount: amount, ceiling: to, currency: cur,
             scopeNote: scope, figure: figure, display: display, tail: tail,
             configurations: configs, configurationLine: configurationLine,
             configurationLabel: mine ? mine.label : null,
             basis: basis, vatNote: PN_VAT_BASIS_COPY[basis] || null,
             terms: pnPriceTerms(P) };
  }"""


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 3 · pnPriceDelta() refuses to rank unlike things.
# ═══════════════════════════════════════════════════════════════════════════
A3_OLD = """  function pnPriceDelta(a, b){
    const ca = pnPriceCurrency(a), cb = pnPriceCurrency(b);
    if (!ca || !cb || ca !== cb) return null;
    const va = pnUsablePrice(a && a.price), vb = pnUsablePrice(b && b.price);
    if (va == null || vb == null) return null;
    return { currency: ca, diff: va - vb };
  }"""

A3_NEW = """  function pnPriceDelta(a, b){
    const ca = pnPriceCurrency(a), cb = pnPriceCurrency(b);
    if (!ca || !cb || ca !== cb) return null;
    const va = pnUsablePrice(a && a.price), vb = pnUsablePrice(b && b.price);
    if (va == null || vb == null) return null;

    /* UNLIKE CONFIGURATIONS ARE NOT RANKED.

       Subtracting a finished home's price from a shell's produces a real
       number that means nothing, and presenting it as "costs EUR 58,000 more"
       would be a comparison PlotNua cannot stand behind. Two products are
       comparable on price only when each publishes ONE configuration and the
       two name the same one — or when neither names any, which is every
       single-price product in the universe and is why their comparison
       experience is untouched.

       The governed VAT basis is the same question in a second dimension: at
       23% a price excluding VAT and a price including it are not the same
       kind of figure. Unknown-against-unknown is left exactly as it was,
       because that is what today's products carry and this is not the Piece
       that resolves them. */
    const ga = pnPriceConfigurations(a), gb = pnPriceConfigurations(b);
    if (ga.length > 1 || gb.length > 1) return null;
    const la = ga.length ? ga[0].label : null;
    const lb = gb.length ? gb[0].label : null;
    if (la !== lb) return null;

    const bA = pnVatBasis(a), bB = pnVatBasis(b);
    if (bA && bB && bA !== 'VAT_UNKNOWN' && bB !== 'VAT_UNKNOWN' && bA !== bB)
      return null;

    return { currency: ca, diff: va - vb };
  }"""


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 4 · the Additional Home bridge carries the governed price whole.
# ═══════════════════════════════════════════════════════════════════════════
A4_OLD = """      priceEvidence: (p.price ? {
        priceType: p.price.priceType || null,
        currency: p.price.currency || null,
        base: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&
               typeof p.price.amount === 'number') ? p.price.amount : null,
        from: null, to: null,
        quoteOnly: p.price.state === 'EVIDENCED_POA_QUOTE'
      } : null),"""

A4_NEW = """      priceEvidence: (p.price ? {
        priceType: p.price.priceType || null,
        currency: p.price.currency || null,
        base: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&
               typeof p.price.amount === 'number') ? p.price.amount : null,
        from: null, to: null,
        quoteOnly: p.price.state === 'EVIDENCED_POA_QUOTE',
        /* THE NAMED CONFIGURATIONS, THE VAT BASIS AND THE COMMERCIAL TERMS.

           Carried only for a VERIFIED numeric price. On a POA or
           not-published product there is no figure for a label to belong to,
           and attaching commercial terms to an absent price would dress a
           blank in detail. The shapes below are the generator's own; nothing
           is re-derived, re-ordered or filled in. */
        configurations: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&
          Object.prototype.toString.call(p.price.configurations) === '[object Array]')
          ? p.price.configurations : null,
        basis: (p.price.state === 'VERIFIED_NUMERIC_PRICE')
          ? (p.price.basis || null) : null,
        vatRatePercent: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&
          typeof p.price.vatRatePercent === 'number')
          ? p.price.vatRatePercent : null,
        commercialTerms: (p.price.state === 'VERIFIED_NUMERIC_PRICE' &&
          Object.prototype.toString.call(p.price.commercialTerms) === '[object Array]')
          ? p.price.commercialTerms : null
      } : null),"""


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 5 · Compare's price row reads the governed contract, not an ad-hoc
#          second field.
#
# `product.turnkeyPrice` appears in no artefact in the repository — measured
# across every generated JSON on 11 October 2026. It was an ad-hoc second
# price invented at this one call site, and it printed "(basic) / (turnkey)"
# as labels nobody governed. The governed configurations replace it with the
# supplier's own names for their own configurations.
# ═══════════════════════════════════════════════════════════════════════════
A5_OLD = """        ['Published price', pnPriceDisplay(product) + (product.turnkeyPrice ? ' (basic) / ' + pnMoney(product.turnkeyPrice, pnPriceCurrency(product)) + ' (turnkey)' : '')],"""

A5_NEW = """        ['Published price', (function(){
          /* Every configuration the supplier publishes, with the supplier's
             own name against each figure. One configuration, or none, falls
             through to the single-price display this row has always shown. */
          const v = pnPriceView(product);
          const line = (v.configurations && v.configurations.length > 1)
            ? v.configurationLine : v.display;
          return line + (v.vatNote ? ' \\u00B7 ' + v.vatNote : '');
        })()],"""


# ═══════════════════════════════════════════════════════════════════════════
# EDIT 6 · the Additional Home journey reads the one contract.
#
# This runs in the other <script type="module">, which cannot see
# pnPriceView(). It had its own reader, and that reader printed the governed
# scalar BARE — the shell price of a two-configuration building, with nothing
# to say so. It now goes through the published handle.
#
# The degradation is deliberate: if the handle is ever absent, a product with
# more than one configuration says NOTHING about price rather than falling
# back to an unlabelled figure. A missing sentence is a gap; an unlabelled
# figure is a false one.
# ═══════════════════════════════════════════════════════════════════════════
A6_OLD = """  function pnCandidateEvidence(p, lead){
    var fa = pnFloorAreaEvidence(p);
    var price = pnMoney(p);
    var priceNote = pnPriceNote(p);"""

A6_NEW = """  /* How many named configurations the GOVERNED record carries. Read from the
     record itself, so the safety decision below never depends on the handle
     it is guarding against. */
  function pnConfigCount(p){
    var c = p && p.price && p.price.configurations;
    return (Object.prototype.toString.call(c) === '[object Array]') ? c.length : 0;
  }

  function pnCandidateEvidence(p, lead){
    var fa = pnFloorAreaEvidence(p);
    /* THE ONE PRICE PRESENTATION, through the published handle. */
    var pv = (typeof window.__PN_PRICE_VIEW__ === 'function')
      ? window.__PN_PRICE_VIEW__(pnAdditionalHomeView(p)) : null;
    var price = pv
      ? (pv.known
          ? ((pv.configurations && pv.configurations.length > 1)
              ? pv.configurationLine : pv.display)
          : null)
      /* No handle. A single-price product reads exactly as it does today; a
         multi-configuration one says nothing rather than show a bare figure
         that would read as the price of the finished building. */
      : (pnConfigCount(p) > 1 ? null : pnMoney(p));
    var priceNote = pnPriceNote(p);"""

# ═══════════════════════════════════════════════════════════════════════════
# EDIT 7 · the VAT basis and the commercial terms, in front of the homeowner.
#
# The founder's requirement: "Make the important information visible to
# homeowners." These sit in the SAME governed list the card already renders,
# immediately after the figures they qualify, so the price and its terms
# cannot be read apart.
# ═══════════════════════════════════════════════════════════════════════════
A7_OLD = """      if (price) known.push('Price recorded by Atlas: ' + price);
      else if (priceNote) known.push(priceNote);"""

A7_NEW = """      if (price) {
        /* The figures, then what they are and are not. The VAT basis rides
           with the figure rather than sitting in a separate line, because a
           price and its basis read apart are how a homeowner ends up
           comparing two unlike numbers. */
        known.push('Price recorded by Atlas: ' + price
                   + ((pv && pv.vatNote) ? ' \\u00B7 ' + pv.vatNote : ''));
        /* The governed commercial terms, each one an approved sentence for a
           token the generator recognised. Nothing is added when there are no
           tokens, and nothing anywhere says the unlisted is included. */
        if (pv && pv.terms) pv.terms.forEach(function(t){ known.push(t); });
      }
      else if (priceNote) known.push(priceNote);"""


REQUIRED_COPY = [
    "Transport and assembly on prepared ground screws are included.",
    "Foundations, utility connections and site works are quoted separately.",
    "Kitchen furniture and appliances are not included.",
]

# Nothing in the page may claim that an unlisted item is covered.
FORBIDDEN = [
    "everything else is included",
    "all other costs are included",
    "nothing else to pay",
    "fully inclusive price",
    "no further costs",
]


def main():
    if not SRC.exists():
        die("your-plot.html is not where this builder expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED your-plot.html from its .bak sidecar.")
        return

    already = SENTINEL in src
    edits = [("the price-view preamble", A1_OLD, A1_NEW),
             ("the price-view return", A2_OLD, A2_NEW),
             ("pnPriceDelta", A3_OLD, A3_NEW),
             ("the Additional Home price bridge", A4_OLD, A4_NEW),
             ("Compare's published-price row", A5_OLD, A5_NEW),
             ("the Additional Home evidence assembler", A6_OLD, A6_NEW),
             ("the Additional Home price sentence", A7_OLD, A7_NEW)]

    if already:
        out = src
    else:
        # G1 · EVERY ANCHOR, EXACTLY ONCE. Seven edits, seven assertions; a
        # builder that silently applied six of seven would leave the contract
        # half-changed, which is worse than not changing it.
        for name, old, _ in edits:
            n = src.count(old)
            if n != 1:
                die("%s was found %d times, not once. your-plot.html has "
                    "moved. Nothing written." % (name, n))
        out = src
        for _, old, new in edits:
            out = out.replace(old, new, 1)

        # G2 · NOTHING OUTSIDE THE FIVE BLOCKS MOVED.
        back = out
        for _, old, new in reversed(edits):
            back = back.replace(new, old, 1)
        if back != src:
            die("reversing the seven replacements did not reproduce the "
                "original file. Nothing written.")

    # G3 · THE SCALAR IS NEVER PRINTED WITHOUT ITS NAME. The suffix must be
    # applied to BOTH display and tail inside pnPriceView, because the
    # sentence form is what Product Detail and the reasoning lines use.
    if ("const display = display0 + suffix;" not in out or
            "const tail = tail0 + suffix;" not in out):
        die("the configuration name is not attached to both the headline and "
            "the sentence form of the price. Nothing written.")

    # G4 · THE REFUSALS ARE REAL. Two returns of null, for two different
    # kinds of unlikeness, inside pnPriceDelta.
    delta = out[out.find("function pnPriceDelta"):]
    delta = delta[:delta.find("\n  }") + 4]
    if ("if (ga.length > 1 || gb.length > 1) return null;" not in delta or
            "if (la !== lb) return null;" not in delta or
            "bA !== bB)" not in delta):
        die("pnPriceDelta does not refuse unlike configurations and unlike "
            "VAT bases. Nothing written.")

    # G5 · THE AD-HOC SECOND PRICE IS GONE. It was never governed and never
    # present in any artefact; leaving it beside the real contract would
    # leave two answers to one question.
    if "turnkeyPrice ? ' (basic) / '" in out:
        die("the ad-hoc (basic)/(turnkey) construction survived. Nothing "
            "written.")

    # G6 · THE APPROVED SENTENCES ARE PRESENT, as approved. Line wrapping is
    # removed before comparison so the assertion is about the sentence a
    # homeowner reads, not where the source breaks.
    flat = out.replace("'\n      + '", "")
    for s in REQUIRED_COPY:
        if s not in flat:
            die("an approved commercial-terms sentence is missing: %r" % s[:48])

    # G7 · NO SURFACE CLAIMS THAT WHAT IS UNLISTED IS COVERED.
    low = out.lower()
    for phrase in FORBIDDEN:
        if phrase in low:
            die("the page would assert %r. A term with no evidence is not an "
                "inclusion. Nothing written." % phrase)

    # G8 · THE VAT BASIS IS NEVER DEFAULTED. VAT_UNKNOWN must have no copy.
    basis_block = out[out.find("const PN_VAT_BASIS_COPY"):]
    basis_block = basis_block[:basis_block.find("};") + 2]
    if "VAT_UNKNOWN" in basis_block:
        die("VAT_UNKNOWN carries a homeowner sentence. An unknown basis must "
            "say nothing rather than assume one. Nothing written.")

    print("\nNAMED PRICE CONFIGURATIONS IN RESULTS AND COMPARE")
    print("=" * 74)
    if already:
        print("  ok    the contract is already in place; nothing to do")
    else:
        print("  ok    G1  all seven anchors matched exactly once")
        print("  ok    G2  every byte outside the seven blocks is unchanged")
    print("  ok    G3  the scalar carries its configuration name, headline "
          "and sentence")
    print("  ok    G4  pnPriceDelta refuses unlike configurations and bases")
    print("  ok    G5  the ad-hoc (basic)/(turnkey) second price is retired")
    print("  ok    G6  the approved commercial-terms sentences are present")
    print("  ok    G7  nothing claims that an unlisted item is covered")
    print("  ok    G8  an unknown VAT basis carries no sentence")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(), "your-plot.html",
                "your-plot.html (proposed)", lineterm="", n=1)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not STAGE and not BAK.exists():
        shutil.copyfile(SRC, BAK)
    OUT.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(out.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched.")


if __name__ == "__main__":
    main()
