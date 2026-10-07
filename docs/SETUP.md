# Setup Guide

Panduan ini menyiapkan demo lokal yang sesuai dengan workflow di repository. Secret asli hanya boleh disimpan di `.env` atau n8n Credential Store.

## Prasyarat

- Docker Desktop dan Docker Compose v2.
- Google Cloud project dengan Google Drive API dan Google Sheets API.
- Google OAuth client untuk n8n.
- Spreadsheet dan folder Drive untuk invoice.
- Telegram bot dan chat ID owner/admin.
- DeepSeek API key dan model yang menerima image input.

Jalur aktif tidak membutuhkan local-ai/Ollama. `LOCAL_AI_BASE_URL` yang ada di template environment adalah nilai kompatibilitas/legacy dan tidak dipanggil oleh workflow ingestion saat ini.

## 1. Environment

```powershell
Copy-Item .env.template .env
```

Isi sekurangnya:

```text
N8N_BASIC_AUTH_USER=...
N8N_BASIC_AUTH_PASSWORD=...
N8N_ENCRYPTION_KEY=...
DB_POSTGRESDB_PASSWORD=...
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

`WEBHOOK_URL` untuk stack ini adalah base URL webhook, bukan URL dengan suffix `/webhook`. Contoh lokal: `http://localhost:5678`.

## 2. Google OAuth

Di Google Cloud Console, tambahkan redirect URI berikut untuk credential OAuth n8n lokal:

```text
http://localhost:5680/rest/oauth2-credential/callback
```

Kemudian:

1. Buka `http://localhost:5680`.
2. Buat atau edit credential Google Drive OAuth2.
3. Masukkan client ID/secret dari Google Cloud.
4. Hubungkan akun Google dummy atau akun kerja yang memang diberi izin.
5. Ulangi untuk Google Sheets OAuth2 bila credential terpisah digunakan.

Pastikan akun tersebut memiliki akses ke spreadsheet dan folder Drive target.

## 3. Telegram Credential

1. Buat bot melalui `@BotFather`.
2. Simpan token hanya di n8n Credential Store.
3. Kirim `/start` ke bot dari akun owner dan admin.
4. Isi `TELEGRAM_OWNER_CHAT_ID` dan `TELEGRAM_ADMIN_CHAT_ID` di environment n8n.

Workflow saat ini mengirim pesan Telegram melalui Bot API; tidak ada Telegram webhook atau Telegram inline-button approval yang menjadi trigger aktif.

## 4. Start Docker Stack

```powershell
docker compose up -d
docker compose ps
```

Port yang digunakan:

| Service | Host port | Fungsi |
|---|---:|---|
| `n8n-main` | `5680` | UI, editor, OAuth callback |
| `n8n-webhook` | `5678` | Public webhook entrypoint |
| `n8n-worker` | - | Queue execution |
| PostgreSQL | internal | Metadata dan execution n8n |
| Redis | internal | Queue |

Verifikasi:

```powershell
Invoke-RestMethod http://localhost:5680/healthz
Invoke-RestMethod http://localhost:5678/healthz
```

## 5. Import dan Aktivasi Workflow

Import dari UI n8n atau CLI. File yang digunakan:

- `n8n-workflows/01-invoice-ingestion.json`
- `n8n-workflows/02-approval-handler.json`
- `n8n-workflows/03-reminder-escalation.json`

Setelah import:

1. Bind credential Google Drive pada trigger dan download node.
2. Bind credential Google Sheets pada node read/write.
3. Bind credential Telegram pada node send.
4. Periksa expression environment DeepSeek dan chat ID.
5. Aktifkan workflow satu per satu.
6. Pastikan tidak ada duplicate workflow dengan nama sama.

> Import CLI membuat workflow baru dan biasanya inactive. Jika re-import, nonaktifkan/hapus workflow lama setelah workflow baru diverifikasi agar satu file tidak memicu dua kali.

Default source JSON menyimpan `active: false`; aktivasi adalah keputusan runtime, bukan bagian dari file export.

## 6. Google Sheets Schema

Gunakan tab invoice dengan header berikut:

```text
invoice_id, received_at, vendor, invoice_date, invoice_number, amount,
status, confidence, drive_file_id, drive_file_link, source, approved_at,
approved_by, rejected_at, reject_reason, reminder_count, last_reminder_at,
created_at, updated_at
```

Workflow menggunakan `GOOGLE_SHEETS_SPREADSHEET_ID` dari environment dan nama tab yang tersimpan di node Google Sheets. Periksa kembali nama tab saat binding credential.

## 7. Smoke Test Aman

1. Upload satu JPG/JPEG/PNG invoice dummy ke folder Drive.
2. Tunggu maksimal satu interval polling.
3. Periksa execution `01-invoice-ingestion`.
4. Periksa row di Sheets.
5. Periksa Telegram owner.
6. Untuk confidence rendah, pastikan row menjadi `Low Confidence` dan tidak ada notifikasi owner.
7. Hindari mengulang file yang sama jika tidak ingin membuat row duplikat.

Regression test lokal:

```powershell
pytest -q
```

## Troubleshooting Cepat

| Masalah | Tindakan |
|---|---|
| n8n tidak sehat | `docker compose logs --tail=100 n8n` dan cek PostgreSQL/Redis |
| OAuth gagal | Pastikan callback persis memakai port `5680` dan client Google mengizinkannya |
| Drive tidak memicu | Cek folder ID, scope OAuth, dan ekstensi file |
| DeepSeek gagal | Cek endpoint, model vision, API key, quota, dan ukuran image base64 |
| Sheets tidak berubah | Cek credential, spreadsheet ID, nama tab, dan execution detail |
| Telegram tidak terkirim | Cek token credential, chat ID, `/start`, dan log node Telegram |
| Approval `401` | Cek HMAC secret, timestamp, dan canonical payload caller |

Untuk operasi harian, lihat [OPERATIONS.md](OPERATIONS.md). Untuk perilaku bisnis, lihat [USER_GUIDE.md](USER_GUIDE.md).
