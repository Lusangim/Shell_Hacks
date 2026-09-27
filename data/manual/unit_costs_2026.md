# Unit-cost file for savings estimates

- `unit_costs_team_2026-09-26.csv` is the team's file (`product_savings.csv`, 2026-09-26), kept byte for
  byte. For six 230 kV job types (new line, rebuild, reconductor per mile; new substation, substation
  upgrade, transformer-and-reactor equipment per project), it lists each cost item and the following:
  - its unit price, year and quantity;
  - whether two nearby projects could share it;
  - from what distance they could share it (any distance, under 40 km, under 8 km, under 1.6 km,
    touching or co-sited);
  - the team's saving rate, and whether that rate rests on public precedent (`Evidence`,
    `Evidence+Inference`) or is the team's reasoning (`Inference`).

  Prices come from the sources named on each row: MISO Transmission Cost Estimation Guide for MTEP24,
  USDA NASS land values, BLS OEWS wages, and equipment, mat and yard rental guides.
- `unit_costs_2026.csv` is what the pipeline reads. `scripts/update_unit_costs.py` rebuilds it from the
  team file with one newer public source. MISO's *Transmission Cost Estimation Guide for MTEP26*
  (Planning Subcommittee, March 11, 2026) escalates most costs 4% a year, and breakers, disconnect
  switches and power transformers by more. The team file escalated its 2024 MISO prices about 2.5% a
  year.
  - MISO-priced rows are re-escalated to 2026 at 4% a year. That rate is a floor for the breaker, switch
    and transformer rows.
  - Every other row keeps the team's cost.
  - The engineering (3%) and project-management (7%) rows are recomputed on direct cost without the
    optional spare transformer, which the file's totals already exclude.
  - Savings rates, distances, evidence labels and sources are unchanged.
- Estimates are direct costs before MISO's 15-30% contingency and financing (AFUDC). They are screening
  estimates, not measured savings. See `docs/METHODOLOGY.md` § How savings are estimated.
