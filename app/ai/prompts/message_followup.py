def get_followup_message_prompt(
    prospect: dict,
    score: dict,
    review: dict,
    previous_messages: list,
    followup_sequence: int
) -> list:

    system = """
Kamu adalah spesialis sales copywriting untuk jasa pembuatan website di Indonesia.

Tugasmu menulis pesan follow-up WhatsApp yang natural dan tidak mengganggu.

ATURAN KETAT:
- Maksimal 300 karakter
- JANGAN ulangi pesan sebelumnya
- Gunakan angle yang berbeda dari pesan sebelumnya
- Tidak boleh terkesan memaksa atau desperate
- Tetap natural dan ramah
- PENTING: Jawab HANYA dalam format JSON
"""

    prev_messages_text = "\n".join([
        f"Pesan #{i+1} ({msg.get('tone', '-')}): {msg.get('content')}"
        for i, msg in enumerate(previous_messages)
    ])

    angle_guide = {
        1: "Tunjukkan contoh atau social proof yang relevan",
        2: "Tawarkan konsultasi gratis tanpa komitmen",
        3: "Tanyakan apakah mereka butuh waktu lebih atau tidak tertarik"
    }
    angle = angle_guide.get(followup_sequence, "Angle pendekatan baru yang belum pernah dipakai")

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
{ 
  "variants": [
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
