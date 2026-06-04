def get_preview_content_prompt(prospect: dict, score: dict, review: dict = None) -> list:
    system = """
Kamu adalah copywriter profesional untuk website bisnis lokal Indonesia.

Tugasmu membuat konten website yang menarik, natural, dan sesuai dengan karakter bisnis tersebut.

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
Keywords   : {score.get('relevant_keywords') if score else '-'}
Layanan    : {score.get('recommended_service') if score else '-'}
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
