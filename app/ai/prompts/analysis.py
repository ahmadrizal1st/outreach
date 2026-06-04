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
{ 
  "digital_maturity": "rendah/menengah/tinggi",
  "main_opportunity": "...",
  "pain_points": ["...", "..."],
  "value_proposition": "...",
  "competitor_advantage": "...",
  "urgency_reason": "..."
} 
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
