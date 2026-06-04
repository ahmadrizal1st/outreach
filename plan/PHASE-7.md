## Plan Lengkap Phase 7: Follow-up System

---

### Tujuan
Sistem otomatis flag prospek yang belum dibalas setelah X hari, generate pesan follow-up dengan angle berbeda, dan auto mark COLD setelah maksimal follow-up tercapai.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── followup/
│   │   ├── __init__.py
│   │   ├── scheduler.py        # APScheduler jobs
│   │   ├── tracker.py          # Logic follow-up
│   │   └── notifier.py         # Notifikasi dashboard
│   ├── api/
│   │   └── routes/
│   │       └── followup.py     # API endpoint follow-up
│   └── templates/
│       ├── followup/
│       │   ├── list.html       # Daftar follow-up hari ini
│       │   └── card.html       # Card per follow-up
│       └── partials/
│           └── followup_badge.html  # Badge status
```

---

### Alur Follow-up System

```
Setiap hari (cron job pagi)
              ↓
Cek semua prospect yang sudah dihubungi
tapi belum ada response
              ↓
Hitung selisih hari sejak last contact
              ↓
Jika >= interval hari (default 3)
→ Flag sebagai perlu follow-up
              ↓
Jika followup_count >= max_followup (default 2)
→ Auto mark COLD, stop follow-up
              ↓
Tampilkan di dashboard:
"Follow-up Hari Ini (X)"
              ↓
Generate pesan follow-up dengan angle berbeda
              ↓
Kamu klik WA → send manual
              ↓
Update followup_count + next_followup_date
```

---

### Detail Tiap File

---

#### `tracker.py`
Core logic tracking follow-up:

```python
from datetime import date, datetime, timedelta
from app.core.database import get_db
from app.core.config import settings

class FollowupTracker:

    def __init__(self):
        self.db = get_db()
        self.interval_days = settings.FOLLOWUP_INTERVAL_DAYS
        self.max_followup = settings.MAX_FOLLOWUP

    def check_and_flag(self) -> dict:
        # Ambil semua prospect yang perlu dicek
        prospects = self._get_prospects_to_check()

        flagged = 0
        coldened = 0

        for prospect in prospects:
            pipeline = self._get_pipeline(prospect['id'])

            if not pipeline:
                continue

            # Hitung hari sejak terakhir dihubungi
            last_contact = pipeline.get('last_followup_at') \
                or pipeline.get('contacted_at')

            if not last_contact:
                continue

            last_contact_date = datetime.fromisoformat(
                str(last_contact)
            ).date()
            days_since = (date.today() - last_contact_date).days

            # Cek apakah sudah waktunya follow-up
            if days_since >= self.interval_days:

                # Cek apakah sudah max follow-up
                if pipeline['followup_count'] >= self.max_followup:
                    # Auto mark COLD
                    self._mark_cold(prospect['id'])
                    coldened += 1
                else:
                    # Flag perlu follow-up
                    self._flag_followup(prospect['id'])
                    flagged += 1

        return {
            "flagged": flagged,
            "coldened": coldened,
            "checked": len(prospects)
        }

    def get_followups_today(self) -> list:
        return self.db.execute("""
            SELECT
                p.*,
                pl.followup_count,
                pl.next_followup_date,
                pl.contact_status,
                ps.priority_tier,
                ps.pitch_angle
            FROM prospects p
            JOIN pipeline pl ON p.id = pl.prospect_id
            JOIN prospect_scores ps ON p.id = ps.prospect_id
            WHERE pl.contact_status = 'perlu_followup'
            AND pl.is_blacklisted = FALSE
            AND (
                pl.next_followup_date <= DATE('now')
                OR pl.next_followup_date IS NULL
            )
            ORDER BY ps.priority_score DESC
        """).fetchall()

    def mark_followup_sent(self, prospect_id: int):
        pipeline = self._get_pipeline(prospect_id)
        new_count = (pipeline['followup_count'] or 0) + 1
        next_date = date.today() + timedelta(
            days=self.interval_days
        )

        self.db.execute("""
            UPDATE pipeline
            SET followup_count = ?,
                last_followup_at = CURRENT_TIMESTAMP,
                next_followup_date = ?,
                contact_status = 'sudah_dihubungi'
            WHERE prospect_id = ?
        """, (new_count, next_date, prospect_id))
        self.db.commit()

    def _get_prospects_to_check(self) -> list:
        return self.db.execute("""
            SELECT p.* FROM prospects p
            JOIN pipeline pl ON p.id = pl.prospect_id
            WHERE pl.contact_status IN (
                'sudah_dihubungi',
                'perlu_followup'
            )
            AND pl.is_blacklisted = FALSE
            AND pl.followup_count < ?
        """, (self.max_followup,)).fetchall()

    def _get_pipeline(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM pipeline
            WHERE prospect_id = ?
        """, (prospect_id,)).fetchone()

    def _flag_followup(self, prospect_id: int):
        self.db.execute("""
            UPDATE pipeline
            SET contact_status = 'perlu_followup',
                next_followup_date = DATE('now')
            WHERE prospect_id = ?
        """, (prospect_id,))
        self.db.commit()

    def _mark_cold(self, prospect_id: int):
        self.db.execute("""
            UPDATE pipeline
            SET contact_status = 'tidak_tertarik',
                updated_at = CURRENT_TIMESTAMP
            WHERE prospect_id = ?
        """, (prospect_id,))
        # Update prospect scores tier ke COLD
        self.db.execute("""
            UPDATE prospect_scores
            SET priority_tier = 'COLD'
            WHERE prospect_id = ?
        """, (prospect_id,))
        self.db.commit()
```

---

#### `scheduler.py`
APScheduler untuk cron job harian:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.followup.tracker import FollowupTracker
from app.scraper.runner import ScraperRunner
from app.ai.scorer import BusinessScorer
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def init_scheduler():

    # Job 1: Cek follow-up setiap pagi jam 07.00
    scheduler.add_job(
        func=run_followup_check,
        trigger=CronTrigger(hour=7, minute=0),
        id="followup_check",
        name="Cek Follow-up Harian",
        replace_existing=True
    )

    # Job 2: Scraping setiap pagi jam 08.00
    scheduler.add_job(
        func=run_daily_scraping,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_scraping",
        name="Scraping Harian",
        replace_existing=True
    )

    # Job 3: Auto scoring setiap jam 09.00
    scheduler.add_job(
        func=run_auto_scoring,
        trigger=CronTrigger(hour=9, minute=0),
        id="auto_scoring",
        name="Auto Scoring",
        replace_existing=True
    )

    # Job 4: Reset token provider setiap tengah malam
    scheduler.add_job(
        func=reset_provider_tokens,
        trigger=CronTrigger(hour=0, minute=0),
        id="reset_tokens",
        name="Reset Token Provider",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")

async def run_followup_check():
    try:
        tracker = FollowupTracker()
        result = tracker.check_and_flag()
        logger.info(f"Follow-up check: {result}")
    except Exception as e:
        logger.error(f"Follow-up check error: {e}")

async def run_daily_scraping():
    try:
        runner = ScraperRunner()
        result = await runner.run()
        logger.info(f"Scraping: {result}")
    except Exception as e:
        logger.error(f"Scraping error: {e}")

async def run_auto_scoring():
    try:
        scorer = BusinessScorer()
        result = await scorer.score_all_unscored()
        logger.info(f"Scoring: {result}")
    except Exception as e:
        logger.error(f"Scoring error: {e}")

async def reset_provider_tokens():
    try:
        from app.core.database import get_db
        db = get_db()
        db.execute("""
            UPDATE llm_providers
            SET tokens_used_today = 0,
                is_available = TRUE,
                last_reset_at = DATE('now')
        """)
        db.commit()
        logger.info("Provider tokens reset")
    except Exception as e:
        logger.error(f"Token reset error: {e}")
```

---

#### `notifier.py`
Logic notifikasi untuk dashboard:

```python
from datetime import date
from app.core.database import get_db

class FollowupNotifier:

    def __init__(self):
        self.db = get_db()

    def get_summary(self) -> dict:
        return {
            "followups_today": self._count_followups_today(),
            "contacted_today": self._count_contacted_today(),
            "pending_cold": self._count_pending_cold(),
            "total_active": self._count_active_prospects()
        }

    def _count_followups_today(self) -> int:
        result = self.db.execute("""
            SELECT COUNT(*) FROM pipeline
            WHERE contact_status = 'perlu_followup'
            AND next_followup_date <= DATE('now')
            AND is_blacklisted = FALSE
        """).fetchone()
        return result[0]

    def _count_contacted_today(self) -> int:
        result = self.db.execute("""
            SELECT COUNT(*) FROM pipeline
            WHERE DATE(contacted_at) = DATE('now')
            OR DATE(last_followup_at) = DATE('now')
        """).fetchone()
        return result[0]

    def _count_pending_cold(self) -> int:
        result = self.db.execute("""
            SELECT COUNT(*) FROM pipeline pl
            JOIN prospect_scores ps
            ON pl.prospect_id = ps.prospect_id
            WHERE pl.followup_count >= ?
            AND pl.contact_status != 'tidak_tertarik'
        """, (2,)).fetchone()
        return result[0]

    def _count_active_prospects(self) -> int:
        result = self.db.execute("""
            SELECT COUNT(*) FROM pipeline
            WHERE contact_status NOT IN (
                'tidak_tertarik', 'deal'
            )
            AND is_blacklisted = FALSE
        """).fetchone()
        return result[0]
```

---

### Update Config `.env`

```
# Follow-up Settings
FOLLOWUP_INTERVAL_DAYS=3
MAX_FOLLOWUP=2
```

---

### Update `config.py`

```python
class Settings:
    # Follow-up
    FOLLOWUP_INTERVAL_DAYS: int = int(
        os.getenv("FOLLOWUP_INTERVAL_DAYS", 3)
    )
    MAX_FOLLOWUP: int = int(
        os.getenv("MAX_FOLLOWUP", 2)
    )
```

---

### API Endpoints Follow-up

```python
# app/api/routes/followup.py

@router.get("/followup/today")
async def get_followups_today():
    tracker = FollowupTracker()
    followups = tracker.get_followups_today()
    return templates.TemplateResponse(
        "followup/list.html",
        {"followups": followups}
    )

@router.post("/api/followup/check")
async def run_followup_check():
    tracker = FollowupTracker()
    result = tracker.check_and_flag()
    return result

@router.post("/api/followup/sent/{prospect_id}")
async def mark_followup_sent(prospect_id: int):
    tracker = FollowupTracker()
    tracker.mark_followup_sent(prospect_id)
    return {"status": "updated"}

@router.post("/api/followup/cold/{prospect_id}")
async def manual_mark_cold(prospect_id: int):
    tracker = FollowupTracker()
    tracker._mark_cold(prospect_id)
    return {"status": "marked cold"}

@router.get("/api/followup/summary")
async def followup_summary():
    notifier = FollowupNotifier()
    return notifier.get_summary()
```

---

### Update Pipeline Status

Tambah status baru ke tabel pipeline:

```sql
-- Status yang valid di pipeline:
-- belum_dihubungi
-- sudah_dihubungi
-- perlu_followup   ← BARU
-- dibalas
-- deal
-- tidak_tertarik
```

---

### Templates

#### `followup/list.html`

```html
{% extends 'base.html' %}
{% block content %}

<div class="max-w-3xl mx-auto">

  <div class="flex justify-between items-center mb-4">
    <h1 class="font-bold text-lg">
      🔔 Follow-up Hari Ini
    </h1>
    <span class="bg-orange-100 text-orange-600
                 text-sm px-3 py-1 rounded-full">
      {{ followups | length }} pending
    </span>
  </div>

  {% if not followups %}
  <div class="bg-white rounded-xl p-8 text-center
              text-gray-400 shadow-sm">
    <p class="text-4xl mb-2">✅</p>
    <p>Tidak ada follow-up hari ini</p>
  </div>
  {% endif %}

  {% for prospect in followups %}
  {% include 'followup/card.html' %}
  {% endfor %}

</div>

{% endblock %}
```

---

#### `followup/card.html`

```html
<div id="followup-{{ prospect.id }}"
     class="bg-white rounded-xl p-4 shadow-sm mb-3">

  <!-- Header -->
  <div class="flex justify-between items-start mb-3">
    <div>
      <p class="font-semibold">{{ prospect.name }}</p>
      <p class="text-xs text-gray-500">
        {{ prospect.category }} · {{ prospect.city }}
      </p>
    </div>
    <div class="text-right">
      <span class="text-xs bg-orange-100 text-orange-600
                   px-2 py-0.5 rounded-full">
        Follow-up #{{ prospect.followup_count + 1 }}
      </span>
      <p class="text-xs text-gray-400 mt-1">
        {{ prospect.priority_tier }}
        {{ prospect.priority_score }}
      </p>
    </div>
  </div>

  <!-- Pitch Angle -->
  <div class="bg-indigo-50 rounded-lg p-2 mb-3">
    <p class="text-xs text-indigo-600">
      💡 {{ prospect.pitch_angle }}
    </p>
  </div>

  <!-- Generate & WA -->
  <div id="followup-message-{{ prospect.id }}">
    <button
      hx-post="/api/messages/followup/{{ prospect.id }}"
      hx-vals='{"sequence": {{ prospect.followup_count + 1 }}}'
      hx-target="#followup-message-{{ prospect.id }}"
      hx-swap="innerHTML"
      class="w-full bg-indigo-600 text-white
             text-sm py-2 rounded-lg mb-2">
      ✨ Generate Pesan Follow-up
    </button>
  </div>

  <!-- Actions -->
  <div class="flex gap-2 mt-2">

    <button
      hx-post="/api/followup/sent/{{ prospect.id }}"
      hx-target="#followup-{{ prospect.id }}"
      hx-swap="outerHTML"
      class="flex-1 border text-xs py-2
             rounded-lg text-green-600">
      ✅ Tandai Terkirim
    </button>

    <button
      hx-post="/api/followup/cold/{{ prospect.id }}"
      hx-confirm="Tandai sebagai COLD?"
      hx-target="#followup-{{ prospect.id }}"
      hx-swap="outerHTML"
      class="flex-1 border text-xs py-2
             rounded-lg text-gray-400">
      🧊 Jadikan COLD
    </button>

    <button
      hx-post="/api/pipeline/blacklist/{{ prospect.id }}"
      hx-confirm="Blacklist bisnis ini?"
      hx-target="#followup-{{ prospect.id }}"
      hx-swap="outerHTML"
      class="px-3 border text-xs py-2
             rounded-lg text-red-400">
      🚫
    </button>

  </div>

</div>
```

---

#### `partials/followup_badge.html`

```html
{% if pipeline.contact_status == 'perlu_followup' %}
<span class="bg-orange-100 text-orange-600
             text-xs px-2 py-0.5 rounded-full">
  🔔 Perlu Follow-up #{{ pipeline.followup_count + 1 }}
</span>

{% elif pipeline.contact_status == 'sudah_dihubungi' %}
<span class="bg-blue-100 text-blue-600
             text-xs px-2 py-0.5 rounded-full">
  📨 Sudah Dihubungi
</span>

{% elif pipeline.contact_status == 'dibalas' %}
<span class="bg-green-100 text-green-600
             text-xs px-2 py-0.5 rounded-full">
  💬 Dibalas
</span>

{% elif pipeline.contact_status == 'tidak_tertarik' %}
<span class="bg-gray-100 text-gray-400
             text-xs px-2 py-0.5 rounded-full">
  🧊 COLD
</span>

{% elif pipeline.contact_status == 'deal' %}
<span class="bg-purple-100 text-purple-600
             text-xs px-2 py-0.5 rounded-full">
  🎉 Deal!
</span>
{% endif %}
```

---

### Update Dashboard Utama

Tambah section follow-up di sidebar dashboard:

```html
<!-- Sidebar dashboard.html -->
<div class="bg-white rounded-xl p-4 shadow-sm">

  <div class="flex justify-between items-center mb-3">
    <h3 class="font-semibold text-sm">
      🔔 Follow-up Hari Ini
    </h3>
    <a href="/followup/today"
       class="text-xs text-indigo-600">
      Lihat semua →
    </a>
  </div>

  {% if summary.followups_today == 0 %}
  <p class="text-xs text-gray-400 text-center py-2">
    ✅ Tidak ada follow-up hari ini
  </p>
  {% else %}
  <p class="text-2xl font-bold text-orange-500">
    {{ summary.followups_today }}
  </p>
  <p class="text-xs text-gray-500">
    prospect menunggu follow-up
  </p>
  <a href="/followup/today"
     class="block mt-2 w-full bg-orange-500
            text-white text-xs py-2 rounded-lg
            text-center">
    Lihat & Kirim →
  </a>
  {% endif %}

</div>
```

---

### Checklist Phase 7

**Core Logic**
- [ ] `tracker.py` — flag, check, mark cold
- [ ] `scheduler.py` — cron job harian
- [ ] `notifier.py` — summary notifikasi
- [ ] Logic interval hari configurable
- [ ] Logic max follow-up configurable
- [ ] Auto mark COLD setelah max tercapai

**Scheduler Jobs**
- [ ] Job cek follow-up jam 07.00
- [ ] Job scraping jam 08.00
- [ ] Job auto scoring jam 09.00
- [ ] Job reset token tengah malam
- [ ] Integrasi scheduler ke `main.py`

**Database**
- [ ] Tambah status `perlu_followup` ke pipeline
- [ ] Test update followup_count
- [ ] Test next_followup_date tersimpan
- [ ] Test auto mark COLD

**API Routes**
- [ ] Get follow-up hari ini
- [ ] Run check manual
- [ ] Mark follow-up sent
- [ ] Manual mark COLD
- [ ] Follow-up summary

**Templates**
- [ ] `followup/list.html` — daftar follow-up
- [ ] `followup/card.html` — card per follow-up
- [ ] `partials/followup_badge.html` — badge status
- [ ] Update sidebar dashboard
- [ ] Update `prospects/detail.html`

**Config**
- [ ] Tambah `FOLLOWUP_INTERVAL_DAYS` ke `.env`
- [ ] Tambah `MAX_FOLLOWUP` ke `.env`
- [ ] Update `config.py`

**Testing**
- [ ] Test flag prospect setelah X hari
- [ ] Test auto mark COLD setelah 2x follow-up
- [ ] Test scheduler berjalan sesuai jadwal
- [ ] Test notifikasi muncul di dashboard
- [ ] Test generate pesan follow-up angle berbeda
- [ ] Test manual mark COLD dari dashboard

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| tracker.py | 2–3 jam |
| scheduler.py | 2 jam |
| notifier.py | 1 jam |
| API routes | 1–2 jam |
| Templates & UI | 2–3 jam |
| Config & integrasi | 1 jam |
| Testing & debugging | 2–3 jam |
| **Total** | **~2–3 hari** |