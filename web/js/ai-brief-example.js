// Example of the optional AI-drafted brief for pair #1. Claude (Opus) wrote it outside the app from this
// pair's data under the live feature's rules, and tests/eval/test_grader.py checks it with the same evidence
// grader. The live feature is off in this build; the brief panel labels this as an example.
export const AI_BRIEF_EXAMPLE = {
  "overlap_id": "desc-p41__sertp-p107-9bc088",
  "what": "Dominion Energy SC lists Okatie – McIntosh 115kV Tie: Add Series Reactor, and the plan data attributes MCINTOSH 230 KV, BREAKER CONTROL RELAY UPGRADES to Georgia Power, inferred from location. Both entries name McIntosh. Dominion Energy SC's reactor work is at the new Deerfield switching station, whose location is not stated in the plan documents, while the Georgia Power relay work is at the McIntosh 230 kV bus. They remain separate plan entries.",
  "where": "The screen puts the pair in the touching band at a mapped separation of 0.0 km, but one location is approximate, so the projects are only possibly touching. The link is the named McIntosh end of the tie line, not a surveyed shared site.",
  "when": "Both plans list 2028, so the two schedules can be compared before either outage plan is fixed. Confirm current milestones with each organization first.",
  "what_to_share": [
    "Ask Dominion Energy SC where the Deerfield switching station will sit and whether any tie line work reaches the McIntosh end.",
    "If it does, compare the 2028 outage windows for the tie line and the McIntosh 230 kV bus relay work.",
    "Check whether one engineering review and one laydown area could serve both jobs, the basis of the savings estimate."
  ],
  "savings_range": {
    "status": "range",
    "low_usd": 62000,
    "high_usd": 264000,
    "basis": "Estimated possible saving: $62,000 to $264,000 from team unit costs for these job types at this distance. An estimate, not a measured or agreed saving."
  },
  "who_to_contact": [
    "Dominion Energy SC",
    "Georgia Power"
  ],
  "caveats": [
    "Neither plan confirms a joint project, shared scope or saving.",
    "One mapped location is approximate; check the source pages and site details before discussing a shared location.",
    "The Georgia Power attribution is inferred from location; confirm ownership before outreach."
  ],
  "sources": [
    {
      "doc": "SCRTP Planned Facilities 2026-2030 $2M & Above",
      "page": 41,
      "url": "https://www.scrtp.com/assets/pdfs/home/2026-2030-2million-and-above-project-descriptions.pdf"
    },
    {
      "doc": "SERTP 2025 Regional Transmission Plan (Nov 26 2025)",
      "page": 107,
      "url": "https://www.southeasternrtp.com/docs/general/2025/2025%20Regional%20Transmission%20Plan%20and%20Input%20Assumptions.pdf"
    }
  ],
  "generated_by": "claude-opus-5-5",
  "prompt_version": "claude-brief-v1",
  "generated_at": "2026-09-27T00:30:00Z",
  "input_hash": "eca5087656da04102f35e4aafc09a4f8cd83863849a631682912276c3dd1b905"
};
