from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def init_scheduler():
    # Job 1: Cek follow-up setiap pagi jam 07.00
    scheduler.add_job(
        func=run_followup_check,
        trigger=CronTrigger(hour=7, minute=0),
        id="followup_check",
        name="Cek Follow-up Harian",
        replace_existing=True
    )

    # Job 2: Scraping setiap pagi jam 08.00
    # scheduler.add_job(
    #     func=run_daily_scraping,
    #     trigger=CronTrigger(hour=8, minute=0),
    #     id="daily_scraping",
    #     name="Scraping Harian",
    #     replace_existing=True
    # )

    # Job 3: Auto scoring setiap jam 09.00
    # scheduler.add_job(
    #     func=run_auto_scoring,
    #     trigger=CronTrigger(hour=9, minute=0),
    #     id="auto_scoring",
    #     name="Auto Scoring",
    #     replace_existing=True
    # )

    # Job 4: Reset token provider setiap tengah malam
    # scheduler.add_job(
    #     func=reset_provider_tokens,
    #     trigger=CronTrigger(hour=0, minute=0),
    #     id="reset_tokens",
    #     name="Reset Token Provider",
    #     replace_existing=True
    # )

    scheduler.start()
    logger.info("Scheduler started")

async def run_followup_check():
    try:
        from app.followup.tracker import FollowupTracker
        tracker = FollowupTracker()
        result = tracker.check_and_flag()
        logger.info(f"Follow-up check: {result}")
    except Exception as e:
        logger.error(f"Follow-up check error: {e}")

# Commented out others as they are not fully implemented/imported yet but mentioned in the plan
# async def run_daily_scraping():
#     try:
#         from app.scraper.runner import ScraperRunner
#         runner = ScraperRunner()
#         result = await runner.run()
#         logger.info(f"Scraping: {result}")
#     except Exception as e:
#         logger.error(f"Scraping error: {e}")

# async def run_auto_scoring():
#     try:
#         from app.ai.scorer import BusinessScorer
#         scorer = BusinessScorer()
#         result = await scorer.score_all_unscored()
#         logger.info(f"Scoring: {result}")
#     except Exception as e:
#         logger.error(f"Scoring error: {e}")

# async def reset_provider_tokens():
#     try:
#         from app.core.database import get_db
#         db = next(get_db())
#         db.execute("""
#             UPDATE llm_providers
#             SET tokens_used_today = 0,
#                 is_available = TRUE,
#                 last_reset_at = DATE('now')
#         """)
#         db.commit()
#         logger.info("Provider tokens reset")
#     except Exception as e:
#         logger.error(f"Token reset error: {e}")
