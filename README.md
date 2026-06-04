# 🤖 AI-Powered Client Finder & Outreach System

> Tools untuk penyedia jasa website menemukan, menganalisis, dan menghubungi calon client secara efisien dengan bantuan AI — berjalan 100% lokal via Docker.

---

## Daftar Isi

- [Gambaran Umum](#gambaran-umum)
- [Fitur Utama](#fitur-utama)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Struktur Folder](#struktur-folder)
- [Prasyarat](#prasyarat)
- [Instalasi & Setup](#instalasi--setup)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Sistem](#menjalankan-sistem)
- [Panduan Penggunaan](#panduan-penggunaan)
- [LLM Provider](#llm-provider)
- [Preview Website Lokal](#preview-website-lokal)
- [Pipeline & Status](#pipeline--status)
- [Export Data](#export-data)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Gambaran Umum

Sistem ini dirancang untuk freelancer atau agency web yang ingin mencari calon client secara sistematis. Alur kerjanya:

```
Scraping Google Maps → AI Scoring & Ranking → Review Manual
       ↓
Generate Pesan Personal (via LLM) → Kirim via WhatsApp (manual)
       ↓
Tracking Follow-up → Update Status Pipeline
```

Semua proses berjalan di laptop/PC sendiri tanpa perlu server publik. Data tersimpan lokal di SQLite.

---

## Fitur Utama

### 1. Scraping & Pengumpulan Data
- Scraping bisnis dari Google Maps via Playwright (Chromium headless)
- Batas 20 bisnis/hari dengan delay random antar request (anti-ban)
- Resume otomatis jika scraping terputus di tengah jalan
- Deduplication otomatis — bisnis yang sama tidak masuk dua kali
- Data yang dikumpulkan: nama, kategori, alamat, nomor telepon, website, email, rating, jumlah review, jam buka, foto

### 2. AI Scoring & Ranking
- Setiap bisnis diberi skor prioritas 1–10 oleh AI
- Klasifikasi tier: **HOT** / **WARM** / **COLD**
- AI memberikan alasan skor dan rekomendasi layanan (buat baru / redesign / optimasi)
- Pitch angle terbaik dan relevant keywords per bisnis

### 3. Review Website Manual
- AI scan otomatis: mobile-friendly, SSL, kecepatan, kualitas konten
- Konfirmasi dengan satu klik
- Pilih opportunity: remake / redesign / optimasi / none
- Tambah catatan manual sebagai konteks tambahan untuk generate pesan

### 4. Top 10 Rekomendasi Harian
- Sistem otomatis memilih 10 bisnis terbaik yang belum dihubungi
- Filter otomatis bisnis yang sudah di-blacklist
- Prioritas berdasarkan skor AI + follow-up yang pending
- Notifikasi harian jika belum ada yang dihubungi

### 5. Preview Website Lokal
- Generate halaman HTML preview per bisnis (contoh website yang akan dibuat)
- Template per industri: Restoran, Salon, Klinik, Toko Retail, Penginapan
- Link unik per bisnis: `http://localhost:8000/preview/{id}`
- Tracking berapa kali dibuka dan kapan terakhir dibuka
- Auto upgrade priority score jika preview sering dibuka
- Preview expired otomatis setelah 14 hari (configurable)

### 6. Generate Pesan via LLM
- Pesan pertama dipersonalisasi per bisnis
- Berdasarkan data scraping + analisis website + catatan manual
- Menyertakan link preview website
- Riwayat semua pesan tersimpan

### 7. Follow-up Sequence
- Follow-up otomatis terjadwal setelah X hari tidak dibalas
- Maksimal 2x follow-up (configurable)
- Setiap follow-up menggunakan angle berbeda dari sebelumnya
- Auto mark COLD setelah maksimal follow-up tercapai
- Notifikasi follow-up muncul di dashboard

### 8. WhatsApp Link Siap Klik
- Tombol buka WA dengan pesan sudah terisi otomatis
- Format nomor otomatis: `08xx` → `628xx`
- Tidak ada auto-send — semua manual untuk menghindari risiko

### 9. Pipeline & Status Tracking
- Status per bisnis: `belum_dihubungi` / `dihubungi` / `dibalas` / `deal` / `tidak_tertarik`
- Riwayat semua pesan yang pernah digenerate
- Follow-up sequence tracker
- Blacklist permanen per bisnis

### 10. Multi-Provider LLM
- Provider: **Groq** dan **Gemini Google AI Studio**
- Mode manual: pilih provider sendiri
- Mode auto: rotasi random dari yang tersedia
- Auto fallback jika quota habis
- Tracking token usage per provider per hari

### 11. Export
- Export data pipeline ke CSV / Excel

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                      │
│                                                     │
│  ┌──────────────────────┐  ┌─────────────────────┐  │
│  │  Service: app         │  │  Service: scraper   │  │
│  │  FastAPI + HTMX       │◄─┤  Playwright         │  │
│  │  Port: 8000           │  │  Chromium headless  │  │
│  └──────────┬───────────┘  └─────────────────────┘  │
│             │                                        │
│  ┌──────────▼───────────┐                           │
│  │  Volume: ./data/      │                           │
│  │  - database.db        │                           │
│  │  - previews/          │                           │
│  │  - exports/           │                           │
│  └──────────────────────┘                           │
└─────────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
  Groq API             Gemini Google AI Studio API
  (LLM scoring,        (LLM scoring,
   generate pesan)      generate pesan)
```

**Komunikasi antar service:** `app` memanggil `scraper` via Docker internal network (`http://scraper:8001`). User hanya mengakses `http://localhost:8000`.

---

## Struktur Folder

```
client-finder/
├── docker-compose.yml          # Definisi semua service Docker
├── .env                        # API keys & konfigurasi (JANGAN di-commit)
├── .env.example                # Template .env untuk referensi
├── .gitignore
├── README.md
│
├── app/                        # Service FastAPI utama
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Entry point FastAPI
│   ├── config.py               # Baca konfigurasi dari .env
│   ├── database.py             # Setup SQLite + SQLAlchemy
│   ├── models.py               # Model database (Business, Message, dll)
│   │
│   ├── routers/                # Route handler per fitur
│   │   ├── dashboard.py        # Halaman utama & top 10
│   │   ├── businesses.py       # List, detail, review bisnis
│   │   ├── scraping.py         # Trigger & monitor scraping
│   │   ├── messages.py         # Generate & lihat pesan
│   │   ├── pipeline.py         # Update status, follow-up
│   │   ├── preview.py          # Generate & serve preview HTML
│   │   ├── settings.py         # Konfigurasi sistem
│   │   └── export.py           # Export CSV/Excel
│   │
│   ├── services/               # Business logic
│   │   ├── ai_scoring.py       # Scoring bisnis via LLM
│   │   ├── message_generator.py # Generate pesan via LLM
│   │   ├── followup_scheduler.py# Logika follow-up otomatis
│   │   ├── preview_generator.py # Buat HTML preview
│   │   └── llm_client.py       # Abstraksi Groq + Gemini
│   │
│   ├── templates/              # Jinja2 HTML templates (HTMX)
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── businesses/
│   │   ├── pipeline/
│   │   └── settings/
│   │
│   └── static/                 # CSS, JS, assets
│       ├── css/
│       └── js/
│
├── scraper/                    # Service Playwright
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI mini untuk trigger scraping
│   └── gmaps_scraper.py        # Logika scraping Google Maps
│
├── templates/                  # Template HTML preview per industri
│   ├── restoran.html
│   ├── salon.html
│   ├── klinik.html
│   ├── toko_retail.html
│   └── penginapan.html
│
└── data/                       # Volume Docker (auto-created, jangan edit manual)
    ├── database.db             # SQLite database
    ├── previews/               # File HTML preview yang digenerate
    └── exports/                # File CSV/Excel hasil export
```

---

## Prasyarat

Pastikan hal-hal berikut sudah terinstal di laptop/PC:

| Software | Versi minimum | Cek dengan |
|----------|--------------|------------|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | 2.x (sudah bundled di Docker Desktop) | `docker compose version` |
| Git | any | `git --version` |
| Browser modern | Chrome/Firefox/Edge terbaru | — |

**Spesifikasi laptop yang direkomendasikan:**
- RAM: minimal 4 GB (8 GB lebih nyaman)
- Storage: minimal 2 GB kosong untuk Docker images
- Koneksi internet: diperlukan untuk scraping Google Maps dan memanggil LLM API

**Tidak diperlukan:**
- Python di host machine (semua berjalan di dalam container)
- Node.js
- Server atau VPS

---

## Instalasi & Setup

### Langkah 1: Clone repository

```bash
git clone https://github.com/username/client-finder.git
cd client-finder
```

### Langkah 2: Buat file `.env`

```bash
cp .env.example .env
```

Buka `.env` dan isi API key (lihat bagian [Konfigurasi](#konfigurasi) di bawah).

### Langkah 3: Build Docker images

```bash
docker compose build
```

Proses ini hanya perlu dilakukan sekali, atau setiap kali ada perubahan kode. Chromium akan didownload otomatis saat build — butuh beberapa menit tergantung koneksi internet.

### Langkah 4: Inisialisasi database

```bash
docker compose run --rm app python -c "from database import init_db; init_db()"
```

### Langkah 5: Jalankan sistem

```bash
docker compose up -d
```

Buka browser dan akses: **http://localhost:8000**

---

## Konfigurasi

### File `.env`

```env
# ─── LLM Provider ─────────────────────────────────────────
# Groq — dapatkan API key di: https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# Gemini Google AI Studio — dapatkan API key di: https://aistudio.google.com
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.0-flash

# Mode provider: "auto" (rotasi), "groq", atau "gemini"
LLM_PROVIDER_MODE=auto

# ─── Scraping ─────────────────────────────────────────────
MAX_BUSINESSES_PER_DAY=20
SCRAPE_DELAY_MIN=3        # detik, minimum delay antar request
SCRAPE_DELAY_MAX=8        # detik, maksimum delay antar request

# ─── Follow-up ────────────────────────────────────────────
FOLLOWUP_INTERVAL_DAYS=3  # tunggu X hari sebelum follow-up
MAX_FOLLOWUP_COUNT=2      # maksimal berapa kali follow-up

# ─── Preview Website ──────────────────────────────────────
PREVIEW_EXPIRE_DAYS=14    # preview expired setelah X hari
PREVIEW_BASE_URL=http://localhost:8000  # URL dasar untuk link preview

# ─── Aplikasi ─────────────────────────────────────────────
SECRET_KEY=ganti-dengan-random-string-panjang
DEBUG=false
```

### Cara mendapatkan API key

**Groq (gratis, tidak perlu kartu kredit):**
1. Daftar di [console.groq.com](https://console.groq.com)
2. Masuk ke menu **API Keys**
3. Klik **Create API Key**
4. Copy dan paste ke `GROQ_API_KEY` di `.env`

**Gemini Google AI Studio (gratis, tidak perlu kartu kredit):**
1. Buka [aistudio.google.com](https://aistudio.google.com)
2. Login dengan akun Google
3. Klik **Get API key** di pojok kiri atas
4. Klik **Create API key**
5. Copy dan paste ke `GEMINI_API_KEY` di `.env`

> **Catatan:** Kedua provider menyediakan free tier yang cukup untuk penggunaan harian (scraping 20 bisnis/hari). Tidak perlu memasukkan kartu kredit untuk memulai.

---

## Menjalankan Sistem

### Start sistem

```bash
docker compose up -d
```

Akses di browser: `http://localhost:8000`

### Stop sistem

```bash
docker compose down
```

Data tetap aman karena tersimpan di volume `./data/`.

### Restart setelah update kode

```bash
docker compose down
docker compose build
docker compose up -d
```

### Melihat log

```bash
# Semua service
docker compose logs -f

# Hanya app
docker compose logs -f app

# Hanya scraper
docker compose logs -f scraper
```

### Masuk ke shell container (untuk debugging)

```bash
docker compose exec app bash
docker compose exec scraper bash
```

---

## Panduan Penggunaan

### Alur kerja harian yang direkomendasikan

```
Pagi  →  Buka dashboard, lihat notifikasi follow-up pending
          Kirim follow-up yang sudah jatuh tempo via WA

Siang →  Klik "Scraping Hari Ini" → isi keyword & lokasi → mulai scraping
          Tunggu selesai (20 bisnis ~5-10 menit)

Sore  →  Buka "Top 10 Hari Ini"
          Review bisnis satu per satu
          Generate pesan → klik tombol WA → kirim manual
```

### 1. Setup awal (pertama kali)

1. Buka **Settings** → isi profil jasa Anda (nama, layanan yang ditawarkan, portofolio URL)
2. Pilih mode LLM provider (auto direkomendasikan)
3. Konfirmasi interval follow-up sesuai preferensi

### 2. Scraping bisnis baru

1. Buka menu **Scraping**
2. Isi form:
   - **Keyword**: `restoran`, `salon kecantikan`, `klinik gigi`, dll.
   - **Lokasi**: `Yogyakarta`, `Semarang Tengah`, dll.
   - **Kategori**: pilih dari dropdown
3. Klik **Mulai Scraping**
4. Progress ditampilkan real-time. Bisa ditinggal — scraping jalan di background
5. Jika terputus, klik **Resume** untuk melanjutkan dari posisi terakhir

### 3. Review & scoring

Setelah scraping selesai:
1. Buka **Businesses** → filter by `Belum DiReview`
2. Klik bisnis → AI scoring sudah otomatis digenerate
3. Lihat skor, tier (HOT/WARM/COLD), dan reasoning AI
4. Klik **Review Website** untuk analisis website mereka
5. Pilih opportunity: `remake` / `redesign` / `optimasi` / `none`
6. Tambah catatan manual jika ada info tambahan
7. Klik **Konfirmasi Review**

### 4. Generate & kirim pesan

1. Buka **Top 10 Hari Ini** — sistem sudah pilihkan 10 terbaik
2. Klik bisnis yang ingin dihubungi
3. Klik **Generate Preview** → sistem buat halaman HTML contoh website
4. Klik **Generate Pesan** → LLM buat pesan personal
5. Baca dan edit pesan jika diperlukan
6. Klik **Buka WhatsApp** → WA Web terbuka dengan pesan sudah terisi
7. Kirim manual dari WA
8. Kembali ke sistem → klik **Tandai Sudah Dihubungi**

### 5. Follow-up

- Dashboard menampilkan notifikasi follow-up yang sudah jatuh tempo
- Klik bisnis → **Generate Follow-up** → angle berbeda dari pesan sebelumnya otomatis dibuat
- Kirim via WA seperti biasa
- Setelah 2x follow-up tanpa respons → status otomatis jadi COLD

### 6. Update status setelah respons

- Bisnis balas → klik **Tandai Dibalas**
- Bisnis setuju → klik **Tandai Deal** 🎉
- Bisnis tidak tertarik → klik **Tidak Tertarik** atau **Blacklist**

---

## LLM Provider

### Groq

Groq menggunakan model Llama 3.3 70B yang berjalan di hardware khusus mereka. Keunggulan:
- Sangat cepat (inferensi <1 detik untuk pesan pendek)
- Free tier cukup besar untuk penggunaan harian

**Rate limit free tier (per hari):**
- 14.400 request/hari
- 500.000 token/hari untuk model `llama-3.3-70b-versatile`

### Gemini Google AI Studio

Model Gemini 2.0 Flash dari Google. Keunggulan:
- Context window besar (1 juta token)
- Kemampuan analisis website yang baik

**Rate limit free tier (per menit/hari):**
- 15 request/menit
- 1.500 request/hari
- 1 juta token/menit

### Logika fallback

```
Request masuk
     │
     ▼
Mode = "auto"?
     │
     ├─ Ya → Pilih provider random (Groq atau Gemini)
     │           │
     │           ▼
     │        Request gagal / rate limit?
     │           │
     │           ├─ Ya → Coba provider lain
     │           │           │
     │           │           ▼
     │           │        Kedua provider habis?
     │           │           ├─ Ya → Tampilkan error, coba lagi besok
     │           │           └─ Tidak → Gunakan provider alternatif
     │           └─ Tidak → Gunakan hasilnya ✓
     │
     └─ Tidak → Gunakan provider yang dipilih manual
```

### Monitoring usage

Buka **Settings → LLM Usage** untuk melihat:
- Token yang sudah digunakan hari ini per provider
- Estimasi sisa kuota
- Riwayat penggunaan 7 hari terakhir

---

## Preview Website Lokal

### Cara kerja

Preview adalah halaman HTML statis yang digenerate otomatis berisi:
- Nama dan logo placeholder bisnis
- Konten yang diambil dari data scraping (deskripsi, layanan, foto)
- Desain modern sesuai template industri
- CTA (Call-to-Action) yang relevan

File disimpan di `./data/previews/{id-bisnis}.html` dan dapat diakses via:
```
http://localhost:8000/preview/{id-bisnis}
```

### Keterbatasan lokal

Karena berjalan di localhost, link preview **hanya bisa dibuka dari browser di laptop yang sama**. Link tidak bisa dikirim ke client via WA dan dibuka dari HP mereka.

**Solusi jika ingin mengirim link ke client:**

Gunakan [ngrok](https://ngrok.com) untuk expose localhost ke internet sementara:

```bash
# Install ngrok (gratis, tidak perlu Docker)
# Download di https://ngrok.com/download

# Jalankan tunnel (lakukan sebelum mengirim link ke client)
ngrok http 8000
```

ngrok akan memberikan URL publik sementara seperti `https://abc123.ngrok-free.app`. Ganti `PREVIEW_BASE_URL` di `.env` sementara dengan URL tersebut, lalu generate ulang link preview.

> **Catatan:** URL ngrok gratis berubah setiap kali dijalankan ulang. Ini opsional dan hanya diperlukan jika ingin mengirim link preview ke client.

### Template industri

Template tersedia di folder `./templates/`. Setiap template dapat dikustomisasi:

| File | Industri | Warna dominan |
|------|----------|---------------|
| `restoran.html` | Restoran, Cafe, Warung Makan | Merah hangat |
| `salon.html` | Salon, Barbershop, Spa | Ungu elegan |
| `klinik.html` | Klinik, Dokter, Apotek | Biru bersih |
| `toko_retail.html` | Toko, Butik, Minimarket | Hijau segar |
| `penginapan.html` | Hotel, Guest House, Villa | Emas premium |

Untuk menambah template baru: buat file HTML baru di folder `./templates/` dengan nama kategori (lowercase, underscore), lalu restart container `app`.

---

## Pipeline & Status

### Status bisnis

| Status | Artinya | Aksi selanjutnya |
|--------|---------|------------------|
| `belum_dihubungi` | Belum pernah dikirim pesan | Generate pesan & kirim |
| `dihubungi` | Pesan sudah dikirim, belum ada respons | Tunggu atau follow-up |
| `dibalas` | Ada respons dari bisnis | Tindak lanjut manual |
| `deal` | Sepakat untuk kerja sama | — |
| `tidak_tertarik` | Menolak atau tidak relevan | Bisa di-blacklist |
| `cold` | Sudah max follow-up, tidak ada respons | Auto-set oleh sistem |
| `blacklist` | Tidak akan muncul lagi | — |

### Kanban view

Menu **Pipeline** menampilkan semua bisnis dalam tampilan kanban per status. Bisa drag-and-drop untuk update status, atau klik detail untuk update manual.

### Filter & search

Di halaman **Businesses**, tersedia filter:
- By status
- By tier (HOT / WARM / COLD)
- By kategori bisnis
- By tanggal scraping
- By kota/lokasi
- Search by nama bisnis

---

## Export Data

### Export ke CSV

```
Menu: Pipeline → Export → Download CSV
```

File disimpan di `./data/exports/export_YYYY-MM-DD.csv`

### Kolom yang diekspor

```
id, nama_bisnis, kategori, kota, telepon, website, email,
rating, jumlah_review, skor_ai, tier, status, tanggal_dihubungi,
jumlah_followup, tanggal_deal, catatan
```

### Export ke Excel

```
Menu: Pipeline → Export → Download Excel
```

Format `.xlsx` dengan sheet terpisah per status.

---

## Troubleshooting

### Container tidak bisa start

```bash
# Cek log error
docker compose logs

# Pastikan port 8000 tidak dipakai aplikasi lain
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Scraping gagal / tidak ada hasil

**Kemungkinan penyebab:**
- Google Maps memblokir request → tunggu beberapa jam, coba lagi
- Koneksi internet terputus saat scraping → klik Resume
- Keyword terlalu spesifik → coba keyword yang lebih umum

**Solusi:**
```bash
# Restart service scraper
docker compose restart scraper

# Cek log scraper
docker compose logs scraper
```

### LLM tidak merespons / error

**Kemungkinan penyebab:**
- API key salah atau expired
- Rate limit habis untuk hari ini
- Tidak ada koneksi internet

**Cek di Settings → LLM Usage** untuk melihat status quota. Jika Groq habis, sistem otomatis pindah ke Gemini dan sebaliknya.

**Validasi API key:**
```bash
# Test Groq
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Test Gemini
curl "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY"
```

### Database corrupt / error SQLite

```bash
# Backup database dulu
cp ./data/database.db ./data/database.db.backup

# Masuk ke container dan cek integrity
docker compose exec app python -c "
import sqlite3
conn = sqlite3.connect('/data/database.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(result)
"
```

### Preview website tidak muncul

- Pastikan file ada di `./data/previews/`
- Cek permission folder: `ls -la ./data/previews/`
- Restart container app: `docker compose restart app`

### Reset data (mulai dari awal)

> ⚠️ **PERINGATAN:** Perintah ini menghapus semua data permanen.

```bash
docker compose down
rm -rf ./data/database.db ./data/previews/* ./data/exports/*
docker compose up -d
docker compose run --rm app python -c "from database import init_db; init_db()"
```

---

## FAQ

**Q: Apakah sistem ini aman digunakan? Apakah melanggar ToS Google Maps?**

A: Sistem ini menggunakan delay random dan batas 20 bisnis/hari untuk meminimalisir risiko. Scraping Google Maps berada di area abu-abu dari sisi ToS. Gunakan dengan bijak dan bertanggung jawab. Sistem ini hanya untuk penggunaan pribadi/internal, bukan untuk dijual atau didistribusikan datanya.

---

**Q: Bisakah dijalankan di Windows?**

A: Ya, selama Docker Desktop for Windows sudah terinstal dan WSL2 aktif. Semua command yang ada di README ini berjalan di Terminal/PowerShell.

---

**Q: Data saya aman jika Docker dihapus?**

A: Ya, selama folder `./data/` tidak dihapus. Data SQLite tersimpan sebagai file di host machine (`./data/database.db`), bukan di dalam container. Menghapus container atau image Docker tidak menghapus data.

---

**Q: Bagaimana cara backup data?**

A: Cukup copy folder `./data/`:
```bash
cp -r ./data/ ./data-backup-$(date +%Y%m%d)/
```

---

**Q: Bisakah dijalankan di lebih dari satu laptop?**

A: Bisa, tapi database tidak sinkron otomatis. Untuk penggunaan multi-device, perlu setup server database terpisah (PostgreSQL) — ini bisa ditambahkan sebagai fitur lanjutan.

---

**Q: Apakah preview website bisa dibuka dari HP client?**

A: Secara default tidak, karena berjalan di localhost. Untuk mengirim link ke client, gunakan ngrok (lihat bagian [Preview Website Lokal](#preview-website-lokal)).

---

**Q: Berapa estimasi biaya API per bulan?**

A: Dengan penggunaan 20 bisnis/hari dan free tier Groq + Gemini, biaya bulanan adalah **Rp 0** (gratis). Free tier kedua provider sudah lebih dari cukup untuk skala ini. Biaya baru muncul jika penggunaan meningkat signifikan.

---

**Q: Model LLM apa yang paling bagus untuk generate pesan?**

A: Dari pengujian, `gemini-2.0-flash` menghasilkan pesan yang lebih natural dan kontekstual untuk bahasa Indonesia. `llama-3.3-70b-versatile` lebih cepat. Mode auto akan menggunakan keduanya secara bergantian.

---

## Lisensi

Proyek ini untuk penggunaan pribadi. Tidak untuk didistribusikan atau dijual.

---

*Dibuat dengan ❤️ untuk freelancer & agency web Indonesia*