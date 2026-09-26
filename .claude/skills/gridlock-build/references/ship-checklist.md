# Ship checklist — demo, Q&A, Devpost, repo

Built from the challenge text (Notion Hacker Guide, re-fetched 2026-09-26), Ian Too's hackathon skill
phases 6–7 (rewritten here), and Addy Osmani's `shipping-and-launch`.

## Submission facts (re-check the Notion guide on Sunday morning — organisers update it)
- Hacking and Devpost submission close **Sun Sep 27, 11:00 AM EST** as written; Miami is on EDT in
  September, so treat it as 11:00 local (EDT) — the earlier reading. Our target: submitted by **10:30**.
- At the judging location by **1:00 PM** (table/room list on Discord); absence can disqualify.
- **Round 1:** one general judge, 3-minute live demo; each sponsor (Sperry Tech here) evaluates
  separately. **Round 2:** top projects, 3–5 minutes.
- Devpost: one teammate creates the project and invites the others (same email as ShellHacks
  registration; full names); **opt into the Sperry Tech challenge** or it is not judged for it; GitHub
  repo link; at least one Discord tag. Disclose that AI tools (Codex, Claude) were used to build it.
- The app footer and README carry: "Independent student project; not affiliated with Dominion Energy,
  Georgia Power, Southern Company, GTC, MEAG or Sperry Tech. Estimates are for discussion only."

## Devpost draft (H9 early; T5.0 draft text) → final (T5.4)
`docs/DEVPOST.md`: inspiration (cities and utilities already coordinate street work on shared platforms
such as PaverOps; neighbouring transmission utilities have no public equivalent that we found — see SPEC
§ Prior art) · what it does · how we built it (pipeline → API → map; a Codex lead with sub-agents built and
judged it; Claude reviewed last) · challenges (locations, CEII question, data quality) · accomplishments ·
what we learned · what's next · built with. Claims only what the demo shows; savings are estimates.

## Repo (T5.5; every push needs the founder's yes — Q7)
- [ ] Local paths scrubbed: no `C:\Users\…` in tracked files (use `%USERPROFILE%` forms); no private
      vault notes; Q11 honoured (no new third-party documents; route-map PDF removed; SERTP PDF per Q2).
- [ ] Secret scan prints **counts only** — e.g. `git grep -c -I -E "sk-ant-|OPENAI_API_KEY|Bearer "`
      over tracked files and `git log -p` piped to a count — never the matching lines.
- [ ] Public; default branch `main`; the submitted commit is the latest gate commit.
- [ ] README: what it does (2–3 sentences), screenshot, how to run (SETUP → START), how to verify, data
      sources and licences, methodology link (incl. the ranking formula — savings are shown, not scored),
      known limits, team, hackathon context.
- [ ] `LICENSE` (Q5) · `docs/DATA-SOURCES.md` with attribution (OpenStreetMap ODbL, HIFLD, Census, SCRTP
      and SERTP documents with URLs and dates).
- [ ] Fresh clone outside OneDrive → `SETUP.cmd` → `VERIFY.cmd` = 0 → `START.cmd` works.

## Demo (T5.1b, T5.2, H7)
- [ ] `docs/DEMO.md` 3-minute beats: (1) the problem in one sentence with the FERC Order 1920 hook and
      the street-level precedent ("cities already do this for street work, e.g. PaverOps"),
      (2) the map: two utilities, the border, (3) search "Savannah" → the top Savannah pair, (4) why they
      touch — worded exactly as the PDFs support (e.g. "the tie line ends at McIntosh"), years, sources,
      accuracy, (5) savings range and assumptions, (6) the brief, (7) timeline or area explorer, (8) the
      CSV export — each beat: do / say / proves / honest limit.
- [ ] 5-minute version for Round 2 (methodology and the data-quality story).
- [ ] Every beat verified by a scripted walk on a copy (docs-truth), not from memory.
- [ ] Screenshot fallback for every beat (1440 px); optional 60–90 s recording made only after a rehearsal
      script that fails loudly on any missing element.
- [ ] Offline dry run: Wi-Fi off, fully demoable.
- [ ] Three timed rehearsals; speaker map set (Q1).

## Q&A crib (T5.3, `docs/QA-CRIB.md`)
How distance is measured (nearest points, geodesic km) · why "shared endpoint" vs "same substation" ·
what "approximate" means and how locations were found · why Georgia-only pairs are marked · what the
savings assume and where each assumption comes from · why SERTP and not the IRP (and the CEII answer) ·
what is missing (Thomson–Vogtle, Bluffton not in the loaded plans) · how briefs avoid invented facts ·
**who else does this** (PaverOps and the peers in SPEC § Prior art: street-level, members-only data;
GridLock: transmission scale, across state lines, public filings only) · **why it doesn't exist already**
(from `research/prior-art-2026-09-26.md`: SERTP posts documents only; inputs gated by confidentiality,
CEII, forms or paid exports; HIFLD Open retired in 2025; the Order 1920 duty to share across regions is
new) · **why this pair of utilities** (DESC plans in SCRTP, the Georgia utilities in SERTP: the pairs sit
on an interregional boundary) · **which plan edition** (SERTP 2025; the 2026 preliminary report exists
and is not loaded) · what we would do next.

## Presentation (T5.3)
`docs/PRESENTATION.md`: title · problem · proof the need is real (street-level coordination platforms
such as PaverOps; cited) · our solution · live demo · how it works · impact (who saves what, why now) ·
what's next (more utilities, data shared with permission, construction windows) · team.

## Final gate (G5; the T-2h check is at Sun 09:00)
- [ ] Merged verify green on the commit being submitted; passing totals ≥ baseline.
- [ ] Every box above ticked or explicitly waived by the founder.
- [ ] T-2h protocol run and recorded in the tracker.
