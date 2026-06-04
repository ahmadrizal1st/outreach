# Architecture & Tech Stack

## 1. System Overview
The **Outreach** project is an automated client prospecting platform.
It is designed to:
1. **Scrape** target businesses from Google Maps.
2. **Score & Prioritize** leads using LLMs (Gemini/Groq).
3. **Manage** the data through a local web dashboard.
4. **Review** potential client websites via AI.
5. **Generate** tailored WhatsApp outreach messages.
6. **Track** follow-ups automatically.
7. **Generate** preview HTML websites to send to prospects.

## 2. Technology Stack
- **Backend Core:** Python 3.x, FastAPI
- **Frontend Core:** HTML5, HTMX, Tailwind CSS, Jinja2 Templates
- **Database:** SQLite (local, single file DB)
- **Scraping Engine:** Playwright (Python async)
- **AI Integration:** LiteLLM (Supports both Gemini and Groq)

## 3. Directory Structure (Proposed)
```
outreach/
├── main.py               # FastAPI application entry point
├── config.py             # Environment variables and configuration
├── database/             # SQLite connection and schema definitions
├── models/               # Pydantic models & Database ORM models
├── routers/              # FastAPI route definitions (endpoints)
├── services/             # Business logic
│   ├── scraper.py        # Playwright Google Maps logic
│   ├── ai_scorer.py      # LiteLLM scoring logic
│   ├── generator.py      # WhatsApp message & Website preview logic
│   └── follow_up.py      # Follow-up interval tracking
├── templates/            # Jinja2 HTML files (Dashboard, partials)
├── static/               # Static assets (Tailwind output, images)
├── plan/                 # Project documentation and phases
└── .agents/              # AI Agent rules (You are here)
```

## 4. Key Architectural Decisions
- **Monolith with Services:** The application is a local monolith. It is designed to be run locally by the user (not a cloud SaaS initially).
- **Server-Side Rendering (SSR) via HTMX:** To reduce frontend complexity, the backend renders HTML directly and HTMX handles DOM swaps. No heavy SPA frameworks.
- **Resilient Scraping:** The scraping engine must handle interruptions. Deduplication (checking if a business is already scraped) must occur before insertion.
- **AI Fallbacks:** The LiteLLM integration ensures we are not locked into a single provider and can gracefully degrade or switch providers on rate limits.
