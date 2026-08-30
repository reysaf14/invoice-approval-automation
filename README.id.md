# 📄 Invoice Approval Automation

> Sistem otomasi approval invoice berbasis [n8n](https://n8n.io) yang menghilangkan proses manual ekstrak data, catat ke spreadsheet, dan *chasing* approval via WhatsApp. Invoice masuk → OCR otomatis → Google Sheets → Telegram → Owner approve/reject → Admin eksekusi pembayaran.

---

## Ringkasan

| | |
|---|---|
| **Volume desain** | ~120 invoice/bulan (~4-6/hari) |
| **Tipe workflow** | Event-driven (Gmail/Drive trigger), Webhook (Telegram callback), Cron (reminder 15 menit) |
| **Data store** | Google Sheets (master bisnis) + PostgreSQL (metadata n8n) |
| **OCR** | Google Document AI — Enterprise OCR, region `asia-southeast1` |
| **Notifikasi** | Telegram (Owner approve + Admin notif + reminder/escalation) |
| **Keamanan webhook** | HMAC-SHA256 + timestamp anti-replay + `timingSafeEqual` |
| **Testing** | 35 unit test (pytest), 0 failures |

---

## Arsitektur

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        INPUT SOURCES                                     │
│   ┌──────────┐        ┌───────────────────┐                             │
│   │  Gmail   │        │   Google Drive     │                             │
│   │ (poll 2m)│        │   (poll 5m)        │                             │
│   └────┬─────┘        └────────┬──────────┘                             │
│        │                       │                                         │
│        └───────────┬───────────┘                                         │
│                    ▼                                                     │
│   ┌────────────────────────────────────────────────┐                     │
│   │  WORKFLOW 01 — Invoice Ingestion               │                     │
│   │  19 nodes: download → Doc AI OCR → parse        │                     │
│   │  → confidence check → dedupe → write Sheets     │                     │
│   │  → notify Owner via Telegram                   │                     │
│   └───────────────────┬────────────────────────────┘                     │
│                       │                                                  │
│   ┌───────────────────┼────────────────────────────┐                     │
│   │                   ▼                            │                     │
│   │  Telegram ←── Owner klik [Approve]/[Reject]   │                     │
│   │                   │                            │                     │
│   │  WORKFLOW 02 — Approval Handler  (19 nodes)   │                     │
│   │  POST /webhook/approve → HMAC verify           │                     │
│   │  → lookup Sheets → n8n Form → update status    │                     │
│   │  → notify Admin + konfirmasi Owner             │                     │
│   └────────────────────────────────────────────────┘                     │
│                                                                          │
│   ┌────────────────────────────────────────────────┐                     │
│   │  WORKFLOW 03 — Reminder & Escalation (12 nodes)│                     │
│   │  Cron 15m → baca pending → aging check:        │                     │
│   │  1h reminder → 4h reminder → 12h reminder     │                     │
│   │  → >24h escalation ke Admin                   │                     │
│   └────────────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────────────┘

Stack (Docker Compose):
┌──────────────────────────────────────────────────┐
│  n8n-main (UI :5682)  n8n-webhook (:5678)  n8n-worker │
│  PostgreSQL 16        Redis 7                        │
└──────────────────────────────────────────────────┘
```

---

## Tech Stack

| Komponen | Teknologi | Alasan (→ [ADR](.ai/decisions/)) |
|---|---|---|
| Orkestrator | n8n 1.74.0 (self-hosted, Docker) | [ADR-001](.ai/decisions/ADR-001-orchestrator-n8n.md) — visual, 400+ integrasi, Google native |
| OCR | Google Document AI | [ADR-002](.ai/decisions/ADR-002-ocr-google-doc-ai.md) — free 1K pages/bulan, akurat, native GCP |
| Approval UI | n8n Form Node | [ADR-003](.ai/decisions/ADR-003-approval-ui-n8n-form.md) — zero deploy, MVP-first |
| Data Store | Google Sheets | [ADR-004](.ai/decisions/ADR-004-database-google-sheets.md) — zero infra, Admin familiar |
| Webhook Auth | HMAC-SHA256 + timestamp | [ADR-005](.ai/decisions/ADR-005-webhook-auth-hmac.md) — integrity + anti-replay |
| Runtime | n8n queue mode (main + webhook + worker) | [ADR-006](.ai/decisions/ADR-006-webhook-blocker-dual-track.md) — impl notes |
| Infrastructure | Docker Compose, PostgreSQL, Redis | — |
| Testing | pytest (Python) | 35 unit test: dedupe, OCR parsing, Sheets schema, HMAC auth |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2.x
- Google Cloud project (Sheets API, Drive API, Document AI)
- Telegram bot ([@BotFather](https://t.me/BotFather))
- Server/VM: min. 2 CPU, 4GB RAM, 20GB disk

### Jalankan

```bash
# 1. Clone
git clone https://github.com/reysaf14/invoice-approval-automation.git
cd invoice-approval-automation

# 2. Konfigurasi
cp .env.template .env
# Edit .env — isi semua nilai (lihat .env.template untuk penjelasan tiap variabel)

# 3. Siapkan credentials
mkdir -p credentials
# Copy Google Service Account key ke credentials/sa-key.json

# 4. Start
docker compose up -d

# 5. Verifikasi
curl http://localhost:5678/healthz   # n8n-webhook
curl http://localhost:5682/healthz   # n8n-main (UI)

# 6. Setup n8n
# Buka http://localhost:5682 → Login
# Import workflow 01, 02, 03 dari n8n-workflows/
# Setup credentials (Google OAuth, Telegram, Doc AI)
# Aktifkan workflow via toggle UI

# 7. Set Telegram webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://<DOMAIN>/webhook/telegram"
```

> 📖 **Panduan lengkap:** [docs/SETUP.md](docs/SETUP.md) | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | [docs/OPERATIONS.md](docs/OPERATIONS.md)

---

## Struktur Repo

```
invoice-approval-automation/
├── .ai/                          # Arsitektur & keputusan teknis
│   ├── knowledge/
│   │   ├── prd.md                # Product Requirements Document
│   │   ├── architecture.md       # Desain arsitektur (data flow, stack, infra)
│   │   └── project-brief.md      # Ringkasan awal project
│   ├── decisions/                # Architecture Decision Records
│   │   ├── ADR-001-orchestrator-n8n.md
│   │   ├── ADR-002-ocr-google-doc-ai.md
│   │   ├── ADR-003-approval-ui-n8n-form.md
│   │   ├── ADR-004-database-google-sheets.md
│   │   ├── ADR-005-webhook-auth-hmac.md
│   │   └── ADR-006-webhook-blocker-dual-track.md
│   └── implementation/
│       └── IMPLEMENTATION_PLAN.md
├── n8n-workflows/                # Workflow JSON (import langsung ke n8n)
│   ├── 01-invoice-ingestion.json      # 19 nodes — trigger, OCR, dedupe, notify
│   ├── 02-approval-handler.json       # 19 nodes — webhook, HMAC, form, update
│   ├── 03-reminder-escalation.json    # 12 nodes — cron, aging, reminder, escalation
│   └── test-webhook-only.json         #  2 nodes — minimal webhook test
├── src/helpers/                  # Logger helper (Python)
├── scripts/
│   ├── validate-env.sh           # Validasi 27 env vars wajib
│   └── test-telegram-bot.sh      # Quick test koneksi Telegram bot
├── tests/                        # Unit tests (pytest)
│   ├── test_dedupe_logic.py      # 10 test — composite key dedupe
│   ├── test_ocr_extraction.py    #  3 test — OCR response parsing
│   ├── test_sheets_schema.py     # 12 test — Sheets column validation
│   └── test_webhook_auth.py      #  9 test — HMAC + timestamp + edge cases
├── docker-compose.yml            # Stack production (queue mode)
├── docker-compose.single.yml     # Stack dev/test (single mode)
├── .env.template                 # Template environment variables
└── docs/                         # Dokumentasi operasional
    ├── SETUP.md                  # Instalasi lengkap
    ├── USER_GUIDE.md             # Panduan Owner & Admin
    └── OPERATIONS.md             # Operasional harian
```

---

## Testing

```bash
python -m pytest tests/ -v
```

```
tests/test_dedupe_logic.py     10 passed
tests/test_ocr_extraction.py    3 passed
tests/test_sheets_schema.py    12 passed
tests/test_webhook_auth.py      9 passed
────────────────────────────────────────
35 passed in 0.10s
```

### Apa yang ditest

| Modul | Fokus | Kasus kritis |
|---|---|---|
| `test_dedupe_logic.py` | Composite key deduplication | case-insensitive, whitespace trim, duplicate detection, edge cases |
| `test_ocr_extraction.py` | OCR response parsing | field extraction, missing fields, amount formatting |
| `test_sheets_schema.py` | Google Sheets column structure | 19 kolom valid, tipe data, status enum, referensial |
| `test_webhook_auth.py` | HMAC-SHA256 webhook auth | valid signature, tamper detection, timestamp expiry/replay, timing-safe comparison, unicode handling |

---

## Keterbatasan (Jujur)

Bagian ini **disengaja**. Sebuah sistem yang mengklaim sempurna untuk volume 120/bulan layak dipertanyakan.

| Keterbatasan | Mengapa | Rencana peningkatan |
|---|---|---|
| **Google Sheets sebagai data store utama** | Tidak ada transaksi, dedupe O(n) per invoice baru, race condition pada concurrent update | → PostgreSQL saat volume >500/bulan (lihat ADR-004) |
| **Approval UI pakai n8n Form Node** | Tidak ada preview PDF/gambar invoice di halaman approval | → Custom web app (Cloud Run + signed Drive URL) |
| **Queue mode 3-service untuk volume 120/bulan** | Over-provisioned — 5 container (n8n×3, Postgres, Redis) untuk ~4-6 eksekusi berat/hari | → Single mode cukup untuk MVP; queue mode berguna saat burst ≥100 file/hari |
| **Tidak ada auto-approve** | Semua invoice melewati Owner meskipun vendor tepercaya + nominal kecil | → Whitelist vendor + threshold (PRD nice-to-have #5) |
| **OCR free tier terbatas** | Google Document AI: 1.000 pages/bulan (3 bulan pertama) | → Gemini Flash sebagai fallback, atau batching + cache hash |

---

## Debugging Saga: Webhook 404

Salah satu tantangan teknis terbesar di project ini adalah **webhook tidak pernah menerima request** — semua POST mengembalikan 404 meskipun workflow aktif.

### Kronologi

| Tahap | Temuan | Status |
|---|---|---|
| QA #1–#6 | Iterasi berbagai konfigurasi webhook, testing di beberapa versi n8n | ❌ Webhook tetap 404 |
| QA #7 | Hipotesis: DB split-brain atau queue mode tanpa webhook processor | ❓ Belum terjawab |
| **DevOps Track A** | Reproduksi di rig isolasi satu-DB — diskonfirmasi DB split-brain | ❌ H1 salah |
| **DevOps Track B** | Polling fallback disiapkan sebagai kill-switch | ✅ Fallback ready |
| **Engineer** | Ditemukan: **`webhookId` diletakkan di DALAM `parameters`**, seharusnya di **level node** | ✅ Root cause |
| **QA #8** | Retest: `webhook_entity` 0→3+ rows, POST → 200, execution success | ✅ PASS |

### Akar masalah

```json
// ❌ SALAH — webhookId di dalam parameters
{ "parameters": { "path": "approve", "webhookId": "..." } }

// ✅ BENAR — webhookId di level node (sibling parameters)
{ "parameters": { "path": "approve" }, "webhookId": "..." }
```

Konsekuensi: n8n mendaftarkan webhook dengan path dinamik `<workflowId>/webhook/<path>` → POST ke path polos → 404.

> 📖 **Laporan lengkap:** [docs/QA_REPORT_REGRESSION_7.md](docs/QA_REPORT_REGRESSION_7.md) | [docs/QA_REPORT_REGRESSION_8.md](docs/QA_REPORT_REGRESSION_8.md) | [docs/FIX_REPORT.md](docs/FIX_REPORT.md)

---

## Arsitektur Decision Records

| ADR | Judul | Key Trade-off |
|---|---|---|
| [ADR-001](.ai/decisions/ADR-001-orchestrator-n8n.md) | Orchestrator: n8n self-hosted | Visual + integrasi native vs infra tambahan (Postgres + Redis) |
| [ADR-002](.ai/decisions/ADR-002-ocr-google-doc-ai.md) | OCR: Google Document AI | Free 1K pages/bulan, native GCP vs Gemini Flash (lebih fleksibel) |
| [ADR-003](.ai/decisions/ADR-003-approval-ui-n8n-form.md) | Approval UI: n8n Form Node | Zero deploy vs custom web app (preview PDF) |
| [ADR-004](.ai/decisions/ADR-004-database-google-sheets.md) | Database: Google Sheets only | Zero infra vs PostgreSQL (transactions, referential integrity) |
| [ADR-005](.ai/decisions/ADR-005-webhook-auth-hmac.md) | Webhook Auth: HMAC-SHA256 | Integrity + anti-replay vs IP whitelist (fragile) |
| [ADR-006](.ai/decisions/ADR-006-webhook-blocker-dual-track.md) | Webhook Blocker: dual-track | Root cause isolation + polling fallback kill-switch |

---

## Biaya Operasional (Estimasi)

| Komponen | Biaya/bulan |
|---|---|
| Google Document AI | $0 (free tier) — setelah free tier: ~$0.27 |
| Google Sheets + Drive | $0 (free) |
| Telegram Bot API | $0 (free) |
| Server/VPS | Sesuai provider |
| **Total software** | **$0 — $0.27/bulan** |

---

## Catatan untuk Perekrut/Reviewer

Project ini dibangun untuk mempelajari:
- **Arsitektur event-driven** dengan n8n (bukan sekadar CRUD)
- **Trade-off teknis** yang didokumentasi (6 ADR)
- **Debugging sistematis** — 8 siklus regression testing untuk menemukan root cause satu properti JSON yang salah posisi
- **Keamanan webhook** — HMAC, anti-replay, timing-safe comparison
- **Dedupe design** — composite key, case-insensitive, race condition mitigation
- **Operasional AI** — Document AI OCR, confidence scoring, fallback untuk low confidence

> Seluruh keputusan teknis dilengkapi **alasan** (bukan cuma "pakai X karena populer"). Lihat `.ai/decisions/` untuk analisis trade-off lengkap.

---

## Lisensi

Dibangun sebagai learning project. Gunakan untuk referensi belajar.

---

**Built with curiosity, documented with honesty.**
