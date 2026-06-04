def get_website_review_prompt(prospect: dict, check_result: dict) -> list:
    system = """
Kamu adalah web developer senior yang menganalisis kualitas website bisnis lokal Indonesia.

Tugasmu menilai website dan menemukan peluang improvement yang bisa ditawarkan sebagai jasa.

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

KONTEN WEBSITE (Potongan Teks):
Title: {check_result.get('page_title')}
Meta : {check_result.get('meta_description')}
Teks : {check_result.get('page_text', '')[:1000]}

Berikan analisis dalam format JSON berikut:
{ 
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
} 

opportunity_type: remake/redesign/optimasi/none
estimated_value: low/medium/high
urgency: low/medium/high
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
