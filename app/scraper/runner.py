from app.scraper.maps_scraper import MapsScraper
from app.core.database import SessionLocal
from app.models.prospect import Prospect, ScraperConfig, ScraperProgress
from datetime import datetime

class ScraperRunner:

    def __init__(self):
        self.progress = {}

    async def run(self):
        db = SessionLocal()
        try:
            config = db.query(ScraperConfig).filter(ScraperConfig.is_active == True).first()
            if not config:
                return {"error": "Konfigurasi scraper belum diset atau tidak aktif"}

            if not config.keywords or not config.target_cities:
                return {"error": "Keywords atau cities belum diset di konfigurasi"}

            keywords = [k.strip() for k in config.keywords.split(',')]
            cities = [c.strip() for c in config.target_cities.split(',')]
            total_saved_today = 0

            for city in cities:
                for keyword in keywords:

                    if self._is_completed(db, keyword, city):
                        continue

                    scraper = MapsScraper(config)
                    results = await scraper.scrape(keyword, city)

                    # Simpan ke database
                    saved = self._save_results(db, results, keyword, city)
                    total_saved_today += saved

                    # Catat progress
                    self._mark_completed(db, keyword, city, len(results), saved)

                    # Delay antar keyword
                    await scraper.limiter.wait_between_sessions()

            return {"status": "done", "total_saved": total_saved_today}
        finally:
            db.close()

    def _save_results(self, db, results, keyword, city):
        count = 0
        for data in results:
            try:
                prospect = Prospect(**data)
                db.add(prospect)
                db.commit()
                count += 1
            except Exception as e:
                db.rollback()
                continue
        return count

    def _is_completed(self, db, keyword, city):
        today = datetime.utcnow().date()
        from sqlalchemy import func
        result = db.query(ScraperProgress).filter(
            ScraperProgress.keyword == keyword,
            ScraperProgress.city == city,
            func.date(ScraperProgress.scraped_at) == today
        ).first()
        return result is not None

    def _mark_completed(self, db, keyword, city, total_found, total_saved):
        progress = ScraperProgress(
            keyword=keyword,
            city=city,
            total_found=total_found,
            total_saved=total_saved
        )
        db.add(progress)
        db.commit()
