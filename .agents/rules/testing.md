# Testing & Debugging Guidelines

## 1. Python Backend Testing
- **Framework:** Use `pytest` for all backend testing.
- **API Tests:** Use `TestClient` from FastAPI to test routes without spinning up a real server.
- **Database:** When running tests, always use an in-memory SQLite database (`sqlite:///:memory:`) to avoid polluting the development database.

## 2. Scraping Debugging (Playwright)
- **Headless Mode:** During active development of the scraper, run Playwright with `headless=False` so we can visually debug what the browser is doing.
- **Mocking:** Do not run live Google Maps scraping in unit tests. Mock the Playwright responses or use saved HTML snapshots of Google Maps for testing the parsing logic.

## 3. AI Integrations (LiteLLM)
- **Mocking LLMs:** Do not hit the real Gemini/Groq APIs during automated testing to save costs and avoid rate limits. Use LiteLLM's built-in mocking or `pytest-mock` to mock `litellm.completion`.
- **Prompt Debugging:** Always log the exact prompt being sent and the raw response received when in `DEBUG` logging mode.
