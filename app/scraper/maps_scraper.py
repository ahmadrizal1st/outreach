import os
import random
import asyncio
from playwright.async_api import async_playwright
from app.scraper.detail_parser import DetailParser
from app.scraper.rate_limiter import RateLimiter
from app.scraper.normalizer import DataNormalizer
from app.scraper.deduplicator import Deduplicator

class MapsScraper:

    def __init__(self, config):
        self.config = config
        self.parser = DetailParser()
        self.limiter = RateLimiter(
            config.delay_min_seconds,
            config.delay_max_seconds
        )
        self.normalizer = DataNormalizer()
        self.deduplicator = Deduplicator()
        self.results = []

    def _profile_exists(self):
        return os.path.exists("browser_profile.json")

    def _normalize(self, raw_data):
        raw_data['phone_normalized'] = self.normalizer.normalize_phone(raw_data.get('phone_raw'))
        raw_data['rating'] = self.normalizer.normalize_rating(raw_data.get('rating'))
        raw_data['review_count'] = self.normalizer.normalize_review_count(raw_data.get('review_count'))
        raw_data['website'] = self.normalizer.normalize_url(raw_data.get('website'))

        place_id_match = raw_data.get('google_maps_url', '').split('!')
        if len(place_id_match) > 1:
            raw_data['place_id'] = place_id_match[-1]
        else:
            raw_data['place_id'] = raw_data.get('name', '') + raw_data.get('address', '')
            
        return raw_data

    async def scrape(self, keyword: str, city: str, stop_flag: dict = None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            context = await browser.new_context(
                storage_state="browser_profile.json" if self._profile_exists() else None,
                viewport={
                    'width': random.randint(1200, 1400),
                    'height': random.randint(800, 900)
                },
                user_agent=self._random_user_agent()
            )
            page = await context.new_page()

            query = f"{keyword} {city}"
            url = f"https://www.google.com/maps/search/{query}"
            await page.goto(url)
            await page.wait_for_load_state('networkidle')

            await self._scroll_listings(page)

            listings = await page.query_selector_all('div.Nv2PK')

            for listing in listings:
                
                if stop_flag and stop_flag.get("should_stop"):
                    break

                if self.limiter.is_daily_limit_reached():
                    break

                await listing.click()
                await page.wait_for_load_state('networkidle')
                await self.limiter.wait()

                raw_data = await self.parser.parse(page)
                raw_data['source_keyword'] = keyword
                raw_data['source_city'] = city

                data = self._normalize(raw_data)

                if self.deduplicator.is_duplicate(data.get('place_id')):
                    continue

                self.results.append(data)
                self.limiter.increment()

                await self.limiter.wait()

            await browser.close()
            return self.results

    async def _scroll_listings(self, page, max_attempts: int = 25):
        """Scroll the listings panel to load more, with max_attempts limit."""
        panel = await page.query_selector('div[role="feed"]')
        if panel:
            prev_count = 0
            attempts = 0
            while attempts < max_attempts:
                await panel.evaluate('el => el.scrollTop += 1000')
                await asyncio.sleep(2)
                listings = await page.query_selector_all('div.Nv2PK')
                if len(listings) == prev_count:
                    break
                prev_count = len(listings)
                attempts += 1

    def _random_user_agent(self):
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        return random.choice(agents)
