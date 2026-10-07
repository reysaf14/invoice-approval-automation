# PRD: Invoice Approval Automation

**Status:** Implemented MVP baseline with explicit follow-up backlog
**Reviewed:** 2026-10-07

## 1. Problem

Small finance teams often receive invoice images and manually copy vendor, date, invoice number, and amount into a spreadsheet before asking an owner to review them. The manual path is repetitive and makes duplicate detection, low-quality documents, and pending approvals difficult to manage.

This repository implements a local automation baseline for that workflow. It does not prove a specific customer's volume, savings, accuracy, or payment-delay reduction.

## 2. Users

- **Finance admin:** places source files in Drive, monitors the invoice sheet, handles low-confidence and duplicate cases, and executes approved payments under the organization's own SOP.
- **Owner/approver:** receives a Telegram summary and makes an approval decision through the signed approval flow when a caller/integration invokes it.
- **Technical operator:** maintains n8n, credentials, provider configuration, queues, and execution history.

## 3. Current Scope

### Implemented

1. Google Drive folder trigger with five-minute polling.
2. JPG/JPEG/PNG file filter.
3. DeepSeek vision OCR and second-pass JSON normalization.
4. Vendor, invoice date, invoice number, amount, and confidence extraction.
5. Confidence routing at `0.85`.
6. Google Sheets write path for normal, duplicate, and low-confidence rows.
7. Composite-key deduplication using vendor, invoice number, date, and amount.
8. Plain-text Telegram owner notification for a new accepted invoice.
9. HMAC-protected approval webhook, status guard, n8n form, Sheets update, and result notifications.
10. Separate reminder/escalation workflow definition.

### Partial or Runtime-Dependent

- The approval workflow is available, but the new-invoice Telegram message does not yet carry an approval button/deep link.
- Reminder/escalation is implemented in source but may be inactive in a given runtime.
- Google, DeepSeek, and Telegram integrations require valid credentials and external service availability.

### Out of Scope / Backlog

- Gmail or WhatsApp Business API ingestion.
- Direct PDF/WEBP ingestion in the active file filter.
- Embedded invoice preview in the form.
- Payment execution in an ERP/accounting platform.
- Multi-level approval, vendor whitelist, dashboard, and advanced reporting.
- Production SLO, accuracy, or cost commitments.

## 4. Functional Requirements and Acceptance

| Requirement | Current acceptance condition | Status |
|---|---|---|
| Drive intake | New JPG/JPEG/PNG in configured folder reaches workflow | Implemented |
| AI extraction | DeepSeek returns OCR text and normalized JSON | Implemented, provider-dependent |
| Confidence routing | `< 0.85` becomes `Low Confidence`; `>= 0.85` continues | Implemented |
| Duplicate detection | Matching normalized composite key is written as `Duplicate` | Implemented |
| Invoice storage | New accepted invoice is appended to configured Sheet | Implemented |
| Owner notification | Plain-text summary is sent through Telegram credential | Implemented |
| Approval | Signed `POST /webhook/approve` can open form and update status | Implemented in workflow |
| Reminder | 1h/4h/12h tiers and >24h escalation exist in source | Runtime activation required |
| Auditability | Status/actor/time/reason fields are carried in the Sheet row | Partial; Sheets history is the supporting audit layer |

## 5. Data Contract

The business row fields are:

```text
invoice_id, received_at, vendor, invoice_date, invoice_number, amount,
status, confidence, drive_file_id, drive_file_link, source, approved_at,
approved_by, rejected_at, reject_reason, reminder_count, last_reminder_at,
created_at, updated_at
```

Allowed operational statuses include `Pending Approval`, `Approved`, `Rejected`, `Duplicate`, `Low Confidence`, and `Failed`.

## 6. Non-Functional Considerations

- Keep provider secrets in n8n credentials or local environment configuration.
- Protect approval requests with HMAC-SHA256 and timestamp freshness checks.
- Avoid sending the full invoice file or OCR body through Telegram.
- Treat Google Sheets as a low-volume MVP data store, not a transactional ledger.
- Keep source workflow JSON importable and testable without committing runtime secrets.

## 7. Validation Evidence

- Local Python/workflow regression suite: `42 passed` on 2026-10-07.
- Local n8n health endpoint returned `ok`.
- Last runtime status: ingestion and approval active; reminder inactive.

These are local validation facts, not production acceptance or business outcome metrics.

## 8. Revision History

| Version | Date | Change |
|---|---|---|
| v1 | 2026-08-12 | Initial business requirements draft |
| v2 | 2026-10-07 | Aligned requirements with implemented Drive → DeepSeek → Sheets → Telegram path; separated partial and planned capabilities |
