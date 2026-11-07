# Phase 1.4 — Data Quality, Mapping and Governance

## Automated profiling outputs
- `reports/phase1/source_inventory.csv`: row/column counts, full-row duplicate counts.
- `reports/phase1/column_profile.csv`: each column type, distinct count, null count %, numeric/date range.
- `reports/phase1/quality_checks.csv`: uniqueness, source duplicates, foreign-key integrity, event/date and FTE checks; REVIEW issues.
- `docs/phase1/source_to_target_mapping.csv`: direct raw → staging field mapping; target transformations come in Phase 2/3.

## Quality rule severity
- **BLOCK**: duplicate key, orphan foreign key, invalid FTE/headcount, corrupt file/schema missing a required column.
- **REVIEW**: five-person historical HC mismatch; DimDate too short; salary budget definition unknown; transfer events absent despite challenge description.
- **ALLOW**: TerminationDate/Type/Reason null for active staff; TerminationType/Reason null on Hire events.

## Proposed acceptance tests in the next phase
1. Source checksum, file metadata, sheet count and required header check.
2. Uniqueness and not-null constraints on business keys.
3. Employee/department/location foreign-key relationship tests.
4. Event type accepted values; employment status and termination fields consistency.
5. Historical snapshot reconciliation vs event-derived headcount by month (document exceptions).
6. Time-aware join tests for salary, surveys and reviews (avoid leakage).
7. Targets grain and scenario consistency checks.
8. Idempotent ingestion: re-running input produces no extra rows.

## Governance and privacy
- Keep raw HR files on local machine / private storage, ignore in public Git repositories.
- Use aggregated screenshots and anonymized IDs; avoid sharing personal salary/absence/performance rows.
- Record data provenance, assumptions and issues (not silently overwrite source anomalies).
- Explicitly document whether data is synthetic/public and its permitted reuse.

## Post-review remediation status

Run `python src/phase1/run_phase1.py` for the complete 2-script audit plus regression tests.
- `reports/phase1/monthly_reconciliation.csv` compares month-end snapshot HC with employee hire/termination as-of HC for all 36 periods; 33 periods require review.
- `reports/phase1/restructuring_evidence.csv` documents June 2025 departures and July scenario resets across D002–D005.
- `reports/phase1/review_status.csv` distinguishes documented source anomalies, derived fixes and metrics blocked by missing metadata.
- `data/processed/dim_date_extended.csv` is a generated calendar (2018–2025); raw source retained without modification.
- Public column profiles intentionally suppress row-level example values.

The four original REVIEW checks remain visible to avoid concealing upstream limitations. The derived calendar resolves the technical date gap; it does not retroactively change the DimDate worksheet. See `06_review_resolutions.md`.
