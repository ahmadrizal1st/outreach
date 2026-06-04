"""
ScraperRunner — orchestrates scraping sessions with start/stop/progress support.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.scraper.maps_scraper import MapsScraper
from app.models.prospect import Prospect, ScraperConfig, ScraperProgress

logger = logging.getLogger(__name__)

class ScraperRunner:

    def __init__(self, db: Session):
        self.db = db

    async def run_single(
        self,
        keyword: str,
        city: str,
        max_results: int = 20,
        stop_flag: dict = None,
    ) -> dict:
        """
        Run scraping for a single keyword + city pair.
        stop_flag is a shared dict with key 'should_stop'; checked between listings.
        """
        config = self.db.query(ScraperConfig).first()
        if not config:
            config = ScraperConfig(keywords=keyword, target_cities=city, max_per_day=max_results)

        config.max_per_day = max_results

        scraper = MapsScraper(config)

        results = await scraper.scrape(
            keyword=keyword,
            city=city,
            stop_flag=stop_flag,
        )

        found = len(results)
        saved = self._save_results(results, keyword, city)
        self._mark_progress(keyword, city, found, saved)

        return {"found": found, "saved": saved}

    async def run_from_config(self, stop_flag: dict = None) -> dict:
        """Run using the saved ScraperConfig from DB (legacy method)."""
        config = self.db.query(ScraperConfig).filter(ScraperConfig.is_active == True).first()
        if not config:
            return {"error": "Konfigurasi scraper belum diset atau tidak aktif"}

        if not config.keywords or not config.target_cities:
            return {"error": "Keywords atau cities belum diset di konfigurasi"}

        keywords = [k.strip() for k in config.keywords.split(',') if k.strip()]
        cities = [c.strip() for c in config.target_cities.split(',') if c.strip()]
        total_saved = 0

        for city in cities:
            for keyword in keywords:
                if stop_flag and stop_flag.get("should_stop"):
                    break
                if self._is_completed_today(keyword, city):
                    logger.info(f"Skipping {keyword}@{city} (done today)")
                    continue
                result = await self.run_single(keyword, city, config.max_per_day, stop_flag)
                total_saved += result.get("saved", 0)

            if stop_flag and stop_flag.get("should_stop"):
                break

        return {"status": "done", "total_saved": total_saved}

    def _save_results(self, results: list, keyword: str, city: str) -> int:
        """Save scraped prospects to DB, skip duplicates."""
        count = 0
        for data in results:
            try:
                
                existing = self.db.query(Prospect).filter(
                    Prospect.place_id == data.get("place_id")
                ).first() if data.get("place_id") else None

                if existing:
                    continue

                prospect = Prospect(**data)
                self.db.add(prospect)
                self.db.commit()
                count += 1
            except Exception as e:
                logger.warning(f"Error saving prospect: {e}")
                self.db.rollback()
        return count

    def _is_completed_today(self, keyword: str, city: str) -> bool:
        today = datetime.utcnow().date()
        result = self.db.query(ScraperProgress).filter(
            ScraperProgress.keyword == keyword,
            ScraperProgress.city == city,
            func.date(ScraperProgress.scraped_at) == today,
            ScraperProgress.status == "completed",
        ).first()
        return result is not None

    def _mark_progress(self, keyword: str, city: str, found: int, saved: int):
        progress = ScraperProgress(
            keyword=keyword,
            city=city,
            total_found=found,
            total_saved=saved,
            status="completed",
        )
        self.db.add(progress)
        self.db.commit()
