# Final review after delivery (September 26-27, 2026)

The Codex lead delivered the build on Saturday evening (tag `delivered`). This folder records what happened next.
Claude (Opus) reviewed and improved the delivered build, directed by the team, with one Claude UI agent and
three Codex tasks working in parallel.

| File | What it is |
| --- | --- |
| [LOG.md](LOG.md) | Claude's running log from setup to the final push: decisions, test results, commits |
| [route-measurement/](route-measurement/) | How the line-route and town-centre changes were measured before they were adopted (scripts, results, scenarios) |
| [briefs/impeccable-ui-brief.md](briefs/impeccable-ui-brief.md) | The brief for the UI pass (less text, a three-step panel, map styles) |
| [briefs/codex-area-mode-brief.md](briefs/codex-area-mode-brief.md) | Codex task: the "Explore an area" map button |
| [briefs/codex-insights-brief.md](briefs/codex-insights-brief.md) | Codex task: Start here places and the impact summary |
| [briefs/codex-tracker-brief.md](briefs/codex-tracker-brief.md) | Codex task: the coordination tracker |

What changed after delivery, in short:
- **Locations.** Line projects follow existing HIFLD lines when the route is plausible. A town centre is never
  used as a line end when a real substation end is known, and projects placed only at a town centre are
  flagged "town only".
- **Savings.** Savings are estimated by job type and distance from the team's unit-cost file, and are part of
  the ranking. Distance still leads.
- **Score and tour.** Every pair shows its score factor by factor, and the tour is written for judges.
- **Page.** The UI pass cut the text and gave the panel three numbered steps. The brief no longer repeats the
  pair detail, and it shows what the Claude API brief would add.
- **New tools.** Start here places, an impact summary, an area tool behind a button and a coordination
  tracker.
- **Exports.** The CSV and the print report are tailored to planners.
- **For judges.** Screenshots and backend docs were added (`docs/DEMO.md`, `docs/ARCHITECTURE.md`).
