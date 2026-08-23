# IMPLEMENTATION PLAN — Invoice Approval Automation

**Role**: Engineer Agent  
**Date**: 2026-08-23  
**Mode**: Bangun Baru (Build Mode)  
**Base Documents**: architecture.md (v1), 5 ADRs, PRD v1, n8n-technical-boilerplate.md

---

## Current State

| Komponen | Status |
|----------|--------|
| docker-compose.yml, .env.template, .gitignore | Done |
| n8n-workflows/01-invoice-ingestion.json | STUB KOSONG (nodes:[]) |
| n8n-workflows/02-approval-handler.json | STUB KOSONG (nodes:[]) |
| n8n-workflows/03-reminder-escalation.json | STUB KOSONG (nodes:[]) |
| tests/ (4 file) | Done |
| docs/ (3 file) | Done |
| src/ helpers | BELUM ADA |

---

## Milestone 1 — Foundation & Helper Scripts

### File yang dibuat:
1. `.n8nignore` — Exclude docs/tests dari n8n
2. `src/helpers/logger.py` — Standard logging helper (reuse python-script-boilerplate)
3. `scripts/validate-env.sh` — Validate .env terisi lengkap
4. Pin n8n version di docker-compose.yml (ganti `latest` → `1.60.0`)

### File yang diubah:
- `docker-compose.yml` — Pin version, tambah volume mount untuk n8n-workflows/

---

## Milestone 2 — Workflow 01: Invoice Ingestion

### Node Structure (14 nodes):

```
Gmail Trigger (poll 2m)
    ↓
Google Drive Trigger (poll 5m)  
    ↓
Merge (combine 2 sumber)
    ↓
Download File
    ↓
Google Document AI (OCR)
    ↓
Code: Parse OCR Response (extract 4 fields + confidence)
    ↓
IF: Confidence >= 0.85?
  ├── YES → Google Sheets: Read Existing (for dedupe)
  │         ↓
  │     Code: Check Dedupe (composite key)
  │         ↓
  │     IF: Is Duplicate?
  │       ├── YES → Code: Build Duplicate Row → Google Sheets: Append
  │       └── NO → Code: Build New Row → Google Sheets: Append
  │                    ↓
  │                Telegram: Notify Owner
  └── NO → Code: Build Low Confidence Row → Google Sheets: Append

Error Trigger → Telegram: Notify Admin (error)
```

### Key Function Code:
- `parseDocAiResponse()` — Extract vendor, date, number, amount + confidence
- `checkDedupe()` — Composite key (vendor + number + date + amount), case-insensitive
- `buildInvoiceRow()` — Build complete row with all 19 columns

---

## Milestone 3 — Workflow 02: Approval Handler

### Node Structure (11 nodes):

```
Webhook: POST /webhook/approve
    ↓
Code: HMAC Verification (ADR-005)
    ↓
IF: Valid Signature?
  ├── YES → Google Sheets: Find Invoice (by invoice_id)
  │         ↓
  │     IF: Status == "Pending Approval"?
  │       ├── YES → n8n Form Node (editable fields + approve/reject)
  │       │         ↓
  │       │     Code: Process Decision (build update payload)
  │       │         ↓
  │       │     Google Sheets: Update Row
  │       │         ↓
  │       │     Telegram: Notify Admin + Confirm Owner
  │       └── NO → Respond to Webhook (status already processed)
  └── NO → Respond to Webhook (401 Unauthorized)

Error Trigger → Telegram: Notify Admin (error)
```

### Key Function Code:
- `verifyHmac()` — HMAC-SHA256 + timestamp tolerance (300s)
- `processDecision()` — Build update payload based on form submission

---

## Milestone 4 — Workflow 03: Reminder & Escalation

### Node Structure (9 nodes):

```
Cron Trigger (every 15 minutes)
    ↓
Google Sheets: Read All (status="Pending Approval")
    ↓
Code: Calculate Aging (time since received_at)
    ↓
Code: Categorize by Reminder Tier
    ↓
Split Reminder Tiers:
  ├── Tier 1 (1-3h): Telegram: Send Reminder 1
  ├── Tier 2 (4-11h): Telegram: Send Reminder 2
  ├── Tier 3 (12-24h): Telegram: Send Reminder 3
  └── Escalation (>24h): Telegram: Notify Admin
    ↓
Google Sheets: Update reminder_count & last_reminder_at

Error Trigger → Telegram: Notify Admin (error)
```

---

## Self-Review Checklist

### 1. JSON Validity
- [ ] Semua 3 workflow valid JSON (python3 -c "import json; json.load(open(f))")
- [ ] Struktur sesuai n8n-technical-boilerplate.md

### 2. Function Code Verification
- [ ] Semua functionCode disalin ke .js file → node --check pass
- [ ] Semua functionCode dijalankan dengan mock data → output benar

### 3. Security
- [ ] Tidak ada hardcoded secrets (pakai $env reference)
- [ ] HMAC verification di workflow 02
- [ ] Error Trigger di semua workflow

### 4. Python Tests
- [ ] pytest tests/ -v → semua PASS

---

## Timeline

| Milestone | Estimasi | Status |
|-----------|----------|--------|
| M1: Foundation | 30 min | Pending |
| M2: Invoice Ingestion | 2 jam | Pending |
| M3: Approval Handler | 2 jam | Pending |
| M4: Reminder Escalation | 1.5 jam | Pending |
| Self-Review | 30 min | Pending |

---

**Status**: Siap dieksekusi. Tunggu approval untuk mulai.
