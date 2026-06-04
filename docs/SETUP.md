# Setup Client Finder

## Kebutuhan Sistem
- Python 3.11+
- pip
- Browser Chromium (otomatis via Playwright)

## Instalasi

1. Pastikan Anda berada di direktori project:
   ```bash
   cd outreach
   ```

2. Buat virtual environment (opsional tapi disarankan):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browser:
   ```bash
   playwright install chromium
   ```

5. Copy file konfigurasi:
   ```bash
   cp .env.example .env
   ```

6. Inisialisasi database awal:
   ```bash
   python main.py --init-db
   ```

7. Masukkan dummy data (opsional, untuk test UI):
   ```bash
   python scripts/seed_data.py
   ```

8. Jalankan server:
   ```bash
   uvicorn main:app --reload
   ```

9. Buka di browser:
   `http://localhost:8000`

## Menjalankan Uji Coba (Tests)
Pastikan dependensi `pytest` sudah terinstal (termasuk `pytest-asyncio`):
```bash
pytest tests/
```
