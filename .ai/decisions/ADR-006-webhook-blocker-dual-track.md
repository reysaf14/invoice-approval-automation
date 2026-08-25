# ADR-006: Webhook Blocker Mitigation - Dual Track (Root Cause Isolation + Polling Fallback)

## Status
**RESOLVED** — Track A completed; root cause confirmed (2026-08-25).

## Context
QA REGRESSION #7 (2026-08-25) menemukan blocker kritis: production webhook n8n mengembalikan **404** pada v1.60.0 DAN v1.74.0. Evidence awal:

- Workflow `active=true` di DB, startup logs "Adding webhooks" + "Successfully started"
- Request sampai ke n8n (log muncul), tapi response 404
- Tabel `webhook_entity` **0 rows** di kedua versi
- Semua metode aktivasi gagal persist registrasi: CLI import, REST API PATCH, REST API create-new, UI toggle

Karena bug terjadi di dua versi berbeda, ini bukan regression n8n — ini masalah konfigurasi/lingkungan. Pola gejala (`webhook_entity` kosong + log "Adding webhooks" muncul + request diterima tapi tidak match) konsisten dengan dua hipotesis terkuat:
1. **DB split-brain**: instance yang menerima HTTP request memakai database berbeda dari instance tempat workflow diaktifkan (mis. compose single-mode vs queue-mode menunjuk DB/volume berbeda)
2. **Queue mode tanpa webhook processor**: dalam arsitektur queue n8n, registrasi webhook adalah tanggung jawab proses khusus; jika hanya main+worker yang jalan tanpa proses webhook, live-webhooks registry kosong meski DB bilang active

## Track A Results — COMPLETED (2026-08-25)

**Root cause: Malformed workflow JSON — properti `webhookId` diletakkan di DALAM `parameters`, bukan di level node.**

Karena itu n8n tidak mengenali webhook sebagai fixed path → registrasi jatuh ke dynamic path ber-prefix `<workflowId>/webhook/<path>` → semua POST ke path polos 404.

| Hipotesis | Verdict | Bukti |
|---|---|---|
| H1 — DB split-brain | ❌ DISKONFIRMASI | Gejala 100% direproduksi di rig satu-DB/one-volume terisolasi |
| H2 — Queue mode tanpa webhook processor | ❌ DISKONFIRMASI | Regular mode gagal identik; queue mode BERHASIL 200 begitu JSON diperbaiki |

Bukti fix: setelah `webhookId` dipindah ke level node, `webhook_entity` = 1 row path polos, POST → 200 + execution success.

**Stack updated**: 3 service n8n — `n8n` (UI, host 5682), `n8n-webhook` (public entrypoint, host 5678), `n8n-worker`.

## Track B — DIPEPERTAHANKAN sebagai Kill-Switch

Meski webhook sudah fixed, Track B (polling fallback) tetap dipertahankan: jika webhook regresi di masa depan → flip env `APPROVAL_MODE=polling` tanpa deploy ulang. Latensi ≤60 detik masih memenuhi kebutuhan bisnis.

## Alternatives Considered
1. **Downgrade n8n ke v1.30.x/v1.40.x** — ditolak: bug identical di dua versi, bukan regression versi.
2. **Pindah ke n8n Cloud** — ditunda: biaya rekuren; hanya opsi eskalasi.
3. **Full rewrite tanpa n8n** — ditolak: overengineering.

## Consequences
- **Positive**: Root cause dikonfirmasi dengan evidence reproduksi dua arah; fix minimal = 1 properti dipindah; stack topology lebih sehat (3 service vs 2).
- **Negative**: Webhook flow butuh Engineer fix JSON sebelum production-ready; Track B tetap membutuhkan implementasi jika ingin kill-switch.
- **Mitigasi**: `docker-compose.track-a-audit.yml` dipertahankan sebagai alat reproduksi bagi QA.

## Implementation Notes
- **Engineer (P1 — blocker produksi)**: Pindahkan `webhookId` ke level node di `n8n-workflows/02-approval-handler.json` dan `test-webhook-only.json`. Satu baris lokasi properti per node. Referensi: `scripts/track-a-workflows/test-webhook-only.json` (versi FIXED). Import via CLI harus file **array-wrapped** (bukan objek tunggal). Aktivasi via UI toggle atau PATCH REST (bukan SQL).
- **Engineer/DevOps (P2)**: Apply race migration fix — `depends_on` worker: `n8n: condition: service_healthy`. DevOps sudah menyiapkan patch, menunggu Engineer apply di compose.
- **QA (REGRESSION #8)**: (a) verify JSON fixed; (b) import via CLI array-wrapped atau REST create; (c) activate via UI toggle / PATCH REST; (d) `SELECT * FROM webhook_entity` → 1 row path polos tanpa prefix; (e) POST probe → expect 200 atau 4xx-validasi-bisnis, BUKAN 404-not-registered.
