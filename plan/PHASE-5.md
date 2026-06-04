## Plan Lengkap Phase 5: Review Website

---

### Tujuan
Sistem otomatis scan website calon client, AI analisis kualitasnya, lalu kamu konfirmasi peluang dengan satu klik — hasilnya jadi konteks tambahan untuk generate pesan.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── scraper/
│   │   ├── website_analyzer.py   # Fetch & analisis website
│   │   └── website_checker.py    # Cek elemen teknis
│   ├── ai/
│   │   └── prompts/
│   │       └── website_review.py # Prompt review website
│   ├── api/
│   │   └── routes/
│   │       └── review.py         # API endpoint review
│   └── templates/
│       ├── review/
│       │   ├── form.html         # Form review manual
│       │   └── result.html       # Hasil review
│       └── partials/
│           └── website_badge.html # Badge status website
```

---

### Alur Review Website

```
Prospect punya website (field website != NULL)
              ↓
Fetch konten halaman utama
              ↓
Cek elemen teknis (SSL, mobile, speed)
              ↓
Kirim konten ke AI untuk analisis kualitas
              ↓
Tampilkan hasil scan di dashboard
              ↓
Kamu konfirmasi dengan satu klik:
remake / redesign / optimasi / none
              ↓
Tambah catatan manual (opsional)
              ↓
Simpan ke tabel website_reviews
              ↓
Hasil jadi konteks generate pesan
```

---

### Detail Tiap File

---

#### `website_checker.py`
Cek elemen teknis website:

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

class WebsiteChecker:

    def __init__(self, timeout=10):
        self.timeout = timeout

    async def check(self, url: str) -> dict:
        result = {
            "website_status": "accessible",
            "is_mobile_friendly": False,
            "has_ssl": False,
            "has_ecommerce": False,
            "has_booking": False,
            "has_contact_form": False,
            "speed_score": 5,
            "raw_html": None,
            "page_title": None,
            "meta_description": None,
            "page_text": None,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                # Cek SSL
                result["has_ssl"] = url.startswith("https")

                # Parse HTML
                soup = BeautifulSoup(
                    response.text, 'html.parser'
                )

                # Cek mobile friendly
                viewport = soup.find(
                    'meta', attrs={'name': 'viewport'}
                )
                result["is_mobile_friendly"] = (
                    viewport is not None
                )

                # Cek ecommerce
                ecommerce_keywords = [
                    'cart', 'keranjang', 'checkout',
                    'add to cart', 'beli', 'shop'
                ]
                page_text = soup.get_text().lower()
                result["has_ecommerce"] = any(
                    kw in page_text
                    for kw in ecommerce_keywords
                )

                # Cek booking
                booking_keywords = [
                    'booking', 'reservasi', 'jadwal',
                    'appointment', 'pesan sekarang'
                ]
                result["has_booking"] = any(
                    kw in page_text
                    for kw in booking_keywords
                )

                # Cek contact form
                forms = soup.find_all('form')
                result["has_contact_form"] = len(forms) > 0

                # Speed score (estimasi dari jumlah resource)
                scripts = len(soup.find_all('script'))
                images = len(soup.find_all('img'))
                total_resources = scripts + images
                if total_resources < 10:
                    result["speed_score"] = 9
                elif total_resources < 20:
                    result["speed_score"] = 7
                elif total_resources < 40:
                    result["speed_score"] = 5
                else:
                    result["speed_score"] = 3

                # Ambil teks untuk AI
                result["page_title"] = (
                    soup.title.string
                    if soup.title else None
                )
                result["meta_description"] = (
                    soup.find(
                        'meta',
                        attrs={'name': 'description'}
                    )
                )
                result["page_text"] = page_text[:3000]
                result["raw_html"] = response.text[:5000]

        except httpx.TimeoutException:
            result["website_status"] = "timeout"
        except httpx.ConnectError:
            result["website_status"] = "error"
        except Exception as e:
            result["website_status"] = "error"

        return result
```

---

#### `prompts/website_review.py`
Prompt AI untuk analisis kualitas website:

```python
def get_website_review_prompt(
    prospect: dict,
    check_result: dict
) -> list:

    system = """
Kamu adalah web developer senior yang menganalisis
kualitas website bisnis lokal Indonesia.

Tugasmu menilai website dan menemukan peluang
improvement yang bisa ditawarkan sebagai jasa.

PENTING: Jawab HANYA dalam format JSON.
Jangan tambahkan teks apapun di luar JSON.
"""

    user = f"""
Analisis website bisnis berikut:

PROFIL BISNIS:
Nama     : {prospect.get('name')}
Kategori : {prospect.get('category')}
Kota     : {prospect.get('city')}

DATA TEKNIS WEBSITE:
URL            : {prospect.get('website')}
Status         : {check_result.get('website_status')}
Mobile Friendly: {check_result.get('is_mobile_friendly')}
SSL            : {check_result.get('has_ssl')}
Ada Ecommerce  : {check_result.get('has_ecommerce')}
Ada Booking    : {check_result.get('has_booking')}
Ada Form Kontak: {check_result.get('has_contact_form')}
Speed Score    : {check_result.get('speed_score')}/10

KONTEN WEBSITE:
Title: {check_result.get('page_title')}
Meta : {check_result.get('meta_description')}
Teks : {check_result.get('page_text', '')[:1000]}

Berikan analisis dalam format JSON:
{{
  "design_quality_score": 7,
  "website_age_estimate": "terlihat >5 tahun",
  "website_issues": [
    "Tidak mobile friendly",
    "Tidak ada sistem booking"
  ],
  "website_summary": "...",
  "opportunity_type": "redesign",
  "opportunity_reason": "...",
  "estimated_value": "high",
  "urgency": "medium"
}}

opportunity_type: remake/redesign/optimasi/none
estimated_value: low/medium/high
urgency: low/medium/high
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `website_analyzer.py`
Orkestrasi cek teknis + AI analisis:

```python
import json
from app.scraper.website_checker import WebsiteChecker
from app.ai.provider import LLMProvider
from app.ai.prompts.website_review import (
    get_website_review_prompt
)
from app.core.database import get_db

class WebsiteAnalyzer:

    def __init__(self, manual_provider=None):
        self.checker = WebsiteChecker()
        self.provider = LLMProvider(manual_provider)
        self.db = get_db()

    async def analyze(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        # Jika tidak ada website skip AI scan
        if not prospect.get('website'):
            return self._save_no_website(prospect_id)

        # Cek teknis website
        check_result = await self.checker.check(
            prospect['website']
        )

        # Jika website tidak bisa diakses
        if check_result['website_status'] != 'accessible':
            return self._save_inaccessible(
                prospect_id, check_result
            )

        # AI analisis
        messages = get_website_review_prompt(
            dict(prospect), check_result
        )
        response = await self.provider.complete(messages)

        # Parse JSON response
        try:
            clean = response.strip()
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            ai_result = json.loads(clean)
        except:
            ai_result = {}

        # Gabungkan hasil teknis + AI
        final_result = {**check_result, **ai_result}

        # Simpan ke database
        self._save_review(prospect_id, final_result)

        # Update prospect status
        self._update_status(prospect_id, 'reviewed')

        return final_result

    async def analyze_all_unreviewed(self) -> dict:
        prospects = self.db.execute("""
            SELECT p.* FROM prospects p
            LEFT JOIN website_reviews wr
            ON p.id = wr.prospect_id
            WHERE wr.id IS NULL
            AND p.website IS NOT NULL
            AND p.status = 'scored'
            LIMIT 20
        """).fetchall()

        results = {
            "total": len(prospects),
            "success": 0,
            "failed": 0,
            "no_website": 0
        }

        for prospect in prospects:
            try:
                await self.analyze(prospect['id'])
                results["success"] += 1
            except Exception:
                results["failed"] += 1

        return results

    def _save_review(
        self,
        prospect_id: int,
        data: dict
    ):
        self.db.execute("""
            INSERT OR REPLACE INTO website_reviews (
                prospect_id,
                website_status,
                is_mobile_friendly,
                has_ssl,
                has_ecommerce,
                has_booking,
                has_contact_form,
                speed_score,
                design_quality_score,
                website_issues,
                website_summary,
                opportunity_type,
                opportunity_notes,
                estimated_value,
                urgency
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            prospect_id,
            data.get('website_status'),
            data.get('is_mobile_friendly'),
            data.get('has_ssl'),
            data.get('has_ecommerce'),
            data.get('has_booking'),
            data.get('has_contact_form'),
            data.get('speed_score'),
            data.get('design_quality_score'),
            str(data.get('website_issues', [])),
            data.get('website_summary'),
            data.get('opportunity_type'),
            data.get('opportunity_reason'),
            data.get('estimated_value'),
            data.get('urgency'),
        ))
        self.db.commit()

    def _save_no_website(self, prospect_id: int):
        self.db.execute("""
            INSERT OR REPLACE INTO website_reviews
            (prospect_id, website_status)
            VALUES (?, 'no_website')
        """, (prospect_id,))
        self.db.commit()
        return {"website_status": "no_website"}

    def _save_inaccessible(
        self,
        prospect_id: int,
        check_result: dict
    ):
        self.db.execute("""
            INSERT OR REPLACE INTO website_reviews
            (prospect_id, website_status)
            VALUES (?, ?)
        """, (prospect_id, check_result['website_status']))
        self.db.commit()
        return check_result

    def _get_prospect(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM prospects WHERE id = ?
        """, (prospect_id,)).fetchone()

    def _update_status(
        self,
        prospect_id: int,
        status: str
    ):
        self.db.execute("""
            UPDATE prospects
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, prospect_id))
        self.db.commit()
```

---

### API Endpoints Review

```python
# app/api/routes/review.py

@router.post("/api/review/{prospect_id}")
async def scan_website(
    prospect_id: int,
    provider: str = None
):
    analyzer = WebsiteAnalyzer(provider)
    result = await analyzer.analyze(prospect_id)
    return templates.TemplateResponse(
        "review/result.html",
        {"result": result, "prospect_id": prospect_id}
    )

@router.post("/api/review/all")
async def scan_all_unreviewed(provider: str = None):
    analyzer = WebsiteAnalyzer(provider)
    result = await analyzer.analyze_all_unreviewed()
    return result

@router.post("/api/review/manual/{prospect_id}")
async def save_manual_review(
    prospect_id: int,
    opportunity_type: str,
    opportunity_notes: str = None,
    estimated_value: str = None,
    urgency: str = None
):
    # Simpan hasil review manual
    db.execute("""
        UPDATE website_reviews
        SET manual_reviewed = TRUE,
            manual_reviewed_at = CURRENT_TIMESTAMP,
            opportunity_type = ?,
            opportunity_notes = ?,
            estimated_value = ?,
            urgency = ?
        WHERE prospect_id = ?
    """, (
        opportunity_type,
        opportunity_notes,
        estimated_value,
        urgency,
        prospect_id
    ))
    db.commit()
    return {"status": "saved"}
```

---

### Tampilan Review di Dashboard

#### Hasil Scan Otomatis
```
┌─────────────────────────────────────────┐
│ 🌐 Website Review — Salon Cantik Mira   │
├─────────────────────────────────────────┤
│ Status    : ✅ Accessible               │
│ Mobile    : ❌ Tidak mobile friendly    │
│ SSL       : ✅ Ada                      │
│ Ecommerce : ❌ Tidak ada               │
│ Booking   : ❌ Tidak ada               │
│ Speed     : 4/10 (lambat)              │
│                                         │
│ 🤖 AI Summary:                          │
│ "Website terlihat sudah >5 tahun,       │
│  desain lama, tidak responsif di HP,    │
│  tidak ada CTA yang jelas"              │
│                                         │
│ Issues:                                 │
│ • Tidak mobile friendly                 │
│ • Loading lambat                        │
│ • Tidak ada sistem booking              │
│ • Desain outdated                       │
├─────────────────────────────────────────┤
│ ✍️ Konfirmasi Manual                    │
│                                         │
│ Opportunity:                            │
│ [Remake] [Redesign✓] [Optimasi] [None] │
│                                         │
│ Nilai: [Low] [Medium✓] [High]          │
│ Urgensi: [Low] [Medium✓] [High]        │
│                                         │
│ Catatan:                                │
│ ┌─────────────────────────────────────┐ │
│ │ Website lama, tidak ada booking,    │ │
│ │ perlu redesign total               │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [💾 Simpan Review]                      │
└─────────────────────────────────────────┘
```

#### Badge Status di Card Prospect
```html
<!-- partials/website_badge.html -->

{% if review %}
  {% if review.opportunity_type == 'remake' %}
  <span class="bg-red-100 text-red-600
               text-xs px-2 py-0.5 rounded-full">
    🔴 Perlu Remake
  </span>
  {% elif review.opportunity_type == 'redesign' %}
  <span class="bg-orange-100 text-orange-600
               text-xs px-2 py-0.5 rounded-full">
    🟠 Perlu Redesign
  </span>
  {% elif review.opportunity_type == 'optimasi' %}
  <span class="bg-yellow-100 text-yellow-600
               text-xs px-2 py-0.5 rounded-full">
    🟡 Perlu Optimasi
  </span>
  {% elif review.opportunity_type == 'none' %}
  <span class="bg-gray-100 text-gray-500
               text-xs px-2 py-0.5 rounded-full">
    ✅ Website OK
  </span>
  {% endif %}
{% elif prospect.website %}
  <span class="bg-blue-50 text-blue-400
               text-xs px-2 py-0.5 rounded-full">
    🔍 Belum di-scan
  </span>
{% else %}
  <span class="bg-red-50 text-red-400
               text-xs px-2 py-0.5 rounded-full">
    ❌ Tidak punya website
  </span>
{% endif %}
```

---

### Update Scoring Otomatis Setelah Review

Setelah review manual disimpan, skor prospect diupdate otomatis:

```python
def recalculate_score_after_review(prospect_id: int):
    review = get_review(prospect_id)
    score = get_score(prospect_id)

    # Bonus score jika ada peluang jelas
    bonus = 0
    if review.opportunity_type in ['remake', 'redesign']:
        bonus = 1.5
    elif review.opportunity_type == 'optimasi':
        bonus = 0.5

    # Bonus urgency
    if review.urgency == 'high':
        bonus += 0.5

    new_score = min(10.0, score.priority_score + bonus)

    # Update tier
    if new_score >= 7.0:
        tier = 'HOT'
    elif new_score >= 4.0:
        tier = 'WARM'
    else:
        tier = 'COLD'

    db.execute("""
        UPDATE prospect_scores
        SET priority_score = ?,
            priority_tier = ?
        WHERE prospect_id = ?
    """, (new_score, tier, prospect_id))
    db.commit()
```

---

### Checklist Phase 5

**Core Logic**
- [ ] `website_checker.py` — cek teknis website
- [ ] `prompts/website_review.py` — prompt AI review
- [ ] `website_analyzer.py` — orkestrasi analisis

**Database**
- [ ] Pastikan tabel `website_reviews` sudah ada
- [ ] Test insert & update review
- [ ] Logic recalculate score setelah review manual

**API Routes**
- [ ] Endpoint scan single website
- [ ] Endpoint scan semua yang belum direview
- [ ] Endpoint simpan review manual
- [ ] Return partial HTML untuk HTMX swap

**Templates**
- [ ] `review/result.html` — tampilan hasil scan
- [ ] `review/form.html` — form konfirmasi manual
- [ ] `partials/website_badge.html` — badge status
- [ ] Integrasi di `prospects/detail.html`

**Testing**
- [ ] Test scan website yang accessible
- [ ] Test scan website yang timeout/error
- [ ] Test prospect tanpa website
- [ ] Test simpan review manual
- [ ] Test recalculate score setelah review
- [ ] Test badge muncul sesuai status

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| website_checker.py | 2–3 jam |
| prompts/website_review.py | 1 jam |
| website_analyzer.py | 2–3 jam |
| API routes | 1–2 jam |
| Templates & UI | 2–3 jam |
| Recalculate score logic | 1 jam |
| Testing & debugging | 2–3 jam |
| **Total** | **~2–3 hari** |