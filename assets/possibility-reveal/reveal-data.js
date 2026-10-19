/* PlotNua Possibility Reveal · L2B "The House as a Power Station" · prototype data (v1, 18 Oct 2026)
 *
 * Content rule: every claim is quoted or closely paraphrased from the live Discovery
 * (discovery-house-as-power-station.html). Status chips use the Discovery's exact labels.
 * Commerce rule: the offer model is present; every offer is inactive (status "designed",
 * approval null) and COMMERCE is hard-disabled below. The renderer never shows an offer
 * unless commerceEnabled && offer.status === "active" && offer.approval.
 */
window.PN_REVEAL = {
  version: "L2B-prototype-1",
  commerceEnabled: false,
  discoveryUrl: "https://plotnua.ie/discovery-house-as-power-station.html",

  /* Three maturity classes, shown by shape as well as colour. Labels on chips stay the Discovery's own. */
  maturity: {
    established: { name: "Available today", shape: "full" },
    conditional: { name: "Depends on the site or the house", shape: "half" },
    emerging:    { name: "Emerging · not available to Irish homes", shape: "ring" },
    illustration:{ name: "Illustrative possibility · not assessed", shape: "dash" }
  },

  chips: {
    today:     { text: "Here today", tone: "today" },
    site:      { text: "Depends on the site", tone: "cond" },
    legal:     { text: "Today — legally and administratively", tone: "cond" },
    elsewhere: { text: "Operating elsewhere, not in Ireland", tone: "else" },
    large:     { text: "Large sites in Ireland, not homes", tone: "large" }
  },

  paths: [
    { id: "now",    title: "See what’s possible now",  total: 5, discoveries: [], note: "Next build stage" },
    { id: "beyond", title: "Look beyond the obvious",  total: 4, discoveries: ["ground", "wind"] },
    { id: "coming", title: "Discover what’s coming",   total: 3, discoveries: ["compute"] }
  ],

  discoveries: {
    ground: {
      path: "beyond",
      maturity: "conditional",
      tag: "Depends on the site",
      beacon: { x: 1900, y: 1250, q: "What’s under the lawn?" },
      hook: "What’s under the lawn?",
      line: "Steady heat from the ground — instead of the air unit, not as well as it.",
      chips: ["today", "site"],
      alt: "Illustration: the lawn opens into a cutaway. Two ground loops run through the soil, and heat travels up to the house. The air-source unit is marked: one or the other, not both.",
      more: {
        quote: "A few metres down, the ground sits at roughly the same temperature all year.",
        body: "A ground-source system draws that heat through pipework laid in shallow trenches across the garden — or down a borehole where there is no room to dig. This is the one position where the shape of the site, rather than the house, is the constraint.",
        honest: "An alternative to the air-source heat pump, not an addition. Whether a domestic ground loop in Ireland can be used for cooling is something PlotNua has not established."
      },
      nextStep: { kind: "learn", label: "Read what decides it", href: "#look-again" },
      offers: [
        { offerType: "check",   fulfiller: "plotnua",   commercialTerms: "none",     suitabilityGate: "site:garden-area-or-drill-access", evidenceRefs: [], legalGates: [],                               approval: null, status: "designed" },
        { offerType: "explore", fulfiller: "installer", commercialTerms: "referral", suitabilityGate: "site:suitable",                   evidenceRefs: [], legalGates: ["disclosure"],                   approval: null, status: "designed" },
        { offerType: "enquire", fulfiller: "installer", commercialTerms: "referral", suitabilityGate: "site:suitable",                   evidenceRefs: [], legalGates: ["privacy", "consent", "disclosure"], approval: null, status: "designed" }
      ]
    },

    wind: {
      path: "beyond",
      maturity: "illustration",
      tag: "Illustrative possibility — specialist assessment required",
      beacon: { x: 735, y: 190, q: "Could your roof catch the wind?" },
      hook: "Could your roof catch the wind?",
      line: "Small wind turbines can generate electricity, but roof turbulence, structural requirements and planning conditions make suitability highly site-dependent.",
      chips: [],
      alt: "Illustration: a small, translucent wind turbine appears above the left end of the roof ridge, beside the existing solar panels. Its rotor turns, wind lines move towards it and a line of electricity runs down into the house. It is labelled as an illustration, not an assessment of this roof.",
      more: {
        quote: "What is settled is what you may build and connect. What is not settled is whether it would be worth building at your property.",
        body: "PlotNua has not established realistic output, turbulence from surrounding buildings and trees, installation and maintenance costs, or credible Irish suppliers for domestic wind. A roof is a particularly turbulent place for wind, and a roof-mounted turbine also raises questions of structural loading, vibration and noise. Where there is open, exposed ground, a freestanding turbine may perform better than one on a roof — a specialist assessment would decide.",
        honest: "The Discovery’s planning summary describes a turbine that is not attached to the building and stands back from the boundary. PlotNua has not established how a roof-mounted turbine is treated, so this view makes no planning or suitability claim for this roof."
      },
      nextStep: { kind: "learn", label: "Read what PlotNua has and hasn’t established", href: "#look-again" },
      offers: [
        { offerType: "check", fulfiller: "plotnua", commercialTerms: "none", suitabilityGate: "specialist-assessment", evidenceRefs: [], legalGates: ["planning-position-unestablished"], approval: null, status: "designed" }
      ]
    },

    compute: {
      path: "coming",
      maturity: "emerging",
      tag: "Emerging · homes abroad",
      beacon: { x: 1190, y: 690, q: "A computer that heats water?" },
      hook: "A computer that heats your water.",
      line: "In homes abroad. In Ireland, only at town scale — not in houses.",
      chips: ["elsewhere", "large"],
      alt: "Illustration: an x-ray view opens on the house wall. A computer warms, its heat runs to the hot water cylinder, which fills with warmth, and on to a tap. The view pulls back to the horizon: in Ireland, recovered heat exists only at town scale, in Tallaght.",
      more: {
        quote: "In Britain there are occupied homes with a computer bolted to the hot water cylinder. A business pays for the electricity; the work it does becomes the household’s hot water.",
        body: "In Tallaght, waste heat from a data centre has warmed public buildings since 2023 — at district scale, delivered to buildings, not generated by a house.",
        honest: "None of this is available to an Irish homeowner today.",
        split: [
          { title: "Abroad · in homes", chip: "elsewhere", text: "Britain: a computer at the cylinder heats the household’s water." },
          { title: "Ireland · town scale", chip: "large", text: "Tallaght: data-centre heat for public buildings." }
        ]
      },
      nextStep: { kind: "check", label: "Residential Compute Readiness", href: "https://plotnua.ie/disc026-compute-readiness-check.html", note: "Information, not an application." },
      offers: [
        { offerType: "register", fulfiller: "plotnua", commercialTerms: "none", suitabilityGate: "owner:hosting-yes-or-not-sure", evidenceRefs: [], legalGates: ["privacy", "consent"], approval: null, status: "designed" }
      ]
    }
  }
};
