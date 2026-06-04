# Code Rules & Guidelines

## 1. Backend (Python & FastAPI)
- **Typing:** Use strict Python type hints (`->`, `str`, `int`, `List`, `Dict`) for all function signatures and variables where applicable.
- **Async/Await:** Playwright scraping and API calls (LiteLLM) must be handled asynchronously (`async def`) so they do not block the FastAPI event loop. Database calls should be async if using an async driver, or run in a thread pool if synchronous.
- **Error Handling:** Use granular `try/except` blocks for all external dependencies (Scraping, AI APIs, DB operations). Return appropriate HTTP status codes via FastAPI `HTTPException`.
- **Modularity:** Do not put complex logic in FastAPI router files. Keep route functions thin and delegate business logic to separate service files (e.g., `services/scraper.py`, `services/ai_scorer.py`).
- **Validation:** Use Pydantic models extensively for all incoming request bodies and outgoing responses.

## 2. Frontend (HTMX & Tailwind)
- **Styling:** Rely solely on Tailwind CSS utility classes. Avoid writing custom CSS (like inline styles or custom `.css` files) unless absolutely necessary.
- **Interactivity:** Use HTMX for dynamic behaviors (e.g., `hx-get`, `hx-post`, `hx-swap="innerHTML"`, `hx-target`). Minimize the use of custom JavaScript (Vanilla JS or frameworks like React/Vue are NOT used).
- **Templates:** Use Jinja2 as the templating engine. Return partial HTML snippets from FastAPI endpoints for HTMX to swap into the DOM.

## 3. Database (SQLite)
- **Integrity & Schema:** Ensure foreign keys are enabled (SQLite PRAGMA foreign_keys = ON).
- **Performance:** Use `WAL` (Write-Ahead Logging) mode to handle concurrent reads and writes safely.
- **Queries:** Use an ORM (like SQLAlchemy or SQLModel) or Raw SQL, but ensure queries are optimized with appropriate indexes on fields frequently queried (e.g., `status`, `city`, `priority_score`).

## 4. Scraping & AI Rules
- **Playwright:** Always implement random delays, rate limit handling, and human-like interactions to prevent getting blocked by Google Maps.
- **LiteLLM:** Ensure proper fallback logic. If Gemini rate limits or fails, fallback to Groq automatically.
- **Token Tracking:** Log AI token usage to avoid unexpected costs.
