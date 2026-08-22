# PRD: Invoice Approval Automation

## Latar Belakang

Owner bisnis mengalami bottleneck pada proses approval invoice karena Admin Keuangan harus mengekstrak data manual dari 15–30 invoice per minggu yang masuk via Gmail dan WhatsApp, mencatat ke Google Sheets, lalu chasing Owner berulang kali via WhatsApp untuk persetujuan. Keterlambatan approval menyebabkan pengiriman barang dari supplier tertunda. Sistem otomasi end-to-end dibutuhkan untuk menghilangkan proses manual, mempercepat siklus approval, dan memastikan pembayaran tepat waktu.

## User Stories

1. **Sebagai Admin Keuangan**, saya ingin invoice yang masuk ke Gmail atau Google Drive otomatis diekstrak datanya dan tercatat di Google Sheets, agar tidak perlu input manual dan menghindari kesalahan ketik.
2. **Sebagai Admin Keuangan**, saya ingin sistem mendeteksi duplikat invoice (Vendor + Nomor Invoice + Tanggal + Nominal sama), agar tidak terjadi risiko double payment.
3. **Sebagai Owner**, saya ingin menerima notifikasi Telegram berisi ringkasan invoice (Vendor, Tanggal, Nomor, Nominal) dengan tombol Approve/Reject sekali klik, agar bisa menyetujui pembayaran dari mana saja tanpa buka spreadsheet.
4. **Sebagai Owner**, saya ingin melihat preview gambar invoice di halaman approval sebelum memutuskan, agar memastikan data yang diekstrak sesuai dengan dokumen asli.
5. **Sebagai Owner**, saya ingin mendapat reminder otomatis jika belum approve setelah 1 jam, 4 jam, dan 12 jam, agar tidak lupa dan approval tidak tertunda lama.
6. **Sebagai Owner**, saya ingin bisa menolak (Reject) invoice dengan alasan, dan Admin mendapat notifikasi penolakan tersebut, agar proses koreksi bisa segera dilakukan.
7. **Sebagai Admin Keuangan**, saya ingin mendapat notifikasi real-time saat status invoice berubah menjadi Approved, agar bisa segera eksekusi pembayaran ke supplier.
8. **Sebagai Admin Keuangan**, saya ingin bisa mengedit data invoice di Google Sheets jika hasil ekstraksi salah, dan sistem tetap melacak perubahan tersebut, agar koreksi data tidak menghilangkan audit trail.

## Fitur Wajib (Must Have)

1. **Penerimaan Invoice Multi-Sumber**  
   Sistem menerima invoice dari Gmail (attachment PDF/gambar) dan folder Google Drive tertentu (upload manual/forward dari WhatsApp).

2. **Ekstraksi Data Otomatis (OCR/AI)**  
   Ekstrak 4 field wajib: Nama Vendor, Tanggal Invoice, Nomor Invoice, Total Nominal. Hasil ekstraksi disertai confidence score per field.

3. **Pencatatan Otomatis ke Google Sheets**  
   Setiap invoice valid tercatat sebagai baris baru dengan kolom: Timestamp Masuk, Vendor, Tanggal, No. Invoice, Nominal, Status (Pending/Approved/Rejected), Approved At, Approved By, Confidence Score, Link File Sumber.

4. **Deduplikasi Invoice**  
   Cek duplikat berdasarkan kombinasi: Vendor + Nomor Invoice + Tanggal + Nominal. Invoice duplikat di-flag (status "Duplicate") dan tidak membuat baris baru, tetap tercatat di log.

5. **Notifikasi Approval ke Telegram Owner**  
   Kirim pesan terstruktur berisi ringkasan invoice + tombol **Approve** / **Reject**. Payload callback tidak mengandung data sensitif lengkap.

6. **Halaman Approval Web (Preview + Aksi)**  
   Tombol Telegram mengarah ke halaman aman yang menampilkan: preview gambar/PDF invoice, data terisi (editable oleh Owner sebelum approve), tombol Approve/Reject dengan field alasan reject (wajib jika Reject).

7. **Update Status Real-time ke Google Sheets**  
   Saat Owner klik Approve: status → Approved, kolom Approved At diisi timestamp, Approved By diisi identitas Owner. Saat Reject: status → Rejected, alasan tertulis di kolom Catatan/Reject Reason.

8. **Notifikasi ke Admin saat Approved**  
   Admin menerima notifikasi (Telegram/Email) berisi detail invoice yang sudah disetujui, siap untuk eksekusi pembayaran.

9. **Reminder & Escalation Otomatis**  
   Reminder ke Owner: 1 jam, 4 jam, 12 jam setelah notifikasi pertama. Jika > 24 jam belum di-approve, escalation notifikasi ke Admin.

10. **Audit Trail Perubahan**  
    Setiap perubahan status (Pending→Approved, Pending→Rejected, edit manual di Sheets) tercatat dengan timestamp, actor, dan nilai sebelum/sesudah.

## Fitur Tambahan (Nice to Have)

1. **Dashboard Ringkasan Mingguan/Bulanan** — Rekap jumlah invoice, total nominal, rata-rata waktu approval, aging invoice pending.
2. **Klasifikasi Otomatis Kategori Pengeluaran** — Berdasarkan nama vendor atau deskripsi invoice (mis. Restock, Operasional, Marketing).
3. **Integrasi Kalender** — Otomatis buat event "Jatuh Tempo Pembayaran" di Google Calendar Owner/Admin berdasarkan tanggal invoice + terms.
4. **Export Laporan ke PDF/Excel** — Untuk keperluan audit/internal review bulanan.
5. **Whitelist/Blacklist Vendor** — Approve otomatis untuk vendor tepercaya (bypass approval), flag vendor bermasalah.

## Kriteria Sukses

| Metric | Target |
|--------|--------|
| Waktu ekstrak data invoice → masuk Google Sheets | < 2 menit setelah invoice diterima |
| Waktu Owner approve via Telegram → status update di Sheets | < 10 detik |
| Akurasi ekstraksi data (Vendor, Tanggal, No. Invoice, Nominal) | ≥ 95% |
| Admin tidak perlu chasing Owner via WhatsApp | 0 kali per minggu |
| Invoice yang terlewat/tidak terekam | 0 per bulan |
| Duplicate invoice terdeteksi & di-flag | 100% |
| Reminder terkirim tepat waktu (1j, 4j, 12j) | 100% |
| Uptime sistem penerimaan & notifikasi | ≥ 99.5% |

## Riwayat Revisi

| Versi | Tanggal | Perubahan | Diminta oleh |
|-------|---------|-----------|--------------|
| v1 | 2026-08-12 | Draft awal dari project brief | User |

---

**Mohon review dan beri persetujuan (Approve) sebelum saya lanjutkan ke tahap desain teknis.**