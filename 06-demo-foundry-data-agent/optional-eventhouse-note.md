# Optional design note: add Eventhouse / KQL for raw telemetry

If you want a short “what next?” extension, keep the reconciled lakehouse as the business layer and add an Eventhouse/KQL source only for exploratory raw telemetry questions.

## Why add it

- KQL is better than lakehouse SQL for bursty raw log slicing, time-window scans, and operator-style troubleshooting over the unreconciled stream.
- The lakehouse should remain the stable business-answer layer used by the workshop’s gold metrics and frozen scores.

## Suggested pattern

1. Keep `gold.*` and `ml.*` as the canonical business source.
2. Add a second published source for raw telemetry summaries in Eventhouse/KQL.
3. Route business questions to the lakehouse source and troubleshooting questions to the KQL source.
4. Keep the same refusal rules and do not mix raw-log answers with the frozen risk story unless the question explicitly asks for raw evidence.

## Watch-outs

- Cross-source tool behavior is preview-heavy.
- Verify source-count limits and any extra capacity implications before promising it live.
