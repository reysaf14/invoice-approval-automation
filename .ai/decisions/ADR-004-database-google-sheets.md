# ADR-004: Database - Google Sheets Only (MVP)

## Status
Accepted

## Context
Need to store invoice master data, status, audit trail, and support deduplication queries. Volume: ~120 rows/month, ~1,440 rows/year. Low complexity queries (filter by status, date range, vendor). Team already uses Google Sheets for manual rekap.

## Decision
Use **Google Sheets as the sole database** for MVP. No separate SQL database.

## Alternatives Considered
1. **PostgreSQL (local Docker)** - Full SQL, ACID, but separate infra, need sync to Sheets for Admin visibility
2. **SQLite (file-based)** - Lightweight, but single-writer, no concurrent access, still need Sheets for UI
3. **Airtable / Baserow** - Better UI, but additional cost/vendor, Sheets already mandated

## Consequences
- **Positive**: Zero additional infrastructure, Admin/Owner already familiar, real-time collaboration, native n8n integration, audit trail via version history, free
- **Negative**: No referential integrity, row limit (10M cells ~ OK for years), query performance degrades >10K rows, concurrent write conflicts possible, no transactions
- **Risk**: Race condition on status update (two approvals simultaneously) → mitigate with idempotent update by invoice_id + status check

## Implementation Notes
- Single master sheet: `Invoices` with columns per LDL schema
- Dedupe: Read sheet → filter in n8n (composite key) → only write if not exists
- Idempotent update: `Update` operation by `invoice_id` (unique), check current status before write
- Archive strategy: After 2 years, move old rows to `Invoices_Archive_YYYY` sheet
- Future: If volume > 500/month or complex reporting needed → ADR for PostgreSQL + Sheets sync

## Columns (per LDL)
invoice_id, received_at, vendor, invoice_date, invoice_number, amount, status, confidence, drive_file_id, drive_file_link, source, approved_at, approved_by, rejected_at, reject_reason, reminder_count, last_reminder_at, created_at, updated_at