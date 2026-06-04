## Plan Lengkap Phase 1: Foundation

---

### Tujuan
Project bisa jalan secara lokal, struktur rapi, siap untuk development phase berikutnya.

---

### Struktur Folder Project

```
client_finder/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── dashboard.py
│   │       ├── scraper.py
│   │       ├── prospects.py
│   │       └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── prospect.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── settings.html
│   └── static/
│       ├── css/
│       └── js/
├── previews/
│   ├── templates/
│   │   ├── restoran/
│   │   ├── cafe/
│   │   ├── salon/
│   │   ├── klinik/
│   │   └── hotel/
│   └── generated/
├── logs/
├── data/
├── tests/
│   └── test_database.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py
```

---

### Database Schema Lengkap

**Tabel 1: prospects**
```sql
CREATE TABLE prospects (
  -- Identitas
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  place_id              TEXT UNIQUE NOT NULL,
  name                  TEXT NOT NULL,
  category              TEXT,
  subcategory           TEXT,

  -- Lokasi
  address               TEXT,
  city                  TEXT,
  province              TEXT,
  latitude              REAL,
  longitude             REAL,
  google_maps_url       TEXT,

  -- Kontak
  phone_raw             TEXT,
  phone_normalized      TEXT,
  website               TEXT,
  email                 TEXT,
  wa_valid              BOOLEAN DEFAULT FALSE,

  -- Reputasi
  rating                REAL,
  review_count          INTEGER,
  price_level           TEXT,

  -- Operasional
  hours                 TEXT,
  is_open               BOOLEAN,
  is_permanently_closed BOOLEAN DEFAULT FALSE,

  -- Media
  photo_urls            TEXT,
  total_photos          INTEGER,

  -- Scraping metadata
  scraped_at            DATETIME,
  source_keyword        TEXT,
  source_city           TEXT,
  status                TEXT DEFAULT 'raw',

  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 2: prospect_scores**
```sql
CREATE TABLE prospect_scores (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),
  priority_score        REAL,
  priority_tier         TEXT,
  score_reasoning       TEXT,
  recommended_service   TEXT,
  pitch_angle           TEXT,
  relevant_keywords     TEXT,
  scored_at             DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 3: website_reviews**
```sql
CREATE TABLE website_reviews (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),

  -- AI Scan
  website_status        TEXT,
  is_mobile_friendly    BOOLEAN,
  has_ssl               BOOLEAN,
  has_ecommerce         BOOLEAN,
  has_booking           BOOLEAN,
  has_contact_form      BOOLEAN,
  speed_score           INTEGER,
  design_quality_score  INTEGER,
  website_issues        TEXT,
  website_summary       TEXT,

  -- Manual Review
  manual_reviewed       BOOLEAN DEFAULT FALSE,
  manual_reviewed_at    DATETIME,
  opportunity_type      TEXT,
  opportunity_notes     TEXT,
  estimated_value       TEXT,
  urgency               TEXT,

  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 4: messages**
```sql
CREATE TABLE messages (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),
  sequence              INTEGER DEFAULT 0,
  content               TEXT,
  provider_used         TEXT,
  model_used            TEXT,
  generated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
  sent_at               DATETIME,
  status                TEXT DEFAULT 'draft'
);
```

**Tabel 5: followups**
```sql
CREATE TABLE followups (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),
  sequence              INTEGER DEFAULT 1,
  scheduled_date        DATE,
  sent_at               DATETIME,
  status                TEXT DEFAULT 'pending',
  notes                 TEXT,
  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 6: pipeline**
```sql
CREATE TABLE pipeline (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),
  contact_status        TEXT DEFAULT 'belum_dihubungi',
  contacted_at          DATETIME,
  last_followup_at      DATETIME,
  followup_count        INTEGER DEFAULT 0,
  next_followup_date    DATE,
  is_blacklisted        BOOLEAN DEFAULT FALSE,
  blacklisted_at        DATETIME,
  blacklist_reason      TEXT,
  notes                 TEXT,
  updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 7: previews**
```sql
CREATE TABLE previews (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  prospect_id           INTEGER REFERENCES prospects(id),
  file_path             TEXT,
  industry_template     TEXT,
  generated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
  expired_at            DATE,
  open_count            INTEGER DEFAULT 0,
  last_opened_at        DATETIME,
  status                TEXT DEFAULT 'active'
);
```

**Tabel 8: llm_providers**
```sql
CREATE TABLE llm_providers (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_name         TEXT NOT NULL,
  api_key               TEXT NOT NULL,
  model_name            TEXT NOT NULL,
  is_active             BOOLEAN DEFAULT TRUE,
  priority_order        INTEGER DEFAULT 1,
  daily_token_limit     INTEGER,
  tokens_used_today     INTEGER DEFAULT 0,
  last_used_at          DATETIME,
  last_reset_at         DATE,
  is_available          BOOLEAN DEFAULT TRUE,
  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Tabel 9: scraper_config**
```sql
CREATE TABLE scraper_config (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  keywords              TEXT,
  target_categories     TEXT,
  target_cities         TEXT,
  max_per_day           INTEGER DEFAULT 20,
  delay_min_seconds     INTEGER DEFAULT 3,
  delay_max_seconds     INTEGER DEFAULT 7,
  is_active             BOOLEAN DEFAULT TRUE,
  last_run_at           DATETIME,
  created_at            DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### Dependencies

**requirements.txt**
```
fastapi
uvicorn
sqlalchemy
playwright
litellm
python-dotenv
apscheduler
httpx
beautifulsoup4
jinja2
python-multipart
openpyxl
```

---

### File .env.example
```
# LLM Providers
GEMINI_API_KEY=
GROQ_API_KEY=

# App Config
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=True

# Scraper Config
MAX_PER_DAY=20
DELAY_MIN=3
DELAY_MAX=7

# Preview Config
PREVIEW_EXPIRED_DAYS=14
PREVIEW_OUTPUT_DIR=previews/generated

# Database
DATABASE_URL=sqlite:///./data/client_finder.db
```

---

### Checklist Phase 1

**Setup Project**
- [x] Buat struktur folder
- [x] Init virtual environment
- [x] Install requirements.txt
- [x] Setup .env dari .env.example
- [x] Setup .gitignore

**Database**
- [x] Setup SQLAlchemy connection
- [x] Buat semua 9 tabel
- [x] Test koneksi database
- [x] Seed data dummy untuk testing

**FastAPI**
- [x] Setup main.py entry point
- [x] Setup router dasar
- [x] Setup Jinja2 template engine
- [x] Setup static files

**Frontend**
- [x] Setup Tailwind via CDN
- [x] Setup HTMX via CDN
- [x] Buat base.html template
- [x] Buat halaman dashboard kosong
- [x] Buat halaman settings kosong

**Testing**
- [ ] Jalankan server: `uvicorn main:app --reload`
- [ ] Akses `http://localhost:8000`
- [ ] Pastikan semua tabel terbuat
- [ ] Pastikan halaman dashboard & settings terbuka

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| Setup folder & environment | 1 jam |
| Database schema & koneksi | 2–3 jam |
| FastAPI setup dasar | 1–2 jam |
| Frontend base template | 1–2 jam |
| Testing & fix | 1 jam |
| **Total** | **~1 hari** |