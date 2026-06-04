## Plan Lengkap Phase 6: Generate Pesan

---

### Tujuan
Sistem generate pesan WA yang personal per bisnis menggunakan AI, berdasarkan seluruh data yang sudah dikumpulkan — lalu sajikan sebagai WA link siap klik.

---

### Struktur Folder Tambahan

```
client_finder/
├── app/
│   ├── ai/
│   │   ├── message_generator.py    # Core generate pesan
│   │   └── prompts/
│   │       ├── message_first.py    # Prompt pesan pertama
│   │       └── message_followup.py # Prompt follow-up
│   ├── api/
│   │   └── routes/
│   │       └── messages.py         # API endpoint pesan
│   └── templates/
│       ├── messages/
│       │   ├── preview.html        # Preview pesan
│       │   └── history.html        # Riwayat pesan
│       └── partials/
│           └── wa_button.html      # Tombol WA link
```

---

### Alur Generate Pesan

```
Prospect sudah di-score & di-review
              ↓
Kumpulkan semua konteks:
- Data bisnis (nama, kategori, kota)
- Skor & pitch angle
- Hasil review website
- Relevant keywords
- Catatan manual
              ↓
Kirim ke AI dengan prompt pesan pertama
              ↓
AI generate 3 variasi pesan
              ↓
Tampilkan di dashboard untuk dipilih
              ↓
Generate WA link dari pesan yang dipilih
              ↓
Simpan pesan ke tabel messages
              ↓
Kamu klik → buka WA → send manual
```

---

### Detail Tiap File

---

#### `prompts/message_first.py`
Prompt pesan pertama:

```python
def get_first_message_prompt(
    prospect: dict,
    score: dict,
    review: dict = None
) -> list:

    system = """
Kamu adalah spesialis sales copywriting untuk
jasa pembuatan website di Indonesia.

Tugasmu menulis pesan WhatsApp yang personal,
natural, dan tidak terasa seperti spam.

ATURAN KETAT:
- Maksimal 300 karakter per pesan
- Selalu sebut nama bisnis di awal
- Spesifik — sebutkan 1 hal konkret tentang bisnis ini
- Tidak boleh lebay atau berlebihan
- Tidak boleh pakai emoji berlebihan (max 1-2)
- Terasa seperti ditulis manusia, bukan bot
- Gunakan bahasa Indonesia yang natural
- Akhiri dengan pertanyaan atau CTA ringan

PENTING: Jawab HANYA dalam format JSON.
"""

    # Konteks website
    website_context = "Tidak punya website"
    if review:
        if review.get('opportunity_type') == 'remake':
            website_context = "Website ada tapi perlu dibuat ulang"
        elif review.get('opportunity_type') == 'redesign':
            website_context = "Website ada tapi perlu redesign"
        elif review.get('opportunity_type') == 'optimasi':
            website_context = "Website ada, perlu optimasi"

    user = f"""
Buat 3 variasi pesan WhatsApp untuk bisnis ini:

DATA BISNIS:
Nama           : {prospect.get('name')}
Kategori       : {prospect.get('category')}
Kota           : {prospect.get('city')}
Rating         : {prospect.get('rating')}
Jumlah Review  : {prospect.get('review_count')}
Status Website : {website_context}
Pitch Angle    : {score.get('pitch_angle')}
Layanan        : {score.get('recommended_service')}
Keywords       : {score.get('relevant_keywords')}

Catatan manual : {review.get('opportunity_notes') if review else '-'}

Buat 3 variasi dengan tone berbeda:
1. Formal — sopan dan profesional
2. Semi-formal — friendly tapi tetap profesional
3. Kasual — santai seperti kenalan

Format response:
{{
  "variants": [
    {{
      "tone": "formal",
      "message": "..."
    }},
    {{
      "tone": "semi-formal",
      "message": "..."
    }},
    {{
      "tone": "kasual",
      "message": "..."
    }}
  ]
}}
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `prompts/message_followup.py`
Prompt pesan follow-up:

```python
def get_followup_message_prompt(
    prospect: dict,
    score: dict,
    review: dict,
    previous_messages: list,
    followup_sequence: int
) -> list:

    system = """
Kamu adalah spesialis sales copywriting untuk
jasa pembuatan website di Indonesia.

Tugasmu menulis pesan follow-up WhatsApp yang
natural dan tidak mengganggu.

ATURAN KETAT:
- Maksimal 300 karakter
- JANGAN ulangi pesan sebelumnya
- Gunakan angle yang berbeda dari pesan sebelumnya
- Tidak boleh terkesan memaksa atau desperate
- Tetap natural dan ramah
- PENTING: Jawab HANYA dalam format JSON
"""

    # Format riwayat pesan sebelumnya
    prev_messages_text = "\n".join([
        f"Pesan #{i+1} ({msg.get('tone', '-')}): {msg.get('content')}"
        for i, msg in enumerate(previous_messages)
    ])

    # Tentukan angle follow-up berdasarkan sequence
    angle_guide = {
        1: "Tunjukkan contoh atau social proof yang relevan",
        2: "Tawarkan konsultasi gratis tanpa komitmen"
    }
    angle = angle_guide.get(followup_sequence, "Angle baru")

    user = f"""
Buat pesan follow-up untuk bisnis ini:

DATA BISNIS:
Nama     : {prospect.get('name')}
Kategori : {prospect.get('category')}
Kota     : {prospect.get('city')}

PESAN SEBELUMNYA:
{prev_messages_text}

FOLLOW-UP KE: {followup_sequence}
ANGLE YANG HARUS DIPAKAI: {angle}

Buat 2 variasi pesan follow-up:
{{
  "variants": [
    {{
      "tone": "semi-formal",
      "message": "..."
    }},
    {{
      "tone": "kasual",
      "message": "..."
    }}
  ]
}}
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
```

---

#### `message_generator.py`
Core logic generate pesan:

```python
import json
from urllib.parse import quote
from app.ai.provider import LLMProvider
from app.ai.prompts.message_first import (
    get_first_message_prompt
)
from app.ai.prompts.message_followup import (
    get_followup_message_prompt
)
from app.core.database import get_db

class MessageGenerator:

    def __init__(self, manual_provider=None):
        self.provider = LLMProvider(manual_provider)
        self.db = get_db()

    async def generate_first(
        self,
        prospect_id: int
    ) -> dict:
        # Kumpulkan semua konteks
        prospect = self._get_prospect(prospect_id)
        score = self._get_score(prospect_id)
        review = self._get_review(prospect_id)

        if not prospect or not score:
            return {"error": "Data tidak lengkap"}

        # Generate via AI
        messages = get_first_message_prompt(
            dict(prospect),
            dict(score),
            dict(review) if review else None
        )
        response = await self.provider.complete(messages)

        # Parse response
        variants = self._parse_variants(response)
        if not variants:
            return {"error": "Gagal generate pesan"}

        # Simpan semua variasi
        saved = self._save_variants(
            prospect_id, variants, sequence=0
        )

        return {
            "variants": variants,
            "prospect": dict(prospect)
        }

    async def generate_followup(
        self,
        prospect_id: int,
        sequence: int
    ) -> dict:
        prospect = self._get_prospect(prospect_id)
        score = self._get_score(prospect_id)
        review = self._get_review(prospect_id)
        previous = self._get_previous_messages(prospect_id)

        if not prospect or not score:
            return {"error": "Data tidak lengkap"}

        messages = get_followup_message_prompt(
            dict(prospect),
            dict(score),
            dict(review) if review else {},
            previous,
            sequence
        )
        response = await self.provider.complete(messages)

        variants = self._parse_variants(response)
        if not variants:
            return {"error": "Gagal generate pesan"}

        saved = self._save_variants(
            prospect_id, variants, sequence=sequence
        )

        return {
            "variants": variants,
            "prospect": dict(prospect)
        }

    def generate_wa_link(
        self,
        phone: str,
        message: str
    ) -> str:
        # Encode pesan untuk URL
        encoded = quote(message)
        return f"https://wa.me/{phone}?text={encoded}"

    def mark_as_sent(self, message_id: int):
        self.db.execute("""
            UPDATE messages
            SET status = 'sent',
                sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (message_id,))
        self.db.commit()

    def _parse_variants(self, response: str) -> list:
        try:
            clean = response.strip()
            clean = clean.replace('```json', '')
            clean = clean.replace('```', '')
            data = json.loads(clean)
            return data.get('variants', [])
        except:
            return []

    def _save_variants(
        self,
        prospect_id: int,
        variants: list,
        sequence: int
    ) -> list:
        saved_ids = []
        for variant in variants:
            cursor = self.db.execute("""
                INSERT INTO messages (
                    prospect_id,
                    sequence,
                    content,
                    tone,
                    provider_used,
                    status
                ) VALUES (?, ?, ?, ?, ?, 'draft')
            """, (
                prospect_id,
                sequence,
                variant.get('message'),
                variant.get('tone'),
                self.provider.last_used_provider
            ))
            saved_ids.append(cursor.lastrowid)
        self.db.commit()
        return saved_ids

    def _get_prospect(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM prospects WHERE id = ?
        """, (prospect_id,)).fetchone()

    def _get_score(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM prospect_scores
            WHERE prospect_id = ?
            ORDER BY scored_at DESC LIMIT 1
        """, (prospect_id,)).fetchone()

    def _get_review(self, prospect_id: int):
        return self.db.execute("""
            SELECT * FROM website_reviews
            WHERE prospect_id = ?
        """, (prospect_id,)).fetchone()

    def _get_previous_messages(
        self,
        prospect_id: int
    ) -> list:
        rows = self.db.execute("""
            SELECT content, tone, sequence
            FROM messages
            WHERE prospect_id = ?
            AND status = 'sent'
            ORDER BY sent_at ASC
        """, (prospect_id,)).fetchall()
        return [dict(r) for r in rows]
```

---

### Update Tabel Messages

Tambah kolom `tone` yang belum ada di Phase 1:

```sql
ALTER TABLE messages ADD COLUMN tone TEXT;
```

---

### API Endpoints Messages

```python
# app/api/routes/messages.py

@router.post("/api/messages/generate/{prospect_id}")
async def generate_first_message(
    prospect_id: int,
    provider: str = None
):
    generator = MessageGenerator(provider)
    result = await generator.generate_first(prospect_id)
    return templates.TemplateResponse(
        "messages/preview.html",
        {"result": result}
    )

@router.post("/api/messages/followup/{prospect_id}")
async def generate_followup_message(
    prospect_id: int,
    sequence: int = 1,
    provider: str = None
):
    generator = MessageGenerator(provider)
    result = await generator.generate_followup(
        prospect_id, sequence
    )
    return templates.TemplateResponse(
        "messages/preview.html",
        {"result": result}
    )

@router.post("/api/messages/regenerate/{prospect_id}")
async def regenerate_message(
    prospect_id: int,
    provider: str = None
):
    # Generate ulang pesan baru
    generator = MessageGenerator(provider)
    result = await generator.generate_first(prospect_id)
    return templates.TemplateResponse(
        "messages/preview.html",
        {"result": result}
    )

@router.post("/api/messages/sent/{message_id}")
async def mark_sent(message_id: int):
    generator = MessageGenerator()
    generator.mark_as_sent(message_id)
    return {"status": "updated"}

@router.get("/api/messages/history/{prospect_id}")
async def message_history(prospect_id: int):
    messages = db.execute("""
        SELECT * FROM messages
        WHERE prospect_id = ?
        ORDER BY generated_at DESC
    """, (prospect_id,)).fetchall()
    return templates.TemplateResponse(
        "messages/history.html",
        {"messages": messages}
    )
```

---

### Templates

#### `messages/preview.html`

```html
<div id="message-preview" class="space-y-3">

  <div class="flex justify-between items-center">
    <h3 class="font-semibold text-sm">
      💬 Pilih Variasi Pesan
    </h3>
    <button
      hx-post="/api/messages/regenerate/{{ prospect_id }}"
      hx-target="#message-preview"
      hx-swap="outerHTML"
      class="text-xs text-indigo-600 underline">
      🔄 Generate Ulang
    </button>
  </div>

  {% for variant in result.variants %}
  <div class="border rounded-xl p-4
              hover:border-indigo-300 cursor-pointer
              transition"
       onclick="selectVariant({{ loop.index }})">

    <!-- Tone Badge -->
    <span class="text-xs px-2 py-0.5 rounded-full mb-2
                 inline-block
      {% if variant.tone == 'formal' %}
        bg-blue-100 text-blue-600
      {% elif variant.tone == 'semi-formal' %}
        bg-purple-100 text-purple-600
      {% else %}
        bg-green-100 text-green-600
      {% endif %}">
      {{ variant.tone | capitalize }}
    </span>

    <!-- Isi Pesan -->
    <p class="text-sm text-gray-700 mb-3">
      {{ variant.message }}
    </p>

    <!-- Karakter count -->
    <p class="text-xs text-gray-400 mb-3">
      {{ variant.message | length }} karakter
    </p>

    <!-- WA Button -->
    <a href="{{ generator.generate_wa_link(
                prospect.phone_normalized,
                variant.message
              ) }}"
       target="_blank"
       hx-post="/api/messages/sent/{{ variant.id }}"
       hx-swap="none"
       class="block w-full bg-green-500 text-white
              text-sm py-2 rounded-lg text-center">
      📱 Kirim via WA
    </a>

  </div>
  {% endfor %}

</div>
```

---

#### `partials/wa_button.html`

```html
{% if message %}
<a href="https://wa.me/{{ prospect.phone_normalized }}
         ?text={{ message.content | urlencode }}"
   target="_blank"
   hx-post="/api/messages/sent/{{ message.id }}"
   hx-swap="none"
   class="flex items-center justify-center gap-2
          bg-green-500 text-white text-sm
          py-2 px-4 rounded-lg w-full">
  📱 Buka WA
</a>
{% else %}
<button
  hx-post="/api/messages/generate/{{ prospect.id }}"
  hx-target="#message-preview"
  hx-swap="innerHTML"
  class="flex items-center justify-center gap-2
         bg-indigo-600 text-white text-sm
         py-2 px-4 rounded-lg w-full">
  ✨ Generate Pesan
</button>
{% endif %}
```

---

#### `messages/history.html`

```html
<div class="space-y-3">
  <h3 class="font-semibold text-sm">
    📜 Riwayat Pesan
  </h3>

  {% for msg in messages %}
  <div class="border rounded-xl p-3 text-sm">

    <div class="flex justify-between text-xs
                text-gray-500 mb-2">
      <span>
        {% if msg.sequence == 0 %}
          Pesan Pertama
        {% else %}
          Follow-up #{{ msg.sequence }}
        {% endif %}
        · {{ msg.tone }}
      </span>
      <span>{{ msg.generated_at }}</span>
    </div>

    <p class="text-gray-700">{{ msg.content }}</p>

    <div class="flex justify-between items-center mt-2">
      <span class="text-xs
        {% if msg.status == 'sent' %}
          text-green-600
        {% else %}
          text-gray-400
        {% endif %}">
        {{ msg.status | capitalize }}
        {% if msg.sent_at %}· {{ msg.sent_at }}{% endif %}
      </span>

      {% if msg.status == 'draft' %}
      <a href="https://wa.me/{{ phone }}
               ?text={{ msg.content | urlencode }}"
         target="_blank"
         class="text-xs text-green-600 underline">
        Kirim via WA →
      </a>
      {% endif %}
    </div>

  </div>
  {% endfor %}

</div>
```

---

### Contoh Output Pesan yang Dihasilkan

```
FORMAL:
"Halo Salon Cantik Mira, kami melihat bisnis Anda
memiliki rating 4.8 di Google namun belum memiliki
website. Kami siap membantu membuatkan website
profesional untuk Salon Anda. Apakah ada waktu
untuk kami diskusikan?"

SEMI-FORMAL:
"Halo Salon Cantik Mira 👋 Salon Anda punya rating
bagus di Google tapi belum ada website-nya. Kami
bisa bantu buatkan website yang bisa terima booking
online. Tertarik untuk info lebih lanjut?"

KASUAL:
"Halo kak Mira, liat salon kakak di Google,
reviewnya bagus banget! Sayang belum ada websitenya.
Kami bisa bantu buatin, bisa buat booking online
juga. Boleh minta info lebih lanjut ga kak? 😊"
```

---

### Checklist Phase 6

**Core Logic**
- [ ] `prompts/message_first.py` — prompt pesan pertama
- [ ] `prompts/message_followup.py` — prompt follow-up
- [ ] `message_generator.py` — core generate logic
- [ ] WA link generator dari nomor + pesan
- [ ] Mark as sent setelah klik WA

**Database**
- [ ] Tambah kolom `tone` ke tabel messages
- [ ] Test insert pesan ke database
- [ ] Test query riwayat pesan

**API Routes**
- [ ] Generate pesan pertama
- [ ] Generate follow-up
- [ ] Regenerate pesan
- [ ] Mark as sent
- [ ] Get message history

**Templates**
- [ ] `messages/preview.html` — pilih variasi
- [ ] `messages/history.html` — riwayat pesan
- [ ] `partials/wa_button.html` — tombol WA
- [ ] Integrasi di `prospects/detail.html`

**Testing**
- [ ] Test generate pesan pertama
- [ ] Test generate follow-up angle berbeda
- [ ] Test WA link terbuka dengan pesan benar
- [ ] Test mark as sent tersimpan
- [ ] Test regenerate menghasilkan pesan berbeda
- [ ] Verifikasi pesan ≤300 karakter

---

### Estimasi Waktu

| Task | Waktu |
|---|---|
| prompts first & followup | 2–3 jam |
| message_generator.py | 3–4 jam |
| WA link generator | 1 jam |
| API routes | 1–2 jam |
| Templates & UI | 2–3 jam |
| Testing & debugging | 2–3 jam |
| **Total** | **~2–3 hari** |