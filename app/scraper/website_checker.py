import httpx
from bs4 import BeautifulSoup

class WebsiteChecker:
    def __init__(self, timeout=15):
        self.timeout = timeout

    async def check(self, url: str) -> dict:
        result = {
            "website_status": "accessible",
            "is_mobile_friendly": False,
            "has_ssl": False,
            "has_ecommerce": False,
            "has_booking": False,
            "has_contact_form": False,
            "speed_score": 5,
            "raw_html": None,
            "page_title": None,
            "meta_description": None,
            "page_text": None,
        }

        # Normalize URL
        if not url.startswith("http"):
            url = "https://" + url

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False # We might encounter self-signed certificates, just ignore for scraping
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                )

                # Check SSL based on final URL after redirects
                final_url = str(response.url)
                result["has_ssl"] = final_url.startswith("https")

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Check mobile friendly
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                result["is_mobile_friendly"] = viewport is not None

                # Clean up text for keyword matching and AI context
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.extract()
                
                page_text_raw = soup.get_text(separator=' ')
                # Compress spaces
                page_text = ' '.join(page_text_raw.split())
                page_text_lower = page_text.lower()

                # Check ecommerce
                ecommerce_keywords = [
                    'cart', 'keranjang', 'checkout',
                    'add to cart', 'beli', 'shop', 'troli'
                ]
                result["has_ecommerce"] = any(kw in page_text_lower for kw in ecommerce_keywords)

                # Check booking
                booking_keywords = [
                    'booking', 'reservasi', 'jadwal',
                    'appointment', 'pesan sekarang', 'buat janji'
                ]
                result["has_booking"] = any(kw in page_text_lower for kw in booking_keywords)

                # Check contact form
                forms = soup.find_all('form')
                result["has_contact_form"] = len(forms) > 0

                # Speed score (estimation from resource count)
                # Note: We parse the raw text for this, not the cleaned soup
                soup_raw = BeautifulSoup(response.text, 'html.parser')
                scripts = len(soup_raw.find_all('script'))
                images = len(soup_raw.find_all('img'))
                stylesheets = len(soup_raw.find_all('link', attrs={'rel': 'stylesheet'}))
                total_resources = scripts + images + stylesheets
                
                if total_resources < 15:
                    result["speed_score"] = 9
                elif total_resources < 30:
                    result["speed_score"] = 7
                elif total_resources < 60:
                    result["speed_score"] = 5
                else:
                    result["speed_score"] = 3

                # Extract text for AI
                result["page_title"] = soup.title.string.strip() if soup.title and soup.title.string else None
                
                meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_desc_tag:
                    result["meta_description"] = meta_desc_tag.get('content', '').strip()
                else:
                    result["meta_description"] = None
                    
                result["page_text"] = page_text[:3000] # Limit context size for AI
                result["raw_html"] = response.text[:5000]

        except httpx.TimeoutException:
            result["website_status"] = "timeout"
        except httpx.ConnectError:
            result["website_status"] = "error"
        except Exception as e:
            result["website_status"] = "error"
            print(f"Error checking {url}: {e}")

        return result
