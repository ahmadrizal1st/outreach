from playwright.async_api import Page

class DetailParser:

    async def parse(self, page: Page) -> dict:
        data = {}

        # Nama bisnis
        data['name'] = await self._get_text(
            page, 'h1.DUwDvf'
        )

        # Kategori
        data['category'] = await self._get_text(
            page, 'button.DkEaL'
        )

        # Rating
        data['rating'] = await self._get_text(
            page, 'div.F7nice span'
        )

        # Jumlah review
        data['review_count'] = await self._get_text(
            page, 'div.F7nice span[aria-label]'
        )

        # Alamat
        data['address'] = await self._get_text(
            page, 'button[data-item-id="address"]'
        )

        # Telepon
        data['phone_raw'] = await self._get_text(
            page, 'button[data-item-id^="phone"]'
        )

        # Website
        data['website'] = await self._get_attr(
            page, 'a[data-item-id="authority"]', 'href'
        )

        # Jam operasional
        data['hours'] = await self._get_hours(page)

        # Google Maps URL
        data['google_maps_url'] = page.url

        # Foto
        data['photo_urls'] = await self._get_photos(page)

        # Status Klaim Bisnis
        data['is_claimed'] = await self._check_is_claimed(page)
        
        # Instagram URL
        data['instagram_url'] = await self._get_instagram(page)
        
        # About Summary
        data['about_summary'] = await self._get_about_summary(page)

        return data

    async def _get_text(self, page, selector):
        try:
            el = await page.query_selector(selector)
            if el:
                return await el.inner_text()
        except:
            pass
        return None

    async def _get_attr(self, page, selector, attr):
        try:
            el = await page.query_selector(selector)
            if el:
                return await el.get_attribute(attr)
        except:
            pass
        return None

    async def _get_hours(self, page):
        # Extract jam operasional sebagai JSON string
        try:
            hours = {}
            rows = await page.query_selector_all(
                'table.eK4R0e tr'
            )
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 2:
                    day = await cells[0].inner_text()
                    time = await cells[1].inner_text()
                    hours[day.strip()] = time.strip()
            return str(hours) if hours else None
        except:
            return None

    async def _get_photos(self, page):
        try:
            photos = []
            imgs = await page.query_selector_all(
                'div.RZ66Rb img'
            )
            for img in imgs[:5]:
                src = await img.get_attribute('src')
                if src:
                    photos.append(src)
            return str(photos)
        except:
            return None

    async def _check_is_claimed(self, page):
        try:
            content = await page.content()
            if "Klaim bisnis ini" in content or "Own this business?" in content or "Claim this business" in content:
                return False
            return True
        except:
            return True

    async def _get_instagram(self, page):
        try:
            links = await page.query_selector_all('a[href*="instagram.com"]')
            for link in links:
                href = await link.get_attribute('href')
                if href and 'instagram.com' in href:
                    return href
        except:
            pass
        return None

    async def _get_about_summary(self, page):
        try:
            summary_el = await page.query_selector('div.PYvSYb')
            if summary_el:
                return await summary_el.inner_text()
        except:
            pass
        return None
