# Panduan Pemakaian: Client Finder

## Gambaran Umum
Client Finder adalah asisten outreach AI yang membantu Anda mencari prospek bisnis lokal di Google Maps, menganalisis website mereka, memberikan skor prospek, dan membuat template pesan WhatsApp yang di-personalisasi secara otomatis.

---

## 1. Setup Awal (Satu Kali)
1. **Konfigurasi Provider AI**:
   - Buka menu **Settings** (ikon gear di pojok kanan atas).
   - Masukkan API Key untuk **Gemini** (Google) atau **Groq** (Meta LLaMA).
   - Pastikan status API Key aktif.
2. **Konfigurasi Pencarian**:
   - Pada halaman **Settings**, buka tab **Scraper Config**.
   - Tentukan **Keywords** (misal: `restoran, klinik, salon`).
   - Tentukan **Kota Target** (misal: `Jakarta Selatan, Bandung`).
   - Tentukan limit pencarian harian agar akun Google Anda aman.

## 2. Alur Kerja Harian (Daily Routine)
Kami menyarankan Anda meluangkan waktu **30 menit setiap pagi** untuk rutinitas berikut:

### Langkah A: Kumpulkan Lead Baru
1. Buka menu **Scraper**.
2. Klik tombol **▶️ Start Scraping**.
3. Sistem akan memanggil Outscraper untuk mencari data dari Google Maps di background.
4. Anda bisa melihat log progres secara live.

### Langkah B: AI Scoring (Penyaringan)
1. Buka menu **Scoring**.
2. Klik **Jalankan Batch Scoring**.
3. AI akan menyeleksi prospek mentah dan membagi mereka menjadi 3 Tier:
   - 🔥 **HOT**: Sangat butuh website / rating tinggi tapi website mati.
   - 🟡 **WARM**: Sudah punya website tapi butuh optimasi SEO/UI.
   - 🔵 **COLD**: Belum menjadi prioritas (atau tidak ada data).

### Langkah C: Tinjau & Follow-up
1. Kembali ke **Dashboard**.
2. Fokus pada prospek berstatus **HOT**. Klik nama bisnis mereka.
3. Di halaman detail prospek:
   - **Tinjau Website**: Klik "Scan Website Sekarang" untuk melihat hasil bedah website.
   - **Preview Website**: Jika mereka tidak punya website, Anda bisa klik "Generate Preview Website" untuk membuat dummy website otomatis.
   - **Pesan WA**: Pilih template pesan (Formal, Kasual, dsb.) yang dibuat AI khusus untuk mereka.
   - Klik **Buka WhatsApp** untuk mengirim pesan.
4. Setelah pesan terkirim, update Pipeline Status di bagian bawah menjadi **"Sudah Dihubungi"**.

### Langkah D: Follow-up Ulang (Otomatis)
- Sistem akan secara otomatis menandai prospek yang butuh di-*follow-up* ulang setelah 3 hari tanpa respon.
- Anda akan melihat indikator ⏰ merah di sebelah nama bisnis di halaman Prospects.

## 3. Fitur Tambahan
- **Ekspor Data**: Anda dapat mengekspor seluruh basis data klien ke format CSV atau Excel langsung dari menu Export yang akan tersedia di pembaruan selanjutnya.
- **Backup**: Jalankan `python scripts/backup_db.py` secara berkala untuk mencadangkan data.
