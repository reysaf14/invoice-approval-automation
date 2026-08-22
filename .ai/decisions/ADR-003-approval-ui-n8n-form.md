# ADR-003: Approval UI - n8n Form Node (MVP)

## Status
Accepted

## Context
Owner needs to approve/reject invoices via Telegram notification. The approval action should show invoice preview, allow editing extracted fields, require reject reason, and update Google Sheets.

## Decision
Use **n8n Form Node** for the approval web page (MVP).

## Alternatives Considered
1. **Custom Web App (FastAPI/Flask + HTMX)** - Full UI control, preview PDF, but separate service to deploy/maintain
2. **Google Apps Script Web App** - Native Sheets access, free, but limited UI, CORS issues, slow
3. **Cloud Run + Static HTML** - Scalable, but additional GCP service, more setup

## Consequences
- **Positive**: Zero additional deployment, native n8n webhook integration, form data directly available in workflow, sufficient for Approve/Reject + reason + field editing
- **Negative**: Limited UI customization (no PDF preview iframe, basic styling), no file upload, form URL contains workflow ID (not pretty)
- **Risk**: n8n Form node may not support all desired UX → upgrade path to custom webapp documented for Phase 2

## Implementation Notes
- Form fields: Vendor (editable), Date (editable), Invoice Number (editable), Amount (editable), Action (radio: Approve/Reject), Reject Reason (textarea, required if Reject), Hidden: invoice_id, row_index
- Webhook URL: `/webhook/approve/:invoice_id` (or use query param)
- On submit: Validate → Update Sheets → Notify Admin → Respond with success page
- Future: If PDF preview critical → ADR for custom webapp (Cloud Run + signed Drive URL)