# AI Agent Decision Log

Khong can copy full conversation. Ghi cac decision quan trong.

## Decision 1
- Hypothesis: Contract validation can detect schema drift before transformation.
- Prompt / request to agent: Complete type, freshness, severity, and action validation.
- Agent proposal: Parse declared integer/number/string/datetime types, validate freshness, and emit block/quarantine/warn actions.
- Evidence/test: Duplicate order IDs produce a failed `unique`/critical/block issue; invalid currency produces accepted-values failure.
- Accept / reject / revise: Accept.
- Why: Deterministic failures are actionable and preserve the stable list-of-dicts API.

## Decision 2
- Hypothesis: Revenue can inflate when multiple active customer versions join one order.
- Prompt / request to agent: Add the smallest protection for the SCD join and a dbt unit test.
- Agent proposal: Deduplicate active customers with `row_number()` before joining; assert two orders totaling 170.0 remain two rows.
- Evidence/test: The unit fixture includes two active versions for C0001 and expects revenue 170.0, exposing the one-to-many join.
- Accept / reject / revise: Accept.
- Why: The invariant protects the CEO revenue mart without hiding source duplicates.

## Decision 3
- Hypothesis: A short anomaly spike should not page unless the long window also burns.
- Prompt / request to agent: Complete robust anomaly, transitive column lineage, and multi-window burn behavior.
- Agent proposal: Use same-segment history/MAD in auto mode, BFS for columns, and page only sustained short+long burn thresholds.
- Evidence/test: Volume drop is detected against a stable baseline; a transient high short-window burn with low long-window burn returns `page=False`; lineage traversal includes all descendants.
- Accept / reject / revise: Accept.
- Why: This reduces seasonality false positives and makes alerts actionable.
