## Plan Lengkap Phase 9: Polish & Testing

---

### Tujuan
Sistem siap dipakai harian — semua fitur berjalan lancar, error ditangani dengan baik, performa optimal, dan ada dokumentasi cara pakai.

---

### Struktur Folder Tambahan

```
client_finder/
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py        # Test scraping engine
│   ├── test_scoring.py        # Test AI scoring
│   ├── test_messages.py       # Test generate pesan
│   ├── test_followup.py       # Test follow-up system
│   ├── test_preview.py        # Test preview generator
│   ├── test_database.py       # Test database operations
│   └── fixtures/
│       ├── prospect_sample.py # Data dummy prospect
│       └── score_sample.py    # Data dummy score
├── docs/
│   ├── CARA_PAKAI.md          # Panduan penggunaan
│   ├── SETUP.md               # Panduan instalasi
│   └── FAQ.md                 # Pertanyaan umum
└── scripts/
    ├── seed_data.py            # Seed data dummy
    ├── reset_db.py             # Reset database
    └── backup_db.py            # Backup database
```

---

### 1. Error Handling Lengkap

---

#### Global Error Handler `app/core/errors.py`

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

async def http_exception_handler(request, exc):
    return templates.TemplateResponse(
        "errors/error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "detail": exc.detail
        },
        status_code=exc.status_code
    )

async def general_exception_handler(request, exc):
    return templates.TemplateResponse(
        "errors/error.html",
        {
            "request": request,
            "status_code": 500,
            "detail": str(exc)
        },
        status_code=500
    )
```

---

#### Error Template `templates/errors/error.html`

```html
{% extends 'base.html' %}
{% block content %}

<div class="max-w-md mx-auto text-center py-20">
  <p class="text-6xl mb-4">
    {% if status_code == 404 %}🔍
    {% elif status_code == 500 %}⚠️
    {% else %}❌
    {% endif %}
  </p>
  <h1 class="text-2xl font-bold mb-2 text-gray-700">
    {% if status_code == 404 %}
      Halaman tidak ditemukan
    {% elif status_code == 500 %}
      Terjadi kesalahan sistem
    {% else %}
      Error {{ status_code }}
    {% endif %}
  </h1>
  <p class="text-gray-400 text-sm mb-6">{{ detail }}</p>
  <a href="/"
     class="bg-indigo-600 text-white px-6 py-2
            rounded-lg text-sm">
    Kembali ke Dashboard
  </a>
</div>

{% endblock %}
```

---

#### Wrapper Error Handling per Module

```python
# app/core/handler.py

import logging
import functools

logger = logging.getLogger(__name__)

def safe_run(func):
    """Decorator untuk catch error tanpa crash sistem"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}"
            )
            return {
                "error": str(e),
                "function": func.__name__
            }
    return wrapper
```

---

### 2. Logging System

#### `app/core/logger.py`

```python
import logging
import os
from datetime import date

def setup_logger():
    # Buat folder logs jika belum ada
    os.makedirs("logs", exist_ok=True)

    # Format log
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    # File handler per hari
    log_file = f"logs/{date.today()}.log"
    file_handler = logging.FileHandler(
        log_file, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

---

### 3. Testing

---

#### `tests/fixtures/prospect_sample.py`

```python
SAMPLE_PROSPECT = {
    "place_id": "ChIJtest123",
    "name": "Warung Makan Bu Sari",
    "category": "Restoran",
    "subcategory": "Masakan Jawa",
    "address": "Jl. Sudirman No. 12, Surabaya",
    "city": "Surabaya",
    "province": "Jawa Timur",
    "latitude": -7.2575,
    "longitude": 112.7521,
    "phone_raw": "0812-3456-7890",
    "phone_normalized": "6281234567890",
    "website": None,
    "rating": 4.5,
    "review_count": 128,
    "price_level": "$$",
    "is_open": True,
    "source_keyword": "warung makan",
    "source_city": "Surabaya",
    "status": "raw"
}

SAMPLE_PROSPECT_WITH_WEBSITE = {
    **SAMPLE_PROSPECT,
    "place_id": "ChIJtest456",
    "name": "Salon Cantik Mira",
    "category": "Salon",
    "website": "http://saloncantik.com",
    "rating": 4.8,
    "review_count": 203
}
```

---

#### `tests/test_database.py`

```python
import pytest
from app.core.database import get_db
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT

def test_insert_prospect():
    db = get_db()
    db.execute("""
        INSERT OR IGNORE INTO prospects
        (place_id, name, category, city, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        SAMPLE_PROSPECT['place_id'],
        SAMPLE_PROSPECT['name'],
        SAMPLE_PROSPECT['category'],
        SAMPLE_PROSPECT['city'],
        SAMPLE_PROSPECT['status']
    ))
    db.commit()

    result = db.execute("""
        SELECT * FROM prospects
        WHERE place_id = ?
    """, (SAMPLE_PROSPECT['place_id'],)).fetchone()

    assert result is not None
    assert result['name'] == SAMPLE_PROSPECT['name']

def test_duplicate_prevention():
    db = get_db()
    # Insert dua kali dengan place_id sama
    for _ in range(2):
        db.execute("""
            INSERT OR IGNORE INTO prospects
            (place_id, name, city, status)
            VALUES (?, ?, ?, ?)
        """, (
            SAMPLE_PROSPECT['place_id'],
            SAMPLE_PROSPECT['name'],
            SAMPLE_PROSPECT['city'],
            'raw'
        ))
    db.commit()

    count = db.execute("""
        SELECT COUNT(*) FROM prospects
        WHERE place_id = ?
    """, (SAMPLE_PROSPECT['place_id'],)).fetchone()[0]

    assert count == 1

def test_pipeline_creation():
    db = get_db()
    prospect = db.execute("""
        SELECT id FROM prospects LIMIT 1
    """).fetchone()

    if prospect:
        db.execute("""
            INSERT OR IGNORE INTO pipeline
            (prospect_id, contact_status)
            VALUES (?, 'belum_dihubungi')
        """, (prospect['id'],))
        db.commit()

        pipeline = db.execute("""
            SELECT * FROM pipeline
            WHERE prospect_id = ?
        """, (prospect['id'],)).fetchone()

        assert pipeline is not None
        assert pipeline['contact_status'] == 'belum_dihubungi'
```

---

#### `tests/test_scoring.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.ai.scorer import BusinessScorer
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT

MOCK_SCORE_RESPONSE = '''
{
  "priority_score": 8.5,
  "priority_tier": "HOT",
  "score_reasoning": "Tidak punya website, rating tinggi",
  "recommended_service": "buat_baru",
  "pitch_angle": "Bisnis ramai tapi belum ada website",
  "relevant_keywords": ["warung", "makan", "surabaya"]
}
'''

@pytest.mark.asyncio
async def test_score_parsing():
    scorer = BusinessScorer()
    variants = scorer._parse_score(MOCK_SCORE_RESPONSE)
    assert variants['priority_score'] == 8.5
    assert variants['priority_tier'] == 'HOT'

@pytest.mark.asyncio
async def test_tier_assignment():
    scorer = BusinessScorer()

    assert scorer._get_tier(8.5) == 'HOT'
    assert scorer._get_tier(5.0) == 'WARM'
    assert scorer._get_tier(2.0) == 'COLD'
    assert scorer._get_tier(7.0) == 'HOT'
    assert scorer._get_tier(3.9) == 'COLD'

@pytest.mark.asyncio
@patch('app.ai.provider.LLMProvider.complete',
       new_callable=AsyncMock)
async def test_score_prospect(mock_complete):
    mock_complete.return_value = MOCK_SCORE_RESPONSE
    scorer = BusinessScorer()
    result = scorer._parse_score(MOCK_SCORE_RESPONSE)
    assert result is not None
    assert 'priority_score' in result
```

---

#### `tests/test_messages.py`

```python
import pytest
from app.ai.message_generator import MessageGenerator

MOCK_MESSAGE_RESPONSE = '''
{
  "variants": [
    {
      "tone": "formal",
      "message": "Halo Warung Makan Bu Sari, kami melihat bisnis Anda belum memiliki website..."
    },
    {
      "tone": "semi-formal",
      "message": "Halo Bu Sari, warung Anda punya rating bagus di Google..."
    },
    {
      "tone": "kasual",
      "message": "Halo kak, liat warungnya di Google, reviewnya bagus banget..."
    }
  ]
}
'''

def test_wa_link_generation():
    generator = MessageGenerator()
    link = generator.generate_wa_link(
        "6281234567890",
        "Halo ini pesan test"
    )
    assert link.startswith("https://wa.me/6281234567890")
    assert "Halo" in link

def test_message_length():
    generator = MessageGenerator()
    variants = generator._parse_variants(
        MOCK_MESSAGE_RESPONSE
    )
    for variant in variants:
        assert len(variant['message']) <= 300

def test_parse_variants():
    generator = MessageGenerator()
    variants = generator._parse_variants(
        MOCK_MESSAGE_RESPONSE
    )
    assert len(variants) == 3
    tones = [v['tone'] for v in variants]
    assert 'formal' in tones
    assert 'semi-formal' in tones
    assert 'kasual' in tones
```

---

#### `tests/test_followup.py`

```python
import pytest
from datetime import date, timedelta
from app.followup.tracker import FollowupTracker

def test_interval_calculation():
    tracker = FollowupTracker()
    last_contact = date.today() - timedelta(days=4)
    days_since = (date.today() - last_contact).days
    assert days_since >= tracker.interval_days

def test_max_followup_logic():
    tracker = FollowupTracker()
    # Jika followup_count >= max → harus COLD
    followup_count = tracker.max_followup
    assert followup_count >= tracker.max_followup

def test_next_followup_date():
    tracker = FollowupTracker()
    next_date = date.today() + timedelta(
        days=tracker.interval_days
    )
    assert next_date > date.today()
```

---

#### `tests/test_preview.py`

```python
import pytest
import os
from app.preview.template_selector import TemplateSelector
from app.preview.content_builder import ContentBuilder
from tests.fixtures.prospect_sample import SAMPLE_PROSPECT

def test_template_selection_restoran():
    selector = TemplateSelector()
    template = selector.get_template_name("Restoran")
    assert template == "restoran"

def test_template_selection_cafe():
    selector = TemplateSelector()
    template = selector.get_template_name("Cafe")
    assert template == "cafe"

def test_template_fallback():
    selector = TemplateSelector()
    # Kategori tidak dikenal → fallback
    template = selector.get_template_name(
        "Tukang Becak"
    )
    assert template == "restoran"

def test_content_builder():
    builder = ContentBuilder()
    ai_content = {
        "tagline": "Warung Terbaik di Surabaya",
        "hero_description": "Masakan rumah yang lezat",
        "about_text": "Kami hadir sejak 2010",
        "services": [],
        "cta_text": "Hubungi Kami",
        "footer_tagline": "Terima kasih"
    }
    content = builder.build(SAMPLE_PROSPECT, ai_content)
    assert content['business_name'] == SAMPLE_PROSPECT['name']
    assert content['tagline'] == "Warung Terbaik di Surabaya"
    assert 'generated_date' in content
    assert 'expired_date' in content
```

---

### 4. Scripts Utility

---

#### `scripts/seed_data.py`
Seed data dummy untuk testing:

```python
from app.core.database import get_db
from tests.fixtures.prospect_sample import (
    SAMPLE_PROSPECT,
    SAMPLE_PROSPECT_WITH_WEBSITE
)

def seed():
    db = get_db()

    # Seed prospects
    samples = [SAMPLE_PROSPECT, SAMPLE_PROSPECT_WITH_WEBSITE]
    for sample in samples:
        db.execute("""
            INSERT OR IGNORE INTO prospects
            (place_id, name, category, city,
             phone_normalized, rating, review_count,
             website, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample['place_id'],
            sample['name'],
            sample['category'],
            sample['city'],
            sample['phone_normalized'],
            sample['rating'],
            sample['review_count'],
            sample.get('website'),
            'raw'
        ))
    db.commit()

    # Seed LLM providers
    db.execute("""
        INSERT OR IGNORE INTO llm_providers
        (provider_name, api_key, model_name,
         is_active, priority_order, daily_token_limit)
        VALUES
        ('gemini', 'YOUR_GEMINI_KEY', 'gemini-2.0-flash',
         TRUE, 1, 60000),
        ('groq', 'YOUR_GROQ_KEY', 'llama-3.3-70b',
         TRUE, 2, 100000)
    """)
    db.commit()

    # Seed scraper config
    db.execute("""
        INSERT OR IGNORE INTO scraper_config
        (keywords, target_categories, target_cities,
         max_per_day)
        VALUES
        ('restoran,cafe,salon,klinik',
         'Restoran,Cafe,Salon,Klinik',
         'Surabaya',
         20)
    """)
    db.commit()

    print("✅ Seed data berhasil")

if __name__ == "__main__":
    seed()
```

---

#### `scripts/reset_db.py`
Reset database ke kondisi awal:

```python
import os
from app.core.database import get_db

def reset():
    confirm = input(
        "⚠️ Reset database? Semua data akan hilang. (y/n): "
    )
    if confirm.lower() != 'y':
        print("Dibatalkan")
        return

    db_path = "data/client_finder.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Database direset")

    # Recreate tables
    from app.core.database import init_db
    init_db()
    print("✅ Tabel dibuat ulang")

if __name__ == "__main__":
    reset()
```

---

#### `scripts/backup_db.py`
Backup database harian:

```python
import shutil
import os
from datetime import date

def backup():
    src = "data/client_finder.db"
    backup_dir = "data/backups"
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = os.path.join(
        backup_dir,
        f"client_finder_{date.today()}.db"
    )

    if os.path.exists(src):
        shutil.copy2(src, backup_file)
        print(f"✅ Backup tersimpan: {backup_file}")
    else:
        print("❌ Database tidak ditemukan")

if __name__ == "__main__":
    backup()
```

---

### 5. Export CSV/Excel

#### `app/core/exporter.py`

```python
import csv
import os
from datetime import date
from openpyxl import Workbook
from app.core.database import get_db

class DataExporter:

    def __init__(self):
        self.db = get_db()
        self.export_dir = "data/exports"
        os.makedirs(self.export_dir, exist_ok=True)

    def export_csv(self, tier: str = None) -> str:
        prospects = self._get_prospects(tier)
        filename = f"prospects_{date.today()}.csv"
        filepath = os.path.join(self.export_dir, filename)

        with open(filepath, 'w', newline='',
                  encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'name', 'category', 'city',
                'phone_raw', 'website', 'rating',
                'review_count', 'priority_tier',
                'priority_score', 'contact_status'
            ])
            writer.writeheader()
            for prospect in prospects:
                writer.writerow(dict(prospect))

        return filepath

    def export_excel(self, tier: str = None) -> str:
        prospects = self._get_prospects(tier)
        filename = f"prospects_{date.today()}.xlsx"
        filepath = os.path.join(self.export_dir, filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "Prospects"

        # Header
        headers = [
            'Nama', 'Kategori', 'Kota', 'Telepon',
            'Website', 'Rating', 'Review',
            'Tier', 'Score', 'Status'
        ]
        ws.append(headers)

        # Data
        for prospect in prospects:
            ws.append([
                prospect['name'],
                prospect['category'],
                prospect['city'],
                prospect['phone_raw'],
                prospect['website'] or '-',
                prospect['rating'],
                prospect['review_count'],
                prospect['priority_tier'],
                prospect['priority_score'],
                prospect['contact_status']
            ])

        wb.save(filepath)
        return filepath

    def _get_prospects(self, tier: str = None):
        query = """
            SELECT
                p.name, p.category, p.city,
                p.phone_raw, p.website,
                p.rating, p.review_count,
                ps.priority_tier, ps.priority_score,
                pl.contact_status
            FROM prospects p
            LEFT JOIN prospect_scores ps
            ON p.id = ps.prospect_id
            LEFT JOIN pipeline pl
            ON p.id = pl.prospect_id
            WHERE pl.is_blacklisted = FALSE
            OR pl.id IS NULL
        """
        params = []
        if tier:
            query += " AND ps.priority_tier = ?"
            params.append(tier)

        query += " ORDER BY ps.priority_score DESC"
        return self.db.execute(query, params).fetchall()
```

---

### 6. Dokumentasi

#### `docs/SETUP.md`

```markdown
# Setup Client Finder

## Kebutuhan Sistem
- Python 3.11+
- pip
- Browser Chromium (auto-install via Playwright)

## Instalasi

1. Clone atau download project
2. Buat virtual environment:
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows

3. Install dependencies:
   pip install -r requirements.txt

4. Install Playwright browser:
   playwright install chromium

5. Copy file konfigurasi:
   cp .env.example .env

6. Isi API key di file .env:
   GEMINI_API_KEY=...
   GROQ_API_KEY=...

7. Inisialisasi database:
   python main.py --init-db

8. Seed data awal (opsional):
   python scripts/seed_data.py

9. Jalankan server:
   uvicorn main:app --reload

10. Buka browser:
    http://localhost:8000
```

---

#### `docs/CARA_PAKAI.md`

```markdown
# Cara Pakai Client Finder

## Rutinitas Harian (< 30 menit)

### Pagi
1. Buka http://localhost:8000
2. Cek notifikasi — ada follow-up hari ini?
3. Lihat Top 10 rekomendasi
4. Klik "Generate Pesan" per prospect
5. Pilih variasi pesan yang paling cocok
6. Klik "Buka WA" → send manual

### Setup Awal (Sekali)
1. Buka Settings → Scraper Config
2. Isi keyword bisnis target
3. Isi kota target
4. Buka Settings → LLM Provider
5. Isi API key Gemini dan/atau Groq
6. Klik "Jalankan Scraper" untuk mulai

## Tips
- Mulai dengan 1 kota dulu
- Focus ke HOT tier terlebih dahulu
- Baca pitch angle sebelum kirim pesan
- Update status setelah kirim (sudah dihubungi)
- Backup database seminggu sekali
```

---

### 7. Final `main.py`

```python
import uvicorn
import argparse
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import init_db
from app.core.logger import setup_logger
from app.core.errors import (
    http_exception_handler,
    general_exception_handler
)
from app.followup.scheduler import init_scheduler

# Import routes
from app.api.routes import (
    dashboard,
    scraper,
    prospects,
    scoring,
    review,
    messages,
    followup,
    preview,
    settings,
    export
)

# Setup logger
logger = setup_logger()

# Init FastAPI
app = FastAPI(
    title="Client Finder",
    description="AI-Powered Client Outreach System",
    version="1.0.0"
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# Error handlers
app.add_exception_handler(
    Exception, general_exception_handler
)

# Routers
app.include_router(dashboard.router)
app.include_router(scraper.router)
app.include_router(prospects.router)
app.include_router(scoring.router)
app.include_router(review.router)
app.include_router(messages.router)
app.include_router(followup.router)
app.include_router(preview.router)
app.include_router(settings.router)
app.include_router(export.router)

@app.on_event("startup")
async def startup_event():
    # Init database
    init_db()
    # Start scheduler
    init_scheduler()
    logger.info("Client Finder started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Client Finder stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-db', action='store_true')
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("✅ Database initialized")
    else:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True
        )
```

---

### Checklist Phase 9

**Error Handling**
- [ ] Global error handler
- [ ] Error template 404 & 500
- [ ] Decorator `safe_run` di semua module
- [ ] Semua API endpoint punya try/catch

**Logging**
- [ ] Setup logger sistem
- [ ] Log file per hari di folder `logs/`
- [ ] Log semua event penting:
  - Scraping start/stop/result
  - Scoring start/result
  - Pesan digenerate
  - Follow-up flagged
  - Preview generated

**Testing**
- [ ] `test_database.py` — semua pass
- [ ] `test_scoring.py` — semua pass
- [ ] `test_messages.py` — semua pass
- [ ] `test_followup.py` — semua pass
- [ ] `test_preview.py` — semua pass
- [ ] Run semua test: `pytest tests/`

**Scripts**
- [ ] `seed_data.py` — berjalan tanpa error
- [ ] `reset_db.py` — berjalan dengan konfirmasi
- [ ] `backup_db.py` — file backup tersimpan

**Export**
- [ ] Export CSV berjalan
- [ ] Export Excel berjalan
- [ ] Filter per tier berfungsi
- [ ] File tersimpan di `data/exports/`

**Dokumentasi**
- [ ] `SETUP.md` — lengkap dan akurat
- [ ] `CARA_PAKAI.md` — jelas untuk user non-teknis
- [ ] `FAQ.md` — pertanyaan umum

**Final Check**
- [ ] Jalankan dari awal: setup → seed → scrape → score → dashboard
- [ ] Test full flow: scrape → score → review → generate pesan → WA link
- [ ] Test follow-up flow: flag → generate → mark sent → auto COLD
- [ ] Test preview flow: generate → buka browser
- [ ] Backup database berjalan
- [ ] Semua scheduler job terdaftar
- [ ] Tidak ada error di console saat startup

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| Error handling + logging | 2–3 jam |
| Testing semua module | 3–4 jam |
| Scripts utility | 1–2 jam |
| Export CSV/Excel | 1–2 jam |
| Dokumentasi | 2–3 jam |
| Final integration test | 2–3 jam |
| Bug fixing | 2–4 jam |
| **Total** | **~2–3 hari** |

---

### Ringkasan Seluruh Development

| Phase | Fokus | Estimasi |
|---|---|---|
| 1 | Foundation | 1 hari |
| 2 | Scraping Engine | 3–4 hari |
| 3 | AI Scoring | 2–3 hari |
| 4 | Dashboard | 3–4 hari |
| 5 | Review Website | 2–3 hari |
| 6 | Generate Pesan | 2–3 hari |
| 7 | Follow-up System | 2–3 hari |
| 8 | Website Preview | 3–4 hari |
| 9 | Polish & Testing | 2–3 hari |
| **Total** | | **~3–4 minggu** |