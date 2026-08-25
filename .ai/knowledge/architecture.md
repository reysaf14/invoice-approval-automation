# ARSITEKTUR TEKNIS - Invoice Approval Automation

## 1. Pendekatan Utama
- [x] n8n Orchestration (Self-hosted via Docker)
- [ ] Custom Script (Python/Node)
- [ ] Desktop App
- [ ] Kombinasi

**Alasan:** Flow linear dengan banyak integrasi SaaS (Gmail, Drive, Sheets, Telegram), volume rendah (~120/bln), butuh human-in-the-loop approval. n8n native integrations mengurangi custom code >80%, visual debugging, queue mode untuk reliability.

## 2. Aliran Data (Data Flow)

```
Sumber: 
  ├─ Gmail (attachment PDF/JPG/PNG) → Gmail Trigger (poll 2 menit)
  └─ Google Drive (folder "Invoices_Incoming") → Drive Trigger (poll 5 menit)

Proses:
  1. Download file → Generate UUID → Determine MIME
  2. Google Document AI (Enterprise OCR) → Extract 4 fields + confidence
  3. Validate confidence ≥ 0.85 → Flag "Low Confidence" jika gagal
  4. Dedupe: Composite key (vendor + invoice_number + date + amount) vs Sheets
  5. Write to Google Sheets (status: "Pending Approval")
  6. Telegram Bot → Owner: formatted message + inline buttons (Approve/Reject)
  7. Owner clicks → n8n Webhook (HMAC verified) → n8n Form Node
  8. Form submit → Validate → Update Sheets (Approved/Rejected + audit fields)
  9. Notify Admin (Telegram/Email) → "Ready for payment"
  10. Scheduled workflow (cron 15min) → Reminders (1h, 4h, 12h) → Escalation (>24h)

Tujuan:
  ├─ Google Sheets (Master data + audit trail)
  ├─ Telegram (Owner approval + Admin notifications + Reminders)
  └─ Google Drive (File storage + preview links)
```

## 3. Struktur Folder

```
invoice-approval-automation/
├── .ai/
│   ├── knowledge/
│   │   ├── project-brief.md
│   │   ├── prd.md
│   │   └── architecture.md
│   └── decisions/
│       ├── ADR-001-orchestrator-n8n.md
│       ├── ADR-002-ocr-google-doc-ai.md
│       ├── ADR-003-approval-ui-n8n-form.md
│       ├── ADR-004-database-google-sheets.md
│       └── ADR-005-webhook-auth-hmac.md
├── docker-compose.yml
├── .env.template
├── n8n-workflows/
│   ├── 01-invoice-ingestion.json
│   ├── 02-approval-handler.json
│   └── 03-reminder-escalation.json
├── src/
│   └── (reserved for future custom services)
├── tests/
│   ├── test_ocr_extraction.py
│   ├── test_dedupe_logic.py
│   ├── test_sheets_schema.py
│   └── test_webhook_auth.py
└── docs/
    ├── SETUP.md
    ├── OPERATIONS.md
    └── USER_GUIDE.md
```

## 4. Dependency & Environment Variables

```bash
# n8n Core
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=***
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/webhook
GENERIC_TIMEZONE=Asia/Jakarta
N8N_MODE=queue
EXECUTIONS_MODE=queue

# Database (PostgreSQL for n8n)
DB_TYPE=postgresdb
DB_POSTGRESDB=n8n
DB_POSTGRESHOST=postgres
DB_POSTGRESPORT=5432
DB_POSTGRESUSER=n8n
DB_POSTGRES_PASSWORD=***

# Redis (Queue)
REDIS_HOST=redis
REDIS_PORT=6379

# Google OAuth (Service Account recommended)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=***
GOOGLE_REDIRECT_URI=http://localhost:5678/oauth2/callback
GOOGLE_SHEETS_SPREADSHEET_ID=1AbC...
GOOGLE_DRIVE_FOLDER_ID=1XyZ...

# Google Document AI
GOOGLE_DOC_AI_PROJECT_ID=your-gcp-project
GOOGLE_DOC_AI_LOCATION=asia-southeast1
GOOGLE_DOC_AI_PROCESSOR_ID=your-ocr-processor-id
GOOGLE_APPLICATION_CREDENTIALS=/home/node/.gcp/sa-key.json

# Telegram
TELEGRAM_BOT_TOKEN=***
TELEGRAM_OWNER_CHAT_ID=123456789
TELEGRAM_ADMIN_CHAT_ID=987654321

# Webhook Security
WEBHOOK_HMAC_SECRET=***  # 32-byte hex, generate: openssl rand -hex 32
WEBHOOK_TIMESTAMP_TOLERANCE=300  # seconds
```

## 5. Database

- [ ] SQLite
- [ ] PostgreSQL
- [x] Tidak pakai database terpisah (Google Sheets sebagai data store utama)

**Catatan:** n8n internal menggunakan PostgreSQL (workflow, credentials, execution history). Data bisnis invoice 100% di Google Sheets.

## 6. Catatan Keamanan & Robustness (Desain Level)

- **Webhook Authentication**: Semua endpoint webhook (Telegram callback, Doc AI callback) WAJIB verifikasi HMAC-SHA256 signature + timestamp (ADR-005). Engineer implementasikan di Function node sebelum processing.
- **Idempotency**: Dedupe by `invoice_id` (UUID) + composite key (vendor + invoice_number + date + amount) sebelum write Sheets. Approval handler check current status sebelum update (hindari double-approve).
- **Secrets Management**: Semua secret di `.env` → Docker secrets / n8n Credentials (encrypted di PostgreSQL). JANGAN hardcode di workflow JSON.
- **File Access Control**: Drive files: `anyone with link can view` HANYA untuk preview approval. Folder `Invoices_Incoming` restricted ke Admin/Owner service account.
- **Rate Limiting**: n8n queue mode + Redis. Gmail/Drive API quota monitored (120 req/bln << quota). Doc AI: 1K pages/bln free tier.
- **Audit Trail**: Setiap status change write `updated_at`, `approved_by`, `reject_reason`. Sheets version history sebagai backup audit.
- **PII in Telegram**: Pesan hanya ringkasan (vendor, nominal, no invoice). Data lengkap di Sheets (access controlled). Callback data hanya `invoice_id|action`.
- **Command Injection Prevention**: Jika n8n Execute Command node dipakai (tidak direncanakan), Engineer WAJIB avoid string interpolation dari data eksternal ke shell command.
- **[QA-7] Webhook Registration Blocker**: Production webhook 404 terdeteksi QA pada n8n v1.60.0 & v1.74.0 (`webhook_entity` kosong meski workflow aktif; CLI/REST/UI toggle semuanya gagal persist registrasi). WAJIB ikuti dual-track plan di ADR-006: Track A root-cause isolation (timebox 48 jam) + Track B polling-based fallback yang bekerja TANPA inbound webhook sama sekali.

## 7. Catatan Khusus

- **n8n Queue Mode**: Wajib untuk production (main + worker). `EXECUTIONS_MODE=queue` + Redis.
- **Google Doc AI Processor**: Buat di region `asia-southeast1` (Jakarta) untuk latency. Processor type: "Enterprise Document OCR".
- **Telegram Bot**: Set webhook ke `WEBHOOK_URL/telegram` via `setWebhook` API. Inline keyboard buttons dengan `callback_data: "approve|uuid"` / `reject|uuid"`.
- **Reminder Cron**: Workflow terpisah `03-reminder-escalation` jalan tiap 15 menit. Baca Sheets filter `status="Pending Approval" AND reminder_count < 3 AND created_at < now() - interval`.
- **Approval Form URL**: n8n Form node generate URL unik per execution. Validasi `invoice_id` di form hidden field.
- **Error Handling**: Setiap workflow punya Error Trigger → Telegram ke Admin + log ke Sheets tab `Errors`.
- **[QA-7] Track A (Root Cause Isolation)**: Urutan verifikasi wajib: (1) pastikan instance memakai SATU database saja (hindari DB split-brain antara compose single-mode vs queue-mode), (2) jika tetap queue mode — jalankan service `n8n webhook` terpisah sesuai arsitektur queue n8n, ATAU turun ke regular mode (volume 120/bln tidak butuh queue), (3) test bare-metal `npx n8n` tanpa Docker untuk isolasi faktor environment, (4) audit konsistensi `WEBHOOK_URL` / `N8N_HOST` / `N8N_PROTOCOL`.
- **[QA-7] Track B (Fallback Polling)**: Jalur approval TANPA webhook: Telegram Trigger mode polling (getUpdates) + Google Apps Script Web App menulis aksi ke tab `Approval_Actions` + Schedule Trigger n8n memproses tiap 1 menit. Detail lengkap di ADR-006. Implementasi: Engineer; verifikasi: QA REGRESSION #8.
- **Backup**: PostgreSQL dump harian (cron di host). Sheets: manual export mingguan / Google Drive backup.

## 8. Riwayat Perubahan

| Versi | Tanggal | Perubahan | ADR Terkait |
|-------|---------|-----------|-------------|
| v1 | 2026-08-12 | Desain awal | ADR-001, ADR-002, ADR-003, ADR-004, ADR-005 |
| v2 | 2026-08-25 | Respons QA REGRESSION #7: catat webhook blocker + dual-track plan (root-cause isolation & polling fallback) | ADR-006 |