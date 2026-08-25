# ADR-006: Webhook Blocker Mitigation - Dual Track (Root Cause Isolation + Polling Fallback)

## Status
Accepted

## Context
QA REGRESSION #7 (2026-08-25) menemukan blocker kritis: production webhook n8n mengembalikan **404** pada v1.60.0 DAN v1.74.0. Evidence:

- Workflow `active=true` di DB, startup logs "Adding webhooks" + "Successfully started"
- Request sampai ke n8n (log muncul), tapi response 404
- Tabel `webhook_entity` **0 rows** di kedua versi
- Semua metode aktivasi gagal persist registrasi: CLI import, REST API PATCH, REST API create-new, UI toggle

Karena bug terjadi di dua versi berbeda, ini bukan regression n8n — ini masalah konfigurasi/lingkungan. Pola gejala (`webhook_entity` kosong + log "Adding webhooks" muncul + request diterima tapi tidak match) konsisten dengan dua hipotesis terkuat:
1. **DB split-brain**: instance yang menerima HTTP request memakai database berbeda dari instance tempat workflow diaktifkan (mis. compose single-mode vs queue-mode menunjuk DB/volume berbeda)
2. **Queue mode tanpa webhook processor**: dalam arsitektur queue n8n, registrasi webhook adalah tanggung jawab proses khusus; jika hanya main+worker yang jalan tanpa proses webhook, live-webhooks registry kosong meski DB bilang active

## Decision
Eksekusi **dual-track plan** dengan timebox:

### Track A — Root Cause Isolation (timebox 48 jam)
Urutan verifikasi WAJIB berurutan (stop saat ketemu akar masalah):

1. **Audit DB split-brain**: pastikan SEMUA service n8n (main/worker/single) menunjuk SATU PostgreSQL dan SATU volume `.n8n` yang sama. Cek: jumlah container n8n aktif, env `DB_POSTGRESHOST`/`DB_POSTGRESDB` tiap service, volume mount.
2. **Queue mode audit**: jika queue mode dipakai, jalankan service `n8n webhook` terpisah (`command: webhook`) sesuai arsitektur queue resmi n8n — ATAU turunkan ke regular mode (single container, tanpa worker). Volume 120 invoice/bln tidak membutuhkan queue mode.
3. **Bare-metal isolation**: jalankan `npx n8n` langsung di host (tanpa Docker) dengan DB SQLite lokal → import 1 workflow webhook sederhana → activate → test. Hasil: (a) jalan = Docker/env issue; (b) gagal juga = issue versi/konfigurasi n8n.
4. **Config audit**: bandingkan `WEBHOOK_URL`, `N8N_HOST`, `N8N_PROTOCOL`, `N8N_PORT` antar environment; pastikan tidak ada reverse proxy yang menulis ulang path.

### Track B — Polling Fallback (implement paralel, siap ship)
Arsitektur approval TANPA inbound webhook sama sekali:

```
Owner klik Approve/Reject di Telegram
  → (jalur 1) Telegram Trigger n8n mode POLLING (getUpdates, tanpa setWebhook)
  → (jalur 2) tombol deep-link ke Google Apps Script Web App
       → Apps Script tulis baris aksi ke tab Sheets baru: Approval_Actions
         (invoice_id, action, reason, actor_telegram_id, created_at, processed=false)

Schedule Trigger n8n (setiap 1 menit):
  → baca tab Approval_Actions WHERE processed=false
  → validasi actor vs Owner chat ID
  → update status Invoices (Approved/Rejected + audit fields)
  → tandai baris aksi processed=true
  → kirim notifikasi Admin
```

Konsekuensi desain: latensi approval naik dari <10 detik menjadi ≤60 detik (masih memenuhi kebutuhan bisnis; PRD success criterion perlu direvisi dari "<10 detik" menjadi "<60 detik" bila Track B yang produksi).

## Alternatives Considered
1. **Downgrade n8n ke v1.30.x/v1.40.x** — ditolak sebagai solusi utama: bug muncul di dua versi berbeda, indikasi kuat masalahnya environment; downgrade hanya eksperimen tambahan di Track A step 3 bila bare-metal lolos.
2. **Pindah ke n8n Cloud** — ditunda: biaya rekuren + data residency; hanya opsi eskalasi jika Track A & B gagal.
3. **Full rewrite ke custom script (tanpa n8n)** — ditolak: overengineering, melanggar prinsip reuse-before-create.

## Consequences
- **Positive**: Jalur approval tidak lagi bergantung pada inbound webhook; root cause tetap dicari secara terstruktur dengan timebox; risiko production delay termitigasi.
- **Negative**: Latensi approval ≤60 detik pada Track B; Apps Script Web App butuh deployment + sharing setting terkontrol; polling Telegram memakai resource poll ringan.
- **Risk**: Jika Track A menemukan akar masalah dan webhook normal kembali → Track B tetap dipertahankan sebagai fallback path (kill switch via env flag).

## Implementation Notes
- Engineer: implementasi Track B di workflow `02-approval-handler-polling` + Apps Script `docs/approval-action-writer.gs`; env flag `APPROVAL_MODE=webhook|polling`.
- DevOps: eksekusi Track A steps 1–4, dokumentasikan temuan per step.
- QA: verifikasi kedua track di REGRESSION #8; acceptance = approval end-to-end jalan di minimal satu jalur.
