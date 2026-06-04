from datetime import date, timedelta

class ContentBuilder:
    def build(self, prospect: dict, ai_content: dict) -> dict:
        return {
            "business_name": prospect.get('name', ''),
            "category": prospect.get('category', ''),
            "city": prospect.get('city', ''),
            "address": prospect.get('address', ''),
            "phone": prospect.get('phone_raw', ''),
            "phone_wa": prospect.get('phone_normalized', ''),
            "rating": prospect.get('rating', ''),
            "review_count": prospect.get('review_count', 0),
            "maps_url": prospect.get('google_maps_url', ''),

            "tagline": ai_content.get('tagline', f"Selamat Datang di {prospect.get('name')}"),
            "hero_description": ai_content.get('hero_description', ''),
            "about_text": ai_content.get('about_text', ''),
            "services": ai_content.get('services', []),
            "cta_text": ai_content.get('cta_text', 'Hubungi Kami'),
            "footer_tagline": ai_content.get('footer_tagline', ''),

            "generated_date": date.today().strftime("%d %B %Y"),
            "expired_date": (date.today() + timedelta(days=14)).strftime("%d %B %Y"),
            "preview_note": f"Preview ini dibuat khusus untuk {prospect.get('name')} oleh tim kami."
        }
