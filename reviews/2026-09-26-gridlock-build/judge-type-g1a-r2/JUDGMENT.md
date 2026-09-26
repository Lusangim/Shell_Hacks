# G1a type design confirmation — round 2

Frozen copy HEAD `03ae694925a5a33aacc63f2b00dee45f0d44d451`, verified before review. I reviewed the changed `server/schemas.py`, generated contract diffs, `tests/pipeline/test_contracts.py`, the first judgment, and the governing contract rules. Read-only probes used `GRIDLOCK_AI=off` and port 8781. `tests/pipeline/test_contracts.py`: **26 passed**. I directly validated 12 typed API fixtures: all 12 accepted. The supplied basemap fixture was covered separately by the test module's `dict` case. No product code changed in this review.

Scores are 1–5, where 5 means stronger encapsulation, fewer invalid states, greater caller usefulness, or fewer escape hatches. This is a confirmation score for the current models.

| Model or type | Encapsulation | Impossible states | Caller use | Escape hatches | Assessment |
|---|---:|---:|---:|---:|---|
| `Contract` | 5 | 4 | 5 | 4 | Forbids extra fields and assignment; nested lists remain mutable. |
| `Accuracy` | 5 | 5 | 5 | 5 | Closed accuracy vocabulary. |
| `Band` | 5 | 5 | 5 | 5 | Closed distance-band vocabulary. |
| `Source` | 4 | 3 | 5 | 3 | Requires document, page, URL text. |
| `PointGeometry` | 5 | 5 | 5 | 5 | Bounded coordinate pair. |
| `LineGeometry` | 5 | 5 | 5 | 5 | Requires at least two positions. |
| `MultiLineGeometry` | 5 | 5 | 5 | 5 | Now requires at least two positions in each member. |
| `ProjectProperties` | 4 | 4 | 5 | 3 | Stable ID and cost rules; open provenance text. |
| `ProjectFeature` | 5 | 4 | 5 | 4 | Relates geometry to accuracy. |
| `ProjectCollection` | 3 | 3 | 5 | 3 | Clear JSON shape; nested collection can still mutate. |
| `Savings` | 5 | 5 | 5 | 4 | Ordered range and assumptions required. |
| `Overlap` | 4 | 4 | 5 | 3 | Canonical ID, band, year gap and different utilities checked. |
| `BriefSavings` | 5 | 5 | 5 | 4 | Now rejects absent, reversed and unsupported numeric ranges. |
| `Brief` | 4 | 4 | 5 | 3 | Its nested savings now has the matching invariant. |
| `Center` | 5 | 5 | 5 | 5 | Bounded coordinates. |
| `Area` | 4 | 4 | 5 | 3 | Nonnegative counts must match returned projects and overlaps. |
| `SourceDocument` | 4 | 3 | 4 | 3 | Readable source summary with open text. |
| `Meta` | 3 | 3 | 5 | 2 | Count values are nonnegative; map keys and stage relations remain loose. |
| `SearchResult` | 4 | 4 | 5 | 3 | Closed kind, bounded coordinates, flexible reference. |
| `ErrorDetail` | 4 | 3 | 4 | 3 | Stable shape, free-form code. |
| `ErrorResponse` | 5 | 4 | 5 | 4 | Simple wrapped error. |

`Longitude`, `Latitude`, `Position`, `LinePositions`, `Count`, and `Geometry` are aliases, not models. The new `LinePositions` and `Count` aliases encode the two repaired medium invariants.

## Prior findings and confirmation

1. **[HIGH, CLOSED] Brief savings range** · `server/schemas.py:179-194`, `tests/pipeline/test_contracts.py:108-123`. From `brief.json`, `status="range", low_usd=300, high_usd=100` now **REJECTED** by `Brief.model_validate`; `low_usd=null, high_usd=null` also **REJECTED**, as is a whitespace-only basis. Existing `brief.json` **ACCEPTED**. The `BriefSavings` validator covers direct callers and the nested `Brief`. No fixture adjustment needed.

2. **[HIGH, CLOSED] Same-utility overlap** · `server/schemas.py:135-136,158-162`, `tests/pipeline/test_contracts.py:130-135`. From `overlaps.json`, making `b_utility` equal to `a_utility` now **REJECTED** by `Overlap.model_validate`. An empty utility string is also **REJECTED**. Existing `overlaps.json` and `area.json` **ACCEPTED**. No fixture adjustment needed.

3. **[MEDIUM, CLOSED] Empty multiline member** · `server/schemas.py:38,53-55`, `contracts/project.schema.json:53-75`, `tests/pipeline/test_contracts.py:138-142`. `coordinates:[[]]` and a member with one position both **REJECTED**. The exported project schema now sets `minItems:2` on each line. Existing project fixtures **ACCEPTED**. No fixture adjustment needed.

4. **[MEDIUM, CLOSED] Negative and inconsistent counts** · `server/schemas.py:39,218-232,241-250`, `tests/pipeline/test_contracts.py:145-169`. An area fixture with `counts_by_band:{"touching":-1}` now **REJECTED**; a count of two for one returned Georgia Power project is also **REJECTED**; a meta fixture with `stage_counts.kept=-1` is **REJECTED**. Existing area and meta fixtures **ACCEPTED**. The exported schemas carry nonnegative count limits. No fixture adjustment needed.

5. **[MEDIUM, OPEN] Frozen records still permit nested mutation** · `server/schemas.py:13-14,107-109`. After validating `projects.json`, `ProjectCollection.features.clear()` still succeeds, changing the validated feature count from two to zero. This can invalidate a supposedly read-only artifact after the boundary check. Exact fix remains immutable internal sequences and mappings, or defensive copies at every read boundary. Existing JSON fixtures would still validate if their arrays were coerced to immutable internal containers; this was not implemented or tested here.

6. **[MEDIUM, OPEN; static] JSON Schemas still omit cross-field invariants** · `server/schemas.py:101-104,158-175`, `contracts/project.schema.json:380-409`, `contracts/overlap.schema.json:143-175`. Pydantic **REJECTED** `projects.json` with its first feature changed to `geometry:null` while accuracy remained `approximate`; it also **REJECTED** `overlaps.json` with distance zero and band `lt_40km`. The exported schema text still independently permits those field values and has no conditional relation. A schema-only validator would therefore apply a weaker contract. Exact fix remains generated JSON Schema `if`/`then` rules for geometry/accuracy and distance/band, with paired invalid-case schema tests. Existing fixtures satisfy the rules. This is a static schema finding: the optional `jsonschema` package is absent, and I did not install or run it.

**New contract problems from the fix:** none found in the changed models or supplied fixtures. **Current counts:** 0 CRITICAL, 0 HIGH, 2 MEDIUM, 0 LOW. The high-severity G1a gate is closed; the two remaining medium issues can be tracked for a later correction round.

material improvement still available: yes
