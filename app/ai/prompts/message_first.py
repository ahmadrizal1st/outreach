def get_first_message_prompt(
    prospect: dict,
    score: dict,
    review: dict = None
) -> list:

    system = """
Kamu adalah spesialis sales copywriting untuk jasa pembuatan website di Indonesia.

Tugasmu menulis pesan WhatsApp yang personal, natural, dan tidak terasa seperti spam.

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

    website_context = "Tidak punya website"
    if review:
        if review.get('opportunity_type') == 'remake':
            website_context = "Website ada tapi perlu dibuat ulang"
        elif review.get('opportunity_type') == 'redesign':
            website_context = "Website ada tapi perlu redesign"
        elif review.get('opportunity_type') == 'optimasi':
            website_context = "Website ada, perlu optimasi"
        elif review.get('opportunity_type') == 'none':
            website_context = "Website sudah bagus"

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
{ 
  "variants": [
    { 
      "tone": "formal",
      "message": "..."
    } ,
    { 
      "tone": "semi-formal",
      "message": "..."
    } ,
    { 
      "tone": "kasual",
      "message": "..."
    } 
  ]
} 
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
