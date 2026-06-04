## Plan Lengkap Phase 3: AI Scoring

---

### Tujuan
Setiap bisnis yang masuk database otomatis dianalisis dan diberi skor prioritas oleh AI, dengan sistem rotasi provider Gemini & Groq.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── provider.py        # LiteLLM wrapper & rotasi
│   │   ├── scorer.py          # Scoring & ranking logic
│   │   ├── analyzer.py        # Analisis profil bisnis
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── scoring.py     # Prompt untuk scoring
│   │   │   └── analysis.py    # Prompt untuk analisis
│   └── api/
│       └── routes/
│           └── scoring.py     # API endpoint scoring
```

---

### Alur AI Scoring

```
Prospects baru di database (status='raw')
              ↓
Ambil data lengkap per bisnis
              ↓
Pilih provider (manual/auto rotasi)
              ↓
Kirim ke LLM dengan prompt scoring
              ↓
Parse response JSON dari LLM
              ↓
Hitung final score berdasarkan bobot
              ↓
Tentukan tier: HOT/WARM/COLD
              ↓
Simpan ke tabel prospect_scores
              ↓
Update status prospect → 'scored'
```

---

### Detail Tiap File

---

#### `provider.py`
LiteLLM wrapper dengan rotasi & fallback:

```python
import random
from datetime import date
from litellm import completion
from app.core.database import get_db

class LLMProvider:

    def __init__(self, manual_provider=None):
        self.db = get_db()
        self.manual_provider = manual_provider

    def get_active_provider(self):
        if self.manual_provider:
            return self._get_provider(self.manual_provider)
        return self._get_auto_provider()

    def _get_auto_provider(self):
        # Reset token harian jika hari baru
        self._reset_daily_tokens_if_needed()

        # Ambil semua provider yang masih available
        providers = self.db.execute("""
            SELECT * FROM llm_providers
            WHERE is_active = TRUE
            AND is_available = TRUE
            AND (
                daily_token_limit IS NULL OR
                tokens_used_today < daily_token_limit
            )
            ORDER BY priority_order ASC
        """).fetchall()

        if not providers:
            raise Exception(
                "Semua provider habis quota hari ini"
            )

        # Pilih random dari yang available
        return random.choice(providers)

    def _get_provider(self, name: str):
        provider = self.db.execute("""
            SELECT * FROM llm_providers
            WHERE provider_name = ?
            AND is_active = TRUE
        """, (name,)).fetchone()

        if not provider:
            raise Exception(f"Provider {name} tidak ditemukan")
        return provider

    async def complete(
        self,
        messages: list,
        manual_provider: str = None
    ):
        provider = self.get_active_provider()

        try:
            response = completion(
                model=f"{provider['provider_name']}/{provider['model_name']}",
                messages=messages,
                api_key=provider['api_key'],
                temperature=0.7,
                max_tokens=1000
            )

            # Update token usage
            tokens_used = response.usage.total_tokens
            self._update_token_usage(
                provider['id'],
                tokens_used
            )

            return response.choices[0].message.content

        except Exception as e:
            # Mark provider unavailable & fallback
            self._mark_unavailable(provider['id'])
            return await self._fallback(messages)

    async def _fallback(self, messages: list):
        # Coba provider lain
        provider = self._get_auto_provider()
        if not provider:
            raise Exception("Tidak ada provider yang tersedia")

        response = completion(
            model=f"{provider['provider_name']}/{provider['model_name']}",
            messages=messages,
            api_key=provider['api_key']
        )
        return response.choices[0].message.content

    def _update_token_usage(
        self,
        provider_id: int,
        tokens: int
    ):
        self.db.execute("""
            UPDATE llm_providers
            SET tokens_used_today = tokens_used_today + ?,
                last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (tokens, provider_id))
        self.db.commit()

    def _mark_unavailable(self, provider_id: int):
        self.db.execute("""
            UPDATE llm_providers
            SET is_available = FALSE
            WHERE id = ?
        """, (provider_id,))
        self.db.commit()

    def _reset_daily_tokens_if_needed(self):
        self.db.execute("""
            UPDATE llm_providers
            SET tokens_used_today = 0,
                is_available = TRUE,
                last_reset_at = DATE('now')
            WHERE last_reset_at < DATE('now')
            OR last_reset_at IS NULL
        """)
        self.db.commit()
```

---

#### `prompts/scoring.py`
Prompt untuk scoring bisnis:

```python
def get_scoring_prompt(prospect: dict) -> list:
    system = """
Kamu adalah analis bisnis yang mengevaluasi potensi
calon client untuk jasa pembuatan website.

Tugasmu adalah memberi skor prioritas 1-10 berdasarkan
data bisnis yang diberikan.

KRITERIA SCORING:
- Tidak punya website     : bobot 30%
- Rating Google ≥ 4.0     : bobot 20%
- Jumlah review banyak    : bobot 15%
- Kategori industri       : bobot 15%
- Aktif di media sosial   : bobot 10%
- Website jelek/lama      : bobot 10%

TIER:
- HOT  : skor 7.0 - 10.0
- WARM : skor 4.0 - 6.9
- COLD : skor 1.0 - 3.9

PENTING: Jawab HANYA dalam format JSON.
Jangan tambahkan teks apapun di luar JSON.

Format response:
{
  "priority_score": 8.5,
  "priority_tier": "HOT",
  "score_reasoning": "...",
  "recommended_service": "buat_baru/redesign/optimasi",
  "pitch_angle": "...",
  "relevant_keywords": ["keyword1", "keyword2"]
}
"""

    user = f"""
Analisis bisnis berikut:

Nama         : {prospect.get('name')}
Kategori     : {prospect.get('category')}
Kota         : {prospect.get('city')}
Rating       : {prospect.get('rating')}
Jumlah Review: {prospect.get('review_count')}
Website      : {prospect.get('website') or 'Tidak ada'}
Telepon      : {prospect.get('phone_normalized')}

Berikan skor prioritas dan rekomendasi layanan
yang paling sesuai untuk bisnis ini.
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `prompts/analysis.py`
Prompt untuk analisis lebih dalam:

```python
def get_analysis_prompt(prospect: dict) -> list:
    system = """
Kamu adalah konsultan digital marketing yang
menganalisis kebutuhan digital bisnis lokal Indonesia.

Tugasmu mengidentifikasi peluang spesifik untuk
menawarkan jasa pembuatan website kepada bisnis ini.

PENTING: Jawab HANYA dalam format JSON.
"""

    user = f"""
Analisis peluang digital untuk bisnis berikut:

Nama     : {prospect.get('name')}
Kategori : {prospect.get('category')}
Kota     : {prospect.get('city')}
Rating   : {prospect.get('rating')}
Review   : {prospect.get('review_count')}
Website  : {prospect.get('website') or 'Tidak ada'}

Format response:
{{
  "digital_maturity": "rendah/menengah/tinggi",
  "main_opportunity": "...",
  "pain_points": ["...", "..."],
  "value_proposition": "...",
  "competitor_advantage": "...",
  "urgency_reason": "..."
}}
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `scorer.py`
Core scoring logic:

```python
import json
from app.ai.provider import LLMProvider
from app.ai.prompts.scoring import get_scoring_prompt
from app.ai.prompts.analysis import get_analysis_prompt
from app.core.database import get_db

class BusinessScorer:

    def __init__(self, manual_provider=None):
        self.provider = LLMProvider(manual_provider)
        self.db = get_db()

    async def score_prospect(
        self,
        prospect_id: int
    ) -> dict:
        # Ambil data prospect
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        # Generate scoring
        score_data = await self._get_score(prospect)
        if not score_data:
            return {"error": "Scoring gagal"}

        # Simpan hasil
        saved = self._save_score(prospect_id, score_data)

        # Update status prospect
        self._update_prospect_status(
            prospect_id, 'scored'
        )

        return score_data

    async def score_all_unscored(self) -> dict:
        # Ambil semua prospect yang belum di-score
        prospects = self.db.execute("""
            SELECT p.* FROM prospects p
            LEFT JOIN prospect_scores ps
            ON p.id = ps.prospect_id
            WHERE ps.id IS NULL
            AND p.status = 'raw'
            LIMIT 50
        """).fetchall()

        results = {
            "total": len(prospects),
            "success": 0,
            "failed": 0
        }

        for prospect in prospects:
            try:
                await self.score_prospect(prospect['id'])
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                continue

        return results

    async def _get_score(self, prospect: dict) -> dict:
        messages = get_scoring_prompt(dict(prospect))

        try:
            response = await self.provider.complete(messages)
            # Parse JSON response
            clean = response.strip()
            # Hapus markdown jika ada
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            return json.loads(clean)
        except json.JSONDecodeError:
            return None
        except Exception as e:
            return None

    def _save_score(
        self,
        prospect_id: int,
        score_data: dict
    ):
        self.db.execute("""
            INSERT INTO prospect_scores (
                prospect_id,
                priority_score,
                priority_tier,
                score_reasoning,
                recommended_service,
                pitch_angle,
                relevant_keywords,
                scored_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            prospect_id,
            score_data.get('priority_score'),
            score_data.get('priority_tier'),
            score_data.get('score_reasoning'),
            score_data.get('recommended_service'),
            score_data.get('pitch_angle'),
            str(score_data.get('relevant_keywords', [])),
        ))
        self.db.commit()

    def _get_prospect(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM prospects WHERE id = ?
        """, (prospect_id,)).fetchone()

    def _update_prospect_status(
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

#### `analyzer.py`
Analisis lebih dalam per bisnis:

```python
import json
from app.ai.provider import LLMProvider
from app.ai.prompts.analysis import get_analysis_prompt
from app.core.database import get_db

class BusinessAnalyzer:

    def __init__(self, manual_provider=None):
        self.provider = LLMProvider(manual_provider)
        self.db = get_db()

    async def analyze(self, prospect_id: int) -> dict:
        prospect = self._get_prospect(prospect_id)
        if not prospect:
            return {"error": "Prospect tidak ditemukan"}

        messages = get_analysis_prompt(dict(prospect))

        try:
            response = await self.provider.complete(messages)
            clean = response.strip()
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            analysis = json.loads(clean)

            # Update prospect_scores dengan analisis
            self._save_analysis(prospect_id, analysis)
            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _save_analysis(
        self,
        prospect_id: int,
        analysis: dict
    ):
        self.db.execute("""
            UPDATE prospect_scores
            SET pitch_angle = ?
            WHERE prospect_id = ?
        """, (
            analysis.get('value_proposition'),
            prospect_id
        ))
        self.db.commit()
```

---

### API Endpoints Scoring

```python
# app/api/routes/scoring.py

@router.post("/scoring/run")
async def run_scoring(provider: str = None):
    scorer = BusinessScorer(provider)
    result = await scorer.score_all_unscored()
    return result

@router.post("/scoring/prospect/{prospect_id}")
async def score_single(
    prospect_id: int,
    provider: str = None
):
    scorer = BusinessScorer(provider)
    result = await scorer.score_prospect(prospect_id)
    return result

@router.get("/scoring/status")
async def scoring_status():
    # Total scored vs unscored
    ...

@router.get("/providers")
async def get_providers():
    # Daftar provider + token usage
    ...

@router.post("/providers")
async def save_provider(provider: ProviderSchema):
    # Tambah/update provider
    ...

@router.put("/providers/{id}/toggle")
async def toggle_provider(id: int):
    # Aktif/nonaktifkan provider
    ...
```

---

### Tampilan Dashboard Scoring

```
┌─────────────────────────────────────────┐
│ 🤖 AI Scoring                           │
│ Belum di-score : 24 bisnis              │
│ Sudah di-score : 186 bisnis             │
│                                         │
│ Provider Mode: [ Auto ▼ ]               │
│ [▶ Score Semua] [▶ Score HOT Only]      │
├─────────────────────────────────────────┤
│ 📊 Provider Status                      │
│ ✅ Gemini   Token: 12k/60k  (aktif)     │
│ ✅ Groq     Token: 45k/100k (aktif)     │
│                                         │
│ [+ Tambah Provider]                     │
├─────────────────────────────────────────┤
│ 🔥 HOT  : 23 bisnis                     │
│ 🟡 WARM : 87 bisnis                     │
│ 🔵 COLD : 76 bisnis                     │
└─────────────────────────────────────────┘
```

---

### Settings Provider di Dashboard

```
┌─────────────────────────────────────────┐
│ ⚙️ LLM Provider Settings               │
├─────────────────────────────────────────┤
│ Provider  : Gemini                      │
│ Model     : gemini-2.0-flash            │
│ API Key   : ******************          │
│ Token/hari: 60000                       │
│ Status    : ✅ Aktif                    │
│ [Edit] [Nonaktifkan]                    │
├─────────────────────────────────────────┤
│ Provider  : Groq                        │
│ Model     : llama-3.3-70b               │
│ API Key   : ******************          │
│ Token/hari: 100000                      │
│ Status    : ✅ Aktif                    │
│ [Edit] [Nonaktifkan]                    │
├─────────────────────────────────────────┤
│ [+ Tambah Provider]                     │
└─────────────────────────────────────────┘
```

---

### Checklist Phase 3

**Setup**
- [ ] Install LiteLLM: `pip install litellm`
- [ ] Buat folder `app/ai/` dan `app/ai/prompts/`
- [ ] Setup API key Gemini & Groq di `.env`
- [ ] Seed data provider ke tabel `llm_providers`

**Core Logic**
- [ ] `provider.py` — LiteLLM wrapper & rotasi
- [ ] `prompts/scoring.py` — prompt scoring
- [ ] `prompts/analysis.py` — prompt analisis
- [ ] `scorer.py` — core scoring logic
- [ ] `analyzer.py` — analisis mendalam

**Token Management**
- [ ] Tracking token usage per hari
- [ ] Auto reset token harian
- [ ] Auto fallback jika quota habis
- [ ] Mark provider unavailable jika error

**API & Dashboard**
- [ ] Endpoint run scoring
- [ ] Endpoint score single prospect
- [ ] Endpoint status scoring
- [ ] Endpoint CRUD provider
- [ ] UI scoring status di dashboard
- [ ] UI provider settings

**Testing**
- [ ] Test score 1 prospect manual
- [ ] Test score semua unscored
- [ ] Test rotasi provider otomatis
- [ ] Test fallback jika provider gagal
- [ ] Verifikasi JSON parsing response
- [ ] Verifikasi data tersimpan di database

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| Setup LiteLLM + konfigurasi provider | 1 jam |
| provider.py — rotasi & fallback | 2–3 jam |
| prompts scoring & analysis | 1–2 jam |
| scorer.py — core logic | 2–3 jam |
| analyzer.py | 1–2 jam |
| API endpoints | 1–2 jam |
| Dashboard UI scoring & provider | 2 jam |
| Testing & debugging | 2–3 jam |
| **Total** | **~2–3 hari** |