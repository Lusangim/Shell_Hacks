# G2 T2.11 domain judgment

2026-09-26. Frozen product HEAD: `d355f75c05e3d3cd563ed955949a70219a4d4159`, confirmed before work. Copy: `gridlock-wt/judge-domain-g2-r1`; port 8781. Independent transmission-planning lens; no product or test changes.

**Verdict: two P2 verified wording defects; no P0/P1 findings.** Domain score: **7/10** (useful screening tool with traceable inputs, but two material distinctions between mapped geometry and physical work need clearer wording). The lead has reserved the first correction for WEB T1.7; that assignment does not close the finding.

## Mode and scope

Achieved live Chromium inspection plus source/artifact/code review. Opened all ten leading pair details at 1440 px and the first pair at 768 and 390 px; inspected rendered text and citation hrefs. All widths loaded 489 ranked rows without horizontal page overflow, and no external request occurred. Both local PDF endpoints returned 200 `application/pdf`. Browser and loopback server were stopped in `finally`/close cleanup. No screenshots were retained because the brief authorizes writing only this report; this was not a full visual/accessibility audit.

Read the cited local PDF pages with pypdf, project/overlap artifacts, geometry provenance, manual location record, pipeline touch/distance/savings callers, detail renderer, existing tests, methodology and required judging references. Independently calculated five distances without importing the product distance helper. The lead supplied VERIFY `20260926-123703-505` (344 passed, zero failed/skipped); I did not rerun that full suite and do not claim its totals as my own. My checks were read-only scripts and a live browser walk, all exit 0.

Source review uses the already loaded material. It does not resolve the SERTP classification issue or authorize redistribution. No new source passages or project records were added.

## What is good

- All 14 unique projects behind the top ten have names and descriptions matching their cited PDF text after whitespace normalization. Their printed dates/years and voltages match. The malformed source phrase in the McIntosh relay description is preserved rather than silently rewritten.
- DESC p. 41's $5,376,418 printed total and 12/31/2028 date match the artifact. SERTP costs remain null. Estimated ranges explicitly identify team assumptions; missing cost and distant timing produce reasons rather than invented costs.
- All five recalculated distances and their bands agree with the artifacts. Geometry provenance can be followed to committed OSM/HIFLD inputs; an exact calculation is not being treated here as proof that an approximate work location is exact.
- The first Savannah pair's explanation explicitly distinguishes Deerfield work from the McIntosh endpoint and 230 kV relay work. The Augusta methodology correctly avoids a Vogtle coordination claim, reports its weaker timing, and notes incomplete placement.
- There are zero real `lines_cross` pairs among 489. Every and only pair whose two stored states are GA has the Georgia ITS planning note (zero note mismatches). Distinct Wansley source entries retain distinct IDs and descriptions.

## Top ten source checks

`D` means the 54-page DESC SCRTP 2026–2030 PDF; `S` means the 257-page SERTP 2025 PDF. Page numbers below are actual PDF pages, not footer numbers. All citation links in the live detail matched these pages. Utility prefix assignments are supported as stated below; unprefixed Georgia Power attribution is explicitly an inference in the artifact, not independently certified by this review. Stored GA/SC labels describe the selected mapped representation and do not prove that an entire line stays within that state.

| Rank / exact pair ID | Source facts checked | Mapped relationship / result |
| --- | --- | --- |
| 1 `desc-p41__sertp-p107-9bc088` | D41 Okatie–McIntosh tie series reactor: DESC, 115 kV, 12/31/2028, $5,376,418; S107 McIntosh breaker control relays: inferred Georgia Power, 230 kV, 2028, cost absent. Names/descriptions match. | SC/GA; 0 km, touching, shared named endpoint, approximate. Deerfield work location caveat is present. $54k–$161k is 1–3% of DESC cost rounded to $1k, not a combined-project saving. JDOMAIN-02 applies to the opportunity sentence. |
| 2 `sertp-p68-a0289a__sertp-p72-81610d` | S68 GTC Dresden bus expansion, 500 kV; S72 MEAG Dresden–LaGrange upgrade/jumpers, 230 kV; both 2026, no printed costs or usable mileage for a proxy. Names/descriptions match. | GA/GA; 0 km, touching, shared endpoint, exact mapped route/site. Different voltage levels are preserved; physical sharing is unverified. Georgia ITS note and no-cost reason present. |
| 3 `desc-p41__sertp-p111-fe1e3b` | D41 as rank 1; S111 SAV Goshen–McIntosh rebuild, Georgia Power, 115 kV, 2028, 6.7-mile Goshen–Georgia Pacific (Rincon) section, no printed cost. Names/descriptions match. | SC/GA; 0 km, touching, shared named endpoint, approximate. $54k–$161k correctly uses DESC plan cost. The source work-section limitation is absent from pair explanation: JDOMAIN-02. |
| 4 `desc-p41__sertp-p113-5484a4` | D41 as rank 1; S113 West McIntosh two low-side breaker replacements, inferred Georgia Power, 230 kV, 2028, no printed cost. Names/descriptions match. | SC/GA; 0.734739854605 km, under 1.6 km, proximity, approximate. $54k–$161k uses DESC cost. Rendered confidence incorrectly says possibly touching: JDOMAIN-01. |
| 5 `sertp-p124-e36f41__sertp-p133-9ca229` | S124 GTC New Tenaska–Wansley new line, 500 kV, five miles, 2029; S133 inferred Georgia Power Wansley six-breaker replacement, 500 kV, 2029. Both costs absent. Names/descriptions match. | GA/GA; 0 km from Wansley points, touching, same-substation classification, approximate. S124 explicitly includes station termination accommodations; shared equipment remains unverified. $50k–$450k proxy uses five miles; ITS note present. |
| 6 `sertp-p124-e36f41__sertp-p133-a3bd5b` | S124 as rank 5; second S133 entry is ten breakers, not six; same name, 500 kV, 2029, no cost. Distinct descriptions match separate source entries. | Same mapped Wansley relationship and $50k–$450k proxy as rank 5. ITS note present. No basis to merge these two distinct source records or sum their savings. |
| 7 `sertp-p68-fbd1c0__sertp-p72-81610d` | S68 GTC LaGrange–North Opelika new line, 230 kV; S72 MEAG Dresden–LaGrange upgrade, 230 kV; both 2026, costs absent, no eligible stated mileage. Names/descriptions match. | GA/GA stored locations; 0 km, touching, same-area approximate. GTC line has only LaGrange placed; physical contact explicitly unverified. ITS note and no-cost reason present. |
| 8 `sertp-p72-81610d__sertp-p72-eda876` | S72 MEAG upgrade as above; S72 unprefixed LaGrange–North Opelika TS new line, inferred Georgia Power, 230 kV, 2026, 16.5 miles; actual description names North Opelika TS–West Point SS section. Names/descriptions match; costs absent. | GA/GA stored locations; 0 km, touching, same-area approximate, based on only LaGrange located. $165k–$1.485m proxy arithmetic matches 16.5 miles. ITS note and unverified physical-contact caveat present. Utility/geography inference limits remain; no new attribution invented. |
| 9 `sertp-p82-5bdb2b__sertp-p92-ade224` | S82 GRID Arkwright–Lloyd Shoals rebuild, Georgia ITS (joint); S92 unprefixed Lloyd Shoals limiting elements, inferred Georgia Power; both 115 kV, 2027, no costs/mileage. Names/descriptions match. | GA/GA; 0 km, touching, shared endpoint, approximate route. No-cost reason and ITS note present; a joint ITS label does not establish independent ownership or unplanned work. |
| 10 `sertp-p114-46d04f__sertp-p124-e36f41` | S114 Ashley Park–Wansley new line, inferred Georgia Power, 500 kV, 35 miles, 2029; S124 GTC New Tenaska–Wansley, 500 kV, five miles, 2029. Names/descriptions match; costs absent. | GA/GA; 0 km using only located Wansley endpoints, touching, approximate. The same-substation label is a named-site screening relationship, not verified shared equipment. $50k–$450k uses the smaller five-mile proxy; ITS note present. |

Proxy arithmetic checked: five miles × $1m × 1% = $50k; five × $3m × 3% = $450k; 16.5 miles gives $165k–$1.485m. These are team assumptions, not sourced industry savings rates or additive portfolio benefits.

## Five independent distances

Method: transform raw artifact coordinates to EPSG:5070 with `always_xy`; for each endpoint P and segment A–B compute `t = clamp(dot(P-A,B-A)/dot(B-A,B-A),0,1)`, then Q=A+t(B-A), and select the minimum candidate. Transform the chosen points back to WGS84 and apply the ellipsoidal inverse. This separate scalar implementation did not call `pipeline.overlap_geometry`, Shapely nearest_points or the product band function. These selected geometries have endpoint/segment minima; no segment intersection algorithm was needed. Coordinates below are longitude, latitude.

| Rank / pair | Nearest points | Independent km | Artifact km / band |
| --- | --- | ---: | --- |
| 1 / D41–S107 | (-81.1751124,32.3521162) both | 0 | 0 / touching |
| 2 / S68 Dresden–S72 MEAG | (-84.9054815571534,33.3515880660089) both | 0 | 0 / touching |
| 4 / D41–S113 | (-81.1751124,32.3521162) to (-81.1824528,32.3543695) | 0.7347398546048635 | identical / under 1.6 km |
| 52 / `desc-p12__sertp-p107-9bc088` | (-81.1241523,32.3606993) to (-81.1751124,32.3521162) | 4.890181960780094 | identical / under 8 km |
| 332 / `desc-p7__sertp-p150-ef263c` | (-81.9102615276333,33.4331611937867) to (-81.9953118,33.3197599) | 14.860309268519108 | identical / under 40 km |

All differences were 0 m at displayed machine precision. Provenance corroborated in raw inputs: OSM McIntosh 121624352, West McIntosh 121624371, Jasper 185380597 and Augusta Goshen 52019569 have those coordinates. Dresden–LaGrange geometry exactly matches one raw HIFLD route with those named endpoints. Urquhart coordinate matches three raw HIFLD endpoints labelled URQUHART. Savannah Goshen is a separate OSM object 1008141064 at (-81.2094724,32.2487012), avoiding the Augusta-name collision. The Okatie endpoint remains the explicit INFERRED manual record; no founder route-map verification is claimed.

Augusta source cross-check: D7 115 kV, 8/12/2026, $15,948,620 and S150 MEAG Goshen 230 kV, 2030 produce a four-year gap and null savings with `timing_too_far`. D26 46 kV, 12/31/2027, $3m produces a three-year gap and the same visible reason; only its Urquhart endpoint is placed. The S150 Vogtle mention is in supporting need, not a Thomson–Vogtle project identity. Independent full-PDF term scan reproduced the methodology: Bluffton nowhere; Thomson S219/S237; Vogtle S150/S219/S221/S238; neither term occurs in DESC. These hits do not justify a new project record.

## Verified defects

### JDOMAIN-01 — P2 — Approximate confidence text contradicts non-touching distance bands

**Owner:** WEB, assigned by lead to T1.7. **Location:** `web/js/overlap-detail.js:72`, called by the successful overlap fetch/render path. The condition checks only `accuracy_pair`, never `band`.

**Reproduction:** Live detail for `desc-p41__sertp-p110-2ad81c` (rank 54) simultaneously showed `27.5 km · Under 40 km` and `Approximate locations: possibly touching`; artifact distance is 27.537598849227063 km, band `lt_40km`, reason `proximity`. Rank 4 shows the same contradiction for `lt_1_6km`. This overstates geographic contact and conflates uncertainty with a distance classification. Existing e2e checks require possibly touching for the zero-distance first pair; they do not cover an approximate non-touching pair.

**Correction / acceptance:** Preserve approximation disclosure for every approximate pair. Use possibly touching only when the mapped band is touching (or an equally cautious explicit mapping claim); show neutral approximate-location wording for all three non-touching bands. Browser checks must cover touching plus `lt_1_6km`, `lt_8km` and `lt_40km`, and compare detail wording with list/print siblings without altering stored distance or band.

### JDOMAIN-02 — P2 — Named line endpoint is promoted into an actionable work location

**Owner:** DATA wording, with regenerated artifacts/methodology. **Locations:** `pipeline/overlap_geometry.py:91-97` rank-3 special case and `:126` generic shared-endpoint opportunity; `docs/METHODOLOGY.md:23` repeats the incomplete explanation. `pipeline/find_overlaps.py` passes that opportunity into the artifact; `web/js/overlap-detail.js:67-68` renders source evidence and opportunity without further scope qualification.

**Trigger/evidence:** Rank 3 `desc-p41__sertp-p111-fe1e3b` uses a straight full named Goshen–McIntosh line. S111's source description limits the rebuild to the Goshen (Savannah)–Georgia Pacific (Rincon) section, 6.7 miles. The current pair explanation names the McIntosh line endpoint and the DESC Deerfield uncertainty but omits the SERTP section limitation. Its opportunity tells the user to coordinate work at the named endpoint. Neither the mapped full-line endpoint nor the limited SERTP description establishes that this project's work reaches McIntosh. Rank 1 also gets that imperative despite its accurate caveat that DESC work is at unlocated Deerfield. Generic shared-assets-unverified wording does not clearly qualify the asserted work location. No new geographic claim about Rincon is required to establish this mismatch.

**Correction / acceptance:** Name the SERTP Goshen (Savannah)–Georgia Pacific (Rincon) work section explicitly in rank-3 evidence, retain its source page and the Deerfield caveat, and distinguish the mapped full-line endpoint from the scheduled work site. Make the opportunity a review/verification action until work locations are confirmed. Preserve the settled mapped shared-endpoint classification, distances, costs and source descriptions; this finding does not authorize inventing a section geometry. Tests must require both section and Deerfield caveats for rank 3 and ensure ranks 1/3 no longer imply established work at McIntosh. Regenerated API/detail/CSV/print and methodology should carry the same cautious claim.

## Founder decisions and limits

- **SERTP classification (Q2):** All sampled SERTP project pages visibly contain the `(CEII)` header in extracted text, including PDF pp. 68, 72, 107, 111, 124 and 133. Public availability does not settle classification or permission. This is the existing founder/Sperry decision, not a new clearance and not a builder-authorized deletion or replacement. Keep it explicit in DELIVERY before public release; do not transcribe additional marked project data on this review's authority.
- **Okatie H1:** Still inferred from HIFLD TAP170160/manual note. No new map/aerial verification was performed. The approximation and source basis must remain visible.
- **Attribution and partial routes:** Unprefixed Southern projects are attributed to Georgia Power by location inference. Several line projects are represented by one endpoint or the named whole line. This review validates fidelity to those declared assumptions, not ownership or surveyed construction limits. The ITS note is cautious and consistently present; it does not prove independent utility scope.
- The top ten are screening candidates. No common outage plan, procurement package, access right or realized saving was verified. The duplicate-named Wansley entries cannot be resolved into one or two future packages from this source alone.
- No network, external map, live AI/Google call, release action, full keyboard/error-state audit or full suite rerun was performed.

2026-09-26 lesson: A correct distance to a named line endpoint still needs a separate statement of the source's actual construction section.

Summary: two P2 verified wording findings (JDOMAIN-01, JDOMAIN-02); zero P0/P1; five distances and top-ten source fields checked. Evidence is recorded in this report in `reviews/2026-09-26-gridlock-build/judge-domain-g2-r1/`.

material improvement still available: yes
