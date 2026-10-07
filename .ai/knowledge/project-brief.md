# Project Brief: Invoice Approval Automation

## Purpose

Provide a small-team MVP for turning invoice image files into structured, reviewable rows without manual transcription of every field.

## Current User Journey

1. Finance admin places an invoice JPG/JPEG/PNG in a configured Google Drive folder.
2. n8n polls the folder and downloads the file.
3. DeepSeek performs image OCR and returns normalized JSON fields.
4. The workflow routes low-confidence results to manual review, records duplicates, or appends a pending invoice row.
5. Owner receives a plain-text summary in Telegram.
6. A signed approval request can open the n8n form and update the row to Approved or Rejected.

## In Scope Now

- One Google Drive input source.
- Four core fields: vendor, invoice date, invoice number, amount.
- Confidence score and low-confidence routing.
- Composite-key duplicate detection.
- Google Sheets as the business data store.
- Telegram summary notifications.
- HMAC-protected approval workflow and n8n form.
- Separate reminder/escalation workflow definition.

## Explicitly Not in the Current Baseline

- Gmail trigger.
- Direct WhatsApp Business API ingestion.
- PDF/WEBP input in the active filter.
- Telegram inline approval buttons/deep links.
- Embedded source-file preview in the approval form.
- ERP/payment API, multi-level approval, dashboard, or production SLA.

## Risks

| Risk | Current mitigation |
|---|---|
| Poor image quality | Confidence gate and manual review row |
| Provider failure/quota | Inspect execution, retry deliberately, and preserve failed state |
| Duplicate payment | Composite-key duplicate flag plus status guard |
| Unauthorized approval | HMAC signature and timestamp validation |
| Concurrent Sheet updates | Keep volume small and migrate to transactional storage if needed |

## Status

This is a local portfolio/demo MVP. See `docs/PROJECT_STATUS.md` for the current verification snapshot and the distinction between implemented, partial, and planned capability.
