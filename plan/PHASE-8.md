## Plan Lengkap Phase 8: Website Preview

---

### Tujuan
Generate file HTML preview website per bisnis secara otomatis berdasarkan data scraping dan AI, lalu tampilkan langsung dari browser lokal sebagai bahan presentasi ke calon client.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── preview/
│   │   ├── __init__.py
│   │   ├── generator.py          # Core generate preview
│   │   ├── content_builder.py    # Build konten dari data
│   │   └── template_selector.py  # Pilih template industri
│   ├── ai/
│   │   └── prompts/
│   │       └── preview_content.py # Prompt generate konten
│   ├── api/
│   │   └── routes/
│   │       └── preview.py         # API endpoint preview
│   └── templates/
│       └── preview/
│           └── preview_card.html  # Card preview di dashboard
├── previews/
│   ├── templates/
│   │   ├── restoran/
│   │   │   ├── template.html
│   │   │   └── style.css
│   │   ├── cafe/
│   │   │   ├── template.html
│   │   │   └── style.css
│   │   ├── salon/
│   │   │   ├── template.html
│   │   │   └── style.css
│   │   ├── klinik/
│   │   │   ├── template.html
│   │   │   └── style.css
│   │   └── hotel/
│   │       ├── template.html
│   │       └── style.css
│   └── generated/
│       └── {prospect_id}/
│           └── index.html
```

---

### Alur Generate Preview

```
Prospect dipilih untuk generate preview
              ↓
Tentukan industri → pilih template HTML
              ↓
Kumpulkan data bisnis dari database
              ↓
AI generate konten:
- Deskripsi bisnis
- Layanan yang ditawarkan
- Tagline
- About section
              ↓
Inject data + konten AI ke template HTML
              ↓
Simpan ke previews/generated/{prospect_id}/index.html
              ↓
Catat di tabel previews
              ↓
Tombol "Buka Preview" di dashboard
→ buka file:// di browser lokal
              ↓
Auto expired setelah 14 hari
```

---

### Detail Tiap File

---

#### `prompts/preview_content.py`
Prompt AI untuk generate konten website:

```python
def get_preview_content_prompt(
    prospect: dict,
    score: dict,
    review: dict = None
) -> list:

    system = """
Kamu adalah copywriter profesional untuk website
bisnis lokal Indonesia.

Tugasmu membuat konten website yang menarik,
natural, dan sesuai dengan karakter bisnis tersebut.

ATURAN:
- Gunakan bahasa Indonesia yang natural
- Sesuaikan tone dengan industri bisnis
- Konten harus spesifik, bukan generik
- Jangan gunakan klaim berlebihan
- PENTING: Jawab HANYA dalam format JSON
"""

    user = f"""
Buat konten website untuk bisnis berikut:

DATA BISNIS:
Nama       : {prospect.get('name')}
Kategori   : {prospect.get('category')}
Kota       : {prospect.get('city')}
Rating     : {prospect.get('rating')}
Review     : {prospect.get('review_count')} ulasan
Alamat     : {prospect.get('address')}
Telepon    : {prospect.get('phone_raw')}

KONTEKS TAMBAHAN:
Keywords   : {score.get('relevant_keywords')}
Layanan    : {score.get('recommended_service')}
Catatan    : {review.get('opportunity_notes') if review else '-'}

Buat konten dalam format JSON:
{{
  "tagline": "Tagline bisnis yang menarik (max 10 kata)",
  "hero_description": "Deskripsi singkat di hero section (max 30 kata)",
  "about_text": "Paragraf tentang bisnis ini (max 60 kata)",
  "services": [
    {{
      "title": "Nama Layanan 1",
      "description": "Deskripsi singkat (max 15 kata)"
    }},
    {{
      "title": "Nama Layanan 2",
      "description": "Deskripsi singkat (max 15 kata)"
    }},
    {{
      "title": "Nama Layanan 3",
      "description": "Deskripsi singkat (max 15 kata)"
    }}
  ],
  "cta_text": "Teks tombol call-to-action (max 5 kata)",
  "footer_tagline": "Kalimat penutup singkat (max 10 kata)"
}}
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `template_selector.py`
Pilih template berdasarkan industri:

```python
import os

# Mapping kategori ke folder template
CATEGORY_MAP = {
    # Restoran & Makanan
    "restoran": "restoran",
    "rumah makan": "restoran",
    "warung": "restoran",
    "warung makan": "restoran",
    "mie ayam": "restoran",
    "bakso": "restoran",
    "seafood": "restoran",

    # Cafe
    "cafe": "cafe",
    "kafe": "cafe",
    "coffee shop": "cafe",
    "kedai kopi": "cafe",
    "kedai": "cafe",

    # Salon & Kecantikan
    "salon": "salon",
    "salon kecantikan": "salon",
    "barbershop": "salon",
    "barber": "salon",
    "spa": "salon",
    "nail art": "salon",

    # Klinik & Kesehatan
    "klinik": "klinik",
    "dokter": "klinik",
    "klinik gigi": "klinik",
    "apotek": "klinik",
    "puskesmas": "klinik",
    "rumah sakit": "klinik",

    # Hotel & Penginapan
    "hotel": "hotel",
    "penginapan": "hotel",
    "homestay": "hotel",
    "villa": "hotel",
    "guest house": "hotel",
    "kost": "hotel",
}

DEFAULT_TEMPLATE = "restoran"
TEMPLATES_DIR = "previews/templates"

class TemplateSelector:

    def get_template_path(
        self,
        category: str
    ) -> str:
        # Normalisasi kategori
        category_lower = (category or "").lower().strip()

        # Cari template yang cocok
        template_folder = None
        for key, folder in CATEGORY_MAP.items():
            if key in category_lower:
                template_folder = folder
                break

        # Fallback ke default
        if not template_folder:
            template_folder = DEFAULT_TEMPLATE

        template_path = os.path.join(
            TEMPLATES_DIR,
            template_folder,
            "template.html"
        )

        # Cek file ada
        if not os.path.exists(template_path):
            template_path = os.path.join(
                TEMPLATES_DIR,
                DEFAULT_TEMPLATE,
                "template.html"
            )

        return template_path

    def get_template_name(self, category: str) -> str:
        category_lower = (category or "").lower().strip()
        for key, folder in CATEGORY_MAP.items():
            if key in category_lower:
                return folder
        return DEFAULT_TEMPLATE
```

---

#### `content_builder.py`
Build data siap inject ke template:

```python
from datetime import date, timedelta

class ContentBuilder:

    def build(
        self,
        prospect: dict,
        ai_content: dict
    ) -> dict:
        return {
            # Data bisnis
            "business_name": prospect.get('name', ''),
            "category": prospect.get('category', ''),
            "city": prospect.get('city', ''),
            "address": prospect.get('address', ''),
            "phone": prospect.get('phone_raw', ''),
            "phone_wa": prospect.get('phone_normalized', ''),
            "rating": prospect.get('rating', ''),
            "review_count": prospect.get('review_count', 0),
            "maps_url": prospect.get('google_maps_url', ''),

            # Konten AI
            "tagline": ai_content.get(
                'tagline', f"Selamat Datang di {prospect.get('name')}"
            ),
            "hero_description": ai_content.get(
                'hero_description', ''
            ),
            "about_text": ai_content.get('about_text', ''),
            "services": ai_content.get('services', []),
            "cta_text": ai_content.get(
                'cta_text', 'Hubungi Kami'
            ),
            "footer_tagline": ai_content.get(
                'footer_tagline', ''
            ),

            # Metadata
            "generated_date": date.today().strftime(
                "%d %B %Y"
            ),
            "expired_date": (
                date.today() + timedelta(days=14)
            ).strftime("%d %B %Y"),
            "preview_note": (
                "Preview ini dibuat khusus untuk "
                f"{prospect.get('name')} oleh tim kami."
            )
        }
```

---

#### `generator.py`
Core logic generate preview HTML:

```python
import os
import json
import shutil
from datetime import date, timedelta
from jinja2 import Environment, FileSystemLoader
from app.ai.provider import LLMProvider
from app.ai.prompts.preview_content import (
    get_preview_content_prompt
)
from app.preview.template_selector import TemplateSelector
from app.preview.content_builder import ContentBuilder
from app.core.database import get_db

class PreviewGenerator:

    def __init__(self, manual_provider=None):
        self.provider = LLMProvider(manual_provider)
        self.selector = TemplateSelector()
        self.builder = ContentBuilder()
        self.db = get_db()
        self.output_dir = "previews/generated"

    async def generate(self, prospect_id: int) -> dict:
        # Ambil data
        prospect = self._get_prospect(prospect_id)
        score = self._get_score(prospect_id)
        review = self._get_review(prospect_id)

        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        # Generate konten AI
        ai_content = await self._generate_content(
            prospect, score, review
        )

        # Build data untuk template
        content = self.builder.build(
            dict(prospect), ai_content
        )

        # Pilih template
        template_path = self.selector.get_template_path(
            prospect.get('category')
        )
        template_name = self.selector.get_template_name(
            prospect.get('category')
        )

        # Render HTML
        html = self._render_template(
            template_path, content
        )

        # Simpan file
        file_path = self._save_html(prospect_id, html)

        # Simpan ke database
        self._save_to_db(
            prospect_id,
            file_path,
            template_name
        )

        return {
            "status": "success",
            "file_path": file_path,
            "template": template_name,
            "prospect_name": prospect.get('name')
        }

    async def _generate_content(
        self,
        prospect: dict,
        score: dict,
        review: dict
    ) -> dict:
        messages = get_preview_content_prompt(
            dict(prospect),
            dict(score) if score else {},
            dict(review) if review else None
        )

        try:
            response = await self.provider.complete(messages)
            clean = response.strip()
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            return json.loads(clean)
        except:
            # Fallback konten default
            return {
                "tagline": f"Selamat Datang di {prospect.get('name')}",
                "hero_description": f"Kami hadir untuk melayani Anda di {prospect.get('city')}",
                "about_text": f"{prospect.get('name')} adalah bisnis terpercaya di {prospect.get('city')}.",
                "services": [
                    {"title": "Layanan Utama", "description": "Layanan terbaik untuk Anda"},
                    {"title": "Konsultasi", "description": "Gratis konsultasi untuk Anda"},
                    {"title": "Informasi", "description": "Hubungi kami untuk info lebih lanjut"}
                ],
                "cta_text": "Hubungi Kami",
                "footer_tagline": "Terima kasih telah mempercayai kami"
            }

    def _render_template(
        self,
        template_path: str,
        content: dict
    ) -> str:
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)

        env = Environment(
            loader=FileSystemLoader(template_dir)
        )
        template = env.get_template(template_file)
        return template.render(**content)

    def _save_html(
        self,
        prospect_id: int,
        html: str
    ) -> str:
        # Buat folder per prospect
        folder = os.path.join(
            self.output_dir,
            str(prospect_id)
        )
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, "index.html")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return file_path

    def _save_to_db(
        self,
        prospect_id: int,
        file_path: str,
        template_name: str
    ):
        expired_at = date.today() + timedelta(days=14)

        # Cek jika sudah ada
        existing = self.db.execute("""
            SELECT id FROM previews
            WHERE prospect_id = ?
        """, (prospect_id,)).fetchone()

        if existing:
            self.db.execute("""
                UPDATE previews
                SET file_path = ?,
                    industry_template = ?,
                    generated_at = CURRENT_TIMESTAMP,
                    expired_at = ?,
                    open_count = 0,
                    status = 'active'
                WHERE prospect_id = ?
            """, (
                file_path,
                template_name,
                expired_at,
                prospect_id
            ))
        else:
            self.db.execute("""
                INSERT INTO previews (
                    prospect_id,
                    file_path,
                    industry_template,
                    expired_at,
                    status
                ) VALUES (?, ?, ?, ?, 'active')
            """, (
                prospect_id,
                file_path,
                template_name,
                expired_at
            ))
        self.db.commit()

    def check_and_expire(self):
        self.db.execute("""
            UPDATE previews
            SET status = 'expired'
            WHERE expired_at < DATE('now')
            AND status = 'active'
        """)
        self.db.commit()

    def open_preview(self, prospect_id: int) -> str:
        preview = self.db.execute("""
            SELECT * FROM previews
            WHERE prospect_id = ?
            AND status = 'active'
        """, (prospect_id,)).fetchone()

        if not preview:
            return None

        # Update open count
        self.db.execute("""
            UPDATE previews
            SET open_count = open_count + 1,
                last_opened_at = CURRENT_TIMESTAMP
            WHERE prospect_id = ?
        """, (prospect_id,))
        self.db.commit()

        # Return absolute path untuk buka di browser
        abs_path = os.path.abspath(preview['file_path'])
        return f"file:///{abs_path}"
```

---

### Template HTML per Industri

Struktur template menggunakan Jinja2 syntax dengan Tailwind CSS via CDN — tidak perlu build step.

---

#### `previews/templates/restoran/template.html`

```html
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width">
  <title>{{ business_name }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    /* Warna tema restoran — hangat */
    :root {
      --primary: #D97706;
      --secondary: #92400E;
      --accent: #FEF3C7;
    }
  </style>
</head>
<body class="bg-white font-sans">

  <!-- Preview Banner -->
  <div class="bg-amber-500 text-white text-center
              py-2 text-xs">
    🎨 Preview Website — {{ preview_note }}
    Berlaku hingga {{ expired_date }}
  </div>

  <!-- Hero Section -->
  <section class="bg-amber-700 text-white
                  py-20 px-6 text-center">
    <h1 class="text-4xl font-bold mb-4">
      {{ business_name }}
    </h1>
    <p class="text-xl text-amber-200 mb-2">
      {{ tagline }}
    </p>
    <p class="text-amber-100 mb-8 max-w-xl mx-auto">
      {{ hero_description }}
    </p>
    <div class="flex justify-center gap-3">
      <a href="https://wa.me/{{ phone_wa }}"
         class="bg-white text-amber-700 font-semibold
                px-6 py-3 rounded-full">
        {{ cta_text }}
      </a>
      <a href="{{ maps_url }}"
         class="border border-white text-white
                px-6 py-3 rounded-full">
        Lihat Lokasi
      </a>
    </div>
  </section>

  <!-- Rating Section -->
  <section class="bg-amber-50 py-8 text-center">
    <p class="text-3xl font-bold text-amber-700">
      ⭐ {{ rating }}
    </p>
    <p class="text-gray-500">
      {{ review_count }} ulasan di Google Maps
    </p>
  </section>

  <!-- Services Section -->
  <section class="py-16 px-6 max-w-4xl mx-auto">
    <h2 class="text-2xl font-bold text-center mb-10
               text-gray-800">
      Yang Kami Tawarkan
    </h2>
    <div class="grid grid-cols-3 gap-6">
      {% for service in services %}
      <div class="bg-amber-50 rounded-xl p-6
                  text-center">
        <div class="text-3xl mb-3">🍽️</div>
        <h3 class="font-semibold mb-2">
          {{ service.title }}
        </h3>
        <p class="text-sm text-gray-500">
          {{ service.description }}
        </p>
      </div>
      {% endfor %}
    </div>
  </section>

  <!-- About Section -->
  <section class="bg-gray-50 py-16 px-6">
    <div class="max-w-2xl mx-auto text-center">
      <h2 class="text-2xl font-bold mb-6 text-gray-800">
        Tentang Kami
      </h2>
      <p class="text-gray-600 leading-relaxed">
        {{ about_text }}
      </p>
    </div>
  </section>

  <!-- Contact Section -->
  <section class="bg-amber-700 text-white
                  py-16 px-6 text-center">
    <h2 class="text-2xl font-bold mb-4">
      Hubungi Kami
    </h2>
    <p class="text-amber-200 mb-6">{{ address }}</p>
    <div class="flex justify-center gap-4">
      <a href="tel:{{ phone }}"
         class="bg-white text-amber-700 px-6 py-3
                rounded-full font-semibold">
        📞 {{ phone }}
      </a>
      <a href="https://wa.me/{{ phone_wa }}"
         class="bg-green-500 text-white px-6 py-3
                rounded-full font-semibold">
        💬 WhatsApp
      </a>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-amber-900 text-amber-200
                 py-6 text-center text-sm">
    <p>{{ footer_tagline }}</p>
    <p class="mt-1 text-amber-400">
      © {{ business_name }} · {{ city }}
    </p>
  </footer>

</body>
</html>
```

Struktur serupa dibuat untuk:
- `cafe/template.html` — tema gelap, modern, coffee vibes
- `salon/template.html` — tema pink/pastel, elegan
- `klinik/template.html` — tema biru/putih, bersih, profesional
- `hotel/template.html` — tema premium, luxury

---

### API Endpoints Preview

```python
# app/api/routes/preview.py

@router.post("/api/preview/generate/{prospect_id}")
async def generate_preview(
    prospect_id: int,
    provider: str = None
):
    generator = PreviewGenerator(provider)
    result = await generator.generate(prospect_id)
    return templates.TemplateResponse(
        "preview/preview_card.html",
        {"result": result, "prospect_id": prospect_id}
    )

@router.get("/api/preview/open/{prospect_id}")
async def open_preview(prospect_id: int):
    generator = PreviewGenerator()
    file_url = generator.open_preview(prospect_id)

    if not file_url:
        return {"error": "Preview tidak ditemukan"}

    # Return URL untuk dibuka di browser
    return {"url": file_url}

@router.post("/api/preview/regenerate/{prospect_id}")
async def regenerate_preview(
    prospect_id: int,
    provider: str = None
):
    generator = PreviewGenerator(provider)
    result = await generator.generate(prospect_id)
    return templates.TemplateResponse(
        "preview/preview_card.html",
        {"result": result, "prospect_id": prospect_id}
    )

@router.post("/api/preview/expire")
async def run_expire_check():
    generator = PreviewGenerator()
    generator.check_and_expire()
    return {"status": "done"}
```

---

### Template Dashboard Preview

#### `preview/preview_card.html`

```html
<div id="preview-{{ prospect_id }}"
     class="bg-white rounded-xl p-4 shadow-sm">

  {% if result.status == 'success' %}

  <div class="flex justify-between items-start mb-3">
    <div>
      <p class="font-semibold text-sm">
        🎨 Preview Siap
      </p>
      <p class="text-xs text-gray-500">
        Template: {{ result.template | capitalize }}
      </p>
    </div>
    <span class="bg-green-100 text-green-600
                 text-xs px-2 py-0.5 rounded-full">
      ✅ Active
    </span>
  </div>

  <div class="flex gap-2">

    <!-- Buka Preview -->
    <button
      onclick="openPreview({{ prospect_id }})"
      class="flex-1 bg-indigo-600 text-white
             text-sm py-2 rounded-lg">
      🖥️ Buka Preview
    </button>

    <!-- Regenerate -->
    <button
      hx-post="/api/preview/regenerate/{{ prospect_id }}"
      hx-target="#preview-{{ prospect_id }}"
      hx-swap="outerHTML"
      class="border text-sm py-2 px-3 rounded-lg
             text-gray-500">
      🔄
    </button>

  </div>

  {% else %}

  <button
    hx-post="/api/preview/generate/{{ prospect_id }}"
    hx-target="#preview-{{ prospect_id }}"
    hx-swap="outerHTML"
    class="w-full bg-indigo-600 text-white
           text-sm py-2 rounded-lg">
    ✨ Generate Preview Website
  </button>

  {% endif %}

</div>

<script>
function openPreview(prospectId) {
  fetch(`/api/preview/open/${prospectId}`)
    .then(r => r.json())
    .then(data => {
      if (data.url) {
        window.open(data.url, '_blank')
      }
    })
}
</script>
```

---

### Integrasi ke Detail Page

Tambahkan section preview di `prospects/detail.html`:

```html
<!-- Preview Website Section -->
<div class="bg-white rounded-xl p-6 shadow-sm">
  <h2 class="font-semibold mb-4">
    🎨 Preview Website
  </h2>

  <div id="preview-{{ prospect.id }}"
    hx-get="/api/preview/status/{{ prospect.id }}"
    hx-trigger="load"
    hx-swap="innerHTML">
    <p class="text-sm text-gray-400">
      Memuat status preview...
    </p>
  </div>

</div>
```

---

### Update Scheduler

Tambah job expire preview ke `scheduler.py`:

```python
# Cek expired preview setiap hari jam 00.30
scheduler.add_job(
    func=run_expire_preview,
    trigger=CronTrigger(hour=0, minute=30),
    id="expire_preview",
    name="Expire Preview Harian",
    replace_existing=True
)

async def run_expire_preview():
    generator = PreviewGenerator()
    generator.check_and_expire()
    logger.info("Preview expiry check done")
```

---

### Checklist Phase 8

**Template HTML**
- [ ] `restoran/template.html` — tema hangat
- [ ] `cafe/template.html` — tema modern gelap
- [ ] `salon/template.html` — tema pastel elegan
- [ ] `klinik/template.html` — tema bersih profesional
- [ ] `hotel/template.html` — tema premium

**Core Logic**
- [ ] `template_selector.py` — mapping kategori
- [ ] `content_builder.py` — build data inject
- [ ] `prompts/preview_content.py` — prompt AI konten
- [ ] `generator.py` — core generate & save HTML
- [ ] Logic fallback konten jika AI gagal
- [ ] Logic auto expire 14 hari

**Database**
- [ ] Pastikan tabel `previews` sudah ada
- [ ] Test insert & update preview
- [ ] Test expire otomatis

**API Routes**
- [ ] Generate preview
- [ ] Open preview
- [ ] Regenerate preview
- [ ] Expire check

**Dashboard**
- [ ] `preview/preview_card.html`
- [ ] Integrasi di `prospects/detail.html`
- [ ] Tombol buka preview via file://
- [ ] Update scheduler tambah job expire

**Testing**
- [ ] Test generate preview restoran
- [ ] Test generate preview cafe
- [ ] Test generate preview salon
- [ ] Test generate preview klinik
- [ ] Test generate preview hotel
- [ ] Test kategori tidak dikenal → fallback restoran
- [ ] Test buka file HTML di browser
- [ ] Test auto expire setelah 14 hari
- [ ] Test regenerate override yang lama

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| 5 template HTML (restoran, cafe, salon, klinik, hotel) | 4–5 jam |
| template_selector.py | 1 jam |
| content_builder.py | 1 jam |
| prompts/preview_content.py | 1 jam |
| generator.py | 3–4 jam |
| API routes | 1–2 jam |
| Dashboard UI & integrasi | 2 jam |
| Update scheduler | 30 menit |
| Testing & debugging | 2–3 jam |
| **Total** | **~3–4 hari** |