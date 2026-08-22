# Project Brief: Invoice Approval Automation

## 📋 Business Problem

**Owner** (pemilik bisnis) yang approve pembayaran dan memantau arus kas mengalami bottleneck pada proses approval invoice. Saat ini **Admin Keuangan (VA)** menerima 15–30 invoice per minggu (3–5 invoice/hari, puncak di pertengahan/akhir bulan) via **Email (Gmail)** dan **WhatsApp** (foto kuitansi/PDF). Admin harus mengekstrak data manual, mencatat ke **Google Sheets**, lalu chasing Owner via WhatsApp berulang kali untuk approval. Jika approval terlambat, **pengiriman barang dari supplier tertunda**. Proses manual ini tidak efisien, rawan kesalahan input, dan menciptakan dependency komunikasi yang berlebihan.

## 🎯 Project Goal

Membangun sistem otomasi end-to-end yang:
1. **Mendeteksi & mengekstrak data invoice** (Nama Vendor, Tanggal, Nomor Invoice, Total Nominal) dari PDF/foto yang masuk ke Gmail atau folder Google Drive tertentu.
2. **Mencatat otomatis ke Google Sheets** sebagai baris baru dengan status `Pending Approval`.
3. **Mengirim notifikasi ke Telegram Owner** dengan tombol/link approval sekali klik.
4. **Mengubah status ke `Approved`** di Google Sheets begitu Owner approve, sekaligus **notifikasi Admin** untuk eksekusi pembayaran.

Tujuan akhir: **Menghilangkan chasing manual**, mempercepat siklus approval, dan memastikan supplier dibayar tepat waktu agar pengiriman barang tidak tertunda.

## ✅ Success Criteria

| Metric | Target |
|--------|--------|
| Waktu ekstrak data invoice → masuk Google Sheets | < 2 menit setelah invoice diterima |
| Waktu Owner approve via Telegram → status update di Sheets | < 10 detik |
| Akurasi ekstraksi data (Vendor, Tanggal, No. Invoice, Nominal) | ≥ 95% |
| Admin tidak perlu chasing Owner via WhatsApp | 0 kali per minggu |
| Invoice yang terlewat/tidak terekam | 0 per bulan |

## 📦 Scope Awal (MVP)

**In Scope:**
- Penerimaan invoice dari 2 sumber: Gmail (attachment) + Google Drive folder tertentu (upload manual/forward WhatsApp).
- Ekstraksi 4 field wajib: **Nama Vendor, Tanggal Invoice, Nomor Invoice, Total Nominal**.
- Penulisan otomatis ke Google Sheets (tab/worksheet rekap invoice) dengan kolom: Timestamp Masuk, Vendor, Tanggal, No. Invoice, Nominal, Status (Pending/Approved/Rejected), Approved At, Approved By.
- Notifikasi Telegram ke Owner: ringkasan invoice + tombol **Approve** / **Reject** (callback atau deep-link).
- Update status real-time di Google Sheets setelah Owner action.
- Notifikasi ke Admin (Telegram/Email) saat status jadi `Approved`.
- Hanya **1 level approval** (Owner saja).
- Ekosistem **Google Workspace only** (Gmail, Drive, Sheets, Apps Script / Cloud Functions / Automation tool yang terintegrasi native).

**Out of Scope (MVP):**
- Multi-level approval / hierarchy approval.
- Integrasi ERP / accounting software (Xero, QuickBooks, Jurnal, dll).
- OCR untuk dokumen non-invoice (PO, SPK, kwitansi pembayaran).
- Dashboard visualisasi / reporting lanjutan.
- Mobile app native.
- Handling invoice revisi / credit note / debit note.
- Multi-currency / pajak kompleks (PPN, PPh 23, dll) — nominal diambil as-is dari invoice.

## ⚠️ Risiko yang Sudah Dikenal

| Risiko | Dampak | Mitigasi Awal |
|--------|--------|---------------|
| **Akurasi OCR/AI ekstrak data rendah** (invoice format beragam, foto blur, tangan) | Data salah masuk Sheets → pembayaran salah / reject manual | Validasi wajib di UI approval (Owner lihat preview gambar + data terisi); fallback manual edit di Sheets; confidence score threshold. |
| **Invoice masuk via WhatsApp tidak terstruktur** (forward ke Drive manual) | Bottleneck tetap ada di Admin | SOP: Admin forward ke Drive folder / email alias otomatis; explorasi WhatsApp Business API untuk fase 2. |
| **Owner tidak buka/lewat notifikasi Telegram** | Approval tertunda → supplier delay | Reminder otomatis (mis. 1 jam, 4 jam, 12 jam); fallback notifikasi Email; escalation ke Admin jika > 24 jam. |
| **Google Sheets rate limit / quota** (volume 30/minggu = ~120/bulan, aman) | Gagal write / update status | Batch write jika perlu; monitoring quota. |
| **Duplicate invoice** (supplier kirim ulang, Admin forward 2x) | Double payment risk | Dedupe key: Vendor + No. Invoice + Tanggal + Nominal; flag duplikat di Sheets. |
| **Keamanan data finansial di Telegram** | Bocor nominal/vendor | Hanya kirim ringkasan minimal; link approval ke halaman aman (Web App / Cloud Function) bukan data sensitif di payload callback. |
| **Perubahan format invoice supplier** | Ekstraksi gagal | Template prompt/OCR per vendor; retrain/perbaiki prompt saat pola baru ditemukan. |

---

**Status**: Draft untuk review Owner.  
**Next Step**: Approve project brief → lanjut ke PRD (Product Requirement Document).