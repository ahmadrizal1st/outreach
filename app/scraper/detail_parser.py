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
