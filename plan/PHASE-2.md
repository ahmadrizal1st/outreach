## Plan Lengkap Phase 2: Scraping Engine

---

### Tujuan
Sistem bisa otomatis ambil data bisnis dari Google Maps, simpan ke database, dengan mekanisme anti-ban dan resume jika terputus.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── runner.py          # Orkestrasi scraping
│   │   ├── maps_scraper.py    # Core scraping logic
│   │   ├── detail_parser.py   # Ekstrak detail bisnis
│   │   ├── normalizer.py      # Normalisasi data
│   │   ├── deduplicator.py    # Cek duplikat
│   │   └── rate_limiter.py    # Delay & anti-ban
│   └── api/
│       └── routes/
│           └── scraper.py     # API endpoint scraper
```

---

### Alur Scraping

```
Input: keyword + kota dari scraper_config
              ↓
Playwright buka Google Maps
              ↓
Auto scroll load semua listing
              ↓
Ekstrak data tiap listing
              ↓
Klik tiap listing → ambil detail
              ↓
Normalisasi & validasi data
              ↓
Cek duplikat via place_id
              ↓
Simpan ke database
              ↓
Catat progress (resume point)
              ↓
Delay random → listing berikutnya
```

---

### Detail Tiap File

---

#### `rate_limiter.py`
Logic delay dan anti-ban:

```python
import random
import asyncio

class RateLimiter:
    def __init__(self, min_delay=3, max_delay=7):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.daily_count = 0
        self.max_daily = 20

    async def wait(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def wait_between_pages(self):
        # Lebih lama antar halaman
        delay = random.uniform(15, 30)
        await asyncio.sleep(delay)

    async def wait_between_sessions(self):
        # Paling lama antar keyword/kota
        delay = random.uniform(120, 300)
        await asyncio.sleep(delay)

    def is_daily_limit_reached(self):
        return self.daily_count >= self.max_daily

    def increment(self):
        self.daily_count += 1
```

---

#### `normalizer.py`
Normalisasi & validasi data mentah:

```python
import re

class DataNormalizer:

    def normalize_phone(self, phone: str) -> str:
        if not phone:
            return None
        # Hapus semua non-digit
        digits = re.sub(r'\D', '', phone)
        # Konversi ke format internasional
        if digits.startswith('0'):
            digits = '62' + digits[1:]
        elif not digits.startswith('62'):
            digits = '62' + digits
        return digits

    def normalize_rating(self, rating: str) -> float:
        if not rating:
            return None
        try:
            return float(str(rating).replace(',', '.'))
        except:
            return None

    def normalize_review_count(self, count: str) -> int:
        if not count:
            return 0
        digits = re.sub(r'\D', '', str(count))
        return int(digits) if digits else 0

    def normalize_url(self, url: str) -> str:
        if not url:
            return None
        if not url.startswith('http'):
            url = 'https://' + url
        return url.strip()
```

---

#### `deduplicator.py`
Cek duplikat sebelum simpan:

```python
from app.core.database import get_db

class Deduplicator:

    def is_duplicate(self, place_id: str) -> bool:
        db = get_db()
        exists = db.execute(
            "SELECT id FROM prospects WHERE place_id = ?",
            (place_id,)
        ).fetchone()
        return exists is not None

    def get_duplicate_count(self) -> int:
        db = get_db()
        result = db.execute(
            "SELECT COUNT(*) FROM prospects"
        ).fetchone()
        return result[0]
```

---

#### `detail_parser.py`
Ekstrak semua field dari halaman detail bisnis:

```python
from playwright.async_api import Page

class DetailParser:

    async def parse(self, page: Page) -> dict:
        data = {}

        # Nama bisnis
        data['name'] = await self._get_text(
            page, 'h1.DUwDvf'
        )

        # Kategori
        data['category'] = await self._get_text(
            page, 'button.DkEaL'
        )

        # Rating
        data['rating'] = await self._get_text(
            page, 'div.F7nice span'
        )

        # Jumlah review
        data['review_count'] = await self._get_text(
            page, 'div.F7nice span[aria-label]'
        )

        # Alamat
        data['address'] = await self._get_text(
            page, 'button[data-item-id="address"]'
        )

        # Telepon
        data['phone_raw'] = await self._get_text(
            page, 'button[data-item-id^="phone"]'
        )

        # Website
        data['website'] = await self._get_attr(
            page, 'a[data-item-id="authority"]', 'href'
        )

        # Jam operasional
        data['hours'] = await self._get_hours(page)

        # Google Maps URL
        data['google_maps_url'] = page.url

        # Foto
        data['photo_urls'] = await self._get_photos(page)

        return data

    async def _get_text(self, page, selector):
        try:
            el = await page.query_selector(selector)
            if el:
                return await el.inner_text()
        except:
            pass
        return None

    async def _get_attr(self, page, selector, attr):
        try:
            el = await page.query_selector(selector)
            if el:
                return await el.get_attribute(attr)
        except:
            pass
        return None

    async def _get_hours(self, page):
        # Extract jam operasional sebagai JSON string
        try:
            hours = {}
            rows = await page.query_selector_all(
                'table.eK4R0e tr'
            )
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    day = await cells[0].inner_text()
                    time = await cells[1].inner_text()
                    hours[day.strip()] = time.strip()
            return str(hours) if hours else None
        except:
            return None

    async def _get_photos(self, page):
        try:
            photos = []
            imgs = await page.query_selector_all(
                'div.RZ66Rb img'
            )
            for img in imgs[:5]:
                src = await img.get_attribute('src')
                if src:
                    photos.append(src)
            return str(photos)
        except:
            return None
```

---

#### `maps_scraper.py`
Core logic scraping Google Maps:

```python
from playwright.async_api import async_playwright
from app.scraper.detail_parser import DetailParser
from app.scraper.rate_limiter import RateLimiter
from app.scraper.normalizer import DataNormalizer
from app.scraper.deduplicator import Deduplicator

class MapsScraper:

    def __init__(self, config):
        self.config = config
        self.parser = DetailParser()
        self.limiter = RateLimiter(
            config.delay_min_seconds,
            config.delay_max_seconds
        )
        self.normalizer = DataNormalizer()
        self.deduplicator = Deduplicator()
        self.results = []

    async def scrape(self, keyword: str, city: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            context = await browser.new_context(
                # Simpan session
                storage_state="browser_profile.json"
                if self._profile_exists()
                else None,
                viewport={
                    'width': random.randint(1200, 1400),
                    'height': random.randint(800, 900)
                },
                user_agent=self._random_user_agent()
            )
            page = await context.new_page()

            # Buka Google Maps
            query = f"{keyword} {city}"
            url = f"https://www.google.com/maps/search/{query}"
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            # Scroll untuk load semua listing
            await self._scroll_listings(page)

            # Ambil semua listing
            listings = await page.query_selector_all(
                'div.Nv2PK'
            )

            for listing in listings:
                if self.limiter.is_daily_limit_reached():
                    break

                await listing.click()
                await page.wait_for_load_state('networkidle')
                await self.limiter.wait()

                # Parse detail
                raw_data = await self.parser.parse(page)

                # Normalisasi
                data = self._normalize(raw_data)

                # Skip jika duplikat
                if self.deduplicator.is_duplicate(
                    data.get('place_id')
                ):
                    continue

                self.results.append(data)
                self.limiter.increment()

                await self.limiter.wait()

            await browser.close()
            return self.results

    async def _scroll_listings(self, page):
        # Scroll panel kiri untuk load semua listing
        panel = await page.query_selector('div[role="feed"]')
        if panel:
            prev_count = 0
            while True:
                await panel.evaluate(
                    'el => el.scrollTop += 1000'
                )
                await asyncio.sleep(2)
                listings = await page.query_selector_all(
                    'div.Nv2PK'
                )
                if len(listings) == prev_count:
                    break
                prev_count = len(listings)

    def _random_user_agent(self):
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)...",
            "Mozilla/5.0 (X11; Linux x86_64)..."
        ]
        return random.choice(agents)
```

---

#### `runner.py`
Orkestrasi seluruh proses scraping:

```python
from app.scraper.maps_scraper import MapsScraper
from app.core.database import get_db

class ScraperRunner:

    def __init__(self):
        self.db = get_db()
        self.progress = {}

    async def run(self):
        config = self._get_config()

        if not config:
            return {"error": "Konfigurasi scraper belum diset"}

        keywords = config.keywords.split(',')
        cities = config.target_cities.split(',')

        for city in cities:
            for keyword in keywords:

                # Cek resume point
                if self._is_completed(keyword, city):
                    continue

                scraper = MapsScraper(config)
                results = await scraper.scrape(
                    keyword.strip(),
                    city.strip()
                )

                # Simpan ke database
                saved = self._save_results(
                    results, keyword, city
                )

                # Catat progress
                self._mark_completed(keyword, city, saved)

                # Delay antar keyword
                await scraper.limiter.wait_between_sessions()

        return {"status": "done", "total": self._total_today()}

    def _save_results(self, results, keyword, city):
        count = 0
        for data in results:
            try:
                self.db.execute("""
                    INSERT OR IGNORE INTO prospects
                    (place_id, name, category, ...)
                    VALUES (?, ?, ?, ...)
                """, (...))
                self.db.commit()
                count += 1
            except Exception as e:
                continue
        return count

    def _is_completed(self, keyword, city):
        # Cek apakah kombinasi ini sudah di-scrape hari ini
        result = self.db.execute("""
            SELECT id FROM scraper_progress
            WHERE keyword = ? AND city = ?
            AND DATE(scraped_at) = DATE('now')
        """, (keyword, city)).fetchone()
        return result is not None
```

---

### Tabel Tambahan: scraper_progress

```sql
CREATE TABLE scraper_progress (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  keyword     TEXT,
  city        TEXT,
  total_found INTEGER DEFAULT 0,
  total_saved INTEGER DEFAULT 0,
  scraped_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  status      TEXT DEFAULT 'completed'
);
```

---

### API Endpoint Scraper

```python
# app/api/routes/scraper.py

@router.post("/scraper/run")
async def run_scraper():
    runner = ScraperRunner()
    result = await runner.run()
    return result

@router.get("/scraper/status")
async def scraper_status():
    # Return progress hari ini
    ...

@router.get("/scraper/config")
async def get_config():
    ...

@router.post("/scraper/config")
async def save_config(config: ScraperConfigSchema):
    ...
```

---

### Tampilan Dashboard Scraper

```
┌─────────────────────────────────────────┐
│ ⚙️ Scraper Config                        │
│ Keyword : restoran, cafe, salon         │
│ Kota    : Surabaya, Malang              │
│ Max/hari: 20                            │
│ [Edit Config]                           │
├─────────────────────────────────────────┤
│ 📊 Status Hari Ini                      │
│ Terkumpul : 14/20                       │
│ Duplikat  : 3                           │
│ Gagal     : 1                           │
│ Last run  : 09.00 WIB                   │
├─────────────────────────────────────────┤
│ [▶ Jalankan Sekarang] [⏸ Stop]          │
└─────────────────────────────────────────┘
```

---

### Checklist Phase 2

**Setup**
- [x] Install Playwright: `playwright install chromium`
- [x] Buat folder `app/scraper/`
- [x] Buat semua file scraper

**Core Logic**
- [x] `rate_limiter.py` — delay & anti-ban
- [x] `normalizer.py` — normalisasi data
- [x] `deduplicator.py` — cek duplikat
- [x] `detail_parser.py` — ekstrak field
- [x] `maps_scraper.py` — core scraping
- [x] `runner.py` — orkestrasi

**Database**
- [x] Tambah tabel `scraper_progress`
- [x] Test insert data ke tabel `prospects`

**API & Dashboard**
- [x] Endpoint run scraper
- [x] Endpoint status scraper
- [x] Endpoint config scraper
- [x] UI config & status di dashboard

**Testing**
- [x] Test scrape 1 keyword, 1 kota
- [x] Verifikasi data masuk database
- [x] Test resume jika dijalankan ulang
- [x] Test daily limit 20 bisnis
- [x] Test deduplication

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| Setup & install Playwright | 1 jam |
| rate_limiter + normalizer + deduplicator | 2 jam |
| detail_parser | 2–3 jam |
| maps_scraper | 3–4 jam |
| runner + resume logic | 2 jam |
| API endpoint + dashboard UI | 2 jam |
| Testing & debugging | 3–4 jam |
| **Total** | **~3–4 hari** |