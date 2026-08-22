# User Guide - Invoice Approval Automation

## Overview
Sistem otomasi approval invoice yang menghilangkan proses manual ekstrak data, catat ke spreadsheet, dan chasing approval via WhatsApp. Flow: **Invoice masuk → OCR otomatis → Google Sheets → Notifikasi Telegram → Owner Approve/Reject → Status update → Admin notif bayar**.

---

## Untuk Owner (Pemilik Bisnis / Approver)

### Menerima Notifikasi
- Setiap invoice baru → notifikasi Telegram otomatis
- Format pesan:
  ```
  📄 Invoice Baru Masuk
  
  🏢 Vendor: PT Sumber Makmur
  📅 Tanggal: 2026-08-10
  🔢 No. Invoice: INV-2026-00123
  💰 Nominal: Rp 15.000.000
  🎯 Confidence: 94%
  
  [ 📎 Lihat File ] (link Google Drive)
  
  [✅ Approve] [❌ Reject]
  ```

### Approve Invoice
1. Klik tombol **✅ Approve**
2. Buka halaman form approval (browser)
3. **Review data** (bisa edit kalau ada salah):
   - Vendor, Tanggal, No. Invoice, Nominal
4. Klik **Approve** → Submit
5. Selesai! Status di Sheets jadi "Approved", Admin dapat notif siap bayar.

### Reject Invoice
1. Klik tombol **❌ Reject**
2. Buka halaman form
3. **Wajib isi alasan reject** (contoh: "Nominal tidak sesuai PO", "Invoice double")
4. Klik **Reject** → Submit
5. Admin dapat notifikasi penolakan + alasan.

### Reminder Otomatis
- Jika belum approve dalam **1 jam** → reminder ke-1
- **4 jam** → reminder ke-2
- **12 jam** → reminder ke-3
- **> 24 jam** → escalation ke Admin (Owner tidak perlu action)

---

## Untuk Admin Keuangan (VA / Accounts Payable)

### Tugas Harian
1. **Cek Google Sheets** tab "Invoices" 
2. Filter kolom **Status = "Approved"**
3. Invoice yang approved → **eksekusi pembayaran** ke supplier
4. (Opsional) Update kolom manual: `Payment Date`, `Payment Ref` jika ada kolom tambahan

### Handling Kasus Khusus

| Status di Sheets | Artinya | Action Admin |
|------------------|---------|--------------|
| **Pending Approval** | Menunggu Owner approve | Tunggu, jangan bayar |
| **Approved** | Owner sudah setuju | **Lakukan pembayaran** |
| **Rejected** | Owner tolak + ada alasan | Baca `Reject Reason`, koordinasi dengan vendor/ Owner |
| **Duplicate** | Invoice duplikat terdeteksi | **Jangan bayar**, cek row aslinya |
| **Low Confidence** | OCR kurang yakin (confidence < 85%) | **Cek manual** file di Drive, edit data di Sheets, ubah status jadi "Pending Approval" |
| **Failed** | Error proses otomatis | Cek log n8n / hubungi tech support |

### Edit Data Manual (Jika OCR Salah)
1. Buka Google Sheets
2. Cari row invoice (filter by Vendor/No. Invoice)
3. Edit kolom: `Vendor`, `Tanggal`, `No. Invoice`, `Nominal`
4. Ubah `Status` → `Pending Approval` (kalau sudah Approved/Rejected, jangan diubah)
5. Sistem akan kirim notifikasi baru ke Owner

### Forward Invoice dari WhatsApp ke Drive
Supplier kirim foto/PDF via WhatsApp:
1. Buka WhatsApp Web / HP
2. Forward file ke **Google Drive folder "Invoices_Incoming"**
   - Cara cepat: Share → Google Drive → pilih folder `Invoices_Incoming`
3. Sistem otomatis detect & proses dalam 5 menit

---

## Google Sheets Structure (Tab "Invoices")

| Kolom | Deskripsi | Contoh |
|-------|-----------|--------|
| `invoice_id` | ID unik sistem (UUID) | `a1b2-c3d4...` |
| `received_at` | Waktu file terdeteksi | `2026-08-12 14:30:00` |
| `vendor` | Nama vendor (dari OCR/edit manual) | `PT Sumber Makmur` |
| `invoice_date` | Tanggal invoice (YYYY-MM-DD) | `2026-08-10` |
| `invoice_number` | Nomor invoice | `INV-2026-00123` |
| `amount` | Nominal (angka, tanpa Rp) | `15000000` |
| `status` | **Pending Approval / Approved / Rejected / Duplicate / Low Confidence / Failed** | `Pending Approval` |
| `confidence` | Skor kepercayaan OCR (0-1) | `0.94` |
| `drive_file_id` | ID file Google Drive | `1AbC...` |
| `drive_file_link` | Link buka file | `https://drive.google.com/file/d/...` |
| `source` | Sumber: `Gmail` atau `Drive` | `Gmail` |
| `approved_at` | Waktu approve (kosong kalau belum) | `2026-08-12 14:45:00` |
| `approved_by` | ID Owner yang approve | `owner_telegram_id` |
| `rejected_at` | Waktu reject | - |
| `reject_reason` | Alasan reject (dari Owner) | `Nominal tidak sesuai PO` |
| `reminder_count` | Jumlah reminder terkirim | `0` |
| `last_reminder_at` | Waktu reminder terakhir | - |
| `created_at` | Row dibuat | `2026-08-12 14:30:00` |
| `updated_at` | Terakhir diubah | `2026-08-12 14:45:00` |

---

## Troubleshooting Umum

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| **Invoice tidak muncul di Sheets** | File bukan PDF/JPG/PNG, atau folder Drive salah | Pastikan file di folder `Invoices_Incoming`, format PDF/JPG/PNG |
| **Data OCR salah (vendor/nominal)** | Foto blur, format invoice tidak standar | Edit manual di Sheets → ubah status ke "Pending Approval" |
| **Tidak dapat notifikasi Telegram** | Bot diblokir / chat ID salah | Cek bot aktif, chat ID benar, coba `/start` ke bot |
| **Klik Approve tapi error** | Webhook tidak accessible / HMAC mismatch | Hubungi tech support (cek n8n logs) |
| **Duplicate tidak terdeteksi** | Bedanya spasi/kapital/format tanggal | Sistem sudah handle case/whitespace, cek composite key |
| **Reminder tidak datang** | Workflow reminder tidak jalan | Cek n8n execution `03-reminder-escalation` |

---

## Tips Efisiensi

### Untuk Owner
- **Bookmark** chat bot Telegram untuk akses cepat
- Gunakan **Telegram Desktop** untuk approve dari laptop
- Jika sering approve: Buka form di tab baru, approve batch

### Untuk Admin
- **Filter view** di Sheets: Buat filter view "Pending Approval" & "Approved"
- **Conditional formatting**: Warnai row by status (Hijau=Approved, Merah=Rejected, Kuning=Pending)
- **Notifikasi email** (opsional): Setup n8n kirim email ke Admin saat status=Approved

---

## Keamanan & Privasi

- **Data invoice** hanya di Google Sheets (akses terbatas Owner/Admin)
- **Telegram** hanya kirim ringkasan (vendor, nominal, no invoice) — **bukan file lengkap**
- **File asli** di Google Drive — akses dibatasi Service Account + Owner/Admin
- **Webhook approval** dilindungi HMAC signature — tidak bisa dipalsukan
- **Audit trail** lengkap di Sheets (siapa approve, kapan, alasan reject)

---

## Kontak Bantuan

| Masalah | Kontak |
|---------|--------|
| Teknis (n8n, OCR, Docker) | Tech Support / Developer |
| Akses Google Sheets/Drive | Admin IT / Owner |
| Telegram bot error | Tech Support |
| Data invoice salah | Admin Keuangan (edit manual) |

---

## Versi & Update
- **Versi**: 1.0 (MVP)
- **Terakhir update**: 2026-08-12
- **Changelog**: Lihat `docs/CHANGELOG.md` (jika ada)

---

> **Catatan**: Sistem ini dirancang untuk **Google Workspace only** (Gmail, Drive, Sheets, Document AI). Tidak butuh ERP mahal, server sendiri, atau software berbayar selain biaya minimal GCP (Document AI ~$0.27/bln setelah free tier).