# AI-TriboTwin — Step 4 Data Readiness Report

**Decision:** Step 4 assessment completed. No candidate target is currently
released for model training; proceed to Step 5 only after the release criteria
below are satisfied with authoritative evidence.

## 1. Source and raw-data integrity

- Raw CSV: 108 records, 25 columns.
- Source verification manifest: 108 records, all `VERIFIED_EXACT` according
  to the existing manifest.
- Step 3 mapped-field comparison: 1,116 comparisons and zero reported
  mismatches, against the three indexed DOCX files. This confirms transcription
  to those records; it does not confirm scientific meaning or that the DOCX
  records correspond to the paper's plotted results.
- Current raw CSV SHA-256:
  `bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d`
- Recorded Step 3 SHA-256:
  `bc4b438bfcb472bdb92d653953b23acd3ff20dbaf3e0220704aa0a16bddedd1d`
- Result: **MATCH**. No edits to the raw CSV, original DOCX files, or PDF were
  made in Step 4. No clean/modeling dataset, predictions, or trained models
  were created.

The three DOCX systems have 36 rows each: FeTiO3:SiO2, TiO2:SiO2, and
ZrSiO4:TiO2. The last identity remains scientifically disputed because the
paper's methodology flowchart says ZrSiO4:SiO2.

## 2. Variable inventory and data-quality summary

The full 25-column inventory, including roles, values, missingness, unit
evidence, source traceability and leakage risks, is in
[`STEP4_VARIABLE_INVENTORY.md`](./STEP4_VARIABLE_INVENTORY.md).

Relevant observed quality facts:

| Field(s) | Observed condition | Step 4 interpretation |
|---|---|---|
| All CSV columns | Parsed as text; CSV carries no declared types. Numeric fields were separately parse-checked. | Do not confuse CSV parsing type with scientific type. No raw conversion performed. |
| `coefficient_of_friction_raw` | 108 nonblank; 106 parse; `RAW-096`=`0. 29` and `RAW-105`=`0. 36` do not parse. Both exactly match source rows. | Preserve verbatim; authoritative correction/interpretation required before any numerical use. |
| `wear_rate_value_raw` | 108 values parse numerically; observed literal numeric range 185.69–508.96. | Numeric completeness does not establish target definition or units. |
| `specific_wear_rate_raw` | 108 blank; separate column exists but blank in 72 rows, absent from the FeTiO3 table layout for 36 rows. | No row-level target observations. |
| `wear_volume_loss_raw` | 108 blank; no row-level volume-loss column in inspected DOCX wear tables. | No row-level target observations. |
| `test_remarks_raw` | 72 blank; `Completed` in 36 FeTiO3 records. | Source-dependent metadata, not a physical predictor. |
| `temperature_raw` | 72 blank; other 36 values are `Std. atm.` or `Std.atm.`. | Not a numeric measured temperature; do not normalize/infer. |
| `source_table_label_raw` | 72 blank because TiO2 and ZrSiO4 group labels occur in preceding DOCX paragraphs. | Provenance/context omission, not a physical missing measurement. |
| `filler_a_wt_percent_interpreted`, `filler_b_wt_percent_interpreted` | Values parse, but FeTiO3 paired split is not explicit in its source table labels. | Provisional interpretations, not fully verified formulation inputs. |
| Repeated measurement signatures | 14 identical cross-material signatures affect 28 rows; every row separately matches its source. | Retain; status as shared controls vs repeated measurements is unresolved. |
| Temperature strings | Both `Std. atm.` and `Std.atm.` appear in source. | Preserve as source variants. |

Operating inputs all parse numerically, but have unequal system ranges and
some are mechanically related. By system, FeTiO3 and TiO2 have loads
10/20/30 N, speeds 0.5/1/1.5 m/s, distances 100/200/300 m, diameter 56 mm,
rpm 232/417/605, and duration 10 min. The ZrSiO4-labeled records have loads
10/15/20 N, speeds 1/1.5/2 m/s, distances 50/75/100 m, diameter 46 mm, rpm
200/300/400, and duration 15 min. These observed ranges do not by themselves
prove comparable protocols or transferable feature effects.

## 3. Paper claims versus row-level experimental records

The paper's narrative/figures must remain separate from the DOCX observations:

- Paper p. 12 states COF approximately 0.300–0.303. Figures on pp. 15–17 show
  grouped values in that narrow range by filler level and sliding distance.
  The plots show no sample IDs or traceable mapping to the DOCX rows, whose
  verified COF values span much wider ranges. The paper values are not
  substitutes for the row-level observations.
- Paper p. 10's visible method text references 10 N and 0.96 m/s for the
  described COF setting. The DOCX sets contain multiple loads, speeds and
  distances; their relationship to paper plots is not established.
- The paper's visible p. 12 specific-wear narrative prints `mm³/Nm` and
  `×10⁻⁶`. Its p. 25 conclusion prints `0.5 mm³/Nm` without that exponent.
  The DOCX headings use different strings, including `Specific Wear rate
  (m3/Nm)`; those separate cells are blank where present.
- Figures 11–13 label the y-axis `WEAR VOLUME LOSS` but show no unit or
  sample-level identifier. The paper conclusion's `1.5 mm³` is an aggregate/
  condition claim, not a value tied to an individual CSV row.
- The p. 9 methodology flowchart labels the pair `ZrSiO4:SiO2`; paper results
  text/figures and the associated DOCX records label `ZrSiO4:TiO2`. This
  visible contradiction is unresolved; majority mention does not settle
  experimental identity.

See [SCIENTIFIC_SOURCE_REVIEW.md](./SCIENTIFIC_SOURCE_REVIEW.md) for the
page-by-page visual record and [SOURCE_ISSUES.csv](../data/validation/SOURCE_ISSUES.csv)
for issue-level evidence and follow-up.

## 4. Candidate target decisions

| Target | Current decision | Why |
|---|---|---|
| COF | **BLOCKED** | 108 observations exist and the dimensionless quantity has a prose definition, but two strings are malformed and paper summaries/graphs conflict with the much wider row-level range without a run mapping. |
| Raw wear-related measurement / wear rate | **BLOCKED** | 108 numeric values exist and their transcription is verified, but source headings differ and do not establish common semantics, units, formula, or mapping to the paper's definition. |
| Specific wear rate | **BLOCKED** | No row-level values: all CSV cells are blank; source column is blank in 72 rows and absent in 36. Paper narrative units/scales are not consistently mapped. |
| Wear volume loss | **BLOCKED** | No row-level source column or values. Paper offers grouped plots/conclusion claims, not traceable experimental rows, and chart axes omit units. |

The machine-readable assessment is
[`TARGET_READINESS.csv`](../data/validation/TARGET_READINESS.csv). No target
is marked `READY` or `CONDITIONALLY_READY`.

## 5. Candidate input feature position

Potential future physical inputs, subject to evidence gates, are material
system, filler level/composition, applied load, sliding velocity, sliding
distance, sliding diameter, disc rpm, and test duration. Material identity and
FeTiO3 composition split are unresolved; temperature is not numeric; remarks
are source-dependent. A candidate input is not a claim of predictive value.

Exclude identifiers, sample number, source names/indices/labels, raw JSON,
extraction status, and heading summaries from a physical feature matrix.
Exclude all response fields from predictors when predicting those responses.
See [`STEP4_FEATURE_ASSESSMENT.md`](./STEP4_FEATURE_ASSESSMENT.md).

## 6. Leakage and evaluation risks

- Source documents, table indices, row positions, record IDs, sample numbers,
  remarks availability and heading text can reveal cohort/design and should
  not become ordinary predictors.
- Component filler percentages may duplicate/reveal total filler level.
  Disc rpm, diameter, velocity, duration and distance may be mechanically
  related or derived; confirm acquisition protocol before selecting them
  together.
- COF and wear responses are post-test measurements. Using one response as an
  input for another can leak outcome information unless prediction-time
  availability and the use case are explicitly established.
- There are 108 rows, three material labels, 12 source-table groups, and 14
  repeated cross-material signatures affecting 28 rows. Random row splitting
  could place linked or repeated design patterns in both train and test.
- Protocol, target definitions, material identity and source-cohort
  relationships are unresolved. Performance may reflect source/system
  partitions rather than transferable relationships.
- Future evaluation should group replicates/repeated signatures by confirmed
  independent run, batch or experimental unit. Compare grouped holdout/
  cross-validation with simple baselines only after target release; report
  per-system slices. Distinguish interpolation within the observed domain
  from extrapolation to unseen conditions/materials. For extrapolation, use
  explicitly held-out conditions/systems and later physical validation.
  Current evidence is insufficient to validate any split design.

## 7. Author clarification and release evidence

Before creating a Step 5 modelling dataset, obtain authoritative answers for:

1. **COF linkage:** Do the paper narrative and Figures 8–10 (including the
   narrow 0.300–0.303 values) describe these DOCX runs? Provide row/sample IDs,
   raw measurement records, or an explicit statement that the datasets differ.
   Clarify the two malformed source strings without changing this raw file.
2. **Wear measurement mapping:** For each DOCX system, what exactly does the
   `Wear rate` number measure? Provide the equation, instrument output,
   calibration/procedure, exact scale/unit, and the mapping to the paper's
   wear-rate terminology.
3. **Specific wear rate:** Confirm its exact unit/exponent and resolve the
   paper's different scales. Supply primary row-level values and run IDs if
   this target is intended.
4. **Wear volume loss:** Supply individual values, explicit units, method,
   calibration, and run identifiers underlying Figures 11–13 and the
   conclusion. Do not derive them from current columns.
5. **Material identity:** Confirm whether the tested pair was ZrSiO4:SiO2 or
   ZrSiO4:TiO2 and explain/correct the flowchart only with authoritative
   evidence.
6. **Formulation and protocol:** Confirm the FeTiO3:SiO2 component split,
   DOCX-to-paper test-condition mapping, meaning of `Std. atm.`, and whether
   rpm/velocity/diameter/duration are independent setpoints or related
   quantities.
7. **Experimental grouping:** Identify independent batches, replicates,
   shared controls, repeated signatures and source-table design units needed
   for leakage-safe evaluation.

### Step 5 acceptance criteria

Step 5 may create a separate, reproducible modelling dataset only after:

- At least one target has a written, unambiguous operational definition,
  unit/scale, measurement method, and row-level source traceability.
- The target's missingness, anomalies, and source-to-paper consistency have
  explicit dispositions supported by authoritative evidence; raw values
  remain preserved.
- Input definitions, material formulations/identities, and test-condition
  meanings are documented per source/system.
- A repeat/group key and a leakage-aware evaluation plan are agreed for the
  intended prediction scope (interpolation vs extrapolation).
- The target-specific readiness row is explicitly upgraded based on evidence;
  no assumptions, inferred unit conversions, or grouped-plot digitization are
  silently used as row-level measurements.

**Current outcome: Step 5 is not cleared.** No target meets these criteria.
