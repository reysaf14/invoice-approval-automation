# Invoice Approval Automation

An n8n-based invoice processing MVP that reads invoice images from Google Drive, uses DeepSeek multimodal extraction, records normalized data in Google Sheets, and sends a concise Telegram notification for follow-up.

> Status: **Local portfolio/demo MVP**. The scope below reflects the workflow source and the local runtime verified on 7 October 2026. It does not claim production business results.

## Business Outcome Intended

The workflow removes repetitive copying of vendor, date, invoice number, and amount from image invoices. It routes uncertain OCR results to a manual-review queue, records duplicate candidates, and keeps invoice status visible in Google Sheets.

No time savings, accuracy, volume, revenue, or client results are claimed. Those metrics require measurement against real operational data.

## Current Data Flow

```text
Google Drive folder (JPG/JPEG/PNG)
        │ every 5 minutes
        ▼
Download file
        ▼
DeepSeek Vision: image → OCR text
        ▼
DeepSeek JSON normalization: vendor, date, number, amount, confidence
        │
        ├─ confidence < 0.85 → Google Sheets: Low Confidence; no owner notification
        │
        └─ confidence >= 0.85
             ├─ composite key matches an existing row → Duplicate
             └─ new invoice → Pending Approval → plain-text Telegram summary
```

The approval workflow exposes `POST /webhook/approve`, validates HMAC-SHA256 signatures and timestamps, checks the current invoice status, opens an n8n form, updates Google Sheets, and sends result notifications. The reminder workflow is present in source but was inactive in the last local runtime verification.

## Capability Status

| Capability | Status | Evidence / boundary |
|---|---|---|
| Google Drive folder trigger | Implemented | Five-minute polling; JPG/JPEG/PNG filter |
| OCR and field normalization | Implemented | DeepSeek vision request followed by DeepSeek JSON request |
| Confidence threshold | Implemented | `0.85`; lower results become `Low Confidence` rows |
| Deduplication | Implemented | Vendor + invoice number + date + amount after trim/lowercase normalization |
| Google Sheets recording | Implemented | Invoice and audit fields are written to the configured sheet |
| New-invoice Telegram notification | Implemented | Plain text; no emoji, Markdown, or placeholder file link |
| Approval endpoint and HMAC | Implemented in workflow | Requires a signed caller with timestamp headers |
| Telegram approve/reject buttons | Not connected | The current invoice message is notification-only |
| n8n approval form | Implemented in workflow | Reached after a valid approval request |
| Reminder/escalation | Implemented in source | Inactive in the last local runtime; activate deliberately |
| Gmail, WhatsApp API, PDF, WEBP input | Not in active path | Files must reach Drive as JPG/JPEG/PNG first |

## Architecture

- **Orchestrator:** self-hosted n8n 1.74.0 in Docker Compose queue mode.
- **Main/UI:** `http://localhost:5680`.
- **Webhook edge:** `http://localhost:5678`.
- **Worker:** separate n8n queue worker.
- **n8n metadata:** PostgreSQL 16.
- **Queue:** Redis 7.
- **AI:** DeepSeek chat-completions-compatible API. The active workflow sends an image as a base64 `image_url`, then sends OCR text to a second JSON-normalization request.
- **Business store:** Google Sheets.
- **File store:** Google Drive.
- **Notifications:** Telegram Bot API through n8n credentials.
- **Approval security:** HMAC-SHA256, timestamp freshness, and constant-time comparison.

## Repository Layout

```text
invoice-approval-automation/
├── n8n-workflows/              # importable n8n workflow JSON
├── .ai/                        # PRD, architecture, ADRs, implementation status
├── docs/                       # setup, user, operations, current status
├── tests/                      # pytest regression suite
├── docker-compose.yml          # queue-mode stack
├── docker-compose.single.yml   # single-mode test stack
└── .env.template
```

## Local Setup

1. Copy `.env.template` to `.env` and fill secrets locally.
2. Create/connect Google Drive, Google Sheets, and Telegram credentials in n8n.
3. Set `DEEPSEEK_API_URL`, `DEEPSEEK_API_KEY`, and `DEEPSEEK_MODEL`. The active path does not call local-ai/Ollama.
4. Run `docker compose up -d`.
5. Open `http://localhost:5680`, import the workflows, bind credentials, and activate only the workflows you intend to run.
6. Upload a JPG/JPEG/PNG invoice to the configured Drive folder.
7. Inspect Sheets, n8n executions, and the owner Telegram chat.

See [docs/SETUP.md](docs/SETUP.md), [docs/USER_GUIDE.md](docs/USER_GUIDE.md), [docs/OPERATIONS.md](docs/OPERATIONS.md), and [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Tests

```powershell
pytest -q
```

The latest local regression run passed **42 tests** covering deduplication, OCR parsing, Sheets schema, HMAC verification, workflow contracts, and notification formatting. This does not replace provider-level acceptance testing with the target Google, DeepSeek, and Telegram accounts.

## Known Limitations

- Google Sheets is not a transactional database; concurrent writes and row growth need monitoring.
- DeepSeek is a provider dependency for both vision OCR and normalization; quota, latency, and output behavior can change.
- Blurry or cropped images can produce low confidence or missing fields.
- The active path does not directly ingest Gmail or WhatsApp, and it does not accept PDF/WEBP without an upstream conversion step.
- The new-invoice message intentionally has no file link or approval buttons. The signed approval endpoint and form exist, but the Telegram button/deep-link integration is not connected.
- The reminder workflow is present but must be activated and tested in the target runtime.
- PostgreSQL and Redis support n8n internals; invoice business data remains in Google Sheets.

## Security Notes

- Never commit `.env`, Google credentials, or Telegram tokens.
- Keep provider secrets in the n8n Credential Store.
- Use a strong HMAC secret and a bounded timestamp tolerance for approval requests.
- Telegram receives a summary only; the source file remains in Google Drive.

See `.ai/decisions/` for the rationale behind the main trade-offs.

## License

Learning/portfolio project; not a claim of production deployment.
