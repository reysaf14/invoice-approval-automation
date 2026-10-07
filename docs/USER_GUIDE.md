# Panduan Pengguna

## Ringkasnya

Jalur aktif menerima **gambar invoice JPG, JPEG, atau PNG** dari folder Google Drive yang dikonfigurasi. n8n mengirim gambar ke DeepSeek untuk OCR dan normalisasi, menyimpan hasil ke tab invoice di Google Sheets, lalu mengirim ringkasan plain text ke Telegram owner.

Pesan invoice baru saat ini adalah **notifikasi**, bukan tombol approval. Link file dan tombol `Approve/Reject` sengaja tidak ditampilkan karena belum ada penghubung Telegram button/deep-link ke endpoint approval.

## Alur Invoice Baru

1. Admin menaruh gambar invoice di folder Drive yang sudah dikonfigurasi.
2. Trigger Drive memeriksa folder setiap lima menit.
3. Sistem hanya melanjutkan JPG/JPEG/PNG; tipe file lain diabaikan.
4. DeepSeek membaca teks gambar, kemudian menormalisasi `vendor`, `invoice_date`, `invoice_number`, `amount`, dan confidence.
5. Jika confidence di bawah `0.85`, row ditulis sebagai `Low Confidence` dan tidak ada notifikasi owner.
6. Jika confidence cukup, sistem membaca Sheets untuk dedupe.
7. Invoice baru ditulis sebagai `Pending Approval` dan owner menerima pesan Telegram.
8. Invoice yang cocok dengan composite key ditulis sebagai `Duplicate` dan tidak dikirim sebagai invoice baru.

Contoh pesan:

```text
INVOICE BARU MASUK

Vendor: PT Mitra Agung
Tanggal: 2025-01-01
No. Invoice: LKP-02-03012025
Nominal: Rp 2.500.000
Confidence: 94%
Status: Pending Approval
```

## Untuk Owner

- Gunakan Telegram untuk melihat ringkasan invoice baru.
- Verifikasi keputusan terhadap file asli di Google Drive atau row Google Sheets.
- Karena tombol approval belum terhubung pada pesan, approval dilakukan melalui caller/integrasi yang dapat memanggil endpoint signed `POST /webhook/approve`.
- Setelah request valid, workflow membuka form n8n. Pilih `Approve` atau `Reject`.
- Saat memilih `Reject`, alasan wajib diisi.

### Apa yang Terjadi Setelah Approval

- `Approved`: Sheets diperbarui dengan status, waktu, dan actor; admin menerima notifikasi hasil.
- `Rejected`: Sheets diperbarui dengan status, waktu, dan alasan; admin menerima notifikasi hasil.
- Jika status bukan `Pending Approval`, handler tidak memproses ulang invoice tersebut.

## Untuk Admin Keuangan

### Status di Google Sheets

| Status | Arti | Tindakan |
|---|---|---|
| `Pending Approval` | Menunggu keputusan | Jangan bayar sebelum disetujui |
| `Approved` | Owner menyetujui | Lanjutkan proses pembayaran sesuai SOP bisnis |
| `Rejected` | Invoice ditolak | Baca alasan dan lakukan koreksi/koordinasi |
| `Duplicate` | Composite key cocok dengan row sebelumnya | Jangan membuat pembayaran kedua |
| `Low Confidence` | Hasil AI di bawah threshold | Periksa file asli dan koreksi data secara manual |
| `Failed` | Eksekusi mengalami error | Periksa execution n8n dan konfigurasi credential |

### Koreksi Low Confidence

1. Buka file asli di Drive.
2. Bandingkan dengan row `Low Confidence` di Sheets.
3. Koreksi field invoice sesuai dokumen sumber.
4. Ikuti SOP internal untuk mengubah status menjadi `Pending Approval` bila invoice memang layak diproses.
5. Jangan menghapus row lama jika audit trail masih diperlukan.

## Kolom Utama Sheets

`invoice_id`, `received_at`, `vendor`, `invoice_date`, `invoice_number`, `amount`, `status`, `confidence`, `drive_file_id`, `drive_file_link`, `source`, `approved_at`, `approved_by`, `rejected_at`, `reject_reason`, `reminder_count`, `last_reminder_at`, `created_at`, `updated_at`.

## Batasan yang Perlu Diketahui

- Tidak ada trigger Gmail atau WhatsApp API pada jalur aktif.
- PDF dan WEBP tidak lolos filter file aktif.
- DeepSeek API diperlukan untuk OCR dan normalisasi.
- Foto buram, miring, terpotong, atau berkontras rendah dapat menghasilkan field kosong atau `Low Confidence`.
- Reminder/escalation tersedia sebagai workflow terpisah, tetapi runtime lokal terakhir tidak mengaktifkannya.
- Pesan Telegram hanya berisi ringkasan dan tidak mengirim file invoice.

## Troubleshooting

| Gejala | Pemeriksaan |
|---|---|
| File tidak diproses | Pastikan file berada di folder Drive yang benar dan ekstensi JPG/JPEG/PNG |
| Row masuk `Low Confidence` | Periksa kualitas gambar, field hasil OCR, dan log execution |
| Data vendor/nominal salah | Bandingkan dengan file asli; koreksi row secara manual sesuai SOP |
| Telegram tidak menerima pesan | Pastikan bot tidak diblokir, chat ID benar, dan credential Telegram masih valid |
| DeepSeek gagal | Cek URL endpoint, model, API key, quota, dan ukuran payload gambar |
| Approval ditolak `401` | Cek `WEBHOOK_HMAC_SECRET`, `x-signature`, `x-timestamp`, dan canonical JSON payload |
| Approval tidak diproses | Pastikan invoice masih `Pending Approval` dan invoice ID ditemukan di Sheets |

Untuk setup dan operasi teknis, lihat [SETUP.md](SETUP.md) dan [OPERATIONS.md](OPERATIONS.md).
