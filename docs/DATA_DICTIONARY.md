# Data Dictionary — Raw Extraction

All columns ending in `_raw` preserve source text as extracted. Numeric conversion and normalization are deliberately deferred until the audit is complete.

| Column | Meaning | Status / note |
|---|---|---|
| `record_id` | Stable row ID generated during extraction | Project-generated, not source-provided |
| `material_system_raw` | Material pair identified from source test-record filename | Source-derived label |
| `filler_total_wt_percent_as_label` | Filler-level label found in table heading | Source label parsed into a number; raw heading also retained |
| `filler_a_wt_percent_interpreted` | Provisional component-level filler percentage | Paired proportions are stated in the TiO2 and ZrSiO4 DOCX records; the FeTiO3 table labels do not establish each component's split |
| `filler_b_wt_percent_interpreted` | Provisional component-level filler percentage | Paired proportions are stated in the TiO2 and ZrSiO4 DOCX records; the FeTiO3 table labels do not establish each component's split |
| `sample_no_raw` | Sample number text | Raw source value |
| `applied_load_N_raw` | Applied load | Header indicates N; raw cell text retained |
| `sliding_velocity_m_per_s_raw` | Sliding velocity | Header indicates m/s; raw cell text retained |
| `sliding_distance_m_raw` | Sliding distance | Header indicates m; raw cell text retained |
| `sliding_diameter_mm_raw` | Sliding diameter | Header indicates mm; raw cell text retained |
| `disc_speed_rpm_raw` | Disc rotation speed | Header indicates rpm; raw cell text retained |
| `test_duration_min_raw` | Test duration | Header indicates minutes; raw cell text retained |
| `test_remarks_raw` | Remarks field, if present | May be blank for sources without a remarks column |
| `temperature_raw` | Temperature field, if present | Values such as `Std. atm.` preserved as text |
| `coefficient_of_friction_raw` | COF measurement | Preserved as source text; `RAW-096` (`0. 29`) and `RAW-105` (`0. 36`) are source-confirmed formatting anomalies; paper narrative not reconciled |
| `wear_rate_value_raw` | Numeric wear-related response in source table | Unit/meaning unresolved; never assume this is specific wear rate |
| `wear_rate_unit_as_table_heading` | Description of relevant table headings | Textual summary; inspect source heading |
| `specific_wear_rate_raw` | Separate specific-wear-rate column, where present | Blank in all 72 rows where the TiO2 and ZrSiO4 source tables contain this column; FeTiO3 source tables have no separate column |
| `wear_volume_loss_raw` | Wear-volume-loss response | Blank in all rows; no row-level volume-loss column in the inspected wear tables; do not infer from separate weight-loss tables |
| `source_document` | Exact source DOCX filename | Provenance |
| `source_table_index_zero_based` | Table index in DOCX | Zero-based programmatic index |
| `source_row_index_zero_based` | Row index in DOCX | Zero-based programmatic index |
| `source_table_label_raw` | Extracted title/label for the table | Blank for 72 TiO2 and ZrSiO4 rows whose group labels occur in preceding document paragraphs |
| `raw_cells_json` | JSON array containing every original cell from the row | Loss-minimizing transcription aid |
| `extraction_status` | Extraction review status recorded in the raw file | Original source rows are compared in `data/validation/ROW_LEVEL_SOURCE_VERIFICATION.csv`; scientific ambiguities remain open |

## Naming and units policy

The `_raw` suffix means the value is not yet normalized or approved for modeling. The `interpreted` suffix means an explicit provisional interpretation has been made. Never use either wear field as a modeling target until the audit resolves what the values represent and their units.
