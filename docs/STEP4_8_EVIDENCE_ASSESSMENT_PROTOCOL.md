# Step 4.8 — Evidence Assessment Protocol

## 1. Preserve incoming evidence

1. Save each original email/message in its native export format when
   available. Preserve original attachments without editing or renaming their
   internal contents; make a separate working copy for analysis.
2. Record receipt date/time and timezone as shown by the message, sender and
   recipient metadata, channel, subject, and message artifact path. Do not
   treat a forwarded summary as the original message.
3. For every attachment or provided file, record filename, file type, size,
   source/version/date information when available, and SHA-256 where practical.
   Keep an immutable copy and document any extraction or conversion.
4. If evidence cannot be archived or its source is unclear, record that
   limitation. Do not label it primary or verified solely because it arrived
   in an author response.

## 2. Assess each question and blocker separately

Create or update the corresponding row in
[`../data/validation/STEP4_8_EVIDENCE_ASSESSMENT.csv`](../data/validation/STEP4_8_EVIDENCE_ASSESSMENT.csv)
and tracker. Record the literal claim/answer, evidence artifact and exact
location, source authority, traceability, consistency checks, reviewer, and
readiness impact. One response can address multiple questions, but each
question requires its own evidence assessment and decision.

Compare new material with:

- The original paper and the existing scientific review.
- The three source DOCX records and the Step 3 row-verification manifest.
- The unchanged raw CSV and its raw cell strings.
- Existing data dictionary, audit, issue registers, and target-readiness
  matrix.

Check row/run identifiers, material/formulation, conditions, field names,
units/scales, missingness, and source version. Verify that each mapping is
complete and that measurements match any existing source record exactly
where exact comparison is expected. Do not normalize anomalous raw strings,
impute blanks, derive volume loss from another field, digitize grouped graphs
as row values, or discard contradictions.

## 3. Assessment statuses

- `AWAITING_RESPONSE`: no relevant response/evidence has been recorded.
- `RECEIVED_UNREVIEWED`: a response or artifact is recorded but not yet
  checked for source, completeness, and consistency.
- `PARTIALLY_RESOLVED`: some parts are supported, while required evidence or
  questions remain open. State exactly what remains.
- `RESOLVED`: authoritative, relevant, traceable evidence satisfies the
  blocker-specific acceptance criteria. A response alone is insufficient
  where original measurements or run-level mapping are needed.
- `UNRESOLVED`: reviewed evidence is insufficient, contradictory, unverifiable,
  or confirms required measurements/records are unavailable.

Use separate delivery and verification statuses in the tracker. A successful
delivery is not a response; a response is not verified evidence.

## 4. Blocker-specific acceptance

| Blocker | Evidence required before marking resolved |
|---|---|
| Material identity | Authoritative composition/preparation record or explicit author confirmation tied to actual tested sample labels/runs. A flowchart alone or majority wording is insufficient. |
| COF | Original row-level measurements or authoritative run-to-figure mapping that explains the reported range and identifies conditions/protocol. Preserve `0. 29` and `0. 36` as raw strings regardless. |
| Wear rate | Precise measurement definition, procedure/formula, units and scale, with table/column mapping; establish cross-system comparability before pooling. |
| Specific wear rate | Definition and units plus traceable row-level values and run IDs. A definition alone cannot create missing measurements. |
| Wear volume loss | Individual measurements, units, measurement method and run identifiers; grouped plots or summary claims alone do not qualify. |
| Run mapping | Enough stable identifiers to connect material, filler ratio, load, speed, distance, measured responses, and paper figures/tables; assess repeated-run/group leakage before future evaluation. |
| Supporting records | Verify provenance, file integrity, version, field meanings, row/run mapping, and consistency with existing sources. Log every contradiction rather than silently choosing a source. |

## 5. Updating target readiness

Update `TARGET_READINESS.csv` only after the evidence register and assessment
record contain enough evidence for the target-specific criteria. Review
independently whether definition, units, row-level availability,
traceability, consistency, missingness, and leakage/grouping are adequate.
Keep a target `BLOCKED` if its row-level values are absent even when an author
confirms the intended definition or unit. Update the readiness rationale and
link the evidence used; do not change the raw CSV as part of evidence review.

Any proposed alternative objective requires a separate explicit research
decision. It must not be used as a shortcut around unresolved target evidence.

## 6. No response, bounce, unavailable records, or contradiction

- **No response:** Leave questions `AWAITING_RESPONSE`; do not infer consent,
  confirmation, or resolution from silence. A human may approve a follow-up
  through a verified official route. Do not follow up automatically.
- **Bounce:** Preserve the bounce evidence, set delivery to `BOUNCED`, keep the
  question unanswered, and ask a human to verify another official channel.
  Do not guess addresses.
- **Records unavailable:** Record the author's statement as a response, but
  retain missing targets as `UNRESOLVED`/`BLOCKED`. Do not derive or recreate
  missing values. Any alternative objective needs separate approval.
- **Contradiction:** Preserve both claims, identify their source and authority,
  mark the assessment `UNRESOLVED` or `PARTIALLY_RESOLVED`, and request
  targeted clarification only with human approval. Never silently select one
  version.
- **Definition without measurements:** It may clarify terminology, but does
  not unlock a target whose traceable row-level values are missing.

## Current state

The clarification request remains `NOT_SENT`; no reply or response artifact
has been recorded. No inbox connector or continuous monitoring is configured.
All scientific targets remain blocked.
