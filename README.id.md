# Invoice Approval Automation

Otomasi pemrosesan invoice berbasis n8n yang mengambil file gambar dari Google Drive, membaca isinya dengan DeepSeek multimodal, menyimpan hasil terstruktur ke Google Sheets, lalu mengirim ringkasan ke Telegram untuk ditindaklanjuti.

> Status: **MVP lokal / portfolio demo**. Implementasi dan batasannya dijelaskan berdasarkan workflow yang ada di repository dan runtime lokal yang diverifikasi pada 7 Oktober 2026.

## Nilai Bisnis

Admin tidak perlu menyalin vendor, tanggal, nomor invoice, dan nominal secara manual dari setiap gambar. Sistem memproses invoice secara berkala, menandai hasil OCR yang kurang meyakinkan, mencegah duplikasi berdasarkan kombinasi field invoice, dan menyimpan status approval di satu spreadsheet yang mudah dipantau.

Project ini tidak mengklaim penghematan waktu, akurasi bisnis, volume produksi, atau hasil komersial tertentu. Angka tersebut harus diukur setelah dipakai pada data dan proses bisnis nyata.

## Alur Saat Ini

```text
Google Drive folder (JPG/JPEG/PNG)
        │ polling setiap 5 menit
        ▼
Download file
        ▼
DeepSeek Vision: OCR teks dari gambar
        ▼
DeepSeek JSON normalization: vendor, tanggal, nomor, nominal, confidence
        │
        ├─ confidence < 0.85 → Google Sheets: Low Confidence, tanpa notifikasi owner
        │
        └─ confidence >= 0.85
             ├─ cocok dengan row lama → Google Sheets: Duplicate
             └─ invoice baru → Google Sheets: Pending Approval
                                      │
                                      └─ Telegram owner: ringkasan teks biasa
```

Workflow approval terpisah menyediakan endpoint `POST /webhook/approve` dengan verifikasi HMAC-SHA256, pemeriksaan status, form n8n untuk keputusan, update Google Sheets, dan notifikasi hasil ke Telegram. Workflow reminder membaca invoice pending setiap 15 menit, tetapi pada runtime lokal terakhir workflow reminder masih **inactive**.

## Status Kapabilitas

| Kapabilitas | Status | Catatan |
|---|---|---|
| Trigger Google Drive folder | Terimplementasi | Polling 5 menit; hanya file JPG/JPEG/PNG |
| OCR gambar dan normalisasi field | Terimplementasi | Dua request ke DeepSeek: vision OCR lalu JSON normalization |
| Confidence gate 0.85 | Terimplementasi | Hasil rendah masuk Sheets sebagai `Low Confidence` |
| Deduplikasi | Terimplementasi | Vendor + nomor + tanggal + nominal, setelah normalisasi trim/lowercase |
| Pencatatan Google Sheets | Terimplementasi | Row invoice menyimpan status dan field audit utama |
| Notifikasi invoice baru | Terimplementasi | Telegram plain text; tidak ada emoji, Markdown, atau link placeholder |
| Approval endpoint + HMAC | Terimplementasi di workflow | Memerlukan caller yang dapat mengirim header signature dan timestamp |
| Approval via tombol Telegram | Belum terhubung | Pesan invoice saat ini hanya notifikasi teks |
| Approval form n8n | Terimplementasi di workflow | Dibuka setelah request approval yang valid |
| Reminder/escalation | Terimplementasi di source workflow | Runtime lokal terakhir inactive; perlu diaktifkan bila ingin dipakai |
| PDF, Gmail, WhatsApp API, WEBP | Belum didukung oleh jalur aktif | File harus lebih dulu berada di Drive dan berformat JPG/JPEG/PNG |

## Komponen Teknis

- **Orchestrator:** n8n 1.74.0, self-hosted dengan Docker Compose queue mode.
- **n8n main/UI:** `http://localhost:5680`.
- **Webhook edge:** `http://localhost:5678`.
- **Worker:** proses queue n8n terpisah.
- **Metadata n8n:** PostgreSQL 16.
- **Queue:** Redis 7.
- **AI:** DeepSeek API yang kompatibel dengan chat completions; request vision memakai `image_url` base64 dan request kedua meminta JSON terstruktur.
- **Business store:** Google Sheets.
- **File store:** Google Drive.
- **Notifikasi:** Telegram Bot API melalui credential n8n.
- **Approval security:** HMAC-SHA256, timestamp tolerance, dan constant-time comparison.

## Struktur Repository

```text
invoice-approval-automation/
├── n8n-workflows/
│   ├── 01-invoice-ingestion.json
│   ├── 02-approval-handler.json
│   ├── 03-reminder-escalation.json
│   └── test-webhook-only.json
├── .ai/
│   ├── knowledge/              # PRD, architecture, project brief
│   ├── decisions/              # ADR dan trade-off teknis
│   └── implementation/         # status implementasi
├── docs/
│   ├── SETUP.md
│   ├── USER_GUIDE.md
│   ├── OPERATIONS.md
│   └── PROJECT_STATUS.md
├── tests/                      # pytest regression tests
├── docker-compose.yml          # queue-mode stack
├── docker-compose.single.yml   # single-mode test stack
└── .env.template
```

## Quick Start Lokal

1. Salin `.env.template` menjadi `.env` dan isi secret asli secara lokal.
2. Hubungkan credential Google Drive/Sheets dan Telegram di n8n.
3. Pastikan `DEEPSEEK_API_URL`, `DEEPSEEK_API_KEY`, dan `DEEPSEEK_MODEL` benar. Jalur aktif tidak memanggil local-ai/Ollama.
4. Jalankan `docker compose up -d`.
5. Buka `http://localhost:5680`, import workflow, bind credential, lalu aktifkan workflow yang diperlukan.
6. Upload gambar invoice JPG/JPEG/PNG ke folder Drive yang dikonfigurasi.
7. Periksa Google Sheets, eksekusi n8n, dan chat Telegram owner.

Panduan rinci: [SETUP.md](docs/SETUP.md), [USER_GUIDE.md](docs/USER_GUIDE.md), [OPERATIONS.md](docs/OPERATIONS.md), dan [PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

## Pengujian

```powershell
pytest -q
```

Regression suite lokal terakhir: **42 passed**. Test mencakup dedupe, parsing OCR, schema Sheets, HMAC webhook, workflow contract, dan format notifikasi. Test tersebut bukan pengganti uji penerimaan pada akun Google, DeepSeek, dan Telegram milik pengguna.

## Keterbatasan Penting

- Google Sheets bukan database transaksional; konflik update dan pertumbuhan row perlu dipantau.
- DeepSeek menjadi dependency untuk vision OCR dan normalisasi; quota, latency, dan format output provider dapat berubah.
- Foto buram atau terpotong dapat menghasilkan `Low Confidence` atau field kosong.
- Jalur aktif tidak menerima PDF/WEBP langsung, tidak membaca Gmail, dan tidak terhubung ke WhatsApp API.
- Pesan invoice baru tidak membawa link file atau tombol approval. Approval endpoint dan form tersedia, tetapi penghubung tombol Telegram belum dibuat.
- Workflow reminder tersedia di repository, namun harus diaktifkan dan diuji pada runtime target.
- PostgreSQL dan Redis menyimpan kebutuhan internal n8n, bukan data bisnis invoice utama.

## Keamanan

- Jangan commit `.env`, credential Google, atau token Telegram.
- Simpan provider credential di n8n Credential Store.
- Approval webhook harus memakai secret HMAC yang kuat dan timestamp tolerance yang sesuai.
- Telegram hanya menerima ringkasan invoice; file asli tetap di Google Drive.

Untuk keputusan teknis dan alasan trade-off, lihat folder `.ai/decisions/`.

## Lisensi

Project ini adalah learning/portfolio project dan bukan klaim deployment produksi.
