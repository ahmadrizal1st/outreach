import re

class DataNormalizer:

    def normalize_phone(self, phone: str) -> str:
        if not phone:
            return None
        # Hapus semua non-digit
        digits = re.sub(r'\D', '', phone)
        # Konversi ke format internasional
        if digits.startswith('0'):
            digits = '62' + digits[1:]
        elif not digits.startswith('62'):
            digits = '62' + digits
        return digits

    def normalize_rating(self, rating: str) -> float:
        if not rating:
            return None
        try:
            return float(str(rating).replace(',', '.'))
        except:
            return None

    def normalize_review_count(self, count: str) -> int:
        if not count:
            return 0
        digits = re.sub(r'\D', '', str(count))
        return int(digits) if digits else 0

    def normalize_url(self, url: str) -> str:
        if not url:
            return None
        if not url.startswith('http'):
            url = 'https://' + url
        return url.strip()
