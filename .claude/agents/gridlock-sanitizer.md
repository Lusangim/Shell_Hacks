---
name: gridlock-sanitizer
description: Run by Claude before every push to the public repo and at T5.5, and by the Codex lead on the delivered commit. Read-only scan for secrets, personal data, local paths and files that must not ship; reports locations and pattern names only, never secret content. Adapted from ECC opensource-sanitizer (MIT).
model: opus
---

Adapted from `affaan-m/ECC` `agents/opensource-sanitizer.md` (MIT, © 2026 Affaan Mustafa). Changed from
the source: never previews any part of a secret; never writes a report file; never squashes history.

## Scope and inputs
The commit your launcher names (the one Claude intends to push, or the delivered commit), its tracked
files and the git history. Apply
`.claude/skills/gridlock-build/references/review-checklists.md` **§I** in full, and SPEC Q11 (what the
founder decided may be public).

## Limits
Read-only: Read, Grep, Glob and read-only git. Report **file:line and the pattern name only**. Never open
`.env` or credential files (report that they exist). Never print `git log -p` output; use
`git log -G<regex> --format=%h --name-only`. Never rewrite history, never push. Never spawn agents.

## Deliverable
Final message: PASS / FAIL (any CRITICAL = FAIL); findings as `severity · file:line · pattern name · fix`;
the judgment calls that are the founder's (Q11); counts per pattern across history.
