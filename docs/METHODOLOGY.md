# Methodology

## How project locations are drawn

The plans name substations, not coordinates. `pipeline/place_projects.py` matches each named end to public
map data: OpenStreetMap substations, the ends of HIFLD transmission lines, and one hand-placed point
(Okatie, inferred and flagged for checking). A Census town centre is used only when nothing else
matches.

| What was matched | How it is drawn | Accuracy | Projects |
| --- | --- | --- | ---: |
| A HIFLD line joins both named substations | that line's route | exact | 5 |
| One clearly matched substation | a dot | exact | 37 |
| Both ends matched, and existing HIFLD lines connect them plausibly | the route along those lines | approximate | 10 |
| Both ends matched, with no plausible route | a straight line between the two substations | approximate | 18 |
| One end matched, or the match is uncertain | a dot at the matched substation | approximate | 68 |
| Only a town matched | at the Census town centre, flagged "town only" | approximate | 43 |
| Nothing matched | not drawn; listed with its reason | unknown | 49 |

**Routes along existing lines** (`pipeline/hifld_routes.py`). The HIFLD lines form a network whose nodes
are line ends within 100 m of each other. A route between two matched substations is used only when all
of these hold:
- both substations are within 1.5 km of the network;
- it runs on lines of the project's voltage class;
- it passes no other named substation (unnamed taps are allowed);
- it is at most 1.5 times the straight distance.

The route is still an inference, so it stays approximate. A line with the hand-placed Okatie end is
never routed.

**Town centres.** A town centre is not where a transmission line ends. It is never used as a line end
when a real substation end is known; the line keeps its real end(s), and the source says which town
match was not used. A project whose only location is a town centre stays on the map, flagged "town
only". On its own it cannot put a pair closer than "under 40 km": such a pair is counted as under 40 km
(15 pairs, each with a note), unless both plans name the same substation.

## Draft named examples and demo pair

This draft covers only the challenge's named examples. A pair means the current offline overlap artifact associates two **different utilities'** loaded projects within 40 km of mapped geometry. It does not establish a common work site or a shareable asset. Names below are the existing artifact's source-name fields; citations point to the local plan PDF page recorded on each project. The ranked list covers the named-area candidates found in the loaded plans, not every project around those cities. PDF page numbers mean PDF pages, not the number printed in the page footer.

### Named-example status

| Example | Status | Pair ID | Evidence |
| --- | --- | --- | --- |
| Jasper | found | desc-p12__sertp-p107-9bc088 | DESC p. 12 Jasper–Okatie line and SERTP p. 107 McIntosh relay project; mapped proximity only. |
| Okatie | found | desc-p41__sertp-p107-9bc088 | DESC p. 41 tie-line series reactor project and SERTP p. 107 relay project; Deerfield work location is not stated. |
| Bluffton | not in loaded plans | — | `bluffton` has no hit on either local PDF page and no kept project name; see source-name search. |
| Urquhart | found | desc-p7__sertp-p150-ef263c | DESC p. 7 Urquhart line and SERTP p. 150 Goshen solution; 4-year gap and mapped proximity only. |
| McIntosh | found | desc-p41__sertp-p107-9bc088 | DESC p. 41 names McIntosh as a tie-line endpoint; SERTP p. 107 names relay work at McIntosh. |
| Thomson–Vogtle | not in loaded plans | — | `thomson` and `vogtle` occur in SERTP PDF material listed below, but neither names a kept transmission project; no Thomson–Vogtle pair is in the loaded plans. |

### Pair evidence

| Area | Rank | Pair ID | Project A | Project B | Distance km | Touch reason | Touch detail | Pair accuracy |
| --- | ---: | --- | --- | --- | ---: | --- | --- | --- |
| Savannah | 1 | desc-p41__sertp-p107-9bc088 | Okatie – McIntosh 115kV Tie: Add Series Reactor (`desc-p41`) — Dominion Energy SC — SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41 (approximate) | MCINTOSH 230 KV, BREAKER CONTROL RELAY UPGRADES (`sertp-p107-9bc088`) — Georgia Power — SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 107 (exact) | 0.000 | shared_endpoint | The Okatie–McIntosh 115 kV tie line names McIntosh as an endpoint. The DESC series reactor work is at new Deerfield Switching Station, location not stated; the SERTP relay work is at the McIntosh 230 kV bus (SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41; SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 107). | approximate |
| Savannah | 3 | desc-p41__sertp-p111-fe1e3b | Okatie – McIntosh 115kV Tie: Add Series Reactor (`desc-p41`) — Dominion Energy SC — SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41 (approximate) | SAV: GOSHEN (SAV) – MCINTOSH 115 KV TRANSMISSION LINE, REBUILD (`sertp-p111-fe1e3b`) — Georgia Power — SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 111 (approximate) | 0.000 | shared_endpoint | Both plans name McIntosh as an endpoint of a 115 kV line. The SERTP rebuild covers the 6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon) section; the mapped full Goshen–McIntosh line endpoint does not establish work at McIntosh. The DESC series reactor work is at new Deerfield Switching Station, location not stated (SCRTP Planned Facilities 2026-2030 $2M & Above, p. 41; SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 111). | approximate |
| Jasper | 45 | desc-p12__sertp-p107-9bc088 | Jasper – Okatie 230 kV #2: Construct (`desc-p12`) — Dominion Energy SC — SCRTP Planned Facilities 2026-2030 $2M & Above, p. 12 (approximate) | MCINTOSH 230 KV, BREAKER CONTROL RELAY UPGRADES (`sertp-p107-9bc088`) — Georgia Power — SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 107 (exact) | 4.890 | proximity | Mapped geometries are nearby; a shared asset is not established. | approximate |
| Augusta | 306 | desc-p7__sertp-p150-ef263c | Urquhart – Toolebeck 115kV line: Rebuild (`desc-p7`) — Dominion Energy SC — SCRTP Planned Facilities 2026-2030 $2M & Above, p. 7 (approximate) | MEAG: GOSHEN AREA STRATEGIC SOLUTION (`sertp-p150-ef263c`) — MEAG Power — SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 150 (approximate) | 14.860 | proximity | Mapped geometries are nearby; a shared asset is not established. | approximate |
| Augusta | 372 | desc-p26__sertp-p150-ef263c | Urquhart – Aiken PSA 46 kV: Rebuild (`desc-p26`) — Dominion Energy SC — SCRTP Planned Facilities 2026-2030 $2M & Above, p. 26 (approximate) | MEAG: GOSHEN AREA STRATEGIC SOLUTION (`sertp-p150-ef263c`) — MEAG Power — SERTP 2025 Regional Transmission Plan (Nov 26 2025), p. 150 (approximate) | 14.860 | proximity | Mapped geometries are nearby; a shared asset is not established. | approximate |

For both Savannah pairs, verify work locations before reviewing possible coordination; shared assets remain unverified. In rank 3, SERTP p. 111 identifies the 6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon) work section, while the map represents the full named Goshen–McIntosh line. Its endpoint coincidence does not establish scheduled work at McIntosh. DESC p. 41 also leaves the Deerfield Switching Station work location unstated. No work-section geometry is inferred.

The Augusta candidates above are weaker than the Savannah candidates: the loaded Urquhart projects are 3–4 years earlier than the Goshen solution, and the nearest mapped geometries are 14.860 km apart. The `desc-p26` geometry uses only the located Urquhart endpoint; its Aiken PSA tap point remains unplaced. Neither row demonstrates coordination at Vogtle.

### Source-name search

| Term | DESC PDF pages | SERTP PDF pages | Kept project names |
| --- | --- | --- | --- |
| Bluffton | none | none | none |
| Thomson | none | 219, 237 | none |
| Vogtle | none | 150, 219, 221, 238 | none |

Search method: case-insensitive literal term search across extracted text on **every page** of `data/raw/desc_scrtp_2026_2030.pdf` (54 pages) and `data/raw/sertp_2025_rtp.pdf` (257 pages), followed by a case-insensitive search of every kept `name` in `data/build/projects.geojson` and a pair-ID check in `data/build/overlaps.json`. The SERTP p. 150 mention of Vogtle is in the Goshen project's need, not a project named Thomson–Vogtle. The later SERTP Thomson and Vogtle hits are in non-transmission-project appendix material. No absent term is silently promoted to a located transmission project.

**Defensible demo pair:** `desc-p41__sertp-p107-9bc088`, rank 1. The mapped Okatie–McIntosh tie line ends at McIntosh, and the other project is relay work at the McIntosh 230 kV bus. DESC says the series reactor and new **Deerfield Switching Station** are the work; that station's location is **location not stated** in the loaded plan. Thus the zero mapped distance indicates a named endpoint, while a shared physical asset is unverified. The pair's location accuracy is approximate, and its same-year timing is a separate signal. The named plan cost supports only a team-assumption savings estimate on known scope, not a realized saving.

**Founder question:** Should the team obtain and verify a specific Georgia Power IRP source for a potential Thomson–Vogtle hand-entry? Until a source, page, project identity and location are checked, the safe default is no hand-entry. The lead will carry this founder question into `DELIVERY.md`. The public SERTP overview's project-page classification header remains a Q2 provenance caveat for the G2 domain review; this draft uses existing validated artifact fields and page citations and adds no newly transcribed source passage.
