# GridLock Resilience Lab: finished plan and build estimate

Status: **proposal, not built.** This completes the team's plan (*Plan de producto e implementación: GridLock Resilience
Lab*). The phases, principles and structure stay the same; this version adds the decisions, formulas, contracts, test
list and hours each phase needs. Unknowns stay marked **TO CONFIRM**.

## 1. What the judge sees (MVP)

1. Open **Resilience Lab** from the top bar.
2. The demo scenario is preselected: **"Hypothetical storm GL-1 (synthetic)"**, with a banner: *Hypothetical scenario,
   not a forecast, not observed damage.*
3. Press **Run simulation**. The storm track plays over the GridLock map in 6-hour steps, with play, pause, step, reset
   and a time scrubber. Transmission lines and substations light up by exposure.
4. The cost card shows **P10 / P50 / P90** direct repair cost for the covered assets, plus coverage and the top three
   assumptions that drive the range. The coverage line has the form "N of M line segments located exactly; costs
   available for X%", with numbers the engine computes.
5. The decision card shows the recommended action, its confidence and the evidence behind it. When the gate trips, it
   shows **Requires human review** and why.
6. **View evidence** opens any number back to the asset, the hazard frame, the fragility curve version and the cost row.
7. **Add to tracker** records the action through GridLock's existing coordination tracker.

The existing GridLock flow (pairs, map, detail, brief, export) is untouched and keeps its meaning.

## 2. Decisions for Phase 0 (defaults if the team doesn't change them)

| Question | Decision | Why |
| --- | --- | --- |
| Historical replay or hypothetical? | **Hypothetical, fully synthetic track, clearly labelled.** A historical replay (for example an archived NHC track near Savannah) comes later. | It works offline with no new downloads, and a hypothetical can't be mistaken for a forecast. |
| Area | The Georgia and South Carolina coastal plain within 150 km of Savannah. | Our top pairs (McIntosh) and densest line data are here. |
| Assets | Existing transmission lines (HIFLD, archived layer, already in `data/raw`) cut into 1 km segments, and OpenStreetMap substations (ODbL, already in `data/raw`). GridLock's planned projects appear as an overlay, not as damaged assets. | Public data only; no CEII; nothing new to license. |
| Hazard | Wind only for the MVP; storm surge and flood are listed as not modelled. | Hazus documents limits for utility wind and flood; wind alone is defensible and explainable. |
| Cost basis | Direct repair or replacement from the team's unit-cost file (MISO 2026 prices): per-mile rebuild cost by voltage class; per-substation equipment cost. | Already sourced and escalated. |
| Uncertainty | Monte Carlo, N = 1,000 draws with a fixed seed. Draws vary track offset (±25 km), intensity (±10%), fragility medians (±15%) and unit costs (low/high band). | Reproducible numbers and an honest range. |
| Human-review gate | Confidence < 0.70; any essential cost or location missing; conflicting sources; malformed provider output; provider error or timeout (8 s). | From the team's plan, section 6. |
| Decision provider ("Jev") | **TO CONFIRM:** what Jev is (provider, API, key owner, cost). Until then the lab uses a deterministic **system rule**, labelled as such and never as Jev. | Principle 6: keys stay on the server, and nothing is invented. |

## 3. Method (deterministic engine)

### 3.1 Hazard frames

- **Track:** a fixed list of positions every 6 hours, from 72 hours before landfall to 24 hours after. Each point has
  latitude, longitude, central pressure deficit Δp (hPa), radius of maximum winds Rmax (km) and forward speed.
- **Wind field:** the Holland (1980) gradient-wind profile, V(r) = sqrt(B·Δp/ρ · (Rmax/r)^B · e^(−(Rmax/r)^B) + (r·f/2)²)
  − r·f/2. It uses ρ = 1.15 kg/m³ and B = 1.3, the Coriolis parameter f at each latitude, a 0.8 reduction from gradient
  to 10 m wind, and a forward-speed asymmetry of +half the forward speed on the right side.
- **Output:** for every asset, the maximum sustained wind across all frames, V_max, and the frame where it peaks. The
  animation plays these computed frames; nothing is interpolated as observation.

### 3.2 Damage

- **Damage states:** none, minor, moderate, severe or failed.
- **Fragility:** a lognormal CDF by asset class, P(DS ≥ k | V) = Φ(ln(V / m_k) / β_k).
- **Parameters are illustrative:** medians m_k and dispersions β_k for (a) wood-pole lines under 115 kV, (b) steel-lattice
  lines of 115 kV and up, and (c) substations. **TO CONFIRM** against a published source before any claim beyond "a
  screening illustration". The UI labels them "Illustrative parameters (source to confirm)".
- **Line segments:** use the segment's own peak wind. **Substations:** use peak wind at the substation point.

### 3.3 Cost

- For each asset, expected cost = Σ_k P(DS = k) × repair ratio_k × replacement cost.
- Repair ratios are 0.02, 0.10, 0.40 and 1.00 for minor, moderate, severe and failed. They are **assumptions, labelled**.
- **Replacement cost:** line segment = miles × the rebuild unit cost for its voltage class; substation = the equipment
  reference job. Both come from `data/manual/unit_costs_2026.csv`.
- If an asset has no defensible cost, it adds **nothing** and counts against coverage. It is never set to zero as if known.
- Run the 1,000 draws and report P10, P50 and P90 of the covered total, the expected total, and coverage as a count
  and a share of assets and of replacement value.

### 3.4 Evidence

Every number carries `evidence_ids` pointing to:
- the hazard frame (track point and wind model version);
- the asset (source, location accuracy);
- the fragility curve (version, parameter status);
- the unit-cost row (tier, source).

## 4. Contracts and API

Pydantic models use `extra="forbid"`, with JSON Schemas exported to `contracts/` by the existing exporter:

- **`ScenarioInput`:** id, name, mode (hypothetical | historical_replay), version, window, track points, sources, and
  labelled assumptions.
- **`HazardFrame`:** time, position, intensity, Rmax and model version.
- **`Asset`:** id, class, geometry, location accuracy (reusing GridLock's labels), source, replacement cost or null, and
  cost basis.
- **`AssetExposure`:** asset id, V_max, peak frame, and damage-state probabilities.
- **`DamageEstimate`:** P10, P50 and P90, expected total, coverage, draws, seed, method version and evidence ids.
- **`Decision`:** one action from the enum, candidates, confidence, reasons (each with evidence ids), review flag and
  reason, and provider plus version ("system-rule-v1" until Jev is confirmed).
- **`EvidenceItem`:** claim, datum, source, date, accuracy and link.

Routes live under `server/disaster/routes.py` and are registered next to the existing routes, which stay unchanged:

- `GET /api/scenarios` returns the list of packaged scenarios.
- `GET /api/scenarios/{id}` returns the input and the precomputed reference result.
- `POST /api/scenarios/{id}/simulate` runs the engine on the server. It should take about a second for a few hundred
  assets × 1,000 draws with numpy (an estimate to measure).
- `POST /api/scenarios/{id}/decision` calls the provider through the review gate. It needs a same-origin header, like
  the brief route.
- `GET /api/scenarios/{id}/evidence/{evidence_id}` returns one evidence item.

The scenario package lives in `data/scenarios/gl1_hypothetical.json`. It never touches `data/build/`.

## 5. Decisions (the "Jev" layer)

The action enum is the team's list:
- `inspect_asset`
- `preposition_crews`
- `coordinate_land`
- `coordinate_project_timing`
- `verify_source`
- `human_review`

The provider receives only the summary, the eligible candidates and their evidence ids. It cannot change a number. Its
answer is validated against `Decision`. Anything outside the enum, missing evidence or below the threshold goes to
`human_review`.

`tests/eval/test_scenario_policy.py` holds ten labelled cases:
- three clear `inspect_asset` cases;
- two `preposition_crews` cases;
- two ambiguous cases that should be sent to review;
- one case with an unknown cost;
- one malformed provider answer;
- one timeout.

## 6. UI (fits the new map-first layout)

- A **Resilience Lab** toggle in the top bar switches the left pane from Pairs to Scenario. The map stays central.
- **Layers:** the track line with 6-hour dots; the peak-wind swath (four bands, with text labels in the key); assets by
  damage-probability class (shape and pattern plus colour, never colour alone); planned projects dimmed.
- **Timeline:** its own scrubber, separate from the in-service year slider, with play, pause, step and reset. Under
  `prefers-reduced-motion` it steps rather than animates.
- **Right pane:** the scenario summary, the cost card (P10/P50/P90, coverage, top assumptions), the decision card with
  its human-review banner, and View evidence.
- Offline by default. The provider state is always visible ("Decision: system rule; Jev not configured").

## 7. Build estimate

These hours are based on tonight's measured pace. Codex (gpt-6-sol or gpt-6-astra) built:
- the area tool in about 20 minutes;
- Start here and the impact summary, with data, contract and UI, in about 20 minutes;
- the tracker in about 25 minutes;
- the redesign shell in about 75 minutes.

Claude's review, merge and verification added 20–40 minutes each time.

| Phase | Work | Agent hours | Wall clock (3 parallel lanes) |
| --- | --- | ---: | ---: |
| 0 | Decisions above confirmed, fragility source chosen, Jev confirmed | 1.5 (team + Claude) | 1.5 |
| 1 | Contracts, scenario package, fixture tests | 2.0 | 1.0 |
| 2 | Wind model, exposure, fragility, cost, Monte Carlo, evidence, hand-checked cases | 5.0 | 2.5 |
| 3 | API routes and tests | 1.5 | (parallel with 2) |
| 4 | Decision layer: system rule, Jev adapter, review gate, 10-case eval | 2.5 | 1.5 |
| 5 | UI: lab mode, layers, timeline animation, cost and decision cards, evidence, accessibility | 5.5 | 3.0 |
| 6 | Docs (DISASTER_MODEL, the decision policy, demo, pitch), rehearsal | 1.5 | 1.0 |
| - | Integration: full test run, fixes, screenshots | 2.0 | 1.5 |
| **Total** | | **≈ 21.5** | **≈ 10–12 hours** |

- **MVP-lite:** system rule only, no Jev, wind only, desktop only, minimal docs. About **9 agent hours, 5–6 hours wall
  clock.**
- **Not before today's 10:30 submission.** The redesign is still in progress and would compete with it for the same
  files and test runs. Recommendation: present Resilience Lab as **"What's next"** in the pitch and on Devpost, with this
  plan and a clearly labelled concept animation, and build it after the hackathon.

## 8. Concept animations (Higgsfield, paid)

These are for the pitch and the Devpost video only. They are **AI-generated concept visuals, not simulation output**,
and are captioned "Concept animation, AI-generated" wherever used.

| # | Shot | Model | Length | Cost |
| --- | --- | --- | --- | ---: |
| A | Stylised night map of the GA-SC coast; a hurricane spiral approaches Savannah; lines in its path pulse amber | Seedance 2.5, 1080p, 16:9, no audio | 8 s | 96 credits |
| B | Light map; an orange SC line and a blue GA line draw in and meet near Savannah; a "1" marker pulses | Seedance 2.5, 1080p, 16:9, no audio | 8 s | 96 credits |

The balance on 2026-09-27 was 1,199.75 credits. Generate one at a time, each only after the team says yes.

## 9. Tests (added when built)

- **Pipeline/package:** malformed scenario, bad coordinates, non-monotonic times, reproducible package hash.
- **Engine:**
  - the wind profile peaks at Rmax and decays;
  - damage probabilities stay monotonic in wind;
  - cost equals a hand-computed small case;
  - the same seed gives the same P10/P50/P90;
  - a missing cost counts as uncovered, never as zero.
- **API:** contracts, 4xx on bad input, evidence ids resolve, provider not configured, timeout, malformed answer.
- **Eval:** the ten labelled decision cases above.
- **End-to-end:** open the lab, run it, pause, step and reset, inspect an asset, open evidence, see the review banner,
  add to the tracker, reduced motion. Plus a full regression of the existing GridLock flow.

## 10. Risks (additions to the team's table)

| Risk | Mitigation |
| --- | --- |
| Fragility numbers look authoritative | "Illustrative parameters" label until a published source is attached. The P10-P90 range is shown with the total. |
| HIFLD layer is archived (HIFLD Open retired in 2025) | Say so in the lab, as GridLock already does. |
| Scope creep before the deadline | This plan is roadmap only until after submission. |
