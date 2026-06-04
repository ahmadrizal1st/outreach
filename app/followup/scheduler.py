from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.followup.tracker import FollowupTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def run_followup_check():
    logger.info("Starting scheduled follow-up check...")
    tracker = FollowupTracker()
    result = tracker.check_and_flag()
    logger.info(f"Follow-up check completed: {result}")

async def run_expire_preview():
    from app.preview.generator import PreviewGenerator
    logger.info("Starting preview expiry check...")
    generator = PreviewGenerator()
    generator.check_and_expire()
    logger.info("Preview expiry check completed.")

def init_scheduler():
    # Run follow-up check every day at 07:00 AM
    scheduler.add_job(
        func=run_followup_check,
        trigger=CronTrigger(hour=7, minute=0),
        id="followup_check_job",
        name="Daily Follow-up Check",
        replace_existing=True
    )

    # Run expire check every day at 00:30 AM
    scheduler.add_job(
        func=run_expire_preview,
        trigger=CronTrigger(hour=0, minute=30),
        id="expire_preview_job",
        name="Expire Preview Harian",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("APScheduler started successfully.")
