## Step Development

---

### Phase 1: Foundation (3–4 hari)
**Tujuan: Project bisa jalan secara lokal**

- [ ] Setup struktur folder project
- [ ] Setup virtual environment Python
- [ ] Install semua dependencies
- [ ] Setup database SQLite + schema lengkap
- [ ] Setup FastAPI server dasar
- [ ] Setup HTMX + Tailwind frontend dasar

---

### Phase 2: Scraping Engine (3–4 hari)
**Tujuan: Bisa ambil data dari Google Maps**

- [ ] Setup Playwright
- [ ] Scraper Google Maps dasar
- [ ] Ekstrak semua field data bisnis
- [ ] Deduplication logic
- [ ] Rate limiter & delay random
- [ ] Resume jika scraping terputus
- [ ] Simpan ke database

---

### Phase 3: AI Scoring (2–3 hari)
**Tujuan: Setiap bisnis punya skor prioritas**

- [ ] Setup LiteLLM
- [ ] Konfigurasi Gemini + Groq
- [ ] Logic rotasi & fallback provider
- [ ] Tracking token usage harian
- [ ] Prompt scoring & ranking
- [ ] Simpan hasil scoring ke database

---

### Phase 4: Dashboard Dasar (3–4 hari)
**Tujuan: Bisa lihat dan kelola data**

- [ ] Halaman top 10 rekomendasi harian
- [ ] Halaman daftar semua bisnis
- [ ] Filter: tier, industri, kota, status
- [ ] Detail per bisnis
- [ ] Tombol blacklist
- [ ] Status pipeline per bisnis
- [ ] Notifikasi harian

---

### Phase 5: Review Website (2–3 hari)
**Tujuan: Bisa analisis website calon client**

- [ ] AI scan website otomatis
- [ ] Tampilan hasil scan di dashboard
- [ ] Konfirmasi manual satu klik
- [ ] Input opportunity & catatan manual
- [ ] Simpan hasil review ke database

---

### Phase 6: Generate Pesan (2–3 hari)
**Tujuan: Pesan WA siap pakai per bisnis**

- [ ] Prompt generate pesan pertama
- [ ] Prompt generate follow-up (angle berbeda)
- [ ] Input relevant keywords per bisnis
- [ ] Tampilkan pesan di dashboard
- [ ] WA link siap klik
- [ ] Simpan riwayat pesan

---

### Phase 7: Follow-up System (2–3 hari)
**Tujuan: Tidak ada prospek yang terlupakan**

- [ ] Logic flag follow-up otomatis
- [ ] Konfigurasi interval hari
- [ ] Konfigurasi max follow-up
- [ ] Auto mark COLD
- [ ] Notifikasi follow-up di dashboard
- [ ] Riwayat follow-up per bisnis

---

### Phase 8: Website Preview (3–4 hari)
**Tujuan: Generate preview website per bisnis**

- [ ] Buat 5 template HTML Batch 1
- [ ] Logic generate konten dari data scraping
- [ ] AI generate deskripsi & konten per bisnis
- [ ] Simpan file HTML lokal per bisnis
- [ ] Tombol buka preview di dashboard
- [ ] Tracking preview dibuka
- [ ] Auto expired 14 hari

---

### Phase 9: Polish & Testing (2–3 hari)
**Tujuan: Sistem siap dipakai harian**

- [ ] Export CSV/Excel
- [ ] Error handling lengkap
- [ ] Testing semua fitur
- [ ] Optimasi performa
- [ ] Dokumentasi cara pakai

---

### Ringkasan Waktu

| Phase | Fokus | Estimasi |
|---|---|---|
| 1 | Foundation | 3–4 hari |
| 2 | Scraping | 3–4 hari |
| 3 | AI Scoring | 2–3 hari |
| 4 | Dashboard | 3–4 hari |
| 5 | Review Website | 2–3 hari |
| 6 | Generate Pesan | 2–3 hari |
| 7 | Follow-up | 2–3 hari |
| 8 | Website Preview | 3–4 hari |
| 9 | Polish & Testing | 2–3 hari |
| **Total** | | **~3–4 minggu** |

---

### Milestone Penting

```
Akhir Phase 2 → Sudah bisa scrape data
Akhir Phase 4 → Sudah bisa lihat rekomendasi
Akhir Phase 6 → Sudah bisa kirim pesan WA
Akhir Phase 9 → Sistem lengkap siap pakai
```

---