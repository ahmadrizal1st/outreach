# Workflow & Execution Guidelines

## 1. Phased Development (Strict Rule)
The project is divided into 9 phases (documented in `plan/PLAN.md`).
**CRITICAL RULE:** The Agent must strictly follow the phase order. Do not implement features or write code for Phase N+1 if Phase N is not complete, unless explicitly instructed by the user.

- **Phase 1:** Foundation (Setup, DB, FastAPI, HTMX+Tailwind)
- **Phase 2:** Scraping Engine (Playwright, Maps, Deduplication)
- **Phase 3:** AI Scoring (LiteLLM, Prompts, Tracking)
- **Phase 4:** Dashboard (Views, Filters, Data Management)
- **Phase 5:** Review Website (AI Scan, Confirmations)
- **Phase 6:** Generate Pesan (WA Messages, Keywords)
- **Phase 7:** Follow-up System (Intervals, Status)
- **Phase 8:** Website Preview (HTML Generation)
- **Phase 9:** Polish & Testing

## 2. Pre-Task Verification
Before starting any coding task, you MUST:
1. Read the corresponding `plan/PHASE-X.md` to understand the exact scope.
2. Review any existing code relevant to the phase.
3. Check `plan/PLAN.md` to keep the high-level context in mind.

## 3. Post-Task Action (Checklist Updates)
When a task within a phase is completed:
1. Open the relevant `plan/PHASE-X.md` or `plan/PLAN.md`.
2. Locate the checklist item (e.g., `- [ ] Setup database`).
3. Modify it to show completion (e.g., `- [x] Setup database`).
4. This ensures the user and the agent always have a synchronized view of progress.

## 4. Dealing with Ambiguity
If a requirement is vague (for example, "Setup prompt for scoring" without specifying the exact criteria), the Agent must:
- Either propose a sensible default and ask the user for confirmation.
- Or halt and ask the user for the specific criteria before writing the code.
Do not guess complex business rules without user validation.
