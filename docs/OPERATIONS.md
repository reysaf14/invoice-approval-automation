# Operations Guide

Dokumen ini adalah checklist operasi untuk runtime Docker lokal atau staging. Sesuaikan nama service jika deployment memakai host berbeda.

## Status Runtime yang Diharapkan

Pada runtime lokal yang terakhir diverifikasi:

- `01-invoice-ingestion`: active.
- `02-approval-handler`: active.
- `03-reminder-escalation`: inactive.
- n8n health endpoint: `ok`.

Status tersebut dapat berubah setelah restart atau import ulang. Selalu cek UI/CLI sebelum menganggap workflow aktif.

## Monitoring Harian

```powershell
docker compose ps
docker compose logs --tail=100 n8n
docker compose logs --tail=100 n8n-worker
docker compose logs --tail=100 n8n-webhook
```

Di UI n8n, periksa executions untuk:

- `01-invoice-ingestion`: trigger, DeepSeek response, confidence branch, Sheets write, Telegram send.
- `02-approval-handler`: HMAC result, invoice lookup, status guard, form, Sheets update.
- `03-reminder-escalation`: hanya jika workflow sengaja diaktifkan.

## Google Sheets Review

Filter tab invoice berdasarkan:

- `Pending Approval`: menunggu keputusan.
- `Low Confidence`: perlu pemeriksaan manual terhadap file asli.
- `Duplicate`: jangan bayar sebelum membandingkan row asal.
- `Approved`: siap diproses sesuai SOP pembayaran internal.
- `Rejected`: baca `reject_reason`.
- `Failed`: buka execution n8n dan periksa provider/credential.

Jangan menghapus row lama hanya untuk merapikan tampilan; row tersebut dapat menjadi bagian dari audit trail.

## Telegram Health Check

1. Pastikan bot tidak diblokir oleh recipient.
2. Pastikan owner/admin sudah mengirim `/start` bila bot baru dibuat.
3. Jalankan smoke test hanya pada data dummy agar tidak menambah row bisnis.
4. Periksa bahwa notifikasi invoice baru berupa plain text tanpa link placeholder.

## Approval Webhook

Endpoint approval memerlukan:

- `POST /webhook/approve`.
- Header `x-signature` dalam bentuk `sha256=<hex>`.
- Header `x-timestamp` Unix seconds.
- Canonical JSON body yang sama dengan payload signing.
- `WEBHOOK_HMAC_SECRET` yang sama di caller dan n8n.

Handler menolak request tanpa signature, timestamp kedaluwarsa, signature tidak cocok, invoice yang tidak ditemukan, atau invoice yang statusnya bukan `Pending Approval`.

## Reminder dan Escalation

Workflow reminder memeriksa invoice pending setiap 15 menit dan memiliki tier berbasis umur invoice. Saat ini workflow tersebut tersedia di source tetapi inactive pada runtime lokal terakhir. Jangan mengiklankan reminder otomatis sebagai operationally active sebelum mengaktifkan dan melakukan smoke test.

## Incident Response

### Tidak ada row baru

1. Cek `docker compose ps`.
2. Cek Google Drive folder ID dan OAuth scope.
3. Pastikan file JPG/JPEG/PNG.
4. Buka execution terakhir dan cari node pertama yang gagal.
5. Jika DeepSeek gagal, cek endpoint, model, quota, dan payload image.

### Telegram tidak menerima notifikasi

1. Periksa credential Telegram di node.
2. Periksa chat ID yang berasal dari environment.
3. Pastikan recipient pernah mengirim `/start`.
4. Jangan melakukan retry membabi buta jika status request tidak jelas; periksa execution dan chat Telegram terlebih dahulu.

### Banyak `Low Confidence`

1. Ambil sampel gambar dan periksa blur, crop, rotasi, dan kontras.
2. Bandingkan OCR text dengan field normalisasi.
3. Koreksi manual sesuai SOP.
4. Pertimbangkan preprocessing gambar atau provider OCR khusus sebagai fase berikutnya.

### Duplicate tidak sesuai harapan

Composite key saat ini adalah:

```text
vendor + invoice_number + invoice_date + amount
```

Nilai di-trim dan diubah ke lowercase sebelum dibandingkan. Perbedaan format tanggal atau nominal yang semantik tetapi teksnya berbeda masih dapat lolos.

## Backup dan Secret Rotation

- Backup PostgreSQL volume secara berkala; database ini berisi metadata/execution n8n.
- Export/backup spreadsheet Google sesuai kebijakan organisasi.
- Jangan mencetak token pada log atau dokumentasi.
- Rotasi token DeepSeek, Telegram, OAuth, dan HMAC sesuai kebijakan organisasi.
- Setelah rotasi credential, jalankan smoke test satu invoice dummy.

## Update Workflow

1. Simpan perubahan pada file JSON sumber.
2. Jalankan `pytest -q`.
3. Import sebagai workflow baru atau replace dengan prosedur yang mencegah duplicate.
4. Bind ulang credential jika ID credential berubah.
5. Nonaktifkan workflow lama.
6. Restart n8n bila perubahan aktivasi belum terlihat.
7. Verifikasi health, active state, dan satu smoke test.

## Cleanup Development

Jangan menjalankan `docker compose down -v` pada runtime yang berisi data penting. Perintah tersebut dapat menghapus volume PostgreSQL, Redis, dan n8n.
