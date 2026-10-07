# Arsitektur Teknis - Invoice Approval Automation

**Versi:** 2 (aligned with repository and local runtime, 2026-10-07)

## 1. Topologi Runtime

```text
Browser
  │
  └── n8n-main :5680  (UI, editor, OAuth callback, scheduler)

Inbound approval caller
  │
  └── n8n-webhook :5678 (webhook process)

n8n-main / n8n-webhook ── Redis 7 ── n8n-worker
          │
          └── PostgreSQL 16 (n8n metadata, credentials, executions)
```

Invoice business data is stored in Google Sheets. Original files remain in Google Drive. PostgreSQL is not the invoice master database.

## 2. Implemented Data Flow

```text
Google Drive folder
  → Google Drive Trigger (poll 5 min)
  → JPG/JPEG/PNG filter
  → Download File
  → Build base64 image request
  → DeepSeek vision request
  → DeepSeek JSON normalization request
  → Parse fields and confidence
       ├─ < 0.85 → append Low Confidence row to Sheets
       └─ >= 0.85 → read existing rows
                    → composite-key dedupe
                         ├─ duplicate → append Duplicate row
                         └─ new → append Pending Approval row
                                  → plain-text Telegram summary
```

The active OCR path is DeepSeek for both image OCR and normalization. The current workflow does not call the local-ai/Ollama service even though `LOCAL_AI_BASE_URL` remains in environment templates for compatibility.

## 3. Approval Flow

```text
Signed POST /webhook/approve
  → HMAC-SHA256 + timestamp verification
  → invoice lookup in Sheets
  → status must be Pending Approval
  → n8n Form: edit fields, Approve or Reject
  → reject reason validation
  → update Sheets
  → Telegram admin notification + owner confirmation
```

The owner-facing ingestion message does not currently include a Telegram inline button or deep link. A separate caller must invoke the signed endpoint to reach the form.

## 4. Reminder Flow

```text
Schedule every 15 min
  → read pending rows
  → calculate age and reminder_count
  → tier 1 / tier 2 / tier 3 owner reminder
  → >24h admin escalation
  → update reminder_count and last_reminder_at
```

This workflow is present in source but is inactive in the last local runtime verification.

## 5. Components

| Component | Responsibility |
|---|---|
| n8n 1.74.0 | Orchestration and provider integration |
| Google Drive | Input file storage and trigger source |
| DeepSeek API | Multimodal OCR and structured field normalization |
| Google Sheets | Invoice rows, statuses, confidence, and audit fields |
| Telegram Bot API | Owner/admin summary notifications |
| PostgreSQL 16 | n8n internal persistence |
| Redis 7 | n8n queue transport |
| Docker Compose | Reproducible local topology |

## 6. Security Boundaries

- Provider tokens are supplied through n8n credentials or environment variables; they are not part of workflow code.
- Approval requests require `x-signature` and `x-timestamp` headers.
- HMAC uses canonical sorted-key JSON, a timestamp tolerance, and constant-time comparison.
- Telegram receives a small invoice summary, not the original file or complete OCR text.
- Google Drive and Sheets access remains controlled by the connected Google account.

## 7. Trade-offs

### DeepSeek for both OCR and normalization

Using one multimodal provider reduces the number of provider integrations and keeps the prompt/JSON contract in one workflow. The trade-off is provider dependency, variable vision accuracy, and the need for a manual low-confidence path.

### Google Sheets as the business store

Sheets is familiar and easy for a small finance team to inspect. It does not provide transactional writes, strong concurrency control, or database-grade querying. A relational store becomes more appropriate as volume or workflow concurrency grows.

### n8n Form for approval

The form avoids deploying a separate web application. It is sufficient for an MVP decision form, but it does not provide a polished invoice preview or a native Telegram approval interaction.

### Queue mode

The main/webhook/worker split isolates inbound work from background execution and matches the intended n8n topology. For a small local workload it is more infrastructure than a single process requires.

## 8. Environment Contract

Important variables include:

```text
N8N_EDITOR_BASE_URL=http://localhost:5680
WEBHOOK_URL=http://localhost:5678
GOOGLE_SHEETS_SPREADSHEET_ID=...
GOOGLE_DRIVE_FOLDER_ID=...
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=...
TELEGRAM_OWNER_CHAT_ID=...
TELEGRAM_ADMIN_CHAT_ID=...
WEBHOOK_HMAC_SECRET=...
WEBHOOK_TIMESTAMP_TOLERANCE=300
```

`LOCAL_AI_BASE_URL` is not part of the active OCR call graph.

## 9. Future Extensions

- Connect Telegram buttons/deep links to the signed approval endpoint.
- Activate and validate reminder workflow in the target runtime.
- Add preprocessing or a specialized OCR fallback.
- Add PDF/WEBP conversion and Gmail/WhatsApp intake adapters.
- Move business data to PostgreSQL or another transactional store when needed.
- Add an approval UI with signed file preview and stronger role controls.
