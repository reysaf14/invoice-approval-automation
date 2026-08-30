# 📄 Invoice Approval Automation

> An [n8n](https://n8n.io)-based invoice approval system that removes the manual work of extracting invoice data, logging it to a spreadsheet, and chasing approvals over WhatsApp. Invoice arrives → automatic OCR → Google Sheets → Telegram → Owner approves/rejects → Admin executes payment.

---

## Overview

| | |
|---|---|
| **Design volume** | ~120 invoices/month (~4-6/day) |
| **Workflow types** | Event-driven (Gmail/Drive triggers), Webhook (Telegram callback), Cron (15-min reminders) |
| **Data store** | Google Sheets (business master) + PostgreSQL (n8n metadata) |
| **OCR** | Google Document AI — Enterprise OCR, region `asia-southeast1` |
| **Notifications** | Telegram (Owner approval + Admin alerts + reminders/escalation) |
| **Webhook security** | HMAC-SHA256 + anti-replay timestamp + `timingSafeEqual` |
| **Testing** | 35 unit tests (pytest), 0 failures |

---

## Architecture

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
│   │  Telegram ←── Owner clicks [Approve]/[Reject] │                     │
│   │                   │                            │                     │
│   │  WORKFLOW 02 — Approval Handler  (19 nodes)   │                     │
│   │  POST /webhook/approve → HMAC verify           │                     │
│   │  → lookup Sheets → n8n Form → update status    │                     │
│   │  → notify Admin + confirm to Owner             │                     │
│   └────────────────────────────────────────────────┘                     │
│                                                                          │
│   ┌────────────────────────────────────────────────┐                     │
│   │  WORKFLOW 03 — Reminder & Escalation (12 nodes)│                     │
│   │  Cron 15m → read pending → aging check:        │                     │
│   │  1h reminder → 4h reminder → 12h reminder     │                     │
│   │  → >24h escalation to Admin                   │                     │
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

| Component | Technology | Rationale (→ [ADR](.ai/decisions/)) |
|---|---|---|
| Orchestrator | n8n 1.74.0 (self-hosted, Docker) | [ADR-001](.ai/decisions/ADR-001-orchestrator-n8n.md) — visual, 400+ integrations, Google native |
| OCR | Google Document AI | [ADR-002](.ai/decisions/ADR-002-ocr-google-doc-ai.md) — free 1K pages/mo, accurate, native GCP |
| Approval UI | n8n Form Node | [ADR-003](.ai/decisions/ADR-003-approval-ui-n8n-form.md) — zero deploy, MVP-first |
| Data Store | Google Sheets | [ADR-004](.ai/decisions/ADR-004-database-google-sheets.md) — zero infra, Admin-friendly |
| Webhook Auth | HMAC-SHA256 + timestamp | [ADR-005](.ai/decisions/ADR-005-webhook-auth-hmac.md) — integrity + anti-replay |
| Runtime | n8n queue mode (main + webhook + worker) | [ADR-006](.ai/decisions/ADR-006-webhook-blocker-dual-track.md) — impl notes |
| Infrastructure | Docker Compose, PostgreSQL, Redis | — |
| Testing | pytest (Python) | 35 unit tests: dedupe, OCR parsing, Sheets schema, HMAC auth |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2.x
- Google Cloud project (Sheets API, Drive API, Document AI)
- Telegram bot ([@BotFather](https://t.me/BotFather))
- Server/VM: min. 2 CPU, 4GB RAM, 20GB disk

### Run

```bash
# 1. Clone
git clone https://github.com/reysaf14/invoice-approval-automation.git
cd invoice-approval-automation

# 2. Configure
cp .env.template .env
# Edit .env — fill in all values (see .env.template for per-variable notes)

# 3. Prepare credentials
mkdir -p credentials
# Copy your Google Service Account key to credentials/sa-key.json

# 4. Start
docker compose up -d

# 5. Verify
curl http://localhost:5678/healthz   # n8n-webhook
curl http://localhost:5682/healthz   # n8n-main (UI)

# 6. Set up n8n
# Open http://localhost:5682 → Login
# Import workflows 01, 02, 03 from n8n-workflows/
# Set up credentials (Google OAuth, Telegram, Doc AI)
# Activate workflows via the UI toggle

# 7. Set Telegram webhook
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://<DOMAIN>/webhook/telegram"
```

> 📖 **Full guide:** [docs/SETUP.md](docs/SETUP.md) | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | [docs/OPERATIONS.md](docs/OPERATIONS.md)

---

## Repository Structure

```
invoice-approval-automation/
├── .ai/                          # Architecture & technical decisions
│   ├── knowledge/
│   │   ├── prd.md                # Product Requirements Document
│   │   ├── architecture.md       # Architecture design (data flow, stack, infra)
│   │   └── project-brief.md      # Initial project summary
│   ├── decisions/                # Architecture Decision Records
│   │   ├── ADR-001-orchestrator-n8n.md
│   │   ├── ADR-002-ocr-google-doc-ai.md
│   │   ├── ADR-003-approval-ui-n8n-form.md
│   │   ├── ADR-004-database-google-sheets.md
│   │   ├── ADR-005-webhook-auth-hmac.md
│   │   └── ADR-006-webhook-blocker-dual-track.md
│   └── implementation/
│       └── IMPLEMENTATION_PLAN.md
├── n8n-workflows/                # Workflow JSON (import directly into n8n)
│   ├── 01-invoice-ingestion.json      # 19 nodes — trigger, OCR, dedupe, notify
│   ├── 02-approval-handler.json       # 19 nodes — webhook, HMAC, form, update
│   ├── 03-reminder-escalation.json    # 12 nodes — cron, aging, reminder, escalation
│   └── test-webhook-only.json         #  2 nodes — minimal webhook test
├── src/helpers/                  # Logger helper (Python)
├── scripts/
│   ├── validate-env.sh           # Validates 27 required env vars
│   └── test-telegram-bot.sh      # Quick Telegram bot connectivity test
├── tests/                        # Unit tests (pytest)
│   ├── test_dedupe_logic.py      # 10 tests — composite key dedupe
│   ├── test_ocr_extraction.py    #  3 tests — OCR response parsing
│   ├── test_sheets_schema.py     # 12 tests — Sheets column validation
│   └── test_webhook_auth.py      #  9 tests — HMAC + timestamp + edge cases
├── docker-compose.yml            # Production stack (queue mode)
├── docker-compose.single.yml     # Dev/test stack (single mode)
├── .env.template                 # Environment variables template
└── docs/                         # Operational documentation
    ├── SETUP.md                  # Full installation
    ├── USER_GUIDE.md             # Owner & Admin guide
    └── OPERATIONS.md             # Day-to-day operations
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

### What is tested

| Module | Focus | Critical cases |
|---|---|---|
| `test_dedupe_logic.py` | Composite-key deduplication | case-insensitive, whitespace trim, duplicate detection, edge cases |
| `test_ocr_extraction.py` | OCR response parsing | field extraction, missing fields, amount formatting |
| `test_sheets_schema.py` | Google Sheets column structure | 19 valid columns, data types, status enum, referential |
| `test_webhook_auth.py` | HMAC-SHA256 webhook auth | valid signature, tamper detection, timestamp expiry/replay, timing-safe comparison, unicode handling |

---

## Known Limitations (Honest)

This section is **intentional**. A system claiming to be perfect for 120 invoices/month would deserve skepticism.

| Limitation | Why | Improvement path |
|---|---|---|
| **Google Sheets as primary data store** | No transactions, O(n) dedupe per new invoice, race conditions on concurrent updates | → PostgreSQL when volume > 500/month (see ADR-004) |
| **Approval UI uses n8n Form Node** | No PDF/image preview of the invoice on the approval page | → Custom web app (Cloud Run + signed Drive URL) |
| **Queue-mode 3-service for 120 invoices/month** | Over-provisioned — 5 containers (n8n×3, Postgres, Redis) for ~4-6 heavy executions/day | → Single mode is sufficient for MVP; queue mode helps at ≥100 files/day bursts |
| **No auto-approval** | Every invoice passes through the Owner, even for trusted vendors with small amounts | → Vendor whitelist + threshold (PRD nice-to-have #5) |
| **Limited OCR free tier** | Google Document AI: 1,000 pages/month (first 3 months) | → Gemini Flash as a fallback, or batching + file-hash cache |

---

## Debugging Saga: The Webhook 404

One of the biggest technical challenges in this project was a **webhook that never received requests** — every POST returned 404 even though the workflow was active.

### Timeline

| Stage | Finding | Status |
|---|---|---|
| QA #1–#6 | Iterated various webhook configs, tested across multiple n8n versions | ❌ Webhook still 404 |
| QA #7 | Hypotheses: DB split-brain or queue mode without a webhook processor | ❓ Unresolved |
| **DevOps Track A** | Reproduced in an isolated single-DB rig — DB split-brain disproved | ❌ H1 wrong |
| **DevOps Track B** | Polling fallback prepared as a kill-switch | ✅ Fallback ready |
| **Engineer** | Found: **`webhookId` was placed INSIDE `parameters`** — it belongs at **node level** | ✅ Root cause |
| **QA #8** | Retest: `webhook_entity` 0→3+ rows, POST → 200, execution success | ✅ PASS |

### Root cause

```json
// ❌ WRONG — webhookId inside parameters
{ "parameters": { "path": "approve", "webhookId": "..." } }

// ✅ CORRECT — webhookId at node level (sibling of parameters)
{ "parameters": { "path": "approve" }, "webhookId": "..." }
```

Consequence: n8n registered the webhook under a dynamic path `<workflowId>/webhook/<path>` → POST to the bare path → 404.

> 📖 **Full reports:** [docs/QA_REPORT_REGRESSION_7.md](docs/QA_REPORT_REGRESSION_7.md) | [docs/QA_REPORT_REGRESSION_8.md](docs/QA_REPORT_REGRESSION_8.md) | [docs/FIX_REPORT.md](docs/FIX_REPORT.md)

---

## Architecture Decision Records

| ADR | Title | Key Trade-off |
|---|---|---|
| [ADR-001](.ai/decisions/ADR-001-orchestrator-n8n.md) | Orchestrator: n8n self-hosted | Visual + native integrations vs extra infra (Postgres + Redis) |
| [ADR-002](.ai/decisions/ADR-002-ocr-google-doc-ai.md) | OCR: Google Document AI | Free 1K pages/mo, native GCP vs Gemini Flash (more flexible) |
| [ADR-003](.ai/decisions/ADR-003-approval-ui-n8n-form.md) | Approval UI: n8n Form Node | Zero deploy vs custom web app (PDF preview) |
| [ADR-004](.ai/decisions/ADR-004-database-google-sheets.md) | Database: Google Sheets only | Zero infra vs PostgreSQL (transactions, referential integrity) |
| [ADR-005](.ai/decisions/ADR-005-webhook-auth-hmac.md) | Webhook Auth: HMAC-SHA256 | Integrity + anti-replay vs IP whitelist (fragile) |
| [ADR-006](.ai/decisions/ADR-006-webhook-blocker-dual-track.md) | Webhook Blocker: dual-track | Root cause isolation + polling fallback kill-switch |

---

## Operational Cost (Estimate)

| Component | Cost/month |
|---|---|
| Google Document AI | $0 (free tier) — after free tier: ~$0.27 |
| Google Sheets + Drive | $0 (free) |
| Telegram Bot API | $0 (free) |
| Server/VPS | Provider-dependent |
| **Total software cost** | **$0 — $0.27/month** |

---

## Notes for Recruiters / Reviewers

This project was built to explore:
- **Event-driven architecture** with n8n (not just another CRUD app)
- **Documented technical trade-offs** (6 ADRs)
- **Systematic debugging** — 8 regression-testing cycles to isolate the root cause of a single misplaced JSON property
- **Webhook security** — HMAC, anti-replay, timing-safe comparison
- **Dedupe design** — composite key, case-insensitive, race-condition mitigation
- **Operational AI** — Document AI OCR, confidence scoring, fallback for low-confidence results

> Every technical decision comes with a **rationale** (not just "used X because it's popular"). See `.ai/decisions/` for full trade-off analysis.

---

## License

Built as a learning project. Feel free to reference it for study.

---

**Built with curiosity, documented with honesty.**
