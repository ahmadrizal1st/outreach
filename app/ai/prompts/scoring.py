def get_scoring_prompt(prospect: dict) -> list:
    system = """
Kamu adalah analis bisnis yang mengevaluasi potensi
calon client untuk jasa pembuatan website.

Tugasmu adalah memberi skor prioritas 1-10 berdasarkan
data bisnis yang diberikan.

KRITERIA SCORING:
- Tidak punya website     : bobot 30%
- Rating Google >= 4.0     : bobot 20%
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
