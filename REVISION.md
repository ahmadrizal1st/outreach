# 🔍 REVISION — Review Mendalam & Daftar Revisi

> Dokumen ini berisi hasil review mendalam terhadap seluruh codebase project **AI-Powered Client Finder & Outreach System**.
> Setiap temuan dikategorikan berdasarkan prioritas dan area fungsional.
>
> 📅 Tanggal Review: 4 Juni 2026

---

## Daftar Isi

- [1. Scraper — Tidak Fungsional](#1-scraper--tidak-fungsional)
- [2. LLM Provider — Tidak Lengkap](#2-llm-provider--tidak-lengkap)
- [3. Settings — Halaman Kosong](#3-settings--halaman-kosong)
- [4. CRUD Prospect Manual — Belum Ada](#4-crud-prospect-manual--belum-ada)
- [5. Bug & Inkonsistensi Kode](#5-bug--inkonsistensi-kode)
- [6. UI/UX & Frontend](#6-uiux--frontend)
- [7. Database & Migrasi](#7-database--migrasi)
- [8. Keamanan](#8-keamanan)
- [9. Testing](#9-testing)
- [10. DevOps & Deployment](#10-devops--deployment)
- [11. Arsitektur & Kualitas Kode](#11-arsitektur--kualitas-kode)
- [12. Ringkasan Prioritas Revisi](#12-ringkasan-prioritas-revisi)

---

## 1. Scraper — Tidak Fungsional

### 🔴 KRITIS: Scraper Tidak Bisa Dijalankan dari UI

**Masalah:**
- Tombol **"Jalankan Scraper"** di dashboard (`dashboard.html:63`) hanya melakukan `hx-post="/scraper/run"` dengan `hx-swap="none"`, artinya:
  - Tidak ada feedback visual sama sekali ke user (loading, progress, error).
  - User tidak tahu apakah scraper berjalan, gagal, atau sudah selesai.
  - Tidak ada mekanisme **STOP / CANCEL** scraping yang sedang berjalan.
- Endpoint `POST /scraper/run` (`scraper.py:14-19`) menjalankan scraper **secara synchronous** di dalam request handler — ini akan **timeout** karena scraping bisa memakan waktu 5-30 menit.

**File terkait:**
- `app/api/routes/scraper.py` — route handler
- `app/scraper/runner.py` — runner logic
- `app/templates/dashboard.html:63-65` — tombol di UI

**Yang harus diperbaiki:**
1. Scraping harus berjalan sebagai **background task** (menggunakan `asyncio.create_task` atau task queue).
2. Tambahkan endpoint progress yang bisa di-poll oleh frontend (SSE / polling via HTMX).
3. Tambahkan tombol **Stop Scraping** yang bisa membatalkan task yang sedang berjalan.
4. Tampilkan status real-time: jumlah yang sudah di-scrape, sedang berjalan, error, dsb.

---

### 🔴 KRITIS: Tidak Ada Form Input Sebelum Scraping

**Masalah:**
- Di README, disebutkan user bisa input **keyword**, **lokasi**, dan **kategori** sebelum scraping.
- Pada kenyataannya, **tidak ada form scraping di UI**. Scraper langsung membaca dari tabel `scraper_config` di database.
- Endpoint `POST /scraper/config` ada, tapi **tidak ada halaman frontend** yang memanggil endpoint ini.
- Tidak ada halaman khusus scraping (`/scraper`) — hanya tombol di sidebar dashboard tanpa parameter apapun.

**Yang harus diperbaiki:**
1. Buat halaman `/scraper` dengan form input yang berisi:
   - **Keyword** (input text, multi-input): contoh "restoran", "cafe", "salon"
   - **Lokasi/Kota** (input text, multi-input): contoh "Surabaya", "Jakarta Selatan"
   - **Radius/Area** (opsional): sekitar mana pencarian difokuskan
   - **Kategori target** (checkbox/multi-select)
   - **Max per hari** (number input, default 20)
   - **Delay settings** (advanced, collapsible)
2. Form submit → simpan ke `scraper_config` → mulai scraping background task.
3. Tampilkan progress bar dan log real-time di halaman yang sama.

---

### 🟡 SEDANG: Scroll Listing Tanpa Batas

**Masalah:**
- `maps_scraper.py:102-117` — Method `_scroll_listings` tidak memiliki batas maksimal scroll. Jika Google Maps memiliki banyak listing, loop akan berjalan terus.
- Tidak ada timeout atau max iteration untuk loop scroll.

**File terkait:** `app/scraper/maps_scraper.py:102-117`

**Yang harus diperbaiki:**
1. Tambahkan `max_scroll_attempts` (misalnya 20 kali scroll).
2. Tambahkan timeout global untuk seluruh proses scroll (misalnya 60 detik).

---

### 🟡 SEDANG: Deduplicator Membuat Koneksi DB Baru Setiap Kali

**Masalah:**
- `deduplicator.py:10` — Setiap kali `is_duplicate()` dipanggil, dibuat koneksi database baru (`SessionLocal()`), lalu langsung ditutup.
- Dalam satu sesi scraping, ini bisa terjadi 20+ kali — sangat tidak efisien.

**File terkait:** `app/scraper/deduplicator.py`

**Yang harus diperbaiki:**
1. Inject session database dari luar (dependency injection), atau
2. Cache `place_id` yang sudah ada di memory saat awal scraping.

---

### 🟡 SEDANG: Place ID Extraction Tidak Reliable

**Masalah:**
- `maps_scraper.py:33-37` — Place ID diekstrak dengan split `'!'` dari URL Google Maps. Ini sangat fragile karena format URL Google Maps bisa berubah.
- Fallback menggunakan `name + address` sebagai place_id — ini bisa menyebabkan duplikasi jika nama/alamat sedikit berbeda.

**File terkait:** `app/scraper/maps_scraper.py:33-37`

**Yang harus diperbaiki:**
1. Gunakan regex yang lebih robust untuk mengekstrak place ID dari URL.
2. Coba ambil `data-place-id` dari elemen DOM jika tersedia.
3. Tambahkan hash dari beberapa field sebagai alternatif unique ID.

---

### 🟡 SEDANG: Tidak Ada Resume/Checkpoint yang Nyata

**Masalah:**
- README menyebutkan fitur "Resume otomatis jika scraping terputus di tengah jalan".
- Pada kenyataannya, `runner.py` hanya mengecek apakah kombinasi `keyword + city` sudah pernah di-scrape hari ini (`_is_completed`). Ini bukan resume — ini skip.
- Jika scraping terputus di tengah (misalnya listing ke-10 dari 20), **tidak ada cara untuk melanjutkan dari listing ke-10**. Harus mulai dari awal.

**File terkait:** `app/scraper/runner.py:61-69`

**Yang harus diperbaiki:**
1. Simpan progress per-listing (bukan per keyword+city).
2. Tandai listing mana yang sudah di-proses.
3. Implementasi resume yang sesungguhnya berdasarkan bookmark posisi scroll.

---

### 🟢 RENDAH: CSS Selector Google Maps Hardcoded

**Masalah:**
- `detail_parser.py` menggunakan selector seperti `h1.DUwDvf`, `button.DkEaL`, `div.F7nice span`, `div.Nv2PK`.
- Selector ini bisa berubah kapan saja saat Google Maps update UI mereka.

**Yang harus diperbaiki:**
1. Centralize semua selector ke satu file konfigurasi.
2. Tambahkan fallback selector alternatif.
3. Tambahkan logging jika selector tidak ditemukan.

---

## 2. LLM Provider — Tidak Lengkap

### 🔴 KRITIS: Tidak Ada CRUD LLM Provider di Settings UI

**Masalah:**
- Halaman **Settings** (`settings.html`) hanya menampilkan teks placeholder: *"Settings implementation goes here."*
- Endpoint API untuk CRUD provider ada (`/scoring/providers` POST, `/scoring/providers` GET, `/scoring/providers/{id}/toggle` PUT), tapi **tidak ada UI frontend** untuk mengaksesnya.
- User tidak bisa menambah, mengedit, menghapus, atau melihat status provider dari browser.

**File terkait:**
- `app/templates/settings.html` — template kosong (18 baris)
- `app/api/routes/settings.py` — hanya render template kosong
- `app/api/routes/scoring.py:40-73` — API ada tapi tanpa UI

**Yang harus diperbaiki:**
1. Buat halaman Settings yang lengkap dengan tab/section:
   - **LLM Providers**: CRUD penuh (tambah, edit, hapus, toggle aktif/nonaktif)
   - **Scraper Config**: setting default keyword, lokasi, delay
   - **Follow-up Config**: interval hari, max follow-up
   - **Profil Jasa**: nama jasa, layanan, portofolio URL (untuk context AI)
   - **Export Config**: format default, filter default
2. Setiap provider harus memiliki form input:
   - `provider_name` (e.g., groq, gemini, openai, ollama, deepseek)
   - `base_url` (untuk custom/self-hosted endpoint) ← **BELUM ADA DI MODEL**
   - `api_key` (masked input)
   - `model_name`
   - `daily_token_limit`
   - `priority_order`
   - `is_active` (toggle)
   - `custom_headers` atau `payload_template` (untuk provider custom)

---

### 🔴 KRITIS: Model LLMProvider Tidak Punya `base_url`

**Masalah:**
- Model `LLMProvider` di `prospect.py:140-155` tidak memiliki kolom `base_url`.
- Ini berarti tidak bisa support provider custom (Ollama lokal, OpenAI-compatible API, self-hosted LLM, dll).
- `provider.py:60` memanggil `completion(model=f"{provider.provider_name}/{provider.model_name}")` — format ini hanya bekerja untuk provider yang di-support langsung oleh `litellm`.

**File terkait:**
- `app/models/prospect.py:140-155` — model database
- `app/ai/provider.py:59-61` — pemanggilan API

**Yang harus diperbaiki:**
1. Tambahkan kolom di model `LLMProvider`:
   - `base_url` (String, nullable) — untuk custom endpoint
   - `api_type` (String) — "openai", "gemini", "groq", "ollama", "custom"
   - `extra_headers` (String/JSON, nullable) — header tambahan
   - `extra_params` (String/JSON, nullable) — parameter tambahan untuk payload
   - `max_tokens` (Integer, default 1000)
   - `temperature` (Float, default 0.7)
2. Update `provider.py` untuk pass `base_url` dan parameter tambahan ke `litellm.completion()`.

---

### 🔴 KRITIS: Tidak Ada Delete Provider

**Masalah:**
- API hanya punya Create/Update dan Toggle. Tidak ada endpoint DELETE untuk menghapus provider.
- Tidak ada endpoint untuk mengedit detail provider yang sudah ada (hanya overwrite by name).

**File terkait:** `app/api/routes/scoring.py:45-73`

**Yang harus diperbaiki:**
1. Tambahkan `DELETE /scoring/providers/{id}`.
2. Tambahkan `PUT /scoring/providers/{id}` untuk edit individual.
3. Tambahkan `POST /scoring/providers/test` untuk test koneksi sebelum menyimpan.

---

### 🟡 SEDANG: Tidak Ada Pilihan Manual vs Auto di UI

**Masalah:**
- README menyebutkan mode **manual** (pilih provider sendiri) dan **auto** (rotasi random).
- Di kode backend, `LLMProvider.__init__` menerima parameter `manual_provider`, tapi **tidak ada UI** untuk memilih mode ini.
- Di `.env.example` ada `LLM_PROVIDER_MODE=auto` tapi ini **tidak dibaca** oleh kode manapun.

**File terkait:**
- `app/ai/provider.py:10-13` — constructor
- `.env.example:6-7` — env variable tidak dipakai
- Semua route yang memanggil LLM (`messages.py`, `review.py`, `scoring.py`)

**Yang harus diperbaiki:**
1. Tambahkan global setting "LLM Mode" di Settings page (Auto / Manual / Specific Provider).
2. Jika manual, tampilkan dropdown untuk memilih provider.
3. Simpan setting ini di database (tabel baru `app_settings` atau kolom di tabel existing).
4. Route-route yang memanggil LLM harus membaca setting ini.

---

### 🟡 SEDANG: Token Usage Tracking Tidak Tampil di UI

**Masalah:**
- Dashboard (`dashboard.html:71-78`) menampilkan `tokens_used_today` per provider, tapi:
  - Tidak ada grafik/chart penggunaan harian.
  - Tidak ada riwayat 7 hari terakhir (padahal disebutkan di README).
  - Tidak ada peringatan saat mendekati limit.

**Yang harus diperbaiki:**
1. Buat tabel `llm_usage_history` untuk menyimpan riwayat harian.
2. Tampilkan chart penggunaan token 7 hari terakhir di Settings → LLM Usage.
3. Tambahkan notifikasi/badge jika usage mendekati limit (80%+).

---

### 🟡 SEDANG: Inconsistent Provider Constructor

**Masalah:**
- `app/ai/provider.py:10` — `LLMProvider.__init__(self, db: Session, manual_provider=None)` menerima `db` session.
- `app/ai/message_generator.py:11` — `MessageGenerator.__init__` memanggil `LLMProvider(manual_provider)` **tanpa** `db` session. Ini akan **crash** dengan `TypeError`.
- `app/scraper/website_analyzer.py:10` — `WebsiteAnalyzer.__init__` juga memanggil `LLMProvider(manual_provider)` **tanpa** `db`. Crash juga.

**File terkait:**
- `app/ai/provider.py:10` — constructor butuh `db`
- `app/ai/message_generator.py:11` — panggil tanpa `db`
- `app/scraper/website_analyzer.py:10` — panggil tanpa `db`

**Yang harus diperbaiki:**
1. Konsistenkan constructor — semua caller harus pass `db` session.
2. Atau ubah `LLMProvider` untuk bisa membuat session sendiri jika tidak diberikan.

---

## 3. Settings — Halaman Kosong

### 🔴 KRITIS: Settings Adalah Placeholder Kosong

**Masalah:**
- `app/templates/settings.html` hanya berisi 18 baris — teks *"Settings implementation goes here."*
- `app/api/routes/settings.py` hanya render template kosong.
- Seluruh konfigurasi sistem yang seharusnya bisa diatur dari UI **tidak bisa diakses**:
  - LLM Provider management
  - Scraper configuration
  - Follow-up interval settings
  - Profil jasa/agency
  - Preview website settings
  - Export preferences

**File terkait:**
- `app/templates/settings.html`
- `app/api/routes/settings.py`

**Yang harus diperbaiki:**
1. Implementasikan halaman Settings lengkap dengan tab/section berikut:
   - **Profil Jasa** — nama, layanan, portofolio URL, kontak
   - **LLM Provider** — CRUD provider (lihat Bagian 2)
   - **Scraper** — keyword default, lokasi default, delay, max per hari
   - **Follow-up** — interval hari, max follow-up
   - **Preview** — expire days, base URL
   - **General** — mode debug, secret key display
2. Buat model `AppSettings` untuk menyimpan konfigurasi umum.

---

## 4. CRUD Prospect Manual — Belum Ada

### 🔴 KRITIS: Tidak Bisa Tambah Prospect Secara Manual

**Masalah:**
- Semua prospect hanya bisa masuk via scraping. Tidak ada cara untuk:
  - **Tambah** calon client secara manual (input form).
  - **Edit** data prospect yang sudah ada (koreksi nama, telepon, dll).
  - **Delete** prospect individual (bukan blacklist).
  - **Import** data dari CSV/Excel.

**File terkait:**
- `app/api/routes/prospects.py` — hanya ada GET (list, detail, filter)
- `app/templates/prospects/` — hanya list dan detail view

**Yang harus diperbaiki:**
1. **Create**: Tambahkan form di `/prospects/new` untuk input manual:
   - Nama bisnis, kategori, kota, alamat
   - Telepon, email, website
   - Instagram URL
   - Catatan/notes
   - Source: "manual" (untuk membedakan dari scraping)
2. **Edit**: Tambahkan tombol edit di detail prospect.
3. **Delete**: Tambahkan tombol hapus dengan konfirmasi.
4. **Import CSV**: Endpoint dan form upload untuk import bulk dari CSV/Excel.
5. **Merge**: Fitur untuk merge dua prospect yang ternyata sama.

---

## 5. Bug & Inkonsistensi Kode

### 🔴 KRITIS: `MessageGenerator` dan `WebsiteAnalyzer` Akan Crash

**Masalah:**
- `message_generator.py:11`:
  ```python
  self.provider = LLMProvider(manual_provider)  # ← MISSING db argument
  ```
- `website_analyzer.py:10`:
  ```python
  self.provider = LLMProvider(manual_provider)  # ← MISSING db argument
  ```
- `LLMProvider.__init__` di `provider.py:10` membutuhkan `db: Session` sebagai argumen pertama.
- Kedua class ini akan crash dengan `TypeError` saat dipanggil.

**File terkait:**
- `app/ai/message_generator.py:11`
- `app/scraper/website_analyzer.py:10`
- `app/ai/provider.py:10`

**Fix:** Pass `db` session ke constructor `LLMProvider`.

---

### 🔴 KRITIS: `@app.on_event("startup")` Deprecated

**Masalah:**
- `main.py:33-37` menggunakan `@app.on_event("startup")` yang sudah deprecated di FastAPI terbaru.
- Akan muncul deprecation warning dan bisa dihapus di versi mendatang.

**Fix:** Gunakan `lifespan` context manager yang merupakan pola baru FastAPI.

---

### 🟡 SEDANG: Database URL Inkonsisten

**Masalah:**
- `app/core/config.py:8`: `DATABASE_URL = "sqlite:///./data/client_finder.db"`
- `app/core/database.py:11`: `DATABASE_URL = "sqlite:///./data/database.sqlite"`
- `.env.example:20`: `DATABASE_URL=sqlite:///./data/database.sqlite`
- `migrate_db_tone.py:5`: `db_path = os.path.join("data", "client_finder.db")`
- Ada 3 nama database berbeda: `client_finder.db`, `database.sqlite`, `database.db` (di README).

**File terkait:** Multiple files

**Fix:** Standardisasi ke satu nama database. `database.py` yang benar-benar dipakai runtime, jadi pakai `database.sqlite`.

---

### 🟡 SEDANG: Filter di Prospect List Tidak Gabung Multi-Parameter

**Masalah:**
- `prospects/list.html:10-41` — Setiap filter `<select>` dan search memanggil `hx-get="/prospects/filter"` sendiri-sendiri.
- Filter **tidak dikombinasikan**: memilih tier "HOT" lalu memilih kategori "Restoran" akan hanya mengirim parameter terakhir, bukan keduanya.
- `hx-include` atau `hx-vals` tidak dipakai untuk menggabungkan parameter dari semua filter.

**File terkait:** `app/templates/prospects/list.html:10-41`

**Fix:** Gunakan `hx-include` untuk menginclude semua form control dalam satu request, atau wrap semua filter dalam satu `<form>`.

---

### 🟡 SEDANG: Pipeline Board Tidak Tampilkan `priority_tier`

**Masalah:**
- `pipeline.py:61`:
  ```python
  "priority_tier": None, # Should join ProspectScore to get this accurately
  ```
- Pipeline board selalu menampilkan `priority_tier` sebagai `None` karena ProspectScore tidak di-join.

**File terkait:** `app/api/routes/pipeline.py:40-63`

**Fix:** Tambahkan join ke `ProspectScore` di query pipeline board.

---

### 🟡 SEDANG: `website_analyzer.py:65-73` Menggunakan Raw SQL

**Masalah:**
- `analyze_all_unreviewed()` menggunakan raw SQL (`db.execute("""SELECT ..."`)`) alih-alih SQLAlchemy ORM.
- Ini inconsistent dengan seluruh codebase yang menggunakan ORM.
- `self.db` dibuat via `next(get_db())` — ini tidak proper karena generator `get_db()` seharusnya di-yield dan di-close oleh FastAPI dependency injection.

**File terkait:** `app/scraper/website_analyzer.py:63-73`

**Fix:** Gunakan SQLAlchemy ORM query. Gunakan dependency injection untuk db session.

---

### 🟡 SEDANG: `_update_status` di `website_analyzer.py` Tidak Melakukan Apa-apa

**Masalah:**
- `website_analyzer.py:155-162`:
  ```python
  def _update_status(self, prospect_id, status):
      prospect = self._get_prospect(prospect_id)
      if prospect:
          pass  # ← Does nothing!
  ```
- Kode update status di-comment out. Status prospect tidak pernah diupdate setelah review.

**File terkait:** `app/scraper/website_analyzer.py:155-162`

**Fix:** Uncomment dan implementasikan status update yang benar.

---

### 🟢 RENDAH: `bare except` Tanpa Logging

**Masalah:**
- `detail_parser.py` menggunakan `except:` (bare except) tanpa catch exception spesifik dan tanpa logging di seluruh file (line 68, 78, 96, 110, 119, 138).
- Error silently diabaikan, membuat debugging sangat sulit.

**File terkait:** `app/scraper/detail_parser.py`

**Fix:** Gunakan `except Exception as e:` dengan logging.

---

### 🟢 RENDAH: `print()` Digunakan Sebagai Logger

**Masalah:**
- Beberapa file menggunakan `print()` alih-alih `logger`:
  - `website_analyzer.py:49, 92`
  - `message_generator.py:134`
  - `website_checker.py:112`
  - `seed_data.py:59`

**Fix:** Ganti semua `print()` dengan `logger.info()` / `logger.error()`.

---

## 6. UI/UX & Frontend

### 🟡 SEDANG: CSS dan JS Kosong

**Masalah:**
- `app/static/css/style.css` — hanya berisi `/* Custom styles */` (20 bytes).
- `app/static/js/main.js` — hanya berisi `// Main application logic` (26 bytes).
- Seluruh styling bergantung 100% pada **Tailwind CDN** (`<script src="https://cdn.tailwindcss.com">`).
- Tidak ada custom CSS atau JavaScript logic apapun.

**Dampak:**
- Jika CDN down atau offline, seluruh UI akan rusak total (unstyled).
- Tidak ada micro-animations, transitions, atau interaksi JS kustom.
- Tailwind CDN versi production seharusnya tidak dipakai untuk production (hanya development).

**Yang harus diperbaiki:**
1. Install Tailwind CSS secara lokal atau gunakan CSS framework yang di-bundle.
2. Tambahkan custom CSS untuk komponen yang sering dipakai.
3. Tambahkan JavaScript untuk:
   - Loading states / spinners
   - Toast notification
   - Konfirmasi dialog (delete, blacklist)
   - Auto-refresh dashboard stats
   - Copy-to-clipboard untuk pesan WA
   - Drag-and-drop di pipeline board

---

### 🟡 SEDANG: Tidak Ada Loading/Spinner Global

**Masalah:**
- Saat HTMX melakukan request (generate pesan, scan website, jalankan scoring), tidak ada indikator loading global.
- Beberapa tombol menggunakan `onclick="this.innerHTML='...'"` sebagai loading state, tapi ini:
  - Tidak bisa di-reset jika request gagal.
  - Tidak konsisten di semua tombol.
  - Tidak ada timeout handling.

**Yang harus diperbaiki:**
1. Implementasikan HTMX global loading indicator menggunakan `htmx:beforeRequest` dan `htmx:afterRequest`.
2. Gunakan HTMX indicators (`hx-indicator`) untuk per-element loading.
3. Tambahkan error handling dengan `htmx:responseError`.

---

### 🟡 SEDANG: Pipeline Board Tidak Support Drag-and-Drop

**Masalah:**
- README menyebutkan "Bisa drag-and-drop untuk update status".
- Pipeline board saat ini hanya menampilkan kartu statis — **drag-and-drop belum diimplementasi**.

**File terkait:** `app/templates/pipeline/board.html`

**Yang harus diperbaiki:**
1. Implementasi drag-and-drop dengan library seperti SortableJS.
2. Saat card di-drop ke kolom lain, trigger HTMX POST ke `/pipeline/status/{id}`.

---

### 🟡 SEDANG: Tidak Ada Pagination

**Masalah:**
- `prospects.py:18`: `db.query(Prospect).limit(20).all()` — hardcoded 20 tanpa pagination.
- `prospects.py:48`: Filter juga hardcoded `limit(50)`.
- Jika database memiliki ratusan/ribuan prospect, tidak ada cara scroll ke halaman berikutnya.

**Yang harus diperbaiki:**
1. Implementasi pagination (offset-based atau cursor-based).
2. Tampilkan tombol "Load More" atau page numbers di UI.
3. Tambahkan parameter `page` dan `per_page` ke endpoint filter.

---

### 🟡 SEDANG: Navbar Tidak Menunjukkan Active Page

**Masalah:**
- `partials/navbar.html` — semua link navigation memiliki class yang sama. Tidak ada indikator halaman mana yang sedang aktif.

**Fix:** Tambahkan conditional class berdasarkan `request.url.path`.

---

### 🟡 SEDANG: Notifikasi Partial Mungkin Error

**Masalah:**
- `base.html:21` — `{% include 'partials/notification.html' %}` di-include di setiap halaman.
- Template `notification.html` kemungkinan mengacu ke variabel `summary` yang hanya tersedia di dashboard context. Halaman lain yang tidak passing `summary` ke context akan error.

**File terkait:**
- `app/templates/base.html:21`
- `app/templates/partials/notification.html`

**Fix:** Cek apakah variabel `summary` tersedia sebelum render, atau pindahkan notifikasi ke dashboard saja.

---

### 🟢 RENDAH: Tidak Ada Halaman Scraper Dedicated

**Masalah:**
- Link "Scraper" tidak ada di navbar. Hanya tombol kecil di sidebar dashboard.
- Seharusnya ada halaman `/scraper` khusus dengan:
  - Form input keyword & lokasi
  - Riwayat scraping sebelumnya
  - Progress scraping yang sedang berjalan
  - Log detail per sesi scraping

---

### 🟢 RENDAH: Tidak Ada Konfirmasi Dialog

**Masalah:**
- Aksi berbahaya seperti Blacklist, Delete, Skip dilakukan tanpa konfirmasi apapun.
- `pipeline.py:86-91` — Blacklist langsung dieksekusi.

**Fix:** Tambahkan modal konfirmasi sebelum aksi destruktif.

---

### 🟢 RENDAH: Tidak Ada Toast/Snackbar Notification

**Masalah:**
- Banyak aksi HTMX yang menggunakan `hx-swap="none"` — artinya user tidak mendapat feedback apapun setelah aksi berhasil/gagal.
- Misalnya: update status pipeline, simpan notes, save config.

**Fix:** Implementasi toast notification menggunakan HTMX out-of-band swap atau custom JS.

---

### 🟢 RENDAH: Preview Website Belum Diimplementasi

**Masalah:**
- README menyebutkan fitur "Preview Website Lokal" yang bisa generate halaman HTML contoh website.
- Di codebase, ada prompt `preview_content.py`, tapi **tidak ada**:
  - Route untuk generate preview (`/preview/` endpoint).
  - Route untuk serve preview HTML.
  - Template HTML preview per industri (folder `templates/` di root kosong, tidak ada).
  - Logic generator preview.
  - Tracking berapa kali preview dibuka.
  - Auto-expire preview.

**File terkait:**
- `app/ai/prompts/preview_content.py` — prompt ada
- `app/followup/scheduler.py:18-23` — scheduler memanggil `PreviewGenerator` yang **tidak ada**

**Yang harus diperbaiki:**
1. Buat module `app/preview/generator.py`.
2. Buat template HTML per industri.
3. Buat route `/preview/{id}` untuk serve preview.
4. Tracking view count dan last viewed.
5. Implementasi expiry.

---

## 7. Database & Migrasi

### 🟡 SEDANG: Tidak Ada Migration Tool

**Masalah:**
- Database migration dilakukan secara manual dengan script `migrate_db_tone.py` — raw SQL `ALTER TABLE`.
- Tidak ada migration framework (Alembic) yang ter-setup.
- Jika ada perubahan model, user harus menulis migration manual atau reset database.

**Yang harus diperbaiki:**
1. Setup Alembic untuk database migration.
2. Buat initial migration dari model yang ada.
3. Dokumentasikan cara menjalankan migration.

---

### 🟡 SEDANG: Tidak Ada Relationship di Model SQLAlchemy

**Masalah:**
- Model `Prospect`, `ProspectScore`, `Pipeline`, `Message`, dll menggunakan `ForeignKey` tapi **tidak mendefinisikan `relationship()`** di SQLAlchemy.
- Ini berarti setiap query harus melakukan manual join, alih-alih bisa akses via `prospect.scores`, `prospect.pipeline`, dll.

**File terkait:** `app/models/prospect.py`

**Yang harus diperbaiki:**
1. Tambahkan `relationship()` di setiap model yang berelasi.
2. Definisikan `back_populates` untuk bidirectional relationship.

---

### 🟡 SEDANG: Semua Model di Satu File

**Masalah:**
- `app/models/prospect.py` berisi **9 model** (182 baris) — `Prospect`, `ProspectScore`, `WebsiteReview`, `Message`, `Followup`, `Pipeline`, `LLMProvider`, `ScraperConfig`, `ScraperProgress`.
- Ini membuat file sulit di-maintain saat model bertambah.

**Yang harus diperbaiki:**
1. Pisahkan model ke file terpisah per domain:
   - `prospect.py` — Prospect, ProspectScore
   - `pipeline.py` — Pipeline, Followup
   - `message.py` — Message
   - `website.py` — WebsiteReview
   - `llm.py` — LLMProvider
   - `scraper.py` — ScraperConfig, ScraperProgress

---

### 🟢 RENDAH: Tidak Ada Tabel `app_settings`

**Masalah:**
- Konfigurasi global (LLM mode, profil jasa, preview base URL) tidak punya tempat di database.
- Sekarang bergantung pada `.env` yang tidak bisa diubah dari UI.

**Fix:** Buat tabel `app_settings` key-value atau model dedicated.

---

### 🟢 RENDAH: Tidak Ada Tabel `scraper_sessions`

**Masalah:**
- Tidak ada logging detail per sesi scraping: kapan mulai, kapan selesai, berapa lama, error apa saja.
- `ScraperProgress` hanya menyimpan total per keyword+city, tidak per sesi.

**Fix:** Buat model `ScraperSession` untuk tracking detail sesi.

---

## 8. Keamanan

### 🔴 KRITIS: API Key Disimpan Plaintext di Database

**Masalah:**
- `LLMProvider.api_key` disimpan sebagai plaintext di SQLite.
- Jika database bocor, semua API key terekspos.
- Tidak ada enkripsi atau masking di UI.

**Yang harus diperbaiki:**
1. Enkripsi API key sebelum simpan ke database (menggunakan Fernet/AES).
2. Tampilkan API key yang di-mask di UI (misalnya `gsk_xxxxx...xxxx`).
3. Opsi: simpan API key di `.env` saja, database hanya menyimpan referensi.

---

### 🟡 SEDANG: Tidak Ada Autentikasi

**Masalah:**
- Seluruh aplikasi dapat diakses tanpa login — siapa saja yang bisa akses `localhost:8000` bisa melihat semua data, mengubah status, dan menghapus data.
- Meskipun berjalan lokal, ini risiko jika diakses via ngrok atau jaringan LAN.

**Yang harus diperbaiki:**
1. Tambahkan basic auth atau session-based auth (minimal username + password).
2. Proteksi endpoint sensitif (delete, blacklist, config).

---

### 🟡 SEDANG: `verify=False` di HTTP Client

**Masalah:**
- `website_checker.py:31`:
  ```python
  async with httpx.AsyncClient(verify=False) as client:
  ```
- SSL verification dinonaktifkan — ini bisa menjadi attack vector jika ada MITM.

**Fix:** Gunakan `verify=True` sebagai default, dengan fallback `verify=False` hanya jika request pertama gagal.

---

### 🟡 SEDANG: Tidak Ada CSRF Protection

**Masalah:**
- Form POST tidak memiliki CSRF token.
- Meskipun lokal, ini bisa dieksploitasi jika user membuka halaman malicious saat server berjalan.

**Fix:** Implementasikan CSRF token middleware.

---

### 🟡 SEDANG: SQL Injection Potential

**Masalah:**
- `website_analyzer.py:65-73` menggunakan raw SQL tanpa parameterized query:
  ```python
  self.db.execute("""SELECT p.id FROM prospects p...""")
  ```
- Meskipun query ini tidak menerima input user langsung, pola ini berbahaya jika di-copy.

**Fix:** Gunakan SQLAlchemy ORM query.

---

### 🟢 RENDAH: SECRET_KEY di `.env` Tidak Dipakai

**Masalah:**
- `.env.example` menyebutkan `SECRET_KEY` tapi tidak digunakan di kode manapun.

**Fix:** Implement atau hapus dari `.env.example`.

---

## 9. Testing

### 🟡 SEDANG: Test Coverage Sangat Rendah

**Masalah:**
- Hanya ada 5 file test: `test_database.py`, `test_followup.py`, `test_messages.py`, `test_preview.py`, `test_scoring.py`.
- Tidak ada test untuk:
  - Scraper (maps_scraper, detail_parser, normalizer, deduplicator, rate_limiter)
  - API routes (dashboard, prospects, pipeline, settings, export)
  - LLM Provider (fallback logic, token tracking)
  - Website analyzer/checker
  - Export functionality

**Yang harus diperbaiki:**
1. Tambahkan unit test untuk setiap module.
2. Tambahkan integration test untuk API routes.
3. Tambahkan test untuk edge cases:
   - Provider tidak available
   - Database kosong
   - LLM return format yang salah
   - Scraper timeout
4. Setup CI/CD dengan test otomatis.

---

### 🟡 SEDANG: Tidak Ada Fixtures yang Lengkap

**Masalah:**
- `tests/fixtures/` hanya berisi sample prospect (kemungkinan).
- Tidak ada fixture untuk: LLM providers, pipeline data, messages, scraper configs.

**Fix:** Buat fixture lengkap untuk setiap model yang ditest.

---

## 10. DevOps & Deployment

### 🔴 KRITIS: Tidak Ada Docker Configuration

**Masalah:**
- README menyebutkan Docker Compose, tapi **tidak ada** file di repository:
  - `docker-compose.yml` — tidak ada
  - `Dockerfile` — tidak ada
  - `scraper/Dockerfile` — tidak ada (dan folder `scraper/` di root tidak ada)
- Arsitektur README menunjukkan dua service (`app` dan `scraper`) yang berkomunikasi via Docker internal network, tapi implementasi aktual menjalankan **semuanya dalam satu proses** FastAPI.

**Yang harus diperbaiki:**
1. Buat `Dockerfile` untuk aplikasi.
2. Buat `docker-compose.yml` sesuai arsitektur.
3. Atau — update README untuk mencocokkan implementasi aktual (single process).

---

### 🟡 SEDANG: `requirements.txt` Tanpa Version Pinning

**Masalah:**
- `requirements.txt` tidak menyebutkan versi dependency apapun:
  ```
  fastapi
  uvicorn
  sqlalchemy
  playwright
  litellm
  ...
  ```
- Ini bisa menyebabkan build yang tidak reproducible — versi bisa berubah kapan saja.

**Fix:** Pin semua versi dependency (`fastapi==0.115.x`, `sqlalchemy==2.x`, dll).

---

### 🟢 RENDAH: Tidak Ada Health Check Endpoint

**Masalah:**
- Tidak ada endpoint `/health` atau `/api/status` untuk monitoring.

**Fix:** Tambahkan endpoint health check sederhana.

---

## 11. Arsitektur & Kualitas Kode

### 🟡 SEDANG: `next(get_db())` Anti-Pattern

**Masalah:**
- Beberapa class (FollowupTracker, FollowupNotifier, MessageGenerator, WebsiteAnalyzer) menggunakan `self.db = next(get_db())`.
- `get_db()` adalah generator yang seharusnya di-manage oleh FastAPI dependency injection. Memanggil `next()` secara manual:
  - Tidak menjamin `finally: db.close()` dipanggil.
  - Bisa menyebabkan connection leak.
  - Membuat testing lebih sulit (tidak bisa mock dependency).

**File terkait:**
- `app/followup/tracker.py:8`
- `app/followup/notifier.py:8`
- `app/ai/message_generator.py:12`
- `app/scraper/website_analyzer.py:11`

**Yang harus diperbaiki:**
1. Terima `db: Session` sebagai parameter constructor (dependency injection).
2. Atau buat context manager yang proper.

---

### 🟡 SEDANG: Template Path Didefinisikan Berulang-ulang

**Masalah:**
- Setiap route file mendefinisikan `templates_dir` dan `templates` sendiri-sendiri:
  ```python
  templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
  templates = Jinja2Templates(directory=templates_dir)
  ```
- Ini ada di: `dashboard.py`, `settings.py`, `prospects.py`, `pipeline.py`, `review.py`, `messages.py`, `followup.py`, `errors.py`.

**Fix:** Buat satu instance global `templates` dan import di semua route.

---

### 🟡 SEDANG: Tidak Ada Error Handling yang Konsisten di Route

**Masalah:**
- Kebanyakan route tidak memiliki try-catch.
- Jika terjadi error (misalnya LLM timeout, database error), user akan melihat generic error page.
- Tidak ada error message yang actionable.

**Yang harus diperbaiki:**
1. Wrap semua route dalam try-catch yang proper.
2. Return error message yang bisa dipahami user.
3. Untuk HTMX partial response, return HTML error inline.

---

### 🟢 RENDAH: Tidak Ada Type Hints yang Konsisten

**Masalah:**
- Beberapa function punya type hints (`-> dict`, `-> str`), beberapa tidak.
- Tidak konsisten di seluruh codebase.

**Fix:** Tambahkan type hints ke semua function dan parameter.

---

### 🟢 RENDAH: Import di Dalam Function

**Masalah:**
- Beberapa file melakukan import di dalam function body:
  - `scorer.py:107` — `from sqlalchemy.sql import func`
  - `provider.py:106, 117` — `from datetime import datetime`, `from datetime import date`
  - `pipeline.py:33` — `from app.models.prospect import ...`
  - `dashboard.py:80` — `from app.followup.notifier import ...`

**Fix:** Pindahkan semua import ke top-level kecuali ada circular dependency yang valid.

---

## 12. Ringkasan Prioritas Revisi

### 🔴 Prioritas KRITIS (Harus Diperbaiki Segera)

| # | Masalah | Area |
|---|---------|------|
| 1 | Scraper tidak fungsional — tidak ada play/stop/progress | Scraper |
| 2 | Tidak ada form input sebelum scraping (keyword, lokasi) | Scraper |
| 3 | CRUD LLM Provider tidak ada di UI Settings | LLM Provider |
| 4 | Model LLMProvider tidak punya `base_url` & kolom API template | LLM Provider |
| 5 | Halaman Settings adalah placeholder kosong | Settings |
| 6 | CRUD prospect manual tidak ada | Prospect |
| 7 | `MessageGenerator` & `WebsiteAnalyzer` akan crash (missing `db` arg) | Bug |
| 8 | API Key disimpan plaintext di database | Keamanan |
| 9 | Tidak ada Docker config padahal README bilang Docker | DevOps |
| 10 | Preview Website belum diimplementasi sama sekali | Fitur |

### 🟡 Prioritas SEDANG (Perbaiki Sebelum Rilis)

| # | Masalah | Area |
|---|---------|------|
| 11 | Pilihan manual vs auto LLM tidak ada di UI | LLM Provider |
| 12 | Token usage tracking tidak tampil di UI | LLM Provider |
| 13 | Filter prospects tidak gabung multi-parameter | UI/UX |
| 14 | Pipeline board tidak support drag-and-drop | UI/UX |
| 15 | Tidak ada pagination | UI/UX |
| 16 | CSS dan JS file kosong, depend 100% CDN | UI/UX |
| 17 | Tidak ada loading/spinner global | UI/UX |
| 18 | Database URL inkonsisten 3 nama berbeda | Database |
| 19 | Tidak ada migration tool (Alembic) | Database |
| 20 | Tidak ada SQLAlchemy relationship | Database |
| 21 | `next(get_db())` anti-pattern di banyak class | Arsitektur |
| 22 | Test coverage sangat rendah | Testing |
| 23 | Tidak ada autentikasi | Keamanan |
| 24 | `requirements.txt` tanpa version pinning | DevOps |
| 25 | Scroll listing scraper tanpa batas | Scraper |
| 26 | Deduplicator membuat koneksi DB baru tiap kali | Scraper |
| 27 | Place ID extraction tidak reliable | Scraper |
| 28 | Resume scraping tidak nyata | Scraper |
| 29 | Inconsistent LLMProvider constructor | Bug |
| 30 | `_update_status` di website_analyzer tidak melakukan apa-apa | Bug |
| 31 | Pipeline board tidak tampilkan `priority_tier` | Bug |
| 32 | Raw SQL di `website_analyzer.py` | Arsitektur |
| 33 | `@app.on_event("startup")` deprecated | Bug |
| 34 | Notification template mungkin error di halaman non-dashboard | Bug |
| 35 | Template path didefinisikan berulang di setiap route | Arsitektur |
| 36 | Tidak ada CSRF protection | Keamanan |
| 37 | `verify=False` di HTTP client | Keamanan |

### 🟢 Prioritas RENDAH (Nice to Have)

| # | Masalah | Area |
|---|---------|------|
| 38 | CSS selector Google Maps hardcoded | Scraper |
| 39 | `bare except` tanpa logging | Kode |
| 40 | `print()` digunakan sebagai logger | Kode |
| 41 | Tidak ada halaman scraper dedicated | UI/UX |
| 42 | Tidak ada konfirmasi dialog | UI/UX |
| 43 | Tidak ada toast notification | UI/UX |
| 44 | Navbar tidak menunjukkan active page | UI/UX |
| 45 | Tidak ada tabel `app_settings` | Database |
| 46 | Tidak ada tabel `scraper_sessions` | Database |
| 47 | Semua model di satu file | Arsitektur |
| 48 | Tidak ada type hints konsisten | Kode |
| 49 | Import di dalam function body | Kode |
| 50 | Tidak ada health check endpoint | DevOps |
| 51 | SECRET_KEY di .env tidak dipakai | Keamanan |

---

## Total Temuan

| Prioritas | Jumlah |
|-----------|--------|
| 🔴 KRITIS | 10 |
| 🟡 SEDANG | 27 |
| 🟢 RENDAH | 14 |
| **Total** | **51** |

---

> 📌 **Rekomendasi**: Mulai dari perbaikan **KRITIS** terlebih dahulu, terutama:
> 1. Fix bug crash (`MessageGenerator`, `WebsiteAnalyzer`) — agar app bisa jalan.
> 2. Buat form scraping + background task — agar fitur inti bisa dipakai.
> 3. Implementasi Settings UI — agar user bisa konfigurasi system.
> 4. Implementasi CRUD prospect manual — agar user bisa input data tanpa scraping.
> 5. Lengkapi LLM Provider dengan `base_url` dan CRUD penuh — agar support provider custom.

---

*Dokumen ini di-generate berdasarkan analisis kode per 4 Juni 2026.*
