# Step 4 — Candidate Input Feature Assessment

**Assessment only:** no feature engineering or model fitting was performed.
“Candidate” means potentially usable after the listed evidence gates; it does
not claim a variable is predictive.

## Physical inputs and operating conditions

| Candidate field(s) | Physical meaning / confirmed units | Source verification and encoding | Scientific interpretation and interactions | Future-model position / leakage concern |
|---|---|---|---|---|
| `material_system_raw` | Material-pair label; categorical, no unit. | Three source-derived categories, 36 rows each; row labels match DOCX records. | Meaning is partially interpretable. The paper methodology flowchart says ZrSiO4:SiO2, while results and DOCX say ZrSiO4:TiO2. Paper summary-to-DOCX mapping is not established. | Consider only once material identity and cohort mapping are author-confirmed. One-hot/categorical treatment later; never ordinal-encode arbitrary material names. High grouping/leakage risk because source file and many conditions co-vary with system. |
| `filler_total_wt_percent_as_label` | Filler-level label, source tables present `%` / wt% context; values 0, 5, 10, 15. | All 108 parse as numeric-like labels; four levels, 27 rows each. Source labels verified. | Candidate dose/level. In FeTiO3 source, labels state total-style filler levels but do not establish each component's split. It co-varies with paired component values and table group. | Candidate after formulation clarification. Treat as designed categorical/ordered level or numeric dose only after confirming intended scale. Not evidence of monotonic/predictive effect. |
| `filler_a_wt_percent_interpreted`, `filler_b_wt_percent_interpreted` | Provisional component weight fractions; numbers 0, 2.5, 5, 7.5. Nominal wt%. | Parse numerically for all rows. Paired proportions are explicitly stated for TiO2:SiO2 and ZrSiO4:TiO2 DOCX contexts; FeTiO3 split is not explicitly established by its table labels. | A/B identities depend on the material system; paired values move together and are algebraically dependent on the total label under the current interpretation. | Do not treat as confirmed features until FeTiO3 formulation is verified. If retained later, avoid simultaneous redundant representations unless scientifically justified. |
| `applied_load_N_raw` | Applied load, N. | All 108 parse numerically. FeTiO3/TiO2 rows: 10, 20, 30; ZrSiO4-labeled rows: 10, 15, 20. DOCX headers and cells verified. | Interacts with sliding speed/distance and wear response by definition; cross-system ranges differ. | Strong future candidate operating input, but no effect is assumed. Design-based grouping and system confounding need evaluation. |
| `sliding_velocity_m_per_s_raw` | Sliding velocity, m/s. | All 108 parse; FeTiO3/TiO2: 0.5, 1, 1.5; ZrSiO4-labeled: 1, 1.5, 2. Source rows verified. | May be physically linked to disc speed and track diameter; interacts with load and distance. | Future candidate, conditional on confirming that the table's velocity is the intended control/measurement. Avoid redundant settings without checking relationships. |
| `sliding_distance_m_raw` | Sliding distance, m. | All 108 parse; FeTiO3/TiO2: 100, 200, 300; ZrSiO4-labeled: 50, 75, 100. Source rows verified. | Related to speed and duration. Experimental range differs by source/system. | Future candidate for interpolation only within supported conditions. It does not justify prediction outside the observed domain. |
| `sliding_diameter_mm_raw` | Sliding/track diameter, mm. | All 108 parse; 56 mm in FeTiO3/TiO2 and 46 mm in ZrSiO4-labeled records. DOCX header verified. | May determine speed from rpm; almost perfectly associated with dataset/system grouping here, so its independent effect cannot be separated confidently from material/source. | Candidate only if protocol confirms comparability. High confounding risk with material and source; report within-domain results separately. |
| `disc_speed_rpm_raw` | Disc rotation speed, rpm. | All 108 parse; FeTiO3/TiO2: 232, 417, 605; ZrSiO4-labeled: 200, 300, 400. DOCX header verified. | Related to velocity and diameter. May be a setpoint derived from the other two or a measured output; raw file alone does not settle which. | Investigate protocol before including alongside velocity and diameter. Redundant or derived input can obscure interpretation, although it is not automatically target leakage. |
| `test_duration_min_raw` | Test duration, minutes. | All 108 parse; 10 min in FeTiO3/TiO2 and 15 min in ZrSiO4-labeled records. | Related to velocity and sliding distance; system/source-specific values limit independent comparisons. | Candidate only if duration is known to be set independently and consistently. May act as a source/system proxy. |
| `temperature_raw` | Temperature field as extracted, but values are literal `Std. atm.` / `Std.atm.` in 36 rows; 72 rows blank. | Text-only, two formatting variants; matches source. No numeric temperatures are present. | Does not establish specimen or contact temperature. Presence is specific to one source. | Not usable as a numeric physical predictor as-is. Do not normalize spellings or infer a temperature value. Ask authors what this field denotes. |
| `test_remarks_raw` | Test remark; `Completed` where present. | 36 nonblank FeTiO3 values, 72 blanks in other source sets. | Likely procedural/status text rather than quantitative operating condition; missingness follows source. | Exclude from physical feature matrix. Presence can leak source identity. |

## Fields not suitable as physical predictors

| Field(s) | Reason to exclude from the candidate physical feature matrix |
|---|---|
| `record_id`, `sample_no_raw` | Identifiers/design labels, not physical causes. Sample number may encode orthogonal-array settings. |
| `source_document`, `source_table_index_zero_based`, `source_row_index_zero_based`, `source_table_label_raw` | Provenance and source layout; can reveal material group, filler level, design, or outcome strata. Preserve for audit and grouping only. |
| `raw_cells_json`, `extraction_status` | Audit/extraction metadata; raw cell JSON contains measurements and could expose the target directly. |
| `wear_rate_unit_as_table_heading` | Heading/provenance summary; identifies source-specific measurement definitions rather than an operating condition. |
| `coefficient_of_friction_raw`, `wear_rate_value_raw`, `specific_wear_rate_raw`, `wear_volume_loss_raw` | Candidate responses, not inputs when predicting those responses. Including one target as a feature while predicting another could leak outcomes or shared post-test measurements; require a separately justified prediction-time use case. |

## Feature-level cautions

- Actual values are stored as strings. Numeric parsing is possible for the
  operating-condition fields, but Step 4 does not rewrite or normalize them.
- `filler_total_wt_percent_as_label` and the two interpreted component columns
  are not independent. The component splits for FeTiO3 need authoritative
  formulation evidence.
- Velocity, diameter, and disc rpm may be mechanically related. Confirm the
  experimental protocol and whether each is a setpoint or derived/observed
  value before selecting simultaneous predictors.
- Load, speed, distance, filler level, and sample number follow designed
  tables. Random splitting can distribute near-identical design patterns or
  shared measurement signatures across train/test and inflate apparent
  performance.
- Operating ranges differ by material-source group; a model could learn the
  source/system partition rather than transferable physical relationships.
- Evaluation must distinguish interpolation among observed conditions from
  extrapolation to untested operating conditions or unseen formulations.
  Neither has been evaluated here.

## Future evaluation outline (not executed)

After target and input definitions are released, first establish independent
experiment/batch/replicate identifiers with the authors. Group all replicates
and repeated measurement signatures into a single split unit. Prefer grouped
cross-validation/holdout over ordinary random splitting; report per-material
and per-condition slices. If testing transfer to unseen material systems,
reserve a whole system only after resolving its identity and ensure sufficient
independent systems exist. Keep interpolation tests within the observed
feature domain separate from explicit extrapolation tests. Confirm final
performance with new physical validation experiments. With 108 records and
unresolved grouping, no evaluation design is yet validated.
