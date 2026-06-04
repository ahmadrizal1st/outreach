import csv
import os
from datetime import date
from openpyxl import Workbook
from app.core.database import SessionLocal
from app.models.prospect import Prospect, ProspectScore, Pipeline

class DataExporter:
    def __init__(self):
        self.export_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "exports"))
        os.makedirs(self.export_dir, exist_ok=True)

    def export_csv(self, tier: str = None) -> str:
        prospects = self._get_prospects(tier)
        filename = f"prospects_{date.today()}.csv"
        filepath = os.path.join(self.export_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'name', 'category', 'city', 'phone_raw', 'website', 'rating',
                'review_count', 'priority_tier', 'priority_score', 'contact_status'
            ])
            writer.writeheader()
            for prospect in prospects:
                writer.writerow(dict(prospect))

        return filepath

    def export_excel(self, tier: str = None) -> str:
        prospects = self._get_prospects(tier)
        filename = f"prospects_{date.today()}.xlsx"
        filepath = os.path.join(self.export_dir, filename)

        wb = Workbook()
        ws = wb.active
        ws.title = "Prospects"

        headers = [
            'Nama', 'Kategori', 'Kota', 'Telepon', 'Website', 'Rating', 'Review',
            'Tier', 'Score', 'Status'
        ]
        ws.append(headers)

        for prospect in prospects:
            ws.append([
                prospect['name'],
                prospect['category'],
                prospect['city'],
                prospect['phone_raw'],
                prospect['website'] or '-',
                prospect['rating'],
                prospect['review_count'],
                prospect['priority_tier'],
                prospect['priority_score'],
                prospect['contact_status']
            ])

        wb.save(filepath)
        return filepath

    def _get_prospects(self, tier: str = None):
        db = SessionLocal()
        try:
            query = db.query(Prospect, ProspectScore, Pipeline).outerjoin(
                ProspectScore, Prospect.id == ProspectScore.prospect_id
            ).outerjoin(
                Pipeline, Prospect.id == Pipeline.prospect_id
            ).filter(
                (Pipeline.is_blacklisted == False) | (Pipeline.id == None)
            )

            if tier:
                query = query.filter(ProspectScore.priority_tier == tier)

            query = query.order_by(ProspectScore.priority_score.desc())
            results = query.all()

            data = []
            for p, s, pl in results:
                data.append({
                    'name': p.name,
                    'category': p.category,
                    'city': p.city,
                    'phone_raw': p.phone_raw,
                    'website': p.website,
                    'rating': p.rating,
                    'review_count': p.review_count,
                    'priority_tier': s.priority_tier if s else None,
                    'priority_score': s.priority_score if s else None,
                    'contact_status': pl.contact_status if pl else 'belum_dihubungi'
                })
            return data
        finally:
            db.close()
