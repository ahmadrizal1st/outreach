## Plan Lengkap Phase 4: Dashboard

---

### Tujuan
Dashboard web sederhana yang bisa dipakai harian — lihat top 10 rekomendasi, kelola pipeline prospek, dan akses semua fitur dari satu halaman.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── dashboard.py    # Route utama dashboard
│   │       ├── prospects.py    # CRUD prospects
│   │       └── pipeline.py     # Pipeline management
│   ├── templates/
│   │   ├── base.html           # Layout utama
│   │   ├── dashboard.html      # Halaman utama
│   │   ├── prospects/
│   │   │   ├── list.html       # Daftar semua prospects
│   │   │   ├── detail.html     # Detail per prospect
│   │   │   └── filter.html     # Komponen filter
│   │   ├── pipeline/
│   │   │   └── board.html      # Pipeline board
│   │   └── partials/
│   │       ├── navbar.html     # Navigasi
│   │       ├── top10.html      # Komponen top 10
│   │       ├── stats.html      # Statistik ringkasan
│   │       ├── prospect_card.html  # Card per prospect
│   │       └── notification.html  # Notifikasi harian
│   └── static/
│       ├── css/
│       │   └── custom.css
│       └── js/
│           └── app.js
```

---

### Halaman & Komponen

---

### 1. Base Layout `base.html`

```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width">
  <title>Client Finder</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- HTMX -->
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
</head>
<body class="bg-gray-50 min-h-screen">

  <!-- Navbar -->
  {% include 'partials/navbar.html' %}

  <!-- Notifikasi Harian -->
  {% include 'partials/notification.html' %}

  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-4 py-6">
    {% block content %}{% endblock %}
  </main>

</body>
</html>
```

---

### 2. Navbar `partials/navbar.html`

```html
<nav class="bg-white shadow-sm border-b">
  <div class="max-w-7xl mx-auto px-4 py-3
              flex items-center justify-between">

    <!-- Logo -->
    <span class="font-bold text-lg text-indigo-600">
      Client Finder
    </span>

    <!-- Menu -->
    <div class="flex gap-6 text-sm font-medium">
      <a href="/"
         class="text-gray-700 hover:text-indigo-600">
        Dashboard
      </a>
      <a href="/prospects"
         class="text-gray-700 hover:text-indigo-600">
        Prospects
      </a>
      <a href="/pipeline"
         class="text-gray-700 hover:text-indigo-600">
        Pipeline
      </a>
      <a href="/settings"
         class="text-gray-700 hover:text-indigo-600">
        Settings
      </a>
    </div>

  </div>
</nav>
```

---

### 3. Dashboard Utama `dashboard.html`

```html
{% extends 'base.html' %}
{% block content %}

<!-- Stats Row -->
<div class="grid grid-cols-4 gap-4 mb-6">

  <div class="bg-white rounded-xl p-4 shadow-sm">
    <p class="text-xs text-gray-500">Total Prospects</p>
    <p class="text-2xl font-bold">{{ stats.total }}</p>
  </div>

  <div class="bg-red-50 rounded-xl p-4 shadow-sm">
    <p class="text-xs text-red-500">🔥 HOT</p>
    <p class="text-2xl font-bold text-red-600">
      {{ stats.hot }}
    </p>
  </div>

  <div class="bg-yellow-50 rounded-xl p-4 shadow-sm">
    <p class="text-xs text-yellow-500">🟡 WARM</p>
    <p class="text-2xl font-bold text-yellow-600">
      {{ stats.warm }}
    </p>
  </div>

  <div class="bg-blue-50 rounded-xl p-4 shadow-sm">
    <p class="text-xs text-blue-500">Dihubungi Hari Ini</p>
    <p class="text-2xl font-bold text-blue-600">
      {{ stats.contacted_today }}/10
    </p>
  </div>

</div>

<!-- Main Grid -->
<div class="grid grid-cols-3 gap-6">

  <!-- Top 10 Rekomendasi — 2/3 width -->
  <div class="col-span-2">
    {% include 'partials/top10.html' %}
  </div>

  <!-- Sidebar — 1/3 width -->
  <div class="space-y-4">

    <!-- Follow-up Hari Ini -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <h3 class="font-semibold text-sm mb-3">
        🔔 Follow-up Hari Ini
      </h3>
      {% for f in followups_today %}
      <div class="border-b py-2 text-sm">
        <p class="font-medium">{{ f.name }}</p>
        <p class="text-gray-500 text-xs">
          Follow-up #{{ f.sequence }}
        </p>
        <a href="{{ f.wa_link }}"
           target="_blank"
           class="text-green-600 text-xs font-medium">
          Buka WA →
        </a>
      </div>
      {% endfor %}
    </div>

    <!-- Scraper Status -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <h3 class="font-semibold text-sm mb-3">
        ⚙️ Scraper Hari Ini
      </h3>
      <p class="text-sm text-gray-600">
        Terkumpul:
        <span class="font-bold">
          {{ scraper.today }}/{{ scraper.max }}
        </span>
      </p>
      <button
        hx-post="/api/scraper/run"
        hx-swap="none"
        class="mt-2 w-full bg-indigo-600 text-white
               text-xs py-2 rounded-lg">
        ▶ Jalankan Scraper
      </button>
    </div>

    <!-- Provider Status -->
    <div class="bg-white rounded-xl p-4 shadow-sm">
      <h3 class="font-semibold text-sm mb-3">
        🤖 LLM Provider
      </h3>
      {% for p in providers %}
      <div class="flex justify-between text-xs py-1">
        <span>{{ p.provider_name }}</span>
        <span class="text-gray-500">
          {{ p.tokens_used_today }}
          /{{ p.daily_token_limit }}
        </span>
      </div>
      {% endfor %}
    </div>

  </div>
</div>

{% endblock %}
```

---

### 4. Top 10 Component `partials/top10.html`

```html
<div class="bg-white rounded-xl shadow-sm p-4">

  <div class="flex justify-between items-center mb-4">
    <h2 class="font-semibold">
      🎯 Top 10 Rekomendasi Hari Ini
    </h2>
    <button
      hx-post="/api/scoring/run"
      hx-swap="none"
      class="text-xs bg-indigo-100 text-indigo-600
             px-3 py-1 rounded-full">
      Refresh Scoring
    </button>
  </div>

  {% for prospect in top10 %}
  <div class="border rounded-xl p-4 mb-3
              hover:border-indigo-300 transition">

    <!-- Header -->
    <div class="flex justify-between items-start mb-2">
      <div>
        <span class="font-semibold">{{ prospect.name }}</span>
        <span class="text-xs text-gray-500 ml-2">
          {{ prospect.category }}
        </span>
      </div>
      <!-- Tier Badge -->
      {% if prospect.tier == 'HOT' %}
      <span class="bg-red-100 text-red-600
                   text-xs px-2 py-1 rounded-full">
        🔥 HOT {{ prospect.score }}
      </span>
      {% elif prospect.tier == 'WARM' %}
      <span class="bg-yellow-100 text-yellow-600
                   text-xs px-2 py-1 rounded-full">
        🟡 WARM {{ prospect.score }}
      </span>
      {% endif %}
    </div>

    <!-- Info -->
    <div class="text-xs text-gray-500 mb-2 space-y-1">
      <p>📍 {{ prospect.city }}</p>
      <p>⭐ {{ prospect.rating }}
         ({{ prospect.review_count }} review)</p>
      <p>🌐
        {% if prospect.website %}
          Ada website
        {% else %}
          <span class="text-red-500">
            Tidak ada website
          </span>
        {% endif %}
      </p>
      <p class="text-indigo-600 italic">
        💡 {{ prospect.pitch_angle }}
      </p>
    </div>

    <!-- Actions -->
    <div class="flex gap-2 mt-3">

      <!-- Buka WA -->
      <a href="{{ prospect.wa_link }}"
         target="_blank"
         class="flex-1 bg-green-500 text-white
                text-xs py-2 rounded-lg text-center">
        📱 Buka WA
      </a>

      <!-- Detail -->
      <a href="/prospects/{{ prospect.id }}"
         class="flex-1 border text-xs py-2
                rounded-lg text-center text-gray-600">
        Lihat Detail
      </a>

      <!-- Skip -->
      <button
        hx-post="/api/pipeline/skip/{{ prospect.id }}"
        hx-swap="outerHTML"
        hx-target="closest div.border"
        class="px-3 border text-xs py-2
               rounded-lg text-gray-400">
        Skip
      </button>

      <!-- Blacklist -->
      <button
        hx-post="/api/pipeline/blacklist/{{ prospect.id }}"
        hx-confirm="Blacklist bisnis ini?"
        hx-swap="outerHTML"
        hx-target="closest div.border"
        class="px-3 border text-xs py-2
               rounded-lg text-red-400">
        🚫
      </button>

    </div>
  </div>
  {% endfor %}

</div>
```

---

### 5. Halaman Detail Prospect `prospects/detail.html`

```html
{% extends 'base.html' %}
{% block content %}

<div class="max-w-3xl mx-auto space-y-4">

  <!-- Header -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <div class="flex justify-between items-start">
      <div>
        <h1 class="text-xl font-bold">{{ prospect.name }}</h1>
        <p class="text-gray-500 text-sm">
          {{ prospect.category }} · {{ prospect.city }}
        </p>
      </div>
      <span class="bg-red-100 text-red-600
                   px-3 py-1 rounded-full text-sm">
        🔥 HOT {{ score.priority_score }}
      </span>
    </div>
  </div>

  <!-- Info Bisnis -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">📋 Info Bisnis</h2>
    <div class="grid grid-cols-2 gap-3 text-sm">
      <div>
        <p class="text-gray-500">Telepon</p>
        <p class="font-medium">{{ prospect.phone_raw }}</p>
      </div>
      <div>
        <p class="text-gray-500">Rating</p>
        <p class="font-medium">
          ⭐ {{ prospect.rating }}
          ({{ prospect.review_count }})
        </p>
      </div>
      <div>
        <p class="text-gray-500">Website</p>
        <p class="font-medium">
          {{ prospect.website or 'Tidak ada' }}
        </p>
      </div>
      <div>
        <p class="text-gray-500">Alamat</p>
        <p class="font-medium">{{ prospect.address }}</p>
      </div>
    </div>
  </div>

  <!-- AI Analysis -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">🤖 AI Analysis</h2>
    <div class="space-y-3 text-sm">
      <div class="bg-indigo-50 rounded-lg p-3">
        <p class="text-xs text-indigo-500 mb-1">
          Pitch Angle
        </p>
        <p>{{ score.pitch_angle }}</p>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <p class="text-xs text-gray-500 mb-1">Reasoning</p>
        <p>{{ score.score_reasoning }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">
          Layanan Rekomendasi
        </p>
        <span class="bg-green-100 text-green-700
                     text-xs px-2 py-1 rounded-full">
          {{ score.recommended_service }}
        </span>
      </div>
    </div>
  </div>

  <!-- Website Review -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">🌐 Review Website</h2>
    {% if review %}
    <div class="space-y-2 text-sm">
      <p>Mobile Friendly:
        {{ '✅' if review.is_mobile_friendly else '❌' }}
      </p>
      <p>SSL: {{ '✅' if review.has_ssl else '❌' }}</p>
      <p>Opportunity:
        <span class="font-medium">
          {{ review.opportunity_type }}
        </span>
      </p>
      <p class="text-gray-600">{{ review.opportunity_notes }}</p>
    </div>
    {% else %}
    <button
      hx-post="/api/review/{{ prospect.id }}"
      hx-swap="outerHTML"
      class="w-full bg-indigo-600 text-white
             py-2 rounded-lg text-sm">
      🔍 Scan Website Sekarang
    </button>
    {% endif %}
  </div>

  <!-- Pesan & WA Link -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">💬 Pesan Outreach</h2>
    {% if message %}
    <div class="bg-gray-50 rounded-lg p-3 text-sm mb-3">
      {{ message.content }}
    </div>
    <div class="flex gap-2">
      <a href="{{ wa_link }}"
         target="_blank"
         class="flex-1 bg-green-500 text-white
                py-2 rounded-lg text-sm text-center">
        📱 Buka WA
      </a>
      <button
        hx-post="/api/messages/regenerate/{{ prospect.id }}"
        hx-swap="outerHTML"
        class="flex-1 border py-2 rounded-lg
               text-sm text-gray-600">
        🔄 Generate Ulang
      </button>
    </div>
    {% else %}
    <button
      hx-post="/api/messages/generate/{{ prospect.id }}"
      hx-swap="outerHTML"
      class="w-full bg-indigo-600 text-white
             py-2 rounded-lg text-sm">
      ✨ Generate Pesan
    </button>
    {% endif %}
  </div>

  <!-- Riwayat Pesan -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">📜 Riwayat Pesan</h2>
    {% for msg in message_history %}
    <div class="border-b py-3 text-sm">
      <div class="flex justify-between text-xs
                  text-gray-500 mb-1">
        <span>Follow-up #{{ msg.sequence }}</span>
        <span>{{ msg.generated_at }}</span>
      </div>
      <p class="text-gray-700">{{ msg.content }}</p>
      <span class="text-xs text-green-600">
        {{ msg.status }}
      </span>
    </div>
    {% endfor %}
  </div>

  <!-- Pipeline Status -->
  <div class="bg-white rounded-xl p-6 shadow-sm">
    <h2 class="font-semibold mb-4">📊 Pipeline Status</h2>
    <div class="flex gap-2 flex-wrap">
      {% for status in pipeline_statuses %}
      <button
        hx-post="/api/pipeline/status/{{ prospect.id }}"
        hx-vals='{"status": "{{ status.value }}"}'
        hx-swap="none"
        class="px-3 py-1 rounded-full text-xs border
          {% if current_status == status.value %}
            bg-indigo-600 text-white border-indigo-600
          {% else %}
            text-gray-600
          {% endif %}">
        {{ status.label }}
      </button>
      {% endfor %}
    </div>
    <textarea
      hx-post="/api/pipeline/notes/{{ prospect.id }}"
      hx-trigger="change"
      class="w-full mt-3 border rounded-lg p-2
             text-sm text-gray-600"
      placeholder="Catatan...">
      {{ pipeline.notes }}
    </textarea>
  </div>

</div>

{% endblock %}
```

---

### 6. Halaman Daftar Prospects `prospects/list.html`

```html
{% extends 'base.html' %}
{% block content %}

<!-- Filter Bar -->
<div class="bg-white rounded-xl p-4 shadow-sm mb-4">
  <div class="flex gap-3 flex-wrap">

    <!-- Filter Tier -->
    <select
      hx-get="/api/prospects"
      hx-trigger="change"
      hx-target="#prospect-list"
      name="tier"
      class="border rounded-lg px-3 py-2 text-sm">
      <option value="">Semua Tier</option>
      <option value="HOT">🔥 HOT</option>
      <option value="WARM">🟡 WARM</option>
      <option value="COLD">🔵 COLD</option>
    </select>

    <!-- Filter Industri -->
    <select
      name="category"
      class="border rounded-lg px-3 py-2 text-sm">
      <option value="">Semua Industri</option>
      <option>Restoran</option>
      <option>Cafe</option>
      <option>Salon</option>
      <option>Klinik</option>
      <option>Hotel</option>
    </select>

    <!-- Filter Status -->
    <select
      name="status"
      class="border rounded-lg px-3 py-2 text-sm">
      <option value="">Semua Status</option>
      <option value="belum_dihubungi">Belum Dihubungi</option>
      <option value="sudah_dihubungi">Sudah Dihubungi</option>
      <option value="dibalas">Dibalas</option>
      <option value="deal">Deal ✅</option>
    </select>

    <!-- Search -->
    <input
      type="text"
      name="search"
      placeholder="Cari nama bisnis..."
      hx-get="/api/prospects"
      hx-trigger="keyup changed delay:500ms"
      hx-target="#prospect-list"
      class="border rounded-lg px-3 py-2 text-sm
             flex-1 min-w-48">

  </div>
</div>

<!-- Prospect List -->
<div id="prospect-list" class="space-y-3">
  {% include 'partials/prospect_card.html' %}
</div>

{% endblock %}
```

---

### 7. Pipeline Board `pipeline/board.html`

```html
{% extends 'base.html' %}
{% block content %}

<div class="grid grid-cols-5 gap-4">

  {% for column in pipeline_columns %}
  <div class="bg-gray-100 rounded-xl p-3">

    <h3 class="font-semibold text-sm mb-3 text-center">
      {{ column.label }}
      <span class="bg-white px-2 py-0.5 rounded-full
                   text-xs ml-1">
        {{ column.count }}
      </span>
    </h3>

    {% for prospect in column.prospects %}
    <div class="bg-white rounded-lg p-3 mb-2
                shadow-sm text-xs">
      <p class="font-medium">{{ prospect.name }}</p>
      <p class="text-gray-500">{{ prospect.category }}</p>
      <p class="text-gray-500">{{ prospect.city }}</p>
      {% if prospect.next_followup_date %}
      <p class="text-orange-500 mt-1">
        📅 Follow-up: {{ prospect.next_followup_date }}
      </p>
      {% endif %}
      <a href="/prospects/{{ prospect.id }}"
         class="text-indigo-600 mt-1 block">
        Lihat Detail →
      </a>
    </div>
    {% endfor %}

  </div>
  {% endfor %}

</div>

{% endblock %}
```

---

### API Endpoints Dashboard

```python
# app/api/routes/dashboard.py

@router.get("/")
async def dashboard():
    # Render dashboard utama
    stats = get_dashboard_stats()
    top10 = get_top10_prospects()
    followups_today = get_followups_today()
    return templates.TemplateResponse(
        "dashboard.html",
        {"stats": stats, "top10": top10, ...}
    )

# app/api/routes/prospects.py

@router.get("/prospects")
async def list_prospects(
    tier: str = None,
    category: str = None,
    status: str = None,
    search: str = None
):
    ...

@router.get("/prospects/{id}")
async def prospect_detail(id: int):
    ...

# app/api/routes/pipeline.py

@router.post("/api/pipeline/skip/{id}")
async def skip_prospect(id: int):
    ...

@router.post("/api/pipeline/blacklist/{id}")
async def blacklist_prospect(id: int):
    ...

@router.post("/api/pipeline/status/{id}")
async def update_status(id: int, status: str):
    ...

@router.post("/api/pipeline/notes/{id}")
async def update_notes(id: int, notes: str):
    ...
```

---

### Logic Top 10 Harian

```python
def get_top10_prospects():
    return db.execute("""
        SELECT
            p.*,
            ps.priority_score,
            ps.priority_tier,
            ps.pitch_angle,
            ps.recommended_service,
            pl.contact_status
        FROM prospects p
        JOIN prospect_scores ps ON p.id = ps.prospect_id
        LEFT JOIN pipeline pl ON p.id = pl.prospect_id
        WHERE
            (pl.is_blacklisted = FALSE OR pl.id IS NULL)
            AND (pl.contact_status = 'belum_dihubungi'
                 OR pl.id IS NULL)
            AND p.phone_normalized IS NOT NULL
        ORDER BY
            ps.priority_score DESC,
            p.review_count DESC
        LIMIT 10
    """).fetchall()
```

---

### Notifikasi Harian `partials/notification.html`

```html
{% if contacted_today < 10 %}
<div class="bg-amber-50 border-b border-amber-200
            px-4 py-2 text-sm text-amber-700">
  📢 Kamu baru menghubungi
  <strong>{{ contacted_today }}</strong> dari
  <strong>10</strong> target hari ini.
  <a href="/" class="underline ml-1">
    Lihat rekomendasi →
  </a>
</div>
{% elif contacted_today >= 10 %}
<div class="bg-green-50 border-b border-green-200
            px-4 py-2 text-sm text-green-700">
  ✅ Target hari ini tercapai!
  {{ contacted_today }} kontak sudah dihubungi.
</div>
{% endif %}
```

---

### Checklist Phase 4

**Templates**
- [ ] `base.html` — layout + navbar + notifikasi
- [ ] `dashboard.html` — halaman utama
- [ ] `partials/top10.html` — komponen top 10
- [ ] `partials/stats.html` — statistik ringkasan
- [ ] `partials/notification.html` — notifikasi harian
- [ ] `partials/prospect_card.html` — card prospect
- [ ] `prospects/list.html` — daftar dengan filter
- [ ] `prospects/detail.html` — detail lengkap
- [ ] `pipeline/board.html` — pipeline board

**API Routes**
- [ ] Dashboard stats endpoint
- [ ] Top 10 query logic
- [ ] List prospects + filter
- [ ] Detail prospect
- [ ] Skip prospect
- [ ] Blacklist prospect
- [ ] Update pipeline status
- [ ] Update notes

**HTMX Interactions**
- [ ] Filter prospects tanpa reload
- [ ] Skip/blacklist langsung dari card
- [ ] Update status pipeline inline
- [ ] Trigger scraper dari dashboard
- [ ] Generate pesan dari detail page

**Testing**
- [ ] Dashboard load dengan data dummy
- [ ] Filter berjalan dengan benar
- [ ] Skip & blacklist berfungsi
- [ ] Pipeline status update tersimpan
- [ ] Top 10 tidak tampilkan yang blacklist
- [ ] Notifikasi muncul sesuai kondisi

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| base.html + navbar + notifikasi | 2 jam |
| Dashboard utama + stats | 2–3 jam |
| Top 10 component + logic | 2–3 jam |
| List prospects + filter | 2 jam |
| Detail prospect page | 3–4 jam |
| Pipeline board | 2 jam |
| API routes semua | 2–3 jam |
| HTMX interactions | 2 jam |
| Testing & debugging | 2–3 jam |
| **Total** | **~3–4 hari** |