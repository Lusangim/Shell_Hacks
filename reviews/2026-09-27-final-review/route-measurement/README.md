# Route measurement: can straight-line projects follow real HIFLD lines? (read-only, 2026-09-26 ~19:30)

The founder asked, and approved this measurement. The input was a snapshot of main at `1adc178` (G3 data).
The script is `scratchpad\measure_routes.py`, a copy of which is saved next to this file. Nothing in
the repository was changed.

**Method.** The script builds a graph from the 8,782 HIFLD lines: line ends within 100 m become one node,
giving 5,873 nodes and 7,821 edges. For each of the 55 straight-line projects, it snaps both project
ends to the nearest network node (each must be within 1.5 km). It then takes the shortest path along
real lines, preferring the project's voltage class. A route counts as confident only when all of these
hold:
- the path is at most 1.5× the straight distance;
- it passes no other named substation (taps and unnamed nodes are allowed);
- no end is a town centre;
- the voltage class matches.

The results were the same with a 300 m node tolerance.

| Result for the 55 straight-line projects | All | Rebuild or reconductor (40) |
|---|---:|---:|
| Confident real route (2 a single line, 9 via taps) | 11 | 10 |
| Plausible, but passes other substations or another voltage | 7 | 4 |
| Only a long detour (> 1.5×) | 6 | 6 |
| An end is a town centre | 14 | 8 |
| An end is not on the HIFLD network | 17 | 12 |

- **How far off the straight lines were** for the 11 routed projects: up to 12.6 km. Examples are GTC
  Bonaire Primary – Eastman Primary, Gordon – Sandersville #1 (two plan rows) and Kettle Creek –
  Pine Grove. The median detour ratio is 1.18.
- **Effect on pairs if the 11 are routed**, with ends kept at the matched substations and accuracy
  left approximate:
  - 489 → 493 pairs (4 new within 40 km);
  - 2 pairs move from under 8 km to under 1.6 km;
  - 37 keep their band;
  - none drops out;
  - the top 20 are unchanged, and rank 1 is unchanged.

Files: `routes-tol100.csv` and `routes-tol300.csv` (per project), `summary-tol100.json` and
`summary-tol300.json`.

## Why the other 44 fail (`unrouted-why.txt`)
- 29 have a town-centre end: the substation name wasn't found, so the app used the town.
- 13 have a path, but it detours or passes other substations or another voltage.
- 2 have a matched point 7.6 km from any line.
- New lines have no public route yet.

## Keep or remove guessed locations (`scenarios*.py`, `scenarios-*.txt`, ~20:00)
The simulation reproduces today's ranking exactly (S0 = pipeline order). Every option below includes the
11 routes.

| Option | Pairs | Top 20 / Savannah demo | Today's top 50 kept | Notes |
|---|---:|---|---:|---|
| Routes only | ~489 | same | 50 | Watch out: a route's centroid can move a project's state. Take the state from the end substations. |
| B: trim town-centre ends from the 19 lines with a real end | 461 | same | 50 | |
| **C: B + the 43 town-only projects stay, flagged; they can't create touching / under 8 km on their own** (unless both plans name the same substation) | 461 | same | 43 | Caps 15 claims (10 touching, 5 under 8 km). Cross-state stays 43. |
| D (S2): town-only projects lose map location | 252 | same | 39 | 23 rows leave the dataset under the current rule. Loses 9 pairs where both plans name the same substation (Barnesville, Union City, Dawson Crossing–Nelson, Conyers). |
| S3: D + ends only for the remaining straight lines | 251 | same | 39 | The guessed middles barely matter. |
| S2o: D + the Okatie point unknown | 239 | **rank 1 changes** | 39 | Cross-state 42 → 15. Okatie is load-bearing for the demo; don't touch it without the founder's location check. |

Recommendation to the founder: C.
