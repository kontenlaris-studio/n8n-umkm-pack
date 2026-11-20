# PANDUAN — Paket Workflow n8n untuk UMKM

Empat workflow siap impor. Total waktu setup pertama: ±20 menit.

## Yang Anda butuhkan

1. **n8n** — gratis: n8n Cloud (trial) atau self-host (Docker, 1 perintah). Semua workflow di paket ini memakai node bawaan n8n, tanpa node tambahan.
2. Akun Google (untuk Google Sheets & Gmail), akun Telegram (untuk notifikasi).

## Cara impor (semua workflow sama)

1. Buka n8n → **Workflows → Import from File** → pilih berkas `.json` dari folder `workflows/`.
2. Klik node yang bertanda perlu kredensial → **Create new credential** → login akun Anda.
3. Ganti placeholder: `GANTI_ID_SHEET` (tempel link Google Sheet Anda), `GANTI_CHAT_ID` (ID chat Telegram — cara mendapatkannya di bawah).
4. Klik **Save**, lalu aktifkan tombol **Active** di kanan atas.

## Template Google Sheets

Buat sheet bernama **Orders** dengan kolom baris pertama persis:
`nama | telepon | produk | jumlah | total | status | tanggal | jatuh_tempo | chat_id | diingatkan`

- Workflow 1 menulis order baru (status `BARU`).
- Workflow 2 membaca yang `status = BELUM LUNAS`; isi `jatuh_tempo` format `yyyy-MM-dd` dan `chat_id` Telegram pelanggan bila ada.
- Workflow 3 memfilter kolom `tanggal` yang diawali tanggal hari ini.

Sheet **Leads** untuk workflow 4: `nama | email | telepon | sumber | tanggal`.

## Mendapatkan Chat ID Telegram

1. Buat bot lewat @BotFather (perintah `/newbot`) — atau pakai bot yang sudah Anda punya.
2. Chat bot Anda sekali (kirim "halo").
3. Buka `https://api.telegram.org/bot<TOKEN>/getUpdates` di browser — angka `chat.id` di hasilnya adalah chat ID Anda.

## Mengganti Telegram menjadi WhatsApp (workflow 2)

Node "Kirim Pengingat" bisa diganti **HTTP Request** ke gateway WhatsApp yang Anda pakai (mis. Fonnte/Wablas/Twilio): method POST, header Authorization token gateway, body berisi nomor tujuan & isi pesan yang sama. Sisanya tidak berubah.

## Uji sebelum aktif

Setiap workflow punya tombol **Execute Workflow** di n8n. Untuk webhook, gunakan URL *test* yang ditampilkan node Webhook, kirim contoh JSON:

```json
{"nama": "Budi", "telepon": "0812xxxx", "produk": "Kopi Senja 250g", "jumlah": 2, "total": 98000}
```

Pastikan baris muncul di Sheets dan notifikasi Telegram tiba — baru aktifkan.

## Batasan jujur

- Workflow adalah templat: nama kolom & format tanggal harus sama dengan panduan ini agar filter bekerja.
- Kredensial tidak pernah kami minta — semua login Anda lakukan sendiri di n8n Anda.
- Butuh disesuaikan untuk toko Anda (kolom lain, gateway WA tertentu, marketplace)? Layanan kustomisasi: kontenlaris.studio@gmail.com.
