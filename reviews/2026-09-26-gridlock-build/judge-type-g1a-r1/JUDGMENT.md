# G1a type design judgment — round 1

Frozen copy HEAD `0426747b68130b18bde1b1b1a6731cc59b885e0f`, verified before review. Scope: `server/schemas.py`, exported `contracts/*.json`, and API fixtures. I ran read-only Pydantic probes with `GRIDLOCK_AI=off` on port 8781. I did not run the gate. An optional JSON Schema runtime probe stopped because `jsonschema` is absent; schema observations below are line-cited static review.

Scores are 1–5, with 5 meaning strong encapsulation, fewer representable invalid states, useful caller contract, and few escape hatches. The fourth score is higher when escape hatches are fewer.

| Model or type | Encapsulation | Impossible states | Caller use | Escape hatches | Assessment |
|---|---:|---:|---:|---:|---|
| `Contract` | 5 | 4 | 5 | 4 | Forbids extra keys and freezes attributes, but nested containers remain mutable. |
| `Accuracy` | 5 | 5 | 5 | 5 | Clear closed vocabulary. |
| `Band` | 5 | 5 | 5 | 5 | Clear closed vocabulary; `Overlap` checks it against distance. |
| `Source` | 4 | 3 | 5 | 3 | Requires doc, positive page and URL text; URL shape is loose. |
| `PointGeometry` | 5 | 5 | 5 | 5 | Fixed coordinate pair and bounded longitude/latitude. |
| `LineGeometry` | 5 | 5 | 5 | 5 | Requires at least two bounded positions. |
| `MultiLineGeometry` | 4 | 2 | 4 | 3 | Outer array is nonempty, but its lines may be empty or single point. |
| `ProjectProperties` | 4 | 4 | 5 | 3 | Strong IDs, enums and cost consistency; free text and optional location provenance remain. |
| `ProjectFeature` | 5 | 4 | 5 | 4 | Couples null geometry to unknown accuracy. |
| `ProjectCollection` | 3 | 3 | 5 | 3 | Shape is clear; mutable list and duplicate IDs are possible. |
| `Savings` | 5 | 5 | 5 | 4 | Ordered numeric ranges require basis and assumptions. |
| `Overlap` | 4 | 2 | 5 | 2 | Canonical order, bands and year gaps are checked; same-utility and arbitrary project IDs pass. |
| `BriefSavings` | 3 | 1 | 4 | 2 | Its status and numeric bounds can contradict each other. |
| `Brief` | 4 | 3 | 5 | 3 | Useful complete shape; nested savings inherits its gap. |
| `Center` | 5 | 5 | 5 | 5 | Bounded coordinates. |
| `Area` | 3 | 2 | 4 | 2 | Counts are loose maps with no nonnegative or reconciliation rule. |
| `SourceDocument` | 4 | 3 | 4 | 3 | Readable source summary, but text is unconstrained. |
| `Meta` | 3 | 2 | 5 | 2 | Named top-level counts, loose maps and no stage reconciliation. |
| `SearchResult` | 4 | 4 | 5 | 3 | Closed result kind and bounded coordinates; reference meaning is loose. |
| `ErrorDetail` | 4 | 3 | 5 | 3 | Stable error shape; codes are free strings. |
| `ErrorResponse` | 5 | 4 | 5 | 4 | Simple wrapped error contract. |

`Longitude`, `Latitude`, `Position`, and `Geometry` are aliases rather than models. Their bounds and fixed pair shape are useful, while the `Geometry` union relies on `type` literals to discriminate.

## Findings

1. **[HIGH] Brief savings can assert an impossible range** · `server/schemas.py:174-178`, `contracts/brief.schema.json:3-59`. Starting with `tests/fixtures/api/brief.json`, changing `savings_range` to `{"status":"range","low_usd":300,"high_usd":100,"basis":"Synthetic test assumption"}` was **ACCEPTED** by `Brief.model_validate`; replacing both bounds with `null` while retaining `status="range"` was also **ACCEPTED**. A generated or cached brief can therefore claim a range without a usable range, or with its low above its high, unlike `Savings` at `server/schemas.py:117-126`. Fix: add a `BriefSavings` `model_validator(mode="after")` enforcing both bounds present, `low_usd <= high_usd`, and nonempty basis for `range`; require null bounds for every non-range status. The existing brief fixture still validates. Guarding only `Brief` would leave direct `BriefSavings` callers exposed.

2. **[HIGH] Same-utility pairs pass the overlap contract** · `server/schemas.py:128-133,155-172`, `contracts/overlap.schema.json:100-102,126-128`. Starting with `tests/fixtures/api/overlaps.json`, I set `b_utility` equal to `a_utility` (`"Dominion Energy SC"`); `Overlap.model_validate` **ACCEPTED** it. This violates `SPEC.md` § Overlap rules (pairs only between different utilities) and can place a same-utility project pair in the ranked coordination list. Existing canonical ID, band, and year-gap guards do not compare utilities. Fix: add `if self.a_utility == self.b_utility: raise ValueError(...)` to `pair_consistency`, and require each utility name to be nonempty. The existing overlap and area fixtures still validate.

3. **[MEDIUM] Invalid `MultiLineString` members pass** · `server/schemas.py:50-52`, `contracts/project.schema.json:53-76`. `MultiLineGeometry.model_validate({"type":"MultiLineString","coordinates":[[]]})` was **ACCEPTED**. Its outer list has one member, but that member is not a line, so a downstream geometry renderer or distance routine gets an invalid GeoJSON line. Fix: define an annotated `LinePositions = Annotated[list[Position], Field(min_length=2)]` and use `list[LinePositions] = Field(min_length=1)` for `coordinates`. No supplied fixture uses an invalid multiline; existing fixtures still validate.

4. **[MEDIUM] Area counts accept negative values** · `server/schemas.py:202-208`, `contracts/area.schema.json:690-702`; the same loose count-map pattern occurs in `Meta` at `server/schemas.py:217-226`. Starting with `tests/fixtures/api/area.json`, I replaced `counts_by_band` with `{"touching":-1}`; `Area.model_validate` **ACCEPTED** it. A displayed negative count is nonsensical and undermines the area summary. Fix: use `dict[Band, Annotated[int, Field(ge=0)]]` for band counts and `dict[str, Annotated[int, Field(ge=0)]]` for utility and metadata counts; add an `Area` validator that reconciles band counts with `overlaps` and utility counts with `projects`. Existing area and meta fixtures still validate.

5. **[MEDIUM] Frozen contract records can change through nested lists** · `server/schemas.py:12-13,104-106`. After `ProjectCollection.model_validate(tests/fixtures/api/projects.json)`, `collection.features.clear()` succeeded; its feature count went from two to zero. `frozen=True` prevents attribute assignment but does not freeze list and dict contents, so a shared, supposedly read-only artifact can drift after validation without another contract check. Fix: use immutable sequences for read-only collections (including nested geometry, savings assumptions, area lists) and read-only mappings where needed, or copy validated data on every read boundary. The existing JSON fixtures remain valid if the models accept JSON arrays and coerce them to immutable internal containers; verify this in Pydantic and regenerate the exported schemas.

6. **[MEDIUM, static review] Exported JSON Schemas omit runtime cross-field rules** · `server/schemas.py:98-101,155-172`, `contracts/project.schema.json:379-408`, `contracts/overlap.schema.json:141-174`. The project schema independently allows `geometry:null` and `accuracy:"approximate"`; the overlap schema independently allows `distance_km:0` and `band:"lt_40km"`. The Pydantic validators reject these combinations, but the exported schema text contains no conditional constraint, so a schema-only client or fixture checker would accept them. Fix: export matching JSON Schema `if`/`then` clauses for geometry/accuracy and distance/band ranges, and add paired Pydantic and JSON Schema validation tests using the same invalid examples. Existing fixtures satisfy these relationships and would still validate. I did not execute a JSON Schema validator because the optional `jsonschema` package is absent.

Counts: **0 CRITICAL, 2 HIGH, 4 MEDIUM, 0 LOW**. The strongest design work is the explicit null treatment for unknown location and cost, the canonical pair ordering, and the band and year-gap checks. The two HIGH findings should be fixed before freezing G1a contracts, then all fixtures revalidated and the exported schemas regenerated.

material improvement still available: yes
