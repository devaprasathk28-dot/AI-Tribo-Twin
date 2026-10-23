# AI-TriboTwin — Step 4.9 Evidence Intake Checklist

## Purpose

This checklist governs how the project records and reviews scientific evidence
related to the remaining blockers. It exists to preserve the raw dataset,
keep the scientific boundary strict, and update target readiness only when
traceable evidence is actually received.

## 1. Preserve current outreach status

- Confirm the current outreach status from the tracker before taking any action.
- If there is no documented evidence of sending, keep the request status as
  `NOT_SENT`.
- If a human has sent the message, record the actual date, method, recipient,
  and the exact message version used. Do not infer send status from planning
  or draft-generation alone.
- If no actual send evidence exists, do not change the tracker to
  `SENT_AWAITING_RESPONSE`.

## 2. Record incoming evidence correctly

When a reply or attachment is received:

- Preserve the original email/message and each attachment in its native form.
- Do not modify the raw experimental CSV or any other original source file.
- Record the receipt date/time, sender, subject line, recipient, and channel.
- Save the original artifact with a stable filename and record its SHA-256 when
  practical.
- Record the relevant source pages, table names, figure numbers, or row IDs that
  the evidence addresses.
- Keep a separate working copy for analysis if a conversion or extraction is
  needed for readability.

## 3. Distinguish evidence types

Each item of evidence must be classified as one of the following:

- Author statement or email response.
- Original experimental record or laboratory sheet.
- Supplementary file or erratum.
- Published figure or table in the paper.
- Derived interpretation created by the project team.

Do not treat a verbal explanation as equivalent to the original measurement or
run sheet. A statement may clarify terminology, but it cannot replace missing
row-level data.

## 4. Link evidence to questions and blockers

Every received artifact should map to one or more of the following questions:

- Q-01: material identity
- Q-02: COF reconciliation and run-to-figure mapping
- Q-03: wear-rate definition and unit mapping
- Q-04: specific wear-rate definition and row-level availability
- Q-05: wear-volume-loss definition and row-level availability
- Q-06: run mapping between DOCX rows and paper figures/results
- Q-07: supplementary or corrected records

Map each artifact to the relevant blocker IDs and to the associated target
readiness record.

## 5. Record contradictions and limitations

When an item is unclear, partial, contradictory, or inaccessible:

- Record the limitation explicitly.
- Preserve both conflicting statements if they exist.
- Do not silently resolve the discrepancy by choosing the most plausible one.
- Label evidence as `INCOMPLETE`, `UNVERIFIED`, `CONTRADICTORY`, or
  `UNREADABLE` when appropriate.
- If original row-level measurements are unavailable, record that status and
  keep the target `BLOCKED`.

## 6. Update the tracker only with actual evidence

After evidence is received and archived:

- Update `data/validation/AUTHOR_CLARIFICATION_TRACKER.csv` only with actual
  recorded facts.
- Update `data/validation/STEP4_8_EVIDENCE_ASSESSMENT.csv` with the evidence
  reviewed, the assessment status, and any remaining gaps.
- Record a traceable audit trail when changing a status from `AWAITING_RESPONSE`
  to a more advanced state.
- Keep every update linked to the relevant question and blocker.

Do not mark a response as `VERIFIED` without checking the source, traceability,
consistency, and evidence relevance.

## 7. Preserve audit trail

For every status change:

- record the date of the review,
- the reviewer,
- the evidence artifact used,
- the specific question(s) and blocker(s) affected,
- the reason for the change,
- and whether the change affects target readiness.

If evidence remains insufficient, keep the target in its current blocked state.
No alternative target or model-ready decision may be made without explicit,
traceable evidence.

## 8. Scientific boundary

The project must not:

- modify raw measurements,
- add fabricated row values,
- silently resolve contradictory data,
- create a cleaned modelling dataset,
- train an ML model,
- or unlock a target based on assumptions.

Any evidence that clarifies a definition but does not provide the underlying
measurements must be recorded as such. It does not replace missing data.

## 9. Human action required next

The next human action is to:

1. Verify the paper-listed contact address against an official institutional or
   publication channel if possible.
2. Decide whether to send the approved clarification request manually.
3. Record the actual send event and delivery or bounce evidence if a message is
   sent.
4. Preserve any reply or supporting file exactly as received.
5. Assess each reply against the evidence protocol before revising target
   readiness.

No automated sending or monitoring is authorized in this step.
