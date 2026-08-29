# Incident Report

## Severity
P1 — revenue data integrity and support knowledge freshness were both at risk.

## Summary
The pipeline could report success while an input fault changed business semantics. The controls now detect deterministic contract failures, volume anomalies, stale KB documents, and trace their downstream consumers.

## Detection
- Signal: contract validation, row-count anomaly, and KB freshness check.
- First observed time: 2026-08-29 game-day validation run.

## Root Cause
Public fault injection demonstrated two independent causes: duplicate order ingestion creates repeated primary keys, while the stale-KB scenario shifts `published_at` beyond the 60-minute contract. A separate transformation risk was an active-customer one-to-many join; the mart now keeps the newest active version per customer.

## Evidence
1. `order_id` is declared critical/unique; duplicate rows fail deterministically and action `block` is emitted.
2. `kb_documents.published_at` is governed by a 60-minute freshness contract; stale data is quarantined.
3. `stg_orders -> fct_daily_revenue -> ceo_revenue_dashboard` is the order-data blast radius.

## Blast Radius

```text
root
stg_orders
-> fct_daily_revenue
-> ceo_revenue_dashboard
```

## Mitigation
Block the affected orders load on critical contract failures; quarantine stale KB input; rebuild only after the source is corrected. Deduplicate active customer versions in the mart to prevent revenue inflation.

## Recovery
Reset/re-ingest the source, rerun contract and anomaly checks, then rebuild dbt models and verify dashboard totals.

## Verification
- [ ] Contract healthy
- [ ] dbt tests healthy
- [ ] anomaly returned to expected range
- [ ] SLO healthy / budget understood
- [ ] downstream output verified

## Prevention / Action Items
| Action | Owner | Deadline | Why |
|---|---|---|---|
| Add freshness/type checks to CI | Data Platform | Next sprint | Detect schema and staleness before publish |
| Add source ingestion idempotency | Ingestion | Next sprint | Prevent duplicate primary keys |
| Monitor multi-window burn | SRE | Next sprint | Page only for sustained impact |
